"""UDC 运行态（udc-starter-runtime 5.3.517）端点目录与 DTO 约束模型。

证据（CFR 反编译 udc-starter-runtime-5.3.517.jar，<MAVEN_REPO>/com/seeyon/udc-starter-runtime）：
- com.seeyon.boot.starter.udcrt.controller.*（19 个 Controller，78 个端点）
- com.seeyon.boot.starter.udcrt.dto.EntityDataRequestDto / UdcSerialConfigDto 等

用途：
1. LIVE 探针只读面的端点权威目录（只读/写分级，避免误调写接口）
2. 运行态 DTO 必填校验（@NotNull）
3. 与 udc-web 设计态 REST 面区分（设计态 /udc/*，运行态 /udc-runtime/*）
"""
from __future__ import annotations

# ---- Controller 基址（@RequestMapping 值，19 个）----
RUNTIME_CONTROLLERS: dict[str, str] = {
    "AppDraftController": "udc-runtime/app-draft",
    "AttachmentTemplateController": "udc-runtime/attachment-template",
    "CustomApplicationController": "udc-runtime/custom-app",
    "DynamicJarController": "udc-runtime/dynamic/jar",
    "FrontFunctionSupportController": "udc-runtime/function-support",
    "GraphqlProxyController": "udc-runtime/graphql-proxy",
    "RuntimeCOLISplitController": "udc-runtime/coli",
    "RuntimeEnvCheckController": "udc-runtime/evn-check",
    "UdcAppLogController": "udc-runtime/app-log",
    "UdcAttrSnapshotRtController": "udc-runtime/attr-snapshot",
    "UdcDataTypeController": "udc-runtime/datatype",
    "UdcEntityUpdateRtTestController": "udc-runtime/update-test",
    "UdcFormDataQueryController": "udc-runtime/data",
    "UdcFunctionNodeController": "udc-runtime/meta-data",
    "UdcRoleRtController": "udc-runtime/udc-role",
    "UdcRtPageInfoController": "udc-runtime/meta-data",
    "UdcRtPageLogController": "udc-runtime/rt-page-log",
    "UdcRuntimeDatabaseController": "udc-runtime/database",
    "UdcSerialConfigController": "udc-runtime/serial-config",
    # extmetadata 构件（基址不同，同样登记）
    "UdcMetaDataController": "udc-runtime/meta-data",
    "UdcAppInfoController": "udc-app-info",
}

# ---- 端点目录：(controller, method, sub_path, op, dto, readonly) ----
#   op: HTTP 方法；readonly: True=查询/只读，False=写（LIVE 探针禁调）
RUNTIME_ENDPOINTS: tuple[tuple[str, str, str, str, str, bool], ...] = (
    # AppDraft（草稿箱）
    ("AppDraftController", "POST", "create", "创建草稿", "AppDraftDto", False),
    ("AppDraftController", "POST", "exist", "草稿是否存在", "Map", True),
    ("AppDraftController", "POST", "select", "查询草稿", "Map", True),
    ("AppDraftController", "POST", "delete", "删除草稿", "Map", False),
    ("AppDraftController", "POST", "delete-all", "删除全部草稿", "Map", False),
    ("AppDraftController", "POST", "delete/timeout", "删除超时草稿", "Map", False),
    # CustomApplication（应用生命周期）
    ("CustomApplicationController", "POST", "create", "创建应用", "CustomApplicationDto", False),
    ("CustomApplicationController", "POST", "create-async", "异步创建应用", "CustomApplicationDto", False),
    ("CustomApplicationController", "POST", "new-layout-create-async", "新布局异步创建", "CustomApplicationDto", False),
    ("CustomApplicationController", "POST", "copy", "复制应用", "Map", False),
    ("CustomApplicationController", "POST", "copy-async", "异步复制应用", "Map", False),
    ("CustomApplicationController", "POST", "delete", "删除应用", "Map", False),
    ("CustomApplicationController", "POST", "update-caption", "更新应用名称", "Map", False),
    ("CustomApplicationController", "POST", "update-usage-state", "更新使用状态", "Map", False),
    ("CustomApplicationController", "POST", "update-deploy-state", "更新部署状态", "Map", False),
    ("CustomApplicationController", "POST", "update-auth", "更新授权", "Map", False),
    ("CustomApplicationController", "POST", "search-no-page", "不分页查询应用", "Map", True),
    ("CustomApplicationController", "POST", "search-page", "分页查询应用", "Map", True),
    ("CustomApplicationController", "POST", "upgrade", "升级应用", "Map", False),
    # UdcFormDataQuery（表单数据查询——核心只读）
    ("UdcFormDataQueryController", "POST", "query", "表单数据查询", "EntityDataRequestDto", True),
    # UdcRuntimeDatabase（数据库直查——核心只读）
    ("UdcRuntimeDatabaseController", "GET", "query-data", "查询数据库数据", "RuntimeDataBaseQueryDataReqDto", True),
    # UdcDataType
    ("UdcDataTypeController", "GET", "getAll", "全部数据类型", "-", True),
    # GraphqlProxy（GraphQL 代理——6 个未归位 op 的后端通道）
    ("GraphqlProxyController", "POST", "graphql", "执行 GraphQL", "GraphqlProxyRequestDto", False),
    # UdcSerialConfig（流水号配置）
    ("UdcSerialConfigController", "POST", "update", "更新流水号配置", "UdcSerialConfigDto", False),
    ("UdcSerialConfigController", "POST", "list", "条件查询(不分页)", "Map", True),
    ("UdcSerialConfigController", "GET", "select-entity-list", "有流水号配置的实体列表", "String appName", True),
    ("UdcSerialConfigController", "POST", "select-entity-by-serial-id", "按流水号Id取实体字段", "Map", True),
    ("UdcSerialConfigController", "GET", "refresh-historical-data/{appName}", "清理流水号配置", "String", False),
    ("UdcSerialConfigController", "GET", "cache-evict/{appName}", "清理流水号缓存", "String", False),
    # RuntimeEnvCheck（环境自检——全只读）
    ("RuntimeEnvCheckController", "GET", "build-info/{appName}", "构建信息", "String", True),
    ("RuntimeEnvCheckController", "GET", "app-version/{appName}", "应用版本", "String", True),
    ("RuntimeEnvCheckController", "GET", "data-permission/{entityFullName}", "数据权限检查", "String", True),
    ("RuntimeEnvCheckController", "GET", "response-length/{length}", "响应长度检查", "Integer", True),
    ("RuntimeEnvCheckController", "POST", "request-content", "请求内容检查", "String", True),
    # UdcAppLog（应用日志——查询只读 / 管理写）
    ("UdcAppLogController", "POST", "create-batch", "批量创建日志", "List", False),
    ("UdcAppLogController", "POST", "search/microflow", "微流程日志查询", "Map", True),
    ("UdcAppLogController", "POST", "search-details/microflow", "微流程日志详情", "Map", True),
    ("UdcAppLogController", "POST", "search-details/microflow/flowLog", "微流程流转日志", "Map", True),
    ("UdcAppLogController", "POST", "search/dataflow", "数据流日志查询", "Map", True),
    ("UdcAppLogController", "POST", "search-details/dataflow", "数据流日志详情", "Map", True),
    ("UdcAppLogController", "POST", "search/deduction", "推导日志查询", "Map", True),
    ("UdcAppLogController", "POST", "search-details/deduction", "推导日志详情", "Map", True),
    ("UdcAppLogController", "POST", "datalog/search", "数据日志查询", "Map", True),
    ("UdcAppLogController", "GET", "datalog/{id}", "数据日志详情", "Long", True),
    ("UdcAppLogController", "GET", "datalog/list-by-dataid/{dataId}", "按数据Id查日志", "Long", True),
    ("UdcAppLogController", "POST", "save/front-log", "保存前端日志", "Map", False),
    ("UdcAppLogController", "POST", "delete-all", "删除全部日志", "Map", False),
    ("UdcAppLogController", "POST", "clear-org-manager", "清理组织管理者", "Map", False),
    ("UdcAppLogController", "POST", "clear-runtime-data-source-cache", "清运行态数据源缓存", "Map", False),
    ("UdcAppLogController", "POST", "init-tenant-data", "初始化租户数据", "Map", False),
    ("UdcAppLogController", "POST", "update-data-init-version", "更新数据初始化版本", "Map", False),
    ("UdcAppLogController", "GET", "unload-dynamic-app/{appName}", "卸载动态应用", "String", False),
    ("UdcAppLogController", "GET", "enable-log/{enable}", "启停日志", "Boolean", False),
    # 其它
    ("UdcFunctionNodeController", "GET", "select-function-node-tree/{appName}", "功能节点树", "String", True),
    ("UdcRtPageInfoController", "POST", "check-page-exists", "页面是否存在", "Map", True),
    ("UdcRtPageInfoController", "POST", "select-host-and-only-page-pages", "宿主应用页面列表", "Map", True),
    # ---- extmetadata.UdcMetaDataController（同挂 udc-runtime/meta-data 基址）----
    ("UdcMetaDataController", "GET", "select-all-entity-by-app-name/{appName}", "应用全部实体简表", "String", True),
    ("UdcMetaDataController", "GET", "select-aggregation-entity/list/{appName}", "应用聚合实体简表", "String", True),
    ("UdcMetaDataController", "POST", "select-entity", "查实体元数据", "UdcEntityMetaDataSearchDto", True),
    ("UdcMetaDataController", "POST", "select-aggregation-entity", "聚合实体(含关联)", "UdcEntityMetaDataSearchDto", True),
    ("UdcMetaDataController", "POST", "select-refer-by-entity", "按实体查引用元数据", "UdcReferMetaDataSearchDto", True),
    ("UdcMetaDataController", "POST", "refer-and-metadata", "引用+元数据(V1)", "UdcReferMetaDataSearch_V1_Dto", True),
    ("UdcMetaDataController", "POST", "v2/refer-and-metadata", "引用+元数据(V2)", "UdcReferMetaDataSearchDto", True),
    ("UdcMetaDataController", "POST", "select-page", "查页面元数据", "UdcPageInfoSearchV2Dto", True),
    ("UdcMetaDataController", "POST", "select-page-list", "批量查页面元数据", "List", True),
    ("UdcMetaDataController", "GET", "select-page-layout-info-list/{appName}", "应用页面布局信息列表", "String", True),
    ("UdcMetaDataController", "POST", "select-page-layout-info", "查页面布局信息", "UdcPageInfoSearchV2Dto", True),
    ("UdcMetaDataController", "POST", "select-page-layout", "查页面布局", "UdcPageInfoSearchV2Dto", True),
    ("UdcMetaDataController", "POST", "select-page-layout-list", "批量查页面布局", "List", True),
    ("UdcMetaDataController", "POST", "select-host-app-page-layout", "宿主应用页面布局", "UdcMetaDataSearchDto", True),
    ("UdcMetaDataController", "POST", "check-app-include-url", "检查应用包含URL", "UdcCheckAppIncludeUrlDto", True),
    ("UdcMetaDataController", "POST", "read-runtime-json", "读运行态JSON", "SearchJsonMetadataDto", True),
    ("UdcMetaDataController", "POST", "delete-metadata-by-app-name", "按应用名删元数据", "Map", False),
    ("UdcMetaDataController", "POST", "delete-layout-app-metadata-by-host-app-name", "按宿主删布局元数据", "Map", False),
    # ---- extmetadata.UdcAppInfoController（udc-app-info 基址）----
    ("UdcAppInfoController", "GET", "entity-table/{appName}", "应用实体→表映射", "String", True),
    ("UdcAppInfoController", "GET", "entity-table-info/{appName}/{tableName}", "实体→表详情", "String", True),
    ("UdcRtPageLogController", "POST", "create-batch", "批量创建页面日志", "List", False),
    ("UdcRtPageLogController", "POST", "search", "页面日志查询", "Map", True),
    ("UdcRtPageLogController", "POST", "search-non-metadata", "页面日志查询(无元数据)", "Map", True),
    ("UdcRtPageLogController", "POST", "delete-all", "删除全部页面日志", "Map", False),
    ("UdcRoleRtController", "GET", "has-system-admin/{appName}", "是否系统管理员", "String", True),
    ("UdcAttrSnapshotRtController", "POST", "delete-by-data-id/{dataId}", "按数据Id删属性快照", "Long", False),
    ("UdcAttrSnapshotRtController", "POST", "delete-by-master-data-id/{masterDataId}", "按主数据Id删快照", "Long", False),
    ("AttachmentTemplateController", "POST", "create", "创建附件模板", "AttachmentTemplateDto", False),
    ("AttachmentTemplateController", "POST", "create-batch", "批量创建附件模板", "List", False),
    ("AttachmentTemplateController", "GET", "{guid}", "附件模板详情", "String", True),
    ("AttachmentTemplateController", "POST", "select-by-guids", "按guid批量查", "List", True),
    ("AttachmentTemplateController", "GET", "app/{appId}", "按应用查附件模板", "Long", True),
    ("AttachmentTemplateController", "POST", "delete/{guid}", "删除附件模板", "String", False),
    ("AttachmentTemplateController", "POST", "delete-by-guids", "按guid批量删除", "List", False),
    ("DynamicJarController", "POST", "import", "导入动态jar", "MultipartFile", False),
    ("DynamicJarController", "GET", "import/status/{requestId}", "导入状态", "String", True),
    ("DynamicJarController", "GET", "download/{appName}", "下载动态jar", "String", True),
    ("DynamicJarController", "GET", "download", "下载动态jar(旧)", "String", True),
    ("RuntimeCOLISplitController", "POST", "upgrade", "COLI升级", "MultipartFile", False),
    ("RuntimeCOLISplitController", "POST", "upload/result", "上传COLI结果", "Map", False),
    ("FrontFunctionSupportController", "POST", "calculate", "功能计算", "Map", False),
    ("UdcEntityUpdateRtTestController", "POST", "update-with-fields", "按字段更新(测试)", "Map", False),
)

# ---- 派生：全量端点路径（归一化 {var}）----
def _norm(p: str) -> str:
    import re
    return re.sub(r"/\{[^}]+\}", "/{x}", p).rstrip("/")


RUNTIME_ENDPOINT_PATHS: dict[str, tuple[str, str, bool]] = {
    _norm(f"{RUNTIME_CONTROLLERS[c]}/{s}"): (m, desc, ro)
    for c, m, s, desc, _dto, ro in RUNTIME_ENDPOINTS
}
# 真实路径（{var} 替换为具体值）→ 模式的反向索引：按段数匹配
import re as _re


def _match_pattern(path: str) -> str | None:
    """把真实路径（含具体值）匹配到端点模式（含 {x}）。

    规则：逐段比较——字面段必须相等，{x} 段匹配任意非空段。
    """
    p = path.rstrip("/")
    for pat in RUNTIME_ENDPOINT_PATHS:
        pa, pp = pat.split("/"), p.split("/")
        if len(pa) != len(pp):
            continue
        if all(a == b or (a == "{x}" and b) for a, b in zip(pa, pp)):
            return pat
    return None


# ---- 运行态 DTO 必填字段（@NotNull/@NotBlank，反编译权威）----
RUNTIME_DTO_REQUIRED: dict[str, tuple[str, ...]] = {
    # POST /udc-runtime/data/query（表单数据查询）
    "EntityDataRequestDto": ("appName", "entityFullName", "dataId"),
    # POST /udc-runtime/serial-config/update（流水号配置更新）
    "UdcSerialConfigDto": ("sourceFullName", "entityFullName"),
    # GET /udc-runtime/database/query-data（无 @NotNull，都可空）
    "RuntimeDataBaseQueryDataReqDto": (),
}


def validate_runtime_dto(dto_name: str, body: dict) -> list[str]:
    """校验运行态 DTO 必填字段（空=通过；未登记的 DTO 返回提示）。"""
    req = RUNTIME_DTO_REQUIRED.get(dto_name)
    if req is None:
        return [f"运行态 DTO '{dto_name}' 未登记（见 RUNTIME_DTO_REQUIRED）"]
    errs: list[str] = []
    for f in req:
        v = body.get(f)
        if v is None or v == "":
            errs.append(f"{dto_name} 缺必填字段 {f}")
    return errs


def is_readonly_endpoint(path: str) -> bool | None:
    """判断路径是否只读（支持 {var} 模式与含具体值的真实路径）。返回 None 表示未登记。"""
    e = RUNTIME_ENDPOINT_PATHS.get(_norm(path))
    if e is None:
        pat = _match_pattern(path)
        e = RUNTIME_ENDPOINT_PATHS.get(pat) if pat else None
    return e[2] if e else None


def find_endpoint(path: str) -> tuple[str, str, bool] | None:
    """按路径找端点描述：(HTTP方法, 描述, 只读)。支持模式与真实路径，未登记返回 None。"""
    e = RUNTIME_ENDPOINT_PATHS.get(_norm(path))
    if e is None:
        pat = _match_pattern(path)
        e = RUNTIME_ENDPOINT_PATHS.get(pat) if pat else None
    return e
