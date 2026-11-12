# registry-entries — runtime 域只读契约建议条目（供 UDC-MERGE 任务照抄）

不实际改 `registry.py`（冻结文件，本任务只读复核）。字段顺序与 `models.py` `UdcOperationContract` 10 字段构造签名一致：
`operation_id, method, path, request_type, response_type, status, write, evidence, required_inputs, verification_rules`。

## 结论：**13 条只读候选（registry 全键 0 命中）**

去重实测（本轮，registry.py 只读）: `UdcOperationRegistry.default()` 运行态 distinct 键 **76**；13 条候选的 operation_id 与 path 模板对 registry 全键 grep **均 0 命中**（`docs/audit/artifacts/udc-runtime-5.3.517/r2_registry_key_check.txt`）→ **全部为净新增，无 key 冲突**。

分组:
- **A 组（7）runtime 域原生面**（环境检查 / 前端函数支持 / GraphQL 代理）—— 无既有概念域词干覆盖，直接入本域。
- **B 组（6）跨域词干重叠**（`app-log` / `serial-config` / `jar`）—— 只读 0 命中但落在既有概念域词干；本文件按既有概念域给 operation_id 域段（`udc.applog.*`/`udc.serial.*`/`udc.runtime.*`），**最终域段归并交 MERGE 裁定**。

> ⚠ 盘面漂移警示：上述 0 命中基于本轮实测 registry.py（运行态 76 键）。MERGE 落库前必须对当时 registry.py 重新实测 key 唯一性。
> ⚠ 门控提示（非验收变更）：A1–A4、B6 为 `GET` + `write=False` → `.effective()=True`；A5–A7、B1–B5 为 `POST` 只读（`write=False`）→ `.effective()=False`（与 page/flow 域 POST 只读同一门控事实，MERGE 须走与普通只读 POST 相同的 auth_scope 通道）。

## 建议构造调用（可直接并入 `UdcOperationRegistry.default()`）

```python
# ---- A 组：runtime 域原生 ----
runtime_env_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.RuntimeEnvCheckController", "method": "getBuildInfo", "class_sha256": "86e4598cd2124e8bc0f280b17e7e9965d626acb5a0adb9b5a80026d41c193582", "javap": "docs/audit/artifacts/udc-runtime-5.3.517/r2-RuntimeEnvCheckController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
contracts["udc.runtime.env_check_build_info"] = UdcOperationContract("udc.runtime.env_check_build_info", "GET", "udc-runtime/evn-check/build-info/{appName}", "String appName(@PathVariable)", "SingleResponse<Map<String, Object>>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [runtime_env_evidence], ("appName",), ("同一 appName 回读构建信息 identity_matches", "响应 SingleResponse<Map<String,Object>> 非空（buildVersion/frontResource 等键）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

runtime_env_app_version = dict(runtime_env_evidence, method="checkAppVersion")
contracts["udc.runtime.env_check_app_version"] = UdcOperationContract("udc.runtime.env_check_app_version", "GET", "udc-runtime/evn-check/app-version/{appName}", "String appName(@PathVariable)", "SingleResponse<String>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [runtime_env_app_version], ("appName",), ("同一 appName 回读应用版本 identity_matches", "响应 SingleResponse<String> 非空（版本号串）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

runtime_env_data_perm = dict(runtime_env_evidence, method="checkDataPermission")
contracts["udc.runtime.env_check_data_permission"] = UdcOperationContract("udc.runtime.env_check_data_permission", "GET", "udc-runtime/evn-check/data-permission/{entityFullName}", "String entityFullName(@PathVariable)", "SingleResponse<Object>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [runtime_env_data_perm], ("entityFullName",), ("同一 entityFullName 回读数据权限判定 identity_matches", "响应 SingleResponse<Object> 非空（权限判定结果）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

runtime_env_resp_len = dict(runtime_env_evidence, method="checkResponseLength")
contracts["udc.runtime.env_check_response_length"] = UdcOperationContract("udc.runtime.env_check_response_length", "GET", "udc-runtime/evn-check/response-length/{length}", "Integer length(@PathVariable)", "SingleResponse<String>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [runtime_env_resp_len], ("length",), ("同一 length 回读响应长度判定 identity_matches", "响应 SingleResponse<String> 非空", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

runtime_env_req_content = dict(runtime_env_evidence, method="checkRequestContent")
contracts["udc.runtime.env_check_request_content"] = UdcOperationContract("udc.runtime.env_check_request_content", "POST", "udc-runtime/evn-check/request-content", "String content(@MultiRequestBody)", "SingleResponse<String>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [runtime_env_req_content], ("content",), ("同一 content 回读请求内容判定 identity_matches", "响应 SingleResponse<String> 非空", "POST 只读形态（对照 registry L86 udc.application.search.no_page 先例，write=False）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

runtime_func_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.FrontFunctionSupportController", "method": "selectListByEntityName", "class_sha256": "c9be69ceb85a8c8e6e171b4f494c2d3124d9a08283b8cebfebca43e2a7db5f8a", "javap": "docs/audit/artifacts/udc-runtime-5.3.517/r2-FrontFunctionSupportController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
contracts["udc.runtime.function_support_calculate"] = UdcOperationContract("udc.runtime.function_support_calculate", "POST", "udc-runtime/function-support/calculate", "FrontFunctionSupportDto(@RequestBody)", "SingleResponse<Object>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [runtime_func_evidence], ("request",), ("同一 FrontFunctionSupportDto 回读前端函数支持数据 identity_matches", "响应 SingleResponse<Object> 非空", "POST 只读形态（方法名 selectListByEntityName，语义=列表查询）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

runtime_graphql_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.GraphqlProxyController", "method": "doGraphql", "class_sha256": "a83c2355e040c799eddd152c43ad2d4dbc0ceb3cae444bfb892b785c5a6bcb56", "javap": "docs/audit/artifacts/udc-runtime-5.3.517/r2-GraphqlProxyController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
contracts["udc.runtime.graphql_proxy_graphql"] = UdcOperationContract("udc.runtime.graphql_proxy_graphql", "POST", "udc-runtime/graphql-proxy/graphql", "GraphqlProxyRequestDto(@RequestBody)", "SingleResponse<String>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [runtime_graphql_evidence], ("request",), ("同一 GraphQL 请求体回读 identity_matches（同一 query 双读 strip(traceId) 一致）", "响应 SingleResponse<String> 非空（GraphQL JSON 结果）", "⚠ 只读性未确证：GraphQL 请求体可含 mutation（写操作）；离线字节码不可判别。MERGE 前须由 main/human 裁定是否收为只读契约或降为边界登记", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

# ---- B 组：跨域词干重叠（域段交 MERGE 裁定）----
applog_dataflow_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController", "method": "searchDataFlow", "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775", "javap": "docs/audit/artifacts/udc-runtime-5.3.517/r2-UdcAppLogController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
contracts["udc.applog.search_dataflow"] = UdcOperationContract("udc.applog.search_dataflow", "POST", "udc-runtime/app-log/search/dataflow", "PageDtoRequest<DataFlowLogSearchDto>(@RequestBody)", "PageResponse<UdcDataFlowLogDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [applog_dataflow_evidence], ("query",), ("同一 query 条件回读 identity_matches", "响应 data 为 UdcDataFlowLogDto 分页列表", "POST 只读形态；operation_id 域段=既有 applog 概念域（与 udc.applog.search_microflow 同域，MERGE 去重归并）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

applog_dataflow_details = dict(applog_dataflow_evidence, method="searchDataFlowDetails")
contracts["udc.applog.search_dataflow_details"] = UdcOperationContract("udc.applog.search_dataflow_details", "POST", "udc-runtime/app-log/search-details/dataflow", "PageDtoRequest<DataFlowLogSearchDto>(@RequestBody)", "PageResponse<UdcDataFlowLogDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [applog_dataflow_details], ("query",), ("同一 query 条件回读 identity_matches", "响应 data 为 UdcDataFlowLogDto 分页列表（明细层）", "POST 只读形态；applog 概念域", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

applog_deduction_evidence = dict(applog_dataflow_evidence, method="searchDeduction")
contracts["udc.applog.search_deduction"] = UdcOperationContract("udc.applog.search_deduction", "POST", "udc-runtime/app-log/search/deduction", "PageDtoRequest<DeductionLogSearchDto>(@RequestBody)", "PageResponse<UdcDeductionLogDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [applog_deduction_evidence], ("query",), ("同一 query 条件回读 identity_matches", "响应 data 为 UdcDeductionLogDto 分页列表", "POST 只读形态；applog 概念域", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

applog_deduction_details = dict(applog_dataflow_evidence, method="searchDeductionDetails")
contracts["udc.applog.search_deduction_details"] = UdcOperationContract("udc.applog.search_deduction_details", "POST", "udc-runtime/app-log/search-details/deduction", "PageDtoRequest<DeductionLogSearchDto>(@RequestBody)", "PageResponse<UdcDeductionLogDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [applog_deduction_details], ("query",), ("同一 query 条件回读 identity_matches", "响应 data 为 UdcDeductionLogDto 分页列表（明细层）", "POST 只读形态；applog 概念域", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

serial_list_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcSerialConfigController", "method": "selectListByConditions", "class_sha256": "fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658", "javap": "docs/audit/artifacts/udc-runtime-5.3.517/r2-UdcSerialConfigController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
contracts["udc.serial.config_list"] = UdcOperationContract("udc.serial.config_list", "POST", "udc-runtime/serial-config/list", "Map params + Sort sort(@RequestBody)", "ListResponse", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [serial_list_evidence], ("params", "sort"), ("同一 params/sort 回读 serial 配置列表 identity_matches", "响应 ListResponse 非空（或条件致空亦自证）", "POST 只读形态（方法名 selectListByConditions）；serial 概念域（与 udc.serial.* 同域，MERGE 去重归并）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

jar_status_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.DynamicJarController", "method": "getRequestStatus", "class_sha256": "0eb1fd79e96e09eb0122c0aafd77d8922ee3163f46f5436a44c98b476726def2", "javap": "docs/audit/artifacts/udc-runtime-5.3.517/r2-DynamicJarController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
contracts["udc.runtime.jar_import_status"] = UdcOperationContract("udc.runtime.jar_import_status", "GET", "udc-runtime/dynamic/jar/import/status/{requestId}", "String requestId(@PathVariable)", "SingleResponse<RequestStatusDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [jar_status_evidence], ("requestId",), ("同一 requestId 回读导入状态 identity_matches", "响应 SingleResponse<RequestStatusDto> 非空", "边界项：resource 域建议件已显式登记该端点为「只读但无 resource 词干·词干口径外」，交本域收（见 udc-resource-readonly-contracts 排除清单）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
```

## 逐字段说明（本域口径）
| 字段 | 取值规则 |
|---|---|
| operation_id | `udc.<域>.<操作>`；A 组域段=`runtime`，B 组域段=既有概念域（`applog`/`serial`/`runtime`） |
| method | javap verb 原值（`GET`/`POST` 逐字） |
| path | 类级 `@RequestMapping` value + 方法级注解 value **逐字拼接**；**禁拼网关前缀**；类级基路径均无前导 `/`，方法级原值照录 |
| request_type | 参数名 + 类型 + 绑定注解（`@PathVariable`/`@RequestBody`/`@MultiRequestBody` 按 javap 原值） |
| response_type | 完整泛型写法（javap `Signature` 原值） |
| status | `OperationStatus.VERIFIED_STATIC_BYTECODE`（13 条同） |
| write | `False`（13 条均只读；写形态 50 条已排除，不入本文件） |
| evidence | dict 列表，八键（source/artifact/version/class/method/class_sha256/javap/evidence_level），与 registry 既有条目同构 |
| required_inputs | 路径变量/入参名元组 |
| verification_rules | 含 identity_matches 回读 + 网关前缀 UNVERIFIED 如实标注；A7 另加「只读性未确证」项；B6 另加 resource 域边界项 |

## 排除与不入建议清单（显式）
| 项 | 原因 |
|---|---|
| `UdcBaseGeneralController` `{…}/create|update|delete-by-id(s)|update-batch|update-with-result|operate-root-batch|runtime-copy|export|import` | 写形态 |
| `UdcBaseGeneralController` `{…}/create-bpm|update-bpm` + `dataflow/{entityName}/{restMappingName}(/dynamic/select)` + `microflow/{microFlowName}` + `host/microflow/{microFlowName}` | **R7/R8④ 移交**（flow/microflow 透明路径），裁定勿入本域只读契约 |
| `UdcBaseGeneralController` / `UdcReferController` 的 refer/cascade/tree/filter 只读读面（24 行） | **proxy 层动态 REST 读面**，移交（微流程域合并裁定 / page 域 C5+条目6/7/8 已登记）；本域仅登记不构造 |
| `page-refer/{…}` 11 行 | **human 裁定域**（page refer 条目 6/7/8），本批零触碰 |
| `udcrt.controller` 写端点 50 行（create/update/delete/clear/unload/evict/refresh/enable/import/upgrade/upload/init/save…） | 写形态 |
| `AppDraftController` / `CustomApplicationController` / `AttachmentTemplateController` / `DynamicJarController#importJar` / `RuntimeCOLISplitController` / `UdcAttrSnapshotRtController` / `UdcRtPageLogController#createBatch,deleteAll` | 写形态（部分端点已由 application/resource 域覆盖） |

## 执行记录（待 MERGE）
- 本文件为**建议件**，registry.py 本轮零改动（R2 写面仅 `docs/operation-contracts/udc/runtime/**` + `docs/audit/artifacts/udc-runtime-5.3.517/**`）。
- 落库由后续 MERGE 任务执行；落库时点须复测 registry.py 全键唯一性 + 运行全量测试（`.venv/Scripts/python.exe -m pytest tests/ -q`，基线 395 passed）。
