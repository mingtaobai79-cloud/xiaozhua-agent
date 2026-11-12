# UDC 五张调用面与运行态端点目录

适用：追某个 UDC 接口/能力时先确定它在哪一面（串面必 404 或误判），以及需要 `/udc-runtime/*` 运行态端点清单/只读分级。

## 1. 四张调用面
| 面 | 前缀/特征 | 承接构件 | 用途 |
|---|---|---|---|
| 设计态 REST | `/udc/*` | udc-web（54 Controller / 299 REST） | 设计器页面操作（实体/页面/微流程/菜单增删改查） |
| GraphQL 动态字段 | 前端 `udcQueryLoader`/`udcMutationLoader` | 后端 `udc-runtime/graphql-proxy/graphql` → `GraphqlProxyAppServiceImpl`（autocode `GraphQLControllerUtil.java.ftl` 生成桥接） | 设计器部分动态查询（op 无 REST 路径时的去向） |
| 运行态 REST | `/udc-runtime/*` | **跨构件并集**：udc-starter-runtime 19 + boot-starter-extmetadata 2 = 21 Controller | 应用运行时（表单查询/流水号/日志/环境自检/草稿/应用生命周期/元数据查询） |
| 元数据 | `/metadata/*` | boot-starter-metadata（12 端点） | appName 合法性/发布状态/`udcApp`/`enableGraphql`/宿主应用 |
| **流水号** | `/serial-*`（serial-scheme / serial-number / serial-range / serial-condition） | boot-starter-serialnumber（**独立于 udc 构件**，4 Controller / 45 端点） | 流水号方案设计/取号/号段/条件——不是 `/udc-runtime/*` 子集 |

关键：starter（`udc-starter-*`）里可以有完整 Controller 层，不是只有 AppService。抽端点目录时 `@RequestMapping` 扫描范围必须包含它们，否则运行态整面漏掉——`udc-runtime/*` 端点在 udc-web 的 54 个 Controller 里一个都没有。**URL 前缀 ≠ 构件归属**：`udc-runtime/meta-data` 基址由三个 Controller 共服务（udc-starter-runtime 的 UdcFunctionNodeController/UdcRtPageInfoController + boot-starter-extmetadata 的 UdcMetaDataController），另有 extmetadata 的 UdcAppInfoController 用独立 `udc-app-info` 基址。

## 2. 运行态端点目录（按 `/udc-runtime/*` 前缀跨构件取并集，21 Controller / 98 端点）
落在 `components/udc/runtime_constraints.py` `RUNTIME_ENDPOINTS`（controller/method/path/描述/DTO/只读）。

抽端点目录只扫 `udc-starter-*` 会漏 20 个端点（select-entity / select-page / check-app-include-url / entity-table 等，全在 extmetadata 的两个 Controller 上）。

udc-starter-runtime 只读核心面：
| 端点 | 方法 | 说明 |
|---|---|---|
| `udc-runtime/data/query` | POST | 表单数据查询（EntityDataRequestDto: appName/entityFullName/dataId @NotNull） |
| `udc-runtime/database/query-data` | GET | 数据库直查（无必填） |
| `udc-runtime/datatype/getAll` | GET | 全部数据类型 |
| `udc-runtime/graphql-proxy/graphql` | POST | GraphQL 代理（表面是写，实为查询通道） |
| `udc-runtime/serial-config/list` | POST | 流水号方案不分页查询 |
| `udc-runtime/evn-check/{build-info,app-version,data-permission,response-length,request-content}` | GET/POST | 环境自检 5 项 |
| `udc-runtime/app-log/search*`、`datalog/{id}`、`datalog/list-by-dataid/{dataId}` | POST/GET | 日志查询族 |
| `udc-runtime/meta-data/{select-function-node-tree,check-page-exists,select-host-and-only-page-pages}` | GET/POST | 功能节点树/页面存在性/宿主页面 |

extmetadata 只读核心面（同样挂 `udc-runtime/meta-data`）：
| 端点 | 方法 | 说明 |
|---|---|---|
| `select-all-entity-by-app-name/{appName}` | GET | 应用全部实体简表 |
| `select-aggregation-entity/list/{appName}` | GET | 应用聚合实体简表 |
| `select-entity` / `select-aggregation-entity` | POST | 查实体元数据（含关联） |
| `select-refer-by-entity` | POST | 按实体查引用元数据 |
| `refer-and-metadata` / `v2/refer-and-metadata` | POST | 引用+元数据（V1/V2，DTO 不同） |
| `select-page` / `select-page-list` | POST | 查页面元数据 |
| `select-page-layout-info-list/{appName}` | GET | 应用页面布局信息列表 |
| `select-page-layout-info` / `select-page-layout` / `select-page-layout-list` | POST | 查页面布局（3 个变体） |
| `select-host-app-page-layout` | POST | 宿主应用页面布局 |
| `check-app-include-url` | POST | 检查应用包含 URL |
| `read-runtime-json` | POST | 读运行态 JSON |

`udc-app-info/*`（2 端点，独立基址）：`entity-table/{appName}`（应用实体→表映射）、`entity-table-info/{appName}/{tableName}`（实体→表详情）。

写端点（LIVE 只读探针禁调）：`custom-app/*`（create/copy/copy-async/create-async/delete/update-*/upgrade）、`serial-config/{update,refresh-historical-data,cache-evict}`、`app-draft/{create,delete,delete-all,delete/timeout}`、`app-log/{delete-all,clear-*,init-tenant-data,unload-dynamic-app,enable-log,save/front-log,update-data-init-version,create-batch}`、`attachment-template/{create,create-batch,delete/*}`、`dynamic/jar/import`、`coli/*`、`attr-snapshot/*`、`rt-page-log/{create-batch,delete-all}`、`meta-data/{delete-metadata-by-app-name,delete-layout-app-metadata-by-host-app-name}`。**例外**：`dynamic/jar/import/status/{requestId}` 名字含 import 但功能是查询状态 → 只读。

DTO 必填（反编译 @NotNull）：`EntityDataRequestDto`(appName/entityFullName/dataId)、`UdcSerialConfigDto`(sourceFullName/entityFullName)；`RuntimeDataBaseQueryDataReqDto` 无必填。

## 3. 元数据域（boot-starter-metadata 5.3.358）
- 端点：`metadata/{starter-all,starter,starters,starter-multi-version,check-service-version,service-all,service,services,service-multi-version,service-by-hostAppName,service-normal,service-development}`
- `MetadataTypeEnum` 14 种（带 code）：Service(0) Entity(1) Agg(2) Enum(3) RestApi(4) OpenApi(5) Mq(6) Dto(7) AppService(8) CtpEnum(9) Page(10) Starter(11) AggEntity(12) CtpEnumItem(13)
- `ServiceStatusEnum`：PUBLISHED / UNPUBLISHED
- `ServiceMetadataDto` 语义键：`udcApp`（是否 UDC 应用）、`hostAppName`、`enableGraphql`（默认 true）、`status`、`appVersion`、`udcDesignVersion`、`dynamicService`、`md5`、`depends`
- 落地：`components/udc/metadata_constraints.py`（`is_udc_app`/`is_service_published`/`is_graphql_enabled` 谓词）

## 4. 抽端点目录的陷阱
- **计数别信全局正则**：`@GetMapping(value={"datalog/{id}"})` 的 `{var}` 会被截断正则吃成 `{id`，归一化后字典键对不上，平白多出假缺口/假多。逐 Controller 列出注解完整文本再计数。
- **查找要逐段匹配**：字典键是 `datalog/{x}`，查 `datalog/123` 用字面 key 必 miss——段级比较（字面段相等 + `{x}` 段匹配任意非空段）。
- **只读/写按功能而非名字**：见上面 import/status 例外。
- **计数以模型落盘为准，不以草稿为准**：登记进 `RUNTIME_ENDPOINTS` 的元组数才是真数；写测试断言前先 `python -c "from ... import RUNTIME_ENDPOINTS; print(len(RUNTIME_ENDPOINTS))"`，不要照草稿里算的数（草稿常把跨构件并集重复计或漏计）。

## 5. 流水号域（boot-starter-serialnumber 5.3.318，独立构件）

**不是 `/udc-runtime/*` 子集**，有自己的 4 个 Controller 与 `/serial-*` 前缀。落在 `components/udc/serialnumber_constraints.py`。

| Controller | 基址 | 端点 | 核心 |
|---|---|---|---|
| SerialSchemeController | serial-scheme | 17 | create / **createEasyScheme** / update-active / search-page-4-entity-fullname / context-value/{contextKey} |
| SerialNumberController | serial-number | 13 | **get-serial-number（取号=写操作）** / batch-serial-number / preview-serial-value（只读预览） / reset-serial-number/{schemeId} / reset-app-serial-number/{appId} |
| SerialRangeController | serial-range | 14 | createUnused / createBatchUnused / batch-updateForbiddenFlag |
| SerialConditionController | serial-condition | 3 | batch-create / list / eval |

六张表（`@Table`/`@Column` 数据库层权威，nullable+默认值在列定义里）：`ctp_serial_scheme`(17列) / `ctp_serial_section`(19列) / `ctp_serial_range` / `ctp_serial_condition` / `ctp_serial_current` / `ctp_serial_history`。

枚举值域：段类型 `SerialTypeEnum` CONSTANT(0)/CONTEXT(1)/ENTITY(2)/SERIAL(3)；方案类型 `SerialRuleTypeEnum` APP(0)/BIG(1)/SMALL(2)；重置规则 `SerialResetRuleEnum` NONE(0)/YEAR(1)/MONTH(2)/DAY(3)；号段 `SerialRangeTypeEnum` RESERVE(0)/UNUSED(1)；补位/截取 `FillTypeEnum`/`CutTypeEnum` LEFT(0)/RIGHT(1)/NONE(2)。

订单编号 = 多段拼接（`ctp_serial_section`）：常量段 + 日期段（`is_date_type`+`date_pattern`）+ 流水号段（`type=SERIAL`，`section_size` 左补 `fill_char`，`start_value`/`end_value`=-1 表无上限）。

与 udc-plugin-api `UdcSerialSchemeAppService.createEasyScheme`（设计态契约）、udc-starter-runtime `serial-config/*`（运行态字段配置面）是三层关系。

### 5.1 设计器实际走的 GraphQL 面（建方案的真实路径）

`/serial-scheme/*` 是构件自己的 REST 面，但设计器里建流水号走的是 **GraphQL 代理**：

```
写  udcSerialSchemeCreatePost / udcSerialSchemeUpdatePost / udcSerialSchemeDeletePost
读  udcSerialSchemeSearchPagePost / udcSerialSchemeMaxSortNumberAppGet
    udcSerialSchemeContextValueListGet / udcDesignMetadataAggEntityExcludeBootGet
```

`DeletePost` 只认单条 `{appId, id}`（→ `content=1`）；`{appId, serialSchemeId}` 报
`BOOT_4002 数据不存在或无权限查看`。`MaxSortNumberAppGet` 是 path 形态，空参报
`@PathVariable 标注字段(path)为必填`。

### 5.2 DTO 字段名（`SerialSchemeDto` / `SerialSectionDto`，CFR 反编译）

⚠ **DTO 名 ≠ 表列名**，写 body 用 DTO 名，回读用列名：

| DTO 字段 | DB 列 | 备注 |
|---|---|---|
| `serialSectionDtoList` | — | **段列表就是这个名**；`sections` / `serialSections` / `serialSectionDtos` 全错 |
| `serialConditionDtoList` | — | 绑定实体条件 |
| `size` | `section_size` | 不是 `sectionSize` |
| `dateType` | `is_date_type` | 不是 `isDateType` |
| `show` | `is_show` | 不是 `isShow` |
| `flow` | `is_flow` | 不是 `isFlow` |
| `increase` | `is_increase` | 不是 `isIncrease` |
| `serialType` | `serial_type` | 用 `SerialRuleTypeEnum` |
| `containFlow` / `active` / `editEntity` | `is_contain_flow` / `is_active` / `edit_entity` | |

约束：`code` 只允许字母数字（`@Pattern ^[^\u4e00-\u9fa5]*$`，含中文直接拒）；
`serialSectionDtoList` 有 `@Size(min=1,max=12, groups=Create)`；
`totalSize` 必须等于各段 `size` 之和。

**枚举传字符串，DB 存 ordinal**：body 写 `"NONE"`，落库是 `2`。回读时用本节的
ordinal 表反查名字，不要凭数字猜语义（`fill_type=0` 是 `LEFT` 而非 `NONE`）。

## 6. 实体/页面枚举值域（boot-starter-extmetadata enums 包，权威全集）
抽法：整包反编译 `com/seeyon/boot/starter/extmetadata/enums/*.class`，逐枚举 dump 常量名+构造参数（code 与中文显示名都在构造参数里；code 可非连续）。

| 枚举 | 值域 | 备注 |
|---|---|---|
| EntityCategoryEnum | ENTITY(0) EXT(1) EXT_GLOBAL(2) THIRD(3) COMPONENT_ENTITY(4) BASIC_DATA(5) | 实体类别，共 6 种 |
| AttributeCalculateEnum | NORMAL(0) COMPUTE(1) AGGREGATION(2) | 计算属性 |
| AttributeSourceTypeEnum | ENTITY(0) ATTRIBUTESET(1) SYSTEM_ATTRIBUTE_SET(2) SYSTEM(4) EXT(5) | code 跳 3 |
| PageSourceTypeEnum | DESIGNER(0) PRESET(1) COPY(2) TEMPLATE(3) | 页面来源 |
| MedaDataPageTypeEnum | PORTAL(1) WELCOME(2) REPORT_FORM(3) DETAIL(4) LIST(5) APPROVAL(6) PORTLET(7) SEARCH_LIST(8) EDIT_LIST(9) LIST_DETAIL(10) ASSIST_INFO(11) OTHER(12) LAYOUT(14) SUBPAGE(13) | 14 种，LAYOUT=14 与 SUBPAGE=13 不连续 |
| OpenWayEnum | REFRESH(1) NEW_PAGE(2) | 打开方式 |
| DependentAppTypeEnum | SERVICE(0,"应用依赖") STARTER(1,"后端组件") FROM(2,"表单应用") FRONTEND(3,"前端组件") PLATFORM(4,"平台") | 含中文名 |
| FrontendPackageTypeEnum | NONE(0,"无") CONTROL(1,"控件") ACTION(2) | |
| DynamicDependencyTypeEnum | NONE(0) FORM_NORMAL(1) INTEGRATION(2) | |
| EntityActionEnum | 22 个（ENTITY_SELECT_SINGLE(1)…CASCADE_DEFAULT_VALUE(30)） | 实体动作码 |

落在 `components/udc/entity_constraints.py`（`ENTITY_CATEGORIES`/`ENTITY_CATEGORY_CODES`/`ATTRIBUTE_CALCULATE_TYPES`/`ATTRIBUTE_SOURCE_CODES`/`PAGE_SOURCE_TYPES`/`PAGE_META_CODES`/`OPEN_WAYS`/`DEPENDENT_APP_TYPES`）。
