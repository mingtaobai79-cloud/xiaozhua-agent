"""UDC 元数据域（boot-starter-metadata 5.3.358）约束模型。

证据（**字节码直读**，非 javap 文本）：
- `docs/audit/artifacts/metadata-5.3.358/MetadataController.class`
  sha256 `54d4550b60ae729bfbf9c3bf06aced32ba60c64d758fd45febb219e97808265f` / 59711 字节
- 解析器：`tools/core/enumerate_class_http_mappings.py`（直读常量池 + RuntimeVisibleAnnotations，
  不经 javap / 不经 CFR）；与 CFR 反编译双轴逐条一致（见 tests/udc/test_metadata_controller_registry.py）
- 语义支撑：`MetadataQueryAppService` / `MetadataTypeEnum` / `ServiceStatusEnum` / `ServiceMetadataDto`

**口径（2026-10-15 修正）**：本模块此前只登记 **12** 条（且 docstring 写 13，自相矛盾），
根因是当时唯一证据源 `MetadataController.javap.txt` 是**无 `-v` 的 javap 文本**，
**不含任何注解值**——按它 grep 任何路由字面量都返回 0，是**假阴性**而非「不存在」。
字节码实际：**105 个 mapping 端点**，其中 **99** 条具备类级 `@RestApi` ∧ 方法级
`@RestApiOperation`（进 GraphQL op 面），余 **6** 条只有 mapping 无 `@RestApiOperation`
（生命周期/缓存类，不进 op 面）。继承 `BaseComponentController` ⇒ 外部路径带 `/udc` 前缀。

用途：UDC 应用的"宿主应用/元数据"查询权威面。设计态与运行态都依赖它判断
 appName 是否合法、服务是否 PUBLISHED、udcApp 标记、GraphQL 是否启用等。
"""
from __future__ import annotations

# ---- Controller 基址（字节码类级 @RequestMapping 真值；外部路径另加 /udc 前缀）----
METADATA_CONTROLLER = "com.seeyon.ctp.metadata.controller.MetadataController"
METADATA_CLASS_MAPPING = "metadata"
METADATA_EXTERNAL_PREFIX = "/udc"

# ---- 元数据端点（105 条，字节码逐条直读）----
#   (http, sub_path, handler, op_code)；op_code == "" 表示无 @RestApiOperation（不进 op 面）
METADATA_ENDPOINTS: tuple[tuple[str, str, str, str], ...] = (
    ("GET", "starter-all", "selectStarterMetadataList", "Starter.1001.查询所有组件"),  # GetMapping
    ("GET", "starter", "selectStarterMetadataByName", "Starter.1002.按组件名称查询组件"),  # GetMapping
    ("POST", "starters", "selectStarterMetadataByNames", "Starter.1003.按组件名称批量查询组件"),  # PostMapping
    ("GET", "starter-multi-version", "selectMultiVersionStarterMetadataByName", "Starter.1004.组件多版本列表"),  # GetMapping
    ("POST", "check-service-version", "checkServiceVersion", "Service.1000.检查微服务版本"),  # PostMapping
    ("GET", "service-all", "selectServiceMetadataList", "Service.1001.查询所有微服务"),  # GetMapping
    ("GET", "service", "selectServiceMetadataByName", "Service.1002.按服务名查询微服务"),  # GetMapping
    ("POST", "services", "selectServiceMetadataByNames", "Service.1003.按服务名批量查询微服务"),  # PostMapping
    ("GET", "service-multi-version", "selectMultiVersionServiceMetadataByName", "Service.1004.微服务多版本列表"),  # GetMapping
    ("GET", "service-by-hostAppName", "selectServiceMetadataByHostAppName", "Service.1005.按宿主应用名称查询微服务(已发布)"),  # GetMapping
    ("GET", "service-normal", "selectNormalServiceMetadataList", "Service.1006.查询所有普通应用(已发布并且非表单应用)"),  # GetMapping
    ("GET", "service-development", "selectDevelopmentServiceMetadataList", "Service.1007.获取开发的标准应用元数据列表"),  # GetMapping
    ("GET", "online-service", "selectOnlineServiceMetadataList", "Service.1008.获取在线应用元数据列表"),  # GetMapping
    ("GET", "rest", "selectRestApiMetadata", "Rest.1001.查询指定服务Rest信息"),  # GetMapping
    ("POST", "rest-page", "selectRestApiMetadataForPage", "Rest.1002.分页查询指定服务Rest信息"),  # PostMapping
    ("POST", "rest-by-names", "selectRestApiMetadataByFullNames", "Rest.1003.批量查询Rest信息"),  # PostMapping
    ("POST", "rest-by-name", "selectRestApiMetadataByFullName", "Rest.1004.查询Rest信息"),  # PostMapping
    ("GET", "rest-and-dto", "graphql", "Rest.1005.获取指定服务的Rest和Dto元数据"),  # GetMapping
    ("GET", "rest-exclude-boot", "selectRestApiMetadataExcludeBoot", "Rest.1006.查询指定服务Rest信息(排除组件)"),  # GetMapping
    ("POST", "rest-exclude-boot-page", "selectRestApiMetadataExcludeBootForPage", "Rest.1007.分页查询指定服务Rest信息(排除组件)"),  # PostMapping
    ("GET", "open-api", "selectOpenApiMetadata", "OpenApi.1001.查询指定服务OpenApi信息"),  # GetMapping
    ("POST", "open-api-page", "selectOpenApiMetadataForPage", "OpenApi.1002.分页查询指定服务OpenApi信息"),  # PostMapping
    ("POST", "open-api-by-names", "selectOpenApiMetadataByFullNames", "OpenApi.1003.批量查詢OpenApi信息"),  # PostMapping
    ("POST", "open-api-by-name", "selectOpenApiMetadataByFullName", "OpenApi.1004.查询OpenApi信息"),  # PostMapping
    ("GET", "dto", "selectDtoMetadata", "DTO.1001.查询指定服务DTO信息"),  # GetMapping
    ("POST", "dto-page", "selectDtoMetadataForPage", "DTO.1002.分页查询指定服务DTO信息"),  # PostMapping
    ("POST", "dto-by-names", "selectDtoMetadataByFullNames", "DTO.1003.批量查詢DTO信息"),  # PostMapping
    ("POST", "dto-by-name", "selectDtoMetadataByFullName", "DTO.1004.查询DTO信息"),  # PostMapping
    ("GET", "entity-relation-dto", "selectEntityRelationDtoMetadata", "DTO.1005.查询实体关联的DTO信息"),  # GetMapping
    ("POST", "dto-by-entitys", "selectDtoMetadataByEntityFullNames", "DTO.1006.按实体FullName批量查询关联的DTO信息"),  # PostMapping
    ("POST", "dto-by-entity", "selectDtoMetadataByEntityFullName", "DTO.1007.按实体FullName查询关联的DTO信息"),  # PostMapping
    ("POST", "agg-dto", "selectAggDtoMetadataByFullName", "DTO.1008.按FullName聚合DTO信息"),  # PostMapping
    ("POST", "agg-dto-list", "selectAggDtoMetadataByFullNames", "DTO.1009.按FullName批量聚合DTO信息"),  # PostMapping
    ("GET", "dto-exclude-boot", "selectDtoMetadataExcludeBoot", "DTO.1010.查询指定服务DTO信息(排除组件)"),  # GetMapping
    ("POST", "dto-exclude-boot-page", "selectDtoMetadataExcludeBootForPage", "DTO.1011.分页查询指定服务DTO信息(排除组件)"),  # PostMapping
    ("GET", "entity-relation-dto-exclude-boot", "selectEntityRelationDtoMetadataExcludeBoot", "DTO.1012.查询实体关联的DTO信息(排除组件)"),  # GetMapping
    ("POST", "entity-relation-dto-exclude-boot-page", "selectEntityRelationDtoMetadataExcludeBootForPage", "DTO.1013.分页查询实体关联的DTO信息(排除组件)"),  # PostMapping
    ("GET", "public-dto", "selectPublicDtoMetadataList", "DTO.1014.查询指定服务公开的DTO元数据信息"),  # GetMapping
    ("POST", "public-dto-page", "selectPublicDtoMetadataForPage", "DTO.1015.分页查询指定服务公开的DTO元数据信息"),  # PostMapping
    ("GET", "enum", "selectEnumMetadata", "JavaEnum.1001.查询指定服务Enum信息"),  # GetMapping
    ("POST", "enum-page", "selectEnumMetadataForPage", "JavaEnum.1002.分页查询指定服务Enum信息"),  # PostMapping
    ("POST", "enum-by-names", "selectEnumMetadataByFullNames", "JavaEnum.1003.批量查询Enum信息"),  # PostMapping
    ("POST", "enum-by-name", "selectEnumMetadataByFullName", "JavaEnum.1004.查询Enum信息"),  # PostMapping
    ("GET", "public-enum", "selectPublicEnumMetadata", "JavaEnum.1005.查询指定服务公开的Enum元数据信息"),  # GetMapping
    ("POST", "public-enum-page", "selectPublicEnumMetadataForPage", "JavaEnum.1006.分页查询指定服务公开的Enum元数据信息"),  # PostMapping
    ("GET", "entity", "selectEntityMetadata", "Entity.1001.查询指定服务Entity信息"),  # GetMapping
    ("POST", "entity-page", "selectEntityMetadataForPage", "Entity.1002.分页查询指定服务Entity信息"),  # PostMapping
    ("POST", "entity-by-names", "selectEntityMetadataByFullNames", "Entity.1003.批量查询Entity信息"),  # PostMapping
    ("POST", "entity-by-name", "selectEntityMetadataByFullName", "Entity.1004.查询Entity信息"),  # PostMapping
    ("GET", "entity-exclude-boot", "selectEntityMetadataExcludeBoot", "Entity.1005.查询指定服务Entity信息(排除组件)"),  # GetMapping
    ("POST", "entity-exclude-boot-page", "selectEntityMetadataExcludeBootForPage", "Entity.1006.分页查询指定服务Entity信息(排除组件)"),  # PostMapping
    ("GET", "public-entity", "selectPublicEntityMetadata", "Entity.1007.查询指定服务公开的Entity元数据信息"),  # GetMapping
    ("GET", "app-service", "selectAppServiceMetadata", "AppService.1001.查询指定服务AppService元数据信息"),  # GetMapping
    ("POST", "app-service-page", "selectAppServiceMetadataForPage", "AppService.1002.分页查询指定服务AppService元数据信息"),  # PostMapping
    ("GET", "public-app-service", "selectPublicAppServiceMetadata", "AppService.1003.查询指定服务公开的AppService元数据信息"),  # GetMapping
    ("POST", "public-app-service-page", "selectPublicAppServiceMetadataForPage", "AppService.1004.分页查询指定服务公开的AppService元数据信息"),  # PostMapping
    ("POST", "app-service-by-names", "selectAppServiceMetadataByFullNames", "AppService.1005.批量查询AppService信息"),  # PostMapping
    ("POST", "app-service-by-name", "selectAppServiceMetadataByFullName", "AppService.1006.查询AppService信息"),  # PostMapping
    ("GET", "app-service-exclude-boot", "selectAppServiceMetadataExcludeBoot", "AppService.1007.查询指定服务AppService元数据信息(排除组件)"),  # GetMapping
    ("POST", "app-service-exclude-boot-page", "selectAppServiceMetadataExcludeBootForPage", "AppService.1008.分页查询指定服务AppService元数据信息(排除组件)"),  # PostMapping
    ("GET", "mq", "selectMqMetadata", "MQ.1001.查询指定服务MQ元数据信息"),  # GetMapping
    ("POST", "mq-page", "selectMqMetadataForPage", "MQ.1002.分页查询指定服务MQ元数据信息"),  # PostMapping
    ("POST", "mq-by-names", "selectMqMetadataByFullNames", "MQ.1003.批量查询MQ信息"),  # PostMapping
    ("POST", "mq-by-name", "selectMqMetadataByFullName", "MQ.1004.查询MQ信息"),  # PostMapping
    ("GET", "mq-exclude-boot", "selectMqMetadataExcludeBoot", "MQ.1005.查询指定服务MQ元数据信息(排除组件)"),  # GetMapping
    ("POST", "mq-exclude-boot-page", "selectMqMetadataExcludeBootForPage", "MQ.1006.分页查询指定服务MQ元数据信息(排除组件)"),  # PostMapping
    ("GET", "public-mq", "selectPublicMqMetadata", "MQ.1007.查询指定服务公开的MQ元数据信息"),  # GetMapping
    ("POST", "public-mq-page", "selectPublicMqMetadataForPage", "MQ.1008.分页查询指定服务公开的MQ元数据信息"),  # PostMapping
    ("GET", "agg", "selectAggMetadata", "Agg.1001.查询指定服务聚合根列表"),  # GetMapping
    ("POST", "agg-page", "selectAggMetadataForPage", "Agg.1002.分页查询指定服务聚合根列表"),  # PostMapping
    ("POST", "agg-by-names", "selectAggMetadataByFullNames", "Agg.1003.批量查询聚合根列表"),  # PostMapping
    ("POST", "agg-by-name", "selectAggMetadataByFullName", "Agg.1004.按实体FullName查询聚合根信息"),  # PostMapping
    ("GET", "agg-entity", "selectAggEntityMetadata", "Agg.1005.查询指定服务聚合根(包含实体元数据)"),  # GetMapping
    ("POST", "agg-entity-page", "selectAggEntityMetadataForPage", "Agg.1006.分页查询指定服务聚合根(包含实体元数据)"),  # PostMapping
    ("POST", "agg-entity-by-name", "selectAggEntityMetadataByFullName", "Agg.1007.按实体FullName查询聚合根(包含实体元数据)"),  # PostMapping
    ("POST", "agg-entity-by-names", "selectAggEntityMetadataByFullNames", "Agg.1008.按实体FullName批量查询聚合根(包含实体元数据)"),  # PostMapping
    ("POST", "entity-by-agg", "selectEntityListByAgg", "Agg.1009.查询聚合根下实体元数据列表"),  # PostMapping
    ("GET", "agg-exclude-boot", "selectAggMetadataExcludeBoot", "Agg.1010.查询指定服务聚合根列表(排除组件)"),  # GetMapping
    ("POST", "agg-exclude-boot-page", "selectAggMetadataExcludeBootForPage", "Agg.1011.分页查询指定服务聚合根列表(排除组件)"),  # PostMapping
    ("GET", "agg-entity-exclude-boot", "selectAggEntityMetadataExcludeBoot", "Agg.1012.查询指定服务聚合根(包含实体元数据)(排除组件)"),  # GetMapping
    ("POST", "agg-entity-exclude-boot-page", "selectAggEntityMetadataExcludeBootForPage", "Agg.1013.分页查询指定服务聚合根(包含实体元数据)(排除组件)"),  # PostMapping
    ("POST", "refer", "selectReferMetadataByEntity", "Refer.1001.按实体FullName查询参照信息"),  # PostMapping
    ("POST", "refer-and-app", "selectReferAndAppMetadataByEntity", "Refer.1002.按实体FullName查询参照及微服务信息"),  # PostMapping
    ("GET", "ctp-enum", "selectCtpEnumMetadata", "CtpEnum.1001.查询指定服务CtpEnum信息"),  # GetMapping
    ("POST", "ctp-enum-page", "selectCtpEnumMetadataForPage", "CtpEnum.1002.分页查询指定服务CtpEnum信息"),  # PostMapping
    ("POST", "ctp-enum-by-names", "selectCtpEnumMetadataByFullNames", "CtpEnum.1003.批量查詢CtpEnum信息"),  # PostMapping
    ("POST", "ctp-enum-by-name", "selectCtpEnumMetadataByFullName", "CtpEnum.1004.查询CtpEnum信息"),  # PostMapping
    ("GET", "ctp-enum-item", "selectCtpEnumItemMetadata", "CtpEnumItem.1001.查询指定服务CtpEnumItem信息"),  # GetMapping
    ("POST", "ctp-enum-item-page", "selectCtpEnumItemMetadataForPage", "CtpEnumItem.1002.分页查询指定服务CtpEnumItem信息"),  # PostMapping
    ("POST", "ctp-enum-item-by-names", "selectCtpEnumItemMetadataByFullNames", "CtpEnumItem.1003.批量查詢CtpEnumItem信息"),  # PostMapping
    ("POST", "ctp-enum-item-by-name", "selectCtpEnumItemMetadataByFullName", "CtpEnumItem.1004.查询CtpEnumItem信息"),  # PostMapping
    ("GET", "page", "selectPageMetadata", "Page.1001.查询指定服务Page信息"),  # GetMapping
    ("POST", "page-page", "selectPageMetadataForPage", "Page.1002.分页查询指定服务Page信息"),  # PostMapping
    ("POST", "page-by-names", "selectPageMetadataByFullNames", "Page.1003.批量查詢Page信息"),  # PostMapping
    ("POST", "page-by-name", "selectPageMetadataByFullName", "Page.1004.查询Page信息"),  # PostMapping
    ("GET", "json", "selectPageMetadataByFullName", "Json.1001.查询Json元数据信息"),  # GetMapping
    ("GET", "downgrade", "downgrade", "元数据降级为当前启动版本"),  # GetMapping
    ("GET", "upgrade", "upgrade", "元数据2024430版本升级"),  # GetMapping
    ("GET", "downgrade-starter", "downgradeStarterMetadata", "降级指定组件元数据版本"),  # GetMapping
    ("GET", "sync-cache", "syncCache", ""),  # GetMapping
    ("GET", "refresh", "refresh", ""),  # GetMapping
    ("GET", "downgrade-all", "downgradeAll", ""),  # GetMapping
    ("GET", "refresh-all", "refreshAll", ""),  # GetMapping
    ("GET", "online-app-info", "appInfo", ""),  # GetMapping
    ("GET", "online-front-app-info", "frontAppInfo", ""),  # GetMapping
)

METADATA_ENDPOINT_COUNT = 105          # 带 HTTP mapping 的端点数
METADATA_OP_SURFACE_COUNT = 99         # 其中进 GraphQL op 面的条数
METADATA_NO_OP_SUBS: tuple[str, ...] = (
    "sync-cache", "refresh", "downgrade-all", "refresh-all",
    "online-app-info", "online-front-app-info",
)

METADATA_ENDPOINT_PATHS: dict[str, tuple[str, str]] = {
    f"metadata/{sub}": (http, op or handler) for http, sub, handler, op in METADATA_ENDPOINTS
}


# ---- 元数据类型（MetadataTypeEnum，14 种，含 code）----
METADATA_TYPES: dict[str, int] = {
    "Service": 0, "Entity": 1, "Agg": 2, "Enum": 3, "RestApi": 4, "OpenApi": 5,
    "Mq": 6, "Dto": 7, "AppService": 8, "CtpEnum": 9, "Page": 10,
    "Starter": 11, "AggEntity": 12, "CtpEnumItem": 13,
}

# ---- 服务状态（ServiceStatusEnum）----
SERVICE_STATES: tuple[str, ...] = ("PUBLISHED", "UNPUBLISHED")

# ---- ServiceMetadataDto 字段（元数据语义键）----
SERVICE_METADATA_FIELDS: dict[str, str] = {
    "appName": "应用编码",
    "mavenInfo": "Maven 坐标（groupId/artifactId/version）",
    "dynamicService": "是否动态服务（默认 false）",
    "dynamicModuleGroup": "动态模块组",
    "dynamicFeatureType": "动态功能类型",
    "hostAppName": "宿主应用编码（UDC 应用挂在宿主上）",
    "tenantId": "租户Id",
    "udcDesignVersion": "UDC 设计态版本",
    "udcApp": "是否 UDC 应用",
    "enableGraphql": "是否启用 GraphQL（默认 true）",
    "status": "服务状态（PUBLISHED/UNPUBLISHED）",
    "appVersion": "应用版本",
    "caption": "显示名",
    "description": "描述",
    "md5": "元数据 md5",
    "depends": "依赖列表（BuildInfo）",
}

# ---- StarterMetadataDto 字段 ----
STARTER_METADATA_FIELDS: dict[str, str] = {
    "name": "starter 名称",
    "caption": "显示名",
    "basePackage": "基础包名",
    "type": "类型",
    "buildInfo": "构建信息",
}


def metadata_external_path(sub_path: str) -> str:
    """子路径 -> 外部可寻址路径（BaseComponentController 子类叠加 /udc 前缀）。

    LIVE 实证：`/udc/metadata/app-service-by-name`（RUNTIME-URL-SURFACE.md 发现 A）。
    """
    return f"{METADATA_EXTERNAL_PREFIX}/{METADATA_CLASS_MAPPING}/{sub_path.strip('/')}"


def is_metadata_op_exposed(sub_path: str) -> bool:
    """该子路径是否进 GraphQL op 面（类级 @RestApi ∧ 方法级 @RestApiOperation 缺一不可）。"""
    return sub_path.strip("/") not in METADATA_NO_OP_SUBS


def find_metadata_endpoint(path: str) -> tuple[str, str] | None:
    """按路径查元数据端点：(HTTP方法, op_code 或 handler)。未登记返回 None。

    接受 `metadata/<sub>` 与 `/udc/metadata/<sub>` 两种写法。
    """
    key = path.strip("/")
    if key.startswith("udc/"):
        key = key[len("udc/"):]
    return METADATA_ENDPOINT_PATHS.get(key)


def is_udc_app(service_metadata: dict) -> bool:
    """按 ServiceMetadataDto 语义判断是否 UDC 应用。"""
    return bool(service_metadata.get("udcApp"))


def is_service_published(service_metadata: dict) -> bool:
    """按 ServiceMetadataDto.status 判断服务是否已发布。"""
    return service_metadata.get("status") == "PUBLISHED"


def is_graphql_enabled(service_metadata: dict) -> bool:
    """按 ServiceMetadataDto.enableGraphql 判断是否启用 GraphQL（默认 true）。"""
    return service_metadata.get("enableGraphql", True) is not False
