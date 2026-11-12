# 30 秒装好

## 这是什么

致远 UDC 平台的**操作能力包**。给你 54 个 MCP 工具，用来在致远低代码平台上
建应用对象、建枚举、建实体字段、配事件、配参照、建微流程等。

它不是 SDK，不需要写代码调用。装好之后，你在 Hermes / Codex / Claude Code 里
直接说话，AI 用这些工具去操作平台。

## 环境要求

- Python **3.12 或更高**（`python --version` 确认）
- 网络能访问你的致远环境（例如 `lowcode-test2.<你的域名>`）

## 三步

```bash
# 1. 解压
unzip xiaozhua-agent-0.1.0.zip
cd xiaozhua-agent-0.1.0

# 2. 装依赖（只有两个包）
pip install "pyyaml>=6.0" "websocket-client>=1.6"

# 3. 装到你的 AI 宿主（三选一或全装）
python installer/install.py --host hermes      --target ~/xiaozhua-pkg --write
python installer/install.py --host codex       --target ~/xiaozhua-pkg --write
python installer/install.py --host claude-code --target ~/xiaozhua-pkg --write
```

`--host all` 一次装三个。

装完会生成这个结构：

```
xiaozhua-pkg/
  hermes/
    mcp_servers.yaml                  ← 贴进 Hermes 配置
    skills/xiaozhua-agent-hermes/SKILL.md
  codex/
    config.toml                       ← 贴进 Codex 配置
    AGENTS.md
  claude-code/
    .mcp.json                         ← 贴进 Claude Code 配置
    CLAUDE.md
  MANIFEST.json                       装了什么、装到哪、校验和
```

里面的 python 路径和 server.py 路径都是**按你机器的实际位置自动生成的**，
直接复制粘贴就能用。

## 必须看到这个才算装好

```bash
python -c "
import sys, json; sys.path.insert(0, '.')
from adapters.mcp.server import TOOL_KEYS
print('工具数:', len(TOOL_KEYS))
"
```

**必须输出 `工具数: 54`**。不是 54 就是没装对，别往下走。

再验一次 MCP 真的能起（把两行 JSON 喂给它）：

```bash
printf '%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | python adapters/mcp/server.py
```

看到两行 JSON 返回、第二行里有 54 个 `"name"` 就对了。

## 工具怎么用分两种

### 第一种：只出 body，你自己发（33 个）

像 `enum_body` / `dto_body` / `refer_config_body` 这些，调用只返回一个 JSON body。
要不要真的提交、提交到哪，你自己决定。

```python
from xiaozhua_host_bootstrap import bootstrap
b = bootstrap()
body = b["enum_body"](app_id, "枚举名", "enumCode")
print(body)   # → 一个可以直接 POST 的 JSON
```

### 第二种：自己发请求（4 个）

`microflow_publish` / `entity_rule_publish` / `expression_verify` / `expression_filter`。
需要连上你浏览器里**已经登录**的页面，cookie 不会离开浏览器进程。

```python
# 先用调试端口起浏览器（Excel 之外都行）：
# chrome.exe --remote-debugging-port=9333
b["expression_verify"](tokens, context, cdp_port=9333)
```

**不需要把 cookie 复制到任何地方**。工具让页面自己发 `fetch(credentials:'include')`。

## 哪些工具能信

**不要凭本文判断，看权威清单**：`README.md` 第 2 节的工具表由
`docs/delivery/tool-status.json` 生成，每个工具都标了「只读/写/删」「是否需授权」
「已验证/未验证/已知不通」，并写明阻塞原因。

当前汇总：

```
54 个工具 = 平台侧 42 + 本地 12

✅ 已验证      33   （平台侧 21 个在 test2 跑过完整闭环，本地 12 个装上即可用）
◐  部分验证     2   app_dependency_remove（REST 批删验过，GraphQL 单删未验）
                    expression_verify（传输通了，token 结构未定）
⚠  未验证      16   能出 body，不知道平台收不收
🔒 需授权       1   app_deploy_body（会触发真实构建，覆盖沙箱态）
❌ 已知不通     2   excel_template_body / excel_template_column
```

### 两个已知不通的

- `excel_template_body` / `excel_template_column`：test2 上
  `/service/udc/excel/template/create` 返回 Spring 404，
  `/udc/excel/template/create` 返回 OSS MethodNotAllowed。
  **不是工具写错，是链路缺失。** 换个环境可能就通了，用之前先探一次。

### 七个微流程工具要特别小心

`microflow_*` 七个全部**未验证**。后端 `checkSchema` 通过**不等于**前端能过 ——
必须在页面点「检查」，并逐个节点打开抽屉看有没有红字。前端绑定错只有前端认得出。

## ⚠ 会真删数据的工具

`app_dependency_remove` 调一次就真删。返回 `content: 1` 表示**删成功**，不是"接口通了"。

**只能删你自己刚 create 出来的行。** 拿列表里现成的行去试 = 事故
（本轮就发生过一次，见 `docs/audit/INCIDENT-20261112-deleted-builtin-dependency.md`）。

`enableDelete` 是准确的：`true` = 界面绿色「移除」可点，`false` = 灰色禁删。
但它只说「平台允许」，不说「你该拿它试接口」。

## 出问题看这里

| 现象 | 原因 | 解决 |
|---|---|---|
| `ModuleNotFoundError: No module named 'yaml'` | 没装 pyyaml | `pip install "pyyaml>=6.0"` |
| `ModuleNotFoundError: No module named 'websocket'` | 没装 websocket-client | `pip install "websocket-client>=1.6"` |
| 工具列表是空的 / internal error | python 版本太低 | `python --version` 要 ≥ 3.12 |
| `PageUnavailable: 调试端口 9333 不可达` | 浏览器没开调试端口 | 用 `--remote-debugging-port=9333` 重启浏览器 |
| `PageUnavailable: 没找到含 'lowcode-test2' 的页面` | 端口上的浏览器没打开你的环境 | 在那个浏览器里登录并打开平台首页 |
| 工具调用回 `BOOT_3000 message:null` | 参数形态不对，平台没给线索 | 对照 `docs/operation-contracts/` 下的契约 |

## 自己看细节

- `README.md` —— 九域能力表、安全边界、实测进度
- `docs/operation-contracts/` —— 99 份接口契约，每个接口的入参、错误码、坑
- `core/facts/` —— 225 份事实格，反编译 + 实测得出
- `docs/audit/mcp-setting-tools-live-batch1.md`、`mcp-tools-live-batch2.md`
  —— 哪些工具真跑过、跑出什么结果
