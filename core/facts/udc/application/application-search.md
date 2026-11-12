# udc.application（非草稿面）｜应用对象查询与检索能力族（九段式事实格 · S3）

> 基线：registry `udc.application.*` 契约登记（L45 / L86 / L88 / L90）+ 在盘 LIVE 证据（E2 = 本格 search 两条，S1P 已 PASS；E3 = `application.get`，09-04/口径 09-20 见 §8.2）。
> 段序与 B1 样板格 `core/facts/udc/entity/create.md` 一致；本件**只做 application 域非草稿面 4 条**，
> draft 两条归 S2（**已完成，不重复计数、不重写**）、applog 全族归 S4；同控制器写端点**仅注记、不入格、不计数**。
> 只写事实文档，不改 `registry.py`/`components/`/`docs/`；网关与凭据只写 config 键，值 0 入件（E3 内含字面，**禁转抄**）。
> 仓库 `<SEEYON_AGENT_ROOT>`，实测 HEAD `16a384c`。本轮**未联网、未新建探针、未读凭据目录**（按 S3 规格 §1 裁剪）。

---

## 1. Capability

| operation_id | HTTP | 控制器原路径（逐字） | 入参 | 响应 | 层 |
|---|---|---|---|---|---|
| `udc.application.get` | GET | `/udc/application/{id}` | `application_id`（路径变量） | `SingleResponse<ApplicationDto>` | 平台元数据应用面（**口径见下**） |
| `udc.application.search.no_page` | POST | `udc-runtime/custom-app/search-no-page` | `Map<String,Object> params + Sort`（@MultiRequestBody） | `ListResponse<CustomApplicationDto>` | 应用对象元数据查询面（custom-app） |
| `udc.application.search.page` | POST | `udc-runtime/custom-app/search-page` | `PageInfo + Map + Sort`（@MultiRequestBody） | `PageResponse<CustomApplicationDto>` | 应用对象元数据查询面（custom-app） |
| `udc.application.deploy_info` | GET | `{currentAppName}/app-info/deploy-info` | `String currentAppName`（PathVariable） | `SingleResponse<String>` | 生成物层（app-deploy-info.json） |

- **层次口径（实测复核后如实登记，含一处不符）**：E5 `udc-app-basic-readonly-contracts.md` L101 原文只给出——契约 1/2 = **应用对象元数据查询面（custom-app）**、契约 3 = **生成物层（app-deploy-info.json）**、契约 4/5 = 设计态配置层（AppDraft）；
  L100 记相邻面（meta-data 族）关系。**HANDOFF §2/E5 所记「`application.get` = 平台元数据应用面、search = 自定义应用列表面」的逐字表述在本轮实测中未在盘找到出处**
  （`grep -rn '平台元数据应用面\|自定义应用列表面' docs/ core/facts/` → 0 命中），且 **E5 五条契约中不含 `udc.application.get`**（E6 亦不含）→ 该定性 **UNVERIFIED**，本格不采信转述；`application.get` 的层归属**未证**。
- **层不可顶替（E5 L101 + ROUTE §6.5）**：`application.get`（平台应用对象查询）与 search（custom-app 列表检索）**不是同一层**，不得互相顶替；本格分开登记。
- **同控制器写端点（只注记不入格）**：`CustomApplicationController` 的 create / createAsync / copy / deleteByIds / update* / newLayoutCreateAsync 等写端点；以及 `AppDraftController` 的 create/delete（归 S2 注记）。
  均非本格能力，**不计入任何计数**。

## 2. Version

- Canonical = **5.3.517**（registry javap 锚点：E1 L85/L87/L89 `"version": "5.3.517"`；artifact = `udc-starter-runtime-5.3.517.jar`）。
- class_sha256（字节码类指纹，非文本件哈希）：`CustomApplicationController` = `d3e82d8bbc65dc92d5f9d30532159f1d10169f2aef1eae6ab67c70d7ad75ae55`（search 两条共用：E1 L85/L87）；
  deploy_info 面 = `UdcBaseAppInfoController` = `deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95`（E1 L89）。
- **javap 文本件 sha256（与 class_sha256 口径不同，禁混写）**：`CustomApplicationController.javap.txt` = `7984d98b1199931ec73576706a399ec7246f4bd7e7fb2d89adf1e8644b1e37f8`（**82330 B**，E4）。
- 本格 LIVE 证据件哈希：`core/facts/udc/application/evidence/app-search-live-20260926.md` = `57b89e496664aa49a0435caaee5dfded5155932f0c34065ebad934e5f0db7b3c`（**5675 B**，E2）。

## 3. Input

- `udc.application.get`：`application_id`（**路径变量**，registry L45 `request_type="application_id"`；路径 `/udc/application/{id}`）。
  LIVE 实测（E3）：request 为 `GET`，`target_path` 为 `/udc/application/{id×实际值}`（该 json 含 app_id 字面，**本格不转抄**，只写 config 键 `default_app_id`）。
- `search.no_page`：`Map<String,Object> params + Sort`（@MultiRequestBody；E1 L86，E4 javap L920 方法签名 + L956/L959 参数注解）。
  **LIVE 实测形态（E2 行 25）**：请求体为 `{}` 即 200/BOOT_0000。
- `search.page`：`PageInfo + Map<String,Object> + Sort`（@MultiRequestBody；E1 L88，E4 javap L961 签名 + L999/L1002/L1005 注解）。
  **LIVE 实测形态（E2 行 26）**：请求体为 `{"pageInfo":{"pageNo":1,"pageSize":10}}` 即 200/BOOT_0000。
- `deploy_info`：`String currentAppName`（PathVariable；E1 L90，E6 L14/L27 同述）；**无 LIVE**（§8.2）。
- 响应 DTO：`SingleResponse<ApplicationDto>` / `ListResponse<CustomApplicationDto>` / `PageResponse<CustomApplicationDto>` / `SingleResponse<String>`（E1 L45/L86/L88/L90 实测）。

## 4. Required（必填链与缺省推断）

- **registry 声明（E1 实测）**：`application.get` → `("application_id",)`；`search.no_page` → `("params", "sort")`；`search.page` → `("pageInfo", "params", "sort")`；`deploy_info` → `("currentAppName",)`。
- **LIVE 观测（E2 实测）**：`search.no_page` 以 `{}`（**无任何键**）即 200；`search.page` 仅带 `pageInfo`（**无 params / sort**）即 200。
- **两条并列、不做归一（ROUTE §6.5 强制）**：
  ① registry 声明把 `params`/`sort`（及 `pageInfo`）列为必填输入；② LIVE 实测这两组键**未被服务端要求**。
  **两方均保留、不删任一方**；其语义差异（声明=必填契约 vs 观测=可缺省）→ **UNVERIFIED**，不外推、不判孰对。
  边界：`params`/`sort` 是否影响结果集、`{}` 与带参是否语义等价 → **无证据 = UNVERIFIED**（承 E2 §2 既有结论）。
- 缺省值：四条均**未观测**缺省行为（`deploy_info` 无 LIVE；`application.get` 无缺参记录）→ **UNVERIFIED**。
- 网关前缀不构成入参：search 两条 verification_rules 第三条明标 **UNVERIFIED（离线不可确证，禁止拼前缀）**（E1 L86/L88）。

## 5. Execution

- 路径组装（**键组装，禁写字面**）：
  - `search.no_page` = `{config键 gateway_base}/service/{app_id}/udc-runtime/custom-app/search-no-page`
  - `search.page` = `{config键 gateway_base}/service/{app_id}/udc-runtime/custom-app/search-page`
  - `application.get` = `{config键 gateway_base}` + 控制器原路径 `/udc/application/{id}`
  - `deploy_info` = **完整路由 UNVERIFIED**（类级前缀因子类而异，禁拼；E1 L90 + E6 L33）
- 字节码映射链（E4 实测）：类级 `@RequestMapping(value=["udc-runtime/custom-app"])`（javap **L1133**）
  → `selectListByConditions(Map,Sort)` 声明 **L920** + `@PostMapping(value=["/search-no-page"])` **L951**；
  → `selectListByConditions(PageInfo,Map,Sort)` 声明 **L961** + `value=["/search-page"]` **L994**；
  方法体调用后端 `CustomApplicationAppService.selectListByConditions(ListRequest)`（javap Methodref #53）。
- **agent 侧可执行性——逐条判、不概称（引源码 STATIC，本轮未运行期复现，按 S3 规格 §1 允许的纯静态路径）**：
  `components/platform_operations/models.py` L46-48 定义 `effective = status ∈ {PASS, VERIFIED_STATIC_BYTECODE, OBSERVED} ∧ ¬write ∧ method == "GET"`；
  `components/platform_operations/layer.py` L22-23：命中 `write or method != "GET" or not effective` → `DENIED` / `POLICY_DENIED`。
  | op | method | write | status | effective（按 L46-48 判） | agent 侧结论 |
  |---|---|---|---|---|---|
  | `udc.application.get` | GET | False | VERIFIED_STATIC_BYTECODE | **True** | 通过写门；仍受 auth_scope 约束（layer.py L24-25）→ **未实测执行**，标 STATIC 判定 |
  | `search.no_page` | POST | False | VERIFIED_STATIC_BYTECODE | **False** | **DENIED / POLICY_DENIED**（只能宿主授权执行） |
  | `search.page` | POST | False | VERIFIED_STATIC_BYTECODE | **False** | **DENIED / POLICY_DENIED**（同上） |
  | `deploy_info` | GET | False | VERIFIED_STATIC_BYTECODE | **True**（按公式） | **路由 UNVERIFIED → 无可用 URL，实际不可发起**（两事并列登记） |
- 同法复现：`tests/test_application_readonly_contract.py` L25 把 search 两条列入 `POST_CONTRACTS`（POST → effective=False 的入库断言，E7）。

## 6. Side Effects

- 注册侧：四条 `write=False`（E1 L45/L86/L88/L90 实测）。
- 语义侧：四条均为**只读**（检索/读取类操作，无写语义；registry verification_rules 只含 readback 一致性断言）。
- agent 侧：search 两条因 `POLICY_DENIED` **不产生任何副作用**；`application.get` 通过写门但**本轮未发起**（无执行记录）→ agent 侧无副作用可报；`deploy_info` 路由未证，未发起。
- 宿主侧副作用：**全部未观测 → UNVERIFIED**（本格不含任何写端点的 LIVE），不外推。

## 7. Known Constraints

- **网关 service 前缀 UNVERIFIED**：search 两条明标「禁止拼前缀」（E1 L86/L88）。
- **`deploy_info` 完整路由 UNVERIFIED**：类级前缀因子类而异（FormAppInfoController 含 `dynamic-rest/com-seeyon` 段 / NormalAppInfoController 不同），父类本体无类级 @RequestMapping（E1 L90 + E6 L33）→ 禁止拼前缀。
- **层不可顶替**：`application.get` 与 search 不同层（§1）；E5 L101 五层不顶替（设计态配置 ≠ 运行态元数据 ≠ 生成物 ≠ 物理表 ≠ Redis）。
- **registry 声明 vs LIVE 观测张力**：`params`/`sort` 两条并列、差异 UNVERIFIED（§4）。
- **`data.content` 空集**：search 两条 LIVE 的 `data.content` **均为空（0 条）** → **「返回非空列表未观测到」**；空集成因（凭据用户可见范围 / 目标应用无自定义应用 / 参数过滤）**UNVERIFIED**，直接承 E2 §3 结论，本格不另起推断。
- **E3 含字面**：该 LIVE json 内含网关与 app_id 字面 → 引用只写路径与 config 键，**禁转抄**（§8.2 已按此处理）。
- **`application.get` 的 registry 证据 dict 跨域复用**：E1 L45 使用共享变量 `evidence`（registry.py **L16**：`source=test2-container`、`artifact=udc-web-5.3.517.jar`、`class=com.seeyon.udc.controller.EntityController`、**无 `javap` 字段**）——
  其 class 属 entity 域、与 `application.get` **不同类**，**不能充当该端点的类级字节码锚点**；本格如实登记（§8.2），不外推为 ApplicationController 证据。

## 8. Evidence（逐条实测复核；禁转述）

| # | 路径（在盘实测） | 实测要点 |
|---|---|---|
| E1 | `components/platform_operations/registry.py`（**51734 B**）L45 / L86 / L88 / L90（+ L16 共享 evidence、L110 相关面） | 四条契约登记（method/path/req/resp/status/write/required_inputs + verification_rules）；`application.get` 证据 dict 见 §7/§8.2 |
| E2 | `core/facts/udc/application/evidence/app-search-live-20260926.md`（**5675 B** / sha256 `57b89e49…`）§1 行 25-26、§2、§3 | **search 两条的 LIVE 依据**：no_page `{}` → 200 / **105 B** / BOOT_0000 / traceId `3247042976269994172`（二次 `3247042983182207164`）/ md5(去 traceId) `1e6f194d…` ×2 MATCH；page `{"pageInfo":{...}}` → 200 / **202 B** / BOOT_0000 / traceId `3247042987309402300`（二次 `3247042991671478460`）/ md5 `65933780…` ×2 MATCH；**两条 `data.content` 均空（0 条）** |
| E3 | `docs/operation-contracts/gateway/live-readonly-udc-application-get-evidence.json`（**1371 B**，实读 24 行） | **`application.get` 的 LIVE 依据**：`status=PASS`、`verification` transport/normalization/business/evidence **四验 PASS**、`response_redacted.status_code=200` + `code=BOOT_0000` + `message=SUCCESS`、`normalized_data.application_id` 在位；`redaction.raw_credential_persisted=false`。**内含 `gateway` / `gateway_path` / app_id 字面 → 本格只写路径与 config 键** |
| E4 | `docs/audit/artifacts/udc-app-basic/CustomApplicationController.javap.txt`（**82330 B** / sha256 `7984d98b…`） | 类级 `value=["udc-runtime/custom-app"]` **L1133**；`selectListByConditions(Map,Sort)` 声明 **L920** + `value=["/search-no-page"]` **L951**；`selectListByConditions(PageInfo,Map,Sort)` 声明 **L961** + `value=["/search-page"]` **L994**；@MultiRequestBody 注解 L956/L959、L999/L1002/L1005；常量池 `#154 selectListByConditions`、`#163 /search-no-page`、`#169 /search-page`、`#190 udc-runtime/custom-app` |
| E5 | `docs/operation-contracts/udc/application/udc-app-basic-readonly-contracts.md`（**12899 B**）§契约 1 L18 / 契约 2 L33 / 契约 3 L48；L100-101 | 契约字段级（三条）；L101 五层不顶替与层次定性；L100 相邻面。**该件不含 `udc.application.get` 契约条款** |
| E6 | `docs/operation-contracts/udc/application/registry-entries.md`（**7946 B**）L11-14 代码块 / L25-27 表 / L33 | MERGE 照抄条目（search 两条 + deploy_info）；**不含 `udc.application.get`**（`grep -n 'udc.application.get'` → 0 命中）→ 来源与本格其余三条不同，须注明 |
| E7 | `tests/test_application_readonly_contract.py`（**5401 B**）L25 | 入库断言：`search.no_page` / `search.page` 属 `POST_CONTRACTS`（POST → effective=False） |
| E8 | `docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md`（**5810 B**）行 28 / L64-67 | **`udc.appinfo.get_deploy_info` 的 LIVE = HTTP 404**（110 B / non-json / identity MISMATCH；recorded, not FAIL）——**与本格 `udc.application.deploy_info` 是两条不同 operation_id**，分别登记，**不得混同** |
| E9 | `components/platform_operations/registry.py` **L110**（`udc.appinfo.get_deploy_info`，GET `deploy-info`） | 上条 404 记录对应的契约（相关面注记，非本格能力） |

### 8.1 实测计数（本机命令 + 结果，禁照抄任务书）

- `grep -c 'contracts\["udc\.application' components/platform_operations/registry.py` → **6**（application 域真条目：get / search.no_page / search.page / deploy_info / draft.select / draft.exist）。
- 本格**覆盖 4 条**（非草稿面）；draft 2 条归 S2（已完成，不重复计数）。
- 旁证：`grep -c 'contracts\["udc\.applog' …` → **6**（applog 域，归 S4，本格不涉及）。
- **口径差异注记（不改数迎合）**：任务书原料写「application 12 条」，实测 registry.py 内 application 域条目 = **6**（main 本轮实测同值，ROUTE §6.2）。
  差异在于任务书按「域内命名总数（含别名/文档候选）」计数，本格按**可复现命令输出**为准。**不修改任何数字以迎合任务书。**

### 8.2 负证据与不符项（明确未观测/不符，防外推）

- **`udc.application.deploy_info` 无 LIVE**：E8 的 404 记录属 `udc.appinfo.get_deploy_info`（E9 L110 另一 operation_id），**不得**充作本格 deploy_info 的 LIVE；本格 deploy_info 终态 = **UNVERIFIED**（§9）。
- **`udc.application.get` 的证据 dict 跨域复用**：E1 L45 引用的共享 `evidence`（L16）其 `class=com.seeyon.udc.controller.EntityController`、`artifact=udc-web-5.3.517.jar`、**无 javap 字段** → 该端点**在本仓无对应的类级字节码锚点**（ApplicationController javap 件未复现于 registry）→ 如实登记为**锚点缺失（UNVERIFIED）**。
- **日期口径不符（如实并列，不择一改写）**：HANDOFF/上游记 `application.get` LIVE 为「**09-20 证据**」；
  本格实测 E3 文件 **mtime = 2026-09-04T23:59**，且**该 json 内无任何时间戳字段**（24 行逐读：仅有 `session_id="v02-live-session"` / `run_id="v02-live-run"`）。
  两条并列：**上游口径 09-20 / 文件 mtime 09-04 / 件内无时间戳** → 精确日期 **UNVERIFIED**；仅可确证「非本轮（2026-09-26）产生」。
- **层定性不符**：HANDOFF 所记「`application.get` = 平台元数据应用面」的逐字出处**未在盘找到**（§1）→ UNVERIFIED。
- **`application.get` 无 LIVE 之外的观测**：其执行面仅有 E3 一次 PASS 记录；无二次回读记录 → 稳定性/幂等性 **UNVERIFIED**。
- **`deploy_info` 无任何 LIVE / 404 之外的观测**；applog 族全部**不在本格**（归 S4），本格未探测。

### 8.3 口径张力登记（ROUTE §6.5）

| op | registry 声明（E1） | LIVE 观测（E2） | 处置 |
|---|---|---|---|
| `search.no_page` | `required_inputs=("params","sort")` | 实测 `{}` 即 200 | **两条并列、不归一**；语义差异 UNVERIFIED |
| `search.page` | `required_inputs=("pageInfo","params","sort")` | 实测仅 `pageInfo` 即 200 | **两条并列、不归一**；语义差异 UNVERIFIED |

## 9. Verified（逐项等级 + 未直读项）

| 项 | 等级 | 依据 |
|---|---|---|
| `search.no_page` / `search.page` 契约登记与控制器映射 | VERIFIED_STATIC_BYTECODE | E1 L86/L88；E4 javap L920/L951/L961/L994/L1133；E5 契约 1/2；E6 L11-12 |
| `search.no_page` / `search.page` **执行面** | **LIVE** | E2 §1 行 25-26（200 + BOOT_0000 + traceId + 双发 identity MATCH；105 B / 202 B） |
| `search.*` agent 侧可执行性（写门） | STATIC（源码判定，未运行期复现） | §5：models.py L46-48 + layer.py L22-23 → `DENIED`/`POLICY_DENIED`；E7 L25 入库断言 |
| `application.get` 契约登记 | VERIFIED_STATIC_BYTECODE | E1 L45（**证据 dict 跨域、类级锚点缺失**，见 §8.2） |
| `application.get` **执行面** | **LIVE**（**非本轮**：上游口径 09-20 / 件 mtime 09-04，精确日期 UNVERIFIED） | E3：`status=PASS` + 四验 PASS + 200/BOOT_0000/SUCCESS |
| `deploy_info` 契约登记与映射声明 | VERIFIED_STATIC_BYTECODE | E1 L90；E5 契约 3；E6 L14/L27 |
| `deploy_info` **执行面** | **UNVERIFIED** | §8.2（E8 的 404 属 `appinfo` 族另一 op_id，不混同）；完整路由 UNVERIFIED（E1 L90/E6 L33） |
| 网关 service 前缀（search 两条） | UNVERIFIED | E1 L86/L88 第三条规则（禁止拼前缀） |
| `params`/`sort` 必填性语义 | UNVERIFIED | §4/§8.3 并列口径 |
| `application.get` 层归属 / 精确 LIVE 日期 / 幂等性 | UNVERIFIED | §8.2 |
| 宿主侧副作用（四条） | UNVERIFIED | §6（无写端点 LIVE） |

**未直读项（如实登记）**：本轮**未联网**、**未读 `shared-credentials/`**、**未新建探针**、**未做运行期复现**（按 S3 规格 §1 裁剪）；
`application.get` 无类级字节码锚点；`deploy_info` 无 LIVE；applog 族未触及。

## 溯源索引（可复现）

| 项 | 路径 |
|---|---|
| 契约登记（4 条 + 相关面） | `components/platform_operations/registry.py` L45 / L86 / L88 / L90（+ L16 / L110） |
| search 两条 LIVE 证据 | `core/facts/udc/application/evidence/app-search-live-20260926.md`（S1P 产物，已 PASS） |
| `application.get` LIVE 证据 | `docs/operation-contracts/gateway/live-readonly-udc-application-get-evidence.json` |
| 字节码证据（search 两条） | `docs/audit/artifacts/udc-app-basic/CustomApplicationController.javap.txt` |
| 字段级契约 | `docs/operation-contracts/udc/application/udc-app-basic-readonly-contracts.md` §契约 1 / 2 / 3 + L100-101 |
| MERGE 条目 | `docs/operation-contracts/udc/application/registry-entries.md` L11-14 / L25-27 / L33 |
| 入库断言 | `tests/test_application_readonly_contract.py` L25 |
| deploy_info 相关面 404 记录 | `docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md` 行 28 / L64-67 |
| 写门源码（STATIC） | `components/platform_operations/models.py` L46-48；`components/platform_operations/layer.py` L22-23 |

> 本件自报字节数（写后 `wc -c` 实测，等宽回填不改大小）：20056 B · 时钟 2026-09-26 CST · 仓库 HEAD 16a384c
