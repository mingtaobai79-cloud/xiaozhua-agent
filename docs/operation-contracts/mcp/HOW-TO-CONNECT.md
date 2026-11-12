# 怎么接 xiaozhua MCP

> 面向：想在 Hermes / Codex / Claude Code 之外，或者自己的 agent 里接入的人。
> 权威工具清单：`docs/operation-contracts/mcp/TOOLS.md`（自动生成，勿手改）
> 2026-11-09 实测：stdio 端到端通，44 个工具，`initialize` / `tools/list` / `tools/call` 全部正常。

## 一、前置

```
Python 3.11+
仓库：<XIAOZHUA_AGENT_ROOT>（本机示例 <XIAOZHUA_AGENT_ROOT>）
虚拟环境：<XIAOZHUA_AGENT_ROOT>/.venv
```

依赖装好之后先自检一遍（不联网）：

```bash
cd <XIAOZHUA_AGENT_ROOT>
./.venv/Scripts/python.exe -c "from xiaozhua_host_bootstrap import bootstrap; b=bootstrap(); print(len(b))"
```

能打印出数字（约 50）就说明装配正常。

## 二、传输层

**stdio，JSON-RPC 2.0，一行一帧。** 没有 HTTP、没有端口、没有额外服务。

```bash
<XIAOZHUA_AGENT_ROOT>/.venv/Scripts/python.exe <XIAOZHUA_AGENT_ROOT>/adapters/mcp/server.py
```

| 项 | 值 |
|---|---|
| protocolVersion | `2024-11-05` |
| serverInfo | `{"name": "xiaozhua-mcp", "version": "0.1.0"}` |
| method 白名单 | `initialize` / `tools/list` / `tools/call`（`notifications/initialized` 静默 ack） |
| 未知 method | `-32601` |
| 参数缺/型错 | `-32602` |

## 三、三宿主配置

### Hermes

贴进 `~/.hermes/config.yaml` 的**顶层** `mcp_servers:` 段：

```yaml
mcp_servers:
  xiaozhua:
    command: <XIAOZHUA_AGENT_ROOT>/.venv/Scripts/python.exe
    args:
      - <XIAOZHUA_AGENT_ROOT>/adapters/mcp/server.py
    timeout: 180
```

### Codex

`~/.codex/config.toml`：

```toml
[mcp_servers.xiaozhua]
command = "<XIAOZHUA_AGENT_ROOT>/.venv/Scripts/python.exe"
args = ["<XIAOZHUA_AGENT_ROOT>/adapters/mcp/server.py"]
```

### Claude Code

项目根 `.mcp.json`：

```json
{
  "mcpServers": {
    "xiaozhua": {
      "command": "<XIAOZHUA_AGENT_ROOT>/.venv/Scripts/python.exe",
      "args": ["<XIAOZHUA_AGENT_ROOT>/adapters/mcp/server.py"]
    }
  }
}
```

### 不想写死绝对路径

```bash
python installer/install.py --host all --target <输出目录> --portable
```

`--portable` 用 `<XIAOZHUA_AGENT_ROOT>` 占位符代替本机路径。不加 `--write` 是 dry-run，
只打印计划不落盘。

## 四、验证连上了

配完重启宿主，然后问：

```
调用 xiaozhua_capability_index，传空参数
```

正常返回：

```json
{
  "domain_count": 9,
  "summary": {"契约合计": 133, "有工具": ["entity","flow","rule","setting"], "未做": ["bi","column","role"]},
  "domains": {...},
  "custom": {...}
}
```

看不到这个工具就是没连上。排查顺序：
1. `command` 路径里有没有 `.venv`（用系统 python 会缺依赖）
2. `args` 是不是指向 `adapters/mcp/server.py`（不是仓库根）
3. 宿主日志里有没有 spawn 失败

## 五、怎么用

### 先查能力面

```
xiaozhua_capability_index()              → 九大域全量
xiaozhua_capability_index("setting")     → 只返回设置域
xiaozhua_capability_index("rule")        → 规则域
```

每个域返回 `tools` / `facts` / `contracts` / `status` / `note`，`note` 里写着这个域的坑。

### 典型链路：生成一条微流程

```
1. xiaozhua_microflow_trigger(kind="MANUAL")                    造触发器
2. xiaozhua_microflow_node(action="create_variable", ...)       造节点（重复 N 次）
3. xiaozhua_microflow_data_schema(name, caption, trigger, nodes) 组装 dataSchema
4. xiaozhua_microflow_gates(schema)                             过 G1–G41，problems 必须为空
5. xiaozhua_microflow_create_body(...)                          出 create/checkSchema body
6. xiaozhua_microflow_publish(host, cookie, mid, ...)           发布（🔑 需凭据）
```

**第 4 步不能跳。** 闸门不过就别往下走 —— 平台 checkSchema 是浅校验，
只在构建期才会暴露的问题（一致性检测）代价高得多。

### 典型链路：建一套设置

```
xiaozhua_option_set_category_body  → 分组
xiaozhua_option_set_body           → 选项集（category_id 用上一步的 id）
xiaozhua_option_set_item_body      → 枚举项（enum_id 用上一步的 id）
```

### 凭据怎么传

🔑 标记的 4 个工具（`microflow_publish` / `expression_verify` / `expression_filter` /
`entity_rule_publish`）**强制要求 `host` + `cookie` 两个必填参数**，不传就调不起来。

```python
xiaozhua_microflow_publish(
    host="https://<环境域名>",
    cookie="SY_ACCESS_TOKEN=...; SY_UID=...",
    mid="<微流程 id>",
    app_id="<应用 id>",
    data_schema={...},
)
```

这是「MCP 面默认只读」红线的实现方式：写动作必须由宿主显式授权，
不可能被误触发。`tests/test_mcp_server.py::test_write_not_exposed` 守着这条 ——
它断言凡是写类工具，`required` 必须包含 `host` 和 `cookie`。

**其余 40 个工具都是纯函数**，不联网、不需要凭据，只把参数拼成平台认的 body / 节点 / 表达式。

## 六、边界（别踩）

```
① 全部工具只出 data，不落库。
   落库由宿主拿 body 自己去 POST —— 这是刻意的：agent 不该有隐式写能力。

② 实体/结构不能手拼。
   xiaozhua_microflow_node 的 app/structure 必须来自
   udcMicroflowSearchTreeEntityPost 的真实返回，nodes.retrieve() 会校验。

③ 自定义页新建目录后必须重启 dev server。
   syf dev-udc-custom 启动时一次性 glob 扫描 src/pages/**/customPage.tsx，
   之后建的目录永远不识别（表现是页面显示 hello world）。

④ 设置域所有 udc*Post 都要 appGuid，而 appGuid ≠ appId。
   取法：udcApplicationDetailGet(path:{id: appId}).data.content.guid
   缺了报 BOOT_1001 或静默落 app_guid=-1（枚举项表现为 DB 有、页面「暂无数据」）。

⑤ 菜单（menu 域）不提供工具。
   只推进了「建菜单节点」，页面上的控件组件不会用，搭不了完整页面。
   capability_index("menu") 的 note 写着这条。

⑥ BOOT_0000 不代表业务成功。
   checkSchema 返回 BOOT_0000 也可能 check=False，且校验失败不阻塞 create
   （库里会多一条空条件规则）。判据一律是 content.check==true 且 errors==0。
```

## 七、改了工具面怎么同步

```bash
python tools/gen_mcp_manifest.py          # 重新生成 TOOLS.md
python tools/gen_mcp_manifest.py --check  # 校验（CI / 测试用，不一致退出码 1）
```

`tests/test_mcp_manifest_current.py` 会拦住「改了工具没重跑生成器」的情况。
`adapters/*/MCP-TOOL-MANIFEST.md` 是历史记录，已加指针指向 TOOLS.md，**不要再手工改它们**。
