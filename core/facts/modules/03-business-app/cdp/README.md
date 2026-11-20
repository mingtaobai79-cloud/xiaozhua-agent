# 数据平台（cdp）

## 一句话

`com.seeyon.cdp` 域的**可调用接口面**：6 个构件、2,867 个类、19 个 facade 接口 / 90 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `cdp-data-biz` | biz | 1,927 |
| `cdp-schedule-biz` | biz | 483 |
| `cdp-common` | common | 279 |
| `cdp-data-facade` | facade | 127 |
| `cdp-data-web` | web | 48 |
| `cdp-schedule-web` | web | 3 |
| **合计** | | **2,867** |

## 二、分层规律（写代码前必读）

`com.seeyon.cdp` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

| 接口族 | 包 | 能力 | 什么时候用 |
|---|---|---|---|
| `*BaseAppService` | `api.core.*` | **含写**：create / update / 全字段查询 / dynamic | 要改数据，或要完整 DTO |
| `*CoreAppService` | `api.core.*` | **只读**：select*，Core DTO 字段精简 | 只查不改，性能敏感 |
| `OrgCommonAppService` | `api.common` | **业务聚合**：按选人数据解析、权限、组织域、扩展属性反查 | 需要「按规则找人」而不是按 id 查 |

调用顺序建议：

```
知道 id       →  XxxCoreAppService.selectXxxById        （最轻）
知道业务规则   →  OrgCommonAppService.selectXxxBySelectPeopleData
要写          →  XxxBaseAppService.create / update
```

## facade 层：19 个接口 / 90 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.cdp.auth.api` | 7 | 38 |
| `com.seeyon.cdp.bi.api` | 1 | 2 |
| `com.seeyon.cdp.common.api` | 1 | 17 |
| `com.seeyon.cdp.common.metadata.api` | 2 | 14 |
| `com.seeyon.cdp.common.metadata.api.identifier` | 1 | 1 |
| `com.seeyon.cdp.dataset.api` | 1 | 2 |
| `com.seeyon.cdp.etl.api` | 2 | 3 |
| `com.seeyon.cdp.index.api` | 2 | 9 |
| `com.seeyon.cdp.indicator.api` | 1 | 2 |
| `com.seeyon.cdp.stream.api` | 1 | 2 |
| **合计** | **19** | **90** |

### `com.seeyon.cdp.auth.api`

#### DevicePermissionManager

`com.seeyon.cdp.auth.api.DevicePermissionManager` · 构件 `cdp-data-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `register` | `Long arg0` | `void` | 注册（Long） |
| `unRegister` | `Long arg0` | `void` | 注册（Long） |

#### OrgManager

`com.seeyon.cdp.auth.api.OrgManager` · 构件 `cdp-data-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getOrgIdList` | `Long arg0` | `List<String>` | 列表获取组织 |
| `getOrgAndLevelByUser` | `Long arg0` | `CurrentUerOrgAndLevelDto` | 获取组织职务级别And按用户 |
| `getOrgAndLevel` | `Long arg0` | `CurrentUerOrgAndLevelDto` | 获取组织职务级别And |
| `getInstitutionIdLevel` | `Long arg0` | `CurrentUerOrgAndLevelDto` | 获取机构职务级别 |
| `getInstitutionFirstLevelUnitIds` | `Long arg0` | `List<Long>` | 获取机构第一级职务级别单位Ids |
| `getInstitutionLevelDepartmentUnitIds` | `Long arg0` | `List<Long>` | 获取机构职务级别部门单位Ids |
| `getUserAuthorId` | `Long arg0` | `Set<String>` | 获取用户Author |

#### PermissionManager

`com.seeyon.cdp.auth.api.PermissionManager` · 构件 `cdp-data-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `registerResourcePermission` | `PermissionRegisterMessage arg0` | `void` | 注册资源权限 |
| `isResourceHavePermission` | `PermissionQueryParam arg0` | `boolean` | 判断资源权限Have |
| `isHaveAllResource` | `—` | `boolean` | 全部判断资源Have |
| `getResourceCodes` | `PermissionQueryParam arg0` | `List<String>` | 获取资源编码 |
| `deleteResourcePermission` | `String arg0` | `void` | 删除资源权限 |

#### ResourceManager

`com.seeyon.cdp.auth.api.ResourceManager` · 构件 `cdp-data-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `registerResource` | `ResourceRegisterMessage arg0` | `void` | 注册资源 |
| `deleteResource` | `String arg0` | `void` | 删除资源 |

#### RowColumnAuthManager

`com.seeyon.cdp.auth.api.RowColumnAuthManager` · 构件 `cdp-data-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `registerPermission` | `RowPermissionRegisterMessage arg0` | `void` | 注册权限 |
| `deletePermission` | `Long arg0` | `void` | 删除权限 |
| `deletePermissionBatch` | `List<Long> arg0` | `void` | 批量删除权限 |
| `getCheckAuthDtoList` | `Long arg0` | `List<CheckAuthDto>` | 列表获取认证CheckDto |
| `createDataBatch` | `List<ResourceDataAuth> arg0` | `void` | 批量新建数据 |
| `createOrgBatch` | `List<ResourceOrgData> arg0` | `void` | 批量新建组织 |
| `getOrgDataList` | `List<Long> arg0` | `List<ResourceOrgData>` | 列表获取组织数据 |
| `getDataAuthList` | `List<Long> arg0` | `List<ResourceDataAuth>` | 列表获取数据认证 |
| `getRowColumnContext` | `Long arg0` | `RowColumnContext` | 获取行ColumnContext |
| `getUserOrgContext` | `Long arg0` | `UserOrgContext` | 获取用户组织Context |

#### SystemVariableManager

`com.seeyon.cdp.auth.api.SystemVariableManager` · 构件 `cdp-data-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getSystemVarList` | `—` | `List<SystemVarDto>` | 列表获取SystemVar |
| `getSystemVarValues` | `String arg0` | `List<SystemVarData>` | 获取SystemVarValues |
| `isListSystemFunctionName` | `String arg0` | `boolean` | 列表判断名称SystemFunction |

#### UserManager

`com.seeyon.cdp.auth.api.UserManager` · 构件 `cdp-data-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getRoleCodeList` | `Long arg0` | `List<String>` | 列表获取角色编码 |
| `getRoleIdList` | `Long arg0` | `List<String>` | 列表获取角色 |
| `isDevice` | `Long arg0` | `boolean` | 判断Device |
| `getUserInfo` | `Long arg0` | `UserInfo` | 获取用户 |
| `selectDeviceUser` | `—` | `List<UserInfo>` | 查询用户Device |
| `pageSelectDeviceUser` | `PageRequest arg0` | `PageData<UserInfo>` | 查询用户Device |
| `selectUserRoleCodeFromOrg` | `Long arg0` | `List<String>` | 查询用户角色编码组织From |
| `selectAdminAppNames` | `Long arg0` | `List<String>` | 查询应用名称Admin |
| `isExternal` | `Long arg0` | `boolean` | 判断外部人员 |

### `com.seeyon.cdp.bi.api`

#### ReportOpenApiAppService

`com.seeyon.cdp.bi.api.ReportOpenApiAppService` · 构件 `cdp-data-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getReportDetail` | `SingleRequest<ReportDetailRequestDto> arg0` | `SingleResponse<ReportDetailDto>` | 获取ReportDetail |
| `getReportResult` | `SingleRequest<ReportResultRequestDto> arg0` | `SingleResponse<ReportResultDto>` | 获取ReportResult |

### `com.seeyon.cdp.common.api`

#### CdpBiz4UdcAppService

`com.seeyon.cdp.common.api.CdpBiz4UdcAppService` · 构件 `cdp-data-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `deploy` | `SingleRequest<PublishParamsDto> arg0` | `SingleResponse<PublishResultDto>` | 部署PublishParams |
| `detectionV2` | `SingleRequest<ValidationParamsDto> arg0` | `SingleResponse<CdpDetectionDto>` | 检测V2 |
| `transportOut` | `SingleRequest<TransportOutRequestDto> arg0` | `SingleResponse<String>` | CDP 数据导出给 UDC（单版本） |
| `transportOutV2` | `SingleRequest<TransportOutRequestDto> arg0` | `SingleResponse<String>` | CDP 数据导出给 UDC（V2，字段更全） |
| `transportIn` | `SingleRequest<String> arg0` | `SingleResponse<Boolean>` | UDC 数据导入到 CDP（单版本） |
| `transportInV2` | `SingleRequest<String> arg0` | `SingleResponse<Boolean>` | UDC 数据导入到 CDP（V2） |
| `getReportList` | `SingleRequest<UdcReportRequestDto> arg0` | `ListResponse<UdcReportDto>` | 列表获取Report |
| `getCdpDataIdList` | `—` | `ListResponse<String>` | 列表获取数据Cdp |
| `deleteApp` | `SingleRequest<DeleteAppParamsDto> arg0` | `SingleResponse<Boolean>` | 删除应用 |
| `detectionPartEntityForDataset` | `SingleRequest<CdpDetectionEntityDto> arg0` | `ListResponse<CdpDetectionErrorDto>` | 检测实体PartForDataset |
| `detectionPartEntityForStream` | `SingleRequest<CdpDetectionEntityDto> arg0` | `ListResponse<CdpDetectionErrorDto>` | 检测实体PartForStream |
| `detectionPartModelForStream` | `SingleRequest<CdpDetectionModelRequestDto> arg0` | `ListResponse<CdpDetectionErrorDto>` | 检测PartModelForStream |
| `detectionPartModelForIndicator` | `SingleRequest<CdpDetectionModelRequestDto> arg0` | `ListResponse<CdpDetectionErrorDto>` | 检测PartModelForIndicator |
| `detectionPartModelForReport` | `SingleRequest<CdpDetectionModelRequestDto> arg0` | `ListResponse<CdpDetectionErrorDto>` | 检测PartModelForReport |
| `detectionPartIndicatorForTable` | `SingleRequest<CdpDetectionIndicatorRequestDto> arg0` | `ListResponse<CdpDetectionErrorDto>` | 检测表PartIndicatorFor |
| `upgradeApps` | `SingleRequest<List<Map>> arg0` | `SingleResponse<Integer>` | 升级Apps |
| `cascadeHandleEntityForDataset` | `SingleRequest<List<CdpCascadeHandleEntityDto>> arg0` | `SingleResponse<Boolean>` | 处理实体ForDataset |

### `com.seeyon.cdp.common.metadata.api`

#### MetadataInst

`com.seeyon.cdp.common.metadata.api.MetadataInst` · 构件 `cdp-data-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getAppDefPageFromAppCenter` | `PageRequest arg0` | `PageResponse<AppDef>` | 分页获取应用DefFromCenter |
| `getAppDefListFromAppCenter` | `ListRequest arg0` | `ListResponse<AppDef>` | 列表获取应用DefFromCenter |
| `getUserApplicationsByConditions` | `ListRequest arg0` | `ListResponse<AppDef>` | 获取用户Applications按条件 |
| `getAppDefListFromMetadataCenter` | `AppIdentifier... arg0` | `List<AppDef>` | 列表获取应用扩展属性DefFromCenter |
| `getAppDefListFromMetaCenter` | `—` | `List<AppDef>` | 列表获取应用DefFromMetaCenter |
| `getEntityDefList` | `AppIdentifier arg0` | `List<EntityDef>` | 列表获取实体Def |
| `getAggEntityDef` | `EntityIdentifier arg0` | `AggEntityDef` | 获取实体AggDef |
| `getEntityDef` | `EntityIdentifier arg0` | `EntityDef` | 获取实体Def |
| `removeEntityDef` | `EntityIdentifier arg0` | `void` | 移除实体Def |
| `getPlatformEnumDef` | `PlatformEnumIdentifier arg0` | `PlatformEnumDef` | 获取枚举PlatformDef |
| `getJavaEnumDef` | `JavaEnumIdentifier arg0` | `JavaEnumDef` | 获取枚举JavaDef |
| `getReferDefList` | `ReferDefIdentifier arg0` | `List<ReferDef>` | 列表获取ReferDef |
| `getPageDef` | `AppIdentifier arg0` | `List<PageDef>` | 分页获取Def |

#### MetadataInstFactory

`com.seeyon.cdp.common.metadata.api.MetadataInstFactory` · 构件 `cdp-data-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getMetadataInst` | `MetadataBus arg0` | `MetadataInst` | 获取扩展属性Inst |

### `com.seeyon.cdp.common.metadata.api.identifier`

#### MetadataIdentifier

`com.seeyon.cdp.common.metadata.api.identifier.MetadataIdentifier` · 构件 `cdp-data-biz`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getUniqueKey` | `—` | `String` | 获取键Unique |

### `com.seeyon.cdp.dataset.api`

#### DatasetOpenApiAppService

`com.seeyon.cdp.dataset.api.DatasetOpenApiAppService` · 构件 `cdp-data-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getDatasetModel` | `SingleRequest<DatasetModelRequestDto> arg0` | `SingleResponse<DatasetModelDto>` | 获取DatasetModel |
| `getDatasetResult` | `SingleRequest<DatasetResultRequestDto> arg0` | `SingleResponse<ModelExecuteResult>` | 获取DatasetResult |

### `com.seeyon.cdp.etl.api`

#### CdpEtlRunAppService

`com.seeyon.cdp.etl.api.CdpEtlRunAppService` · 构件 `cdp-data-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `jobSuccess` | `SingleRequest<CdpEtlRunDto> arg0` | `SingleResponse<CdpEtlRunResultDto>` | ETL 任务成功回调（调度器通知） |

#### CdpEtlSourceAppService

`com.seeyon.cdp.etl.api.CdpEtlSourceAppService` · 构件 `cdp-data-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getSource` | `SingleRequest<CdpEtlSourceParamsDto> arg0` | `SingleResponse<CdpEtlSourceDto>` | 获取Source |
| `getDatasetPublishMetadata` | `SingleRequest<CdpEtlDatasetMetadataRequest> arg0` | `SingleResponse<CdpEtlDatasetMetadataDto>` | 获取扩展属性DatasetPublish |

### `com.seeyon.cdp.index.api`

#### IndexAppService

`com.seeyon.cdp.index.api.IndexAppService` · 构件 `cdp-data-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `search` | `PageDtoRequest<SearchConditionDto> arg0` | `PageResponse<SearchResultDto>` | 搜索条件 |
| `suggest` | `SingleRequest<SuggestConditionDto> arg0` | `ListResponse<SuggestResultDto>` | 索引联想/补全（搜索建议） |
| `hotSearch` | `SingleRequest<Integer> arg0` | `ListResponse<SearchHistoryDto>` | 搜索SearchHistory |
| `searchHistory` | `SingleRequest<SearchHistoryConditionDto> arg0` | `ListResponse<SearchHistoryDto>` | 搜索History |

#### IndexStoreAppService

`com.seeyon.cdp.index.api.IndexStoreAppService` · 构件 `cdp-data-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `save` | `SingleRequest<IndexStoreDto> arg0` | `SingleResponse<Boolean>` | 保存IndexStore |
| `updateIndexAuth` | `SingleRequest<IndexUpdateAuthDto> arg0` | `SingleResponse<Integer>` | 修改认证Index |
| `delete` | `SingleRequest<IndexDeleteDto> arg0` | `SingleResponse<Integer>` | 删除IndexDelete |
| `batchDelete` | `SingleRequest<IndexDeleteDto> arg0` | `SingleResponse<Boolean>` | 删除IndexDelete |
| `saveIndexBpmData` | `SingleRequest<IndexBpmDataDto> arg0` | `SingleResponse<Boolean>` | 保存数据IndexBpm |

### `com.seeyon.cdp.indicator.api`

#### IndicatorOpenApiAppService

`com.seeyon.cdp.indicator.api.IndicatorOpenApiAppService` · 构件 `cdp-data-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getIndicatorModel` | `SingleRequest<IndicatorModelRequestDto> arg0` | `SingleResponse<IndicatorModelDto>` | 获取IndicatorModel |
| `getIndicatorResult` | `SingleRequest<IndicatorResultRequestDto> arg0` | `SingleResponse<ModelExecuteResult>` | 获取IndicatorResult |

### `com.seeyon.cdp.stream.api`

#### StreamOpenApiAppService

`com.seeyon.cdp.stream.api.StreamOpenApiAppService` · 构件 `cdp-data-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getStreamModel` | `SingleRequest<StreamModelRequestDto> arg0` | `SingleResponse<StreamModelDto>` | 获取StreamModel |
| `getStreamResult` | `SingleRequest<StreamResultRequestDto> arg0` | `SingleResponse<ModelExecuteResult>` | 获取StreamResult |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 120 个领域服务，下表列**方法数最多的 40 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `DatasetService` | 85 | Dataset · 获取×19 / 修改×8 / 发布×6 |
| `ReportService` | 68 | Report · 获取×34 / 修改×9 / 查询×6 |
| `IndicatorService` | 60 | Indicator · 获取×30 / 修改×8 / 删除×5 |
| `BaseStreamService` | 57 | Stream · 获取×17 / 修改×10 / 新建×6 |
| `IndicatorTableService` | 49 | 表 · 获取×16 / 修改×9 / 新建×4 |
| `ModelService` | 44 | Model · 获取×26 / 修改×8 / 删除×3 |
| `ReportRuntimeService` | 36 | ReportRuntime · 构建×10 / 获取×7 / 解析×6 |
| `SchJobInstanceService` | 36 | 任务 · 获取×23 / 修改×5 / 新建×2 |
| `ReportCategoryService` | 35 | 分类 · 构建×25 / 获取×6 / 运行×2 |
| `BigScreenService` | 34 | BigScreen · 获取×9 / 修改×4 / 构建×4 |
| `SchJobService` | 31 | 任务 · 获取×14 / 修改×7 / 删除×4 |
| `StreamService` | 26 | Stream · 获取×9 / 发布×5 / 取消×3 |
| `IndexSearchForFJGSService` | 25 | IndexSearchForFJGS · 构建×13 / 查询×2 / 转换×2 |
| `StreamValidateService` | 24 | StreamValidate · 校验×20 / 判断×2 / 构建×1 |
| `IndexSearchService` | 24 | IndexSearch · 构建×13 / 查询×2 / 获取×2 |
| `PortletTileAdaptService` | 23 | PortletTileAdapt · 获取×12 / 构建×9 / 排序×1 |
| `LinkHandleService` | 22 | LinkHandle · 构建×9 / 对比×4 / 查找×2 |
| `SchemeService` | 20 | Scheme · 获取×8 / 删除×3 / 校验×2 |
| `DataSourceInnerDelegateService` | 20 | SourceInnerDelegate · 获取×9 / 查询×2 / 校验×1 |
| `ModelFieldService` | 18 | 字段 · 构建×6 / 获取×5 / 设置×3 |
| `SchTableMappingService` | 18 | 表映射 · 获取×6 / 新建×3 / 删除×3 |
| `ModelAdaptService` | 15 | ModelAdapt · 获取×9 / 构建×3 / 查找×3 |
| `PortletDashboardAdaptService` | 15 | PortletDashboardAdapt · 构建×8 / 获取×6 / 排序×1 |
| `ReportModelRelationService` | 15 | ReportModelRelation · 获取×6 / 新建×3 / 修改×2 |
| `DataSourceService` | 15 | Source · 获取×5 / 查询×2 / 新建×1 |
| `StreamNodeService` | 15 | StreamNode · 构建×5 / 获取×2 / 格式化×2 |
| `SchJobBizMappingService` | 15 | 任务映射 · 获取×9 / 新建×2 / 删除×2 |
| `ResourceAuthRegisterService` | 14 | 资源认证 · 注册×4 / 删除×4 / 构建×3 |
| `AbstractStorageBasedDataPreviewService` | 14 | 存储 · 获取×4 / 预览×2 / 转换×1 |
| `SchJobRelationService` | 14 | 任务 · 删除×4 / 获取×4 / 新建×3 |
| `ResourceDataAuthService` | 13 | 资源认证 · 获取×7 / 新建×2 / 删除×2 |
| `IndicatorTableValidateService` | 12 | 表 · 校验×7 / 检查×2 / 判断×2 |
| `TableDeriveRelationService` | 12 | 表 · 获取×4 / 新建×3 / 修改×2 |
| `AreaMappingService` | 12 | 映射 · 获取×3 / 删除×3 / 构建×3 |
| `ReportDownloadService` | 11 | ReportDownload · 获取×4 / 下载×3 / 构建×2 |
| `PrecacheSchemeService` | 11 | PrecacheScheme · 校验×5 / 删除×2 / 获取×2 |
| `PortletBannerAdaptService` | 11 | PortletBannerAdapt · 获取×6 / 构建×4 |
| `BigScreenAuthService` | 11 | 认证 · 判断×3 / 修改×2 / 查询×2 |
| `BigScreenDeviceRelationService` | 11 | BigScreenDeviceRelation · 构建×3 / 删除×2 / 获取×2 |
| `SchStreamJobService` | 11 | 任务 · 获取×5 / 新建×2 / 修改×1 |

## biz 层：事件与监听

事件 19 个 · 监听器 2 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| BigScreen | `BigScreenCreateEvent`, `BigScreenDeleteEvent`, `BigScreenUpdateEvent` |
| IndexOnSearch | `IndexOnSearchEvent` |
| Indicator | `IndicatorDeleteEvent`, `IndicatorUpdateEvent` |
| IndicatorCascade | `IndicatorCascadeUpdateEvent` |
| Model | `ModelCreateEvent`, `ModelDeleteEvent`, `ModelUpdateEvent` |
| ModelCascade | `ModelCascadeUpdateEvent` |
| Report | `ReportCreateEvent`, `ReportDeleteEvent`, `ReportUpdateEvent` |
| ReportCacheScheme | `ReportCacheSchemeEvent` |
| SchJobPreview | `SchJobPreviewEvent` |
| SchJobSuccess | `SchJobSuccessEvent` |
| Stream | `StreamDeleteEvent` |
| Table | `TableDeleteEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `ReportDeleteEventListener` | 2 |
| `IndexEventListener` | 1 |

## web 层：Controller

共 51 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 推送/被引用（Refer*） | `ReferenceBiController` | 5 |
| 核心实体 CRUD | `ReportController` | 30 |
| 核心实体 CRUD | `StreamController` | 26 |
| 核心实体 CRUD | `DatasetController` | 22 |
| 核心实体 CRUD | `UdcReportController` | 21 |
| 核心实体 CRUD | `CdpUpgradeController` | 15 |
| 核心实体 CRUD | `IndicatorController` | 13 |
| 核心实体 CRUD | `IndicatorTableController` | 13 |
| 核心实体 CRUD | `DataSourceController` | 12 |
| 核心实体 CRUD | `UdcStreamController` | 12 |
| 核心实体 CRUD | `SchJobController` | 12 |
| 核心实体 CRUD | `UdcIndicatorController` | 10 |
| 核心实体 CRUD | `BigScreenController` | 10 |
| 核心实体 CRUD | `ReportRuntimeController` | 10 |
| 核心实体 CRUD | `CdpEnvController` | 10 |
| 核心实体 CRUD | `ModelController` | 9 |
| 核心实体 CRUD | `UdcDatasetController` | 9 |
| 核心实体 CRUD | `SchJobInstanceController` | 9 |
| 核心实体 CRUD | `IndexController` | 8 |
| 核心实体 CRUD | `UdcIndicatorTableController` | 7 |
| 核心实体 CRUD | `BigScreenAuthController` | 7 |
| 核心实体 CRUD | `SchemeController` | 7 |
| 核心实体 CRUD | `GeoController` | 6 |
| 核心实体 CRUD | `UdcGeoController` | 6 |
| 核心实体 CRUD | `CdpReportTestController` | 6 |
| 核心实体 CRUD | `ReportPortletController` | 5 |
| 核心实体 CRUD | `ModelAuthController` | 4 |
| 核心实体 CRUD | `UdcModelAuthController` | 4 |
| 核心实体 CRUD | `FormSkipController` | 4 |
| 核心实体 CRUD | `ReportAuthController` | 4 |
| 核心实体 CRUD | `ReportCategoryController` | 4 |
| 核心实体 CRUD | `UdcReferenceBiController` | 4 |
| 核心实体 CRUD | `UdcReportPortletController` | 4 |
| 核心实体 CRUD | `UdcReportRuntimeController` | 4 |
| 核心实体 CRUD | `UdcModelController` | 3 |
| 核心实体 CRUD | `BigScreenOldController` | 3 |
| 核心实体 CRUD | `BigScreenTemplateController` | 3 |
| 核心实体 CRUD | `ReportApiController` | 3 |
| 核心实体 CRUD | `V5CapController` | 3 |
| 核心实体 CRUD | `EntityController` | 3 |
| 核心实体 CRUD | `UdcTestController` | 2 |
| 核心实体 CRUD | `UdcFormSkipController` | 2 |
| 核心实体 CRUD | `UdcReportAuthController` | 2 |
| 核心实体 CRUD | `CdpSSOController` | 2 |
| 核心实体 CRUD | `UdcEntityController` | 2 |
| 核心实体 CRUD | `CdpScheduleUpgradeController` | 2 |
| 核心实体 CRUD | `UdcReportCategoryController` | 1 |
| 核心实体 CRUD | `CdpCustomVariableController` | 1 |
| 核心实体 CRUD | `EtlJobController` | 1 |
| 核心实体 CRUD | `SystemVarController` | 1 |
| 核心实体 CRUD | `IndexForFJGSController` | 1 |

## 落表

⚠️ **UNVERIFIED** —— 字节码索引不含 SQL/表名，本文件不写推测的表名。

取证路径（三条，任选其一，务必留证据）：

1. **jar 内 mapper**：`organization-biz` 里 `*.xml` / `*Mapper.java`
2. **库结构**：连 test2 的 MySQL 查 `information_schema.columns` 里 `tb_org_%`
3. **运行态**：开 SQL 日志跑一次写操作，看真实表名

在拿到上述证据前，本文件对「落哪张表」保持空。

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 19 接口 / 90 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 120 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 19 事件 / 2 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 51 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径 | 未取证 | `UNVERIFIED` |
| 落表 | 未取证 | `UNVERIFIED` |
