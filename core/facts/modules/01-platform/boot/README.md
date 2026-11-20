# 平台内核（boot）

## 一句话

`com.seeyon.boot` 域的**可调用接口面**：79 个构件、4,191 个类、47 个 facade 接口 / 141 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `boot-core` | 其他 | 506 |
| `udc-starter-runtime` | 其他 | 306 |
| `boot-starter-datamigration` | 其他 | 247 |
| `boot-starter-formula` | 其他 | 202 |
| `boot-starter-mybatis` | 其他 | 138 |
| `udc-starter-lowcode` | 其他 | 121 |
| `udc-starter-dataflow` | 其他 | 116 |
| `boot-starter-communication` | 其他 | 108 |
| `boot-starter-extmetadata` | 其他 | 103 |
| `boot-starter-documentnumber` | 其他 | 101 |
| `boot-starter-cip` | 其他 | 98 |
| `boot-starter-file` | 其他 | 89 |
| `boot-starter-datainit` | 其他 | 88 |
| `boot-starter-serialnumber` | 其他 | 85 |
| `udc-starter-customplan` | 其他 | 78 |
| `boot-starter-condition` | 其他 | 77 |
| `boot-starter-excel` | 其他 | 72 |
| `boot-starter-graphql` | 其他 | 71 |
| `boot-starter-mq` | 其他 | 68 |
| `boot-starter-opinion` | 其他 | 64 |
| `boot-starter-web` | web | 60 |
| `boot-starter-qrcode` | 其他 | 59 |
| `boot-starter-basicdata` | 其他 | 57 |
| `boot-starter-sandbox` | 其他 | 53 |
| `boot-starter-sharding` | 其他 | 52 |
| `udc-starter-autocode` | 其他 | 52 |
| `boot-starter-enums` | 其他 | 51 |
| `boot-starter-cache` | 其他 | 50 |
| `boot-starter-ganttchart` | 其他 | 50 |
| `boot-starter-schedule` | 其他 | 50 |
| `boot-starter-dubbo` | 其他 | 48 |
| `boot-starter-dynamicsql` | 其他 | 42 |
| `boot-starter-appservice` | 其他 | 41 |
| `boot-formula-engine` | 其他 | 40 |
| `boot-starter-formconvert` | 其他 | 40 |
| `boot-starter-module` | 其他 | 40 |
| `boot-starter-prometheus` | 其他 | 32 |
| `boot-starter-datasource` | 其他 | 29 |
| `boot-starter-i18n` | 其他 | 28 |
| `boot-starter-queue` | 其他 | 28 |
| `boot-starter-elasticsearch` | 其他 | 25 |
| `boot-starter-k8s` | 其他 | 25 |
| `boot-starter-swagger` | 其他 | 25 |
| `boot-starter-index` | 其他 | 24 |
| `boot-starter-nacos` | 其他 | 24 |
| `boot-starter-captcha` | 其他 | 23 |
| `boot-starter-datatype` | 其他 | 23 |
| `boot-starter-eventbus` | 其他 | 23 |
| `boot-starter-labelprint` | 其他 | 23 |
| `boot-starter-parameter` | 其他 | 22 |
| `boot-starter-proxy` | 其他 | 18 |
| `boot-starter-license` | 其他 | 17 |
| `boot-starter-security` | 其他 | 17 |
| `boot-starter-artifact` | 其他 | 16 |
| `boot-starter-attachment` | 其他 | 15 |
| `boot-starter-dynamicloader` | 其他 | 15 |
| `boot-starter-k8s-adapter` | 其他 | 15 |
| `boot-starter-monitor` | 其他 | 15 |
| `boot-starter-transaction` | 其他 | 15 |
| `boot-starter-dynamiccode` | 其他 | 14 |
| `boot-starter-threadpool` | 其他 | 14 |
| `boot-starter-upgrade` | 其他 | 14 |
| `boot-starter-environment` | 其他 | 13 |
| `boot-sentinel-app` | 其他 | 12 |
| `boot-starter-spi` | 其他 | 12 |
| `boot-starter-lock` | 其他 | 9 |
| `boot-starter-mgn-export` | 其他 | 9 |
| `boot-starter-sensitive` | 其他 | 9 |
| `boot-starter-test` | 其他 | 9 |
| `boot-license-generator` | 其他 | 8 |
| `boot-starter-filterchain` | 其他 | 8 |
| `boot-starter-frontend-log` | 其他 | 8 |
| `boot-starter-websocket` | 其他 | 8 |
| `boot-starter-tomcat` | 其他 | 7 |
| `boot-starter-shortlink` | 其他 | 5 |
| `boot-starter-systemvariable` | 其他 | 4 |
| `boot-sentinel-gateway` | 其他 | 3 |
| `boot-spi` | 其他 | 3 |
| `boot-starter-scanner` | 其他 | 2 |
| **合计** | | **4,191** |

## 二、分层规律（写代码前必读）

`com.seeyon.boot` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

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

## facade 层：47 个接口 / 141 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.boot.starter.appservice.annotation` | 1 | 0 |
| `com.seeyon.boot.starter.appservice.domain.dao` | 1 | 0 |
| `com.seeyon.boot.starter.appservice.ex` | 1 | 1 |
| `com.seeyon.boot.starter.appservice.ex.parser` | 1 | 1 |
| `com.seeyon.boot.starter.attachment.api` | 1 | 2 |
| `com.seeyon.boot.starter.basicdata.api` | 1 | 1 |
| `com.seeyon.boot.starter.cip.api` | 1 | 1 |
| `com.seeyon.boot.starter.configmigration.api` | 7 | 27 |
| `com.seeyon.boot.starter.customplan.api` | 4 | 17 |
| `com.seeyon.boot.starter.dataflow.api` | 4 | 11 |
| `com.seeyon.boot.starter.datainit.appservice` | 1 | 5 |
| `com.seeyon.boot.starter.deduction.api` | 2 | 7 |
| `com.seeyon.boot.starter.dubbo.api` | 2 | 5 |
| `com.seeyon.boot.starter.excel.api` | 1 | 5 |
| `com.seeyon.boot.starter.extmetadata.api` | 1 | 2 |
| `com.seeyon.boot.starter.file.appservice.proxy` | 1 | 1 |
| `com.seeyon.boot.starter.i18n.api` | 2 | 5 |
| `com.seeyon.boot.starter.lowcode.api` | 2 | 5 |
| `com.seeyon.boot.starter.proxy.api` | 2 | 9 |
| `com.seeyon.boot.starter.qrcode.detection.api` | 1 | 3 |
| `com.seeyon.boot.starter.schedule.api` | 1 | 1 |
| `com.seeyon.boot.starter.sharding.appservice` | 1 | 6 |
| `com.seeyon.boot.starter.udcrt.api` | 6 | 24 |
| `com.seeyon.boot.starter.upgrade.api` | 1 | 1 |
| `com.seeyon.boot.starter.websocket.api` | 1 | 1 |
| **合计** | **47** | **141** |

### `com.seeyon.boot.starter.appservice.annotation`

#### Idempotent

`com.seeyon.boot.starter.appservice.annotation.Idempotent` · 构件 `boot-starter-appservice` · extends `Annotation`

（无方法）

### `com.seeyon.boot.starter.appservice.domain.dao`

#### IdempotentInfoDao

`com.seeyon.boot.starter.appservice.domain.dao.IdempotentInfoDao` · 构件 `boot-starter-appservice` · extends `BaseMybatisDao<CtpIdempotent>`

（无方法）

### `com.seeyon.boot.starter.appservice.ex`

#### ExceptionHandler

`com.seeyon.boot.starter.appservice.ex.ExceptionHandler` · 构件 `boot-starter-appservice` · extends `Throwable>`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `handle` | `ExceptionContext<?> arg0` | `void` | 处理（ExceptionContext） |

### `com.seeyon.boot.starter.appservice.ex.parser`

#### DBExceptionParser

`com.seeyon.boot.starter.appservice.ex.parser.DBExceptionParser` · 构件 `boot-starter-appservice`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `parser` | `String arg0` | `BusinessException` | 解析器实现（SPI，把入参解析成内部结构） |

### `com.seeyon.boot.starter.attachment.api`

#### AttachmentExtendApi

`com.seeyon.boot.starter.attachment.api.AttachmentExtendApi` · 构件 `boot-starter-attachment`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getAttachmentList` | `AttachmentQueryDto arg0` | `List<AttachmentDto>` | 列表获取Attachment |
| `getAttachmentList` | `SingleRequest<AttachmentQueryDto> arg0` | `ListResponse<AttachmentDto>` | 列表获取Attachment |

### `com.seeyon.boot.starter.basicdata.api`

#### BasicDataRtOpenApiAppService

`com.seeyon.boot.starter.basicdata.api.BasicDataRtOpenApiAppService` · 构件 `boot-starter-basicdata`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectPageByCondition` | `PageRequest arg0` | `PageResponse<Object>` | 分页查询按条件（PageRequest） |

### `com.seeyon.boot.starter.cip.api`

#### WeakTypeEscapeService

`com.seeyon.boot.starter.cip.api.WeakTypeEscapeService` · 构件 `boot-starter-cip`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `findWeakTypeEscapeDto` | `Map arg0` | `WeakTypeEscapeDto` | 查找类型WeakEscapeDto |

### `com.seeyon.boot.starter.configmigration.api`

#### CodeReplacer

`com.seeyon.boot.starter.configmigration.api.CodeReplacer` · 构件 `boot-starter-datamigration`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getRelationType` | `—` | `RelationType` | 获取类型Relation |
| `processRelationCodeById` | `List<FieldRelationData> arg0` | `void` | 处理编码Relation按 id |
| `processRelationIdByCode` | `List<FieldRelationData> arg0` | `void` | 处理Relation按编码 |

#### DataBackupHandler

`com.seeyon.boot.starter.configmigration.api.DataBackupHandler` · 构件 `boot-starter-datamigration`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `backupData` | `Long arg0` | `<T extends BaseEntity> void` | 备份数据 |
| `rollBackData` | `List<ExecutionContext> arg0` | `<T extends BaseEntity> void` | 数据备份回滚：把备份数据写回 |

#### DataComparator

`com.seeyon.boot.starter.configmigration.api.DataComparator` · 构件 `boot-starter-datamigration` · extends `Ordered`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getOrder` | `—` | `int` | 获取Order |
| `supports` | `Class<?> arg0` | `boolean` | 判断是否支持该输入（SPI 能力探测） |
| `compare` | `ExecutionContext arg0` | `void` | 对比（ExecutionContext） |

#### DataConsistencyValidator

`com.seeyon.boot.starter.configmigration.api.DataConsistencyValidator` · 构件 `boot-starter-datamigration`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `supports` | `—` | `List<Class>` | 判断是否支持该输入（SPI 能力探测） |
| `doValidate` | `DataConsistencyContext arg0` | `List<DataValidationResult>` | SPI 扩展点：Validate（框架回调） |

#### DependencyValidator

`com.seeyon.boot.starter.configmigration.api.DependencyValidator` · 构件 `boot-starter-datamigration`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `supports` | `Class<?> arg0` | `boolean` | 判断是否支持该输入（SPI 能力探测） |
| `getSupportedType` | `—` | `RelationType` | 获取类型Supported |
| `getRelationMetaInfo` | `ExecutionContext arg0` | `List<RelationMetaInfo>` | 获取RelationMeta |
| `doValidate` | `ExecutionContext arg0` | `void` | SPI 扩展点：Validate（框架回调） |

#### EntityDataHandler

`com.seeyon.boot.starter.configmigration.api.EntityDataHandler` · 构件 `boot-starter-datamigration` · extends `DataUpdateStrategy, Ordered`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getOrder` | `—` | `int` | 获取Order |
| `supports` | `Class<?> arg0` | `boolean` | 判断是否支持该输入（SPI 能力探测） |
| `getRelationMetaInfo` | `ExecutionContext arg0` | `List<RelationMetaInfo>` | 获取RelationMeta |
| `processQueryData` | `ExecutionContext arg0` | `<T extends BaseEntity> void` | 处理数据Query |
| `processCoverAggData` | `DataBackupHandler arg0` | `void` | 处理数据CoverAgg |
| `processBeforeReplaceData` | `ExecutionContext arg0` | `<T extends BaseEntity> void` | 处理数据BeforeReplace |
| `processReplaceData` | `ExecutionContext arg0` | `<T extends BaseEntity> void` | 处理数据Replace |
| `processAfterReplaceData` | `ExecutionContext arg0` | `<T extends BaseEntity> void` | 处理数据AfterReplace |
| `processCallBack` | `CallBackContext arg0` | `<T extends BaseEntity> void` | 处理CallBack |

#### EntityDslHandler

`com.seeyon.boot.starter.configmigration.api.EntityDslHandler` · 构件 `boot-starter-datamigration`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `supports` | `Class<?> arg0` | `boolean` | 判断是否支持该输入（SPI 能力探测） |
| `getPageSize` | `—` | `int` | 分页获取Size |
| `fetchData` | `FetchCondition arg0` | `PageData<? extends BaseEntity>` | 拉取数据 |
| `handleDsl` | `EntityDslDto arg0` | `void` | 处理Dsl |

### `com.seeyon.boot.starter.customplan.api`

#### CustomPlanAppService

`com.seeyon.boot.starter.customplan.api.CustomPlanAppService` · 构件 `udc-starter-customplan`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectBySourceIds` | `SingleRequest<List<String>> arg0` | `ListResponse<CustomPlanDto>` | 查询CustomPlan按SourceIds |
| `selectByComplexCondition` | `SingleRequest<CustomPlanSearchDto> arg0` | `ListResponse<CustomPlanDto>` | 查询CustomPlanSearch按条件 |

#### PersonalPlanAppService

`com.seeyon.boot.starter.customplan.api.PersonalPlanAppService` · 构件 `udc-starter-customplan`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectByCondition` | `SingleRequest<PersonalQueryDto> arg0` | `SingleResponse<PersonalPlanDto>` | 查询PersonalQuery按条件 |
| `selectListByCondition` | `SingleRequest<PersonalQueryDto> arg0` | `ListResponse<PersonalPlanDto>` | 列表查询PersonalQuery按条件 |
| `createRedirectBatch` | `SingleRequest<List<PersonalPlanDto>> arg0` | `SingleResponse<List<Long>>` | 批量新建Redirect |
| `selectPageByCondition` | `PageRequest arg0` | `PageResponse<PersonalPlanDto>` | 分页查询PersonalPlan按条件 |
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |

#### ScalabilityFieldAppService

`com.seeyon.boot.starter.customplan.api.ScalabilityFieldAppService` · 构件 `udc-starter-customplan`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectMetadataExtEntityTree` | `SingleRequest<String> arg0` | `ListResponse<EntityRuntimeTreeDto>` | 树查询扩展属性扩展实体 |
| `listExtFileds` | `SingleRequest<ScalabilityFieldQueryDto> arg0` | `ListResponse<ScalabilityFieldDto>` | 列出扩展Fileds |
| `selectAvailableDatatype` | `SingleRequest<ScalabilityFieldQueryDto> arg0` | `ListResponse<String>` | 查询AvailableDatatype |
| `selectAttribute` | `SingleRequest<ScalabilityFieldQueryDto> arg0` | `SingleResponse<ScalabilityFieldDto>` | 查询字段 |
| `updateBatch` | `SingleRequest<List<ScalabilityFieldDto>> arg0` | `SingleResponse<Integer>` | 批量修改（SingleRequest） |
| `compensateScalabilityFieldMetadata` | `SingleRequest<Void> arg0` | `SingleResponse<String>` | 补偿扩展字段元数据（扩容/迁移后补齐） |
| `transportIn` | `SingleRequest<List<ScalabilityFieldDto>> arg0` | `SingleResponse<Integer>` | 扩展字段元数据导入 |

#### UdcPageProcessEventService

`com.seeyon.boot.starter.customplan.api.UdcPageProcessEventService` · 构件 `udc-starter-customplan`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectProcessEventListByCondition` | `SingleRequest<PageProcessEventSearchDto> arg0` | `ListResponse<PageProcessEventDto>` | 列表查询流程Event按条件 |
| `selectProcessEventList` | `SingleRequest<CBpmNodePermissionRequestDto> arg0` | `ListResponse<PageProcessEventDto>` | 列表查询流程Event |
| `clearCacheByAppName` | `SingleRequest<String> arg0` | `void` | 按应用名清页面处理缓存 |

### `com.seeyon.boot.starter.dataflow.api`

#### DataFlowForBpmAppService

`com.seeyon.boot.starter.dataflow.api.DataFlowForBpmAppService` · 构件 `udc-starter-dataflow`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `asyncTriggerFlowForBpm` | `SingleRequest<BpmTriggerFlowUdcFinishDto> arg0` | `SingleResponse<Void>` | 触发FlowForBpm |
| `fillErrorFlowData` | `SingleRequest<FillFlowReqDto> arg0` | `SingleResponse<Boolean>` | 填充数据ErrorFlow |

#### DataFlowMapAppService

`com.seeyon.boot.starter.dataflow.api.DataFlowMapAppService` · 构件 `udc-starter-dataflow`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectByCondition` | `SingleRequest<DataFlowRtMapQueryDto> arg0` | `ListResponse<DataFlowRtMapDto>` | 查询FlowRtMapQuery按条件 |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<DataFlowRtMapDto>` | 查询FlowRtMap按 id |

#### DataFlowMappingAppService

`com.seeyon.boot.starter.dataflow.api.DataFlowMappingAppService` · 构件 `udc-starter-dataflow`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectOriginalMappingList` | `SingleRequest<OriginalDataFlowMappingListQueryDto> arg0` | `ListResponse<DataFlowRtMappingDto>` | 列表查询映射Original |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<DataFlowRtMappingDto>` | 查询映射按 id |
| `selectMappingInitData` | `SingleRequest<DataFlowMappingInitQueryDto> arg0` | `SingleResponse<DataFlowRtEditInitialDataDto>` | 查询映射数据Init |
| `update` | `SingleRequest<DataFlowRtMappingSaveDto> arg0` | `SingleResponse<DataFlowRtMappingDto>` | 修改映射 |
| `updateMappingState` | `SingleRequest<DataFlowMappingStateUpdateDto> arg0` | `SingleResponse<OperationResultDto>` | 修改映射State |
| `selectDetailByCondition` | `SingleRequest<DataFlowOriginalMappingQueryDto> arg0` | `SingleResponse<DataFlowRtMappingDto>` | 查询Detail按条件 |

#### UdcRuleAppService

`com.seeyon.boot.starter.dataflow.api.UdcRuleAppService` · 构件 `udc-starter-dataflow`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectRuleByEntity` | `SingleRequest<QueryRuleByEntityDto> arg0` | `SingleResponse<QueryRuleResultDto>` | 查询规则按实体 |

### `com.seeyon.boot.starter.datainit.appservice`

#### InitMonitorAppService

`com.seeyon.boot.starter.datainit.appservice.InitMonitorAppService` · 构件 `boot-starter-datainit`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectAppStarterInitVersions` | `PageRequest arg0` | `PageResponse<AppStarterInitVersionDto>` | 查询应用StarterInitVersions |
| `executeOnetime` | `Long arg0` | `SingleResponse<String>` | 执行Onetime |
| `executeWithRecordType` | `Integer arg0` | `SingleResponse<String>` | 执行类型WithRecord |
| `ignoreError` | `Long arg0` | `SingleResponse<String>` | 初始化监控：忽略指定错误（容错继续） |
| `selectAppInitSingleDetails` | `Map<String, Object> arg0` | `ListResponse<AppInitSingleDetailDto>` | 查询应用InitSingleDetails |

### `com.seeyon.boot.starter.deduction.api`

#### DeductionRtMapAppService

`com.seeyon.boot.starter.deduction.api.DeductionRtMapAppService` · 构件 `udc-starter-dataflow`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectSimpleDeductionMap` | `SingleRequest<Long> arg0` | `ListResponse<DeductionRtMapSimpleDto>` | 查询简单DeductionMap |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<DeductionRtMapDto>` | 查询DeductionRtMap按 id |

#### DeductionRtRuleAppService

`com.seeyon.boot.starter.deduction.api.DeductionRtRuleAppService` · 构件 `udc-starter-dataflow`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectRtRuleVersion` | `SingleRequest<DeductionRtRuleVersionIdQueryDto> arg0` | `ListResponse<DeductionRtRuleCategoryDto>` | 查询规则版本Rt |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<DeductionRtRuleDto>` | 查询规则按 id |
| `initData` | `SingleRequest<DeductionRtRuleVersionQueryDto> arg0` | `SingleResponse<DeductionRtInitDataDto>` | 初始化数据 |
| `saveRuleNewVersion` | `SingleRequest<DeductionRtRuleDto> arg0` | `SingleResponse<DeductionSaveRuleNewVersionRespDto>` | 保存规则版本New |
| `enableRule` | `SingleRequest<Long> arg0` | `SingleResponse<Boolean>` | 启用规则 |

### `com.seeyon.boot.starter.dubbo.api`

#### AppServiceProxy

`com.seeyon.boot.starter.dubbo.api.AppServiceProxy` · 构件 `boot-starter-dubbo`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `invokeAppService` | `SingleRequest<AppServiceInvokeDto> arg0` | `SingleResponse<Object>` | 调用应用Service |
| `invokeAppServiceForList` | `SingleRequest<AppServiceInvokeDto> arg0` | `ListResponse<Object>` | 列表调用应用ServiceFor |
| `invokeAppServiceForPage` | `SingleRequest<AppServiceInvokeDto> arg0` | `PageResponse<Object>` | 分页调用应用ServiceFor |
| `reliableInvokeAppService` | `SingleRequest<AppServiceReliableInvokeDto<T>> arg0` | `<T> SingleResponse` | 调用应用Service |

#### AppServiceProxyCallback

`com.seeyon.boot.starter.dubbo.api.AppServiceProxyCallback` · 构件 `boot-starter-dubbo`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `callback` | `SingleRequest<CommandCallbackDto> arg0` | `SingleResponse<String>` | 回调入口（SPI，外部系统回调时进入） |

### `com.seeyon.boot.starter.excel.api`

#### DesignMetadataQueryApi

`com.seeyon.boot.starter.excel.api.DesignMetadataQueryApi` · 构件 `boot-starter-excel`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectAggEntityMetadataByFullName` | `SingleRequest<DesignMetadataRequestDto> arg0` | `SingleResponse<AggEntityMetadataDto>` | 查询实体扩展属性Agg按名称 |
| `selectEntityMetadataByFullName` | `SingleRequest<DesignMetadataRequestDto> arg0` | `SingleResponse<EntityMetadataDto>` | 查询实体扩展属性按名称 |
| `selectDtoMetadataByEntityFullName` | `SingleRequest<DesignMetadataRequestDto> arg0` | `SingleResponse<DtoMetadataDto>` | 查询扩展属性Dto按实体名称 |
| `selectCtpEnumMetadataByFullNames` | `SingleRequest<SearchByFullNamesDto> arg0` | `ListResponse<CtpEnumMetadataDto>` | 查询枚举扩展属性Ctp按名称 |
| `selectEnumMetadataByFullNames` | `SingleRequest<SearchByFullNamesDto> arg0` | `ListResponse<EnumMetadataDto>` | 查询枚举扩展属性按名称 |

### `com.seeyon.boot.starter.extmetadata.api`

#### HostAppFunctionInterface

`com.seeyon.boot.starter.extmetadata.api.HostAppFunctionInterface` · 构件 `boot-starter-extmetadata`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectDependentApplicationByHostAppName` | `SingleRequest<UdcMetaDataSearchDto> arg0` | `ListResponse<UdcApplicationMetaDataDto>` | 查询应用Dependent按应用名称 |
| `getHostAppName` | `—` | `SingleResponse<UdcApplicationMetaDataDto>` | 获取应用名称Host |

### `com.seeyon.boot.starter.file.appservice.proxy`

#### FileInfoProxy

`com.seeyon.boot.starter.file.appservice.proxy.FileInfoProxy` · 构件 `boot-starter-file`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<FileDto>` | 查询文件按 ids |

### `com.seeyon.boot.starter.i18n.api`

#### I18nLocaleAppService

`com.seeyon.boot.starter.i18n.api.I18nLocaleAppService` · 构件 `boot-starter-i18n`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getEnableLocalesMap` | `SingleRequest<Long> arg0` | `SingleResponse<Map<String, String>>` | 获取EnableLocalesMap |
| `getTenantDefaultLocale` | `—` | `SingleResponse<String>` | 获取DefaultLocale |
| `getSystemDataI18nLocaleList` | `—` | `SingleResponse<List<Map<String, String>>>` | 列表获取数据SystemI18nLocale |
| `getTenantDataI18nLocaleList` | `—` | `SingleResponse<List<Map<String, String>>>` | 列表获取数据I18nLocale |

#### I18nResourceAppService

`com.seeyon.boot.starter.i18n.api.I18nResourceAppService` · 构件 `boot-starter-i18n`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getTenantResourceDtoMap` | `SingleRequest<TenantResourceRequestDto> arg0` | `SingleResponse<Map<String, I18nResourceDto>>` | 获取资源DtoMap |

### `com.seeyon.boot.starter.lowcode.api`

#### AttributeSnapshotAppService

`com.seeyon.boot.starter.lowcode.api.AttributeSnapshotAppService` · 构件 `udc-starter-lowcode`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectByDataId` | `Long arg0` | `List<AttributeSnapshotDto>` | 查询按数据（Long） |
| `selectByDataIds` | `List<Long> arg0` | `List<AttributeSnapshotDto>` | 查询按数据（List） |
| `selectByMasterDataId` | `Long arg0` | `List<AttributeSnapshotDto>` | 查询按数据（Long） |
| `selectByMasterDataIds` | `List<Long> arg0` | `List<AttributeSnapshotDto>` | 查询按数据（List） |

#### DataTransferAppService

`com.seeyon.boot.starter.lowcode.api.DataTransferAppService` · 构件 `udc-starter-lowcode`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `dataTransfer` | `SingleRequest<DataTransferRequest> arg0` | `SingleResponse<DataTransferResponse>` | 转移Transfer |

### `com.seeyon.boot.starter.proxy.api`

#### CustomerProxyAppService

`com.seeyon.boot.starter.proxy.api.CustomerProxyAppService` · 构件 `boot-starter-proxy`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `invokeAppService` | `SingleRequest<AppServiceInvokeDto> arg0` | `SingleResponse<Object>` | 调用应用Service |
| `invokeAppServiceForList` | `SingleRequest<AppServiceInvokeDto> arg0` | `ListResponse<Object>` | 列表调用应用ServiceFor |
| `invokeAppServiceForPage` | `SingleRequest<AppServiceInvokeDto> arg0` | `PageResponse<Object>` | 分页调用应用ServiceFor |
| `reliableInvokeAppService` | `SingleRequest<AppServiceReliableInvokeDto<T>> arg0` | `<T> SingleResponse` | 调用应用Service |
| `schedulePendingServiceInvoke` | `—` | `void` | 调度待执行的代理调用（补偿队列） |
| `scheduleCallbackProcessResult` | `—` | `void` | 处理Result |
| `scheduleRecoveryMisProcess` | `—` | `void` | 调度恢复中断的代理流程 |

#### ParamEscapeService

`com.seeyon.boot.starter.proxy.api.ParamEscapeService` · 构件 `boot-starter-proxy`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `paramEscape` | `String arg0` | `String` | 参数转义（防注入，拼 SQL/表达式前调用） |
| `saveApiLog` | `AppServiceAsyncInvokeDto arg0` | `void` | 保存API日志 |

### `com.seeyon.boot.starter.qrcode.detection.api`

#### CtpQrCodeRuleUdcAppService

`com.seeyon.boot.starter.qrcode.detection.api.CtpQrCodeRuleUdcAppService` · 构件 `boot-starter-qrcode`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getRuleListByAppIdAndFullNames` | `SingleRequest<PartDetectionRequestDto> arg0` | `ListResponse<CtpQrCodeRule>` | 列表获取规则按应用名称 |
| `getRuleListByAppIdAndFieldCodes` | `SingleRequest<PartDetectionRequestDto> arg0` | `ListResponse<CtpQrCodeRule>` | 列表获取规则按应用字段编码 |
| `getRuleListByAppId` | `SingleRequest<Long> arg0` | `ListResponse<CtpQrCodeRule>` | 列表获取规则按应用 |

### `com.seeyon.boot.starter.schedule.api`

#### SeeyonJob

`com.seeyon.boot.starter.schedule.api.SeeyonJob` · 构件 `boot-starter-schedule`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `exec` | `—` | `SingleResponse<?>` | 定时任务执行入口（实现类重写） |

### `com.seeyon.boot.starter.sharding.appservice`

#### ShardingAppServiceInterface

`com.seeyon.boot.starter.sharding.appservice.ShardingAppServiceInterface` · 构件 `boot-starter-sharding`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createTenantSharding` | `SingleRequest<CtpTenantShardingDto> arg0` | `SingleResponse<Long>` | 新建Sharding |
| `batchCreateTenantSharding` | `SingleRequest<List<CtpTenantShardingDto>> arg0` | `SingleResponse<Integer>` | 新建Sharding |
| `updateTenantSharding` | `SingleRequest<CtpTenantShardingDto> arg0` | `SingleResponse<Integer>` | 修改Sharding |
| `deleteTenantShardingByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除Sharding按 ids |
| `deleteTenantShardingById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除Sharding按 id |
| `selectTenantShardingByTenantId` | `SingleRequest<Long> arg0` | `ListResponse<CtpTenantShardingDto>` | 查询Sharding按租户 |

### `com.seeyon.boot.starter.udcrt.api`

#### AppDraftAppService

`com.seeyon.boot.starter.udcrt.api.AppDraftAppService` · 构件 `udc-starter-runtime`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createOrUpdate` | `SingleRequest<AppDraftDto> arg0` | `SingleResponse<Integer>` | 新建OrUpdate |
| `exist` | `SingleRequest<String> arg0` | `SingleResponse<AppDraftExistDto>` | 判断草稿是否存在 |
| `select` | `SingleRequest<String> arg0` | `SingleResponse<AppDraftDto>` | 查询应用草稿 |
| `delete` | `SingleRequest<String> arg0` | `SingleResponse<Integer>` | 删除（SingleRequest） |
| `deleteAll` | `SingleRequest<String> arg0` | `SingleResponse<Integer>` | 全部删除（SingleRequest） |

#### DeployNoticeService

`com.seeyon.boot.starter.udcrt.api.DeployNoticeService` · 构件 `udc-starter-runtime`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `deployNotice` | `SingleRequest<ApplicationExportDto> arg0` | `SingleResponse<Boolean>` | 部署通知 |

#### FormAppService

`com.seeyon.boot.starter.udcrt.api.FormAppService` · 构件 `udc-starter-runtime`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `loadForm` | `SingleRequest<FormLoadParamDto> arg0` | `SingleResponse<Void>` | 加载表单 |
| `getHostAppDepends` | `SingleRequest<String> arg0` | `ListResponse<BuildInfo>` | 获取应用HostDepends |

#### GraphqlProxyAppService

`com.seeyon.boot.starter.udcrt.api.GraphqlProxyAppService` · 构件 `udc-starter-runtime`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `doGraphQL` | `SingleRequest<GraphqlProxyRequestDto> arg0` | `SingleResponse<String>` | SPI 扩展点：GraphQL（框架回调） |
| `doRest` | `SingleRequest<RestRequestProxyDto> arg0` | `SingleResponse<String>` | SPI 扩展点：REST（框架回调） |

#### UdcBpmProcessService

`com.seeyon.boot.starter.udcrt.api.UdcBpmProcessService` · 构件 `udc-starter-runtime`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `validUpdateFilterData` | `SingleRequest<DataValidUpdateFilterDto> arg0` | `SingleResponse<BpmParameterDataDto>` | 修改数据Filter |
| `validCreateFilterData` | `SingleRequest<DataValidCreateFilterDto> arg0` | `SingleResponse<BpmParameterDataDto>` | 新建数据Filter |
| `processBpmApproval` | `SingleRequest<BpmApprovalResultData> arg0` | `SingleResponse<Boolean>` | 处理审批Bpm |
| `processBpmStop` | `SingleRequest<BpmStopEvent> arg0` | `SingleResponse<Boolean>` | 处理BpmStop |
| `processBpmCancel` | `SingleRequest<BpmCancelEvent> arg0` | `SingleResponse<Boolean>` | 处理BpmCancel |
| `processBpmTakeBack` | `SingleRequest<BpmApprovalResultData> arg0` | `SingleResponse<Boolean>` | 处理BpmTakeBack |
| `validFilterData` | `SingleRequest<DataValidUpdateFilterDto> arg0` | `SingleResponse<BpmParameterDataDto>` | 校验流程过滤数据合法性 |
| `updateData` | `SingleRequest<DataValidUpdateFilterDto> arg0` | `SingleResponse<Integer>` | 修改数据 |

#### UdcSerialConfigAppService

`com.seeyon.boot.starter.udcrt.api.UdcSerialConfigAppService` · 构件 `udc-starter-runtime`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `update` | `SingleRequest<UdcSerialConfigDto> arg0` | `SingleResponse<Integer>` | 修改配置 |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<UdcSerialConfigDto>` | 列表查询配置按条件 |
| `selectEntityList` | `SingleRequest<String> arg0` | `SingleResponse<EntityGroupAndItemDto>` | 列表查询实体 |
| `selectEntityBySerialId` | `ListRequest arg0` | `ListResponse<UdcEntityMetaDataDto>` | 查询实体按SerialId |
| `refreshHistoricalData` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 刷新数据Historical |
| `cacheEvict` | `SingleRequest<String> arg0` | `SingleResponse<Boolean>` | 清除流水号配置缓存 |

### `com.seeyon.boot.starter.upgrade.api`

#### CtpUpgrade

`com.seeyon.boot.starter.upgrade.api.CtpUpgrade` · 构件 `boot-starter-web`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `upgrade` | `—` | `UpgradeResult` | 升级 |

### `com.seeyon.boot.starter.websocket.api`

#### ReceiveProcessService

`com.seeyon.boot.starter.websocket.api.ReceiveProcessService` · 构件 `boot-starter-websocket`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `receiveMessage` | `TextMessage arg0` | `void` | 接收消息 |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 183 个领域服务，下表列**方法数最多的 40 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `ExcelConvertService` | 87 | ExcelConvert · 获取×23 / 检查×9 / 初始化×7 |
| `CtpEnumItemService` | 71 | 枚举 · 查询×33 / 获取×8 / 删除×7 |
| `BizMgnStorageService` | 59 | 存储 · 上传×7 / 获取×3 / 驳回×2 |
| `SandboxService` | 46 | Sandbox · 检查×8 / 查询×6 / 新建×4 |
| `FilterPlanService` | 46 | FilterPlan · 查询×12 / 删除×11 / 检查×5 |
| `CtpParameterService` | 40 | 参数 · 获取×18 / 查询×7 / 删除×3 |
| `EdocMarkRecordService` | 39 | EdocMarkRecord · 获取×15 / 删除×7 / 查询×7 |
| `SerialSchemeService` | 38 | SerialScheme · 查询×12 / 获取×4 / 修改×3 |
| `BasicDataEntityService` | 36 | 实体 · 查询×13 / 修改×5 / 获取×4 |
| `CtpEnumService` | 33 | 枚举 · 查询×15 / 删除×6 / 修改×4 |
| `UdcEntityMetaDataService` | 32 | 实体 · 查询×19 / 获取×4 / 设置×3 |
| `DataFlowMappingService` | 32 | 映射 · 转换×5 / 查询×4 / 新建×2 |
| `SerialNumberService` | 30 | 编号 · 获取×14 / 重置×3 / 预览×1 |
| `FlexibleService` | 29 | Flexible · 获取×5 / 启动×4 / 修改×4 |
| `ExpressionService` | 27 | Expression · 获取×12 / 加载×4 / 列出×2 |
| `DeductionRtRuleService` | 27 | 规则 · 查询×7 / 获取×5 / 判断×2 |
| `BasicDataMetaDataService` | 26 | BasicMeta · 获取×7 / 新建×6 / 查询×6 |
| `CtpParameterDefinitionService` | 25 | 参数 · 查询×10 / 删除×3 / 新建×2 |
| `CipParamEscapeDetailService` | 24 | EscapeDetail · 获取×6 / 查询×4 / 导出×3 |
| `FileDownloadService` | 23 | 文件 · 获取×12 / 调用×1 / 构建×1 |
| `SerialCurrentService` | 23 | 当前 · 查询×4 / 获取×2 / 预览×2 |
| `CtpUpgradeService` | 23 | 升级 · 修改×7 / 升级×3 / 获取×3 |
| `FilterPlanRtService` | 23 | FilterPlanRt · 查询×9 / 获取×5 / 删除×4 |
| `FormPermissionAuthService` | 23 | 权限认证 · 获取×9 / 检查×5 / 校验×2 |
| `ApproveFeatureService` | 23 | ApproveFeature · 获取×9 / 启动×2 / 发送×1 |
| `BasicDataAttributeService` | 22 | 字段 · 查询×7 / 发布×3 / 新建×2 |
| `ExcelExportTemplateService` | 22 | 模板 · 查询×6 / 获取×5 / 设置×3 |
| `CtpQrCodeBaseService` | 22 | 编码 · 获取×6 / 构建×5 / 修改×3 |
| `CtpQrCodeRuleService` | 22 | 编码规则 · 查询×7 / 删除×4 / 修改×3 |
| `FilterPlanFormalService` | 22 | FilterPlanFormal · 删除×9 / 查询×6 / 新建×2 |
| `EdocMarkManageService` | 21 | 管理 · 标记×4 / 获取×4 / 删除×2 |
| `EdocMarkRunningService` | 21 | EdocMarkRunning · 获取×9 / 释放×3 / 构建×1 |
| `CtpEnumCategoryService` | 21 | 枚举分类 · 查询×10 / 删除×5 / 修改×3 |
| `SerialRangeService` | 21 | SerialRange · 新建×4 / 检查×4 / 删除×4 |
| `FilterPlanAnalyzeService` | 21 | FilterPlanAnalyze · 获取×10 / 新增×5 / 设置×1 |
| `CustomApplicationService` | 21 | 应用 · 查询×6 / 删除×4 / 修改×4 |
| `SandboxConfigService` | 20 | 配置 · 获取×9 / 修改×2 / 查询×2 |
| `ScalabilityFieldService` | 20 | 字段 · 查询×6 / 修改×5 / 新建×1 |
| `AttachmentService` | 19 | Attachment · 获取×3 / 查询×2 / 调用×2 |
| `SandboxAppRunService` | 18 | 应用 · 查询×4 / 加载×3 / 删除×3 |

## biz 层：事件与监听

事件 73 个 · 监听器 18 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| AcrossEnvAppChange | `AcrossEnvAppChangeEvent` |
| AppChange | `AppChangeEvent` |
| BasicDataAdmin | `BasicDataAdminUpdateEvent` |
| BasicDataAttribute | `BasicDataAttributeDeleteEvent`, `BasicDataAttributeUpdateEvent` |
| BasicDataEntity | `BasicDataEntityDeleteEvent` |
| BasicDataRegisterMetadata | `BasicDataRegisterMetadataEvent` |
| ConfigItemChange | `ConfigItemChangeEvent` |
| CreateWriteBack | `CreateWriteBackEvent` |
| CtpEnum | `CtpEnumCreateEvent`, `CtpEnumDeleteEvent`, `CtpEnumUpdateEvent` |
| CtpEnumItem | `CtpEnumItemCreateEvent`, `CtpEnumItemDeleteEvent`, `CtpEnumItemUpdateEvent` |
| CtpEnumItemBatch | `CtpEnumItemBatchDeleteEvent` |
| CtpJobChange | `CtpJobChangeEvent` |
| CtpQrCode | `CtpQrCodeCreateEvent` |
| CustomAppAuth | `CustomAppAuthDeleteEvent` |
| CustomAppAuthChange | `CustomAppAuthChangeEvent` |
| CustomAppUsageStateChange | `CustomAppUsageStateChangeEvent` |
| CustomApplication | `CustomApplicationCreateEvent` |
| DataChange | `DataChangeEvent` |
| DataInitDdl | `DataInitDdlEvent` |
| DataSignVerify | `DataSignVerifyEvent` |
| DataSourceReady | `DataSourceReadyEvent` |
| Dead | `DeadEvent` |
| DeleteWriteBack | `DeleteWriteBackEvent` |
| DocMessage | `DocMessageEvent` |
| DynamicCodeUnload | `DynamicCodeUnloadEvent` |
| EscapeExport | `EscapeExportEvent` |
| EscapeImport | `EscapeImportEvent` |
| ExcelExport | `ExcelExportEvent` |
| ExcelExportSuccess | `ExcelExportSuccessEvent` |
| ExcelImport | `ExcelImportEvent` |
| ExcelImportCheck | `ExcelImportCheckEvent` |
| ExcelImportSuccess | `ExcelImportSuccessEvent` |
| ExcelImportTrans4UdcDesign | `ExcelImportTrans4UdcDesignEvent` |
| ExcelImportTransToGrid | `ExcelImportTransToGridEvent` |
| ExcelSearchMetaInfo | `ExcelSearchMetaInfoEvent` |
| ExternalFile | `ExternalFileEvent` |
| FormConvertTemplate | `FormConvertTemplateCreateEvent`, `FormConvertTemplateDeleteEvent`, `FormConvertTemplateUpdateEvent` |
| Generic | `GenericEvent` |
| Job | `JobEvent` |
| JobExecution | `JobExecutionEvent` |
| LicenseInit | `LicenseInitEvent` |
| LocalDynamicLoad | `LocalDynamicLoadEvent` |
| ModuleAllCallback | `ModuleAllCallbackEvent` |
| ModuleAppLoad | `ModuleAppLoadEvent` |
| ModuleDiff | `ModuleDiffEvent` |
| ModuleLoad | `ModuleLoadEvent` |
| ModuleMerge | `ModuleMergeEvent` |
| ModuleUnload | `ModuleUnloadEvent` |
| Opinion | `OpinionCreateEvent`, `OpinionDeleteEvent`, `OpinionEvent`, `OpinionUpdateEvent` |
| QrCodeRule | `QrCodeRuleCreateEvent`, `QrCodeRuleDeleteEvent`, `QrCodeRuleUpdateEvent` |
| SPIProviderRegister | `SPIProviderRegisterEvent` |
| ScalabilityFieldStatusChange | `ScalabilityFieldStatusChangeEvent` |
| SerialNumberRecover | `SerialNumberRecoverEvent` |
| SerialSchema | `SerialSchemaDeleteEvent`, `SerialSchemaUpdateEvent` |
| SharingDataSourceRefresh | `SharingDataSourceRefreshEvent` |
| StarterDdlInit | `StarterDdlInitEvent` |
| SuccessProcess | `SuccessProcessEvent` |
| SystemStarted | `SystemStartedEvent` |
| UpdateProcess | `UpdateProcessEvent` |
| UpdateWriteBack | `UpdateWriteBackEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `SerialEntityEventListener` | 12 |
| `LabelCountEventListener` | 8 |
| `FileChangeEventListener` | 7 |
| `ExcelEventListener` | 5 |
| `CtpQrCodeRuleEventListener` | 3 |
| `ConsumerContextClosedEventListener` | 2 |
| `ConsumerContextRefreshedEventListener` | 2 |
| `AppLoadEventListener` | 2 |
| `DeployChangeEventListener` | 2 |
| `DataSourceEventListener` | 1 |
| `CtpQrCodeEventListener` | 1 |
| `DataEventListener` | 1 |
| `ShardingDataSourceEventListener` | 1 |
| `ShardingDataSourceRefreshEventListener` | 1 |
| `SPIConfigChangeEventListener` | 1 |
| `SuccessProcessEventListener` | 1 |
| `UpdateProcessEventListener` | 1 |
| `LogDeleteEventListener` | 1 |

## web 层：Controller

共 114 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 推送/被引用（Refer*） | `ReferEdocMarkDefineController` | 6 |
| 核心实体 CRUD | `MonitorController` | 42 |
| 核心实体 CRUD | `UdcBaseGeneralController` | 40 |
| 核心实体 CRUD | `FileController` | 33 |
| 核心实体 CRUD | `ShardingController` | 26 |
| 核心实体 CRUD | `BasicDataController` | 25 |
| 核心实体 CRUD | `EnumItemController` | 25 |
| 核心实体 CRUD | `OpinionController` | 23 |
| 核心实体 CRUD | `MgnApiController` | 21 |
| 核心实体 CRUD | `ExcelController` | 21 |
| 核心实体 CRUD | `UdcMetaDataController` | 19 |
| 核心实体 CRUD | `UdcAppLogController` | 19 |
| 核心实体 CRUD | `EdocMarkExtendIncrementController` | 18 |
| 核心实体 CRUD | `LabelPrintController` | 18 |
| 核心实体 CRUD | `SerialSchemeController` | 18 |
| 核心实体 CRUD | `FilterPlanController` | 18 |
| 核心实体 CRUD | `EnumController` | 16 |
| 核心实体 CRUD | `SandboxClientController` | 16 |
| 核心实体 CRUD | `UdcReferController` | 16 |
| 核心实体 CRUD | `EdocMarkDefineController` | 15 |
| 核心实体 CRUD | `CtpQrCodeRuleController` | 14 |
| 核心实体 CRUD | `MonitorCollectorController` | 13 |
| 核心实体 CRUD | `SerialRangeController` | 13 |
| 核心实体 CRUD | `CustomApplicationController` | 13 |
| 核心实体 CRUD | `SerialNumberController` | 12 |
| 核心实体 CRUD | `ExpressionController` | 11 |
| 核心实体 CRUD | `CtpParameterController` | 11 |
| 核心实体 CRUD | `DeductionController` | 11 |
| 核心实体 CRUD | `FormulaController` | 10 |
| 核心实体 CRUD | `MigrationJsonController` | 10 |
| 核心实体 CRUD | `EdocMarkUniformSortingController` | 10 |
| 核心实体 CRUD | `GanttChartSchemaController` | 10 |
| 核心实体 CRUD | `JobInfoController` | 9 |
| 核心实体 CRUD | `ScalabilityFieldController` | 9 |
| 核心实体 CRUD | `UdcSerialConfigController` | 9 |
| 核心实体 CRUD | `EdocMarkRangeController` | 8 |
| 核心实体 CRUD | `EnumCategoryController` | 8 |
| 核心实体 CRUD | `GanttChartRunningController` | 8 |
| 核心实体 CRUD | `CtpQrCodeController` | 8 |
| 核心实体 CRUD | `ParamEscapeConfigController` | 7 |
| 核心实体 CRUD | `IntelligentController` | 7 |
| 核心实体 CRUD | `EdocMarkRunningController` | 7 |
| 核心实体 CRUD | `FormConvertTemplateController` | 7 |
| 核心实体 CRUD | `OpinionExtendController` | 7 |
| 核心实体 CRUD | `SandboxAppRunController` | 7 |
| 核心实体 CRUD | `SandboxFlexibleController` | 7 |
| 核心实体 CRUD | `AttachmentTemplateController` | 7 |
| 核心实体 CRUD | `RuntimeEnvCheckController` | 7 |
| 核心实体 CRUD | `DynamicModuleController` | 6 |
| 核心实体 CRUD | `CtpSystemEnvController` | 6 |
| 核心实体 CRUD | `I18nResourceController` | 6 |
| 核心实体 CRUD | `CtpParameterDefinitionController` | 6 |
| 核心实体 CRUD | `SandboxTenantConfigController` | 6 |
| 核心实体 CRUD | `DataFlowRtMappingController` | 6 |
| 核心实体 CRUD | `AppDraftController` | 6 |
| 核心实体 CRUD | `InitMonitorController` | 5 |
| 核心实体 CRUD | `FormConvertCategoryController` | 5 |
| 核心实体 CRUD | `LicenseController` | 5 |
| 核心实体 CRUD | `PraiseController` | 5 |
| 核心实体 CRUD | `AttachmentController` | 4 |
| 核心实体 CRUD | `V5MigrateOpinionController` | 4 |
| 核心实体 CRUD | `ConditionController` | 4 |
| 核心实体 CRUD | `ConfigDataController` | 4 |
| 核心实体 CRUD | `AbstractComponentDynamicSelectController` | 4 |
| 核心实体 CRUD | `AbstractDynamicSelectController` | 4 |
| 核心实体 CRUD | `SandboxSystemConfigController` | 4 |
| 核心实体 CRUD | `CtpUpgradeController` | 4 |
| 核心实体 CRUD | `DynamicJarController` | 4 |
| 核心实体 CRUD | `UdcRtPageLogController` | 4 |
| 核心实体 CRUD | `UdcAppInfoController` | 3 |
| 核心实体 CRUD | `FormConvertController` | 3 |
| 核心实体 CRUD | `OpinionAdminController` | 3 |
| 核心实体 CRUD | `SerialConditionController` | 3 |
| 核心实体 CRUD | `CustomPlanController` | 3 |
| 核心实体 CRUD | `MigrationAutoController` | 2 |
| 核心实体 CRUD | `AbstractDynamicOnEntitySelectController` | 2 |
| 核心实体 CRUD | `DependentExportController` | 2 |
| 核心实体 CRUD | `HealthController` | 2 |
| 核心实体 CRUD | `PrometheusController` | 2 |
| 核心实体 CRUD | `CtpShortLinkController` | 2 |
| 核心实体 CRUD | `DataFlowRtMapController` | 2 |
| 核心实体 CRUD | `RuntimeCOLISplitController` | 2 |
| 核心实体 CRUD | `UdcAttrSnapshotRtController` | 2 |
| 核心实体 CRUD | `UdcRtPageInfoController` | 2 |
| 核心实体 CRUD | `BootArtifactController` | 1 |
| 核心实体 CRUD | `CaptchaController` | 1 |
| 核心实体 CRUD | `OpenApiErrorCodeController` | 1 |
| 核心实体 CRUD | `EdocMarkReleaseRecordController` | 1 |
| 核心实体 CRUD | `FrontendLogController` | 1 |
| 核心实体 CRUD | `DynamicSelectByIdsController` | 1 |
| 核心实体 CRUD | `OpinionBoxController` | 1 |
| 核心实体 CRUD | `PrometheusLocalController` | 1 |
| 核心实体 CRUD | `TomcatMonitorController` | 1 |
| 核心实体 CRUD | `BpmNodeInfoController` | 1 |
| 核心实体 CRUD | `UdcRuntimeHistoryMetaDataController` | 1 |
| 核心实体 CRUD | `DataFlowForBpmController` | 1 |
| 核心实体 CRUD | `DeductionRtUpgradeController` | 1 |
| 核心实体 CRUD | `FrontFunctionSupportController` | 1 |
| 核心实体 CRUD | `GraphqlProxyController` | 1 |
| 核心实体 CRUD | `UdcDataTypeController` | 1 |
| 核心实体 CRUD | `UdcEntityUpdateRtTestController` | 1 |
| 核心实体 CRUD | `UdcFormDataQueryController` | 1 |
| 核心实体 CRUD | `UdcFunctionNodeController` | 1 |
| 核心实体 CRUD | `UdcRoleRtController` | 1 |
| 核心实体 CRUD | `UdcRuntimeDatabaseController` | 1 |
| 核心实体 CRUD | `UdcBaseAppInfoController` | 1 |
| 核心实体 CRUD | `FormAppInfoController` | 0 |
| 核心实体 CRUD | `FormAppMbController` | 0 |
| 核心实体 CRUD | `FormAppPcController` | 0 |
| 核心实体 CRUD | `FormReferController` | 0 |
| 核心实体 CRUD | `NormalAppInfoController` | 0 |
| 核心实体 CRUD | `NormalAppMbController` | 0 |
| 核心实体 CRUD | `NormalAppPcController` | 0 |
| 核心实体 CRUD | `NormalReferController` | 0 |

## 落表

⚠️ **UNVERIFIED** —— 本模块构件 的 class 常量池里没有表名字面量。

原因：该模块的 SQL/表名不在 biz 层常量池（走 Dubbo 远端 / 走配置 / 纯计算或 SDK）。
不写推测表名。

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 47 接口 / 141 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 183 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 73 事件 / 18 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 114 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径 | 未取证 | `UNVERIFIED` |
| 落表 | 本模块代码无表名常量，不适用 | `N/A` |
