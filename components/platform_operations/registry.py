"""最小 UDC readonly operation contracts。"""
from __future__ import annotations

from dataclasses import replace

from .models import OperationRequest, OperationStatus, UdcOperationContract
from ._config_loader import source_jar_ref


class UdcOperationRegistry:
    def __init__(self, contracts):
        self._contracts = dict(contracts)

    @classmethod
    def default(cls):
        evidence = {"source": "test2-container", "artifact": "udc-web-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.udc.controller.EntityController", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        specs = [
            ("udc.entity.create", "POST", "/udc/entity", "com.seeyon.udc.common.dto.EntityDto", "SingleResponse<Long>", True, True, ()),
            ("udc.entity.update", "POST", "/udc/entity/update", "EntityDto", "SingleResponse<Integer>", True, False, ()),
            ("udc.entity.select", "GET", "/udc/entity/{id}", "entity_id", "SingleResponse<EntityDto>", False, True, ("entity_id",)),
            ("udc.entity.search", "POST", "/udc/entity/search-list", "Map<String,Object> + Sort", "ListResponse<EntityDto>", False, False, ()),
            ("udc.entity.search.term", "GET", "/udc/entity/search/term", "appId + term + Sort", "ListResponse<EntityDto>", False, False, ()),
            ("udc.entity.primary.by_app", "GET", "/udc/entity/primary/select-by-appid/{appId}", "application_id", "ListResponse<EntityDto>", False, True, ("application_id",)),
            ("udc.entity.tree.by_app", "GET", "/udc/entity/select-by-appid/tree/{appId}", "application_id", "ListResponse<EntityDto>", False, True, ("application_id",)),
            ("udc.entity.all.by_app", "GET", "/udc/entity/select-all-by-appid/{appId}", "application_id", "ListResponse<EntityDto>", False, True, ("application_id",)),
            ("udc.entity.root_id", "GET", "/udc/entity/primary/select-root/{id}", "entity_id", "SingleResponse<Long>", False, True, ("entity_id",)),
            ("udc.entity.all.by_entity", "GET", "/udc/entity/select-all-by-entityId/{id}", "entity_id", "ListResponse<EntityDto>", False, True, ("entity_id",)),
            ("udc.entity.attribute.create", "POST", "/udc/entity/attribute", "AttributeDto", "SingleResponse<Long>", True, False, ()),
            ("udc.entity.attribute.create_batch", "POST", "/udc/entity/attribute-batch", "List<AttributeDto>", "SingleResponse<Integer>", True, False, ()),
            ("udc.entity.attribute.update", "POST", "/udc/entity/attribute/update", "AttributeDto", "SingleResponse<Integer>", True, False, ()),
            ("udc.entity.attribute.delete", "POST", "/udc/entity/attribute/delete", "attribute_id", "SingleResponse<Integer>", True, False, ()),
            ("udc.entity.attribute.select", "GET", "/udc/entity/attribute/{id}", "attribute_id", "SingleResponse<AttributeDto>", False, True, ("attribute_id",)),
            ("udc.entity.attribute.search", "POST", "/udc/entity/attribute/search-list", "Map<String,Object> + Sort", "ListResponse<AttributeDto>", False, False, ()),
            ("udc.entity.attribute.search.term", "GET", "/udc/entity/attribute/search/term", "appId + term + Sort", "ListResponse<AttributeDto>", False, False, ()),
            ("udc.entity.attribute.by_primary", "GET", "/udc/entity/attribute/select-by-primary/{id}", "entity_id", "ListResponse<AttributeDto>", False, True, ("entity_id",)),
            ("udc.entity.attribute.all_by_entity", "GET", "/udc/entity/attribute/select-all-by-entity-id/{entityId}", "entity_id", "ListResponse<AttributeDto>", False, True, ("entity_id",)),
            ("udc.entity.attributes.list", "GET", "/udc/entity/{entityId}/attributes", "entity_id", "ListResponse<AttributeDto>", False, True, ("entity_id",)),
        ]
        contracts = {}
        for operation, method, path, request_type, response_type, write, verified, inputs in specs:
            contracts[operation] = UdcOperationContract(operation, method, path, request_type, response_type, OperationStatus.VERIFIED_STATIC_BYTECODE if verified else OperationStatus.UNKNOWN, write, [evidence], inputs, ("response envelope", "business identity"))
        contracts["udc.entity.get"] = replace(contracts["udc.entity.select"], operation_id="udc.entity.get")
        contracts["udc.entity.list"] = replace(contracts["udc.entity.all.by_app"], operation_id="udc.entity.list")
        contracts["udc.attribute.list"] = replace(contracts["udc.entity.attribute.all_by_entity"], operation_id="udc.attribute.list")
        contracts["udc.application.get"] = UdcOperationContract("udc.application.get", "GET", "/udc/application/{id}", "application_id", "SingleResponse<ApplicationDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [evidence], ("application_id",), ("response envelope", "application identity"))
        microflow_evidence = {"source": "offline-decompiled", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcFunctionNodeController", "method": "selectFunctionNodeTreeMetaData", "class_sha256": "efd8f9143d0fd44d4e3033a4bb4877c09e891a1049f66382df1ae1d7d08a7748", "javap": "docs/audit/artifacts/udc-runtime-5.3.517/UdcFunctionNodeController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.microflow.function_node_tree"] = UdcOperationContract("udc.microflow.function_node_tree", "GET", "udc-runtime/meta-data/select-function-node-tree/{appName}", "String appName(SingleRequest)", "ListResponse<UdcFunctionNodeMetadataDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [microflow_evidence], ("appName",), ("同一 appName 回读节点树 identity_matches", "响应非空 UdcFunctionNodeMetadataDto 列表"))
        local_javap = source_jar_ref("udc-starter-runtime", "5.3.517") + " (javap -p -v, 只读离线)"
        datatype_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcDataTypeController", "method": "getDataTypes", "class_sha256": "03b3977b50574208eaad2b1925a80520a4686b268a56bacd35b87a144854bc38", "javap": local_javap, "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.datatype.get_all"] = UdcOperationContract("udc.datatype.get_all", "GET", "udc-runtime/datatype/getAll", "()", "ListResponse<DataTypeDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [datatype_evidence], (), ("同一 target 回读 datatype 列表 identity_matches", "响应非空 DataTypeDto 列表", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        applog_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController", "method": "selectAppDataById", "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775", "javap": local_javap, "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.applog.select_by_id"] = UdcOperationContract("udc.applog.select_by_id", "GET", "udc-runtime/app-log/datalog/{id}", "Long id(SingleRequest)", "SingleResponse<UdcEntityMonitorLogDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [applog_evidence], ("id",), ("同一 id 回读节点日志 identity_matches", "响应 UdcEntityMonitorLogDto 非空或 target 不存在", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        page_log_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcRtPageLogController", "method": "search", "class_sha256": "86efc8a3b0924cb46f4d8ca11b527ba9129f3dd6d938e345c5cb11be15038c5e", "javap": "docs/audit/artifacts/udc-page-5.3.517/UdcRtPageLogController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        page_info_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController", "method": "checkPageExistsByConditions", "class_sha256": "7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02", "javap": "docs/audit/artifacts/udc-page-5.3.517/UdcRtPageInfoController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.page_log.search"] = UdcOperationContract("udc.page_log.search", "POST", "udc-runtime/rt-page-log/search", "PageDtoRequest<UdcRtPageLogSearchDto>(RequestBody)", "PageResponse<UdcRtPageLogSearchResultDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [page_log_evidence], ("query",), ("同一 query 条件回读 identity_matches", "响应 data 为 UdcRtPageLogSearchResultDto 分页列表", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        contracts["udc.page_log.search_non_metadata"] = UdcOperationContract("udc.page_log.search_non_metadata", "POST", "udc-runtime/rt-page-log/search-non-metadata", "PageDtoRequest<UdcRtPageLogSearchDto>(RequestBody)", "PageResponse<UdcRtPageLogSearchResultDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [page_log_evidence], ("query",), ("同一 query 条件回读 identity_matches", "与 udc.page_log.search 差异仅限元数据字段（LIVE 样本确认前不作断言）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        contracts["udc.page_info.check_exists"] = UdcOperationContract("udc.page_info.check_exists", "POST", "udc-runtime/meta-data/check-page-exists", "List<UdcRtPageExistsDto>(RequestBody, 参数名 pageExistsDtoList)", "ListResponse<Boolean>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [page_info_evidence], ("pageExistsDtoList",), ("同一条件列表回读 identity_matches", "存在样本恒 true / 不存在样本恒 false", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        contracts["udc.page_info.select_host_and_only_page"] = UdcOperationContract("udc.page_info.select_host_and_only_page", "POST", "udc-runtime/meta-data/select-host-and-only-page-pages", "UdcPagesMetaDataSearchDto(RequestBody, 参数名 request)", "ListResponse<UdcMainPageMetadataDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [page_info_evidence], ("request",), ("同一 UdcPagesMetaDataSearchDto 回读 identity_matches", "响应为 UdcMainPageMetadataDto 非空列表（或条件致空列表亦自证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        metadata_anchor_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController", "method": "selectHostAppAndOnlyPageAppPages", "class_sha256": "7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02", "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcRtPageInfoController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "运行态元数据层（平台 meta-data 接口）；非设计态配置/生成物/物理表/Redis 缓存。该端点 javap 原文为 @PostMapping（非 GET）：registry 登记=契约声明，执行链仅放行 GET，故本契约在 PlatformOperationLayer 上为 DENIED/POLICY_DENIED 直至运行态确证其为只读读面（POST 读语义）；属已知边界，非 FAIL。"}
        contracts["udc.metadata.page_tree"] = UdcOperationContract("udc.metadata.page_tree", "POST", "udc-runtime/meta-data/select-host-and-only-page-pages", "UdcPagesMetaDataSearchDto(RequestBody)", "ListResponse<UdcMainPageMetadataDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [metadata_anchor_evidence], ("UdcPagesMetaDataSearchDto",), ("回读该应用页面树元数据且 identity_matches（同一 target 双读 strip(traceId) 一致）", "响应非空 UdcMainPageMetadataDto 列表", "运行态需确证该 POST 端点为只读读面（不强行升 GET；执行层放行前维持 POLICY_DENIED）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        metadata_page_exists_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController", "method": "checkPageExistsByConditions", "class_sha256": "7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02", "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcRtPageInfoController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "运行态元数据层存在性探测面（平台 meta-data 接口）；非设计态配置/生成物/物理表/Redis 缓存。返回 ListResponse<Boolean>：按 08:45 元数据锚点规则②（Boolean/HTTP 200 不作 identity 锚点），本契约为存在性探测、非验收 identity 面。端点 javap 原文为 @PostMapping：执行链仅放行 GET，故在 PlatformOperationLayer 为 DENIED/POLICY_DENIED（与 C4 同边界），可执行性留活体（R11/P4）。"}
        contracts["udc.metadata.page_exists_check"] = UdcOperationContract("udc.metadata.page_exists_check", "POST", "udc-runtime/meta-data/check-page-exists", "List<UdcRtPageExistsDto>(RequestBody)", "ListResponse<Boolean>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [metadata_page_exists_evidence], ("UdcRtPageExistsDto",), ("存在性探测面：响应为 Boolean 列表，逐条对应入参页面是否存在", "按 08:45 规则② Boolean/HTTP 200 不作 identity 锚点，本契约非验收 identity 面", "POST 执行层不放行（与 C4 同边界），运行态需确证其为只读探测（不强行升 GET；放行前维持 POLICY_DENIED）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        applog_microflow_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController", "method": "search", "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775", "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "运行态日志层（app-log microflow 搜索面，非 meta-data 层）；微流程只读契约族 C6（与 C7/C8 同 class，逐条独立 evidence，不复用 C3）。方法签名锚点 javap L469 PageResponse<MicroFlowLogResultDto> search(PageDtoRequest<MicroFlowLogSearchDto>)，后端 UdcAppLogAppService.search。端点 javap 原文为 @PostMapping：执行链仅放行 GET，故在 PlatformOperationLayer 为 DENIED/POLICY_DENIED（与 C4/C5 同边界），可执行性留活体（P4）。"}
        contracts["udc.applog.search_microflow"] = UdcOperationContract("udc.applog.search_microflow", "POST", "udc-runtime/app-log/search/microflow", "PageDtoRequest<MicroFlowLogSearchDto>(RequestBody)", "PageResponse<MicroFlowLogResultDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [applog_microflow_evidence], ("MicroFlowLogSearchDto",), ("回读该应用微流程日志且 identity_matches（同一 target 双读 strip(traceId) 一致）", "响应非空 MicroFlowLogResultDto 分页列表", "运行态需确证该 POST 端点为只读读面（不强行升 GET；执行层放行前维持 POLICY_DENIED）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        applog_microflow_details_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController", "method": "searchDetails", "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775", "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "运行态日志层（app-log microflow 详情搜索面，非 meta-data 层）；微流程只读契约族 C7（与 C6/C8 同 class，逐条独立 evidence，不复用 C6）。方法签名锚点 javap L504 PageResponse<MicroFlowLogDetailsResultDto> searchDetails(PageDtoRequest<MicroFlowLogDetailsSearchDto>)，后端 UdcAppLogAppService.searchDetails。端点 javap 原文为 @PostMapping：执行链仅放行 GET，故在 PlatformOperationLayer 为 DENIED/POLICY_DENIED（与 C4/C5/C6 同边界），可执行性留活体（P4）。"}
        contracts["udc.applog.search_details_microflow"] = UdcOperationContract("udc.applog.search_details_microflow", "POST", "udc-runtime/app-log/search-details/microflow", "PageDtoRequest<MicroFlowLogDetailsSearchDto>(RequestBody)", "PageResponse<MicroFlowLogDetailsResultDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [applog_microflow_details_evidence], ("MicroFlowLogDetailsSearchDto",), ("回读该应用微流程日志详情且 identity_matches（同一 target 双读 strip(traceId) 一致）", "响应非空 MicroFlowLogDetailsResultDto 分页列表", "运行态需确证该 POST 端点为只读读面（不强行升 GET；执行层放行前维持 POLICY_DENIED）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        applog_microflow_flowlog_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController", "method": "searchFlowDetails", "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775", "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "运行态日志层（app-log microflow flowLog 详情面，非 meta-data 层）；微流程只读契约族 C8（与 C3/C6/C7 同 class，逐条独立 evidence，不复用 C7）。方法签名锚点 javap L539 SingleResponse<MicroFlowFlowLogResultDto> searchFlowDetails(MicroFlowLogDetailsSearchDto)，后端 UdcAppLogAppService.searchDetails4FlowLog。请求为裸 MicroFlowLogDetailsSearchDto(RequestBody)，非 PageDtoRequest 包装，响应 SingleResponse<MicroFlowFlowLogResultDto>。端点 javap 原文为 @PostMapping(L565)：执行链仅放行 GET，故在 PlatformOperationLayer 为 DENIED/POLICY_DENIED（与 C4/C5/C6/C7 同边界），可执行性留活体（P4）。"}
        contracts["udc.applog.search_details_microflow_flowlog"] = UdcOperationContract("udc.applog.search_details_microflow_flowlog", "POST", "udc-runtime/app-log/search-details/microflow/flowLog", "MicroFlowLogDetailsSearchDto(RequestBody)", "SingleResponse<MicroFlowFlowLogResultDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [applog_microflow_flowlog_evidence], ("MicroFlowLogDetailsSearchDto",), ("回读该应用微流程 flowLog 且 identity_matches（同一 target 双读 strip(traceId) 一致）", "响应非空 MicroFlowFlowLogResultDto", "运行态需确证该 POST 端点为只读读面（不强行升 GET；执行层放行前维持 POLICY_DENIED）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        flow_bpm_node_info_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-customplan-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.customplan.controller.BpmNodeInfoController", "method": "selectByComplexCondition", "class_sha256": "95e1752d83c9152e6236d825b2aaea1e82fd60516b1f7c2a3c2f2249df395bb2", "javap": "docs/audit/artifacts/udc-flow-5.3.517/BpmNodeInfoController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "BPM 集成层（node-info 节点权限搜索面，customplan 制品；类级 @RequestMapping=node-info 非 udc-runtime 前缀）；flow 域只读契约。请求 CBpmNodePermissionRequestDto。端点 javap 原文为 @PostMapping：执行链仅放行 GET，故在 PlatformOperationLayer 为 DENIED/POLICY_DENIED（与 C4-C8 同边界），可执行性留活体（P4）。网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）。"}
        contracts["udc.flow.bpm_node_info_search"] = UdcOperationContract("udc.flow.bpm_node_info_search", "POST", "node-info/search", "CBpmNodePermissionRequestDto(SingleRequest)", "SingleResponse<BpmNodePermission4PageDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [flow_bpm_node_info_evidence], ("CBpmNodePermissionRequestDto(user_id 由 RequestContext 回填),",), ("同一条件回读节点权限 identity_matches", "响应 BpmNodePermission4PageDto 非空", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        flow_form_data_query_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcFormDataQueryController", "method": "queryFormData", "class_sha256": "cabd312210665274361568181b6d41b9a86f7ed13f1dba7e3f844dc2e5ea5584", "javap": "docs/audit/artifacts/udc-flow-5.3.517/UdcFormDataQueryController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "运行态数据层（udc-runtime/data 实体数据查询面）；flow 域只读契约。端点 javap 原文为 @PostMapping：执行链仅放行 GET，故在 PlatformOperationLayer 为 DENIED/POLICY_DENIED（与 C4-C8 同边界），可执行性留活体（P4）。网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）。"}
        contracts["udc.flow.form_data_query"] = UdcOperationContract("udc.flow.form_data_query", "POST", "udc-runtime/data/query", "EntityDataRequestDto(SingleRequest)", "SingleResponse<EntityDataResponseDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [flow_form_data_query_evidence], ("EntityDataRequestDto(entity_code+业务键),",), ("同一业务键回读实体数据 identity_matches", "响应 EntityDataResponseDto 命中目标实体", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        flow_data_flow_map_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMapController", "method": "selectById", "class_sha256": "455df593d43558055e01d69f4aacc70ce337ec80b4f7275adc471c49a22d1d95", "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMapController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "运行态数据流层（udc-runtime/data-flow-map 映射表读面）；flow 域只读契约。本条=get_by_id（GET 读型，执行链可放行 effective=True）。网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）。"}
        contracts["udc.flow.data_flow_map_get_by_id"] = UdcOperationContract("udc.flow.data_flow_map_get_by_id", "GET", "udc-runtime/data-flow-map/{id}", "Long id(SingleRequest)", "SingleResponse<DataFlowRtMapDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [flow_data_flow_map_evidence], ("id",), ("同一 id 回读 dataFlowMap identity_matches", "响应 DataFlowRtMapDto.id 与入参一致", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        flow_data_flow_map_search_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMapController", "method": "selectByCondition", "class_sha256": "455df593d43558055e01d69f4aacc70ce337ec80b4f7275adc471c49a22d1d95", "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMapController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "运行态数据流层（udc-runtime/data-flow-map 条件搜索面）；flow 域只读契约。端点 javap 原文为 @PostMapping：执行链仅放行 GET，故在 PlatformOperationLayer 为 DENIED/POLICY_DENIED（与 C4-C8 同边界），可执行性留活体（P4）。网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）。"}
        contracts["udc.flow.data_flow_map_search"] = UdcOperationContract("udc.flow.data_flow_map_search", "POST", "udc-runtime/data-flow-map/search", "DataFlowRtMapQueryDto(SingleRequest)", "ListResponse<DataFlowRtMapDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [flow_data_flow_map_search_evidence], ("DataFlowRtMapQueryDto(过滤条件),",), ("同一过滤条件回读列表 identity_matches", "响应非空 DataFlowRtMapDto 列表", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        flow_data_flow_mapping_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController", "method": "selectById", "class_sha256": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8", "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMappingController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "运行态数据流层（udc-runtime/data-flow-mapping 映射明细读面）；flow 域只读契约。本条=get_by_id（GET 读型，执行链可放行 effective=True）。网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）。"}
        contracts["udc.flow.data_flow_mapping_get_by_id"] = UdcOperationContract("udc.flow.data_flow_mapping_get_by_id", "GET", "udc-runtime/data-flow-mapping/{id}", "Long id(SingleRequest)", "SingleResponse<DataFlowRtMappingDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [flow_data_flow_mapping_evidence], ("id",), ("同一 id 回读 dataFlowMapping identity_matches", "响应 DataFlowRtMappingDto.id 与入参一致", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        flow_data_flow_mapping_search_orig_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController", "method": "selectOriginalMappingList", "class_sha256": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8", "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMappingController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "运行态数据流层（udc-runtime/data-flow-mapping 源映射列表搜索面）；flow 域只读契约。端点 javap 原文为 @PostMapping：执行链仅放行 GET，故在 PlatformOperationLayer 为 DENIED/POLICY_DENIED（与 C4-C8 同边界），可执行性留活体（P4）。网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）。"}
        contracts["udc.flow.data_flow_mapping_search_original"] = UdcOperationContract("udc.flow.data_flow_mapping_search_original", "POST", "udc-runtime/data-flow-mapping/search-original", "OriginalDataFlowMappingListQueryDto(SingleRequest)", "ListResponse<DataFlowRtMappingDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [flow_data_flow_mapping_search_orig_evidence], ("OriginalDataFlowMappingListQueryDto(源映射条件),",), ("同一条件回读源映射列表 identity_matches", "响应非空 DataFlowRtMappingDto 列表", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        flow_data_flow_mapping_init_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController", "method": "selectMappingInitData", "class_sha256": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8", "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMappingController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "运行态数据流层（udc-runtime/data-flow-mapping 编辑初始数据读面，只读探测非写）；flow 域只读契约。端点 javap 原文为 @PostMapping：执行链仅放行 GET，故在 PlatformOperationLayer 为 DENIED/POLICY_DENIED（与 C4-C8 同边界），可执行性留活体（P4）。网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）。"}
        contracts["udc.flow.data_flow_mapping_init_data"] = UdcOperationContract("udc.flow.data_flow_mapping_init_data", "POST", "udc-runtime/data-flow-mapping/init-data", "DataFlowMappingInitQueryDto(SingleRequest)", "SingleResponse<DataFlowRtEditInitialDataDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [flow_data_flow_mapping_init_evidence], ("DataFlowMappingInitQueryDto(初始化条件),",), ("同一条件回读编辑初始数据 identity_matches", "响应 DataFlowRtEditInitialDataDto 字段齐备", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        flow_data_flow_mapping_detail_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController", "method": "selectDetailByCondition", "class_sha256": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8", "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMappingController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "运行态数据流层（udc-runtime/data-flow-mapping 映射详情读面）；flow 域只读契约。端点 javap 原文为 @PostMapping：执行链仅放行 GET，故在 PlatformOperationLayer 为 DENIED/POLICY_DENIED（与 C4-C8 同边界），可执行性留活体（P4）。网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）。"}
        contracts["udc.flow.data_flow_mapping_detail"] = UdcOperationContract("udc.flow.data_flow_mapping_detail", "POST", "udc-runtime/data-flow-mapping/detail", "DataFlowOriginalMappingQueryDto(SingleRequest)", "SingleResponse<DataFlowRtMappingDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [flow_data_flow_mapping_detail_evidence], ("DataFlowOriginalMappingQueryDto(详情条件),",), ("同一条件回读映射详情 identity_matches", "响应 DataFlowRtMappingDto 返回目标详情", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        appbasic_custom_app_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.CustomApplicationController", "method": "selectListByConditions", "class_sha256": "d3e82d8bbc65dc92d5f9d30532159f1d10169f2aef1eae6ab67c70d7ad75ae55", "javap": "docs/audit/artifacts/udc-app-basic/CustomApplicationController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.application.search.no_page"] = UdcOperationContract("udc.application.search.no_page", "POST", "udc-runtime/custom-app/search-no-page", "Map<String,Object> params + Sort (MultiRequestBody)", "ListResponse<CustomApplicationDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [appbasic_custom_app_evidence], ("params", "sort"), ("同一 conditions 回读 application 列表 identity_matches", "响应非空 CustomApplicationDto 列表", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        appbasic_custom_app_page_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.CustomApplicationController", "method": "selectListByConditions", "class_sha256": "d3e82d8bbc65dc92d5f9d30532159f1d10169f2aef1eae6ab67c70d7ad75ae55", "javap": "docs/audit/artifacts/udc-app-basic/CustomApplicationController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "search-page 端点（javap /search-page 方法级映射）对应控制器方法为 selectListByConditions 的 PageInfo 重载（控制器签名 selectListByConditions(PageInfo, Map, Sort)），其方法体调用后端 CustomApplicationAppService.selectPageListByConditions（javap 常量池 Methodref）；控制器方法名以 javap 原文为准（与 no_page 同 method，区别在重载参数）。"}
        contracts["udc.application.search.page"] = UdcOperationContract("udc.application.search.page", "POST", "udc-runtime/custom-app/search-page", "PageInfo + Map<String,Object> + Sort (MultiRequestBody)", "PageResponse<CustomApplicationDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [appbasic_custom_app_page_evidence], ("pageInfo", "params", "sort"), ("固定页码页大小回读 application 分页 identity_matches", "PageResponse total/列表一致", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        appbasic_deploy_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseAppInfoController", "method": "getDeployInfo", "class_sha256": "deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95", "javap": "docs/audit/artifacts/udc-app-basic/com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseAppInfoController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.application.deploy_info"] = UdcOperationContract("udc.application.deploy_info", "GET", "{currentAppName}/app-info/deploy-info", "String currentAppName(PathVariable)", "SingleResponse<String>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [appbasic_deploy_evidence], ("currentAppName",), ("同一 currentAppName 回读部署信息 JSON identity_matches", "响应 SingleResponse<String> 非空", "类级前缀因子类而异（FormAppInfoController={hostAppName}/dynamic-rest/com-seeyon/{currentAppName}/app-info，NormalAppInfoController={currentAppName}/app-info），完整路由 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        appbasic_draft_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.AppDraftController", "method": "select", "class_sha256": "5090304dcb69cd0d3cd7b4e961d6ceff5f41e56d27b60eecf48950a34e5fabb9", "javap": "docs/audit/artifacts/udc-app-basic/com.seeyon.boot.starter.udcrt.controller.AppDraftController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.application.draft.select"] = UdcOperationContract("udc.application.draft.select", "POST", "udc-runtime/app-draft/select", "String dataId(MultiRequestBody, SingleRequest)", "SingleResponse<AppDraftDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [appbasic_draft_evidence], ("dataId",), ("同一 dataId 回读用户草稿 identity_matches", "响应 AppDraftDto 非空或 target 不存在", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        appbasic_draft_exist_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.AppDraftController", "method": "exist", "class_sha256": "5090304dcb69cd0d3cd7b4e961d6ceff5f41e56d27b60eecf48950a34e5fabb9", "javap": "docs/audit/artifacts/udc-app-basic/com.seeyon.boot.starter.udcrt.controller.AppDraftController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.application.draft.exist"] = UdcOperationContract("udc.application.draft.exist", "POST", "udc-runtime/app-draft/exist", "String dataId(MultiRequestBody, SingleRequest)", "SingleResponse<AppDraftExistDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [appbasic_draft_exist_evidence], ("dataId",), ("同一 dataId 回读 exist 布尔值稳定", "响应 AppDraftExistDto 非空", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        # ---- R17: entity 域 13 条只读契约（离线 A1 深化；source=local-maven 照 entity/registry-entries.md 原值；
        #      class_sha256 本轮对本机 jar 重算自证不抄；怪值 #3 双斜杠 / #8 deploy-info 无前缀 / #11 GET 带请求体逐字保留）----
        ent_serial_evidence = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcSerialConfigController", "method": "selectEntityList(String)", "class_sha256": "fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658", "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcSerialConfigController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.serial.select_entity_list"] = UdcOperationContract("udc.serial.select_entity_list", "GET", "udc-runtime/serial-config/select-entity-list", "java.lang.String", "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.EntityGroupAndItemDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [ent_serial_evidence], ("appName",), ("响应为 SingleResponse 包裹 EntityGroupAndItemDto 且 code 成功",))
        ent_serial_by_evidence = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcSerialConfigController", "method": "selectEntityBySerial(Map)", "class_sha256": "fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658", "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcSerialConfigController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.serial.select_entity_by_serial"] = UdcOperationContract("udc.serial.select_entity_by_serial", "POST", "udc-runtime/serial-config/select-entity-by-serial-id", "java.util.Map<String, java.lang.Object>", "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.extmetadata.dto.UdcEntityMetaDataDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [ent_serial_by_evidence], ("serialKey(Map)",), ("响应为 ListResponse 包裹 UdcEntityMetaDataDto 列表",))
        ent_form_data_evidence = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcFormDataQueryController", "method": "queryFormData(EntityDataRequestDto)", "class_sha256": "cabd312210665274361568181b6d41b9a86f7ed13f1dba7e3f844dc2e5ea5584", "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcFormDataQueryController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "双斜杠 udc-runtime/data//query 逐字保留（类级 udc-runtime/data + 方法级 /query）；与已登 F2 udc.flow.form_data_query 同 class(UdcFormDataQueryController cabd3122) 同 method(queryFormData) 同端点但 path 逐字不同（本条双斜杠 vs F2 单斜杠 udc-runtime/data/query）→ 保留双 ID 分域登记（entity md 域内条目），不覆盖 F2；双斜杠路由归一化行为 LIVE 复核 UNVERIFIED（离线不拼接、不美化）。"}
        contracts["udc.entity_data.query_form_data"] = UdcOperationContract("udc.entity_data.query_form_data", "POST", "udc-runtime/data//query", "com.seeyon.boot.starter.udcrt.dto.EntityDataRequestDto", "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.EntityDataResponseDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [ent_form_data_evidence], ("EntityDataRequestDto(appId,dataId,attrKeys)",), ("响应为 SingleResponse 包裹 EntityDataResponseDto；双斜杠路由归一化行为需 LIVE 复核（UNVERIFIED）",))
        ent_applog_list_evidence = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController", "method": "selectAppDataByDataId(Long)", "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775", "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.applog.list_app_data_by_dataid"] = UdcOperationContract("udc.applog.list_app_data_by_dataid", "GET", "udc-runtime/app-log/datalog/list-by-dataid/{dataId}", "java.lang.Long", "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.udcrt.dto.UdcEntityMonitorLogDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [ent_applog_list_evidence], ("dataId",), ("响应为 ListResponse 包裹 UdcEntityMonitorLogDto 列表",))
        ent_applog_search_evidence = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController", "method": "searchAppDataLog(PageRequest)", "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775", "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.applog.search_app_data_log"] = UdcOperationContract("udc.applog.search_app_data_log", "POST", "udc-runtime/app-log/datalog/search", "com.seeyon.boot.transport.PageRequest", "com.seeyon.boot.transport.PageResponse<com.seeyon.boot.starter.udcrt.dto.UdcEntityMonitorLogDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [ent_applog_search_evidence], ("PageRequest(page,size)",), ("响应为 PageResponse 包裹 UdcEntityMonitorLogDto",))
        ent_role_evidence = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcRoleRtController", "method": "search(String)", "class_sha256": "ed024802b6c205041e4368840993412be184ff67c5f9b12938bee5a13a2aae47", "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcRoleRtController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.role.has_system_admin"] = UdcOperationContract("udc.role.has_system_admin", "GET", "udc-runtime/udc-role/has-system-admin/{appName}", "java.lang.String", "com.seeyon.boot.transport.SingleResponse<java.lang.Boolean>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [ent_role_evidence], ("appName",), ("响应为 SingleResponse 包裹 Boolean（true=该 app 系统管理员）",))
        ent_appinfo_evidence = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseAppInfoController", "method": "getDeployInfo(String)", "class_sha256": "deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95", "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcBaseAppInfoController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "完整路由 UNVERIFIED：类级 @RequestMapping 缺省（无前缀），仅方法级 deploy-info，不拼网关/service/子类前缀；与已登 A3 udc.application.deploy_info 同 class(UdcBaseAppInfoController deebcc39) 同 method(getDeployInfo) 但 path 逐字不同（本条 deploy-info vs A3 {currentAppName}/app-info/deploy-info）→ 保留双 ID 分域登记（entity md 域内条目），不覆盖 A3。"}
        contracts["udc.appinfo.get_deploy_info"] = UdcOperationContract("udc.appinfo.get_deploy_info", "GET", "deploy-info", "java.lang.String", "com.seeyon.boot.transport.SingleResponse<java.lang.String>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [ent_appinfo_evidence], ("currentAppName",), ("响应为 SingleResponse 包裹 String（部署信息 JSON）；部署 context-path 需 LIVE 确认（UNVERIFIED）",))
        ent_database_evidence = {"source": "local-maven", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcRuntimeDatabaseController", "method": "queryData(RuntimeDataBaseQueryDataReqDto)", "class_sha256": "588bc1cf97cf53357ce0a851d16eb28244b6a9607aa5c813b80e4c2c8d4b3c48", "javap": "docs/audit/artifacts/udc-entity-5.3.517/UdcRuntimeDatabaseController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE", "note": "GET 携带请求体 RuntimeDataBaseQueryDataReqDto（javap 源码实测原样保留）；GET 带请求体语义需 LIVE 复核（UNVERIFIED，离线不可确证）；不拼网关/service 前缀。"}
        contracts["udc.database.query_data"] = UdcOperationContract("udc.database.query_data", "GET", "udc-runtime/database/query-data", "com.seeyon.boot.starter.udcrt.dto.RuntimeDataBaseQueryDataReqDto", "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.UdcRuntimeDatabaseQueryRespDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [ent_database_evidence], ("RuntimeDataBaseQueryDataReqDto(dataSource,table,condition)",), ("响应为 SingleResponse 包裹 UdcRuntimeDatabaseQueryRespDto；GET 带请求体语义需 LIVE 复核",))
        ent_history_evidence = {"source": "local-maven", "artifact": "udc-starter-customplan-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.customplan.controller.UdcRuntimeHistoryMetaDataController", "method": "selectByCondition(Map)", "class_sha256": "9f197e358d9b7b38e19e1afe280ebcd75b0a2c09f73b29c6f6e0f0cbe025ef1c", "javap": "docs/audit/artifacts/udc-entity-customplan-5.3.517/UdcRuntimeHistoryMetaDataController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.entity.history.select_by_condition"] = UdcOperationContract("udc.entity.history.select_by_condition", "POST", "udc-runtime/history-metadata/select-by-condition", "java.util.Map<String, java.lang.Object>", "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.customplan.dto.UdcHistoryMetaDataDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [ent_history_evidence], ("Map(条件键值)",), ("响应为 ListResponse 包裹 UdcHistoryMetaDataDto 列表",))
        ent_ext_tree_evidence = {"source": "local-maven", "artifact": "udc-starter-customplan-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController", "method": "selectMetadataExtEntityTree(String)", "class_sha256": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151", "javap": "docs/audit/artifacts/udc-entity-customplan-5.3.517/ScalabilityFieldController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.entity.ext.tree"] = UdcOperationContract("udc.entity.ext.tree", "POST", "udc-runtime/scalability/ext-entity-tree", "java.lang.String", "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.customplan.dto.EntityRuntimeTreeDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [ent_ext_tree_evidence], ("appName",), ("响应为 ListResponse 包裹 EntityRuntimeTreeDto（实体扩展树）",))
        ent_ext_list_evidence = {"source": "local-maven", "artifact": "udc-starter-customplan-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController", "method": "listExtFileds(ScalabilityFieldQueryDto)", "class_sha256": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151", "javap": "docs/audit/artifacts/udc-entity-customplan-5.3.517/ScalabilityFieldController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.entity.ext.list"] = UdcOperationContract("udc.entity.ext.list", "POST", "udc-runtime/scalability/list-ext-field", "com.seeyon.boot.starter.customplan.dto.ScalabilityFieldQueryDto", "com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.customplan.dto.ScalabilityFieldDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [ent_ext_list_evidence], ("ScalabilityFieldQueryDto",), ("响应为 ListResponse 包裹 ScalabilityFieldDto（扩展字段列表）",))
        ent_ext_dt_evidence = {"source": "local-maven", "artifact": "udc-starter-customplan-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController", "method": "selectAvailableDatatype(ScalabilityFieldQueryDto)", "class_sha256": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151", "javap": "docs/audit/artifacts/udc-entity-customplan-5.3.517/ScalabilityFieldController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.entity.ext.available_datatype"] = UdcOperationContract("udc.entity.ext.available_datatype", "POST", "udc-runtime/scalability/available-datatype", "com.seeyon.boot.starter.customplan.dto.ScalabilityFieldQueryDto", "com.seeyon.boot.transport.ListResponse<java.lang.String>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [ent_ext_dt_evidence], ("ScalabilityFieldQueryDto",), ("响应为 ListResponse 包裹 String（可用数据类型列表）",))
        ent_ext_attr_evidence = {"source": "local-maven", "artifact": "udc-starter-customplan-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController", "method": "selectAttribute(ScalabilityFieldQueryDto)", "class_sha256": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151", "javap": "docs/audit/artifacts/udc-entity-customplan-5.3.517/ScalabilityFieldController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.entity.ext.attribute"] = UdcOperationContract("udc.entity.ext.attribute", "POST", "udc-runtime/scalability/select-attribute", "com.seeyon.boot.starter.customplan.dto.ScalabilityFieldQueryDto(SingleRequest)", "com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.customplan.dto.ScalabilityFieldDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [ent_ext_attr_evidence], ("ScalabilityFieldQueryDto",), ("响应为 SingleResponse 包裹 ScalabilityFieldDto（单属性）",))
        # ---- R18: 设计态构建/部署写契约族（test2 活体 2026-09-24 全链实证：建实体→建属性→RELEASE 构建→物理表落库）----
        deploy_normal_evidence = {"source": "test2-live-rest+pod-javap", "artifact": "udc-web-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.udc.controller.DeployController", "method": "deployNormal(DeployNormalDto)", "javap": "live pod javap 2026-09-24；**类级前缀 2026-09-27 LIVE 确诊 = udc/runtime**（完整 `POST /service/udc/runtime/deploy-normal` → 200 BOOT_0000 + deployId；旧记的裸 /service/udc/deploy-normal 经 GET 探针=404 无映射，作废）", "evidence_level": "OBSERVED_LIVE", "note": "执行体 boot-starter-sandbox UdcAppDeployService（PipelineProperties 流水线 + SandboxK8sService + Redis 锁 + MQ 异步）。写面：agent gate DENIED，宿主授权执行。RELEASE 数字编码=2/TEST=0（udc_deploy_record.deploy_type LIVE）；state=1 成功/2 失败。形参注 @MultiRequestBody（非 @RequestBody）→ body 必须按形参名包裹为 {\"deployDto\":{...}}，平铺即 DTO=null→EL1007E（09-27 LIVE）。硬门：一致性检测（CdpDataDetectionTask，约 2 分钟），未过则整单 state=2，无部分成功。"}
        contracts["udc.deploy.normal"] = UdcOperationContract("udc.deploy.normal", "POST", "udc/runtime/deploy-normal", "DeployNormalDto(appId+deployType+projectType+terminalType，继承 DeployParamDto)；请求体须包裹于 deployDto 键", "SingleResponse<DeployParamDto>", OperationStatus.OBSERVED, True, [deploy_normal_evidence], ("appId", "deployType(TEST|RELEASE|ON_ONLINE|DELTA)", "projectType(ALL)", "terminalType(ALL)"), ("宿主执行后 RDS udc_test2.udc_deploy_record 新增行 deploy_type=2 state=1", "应用库物理表 SHOW TABLES 命中新实体表", "构建即部署（非实体级 publish 密码面）", "一致性检测未过 → deploy_type 对应行 state=2 + msg 含报错位置"))
        deploy_search_evidence = dict(deploy_normal_evidence, method="searchStatus(Long)", evidence_level="UNVERIFIED")
        deploy_hist_evidence = {"source": "test2-live-rest-20260928", "artifact": "udc-web-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.udc.controller.ApplicationController", "method": "selectAppVersionByAppGuid(Long)", "evidence_level": "OBSERVED_LIVE", "note": "部署历史真面=POST /service/udc/application/appVersion/{appGuid}（按应用族guid查）。09-28 双观测：业务app 2条(RELEASE SUCCESS+ON_ONLINE SUCCESS, failReason='udc发布成功')、副本app 1条(TEST FAIL)。返回 {appVersion, deployType, state:SUCCESS|FAIL, deployTime, failReason}。此路径与 GET deploy/search-status/{deployId} 非同面。"}
        contracts["udc.deploy.search_status"] = UdcOperationContract("udc.deploy.search_status", "POST", "application/appVersion/{appGuid}", "appGuid(Long，应用族guid，非appId)；body 空 {}", "ListResponse<AppVersionDto>", OperationStatus.OBSERVED, False, [deploy_hist_evidence], ("appGuid",), ("部署历史回读 state=SUCCESS|FAIL + failReason", "旧记 GET deploy/search-status/{deployId} 路径误记（类级前缀未实测），保留作历史锚"))
        # ---- UDC-MERGE 批1-微批1（menu 域, main ROUTE 2026-10-08）: P3/P4 新增（照抄 docs/operation-contracts/udc/menu/registry-entries.md python 块）；P1 重用 L108 / P2 重用 L52 零改写；P5 排除（HYPOTHESIS/UNVERIFIED）----
        menu_applog_list_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController", "method": "selectAppDataByDataId", "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775", "javap": "docs/audit/artifacts/udc-menu-5.3.517/UdcAppLogController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.applog.datalog_list_by_data_id"] = UdcOperationContract("udc.applog.datalog_list_by_data_id", "GET", "udc-runtime/app-log/datalog/list-by-dataid/{dataId}", "Long dataId(@PathVariable)", "ListResponse<UdcEntityMonitorLogDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [menu_applog_list_evidence], ("dataId",), ("同一 dataId 回读日志列表 identity_matches", "响应 UdcEntityMonitorLogDto 列表", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        menu_serialcfg_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcSerialConfigController", "method": "selectEntityList", "class_sha256": "fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658", "javap": "docs/audit/artifacts/udc-menu-5.3.517/UdcSerialConfigController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.serial_config.entity_list"] = UdcOperationContract("udc.serial_config.entity_list", "GET", "udc-runtime/serial-config/select-entity-list", "String appName(@MultiRequestBody)", "SingleResponse<EntityGroupAndItemDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [menu_serialcfg_evidence], ("appName",), ("同一 appName 回读实体组与项 identity_matches", "响应 EntityGroupAndItemDto 非空", "MultiRequestBody 经 GET 的传参约定 UNVERIFIED（LIVE 需实测；离线负证据：全域 52 POST 先例 0 GET，P4 为 GET+@MultiRequestBody 唯一法，LIVE 首验优先请求体假设，详见 docs/audit/artifacts/udc-menu-5.3.517/multi-request-body-get-binding.md；LIVE 注：传参形态 LIVE 实测 ?appName= 查询串有效（2026-09-20 10:35:33 开火 200+SUCCESS+entities 非空，见 main/LIVE-READBACK-VERIFIED.md）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        # ---- UDC-MERGE 微批3（bi 域 ganttchart 5.3.260, main 2026-10-08 HUMAN 代派）: 5 条净新增（照抄 docs/operation-contracts/udc/bi/registry-entries.md 追加节 python 块，字段同名同序）----
        gc_running_evidence = {"source": "local-maven-53260", "artifact": "boot-starter-ganttchart-5.3.260.jar", "version": "5.3.260", "class": "com.seeyon.boot.starter.ganttchart.controller.GanttChartRunningController", "method": "dynamicSelectByEntity", "class_sha256": "8d43516d96edfb6c38ef7a9c8a5cdb1e00c9cdf03a8be47d2025b84ff0176f84", "javap": "docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartRunningController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.bi.ganttchart_running_dynamic_select_by_entity"] = UdcOperationContract("udc.bi.ganttchart_running_dynamic_select_by_entity", "POST", "gantt-chart/dynamic-select-by-entity", "ListRequest", "ListResponse<java.lang.Object>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [gc_running_evidence], ("entity 查询条件(ListRequest)",), ("同一入参二次回读 identity_matches", "响应为 ListResponse<java.lang.Object> 非空（或条件致空亦自证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        gc_schema_evidence = {"source": "local-maven-53260", "artifact": "boot-starter-ganttchart-5.3.260.jar", "version": "5.3.260", "class": "com.seeyon.boot.starter.ganttchart.controller.GanttChartSchemaController", "method": "selectById", "class_sha256": "cad8796509e7ccf4ffd0a020ae3ba004e3bf2670c6a058248d825c9d652385cb", "javap": "docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartSchemaController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.bi.ganttchart_schema_select_by_id"] = UdcOperationContract("udc.bi.ganttchart_schema_select_by_id", "POST", "gantt-chart-schema/select-by-id", "java.lang.Long", "SingleResponse<setting.GanttChartSchemaDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [gc_schema_evidence], ("id",), ("同一入参二次回读 identity_matches", "响应为 SingleResponse<setting.GanttChartSchemaDto> 非空（或条件致空亦自证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        gc_schema_code_evidence = {"source": "local-maven-53260", "artifact": "boot-starter-ganttchart-5.3.260.jar", "version": "5.3.260", "class": "com.seeyon.boot.starter.ganttchart.controller.GanttChartSchemaController", "method": "selectByCode", "class_sha256": "cad8796509e7ccf4ffd0a020ae3ba004e3bf2670c6a058248d825c9d652385cb", "javap": "docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartSchemaController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.bi.ganttchart_schema_select_by_code"] = UdcOperationContract("udc.bi.ganttchart_schema_select_by_code", "GET", "gantt-chart-schema/{code}", "java.lang.String", "SingleResponse<setting.GanttChartSchemaDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [gc_schema_code_evidence], ("code", "方案编码"), ("同一入参二次回读 identity_matches", "响应为 SingleResponse<setting.GanttChartSchemaDto> 非空（或条件致空亦自证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        gc_schema_cond_evidence = {"source": "local-maven-53260", "artifact": "boot-starter-ganttchart-5.3.260.jar", "version": "5.3.260", "class": "com.seeyon.boot.starter.ganttchart.controller.GanttChartSchemaController", "method": "selectByConditions", "class_sha256": "cad8796509e7ccf4ffd0a020ae3ba004e3bf2670c6a058248d825c9d652385cb", "javap": "docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartSchemaController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.bi.ganttchart_schema_search_list"] = UdcOperationContract("udc.bi.ganttchart_schema_search_list", "POST", "gantt-chart-schema/search-list", "java.util.Map<java.lang.String, java.lang.Object>, Sort", "ListResponse<setting.GanttChartSchemaDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [gc_schema_cond_evidence], ("conditions(Map)", "sort"), ("同一入参二次回读 identity_matches", "响应为 ListResponse<setting.GanttChartSchemaDto> 非空（或条件致空亦自证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        gc_schema_page_evidence = {"source": "local-maven-53260", "artifact": "boot-starter-ganttchart-5.3.260.jar", "version": "5.3.260", "class": "com.seeyon.boot.starter.ganttchart.controller.GanttChartSchemaController", "method": "selectPageByConditions", "class_sha256": "cad8796509e7ccf4ffd0a020ae3ba004e3bf2670c6a058248d825c9d652385cb", "javap": "docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartSchemaController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.bi.ganttchart_schema_search"] = UdcOperationContract("udc.bi.ganttchart_schema_search", "POST", "gantt-chart-schema/search", "PageInfo, java.util.Map<java.lang.String, java.lang.Object>, Sort", "PageResponse<setting.GanttChartSchemaDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [gc_schema_page_evidence], ("conditions(Map)", "sort"), ("同一入参二次回读 identity_matches", "响应为 PageResponse<setting.GanttChartSchemaDto> 非空（或条件致空亦自证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        # ---- UDC-MERGE 批2（resource 域, main ROUTE 2026-10-09）: 5 条净新增（照抄 docs/operation-contracts/udc/resource/registry-entries.md L27-40 构造；write=False；VERIFIED_STATIC_BYTECODE 封顶）----
        res_attachment_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.AttachmentTemplateController", "method": "selectByGuid", "class_sha256": "72241cb3ae302c91cd3baba690eaa25656adcedc13e7cdf25413deebd31444f3", "javap": "docs/audit/artifacts/udc-resource-5.3.517/r1-AttachmentTemplateController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.attachment.template_get_by_guid"] = UdcOperationContract("udc.attachment.template_get_by_guid", "GET", "udc-runtime/attachment-template/{guid}", "Long guid(@PathVariable)", "SingleResponse<CommonFileDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [res_attachment_evidence], ("guid",), ("同一 guid 回读附件模板记录 identity_matches", "响应 SingleResponse<CommonFileDto> 非空", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

        res_attachment_guids = dict(res_attachment_evidence, method="selectByGuids")
        contracts["udc.attachment.template_list_by_guids"] = UdcOperationContract("udc.attachment.template_list_by_guids", "POST", "udc-runtime/attachment-template/select-by-guids", "List<Long> guids(@RequestBody)", "ListResponse<CommonFileDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [res_attachment_guids], ("guids",), ("同一 guids 集合回读列表长度一致 identity_matches", "响应 ListResponse<CommonFileDto> 非空（或条件致空亦自证）", "POST 查询形态（对照 registry L86 先例，write=False）；网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

        res_attachment_app = dict(res_attachment_evidence, method="selectByAppId")
        contracts["udc.attachment.template_list_by_app_id"] = UdcOperationContract("udc.attachment.template_list_by_app_id", "GET", "udc-runtime/attachment-template/app/{appId}", "Long appId(@PathVariable)", "ListResponse<CommonFileDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [res_attachment_app], ("appId",), ("同一 appId 回读附件模板列表 identity_matches", "响应 ListResponse<CommonFileDto> 非空", "源码 @ParameterInfo 文案为「附件模板guid」与形参名 appId 不符（逐字照录，语义待 LIVE 确认）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

        res_jar_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.DynamicJarController", "method": "download", "class_sha256": "0eb1fd79e96e09eb0122c0aafd77d8922ee3163f46f5436a44c98b476726def2", "javap": "docs/audit/artifacts/udc-resource-5.3.517/r1-DynamicJarController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.jar.download"] = UdcOperationContract("udc.jar.download", "GET", "udc-runtime/dynamic/jar/download", "HttpServletRequest + HttpServletResponse（无参数注解）", "void（Servlet 流式下载，无 transport envelope）", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [res_jar_evidence], (), ("HTTP 200 + Content-Type/Content-Length 类响应头", "落盘字节非空（不适用 envelope 判据；下载对象离线不可确证，LIVE 需先确证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

        res_jar_app = dict(res_jar_evidence, method="downloadApp")
        contracts["udc.jar.export_app"] = UdcOperationContract("udc.jar.export_app", "POST", "udc-runtime/dynamic/jar/download/{appName}", "String appName(@PathVariable)", "SingleResponse<String>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [res_jar_app], ("appName",), ("同一 appName 回读导出结果 identity_matches", "响应 SingleResponse<String> 非空（jar 名/路径或摘要）", "POST 导出形态（非 GET，是否属只读边界由主控裁定）；副作用未确证（离线无写库/写盘证据）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
        # ---- UDC-MERGE 批2（publish/page 域, main ROUTE 2026-10-09）: 2 条 net-new（逐字照抄 docs/operation-contracts/udc/publish/registry-entries.md L47/L49 与 udc/page/registry-entries.md L92/L102；write=False；VERIFIED_STATIC_BYTECODE 封顶；path 占位逐字保留不臆造）----
        publish_deploy_info_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseAppInfoController", "method": "getDeployInfo", "class_sha256": "deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95", "javap": "docs/audit/artifacts/udc-publish-5.3.517/r1-UdcBaseAppInfoController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
        contracts["udc.publish.deploy_info"] = UdcOperationContract("udc.publish.deploy_info", "GET", "deploy-info", "String currentAppName(@PathVariable)", "SingleResponse<String>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [publish_deploy_info_evidence], ("currentAppName",), ("同一 currentAppName 回读部署信息 JSON identity_matches", "响应 SingleResponse<String> 非空", "类级前缀因子类而异（FormAppInfoController={hostAppName}/dynamic-rest/com-seeyon/{currentAppName}/app-info，NormalAppInfoController={currentAppName}/app-info），完整路由 UNVERIFIED（离线不可确证，禁止拼前缀）"))

        refer_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.proxy.controller.UdcReferController", "method": "selectTree", "class_sha256": "912383403dcd0e9e445225308b82a117850fbc98494e54243b6f2d454bf09664", "javap": "docs/audit/artifacts/udc-page-5.3.517/UdcReferController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE(method/value/params/return);UNRESOLVED-in-5.3.517(base)", "negative_evidence": "docs/audit/artifacts/udc-page-5.3.517/C5-negative-evidence.md"}
        contracts["udc.page_refer.select_by_id"] = UdcOperationContract("udc.page_refer.select_by_id", "GET", "<BASE-UNRESOLVED-in-5.3.517>/{entityAppName}/{entityName}/{referGuid}/{objectId}", "String entityAppName + String entityName + String referGuid + Long objectId (PathVariable)", "SingleResponse<Object>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [refer_evidence], ("entityAppName", "entityName", "referGuid", "objectId"), ("同一 objectId 回读 identity_matches，SingleResponse.data 为该参照对象", "base 段 UNRESOLVED-in-5.3.517（同 C5，需 LIVE 解析 BaseComponentController 基址）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

        # ---- 微流程写面（2026-10-20 加；证据 = core/facts/udc/write-chain/microflow-rest-write-chain.md
        #      §1 端点面 + §2.1/2.2 实测链路，均为 LIVE。write=True，执行层需显式 WriteScope 才放行。）----
        mf_rest_base = {"source": "live-rest-microflow", "artifact": "udc-web-5.3.517.jar",
                        "version": "5.3.517", "class": "com.seeyon.udc.controller.MicroFlowController",
                        "class_scope": "udc/microflow", "evidence_level": "LIVE",
                        "evidence": "core/facts/udc/write-chain/microflow-rest-write-chain.md"}
        contracts["udc.microflow.create"] = UdcOperationContract(
            "udc.microflow.create", "POST", "udc/microflow/create",
            "MicroFlowDto（扁平，dataSchema 为 JSON 字符串）", "SingleResponse<Long>",
            OperationStatus.VERIFIED_STATIC_BYTECODE, True, [dict(mf_rest_base, method="create")],
            (), ("返回 data.content = 新微流程 id", "落库后 data_schema 为 NULL（新建不生成骨架）",
                 "写操作：须显式 WriteScope 才执行"),
            )
        contracts["udc.microflow.check_schema"] = UdcOperationContract(
            "udc.microflow.check_schema", "POST", "udc/microflow/checkSchema",
            "MicroFlowDto（与 create 同 body）", "MicroFlowDeserializationResult",
            OperationStatus.VERIFIED_STATIC_BYTECODE, True, [dict(mf_rest_base, method="checkSchema")],
            (), ("check=true 且 errors=0 才创建", "★ 浅校验：不验 actionType/operator/paramType/空流程，不可当日深度校验器"),
            )
        contracts["udc.microflow.update"] = UdcOperationContract(
            "udc.microflow.update", "POST", "udc/microflow/update",
            "MicroFlowDto（须从 findById 完整回读后修改）", "SingleResponse<Long>",
            OperationStatus.VERIFIED_STATIC_BYTECODE, True, [dict(mf_rest_base, method="update")],
            (), ("返回 content=1", "★ type/triggerType/state/sourceId 必须从 DB 原值回读，禁硬编码（2026-10-16 事故）"),
            )
        contracts["udc.microflow.find_by_id"] = UdcOperationContract(
            "udc.microflow.find_by_id", "GET", "udc/microflow/findById/{id}",
            "Long id(@PathVariable)", "SingleResponse<MicroFlowDto>",
            OperationStatus.VERIFIED_STATIC_BYTECODE, False, [dict(mf_rest_base, method="findById")],
            ("id",), ("返回完整 DTO 含 dataSchema", "回读锚点：写后必须用它核对"),
            )

        # ---- 枚举域写面（2026-10-20 加；证据 = core/facts/udc/enum/create.md +
        #      core/facts/udc/write-chain/enum-write-chain.md，全部 LIVE。
        #      三个写端点都是 GraphQL：POST /service/udc/graphql?<operationName>，
        #      body = {"query":"mutation graphqlLoader ($params0: XInputBody) { data0: X(body:$params0) {...} }",
        #              "variables":{"params0":{...}}}
        #      注意：写面一律需要显式 WriteScope 才放行（layer.execute 的 write_scope 参数）。----
        enum_graphql_base = {
            "source": "live-graphql-enum", "artifact": "udc-web-5.3.517.jar",
            "version": "5.3.517",
            "classes": ["UdcEnumController", "UdcEnumCategoryController", "UdcEnumItemController"],
            "evidence_level": "LIVE",
            "evidence": "core/facts/udc/enum/create.md",
        }
        contracts["udc.enum.category.create"] = UdcOperationContract(
            "udc.enum.category.create", "POST", "graphql?udcEnumCategoryPost",
            "udcEnumCategoryPostInputBody（name 为 i18n JSON 字符串）", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True, [dict(enum_graphql_base, operation="udcEnumCategoryPost")],
            (), ("落库 ctp_enum_category（不是 udc_enum_category）",
                 "name 必须 {\"zh_CN\":\"...\"}；缺 orderNo 报 BOOT_1001",
                 "分组名重复报 ENUM_3009",
                 "写操作：须显式 WriteScope"),
            )
        contracts["udc.enum.create"] = UdcOperationContract(
            "udc.enum.create", "POST", "graphql?udcEnumPost",
            "udcEnumPostInputBody（name=i18n JSON / code=英文编码）", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True, [dict(enum_graphql_base, operation="udcEnumPost")],
            (), ("落库 ctp_enum（不是 udc_enum）",
                 "name 传裸文本报 BOOT_1001 枚举编码 不能为空（实缺 i18n 形态）",
                 "appGuid 取自 udc_application.guid，不是 appId",
                 "categoryId 指向分组，顶层用 \"0\"",
                 "写操作：须显式 WriteScope"),
            )
        contracts["udc.enum.item.create"] = UdcOperationContract(
            "udc.enum.item.create", "POST", "graphql?udcEnumItemPost",
            "udcEnumItemPostInputBody", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True, [dict(enum_graphql_base, operation="udcEnumItemPost")],
            (), ("落库 ctp_enum_item",
                 "值槽位是 itemValue（缺它报 BOOT_1001 枚举项编码 不能为空），不是 code",
                 "必须同时给 enumId 与 enumCode",
                 "顶层项 parentId=\"0\"，缺它报 BOOT_1001 上级枚举项ID 不能为null",
                 "写操作：须显式 WriteScope"),
            )
        contracts["udc.enum.batch_delete"] = UdcOperationContract(
            "udc.enum.batch_delete", "POST", "graphql?udcEnumBatchDeletePost",
            "udcEnumBatchDeletePostInputBody（ids: [String]）", "SingleResponse<Boolean>",
            OperationStatus.OBSERVED, True, [dict(enum_graphql_base, operation="udcEnumBatchDeletePost")],
            ("ids",), ("逻辑删除：ctp_enum.is_delete=1，物理行仍在",
                        "回读统计须 is_delete=0 过滤，否则误判没删掉",
                        "偶发返回 BOOT_4000 但数据已生效——回读确认，勿重发",
                        "★ 删除前必须查引用（实体 CTPENUM 属性/微流程/页面/规则）",
                        "写操作：须显式 WriteScope"),
            )
        contracts["udc.enum.search_no_page"] = UdcOperationContract(
            "udc.enum.search_no_page", "POST", "graphql?udcEnumSearchNoPagePost",
            "udcEnumSearchNoPagePostInputBody", "PageResponse<UdcEnum>",
            OperationStatus.OBSERVED, False, [dict(enum_graphql_base, operation="udcEnumSearchNoPagePost")],
            (), ("枚举列表（含 categoryId，用于引用分析）",
                 "读面：POST 但不写数据；不需 WriteScope"),
            )
        contracts["udc.enum.category.search"] = UdcOperationContract(
            "udc.enum.category.search", "POST", "graphql?udcEnumCategorySearch",
            "udcEnumCategorySearchInputBody（params.appId/appGuid/name + sort.orders）",
            "PageResponse<UdcEnumCategory>",
            OperationStatus.OBSERVED, False, [dict(enum_graphql_base, operation="udcEnumCategorySearch")],
            (), ("分组列表", "sort.orders 按 orderNo ASC / createTime DESC",
                 "读面：POST 但不写数据；不需 WriteScope"),
            )

        # ---- 自定义对象域（2026-10-20 加；证据 = core/facts/udc/setting/custom-object/，
        #      GraphQL 探测 + LIVE 创建证实。落库表 udc_data_transfer_object）----
        co_base = {
            "source": "live-graphql-custom-object", "artifact": "udc-web-5.3.517.jar",
            "version": "5.3.517",
            "classes": ["UdcDataTransferObjectController"],
            "evidence_level": "LIVE",
            "evidence": "core/facts/udc/setting/custom-object/create.md",
        }
        contracts["udc.custom_object.create"] = UdcOperationContract(
            "udc.custom_object.create", "POST", "graphql?udcDataTransferObjectPost",
            "udcDataTransferObjectPostInputBody", "SingleResponse<String>",
            OperationStatus.OBSERVED, True, [dict(co_base, operation="udcDataTransferObjectPost")],
            ("appId", "appGuid", "caption", "name", "source"),
            ("落库 udc_data_transfer_object",
             "必填：appId/appGuid/caption(显示名)/name(编码)/source",
             "缺字段报 BOOT_1001；缺 source 报 BOOT_4101",
             "appGuid 取自 udc_application.guid，不是 appId",
             "写操作：须显式 WriteScope"),
            )
        contracts["udc.custom_object.update"] = UdcOperationContract(
            "udc.custom_object.update", "POST", "graphql?udcDataTransferObjectUpdatePost",
            "udcDataTransferObjectUpdatePostInputBody", "SingleResponse<String>",
            OperationStatus.OBSERVED, True, [dict(co_base, operation="udcDataTransferObjectUpdatePost")],
            ("appId", "appGuid", "caption", "name"),
            ("更新自定义对象", "必填与创建同族（BOOT_1001 实测）",
             "写操作：须显式 WriteScope"),
            )
        contracts["udc.custom_object.delete"] = UdcOperationContract(
            "udc.custom_object.delete", "POST", "graphql?udcDataTransferObjectDeletePost",
            "udcDataTransferObjectDeletePostInputBody（appId + id）", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True, [dict(co_base, operation="udcDataTransferObjectDeletePost")],
            ("appId", "id"),
            ("删除自定义对象；返回 content = 实际删除条数",
             "★ 缺 id 时平台仍返回 BOOT_0000 但 content=0 —— 成功码不代表删掉了，必须回读",
             "★ 无批量删除 operation（探测 40+ 候选全 FieldUndefined）",
             "写操作：须显式 WriteScope"),
            )
        contracts["udc.custom_object.list"] = UdcOperationContract(
            "udc.custom_object.list", "DB", "udc_data_transfer_object",
            "DB 表直读（app_id 过滤）", "list[dict]",
            OperationStatus.OBSERVED, False,
            [dict(co_base, operation="(no graphql query op)",
                  evidence="平台**无**自定义对象查询 operation：探测 40+ 候选全 FieldUndefined")],
            ("app_id",),
            ("列表读取走 DB 而非 API —— 这是平台事实，不是能力缺失",
             "★ 删除前必须做引用分析（微流程/页面规则会引用这些对象）"),
            )
        # ---- 选项集 / 参数 / 流水号（2026-10-21 加；证据 = core/facts/udc/setting/ 下对应目录）
        #      选项集与枚举是**两套独立表**（udc_enum* vs ctp_enum*），operation 前缀 udcUdc*。
        opt_base = {
            "source": "live-graphql-option-set", "artifact": "udc-web-5.3.517.jar",
            "version": "5.3.517",
            "classes": ["UdcUdcEnumCategoryController", "UdcUdcEnumController",
                        "UdcUdcEnumItemController"],
            "evidence_level": "LIVE",
            "evidence": "core/facts/udc/setting/option-set/create.md",
        }
        contracts["udc.option_set.category.create"] = UdcOperationContract(
            "udc.option_set.category.create", "POST", "graphql?udcUdcEnumCategoryPost",
            "udcUdcEnumCategoryPostInputBody", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True, [dict(opt_base, operation="udcUdcEnumCategoryPost")],
            ("appId", "appGuid", "name", "caption", "orderNo"),
            ("落库 udc_enum_category（不是 ctp_enum_category）",
             "必填：appId/appGuid/name/caption/orderNo",
             "缺 caption 报 BOOT_1001「分类名称 不能为空」",
             "写操作：须显式 WriteScope"),
            )
        contracts["udc.option_set.create"] = UdcOperationContract(
            "udc.option_set.create", "POST", "graphql?udcUdcEnumPost",
            "udcUdcEnumPostInputBody", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True, [dict(opt_base, operation="udcUdcEnumPost")],
            ("appId", "appGuid", "name", "caption", "categoryId"),
            ("落库 udc_enum（不是 ctp_enum）",
             "★ 编码 name 必须首字母大写，否则 UDC_ENUM_0001「编码只能由首字母大写的数字和字母的组合」",
             "缺 caption 报 BOOT_1001「选项集名称 不能为空」",
             "写操作：须显式 WriteScope"),
            )
        contracts["udc.option_set.item.create"] = UdcOperationContract(
            "udc.option_set.item.create", "POST", "graphql?udcUdcEnumItemPost",
            "udcUdcEnumItemPostInputBody", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True, [dict(opt_base, operation="udcUdcEnumItemPost")],
            ("appId", "appGuid", "enumId", "name", "caption", "code"),
            ("落库 udc_enum_item",
             "★ 三个槽位都不能少：name=编码(英文) / caption=显示名(中文) / code=整数",
             "缺 caption 报 BOOT_1001「选项名称 不能为空」（报错文案有误导）",
             "写操作：须显式 WriteScope"),
            )
        contracts["udc.option_set.category_and_enum"] = UdcOperationContract(
            "udc.option_set.category_and_enum", "POST",
            "graphql?udcUdcEnumCategorySelectCategoryAndEnumPost",
            "udcUdcEnumCategorySelectCategoryAndEnumPostInputBody",
            "SingleResponse<list>", OperationStatus.OBSERVED, False,
            [dict(opt_base, operation="udcUdcEnumCategorySelectCategoryAndEnumPost")],
            ("appId",),
            ("选项集分组+列表一次读出（页面「选项集」tab 加载时调用）",
             "读面：POST 但不写数据；不需 WriteScope"),
            )
        contracts["udc.option_set.batch_delete"] = UdcOperationContract(
            "udc.option_set.batch_delete", "POST", "graphql?udcUdcEnumBatchDeletePost",
            "udcUdcEnumBatchDeletePostInputBody（ids）", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True, [dict(opt_base, operation="udcUdcEnumBatchDeletePost")],
            ("ids",),
            ("删除语义 **UNVERIFIED**：udc_enum **无 is_delete 列**（2026-10-21 逐列核对），"
             "旧写法「逻辑删除 udc_enum.is_delete=1」已作废；空 body 返回 content=0（删 0 条）",
             "★ 删除前必须查引用（自定义对象字段可能引用选项集）",
             "写操作：须显式 WriteScope"),
            )

        # 参数：注意 operation 名里 Definiton 少一个 i —— 平台拼写错误，必须照抄
        param_base = {
            "source": "live-graphql-parameter", "artifact": "udc-web-5.3.517.jar",
            "version": "5.3.517",
            "classes": ["UdcCtpParameterDefinitonController"],
            "evidence_level": "LIVE",
            "evidence": "core/facts/udc/setting/parameter/create.md",
        }
        contracts["udc.parameter.create"] = UdcOperationContract(
            "udc.parameter.create", "POST", "graphql?udcCtpParameterDefinitonPost",
            "udcCtpParameterDefinitonPostInputBody", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True, [dict(param_base, operation="udcCtpParameterDefinitonPost")],
            ("appId", "appGuid", "name", "caption", "dataType", "dataTypeProperties"),
            ("落库 ctp_parameter_definition（app_id 是 varchar，不是 bigint）",
             "★ operation 名 Definiton 少一个 i —— 平台拼写错误，写成 Definition 会 FieldUndefined",
             "缺 caption 报 BOOT_1001「参数显示名称 不能为空」",
             "★ dataTypeProperties 提交时必须是**对象**，传 JSON 字符串报 BOOT_3002 反序列化失败",
             "写操作：须显式 WriteScope"),
            )
        contracts["udc.parameter.update"] = UdcOperationContract(
            "udc.parameter.update", "POST", "graphql?udcCtpParameterDefinitonUpdatePost",
            "udcCtpParameterDefinitonUpdatePostInputBody", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True,
            [dict(param_base, operation="udcCtpParameterDefinitonUpdatePost")],
            ("appId", "id", "caption"),
            ("更新参数；必填与创建同族",
             "写操作：须显式 WriteScope"),
            )
        contracts["udc.parameter.search"] = UdcOperationContract(
            "udc.parameter.search", "POST", "graphql?udcCtpParameterDefinitonSearch",
            "udcCtpParameterDefinitonSearchInputBody", "PageResponse<CtpParameterDefinition>",
            OperationStatus.OBSERVED, False,
            [dict(param_base, operation="udcCtpParameterDefinitonSearch")],
            ("appId",),
            ("参数列表（页面「参数」tab 加载时调用）",
             "读面：POST 但不写数据；不需 WriteScope"),
            )

        # 流水号：写面 body 未定稿（sections 字段名待抓包），状态标 UNKNOWN 而非 LIVE
        serial_base = {
            "source": "live-graphql-serial", "artifact": "udc-web-5.3.517.jar",
            "version": "5.3.517",
            "classes": ["UdcSerialSchemeController"],
            "evidence_level": "PARTIAL",
            "evidence": "core/facts/udc/setting/serial/create.md",
        }
        contracts["udc.serial.search_page"] = UdcOperationContract(
            "udc.serial.search_page", "POST", "graphql?udcSerialSchemeSearchPagePost",
            "udcSerialSchemeSearchPagePostInputBody", "PageResponse<SerialScheme>",
            OperationStatus.OBSERVED, False,
            [dict(serial_base, operation="udcSerialSchemeSearchPagePost")],
            ("appId",),
            ("流水号方案列表（页面「流水号」tab 加载时调用）",
             "读面：POST 但不写数据；不需 WriteScope"),
            )
        contracts["udc.serial.create"] = UdcOperationContract(
            "udc.serial.create", "POST", "graphql?udcSerialSchemeCreatePost",
            "udcSerialSchemeCreatePostInputBody（SerialSchemeDto）",
            "SingleResponse<Long>",
            OperationStatus.OBSERVED, True,
            [dict(serial_base, operation="udcSerialSchemeCreatePost",
                  evidence="core/facts/udc/setting/serial/create.md"
                           "（字段名来自反编译 SerialSchemeDto / SerialSectionDto）")],
            ("appId", "appGuid", "code", "name", "serialSectionDtoList"),
            ("落库 ctp_serial_scheme + ctp_serial_section（LIVE PASS 2026-10-21）",
             "★ 段列表字段名是 serialSectionDtoList —— 不是 sections/serialSections/"
             "serialSectionDtos（试过 11 个候选全失败）",
             "★ GraphQL 层不校验未知字段：传错字段名和传不存在的字段返回同一个业务错，"
             "所以只能反编译读 DTO，不能猜",
             "段 DTO 字段名：size（不是 sectionSize）/ dateType / show / flow / increase",
             "枚举传字符串：CONSTANT/CONTEXT/ENTITY/SERIAL、LEFT/RIGHT/NONE、"
             "NONE/YEAR/MONTH/DAY、APP/BIG/SMALL",
             "★ serialType 用 SerialRuleTypeEnum（APP/BIG/SMALL），不是 SerialTypeEnum",
             "★ 枚举语义反转落库：传 NONE 落成 2，别拿 DB 数字反推语义",
             "段数限制 1~12（DTO @Size）；totalSize 须等于各段 size 之和",
             "写操作：须显式 WriteScope"),
            )
        contracts["udc.serial.delete"] = UdcOperationContract(
            "udc.serial.delete", "POST", "graphql?udcSerialSchemeDeletePost",
            "udcSerialSchemeDeletePostInputBody（appId + id）", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True,
            [dict(serial_base, operation="udcSerialSchemeDeletePost")],
            ("appId", "id"),
            ("删除流水号方案（连带 section）：{appId,id} → content=1 LIVE",
             "缺 id 报 BOOT_4002「数据不存在或无权限查看」",
             "写操作：须显式 WriteScope"),
            )
        # ---- 导入导出模板（2026-10-21 加；REST 不是 GraphQL，路径 /service/udc/excel/*）
        excel_base = {
            "source": "live-rest-excel", "artifact": "boot-starter-excel-5.3.318.jar",
            "version": "5.3.318",
            "classes": ["ExcelController", "ExcelExportTemplateService"],
            "evidence_level": "LIVE",
            "evidence": "core/facts/udc/setting/excel-template/create.md",
        }
        contracts["setting.excel.template.create"] = UdcOperationContract(
            "setting.excel.template.create", "POST", "/udc/excel/create-template",
            "ExcelExportTemplateDto（metadataContent/excelHeadInfo 为 JSON 字符串）",
            "SingleResponse<Long>",
            OperationStatus.OBSERVED, True,
            [dict(excel_base, operation="POST /service/udc/excel/create-template")],
            ("name", "appId", "appGuid", "mainFullName", "metadataContent", "excelHeadInfo"),
            ("LIVE PASS 2026-10-21：建导入+导出两个模板各 16 列，DB 回读一致",
             "★ REST 接口，不是 GraphQL；路径前缀是 /service/udc/excel/* "
             "（/service/excel/* 报 server_404 excel 服务不存在）",
             "★ isCustom=false 才出现在 search 列表；=true 只出现在 "
             "search-custom-list-by-conditions（反编译实证 selectPageByCondition 强制 false）",
             "★ columnList 读回来恒为 null，列定义看 metadataContent / excelHeadInfo",
             "列 DTO 的 attributeFullName 是唯一锚点：<实体全类名>.<字段名>",
             "displayName 是 Excel 表头（可自定义）",
             "name 限 20 字（DTO @Size(max=20)）",
             "写操作：须显式 WriteScope"),
            )
        contracts["setting.excel.template.search"] = UdcOperationContract(
            "setting.excel.template.search", "POST", "/udc/excel/search",
            "PageRequest{pageInfo{pageNumber,pageSize}, params{appId,...}}",
            "PageResponse<ExcelExportTemplateDto>",
            OperationStatus.OBSERVED, False,
            [dict(excel_base, operation="POST /service/udc/excel/search")],
            ("pageInfo", "params"),
            ("列表（只查 isCustom=false）",
             "★ pageInfo 不是 page/size —— 写成 {page:1,size:10} 报 BOOT_3000 message:null",
             "读面：POST 但不写数据；不需 WriteScope"),
            )
        contracts["setting.excel.template.delete"] = UdcOperationContract(
            "setting.excel.template.delete", "POST", "/udc/excel/delete",
            "body {\"id\": <Long>}", "SingleResponse<Integer>",
            OperationStatus.OBSERVED, True,
            [dict(excel_base, operation="POST /service/udc/excel/delete")],
            ("id",),
            ("删除（逻辑删除 deleteFlag=true）",
             "★ 裸 Long 会报 BOOT_4002，必须传 {\"id\": ...}",
             "写操作：须显式 WriteScope"),
            )

        # ---- 二维码（2026-10-21 加；REST，路径 /service/udc/qrcode-rule/*）
        qr_base = {
            "source": "live-rest-qrcode", "artifact": "boot-starter-qrcode-5.3.262.jar",
            "version": "5.3.262",
            "classes": ["CtpQrCodeRuleController"],
            "evidence_level": "LIVE",
            "evidence": "core/facts/udc/setting/qrcode/create.md",
        }
        contracts["setting.qrcode.rule.create"] = UdcOperationContract(
            "setting.qrcode.rule.create", "POST", "/udc/qrcode-rule/create",
            "CtpQrCodeRuleDesignDto", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True,
            [dict(qr_base, operation="POST /service/udc/qrcode-rule/create")],
            ("name", "type", "linkType", "appId", "appGuid", "entityFullName"),
            ("LIVE PASS 2026-10-21：FIELDQRCODE 规则落库 ctp_qr_code_rule",
             "★ type/linkType 传字符串枚举，DB 存 ordinal",
             "  CtpQrCodeTypeEnum BARCODE(0)/LINKQRCODE(1)/FIELDQRCODE(2)/QRCODE(3)",
             "  CtpQrCodeLinkTypeEnum APP(0)/CUSTOM(1)",
             "FIELDQRCODE/BARCODE 必须给 valueFieldCode",
             "LINKQRCODE 必须给 pcPagePath 或 mobilePagePath",
             "name 限 50 字",
             "写操作：须显式 WriteScope"),
            )
        contracts["setting.qrcode.rule.search"] = UdcOperationContract(
            "setting.qrcode.rule.search", "POST", "/udc/qrcode-rule/search",
            "body {pageInfo, paramsDto, sort}", "PageResponse<CtpQrCodeRuleDto>",
            OperationStatus.OBSERVED, False,
            [dict(qr_base, operation="POST /service/udc/qrcode-rule/search")],
            ("pageInfo", "paramsDto"),
            ("分页列表（3 个 @MultiRequestBody 平铺）",
             "★ sort 必须是 null 不能是 {} —— 传 {} 报 BOOT_3000 message:null",
             "search-no-page 只传 {paramsDto}，不要 sort key",
             "读面：POST 但不写数据；不需 WriteScope"),
            )
        # ---- 字段集 / 扩展实体（2026-10-21 加；REST，主表 LIVE、子集合 BLOCKED）
        aset_base = {
            "source": "live-rest-attribute-set", "artifact": "udc-web-5.3.517.jar",
            "version": "5.3.517",
            "classes": ["AttributeSetController", "AttributeGroupController"],
            "evidence_level": "LIVE",
            "evidence": "core/facts/udc/setting/attribute-set/create.md",
        }
        contracts["setting.attribute_set.create"] = UdcOperationContract(
            "setting.attribute_set.create", "POST", "/udc/attributeSet",
            "AttributeSetDto", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True,
            [dict(aset_base, operation="POST /service/udc/attributeSet")],
            ("appId", "name", "caption", "sourceType"),
            ("LIVE PASS 2026-10-21：建壳成功，DB 回读 udc_attribute_set 正确",
             "★ REST，路径是**驼峰** udc/attributeSet；写 udc/attribute-set 报 nginx 403",
             "  （分组是连字符 udc/attribute-group，两者风格不同）",
             "name ≤30 / caption ≤50 / sourceType 必填（APP|UDC|ISV 或 3|1|2）",
             "★ attributes 传了会被**静默忽略**：回 BOOT_0000 但 udc_attribute 零写入 "
             "（BLOCKED，4 种变体全试过）",
             "写操作：须显式 WriteScope"),
            )
        contracts["setting.attribute_set.select_attributes"] = UdcOperationContract(
            "setting.attribute_set.select_attributes", "POST",
            "/udc/attributeSet/select-attribute-list",
            "body {\"attributeSetId\": <Long>}", "ListResponse<AttributeDto>",
            OperationStatus.OBSERVED, False,
            [dict(aset_base, operation="POST /service/udc/attributeSet/select-attribute-list")],
            ("attributeSetId",),
            ("LIVE PASS：读出字段列表",
             "★ 键名是 attributeSetId，不是 id —— 传 id 报 UDC_ENTITY_0022 字段集不存在",
             "读面：POST 但不写数据；不需 WriteScope"),
            )
        contracts["setting.attribute_group.get"] = UdcOperationContract(
            "setting.attribute_group.get", "GET", "/udc/attribute-group/{entityId}",
            "path entityId", "ListResponse<AttributeGroupDto>",
            OperationStatus.OBSERVED, False,
            [dict(aset_base, operation="GET /service/udc/attribute-group/{entityId}")],
            ("entityId",),
            ("LIVE PASS：返回虚拟分组（id='1', virtual=true, caption=null）+ attributeDtoList",
             "读面：GET；不需 WriteScope"),
            )

        contracts["setting.attribute_set.field.create"] = UdcOperationContract(
            "setting.attribute_set.field.create", "POST",
            "graphql?udcEntityAttributePost",
            "udcEntityAttributePostInputBody（AttributeDto 全字段）",
            "SingleResponse<Long>",
            OperationStatus.OBSERVED, True,
            [dict(aset_base, operation="graphql?udcEntityAttributePost",
                  evidence="core/facts/udc/setting/attribute-set/create.md"
                           "（字段写入真实入口，页面抓包确认）")],
            ("caption", "name", "dataType", "sourceType", "entityId", "sourceId"),
            ("LIVE PASS 2026-10-21：页面建 yanshouziduanjiU + 接口复现 probeFieldTwo 均落库",
             "★★ 父 REST / 子 GraphQL：字段写入必须走这个 GraphQL，"
             "REST attributeSet/update 带 attributes 会被静默忽略（4 种变体全试）",
             "字段 body 的排序占位键是**字符串 \"0\"**（不是数字）",
             "widgetConfig 必须是 JSON **字符串**，不是对象",
             "sourceType='ATTRIBUTESET'，entityId=sourceId=字段集 id",
             "name 是编码（英文/拼音），不能含中文",
             "写操作：须显式 WriteScope"),
            )

        scal_base = {
            "source": "live-rest-scalability", "artifact": "udc-web-5.3.517.jar",
            "version": "5.3.517",
            "classes": ["ScalabilityOptionController"],
            "evidence_level": "LIVE",
            "evidence": "core/facts/udc/setting/scalability/create.md",
        }
        contracts["setting.scalability.create"] = UdcOperationContract(
            "setting.scalability.create", "POST", "/udc/scalability-option",
            "ScalabilityOptionDto", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True,
            [dict(scal_base, operation="POST /service/udc/scalability-option")],
            ("appId", "name", "caption"),
            ("LIVE PASS 2026-10-21：建方案壳成功，DB 回读 udc_scalability_option 正确",
             "★ REST，路径**连字符** udc/scalability-option（与 attributeSet 驼峰不同）",
             "appId=-1 表示全局扩展",
             "★ 不能一次带 scalabilityDtoList：子项 optionId @NotNull，create 时方案 id 还不存在",
             "★ 补预留组 BLOCKED：update 静默忽略（子项 id=0 能过校验但 udc_scalability 零写入）",
             "对照：真实方案 dsa 的预留组同样 0 行 → 预留字段疑似懒派生",
             "写操作：须显式 WriteScope"),
            )
        contracts["setting.scalability.select_by_appid_detail"] = UdcOperationContract(
            "setting.scalability.select_by_appid_detail", "GET",
            "/udc/scalability-option/select-by-appid/with-detail/{appId}",
            "path appId", "ListResponse<ScalabilityOptionDto>",
            OperationStatus.OBSERVED, False,
            [dict(scal_base,
                  operation="GET /service/udc/scalability-option/select-by-appid/with-detail/{appId}")],
            ("appId",),
            ("LIVE PASS：读出方案列表（含 scalabilityDtoList / attributeDtoList）",
             "读面：GET；不需 WriteScope"),
            )
        contracts["setting.scalability.group.create"] = UdcOperationContract(
            "setting.scalability.group.create", "POST", "graphql?udcScalabilityPost",
            "udcScalabilityPostInputBody（ScalabilityDto）", "SingleResponse<Long>",
            OperationStatus.OBSERVED, True,
            [dict(scal_base, operation="graphql?udcScalabilityPost",
                  evidence="core/facts/udc/setting/scalability/create.md"
                           "（预留组写入真实入口，页面抓包确认）")],
            ("dataType", "prefix", "count", "optionId", "caption"),
            ("LIVE PASS 2026-10-21：probeExt×5 落库 udc_scalability",
             "★★ 父 REST / 子 GraphQL：预留组必须走这个 GraphQL，"
             "REST scalability-option/update 带 scalabilityDtoList 会被静默忽略",
             "与字段集 udcEntityAttributePost 是同一模式",
             "dataTypeProperties 是 JSON 字符串，minLength 用字符串、maxLength 用数字",
             "count ≤50（DTO）/ ≤20（页面 UI）；prefix ≤20",
             "写操作：须显式 WriteScope"),
            )
        contracts["setting.scalability.group.read"] = UdcOperationContract(
            "setting.scalability.group.read", "POST", "graphql?udcScalabilityOptionOptionGet",
            "body {\"optionId\": <Long>}", "ListResponse<ScalabilityDto>",
            OperationStatus.OBSERVED, False,
            [dict(scal_base, operation="graphql?udcScalabilityOptionOptionGet")],
            ("optionId",),
            ("LIVE PASS：按方案 id 读预留组列表",
             "读面：不需 WriteScope"),
            )
        # ---- 应用域只读面（2026-10-22 test2 LIVE 实测；证据 core/facts/udc/application/evidence/live-app-readonly-2026-10-22.json
        #      契约说明 docs/operation-contracts/udc/application/udc-app-readonly-live-2026-10-22.md
        #      前端字面量来源 core/facts/udc/application/app-frontend-callsurface.md
        #      全部 write=False；网关前缀 /service/udc（sandbox/flexible/* 属独立服务 sandbox，另记）----
        app_live = {"source": "test2-live-rest-20261022", "artifact": "udc-web-5.3.517.jar",
                    "version": "5.3.517", "evidence_level": "OBSERVED_LIVE",
                    "evidence": "core/facts/udc/application/evidence/live-app-readonly-2026-10-22.json",
                    "channel": "CDP Network.getCookies -> python urllib（cookie 仅单请求内存使用）"}
        contracts["udc.application.user_role"] = UdcOperationContract(
            "udc.application.user_role", "GET", "udc/application/user-role?appName={appName}",
            "query appName", "SingleResponse<List<String>>", OperationStatus.OBSERVED, False,
            [dict(app_live, class_hint="ApplicationController")], ("appName",),
            ("LIVE PASS 2026-10-22：appName=udc 回读角色 id 列表 92 条",
             "与 udc.application.role_resource 联合作前端动作权限判定",
             "traceId 样本 3285994432901417148"),
            )
        contracts["udc.application.role_resource"] = UdcOperationContract(
            "udc.application.role_resource", "GET", "udc/application/role-resource?appName={appName}",
            "query appName", "SingleResponse<Map<String,String>>", OperationStatus.OBSERVED, False,
            [dict(app_live, class_hint="ApplicationController")], ("appName",),
            ("LIVE PASS 2026-10-22：8 键 appDesign/appTest/appPublish/appDelete/appExport/appCopy/appCreate/appImport",
             "值域 disabled|basic：disabled=该用户禁用（前端按钮灰化），basic=可用",
             "权限判定在服务端，不是前端硬编码",
             "traceId 样本 3285994433975158972"),
            )
        contracts["udc.deployment.latest_test_info"] = UdcOperationContract(
            "udc.deployment.latest_test_info", "POST", "udc/deployment/latest-test-info",
            "body {\"appId\": \"<Long 字符串>\"}", "SingleResponse<LatestTestInfoDto>",
            OperationStatus.OBSERVED, False,
            [dict(app_live, class_hint="DeploymentController")], ("appId",),
            ("LIVE PASS 2026-10-22：leastTestVersion=1.0.30 / leastTester / testSuccess=true / keepAlive=true",
             "字段：appId,appName,caption,appVersion,buildTime,leastTestVersion,leastTester,testSuccess,keepAlive",
             "写面验收反向证据：测试动作后回读 leastTestVersion 是否递增",
             "traceId 样本 3285994435485108412"),
            )
        contracts["udc.application.front_detection"] = UdcOperationContract(
            "udc.application.front_detection", "POST", "udc/application/search/front-detection",
            "body {\"appId\": \"<Long 字符串>\"}", "SingleResponse<FrontDetectionDto>",
            OperationStatus.OBSERVED, False,
            [dict(app_live, class_hint="ApplicationSearchController")], ("appId",),
            ("LIVE PASS 2026-10-22：count/errorCount/seriuCount/warnCount 为字符串 \"0\"",
             "appId=null + status=null = 尚未跑过检测（占位形态），不得据此断言检测通过",
             "traceId 样本 3285994437028612284"),
            )
        contracts["udc.sandbox.delta_build_info"] = UdcOperationContract(
            "udc.sandbox.delta_build_info", "GET", "udc/sandbox/delta-build-info/{appId}",
            "PathVariable appId", "SingleResponse<DeltaBuildInfoDto>", OperationStatus.OBSERVED, False,
            [dict(app_live, class_hint="SandboxBuildController")], ("appId",),
            ("LIVE PASS 2026-10-22：state=NONE / buildVersion=\"\" / logs=null（无构建）",
             "字段：appName,state,progress,buildVersion,buildTime,startTime,totalTime,logs",
             "测试增量部署的进度轮询面（前端 src_redux_store_ts 同用法）",
             "traceId 样本 3285994438119131324"),
            )
        contracts["udc.sandbox.is_deploy_war"] = UdcOperationContract(
            "udc.sandbox.is_deploy_war", "GET", "udc/sandbox/system/config/is-deploy-war",
            "无参", "SingleResponse<Boolean>", OperationStatus.OBSERVED, False,
            [dict(app_live, class_hint="SandboxSystemConfigController")], (),
            ("LIVE PASS 2026-10-22：test2 实测 false（非 war 部署）",
             "决定沙箱应用形态，影响沙箱测试入口可用性判断",
             "traceId 样本 3285994439343868092"),
            )
        contracts["udc.sandbox.app_search"] = UdcOperationContract(
            "udc.sandbox.app_search", "POST", "udc/sandbox/app/search",
            "body {pageInfo:{pageNo,pageSize}, params:{}}", "PageResponse<SandboxAppDto>",
            OperationStatus.OBSERVED, False,
            [dict(app_live, class_hint="SandboxAppController")], ("pageInfo", "params"),
            ("LIVE PASS 2026-10-22：返回 10 行，含 appState=RUNNING 在跑沙箱应用",
             "行字段：id,appName,appCaption,appVersion,ownerTenantCaption,ownerName,appState,activeTime,createTime",
             "traceId 样本 3285994440467941564"),
            )
        contracts["sandbox.flexible.test_status"] = UdcOperationContract(
            "sandbox.flexible.test_status", "POST", "sandbox/flexible/test-status",
            "body 空 {}", "未确证（服务缺席，未取得业务响应）", OperationStatus.BLOCKED, False,
            [{"source": "test2-live-rest-20261022", "evidence_level": "BLOCKED_SERVICE_ABSENT",
              "evidence": "core/facts/udc/application/evidence/live-app-readonly-2026-10-22.json",
              "note": "POST /service/udc/sandbox/flexible/test-status=404（udc 无映射）；"
                      "POST /service/sandbox/flexible/test-status=200+code=server_404"
                      "「sandbox 服务不存在，请重启服务或重新发布应用后再试！」"}], (),
            ("服务归属 = 独立微服务 sandbox，禁止拼 udc 前缀",
             "test2 当前未部署 sandbox 服务 → 弹性部署族（create/delete/restart/select-deployment-page）整体不可用",
             "该族其余 op 待服务就绪后补登"),
            )
        # 弹性部署族其余入口：仅前端字面量证据（chunk src_pages_udc_sandbox_pages_elastic-deployment_index_tsx），
        # 服务 sandbox 在 test2 缺席 → 全部 DENIED，不得发起
        flex_ev = {"source": "web-bundle-udc", "artifact": "src_pages_udc_sandbox_pages_elastic-deployment_index_tsx.b0321575.js",
                   "version": "5.3.517", "evidence_level": "VERIFIED_STATIC_BYTECODE",
                   "evidence": "core/facts/udc/application/evidence/app-frontend-surface-2026-10-22.json",
                   "note": "前端字面量命中；服务 sandbox 在 test2 缺席（server_404），未发起"}
        for op_id, verb, tail, is_write in (
                ("sandbox.flexible.create_deployment", "POST", "sandbox/flexible/create-deployment", True),
                ("sandbox.flexible.delete_deployment", "POST", "sandbox/flexible/delete-deployment", True),
                ("sandbox.flexible.restart_deployment", "POST", "sandbox/flexible/restart-deployment", True),
                ("sandbox.flexible.select_deployment_page", "POST", "sandbox/flexible/select-deployment-page", False),
        ):
            contracts[op_id] = UdcOperationContract(
                op_id, verb, tail, "body 未取得（服务缺席）", "未确证",
                OperationStatus.DENIED, is_write, [dict(flex_ev)], (),
                ("服务归属 sandbox，禁止 udc 前缀",
                 "写族（create/delete/restart）在 test2 一律 DENIED：服务不存在，且写操作未获授权",
                 "select-deployment-page 为读面，同样因服务缺席不可用"),
                )
        # ---- 应用内功能页（左侧菜单 / 底部日志 tab）只读面 ----
        # 抓法：cdp_click_capture.py 录点击产生的请求 → replay_read_probe.py 用会话 cookie 重放。
        # 两个硬事实：(1) 这些页面的数据面几乎全走 /service/udc/graphql?<operation>，
        #            (2) 运行态日志走应用专属前缀 /service/{appName}/udc-runtime/app-log/search/{kind}。
        inner_ev = {"source": "app-inner-click-replay-20261022",
                    "evidence": "core/facts/udc/application/evidence/app-inner-pages-2026-10-22/replay-probe.json",
                    "evidence_level": "LIVE",
                    "note": "点击录制 + 会话 cookie 重放；cookie 不落盘；未发起任何写动作"}
        gql_note = ("GraphQL 信封：{data0|operationName:{code,data:{content},message,status}}，"
                    "operation 名同时出现在 URL query 上（/service/udc/graphql?<op>）")
        contracts["udc.applog.search.microflow"] = UdcOperationContract(
            "udc.applog.search.microflow", "POST",
            "{app_name}/udc-runtime/app-log/search/microflow",
            "body {params:{appName,appId,logType},pageInfo:{pageNumber,pageSize,needTotal,total}}",
            "List<AppLogRow>", OperationStatus.OBSERVED, False, [dict(inner_ev)],
            ("params", "pageInfo"),
            ("LIVE PASS 2026-10-22：返回 10 行（示例应用真实微流程日志）",
             "行字段：validate,id,traceId,requestId,moduleType(MICRO_FLOW),success,logTime,"
             "subModuleType(MICRO_FLOW_FRONTEND),subModuleTypeName",
             "前缀是应用名而非 udc：/service/{appName}/udc-runtime/...，拼 /service/udc/... 会 404",
             "「微流程运行日志」tab 即此接口"),
            )
        for op_id, kind in (("udc.applog.search.dataflow", "dataflow"),
                            ("udc.applog.search.deduction", "deduction")):
            contracts[op_id] = UdcOperationContract(
                op_id, "POST", "{app_name}/udc-runtime/app-log/search/" + kind,
                "body 同 microflow（logType=" + kind + "）", "List<AppLogRow>",
                OperationStatus.OBSERVED, False, [dict(inner_ev)], ("params", "pageInfo"),
                ("HTTP 200 + code=BOOT_0000，content=[]（示例应用无该类日志，属空结果而非失败）",
                 "「生单规则运行日志」= dataflow、「扣减规则运行日志」= deduction",
                 "空列表不可判为「日志正常/功能通过」，只证明接口存活"),
                )
        contracts["udc.applog.search.absent_kinds"] = UdcOperationContract(
            "udc.applog.search.absent_kinds", "POST",
            "{app_name}/udc-runtime/app-log/search/{design|page|bizrule|sandbox|build|compile|deployment}",
            "body 同 microflow", "无（404 Non-JSON）", OperationStatus.DENIED, False,
            [dict(inner_ev)], ("params", "pageInfo"),
            ("探明命名只有 microflow / dataflow / deduction 三种",
             "design 等 7 个候选一律 404（非 JSON），禁止再拼",
             "「设计日志」不走此族，走 GraphQL udcOperationLogSearch"),
            )
        contracts["udc.operation_log.init_data"] = UdcOperationContract(
            "udc.operation_log.init_data", "POST", "udc/graphql?udcOperationLogSearchInitDataAppGet",
            'body {query,variables:{params0:{appId}}}', "GraphQL data0.data.content",
            OperationStatus.OBSERVED, False, [dict(inner_ev)], ("query", "variables"),
            (gql_note,
             "LIVE PASS 2026-10-22：返回 subModuleMap（ALL/DATAFLOW/DEDUCTION/FUNCTION_NODE/WIDGET/"
             "PORTLET/PORTLET_GROUP/PAGE/LAYOUT/ENTITY_GROUP/ENTITY...）+ moduleMap + members",
             "= 设计日志页的筛选字典 + 可见成员，筛选选项由后端下发，前端不写死"),
            )
        contracts["udc.operation_log.search"] = UdcOperationContract(
            "udc.operation_log.search", "POST", "udc/graphql?udcOperationLogSearch",
            'body {query,variables:{params0:{pageInfo,params:{appId,startTime,endTime,operatorId,'
            'module,subModule},sort:{orders:[{direction,property:createTime}]}}}}',
            "GraphQL data0.data.content[] + pageInfo", OperationStatus.UNVERIFIED, False,
            [dict(inner_ev, evidence_level="VERIFIED_STATIC_BYTECODE")],
            ("query", "variables"),
            ("语义为分页查询，但平台把它声明成 mutation → 按「mutation 一律不重放」纪律未发",
             "行字段：appId,operatorId,operatorCaption,module,subModule,moduleCaption,subModuleCaption,"
             "logElement,elementsSize,recordVersion,logPath,actionType,domainId,storageKey,createTime,"
             "domainCaption,operations,traceId,publishState,originalId,id,guid,extraJson",
             "= 「设计日志」tab 的取数接口；要 LIVE 需授权发一次 mutation 语义的查询"),
            )
        contracts["udc.collaboration.app_get"] = UdcOperationContract(
            "udc.collaboration.app_get", "POST", "udc/graphql?udcCollaborationAppGet",
            'body {query,variables:{path:{appId}}}', "GraphQL udcCollaborationAppGet.data.content[]",
            OperationStatus.OBSERVED, False, [dict(inner_ev)], ("query", "variables"),
            (gql_note,
             "LIVE PASS 2026-10-22：返回成员数组，含 appId,guid,id,isCreator,memberId,memberName,role",
             "= 「团队设置」页取数；role 为应用内角色名（如「应用设计师」），非平台角色 id",
             "应用所有者由 isCreator=true 判定，与 ownerName 字段互为印证"),
            )
        contracts["udc.deployment.app_ready_state"] = UdcOperationContract(
            "udc.deployment.app_ready_state", "POST", "udc/graphql?udcDeploymentAppReadyStatePost",
            'body {query,variables:{params0:{appId}}}', "GraphQL data0.data.content",
            OperationStatus.OBSERVED, False, [dict(inner_ev)], ("query", "variables"),
            (gql_note,
             "LIVE PASS 2026-10-22：state=RUNNING、msg=DEPLOY_SUCCESS、enableClearEntry=true、"
             "enableLoginEntry=false、terminalType=null",
             "= 「沙箱测试」页的状态位（沙箱准备成功 / 应用启动成功 两段判读依据）",
             "读它不会触发构建；触发构建是写面，未获授权"),
            )
        contracts["app_common.theme.select_default_brand"] = UdcOperationContract(
            "app_common.theme.select_default_brand", "POST",
            "app-common/graphql?appCommonThemeSelectDefaultBrandPost",
            'body {query(mutation),variables:{params0:{...}}}', "GraphQL mutation",
            OperationStatus.DENIED, True,
            [dict(inner_ev, evidence_level="VERIFIED_STATIC_BYTECODE")],
            ("query", "variables"),
            ("打开「应用主题」页即自动发此 mutation（选择默认品牌）→ 属平台自动写，非人工动作",
             "本仓库严禁重放：mutation 一律 DENIED",
             "只读替身：app-common/graphql?appCommonThemeSelectDefaultGet（route sweep 中已录到）"),
            )
        # ---- 依赖设置（应用依赖）：弹窗查询 / 列表 / 添加 / 移除 ----
        # 三条链路由用户授权实测：点「添加依赖」→ 勾选 → 确定（真写入）→ 移除 → 复原。
        dep_ev = {"source": "app-inner-dependency-live-20261022",
                  "evidence": "core/facts/udc/application/evidence/app-inner-pages-2026-10-22/dep-*.json",
                  "evidence_level": "LIVE",
                  "note": "写面形状来自真实录制；写入后已立即移除复原，依赖列表回到 2 行"}
        contracts["udc.dependency.available_apps"] = UdcOperationContract(
            "udc.dependency.available_apps", "POST",
            "udc/graphql?udcMetaDataSearchAvailableAppMultiVersionPost",
            'body {query(mutation 声明),variables:{params0:{appId,keyword?,versionType?}}}',
            "GraphQL data0.data.content[]", OperationStatus.OBSERVED, False, [dict(dep_ev)],
            ("query", "variables"),
            ("「添加依赖」弹窗一打开就发：返回可选应用（caption/name/versionList/appVersion/basePackage/"
             "enableDependent/description）",
             "**enableDependent=false 的行 checkbox 必 disabled**（如 addressBook：无版本、必填项为空），"
             "不是前端乱禁 —— 选不了是后端下发的许可位",
             "语义是查询却声明成 mutation：判读看别名层，不看顶层",
             "回包外层还有 traceId，与 data0 同级"),
            )
        contracts["udc.dependency.list"] = UdcOperationContract(
            "udc.dependency.list", "POST",
            "udc/graphql?udcApplicationDependentApplicationSelectByConditionPost",
            'body {params0:{params:{appId},sort:{orders:[{direction:ASC,property:createTime}]}}}',
            "GraphQL data0.data.content[]", OperationStatus.OBSERVED, False, [dict(dep_ev)],
            ("params", "sort"),
            ("LIVE PASS 2026-10-22：content 为依赖数组（含 portal / platform / cip-manager 等内置依赖，"
             "具体版本号见证据文件）",
             "行字段：appId,depAppBasePackage,depAppCaption,depAppName,depAppVersion,id,dependentAppType,"
             "enableDelete,dynamicModuleGroup,supportUpgrade,defaultLastVersion,enable,updateTime,"
             "versionTypeEnum,preSet,terminalType,versionEdit,belongToPlatform,sourceType,packageType",
             "**enableDelete=false 表示内置依赖不可删**（平台/集成平台行虽有「移除」按钮也不该动）",
             "「应用依赖」列表的取数口；切 tab 复用缓存时不重发，所以点击录制常 0 请求"),
            )
        contracts["udc.dependency.create_batch"] = UdcOperationContract(
            "udc.dependency.create_batch", "POST",
            "udc/graphql?udcApplicationDependentApplicationCreateBatchPost",
            'body {params0:[{appId,depAppName,depAppCaption,depAppVersion,depAppBasePackage,'
            'dependentAppType}]}', "GraphQL data0.data.content", OperationStatus.DENIED, True,
            [dict(dep_ev)], ("params0",),
            ("「添加依赖」→ 确定 的写口。已实测一次（公告 5.3.98，dependentAppType=SERVICE，"
             "depAppBasePackage=com.seeyon），随后立即移除复原",
             "params0 是**数组**：支持一次加多个依赖；空数组也发请求（勾选没生效时会出现空写）",
             "确认后页面自动重拉 udc.dependency.list，不需要手动刷新",
             "本仓库默认不发；如需发必须显式授权并登记 appId/depAppName/depAppVersion"),
            )
        contracts["udc.dependency.delete_by_id"] = UdcOperationContract(
            "udc.dependency.delete_by_id", "POST",
            "udc/graphql?udcApplicationDependentApplicationDeleteByIdPost",
            'body {params0:{id}}', "GraphQL data0.data.content", OperationStatus.DENIED, True,
            [dict(dep_ev)], ("params0",),
            ("「移除」→ popconfirm「确定移除该依赖应用?」→ 确定。已实测一次（id 为依赖行 id，非 appId）",
             "点「移除」本身不发请求，**必须在 popconfirm 里再点确定**；只点移除不会产生任何网络事件",
             "删除成功后平台自动串一个 udc.application.detection，用来重算应用检测结果",
             "id 来自 udc.dependency.list 的行 id，不能拿 depAppName 顶替"),
            )
        contracts["udc.application.detection"] = UdcOperationContract(
            "udc.application.detection", "POST",
            "udc/graphql?udcApplicationSearchDetectionPost",
            'body {body:{appId}}',
            "GraphQL udcApplicationSearchDetectionPost.data.content[]", OperationStatus.DENIED, True,
            [dict(dep_ev, evidence_level="VERIFIED_STATIC_BYTECODE")], ("body",),
            ("依赖增删后由平台**自动**串发，不是人工点「检查」",
             "返回检测项：code,detectionType,domainEntityId,interpolatedDocument,interpolatedElement,"
             "interpolatedMessage,moduleType,elementType,moduleProperty,elementProperty,path,route",
             "⚠ 这才是「检查」结果面板的服务端来源候选；"
             "此前登记的 REST front-detection（计数全 0、appId=null）不能当检查通过证据",
             "语义是检测、实际会写检测结果缓存 → 按写面 DENIED 登记，未主动触发"),
            )
        # ---- 沙箱构建（工具栏「测试」→ 弹窗「立即构建」） ----
        build_ev = {"source": "app-inner-build-live-20261022",
                    "evidence": "core/facts/udc/application/evidence/app-inner-build-2026-10-22/sandbox-build-capture.json",
                    "evidence_level": "LIVE",
                    "note": "2026-10-22 一次真实构建全程录制（前端PC编译 14s / 前端MOBILE 8s / "
                            "后端编译 33s / 部署 124s，平台自报 totalTime=224）；构建完成后页面出现"
                            "「测试启动完成 应用启动完成」"}
        contracts["udc.deploy.deploy_normal"] = UdcOperationContract(
            "udc.deploy.deploy_normal", "POST",
            "udc/graphql?udcRuntimeDeployNormalPost",
            'body {params0:{deployDto:{projectType:"ALL",terminalType:"ALL",deployType:"RELEASE",'
            'appId,generateLog:true}}}',
            "GraphQL data0.data.content{appId,deployId,deployType,projectType,terminalType}",
            OperationStatus.DENIED, True, [dict(build_ev)], ("params0",),
            ("「立即构建」的写口：一次调用走完前端编译 + 后端编译 + 部署，返回 deployId",
             "**声明成 query、实际是重写操作**（同 udc.sandbox.app.search 那类）—— 按写面 DENIED 登记，"
             "禁止用只读探针重放",
             "projectType/terminalType 取 ALL 时前后端同时构建；只建一端可传 PC / MOBILE",
             "与 REST 版 udc.deploy.normal 不是同一个入口：沙箱构建走 GraphQL 这条，"
             "REST 那条在发布/升级链路里出现",
             "构建开始前平台先串一个 udc.application.detection（一致性检测）"),
            )
        contracts["udc.sandbox.build_info"] = UdcOperationContract(
            "udc.sandbox.build_info", "POST",
            "udc/graphql?udcSandboxBuildInfoAppGet",
            'body variables:{params0:{appId}}；别名是 path: 不是 body:'
            '（data0: udcSandboxBuildInfoAppGet(path: $params0)）',
            "GraphQL data0.data.content{validate,appName,state,progress,buildVersion,buildTime,"
            "startTime,totalTime,logs[]}", OperationStatus.OBSERVED, False, [dict(build_ev)],
            ("params0",),
            ("LIVE PASS 2026-10-22：state=SUCCESS / progress=100 / totalTime=224 / logs 为完整构建日志数组",
             "**这就是「[展开沙箱日志]」的数据源**，一次请求拿全量历史日志，不需要在构建窗口内抓流",
             "构建期间页面按约 6s 一次轮询本接口（一次构建实测 44 次），state 从 EXECUTING 走到 SUCCESS",
             "logs 行格式：[INFO]【时间】[低代码平台|app-sandbox] [阶段] [完成] [耗时:N毫秒|秒]"),
            )
        contracts["ctp.version.list"] = UdcOperationContract(
            "ctp.version.list", "POST",
            "ctp-application/appcenter/search-app-edition",
            'body {pageInfo:{needTotal,pageNumber,pageSize},params:{IN_appId:[<appName>],clientType:"PC"}}',
            "裸数组 [{id,appId,appName,appVersion,appBuildVersion,hashMd5,latest,i18nVersion,...}]",
            OperationStatus.OBSERVED, False, [dict(build_ev)], ("pageInfo", "params"),
            ("LIVE PASS 2026-10-22：这是「发布版本」页的版本列表取数口（构建完成后自动刷新）",
             "**IN_appId 传的是 appName（datamigration 前缀的字符串），不是数字 appId** —— 传错会返回空数组",
             "回包是裸数组、不套 code 信封；判读看 HTTP 200 + 数组非空",
             "latest=true 标出当前生效版本；appBuildVersion 形如 20261022231110_5.3.17_1.0.0"),
            )
        contracts["udc.ws.business_channels"] = UdcOperationContract(
            "udc.ws.business_channels", "WS",
            "业务消息服务（同一会话 WebSocket，帧信封 {operate,data}）",
            'client→server {businessKey:"ack-business-service"}；server→client {operate,data}',
            "data 为 JSON 字符串，需二次解析", OperationStatus.OBSERVED, False, [dict(build_ev)],
            ("operate",),
            ("构建/发布进度**不是 HTTP 推送**：HTTP 只负责轮询，实时状态走 WebSocket",
             "udc_detection_channel：一致性检测 {validate,appId,status:EXECUTING|SUCCESS,count,errorCount,"
             "seriouCount,warnCount}（字段名就是 seriouCount，少个 s）",
             "udc_deploy_channel：部署 {validate,deployId,appId,appName,deployType,status,errorMsg[]}",
             "common-message：{appName,status:SUCCESS} 构建完成通知",
             "连接在页面加载时建立，CDP 的 webSocketCreated 抓不到后开的面板 —— "
             "要抓握手 URL 必须新开 tab 从头监听"),
            )
        # ---- 组件依赖（前端控件 / 移动端控件） ----
        cmp_ev = {"source": "app-inner-component-dependency-live-20261022",
                  "evidence": "core/facts/udc/application/evidence/app-inner-build-2026-10-22/cmp-dep-*.json",
                  "evidence_level": "LIVE",
                  "note": "「组件依赖」页实测：加一条 web 端控件依赖（@seeyon/biz-lock-sign）后立即批量删除复原；"
                          "列表 44 行（SERVICE 11 + FRONTEND 33），复原后 biz-lock-sign 不再出现"}
        contracts["udc.dependency.component_create"] = UdcOperationContract(
            "udc.dependency.component_create", "POST",
            "udc/graphql?udcApplicationDependentApplicationCreateBatchPost",
            'body {params0:[{appId,defaultLastVersion,depAppBasePackage,depAppCaption,depAppName,'
            'depAppVersion,dependentAppType:"FRONTEND",description,dynamicModuleGroup,dynamicService,'
            'enableDelete,needGenerate,sort,supportUpgrade,terminalType,sourceType,packageType}]}',
            "GraphQL data0.data.content", OperationStatus.DENIED, True, [dict(cmp_ev)], ("params0",),
            ("组件依赖与应用依赖**共用同一个写口**，靠 dependentAppType 区分：FRONTEND=组件，SERVICE=应用",
             "组件行比应用行多 9 个字段：description,dynamicModuleGroup,dynamicService,enableDelete,"
             "needGenerate,sort,supportUpgrade,terminalType,sourceType,packageType",
             "实测行：packageType=CONTROL / sourceType=CUSTOMIZE / terminalType=PC / dynamicService=true",
             "候选组件列表**不请求后端**：86 行来自前端内置目录（@seeyon/biz-* / @seeyon/mbiz-*）",
             "已实测一次后立即批量删除复原"),
            )
        contracts["udc.dependency.delete_by_ids"] = UdcOperationContract(
            "udc.dependency.delete_by_ids", "POST",
            "udc/application/dependent-application/delete-by-ids",
            'body {ids:[<依赖行 id>]}', "JSON（REST，非 GraphQL 信封）",
            OperationStatus.DENIED, True, [dict(cmp_ev)], ("ids",),
            ("组件依赖的删除走 **REST 批量删**，与应用依赖的 GraphQL DeleteByIdPost 不是一条路",
             "入口是列表上方的「批量删除依赖」+ 勾选行；行内没有「移除」按钮",
             "确认弹窗文案是「删除后不可恢复! 确定删除吗」，按钮是 **取消 / 确认**（不是 确定）",
             "ids 是依赖行 id 数组（如 [\"-8375770234550740457\"]），不是 appId 也不是包名",
             "该请求用 CDP requestWillBeSent 常抓不到（事件被 Runtime.evaluate 往返吞掉），"
             "可靠做法是在页面里 hook XMLHttpRequest/fetch 记到 window.__CAP__"),
            )
        return cls(contracts)

    def get(self, operation_id):
        return self._contracts[operation_id]

    def has(self, operation_id):
        return operation_id in self._contracts

    def all(self):
        return dict(self._contracts)
