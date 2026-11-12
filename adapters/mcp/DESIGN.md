# DESIGN｜adapters/mcp/server.py —— 五能力 MCP 工具（S1 设计件）

> 设计先行（ROUTE §S1）。**本件只出设计，不写 `server.py`**（S2）。
> 边界：只写 `adapters/mcp/**` + `tests/test_mcp_server.py`（+`STATUS.md`）；禁改
> `components/` `core/` `docs/capability/`；凭据 0 入件（只写路径引用/环境变量机制）。
> 目标仓库：`<XIAOZHUA_AGENT_ROOT>`。完成定义：server 可起 + 测试绿 + STATUS。

---

## 0. 设计依据实测（本机，可复核）

以下事实为 S1 决策的可验证依据，全部本机实测（非转述）：

| 事实 | 实测值 | 证据 |
|---|---|---|
| 官方 MCP Python SDK 离线可 import？ | **否** | venv(3.12.14) 与 global(3.11.9) 均 `ModuleNotFoundError: No module named 'mcp'` |
| 依赖 `pydantic`/`httpx`/`anyio` 离线可用？ | **否** | 同上三模块均 `ModuleNotFoundError` |
| `pyproject.toml` 依赖 | `dependencies = ["pyyaml>=6.0"]` | pyproject 实测 |
| `jsonrpc` 第三方包 | 未安装 | `ModuleNotFoundError` |
| Python 版本（venv） | 3.12.14 | `python --version` |

**结论前置**：官方 `mcp` SDK 无法离线 import（引入它 = 新增 4 个传递依赖 + 需联网安装，
违反「默认离线」与「只写 adapters/mcp/**」边界）。故**协议选型 = 手写最小 jsonrpc 2.0 over
stdio**，零外部依赖、纯标准库（`json`/`sys`/`inspect`/`dataclasses`），可离线 pytest 全绿。

---

## 1. 协议选型（实测依据 + 结论 + 理由）

**选项**
- **A. 官方 `mcp` Python SDK**：`mcp.server.stdio` + FastMCP。
- **B. 手写最小 jsonrpc 2.0 over stdio**：本设计选 B。

**决策 = B（手写最小实现）**，理由（全部由 §0 实测支撑）：
1. **离线硬约束**：A 需 `mcp`/`pydantic`/`anyio` 依赖且需联网安装；本机实测 A 不可用。
   仓库 pyproject 仅 `pyyaml`，加 4 个传递依赖超边界（只许写 `adapters/mcp/**`，不得改
   pyproject / 不得装包）。
2. **MCP stdio 传输即行分隔 JSON-RPC 2.0**：宿主（Hermes/Claude Code/Codex）只认
   `initialize`/`tools/list`/`tools/call` 三个 method + 结果/错误信封。本仓五能力全是
   本地函数调用，无流式、无双向订阅、无 resources/prompts，最小协议面足够。
3. **可测试性**：纯 stdlib 状态机，pytest 可直接喂 stdin/收 stdout 字节流断言（见 §4 矩阵），
   不依赖 SDK 的 async event-loop，离线确定性可复现。

**代价与兜底（如实登记，非静默）**：手写仅实现 3 method，不兼容 SDK 的
`resources`/`prompts`/`logging` 扩展；若未来宿主声明扩展，需扩展 S2。**本切片按
TASK-GOAL「jsonrpc 2.0,官方 python-sdk 或手写最小实现」口径，选手写即达标。**

### 1.1 最小协议面（S2 实现边界，先定契约）
- **传输**：stdio。每行一个 JSON-RPC 2.0 帧（`\n` 分隔，UTF-8）。
- **method 白名单**：`initialize`、`tools/list`、`tools/call`（+ `notifications/initialized` 静默 ack）。
- **版本**：`protocolVersion` 回 `2024-11-05`（SDK 兼容常量，自描述非依赖）。
- **错误信封**：未知 method → `code -32601`；参数缺/型错 → `code -32602`；
  业务返回走 `result`（`isError` 语义见 §3 错误路径）。

---

## 2. 五工具 schema 自动生成（源：`core/tools/udc/*.md` + `deployment.py` 签名）

**五工具 = 三宿主 MCP-TOOL-MANIFEST 已声明的占位集**（`adapters/*/MCP-TOOL-MANIFEST.md`），
承接 `bootstrap()` dict 的 5 键（行号据 manifest 实测）：

| MCP tool | bootstrap 键(行) | 入参（Python 签名） | 返回 | 只读 | 凭据模式 |
|---|---|---|---|---|---|
| `xiaozhua_dispatch` | `dispatch`(L133) | `intent:str, target?:str` | dict 路由+证据(含 `status`) | 只读 | path-ref-only |
| `xiaozhua_generate` | `generate`(L46) | `application_id, entity_name, attributes?:list, caption?:str` | dict backend+frontend(`status`/`plan_blocked`) | 只读出数据 | path-ref-only |
| `xiaozhua_generate_from_requirement` | `generate_from_requirement`(L71) | `text:str, application_id` | dict `parsed`+backend+frontend | 只读出数据 | path-ref-only |
| `xiaozhua_live_probe` | `live_probe`(L95) | `cred_file?`（缺省用 bootstrap `credential_file`） | dict 4 端点结果 | 只读;**活体需 `allow_network=True`** | path-ref-only |
| `xiaozhua_deploy_plan` | `deploy_plan`(L119) | `application_id, entity_name, attributes, caption?, stereotype="bill", deploy_type="RELEASE"` | dict 4 步方案 data(`readonly_plan=True`) | 只读出方案;宿主执行写 | path-ref-only |

### 2.1 自动生成的两条源
- **入参结构（JSON Schema 的 `type`/`required`/默认值）**：由 `inspect.signature()` 从
  `deployment.py::build_deployment_plan`（deploy_plan 工具直接源）与 bootstrap 闭包签名
  （其余 4 工具）反射生成；`stereotype`/`deploy_type` 默认值 `"bill"`/`"RELEASE"` 取签名默认。
- **枚举约束（`enum` 字段）与 `attributes` 元素 schema**：自动抽取 `deployment.py` 常量
  （非臆造，源 = `components/platform_operations/deployment.py` 实测常量）：
  - `stereotype` → `enum: STEREO_TYPES`（archive/standard/bill/archiveTree，L30）
  - `deploy_type` → `enum: DEPLOY_TYPES`（TEST/RELEASE/ON_ONLINE/DELTA，L37）
  - `attributes[]` 元素 → `{name:str, caption?:str, dataType?:str}`；`dataType` →
    `enum: DATATYPES`（11 值，L33），缺省由 `infer_datatype` 按名保守推断并进 `unknowns`
    （L81）——schema 标注 `dataType` 为可选，缺省语义在描述里写明「未命中进 unknowns」。
  - `project_type`/`terminal_type`（`build_deployment_plan` 形参，L119-120，bootstrap 未透传）
    → 映射 `PROJECT_TYPES`/`TERMINAL_TYPES`；**本切片按 TASK-GOAL 五能力面，deploy_plan
    工具入参以 bootstrap `deploy_plan` 签名为准（不透传 project/terminal），如需全参在
    S2 标 UNVERIFIED 扩展点，不在本设计虚写为已支持。**
- **`core/tools/udc/*.md` 的角色**：4 步 deploy 子契约（entity.create/attribute.create/
  page.create/deploy.normal）= `xiaozhua_deploy_plan` 返回的 `steps[].op` 的语义说明源。
  S2 自动生成时把这 4 个 op 的 `method`/`path`/`body` 锚写进 `xiaozhua_deploy_plan` 的
  工具描述（`description` 字段），使宿主 LLM 知道 4 步写链。**registry-gap 纪律照搬**：
  `udc.page.create` 在 registry 无 op-id（`UNVERIFIED/registry-gap`，page.create.md §registry），
  工具描述只标「链级 OBSERVED_LIVE / registry 未登记」，不编造 registry 条目。

### 2.2 生成的落点（S2）
- `adapters/mcp/server.py` 内一个 `build_tool_schemas() -> list[dict]` 纯函数：
  `inspect` 签名 + `deployment.py` 常量 → 5 个 MCP `Tool`（`name`/`description`/`inputSchema`）。
  该函数无副作用、可被 pytest 直接 import 断言（§4）。**S1 只定契约，S2 才落码。**

---

## 3. 离线默认传导（`allow_network=False` 全链路）

**默认值源**：`bootstrap(allow_network: bool = False)`（xiaozhua_host_bootstrap.py L25）——
离线是函数签名默认，非调用方记忆。

**传导路径（逐跳，每跳可断言）**：
1. **MCP 进程侧**：`xiaozhua_live_probe`（及其它工具）调用前，server 持有
   `self._allow_network`。默认 = 读环境变量 `XIAOZHUA_ALLOW_NETWORK`（未设 = `False`）。
   **不写任何凭据值入件**：凭据走 `XIAOZHUA_CRED_FILE`（路径载体，manifest 口径），仅存路径。
2. **bootstrap 侧**：`bootstrap(credential_file=<path>, allow_network=self._allow_network,
   audit_dir=...)` —— server 把自身 flag 原样传入；不传则落回签名默认 `False`。
3. **live_probe 侧**（xiaozhua_host_bootstrap.py L99-100 实测）：
   - `credential_file` 缺省且无 `cred_file` 入参 → 返回 `{"status":"SKIPPED","reason":"no credential file provided"}`（不联网）。
   - `allow_network=False`（默认）→ 返回 `{"status":"BLOCKED","reason":"allow_network=False (default offline)"}`（**不联网**，不触达 GatewayReadonlyClient）。
   - `allow_network=True` + 有 cred 路径 → 才 `GatewayReadonlyClient(allow_network=True)` 真发 4 端点。
4. **其它 4 工具天然离线**：`dispatch/generate/generate_from_requirement/deploy_plan`
   全是本地计算/读本地 audit 目录（`audit_dir`），不触网；`allow_network` 对其无影响。

**验收不变量**：默认启动下跑全 5 工具 = 0 网络调用；`live_probe` 默认路径必须返回
`BLOCKED`（非 `PASS`）——「任何离线输出不能被解读为 LIVE PASS」（README 测试纪律）。

**活体显式开**：宿主显式 `XIAOZHUA_ALLOW_NETWORK=1`（或未来 S2 的 `live_probe` 参数
`allow_network` 透传）才放行；开启后仍 path-ref-only，凭据值 0 入件。

---

## 4. pytest 覆盖矩阵（`tests/test_mcp_server.py`，三层：工具列表/离线调用/错误路径）

> 全部离线确定性；`live` 层（真联网）留 `@pytest.mark.live` 默认不跑（README 纪律）。
> 载体：import `server.py` 的纯函数/状态机 + 喂 JSON-RPC 帧断言（不依赖真实宿主）。

### 4.1 工具列表层（`tools/list`）
| 用例 | 断言 |
|---|---|
| `list_all_tools` | `build_tool_schemas()` 恰 5 个；`name` 集 = §2 表 5 名 |
| `schema_from_signatures` | 每 tool `inputSchema` 含对应 `required`（deploy_plan:`application_id`/`entity_name`/`attributes`；dispatch:`intent`） |
| `enum_constraints` | deploy_plan `stereotype`/`deploy_type` enum 集 == `deployment.py` `STEREO_TYPES`/`DEPLOY_TYPES`（实测常量，非手抄） |
| `unknown_tool` | `tools/call` 传未知 name → JSON-RPC `-32602`（或 result `isError`)，不抛裸异常 |

### 4.2 离线调用层（默认 `allow_network=False`，全 5 工具）
| 用例 | 断言 | 依据 |
|---|---|---|
| `call_dispatch_offline` | `dispatch("unknown_component_x")` → 结果含 `status`=`UNAVAILABLE`（registry 无该组件，非崩溃） | manifest dispatch 行 |
| `call_deploy_plan_offline` | 传合法 `attributes` → 返回 `readonly_plan=True` + `steps` 恰 4（op 顺序 = entity.create→attribute.create→page.create→deploy.normal） | deployment.py L144-185 |
| `call_deploy_plan_datatype_infer` | `attributes=[{name:"acceptance_date"}]` → step2 body `dataType="DATE"` 且进 `unknowns`（按名推断未证实） | infer_datatype L81/L98 |
| `call_live_probe_offline_blocked` | 无 cred/`allow_network=False` → `status="BLOCKED"`（reason 含 `allow_network=False`）；**断言 0 网络** | bootstrap L99-100 |
| `call_generate_offline` | 传 entity+attributes → 返回含 `backend`/`frontend`/`status`；方法体声明 `UNVERIFIED`（不虚写 PASS） | generate L46/L48 |

### 4.3 错误路径层（写门/缺参/异常信封）
| 用例 | 断言 |
|---|---|
| `missing_required_param` | `tools/call` 缺必填 → JSON-RPC `-32602`，`message` 指出字段名 |
| `write_not_exposed` | 全 5 工具**无写工具暴露**：schema 里 0 个写 method；`deploy_plan` 只出 `readonly_plan` data，宿主执行（A8 §二 写门口径） |
| `bad_json_frame` | 非 JSON 帧 → 返回 JSON-RPC `-32700` parse error，进程不崩 |
| `unknown_method` | `tools/foo` → `-32601` |
| `live_probe_network_guard` | 断言默认路径**未** import `GatewayReadonlyClient`（`allow_network=False` 短路在 L100，不触 L101 import）——离线纪律硬断言 |

### 4.4 分层 marker（沿用 pyproject 已定义 marker）
- `@pytest.mark.offline`：§4.2/§4.3 全部（默认可重复、不联网）。
- `@pytest.mark.live`（默认不跑）：`call_live_probe_network_guard` 的反向真联网版（需真实外部，标注即可，本切片不实装）。
- 通过数增量：本切片**新增** `test_mcp_server.py`（用例数见 S2 实测），不改既有 375/376 基线语义（只加，不动）；收口在 STATUS 记实测总数。

---

## 5. 实现边界与 UNVERIFIED 登记（S2 触发点，先定不虚写）

| 项 | 本切片（S1 设计） | 状态 |
|---|---|---|
| 协议选型 | 定：手写 jsonrpc 2.0 stdio | ✅ 依据 §0 实测 |
| 5 工具 schema 自动生成 | 定契约（`build_tool_schemas()` 纯函数 + 反射 + 常量 enum） | 契约定，码 S2 |
| 离线默认传导 | 定路径（`XIAOZHUA_ALLOW_NETWORK` → bootstrap → live_probe BLOCKED） | 路径定，码 S2 |
| pytest 三层矩阵 | 定用例表 | 表定，码 S2 |
| `live_probe` 真联网路径 | 不实现（默认 BLOCKED 已满足「server 可起+测试绿」） | **UNVERIFIED**（活体需显式开，本切片不连网） |
| deploy_plan 全参（project/terminal_type） | 以 bootstrap `deploy_plan` 签名为准，不透传全参 | **扩展点 UNVERIFIED**（需要时 S2 加，不在本设计虚写） |
| MCP `resources`/`prompts` 扩展 | 不实现（最小 3 method） | **UNVERIFIED**（宿主扩展才需） |
| 凭据 | 仅 `XIAOZHUA_CRED_FILE` 路径载体，值 0 入件 | 纪律 |

---

## 6. 完成定义（对齐 TASK-GOAL / STATUS）
- **server 可起**：`python -m adapters.mcp.server` 起 stdio 循环，`tools/list` 回 5 工具。
- **测试绿**：`python -m pytest tests/test_mcp_server.py -m offline -q` 全绿（离线确定性）。
- **STATUS**：记录实测通过数、HEAD、边界（只写 `adapters/mcp/**` + `tests/` + `STATUS.md`）、
  凭据 0 入件声明、UNVERIFIED 项登记（§5）。
