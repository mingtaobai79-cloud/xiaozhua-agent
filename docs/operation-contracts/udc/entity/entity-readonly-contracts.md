# UDC 实体域 只读契约（entity-readonly-contracts）

域: entity　版本单元: 本地 Maven 5.3.517（<MAVEN_REPO>/com/seeyon，勿与 test2 镜像 5.3.496 混写）
证据等级: VERIFIED_STATIC_BYTECODE（javap -p -v + SHA-256；证据索引见
docs/audit/artifacts/udc-entity-5.3.517/MANIFEST.md）
状态: 全离线取证，未做 LIVE、未连网关/服务。控制器路径逐字照 javap 常量，**未拼网关前缀**；
网关 service 前缀是否真实存在=UNVERIFIED（本任务不连网关，不做推断）。

## 正向只读契约（16 条；≥8 达标，不凑数；11 条 runtime + 5 条 customplan）
> 每条 7 要素: operation_id / HTTP method / 控制器原路径（逐字，禁拼网关前缀）/ 参数形态 /
> 返回 DTO / evidence（artifact+version+class+method+class_sha256）/ LIVE 回读条件（只写需要什么，本轮不做）。

### 1 udc.serial.select_entity_list
- method: GET
- path（控制器原路径）: udc-runtime/serial-config/select-entity-list
- 参数形态: 路径常量，无路径变量；方法参数 java.lang.String（query 体）
- 返回 DTO: SingleResponse<EntityGroupAndItemDto>
- evidence: artifact=udc-starter-runtime-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.udcrt.controller.UdcSerialConfigController;
  method=selectEntityList(String); class_sha256=fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658
- LIVE 回读条件: **已解决**（凭据引用 config/environments.yaml:environments.test2.credential.ref；
  路由/前缀/appId 见 test2 键 gateway_base / gateway_prefix_template / default_app_id；
  本凭据窗口已回读，结果见 docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md）。
  实测: HTTP 200 / envelope BOOT_0000 / 二次回读 identity MATCH。

### 2 udc.serial.select_entity_by_serial
- method: POST
- path（控制器原路径）: udc-runtime/serial-config/select-entity-by-serial-id
- 参数形态: 方法参数 java.util.Map<String,Object>（请求体）
- 返回 DTO: ListResponse<com.seeyon.boot.starter.extmetadata.dto.UdcEntityMetaDataDto>
- evidence: artifact=udc-starter-runtime-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.udcrt.controller.UdcSerialConfigController;
  method=selectEntityBySerial(Map); class_sha256=fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658
- LIVE 回读条件: 需真实 udc-runtime 网关 + 一条实体 serial 键值 Map；断言 ListResponse 返回
  UdcEntityMetaDataDto 列表。本轮不做。

### 3 udc.entity_data.query_form_data
- method: POST
- path（控制器原路径）: udc-runtime/data//query　⚠双斜杠为源值逐字照录（类级前缀
  udc-runtime/data + 方法级 /query 拼接产物），未美化
- 参数形态: EntityDataRequestDto（请求体）
- 返回 DTO: SingleResponse<EntityDataResponseDto>
- evidence: artifact=udc-starter-runtime-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.udcrt.controller.UdcFormDataQueryController;
  method=queryFormData(EntityDataRequestDto); class_sha256=cabd312210665274361568181b6d41b9a86f7ed13f1dba7e3f844dc2e5ea5584
- LIVE 回读条件: 需真实 udc-runtime 网关 + 一个 EntityDataRequestDto（appId/dataId/attrKeys）；
  断言 SingleResponse 包裹 EntityDataResponseDto。双斜杠在网关路由下的真实归一化行为需 LIVE 复核。本轮不做。

### 4 udc.applog.select_app_data_by_id
- method: GET
- path（控制器原路径）: udc-runtime/app-log/datalog/{id}
- 参数形态: 路径变量 java.lang.Long id
- 返回 DTO: SingleResponse<UdcEntityMonitorLogDto>
- evidence: artifact=udc-starter-runtime-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.udcrt.controller.UdcAppLogController;
  method=selectAppDataById(Long); class_sha256=f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775
- LIVE 回读条件: **已解决**（凭据引用 config/environments.yaml:environments.test2.credential.ref；
  路由/前缀/appId 见 test2 键 gateway_base / gateway_prefix_template / default_app_id；
  本凭据窗口已回读，结果见 docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md）。
  实测: HTTP 200 / envelope BOOT_0000 / 二次回读 identity MATCH。

### 5 udc.applog.list_app_data_by_dataid
- method: GET
- path（控制器原路径）: udc-runtime/app-log/datalog/list-by-dataid/{dataId}
- 参数形态: 路径变量 java.lang.Long dataId
- 返回 DTO: ListResponse<UdcEntityMonitorLogDto>
- evidence: artifact=udc-starter-runtime-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.udcrt.controller.UdcAppLogController;
  method=selectAppDataByDataId(Long); class_sha256=f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775
- LIVE 回读条件: **已解决**（凭据引用 config/environments.yaml:environments.test2.credential.ref；
  路由/前缀/appId 见 test2 键 gateway_base / gateway_prefix_template / default_app_id；
  本凭据窗口已回读，结果见 docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md）。
  实测: HTTP 200 / envelope BOOT_0000 / 二次回读 identity MATCH。

### 6 udc.applog.search_app_data_log
- method: POST
- path（控制器原路径）: udc-runtime/app-log/datalog/search
- 参数形态: com.seeyon.boot.transport.PageRequest（分页请求体）
- 返回 DTO: PageResponse<UdcEntityMonitorLogDto>
- evidence: artifact=udc-starter-runtime-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.udcrt.controller.UdcAppLogController;
  method=searchAppDataLog(PageRequest); class_sha256=f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775
- LIVE 回读条件: 需真实 udc-runtime 网关 + 一个 PageRequest（页码/大小）；断言 PageResponse 包裹
  UdcEntityMonitorLogDto。本轮不做。

### 7 udc.role.has_system_admin
- method: GET
- path（控制器原路径）: udc-runtime/udc-role/has-system-admin/{appName}
- 参数形态: 路径变量 java.lang.String appName
- 返回 DTO: SingleResponse<Boolean>
- evidence: artifact=udc-starter-runtime-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.udcrt.controller.UdcRoleRtController;
  method=search(String); class_sha256=ed024802b6c205041e4368840993412be184ff67c5f9b12938bee5a13a2aae47
- LIVE 回读条件: **已解决**（凭据引用 config/environments.yaml:environments.test2.credential.ref；
  路由/前缀/appId 见 test2 键 gateway_base / gateway_prefix_template / default_app_id；
  本凭据窗口已回读，结果见 docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md）。
  实测: HTTP 200 / envelope BOOT_0000 / 二次回读 identity MATCH。

### 8 udc.appinfo.get_deploy_info
- method: GET
- path（控制器原路径）: deploy-info　⚠类级 @RequestMapping 缺省（value 为空，无前缀），
  完整路径仅由方法级 deploy-info 构成；未拼任何网关/service 前缀（UNVERIFIED）
- 参数形态: java.lang.String（currentAppName，query）
- 返回 DTO: SingleResponse<String>
- evidence: artifact=udc-starter-runtime-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseAppInfoController;
  method=getDeployInfo(String); class_sha256=deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95
- LIVE 回读条件: **已解决**（凭据引用 config/environments.yaml:environments.test2.credential.ref；
  路由/前缀/appId 见 test2 键 gateway_base / gateway_prefix_template / default_app_id；
  本凭据窗口已回读，结果见 docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md）。
  实测: HTTP 404 / envelope non-json(HTTP 404) / 二次回读 identity MISMATCH。

### 9 udc.page.check_exists
- method: POST
- path（控制器原路径）: udc-runtime/meta-data/check-page-exists
- 参数形态: java.util.List<UdcRtPageExistsDto>（请求体）
- 返回 DTO: ListResponse<Boolean>
- evidence: artifact=udc-starter-runtime-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController;
  method=checkPageExistsByConditions(List); class_sha256=7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02
- LIVE 回读条件: 需真实 udc-runtime 网关 + 一个页面存在性条件列表；断言 ListResponse 包裹 Boolean 列表。
  本轮不做。

### 10 udc.page.select_host_only_pages
- method: POST
- path（控制器原路径）: udc-runtime/meta-data/select-host-and-only-page-pages
- 参数形态: com.seeyon.boot.starter.extmetadata.dto.request.UdcPagesMetaDataSearchDto（请求体）
- 返回 DTO: ListResponse<UdcMainPageMetadataDto>
- evidence: artifact=udc-starter-runtime-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController;
  method=selectHostAppAndOnlyPageAppPages(UdcPagesMetaDataSearchDto);
  class_sha256=7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02
- LIVE 回读条件: 需真实 udc-runtime 网关 + 一个页面检索 DTO；断言 ListResponse 包裹
  UdcMainPageMetadataDto。本轮不做。

### 11 udc.database.query_data
- method: GET
- path（控制器原路径）: udc-runtime/database/query-data　⚠GET 携带请求体
  RuntimeDataBaseQueryDataReqDto（源码实测 GET 方法带请求参数），未美化
- 参数形态: RuntimeDataBaseQueryDataReqDto（query/请求体）
- 返回 DTO: SingleResponse<UdcRuntimeDatabaseQueryRespDto>
- evidence: artifact=udc-starter-runtime-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.udcrt.controller.UdcRuntimeDatabaseController;
  method=queryData(RuntimeDataBaseQueryDataReqDto); class_sha256=588bc1cf97cf53357ce0a851d16eb28244b6a9607aa5c813b80e4c2c8d4b3c48
- LIVE 回读条件: **已解决**（凭据引用 config/environments.yaml:environments.test2.credential.ref；
  路由/前缀/appId 见 test2 键 gateway_base / gateway_prefix_template / default_app_id；
  本凭据窗口已回读，结果见 docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md）。
  实测: HTTP 200 / envelope BOOT_3000 / 二次回读 identity MATCH。

### 12 udc.entity.history.select_by_condition
- method: POST
- path（控制器原路径）: udc-runtime/history-metadata/select-by-condition　（类级前缀
  udc-runtime/history-metadata + 方法级 select-by-condition，javap 逐字）
- 参数形态: java.util.Map<String,Object>（请求体）
- 返回 DTO: ListResponse<UdcHistoryMetaDataDto>
- evidence: artifact=udc-starter-customplan-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.customplan.controller.UdcRuntimeHistoryMetaDataController;
  method=selectByCondition(Map); class_sha256=9f197e358d9b7b38e19e1afe280ebcd75b0a2c09f73b29c6f6e0f0cbe025ef1c
- LIVE 回读条件: 需真实 udc-runtime 网关 + 一个历史元数据条件 Map；断言 ListResponse 包裹
  UdcHistoryMetaDataDto。本轮不做。

### 13 udc.entity.ext.tree
- method: POST
- path（控制器原路径）: udc-runtime/scalability/ext-entity-tree　（类级前缀 udc-runtime/scalability
  + 方法级 ext-entity-tree，javap 逐字）
- 参数形态: java.lang.String（appName）
- 返回 DTO: ListResponse<EntityRuntimeTreeDto>
- evidence: artifact=udc-starter-customplan-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController;
  method=selectMetadataExtEntityTree(String); class_sha256=4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151
- LIVE 回读条件: 需真实 udc-runtime 网关 + 一个 appName；断言 ListResponse 包裹 EntityRuntimeTreeDto。
  本轮不做。

### 14 udc.entity.ext.list
- method: POST
- path（控制器原路径）: udc-runtime/scalability/list-ext-field
- 参数形态: com.seeyon.boot.starter.customplan.dto.ScalabilityFieldQueryDto（请求体）
- 返回 DTO: ListResponse<ScalabilityFieldDto>
- evidence: artifact=udc-starter-customplan-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController;
  method=listExtFileds(ScalabilityFieldQueryDto); class_sha256=4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151
- LIVE 回读条件: 需真实 udc-runtime 网关 + 一个 ScalabilityFieldQueryDto；断言 ListResponse 包裹
  ScalabilityFieldDto。本轮不做。

### 15 udc.entity.ext.available_datatype
- method: POST
- path（控制器原路径）: udc-runtime/scalability/available-datatype
- 参数形态: com.seeyon.boot.starter.customplan.dto.ScalabilityFieldQueryDto（请求体）
- 返回 DTO: ListResponse<String>
- evidence: artifact=udc-starter-customplan-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController;
  method=selectAvailableDatatype(ScalabilityFieldQueryDto); class_sha256=4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151
- LIVE 回读条件: 需真实 udc-runtime 网关 + 一个 ScalabilityFieldQueryDto；断言 ListResponse 包裹
  String 列表。本轮不做。

### 16 udc.entity.ext.attribute
- method: POST
- path（控制器原路径）: udc-runtime/scalability/select-attribute
- 参数形态: com.seeyon.boot.starter.customplan.dto.ScalabilityFieldQueryDto（请求体）
- 返回 DTO: SingleResponse<ScalabilityFieldDto>
- evidence: artifact=udc-starter-customplan-5.3.517.jar; version=5.3.517;
  class=com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController;
  method=selectAttribute(ScalabilityFieldQueryDto); class_sha256=4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151
- LIVE 回读条件: 需真实 udc-runtime 网关 + 一个 ScalabilityFieldQueryDto；断言 SingleResponse 包裹
  ScalabilityFieldDto。本轮不做。

## 负证据（写/破坏语义 GET/POST，禁入只读，已在 MANIFEST.md 排除项登记）
- UdcAppLogController: delete-all / clear-org-manager / clear-runtime-data-source-cache /
  unload-dynamic-app/{appName} / enable-log/{enable} —— @GetMapping 但语义为清除/卸载/开关，非只读。
- UdcAttrSnapshotRtController: delete-by-data-id / delete-by-master-data-id —— GET 名但 delete 语义。
- UdcSerialConfigController: refresh-historical-data/{appName} / cache-evict/{appName} —— GET 名但
  刷新/逐出语义。
- UdcEntityUpdateRtTestController: update-with-fields（唯一方法，POST，写语义）—— 无 entity 只读面。
- udc-starter-customplan（R5）: ScalabilityFieldController.updateBatch(List)（POST，写语义）/
  compensateScalabilityFieldMetadata()（GET，补偿/修复数据写语义）—— 排除入只读。
- 结论: entity 域只读面非真空，正向候选实测 **16 条 ≥8**（11 条 runtime + 5 条 customplan），
  走正向契约分支，不取「域真空负证据」分支。

## 域语义说明
- udc-facade 的 EntityAppService（javap 已落盘）为 API/服务接口单元（selectById/selectByIds/
  selectByName/selectPageByCondition 等 15 个抽象方法），属后端服务契约侧证据，非 HTTP 控制器；
  本任务 HTTP 只读契约以 udc-starter-runtime 控制器为准。EntityAppService.class 未单独算
  class_sha256（未列入 7 目标 class），其方法签名证据见 MANIFEST javap 项。
