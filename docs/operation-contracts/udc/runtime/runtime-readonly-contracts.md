# UDC runtime 域只读契约 — 差分扫描结论与候选（runtime-readonly-contracts.md）

- 域模块: udc-runtime（`udc-starter-runtime` 启动器 jar 的 HTTP 控制器层 = `com.seeyon.boot.starter.udcrt.controller.*`）
- 版本单元: 5.3.517（本地 Maven `<MAVEN_REPO>\com\seeyon`，只读离线证据；**禁混写相邻版本单元**）
- 证据等级: VERIFIED_STATIC_BYTECODE（三层扫描 + 27 类 `javap -p -v` 全量落盘；**封顶**，无越级）
- 扫描方法: 见同目录 `runtime-domain-scan.md`（照抄 `udc/bi/bi-vacuum-contract.md` 三层法）
- 建议条目: 见同目录 `registry-entries.md`（13 条 python 构造，dry-run PASS）
- 证据包: `docs/audit/artifacts/udc-runtime-5.3.517/`（`r2_*` 前缀件）
- 生成: implementer · 依据 main/ROUTE.md v3 §S3（HANDOFF dedupe_key `R2-handoff-v1`）

## 结论（唯一判定）

**UDC 5.3.517 runtime 域差分出 13 条 registry 全键 0 命中的只读候选（净新增，无 key 冲突）—— 非真空。**

- A 组（7）runtime 域原生面: 环境检查（evn-check 5）+ 前端函数支持（1）+ GraphQL 代理（1）。
- B 组（6）跨域词干重叠: app-log dataflow/deduction 搜索（4）+ serial 配置列表（1）+ jar 导入状态（1）—— operation_id 域段交 MERGE 裁定。
- 与 R7/R8 移交项④一致: `UdcBaseGeneralController` proxy 层 flow/microflow 透明路径 **未作为本域只读契约落库**（仅登记）；page-refer 读面 11 行 **零触碰**（human 裁定域）。
- 判定性质 = **差分（DIFF）**，非 VACUUM: 三层全非 0（27 类 / 133 行 / 38646 Utf8），差分为「registry 已覆盖 27 行（去重映射）+ 106 零命中」，其中只读候选 13。

## 7 要素（按域汇总；逐条全字段见 `registry-entries.md`）

| 要素 | 取值 |
|---|---|
| 1. operation_id | 13 条（A7 + B6），见下表；`udc.<域>.<操作>` |
| 2. HTTP method | javap verb 原值: GET×5（A1-A4, B6）+ POST×8（A5-A7, B1-B5） |
| 3. 控制器原路径 | 类级 `@RequestMapping` value + 方法级注解 value **逐字拼接**；类级基路径无前导 `/`，方法级原值照录；**禁拼网关前缀** |
| 4. 参数形态 | 逐条 javap 原值（`@PathVariable` / `@RequestBody` / `@MultiRequestBody`） |
| 5. 返回 DTO | javap `Signature` 原值（SingleResponse / PageResponse / ListResponse 泛型） |
| 6. evidence | 八键 dict（source/artifact/version/class/method/class_sha256/javap/evidence_level）+ 三层负/正证据 + jar_sha256 |
| 7. LIVE 回读条件 | 需部署态 + 网关 service 前缀 + 非 5.3.517 版本单元；**本轮不做**（离线） |

### 候选清单（13）

| # | operation_id | method | path | 控制器#方法 | class_sha256 前12 |
|---|---|---|---|---|---|
| A1 | udc.runtime.env_check_build_info | GET | udc-runtime/evn-check/build-info/{appName} | RuntimeEnvCheckController#getBuildInfo | 86e4598cd212 |
| A2 | udc.runtime.env_check_app_version | GET | udc-runtime/evn-check/app-version/{appName} | RuntimeEnvCheckController#checkAppVersion | 86e4598cd212 |
| A3 | udc.runtime.env_check_data_permission | GET | udc-runtime/evn-check/data-permission/{entityFullName} | RuntimeEnvCheckController#checkDataPermission | 86e4598cd212 |
| A4 | udc.runtime.env_check_response_length | GET | udc-runtime/evn-check/response-length/{length} | RuntimeEnvCheckController#checkResponseLength | 86e4598cd212 |
| A5 | udc.runtime.env_check_request_content | POST | udc-runtime/evn-check/request-content | RuntimeEnvCheckController#checkRequestContent | 86e4598cd212 |
| A6 | udc.runtime.function_support_calculate | POST | udc-runtime/function-support/calculate | FrontFunctionSupportController#selectListByEntityName | c9be69ceb85a |
| A7 | udc.runtime.graphql_proxy_graphql | POST | udc-runtime/graphql-proxy/graphql | GraphqlProxyController#doGraphql | a83c2355e040 |
| B1 | udc.applog.search_dataflow | POST | udc-runtime/app-log/search/dataflow | UdcAppLogController#searchDataFlow | f6a2111d3f5f |
| B2 | udc.applog.search_dataflow_details | POST | udc-runtime/app-log/search-details/dataflow | UdcAppLogController#searchDataFlowDetails | f6a2111d3f5f |
| B3 | udc.applog.search_deduction | POST | udc-runtime/app-log/search/deduction | UdcAppLogController#searchDeduction | f6a2111d3f5f |
| B4 | udc.applog.search_deduction_details | POST | udc-runtime/app-log/search-details/deduction | UdcAppLogController#searchDeductionDetails | f6a2111d3f5f |
| B5 | udc.serial.config_list | POST | udc-runtime/serial-config/list | UdcSerialConfigController#selectListByConditions | fe1e5a72d7a2 |
| B6 | udc.runtime.jar_import_status | GET | udc-runtime/dynamic/jar/import/status/{requestId} | DynamicJarController#getRequestStatus | 0eb1fd79e96e |

## 域边界（三层 + 移交/排除）

- **三层扫描**: L-A 类名层 346 class（307 顶层；控制器层 19+11）/ L-B 端点层 27 mapping-bearing 类 → 133 行 / L-C 常量池层 346 类 38646 Utf8 → 47 路径型字面量，端点表外新增 = 0。三层齐，非静默推断。
- **差分**: 133 行 = 27 registry 已覆盖（重复形态·去重映射，不入库）+ 106 零命中；106 = 只读 37 + 写形态 50 + R7/R8 排除 8 + human 域排除 11。
- **只读 37 拆分**: 本域候选 13 + **proxy 层动态 REST 只读 24**（`UdcReferController` 14 + `UdcBaseGeneralController` 10）→ 移交（R7/R8④ 微流程域合并裁定 + page 域 C5/条目6/7/8 已登记），本域仅登记不构造。
- **写形态 50**: 全排除（含 GET-写语义者: app-log clear-*/delete-all/enable-log/unload、attr-snapshot delete-by-*、rt-page-log delete-all、serial-config cache-evict/refresh-historical-data）。
- **human 裁定域**: page-refer 11 行零触碰（page refer 条目 6/7/8）。
- 详表见 `runtime-domain-scan.md` §2/§3。

## 门控注记（`.effective`，MERGE 业务取舍点，本任务只标注不代决）

`UdcOperationContract.effective`（`components/platform_operations/models.py`，本会话实测为**属性**（非方法）；判据 = status ∈ {PASS, VERIFIED_STATIC_BYTECODE, OBSERVED} AND NOT write AND method.upper()=="GET"）:
- **`.effective=True`（5 条）**: A1–A4 + B6（GET + VERIFIED_STATIC_BYTECODE + write=False）。
- **`.effective=False`（8 条）**: A5–A7 + B1–B5（POST 只读，`@PostMapping` 注解字面值禁改）。
- MERGE 一句话:『POST 只读条目 `.effective=False`，MERGE 时须走与普通只读 POST 相同的 auth_scope 通道，勿依赖 `.effective` 自动放行』（与 page/flow 域同口径）。

## 证据锚点

- 证据单元: `udc-starter-runtime-5.3.517.jar`（861880 B，sha256 `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`）。
- 三层: `r2_layerA_classname_scan.json` / `r2_endpoints_raw.json`+`r2_endpoints_flat.json` / `r2_layerC_constantpool_scan.json`。
- 差分: `r2_diff.json` / `r2_classified.json` / `r2_candidates.json` / `r2_registry_key_check.txt` / `r2_summary.json`。
- provenance: `r2_javap_manifest.json` + 27 个 `r2-<Class>.javap.txt`（头含五元组+）。
- 可构造性: `r2_registry_entries_dryrun.txt`（13/13 构造 OK，0 冲突）。
- 可复跑脚本 9 个（`r2_*.py`，sha256 见 `r2_staged_manifest.json`）。
- 单条抽查锚（main 可独立复现）: `RuntimeEnvCheckController`，class_sha256 `86e4598cd2124e8bc0f280b17e7e9965d626acb5a0adb9b5a80026d41c193582`（11474 B），类级基路径原值 `udc-runtime/evn-check`，5 条方法级路径原值 `build-info/{appName}` / `app-version/{appName}` / `data-permission/{entityFullName}` / `response-length/{length}` / `request-content`。复现命令:
  ```
  "C:\Program Files\Java\latest\jdk-21\bin\javap.exe" -J-Dstdout.encoding=UTF-8 -p -v \
    -cp <MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar \
    com.seeyon.boot.starter.udcrt.controller.RuntimeEnvCheckController
  ```

## 版本族隔离声明
本文件全部候选（字节码 sha256 / 路径 / 方法 / DTO / evidence_level）绑定 `udc-starter-runtime` 5.3 族 **5.3.517** 单一构件；跨版本族（5.3.496 test2 镜像 / 5.3.345-358 相邻旧版）**不得复用本判定**。

## 待裁事项（本任务只标不代决）
1. **B 组域段**: B1–B4/B5 的 operation_id 域段取 `udc.applog.*`/`udc.serial.*`（既有概念域）还是 `udc.runtime.*`（本域）—— 域归属交 MERGE/main 裁定。
2. **A7 GraphQL 只读性**: `doGraphql` 可含 GraphQL mutation（写），离线字节码不可判别 —— 是否收为只读契约或降为边界登记，交 main/human 裁定。
3. **proxy 层动态 REST 读面（24 行）**: 是否部分扩入本域 —— 按 R7/R8④ 与 page 域既有登记，本任务判为移交；如需扩入请另开 HANDOFF。
