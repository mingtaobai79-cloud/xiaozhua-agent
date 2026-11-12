# 数据流映射只读族 + UDC↔BPM 数据流链路契约｜flow 域第 2 格

> 基线：本任务 TASK-GOAL（`事实模块任务｜BPM-flow(flow 域 16 契约+微流程)`）+ 本会话 `main/ROUTE.md` @ 目标仓库
> `<XIAOZHUA_AGENT_ROOT>` HEAD `16a384c`。九段式能力事实文档（交付物第 2 件，`core/facts/bpm/data-flow-map.md`），
> 节序照在盘样板 `core/facts/udc/entity/create.md`（B1 样板格，PASS）。行尾 CRLF（本格登记形态；族内行尾不统一：族索引 core/facts/INDEX.md 为 CRLF，core/facts/batch-modules-20260925.md 与 core/facts/udc/entity/create.md、core/facts/udc/readonly-faces-batch2.md 为 LF，实测法 tr -cd CR/LF 计数）。
> 本件**只做数据流映射只读族 + UDC↔BPM 数据流链路契约**；第 1 格 `flow-node-tree.md` 已冻结（绑定字节 16070 B /
> sha256 `36ead221…4ec5f`），本件不改动它。只写事实文档，不实现代码、不改 `components/**`；凭据值 0 入件。
> 引注纪律（本会话）：依据栏只写「在盘路径 + 行号」或「在盘实读值」；任务边界引 `inputs/desktop-source/TASK-GOAL.md` 具体行；
> javap 行号一律为实测精确边界。

---

## 1. Capability

**数据流映射只读族（6 条）** — 读运行态数据流映射与其映射明细（flow 域只读读面，`write=False`、全 `GET` 或 POST 读型）。
- **类型**：READ 型（契约 `write=False`；其中 2 条 `GET` → `.effective=True`，4 条 POST 读型 → `.effective=False`，见 §5）。
- **位置**：`components/platform_operations/registry.py` **L74 / L76 / L78 / L80 / L82 / L84**（6 条 `UdcOperationContract`，在盘实测原文）；
  对应 evidence 字典 **L73 / L75 / L77 / L79 / L81 / L83**。执行边界 = `PlatformOperationLayer`（唯一执行边界）。
- **语义**：`udc-runtime/data-flow-map` 读映射表（`DataFlowRtMapDto`）、`udc-runtime/data-flow-mapping` 读映射明细（`DataFlowRtMappingDto`），
  均为运行态数据流层读面（registry.py L73/L77 evidence `note` 原文）。
- **UDC↔BPM 数据流链路契约（本格核心新增面）**：`docs/audit/modules/module-link-evidence.json`
  关系 `udc → standard-product`，类型 `exposes-platform-runtime-contracts-to`，等级 `VERIFIED_STATIC_BYTECODE`（L71-84）。
  该关系**是契约关系、不是运行时调用关系**（同文件 L123 limitations 首条原文，见 §7）。
- **BPM 引擎本体（执行器/模型/调度实现）**：无在盘证据 → 整段 `UNVERIFIED`（依据 `inputs/desktop-source/TASK-GOAL.md` L6）。

## 2. Version

- **Canonical = 5.3.517**。本族 artifact 全为 `udc-starter-dataflow-5.3.517.jar`
  （registry.py L73/L75/L77/L79/L81/L83 evidence `artifact` 实测同值）。
- 链路面对侧 artifact = **`bpm-facade` 3.12.101**（`docs/audit/modules/decompiled/bpm-api-decompile-manifest.json`
  L3 `"artifact": "bpm-facade"` / L4 `"version": "3.12.101"` / L5 `"source_sha256": "26b312fdd40cc921a4cd8d08239f6b8d857c02a5ac8d4db271d07f6fcbd98af0"`）。
- **类哈希（逐件在盘实读 `.class.sha256`）**：
  - `DataFlowRtMapController` = `455df593d43558055e01d69f4aacc70ce337ec80b4f7275adc471c49a22d1d95`
  - `DataFlowRtMappingController` = `ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8`
  - `DataFlowForBpmController`（写侧，仅登记）= `8b31f788f981eaa9a1ee025b72410f9bf71b4dd214b6a8cb3e41d566103ba5e4`
  （均在 `docs/audit/artifacts/udc-flow-5.3.517/<类名>.class.sha256`，与 registry.py L73/L77 同值）。
- **版本纪律（不混写）**：相邻版本 `bpm-facade 5.3.374` 与 `app-approval 5.3.295` **未用作证据**
  （`docs/operation-contracts/udc/flow/flow-domain-scan.md` L6 原文「未触碰 bpm-facade 5.3.374 与 app-approval 5.3.295…未进任何证据」；
  同文件 L102「只读 GET/POST-读 候选共 7 条 ≥ 4，无需扩到相邻版本补数」）。
- **Adapter 未建 → 其他版本 UNVERIFIED**（无在盘证据，不推版本分支）。

## 3. Input

**path 构造 = 类级 `@RequestMapping` + 方法级 `@{Verb}Mapping` 逐字拼接，不拼网关前缀**（javap 行号为实测精确边界）：

| 契约 | method | path（逐字） | 类级锚点 | 方法级锚点 |
|---|---|---|---|---|
| `udc.flow.data_flow_map_get_by_id` | GET | `udc-runtime/data-flow-map/{id}` | javap L178 `value=["udc-runtime/data-flow-map"]` | javap L159 `value=["{id}"]` |
| `udc.flow.data_flow_map_search` | POST | `udc-runtime/data-flow-map/search` | 同上 | javap L126 `value=["search"]` |
| `udc.flow.data_flow_mapping_get_by_id` | GET | `udc-runtime/data-flow-mapping/{id}` | javap L344 `value=["udc-runtime/data-flow-mapping"]` | javap L193 `value=["{id}"]` |
| `udc.flow.data_flow_mapping_search_original` | POST | `udc-runtime/data-flow-mapping/search-original` | 同上 | javap L160 `value=["search-original"]` |
| `udc.flow.data_flow_mapping_init_data` | POST | `udc-runtime/data-flow-mapping/init-data` | 同上 | javap L232 `value=["init-data"]` |
| `udc.flow.data_flow_mapping_detail` | POST | `udc-runtime/data-flow-mapping/detail` | 同上 | javap **L331** `value=["detail"]` |

javap 所在：`docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMapController.javap.txt`（11621 B，类声明 L5）、
`DataFlowRtMappingController.javap.txt`（24210 B，类声明 L5）。

- **入参 / 响应（registry.py 逐字）**：
  - L74 `Long id(SingleRequest)` → `SingleResponse<DataFlowRtMapDto>`
  - L76 `DataFlowRtMapQueryDto(SingleRequest)` → `ListResponse<DataFlowRtMapDto>`
  - L78 `Long id(SingleRequest)` → `SingleResponse<DataFlowRtMappingDto>`
  - L80 `OriginalDataFlowMappingListQueryDto(SingleRequest)` → `ListResponse<DataFlowRtMappingDto>`
  - L82 `DataFlowMappingInitQueryDto(SingleRequest)` → `SingleResponse<DataFlowRtEditInitialDataDto>`
  - L84 `DataFlowOriginalMappingQueryDto(SingleRequest)` → `SingleResponse<DataFlowRtMappingDto>`
- **同 controller 的写侧端点（仅登记，不进只读计数）**：`DataFlowRtMappingController` 另有 `@PostMapping` javap L265 `value=["update"]`
  与 L298 `value=["state"]`，对应拟稿 `udc.flow.data_flow_mapping_update`（`docs/operation-contracts/udc/flow/registry-entries.md` L193，path `udc-runtime/data-flow-mapping/update`）
  与 `udc.flow.data_flow_mapping_update_state`（同文件 L208，path `udc-runtime/data-flow-mapping/state`）。
- **写侧 3 条（登记 `write=True`，策略门控未放开，不进只读计数）**：`registry-entries.md` L175 小节（L178 `udc.flow.bpm_fill_error_data`
  path `udc-runtime/bpm/fill-data` / L193 `…_update` / L208 `…_update_state`）；对应 `DataFlowForBpmController`
  javap L125 `value=["fill-data"]`、类级 javap L134 `value=["udc-runtime/bpm"]`。
- **`.effective` 判据定义在盘**：`components/platform_operations/models.py` L47-49
  （`status ∈ {PASS, VERIFIED_STATIC_BYTECODE, OBSERVED}` 且 `not write` 且 `method.upper()=="GET"`）。

## 4. Required（必填链与缺省推断）

- **必填输入（registry.py `required_inputs` 逐字）**：
  - L74 `("id",)`；L78 `("id",)` —— 两条 `GET` 的 `{id}` 为路径变量，缺失即无法构造路由。
  - L76 `("DataFlowRtMapQueryDto(过滤条件),",)`；L80 `("OriginalDataFlowMappingListQueryDto(源映射条件),",)`；
    L82 `("DataFlowMappingInitQueryDto(初始化条件),",)`；L84 `("DataFlowOriginalMappingQueryDto(详情条件),",)`。
- **缺省推断**：**无**（6 条契约的输入均为显式声明项，格内不臆造替代值）。
- **verification_rules（registry.py 逐字摘要）**：GET 两条为「同一 id 回读 dataFlowMap/dataFlowMapping `identity_matches` + 响应 `.id` 与入参一致」；
  4 条 POST 读型为「同一条件回读列表/初始数据/详情 `identity_matches` + 响应结构断言」。6 条**均含**「网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）」。

## 5. Execution

- **读门放行条件（在盘实测定义）**：`models.py` L47-49（同 §3 末条）。本族三值：`status=VERIFIED_STATIC_BYTECODE`、`write=False`；
  `method` 分 `GET`（2 条）与 `POST`（4 条）。
- **`.effective` 判定表（在盘原文 `registry-entries.md` L232-235）**：
  - `GET` 只读 → **True**（3 条，flow 全域）：`udc.flow.function_node_tree`、`udc.flow.data_flow_map_get_by_id`、`udc.flow.data_flow_mapping_get_by_id`
  - `POST` 读型（`write=False`）→ **False**（6 条，flow 全域）：含本族 4 条 `data_flow_map_search` / `data_flow_mapping_search_original` / `…_init_data` / `…_detail`
  - 写型（`write=True`）→ **False**（3 条）：`udc.flow.bpm_fill_error_data`、`udc.flow.data_flow_mapping_update`、`udc.flow.data_flow_mapping_update_state`
  - 同文件 L236 门控说明原文：「POST 只读条目 `.effective=False`，MERGE 时须走与普通只读 POST 相同的 auth_scope 通道，勿依赖 `.effective` 自动放行」。
  - **本族切片**（6 条内）：`GET` 2 条 → True；`POST` 读型 4 条 → False。
- **静态字节码级可构造**：6 条契约的 method/path/入参/响应均来自 javap 与 registry.py 原文（§3 表），可独立复算构造。
- **活体未探测 → `UNVERIFIED`**：本族**无任何 LIVE/活体证据**（实测：`docs/operation-contracts/udc/microflow/live-evidence/` 内零 `data_flow`/`dataflow`/`mapping` 件，
  `docs/operation-contracts/udc/flow/` 下无 live-evidence 目录）。故**运行时行为、响应实体实际取值、鉴权放行实测 = `UNVERIFIED`**；
  禁止以「应为/通常」句式补空。

## 6. Side Effects

- **全只读**：6 条契约 `write=False`；`POST` 4 条为读型（javap 原文 `@PostMapping`，执行链仅放行 `GET`，故在 `PlatformOperationLayer` 为
  `DENIED`/`POLICY_DENIED` —— registry.py L75/L79/L81/L83 evidence `note` 原文，与 C4-C8 同边界）。
- **写侧零启用**：写侧 3 条 `write=True` 仅登记，策略门控未放开（`registry-entries.md` L175 小节标题 + L226 原文「写侧仍 write=True 策略门控未放开（仅登记，不进入只读计数）」）。
- **链路关系不产生运行时副作用**：`module-link-evidence.json` 记录的是**契约引用关系**；同文件 L123 明示「A contract relationship is not a runtime invocation relationship.」（见 §7）。
- **零凭据落盘**：本件只引路径/对象标识/实读值，凭据值 0 入件。
- **目标仓库文件面**：本格仅新增 `core/facts/bpm/data-flow-map.md`；`registry.py`/`layer.py`/`models.py`/tests/冻结件/第 1 格零改动。

## 7. Known Constraints

| 约束 | 后果 | 在盘依据 |
|---|---|---|
| **契约关系 ≠ 运行时调用关系** | 链路面**不得**升级为「UDC 运行时会实际调用 BPM」的行为断言 | `docs/audit/modules/module-link-evidence.json` **L123**（limitations 首条原文） |
| **文件级等级低于关系级等级（如实分列）** | 该证据文件整体 = `PARTIALLY_VERIFIED`；仅 `udc→standard-product` 该条关系为 `VERIFIED_STATIC_BYTECODE` | 同文件 **L3**（`"status": "PARTIALLY_VERIFIED"`）vs **L75**（关系 `status`） |
| **本族零 LIVE** | §5 一切运行时结论留 `UNVERIFIED`，不得外推 | 实测：`docs/operation-contracts/udc/microflow/live-evidence/` 无本族原生件（`ls` 过滤 `data_flow|dataflow|mapping` 计数 = 0）；`docs/operation-contracts/udc/flow/` 无 live-evidence 子目录 |
| **BPM 引擎本体（执行器/模型/调度实现）无在盘证据** | **整段 `UNVERIFIED`**；在盘仅有 UDC↔BPM 门面/链路层件 | `inputs/desktop-source/TASK-GOAL.md` **L6** 原文「边界: 只写 core/facts/bpm/**;禁改运行代码;BPM 引擎本体无证据处整段 UNVERIFIED,禁止外推。」；在盘门面件 = `docs/audit/modules/module-link-evidence.json` + `docs/audit/modules/decompiled/bpm-facade-3.12.101-*.java` |
| **写侧 3 条未放开** | 仅登记，不进只读计数；启用须另行授权 | `registry-entries.md` L175、L226 |
| **同 controller 写端点混列风险** | 读 `detail` = javap **L331**；`L265`=`update`、`L298`=`state` 属写侧，勿误记为读面 | `DataFlowRtMappingController.javap.txt` L265/L298/L331 实测 `value`；`registry-entries.md` L193/L208 |
| **版本纪律** | 相邻版本 `bpm-facade 5.3.374` / `app-approval 5.3.295` 不得作为证据 | `flow-domain-scan.md` **L6**、**L102** |
| **proxy 层透明路径不属本域** | `UdcBaseGeneralController`（runtime/proxy）的 `dataflow/...`、`microflow/...`、`create-bpm`/`update-bpm` 不构成本域只读契约 | `registry-entries.md` **L227**（R7/R8 裁定原文「勿入本域 6 controller 专属只读契约」） |
| **计数纪律** | 本族只读 **6** 条 + 写侧 **3** 条（拟稿）；flow 全域只读 **9** 条；目标文「16 条」实测不成立，禁照抄 | `registry.py` L74/76/78/80/82/84（本族 6）+ L47/L70/L72（其余 3）；`registry-entries.md` L8（只读 9 条标题）+ L175（写侧 3 条标题） |
| **网关 service 前缀 `UNVERIFIED`** | 禁拼前缀当可用 URL | registry.py L73/L75/L77/L79/L81/L83 evidence `note` 均含该约束；`flow-domain-scan.md` L6「未拼网关前缀…逐字保留」 |

## 8. Evidence（逐条在盘路径 + 行号/实读值）

| # | 证据 | 路径 | 关键原文/实测值 |
|---|---|---|---|
| E1 | 本族只读 6 条契约 | `components/platform_operations/registry.py` L74/L76/L78/L80/L82/L84（evidence L73/L75/L77/L79/L81/L83） | 6 条 operation_id + method + path + 入参 + 响应逐字；全 `VERIFIED_STATIC_BYTECODE`、`write=False`、artifact `udc-starter-dataflow-5.3.517.jar` |
| E2 | javap 类级/方法级映射（RtMap） | `docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMapController.javap.txt` | 类声明 L5；`@PostMapping value=["search"]` L126；`@GetMapping value=["{id}"]` L159；类级 `@RequestMapping value=["udc-runtime/data-flow-map"]` L178 |
| E3 | javap 类级/方法级映射（RtMapping） | `docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMappingController.javap.txt` | 类声明 L5；`search-original` L160；`{id}` GET L193；`init-data` L232；`update` L265；`state` L298；`detail` L331；类级 `udc-runtime/data-flow-mapping` L344 |
| E4 | javap（写侧 ForBpm） | `docs/audit/artifacts/udc-flow-5.3.517/DataFlowForBpmController.javap.txt` | 类声明 L5；`@PostMapping value=["fill-data"]` L125；类级 `@RequestMapping value=["udc-runtime/bpm"]` L134 |
| E5 | 类哈希 3 件 | `docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMapController.class.sha256`、`DataFlowRtMappingController.class.sha256`、`DataFlowForBpmController.class.sha256` | `455df593…d1d95`、`ee742c70…531e8`、`8b31f788…ba5e4`（实读，与 registry.py L73/L77 同值） |
| E6 | UDC↔BPM 链路证据 | `docs/audit/modules/module-link-evidence.json` | L3 文件 `PARTIALLY_VERIFIED`；L71-84 关系 `udc→standard-product` / `exposes-platform-runtime-contracts-to` / `VERIFIED_STATIC_BYTECODE`；L85 note；L92-97 `exact_contracts.standard_product` 4 项；L105-111 `exact_methods.standard_product` 5 项；L113-116 outbound 2；L117-119 inbound 1；L123 limitations[0] |
| E7 | BPM 门面反编译件（7 件，`bpm-facade` 3.12.101） | `docs/audit/modules/decompiled/bpm-facade-3.12.101-{BpmUdcApiService,BpmApiProcessAppService,BpmAppService,BpmDeployAppService,BpmSendUdcDto,BpmSaveDraftUdcDto,BpmTriggerFlowUdcRequestDto}.java` | sha256 实测：`BpmUdcApiService` `5028e167…cf64e`（3366 B，interface L45，9 方法 L46-L72）；`BpmApiProcessAppService` `40d07249…c17c3`（781 B）；`BpmAppService` `56275617…944402`；`BpmDeployAppService` `1bb33700…9c159090`；`BpmSendUdcDto` `2929db4b…0ad5ba`；`BpmSaveDraftUdcDto` `e467675e…d12ad8f`；`BpmTriggerFlowUdcRequestDto` `557f1582…98c3dbf` |
| E8 | 反编译 manifest | `docs/audit/modules/decompiled/bpm-api-decompile-manifest.json` | L3 `"artifact": "bpm-facade"`；L4 `"version": "3.12.101"`；L5 `source_sha256=26b312fdd40cc921a4cd8d08239f6b8d857c02a5ac8d4db271d07f6fcbd98af0` |
| E9 | UDC 侧回流反编译件（4 件） | `docs/audit/modules/decompiled/udcrt-5.3.517-{ApproveFeatureService,ApprovalStateChangeListener,UdcBpmProcessService,UdcBpmProcessServiceImpl}.java` | sha256 实测：`f49a8582…7ceb0d`、`15513d47…e06239`、`feeec5ce…d78c474`、`5d324773…430bdb5f` |
| E10 | 写侧登记 + `.effective` 判表 + 域扫 | `docs/operation-contracts/udc/flow/registry-entries.md` L2/L8/L175/L178/L193/L208/L226/L227/L232-235/L236；`docs/operation-contracts/udc/flow/flow-domain-scan.md` L6/L19-23/L34/L40/L46/L92-95/L102 | 写侧 3 条与门控原文；BPM 命中明细（`udc-starter-dataflow(8)`：`DataFlow4BpmReqDto` / `BpmInterfaceService` / `DataFlowForBpmAppServiceImpl` / `DataFlowForBpmAppService` / `DataFlowForBpmController` / `DataFlow4BpmReqMessage` / `DataFlowWithBpmListener` / `DataFlow4BpmReqRetryDelayMessage`，OBSERVATION 级） |
| E11 | 任务边界（引擎本体 UNVERIFIED） | `inputs/desktop-source/TASK-GOAL.md` L6 | 「边界: 只写 core/facts/bpm/**;禁改运行代码;BPM 引擎本体无证据处整段 UNVERIFIED,禁止外推。」 |

## 9. Verified（逐项证据等级 + 未直读项）

| 项 | 等级 | 依据 |
|---|---|---|
| 本族 6 条契约登记（method/path/入参/响应/status/write） | **VERIFIED_STATIC_BYTECODE** | E1（registry.py L74-L84 原文） |
| 类级 + 方法级映射原文（path 全段可构造；含 `detail` 实测 L331） | **VERIFIED_STATIC_BYTECODE** | E2/E3（javap 实测行） |
| 类哈希 3 件 | **VERIFIED_STATIC_BYTECODE** | E5（`.class.sha256` 实读，与 E1 同值） |
| UDC↔BPM「契约暴露」关系（4 契约 + 5 方法 + outbound 2 + inbound 1） | **VERIFIED_STATIC_BYTECODE**（关系级） | E6（module-link-evidence.json L71-119）；**文件级整体 = PARTIALLY_VERIFIED（如实分列）** |
| BPM 门面反编译类结构与方法签名（`BpmUdcApiService` 等） | **静态反编译（STATIC，3.12.101）** | E7/E8（逐件 sha256 实读 + manifest） |
| UDC 侧回流实现件（`UdcBpmProcessServiceImpl` 等） | **静态反编译（STATIC，5.3.517）** | E9（逐件 sha256 实读） |
| dataflow 侧 BPM 外观类（`DataFlow4BpmReqDto` 等 8 件） | **OBSERVATION 级（jar tf 命中，未升为行为断言）** | E10（flow-domain-scan.md L19-23） |
| 本族运行时行为 / 响应实体实际取值 / 鉴权放行实测 | **UNVERIFIED**（无 LIVE 件，未探测） | 实测：本族零 live-evidence（见 §7 第 3 行） |
| 网关 service 前缀本身（可拼接性） | **UNVERIFIED** | E1（6 条 evidence `note` 均明示禁拼前缀）；E10（flow-domain-scan.md L6） |
| 写侧 3 条（`bpm_fill_error_data` / `…_update` / `…_update_state`） | **仅登记，未启用**（`write=True`，执行层 `POLICY_DENIED`） | E10（registry-entries.md L175/L226）；E4（javap L125/L134） |
| **BPM 引擎本体**（执行器 / 模型 / 调度实现） | **UNVERIFIED（整段）** | E11（TASK-GOAL.md L6）；在盘仅门面/链路层件（E6/E7/E9） |

> **收口**：第 2 格已按九段式落盘，逐段锚定在盘 STATIC 实据；**本族零 LIVE → §5/§9 运行时结论一律 `UNVERIFIED`，未以「应为/通常」补空**；
> BPM 引擎本体整段 `UNVERIFIED`，链路面仅按「契约关系」陈述（未升级为运行时调用断言）。
> 第 1 格 `flow-node-tree.md` 已冻结未动；`core/facts/INDEX.md` 待主线收口时更新（本轮未动）。

---

## 溯源索引（可复现）

| 段 | 在盘来源 |
|---|---|
| Capability / Version | `components/platform_operations/registry.py` L73-L84；`docs/audit/artifacts/udc-flow-5.3.517/*.class.sha256`；`docs/audit/modules/decompiled/bpm-api-decompile-manifest.json` L3-L5；`docs/operation-contracts/udc/flow/flow-domain-scan.md` L6/L102 |
| Input / Required | `registry.py` L73-L84；javap `DataFlowRtMapController` L126/L159/L178、`DataFlowRtMappingController` L160/L193/L232/L265/L298/L331/L344、`DataFlowForBpmController` L125/L134 |
| Execution | `components/platform_operations/models.py` L47-49；`docs/operation-contracts/udc/flow/registry-entries.md` L232-236；实测零 live-evidence（`docs/operation-contracts/udc/microflow/live-evidence/`） |
| Known Constraints | `docs/audit/modules/module-link-evidence.json` L3/L75/L123；`registry-entries.md` L175/L226/L227；`flow-domain-scan.md` L6/L102；`inputs/desktop-source/TASK-GOAL.md` L6 |
| Evidence / Verified | E1-E11（上表逐条路径） |
