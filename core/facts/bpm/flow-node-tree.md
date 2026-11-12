# udc.microflow.function_node_tree｜微流程函数节点树读取（flow 域第 1 格）

> 基线：本任务 TASK-GOAL（`事实模块任务｜BPM-flow(flow 域 16 契约+微流程)`）+ 本会话 `main/ROUTE.md` @ 目标仓库
> `<XIAOZHUA_AGENT_ROOT>` HEAD `16a384c`。九段式能力事实文档（交付物第 1 件，`core/facts/bpm/flow-node-tree.md`），
> 节序照在盘样板 `core/facts/udc/entity/create.md`（B1 样板格，PASS）。
> 本件**只做 `udc.microflow.function_node_tree` 一格**；第 2 格 `data-flow-map.md` 本轮不建、不写。
> 只写事实文档，不实现代码、不改 `components/**`；凭据值 0 入件（仅引对象标识/证据等级）。

---

## 1. Capability

**`udc.microflow.function_node_tree`** — 读指定应用的**微流程函数节点树**元数据（只读 GET 读面）。
- **类型**：READ 型（契约 `write=False`、`method=GET`；agent 侧可走读门，写门不涉及）。
- **位置**：`components/platform_operations/registry.py` **L47**（在盘实测原文）注册为 `UdcOperationContract`；
  evidence 字典同族见 **L46**。执行边界 = `PlatformOperationLayer`（唯一执行边界）。
- **语义**：按 `appName` 返回该应用的函数节点树数组（节点含 `id`/`children`/`code` 结构字段，见 §5 LIVE）。
  `children`/`code` 的**业务语义 = UNVERIFIED**（不在本格断言，见 §7）。

## 2. Version

- **Canonical = 5.3.517**。artifact `udc-starter-runtime-5.3.517.jar`（registry.py L46 evidence.artifact）。
- 类：`com.seeyon.boot.starter.udcrt.controller.UdcFunctionNodeController`
  （javap 头行 `public class …UdcFunctionNodeController extends com.seeyon.boot.starter.web.BaseComponentController`）。
- **class_sha256 = `efd8f9143d0fd44d4e3033a4bb4877c09e891a1049f66382df1ae1d7d08a7748`**
  （在盘实测文件 `docs/audit/artifacts/udc-flow-5.3.517/UdcFunctionNodeController.class.sha256` 全文即此值，66B；与 registry.py L46 同值）。
- **版本分列（不混写）**：本地静态 = 5.3.517（`registry.py` 契约 + javap）；test2 部署态按
  `docs/operation-contracts/udc/microflow/live-evidence/a2_live_pass_R21_20260920T113816Z.md` L8 记
  `udc-starter-runtime-5.3.517.jar sha8=74ae50bd`（部署态胖包 javap 印证同版本族）；客户侧 `1.0.11133` **分列未混写**（同报告 L23）。
- **Adapter 未建 → 其他版本 UNVERIFIED**（无在盘 UDC 证据，不推版本分支）。

## 3. Input

**method = `GET`**；**path = 类级映射 + 方法级映射逐字拼接，不拼网关前缀**：

| 段 | 原文 | 在盘锚点 |
|---|---|---|
| 类级 | `@RequestMapping(value=["udc-runtime/meta-data"])` | javap L121-124（`RuntimeVisibleAnnotations` → `RequestMapping`，精确边界） |
| 方法级 | `@GetMapping(value=["select-function-node-tree/{appName}"])` | javap L108-111（精确边界） |
| 契约 path（全段） | `udc-runtime/meta-data/select-function-node-tree/{appName}` | `registry.py` L47（逐字） |

- **入参**：`String appName`（PathVariable，`@PathVariable` 运行时可见注解见 javap L112-116 参数注解段；
  参数表 `0 12 1 appName Ljava/lang/String;` L101）。
- **响应**：`ListResponse<UdcFunctionNodeMetadataDto>`
  （javap `Signature: #23 // (Ljava/lang/String;)Lcom/seeyon/boot/transport/ListResponse<Lcom/seeyon/udc/common/dto/UdcFunctionNodeMetadataDto;>;`；
  后端调用 `UdcFunctionNodeAppService.selectFunctionNodeTreeMetaData:(Lcom/seeyon/boot/transport/SingleRequest;)Lcom/seeyon/boot/transport/ListResponse;` javap L16/L94）。
- **registry 声明形态**：`request_type="String appName(SingleRequest)"`、`response_type="ListResponse<UdcFunctionNodeMetadataDto>"`（L47 原文）。

## 4. Required（必填链与缺省推断）

- **必填**：`appName` —— `registry.py` L47 `required_inputs=("appName",)`；javap 方法仅 1 个 `String` 形参且标注 `@PathVariable`。
- **实测 target 形态**：活体 full path 为
  `/service/udc/udc-runtime/meta-data/select-function-node-tree/app9000000000000000001`
  （应用名 token = 必需槽位；a2 报告 L14）。
- **缺省推断**：**无**（本契约无缺省/可省略项，不臆造替代值）。
- **verification_rules（registry 原文）**：`("同一 appName 回读节点树 identity_matches", "响应非空 UdcFunctionNodeMetadataDto 列表")`（L47）。

## 5. Execution

- **读门放行条件（在盘实测定义）**：`components/platform_operations/models.py` L47-49
  `effective = status ∈ {PASS, VERIFIED_STATIC_BYTECODE, OBSERVED} and not write and method.upper()=="GET"`。
  本契约三值 = `status=VERIFIED_STATIC_BYTECODE`、`write=False`、`method=GET`（registry.py L47）
  → **`.effective=True`**（读面可放行的一类），仍须 `auth_scope` 含 `<appId>:readonly`
  （`docs/plans/2026-09-17-microflow-readonly-milestone.md` L11 执行边界描述）。
- **完整活体路由**：`/service/{gateway_service=udc}` + 契约 path 原文（a2 报告 L10 实证）。
- **LIVE 双发回读（R21，同一 target）**：`f1 HTTP=200 f2 HTTP=200 business_code=BOOT_0000 status=0`；
  `normalized_sha(f1)=normalized_sha(f2)=26ceca1edc115505`；`identity_matches=TRUE`；
  `data.content = 函数节点树 23 节点`；首节点 identity `f1.id=f2.id=23088985804278345`（a2 报告 L15-18）。
- **本轮实施者独立重算（非转述）**：对两个原生件按「递归剔除 `traceId` + `sort_keys` + `json.dumps(ensure_ascii=False)` 默认分隔 + sha256 前 16」重算，
  得 `26ceca1edc115505`（**与报告同值命中**），f1==f2 相等=TRUE；`code=BOOT_0000`、`status=0`、`len(content)=23`、
  `first_id=23088985804278345`（f1/f2 一致）。原始字节并**不相同**（raw_sha256_16 = `2a40e10f6c2305e5` / `86d40a1735f72bff`，各 187981B），
  差异即 `traceId` 与时间类字段——**identity 判据成立、非字节相等**。
- **09-25 再次 LIVE（本批原料）**：`core/facts/udc/readonly-faces-batch2.md` L11/L20 记
  `udc.microflow.function_node_tree | GET /udc-runtime/meta-data/select-function-node-tree/{app}` →
  `BOOT_0000，节点树数组（id=23088985804278345…children/code 结构）`，`traceId 3247010162132650172`；该次为**单发探测**（非双发），见 §9 等级分列。

## 6. Side Effects

- **全只读**：`write=False`、`method=GET`；无写/发布/部署/DB/Redis/缓存变更。
- **零凭据落盘**：R21 红线记载「全程只读 GET；token 明文零落盘（脱敏前 8 `eyJ0eXAi…`）」（a2 报告 L25）；
  本件凭据值 0 入件，只引对象标识与证据等级。
- **节点树字段不做语义解释**：返回体 `children`/`code` 仅作结构登记，其业务含义不因本契约产生副作用断言（→ UNVERIFIED）。
- 目标仓库文件面：本格仅新增 `core/facts/bpm/flow-node-tree.md`，`registry.py`/`layer.py`/tests/冻结件零改动。

## 7. Known Constraints

| 约束 | 后果 | 在盘依据 |
|---|---|---|
| **跨域重叠（必标）**：`udc.flow.function_node_tree` 与 `udc.microflow.function_node_tree` **同 controller + 同 method + 同 class_sha256 `efd8f914…a7748`** | UDC-MERGE **去重归一、删一留一**；本轮**不得新增第二个 operation_id**、**不得改 `registry.py`（冻结件）** | `docs/operation-contracts/udc/flow/registry-entries.md` **L29-47（§2 标题行 L29 + 合并说明 L30）**；`registry.py` L47；`…/UdcFunctionNodeController.class.sha256` |
| **计数纪律**：目标文写「flow 族 16 条」**不成立** | 格内只写实测枚举，**禁照抄 16** | `registry.py` **实测只读 flow/microflow = 9 条**：L47 `udc.microflow.function_node_tree`、L70 `udc.flow.bpm_node_info_search`、L72 `udc.flow.form_data_query`、L74 `udc.flow.data_flow_map_get_by_id`、L76 `udc.flow.data_flow_map_search`、L78 `udc.flow.data_flow_mapping_get_by_id`、L80 `udc.flow.data_flow_mapping_search_original`、L82 `udc.flow.data_flow_mapping_init_data`、L84 `udc.flow.data_flow_mapping_detail`；拟稿侧 `registry-entries.md` **L8 只读 9 条 + L175 写侧 3 条（未进 registry.py）**。两套 9 条逐一对应，唯一命名差异即本行的 function_node_tree（registry.py 记 `microflow.`、拟稿记 `flow.`） |
| **负证据（如实）**：漏类级前缀 → 404 | 完整活体路由必须**带 `udc-runtime/meta-data` 类级段** | `docs/operation-contracts/udc/microflow/live-evidence/C1_node_tree_f1_20260920T071611Z.json`（275B，本轮直读原文 = Whitelabel Error Page + `status=404`）；a2 报告 L6-11 |
| **网关 service 前缀 `UNVERIFIED`** | 禁止把前缀拼成「可用 URL」；完整路由只写「`/service/{gateway_service=udc}` + path 原文」的实证形态 | a2 报告 L10；`registry.py` 同族契约（除本条 L47 外）`verification_rules` 一律含「网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）」 |
| **javap 双副本并存** | 引用时须指明副本 | `docs/audit/artifacts/udc-flow-5.3.517/UdcFunctionNodeController.javap.txt`（8067B，sha256 `7fa7876d…4041`，**本格锚点**）vs `docs/audit/artifacts/udc-runtime-5.3.517/UdcFunctionNodeController.javap.txt`（8183B，sha256 `9eca1bd9…4040`）。`diff` 实测 22 行差异（jar URI `<MAVEN_REPO>` vs `<PATH> + 中文常量编码形态），两副本同记 `size 1844 bytes`；`registry.py` L46 evidence.javap 指向 **udc-runtime** 副本、拟稿 L43 指向 **udc-flow** 副本 → **MERGE 时归一**；字节级锚点以 `class_sha256=efd8f914…a7748` 为准 |
| **同域邻接（仅一行登记，不展开）** | 只作同域事实，不作本格结论 | `udc.flow.bpm_node_info_search`：POST、path `node-info/search`、artifact `udc-starter-customplan-5.3.517.jar`、`class_sha256=95e1752d…5bb2`、javap 原文 `@PostMapping` → 执行链仅放行 GET ⇒ `POLICY_DENIED`（`registry.py` **L69-70**） |
| **不承载引擎断言** | 整段 `UNVERIFIED`，禁外推 | 微流程**运行时行为**、**BPM 引擎本体（执行器/模型/调度实现）**：无在盘证据；在盘仅有 UDC↔BPM 门面/链路层件（`docs/audit/modules/module-link-evidence.json` status=PARTIALLY_VERIFIED；`docs/audit/modules/decompiled/bpm-facade-3.12.101-*.java`；`docs/audit/modules/decompiled/udcrt-bpm-link-decompile-manifest.json`），归第 2 格原料；依据=在盘任务边界 `inputs/desktop-source/TASK-GOAL.md` L6「边界: 只写 core/facts/bpm/**;禁改运行代码;BPM 引擎本体无证据处整段 UNVERIFIED,禁止外推。」 |

## 8. Evidence（逐条在盘路径）

| # | 证据 | 路径 | 关键原文/实测值 |
|---|---|---|---|
| E1 | 契约登记 | `components/platform_operations/registry.py` L46-47 | `udc.microflow.function_node_tree`, GET, `udc-runtime/meta-data/select-function-node-tree/{appName}`, `VERIFIED_STATIC_BYTECODE`, `write=False` |
| E2 | 字节码 javap（本格锚点副本） | `docs/audit/artifacts/udc-flow-5.3.517/UdcFunctionNodeController.javap.txt` | 类级 `@RequestMapping(value=["udc-runtime/meta-data"])`（L121-124）；方法级 `@GetMapping(value=["select-function-node-tree/{appName}"])`（L108-111）；签名 L85；`@PathVariable` L112-116 |
| E3 | 类哈希 | `docs/audit/artifacts/udc-flow-5.3.517/UdcFunctionNodeController.class.sha256` | `efd8f9143d0fd44d4e3033a4bb4877c09e891a1049f66382df1ae1d7d08a7748` |
| E4 | LIVE 双发报告（R21） | `docs/operation-contracts/udc/microflow/live-evidence/a2_live_pass_R21_20260920T113816Z.md` | HTTP200×2 / `BOOT_0000` / `identity_matches=TRUE` / `normalized_sha=26ceca1edc115505` / 23 节点 / 首节点 `23088985804278345` / 部署态 jar `sha8=74ae50bd` |
| E5 | LIVE 原生件 ×2 | 同目录 `udc_microflow_c1_function_node_tree_f1_20260920T113816Z.json`、`_f2_…json` | 各 **187981B**；raw_sha256_16 = `2a40e10f6c2305e5` / `86d40a1735f72bff`；**本轮独立重算 norm_sha16 = `26ceca1edc115505`（两件相等）** |
| E6 | 09-25 运行态四格（本批原料） | `core/facts/udc/readonly-faces-batch2.md` L11、L20 | `BOOT_0000`，节点树数组 `id=23088985804278345…children/code`，`traceId 3247010162132650172`（该批 4 个 traceId 之一） |
| E7 | 负证据（404） | `…/live-evidence/C1_node_tree_f1_20260920T071611Z.json` | 275B，直读 = `Whitelabel Error Page … status=404` |
| E8 | 跨域重叠/MERGE 口径 | `docs/operation-contracts/udc/flow/registry-entries.md` | §2 L29-30（同 controller+method+class_sha256，删一留一）；L8 只读 9 条；L175 写侧 3 条；L236 POST 只读条 `.effective=False` 门控说明 |
| E9 | 执行边界/放行条件 | `components/platform_operations/models.py` L47-49；`docs/plans/2026-09-17-microflow-readonly-milestone.md` L11、L34-39（A1–A6 验收条目）、L43/L46（P1/P4 取证顺序） | `effective` 定义；「只在契约生效 + method=GET + write=false + auth_scope 含 `<appId>:readonly` 时放行」（plan L11）；微流程只读族来源 P1/P4（plan L43/L46） |

## 9. Verified（逐项证据等级 + 未直读项）

| 项 | 等级 | 依据 |
|---|---|---|
| 契约登记（method/path/request/response/status/write/required_inputs） | **VERIFIED_STATIC_BYTECODE** | E1（registry.py L46-47 原文） |
| 类级 + 方法级映射原文（path 全段可构造） | **VERIFIED_STATIC_BYTECODE** | E2（javap L108-111 / L121-124） |
| 类字节码哈希 `efd8f914…a7748` | **VERIFIED_STATIC_BYTECODE** | E3（sha256 文件实读，与 E1 同值） |
| 同一 target 双发回读 `identity_matches=TRUE` + 非空业务对象（23 节点） | **LIVE** | E4 + **E5 本轮独立重算命中同一 norm_sha16（非转述）** |
| 09-25 单发探测 `BOOT_0000` + 节点树数组 | **LIVE（单发）** | E6（`traceId 3247010162132650172`；**非双发，不作同一 target 双发判据**） |
| 完整活体路由 = `/service/{gateway_service=udc}` + path 原文 | **LIVE**（路由形态实证） | E4（L10）；`gateway_service=udc` 取值来自该活体 target 原文 |
| 网关 service 前缀本身（可拼接性） | **UNVERIFIED** | E1/E8 同族 `verification_rules` 明示禁拼前缀 |
| 节点树 `children`/`code` 的业务语义 | **UNVERIFIED**（未直读语义层） | E6 仅结构登记 |
| 微流程运行时行为（调度/执行/流转） | **UNVERIFIED** | 无在盘证据；本批原料明示不外推 |
| **BPM 引擎本体**（引擎实现、模型、执行器） | **UNVERIFIED（整段）** | 在盘任务边界 `inputs/desktop-source/TASK-GOAL.md` L6「BPM 引擎本体无证据处整段 UNVERIFIED,禁止外推」；在盘仅 UDC↔BPM 门面/链路层件（`docs/audit/modules/module-link-evidence.json` status=PARTIALLY_VERIFIED / `bpm-facade-3.12.101` 反编译），引擎执行器/模型/调度实现零证据；`node-info` 族仅同域邻接 |

> **收口**：第 1 格已按九段式落盘，逐段锚定在盘 STATIC/LIVE 实据；LIVE 主判据（双发 identity）由本轮实施者独立重算复核，
> 非引用转录。**未直读项（引擎本体、运行时行为、字段业务语义、网关前缀）如实标 `UNVERIFIED`，不臆造、不外推。**
> 第 2 格 `data-flow-map.md` 归 HANDOFF-2，本件不扩散；`core/facts/INDEX.md` 待主线收口时更新（本轮不动）。

---

## 溯源索引（可复现）

| 段 | 在盘来源 |
|---|---|
| Capability / Version | `components/platform_operations/registry.py` L46-47；`docs/audit/artifacts/udc-flow-5.3.517/UdcFunctionNodeController.class.sha256` |
| Input / Required | `registry.py` L47；javap L85/L100-116/L121-124 |
| Execution | `models.py` L47-49；`docs/plans/2026-09-17-microflow-readonly-milestone.md` L11；a2 报告 L10-19；本轮独立重算脚本 `implementer/verify_live_sha16.py`（会话目录） |
| Known Constraints | `registry-entries.md` L8/L29-30/L175/L236；负证据 JSON（275B）；`registry.py` L69-70 |
| Evidence / Verified | E1-E9（上表逐条路径） |
