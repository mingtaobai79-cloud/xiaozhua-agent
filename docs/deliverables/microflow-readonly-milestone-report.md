# 微流程只读里程碑 A6 收口报告（能读什么 / 精确怎么读 / 仍 UNVERIFIED·BLOCKED）

> 本文件为里程碑唯一业务产物（A6）。报告本身聚合既有已落地证据，不新跑探测、不发明；
> 全部路径为**仓库根相对路径**（不写死绝对机器路径 / 版本号 / 网关 URL / appId / 凭据值）。
> 证据等级纪律：`STATIC_CONTRACT < VERIFIED_STATIC_BYTECODE < LIVE`，本轮离线，**未升级 LIVE**。
> 本地 Maven（本地反编译 5.3 族）与 test2 部署态版本族隔离，**禁一版推断另一版**。

---

## ① 总目标回答：「看微流程」= xiaozhua-agent 可验证只读能力现状

**总目标**（collaboration.json §一）：把「看微流程」做成 xiaozhua-agent 里**可验证的只读能力**——
微流程只读契约 + 只读调用 + 回读证据；**不实现任何写/发布能力**。

**离线可验证（本轮已达成，可重复、不依赖凭据/VPN）**：
- 8 条微流程/元数据只读契约已入 registry（C1–C8），逐条绑定来源
  `artifact + version + class + method + path + 参数 + 响应类型 + 证据等级`，
  全部 `VERIFIED_STATIC_BYTECODE`、`write=False`。
- 证据可被 evidence ledger / audit bundle 离线聚合（A3）：
  `components/evidence_ledger.py` + `components/audit_bundle.py`，
  `conflict_count=0`、`network=disabled`、`live_pass_count=0`、`status=PARTIALLY_VERIFIED`。
- 离线全量 pytest 全绿（A4），契约 + 计数契约测试同步（A4 计数已含 8 契约 + A3 聚合测试）。
- 写路径维持 POLICY_DENIED（A5），本轮**未新增**任何写能力。

**活体才能验证（本轮未做，维持 UNVERIFIED，走人工门）**：
- A2 ≥1 条在 test2 上 LIVE PASS（同一 target 回读 `identity_matches=true`；HTTP 200/非空≠PASS）。
- C1/C2/C3 + C6/C7/C8 的只读读面 / identity 活体确证（POST 读面语义需运行态确认，非离线可推）。
- 上述活体项需人工门 G1/G2/P1（见 §⑥）开门，或新 jar / 新 token。

**一句话结论**：「看微流程」的**契约 + 离线可聚合证据 + 只读边界**已收口；
「**活体可回读且 identity 一致**」仍停在 UNVERIFIED，须走人工门（A2 LIVE + 活体只读读面确证）。

---

## ② A1–A6 逐项达成表

| 项 | 含义 | 状态 | 落地证据路径（仓库根相对） |
|---|---|---|---|
| **A1** | 微流程只读契约 ≥3 条进 registry，逐条绑定来源/路径/参数/响应/证据等级 | **PASS**（8 条 C1–C8，超出下限） | `components/platform_operations/registry.py`；`tests/test_applog_microflow_readonly.py`；`tests/test_metadata_page_exists_contract.py`；`tests/test_metadata_anchor_contract.py`；`tests/test_microflow_readonly_contract.py` |
| **A2** | ≥1 条在 test2 LIVE PASS（`identity_matches=true`，HTTP 200/非空≠PASS） | **UNVERIFIED**（单分支，人工门 G1/G2/P1；不升 PASS） | `docs/operation-contracts/udc/microflow/live-evidence/`（活体 raw）；`docs/operation-contracts/udc/microflow/microflow-ledger-inputs/http.json`（3 条 probe 均 UNVERIFIED/404）；`docs/operation-contracts/udc/microflow/gateway-live-facts.md` |
| **A3** | 证据落 `docs/operation-contracts/udc/microflow/` 且可被 ledger / audit-bundle 聚合 | **PASS**（`conflict_count=0`、`network=disabled`、`live_pass_count=0`、`status=PARTIALLY_VERIFIED`） | `providers/nacos_evidence_manifest.py`；`components/evidence_ledger.py`；`components/audit_bundle.py`；`tests/test_microflow_evidence_aggregation.py`；`docs/operation-contracts/udc/microflow/microflow-ledger-inputs/`（9 份 JSON） |
| **A4** | 离线全量 pytest 通过 + 新增契约单测 + 文档计数契约同步 | **PASS**（全量 328 passed 0 failed） | `tests/`（全量）；`tests/test_documentation_contract.py`（计数）；`README.md` / `docs/audit/agent-version-audit.md` / `docs/audit/code-reality-audit.md`（计数命中点已同步 328） |
| **A5** | 写路径保持 POLICY_DENIED，本轮不新增写能力 | **PASS**（写管理面 deleteAll/createBatch/saveFrontLog 等不放行；`write=False` 全 8 契约） | `components/platform_operations/registry.py`（8 契约 write=False）；`components/platform_operations/layer.py`（执行边界放行条件）；`auditor/VERDICT-*.md`（各轮写面边界确认） |
| **A6** | 回答：能读什么 / 精确怎么读 / 哪些仍 UNVERIFIED·BLOCKED 及精确缺口 | **= 本报告** | `docs/deliverables/microflow-readonly-milestone-report.md`（本文件） |

> 证据等级纪律：A2 维持 **UNVERIFIED**（**不得**标成 PASS）；A3 聚合结果为 `PARTIALLY_VERIFIED`
>（含 3 条 UNVERIFIED probe + 离线静态契约），不升级 LIVE。

---

## ③ C1–C8 微流程只读契约清单（与 `registry.py` 逐字一致）

> 下表 operation_id / method / path / 请求 / 响应 / 证据等级 / write 均直接取自
> `components/platform_operations/registry.py` `default()`，**逐条可 readback**（`registry.get(op)`）。

| # | operation_id | method | path（控制器原值，未拼网关前缀） | 请求类型 | 响应类型 | 证据等级 | write |
|---|---|---|---|---|---|---|---|
| C1 | `udc.microflow.function_node_tree` | GET | `udc-runtime/meta-data/select-function-node-tree/{appName}` | `String appName(SingleRequest)` | `ListResponse<UdcFunctionNodeMetadataDto>` | VERIFIED_STATIC_BYTECODE | False |
| C2 | `udc.datatype.get_all` | GET | `udc-runtime/datatype/getAll` | `()` | `ListResponse<DataTypeDto>` | VERIFIED_STATIC_BYTECODE | False |
| C3 | `udc.applog.select_by_id` | GET | `udc-runtime/app-log/datalog/{id}` | `Long id(SingleRequest)` | `SingleResponse<UdcEntityMonitorLogDto>` | VERIFIED_STATIC_BYTECODE | False |
| C4 | `udc.metadata.page_tree` | POST | `udc-runtime/meta-data/select-host-and-only-page-pages` | `UdcPagesMetaDataSearchDto(RequestBody)` | `ListResponse<UdcMainPageMetadataDto>` | VERIFIED_STATIC_BYTECODE | False |
| C5 | `udc.metadata.page_exists_check` | POST | `udc-runtime/meta-data/check-page-exists` | `List<UdcRtPageExistsDto>(RequestBody)` | `ListResponse<Boolean>` | VERIFIED_STATIC_BYTECODE | False |
| C6 | `udc.applog.search_microflow` | POST | `udc-runtime/app-log/search/microflow` | `PageDtoRequest<MicroFlowLogSearchDto>(RequestBody)` | `PageResponse<MicroFlowLogResultDto>` | VERIFIED_STATIC_BYTECODE | False |
| C7 | `udc.applog.search_details_microflow` | POST | `udc-runtime/app-log/search-details/microflow` | `PageDtoRequest<MicroFlowLogDetailsSearchDto>(RequestBody)` | `PageResponse<MicroFlowLogDetailsResultDto>` | VERIFIED_STATIC_BYTECODE | False |
| C8 | `udc.applog.search_details_microflow_flowlog` | POST | `udc-runtime/app-log/search-details/microflow/flowLog` | `MicroFlowLogDetailsSearchDto(RequestBody)`（裸 DTO，非 PageDtoRequest 包装） | `SingleResponse<MicroFlowFlowLogResultDto>` | VERIFIED_STATIC_BYTECODE | False |

- **网关 service 前缀**：离线不可确证 → **UNVERIFIED，禁止拼前缀**（C2/C3/C4/C5/C6/C7/C8 均标注）。
- **C8 特别**：请求为裸 `MicroFlowLogDetailsSearchDto`，与 C6/C7 的 `PageDtoRequest<>` 包装不同（按 javap 原文如实登记）。
- **POST 契约已知边界（非 FAIL）**：C4–C8 端点 javap 原文为 `@PostMapping`，而执行链仅放行 `method=GET`，
  故在 `PlatformOperationLayer` 上为 **DENIED/POLICY_DENIED**（执行层放行前维持），可执行性留活体（P4）。
  registry 登记 = 契约声明，不改变执行边界放行条件。

---

## ④ 证据等级声明

- 等级链：`STATIC_CONTRACT < VERIFIED_STATIC_BYTECODE < LIVE`。
- C1–C8 全部停在 **`VERIFIED_STATIC_BYTECODE`**（本地 Maven 离线反编译 javap 原文取证，`VERIFIED_STATIC_BYTECODE`），
  **未升级 LIVE**。
- LIVE 升级仅在 test2 活体回读 `identity_matches=true`（同一 target 双读 `strip(traceId)` 一致）后发生；
  本轮离线，**A2 维持 UNVERIFIED，不标 LIVE**。
- 版本族隔离：本地 Maven（本地 5.3 族，离线反编译）与 test2 部署态版本**分列不混写**，禁一版推断另一版。
  两版本在 evidence 中分别标注（`source=local-maven-53517` / `source=test2-container` 等），不跨族推断。

---

## ⑤ 08:45 元数据锚点规则对齐（层次逐条标注）

> 规则（人指 08:45 生效，见 ROUTE §元数据锚点规则对齐）：
> 平台 UDC 元数据 = 搭建结果**权威载体 + 验收锚点**；平台 meta-data 接口 = 首选读写面。
> 验收判据 = 回读元数据 `identity_matches`；**HTTP 200 / Boolean ≠ PASS**。
> 层次不可混写：**设计态配置 ≠ 运行态元数据 ≠ 生成物 ≠ 物理表 ≠ Redis 缓存**，彼此**不可顶替**。

| 契约 | 层次 | 锚点角色 |
|---|---|---|
| C4 `udc.metadata.page_tree` | **运行态 meta-data 层**（平台 meta-data 接口，页面树元数据） | **identity 验收锚点**（回读页面树元数据 `identity_matches`） |
| C5 `udc.metadata.page_exists_check` | **运行态 meta-data 层**（存在性探测面） | **非 identity 锚点**（返回 `ListResponse<Boolean>`，按 08:45 规则②：Boolean/HTTP 200 不作 identity 锚点，仅存在性探测） |
| C6 `udc.applog.search_microflow` | **运行态 app-log 日志层**（microflow 搜索面，非 meta-data 层） | 日志/存在性探测面，**非 identity 验收锚点** |
| C7 `udc.applog.search_details_microflow` | **运行态 app-log 日志层**（microflow 详情搜索面） | 日志/存在性探测面，**非 identity 验收锚点** |
| C8 `udc.applog.search_details_microflow_flowlog` | **运行态 app-log 日志层**（microflow flowLog 详情面） | 日志/存在性探测面，**非 identity 验收锚点** |

- C1/C2/C3（meta-data 节点树 / datatype / app-log datalog by-id）同为运行态只读面，
  各自回读 identity，但 **C1/C2** 属 meta-data/datatype 层、**C3** 属 app-log 日志层（datalog/{id} 节点日志）。
- 以上层次标注与 registry evidence `note` 字段一致（运行态元数据层 / 运行态日志层，非设计态配置/生成物/物理表/Redis）。
- **设计态配置不可顶替运行态元数据**：设计态缺口（设计态制品目录 `docs/audit/artifacts/udc-design-targeted-*`
  按版本族命名、本地 5.3 族为空，udc-biz/web/assemble/extend 本地 Maven MISSING）已登记为 BLOCKED/UNVERIFIED，
  不得用运行态/设计态互相顶替（版本族隔离，不跨族推断）。

---

## ⑥ 人工门清单（G1 / G2 / P1）+ 开门后动作

| 门 | 内容 | 当前状态 | 精确缺口 |
|---|---|---|---|
| **G1 新 token** | test2 只读凭据（`<appId>:readonly` 授权） | **过期**（凭据文件 mtime 仍旧值，exp 已过） | 需换新只读 token；**凭据值绝不写入任何 evidence/文档/日志，只用文件引用** |
| **G2 Long 型 target** | 真实 app/flow/log id（Long） | **未备**（C3 需真实 log id 复核；微流程回读需 Long target） | 需真实 Long 型 application_id / log_id 作回读 target |
| **P1 新 jar** | 跨版本确证（本地 5.3 族 vs test2 部署态版本族隔离） | **未取** | 若需跨版本活体确证，需从 test2 部署态取同族 jar（禁一版推断另一版） |

**开门后动作（A2 LIVE + C6–C8 只读读面/identity 活体确证）**：
- 三门任一开 → A2 LIVE：C1/C2/C3 **正式 LIVE 回读**（同一 target 双读 `strip(traceId)` `identity_matches=true`）
  + 落 evidence（只读不写）；C6–C8 运行态确证该 `@PostMapping` 端点为**只读读面**（POST 读语义），
  确认后由 POLICY_DENIED 转放行（仍只读，不实现写）。
- 活体探测走 P4：`test2` 只读端点，凭据不落盘（G1），网关前缀 UNVERIFIED（不拼）。
- **本轮不重探 Nacos、不碰凭据、不发无对象 HANDOFF**（main ROUTE 02:18 CST 收口登记已停手）。

---

## ⑦ 边界与限制

- **凭据值**：只用**文件引用**（G1 token 路径），**不写入报告/日志/evidence**；敏感键自动 `[REDACTED]`
  （`providers/nacos_evidence_manifest.py` 的 `_SENSITIVE_KEY` 正则 + `_safe_text`）。
- **非微流程通用日志面**（`datalog/search`、`search/dataflow`、`search/deduction`、`datalog/list-by-dataid` 等）
  **不纳入本里程碑**（超出「看微流程」总目标，属通用数据源日志，非微流程只读契约族；main R11 已定）。
- **HTTP 200 / Boolean ≠ 单独 PASS**（08:45 规则②）：C5 返回 `ListResponse<Boolean>`、活体 404 Whitelabel，
  均**不升级 PASS**，只作存在性探测 / UNVERIFIED 探针。
- **证据等级不升级**：本轮离线，C1–C8 全停 `VERIFIED_STATIC_BYTECODE`，**不升 LIVE**。
- **版本族隔离**：本地 Maven 与 test2 部署态分别标注，**禁一版推断另一版**。
- **040402 配置化铁律**：本报告不写死绝对机器路径 / 版本号 / 网关 URL / appId，全部用**配置或相对引用**。
- **写能力**：本轮**未新增**任何写/发布能力，写管理面维持 A5 POLICY_DENIED。

---

## ⑧ 引用既有 evidence 路径（全部已落地，仓库根相对）

- **契约**：`components/platform_operations/registry.py`（C1–C8，`default()` 逐条可 readback）
- **执行边界**：`components/platform_operations/layer.py`（放行条件 = 契约生效 + method=GET + write=false + auth_scope `<appId>:readonly`）
- **A3 聚合器**：`providers/nacos_evidence_manifest.py` + `components/evidence_ledger.py` + `components/audit_bundle.py`
- **A3 聚合输入**：`docs/operation-contracts/udc/microflow/microflow-ledger-inputs/`（udc/runtime/http/evidence_context/version_audit/path_matrix/impact_graph + ledger-output/bundle-output，9 份 JSON）
- **A3 单测**：`tests/test_microflow_evidence_aggregation.py`（断言 3 静态契约 FACT + 3 HTTP probe UNVERIFIED，`conflict_count=0`、`live_pass_count=0`、`network=disabled`、`status=PARTIALLY_VERIFIED`）
- **活体证据**：`docs/operation-contracts/udc/microflow/live-evidence/`（a2 live readback + C1 node tree + applog datalog raw）
- **网关事实**：`docs/operation-contracts/udc/microflow/gateway-live-facts.md`（网关 service 前缀 UNVERIFIED）
- **候选契约**：`docs/operation-contracts/udc/microflow/local-53517-offline-candidates.md` + `candidate-contracts-evidence.md`
- **审计 verdict**：`auditor/VERDICT-20260918-R10-C5-page-exists.md` / `R11-C6` / `R12-C7` / `R13-C8`（各轮 C5–C8 闭环）
- **离线全量**：`tests/`（`uv run pytest` **328 passed 0 failed**；A4 计数契约已同步 328）
- **A6 报告（本文件）**：`docs/deliverables/microflow-readonly-milestone-report.md`

> 注：`docs/operation-contracts/udc/microflow/a6-milestone-report.md` 为 R14 前一轮（C1–C8 收口后）的收口稿；
> 本 A6 报告为**唯一业务产物**，按 HANDOFF 8 要素重排，聚合上述已落地证据，不重新发明、不新跑探测。

---

## 收口状态

- **离线里程碑 OFFLINE-CLOSED / A2-UNVERIFIED（单分支维持）**。
- A1 PASS（C1–C8）/ A2 UNVERIFIED（人工门 G1/G2/P1）/ A3 PASS / A4 PASS（328 全绿）/ A5 PASS / A6 = 本报告。
- 残余全部走**活体人工门**（A2 LIVE + C6–C8 只读读面/identity 活体确证）；**不重探 Nacos、不碰凭据**。
- 本报告落盘 + 8 要素齐全 + 与 A1–A5 落地证据一致 + 无硬编码机器路径/版本/网关 URL/appId + 凭据值零出现（仅文件引用）
  = **A6 达成，里程碑离线收口完成，仅剩 A2 活体走人工门**。
