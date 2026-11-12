# Seeyon Agent

致远 UDC / SPI 平台的操作能力包（MCP）。给 Hermes、Codex、Claude Code 这类宿主用，
让 AI 以用户身份经平台接口真实操作 —— 建实体、配枚举、发规则、出报文。

**54 个 MCP 工具**，其中 **21 个**在真实环境跑过完整闭环（create → 回读 → delete），
12 个本地工具装上即可用，其余逐项标注状态与阻塞原因（见第 2 节生成的清单）。

---

## 装法（三选一）

### A. pip 装成命令（推荐）

```bash
pip install "git+https://github.com/mingtaobai79-cloud/seeyon-agent.git"
pip install "pyyaml>=6.0" "websocket-client>=1.6"
```

宿主配置只需一行：

```json
{"mcpServers": {"seeyon": {"command": "seeyon-mcp"}}}
```

### B. git clone + installer

```bash
git clone https://github.com/mingtaobai79-cloud/seeyon-agent.git && cd seeyon-agent
pip install "pyyaml>=6.0" "websocket-client>=1.6"
python installer/install.py --host hermes      --target ~/seeyon-pkg --write
python installer/install.py --host codex       --target ~/seeyon-pkg --write
python installer/install.py --host claude-code --target ~/seeyon-pkg --write
```

`--host` 可选 `hermes` / `codex` / `claude-code` / `all`。生成的配置写的是你机器上的真实绝对路径，直接贴进宿主配置。

### C. 解压 zip

见 `INSTALL.md`。

### 装完自检

```bash
printf '%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | seeyon-mcp
```

输出两行 JSON，第二个里有 **54** 个 `"name"` = 连上了。

---

## 1. 装好之后怎么连

包是 **MCP over stdio**（JSON-RPC 2.0，一行一帧）。宿主配置由
`python installer/install.py --host all --target <目录> --write` 自动生成，
里面的 python 路径和 `server.py` 路径都按你机器实际位置算好，直接粘贴。

### Hermes

`installer` 生成的 `hermes/mcp_servers.yaml`，贴进 `~/.hermes/config.yaml` 顶层：

```yaml
mcp_servers:
  seeyon:
    command: <你的 python>
    args:
      - <你的安装路径>/adapters/mcp/server.py
    timeout: 180
```

### Codex

`codex/config.toml` → 追加到 `~/.codex/config.toml`：

```toml
[mcp_servers.seeyon]
command = "<你的 python>"
args = ["<你的安装路径>/adapters/mcp/server.py"]
```

### Claude Code

`claude-code/.mcp.json` → 合并进项目或用户级 `.mcp.json`：

```json
{
  "mcpServers": {
    "seeyon": {
      "command": "<你的 python>",
      "args": ["<你的安装路径>/adapters/mcp/server.py"]
    }
  }
}
```

### 连上没连上，验这一条

```bash
printf '%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | python adapters/mcp/server.py
```

两行 JSON，第二行里有 **54** 个 `"name"` = 连上了。
少于 54 或直接报错，先查 `INSTALL.md` 的故障表。

---

## 2. 工具清单（状态透明，逐项标注）

<!-- BEGIN GENERATED:TOOL-TABLE -->

> 本表由 `tools/core/delivery/gen_tool_table.py` 从 `docs/delivery/tool-status.json` 生成，**不要手改**。

合计 **54** 个工具：平台侧 42 个（其中 **21** 个真机验证过），本地工具 12 个。

| 状态 | 数量 |
|---|---:|
| ✅ 已验证 | 33 |
| ◐ 部分验证 | 2 |
| ⚠ 未验证 | 16 |
| 🔒 需授权 | 1 |
| ❌ 已知不通 | 2 |

### 平台工具

| 工具 | 类型 | 需授权 | 状态 | 说明 / 阻塞原因 |
|---|---|:---:|---|---|
| `live_probe` | 只读 | — | ⚠ 未验证 | 需凭据文件，未取得授权 |
| `enum_category_body` | 写 | — | ✅ 已验证 | udcEnumCategoryPost；已建/查/删闭环 |
| `enum_body` | 写 | — | ✅ 已验证 | udcEnumPost；已建/查/删闭环 |
| `enum_item_body` | 写 | — | ✅ 已验证 | udcEnumItemPost；随 enum 删除 |
| `option_set_category_body` | 写 | — | ✅ 已验证 | udcUdcEnumCategoryPost；已建/查/删闭环 |
| `option_set_body` | 写 | — | ⚠ 未验证 | 同域 option_set_category_body 已验，但 body 与项未真机跑 |
| `option_set_item_body` | 写 | — | ⚠ 未验证 | 需先建 option_set_body 才能验 |
| `attribute_set_body` | 写 | — | ✅ 已验证 | REST /udc/attributeSet；已建/删闭环 |
| `attribute_set_field_body` | 写 | — | ✅ 已验证 | udcEntityAttributePost；随字段集删除 |
| `parameter_body` | 写 | — | ✅ 已验证 | udcCtpParameterDefinitonPost；已建/删闭环 |
| `qrcode_body` | 写 | — | ✅ 已验证 | REST /udc/qrcode-rule/create；已建/删闭环 |
| `scalability_option_body` | 写 | — | ✅ 已验证 | REST /udc/scalability-option；已建/删闭环 |
| `scalability_field_body` | 写 | — | ✅ 已验证 | udcScalabilityPost；dataTypeProperties 必须非空，缺省已填 {} |
| `serial_scheme_body` | 写 | — | ✅ 已验证 | udcSerialSchemeCreatePost；已建/查/删闭环 |
| `serial_section` | 写 | — | ✅ 已验证 | 流水号段；CONSTANT + SERIAL 各一，totalSize 为各段之和 |
| `event_body` | 写 | — | ✅ 已验证 | udcEventPost；eventDataType=0 对此接口正确；已建/删闭环 |
| `event_data_body` | 写 | — | ✅ 已验证 | udcEventCreateWithDataPost；eventDataList 必须是数组；attributes 的 caption 必填 |
| `dto_body` | 写 | — | ✅ 已验证 | udcDataTransferObjectPost；属性字段名是 notNull；已建/删闭环 |
| `index_body` | 写 | — | ✅ 已验证 | udcIndexPost；fieldIds 是逗号分隔字符串；已建/删闭环 |
| `refer_config_body` | 写 | — | ✅ 已验证 | udcReferConfigCreateConfigInfoPost；删除用 deleteByGroupId；已建/删闭环 |
| `entity_rule_body` | 写 | — | ✅ 已验证 | 实体规则 body；已建/删闭环 |
| `app_version_list` | 只读 | — | ✅ 已验证 | REST search-app-edition；IN_appId 必须传 appName，传数字 appId 静默返回空数组 |
| `app_build_info` | 只读 | — | ✅ 已验证 | udcSandboxBuildInfoAppGet；参数类型必须是 Map，InputBody 系类型不存在 |
| `app_dependency_body` | 写 | — | ✅ 已验证 | udcApplicationDependentApplicationCreateBatchPost；params0 是数组；44→45→44 已闭环 |
| `app_dependency_remove` | 删 | 是 | ◐ 部分验证 | ⚠ 会真删数据，content=1 即删除成功；只能删自己刚造的行；GraphQL DeleteByIdPost 未跑（只用 REST 批删验过） |
| `app_deploy_body` | 写 | 是 | 🔒 需授权 | 会触发真实构建并覆盖沙箱态，需用户授权才跑 |
| `excel_template_body` | 写 | — | ❌ 已知不通 | /service/udc/excel/template/create 返回 Spring 404；/udc/excel/template/create 返回 OSS MethodNotAllowed |
| `excel_template_column` | 写 | — | ❌ 已知不通 | 同上，链路缺失 |
| `microflow_create_body` | 写 | — | ⚠ 未验证 | 需 UI 点「检查」+ 逐节点看红字，成本高 |
| `microflow_node` | 写 | — | ⚠ 未验证 | 同上 |
| `microflow_gates` | 写 | — | ⚠ 未验证 | 同上 |
| `microflow_capability` | 写 | — | ⚠ 未验证 | 同上 |
| `microflow_trigger` | 写 | — | ⚠ 未验证 | 同上 |
| `microflow_data_schema` | 写 | — | ⚠ 未验证 | 同上 |
| `microflow_publish` | 写 | 是 | ⚠ 未验证 | 发布是不可逆动作，且需 UI 侧检查配合 |
| `list_page_schema` | 写 | — | ⚠ 未验证 | 宿主需填真实 id 后 submitPage，未闭环 |
| `detail_page_schema` | 写 | — | ⚠ 未验证 | 同上 |
| `custom_page_scaffold` | 写 | — | ⚠ 未验证 | 同上 |
| `filter_plan_body` | 写 | — | ⚠ 未验证 | 未闭环 |
| `expression_verify` | 写 | 是 | ◐ 部分验证 | 传 CONSTANT token 报 FORMULA_6003 不支持的返回值类型: null，token 结构待查 |
| `expression_filter` | 写 | 是 | ⚠ 未验证 | 依赖 expression_verify 的 token 结构 |
| `entity_rule_publish` | 写 | 是 | ⚠ 未验证 | 发布不可逆，未授权 |

### 本地工具（不连平台，装上即可用）

| 工具 | 类型 | 需授权 | 状态 | 说明 |
|---|---|:---:|---|---|
| `dispatch` | 本地 | — | ✅ 已验证 | 按意图路由到域；不连平台 |
| `generate` | 本地 | — | ✅ 已验证 | 需求→Java 骨架，声明级，方法体 UNVERIFIED |
| `generate_from_requirement` | 本地 | — | ✅ 已验证 | 自然语言→实体模型→骨架 |
| `capability_index` | 本地 | — | ✅ 已验证 | 九域能力索引与实测状态 |
| `repo_state` | 本地 | — | ✅ 已验证 | 本地仓库状态 |
| `repo_sync` | 本地 | 是 | ✅ 已验证 | 写 git；必须 confirm=True，无默认值 |
| `repo_url` | 本地 | — | ✅ 已验证 | 仓库地址 |
| `code_targets` | 本地 | — | ✅ 已验证 | 代码落点 |
| `project_shape` | 本地 | — | ✅ 已验证 | 工程形态 |
| `spi_catalog` | 本地 | — | ✅ 已验证 | SPI 目录 |
| `expression_catalog` | 本地 | — | ✅ 已验证 | 表达式函数目录（本地字典） |
| `deploy_plan` | 本地 | — | ✅ 已验证 | 生成部署方案 body（readonly_plan=True），不提交 |

<!-- END GENERATED:TOOL-TABLE -->

> 上表由 `tools/core/delivery/gen_tool_table.py` 从 `docs/delivery/tool-status.json`
> 生成。改状态改 JSON，不要手改表格（手抄一定会漂）。

---

## 3. ⚠ 会改环境 / 会删数据的工具

**这些工具调一次就动真数据，不是干跑。** 用之前必须读懂本节。

| 工具 | 后果 | 前置条件 |
|---|---|---|
| `app_dependency_remove` | **真删依赖行**。`content: 1` = 删成功，不是"接口通了" | 只能删**你自己刚 create 出来的**行。绝不能拿列表里现成的行去试 |
| `app_deploy_body` | 触发真实构建 + 部署，**覆盖沙箱态** | 需用户明确授权；别当读接口重放 |
| `microflow_publish` | 真发布微流程，**不可逆** | 需用户授权；发布前必须在页面点「检查」 |
| `entity_rule_publish` | 真发布实体规则，**不可逆** | 需用户授权 |
| `repo_sync` | 写本地 git | 必须显式 `confirm=True`，无默认值 |
| 全部 `*_body` 写类 | 生成 body 本身不落库；**提交后才写** | 提交前确认 appId 是目标环境 |

### `enableDelete` 是准确的安全信号

```
enableDelete: true   界面上「移除」是绿色可点  → 平台允许删
enableDelete: false  界面上「移除」是灰色禁删  → 删不掉
```

实测一致：`app-common` / `cip-capability` / `cip-manager` 三条 `true`（绿色），
其余 8 条 `false`（灰色）。**用这个字段判断可删性是可靠的。**

但它回答的是「**平台允许不允许**」，不是「**你该不该**」。

**硬约束**：验证删除类接口，先自己 create 一条，再删这一条，再看是否回到原行数。
别人的配置即使允许删，也不该拿来当试验品。
（本轮我违反过一次，见 `docs/audit/INCIDENT-20261112-deleted-builtin-dependency.md`）

---

## 4. 怎么调

**只出 body（不碰网络）** —— 大多数工具：

```python
import sys; sys.path.insert(0, ".")
from seeyon_host_bootstrap import bootstrap
b = bootstrap()

b["enum_category_body"](app_id=8704025620829192834, caption="分类", code="cat1")
b["serial_section"](size=6, section_type="SERIAL", fill_char="0")
```

**真发请求** —— 只有 4 个工具自己发：`microflow_publish` / `entity_rule_publish` /
`expression_verify` / `expression_filter`。两种凭据方式二选一：

```python
# 推荐：页面代发，cookie 不离开浏览器进程
b["expression_verify"](tokens=[...], context=[...], cdp_port=9333)

# 备选：显式 host + cookie（不推荐，cookie 会经过本地内存）
b["expression_verify"](tokens=[...], context=[...], host="...", cookie="...")
```

`cdp_port` 走 `PageFetch`，由页面自己 `fetch(url, {credentials:'include'})`。
cookie 永远不导出到本地、不在本地重放；不代填登录表单（单 token 平台重登会踢掉其他会话）。

### 页面选取

`PageFetch` 会按 host 匹配标签页，**并自动排除 `/login/`**。
同一浏览器里同时开着登录页和工作页时，旧版会挑中登录页 —— 请求打到登录页，
平台回 `Unknown type xxxInputBody`，看起来像类型名写错，其实压根没登录。
（这是本轮修掉的真 bug，见第 6 节。）

---

## 5. 自检

```python
import sys; sys.path.insert(0, ".")
from seeyon_host_bootstrap import bootstrap
from adapters.mcp.server import TOOL_KEYS
b = bootstrap()
idx = b["capability_index"]()
print(len(TOOL_KEYS), idx["domain_count"], len(b))   # 54 9 57
```

`54` = MCP 工具数，`9` = 域数，`57` = bootstrap 暴露的可调用项（含 3 个非 MCP 内部件）。

---

## 6. 已知问题（会咬人的，逐条列清）

### 6.1 `app_build_info` 的参数类型必须是 `Map`

```
$params0: udcSandboxBuildInfoAppGetInputBody  → GraphQL-3001 Unknown type
$params0: udcSandboxBuildInfoAppGetInput      → Unknown type
$params0: udcSandboxBuildInfoGetInputBody     → Unknown type
$params0: Map                                 → BOOT_0000 ✅
```

这个 operation 是 `path:` 入参，平台没给它生成 InputBody 类型。
**按名称猜 `InputBody` 在这里不成立。** 已修，代码里写死 `Map`。

### 6.2 `PageFetch` 曾会命中 `/login/` 标签页

同一浏览器里既有 `/login/` 又有工作页时，按「url 含 host」取第一个可能正好是登录页，
所有请求打到登录页，平台回 `Unknown type xxxInputBody` —— 会被误判成类型名写错。
已修：优先选非 `/login` 的页面。

### 6.3 `app_version_list` 的 `IN_appId` 必须传 appName

```
传数字 appId  → BOOT_0000，content: []      ← 不报错！
传 appName    → BOOT_0000，content 有真实版本行
```

**空数组不报错**，很容易被当成「这应用没有版本」。

### 6.4 `enableDelete` 判断可删性是准确的

`true` = 界面绿色「移除」可点，`false` = 灰色禁删。实测 11 条 SERVICE 依赖完全吻合。
它只说明「平台允许」，不说明「你该拿它试接口」。见第 3 节。

### 6.5 `scalability_field_body` 的 `dataTypeProperties` 不能是空串

```
dataTypeProperties = ""    → BOOT_3000, message=null   ← 什么都没说
dataTypeProperties = "{}"  → BOOT_0000 ✅
```

已修：缺省填 `{}`，显式传值原样保留。

### 6.6 `event_data_body` 的 `eventDataList` 必须是数组

```
传单对象   → BOOT_3002 属性 eventDataList 的值反序列化为 ArrayList 类型时失败
传 [对象]  → 通过
```

DTO 声明 `List<...>` 就是字面意思，GraphQL 层不负责包装。
另：`attributes[].caption` 必填，报错文案是「属性名称 不能为空」（说的不是 `name`）。

### 6.7 excel 模板链路在 test2 上不通

契约写 `LIVE PASS`，实测：

```
/service/udc/excel/template/create  → Spring 404
/udc/excel/template/create          → OSS MethodNotAllowed
```

`excel_template_body` / `excel_template_column` 标 **BROKEN**，不是工具写错，是链路缺失。

### 6.8 平台字段错名不报错

非空约束字段真名是 `notNull`，写成 `isNotNull` 会被**静默忽略**。
GraphQL 层不校验未知字段：传错字段名和传对，可能返回一模一样的业务错。
**猜字段名不可能收敛，只能读 DTO 或真实报文。**

---

## 7. 打包分发

```bash
git archive --format=zip --prefix=seeyon-agent-0.1.0/ \
  -o dist/seeyon-agent-0.1.0.zip HEAD -- . ':!docs/audit/artifacts'
```

`docs/audit/artifacts` 是反编译产物与前端 bundle（380MB），不进分发包；其余全在，约 8MB。

版本与变更摘要见 `CHANGELOG.md`；每次打包的 SHA256 一并公布，下载后可核对。

---

## 8. 本地运行

```bash
python -m pytest tests -q
python -m pytest tests -m "offline and acceptance" -q
```

测试分层：`offline` 默认可重复；`live` 需显式配置真实环境；`blocked` 记录被安全边界拒绝的路径；
`acceptance` 覆盖 CLI 验收边界。

**注意区分两层**：CLI 层是只读的（写操作返回 `DENIED`，规划只能 `dry-run`），
但 MCP 工具层有真写面（见第 3 节）。任何离线输出都不能被解读为 `LIVE PASS`。

Test collection: `3201 tests collected`。收集数量不等于通过数量。
真机验证记录在 `docs/audit/mcp-*-live-*.md`。

---

## 9. 文档入口

文档树根在 `docs/`，**从这里进**：`docs/README.md`。

- 交付相关 → `docs/delivery/`（工具状态 JSON、交付报告）
- 真机验证记录 → `docs/audit/mcp-*-live-*.md`
- 事故记录 → `docs/audit/INCIDENT-*.md`
- 接口契约 → `docs/operation-contracts/`
- 平台事实 → `core/facts/`

---

## 10. CLI 统一入口

所有命令离线读取本地证据/快照并输出单行 JSON；CLI 这层**不会连接真实环境**。

```bash
# 本地 Maven artifact inventory（只读扫描，不连接外部仓库）
python -m seeyon_cli artifact-inventory --root <maven-repo> --output inv.json

# UDC 证据报告 / 分域分析
python -m seeyon_cli udc-report --audit-dir <audit-dir> --target demo
python -m seeyon_cli udc-analyze --audit-dir <audit-dir> --target demo

# Runtime / Integration 本地快照报告（不是实时探测）
python -m seeyon_cli runtime-report --snapshot runtime.json --target udc
python -m seeyon_cli integration-report --snapshot integration.json --target invoice

# 汇总三类离线审计报告
python -m seeyon_cli audit-summary --audit-dir <audit-dir> --udc-json udc.json

# Probe Summary：分别输出 facts、unverified、blocked
python -m seeyon_cli probe-summary

# Evidence Ledger：合并 UDC、Runtime、HTTP 证据并检测冲突
python -m seeyon_cli evidence-ledger --udc-json udc.json --runtime runtime.json --http http.json

# 关键路径矩阵、影响图和客户边界
python -m seeyon_cli udc-path-matrix --udc-json udc.json --runtime runtime.json --http http.json
python -m seeyon_cli impact-graph --path-matrix matrix.json
python -m seeyon_cli extension-boundary --facts-json facts.json --source-dir <source>

# Dry-run：只生成计划，不执行写操作
python -m seeyon_cli dry-run --action create-entity --target demo --environment test2

# Platform Operation Layer 只读操作（默认离线 BLOCKED）
python -m seeyon_cli op-execute --operation udc.application.get --application-id <appId>

# 查看已注册组件能力
python -m seeyon_cli capabilities
```

CLI 层的写操作会明确拒绝并返回退出码 2 —— 写平台走 MCP 工具，不走 CLI：

```bash
python -m seeyon_cli udc-execute publish demo --audit-dir <audit-dir>
```

`Probe Summary` 和 `Evidence Ledger` 都是离线证据投影：它们保留 `UNVERIFIED`/`BLOCKED`，
不会把 HTTP 200、快照读取或静态目录计数升级为真实系统成功。

CLI 层的写操作会明确拒绝并返回退出码 2 —— 写平台走 MCP 工具，不走 CLI。

---

## 11. 安全边界

**不做**：建应用（用户裁决不需要构造器）、菜单搭建（半成品已停）、BI / 角色 / 列三域、
微流程画布渲染。

**受限**：`live_probe` 默认 `allow_network=False` 返回 BLOCKED；`app_dependency_body`
返回的是操作描述 `{op, body, ...}`，只有 `body` 是给平台的。

**硬规矩**：HTTP 200 或 `BOOT_0000` 不等于成功，必须按 id 回读。
平台有些字段错名不报错（见 6.8），只能对 DTO 才能发现。

UDC 是 Seeyon Agent 的组件，不是独立总 Agent；Context、Session、Tool 和 LLM 可由宿主注入。
