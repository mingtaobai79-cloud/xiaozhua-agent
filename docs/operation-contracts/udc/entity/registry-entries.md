# UDC 实体域 registry 建议条目（registry-entries）

## 0. 降级登记（2026-11-07 补：反向指针）

本文件是**主文档**。与之重复的 `registry-entries-code.md`（306 行）已在自身头部写明
「已并入 `registry-entries.md`，保留作历史记录，不再作为入库依据」——那份是 MERGE 期间
「可直接粘贴代码块」的中间件，代码块已落入 `components/platform_operations/registry.py`。
此处补上对向指针，避免读者从主文档看不出还有个 code 变体。

## 用途

用途: 供 UDC-MERGE 任务照抄入库。本文件**不改 registry.py**（冻结，由 MERGE 统一落库）。
字段依据: UdcOperationContract 是 @dataclass，定义在 components/platform_operations/models.py:29
（**不在 registry.py**）。10 个位置参数序（MERGE 照抄依据，models.py:29-40 实测 frozen 定义，
后两字段带默认值）:

    (operation_id, method, path, request_type, response_type, status, write,
     evidence, required_inputs, verification_rules)

约定:
- status 一律 = "VERIFIED_STATIC_BYTECODE"（javap -p -v + SHA-256 实测）。
- write 一律 = False（本任务仅只读契约）。
- evidence dict 键（照微流程先例 udc.datatype.get_all / udc.applog.select_by_id 风格）:
  source / artifact / version / class / method / class_sha256 / javap / evidence_level。
- 证据全部取自本地 5.3.517 javap 实测（MANIFEST.md 索引），**不沿用 registry.py 现有
  udc.entity.* 条目的 test2-container udc-web-5.3.517.jar / com.seeyon.udc.controller.EntityController
  遗留 UNKNOWN 证据字段**。
- class_sha256 见各条 evidence；javap 文件名见对应 .javap.txt（docs/audit/artifacts/udc-entity-5.3.517/）。

---

## 1 udc.serial.select_entity_list
operation_id        = "udc.serial.select_entity_list"
method              = "GET"
path                = "udc-runtime/serial-config/select-entity-list"
request_type        = "java.lang.String"
response_type       = "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.EntityGroupAndItemDto>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-runtime-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.udcrt.controller.UdcSerialConfigController",
  "method": "selectEntityList(String)",
  "class_sha256": "fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658",
  "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcSerialConfigController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["appName"]
verification_rules  = "响应为 SingleResponse 包裹 EntityGroupAndItemDto 且 code 成功"

## 2 udc.serial.select_entity_by_serial
operation_id        = "udc.serial.select_entity_by_serial"
method              = "POST"
path                = "udc-runtime/serial-config/select-entity-by-serial-id"
request_type        = "java.util.Map<String, java.lang.Object>"
response_type       = "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.extmetadata.dto.UdcEntityMetaDataDto>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-runtime-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.udcrt.controller.UdcSerialConfigController",
  "method": "selectEntityBySerial(Map)",
  "class_sha256": "fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658",
  "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcSerialConfigController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["serialKey(Map)"]
verification_rules  = "响应为 ListResponse 包裹 UdcEntityMetaDataDto 列表"

## 3 udc.entity_data.query_form_data
operation_id        = "udc.entity_data.query_form_data"
method              = "POST"
path                = "udc-runtime/data//query"   # ⚠源值双斜杠逐字照录（类级 udc-runtime/data + 方法级 /query）
request_type        = "com.seeyon.boot.starter.udcrt.dto.EntityDataRequestDto"
response_type       = "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.EntityDataResponseDto>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-runtime-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.udcrt.controller.UdcFormDataQueryController",
  "method": "queryFormData(EntityDataRequestDto)",
  "class_sha256": "cabd312210665274361568181b6d41b9a86f7ed13f1dba7e3f844dc2e5ea5584",
  "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcFormDataQueryController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["EntityDataRequestDto(appId,dataId,attrKeys)"]
verification_rules  = "响应为 SingleResponse 包裹 EntityDataResponseDto；双斜杠路由归一化行为需 LIVE 复核（UNVERIFIED）"

## 4 udc.applog.select_app_data_by_id
operation_id        = "udc.applog.select_app_data_by_id"
method              = "GET"
path                = "udc-runtime/app-log/datalog/{id}"
request_type        = "java.lang.Long"
response_type       = "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.UdcEntityMonitorLogDto>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-runtime-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController",
  "method": "selectAppDataById(Long)",
  "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775",
  "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["id"]
verification_rules  = "响应为 SingleResponse 包裹 UdcEntityMonitorLogDto 且 code 成功"

## 5 udc.applog.list_app_data_by_dataid
operation_id        = "udc.applog.list_app_data_by_dataid"
method              = "GET"
path                = "udc-runtime/app-log/datalog/list-by-dataid/{dataId}"
request_type        = "java.lang.Long"
response_type       = "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.udcrt.dto.UdcEntityMonitorLogDto>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-runtime-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController",
  "method": "selectAppDataByDataId(Long)",
  "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775",
  "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["dataId"]
verification_rules  = "响应为 ListResponse 包裹 UdcEntityMonitorLogDto 列表"

## 6 udc.applog.search_app_data_log
operation_id        = "udc.applog.search_app_data_log"
method              = "POST"
path                = "udc-runtime/app-log/datalog/search"
request_type        = "com.seeyon.boot.transport.PageRequest"
response_type       = "com.seeyon.boot.transport.PageResponse<com.seeyon.boot.starter.udcrt.dto.UdcEntityMonitorLogDto>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-runtime-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController",
  "method": "searchAppDataLog(PageRequest)",
  "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775",
  "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["PageRequest(page,size)"]
verification_rules  = "响应为 PageResponse 包裹 UdcEntityMonitorLogDto"

## 7 udc.role.has_system_admin
operation_id        = "udc.role.has_system_admin"
method              = "GET"
path                = "udc-runtime/udc-role/has-system-admin/{appName}"
request_type        = "java.lang.String"
response_type       = "com.seeyon.boot.transport.SingleResponse<java.lang.Boolean>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-runtime-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.udcrt.controller.UdcRoleRtController",
  "method": "search(String)",
  "class_sha256": "ed024802b6c205041e4368840993412be184ff67c5f9b12938bee5a13a2aae47",
  "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcRoleRtController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["appName"]
verification_rules  = "响应为 SingleResponse 包裹 Boolean（true=该 app 系统管理员）"

## 8 udc.appinfo.get_deploy_info
operation_id        = "udc.appinfo.get_deploy_info"
method              = "GET"
path                = "deploy-info"   # ⚠类级 @RequestMapping 缺省（无前缀）；完整路径仅方法级 deploy-info；未拼网关/service 前缀（UNVERIFIED）
request_type        = "java.lang.String"
response_type       = "com.seeyon.boot.transport.SingleResponse<java.lang.String>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-runtime-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseAppInfoController",
  "method": "getDeployInfo(String)",
  "class_sha256": "deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95",
  "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcBaseAppInfoController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["currentAppName"]
verification_rules  = "响应为 SingleResponse 包裹 String（部署信息 JSON）；部署 context-path 需 LIVE 确认（UNVERIFIED）"

## 9 udc.page.check_exists
operation_id        = "udc.page.check_exists"
method              = "POST"
path                = "udc-runtime/meta-data/check-page-exists"
request_type        = "java.util.List<com.seeyon.boot.starter.udcrt.dto.UdcRtPageExistsDto>"
response_type       = "com.seeyon.boot.transport.ListResponse<java.lang.Boolean>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-runtime-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController",
  "method": "checkPageExistsByConditions(List)",
  "class_sha256": "7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02",
  "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcRtPageInfoController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["UdcRtPageExistsDto(appId,pageId) list"]
verification_rules  = "响应为 ListResponse 包裹 Boolean 列表（每项=该页面是否存在）"

## 10 udc.page.select_host_only_pages
operation_id        = "udc.page.select_host_only_pages"
method              = "POST"
path                = "udc-runtime/meta-data/select-host-and-only-page-pages"
request_type        = "com.seeyon.boot.starter.extmetadata.dto.request.UdcPagesMetaDataSearchDto"
response_type       = "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.extmetadata.dto.UdcMainPageMetadataDto>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-runtime-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController",
  "method": "selectHostAppAndOnlyPageAppPages(UdcPagesMetaDataSearchDto)",
  "class_sha256": "7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02",
  "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcRtPageInfoController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["UdcPagesMetaDataSearchDto"]
verification_rules  = "响应为 ListResponse 包裹 UdcMainPageMetadataDto"

## 11 udc.database.query_data
operation_id        = "udc.database.query_data"
method              = "GET"
path                = "udc-runtime/database/query-data"   # ⚠GET 携带请求体 RuntimeDataBaseQueryDataReqDto（源码实测）
request_type        = "com.seeyon.boot.starter.udcrt.dto.RuntimeDataBaseQueryDataReqDto"
response_type       = "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.UdcRuntimeDatabaseQueryRespDto>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-runtime-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.udcrt.controller.UdcRuntimeDatabaseController",
  "method": "queryData(RuntimeDataBaseQueryDataReqDto)",
  "class_sha256": "588bc1cf97cf53357ce0a851d16eb28244b6a9607aa5c813b80e4c2c8d4b3c48",
  "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcRuntimeDatabaseController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["RuntimeDataBaseQueryDataReqDto(dataSource,table,condition)"]
verification_rules  = "响应为 SingleResponse 包裹 UdcRuntimeDatabaseQueryRespDto；GET 带请求体语义需 LIVE 复核"

## 12 udc.entity.history.select_by_condition
operation_id        = "udc.entity.history.select_by_condition"
method              = "POST"
path                = "udc-runtime/history-metadata/select-by-condition"   # 类级 udc-runtime/history-metadata + 方法级 select-by-condition（javap 逐字）
request_type        = "java.util.Map<String, java.lang.Object>"
response_type       = "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.customplan.dto.UdcHistoryMetaDataDto>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-customplan-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.customplan.controller.UdcRuntimeHistoryMetaDataController",
  "method": "selectByCondition(Map)",
  "class_sha256": "9f197e358d9b7b38e19e1afe280ebcd75b0a2c09f73b29c6f6e0f0cbe025ef1c",
  "javap": "docs/audit/artifacts/udc-entity-customplan-5.3.517/UdcRuntimeHistoryMetaDataController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["Map(条件键值)"]
verification_rules  = "响应为 ListResponse 包裹 UdcHistoryMetaDataDto 列表"

## 13 udc.entity.ext.tree
operation_id        = "udc.entity.ext.tree"
method              = "POST"
path                = "udc-runtime/scalability/ext-entity-tree"   # 类级 udc-runtime/scalability + 方法级 ext-entity-tree
request_type        = "java.lang.String"
response_type       = "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.customplan.dto.EntityRuntimeTreeDto>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-customplan-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController",
  "method": "selectMetadataExtEntityTree(String)",
  "class_sha256": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151",
  "javap": "docs/audit/artifacts/udc-entity-customplan-5.3.517/ScalabilityFieldController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["appName"]
verification_rules  = "响应为 ListResponse 包裹 EntityRuntimeTreeDto（实体扩展树）"

## 14 udc.entity.ext.list
operation_id        = "udc.entity.ext.list"
method              = "POST"
path                = "udc-runtime/scalability/list-ext-field"
request_type        = "com.seeyon.boot.starter.customplan.dto.ScalabilityFieldQueryDto"
response_type       = "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.customplan.dto.ScalabilityFieldDto>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-customplan-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController",
  "method": "listExtFileds(ScalabilityFieldQueryDto)",
  "class_sha256": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151",
  "javap": "docs/audit/artifacts/udc-entity-customplan-5.3.517/ScalabilityFieldController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["ScalabilityFieldQueryDto"]
verification_rules  = "响应为 ListResponse 包裹 ScalabilityFieldDto（扩展字段列表）"

## 15 udc.entity.ext.available_datatype
operation_id        = "udc.entity.ext.available_datatype"
method              = "POST"
path                = "udc-runtime/scalability/available-datatype"
request_type        = "com.seeyon.boot.starter.customplan.dto.ScalabilityFieldQueryDto"
response_type       = "com.seeyon.boot.transport.ListResponse<java.lang.String>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-customplan-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController",
  "method": "selectAvailableDatatype(ScalabilityFieldQueryDto)",
  "class_sha256": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151",
  "javap": "docs/audit/artifacts/udc-entity-customplan-5.3.517/ScalabilityFieldController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["ScalabilityFieldQueryDto"]
verification_rules  = "响应为 ListResponse 包裹 String（可用数据类型列表）"

## 16 udc.entity.ext.attribute
operation_id        = "udc.entity.ext.attribute"
method              = "POST"
path                = "udc-runtime/scalability/select-attribute"
request_type        = "com.seeyon.boot.starter.customplan.dto.ScalabilityFieldQueryDto"
response_type       = "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.customplan.dto.ScalabilityFieldDto>"
status              = "VERIFIED_STATIC_BYTECODE"
write               = False
evidence            = {
  "source": "local-maven",
  "artifact": "udc-starter-customplan-5.3.517.jar",
  "version": "5.3.517",
  "class": "com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController",
  "method": "selectAttribute(ScalabilityFieldQueryDto)",
  "class_sha256": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151",
  "javap": "docs/audit/artifacts/udc-entity-customplan-5.3.517/ScalabilityFieldController.javap.txt",
  "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
required_inputs     = ["ScalabilityFieldQueryDto"]
verification_rules  = "响应为 SingleResponse 包裹 ScalabilityFieldDto（单属性）"

---

## 排除项（禁入 registry 只读条目，已登记 MANIFEST.md 排除项）
写/破坏语义 GET（禁入只读）:
- UdcAppLogController: delete-all / clear-org-manager / clear-runtime-data-source-cache /
  unload-dynamic-app/{appName} / enable-log/{enable}
- UdcAttrSnapshotRtController: delete-by-data-id / delete-by-master-data-id
- UdcSerialConfigController: refresh-historical-data/{appName} / cache-evict/{appName}
写方法（POST/语义写）:
- UdcEntityUpdateRtTestController.update-with-fields（该 controller 唯一方法，无 entity 只读面）
- AppDraftController create/or-update/exist/select/delete/deleteAll/deleteTimeout

## 待 MERGE 注意
- 上述 path 均为控制器原路径（未拼网关/service 前缀）。UDC-MERGE 落 registry 时如需网关完整
  路由，须另行 LIVE 取证网关 service 前缀（本任务标 UNVERIFIED，不在此处拼接）。
- #3/#8/#11 的怪值（双斜杠、类级前缀缺省、GET 带请求体）原样保留，MERGE 时不得"美化"。

### 排除项（端点重复，删一留一按 R15 C1 先例，勿重复登记 —— R17 MERGE 记名）
以下 3 条为端点重复项，与既有 registry 条目同 class + 同 method + 同 path（逐字），按「去重删一留一」
先例不重复入 registry（保留既有条目），仅在本 md 记名：
- md 第4条 udc.applog.select_app_data_by_id ≡ 已登 C3 udc.applog.select_by_id（同 class f6a2111d 同 method selectAppDataById 同 path udc-runtime/app-log/datalog/{id}）→ 保留 C3，本条不入 registry。
- md 第9条 udc.page.check_exists ≡ 已登 C5 udc.metadata.page_exists_check（同 class 76787348 同 method checkPageExistsByConditions 同 path udc-runtime/meta-data/check-page-exists）→ 保留 C5，本条不入 registry。
- md 第10条 udc.page.select_host_only_pages ≡ 已登 C4 udc.metadata.page_tree（同 class 76787348 同 method selectHostAppAndOnlyPageAppPages 同 path udc-runtime/meta-data/select-host-and-only-page-pages）→ 保留 C4，本条不入 registry。
