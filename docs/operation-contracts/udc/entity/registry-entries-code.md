# UDC 实体域 registry 逐字照抄代码块（registry-entries-code）

> ⚠️ **已并入** `registry-entries.md`（后者为 MERGE 任务的说明 + 条目本体，381 行 vs 本文件 301 行）。
> 本文件是 MERGE 期间的"可直接粘贴代码块"中间件；MERGE 任务已结束，代码块已落入
> `components/platform_operations/registry.py`。保留作历史记录，不再作为入库依据。


用途: 供 UDC-MERGE 任务把本块粘贴进 components/platform_operations/registry.py
（registry.py:6 已 import OperationStatus, UdcOperationContract，本块无需新增 import）。
本块为**独立函数 build_udc_entity_contracts()**，返回 {operation_id: UdcOperationContract}，
MERGE 可整体并入现有契约构建流程；**本文件不改 registry.py（冻结）**。

类型契约（对照 models.py:29-40 与 registry.py:40-51 调用点实测）:
- 每条 UdcOperationContract 严格 10 位置参数，无 *args/**kwargs。
- status = OperationStatus.VERIFIED_STATIC_BYTECODE（枚举名，非裸串）。
- write = False。
- evidence = [dict]（包 list，models.py:37）。
- required_inputs / verification_rules = tuple（models.py:38-39）。
- path 逐字保留 D1/D3 现有控制器原路径与怪值（#3 双斜杠 //query、#8 无前缀 deploy-info、
  #11 GET 携带请求体），**未拼网关/service 前缀（前缀 UNVERIFIED）**。

## 校验
- py_compile: PASS（exit=0，独立落盘副本编译，不 import、不写 registry.py）
- 16 条 × 10 位置参数 AST 自证: ALL 10-positional OK, 0 条用 *args/**kwargs
  （R1-RESUME 11 条 runtime + R5 补扫 5 条 udc-starter-customplan）
- 代码块 SHA-256: e2b82dc3453ac35de3f1d65ef3f83001398566cb5d0ea60954e5977109c618cf
  口径=代码块 17871 字节（双反引号 ```python 与 ``` 之间、不含 fence 标记与结尾换行）的 SHA-256；
  （R5 追加 5 条后由 c438d118/12497B 更新为本值）

```python
#!/usr/bin/env python
# Paste-ready block: UDC entity-domain readonly contracts (11).
# Drop-in for components/platform_operations/registry.py (registry.py:6 already imports
# OperationStatus, UdcOperationContract). NOT a runnable module on its own -- names resolve
# in registry.py scope. py_compile checks SYNTAX ONLY (no import/exec), so undefined
# names are expected and fine here.
#
# Each call passes exactly 10 positional args (models.py:29-40):
#   operation_id, method, path, request_type, response_type,
#   status, write, evidence(list[dict]), required_inputs(tuple), verification_rules(tuple)
#
# Type contract (from models.py + registry.py call-site):
#   status       -> OperationStatus.VERIFIED_STATIC_BYTECODE (enum member, not a bare string)
#   write        -> False
#   evidence     -> wrap the dict in a list
#   required_inputs / verification_rules -> tuples
# Paths are controller-verbatim (no gateway/service prefix appended; prefix = UNVERIFIED).


def build_udc_entity_contracts():
    contracts = {}
    r = "docs/audit/artifacts/udc-entity-5.3.517/"

    # 1 udc.serial.select_entity_list
    ev = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.udcrt.controller.UdcSerialConfigController",
          "method": "selectEntityList(String)",
          "class_sha256": "fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658",
          "javap": r + "UdcSerialConfigController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.serial.select_entity_list"] = UdcOperationContract(
        "udc.serial.select_entity_list", "GET",
        "udc-runtime/serial-config/select-entity-list",
        "java.lang.String",
        "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.EntityGroupAndItemDto>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("appName",),
        ("响应为 SingleResponse 包裹 EntityGroupAndItemDto 且 code 成功",))

    # 2 udc.serial.select_entity_by_serial
    ev = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.udcrt.controller.UdcSerialConfigController",
          "method": "selectEntityBySerial(Map)",
          "class_sha256": "fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658",
          "javap": r + "UdcSerialConfigController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.serial.select_entity_by_serial"] = UdcOperationContract(
        "udc.serial.select_entity_by_serial", "POST",
        "udc-runtime/serial-config/select-entity-by-serial-id",
        "java.util.Map<String, java.lang.Object>",
        "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.extmetadata.dto.UdcEntityMetaDataDto>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("serialKey(Map)",),
        ("响应为 ListResponse 包裹 UdcEntityMetaDataDto 列表",))

    # 3 udc.entity_data.query_form_data  (path //query 双斜杠为源值逐字照录，勿美化)
    ev = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.udcrt.controller.UdcFormDataQueryController",
          "method": "queryFormData(EntityDataRequestDto)",
          "class_sha256": "cabd312210665274361568181b6d41b9a86f7ed13f1dba7e3f844dc2e5ea5584",
          "javap": r + "UdcFormDataQueryController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.entity_data.query_form_data"] = UdcOperationContract(
        "udc.entity_data.query_form_data", "POST",
        "udc-runtime/data//query",  # 源值双斜杠（类级 udc-runtime/data + 方法级 /query）
        "com.seeyon.boot.starter.udcrt.dto.EntityDataRequestDto",
        "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.EntityDataResponseDto>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("EntityDataRequestDto(appId,dataId,attrKeys)",),
        ("响应为 SingleResponse 包裹 EntityDataResponseDto；双斜杠路由归一化行为需 LIVE 复核（UNVERIFIED）",))

    # 4 udc.applog.select_app_data_by_id
    ev = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController",
          "method": "selectAppDataById(Long)",
          "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775",
          "javap": r + "UdcAppLogController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.applog.select_app_data_by_id"] = UdcOperationContract(
        "udc.applog.select_app_data_by_id", "GET",
        "udc-runtime/app-log/datalog/{id}",
        "java.lang.Long",
        "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.UdcEntityMonitorLogDto>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("id",),
        ("响应为 SingleResponse 包裹 UdcEntityMonitorLogDto 且 code 成功",))

    # 5 udc.applog.list_app_data_by_dataid
    ev = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController",
          "method": "selectAppDataByDataId(Long)",
          "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775",
          "javap": r + "UdcAppLogController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.applog.list_app_data_by_dataid"] = UdcOperationContract(
        "udc.applog.list_app_data_by_dataid", "GET",
        "udc-runtime/app-log/datalog/list-by-dataid/{dataId}",
        "java.lang.Long",
        "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.udcrt.dto.UdcEntityMonitorLogDto>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("dataId",),
        ("响应为 ListResponse 包裹 UdcEntityMonitorLogDto 列表",))

    # 6 udc.applog.search_app_data_log
    ev = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController",
          "method": "searchAppDataLog(PageRequest)",
          "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775",
          "javap": r + "UdcAppLogController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.applog.search_app_data_log"] = UdcOperationContract(
        "udc.applog.search_app_data_log", "POST",
        "udc-runtime/app-log/datalog/search",
        "com.seeyon.boot.transport.PageRequest",
        "com.seeyon.boot.transport.PageResponse<com.seeyon.boot.starter.udcrt.dto.UdcEntityMonitorLogDto>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("PageRequest(page,size)",),
        ("响应为 PageResponse 包裹 UdcEntityMonitorLogDto",))

    # 7 udc.role.has_system_admin
    ev = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.udcrt.controller.UdcRoleRtController",
          "method": "search(String)",
          "class_sha256": "ed024802b6c205041e4368840993412be184ff67c5f9b12938bee5a13a2aae47",
          "javap": r + "UdcRoleRtController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.role.has_system_admin"] = UdcOperationContract(
        "udc.role.has_system_admin", "GET",
        "udc-runtime/udc-role/has-system-admin/{appName}",
        "java.lang.String",
        "com.seeyon.boot.transport.SingleResponse<java.lang.Boolean>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("appName",),
        ("响应为 SingleResponse 包裹 Boolean（true=该 app 系统管理员）",))

    # 8 udc.appinfo.get_deploy_info  (类级 @RequestMapping 缺省，完整路径仅方法级 deploy-info，UNVERIFIED 无网关前缀)
    ev = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseAppInfoController",
          "method": "getDeployInfo(String)",
          "class_sha256": "deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95",
          "javap": r + "UdcBaseAppInfoController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.appinfo.get_deploy_info"] = UdcOperationContract(
        "udc.appinfo.get_deploy_info", "GET",
        "deploy-info",  # 类级 req-mapping 缺省；未拼网关/service 前缀（UNVERIFIED）
        "java.lang.String",
        "com.seeyon.boot.transport.SingleResponse<java.lang.String>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("currentAppName",),
        ("响应为 SingleResponse 包裹 String（部署信息 JSON）；部署 context-path 需 LIVE 确认（UNVERIFIED）",))

    # 9 udc.page.check_exists
    ev = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController",
          "method": "checkPageExistsByConditions(List)",
          "class_sha256": "7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02",
          "javap": r + "UdcRtPageInfoController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.page.check_exists"] = UdcOperationContract(
        "udc.page.check_exists", "POST",
        "udc-runtime/meta-data/check-page-exists",
        "java.util.List<com.seeyon.boot.starter.udcrt.dto.UdcRtPageExistsDto>",
        "com.seeyon.boot.transport.ListResponse<java.lang.Boolean>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("UdcRtPageExistsDto(appId,pageId) list",),
        ("响应为 ListResponse 包裹 Boolean 列表（每项=该页面是否存在）",))

    # 10 udc.page.select_host_only_pages
    ev = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController",
          "method": "selectHostAppAndOnlyPageAppPages(UdcPagesMetaDataSearchDto)",
          "class_sha256": "7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02",
          "javap": r + "UdcRtPageInfoController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.page.select_host_only_pages"] = UdcOperationContract(
        "udc.page.select_host_only_pages", "POST",
        "udc-runtime/meta-data/select-host-and-only-page-pages",
        "com.seeyon.boot.starter.extmetadata.dto.request.UdcPagesMetaDataSearchDto",
        "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.extmetadata.dto.UdcMainPageMetadataDto>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("UdcPagesMetaDataSearchDto",),
        ("响应为 ListResponse 包裹 UdcMainPageMetadataDto",))

    # 11 udc.database.query_data  (GET 携带请求体，源码实测，勿改方法)
    ev = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.udcrt.controller.UdcRuntimeDatabaseController",
          "method": "queryData(RuntimeDataBaseQueryDataReqDto)",
          "class_sha256": "588bc1cf97cf53357ce0a851d16eb28244b6a9607aa5c813b80e4c2c8d4b3c48",
          "javap": r + "UdcRuntimeDatabaseController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.database.query_data"] = UdcOperationContract(
        "udc.database.query_data", "GET",
        "udc-runtime/database/query-data",  # GET 携带请求体 RuntimeDataBaseQueryDataReqDto（源码实测）
        "com.seeyon.boot.starter.udcrt.dto.RuntimeDataBaseQueryDataReqDto",
        "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.UdcRuntimeDatabaseQueryRespDto>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("RuntimeDataBaseQueryDataReqDto(dataSource,table,condition)",),
        ("响应为 SingleResponse 包裹 UdcRuntimeDatabaseQueryRespDto；GET 带请求体语义需 LIVE 复核",))

    # ---- R5: udc-starter-customplan 5.3.517（实体域完整性补扫）----
    r2 = "docs/audit/artifacts/udc-entity-customplan-5.3.517/"

    # 12 udc.entity.history.select_by_condition
    ev = {"source": "local-maven", "artifact": "udc-starter-customplan-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.customplan.controller.UdcRuntimeHistoryMetaDataController",
          "method": "selectByCondition(Map)",
          "class_sha256": "9f197e358d9b7b38e19e1afe280ebcd75b0a2c09f73b29c6f6e0f0cbe025ef1c",
          "javap": r2 + "UdcRuntimeHistoryMetaDataController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.entity.history.select_by_condition"] = UdcOperationContract(
        "udc.entity.history.select_by_condition", "POST",
        "udc-runtime/history-metadata/select-by-condition",  # 类级 udc-runtime/history-metadata + 方法级 select-by-condition
        "java.util.Map<String, java.lang.Object>",
        "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.customplan.dto.UdcHistoryMetaDataDto>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("Map(条件键值)",),
        ("响应为 ListResponse 包裹 UdcHistoryMetaDataDto 列表",))

    # 13 udc.entity.ext.tree
    ev = {"source": "local-maven", "artifact": "udc-starter-customplan-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController",
          "method": "selectMetadataExtEntityTree(String)",
          "class_sha256": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151",
          "javap": r2 + "ScalabilityFieldController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.entity.ext.tree"] = UdcOperationContract(
        "udc.entity.ext.tree", "POST",
        "udc-runtime/scalability/ext-entity-tree",  # 类级 udc-runtime/scalability + 方法级 ext-entity-tree
        "java.lang.String",
        "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.customplan.dto.EntityRuntimeTreeDto>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("appName",),
        ("响应为 ListResponse 包裹 EntityRuntimeTreeDto（实体扩展树）",))

    # 14 udc.entity.ext.list
    ev = {"source": "local-maven", "artifact": "udc-starter-customplan-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController",
          "method": "listExtFileds(ScalabilityFieldQueryDto)",
          "class_sha256": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151",
          "javap": r2 + "ScalabilityFieldController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.entity.ext.list"] = UdcOperationContract(
        "udc.entity.ext.list", "POST",
        "udc-runtime/scalability/list-ext-field",
        "com.seeyon.boot.starter.customplan.dto.ScalabilityFieldQueryDto",
        "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.customplan.dto.ScalabilityFieldDto>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("ScalabilityFieldQueryDto",),
        ("响应为 ListResponse 包裹 ScalabilityFieldDto（扩展字段列表）",))

    # 15 udc.entity.ext.available_datatype
    ev = {"source": "local-maven", "artifact": "udc-starter-customplan-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController",
          "method": "selectAvailableDatatype(ScalabilityFieldQueryDto)",
          "class_sha256": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151",
          "javap": r2 + "ScalabilityFieldController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.entity.ext.available_datatype"] = UdcOperationContract(
        "udc.entity.ext.available_datatype", "POST",
        "udc-runtime/scalability/available-datatype",
        "com.seeyon.boot.starter.customplan.dto.ScalabilityFieldQueryDto",
        "com.seeyon.boot.transport.ListResponse<java.lang.String>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("ScalabilityFieldQueryDto",),
        ("响应为 ListResponse 包裹 String（可用数据类型列表）",))

    # 16 udc.entity.ext.attribute
    ev = {"source": "local-maven", "artifact": "udc-starter-customplan-5.3.517.jar", "version": "5.3.517",
          "class": "com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController",
          "method": "selectAttribute(ScalabilityFieldQueryDto)",
          "class_sha256": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151",
          "javap": r2 + "ScalabilityFieldController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
    contracts["udc.entity.ext.attribute"] = UdcOperationContract(
        "udc.entity.ext.attribute", "POST",
        "udc-runtime/scalability/select-attribute",
        "com.seeyon.boot.starter.customplan.dto.ScalabilityFieldQueryDto",
        "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.customplan.dto.ScalabilityFieldDto>",
        OperationStatus.VERIFIED_STATIC_BYTECODE, False,
        [ev], ("ScalabilityFieldQueryDto",),
        ("响应为 SingleResponse 包裹 ScalabilityFieldDto（单属性）",))

    return contracts


__all__ = ["build_udc_entity_contracts"]

```

<!-- py_compile PASS (exit=0); 16 x 10 positional AST-verified; block sha256 e2b82dc3453ac35de3f1d65ef3f83001398566cb5d0ea60954e5977109c618cf
     口径=代码块 17871 字节（双反引号 fence 之间、不含 fence 标记与 1 个结尾换行）的 SHA-256
     R5 追加 5 条 customplan 后由 c438d118/12497B 更新为本值 -->
