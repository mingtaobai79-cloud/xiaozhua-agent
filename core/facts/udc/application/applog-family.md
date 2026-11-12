# udc.applog｜应用日志能力族（九段式事实格 · S4）

> 基线：registry `udc.applog.*` 6 条契约登记（L52 / L64 / L66 / L68 / L104 / L106）+ 在盘 LIVE 记录 2 条（E2 行 2/行 3，离线窗口 09-18 已过期）+ 微流程负证据 6 件（E8，均为 404）+ menu 域 2 别名权威出处（E6）。
> 段序与 B1 样板格 `core/facts/udc/entity/create.md` 一致；本件**只做 applog 域非写面**，
> draft 两条归 S2（已完成）、application get/search/deploy_info 归 S3（已完成）；**applog 写端点仅注记、不入格、不计数**。
> 只写事实文档，不改 `registry.py`/`components/`/`docs/`；网关与凭据只写 config 键，值 0 入件；**不联网、不运行期复现**。
> 仓库 `<XIAOZHUA_AGENT_ROOT>`，实测 HEAD `16a384c`（本件写前 git 状态：**clean tree**，`git status --porcelain` 0 行，冻结件 S1/S2/S3 四件哈希与 ROUTE 绑定一致）。

---

## 1. Capability

| operation_id（registry 名） | HTTP | 控制器原路径（逐字） | 入参 | 响应 | 写门判定（STATIC，§5） |
|---|---|---|---|---|---|
| `udc.applog.select_by_id` | GET | `udc-runtime/app-log/datalog/{id}` | `Long id`（SingleRequest 包裹） | `SingleResponse<UdcEntityMonitorLogDto>` | GET + ¬write → **effective=True**，通过写门 |
| `udc.applog.search_microflow` | POST | `udc-runtime/app-log/search/microflow` | `PageDtoRequest<MicroFlowLogSearchDto>`（RequestBody） | `PageResponse<MicroFlowLogResultDto>` | POST → **effective=False** → `DENIED/POLICY_DENIED` |
| `udc.applog.search_details_microflow` | POST | `udc-runtime/app-log/search-details/microflow` | `PageDtoRequest<MicroFlowLogDetailsSearchDto>`（RequestBody） | `PageResponse<MicroFlowLogDetailsResultDto>` | POST → **effective=False** → `DENIED/POLICY_DENIED` |
| `udc.applog.search_details_microflow_flowlog` | POST | `udc-runtime/app-log/search-details/microflow/flowLog` | `MicroFlowLogDetailsSearchDto`（RequestBody，**非** PageDtoRequest 包裹） | `SingleResponse<MicroFlowFlowLogResultDto>` | POST → **effective=False** → `DENIED/POLICY_DENIED` |
| `udc.applog.list_app_data_by_dataid` | GET | `udc-runtime/app-log/datalog/list-by-dataid/{dataId}` | `Long dataId`（PathVariable） | `ListResponse<UdcEntityMonitorLogDto>` | GET + ¬write → **effective=True**，通过写门 |
| `udc.applog.search_app_data_log` | POST | `udc-runtime/app-log/datalog/search` | `PageRequest(page,size)` | `PageResponse<UdcEntityMonitorLogDto>` | POST → **effective=False** → `DENIED/POLICY_DENIED` |

- **同控制器写端点（仅注记、不入格、不计数）**：`createBatch`（javap L436 + L464 `@PostMapping`）、
  `searchDataFlow`（L575 + L602 `value=["search/dataflow"]`）、`searchDataFlowDetails`（L610）、
  `searchDeduction` / `searchDeductionDetails`（L645/L680）、及 registry 未纳的 `delete_all` / `clear_org_manager` / `clear_runtime_data_source` / `set_rest_enable_log` / `unload_dynamic_app`（E7 `test_datatype_applog_readonly.py` L94-95 排除断言 5 条写侧）——**均非本域只读能力，不建条目、不计入 6 条计数**。

## 2. Version

- Canonical = **5.3.517**（registry 证据 dict 逐字：`artifact=udc-starter-runtime-5.3.517.jar`，`version=5.3.517`，E1 L51/L63/L65/L67/L103/L105 全源同值）。
- class_sha256（字节码类指纹，6 条共用）：`f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775`
  （`com.seeyon.boot.starter.udcrt.controller.UdcAppLogController`，E1 L51 逐字）。
- **javap 文本件 sha256（两份非等价，分开登记，同 S1/S2 纪律）**：
  | 副本 | 字节 | sha256 |
  |---|---|---|
  | `docs/audit/artifacts/udc-menu-5.3.517/UdcAppLogController.javap.txt` | **80629 B** | `ebca5ad0f990037134c6bd1819ee3e6ada41fdddf73aa19aed170e46759171c5` |
  | `docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt` | **80367 B** | `0e74f6de26b9f1299895f901b1c3c659b94b5a615085edd62377712665063abd` |

  两份字节不同 → **非等价**，引用时**分开登记、不得互替**（spec §2 E3 口径）。

## 3. Input

- `select_by_id`：`Long id`（路径变量 `datalog/{id}`；E1 L52 `request_type="Long id(SingleRequest)"`，E4 P2 契约 L6 javap 原值 `@GetMapping(value=["datalog/{id}"])` + 类级 `@RequestMapping(value=["udc-runtime/app-log"])`）。
- `search_microflow` / `search_details_microflow` / `search_details_microflow_flowlog`：均为 `PageDtoRequest<...SearchDto>` / 裸 `...SearchDto`（RequestBody；E1 L64/L66/L68 + E3 javap 方法签名 L472/L507/L542 + `@PostMapping` 注解 L499/L534/L567）。
- `list_app_data_by_dataid`：`Long dataId`（PathVariable `datalog/list-by-dataid/{dataId}`；E1 L104，E5 P3 契约 L6 javap 原值）。
- `search_app_data_log`：`PageRequest(page,size)`（RequestBody；E1 L106，E3 javap L715 `searchAppDataLog(PageRequest)` + L740 `value=["datalog/search"]`）。
- **LIVE 实测入参（E2 行 2/行 3，09-18 窗口内）**：`select_by_id` 用 `id=1`（占位）；`list_app_data_by_dataid` 用 `dataId=1`（占位）。**占位 id 的业务含义 UNVERIFIED**（行 2 的 107 B 响应体未展开、行 3 的 598076 B 大响应未落格，§7）。

## 4. Required（必填链与缺省推断）

- registry 声明（E1 实测）：`select_by_id` → `("id",)`；`search_microflow` → `("MicroFlowLogSearchDto",)`；
  `search_details_microflow` → `("MicroFlowLogDetailsSearchDto",)`；`search_details_microflow_flowlog` → `("MicroFlowLogDetailsSearchDto",)`；
  `list_app_data_by_dataid` → `("dataId",)`；`search_app_data_log` → `("PageRequest(page,size)",)`。
- 缺省值：全部 6 条**未观测**缺省行为 → **UNVERIFIED**，不外推。
- 网关前缀：6 条 verification_rules 第三条均为 **UNVERIFIED（离线不可确证，禁止拼前缀）**（E1 L52/L64/L66/L68 逐字；L104/L106 省略第三条，等价默认）。
- **microflow 三条的第三条规则（逐字引 E1 L64/L66/L68 note 字段）**：
  「运行态需确证该 POST 端点为只读读面（不强行升 GET；执行层放行前维持 POLICY_DENIED）」→ **写门维持 POLICY_DENIED，不因「语义只读」而升为 GET**。

## 5. Execution

- 路径组装（**键组装，禁写字面**）：
  - `select_by_id` = `{config键 gateway_base}/service/{app_id}/udc-runtime/app-log/datalog/{id}`
  - `search_microflow` = `{config键 gateway_base}/service/{app_id}/udc-runtime/app-log/search/microflow`
  - `search_details_microflow` = `{config键 gateway_base}/service/{app_id}/udc-runtime/app-log/search-details/microflow`
  - `search_details_microflow_flowlog` = `{config键 gateway_base}/service/{app_id}/udc-runtime/app-log/search-details/microflow/flowLog`
  - `list_app_data_by_dataid` = `{config键 gateway_base}/service/{app_id}/udc-runtime/app-log/datalog/list-by-dataid/{dataId}`
  - `search_app_data_log` = `{config键 gateway_base}/service/{app_id}/udc-runtime/app-log/datalog/search`
- **写门判定（等级 = STATIC，本格不联网、不做运行期复现，引源码）**：
  `components/platform_operations/models.py` L46-48：`effective = status ∈ {PASS, VERIFIED_STATIC_BYTECODE, OBSERVED} ∧ ¬write ∧ method == "GET"`；
  `components/platform_operations/layer.py` L22-23：命中 `write or method != "GET" or not effective` → `DENIED` / `POLICY_DENIED`。
  | op | method | write | effective（按 L46-48） | agent 侧结论 |
  |---|---|---|---|---|
  | `select_by_id` | GET | False | **True** | 通过写门；仍受 auth_scope 约束（layer.py L24-25）；LIVE 证据见 §9 |
  | `search_microflow` / `search_details_microflow` / `search_details_microflow_flowlog` / `search_app_data_log` | POST | False | **False** | **DENIED / POLICY_DENIED**（只能宿主授权执行） |
  | `list_app_data_by_dataid` | GET | False | **True** | 通过写门；LIVE 证据见 §9 |

- **运行期复现**：本动作**未联网、未运行期复现**（S4 spec §4 明确禁 `python -c` 内联、禁新建探针；如需复现只可静态引模型源码或复用既有脚本，本轮未执行）→ 写门等级**仅 STATIC**，不得标 LIVE。

## 6. Side Effects

- 注册侧：6 条 `write=False`（E1 L52/L64/L66/L68/L104/L106 逐字）。
- 语义侧：6 条均为**只读**（检索/读取类操作；E4/E5 契约均明记「仅只读 GET / POST，不写」；E7 排除断言把写侧 5 条**明确分离**）。
- agent 侧：POST 四条因 `POLICY_DENIED` **不产生任何副作用**；两条 GET 通过写门但**本轮未发起**（不联网）→ agent 侧无副作用可报。
- 宿主侧副作用：**未观测 → UNVERIFIED**（本格 LIVE 证据均为 09-18 离线窗口记录，本轮未复跑）。

## 7. Known Constraints

- **网关 service 前缀 UNVERIFIED**（6 条同口径，E1 第三条规则）。
- **`search_details_microflow_flowlog` 请求形态特殊**：请求为**裸 `MicroFlowLogDetailsSearchDto`（RequestBody）**，**非** `PageDtoRequest` 包裹（E1 L67 note 字段逐字）；响应 `SingleResponse`（非分页）——与同族另两条（PageResponse）**不同形态，并列登记、不归一**。
- **microflow 三条「只读语义但 POST 动词」**：执行链仅放行 GET → 维持 `POLICY_DENIED`（E1 L64/L66/L68 note 字段逐字）；**不因语义只读而升 GET**。
- **大响应不落格（E2 行 3）**：`list_app_data_by_dataid` LIVE 响应 **598076 B**——引用只写字节数与 envelope，**列内容不落格**（避免把业务数据抄进事实格，spec §3 硬口径）。
- **占位 id / 大响应的业务内容 UNVERIFIED**：行 2（107 B）与行 3（598076 B）的响应体内容均未展开、未复核 → **UNVERIFIED**。
- **E2 离线窗口已过期**：`LIVE-readback.md` 行 3 原文「窗口: 2026-09-18…本回读于窗口内完成，现已过期作废——本文档为离线结果记录，不再复跑」→ 行 2/行 3 的 LIVE 均为**离线记录，本轮未联网**。
- **写端点排除项**（§1 末）：`createBatch` / `searchDataFlow*` / `searchDeduction*` / `delete_all` 等 5 条写侧**不入格、不计数**（E3 javap + E7 test_datatype_applog_readonly.py L94-95 排除断言）。

## 8. Evidence（逐条实测复核；禁转述）

| # | 路径（在盘实测） | 实测要点 |
|---|---|---|
| E1 | `components/platform_operations/registry.py`（**51734 B**）L52 / L64 / L66 / L68 / L104 / L106（+ L51/L63/L65/L67/L103/L105 证据 dict） | 6 条契约登记 + 逐条独立 evidence dict（microflow 三条各 note 字段记 POLICY_DENIED 维持口径）；`grep -c 'contracts\["udc\.applog' = 6`（§8.1） |
| E2 | `docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md`（**5810 B**）行 3 / 行 25（表 2 行）/ 行 26（表 3 行） | **本格唯一 LIVE**：行 25 `udc.applog.select_app_data_by_id`（别名）GET `.../app-log/datalog/1` → **200 / 107 B / BOOT_0000 / SUCCESS / 二次 identity MATCH**；行 26 `udc.applog.list_app_data_by_dataid` GET `.../list-by-dataid/1` → **200 / 598076 B / BOOT_0000 / SUCCESS / MATCH**。行 3 明记**离线窗口 09-18 已过期，本轮不复跑** |
| E3 | `docs/audit/artifacts/udc-menu-5.3.517/UdcAppLogController.javap.txt`（**80629 B** / `ebca5ad0…`）+ `docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt`（**80367 B** / `0e74f6de…`） | **两副本字节不同 → 非等价**；menu 副本 L472/L507/L542/L715/L740/L773/L786/L812（方法签名与 `@PostMapping`/`@GetMapping` 值）；entity 副本 L26-28/L151/L158/L168/L249-251/L712（同方法名对应常量池 + 方法体）——**分开登记、禁互替** |
| E4 | `docs/operation-contracts/udc/menu/P2-udc-applog-datalog-get-by-id.md`（**3190 B**） | `datalog/{id}` 面契约；L11 明记「**P2 复用 registry L52 `udc.applog.select_by_id`**（本轮 grep 实测在 L52）, 同路径/同 controller/同 method, MERGE 时 P2 **不新增条目** 直接复用（见 registry-entries.md L16）」——**「名字不同、同端点」权威出处之一** |
| E5 | `docs/operation-contracts/udc/menu/P3-udc-applog-datalog-list-by-data-id.md`（**2904 B**）L1/L5/L6/L7 | `list-by-dataid` 面契约；operation_id = `udc.applog.datalog_list_by_data_id`（P3 名，与 registry L104 `udc.applog.list_app_data_by_dataid` **同路径同族、名字不同 → 别名只注记不重复计数**，E6 L53 权威出处） |
| E6 | `docs/operation-contracts/udc/menu/registry-entries.md`（**13162 B**）L16 / L26 / L27 / L37 / L53 | **别名判定权威出处**：L16 P2 去重目标（`udc.applog.select_by_id` 复用）；L26/L27 P3 唯一性（`udc.applog.datalog_list_by_data_id` 实测**仍唯一，可新增**）；L53 P3 契约登记（`datalog/list-by-dataid/{dataId}`） |
| E7 | `tests/test_applog_microflow_readonly.py`（**7037 B**）+ `tests/test_datatype_applog_readonly.py`（**4241 B**）L29/L59/L94-95 | microflow 族入库断言（6 条）；**排除 5 条写侧**：`delete_all` / `clear_org_manager` / `clear_runtime_data_source` / `set_rest_enable_log` / `unload_dynamic_app`（L94-95 逐字） |
| E8 | `docs/operation-contracts/udc/microflow/live-evidence/C3_applog_*.json`（**6 件**，实测字节 151 / 275 / 151 / 275 / 275 / 275 B） | **负证据原件**：6 件**全为 404**——2 件 JSON（`{"status":3,"code":"server_404",...}`）+ 4 件 Whitelabel 404 HTML；→ **microflow 三端点 + `search_app_data_log` 无 LIVE 200 记录** |
| E9 | `docs/operation-contracts/udc/microflow/a6-milestone-report.md`（**14514 B**）L16 / L68 / L74-81 | microflow 族归因与排除说明：L16 C3 契约行（`select_by_id`）；L74-78「13 条候选未并入归因」（写侧 3 / 跨域重复 5 / 门控 5），**含 `datalog_list_by_data_id ≡ R17 applog.list_app_data_by_dataid` 的去重判定**（跨域同端点） |

### 8.1 实测计数（本机命令 + 结果，禁照抄任务书）

- `grep -c 'contracts\["udc\.applog' components/platform_operations/registry.py` → **6**（applog 域真条目数：L52/L64/L66/L68/L104/L106）。
- 本格**覆盖 6 条**（applog 域全部只读面；写端点 5 条不计数）。
- **口径差异注记（不改数迎合）**：任务书原料写「applog 12 条」，实测 registry.py 内 applog 域条目 = **6**（main 本轮实测同值，ROUTE §6.2）。
  差异在于任务书按「域内命名总数（含别名 / 文档候选）」计数，本格按**可复现命令输出**（registry.py 内 6 条）为准。**不修改任何数字以迎合任务书。**

### 8.2 别名纪律（硬，同端点不同名 → 并列登记、不归一，spec §1 最大陷阱）

- **`udc.applog.select_app_data_by_id`（E2 LIVE 记录名） ≡ `udc.applog.select_by_id`（registry L52）**：
  两者**同控制器 `UdcAppLogController`、同方法 `selectAppDataById(Long)`、同路径 `udc-runtime/app-log/datalog/{id}`**
  （E3 javap L747/L773 + E1 L52 + E4 P2 L11 三方互证；E6 L16 明记「P2 不新增条目，直接复用 `udc.applog.select_by_id`」）。
  → **必须写明「名字不同、同端点」**，不得静默改名归一；LIVE 证据（E2 行 25）**可引入 `select_by_id`，但须注明「LIVE 记录所用 operation_id 名 = `udc.applog.select_app_data_by_id`（别名）」**。
- **`udc.applog.datalog_list_by_data_id`（E5 P3 名） ≡ `udc.applog.list_app_data_by_dataid`（registry L104）**：
  同控制器、同方法 `selectAppDataByDataId(Long)`、同路径 `datalog/list-by-dataid/{dataId}`
  （E3 javap L786/L812 + E1 L104 + E5 L5-7 + E6 L26/L53 + E9 L76 跨域去重判定）。
  → **只注记别名关系，不新增条目、不重复计数**（spec §1 硬口径）；LIVE 证据（E2 行 26）已用 registry 名 `udc.applog.list_app_data_by_dataid` 登记，**无别名歧义**。
- **E6 L16 一处行号漂移（如实登记，不归因）**：E6 L16 文字写「registry.py **L51** `udc.applog.select_by_id`」，但 **registry.py 内该条目实测在 L52**（E1 L52 逐字 + E4 P2 L11「本轮 grep 实测在 L52」）；E6 L51 是 `applog_evidence` dict 定义行、非条目行 → **L16 的 L51 引用为行号漂移**，本格以**实测 L52** 为准，E6 原文照录、不改字。

### 8.3 负证据（明确未观测，防外推）

- **`udc.applog.search_app_data_log` 无 LIVE 记录**。复现命令与命中（本轮实测）：
  - `grep -rn 'search_app_data_log\|datalog/search' --include='*.py' --include='*.md' --include='*.json' .`（排除 `__pycache__`）→ 命中仅**契约 / 登记 / 报告侧**（registry.py L106、entity-readonly-contracts.md §6、PRE-MERGE-GATE-R7-report.md、registry-entries-code.md L130、registry-entries.md L128、a6-milestone-report.md 等），**无任何 HTTP 200 / 回读记录**。
- **microflow 三端点无 LIVE 200**（E8 负证据）：
  - `grep -il '404\|Whitelabel' docs/operation-contracts/udc/microflow/live-evidence/C3_applog_*.json` → **6/6 全命中 404**（2 件 JSON `server_404` + 4 件 Whitelabel HTML 404）。
  - `grep -rln 'search/microflow\|search-details/microflow' docs/audit/ core/facts/` → 仅命中 javap 文本件与非 flow 路径扫描（`non-flow-path-scan.txt`），**无任何 LIVE 回读 / 只读面记录**。
- **`list_app_data_by_dataid` 大响应内容未观测**：E2 行 26 的 598076 B 响应体**未展开**（§7 只引字节数与 envelope）；**列内容 UNVERIFIED**。
- **`select_by_id` 的响应体内容未观测**：E2 行 25 的 107 B 响应体**未展开**；**业务字段 UNVERIFIED**。
- **宿主侧副作用**：全部**未观测 → UNVERIFIED**（§6，本轮未联网）。

### 8.4 口径张力登记（ROUTE §6.5 精神）

| op | registry 声明（E1） | LIVE 观测（E2） | 处置 |
|---|---|---|---|
| `select_by_id`（别名 `select_app_data_by_id`） | `required_inputs=("id",)` | 实测 `id=1`（占位）即 200 | **并列登记**：声明必填 `id` 与占位 `id=1` 实测值并存；占位业务含义 **UNVERIFIED** |
| `list_app_data_by_dataid` | `required_inputs=("dataId",)` | 实测 `dataId=1`（占位）即 200（598076 B 大响应） | **并列登记**；占位业务含义 **UNVERIFIED** |
| `search_details_microflow_flowlog` | `request_type="MicroFlowLogDetailsSearchDto(RequestBody)"` | 无 LIVE（404 负证据） | **并列登记**；请求形态特殊性（裸 DTO、非 PageDtoRequest）已在 §4/§7 注明 |

## 9. Verified（逐项等级 + 未直读项）

| 项 | 等级 | 依据 |
|---|---|---|
| 6 条契约登记（method/path/req/resp/write/required） | VERIFIED_STATIC_BYTECODE | E1 L52/L64/L66/L68/L104/L106（+ 各 evidence dict） |
| 6 条控制器映射与注解 | VERIFIED_STATIC_BYTECODE | E3 javap 两副本（L472/L507/L542/L715/L740/L773/L786/L812 + 实体副本常量池）；E4/E5 契约 |
| `select_by_id` **执行面** | **LIVE（离线，09-18 窗口已过期；别名名 `select_app_data_by_id`）** | E2 行 25：200 / 107 B / BOOT_0000 / 二次 MATCH；**本轮未联网** |
| `list_app_data_by_dataid` **执行面** | **LIVE（离线，09-18 窗口已过期；大响应 598076 B 未落格）** | E2 行 26：200 / 598076 B / BOOT_0000 / 二次 MATCH；**本轮未联网** |
| `search_microflow` / `search_details_microflow` / `search_details_microflow_flowlog` **执行面** | **UNVERIFIED（404 负证据）** | E8（6 件 C3_applog 全 404）+ §8.3；**禁**把 `select_by_id` 的 LIVE 顺延给任一 POST 端点 |
| `search_app_data_log` **执行面** | **UNVERIFIED（无 LIVE 记录，自检索负证据）** | §8.3（全仓 `datalog/search` 命中仅契约 / 登记 / 报告侧，无任何 HTTP 回读）；**禁**把 `select_by_id` 的 LIVE 顺延 |
| agent 侧写门可执行性（4 条 POST） | **STATIC**（源码判定，**未运行期复现**） | §5：models.py L46-48 + layer.py L22-23 → `DENIED`/`POLICY_DENIED`；**不得标 LIVE**（本格未联网） |
| agent 侧写门可执行性（2 条 GET） | **STATIC**（源码判定） | §5：`effective=True`；**仍受 auth_scope 约束**（layer.py L24-25），未实测执行 |
| 网关 service 前缀（6 条） | UNVERIFIED | E1 第三条规则（禁止拼前缀） |
| `flowLog` 请求形态特殊性 | UNVERIFIED（声明级） | E1 L67 note（裸 DTO、非 PageDtoRequest）；无 LIVE 佐证 |
| 占位 id / 大响应业务字段 | UNVERIFIED | §8.3（响应体未展开） |
| 宿主侧副作用（6 条） | UNVERIFIED | §6（本轮未联网） |

**未直读项（如实登记）**：本轮**未联网**、**未运行期复现**、**未新建探针脚本**（按 S4 spec §4 禁 `python -c` / 禁新探针；全部证据取自在盘在盘）；
`select_by_id` / `list_app_data_by_dataid` 的响应体内容未展开；microflow 三端点 + `search_app_data_log` 均无 LIVE；applog 写端点（5 条）未入格、未计数。

## 溯源索引（可复现）

| 项 | 路径 |
|---|---|
| 契约登记（6 条 + 6 evidence dict） | `components/platform_operations/registry.py` L51/L52、L63/L64、L65/L66、L67/L68、L103/L104、L105/L106 |
| LIVE 离线证据（唯一 2 条） | `docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md` 行 3 / 行 25 / 行 26 / 行 28 |
| 字节码证据（两副本，非等价） | `docs/audit/artifacts/udc-menu-5.3.517/UdcAppLogController.javap.txt`（80629 B / `ebca5ad0…`）；`docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt`（80367 B / `0e74f6de…`） |
| 字段级契约 | `docs/operation-contracts/udc/menu/P2-udc-applog-datalog-get-by-id.md`；`docs/operation-contracts/udc/menu/P3-udc-applog-datalog-list-by-data-id.md` |
| 别名权威出处 | `docs/operation-contracts/udc/menu/registry-entries.md` L16 / L26 / L27 / L37 / L53 |
| 入库断言 + 排除 5 写侧 | `tests/test_applog_microflow_readonly.py`；`tests/test_datatype_applog_readonly.py` L29/L59/L94-95 |
| 微流程负证据（6 件 404） | `docs/operation-contracts/udc/microflow/live-evidence/C3_applog_*.json` |
| microflow 归因与去重说明 | `docs/operation-contracts/udc/microflow/a6-milestone-report.md` L16 / L74-81 |
| 写门源码（STATIC） | `components/platform_operations/models.py` L46-48；`components/platform_operations/layer.py` L22-23 |

> 本件自报字节数（写后 `wc -c` 实测，等宽回填不改大小）：22362 B · 时钟 2026-09-27 CST · 仓库 HEAD 16a384c（本件写前 git 状态 = clean tree）
