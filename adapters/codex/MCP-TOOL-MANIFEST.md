# adapters/codex/MCP-TOOL-MANIFEST.md｜MCP 工具清单（Codex 侧 · S3 · H-3；S7 实现态对齐）

---

> ⚠️ **本文件已滞后，不再是权威清单（2026-11-09）**
>
> 工具面从 5 → 14 → **44**，本文件停在 14 个。手工维护的清单必然漂移。
>
> **权威清单 = `docs/operation-contracts/mcp/TOOLS.md`**（由 `tools/gen_mcp_manifest.py`
> 从 `xiaozhua_host_bootstrap.bootstrap()` + `adapters/mcp/server.py` 直接生成，
> `tests/test_mcp_manifest_current.py` 守住一致性）。
>
> 本文件保留作历史记录：它记录了 2026-09 ~ 11-08 期间的工具声明演进。

---

> ## 【当前 2026-11-08 更正】工具面 5 → **14**，宿主注册也已落地
>
> 本文下半部分写的「五能力 5 tool」是 2026-09 时点的声明面。实际 `bootstrap()` 返回 **15 个能力**
> （5 个能力 + 9 个 metadata 构造器 + `agent` 对象），`server.py` 早期只接了 5 个 ——
> 9 个构造器在宿主侧**完全看不见**。现已全部接入：
>
> | 新增 tool | 承接 v1 键 | 入参要点 | 实测产出 |
|---|---|---|---|
| `xiaozhua_list_page_schema` | `list_page_schema` | app_id / entity_name / caption / attributes | 4,612 B（`pageType=SEARCH_LIST` + 列定义） |
| `xiaozhua_detail_page_schema` | `detail_page_schema` | 同上传参 | 2,966 B（`UdcForm SINGLE` + 子页） |
| `xiaozhua_filter_plan_body` | `filter_plan_body` | app_name / app_id / page_id / grid_suffix / driven_entity / caption / conditions | 1,150 B |
| `xiaozhua_microflow_create_body` | `microflow_create_body` | name / caption / app_id / data_schema(object) / trigger_type | 467 B（`dataSchema` 字符串化） |
| `xiaozhua_dto_body` | `dto_body` | app_id / caption / name / attributes | 402 B |
| `xiaozhua_enum_body` | `enum_body` | app_id / caption / name / order_no | 266 B |
| `xiaozhua_event_body` | `event_body` | app_id / caption / event_name / dto_id | 206 B |
| `xiaozhua_enum_item_body` | `enum_item_body` | app_id / enum_id / caption / item_value / enum_code / order_no | 197 B |
| `xiaozhua_index_body` | `index_body` | caption / entity_id / field_ids（integer 数组） | 57 B |

>
> **本文自称的两个「未实现」现在都已翻面**：
> - ~~宿主侧 MCP 注册/接入配置~~ → 已落地：`codex mcp add xiaozhua -- ...` → `codex mcp list` 显示 `xiaozhua / enabled`
> - 仍未实现：v2 宿主专属 tool schema、宿主注入 policy/context/session 三 Port
>
> 守它的测试：`tests/test_mcp_metadata_tools.py`（26 用例）+ `tests/test_mcp_server.py`（20 用例）。
> schema 由 `inspect.signature` 自动生成，只有两处 override（`data_schema` 吃 object、`field_ids` 吃 integer 数组）。


> **声明级清单**。把 v1 adapter `bootstrap()` 的 5 能力 + CLI op 面映射为 Codex 侧 MCP tool 声明，
> 并按层如实标注实现态。
> **传输层已在盘实装**（`adapters/mcp/server.py`，commit `3595d7e`，19 passed）——见 §3 L1。
> **本文件不写任何可运行 server 代码，也不修改 `adapters/mcp/**`**（只引用）。
> **仍未实现**：① 宿主侧 MCP 注册/接入配置 ② v2 宿主专属 tool schema ③ 宿主注入 policy/context/session
> 三 Port（见 §3 L2、§4）。
> 凭据 0 入件：只写凭据模式（`path-ref-only` / `credential_ref` 机制），不引 token/密码/值。

## 0. 口径与边界

- 本清单 = **v1 `xiaozhua-host-bootstrap.v1` 五能力 + CLI op 面 → Codex MCP tool 声明**
  （字段映射承接 AGENT-ADAPTER §四 L78–L91："v1 dict 哪个字段承接进 v2 adapter 暴露面"）。
- 五能力语义在盘实测（`xiaozhua_host_bootstrap.py` L46/L71/L95/L119/L133）；
  CLI op 面在盘实测（`xiaozhua_cli.py` L174/L185–L196）；**传输层实装态见 §3（已实装 / 未实现分层写）**。
- 每 tool 列：`name` / 入参 / 返回 / 只读性 / 凭据模式。凭据模式统一 =
  `credential_mode="path-ref-only"`（bootstrap L147）+ CLI `--credential-file`/`--credential-ref`
  （L191–L192）；**各宿主侧注入实现未实现**（A8 §四 L83；§3 L2③）。

## 1. MCP tool 清单（五能力 5 tool + CLI 只读 op 面）

### 1.1 bootstrap 五能力 → Codex tool

| MCP tool name | 承接 v1 键（行号） | 入参 | 返回 | 只读性 | 凭据模式 |
|---|---|---|---|---|---|
| `xiaozhua_dispatch` | `dispatch`（L133） | `intent:str, target?:str` | `dict`：路由+组件执行+证据化结果（含 `status`） | 只读；未知→`UNAVAILABLE`（registry L36–L52） | `path-ref-only`（离线可用） |
| `xiaozhua_generate` | `generate`（L46） | `application_id, entity_name, attributes?:list, caption?:str` | `dict`：backend（8 类 Java 骨架）+ frontend（页面定义）；`status`/`plan_blocked`/`plan_warnings` | 只读（出数据）；方法体 UNVERIFIED（L48） | `path-ref-only` |
| `xiaozhua_generate_from_requirement` | `generate_from_requirement`（L71） | `text:str, application_id` | `dict`：`parsed`+backend+frontend；不可确定→`UNVERIFIED`+`unknowns`（L74–L76） | 只读（出数据） | `path-ref-only` |
| `xiaozhua_live_probe` | `live_probe`（L95） | `cred_file?`（否则用 bootstrap `credential_file`） | `dict`：test2 4 端点只读 POST；无凭据→`SKIPPED`；有凭据但 `allow_network=False`→`BLOCKED`（L96–L100） | 只读；活体需显式 `allow_network=True` | `path-ref-only`（活体需凭据路径） |
| `xiaozhua_deploy_plan` | `deploy_plan`（L119） | `application_id, entity_name, attributes, caption?, stereotype="bill", deploy_type="RELEASE"` | `dict`：设计态 4 步部署方案 data（`readonly_plan=True`，L122–L130） | 只读出方案 data；写步由宿主执行（`deployment_plan`，L148） | `path-ref-only` |

### 1.2 CLI 只读 op 面 → Codex tool（Codex 走 shell，HOST-INTEGRATION §3 L34–L37）

| MCP tool name（声明） | 承接 CLI 子命令（行号） | 入参 | 返回 | 只读性 | 凭据模式 |
|---|---|---|---|---|---|
| `xiaozhua_cli_capabilities` | `capabilities`（L174） | 无 | `dict`/JSON：只读能力面清单 | 只读 | 无（离线） |
| `xiaozhua_cli_op_execute` | `op-execute`（L185–L196） | `--operation`（required）/`--application-id`（required）/`--entity-id`/`--entity-name`/`--gateway-url`/`--credential-file`/`--credential-ref`/`--principal`/`--timeout`/`--evidence-out`/`--allow-network` | 单行 JSON：脱敏 `OperationResult`（`--evidence-out` 落盘） | **只读**（写面 `udc-execute` L183 = DENIED，退出码 2，不列 tool） | `--credential-file <仓外路径>` + `--credential-ref`（default `cli-default`）；`--allow-network` default 关 |

> 写面 `udc-execute`（L183）**不列**为 Codex tool：写一律 DENIED（`README.md` L96–L100），
> Codex 侧只暴露只读 op 面，写步由宿主按 `deploy_plan` 方案 data 执行（`deployment_plan` 口径）。

## 2. 全局能力面（MCP server 声明级）

- `capabilities.readonly_only = True`（bootstrap L146 实测）→ 全 tool 只读纪律；
  写面写门 DENIED（宿主授权执行，A8 §二 L51）。
- `capabilities.credential_mode = "path-ref-only"`（L147）→ 全 tool 凭据模式统一；
  CLI 侧对应 `--credential-file`/`--credential-ref`（L191–L192）。
- `capabilities.deployment_plan = "readonly data; host executes the write steps"`（L148）
  → 写方案 data、宿主执行写步，MCP tool 面不直接执行写。
- `capabilities.schema = "xiaozhua-host-bootstrap.v1"`（L149）→ 本清单 schema 锚；
  **v2 宿主专属 schema（codex）未定义 = 未实现**（A8 §四 L85；§3 L2②）。
- `allow_network`（bootstrap L143）/ `--allow-network`（CLI L196，default 关）/ MCP 侧
  `XIAOZHUA_ALLOW_NETWORK` env（`server.py` L176–L177）→ 活体探测开关，**传输层已承载**（§3 L1）；
  **宿主侧开关配置未实装**（§3 L2①）。

## 3. 实现态分层（2026-10-19 实测，非转述）

> 分层口径：**L1 = 传输层**（仓内 `adapters/mcp/`，**已实装**）｜**L2 = 宿主侧接入面**（本清单描述对象，**未实现**）。
> 旧表述"MCP server 传输层未实现 = UNVERIFIED"**已作废**——该结论与仓内事实相反（欠报已实现部分，
> 同属证据纪律缺陷）。下述 L2 三项口径与 `adapters/hermes/`、`adapters/claude-code/` 两份清单**一致**。

### L1 传输层 —— 已实装（在盘可复核）

| 事实项 | 实测值 / 证据 |
|---|---|
| 实现件 | `adapters/mcp/server.py`，**12835 B**，sha256 `d20b47e8635b8fb0639902fb311e18549c87b03d2edcf38f97ce03798a5e179e` |
| 提交 | commit `3595d7e`（`feat(mcp): xiaozhua_host_bootstrap 五能力 → MCP stdio server 实装`，2026-09-28 22:54:34 +0800） |
| 单测 | `pytest tests/test_mcp_server.py -q` → **19 passed**（2026-10-19 实测，0.17s，RC=0） |
| 协议面 | stdio 每行一帧 JSON-RPC 2.0；`protocolVersion = "2024-11-05"`；method 白名单 `initialize` / `tools/list` / `tools/call`（`notifications/initialized` 静默 ack）；错误码 -32601 / -32602 / -32700 / -32603 |
| tool 面 | 恰 **5** 个：`xiaozhua_dispatch` / `xiaozhua_generate` / `xiaozhua_generate_from_requirement` / `xiaozhua_live_probe` / `xiaozhua_deploy_plan`（`server.py` L25–L31）；**无任何写工具**（`test_write_not_exposed`） |
| schema 生成 | `build_tool_schemas()` 由 `inspect.signature` + `components/platform_operations/deployment.py` 常量（`DATATYPES`/`DEPLOY_TYPES`/`STEREO_TYPES`）生成，枚举非手抄（`server.py` L83–L120） |
| 凭据 | `path-ref-only`：`XIAOZHUA_CRED_FILE` env 或 `live_probe(cred_file=)`（`server.py` L178），**值 0 入件** |
| 离线默认 | `XIAOZHUA_ALLOW_NETWORK` 未设或非 `1`/`true`/`True` → `allow_network=False`（`server.py` L176–L177） |
| 实跑（本件复核，非单测替代） | `python adapters/mcp/server.py < frames`（RC=0）：`initialize`→`protocolVersion=2024-11-05` + `serverInfo xiaozhua-mcp/0.1.0`；`tools/list`→恰 5 工具；`tools/call(xiaozhua_dispatch)`→离线 `status=UNVERIFIED`；`tools/call(xiaozhua_live_probe)` 无凭据→`status=SKIPPED`（**≠ PASS**） |

### L2 宿主侧接入面 —— 未实现（本清单真正描述的目标态）

| # | 未实现项 | 实测依据 | 状态 |
|---|---|---|---|
| ① | **各宿主侧 MCP 注册/接入配置**（Codex：`~/.codex/config.toml` 的 MCP server 注册项 + `AGENTS.md` 装载） | 仓内无 `.codex/` 目录、无任何 `mcp*.json` 注册件（`find` 实测空） | **未实现** |
| ② | **v2 宿主专属 tool schema**（hermes / codex / claude-code 三套） | 现 schema = v1 `xiaozhua-host-bootstrap.v1` 签名反射结果，宿主差异化 schema 未定义（A8 §四 L85） | **未实现** |
| ③ | **宿主注入 policy / context / session 三 Port 实装** | `xiaozhua_host_bootstrap.py` L39 `XiaozhuaAgent(comps)` 未传 `context`/`session`/`policy`（`core/agent.py` L39 支持注入，默认 `MemoryContext`/`MemorySession`/`ReadOnlyPolicy`）；`server.py` 未暴露注入入口 | **未实现** |

## 4. 已知未实现 / 环境依赖

**已知未实现（如实登记，不虚写完成）**

1. **宿主侧 MCP 注册/接入**：Codex 侧未把 `adapters/mcp/server.py` 注册进宿主 MCP 配置，也未做 `AGENTS.md` 装载工序
   （本清单只给声明，不写宿主配置落地）。
2. **v2 宿主专属 tool schema**：三宿主差异化 schema 未定义。
3. **宿主注入三 Port**：`context`/`session`/`policy` 注入实装未做，`bootstrap()` 走默认实现。
4. **MCP 扩展面**：`resources` / `prompts` / `logging` 未实现（`adapters/mcp/STATUS.md` §未做；本切片按最小协议面达标）。
5. **`installer/` 打包面**：目录约定件在盘，安装脚本未实现（`installer/` 内实现项标 UNVERIFIED）。
6. **Codex 侧 CLI 面**：`xiaozhua_cli op-execute` 在盘可跑（shell 直调），但**未注册为 Codex MCP tool**
   （§1.2 为声明映射，非宿主实装）。
7. **v1 侧历史遗留**：`docs/HOST-INTEGRATION.md` §2 仍写"四个能力"（缺 `generate_from_requirement`/`deploy_plan`），
   属 `docs/` 非本切片可写路径，登记不修。

**环境依赖（BLOCKED，不属本件可写路径）**

- 全量 `pytest tests -q` 当前 = **1490 passed / 1 failed / 21 skipped**（2026-10-19 实测）。失败项
  `tests/udc/test_dynamic_register_channel.py::test_evidence_is_recomputable_by_the_tool_byte_for_byte`
  依赖 `<HERMES_HOME>/cache/scratch/sup_v2`（scratch 24h 清理；jar 成员清单 94 jar / 1170 class
  无在盘可复现来源；证据件按字节判等 ⇒ **不可重建**）。该失败属 **udc-semantics 线环境依赖**，
  已由 main 裁定该分支 BLOCKED，**不在本切片可写路径**（禁改 `tests/`、禁改 components/tools）。
- **通过数表述纪律**：禁再以裸数字（旧文档里的历史通过数）当契约。凡需引用测试通过数，一律写
  "以 `python -m pytest tests -q` 实测为准"，或如实并列来源（不同时点/不同命令口径，**均非契约**）：
  `README.md` L30 现记 `1512 passed`（仓内文档现值，与本机实跑不符）；
  `docs/HOST-INTEGRATION.md` §5 L49 记 `361 passed`（.venv 口径，历史值）；
  2026-09-26 本切片收口记录 `375 passed`；2026-10-19 实测 `1490 passed / 1 failed / 21 skipped`。

## 5. 边界自证

- 本件只改声明件；**未触碰** `adapters/mcp/**`（只读引用）、`components/`、`core/facts/`、`core/tools/`、
  `core/skills/`、`docs/capability/`、`tests/`、`xiaozhua_cli.py`、`adapters/codex/AGENTS.template.md`（sha 不变）。
- 凭据 0 入件；未写可运行 server 代码；未连网；未 `git push`。
