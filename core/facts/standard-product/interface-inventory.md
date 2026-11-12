# 后端接口全量清单

> 自动生成，勿手改。`tools/core/platform/emit_interface_inventory.py` 重跑即可。
> 来源 `interfaces.json`：**1457 个接口** = **1348 个真接口** + **109 个注解**（`@interface`，贴代码上由平台读，不能 implements）。
> 真接口里 **755 个有 abstract 方法** = 真正可以被 implements 的扩展点；其余是纯标记接口或纯 default 接口。
> 「必实现」列只列 abstract 方法，default 方法不列（有默认实现，不必写）。

## 分组总览

| 顶层包 | 接口数 |
|---|---|
| `com.seeyon.boot` | 429 |
| `com.seeyon.udc` | 274 |
| `com.seeyon.cip` | 157 |
| `com.seeyon.bpm` | 128 |
| `com.seeyon.ctp` | 115 |
| `com.seeyon.cdp` | 97 |
| `com.seeyon.organization` | 60 |
| `com.seeyon.app` | 30 |
| `antlr.v4.runtime` | 23 |
| `com.seeyon.m5` | 15 |
| `com.seeyon.portal` | 15 |
| `com.seeyon.devops` | 10 |
| `graphql.execution.instrumentation` | 9 |
| `graphql.schema.idl` | 5 |
| `com.seeyon.ai` | 2 |
| `graphql.execution.batched` | 2 |
| `graphql.execution.nextgen` | 2 |
| `graphql.parser.antlr` | 2 |
| `graphql.schema.transform` | 2 |
| `graphql.DeferredExecutionResult` | 1 |
| `graphql.ErrorClassification` | 1 |
| `graphql.ExecutionResult` | 1 |
| `graphql.GraphQLError` | 1 |
| `graphql.Internal` | 1 |
| `graphql.PublicApi` | 1 |
| `graphql.PublicSpi` | 1 |
| `graphql.ThreadSafe` | 1 |
| `graphql.TrivialDataFetcher` | 1 |
| `graphql.VisibleForTesting` | 1 |
| `graphql.analysis.FieldComplexityCalculator` | 1 |
| `graphql.analysis.QueryReducer` | 1 |
| `graphql.analysis.QueryVisitor` | 1 |
| `graphql.analysis.QueryVisitorFieldArgumentEnvironment` | 1 |
| `graphql.analysis.QueryVisitorFieldArgumentInputValue` | 1 |
| `graphql.analysis.QueryVisitorFieldArgumentValueEnvironment` | 1 |
| `graphql.analysis.QueryVisitorFieldEnvironment` | 1 |
| `graphql.analysis.QueryVisitorFragmentDefinitionEnvironment` | 1 |
| `graphql.analysis.QueryVisitorFragmentSpreadEnvironment` | 1 |
| `graphql.analysis.QueryVisitorInlineFragmentEnvironment` | 1 |
| `graphql.execution.DataFetcherExceptionHandler` | 1 |
| `graphql.execution.ExecutionIdProvider` | 1 |
| `graphql.execution.ValueUnboxer` | 1 |
| `graphql.execution.directives` | 1 |
| `graphql.execution.preparsed` | 1 |
| `graphql.introspection.IntrospectionQuery` | 1 |
| `graphql.language.Definition` | 1 |
| `graphql.language.DescribedNode` | 1 |
| `graphql.language.DirectivesContainer` | 1 |
| `graphql.language.ImplementingTypeDefinition` | 1 |
| `graphql.language.NamedNode` | 1 |
| `graphql.language.Node` | 1 |
| `graphql.language.NodeBuilder` | 1 |
| `graphql.language.NodeDirectivesBuilder` | 1 |
| `graphql.language.NodeVisitor` | 1 |
| `graphql.language.SDLDefinition` | 1 |
| `graphql.language.ScalarValue` | 1 |
| `graphql.language.Selection` | 1 |
| `graphql.language.SelectionSetContainer` | 1 |
| `graphql.language.Type` | 1 |
| `graphql.language.TypeDefinition` | 1 |
| `graphql.language.Value` | 1 |
| `graphql.relay.Connection` | 1 |
| `graphql.relay.ConnectionCursor` | 1 |
| `graphql.relay.Edge` | 1 |
| `graphql.relay.PageInfo` | 1 |
| `graphql.schema.Coercing` | 1 |
| `graphql.schema.DataFetcher` | 1 |
| `graphql.schema.DataFetcherFactory` | 1 |
| `graphql.schema.DataFetchingEnvironment` | 1 |
| `graphql.schema.DataFetchingFieldSelectionSet` | 1 |
| `graphql.schema.GraphQLCompositeType` | 1 |
| `graphql.schema.GraphQLDirectiveContainer` | 1 |
| `graphql.schema.GraphQLFieldsContainer` | 1 |
| `graphql.schema.GraphQLImplementingType` | 1 |
| `graphql.schema.GraphQLInputFieldsContainer` | 1 |
| `graphql.schema.GraphQLInputType` | 1 |
| `graphql.schema.GraphQLInputValueDefinition` | 1 |
| `graphql.schema.GraphQLModifiedType` | 1 |
| `graphql.schema.GraphQLNamedInputType` | 1 |
| `graphql.schema.GraphQLNamedOutputType` | 1 |
| `graphql.schema.GraphQLNamedSchemaElement` | 1 |
| `graphql.schema.GraphQLNamedType` | 1 |
| `graphql.schema.GraphQLNullableType` | 1 |
| `graphql.schema.GraphQLOutputType` | 1 |
| `graphql.schema.GraphQLSchemaElement` | 1 |
| `graphql.schema.GraphQLType` | 1 |
| `graphql.schema.GraphQLTypeVisitor` | 1 |
| `graphql.schema.GraphQLUnmodifiedType` | 1 |
| `graphql.schema.GraphqlTypeComparatorRegistry` | 1 |
| `graphql.schema.SelectedField` | 1 |
| `graphql.schema.TypeResolver` | 1 |
| `graphql.schema.diff` | 1 |
| `graphql.schema.validation` | 1 |
| `graphql.schema.visibility` | 1 |
| `graphql.util.NodeAdapter` | 1 |
| `graphql.util.TraverserContext` | 1 |
| `graphql.util.TraverserVisitor` | 1 |
| `graphql.validation.DocumentVisitor` | 1 |
| `it.sauronsoftware.jave` | 1 |

## com.seeyon.boot（429）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `AppService` | 4 | 4 | `value()`, `description()`, `sort()`, `customs()` |
| `AppServiceOperation` | 9 | 9 | `value()`, `description()`, `returnValue()`, `openApi()`, `sort()` …+4 |
| `BootApp` | 8 | 8 | `name()`, `names()`, `caption()`, `version()`, `description()` …+3 |
| `Custom` | 2 | 2 | `name()`, `properties()` |
| `CustomAttribute` | 2 | 2 | `name()`, `value()` |
| `DtoAttribute` | 13 | 13 | `value()`, `description()`, `hidden()`, `xssProcess()`, `dataI18n()` …+8 |
| `DtoInfo` | 5 | 5 | `value()`, `entity()`, `sort()`, `isPublic()`, `customs()` |
| `EntityAttribute` | 19 | 19 | `value()`, `description()`, `hidden()`, `changeId()`, `dataI18n()` …+14 |
| `EntityIndex` | 4 | 4 | `value()`, `indexType()`, `name()`, `columns()` |
| `EntityInfo` | 12 | 12 | `value()`, `description()`, `entityType()`, `historyEntity()`, `plugins()` …+7 |
| `EnumAttribute` | 6 | 6 | `value()`, `description()`, `icon()`, `color()`, `sort()` …+1 |
| `EnumInfo` | 6 | 6 | `value()`, `type()`, `description()`, `excludes()`, `sort()` …+1 |
| `FileFieldAttribute` | 1 | 1 | `fileFieldType()` |
| `HasRole` | 2 | 2 | `value()`, `orgId()` |
| `Maskable` | 4 | 4 | `type()`, `maskKeys()`, `start()`, `end()` |
| `MessageInfo` | 6 | 6 | `value()`, `description()`, `topic()`, `sort()`, `openApi()` …+1 |
| `MigrationIgnoreField` | 1 | 1 | `ignoreField()` |
| `MigrationStorageField` | 2 | 2 | `value()`, `storageType()` |
| `MultiRequestBody` | 2 | 2 | `required()`, `value()` |
| `OpenApi` | 5 | 5 | `isOpenApi()`, `url()`, `async()`, `sort()`, `customs()` |
| `ParameterInfo` | 3 | 3 | `value()`, `example()`, `customs()` |
| `ResourcePermission` | 2 | 2 | `pageInfo()`, `resourceInfo()` |
| `RestApi` | 4 | 4 | `value()`, `sort()`, `group()`, `customs()` |
| `RestApiOperation` | 6 | 6 | `value()`, `description()`, `returnValue()`, `customs()`, `auditMode()` …+1 |
| `Safety` | 5 | 5 | `encryption()`, `auditLog()`, `permission()`, `sensitive()`, `openApiEncrypt()` |
| `LRUMapListener` | 1 | 1 | `onRemove(K, V)` |
| `AppBeanNameModifier` | 0 | 1 | — |
| `TokenConstants` | 0 | 0 | — |
| `BootRequestContextHolder` | 0 | 2 | — |
| `BaseDao` | 34 | 34 | `create(T)`, `createBatch(List)`, `createBatchNoClob(List)`, `createBatchIgnoreTime(List)`, `update(T)` …+29 |
| `BaseSecretEntityable` | 4 | 4 | `setSecretId(Long)`, `setSecretN(Integer)`, `getSecretId()`, `getSecretN()` |
| `BaseSignEntityable` | 4 | 4 | `setDataSign(String)`, `setDataSignSuccess(Integer)`, `getDataSign()`, `getDataSignSuccess()` |
| `ComponentEntityable` | 1 | 1 | `setAggregationAppName(String)` |
| `Entityable` | 7 | 10 | `setId(Long)`, `getId()`, `getCreateTime()`, `setCreateTime(Date)`, `getUpdateTime()` …+2 |
| `HistorytEntityable` | 1 | 1 | `setArchiveTime(Date)` |
| `AccessAuditLogService` | 1 | 1 | `create(String[], String)` |
| `Asymmetric` | 5 | 5 | `getName()`, `generateKey()`, `encrypt(String, String)`, `decrypt(String, String)`, `getCipherTextPrefix()` |
| `AsymmetricSpi` | 3 | 3 | `encrypt(String, String)`, `decrypt(String, String)`, `generateKey()` |
| `Digest` | 4 | 4 | `getName()`, `getCipherTextPrefix()`, `encrypt(String)`, `equals(String, String)` |
| `DigestSpi` | 1 | 1 | `encrypt(String)` |
| `Symmetric` | 4 | 4 | `getName()`, `getCipherTextPrefix()`, `encrypt(String)`, `decrypt(String)` |
| `SymmetricSpi` | 2 | 2 | `encrypt(String)`, `decrypt(String)` |
| `Messageable` | 1 | 2 | `code()` |
| `FindBusinessExceptionHandler` | 0 | 1 | — |
| `NothingFunction` | 1 | 1 | `apply()` |
| `TenantChangeFunction` | 0 | 6 | — |
| `TenantLoopFunction` | 0 | 2 | — |
| `TenantSetFunction` | 0 | 1 | — |
| `AutoConfigExclude` | 0 | 1 | — |
| `ComponentInitializer` | 0 | 2 | — |
| `SeeyonApplicationRunner` | 1 | 2 | `run()` |
| `Inspection` | 6 | 7 | `getName()`, `enable()`, `getCaption()`, `getSort()`, `getItems()` …+1 |
| `LicensePlugin` | 3 | 3 | `hasPlugin(String)`, `hasAnyPlugin(Set)`, `hasAllPlugin(Set)` |
| `ComponentDynamicLoader` | 1 | 4 | `isComponent(Class)` |
| `ComponentDynamicRegister` | 2 | 2 | `register(String, List)`, `unregister(String)` |
| `DynamicClassLoader` | 1 | 1 | `loadClass(String)` |
| `ModuleBeanRepository` | 3 | 3 | `getBean(String)`, `getBean(Class)`, `getBeansOfType(Class)` |
| `ModuleProcessor` | 2 | 2 | `initialize(ModuleAppClassLoader, String, Set)`, `destroy(String)` |
| `LogInitializer` | 1 | 1 | `init(LogbackConfigurator)` |
| `CommandConstants` | 0 | 0 | — |
| `CtpMeterBinder` | 0 | 0 | — |
| `ComponentSecurityCheck` | 2 | 3 | `check(ComponentCheckDto)`, `checkUser(String, Map, Object>)` |
| `DataSignExecution` | 5 | 5 | `envEnable()`, `SignatureList(List)`, `Signature(String)`, `Verify(String, String)`, `VerifyList(Map, String>)` |
| `EntityEncryption` | 2 | 2 | `decrypt(String)`, `encrypt(String)` |
| `SensitiveSpi` | 1 | 1 | `sensitiveProcess(String)` |
| `Idempotent` | 0 | 0 | — |
| `IdempotentInfoDao` | 0 | 0 | — |
| `ExceptionHandler` | 1 | 1 | `handle(ExceptionContext, EX)` |
| `DBExceptionParser` | 1 | 1 | `parser(String)` |
| `CtpArtifactUploadDao` | 0 | 0 | — |
| `MavenArtifactService` | 3 | 4 | `getMavenType()`, `upload(ArtifactDto)`, `download(ArtifactDto)` |
| `AttachmentExtendApi` | 0 | 2 | — |
| `RateChecker` | 1 | 1 | `check(String, Integer, Long)` |
| `PortProvider` | 1 | 1 | `next()` |
| `Redis` | 4 | 4 | `isActive()`, `start()`, `stop()`, `ports()` |
| `WeakTypeEscapeService` | 1 | 1 | `findWeakTypeEscapeDto(Map)` |
| `CipDatabaseCommonDao` | 3 | 3 | `fetchColumnsByUniqueKey(String, String, List, List, Long)`, `selectAllColumnsWithCondition(String, String, Object, Long)`, `selectColumnsWithNoCondition(String, List, Long)` |
| `CipParamEscapeDetailDao` | 0 | 0 | — |
| `DocFileConvertRecordDao` | 0 | 0 | — |
| `DocFileVersionDao` | 0 | 0 | — |
| `V5DoneLogDao` | 0 | 0 | — |
| `V5FlowPngDao` | 0 | 0 | — |
| `V5OpinionDao` | 0 | 0 | — |
| `ValueConvert` | 2 | 2 | `getTargetDataType()`, `convert(String)` |
| `ConditionConfigOutput` | 1 | 1 | `getContent(ConditionOutputParam)` |
| `MapOperatorParse` | 2 | 2 | `getOperator()`, `parseOperator(SingleConditionDto, Map, Object>, List, Object>>, MapConditionParseConfigurationBo)` |
| `RightParamParser` | 2 | 2 | `getType()`, `parseValue(SingleConditionDto$LeftParamDto, SingleConditionDto$RightParamDto, Map, Object>)` |
| `CodeReplacer` | 3 | 3 | `getRelationType()`, `processRelationCodeById(List)`, `processRelationIdByCode(List)` |
| `DataBackupHandler` | 0 | 2 | — |
| `DataComparator` | 2 | 3 | `supports(Class)`, `compare(ExecutionContext, DataValidationResult)` |
| `DataConsistencyValidator` | 2 | 2 | `supports()`, `doValidate(DataConsistencyContext)` |
| `DependencyValidator` | 3 | 5 | `supports(Class)`, `getSupportedType()`, `doValidate(ExecutionContext, DataValidationResult)` |
| `EntityDataHandler` | 3 | 10 | `supports(Class)`, `processQueryData(ExecutionContext, T)`, `processReplaceData(ExecutionContext, T)` |
| `EntityDslHandler` | 3 | 4 | `supports(Class)`, `fetchData(FetchCondition)`, `handleDsl(EntityDslDto)` |
| `Constants` | 0 | 0 | — |
| `Lifecycle` | 3 | 3 | `start()`, `stop()`, `isRunning()` |
| `FieldResolver` | 1 | 4 | `resolve(T)` |
| `DataUpdateStrategy` | 0 | 1 | — |
| `WritableField` | 2 | 6 | `getValue(T)`, `setValue(T, F)` |
| `EntityConfigDataDao` | 1 | 1 | `selectModuleCodeByPackageId(Long)` |
| `FieldRelationDataDao` | 1 | 1 | `selectRelationTypeByPackageId(Long)` |
| `ExecuteTemplate` | 7 | 7 | `executeQuery(TaskInfoDto)`, `executeUpload(Long, String)`, `executeDownload(Long, String)`, `executeValidate(Long)`, `executeUpdate(Long)` …+2 |
| `TaskExecutor` | 4 | 5 | `getExecutor()`, `getTaskListener()`, `getTaskManager()`, `execute(T)` |
| `TaskManager` | 5 | 5 | `addFutureTask(Long, CompletableFuture)`, `cancelFutureTask(Long)`, `removeFutureTask(Long, CompletableFuture)`, `countFutureTask(Long)`, `getAllTasks()` |
| `TaskListener` | 5 | 5 | `onStart(TaskInfoDto)`, `beforeExecute(TaskInfoDto)`, `afterExecute(TaskInfoDto)`, `onComplete(TaskInfoDto)`, `onError(TaskInfoDto, Exception)` |
| `ConfigServiceInterface` | 2 | 2 | `selectConfigItemList(ConfigItemSearchDto)`, `selectPageConfigItemList(ConfigItemSearchDto)` |
| `CustomPlanAppService` | 2 | 2 | `selectBySourceIds(SingleRequest)`, `selectByComplexCondition(SingleRequest)` |
| `PersonalPlanAppService` | 5 | 5 | `selectByCondition(SingleRequest)`, `selectListByCondition(SingleRequest)`, `createRedirectBatch(SingleRequest)`, `selectPageByCondition(PageRequest)`, `deleteByIds(SingleRequest)` |
| `ScalabilityFieldAppService` | 7 | 7 | `selectMetadataExtEntityTree(SingleRequest)`, `listExtFileds(SingleRequest)`, `selectAvailableDatatype(SingleRequest)`, `selectAttribute(SingleRequest)`, `updateBatch(SingleRequest)` …+2 |
| `UdcPageProcessEventService` | 3 | 3 | `selectProcessEventListByCondition(SingleRequest)`, `selectProcessEventList(SingleRequest)`, `clearCacheByAppName(SingleRequest)` |
| `CustomPlanContentDao` | 0 | 0 | — |
| `CustomPlanDao` | 0 | 0 | — |
| `FilterPlanDao` | 0 | 0 | — |
| `FilterPlanFormalDao` | 0 | 0 | — |
| `FilterPlanRtDao` | 0 | 0 | — |
| `PersonalPlanDao` | 0 | 0 | — |
| `ScalabilityFieldDao` | 0 | 0 | — |
| `UdcRuntimeHistoryMetaDataDao` | 0 | 0 | — |
| `DataFlowForBpmAppService` | 2 | 2 | `asyncTriggerFlowForBpm(SingleRequest)`, `fillErrorFlowData(SingleRequest)` |
| `DataFlowMapAppService` | 2 | 2 | `selectByCondition(SingleRequest)`, `selectById(SingleRequest)` |
| `DataFlowMappingAppService` | 6 | 6 | `selectOriginalMappingList(SingleRequest)`, `selectById(SingleRequest)`, `selectMappingInitData(SingleRequest)`, `update(SingleRequest)`, `updateMappingState(SingleRequest)` …+1 |
| `UdcRuleAppService` | 0 | 1 | — |
| `DataFlowIdMappingBaseDao` | 0 | 2 | — |
| `DataFlowRtMapDao` | 0 | 0 | — |
| `DataFlowRtMappingDao` | 0 | 0 | — |
| `BeforeBatchExeAdapter` | 0 | 1 | — |
| `DataInitAdapter` | 0 | 3 | — |
| `DdlInitAdapter` | 0 | 1 | — |
| `EntitySortAdapter` | 0 | 1 | — |
| `InitMonitorAppService` | 5 | 5 | `selectAppStarterInitVersions(PageRequest)`, `executeOnetime(Long)`, `executeWithRecordType(Integer)`, `ignoreError(Long)`, `selectAppInitSingleDetails(Map, Object>)` |
| `AppDataInitDetailDao` | 0 | 0 | — |
| `AppDataInitVersionDao` | 0 | 0 | — |
| `AppInitSingleDetailDao` | 0 | 0 | — |
| `AppStarterInitDetailDao` | 0 | 0 | — |
| `AppStarterInitVersionDao` | 0 | 0 | — |
| `AppTenantIdRelationDao` | 0 | 0 | — |
| `AppTenantIncrementVersionDao` | 0 | 0 | — |
| `AppTenantInitDeleteDao` | 0 | 0 | — |
| `AppTenantInitDetailDao` | 0 | 0 | — |
| `AppTenantInitVersionDao` | 0 | 0 | — |
| `DDLExceptionParser` | 1 | 3 | `ignorePatterns()` |
| `DataInitializer` | 4 | 4 | `initAppData(String, String, String, String, ClassLoader)`, `initAppData(String, String, String, String, ClassLoader, Boolean)`, `initTenantData(String, String, String, String, ClassLoader, String)`, `deleteTenantData(String, String, String)` |
| `ProxyRelationJobInterface` | 1 | 1 | `initTenantData(DataInitializerMessage)` |
| `TenantDataInitializerInterface` | 2 | 3 | `initTenantData(String)`, `deleteTenantData(String)` |
| `CtpDataMigrationNotifyDao` | 0 | 0 | — |
| `CtpDataMigrationTaskDetailDao` | 0 | 0 | — |
| `CtpDataMigrationTaskInfoDao` | 0 | 0 | — |
| `StorageMigrationService` | 5 | 5 | `uploadForFerryboat(String, String)`, `ossUpload(File)`, `downloadFromFerryboat(String)`, `downloadFromOss(String, String, String)`, `existForFerryboat(String)` |
| `MgnExportBatchInterface` | 1 | 1 | `dynamicExport(MgnExportBatchParam)` |
| `MgnExportInterface` | 1 | 1 | `dynamicExport(List)` |
| `MgnInAdapter` | 3 | 3 | `before(MgnInParam)`, `sort(MgnSortParam)`, `after(MgnInAfterParam)` |
| `MgnUniqueAdapter` | 1 | 1 | `before(MgnUniqueParam)` |
| `StorageServiceInterface` | 11 | 11 | `uploadZip(File, String)`, `uploadJson(String, String)`, `downloadUrl(String)`, `downloadFromOss(String)`, `downloadJson(String)` …+6 |
| `ConnectionCallback` | 3 | 3 | `commit(ProxyConnection)`, `rollback(ProxyConnection)`, `setAutoCommit(boolean, ProxyConnection)` |
| `IConnectionPoolProxy` | 15 | 15 | `init(DBConProviderConfig, Properties)`, `getSJConProviderConfig()`, `clearExceedConnInfos()`, `getNoUseCount()`, `getUseList()` …+10 |
| `DataType` | 12 | 12 | `getName()`, `getVisibility()`, `getCaption()`, `baseDataType()`, `getJavaType()` …+7 |
| `DeductionRtMapAppService` | 2 | 2 | `selectSimpleDeductionMap(SingleRequest)`, `selectById(SingleRequest)` |
| `DeductionRtRuleAppService` | 5 | 5 | `selectRtRuleVersion(SingleRequest)`, `selectById(SingleRequest)`, `initData(SingleRequest)`, `saveRuleNewVersion(SingleRequest)`, `enableRule(SingleRequest)` |
| `RuleDetailRtService` | 4 | 4 | `match(EntityMetadataDto)`, `secondaryStatus()`, `getType()`, `generateTypeDataList(AggEntityMetadataDto)` |
| `DeductionIdMappingDao` | 0 | 0 | — |
| `DeductionRtAlgorithmDao` | 0 | 0 | — |
| `DeductionRtMapDao` | 1 | 1 | `getTotalMap()` |
| `DeductionRtRuleDao` | 0 | 0 | — |
| `DeductionRtRuleDetailDao` | 0 | 0 | — |
| `DeductionUpdateMapper` | 2 | 2 | `update4Deduction(Map, Object>)`, `select4Deduction(Map, Object>)` |
| `DubboFactory` | 5 | 5 | `getProxy(Class, String, String, int)`, `getProxy(Class, String, String)`, `getProxy(Class, String, int)`, `getProxy(Class, String)`, `getProxy(Class)` |
| `DubboComponent` | 0 | 0 | — |
| `AppServiceProxy` | 2 | 4 | `invokeAppService(SingleRequest)`, `reliableInvokeAppService(SingleRequest)` |
| `AppServiceProxyCallback` | 1 | 1 | `callback(SingleRequest)` |
| `InitDataCallback` | 1 | 1 | `initBasicData(Long, String)` |
| `DynamicModuleDao` | 0 | 0 | — |
| `DynamicSelectDao` | 0 | 0 | — |
| `DynamicSelectMapper` | 1 | 1 | `dynamicSelectPageByConditions(PageInfo, String, Sort, Map, Object>)` |
| `DateParser` | 0 | 1 | — |
| `DynamicSqlParameterDataParser` | 1 | 1 | `dataParser(Class, Object, String, Class)` |
| `DynamicSqlReturnDataParser` | 1 | 1 | `dataParser(Class, Object, String, Class)` |
| `BaseElasticsearchRepository` | 26 | 28 | `save(S)`, `saveAll(Iterable)`, `deleteById(String)`, `deleteByIds(Iterable)`, `selectById(String)` …+21 |
| `CtpEnumCategoryDao` | 0 | 0 | — |
| `CtpEnumDao` | 0 | 0 | — |
| `CtpEnumItemDao` | 1 | 1 | `calcEnumItemOrderNo(Map, Object>)` |
| `CtpEnumItemFilterInterface` | 1 | 1 | `filter(List)` |
| `EventHandler` | 0 | 0 | — |
| `EventSubscribe` | 2 | 2 | `threadModel()`, `order()` |
| `SubscriberExceptionHandler` | 1 | 1 | `handleException(Throwable, SubscriberExceptionContext)` |
| `GenericEvent` | 1 | 1 | `getGenericClass()` |
| `DesignMetadataQueryApi` | 5 | 5 | `selectAggEntityMetadataByFullName(SingleRequest)`, `selectEntityMetadataByFullName(SingleRequest)`, `selectDtoMetadataByEntityFullName(SingleRequest)`, `selectCtpEnumMetadataByFullNames(SingleRequest)`, `selectEnumMetadataByFullNames(SingleRequest)` |
| `ExcelExportTemplateDao` | 0 | 0 | — |
| `HostAppFunctionInterface` | 2 | 2 | `selectDependentApplicationByHostAppName(SingleRequest)`, `getHostAppName()` |
| `UdcDynamicResourceService` | 2 | 2 | `getAssembleUrl(String, String)`, `getAssembleUrl(URLClassLoader, String, String)` |
| `FileInfoProxy` | 1 | 1 | `selectByIds(SingleRequest)` |
| `WaterMarkControl` | 1 | 1 | `noWaterMarkDownload(String)` |
| `FileDao` | 0 | 0 | — |
| `ICoder` | 3 | 3 | `initKey(String)`, `encode(InputStream, OutputStream)`, `decode(InputStream, OutputStream)` |
| `StorageKeyGenerator` | 3 | 4 | `getName()`, `getStorageKey(StorageKeyDto)`, `parseStorageKey(String)` |
| `StorageSpi` | 8 | 9 | `getPrivateBucketName()`, `getPublicBucketName()`, `getFerryboatBucketName()`, `upload(SpiUploadRequestDto)`, `download(String, String, HttpServletResponse)` …+3 |
| `V5StorageSpi` | 4 | 4 | `download(String, HttpServletResponse)`, `download(String)`, `exist(String)`, `parseKey(String)` |
| `StorageService` | 3 | 14 | `getStorageType()`, `init(StorageProperties, String)`, `shutdown()` |
| `Filter` | 1 | 2 | `doFilter(C, FilterChain)` |
| `FilterChain` | 1 | 1 | `doFilter(C)` |
| `Named` | 0 | 1 | — |
| `FormConvertCategoryDao` | 0 | 0 | — |
| `FormConvertTemplateDao` | 0 | 0 | — |
| `ExpressionFilter` | 1 | 1 | `order()` |
| `ParamLoadService` | 2 | 2 | `type()`, `useCustom()` |
| `ControlDataResolver` | 1 | 1 | `resolveControlData(ExpressionToken, StringBuilder, ExpressionSaveDto)` |
| `FormulaDao` | 0 | 0 | — |
| `ExprOutsideService` | 1 | 1 | `loadParamSchemaInfo(VariableSchemaLoadDto)` |
| `ExprConsistencyValidator` | 2 | 2 | `validateConsistency(ExpressionDefinitionDto)`, `validateConsistency(ConsistencyValidateConfig)` |
| `ExpressionValidationFilter` | 1 | 1 | `doFilter(ExpressionSaveDto, FilterChain)` |
| `Function` | 7 | 7 | `category()`, `displayName()`, `description()`, `sort()`, `hidden()` …+2 |
| `FunctionClass` | 0 | 0 | — |
| `ParamLinkage` | 2 | 2 | `isLinkage()`, `linkageIndex()` |
| `Parameter` | 3 | 3 | `displayName()`, `description()`, `dataType()` |
| `Parameters` | 1 | 1 | `value()` |
| `ReturnValue` | 4 | 4 | `dataType()`, `description()`, `appName()`, `fullName()` |
| `Caller` | 3 | 3 | `call(Object[])`, `callWithType(Object[], String, String)`, `getOperator()` |
| `FunctionSupporter` | 1 | 1 | `functions()` |
| `ExprHOF` | 1 | 1 | `hoc()` |
| `ExpressionScriptBuilder` | 1 | 1 | `build(ASTNode, ScriptBuildContext)` |
| `ExtensionFunctionScriptBuilder` | 0 | 0 | — |
| `ScriptBuilderInterceptor` | 1 | 3 | `getNodeType()` |
| `CallerSemanticAnalyzer` | 2 | 3 | `analyze(ASTNode, SemanticAnalyzer)`, `getOperatorName()` |
| `FunctionSemanticAnalyzer` | 1 | 1 | `analyze(ASTNode, SemanticAnalyzer)` |
| `GanttChartSchemaDao` | 0 | 0 | — |
| `DynamicSelectByIdsDao` | 0 | 0 | — |
| `DynamicSelectByIdsMapper` | 1 | 1 | `dynamicSelectByIds(String, Map, Object>)` |
| `MessageRepository` | 7 | 7 | `getMessage(String, Object[])`, `getMessage(String)`, `getMessage(String, Object[], Locale)`, `getMessage(String, String, Object[])`, `getMessage(String, String)` …+2 |
| `I18nLocaleAppService` | 0 | 4 | — |
| `I18nResourceAppService` | 0 | 1 | — |
| `MetadataI18nResourceLoader` | 6 | 6 | `loadEntityMetadataResources(String)`, `loadDyAppEntityMetadataResources(String, String)`, `loadStarterEntityMetadataResources(StarterInfo)`, `loadPageMenusMapping(String)`, `loadDyPageInfo(String)` …+1 |
| `LabelPrintCategoryDao` | 0 | 0 | — |
| `LabelPrintRecordDao` | 0 | 0 | — |
| `LabelPrintTemplateDao` | 0 | 0 | — |
| `LicenseProcessor` | 24 | 27 | `init()`, `isTenantMode()`, `getPlugins()`, `getAppPlugins()`, `getProductInfo()` …+19 |
| `LicenseInfoDao` | 0 | 0 | — |
| `ECacheEvict` | 0 | 0 | — |
| `ECachePut` | 1 | 1 | `condition()` |
| `ECacheable` | 1 | 1 | `condition()` |
| `ENoCache` | 1 | 1 | `enabled()` |
| `MethodBizProxy` | 0 | 0 | — |
| `PriorityCache` | 3 | 3 | `cacheName()`, `cacheManager()`, `isAggregateRoot()` |
| `RCacheable` | 1 | 1 | `condition()` |
| `AttributeSnapshotAppService` | 4 | 4 | `selectByDataId(Long)`, `selectByDataIds(List)`, `selectByMasterDataId(Long)`, `selectByMasterDataIds(List)` |
| `DataTransferAppService` | 0 | 1 | — |
| `RecycleSerialNumber` | 0 | 0 | — |
| `ApprovalCallBack` | 0 | 6 | — |
| `ApprovalCallBackExt` | 0 | 6 | — |
| `BillStateCallBack` | 0 | 1 | — |
| `EntityAttrSnapshotCallBack` | 4 | 4 | `saveSnapshot(List, EntityMeta)`, `updateSnapshot(List, Map, T>, Map, T>, EntityMeta)`, `deleteByDataMasterIds(List)`, `deleteDataIds(List)` |
| `EntityDataDiffCallBack` | 1 | 1 | `diffData(List, Map, T>, Map, T>, EntityMeta)` |
| `EntityRuntimeLogCallBack` | 0 | 28 | — |
| `MethodCallBack` | 0 | 10 | — |
| `PermissionCallBack` | 0 | 2 | — |
| `PreCopyCallBack` | 0 | 1 | — |
| `PreCreateCallBack` | 0 | 1 | — |
| `PreUpdateCallBack` | 0 | 1 | — |
| `SecretCallBack` | 1 | 1 | `checkSecret(Collection)` |
| `ValidateCallBack` | 0 | 1 | — |
| `EntityLogFilter` | 1 | 1 | `ignoreLog(String)` |
| `AppInfoService` | 10 | 10 | `getAppName()`, `getHostAppName()`, `getAppVersion()`, `getCaption()`, `getSourceType()` …+5 |
| `UdcModuleBeanHandler` | 3 | 3 | `getAppType()`, `getBeanObject(String, String)`, `getClass(String, String)` |
| `BaseCurdService` | 0 | 35 | — |
| `BaseService` | 1 | 3 | `getEntityClass()` |
| `DataTransferService` | 1 | 1 | `importEntityInitData(ExcelImportTransDto)` |
| `QueryService` | 0 | 6 | — |
| `UpdateService` | 0 | 15 | — |
| `EventHelper` | 3 | 3 | `beforeEvent(EventContainer)`, `afterEvent(EventContainer)`, `transactionSuccessEvent(EventContainer)` |
| `OperateListener` | 1 | 1 | `onOperate(OperateContext)` |
| `AppStartUpProcessor` | 0 | 7 | — |
| `DataProcessor` | 2 | 2 | `dataProcess(OperateContext)`, `flowProcess(OperateContext)` |
| `DataVisitor` | 2 | 3 | `match(OperateContext)`, `visit(OperateContext)` |
| `ModuleEnhance` | 0 | 0 | — |
| `ModuleEnhanceFilter` | 0 | 0 | — |
| `MqConstant` | 0 | 1 | — |
| `MessageConsumer` | 10 | 10 | `start()`, `stop()`, `subscribe(String, Object, Method)`, `unSubscribe(String, Object)`, `dynamicSubscribe(String, Class, String)` …+5 |
| `MessageListener` | 2 | 2 | `topic()`, `broadcast()` |
| `MessageListener` | 14 | 14 | `onMessage(MessageDto)`, `getTopic()`, `setTopic(String)`, `getMethodWrapper()`, `getProcessClassName()` …+9 |
| `DelayTopic` | 0 | 0 | — |
| `AdvancedMessageProducer` | 3 | 3 | `send(MessageDto)`, `sendBatch(List)`, `sendDirectOneTime(MessageDto)` |
| `MessageProducer` | 6 | 6 | `isAvailable()`, `send(BaseMessage)`, `send(List)`, `sendDirectOneTime(BaseMessage)`, `sendDirectOneTimeReMsgId(BaseMessage)` …+1 |
| `MQMessageSpi` | 0 | 4 | — |
| `BusDynamicSubscribeDao` | 0 | 0 | — |
| `DynamicSubscribeDao` | 0 | 0 | — |
| `MQMessageDao` | 0 | 0 | — |
| `BaseMybatisDao` | 0 | 16 | — |
| `DataPermissionCheck` | 1 | 1 | `check(String)` |
| `CountSql` | 1 | 1 | `value()` |
| `DatabaseDialect` | 2 | 2 | `pageSql(PageInfo, String)`, `getDatabaseType()` |
| `AllInOneBaseDao` | 41 | 41 | `create(T)`, `createBatch(List)`, `update(T)`, `versionNoUpdateIgnoreVersion(T)`, `updateColumns(T, Set)` …+36 |
| `AllInOneBaseMybatisDao` | 0 | 0 | — |
| `AllInOneCreateBatchMapper` | 1 | 1 | `inOneCreateBatchInternal(List)` |
| `AllInOneCreateMapper` | 1 | 1 | `inOneCreate(Object)` |
| `AllInOneDeleteByComplexConditionMapper` | 1 | 1 | `inOneDeleteByComplexConditions(Map, Object>)` |
| `AllInOneDeleteByConditionMapper` | 1 | 1 | `inOneDeleteByConditions(Map, Object>)` |
| `AllInOneDeleteByDynamicConditionMapper` | 1 | 1 | `inOneDeleteByDynamicConditions(Map, Object>)` |
| `AllInOneDeleteByIdMapper` | 2 | 2 | `inOneDeleteById(Long)`, `inOneDeleteByIds(List)` |
| `AllInOneSelectByComplexConditionMapper` | 3 | 3 | `inOneSelectCountByComplexConditions(Map, Object>)`, `inOneSelectListByComplexConditions(LinkedHashMap, Object>, Sort)`, `inOneSelectPageByComplexConditions(PageInfo, LinkedHashMap, Object>, Sort)` |
| `AllInOneSelectByConditionMapper` | 7 | 7 | `inOneSelectCountByConditions(Map, Object>)`, `inOneSelectListByConditions(Map, Object>, Sort)`, `inOneSelectListPropertiesByConditions(String[], Map, Object>, Sort)`, `inOneSelectListExcludeByConditions(String[], Map, Object>, Sort)`, `inOneSelectPageByConditions(PageInfo, Map, Object>, Sort)` …+2 |
| `AllInOneSelectByDynamicConditionMapper` | 3 | 3 | `inOneSelectCountByDynamicConditions(LinkedHashMap, Object>)`, `inOneSelectListByDynamicConditions(LinkedHashMap, Object>, Sort)`, `inOneSelectPageByDynamicConditions(PageInfo, LinkedHashMap, Object>, Sort)` |
| `AllInOneSelectByIdMapper` | 2 | 2 | `inOneSelectById(Long)`, `inOneSelectByIds(List)` |
| `AllInOneSelectFuncByComplexConditionMapper` | 1 | 1 | `inOneSelectListFuncByComplexConditions(LinkedHashMap, Object>, Sort, String, List)` |
| `AllInOneSelectFuncByDynamicConditionMapper` | 1 | 1 | `inOneSelectListFuncByDynamicConditions(LinkedHashMap, Object>, Sort, String, List)` |
| `AllInOneUpdateBatchMapper` | 2 | 2 | `inOneUpdateBatchInternal(List)`, `inOneVersionNoUpdateBatchInternalIgnoreVersion(List)` |
| `AllInOneUpdateIgnoreVersionMapper` | 2 | 2 | `inOneUpdateIgnoreVersion(Object)`, `inOneVersionNoUpdateIgnoreVersion(Object)` |
| `AllInOneUpdateMapper` | 2 | 2 | `inOneUpdate(Object)`, `inOneUpdateColumns(Object, Set)` |
| `CreateBatchMapper` | 2 | 2 | `createBatchInternal(List)`, `createBatchInternalIgnoreTime(List)` |
| `CreateMapper` | 2 | 2 | `create(T)`, `createIgnoreTime(T)` |
| `DeleteByComplexConditionMapper` | 1 | 1 | `deleteByComplexConditions(Map, Object>)` |
| `DeleteByConditionMapper` | 1 | 1 | `deleteByConditions(Map, Object>)` |
| `DeleteByDynamicConditionMapper` | 1 | 1 | `deleteByDynamicConditions(Map, Object>)` |
| `DeleteByIdMapper` | 2 | 2 | `deleteById(Long)`, `deleteByIdsInternal(List)` |
| `DeleteByWrapperMapper` | 1 | 1 | `deleteByWrapper(Wrapper)` |
| `SelectByComplexConditionMapper` | 3 | 3 | `selectCountByComplexConditions(Map, Object>)`, `selectListByComplexConditions(LinkedHashMap, Object>, Sort)`, `selectPageByComplexConditions(PageInfo, LinkedHashMap, Object>, Sort)` |
| `SelectByConditionMapper` | 7 | 7 | `selectCountByConditions(Map, Object>)`, `selectListByConditions(Map, Object>, Sort)`, `selectListPropertiesByConditions(String[], Map, Object>, Sort)`, `selectListExcludeByConditions(String[], Map, Object>, Sort)`, `selectPageByConditions(PageInfo, Map, Object>, Sort)` …+2 |
| `SelectByDynamicConditionMapper` | 3 | 3 | `selectCountByDynamicConditions(LinkedHashMap, Object>)`, `selectListByDynamicConditions(LinkedHashMap, Object>, Sort)`, `selectPageByDynamicConditions(PageInfo, LinkedHashMap, Object>, Sort)` |
| `SelectByIdMapper` | 2 | 2 | `selectById(Long)`, `selectByIds(List)` |
| `SelectByWrapperMapper` | 3 | 3 | `selectCountByWrapper(Wrapper)`, `selectListByWrapper(Wrapper)`, `selectPageByWrapper(PageInfo, Wrapper)` |
| `SelectFuncByComplexConditionMapper` | 1 | 1 | `selectListFuncByComplexConditions(LinkedHashMap, Object>, Sort, String, List)` |
| `SelectFuncByConditionMapper` | 1 | 1 | `selectFuncByConditions(Map, Object>, Sort, String, List)` |
| `SelectFuncByDynamicConditionMapper` | 1 | 1 | `selectListFuncByDynamicConditions(LinkedHashMap, Object>, Sort, String, List)` |
| `UpdateBatchIgnoreVersionMapper` | 2 | 2 | `updateBatchInternalIgnoreVersion(List)`, `versionNoUpdateBatchInternalIgnoreVersion(List)` |
| `UpdateBatchMapper` | 3 | 3 | `updateBatchInternal(List)`, `updateBatchInternalIgnoreTime(List)`, `updateColumnsBatch(List, Set)` |
| `UpdateByConditionMapper` | 1 | 1 | `updateByConditions(T, Set, Map, Object>)` |
| `UpdateByWrapperMapper` | 2 | 2 | `updateByWrapper(T, Object)`, `updateByWrapperSelective(T, Object)` |
| `UpdateIgnoreVersionMapper` | 2 | 2 | `updateIgnoreVersion(T)`, `versionNoUpdateIgnoreVersion(T)` |
| `UpdateMapper` | 4 | 4 | `update(T)`, `updateIgnoreTime(T)`, `updateColumns(T, Set)`, `updateColumnsIgnoreVersion(T, Set)` |
| `SeeyonSensitive` | 1 | 1 | `sensitiveProcess(String)` |
| `DateParser` | 0 | 1 | — |
| `ConfigAutoRefresh` | 1 | 1 | `autoRefreshed()` |
| `AppChangeProcess` | 1 | 2 | `process()` |
| `ConfigChangeProcess` | 1 | 1 | `process(String)` |
| `ConfigServiceSPI` | 4 | 9 | `getAppConfigStr()`, `getGlobalConfigStr()`, `getConfigStr(String)`, `getEngineName()` |
| `RegisterServiceSPI` | 9 | 10 | `registerInstance()`, `registerInstance(AppInstanceDto)`, `deregisterInstance()`, `deregisterInstance(String)`, `getInstances(String)` …+4 |
| `ExtendComponentManager` | 0 | 9 | — |
| `OpinionAdminService` | 3 | 3 | `match(String)`, `modifyOpinion(OpinionAdminModifyDto)`, `deleteOpinion(OpinionAdminDeleteDto)` |
| `OpinionService` | 42 | 56 | `create(OpinionDto)`, `update(OpinionDto)`, `updateSilent(OpinionDto)`, `updateBatch(List, Set)`, `selectInformBeforeSend(Long, Long)` …+37 |
| `ExtraUpdateMapper` | 1 | 1 | `updateWithWrapper(ExtraUpdateMapper$ExtraUpdateWrapper)` |
| `OpinionDao` | 0 | 0 | — |
| `PraiseDao` | 0 | 0 | — |
| `CtpParameterDao` | 0 | 0 | — |
| `CtpParameterDefinitionDao` | 0 | 0 | — |
| `MetricMethodCounter` | 2 | 2 | `metricType()`, `metricName()` |
| `MetricMethodGauge` | 2 | 2 | `metricType()`, `metricName()` |
| `MetricMethodHistogram` | 2 | 2 | `metricType()`, `metricName()` |
| `MetricMethodSummary` | 2 | 2 | `metricType()`, `metricName()` |
| `AlertRule` | 1 | 1 | `in(List)` |
| `AlertTrigger` | 1 | 1 | `fireAlert(AlertSatisfied)` |
| `CustomerProxyAppService` | 2 | 7 | `invokeAppService(SingleRequest)`, `reliableInvokeAppService(SingleRequest)` |
| `ParamEscapeService` | 0 | 2 | — |
| `ProxyInvokeInfoDao` | 0 | 0 | — |
| `ReliableInvokeInfoDao` | 0 | 0 | — |
| `CtpQrCodeRuleUdcAppService` | 3 | 3 | `getRuleListByAppIdAndFullNames(SingleRequest)`, `getRuleListByAppIdAndFieldCodes(SingleRequest)`, `getRuleListByAppId(SingleRequest)` |
| `CtpQrCodeDao` | 0 | 0 | — |
| `CtpQrCodeRuleDao` | 0 | 0 | — |
| `CtpQrCodeService` | 0 | 3 | — |
| `CtpSchedule` | 13 | 13 | `systemTenant()`, `isSingle()`, `jobName()`, `cron()`, `description()` …+8 |
| `SeeyonJob` | 1 | 1 | `exec()` |
| `EveryConstant` | 0 | 0 | — |
| `CtpJobCronDao` | 0 | 0 | — |
| `CtpJobInfoDao` | 0 | 0 | — |
| `CtpJobLogDao` | 1 | 1 | `selectJobCount()` |
| `CtpJobSimpleDao` | 0 | 0 | — |
| `ScheduleErrorCode` | 0 | 0 | — |
| `CtpSentinel` | 1 | 1 | `fallback()` |
| `SerialConditionDao` | 0 | 0 | — |
| `SerialCurrentDao` | 1 | 1 | `updateValue(String, Long, Date, Long)` |
| `SerialHistoryDao` | 0 | 0 | — |
| `SerialRangeDao` | 4 | 4 | `deleteValue(String, Long)`, `deleteRange(String)`, `incrementStartValue(String, Long, Long, Date)`, `exist(String, Long)` |
| `SerialSchemeDao` | 1 | 1 | `getMaxSortNumByAppId(String)` |
| `SerialSectionDao` | 1 | 1 | `updateSerialCurrent(Long, Date, Long)` |
| `CtpOBSChecker` | 1 | 1 | `check(CtpOBSInfoDto)` |
| `ShardingAppServiceInterface` | 6 | 6 | `createTenantSharding(SingleRequest)`, `batchCreateTenantSharding(SingleRequest)`, `updateTenantSharding(SingleRequest)`, `deleteTenantShardingByIds(SingleRequest)`, `deleteTenantShardingById(SingleRequest)` …+1 |
| `CtpDBInfoDao` | 0 | 0 | — |
| `CtpOBSInfoDao` | 0 | 0 | — |
| `CtpTenantShardingDao` | 0 | 0 | — |
| `ShortLinkConstant` | 0 | 0 | — |
| `CtpShortLinkDao` | 0 | 0 | — |
| `SpiArtifactService` | 1 | 1 | `download(ArtifactInfo)` |
| `IsolatorExecutor` | 5 | 5 | `isolatorName()`, `coreSize()`, `maxSize()`, `queueSize()`, `rejectionPolicy()` |
| `AppDraftAppService` | 5 | 5 | `createOrUpdate(SingleRequest)`, `exist(SingleRequest)`, `select(SingleRequest)`, `delete(SingleRequest)`, `deleteAll(SingleRequest)` |
| `DeployNoticeService` | 0 | 1 | — |
| `FormAppService` | 2 | 2 | `loadForm(SingleRequest)`, `getHostAppDepends(SingleRequest)` |
| `GraphqlProxyAppService` | 2 | 2 | `doGraphQL(SingleRequest)`, `doRest(SingleRequest)` |
| `UdcBpmProcessService` | 8 | 8 | `validUpdateFilterData(SingleRequest)`, `validCreateFilterData(SingleRequest)`, `processBpmApproval(SingleRequest)`, `processBpmStop(SingleRequest)`, `processBpmCancel(SingleRequest)` …+3 |
| `UdcSerialConfigAppService` | 6 | 6 | `update(SingleRequest)`, `selectListByConditions(ListRequest)`, `selectEntityList(SingleRequest)`, `selectEntityBySerialId(ListRequest)`, `refreshHistoricalData(SingleRequest)` …+1 |
| `UseUdcAppLog` | 3 | 3 | `logModule()`, `appName()`, `signatureName()` |
| `AppDraftDao` | 0 | 0 | — |
| `AttachmentTemplateRtEntityDao` | 0 | 0 | — |
| `AttributeSnapshotDao` | 0 | 0 | — |
| `CustomApplicationDao` | 0 | 0 | — |
| `IdToKeyMapEntityDao` | 0 | 0 | — |
| `UdcAppLogDao` | 0 | 0 | — |
| `UdcDataFlowLogDao` | 0 | 0 | — |
| `UdcDeductionLogDao` | 0 | 0 | — |
| `UdcEntityMonitorLogDao` | 0 | 0 | — |
| `UdcRtPageLogDao` | 0 | 0 | — |
| `UdcSerialConfigDao` | 0 | 0 | — |
| `FormHandler` | 1 | 1 | `dataProcess(FormParamDto)` |
| `SupportService` | 3 | 3 | `getFunctionName()`, `getParameterSize()`, `calculate(List)` |
| `EventPublisher` | 1 | 1 | `publish(String, T, EventPublisher$EventPhase)` |
| `Upgrade` | 1 | 1 | `version()` |
| `CtpUpgrade` | 1 | 1 | `upgrade()` |
| `AntiReCommit` | 2 | 2 | `name()`, `validate()` |
| `CsrfToken` | 3 | 3 | `getHeaderName()`, `getParameterName()`, `getToken()` |
| `CsrfTokenRepository` | 3 | 3 | `generateToken(HttpServletRequest)`, `saveToken(CsrfToken, HttpServletRequest, HttpServletResponse)`, `loadToken(HttpServletRequest)` |
| `RequestMatcher` | 1 | 1 | `matches(HttpServletRequest)` |
| `AccessAuditLgDao` | 0 | 0 | — |
| `ReceiveProcessService` | 1 | 1 | `receiveMessage(TextMessage)` |
| `Constants` | 0 | 0 | — |
| `SysOpsDubboApi` | 2 | 2 | `dubboExport()`, `dubboUnExport()` |
| `DeadLoopFunction` | 1 | 1 | `apply()` |
| `AsyncTrace` | 0 | 0 | — |
| `IgnoredException` | 0 | 0 | — |
| `Trace` | 1 | 1 | `operationName()` |
| `TraceTag` | 2 | 2 | `key()`, `value()` |
| `TraceTags` | 1 | 1 | `value()` |
| `TypeConverter` | 4 | 4 | `getTargetType()`, `getSupportedSourceTypes()`, `convert(Object, Object>, Object, T>)`, `convert(Object, T>)` |
| `TypeConverterManager` | 11 | 11 | `getTypeConverter(Class)`, `getTypeConverter(Class, Class)`, `register(S>, Class, T>)`, `register(TypeConverter)`, `unregister(Class, Class)` …+6 |
| `AutoClearable` | 0 | 0 | — |
| `FinalizableReference` | 1 | 1 | `finalizeReferent()` |
| `SeeyonCache` | 8 | 8 | `size()`, `isEmpty()`, `containsKey(K)`, `get(K)`, `put(K, V)` …+3 |
| `ExcelDataHandler` | 1 | 1 | `handle(T)` |
| `ExcelColumn` | 2 | 2 | `value()`, `width()` |
| `ExcelColumnWidth` | 1 | 1 | `value()` |
| `ExcelContentFontStyle` | 7 | 7 | `fontName()`, `fontHeightInPoints()`, `italic()`, `strikeout()`, `color()` …+2 |
| `ExcelContentStyle` | 17 | 17 | `dataFormat()`, `hidden()`, `locked()`, `wrapped()`, `verticalAlignment()` …+12 |
| `ExcelHeadFontStyle` | 7 | 7 | `fontName()`, `fontHeightInPoints()`, `italic()`, `strikeout()`, `color()` …+2 |
| `ExcelHeadStyle` | 17 | 17 | `dataFormat()`, `hidden()`, `locked()`, `wrapped()`, `verticalAlignment()` …+12 |
| `IdentifierGenerator` | 3 | 3 | `generateLong()`, `generateString()`, `analyze(Long)` |

## com.seeyon.udc（274）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `PluginDefinition` | 2 | 8 | `getName()`, `getCode()` |
| `AppCollaborationAppService` | 5 | 5 | `selectCollaborativeAppNames()`, `selectCollaborativeGuid()`, `handoverApp(SingleRequest)`, `batchHandoverApp(SingleRequest)`, `selectAppMemberInfoListByAppIdList(SingleRequest)` |
| `ApplicationAppService` | 52 | 52 | `create(SingleRequest)`, `selectPageByConditions(PageRequest)`, `selectAppPageByConditions(PageRequest)`, `selectAppPageByConditionsWithVersion(PageRequest)`, `selectAppPageByGuid(PageRequest)` …+47 |
| `ApplicationManagerAppService` | 33 | 53 | `create(SingleRequest)`, `createOnlyPageApplication(SingleRequest)`, `createNewLayoutAfterCall(SingleRequest)`, `copyOnlyPageApp(SingleRequest)`, `upgradeOnlyPageApplication(SingleRequest)` …+28 |
| `ApplicationShelfService` | 1 | 2 | `updateStateAfterAppShelf(ApplicationDto)` |
| `AsyncAppService` | 7 | 7 | `createLayoutApplicationAsync(SingleRequest)`, `createOnlyPageApplicationAsync(SingleRequest)`, `upgradeOnlyPageApplicationAsync(SingleRequest)`, `copyLayoutAppAsync(SingleRequest)`, `copyOnlyPageAppAsync(SingleRequest)` …+2 |
| `AttributeAppService` | 15 | 15 | `create(SingleRequest)`, `createBatch(SingleRequest)`, `createBatch4System(SingleRequest)`, `update(SingleRequest)`, `updateBatch(SingleRequest)` …+10 |
| `AttributeGroupAppService` | 7 | 7 | `create(SingleRequest)`, `update(SingleRequest)`, `cancel(SingleRequest)`, `remove(SingleRequest)`, `swap(SingleRequest)` …+2 |
| `AttributeSetAppService` | 13 | 13 | `create(SingleRequest)`, `createBatch(SingleRequest)`, `deleteById(SingleRequest)`, `deleteByIds(SingleRequest)`, `update(SingleRequest)` …+8 |
| `ConsistenceDetectionAppService` | 4 | 4 | `updateDetection(BaseEntity>>, SingleRequest, SingleRequest)`, `updateDetection4Dto(BaseEntity>>, SingleRequest, BaseTraceableDto>>)`, `selectDetectionListByAppId(SingleRequest)`, `deleteDetection(BaseEntity>>, SingleRequest, BaseTraceableDto>>)` |
| `DataTransferObjectAppService` | 22 | 22 | `create(SingleRequest)`, `createDtoWithAttrs(SingleRequest)`, `update(SingleRequest)`, `updateDtoWithAttrs(SingleRequest)`, `deleteById(SingleRequest)` …+17 |
| `DataTypeAppService` | 7 | 7 | `getAll()`, `selectBaseDataTypes()`, `selectParameterDataTypes()`, `selectDataTypeByName(SingleRequest)`, `selectDataTypeByAppId(SingleRequest)` …+2 |
| `DeployBeforeService` | 1 | 1 | `handle(AppContext)` |
| `DeployFinishService` | 0 | 1 | — |
| `DesignMetadataQueryAppService` | 49 | 49 | `selectServiceMetadata(SingleRequest)`, `selectEntityMetadata(SingleRequest)`, `selectEntityMetadataExcludeBoot(SingleRequest)`, `selectEntityMetadataByFullName(SingleRequest)`, `selectEntityMetadataByFullNames(SingleRequest)` …+44 |
| `DtoAttributeAppService` | 8 | 8 | `create(SingleRequest)`, `createBatch(SingleRequest)`, `update(SingleRequest)`, `deleteById(SingleRequest)`, `deleteByIds(SingleRequest)` …+3 |
| `EntityAppService` | 18 | 18 | `create(SingleRequest)`, `update(SingleRequest)`, `deleteById(SingleRequest)`, `deleteByIds(SingleRequest)`, `selectById(SingleRequest)` …+13 |
| `EntityGroupAppService` | 7 | 7 | `create(SingleRequest)`, `update(SingleRequest)`, `updateBatch(SingleRequest)`, `deleteById(SingleRequest)`, `deleteByIds(SingleRequest)` …+2 |
| `EntityOpenApiAppService` | 1 | 1 | `selectOpenApiData(SingleRequest)` |
| `EntityPresetAppService` | 6 | 6 | `selectPresetByEntityId(SingleRequest)`, `uploadInItData(SingleRequest)`, `create(SingleRequest)`, `update(SingleRequest)`, `createDefaultExcelTemplate(SingleRequest)` …+1 |
| `EventAppService` | 9 | 9 | `create(SingleRequest)`, `selectPageByConditions(PageRequest)`, `selectListByConditions(ListRequest)`, `selectById(SingleRequest)`, `deleteById(SingleRequest)` …+4 |
| `EventWithDataAppService` | 5 | 5 | `createWithEventData(SingleRequest)`, `updateWithEventData(SingleRequest)`, `selectWithEventData(SingleRequest)`, `selectListWithDataByConditions(ListRequest)`, `selectListWithDataByTerm(SingleRequest, SingleRequest, SingleRequest)` |
| `ExprConsistencyValidator` | 1 | 1 | `validateConsistency(ConsistencyValidateConfig)` |
| `ExtendAppOperationAuthCheck` | 1 | 1 | `hasRight(ExtendAppAuthCheckInfoDto)` |
| `FeatureAppService` | 3 | 3 | `list(SingleRequest)`, `listSystemAttributeNames(SingleRequest)`, `upgrade(SingleRequest)` |
| `IndexAppService` | 7 | 7 | `create(SingleRequest)`, `deleteById(SingleRequest)`, `deleteByIds(SingleRequest)`, `update(SingleRequest)`, `selectById(SingleRequest)` …+2 |
| `InnerEntityAppService` | 4 | 4 | `selectEntitiesByEntityId4Tree(SingleRequest)`, `copyEntity(SingleRequest)`, `attributeTransfer(SingleRequest)`, `selectMasterEntityCount(SingleRequest)` |
| `LastVersionMetadataManagerService` | 3 | 5 | `prepareLastVersionAfterDeployed(ApplicationDto)`, `fetchLastVersionMetadataFromDbIfNotExist(LastVersionMetadataSearchDto)`, `getModule()` |
| `LateralAuthChecker` | 2 | 2 | `check(Supplier)`, `checkByAppName(Supplier)` |
| `MetadataHandleService` | 1 | 1 | `handle(AppContext)` |
| `MicroFlowInfoAppService` | 2 | 2 | `findCallConnectorAppService(SingleRequest)`, `findCallIntegrationAppService(SingleRequest)` |
| `MicroFlowUpgradeAppService` | 6 | 6 | `upgradeThirdEntity(SingleRequest)`, `upgradeThirdServiceByNames(SingleRequest)`, `batchUpgradeThirdEntity()`, `upgradeExtendFullNameByAppId(SingleRequest)`, `upgradeCallExtendAppService(SingleRequest)` …+1 |
| `PageMetadataQuery4SfAppService` | 1 | 1 | `selectAppMetaDataByAppName(SingleRequest)` |
| `PageProcessEventAppService` | 1 | 1 | `selectListByCondition(SingleRequest)` |
| `ParameterAppService` | 7 | 7 | `create(SingleRequest)`, `update(SingleRequest)`, `deleteById(SingleRequest)`, `deleteByIds(SingleRequest)`, `selectById(SingleRequest)` …+2 |
| `PluginAttributeAppService` | 1 | 1 | `createBatch(SingleRequest)` |
| `PluginEntityAppService` | 2 | 2 | `create(SingleRequest)`, `update(SingleRequest)` |
| `PluginPageInfoAppService` | 5 | 5 | `createDefaultFilterPlanContentByEntityId(SingleRequest)`, `createDefaultFilterPlanContentByEntity(SingleRequest)`, `parsePageResource(SingleRequest, Object>>)`, `getResourceByCondition(SingleRequest)`, `getResource4UserCenter(SingleRequest)` |
| `PluginReferConfigGroupAppService` | 3 | 3 | `createDefaultRefer(SingleRequest)`, `updateDefaultRefer(SingleRequest)`, `deleteDefaultRefer(SingleRequest)` |
| `PreSetAttributeCapacityAppService` | 2 | 2 | `getAllPreSetAttributeCapacity(SingleRequest)`, `getPreSetAttributeCapacity(SingleRequest)` |
| `PublishStateAppService` | 1 | 1 | `updateState(SingleRequest)` |
| `ReferConfigAppService` | 8 | 8 | `create(SingleRequest)`, `createOrUpdate(SingleRequest)`, `update(SingleRequest)`, `deleteById(SingleRequest)`, `selectById(SingleRequest)` …+3 |
| `ReferConfigGroupAppService` | 4 | 4 | `createConfigInfo(SingleRequest)`, `updateConfigInfo(SingleRequest)`, `deleteById(SingleRequest)`, `selectListByConditions(ListRequest)` |
| `ResourceAppService` | 6 | 6 | `registerRole(SingleRequest)`, `registerResourceBatch(SingleRequest)`, `registerResource(SingleRequest)`, `deleteByRef(SingleRequest)`, `deleteByPage(SingleRequest)` …+1 |
| `ScalabilityAppService` | 6 | 6 | `create(SingleRequest)`, `update(SingleRequest)`, `deleteById(SingleRequest)`, `deleteByIds(SingleRequest)`, `selectById(SingleRequest)` …+1 |
| `ScalabilityOptionAppService` | 7 | 7 | `create(SingleRequest)`, `update(SingleRequest)`, `deleteById(SingleRequest)`, `selectById(SingleRequest)`, `selectByAppId(SingleRequest)` …+2 |
| `StereotypeAllAppService` | 2 | 2 | `getAll()`, `get(String)` |
| `StereotypeAppService` | 2 | 2 | `list(SingleRequest)`, `upgrade(SingleRequest)` |
| `UdcBpmAppService` | 1 | 1 | `selectDefaultLayoutAppName()` |
| `UdcCtpEnumAppService` | 16 | 16 | `selectCategoryByAppGuid(SingleRequest)`, `selectCategoryAndEnum(SingleRequest)`, `selectCtpEnum(SingleRequest)`, `selectCtpEnumByIds(SingleRequest)`, `selectParentByCode(SingleRequest)` …+11 |
| `UdcCtpEnumProxyAppService` | 6 | 6 | `selectOneByIdAndApp(SingleRequest, Object>>)`, `selectByEnumCodeAndAppGuid(SingleRequest, Object>>)`, `selectByEnumCodesAndAppGuid(SingleRequest, Object>>)`, `selectCascadeTreeByEnumCode(SingleRequest, Object>>)`, `selectByEnumItemByDependentApp(SingleRequest, Object>>)` …+1 |
| `UdcDataBaseSqlGenerator` | 3 | 5 | `getChangeList(ApplicationDto, AppDbInfoDto, List)`, `getDropChangeList(ApplicationDto, AppDbInfoDto, List)`, `filterSet()` |
| `UdcEnumAppService` | 8 | 8 | `create(SingleRequest)`, `selectPageByConditions(PageRequest)`, `selectListByConditions(ListRequest)`, `selectById(SingleRequest)`, `deleteById(SingleRequest)` …+3 |
| `UdcEnumCategoryAppService` | 8 | 8 | `create(SingleRequest)`, `selectPageByConditions(PageRequest)`, `selectListByConditions(ListRequest)`, `selectById(SingleRequest)`, `deleteById(SingleRequest)` …+3 |
| `UdcEnumItemAppService` | 11 | 11 | `create(SingleRequest)`, `selectPageByConditions(PageRequest)`, `selectListByConditions(ListRequest)`, `selectById(SingleRequest)`, `selectByEnumId(SingleRequest)` …+6 |
| `UdcFunctionAppService` | 4 | 4 | `createFunctionRefer(SingleRequest, Object>>)`, `deletePortalFunctionRefer(SingleRequest, Object>>)`, `updateFunctionRefer(SingleRequest, Object>>)`, `findMenuDefaultPage(SingleRequest)` |
| `UdcLateralAuthCheckAppService` | 1 | 1 | `check(SingleRequest)` |
| `UdcMetaDataAppService` | 33 | 33 | `selectAppMetaData4PageCode(SingleRequest)`, `selectAvailableUpgradeAppMetadataById(SingleRequest)`, `selectPageAvailableAppMetaDataByCondition(PageRequest)`, `selectPageAvailableAppMultiVersionMetaDataByCondition(PageRequest)`, `selectReferMetaDataByEntity(SingleRequest)` …+28 |
| `UdcPageLayoutPluginAppService` | 3 | 3 | `filterDependentApplicationList(SingleRequest)`, `allowDependentLayoutApplicationList(SingleRequest)`, `filterApplicationFeature(SingleRequest)` |
| `UdcPortalPortletAppService` | 7 | 7 | `createCategory(SingleRequest)`, `updateCategory(SingleRequest)`, `deleteCategoryByIds(SingleRequest)`, `createOrUpdatePortlet(SingleRequest)`, `deletePortletByIds(SingleRequest)` …+2 |
| `UdcPortalSetAppService` | 1 | 1 | `createPcTemplateData(SingleRequest)` |
| `UdcPortalSpaceAppService` | 1 | 1 | `selectDesignSpaceList(SingleRequest)` |
| `UdcSandBoxAppService` | 6 | 6 | `search(PageDtoRequest)`, `searchDetails(PageDtoRequest)`, `searchDetails4FlowLog(SingleRequest)`, `searchPageLog(PageDtoRequest)`, `searchPageLogNonMetadata(PageDtoRequest)` …+1 |
| `UdcSerialSchemeAppService` | 4 | 5 | `selectSerialScheme(SingleRequest)`, `selectSerialSchemeById(SingleRequest)`, `selectSerialRange(SingleRequest)`, `createEasyScheme(SingleRequest)` |
| `AttachmentTemplateDao` | 0 | 0 | — |
| `AuthCheck` | 3 | 3 | `check(AuthOperationType, UdcBaseEntityDto)`, `check(AuthOperationType, Long)`, `getModelName()` |
| `AuthModel` | 1 | 1 | `name()` |
| `AuthOperation` | 1 | 1 | `operationType()` |
| `TypeUpdateAuthChecker` | 2 | 3 | `matchTypeChangeRule(AttributeDto, AttributeDto)`, `doAttributeFieldChangeCheck(AttributeDto, AttributeDto, AttributeUpdateAuthManager, StringBuilder)` |
| `ApplicationInnerReference` | 3 | 3 | `getEntityBackwardRefPages(Long)`, `getMicroFlowBackwardRefPages(Long)`, `getDataflowBackwardRefPages(Long)` |
| `DataFlowCodeService` | 1 | 1 | `deployManuallyMappingCustomDto(CodeContext, Map, EntityAutoCodeDto>, Map, UdcDtoMetadataDto>)` |
| `DependencyAnalysisService` | 1 | 1 | `analysis(CodeContext, Collection, Set)` |
| `TypeChangeSqlResolver` | 2 | 4 | `match(AttributeDto, AttributeDto, CodeContext)`, `registrySql(AttributeDto, AttributeDto, EntityDto, CodeContext)` |
| `MetaDataKey` | 0 | 0 | — |
| `UdcMetaDataHandler` | 0 | 0 | — |
| `SplitImportRecordDao` | 0 | 0 | — |
| `BaseNode` | 18 | 18 | `getNodeId()`, `setNodeId(String)`, `getNodePath()`, `setNodePath(String)`, `getType()` …+13 |
| `BaseTrigger` | 18 | 18 | `getId()`, `setId(Long)`, `getNodeId()`, `setNodeId(String)`, `getCaption()` …+13 |
| `LazyCacheAdapter` | 2 | 3 | `getArgs()`, `handle(I)` |
| `AppOpsAuth` | 2 | 2 | `type()`, `appId()` |
| `AppCollaborationEntityDao` | 0 | 0 | — |
| `ImportUpgradeConst` | 0 | 0 | — |
| `Schemable` | 1 | 1 | `getName()` |
| `TypeMapping` | 3 | 3 | `sourceType()`, `targetType()`, `isFormulaResult()` |
| `UdcTreeQueryService` | 1 | 1 | `selectTreeData(SingleRequest)` |
| `AppFeature` | 4 | 4 | `getTypeEnum()`, `getName()`, `getCaptionI18n()`, `isDynamicService()` |
| `AppFeatureHandler` | 14 | 17 | `getHostAppName(ApplicationDto)`, `getAppUrl(ApplicationDto)`, `getAppDbInfo(ApplicationDto)`, `getAppFeatureByAppType(ApplicationFeatureEnum)`, `getVersion4JavaPackage(ApplicationDto)` …+9 |
| `ApplicationInnerReference` | 14 | 14 | `getEntityBackwardRefPages(String)`, `getEntityBackwardRefPageUrls(String, PageUrlTypeEnum)`, `getMicroFlowBackwardRefPages(Long)`, `getDataflowBackwardRefPages(Long)`, `getControlRestUrls(String)` …+9 |
| `CodeExecutor` | 2 | 2 | `execute(ApplicationDto, CodeParam)`, `executeSegment(ApplicationDto, CodeParam)` |
| `CodeTask` | 1 | 1 | `code(CodeContext)` |
| `Recoverable` | 1 | 1 | `recover()` |
| `ConfigurableCodeContext` | 5 | 10 | `getCodeParam()`, `setCodeParam(CodeParam)`, `registerUpdateChange(Change)`, `registerDmlFileInfo(List)`, `registerStaticFileInfo(List)` |
| `CodeContext` | 12 | 13 | `getAutoCodeProperties()`, `getVersionControl()`, `getBasePackage()`, `getAppName4Package()`, `getAppName()` …+7 |
| `CodeContextPostProcess` | 0 | 2 | — |
| `Lifecycle` | 3 | 3 | `start()`, `stop()`, `isRunning()` |
| `DbCodeHandler` | 1 | 2 | `getDefaultValueString(UdcDataType, String)` |
| `SqlResolver` | 3 | 3 | `outputInitSql(CodeContext, List)`, `outputUpdateSql(CodeContext, List)`, `outputDmlFile(CodeContext, List)` |
| `CodeParamInterceptor` | 1 | 1 | `filter(ApplicationDto, CodeParam)` |
| `FileResolver` | 1 | 1 | `outputStaticFile(CodeContext, List)` |
| `I18nHandler` | 1 | 1 | `handle(T, I18nContext)` |
| `CodeContextAware` | 1 | 1 | `setCodeContext(CodeContext)` |
| `CommonSchemaKey` | 0 | 0 | — |
| `TenantDataFilter` | 1 | 1 | `filter(String, List)` |
| `TransportHandler` | 1 | 6 | `out(CodeContext)` |
| `ColiImportable` | 0 | 2 | — |
| `SplitHandler` | 1 | 4 | `getRelation(SplitContext)` |
| `ComparedSchema` | 1 | 1 | `value()` |
| `Compatible` | 1 | 1 | `compare(CodeContext, List, List)` |
| `SaveAsHandler` | 1 | 3 | `saveAs(TransportData)` |
| `Importable` | 1 | 11 | `in(TransportData)` |
| `Importer` | 2 | 2 | `source()`, `model()` |
| `AsyncRequestConst` | 0 | 0 | — |
| `ExclusivePermit` | 2 | 2 | `value()`, `sourceName()` |
| `CustomPlanPageFeatureHandler` | 0 | 2 | — |
| `TypeHelper` | 6 | 7 | `getDatabaseDataType(BaseUdcAttributeDto)`, `getJavaType(BaseUdcAttributeDto)`, `getLength(BaseUdcAttributeDto)`, `getDatabaseDataType(UdcAttributeMetaDataDto)`, `getJavaType(UdcAttributeMetaDataDto)` …+1 |
| `UdcDataType` | 20 | 39 | `getExtensionProperties()`, `getDefaultDataProperties()`, `getTypeHelper()`, `getFrontComponent()`, `getLength()` …+15 |
| `DeductionSearchMethodType` | 4 | 6 | `getName()`, `getCaption()`, `getOrder()`, `getDeductionSearchMethodTypeEnum()` |
| `AppContextListener` | 0 | 1 | — |
| `MappingMode` | 11 | 14 | `getName()`, `getCaption()`, `getMappingModeCategory()`, `getSupportOperationType()`, `getTargetDataTypes()` …+6 |
| `AppContext` | 1 | 4 | `getAppInfo()` |
| `AppDeployContext` | 1 | 15 | `getBaseProjectPath()` |
| `AppMetaDataContextPostProcess` | 1 | 1 | `postProcessAppMetaDataContext(AppContext)` |
| `ContextListener` | 2 | 2 | `onAdd(AppContext)`, `onRemove(AppContext)` |
| `LambdaMeta` | 2 | 2 | `getImplMethodName()`, `getInstantiatedClass()` |
| `UConsumer` | 0 | 0 | — |
| `UFunction` | 0 | 0 | — |
| `SchemaFilter` | 2 | 2 | `matches(String, String)`, `filter(SchemaInfo, SchemaInfo)` |
| `ImportUpgradeHandler` | 0 | 0 | — |
| `UpgradeMethod` | 3 | 3 | `sourceVersion()`, `targetVersion()`, `group()` |
| `Functor` | 1 | 1 | `map(Function, R>)` |
| `DateValidation` | 5 | 5 | `message()`, `groups()`, `payload()`, `minDate()`, `maxDate()` |
| `TimeValidation` | 5 | 5 | `message()`, `groups()`, `payload()`, `minTime()`, `maxTime()` |
| `AttrTypeMatch` | 4 | 4 | `message()`, `groups()`, `payload()`, `values()` |
| `AttributeExist` | 3 | 3 | `message()`, `groups()`, `payload()` |
| `EntityExist` | 3 | 3 | `message()`, `groups()`, `payload()` |
| `SchemaGenerator` | 1 | 1 | `generate(CompatibilityContext)` |
| `CompatibilityOutput` | 1 | 1 | `output(List, CompatibilityContext)` |
| `AppIdRef` | 2 | 2 | `obtainType()`, `index()` |
| `DataChangeAware` | 1 | 1 | `appIdRef()` |
| `CustomDataTypeDao` | 0 | 0 | — |
| `Condition` | 0 | 1 | — |
| `DeployRecordDao` | 0 | 0 | — |
| `ConsistenceDetection` | 3 | 3 | `getDomainObject()`, `delDetection(List, List)`, `updateDetection(List, List)` |
| `ConsistencyDetection` | 1 | 1 | `service()` |
| `DetectionMetadataRepository` | 3 | 3 | `getElements(Class)`, `getElements(Class, Long)`, `isAffected(Long)` |
| `DetectionTask` | 2 | 2 | `getDomainObjects()`, `detection(DetectionContext)` |
| `FrontDeployDetectionTask` | 1 | 1 | `detection(FrontDeployDetectionContext)` |
| `PartDetectionTask` | 14 | 18 | `getTargetDomainObject()`, `getSourceDomainObject()`, `setSelfIds(Set)`, `getSelfIds()`, `setSourceDeleteIds(Set)` …+9 |
| `DelDetection` | 4 | 4 | `ids()`, `domainObject()`, `serviceObject()`, `isDraft()` |
| `UpdateDetection` | 4 | 4 | `dtoList()`, `domainObject()`, `serviceObject()`, `isDraft()` |
| `DetectionContext` | 5 | 5 | `start()`, `stop(DetectionStatusEnum)`, `isRunning()`, `passDetection()`, `getDetectionMetadataRepository()` |
| `FrontDeployDetectionContext` | 5 | 5 | `getLastDeployTime()`, `getLastDeploySchemeInfoDto()`, `getDeployTerminalType()`, `getAppSchemaContext()`, `getAppSchemaMetadata(String)` |
| `DetectionMetadataAware` | 1 | 1 | `init(DetectionContext, Set)` |
| `LastFrontMetaDataContextPostProcess` | 2 | 2 | `loadMetaDataContext(FrontDeployDetectionContext)`, `readDirectoryToDtoList(String, MetaDataTypeEnum, Class)` |
| `DetectionRuleSupport` | 2 | 4 | `detectionRule(DetectionContext, T)`, `getCodeEnum()` |
| `SourceDetectionSupport` | 3 | 5 | `getSourceMetaData(DetectionContext)`, `getSourceDataType()`, `getSourceDomainObject()` |
| `SourceDetectionSupportWrapper` | 1 | 1 | `setSourceDetectionSupport()` |
| `WidgetExpressionDetectionFunction` | 1 | 1 | `doDetection(Set, PageInfoItemDto, PageDetectionContext, PageExpressionMaterialBo, String, List, ExpressionToken, Pair, List, ElementTypeEnum, Map, Object>, boolean)` |
| `DataDictionaryBuilder` | 7 | 7 | `buildH1(String)`, `buildH2(String)`, `buildH3(String)`, `buildH3(String, String)`, `buildLink(String, String)` …+2 |
| `TableColumn` | 3 | 4 | `getHeader()`, `getData(T)`, `getWidth()` |
| `MicroFlowLastVersionMetadataEnabler` | 4 | 5 | `getType()`, `getTriggerType()`, `getState()`, `getLastVersionMetadataState()` |
| `MicroFlowSchemaDeterminer` | 12 | 12 | `getAppId()`, `getName()`, `getCaption()`, `getDescription()`, `getType()` …+7 |
| `OperationLogSchema` | 1 | 1 | `getOperationLogSchema()` |
| `Stereotype` | 11 | 11 | `getName()`, `getCaption()`, `getOrder()`, `nonDeprecated()`, `getDeprecated()` …+6 |
| `CopyHandler` | 2 | 8 | `type()`, `out(EntityCopyContext)` |
| `EntityCopyResolver` | 2 | 2 | `copyEntity(EntityCopyContext)`, `type()` |
| `AppVersionDao` | 0 | 0 | — |
| `AttributeDao` | 0 | 0 | — |
| `AttributeGroupDao` | 0 | 0 | — |
| `AttributeSetDao` | 0 | 0 | — |
| `DataTransferObjectDao` | 0 | 0 | — |
| `DependentApplicationDao` | 0 | 0 | — |
| `DtoAttributeDao` | 0 | 0 | — |
| `EntityDao` | 0 | 0 | — |
| `EntityGroupDao` | 0 | 0 | — |
| `EntityPresetDao` | 0 | 0 | — |
| `EventDao` | 0 | 0 | — |
| `IndexDao` | 0 | 0 | — |
| `LastVersionMetadataDao` | 0 | 0 | — |
| `ReferConfigDao` | 0 | 0 | — |
| `ReferConfigGroupDao` | 0 | 0 | — |
| `ScalabilityDao` | 0 | 0 | — |
| `ScalabilityOptionDao` | 0 | 0 | — |
| `UdcApplicationDao` | 0 | 0 | — |
| `UdcEnumCategoryDao` | 0 | 0 | — |
| `UdcEnumDao` | 0 | 0 | — |
| `UdcEnumItemDao` | 0 | 0 | — |
| `UdcPushAssociationDao` | 0 | 0 | — |
| `ConfigurationLoader` | 3 | 3 | `loadFeature(String, Class)`, `loadStereotype(String, Class)`, `loadGeneratorConfig(String, Class)` |
| `EntitySaveProcessor` | 3 | 3 | `afterEntitySaved(EntityDto, EntityDto)`, `resolveAttribute4Feature(EntityDto, EntityDto, List)`, `afterEntityDeleted(EntityDto)` |
| `Feature` | 16 | 16 | `getId()`, `getName()`, `getCaption()`, `getDescription()`, `nonIgnored()` …+11 |
| `SqlProcessor` | 2 | 2 | `getSql(EntityDto)`, `getName()` |
| `Code` | 2 | 2 | `getCode()`, `setCode(String)` |
| `Schema` | 2 | 2 | `getSchema()`, `setSchema(String)` |
| `AttributeTransferDispatcher` | 1 | 1 | `dispatch(AttributeTransferDto)` |
| `AttributeTransferHandler` | 2 | 3 | `handleTransfer(AttributeTransferContext)`, `type()` |
| `Template` | 29 | 38 | `valueOpValue()`, `stringOpNumber()`, `numberOpString()`, `longResult()`, `numberOpDecimal()` …+24 |
| `Interpreter` | 1 | 4 | `interpret(ASTNode, ExprCodeGenContext)` |
| `ExtensionFunctionInterpreter` | 0 | 0 | — |
| `Functor` | 1 | 1 | `interpret()` |
| `ExprConsistency` | 1 | 1 | `order()` |
| `ExprConsistencyFilter` | 1 | 1 | `doFilter(ConsistencyFilterContext, ExprConsistencyFilterChain)` |
| `LimitCountCheck` | 4 | 6 | `check(BaseDto, Long)`, `getModelName()`, `getDbCount(Long)`, `count()` |
| `LimitCountOperation` | 2 | 2 | `modelName()`, `appId()` |
| `LogService` | 2 | 2 | `getLogType()`, `getLogs(String, int, long, long, String)` |
| `UdcAuditLogService` | 3 | 3 | `createLog4EntityDelete(List)`, `createLog4AttributeDelete(List)`, `createLog4ApplicationDelete(ApplicationDto)` |
| `ConvertorTypeDeterminer` | 1 | 1 | `getConvertorType()` |
| `AggDtoConvertor` | 1 | 1 | `convert(AggDtoConvertQuery, App)` |
| `AggDtoMetadataDtoConvertor` | 4 | 5 | `getAppInfo(App)`, `buildDtoName(String)`, `getDtoSource()`, `getDtoFullNameModule()` |
| `EnumMetadataDtoConverter` | 1 | 6 | `buildUdcEnumName(String)` |
| `BaseDesignMetadataQueryService` | 6 | 7 | `getMetadataSearchTypeEnum()`, `selectByAppId(Long)`, `selectByCondition(UdcAppMetaDataQueryDto)`, `selectByFullName(Long, String)`, `selectByFullNames(Long, List)` …+1 |
| `ComponentIdentity` | 1 | 1 | `getComponentIdentity()` |
| `MicroFlowComponentCascadeHandler` | 0 | 0 | — |
| `MicroFlowComponentCascadeHandlerDispatcher` | 1 | 1 | `dispatch(ObjectNode)` |
| `MicroFlowComponentHandler` | 8 | 12 | `isArrayComponent()`, `initComponentLocators()`, `addLocator(AbstractBaseNode, String)`, `addLocator(String, String)`, `getLocatorsKeySet()` …+3 |
| `MicroFlowRecursiveComponentHandler` | 0 | 5 | — |
| `MicroFlowSimpleComponentCascadeHandler` | 1 | 1 | `handleComponent(MicroFlowCascadeContext, JsonNode)` |
| `MicroFlowSubComponentHandler` | 4 | 6 | `initSubComponentLocators()`, `addSubLocator(MicroFlowSubComponentHandler>, Function, List)`, `getSubLocator(MicroFlowSubComponentHandler>)`, `getSubLocatorsKeySet()` |
| `ComponentLookup` | 1 | 1 | `lookup(ObjectNode)` |
| `BaseNode` | 18 | 18 | `getNodeId()`, `setNodeId(String)`, `getNodePath()`, `setNodePath(String)`, `getType()` …+13 |
| `BaseTrigger` | 18 | 18 | `getId()`, `setId(Long)`, `getNodeId()`, `setNodeId(String)`, `getCaption()` …+13 |
| `NodeParser` | 1 | 1 | `parse(MicroFlowNodeParseContext, ObjectNode)` |
| `BaseNodeContext` | 47 | 47 | `getApplicationDto()`, `isSubApp()`, `isDetection()`, `isRealGlobalDetection()`, `getAppNameSet()` …+42 |
| `ConnectorFullNameExtractor` | 1 | 4 | `extractUdcAppDtoFullName(VirtualFullNameTable)` |
| `DependencyAppServiceApiActivity` | 1 | 1 | `getDependencyAppServiceApi(VirtualFullNameTransformer)` |
| `DynamicDependencyFullNameModifier` | 2 | 2 | `modifyFullNameInGeneration(VirtualFullNameTransformer)`, `extractDynamicDependencyFullName(VirtualFullNameTable, DynamicDependencyFullNameChecker)` |
| `FullNameExtractor` | 1 | 1 | `extractFullName()` |
| `HandleNull` | 4 | 4 | `getNullHandling()`, `setNullHandling(NullHandlingEnum)`, `getNullPromptMessage()`, `setNullPromptMessage(String)` |
| `MicroFlowEntityDao` | 0 | 0 | — |
| `MicroFlowGroupDao` | 0 | 0 | — |
| `MicroFlowPresetTemplateDao` | 0 | 0 | — |
| `DataMappingFieldTypeDeterminer` | 3 | 3 | `getDataType()`, `getType()`, `getJavaType()` |
| `PresetTemplateHandler` | 6 | 6 | `getNextHandler()`, `setNextHandler(PresetTemplateHandler)`, `generate(EntityDto)`, `generateByName(EntityDto, String)`, `matches(EntityDto)` …+1 |
| `RefactorParam` | 0 | 0 | — |
| `ReferenceComponentProcessor` | 3 | 3 | `convertPreorderNodeReference(List, Set)`, `convertSuccessorNodeReference(List, Set)`, `replaceReferenceComponents(List, MicroFlowNodeReferenceDataMapping, Predicate)` |
| `SFunction` | 1 | 4 | `call(T)` |
| `ElementRepository` | 3 | 6 | `getType()`, `selectById(Long)`, `selectByAppId(Long)` |
| `ReferenceParser` | 3 | 3 | `parse(T)`, `scan(Long)`, `getSourceType()` |
| `ReferenceStore` | 9 | 9 | `save(Long, Collection)`, `deleteBySourceId(Long)`, `deleteBySourceIds(Collection)`, `deleteByAppId(Long)`, `getReferences(Long)` …+4 |
| `ReferenceDao` | 0 | 0 | — |
| `MicroflowNodeParser` | 1 | 1 | `parse(T, MicroFlowDefinitionDto)` |
| `OperationRecordService` | 6 | 6 | `buildOperationLogDetailsDto4Create(T)`, `buildOperationLogDetailsDto4CreateBatch(List)`, `buildOperationLogDetailsDto4Update(T)`, `buildOperationLogDetailsDto4UpdateBatch(List)`, `buildOperationLogDetailsDto4delete(Long)` …+1 |
| `LogDefault` | 5 | 5 | `domainService()`, `domainCaptionField()`, `domainAppIdField()`, `getDomainObjByIdsMethod()`, `update()` |
| `LogDefaultUpdate` | 3 | 3 | `attributeName()`, `attributeField()`, `valueType()` |
| `OperationLog` | 7 | 7 | `operationType()`, `module()`, `subModule()`, `requestDto()`, `recordServiceClass()` …+2 |
| `OperationLogDao` | 0 | 0 | — |
| `FunctionNodeEntityDao` | 0 | 0 | — |
| `PageDataSourceDao` | 0 | 0 | — |
| `PageInfoEntityDao` | 0 | 0 | — |
| `PageLayoutDao` | 0 | 0 | — |
| `PageSchemaEntityDao` | 0 | 0 | — |
| `PageTemplateCategoryEntityDao` | 0 | 0 | — |
| `PageTemplateEntityDao` | 0 | 0 | — |
| `PageTemplatePublishedEntityDao` | 0 | 0 | — |
| `PortletDao` | 0 | 0 | — |
| `PortletGroupEntityDao` | 0 | 0 | — |
| `ParameterDao` | 0 | 0 | — |
| `ChannelPlugin` | 1 | 1 | `execute(PipeLineContext)` |
| `DeployService` | 12 | 12 | `getAppType()`, `start(PipeLineContext)`, `doCreateRecord(PipeLineContext)`, `doCheck(PipeLineContext)`, `doGenerateCode(PipeLineContext)` …+7 |
| `PipeLineService` | 3 | 3 | `startPipeline(PipeLineContext)`, `startDeltaPipeline(PipeLineContext)`, `startOnlinePipeline(PipeLineContext)` |
| `PluginExecutor` | 4 | 4 | `execute(E)`, `executeAsync(E)`, `execute(E)`, `getAllHandler()` |
| `PluginHandler` | 1 | 1 | `execute(T)` |
| `CompleteMultiVersionPluginHandler` | 0 | 0 | — |
| `MultiVersionPluginHandler` | 0 | 0 | — |
| `SandboxPluginHandler` | 0 | 0 | — |
| `QueryAppService` | 4 | 4 | `selectByIds(List)`, `selectById(Long)`, `selectByAppIdAndDeployType(Long, DeployTypeEnum)`, `updateApplication(ApplicationDto)` |
| `MigrateCallback` | 1 | 1 | `extendFilesHandle(Collection)` |
| `BackendComponentDao` | 0 | 0 | — |
| `PageComponentCategoryDao` | 0 | 0 | — |
| `PageComponentDao` | 0 | 0 | — |
| `PageComponentDataTypeDao` | 0 | 0 | — |
| `NpmSyncDataService` | 7 | 7 | `getNpmSyncType()`, `readPackageData(String)`, `getPackageLocalPath(PackageInfoDto)`, `filterData(PackageInfoDto, String)`, `parseControls(PackageInfoDto)` …+2 |
| `TaskCallable` | 1 | 1 | `call(T)` |
| `Consumer3` | 1 | 1 | `accept(P1, P2, P3)` |

## com.seeyon.cip（157）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `ApplicationAffairAppService` | 0 | 8 | — |
| `ApplicationMessageAppService` | 0 | 1 | — |
| `ApplicationMobileAppService` | 0 | 2 | — |
| `ApplicationPluginStatusAppService` | 2 | 2 | `selectStatusByPlugIds(SingleRequest)`, `selectStatusByLinkerIds(SingleRequest)` |
| `MappingDetailAppService` | 0 | 12 | — |
| `MiddleTableAppService` | 0 | 12 | — |
| `MobileAppService` | 0 | 0 | — |
| `WarningCallBackAppService` | 0 | 1 | — |
| `WarningManageAppService` | 0 | 2 | — |
| `DefaultCardInfoService` | 3 | 4 | `getName()`, `getTypeCaption()`, `buildCardInfo(String, String, String, String)` |
| `OrgIntegrationAppService` | 10 | 10 | `queryCardInfo(SingleRequest)`, `updateCardInfo(SingleRequest)`, `queryServiceTypeInfo()`, `queryJsApiAddressByCode(String)`, `queryCardRunInfo(SingleRequest)` …+5 |
| `PersonnelCardService` | 4 | 5 | `getServiceName()`, `getServiceResParam()`, `queryJsApiAddressParam()`, `result(Map, Object>)` |
| `ArchivesAppService` | 0 | 4 | — |
| `BankpayAppService` | 11 | 11 | `balanceQuery(SingleRequest)`, `paymentTransfer(SingleRequest)`, `accountDetail(PageDtoRequest)`, `accountSummary(PageDtoRequest)`, `accountInDetail(SingleRequest)` …+6 |
| `CensorAppService` | 1 | 2 | `textCensor(SingleRequest)` |
| `EnterpriseCreditAppService` | 25 | 25 | `pageEnterpriseInfo(PageRequest)`, `getBasicBusinessInfo(SingleRequest)`, `pageEnterpriseInfo(PageDtoRequest)`, `getBasicInfo(SingleRequest)`, `getPartners(SingleRequest)` …+20 |
| `DocCallBackAppService` | 12 | 12 | `fileInfo(SingleRequest)`, `userInfo(SingleRequest)`, `editFileOnline(SingleRequest)`, `editFileSave(SingleRequest)`, `editFileVersion(SingleRequest)` …+7 |
| `DocGeneralizeAppService` | 1 | 1 | `getAuthorityInfoProxy(SingleRequest)` |
| `DocOnlineAppService` | 27 | 28 | `getOfficeViewUrl(SingleRequest)`, `getCompositeViewUrl(SingleRequest)`, `getLatestPicViewUrl(SingleRequest)`, `getOfficeEditUrl(SingleRequest)`, `cpsOfficeConvert(SingleRequest)` …+22 |
| `CompanyAccountServiceAppService` | 2 | 2 | `createOrUpdate(SingleRequest)`, `queryCompanyAccountInfo(SingleRequest)` |
| `ContractsAppService` | 11 | 11 | `processPersonalCertificate(SingleRequest)`, `processPersonCertificateInfo(SingleRequest)`, `processEnterpriseCertificate(SingleRequest)`, `processBpmTemplateValidCheck(SingleRequest)`, `processFileUpload(SingleRequest)` …+6 |
| `ContractsCallBackAppService` | 1 | 1 | `callBack(SingleRequest)` |
| `SealAppService` | 7 | 7 | `uploadSeal(SingleRequest)`, `listSeal(SingleRequest)`, `getSealDetails(SingleRequest)`, `authSeal(SingleRequest)`, `cancelAuthSeal(SingleRequest)` …+2 |
| `EmailAppService` | 9 | 9 | `sendNormalEmail(SingleRequest)`, `sendNormalEmailByAccount(SingleRequest)`, `sendPersonalEmail(SingleRequest)`, `testSendPersonalEmail(SingleRequest)`, `insertOrUpdate(SingleRequest)` …+4 |
| `EmailPrivateAppService` | 11 | 11 | `insertOrUpdateEmailConfig(SingleRequest)`, `deleteEmailConfig()`, `getCompanySystemEmail()`, `addEmailTemplate(SingleRequest)`, `modifyEmailTemplate(SingleRequest)` …+6 |
| `FaceIdAppService` | 3 | 4 | `addFace(SingleRequest)`, `faceCheck(SingleRequest)`, `updateFace(SingleRequest)` |
| `GisAppService` | 1 | 1 | `getToken(SingleRequest)` |
| `InvoiceAppService` | 9 | 9 | `getOcrInvoiceData(SingleRequest)`, `getOcrAsyncResult(SingleRequest)`, `getOcrInvoiceSingle(SingleRequest)`, `verificationInvoice(SingleRequest)`, `batchGetInvoice(SingleRequest)` …+4 |
| `InvoiceImageAppService` | 2 | 2 | `createImageTask(SingleRequest)`, `uploadImageFile(SingleRequest)` |
| `LocationAppService` | 5 | 7 | `getLocation(SingleRequest)`, `getDistance(SingleRequest)`, `geocoding(SingleRequest)`, `regionSearch(SingleRequest)`, `getJsApiInfo(SingleRequest)` |
| `OfflineMessageAppService` | 1 | 1 | `pushMessage(SingleRequest)` |
| `IntelligentMissiveAppService` | 26 | 26 | `createExtractingTask(SingleRequest)`, `queryExtractingDetail(SingleRequest)`, `queryDiffRule(SingleRequest)`, `createDocDiffTask(SingleRequest)`, `queryDocDiffPage(SingleRequest)` …+21 |
| `MobilePluginAppletAppService` | 11 | 11 | `receiveTicket(SingleRequest)`, `bindAuth(SingleRequest)`, `authUrl(SingleRequest)`, `templateList(SingleRequest)`, `uploadCode(SingleRequest)` …+6 |
| `MobilePluginConfigAppService` | 9 | 9 | `selectOneByConditions(SingleRequest, Object>>)`, `selectById(SingleRequest)`, `create(SingleRequest)`, `update(SingleRequest)`, `updateStatus(SingleRequest)` …+4 |
| `OcrAppService` | 20 | 20 | `getIdCardFrontData(SingleRequest)`, `getIdCardBackData(SingleRequest)`, `getBankCardData(SingleRequest)`, `getBusinessCardData(SingleRequest)`, `getBusinessLicenseData(SingleRequest)` …+15 |
| `OfdAppService` | 5 | 5 | `getOfdViewUrl(SingleRequest)`, `downFile(SingleRequest)`, `getSealInfo(SingleRequest)`, `getSealList(SingleRequest)`, `getOfdMetaData(SingleRequest)` |
| `MerchantAppService` | 0 | 5 | — |
| `PayAppService` | 0 | 8 | — |
| `PhysicalSealAppService` | 10 | 10 | `syncDept(SingleRequest)`, `syncMember(SingleRequest)`, `applyAuthorize(SingleRequest)`, `queryApplyRecord(SingleRequest)`, `cancelApply(SingleRequest)` …+5 |
| `ResumeAppService` | 1 | 1 | `analysisResume(SingleRequest)` |
| `ScheduleAppService` | 0 | 4 | — |
| `SearchAppService` | 1 | 1 | `querySearchUrl(SingleRequest)` |
| `SignatureAppService` | 29 | 39 | `getSignatureViewUrl(SingleRequest)`, `downFile(SingleRequest)`, `getSealInfo(SingleRequest)`, `uploadFile(SingleRequest)`, `initiateSign(SingleRequest)` …+24 |
| `ShortMessageAppService` | 3 | 4 | `sendShortMessage(SingleRequest)`, `sendSycShortMessage(SingleRequest)`, `sendShortMessageAsync(SingleRequest)` |
| `TranslationAppService` | 2 | 2 | `translate(SingleRequest)`, `getLanguages(SingleRequest)` |
| `BusinessTripAppService` | 14 | 14 | `departmentSync(SingleRequest)`, `isvUserSync(SingleRequest)`, `isvCitySync(SingleRequest)`, `addressGetBook(SingleRequest)`, `addressGetOrder(SingleRequest)` …+9 |
| `VideoMeetingAppService` | 20 | 20 | `createVideoMeeting(SingleRequest)`, `createPersonalVideoMeeting(SingleRequest)`, `updateVideoMeeting(SingleRequest)`, `cancelVideoMeeting(SingleRequest)`, `finishVideoMeeting(SingleRequest)` …+15 |
| `VoiceAppService` | 7 | 7 | `createRealTime(SingleRequest)`, `createVoiceFile(SingleRequest)`, `queryVoiceFileResult(SingleRequest)`, `createFileConvertWords(SingleRequest)`, `queryConvertWordsResult(SingleRequest)` …+2 |
| `WeatherAppService` | 2 | 2 | `getLocation(SingleRequest)`, `getWeather(SingleRequest)` |
| `AiAppService` | 3 | 3 | `createThirdApp(SingleRequest)`, `thirdAppIncrease(SingleRequest)`, `queryUsageAmount(SingleRequest)` |
| `CapabilityEnumAppService` | 9 | 9 | `selectList(ListRequest)`, `selectItemList(ListRequest)`, `create(SingleRequest)`, `createItem(SingleRequest)`, `delete(SingleRequest)` …+4 |
| `CapabilityAccessLogDbAppService` | 3 | 3 | `selectById(SingleRequest)`, `selectPageByConditions(PageRequest)`, `countByConditions(SingleRequest)` |
| `CapabilityManageAppService` | 40 | 53 | `selectPageByConditions(PageRequest)`, `operationEnable(SingleRequest)`, `updateDefaultProvider(SingleRequest)`, `selectProvidersByEnum(SingleRequest)`, `selectOptionalProvider(SingleRequest)` …+35 |
| `ExcelSmsImportAndExportAppService` | 3 | 3 | `importExcel(SingleRequest)`, `exportExcel(SingleRequest)`, `exportExcelTemplate(SingleRequest)` |
| `ShortMessageProviderTemplateAppService` | 5 | 5 | `createShortMessageTemplateContent(SingleRequest)`, `updateTemplateContent(SingleRequest)`, `selectTemplateContentById(SingleRequest)`, `deleteTemplateContent(SingleRequest)`, `selectTemplateContentByConditions(PageRequest)` |
| `ShortMessageSignAppService` | 12 | 12 | `createShortMessageSign(SingleRequest)`, `createSmsSign(SingleRequest)`, `updateTemplateSign(SingleRequest)`, `updateSmsSign(SingleRequest)`, `updateShortMessageSign(SingleRequest)` …+7 |
| `ShortMessageTemplateAppService` | 14 | 14 | `createShortMessageTemplate(SingleRequest)`, `createSMSTemplate(SingleRequest)`, `updateTemplate(SingleRequest)`, `setTemplateSign(SingleRequest)`, `selectTemplateById(SingleRequest)` …+9 |
| `TokenAppService` | 2 | 2 | `selectTokenExpireTime(SingleRequest)`, `saveTokenExpireTime(SingleRequest, SingleRequest)` |
| `OpenCapabilityAppService` | 3 | 6 | `createApp(SingleRequest)`, `updateAppCharges(SingleRequest)`, `queryUseCount(SingleRequest)` |
| `CipDaoCondition` | 3 | 3 | `alias()`, `selectType()`, `isI18n()` |
| `CacheCustom` | 0 | 0 | — |
| `CapabilityCallCount` | 0 | 2 | — |
| `CipCapabilityMonitorCallback` | 0 | 3 | — |
| `CipCapabilityMonitorConfig` | 0 | 3 | — |
| `CipCapabilityMonitorRule` | 0 | 2 | — |
| `CipCapabilityRemoteMonitor` | 0 | 3 | — |
| `CipCapabilityShorterStorage` | 0 | 6 | — |
| `CapabilityConcurrentExecuteService` | 0 | 1 | — |
| `CapabilityQueueProcessorService` | 0 | 4 | — |
| `CapabilityBaseService` | 0 | 4 | — |
| `EleCloudDataAdapter` | 0 | 2 | — |
| `Push` | 0 | 1 | — |
| `Repush` | 0 | 1 | — |
| `MobilePluginAppletComponentConfigService` | 0 | 13 | — |
| `BaiduDataAdapter` | 0 | 9 | — |
| `TencentDataAdapter` | 0 | 6 | — |
| `SealMethod` | 0 | 1 | — |
| `ReqHeaderConstants` | 0 | 0 | — |
| `CtpUserStopWatchNoReturnFunction` | 0 | 1 | — |
| `CtpUserStopWatchReturnFunction` | 0 | 1 | — |
| `CipCapabilityConcurrentExecuteService` | 0 | 1 | — |
| `CipConnectorConcurrentExecuteService` | 0 | 1 | — |
| `CipConnectorWhere` | 0 | 2 | — |
| `DelayInitRunner` | 0 | 2 | — |
| `CipConnectorLogExcludeClass` | 0 | 0 | — |
| `CipConnectorLogExcludeMethod` | 0 | 0 | — |
| `CipConnectorLogIncludeClass` | 0 | 0 | — |
| `CipConnectorLogIncludeMethod` | 0 | 0 | — |
| `CipConnectorQueueProcessorService` | 0 | 5 | — |
| `CipConnectorShorterStorage` | 0 | 6 | — |
| `CipConnectorComment` | 2 | 2 | `value()`, `example()` |
| `ConnectorChannelRouter` | 2 | 2 | `value()`, `desc()` |
| `MiddleTableChannelRouter` | 2 | 2 | `value()`, `description()` |
| `CipThirdAffairService` | 1 | 1 | `queryThirdAffairFieldData(ThirdTemplateDataSpiReqDto)` |
| `LinkerSecurityService` | 8 | 9 | `getName()`, `getTypeCaption()`, `getMode()`, `doAuthentication(AuthenticationDto)`, `doDecode(String, AuthEventDto)` …+3 |
| `ConnectorCallbackMessageSendService` | 2 | 2 | `sendMsgAsync(T)`, `sendMsgSync(T)` |
| `ConnectorCallbackProviderService` | 1 | 1 | `doCallback(ConnectorCallbackRequestDto, ConnectorCallbackMessageSendService)` |
| `BaseConfigAppService` | 11 | 11 | `createDatabase(SingleRequest)`, `updateDatabase(SingleRequest)`, `deleteDatabaseById(SingleRequest)`, `selectDatabaseById(SingleRequest)`, `selectDatabaseByIds(SingleRequest)` …+6 |
| `LinkerAppService` | 10 | 12 | `selectPageByCondition(PageRequest)`, `selectAll()`, `selectDetailsByInfoId(SingleRequest)`, `selectLinkerDetailParameterDisplay(SingleRequest)`, `selectEventDetailsByInfoId(SingleRequest)` …+5 |
| `LinkerEnumAppService` | 1 | 1 | `selectItemList(ListRequest)` |
| `LinkerMigrationAppService` | 4 | 4 | `exportEntityTask(SingleRequest)`, `initDataJsonByNames(SingleRequest)`, `listConnectorData(SingleRequest)`, `importConnectorData(SingleRequest)` |
| `SsoExecutorAppService` | 1 | 1 | `ssoLongin(SingleRequest)` |
| `DataBaseExecutorService` | 13 | 14 | `getDbTypeEnum()`, `getName()`, `executeDetail(DatabaseInfoApiDto, LinkerDetailApiDto, Map, Object>)`, `executeDetailForCount(DatabaseInfoApiDto, LinkerDetailApiDto, Map, Object>)`, `transformByType(Object, String)` …+8 |
| `MiddleTableOrgSyncSpiListenerService` | 1 | 1 | `dataGovernance(ConnectorCallbackRequestDto, MiddleTableOrgSyncDataCallbackService, MiddleTableOrgSyncMarkCallbackService, MiddleTableOrgSyncExecuteCallbackService)` |
| `MiddleTableOrgSyncSpiPullService` | 2 | 2 | `pullAll(ConfigInfoApiDto, MiddleTableOrgSyncDataCallbackService, MiddleTableOrgSyncMarkCallbackService, MiddleTableOrgSyncExecuteCallbackService)`, `pullIncrement(ConfigInfoApiDto, MiddleTableOrgSyncDataCallbackService, MiddleTableOrgSyncExecuteCallbackService)` |
| `MiddleTableOrgSyncDataCallbackService` | 5 | 5 | `batchSaveOrg(UnitInfoSpiReqDto)`, `batchSavePosition(PostInfoSpiReqDto)`, `batchSaveDuty(DutyInfoSpiReqDto)`, `batchSaveLevel(LevelInfoSpiReqDto)`, `batchSaveMember(MemberInfoSpiReqDto)` |
| `MiddleTableOrgSyncExecuteCallbackService` | 1 | 1 | `executeSyncToOrgModel(String)` |
| `MiddleTableOrgSyncMarkCallbackService` | 1 | 1 | `markComplete(String)` |
| `MobileApplicationProviderService` | 7 | 10 | `getMobileUrlDto(MobileUrlProviderDto)`, `explainLinkInfo()`, `publishApp(MobilePublishAppRequestDto, MobilePlatformConfigDto)`, `getSignature(MobilePlatformConfigDto, MobilePlatformSignatureDto)`, `sendMessage(boolean, MobileMessageRequestDto, MobilePlatformRequestDto)` …+2 |
| `MobileCallBackProviderService` | 0 | 0 | — |
| `MobileConfigProviderService` | 10 | 14 | `jsonCheck(String)`, `getName()`, `getTypeCaption()`, `getSortNo()`, `getPageJson()` …+5 |
| `MobileOrgSyncBatchProviderService` | 3 | 3 | `syncUnitBatch(MobileDepartmentBatchSyncDto, MobilePlatformConfigDto)`, `userSyncBatch(MobileUserBatchSyncDto, MobilePlatformConfigDto)`, `syncBatchResult(MobileBatchResultDto, MobilePlatformConfigDto)` |
| `MobileOrgSyncProviderService` | 8 | 9 | `syncUnit(MobileUnitRequestDto, MobilePlatformConfigDto)`, `updateUnit(MobileUnitRequestDto, MobilePlatformConfigDto)`, `getUnit(MobileUnitRequestDto, MobilePlatformConfigDto)`, `removeUnit(MobileUnitRequestDto, MobilePlatformConfigDto)`, `syncUser(MobileUserRequestDto, MobilePlatformConfigDto)` …+3 |
| `MobileOrgSyncPullProviderService` | 2 | 5 | `listSyncOrg(MobilePlatformConfigDto, String)`, `listSyncUser(MobilePlatformConfigDto, String)` |
| `MobileProviderService` | 0 | 0 | — |
| `MobileTodoProviderService` | 2 | 6 | `createTodo(MobilePlatformConfigDto, MobileTodoRequestDto)`, `updateTodo(MobilePlatformConfigDto, MobileTodoRequestDto)` |
| `LinkerSignService` | 4 | 4 | `getName()`, `getCaption()`, `doSign(LinkerSignDto, RequestParamDto)`, `getSortNo()` |
| `SsoService` | 7 | 7 | `getName()`, `getTypeCaption()`, `login(String, String, Map, Object>, SsoClientTypeEnum, Map, Object>)`, `check(String)`, `getPageJson()` …+2 |
| `CipConnectorMonitorCallback` | 0 | 3 | — |
| `CipConnectorMonitorConfig` | 0 | 3 | — |
| `CipConnectorMonitorRule` | 0 | 3 | — |
| `CipConnectorRemoteMonitor` | 0 | 4 | — |
| `LinkerExecutorService` | 0 | 1 | — |
| `CommonSecurityService` | 0 | 2 | — |
| `MqStrategy` | 0 | 8 | — |
| `CipConvertQueueProcessorService` | 0 | 5 | — |
| `CipConvertThreadPoolProcessorService` | 0 | 1 | — |
| `WarningCallBackAppService` | 0 | 1 | — |
| `WarningManageAppService` | 0 | 2 | — |
| `SwitchEnable` | 0 | 0 | — |
| `MobileWorkWxCallBackService` | 0 | 1 | — |
| `WechatMessageSender` | 0 | 1 | — |
| `MobileAffairRoute` | 0 | 4 | — |
| `RemotingInvoker` | 0 | 1 | — |
| `OcipDataTransferServiceProvider` | 0 | 4 | — |
| `OcipExchangeProviderService` | 0 | 1 | — |
| `OcipSyncStrategy` | 0 | 2 | — |
| `OcipWebService` | 0 | 5 | — |
| `ApiConstants` | 0 | 0 | — |
| `ReactiveDiscovery` | 0 | 2 | — |
| `Caller` | 0 | 1 | — |
| `CipFileAppService` | 0 | 2 | — |
| `CipMessageAppService` | 0 | 1 | — |
| `OpenApiNotifyAppService` | 0 | 1 | — |
| `RedisDistributeJob` | 0 | 2 | — |
| `CipPlugCapabilityAppService` | 0 | 1 | — |
| `MiddleTableOperationAppService` | 0 | 12 | — |
| `PluginAffairAppService` | 0 | 4 | — |
| `PluginMessageAppService` | 0 | 1 | — |
| `PluginStatusAppService` | 2 | 2 | `selectStatusByPlugIds(SingleRequest)`, `selectStatusByLinkerIds(SingleRequest)` |
| `OrgSyncDataDownLoadService` | 0 | 1 | — |
| `SyncSingleTypeToOrgService` | 0 | 5 | — |
| `DataViewHandlerCallback` | 0 | 1 | — |
| `DeduplicationStrategy` | 0 | 3 | — |
| `CipChannelRouter` | 1 | 1 | `value()` |
| `ValidationGroup` | 0 | 0 | — |
| `ContractApiUrlable` | 1 | 1 | `apiUrl()` |

## com.seeyon.bpm（128）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `BpmActionAppService` | 0 | 2 | — |
| `BpmActivityAppService` | 0 | 4 | — |
| `BpmApiFormPermissionAppService` | 12 | 18 | `create(SingleRequest)`, `update(SingleRequest)`, `deleteById(SingleRequest)`, `selectByTemplateId(SingleRequest)`, `selectById(SingleRequest)` …+7 |
| `BpmApiNodePermissionAppService` | 4 | 11 | `bpmNodePermissionHandel(SingleRequest)`, `selectNodePermissionById(SingleRequest)`, `savePermission(SingleRequest)`, `savePermissionList(SingleRequest)` |
| `BpmApiPermissionAppService` | 0 | 3 | — |
| `BpmApiProcessAppService` | 1 | 1 | `selectDiagramDetailByTemplateCodeAndVersion(SingleRequest)` |
| `BpmAppOrgReplaceService` | 1 | 1 | `replace(SingleRequest)` |
| `BpmAppService` | 22 | 26 | `send(SingleRequest)`, `saveDraft(SingleRequest)`, `submit(SingleRequest)`, `stepBack(SingleRequest)`, `repeal(SingleRequest)` …+17 |
| `BpmApplicationOperateLogAppService` | 3 | 3 | `saveApplicationOperateLog(SingleRequest)`, `selectNewestLogInfo(SingleRequest)`, `updateAppLogs(SingleRequest)` |
| `BpmAutoApprovalAppService` | 4 | 4 | `designerCreate(SingleRequest)`, `designerUpdate(SingleRequest)`, `designerDelete(SingleRequest)`, `designerSelect(PageDtoRequest)` |
| `BpmCaseAppService` | 2 | 23 | `selectCaseById(SingleRequest)`, `selectMainCaseBySubCaseId(SingleRequest)` |
| `BpmCaseLogAppService` | 2 | 2 | `selectByCaseId(SingleRequest)`, `selectByDto(SingleRequest)` |
| `BpmCoMiAppService` | 0 | 1 | — |
| `BpmDeployAppService` | 6 | 6 | `upgradeBpmTemplateVersion(SingleRequest)`, `deployBpmTemplatesIndependent(SingleRequest)`, `afterFormAppDataInit(SingleRequest)`, `upgradeCommon(SingleRequest)`, `autoDeployStartAndAuth(SingleRequest)` …+1 |
| `BpmDetailAppService` | 1 | 1 | `selectDetail(SingleRequest)` |
| `BpmNodeAppService` | 0 | 4 | — |
| `BpmNodePermissionOperationAppService` | 2 | 2 | `getNodePermissionOperation(SingleRequest)`, `selectOperationSimpleByPermissionIds(SingleRequest)` |
| `BpmNormalAppMultiVersionAppService` | 1 | 2 | `selectCurrentHighestVersionBatch(SingleRequest)` |
| `BpmOpinionAppService` | 2 | 7 | `selectOpinionGroupByActivityNodeWithObjectId(PageDtoRequest)`, `deleteOpinion(SingleRequest)` |
| `BpmProcessLogAppService` | 5 | 7 | `create(SingleRequest)`, `createBatch(SingleRequest)`, `selectLogList(SingleRequest)`, `selectOriginalI18nLogList(SingleRequest)`, `selectLogOriginalListByCaseIds(SingleRequest)` |
| `BpmProcessTrackAppService` | 1 | 2 | `selectProcessTrackList(SingleRequest)` |
| `BpmSuperviseAppService` | 3 | 3 | `search(ListRequest)`, `cancelFocus(SingleRequest)`, `skip(SingleRequest)` |
| `BpmTemplateAppService` | 32 | 55 | `createOrUpdate(SingleRequest)`, `deleteById(SingleRequest)`, `updateCategoryByApplicationId(SingleRequest)`, `publishCheck(SingleRequest)`, `publishCheckByAppInfo(SingleRequest)` …+27 |
| `BpmTemplateManageAppService` | 8 | 11 | `grayAuthTemplate(SingleRequest)`, `closeLowerVersionGrayAndStarted(SingleRequest)`, `startByAppName(SingleRequest)`, `selectFormalAuthTemplateList(SingleRequest)`, `selectFormalAuthTemplateListByQueryDto(SingleRequest)` …+3 |
| `BpmThirdTemplateSyncAppService` | 4 | 4 | `createBatch(SingleRequest)`, `updateBatch(SingleRequest)`, `createActivityResponsibilities(SingleRequest)`, `createTemplateRecent(SingleRequest)` |
| `BpmWorkItemAppService` | 0 | 4 | — |
| `ActivityBehavior` | 6 | 8 | `getConfigId()`, `preMatch(BpmSupportOperation, ActivityBehaviorChain)`, `onActivityReady(BpmSupportOperation, ActivityBehaviorChain)`, `onActivityFinish(BpmSupportOperation, ActivityBehaviorChain)`, `onActivityCanceled(BpmSupportOperation, ActivityBehaviorChain)` …+1 |
| `ActivityBehaviorChain` | 2 | 2 | `doBehaviorChain(BpmSupportOperation, Class)`, `hasNext()` |
| `ActivityBehaviorFactory` | 3 | 3 | `getActivityBehaviors(String)`, `getActivityConfiguration(String)`, `supportActivities()` |
| `BpmSupportOperation` | 16 | 16 | `getConfigId()`, `getParameters()`, `setParameter(String, Object)`, `getConfigurationValue(String)`, `getAllConfigurationValues()` …+11 |
| `BpmApiDetectionService` | 9 | 9 | `detectionForAttributeDelete(SingleRequest)`, `detectionForAttributeUpdate(SingleRequest)`, `detectionForCtpEnumDelete(SingleRequest)`, `cascadeHandleAffectedForEntity(SingleRequest)`, `cascadeHandleAffectedForAttr(SingleRequest)` …+4 |
| `BpmApiParamAppService` | 6 | 8 | `saveParamSchema(SingleRequest)`, `saveParamData(SingleRequest)`, `loadParamSchema(SingleRequest)`, `loadParamTypes(SingleRequest)`, `loadParamSchemaByOrigin(SingleRequest)` …+1 |
| `BpmApiSplitImportAppService` | 3 | 3 | `selectTemplateByAppName(SingleRequest)`, `prepareApp(SingleRequest)`, `splitImport(SingleRequest)` |
| `BpmApiTransportAppService` | 6 | 7 | `saveAs(SingleRequest)`, `getApplicationInitData(SingleRequest)`, `getApplicationInitDataAsync(SingleRequest)`, `exportTemplateInfo(SingleRequest)`, `importTemplateInfo(SingleRequest)` …+1 |
| `BpmUdcApiService` | 4 | 10 | `sendForUdc(SingleRequest)`, `repealForUdc(SingleRequest)`, `stopForUdc(SingleRequest)`, `deleteCaseByIdForUdc(SingleRequest, SingleRequest)` |
| `BpmUpgrade51To52AppService` | 1 | 1 | `upgradeExtensionPlan(SingleRequest)` |
| `ApplicationAutoGenerateService` | 0 | 1 | — |
| `DispatcherHandler` | 0 | 1 | — |
| `BpmnXmlAttributeValue` | 0 | 1 | — |
| `BpmnXmlElement` | 0 | 1 | — |
| `BpmMethodLog` | 0 | 3 | — |
| `BpmOpinionAnnotation` | 0 | 1 | — |
| `BpmOpsAuth` | 0 | 1 | — |
| `OptimisticLockRetry` | 0 | 1 | — |
| `NoDuplicateSubmit` | 0 | 3 | — |
| `NoDuplicateSubmitIdentityProvider` | 0 | 1 | — |
| `BpmCascadeHandleAffectedInterface` | 0 | 2 | — |
| `BpmDetectionContext` | 0 | 6 | — |
| `BpmDetectionInterface` | 0 | 8 | — |
| `BpmDetectionMetadataAware` | 0 | 1 | — |
| `BpmDetectionRuntimeInterface` | 0 | 1 | — |
| `BpmFieldsUsedForDetectionInterface` | 0 | 23 | — |
| `BpmLocalCacheParam` | 0 | 1 | — |
| `EnableBpmLocalCache` | 0 | 2 | — |
| `EvictEvent` | 0 | 4 | — |
| `UseBpmLocalCache` | 0 | 16 | — |
| `InvokeLimit` | 0 | 2 | — |
| `MonitorNodeAction` | 0 | 4 | — |
| `BpmInnerSupportOperation` | 0 | 11 | — |
| `InnerActivityBehavior` | 0 | 2 | — |
| `CustomPropertiesConfigInterface` | 0 | 1 | — |
| `BpmActivityFeature` | 0 | 7 | — |
| `BpmActorIdentity` | 0 | 9 | — |
| `BpmAppOrgReplaceInterface` | 0 | 4 | — |
| `AppDesignStateFeatureHandler` | 0 | 8 | — |
| `AppFeatureHandler` | 0 | 15 | — |
| `AppSourceTypeFeatureHandler` | 0 | 13 | — |
| `AutoNodeAction` | 0 | 3 | — |
| `CollectivizeBehavior` | 0 | 3 | — |
| `AsyncOperation` | 0 | 2 | — |
| `DataCompressEnableHandler` | 0 | 1 | — |
| `EntityHandler` | 0 | 2 | — |
| `BpmIsolatedThreadExecutor` | 0 | 11 | — |
| `UseBpmIsolatedThreadExecutor` | 0 | 7 | — |
| `Limiter` | 0 | 2 | — |
| `BpmDeletePhysicsInterface` | 0 | 1 | — |
| `DeployLifeCycleInterface` | 0 | 16 | — |
| `BpmInitExtInterface` | 0 | 4 | — |
| `BpmUpgradeImportInterface` | 0 | 3 | — |
| `SummaryDetail` | 0 | 2 | — |
| `DiagramParser` | 0 | 3 | — |
| `DiagramValidate` | 0 | 2 | — |
| `CaseLock` | 0 | 1 | — |
| `MergeHandle` | 0 | 1 | — |
| `MergeHandleDomain` | 0 | 0 | — |
| `MergeStrategy` | 0 | 2 | — |
| `MergeExclusionHandler` | 0 | 3 | — |
| `BeforeCreateAffairHandler` | 0 | 1 | — |
| `NspFragmentProvider` | 0 | 2 | — |
| `BpmNodeAction` | 0 | 2 | — |
| `BaseOperationService` | 0 | 6 | — |
| `BpmPermissionFilter` | 0 | 1 | — |
| `PostApprovalHandle` | 0 | 1 | — |
| `PostApprovalHandleDomain` | 0 | 0 | — |
| `PostApprovalStrategy` | 0 | 1 | — |
| `PostApprovalExclusionHandler` | 0 | 4 | — |
| `SpiExecutor` | 0 | 2 | — |
| `SpiFunction` | 0 | 1 | — |
| `SubProcessSender` | 0 | 2 | — |
| `ActivityDeleteSelector` | 0 | 3 | — |
| `LevelApprovalOuter` | 0 | 1 | — |
| `BpmBatchTaskExecutor` | 0 | 4 | — |
| `TemplateEventService` | 0 | 1 | — |
| `AcrossEnvInterface` | 0 | 7 | — |
| `BpmTransportInterface` | 0 | 14 | — |
| `AppContext` | 0 | 1 | — |
| `Lifecycle` | 0 | 3 | — |
| `Metadatable` | 0 | 4 | — |
| `DeployExecutor` | 0 | 5 | — |
| `ApplicationInit` | 0 | 13 | — |
| `BpmUniformity` | 0 | 1 | — |
| `BpmUniformityMethod` | 0 | 3 | — |
| `UniformityRunnable` | 0 | 1 | — |
| `UpgradeInterface` | 0 | 2 | — |
| `AppStandardUpgrade` | 0 | 2 | — |
| `BpmSystemSettingOptionsBase` | 0 | 2 | — |
| `BpmSecurityService` | 0 | 2 | — |
| `BpmSecurityUltimateDetailService` | 0 | 3 | — |
| `BpmSecurityWorkflowDetailService` | 0 | 3 | — |
| `BpmApiSimulationAppService` | 1 | 2 | `selectProcessPredictionResult(SingleRequest)` |
| `BpmDetailViewSpi` | 2 | 2 | `forwardAffair(BpmForwardReq)`, `mergeNodePermission(BpmNodePermissionMergeReq)` |
| `BpmOperationSpi` | 1 | 1 | `checkNodePermission(BpmCheckNodePermissionReq)` |
| `BpmForwardDataSubscribe` | 1 | 1 | `handler(SingleRequest)` |
| `BpmUpgradeService` | 0 | 3 | — |
| `ParamAnchorPoint` | 0 | 2 | — |
| `ParamAnchorPoints` | 0 | 1 | — |
| `ThreadParamAnchorPoint` | 0 | 1 | — |
| `ThrowExceptionFunction` | 0 | 1 | — |

## com.seeyon.ctp（115）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `AffairCategoryAppService` | 3 | 3 | `syncCategories(SingleRequest)`, `getAllAppAndSubAppInfoRegisterAffair()`, `searchAffairCategory(SingleRequest)` |
| `AffairCommonAppService` | 11 | 47 | `updateAffairDoneIdempotent(SingleRequest)`, `selectListByCondition(SingleRequest)`, `countAffairByConditions(SingleRequest)`, `createAffair(SingleRequest)`, `createAffairIdempotent(SingleRequest)` …+6 |
| `AffairCustomOperationAppService` | 0 | 1 | — |
| `AffairDataScopeAppService` | 0 | 1 | — |
| `AffairNodePermissionAppService` | 0 | 5 | — |
| `AffairMicroflowAppService` | 0 | 4 | — |
| `AffairOpenAppService` | 3 | 12 | `selectPageByCondition(SingleRequest)`, `selectByConditionIgnoreTenant(SingleRequest)`, `selectActivityUnprocessedMember(SingleRequest)` |
| `AffairSuperviseAppService` | 2 | 3 | `selectTemplateAffairPageData(SingleRequest)`, `updateTemplateAccountId2Affairs(SingleRequest)` |
| `AffairUdcAppService` | 0 | 1 | — |
| `ConditionCache` | 0 | 0 | — |
| `AffairConstant` | 0 | 0 | — |
| `BufferedMergeHandler` | 0 | 1 | — |
| `AffairNoExtendProperty` | 0 | 0 | — |
| `EnableMergeTenant` | 0 | 0 | — |
| `OptimisticLockRetry` | 0 | 1 | — |
| `AffairOperationService` | 0 | 52 | — |
| `IAffair` | 0 | 130 | — |
| `UseCustomResultSetMapping` | 0 | 1 | — |
| `AffairFragmentSQL` | 0 | 9 | — |
| `AffairSummaryDto` | 5 | 5 | `getId()`, `getAppName()`, `getSubAppName()`, `getApplicationName()`, `getFormRecordCode()` |
| `AbstractAffairSearchService` | 0 | 1 | — |
| `AbstractThirdAffairService` | 1 | 1 | `batchOperateThirdAffair(AffairBatchDto)` |
| `Affair4WorkflowAppService` | 0 | 1 | — |
| `CtpApplicationBaseAppService` | 4 | 6 | `create(SingleRequest)`, `update(SingleRequest)`, `updateStatus(SingleRequest, SingleRequest)`, `updateOnlineStatus(SingleRequest, SingleRequest)` |
| `CtpApplicationCommonAppService` | 9 | 10 | `selectCategoryApplications(SingleRequest, Object>>)`, `selectCategorySetting(SingleRequest)`, `selectApplicationsByCategoryAndClientScope(SingleRequest, Object>>)`, `selectAdminAppIdsByUserIdAndOrgId(ListRequest)`, `selectEnabledApplications(SingleRequest, Object>>)` …+4 |
| `CtpApplicationAuthCoreAppService` | 4 | 6 | `selectApplicationAuthByAppId(SingleRequest)`, `selectAuthAppIdsByOrgId(SingleRequest)`, `selectAuthAppIds(SingleRequest, Object>>)`, `selectWithOutAuthAllAppIdsByOrgId(SingleRequest)` |
| `CtpApplicationCoreAppService` | 3 | 3 | `selectListByConditions(ListRequest)`, `selectPageByConditions(PageRequest)`, `selectAppStatusListIgnoreTenantId()` |
| `CtpCapabilityCoreAppService` | 1 | 1 | `selectListByConditions(ListRequest)` |
| `CtpCategoryCoreAppService` | 2 | 2 | `selectListByConditions(ListRequest)`, `selectQuickListByConditions(ListRequest)` |
| `CtpPersonalPlanCoreAppService` | 3 | 4 | `createOrUpdateBatch(SingleRequest)`, `createRedirectBatch(SingleRequest)`, `deleteByIds(SingleRequest)` |
| `ApplicationHandler` | 0 | 2 | — |
| `CtpAccessLogService` | 2 | 2 | `selectAccessLogPageByConditions(ListRequest)`, `selectAccessByConditions(PageRequest)` |
| `CtpManagerTenantAppService` | 14 | 14 | `create(SingleRequest)`, `updateByUseTenantId(SingleRequest)`, `deleteByUseTenantId(SingleRequest)`, `updateStatusByUseTenantId(SingleRequest)`, `selectByUseTenantId(SingleRequest)` …+9 |
| `OpenApiTenantConstant` | 0 | 0 | — |
| `CtpMessageAppService` | 0 | 5 | — |
| `CtpMessageClientAppService` | 0 | 12 | — |
| `CtpMessageManageAppService` | 8 | 8 | `onlineInfo(SingleRequest)`, `kickOffline(SingleRequest)`, `selectBySetType(SingleRequest, Object>>)`, `selectListByUserId(SingleRequest)`, `set(SingleRequest)` …+3 |
| `CtpMessageOpenApiService` | 3 | 3 | `sendMessageSimple(SingleRequest)`, `sendMessage(SingleRequest)`, `saveMessageTemplate(SingleRequest)` |
| `CtpMessageOperateAppService` | 1 | 1 | `deleteMessageByIdentification(SingleRequest)` |
| `CtpMessageSourceTypeAppService` | 2 | 2 | `createSource(SingleRequest)`, `createType(SingleRequest)` |
| `CtpMessageTypeAppService` | 0 | 3 | — |
| `CtpMessageUserSubscribeAppService` | 0 | 3 | — |
| `CtpUdcMessageSendAppService` | 2 | 2 | `sendMessageByUser(SingleRequest)`, `sendMessageByChooseJson(SingleRequest)` |
| `UserChannelCache` | 0 | 0 | — |
| `CtpMessageConstants` | 0 | 0 | — |
| `MessageConstant` | 0 | 0 | — |
| `MqMessageConstant` | 0 | 0 | — |
| `ReSendConstants` | 0 | 0 | — |
| `PushChannel` | 0 | 1 | — |
| `WheelTimerConstants` | 0 | 0 | — |
| `CtpMessageReceiveProcessService` | 0 | 1 | — |
| `SubscribeProcessService` | 0 | 1 | — |
| `MessageUtil` | 0 | 1 | — |
| `LoadJarResourceAppService` | 2 | 2 | `getJsonMetadataData(SingleRequest)`, `getRuntimeJsonData(SingleRequest)` |
| `ThirdPermissionAppService` | 1 | 1 | `checkPermissionByUser(SingleRequest)` |
| `CtpUserBpmAppService` | 1 | 1 | `selectUserResourceIgnoreTenant(PageInfo, Map, Object>)` |
| `CtpDeviceBindCommonAppService` | 3 | 3 | `bindDevice(SingleRequest)`, `batchUnbindDevice(SingleRequest)`, `selectByConditions(SingleRequest, Object>>)` |
| `CtpMenuCommonAppService` | 2 | 2 | `selectChildrenByCode(SingleRequest)`, `selectListByConditions(ListRequest)` |
| `CtpResourceCommonAppService` | 2 | 2 | `selectDesignResources(ListRequest)`, `deleteDesignResources(SingleRequest)` |
| `CtpSecretCommonAppService` | 12 | 13 | `selectSecretEnable()`, `selectSecretLevelEnumItem()`, `selectOrgSecretLevelEnumItem()`, `selectSecretLevelEnumItemByValue(SingleRequest)`, `selectSecretLevelEnumItemByOrderNo(SingleRequest)` …+7 |
| `CtpUserCommonAppService` | 3 | 4 | `getUserInfo(SingleRequest)`, `selectUserByLoginName(SingleRequest)`, `getLoginPageSetParameter()` |
| `CtpUserDefaultIdentityCommonAppService` | 3 | 3 | `selectDefaultSwitchAdminOrg(SingleRequest)`, `selectUDefaultseIdentityInfo(ListRequest)`, `selectFrontUserDefaultTenant(ListRequest)` |
| `CtpUserPermissionCommonAppService` | 15 | 19 | `selectUserResourceCode(SingleRequest)`, `checkUserResourceCode(SingleRequest)`, `selectUserResource(SingleRequest)`, `selectUserResource(PageInfo, CtpUserResourceSearchDto)`, `checkUserResource(SingleRequest)` …+10 |
| `CtpUserRoleCommonAppService` | 5 | 5 | `selectUserByRoleCode(SingleRequest, Object>>)`, `selectPageUserByRoleCode(PageRequest)`, `selectUserByRoleCodeSearch(SingleRequest)`, `selectUserIdByRoleCode(SingleRequest, Object>>)`, `hasRoleByOrgCode(SingleRequest)` |
| `CtpAuthCoreAppService` | 12 | 13 | `authenticate(SingleRequest)`, `switchAdmin(SingleRequest)`, `switchOrg(SingleRequest, Object>>)`, `switchUser(SingleRequest)`, `getLoginUserInfo(SingleRequest, Object>>)` …+7 |
| `CtpDataAuditCoreAppService` | 1 | 1 | `create(SingleRequest)` |
| `CtpLoginLogCoreAppService` | 1 | 1 | `selectPageByConditions(PageRequest)` |
| `CtpLoginPreConfigAppService` | 6 | 6 | `selectByOrgId(SingleRequest)`, `createOrUpdate(SingleRequest)`, `allowChildCustomDefine()`, `allowChildCustomDefine(SingleRequest)`, `selectByUri(SingleRequest)` …+1 |
| `CtpResourceCoreAppService` | 8 | 8 | `register(SingleRequest)`, `registerBatch(SingleRequest)`, `registerResourcePermissionBatch(SingleRequest)`, `updateByCode(SingleRequest)`, `deleteByConditions(SingleRequest, Object>>)` …+3 |
| `CtpResourcePermissionCoreAppService` | 4 | 4 | `register(SingleRequest)`, `deleteByResourceCode(SingleRequest)`, `selectByResourceCode(SingleRequest)`, `selectListByConditions(SingleRequest, Object>>)` |
| `CtpResourceTypeCoreAppService` | 1 | 1 | `selectListByConditions(ListRequest)` |
| `CtpRoleCoreAppService` | 8 | 14 | `create(SingleRequest)`, `update(SingleRequest)`, `selectById(SingleRequest)`, `selectByCode(SingleRequest)`, `selectByIds(SingleRequest)` …+3 |
| `CtpRoleResourceCoreAppService` | 0 | 1 | — |
| `CtpThirdPlatformConfigCoreAppService` | 7 | 7 | `create(SingleRequest)`, `update(SingleRequest)`, `deleteByIds(SingleRequest)`, `selectById(SingleRequest)`, `selectOneByConditions(SingleRequest, Object>>)` …+2 |
| `CtpUserBindMappingAppService` | 7 | 7 | `saveUpdate(SingleRequest)`, `selectOneByCondition(SingleRequest, Object>>)`, `selectListByConditions(ListRequest)`, `pageUserMappingByUserIds(SingleRequest)`, `listUserMappingByUserIds(SingleRequest)` …+2 |
| `CtpUserCoreAppService` | 15 | 18 | `beforeCreateCheck(SingleRequest)`, `create(SingleRequest)`, `createBatch(SingleRequest)`, `beforeUpdateCheck(SingleRequest)`, `update(SingleRequest)` …+10 |
| `CtpUserResourceCoreAppService` | 4 | 4 | `createBatch(SingleRequest)`, `deleteByConditions(SingleRequest, Object>>)`, `selectListByConditions(ListRequest)`, `selectPageListByConditions(PageRequest)` |
| `CtpUserRoleAppService` | 4 | 4 | `selectCascadeById(SingleRequest)`, `selectCascadeByIds(SingleRequest)`, `dynamicJoinSelect(SingleRequest)`, `dynamicSelect(SingleRequest)` |
| `CtpUserRoleCoreAppService` | 8 | 13 | `createBatch(SingleRequest)`, `createUserRule(SingleRequest)`, `createAuthorizationRule(SingleRequest)`, `deleteAuthorizationRuleById(SingleRequest)`, `deleteByIds(SingleRequest)` …+3 |
| `CtpAuthorizationRuleOrgAppService` | 8 | 9 | `create(SingleRequest)`, `update(SingleRequest)`, `delete(SingleRequest)`, `selectPageByConditions(PageRequest)`, `selectAuthorizationObject(SingleRequest)` …+3 |
| `CtpOrgAdminOrgAppService` | 7 | 13 | `configAdmin(SingleRequest)`, `selectByOrgId(SingleRequest)`, `selectByOrgIds(SingleRequest)`, `selectByUserId(SingleRequest)`, `selectPageByConditions(PageRequest)` …+2 |
| `CtpOrgSelectPeopleAppService` | 1 | 1 | `selectPageByConditions(PageRequest)` |
| `CtpOrgUpgradeAppService` | 1 | 1 | `updateBatchUserCode(SingleRequest, String>>)` |
| `CtpPermissionApprovalOrgAppService` | 4 | 4 | `update(SingleRequest)`, `selectById(SingleRequest)`, `batchKnow()`, `selectPageByConditions(PageRequest)` |
| `CtpSecretApprovalOrgAppService` | 2 | 2 | `create(SingleRequest)`, `selectPendingInfo(SingleRequest)` |
| `SyncOrgRoleTempAppService` | 1 | 1 | `syncOrgRole(SingleRequest, Set)` |
| `CtpAuthorizationUdcAppService` | 2 | 2 | `autoAuthAppRoles(SingleRequest)`, `selectAppFirstLinks(SingleRequest)` |
| `ConditionCache` | 0 | 1 | — |
| `CtpUserStopWatchNoReturnFunction` | 0 | 1 | — |
| `CtpUserStopWatchReturnFunction` | 0 | 1 | — |
| `CtpUserSyTokenService` | 0 | 5 | — |
| `UserAuditLog` | 0 | 4 | — |
| `AuthConfigAnn` | 0 | 3 | — |
| `WhiteListAnn` | 0 | 0 | — |
| `ReloadAuthConfigChain` | 0 | 2 | — |
| `CtpAvoidLoginUserService` | 0 | 5 | — |
| `DefaultAvoidLoginService` | 0 | 1 | — |
| `SyTokenProcessorService` | 0 | 1 | — |
| `CtpUserLogInvoker` | 0 | 1 | — |
| `LogDownload` | 0 | 6 | — |
| `CipMobileMultiVersionService` | 0 | 6 | — |
| `SsoBlankProperties` | 0 | 5 | — |
| `ExtAuthHandler` | 0 | 2 | — |
| `ThirdAuthHand` | 0 | 6 | — |
| `DataMultiVersionAdaptation` | 0 | 1 | — |
| `RetrievePasswordProvider` | 0 | 8 | — |
| `SecurityCheckServiceSpi` | 3 | 3 | `preCheckPermission(HttpServletRequest, Object, Set, String[])`, `postCheckPermission(HttpServletRequest)`, `afterCheckPermissionCompletion(HttpServletRequest, Exception)` |
| `UserTenantInitServiceSpi` | 2 | 2 | `getInitType()`, `doInit()` |
| `GatewayConstant` | 0 | 0 | — |
| `ReactiveDiscovery` | 0 | 2 | — |
| `CookieConstants` | 0 | 0 | — |
| `FilterOrders` | 0 | 0 | — |
| `GatewayErrorCode` | 0 | 0 | — |
| `LogPrint` | 0 | 0 | — |
| `WebApiConstants` | 0 | 0 | — |

## com.seeyon.cdp（97）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `DevicePermissionManager` | 0 | 2 | — |
| `OrgManager` | 0 | 7 | — |
| `PermissionManager` | 0 | 5 | — |
| `ResourceManager` | 0 | 2 | — |
| `RowColumnAuthManager` | 0 | 10 | — |
| `SystemVariableManager` | 0 | 3 | — |
| `UserManager` | 0 | 9 | — |
| `ReportOpenApiAppService` | 2 | 2 | `getReportDetail(SingleRequest)`, `getReportResult(SingleRequest)` |
| `QueryEngine` | 0 | 3 | — |
| `FastCalHandler` | 0 | 2 | — |
| `SqlProcessor` | 0 | 3 | — |
| `DimensionSqlProcessor` | 0 | 1 | — |
| `MetricSqlProcessor` | 0 | 1 | — |
| `ComponentExport` | 0 | 5 | — |
| `DefinitionPostBeforeHandler` | 0 | 1 | — |
| `QueryPostAfterHandler` | 0 | 1 | — |
| `QueryPostBeforeHandler` | 0 | 1 | — |
| `RequestPostBeforeHandler` | 0 | 1 | — |
| `VisualizationPostAfterHandler` | 0 | 0 | — |
| `VisualizationPostBeforeHandler` | 0 | 1 | — |
| `VisualizationPostHandler` | 0 | 1 | — |
| `IComponentQuery` | 0 | 2 | — |
| `FilterCondition` | 0 | 0 | — |
| `LeafCondition` | 0 | 0 | — |
| `ComponentValidate` | 0 | 2 | — |
| `OtherValidate` | 0 | 1 | — |
| `VisualizingStrategy` | 0 | 2 | — |
| `CdpBiz4UdcAppService` | 2 | 17 | `deploy(SingleRequest)`, `detectionV2(SingleRequest)` |
| `ItemOperationAuth` | 0 | 3 | — |
| `ModelAuth` | 0 | 3 | — |
| `Plugin` | 0 | 2 | — |
| `ReportAuth` | 0 | 3 | — |
| `UdcAppAuth` | 0 | 1 | — |
| `CascadeUpdateHandler` | 0 | 4 | — |
| `ComponentParamFiller` | 0 | 1 | — |
| `CdpTaskConstant` | 0 | 0 | — |
| `V5IntegrationConstant` | 0 | 0 | — |
| `Cap3FieldPropConst` | 0 | 0 | — |
| `Cap3FormConst` | 0 | 0 | — |
| `Cap4AppConst` | 0 | 0 | — |
| `Cap4FieldPropConst` | 0 | 0 | — |
| `Cap4FormConst` | 0 | 0 | — |
| `V5FormSource` | 0 | 3 | — |
| `SqlComponentFactory` | 0 | 3 | — |
| `EtlCallbackHandler` | 0 | 2 | — |
| `CdpJdbcURL` | 0 | 2 | — |
| `OracleJdbcURLPattern` | 0 | 0 | — |
| `MetadataInst` | 0 | 13 | — |
| `MetadataInstFactory` | 0 | 1 | — |
| `MetadataIdentifier` | 0 | 1 | — |
| `V5MetadataConstants` | 0 | 0 | — |
| `V8MetadataConstants` | 0 | 0 | — |
| `AppPropConstants` | 0 | 0 | — |
| `AttrPropConstants` | 0 | 0 | — |
| `EntityPropConstants` | 0 | 0 | — |
| `ReferPropConstants` | 0 | 0 | — |
| `CdpDataDeploy` | 0 | 7 | — |
| `CdpDataDetection` | 0 | 1 | — |
| `TransportInAble` | 0 | 1 | — |
| `TransportAfterIn` | 0 | 1 | — |
| `TransportBeforeIn` | 0 | 1 | — |
| `TransportOutAble` | 0 | 1 | — |
| `ConsistencyPartValidate` | 0 | 5 | — |
| `DatasetOpenApiAppService` | 2 | 2 | `getDatasetModel(SingleRequest)`, `getDatasetResult(SingleRequest)` |
| `DataPreviewService` | 0 | 2 | — |
| `DatasetToStreamConvertor` | 0 | 13 | — |
| `CdpDatabaseService` | 0 | 6 | — |
| `CdpDataSource` | 0 | 9 | — |
| `CdpDataSourceDataType` | 0 | 1 | — |
| `ConnectionCallback` | 0 | 1 | — |
| `CdpEtlRunAppService` | 1 | 1 | `jobSuccess(SingleRequest)` |
| `CdpEtlSourceAppService` | 1 | 2 | `getSource(SingleRequest)` |
| `IndexAppService` | 4 | 4 | `search(PageDtoRequest)`, `suggest(SingleRequest)`, `hotSearch(SingleRequest)`, `searchHistory(SingleRequest)` |
| `IndexStoreAppService` | 5 | 5 | `save(SingleRequest)`, `updateIndexAuth(SingleRequest)`, `delete(SingleRequest)`, `batchDelete(SingleRequest)`, `saveIndexBpmData(SingleRequest)` |
| `IndexParamsResetServiceSpi` | 1 | 1 | `paramsReset(SearchConditionDto)` |
| `IndicatorOpenApiAppService` | 2 | 2 | `getIndicatorModel(SingleRequest)`, `getIndicatorResult(SingleRequest)` |
| `DsAdapter` | 0 | 6 | — |
| `CkClusterAdapter` | 0 | 3 | — |
| `AliasTrait` | 0 | 1 | — |
| `Location` | 0 | 1 | — |
| `Dialect` | 0 | 45 | — |
| `CkClusterTableOperations` | 0 | 7 | — |
| `StateStore` | 0 | 4 | — |
| `DataReader` | 0 | 3 | — |
| `DataWriter` | 0 | 4 | — |
| `TableSyncTask` | 0 | 1 | — |
| `InnerWriter` | 0 | 3 | — |
| `SchJobBuildService` | 0 | 3 | — |
| `SyncJobPublisher` | 0 | 3 | — |
| `StreamNodeHandler` | 0 | 2 | — |
| `Handler` | 0 | 5 | — |
| `JobRunner` | 0 | 11 | — |
| `JobRunnerDecorator` | 0 | 9 | — |
| `StreamOpenApiAppService` | 2 | 2 | `getStreamModel(SingleRequest)`, `getStreamResult(SingleRequest)` |
| `EntityMetadataBuilder` | 0 | 1 | — |
| `StreamNodeFunction` | 0 | 2 | — |
| `StreamNode` | 0 | 7 | — |

## com.seeyon.organization（60）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `EncryptFilter` | 2 | 2 | `isDecrypt()`, `isEncrypt()` |
| `OrgAffairAppService` | 1 | 1 | `selectByIdOrCode(SingleRequest)` |
| `OrgAppCommonAppService` | 2 | 2 | `selectAccessViewMember(SingleRequest)`, `selectAccessViewOrg(SingleRequest)` |
| `AuthorizationAppService` | 1 | 1 | `registerAppResourceAndPermission(SingleRequest)` |
| `OrgEdocAppService` | 1 | 1 | `selectSortByIds(SingleRequest)` |
| `OrgMobileAppService` | 2 | 2 | `selectPagePhoneNumber(PageRequest)`, `selectOfflineStorageKey(SingleRequest)` |
| `OcipLevelAppService` | 4 | 4 | `pushAll(SingleRequest)`, `pushAllByIncrement(SingleRequest)`, `pushBatch(SingleRequest)`, `pushLevelIncrement(SingleRequest)` |
| `OcipMemberAppService` | 4 | 4 | `pushAll(SingleRequest)`, `pushAllByIncrement(SingleRequest)`, `pushBatch(SingleRequest)`, `pushMemberIncrement(SingleRequest)` |
| `OcipPostAppService` | 4 | 4 | `pushAll(SingleRequest)`, `pushAllByIncrement(SingleRequest)`, `pushBatch(SingleRequest)`, `pushPostIncrement(SingleRequest)` |
| `OcipUnitAppService` | 8 | 8 | `pushAccountAll(SingleRequest)`, `pushAccountAllByIncrement(SingleRequest)`, `pushAccountBatch(SingleRequest)`, `pushAccountIncrement(SingleRequest)`, `pushDepartmentAll(SingleRequest)` …+3 |
| `OrgPlatformAppService` | 1 | 1 | `selectWatermarkInfoByMemberId(SingleRequest)` |
| `OrgPortalAppService` | 10 | 10 | `selectSwitchInstitution(PageRequest)`, `selectSwitchInstitutions(SingleRequest)`, `selectSwitchInstitutionByMemberId(SingleRequest)`, `selectLoginUserInfo(SingleRequest)`, `selectCurrentLoginUserInfo(SingleRequest, Object>>)` …+5 |
| `MultiOrgDepSyncService` | 2 | 2 | `multiOrgCreateBatch(SingleRequest)`, `selectPageChildrenByCondition(PageDtoRequest)` |
| `MultiOrgMemberSyncService` | 2 | 2 | `MultiOrgMemberCreateBatch(SingleRequest)`, `selectByCodes(PageDtoRequest)` |
| `MultiOrgSyncService` | 2 | 2 | `multiOrgCreateBatch(SingleRequest)`, `selectByCodes(SingleRequest)` |
| `OrgJobSyncAppService` | 3 | 4 | `selectByCodes(SingleRequest)`, `createBatch(SingleRequest)`, `selectPageByConditions(PageDtoRequest)` |
| `OrgLevelSyncAppService` | 3 | 4 | `selectByCodes(SingleRequest)`, `createBatch(SingleRequest)`, `selectPageByConditions(PageDtoRequest)` |
| `OrgMemberRoleSyncService` | 1 | 1 | `createBatch(SingleRequest)` |
| `OrgMemberSyncAppService` | 12 | 14 | `createBatch(SingleRequest)`, `selectByCodes(SingleRequest)`, `selectByCondition(PageDtoRequest)`, `createBatchMemberPost(SingleRequest)`, `createBatchMemberMetadata(SingleRequest)` …+7 |
| `OrgPostSyncAppService` | 3 | 4 | `createBatch(SingleRequest)`, `selectByCodes(SingleRequest)`, `selectPageByConditions(PageDtoRequest)` |
| `OrgRoleSyncService` | 2 | 2 | `createBatch(SingleRequest)`, `selectByCodes(SingleRequest)` |
| `OrgTeamSyncAppService` | 4 | 4 | `selectByCode(SingleRequest)`, `selectPageByConditions(PageDtoRequest)`, `create(SingleRequest)`, `createBatch(SingleRequest)` |
| `OrgUnitSyncAppService` | 7 | 8 | `createBatch(SingleRequest)`, `createBatchUnitMetadata(SingleRequest)`, `selectByCodes(SingleRequest)`, `selectChildrenByCondition(SingleRequest)`, `selectPageChildrenByCondition(PageDtoRequest)` …+2 |
| `OrgZhongheService` | 0 | 14 | — |
| `OrgWorkFlowAppService` | 30 | 37 | `selectMemberPostBySelectPeople(SingleRequest)`, `selectMemberPostBySelectPeoples(SingleRequest, List)`, `selectListByCondition(SingleRequest)`, `selectListByMetaCondition(SingleRequest)`, `isOfUp(SingleRequest)` …+25 |
| `OrgCommonAppService` | 35 | 45 | `selectMemberInfoById(SingleRequest)`, `selectMemberDepartmentInfoById(SingleRequest)`, `selectMemberBySelectPeopleData(SingleRequest)`, `selectPageMemberBySelectPeopleData(PageDtoRequest)`, `selectMemberBySelectPeopleDatas(SingleRequest)` …+30 |
| `OrgBusinessBaseAppService` | 10 | 11 | `selectById(SingleRequest)`, `selectByIds(SingleRequest)`, `selectCascadeById(SingleRequest)`, `selectCascadeByIds(SingleRequest)`, `selectListByConditions(ListRequest)` …+5 |
| `OrgBusinessCoreAppService` | 1 | 1 | `selectBusinessListByCondition(SingleRequest, Object>>)` |
| `OrgInstitutionExecutiveAppService` | 1 | 1 | `checkUserExecutiveHide(SingleRequest)` |
| `OrgJobBaseAppService` | 14 | 14 | `create(SingleRequest)`, `update(SingleRequest)`, `selectById(SingleRequest)`, `selectByIds(SingleRequest)`, `selectCascadeById(SingleRequest)` …+9 |
| `OrgJobCoreAppService` | 6 | 6 | `selectJobById(SingleRequest)`, `selectJobByIds(SingleRequest)`, `selectJobListByCondition(SingleRequest, Object>>)`, `selectJobPageListByCondition(PageRequest)`, `selectJobListPropertiesByJobIds(SingleRequest)` …+1 |
| `OrgLevelBaseAppService` | 14 | 14 | `create(SingleRequest)`, `update(SingleRequest)`, `selectById(SingleRequest)`, `selectByIds(SingleRequest)`, `selectCascadeById(SingleRequest)` …+9 |
| `OrgLevelCoreAppService` | 6 | 6 | `selectLevelById(SingleRequest)`, `selectLevelByIds(SingleRequest)`, `selectLevelListByCondition(SingleRequest, Object>>)`, `selectLevelPageListByCondition(PageRequest)`, `selectLevelListPropertiesByLevelIds(SingleRequest)` …+1 |
| `OrgMemberBaseAppService` | 16 | 18 | `create(SingleRequest)`, `update(SingleRequest)`, `selectById(SingleRequest)`, `selectByIds(SingleRequest)`, `selectCascadeById(SingleRequest)` …+11 |
| `OrgMemberCoreAppService` | 13 | 13 | `selectMemberById(SingleRequest)`, `selectMemberInfoById(SingleRequest)`, `selectMemberByIds(SingleRequest)`, `selectMemberByIdsIgnoreTenantId(SingleRequest)`, `selectMemberInfoByIds(SingleRequest)` …+8 |
| `OrgMemberPostBaseAppService` | 12 | 13 | `create(SingleRequest)`, `update(SingleRequest)`, `selectById(SingleRequest)`, `selectByIds(SingleRequest)`, `selectCascadeById(SingleRequest)` …+7 |
| `OrgMemberPostCoreAppService` | 5 | 5 | `selectMemberPostListByCondition(SingleRequest, Object>>)`, `selectMemberPostListByMemberIds(SingleRequest)`, `selectMemberPostPageListByCondition(PageRequest)`, `selectMemberPostListPropertiesByMemberIds(SingleRequest)`, `selectMemberPostPageListPropertiesByCondition(PageDtoRequest)` |
| `OrgMemberRoleBaseAppService` | 11 | 13 | `selectById(SingleRequest)`, `selectByIds(SingleRequest)`, `selectCascadeById(SingleRequest)`, `selectCascadeByIds(SingleRequest)`, `selectListByConditions(ListRequest)` …+6 |
| `OrgMemberRoleCoreAppService` | 4 | 4 | `selectById(SingleRequest)`, `selectByIds(SingleRequest)`, `selectListByConditions(SingleRequest, Object>>)`, `selectPageByConditions(PageRequest)` |
| `OrgMetadataCoreAppService` | 12 | 16 | `selectOrgMetadataColumnListByCondition(SingleRequest, Object>>)`, `selectMetadataColumnList(SingleRequest)`, `selectPageMetadataColumnList(PageRequest)`, `selectOrgByUnitMemberMetadata(SingleRequest, Object>>)`, `selectMemberByUnitMetadata(SingleRequest, Object>>)` …+7 |
| `OrgRoleBaseAppService` | 11 | 13 | `selectById(SingleRequest)`, `selectByIds(SingleRequest)`, `selectCascadeById(SingleRequest)`, `selectCascadeByIds(SingleRequest)`, `selectListByConditions(ListRequest)` …+6 |
| `OrgRoleCoreAppService` | 4 | 4 | `selectById(SingleRequest)`, `selectByIds(SingleRequest)`, `selectListByConditions(SingleRequest, Object>>)`, `selectPageByConditions(PageRequest)` |
| `OrgPostBaseAppService` | 14 | 14 | `create(SingleRequest)`, `update(SingleRequest)`, `selectById(SingleRequest)`, `selectByIds(SingleRequest)`, `selectCascadeById(SingleRequest)` …+9 |
| `OrgPostCoreAppService` | 6 | 6 | `selectPostById(SingleRequest)`, `selectPostByIds(SingleRequest)`, `selectPostListByCondition(SingleRequest, Object>>)`, `selectPostPageListByCondition(PageRequest)`, `selectPostListPropertiesByPostIds(SingleRequest)` …+1 |
| `OrgSystemTeamCoreAppService` | 5 | 5 | `selectTeamMemberByTeamId(SingleRequest)`, `selectTeamMemberByTeamIds(SingleRequest)`, `selectTeamById(SingleRequest)`, `selectTeamByIds(SingleRequest)`, `selectTeamByCondition(PageRequest)` |
| `OrgUnitBaseAppService` | 20 | 20 | `create(SingleRequest)`, `update(SingleRequest)`, `selectById(SingleRequest)`, `selectByIds(SingleRequest)`, `selectOrgById(SingleRequest)` …+15 |
| `OrgUnitCoreAppService` | 13 | 13 | `selectOrgById(SingleRequest)`, `selectOrgInfoById(SingleRequest)`, `selectOrgByIds(SingleRequest)`, `selectOrgByIdsIgnoreTenantId(SingleRequest)`, `selectOrgInfoByIds(SingleRequest)` …+8 |
| `OrgUnitTeamCoreAppService` | 6 | 8 | `create(SingleRequest)`, `delete(SingleRequest)`, `selectUnitTeamById(SingleRequest)`, `selectUnitTeamByIds(SingleRequest)`, `selectUnitTeamListByCondition(SingleRequest, Object>>)` …+1 |
| `OrgUnitVerticalBaseAppService` | 10 | 10 | `selectById(SingleRequest)`, `selectByIds(SingleRequest)`, `selectCascadeById(SingleRequest)`, `selectCascadeByIds(SingleRequest)`, `selectListByConditions(ListRequest)` …+5 |
| `OrgUnitVerticalCoreAppService` | 1 | 1 | `selectUnitVerticalListByCondition(SingleRequest, Object>>)` |
| `OrgParameterCoreAppService` | 1 | 1 | `selectValueByParamsKey(SingleRequest)` |
| `OrgSelectPeopleForDeptAppService` | 3 | 3 | `departmentTree(SingleRequest)`, `selectOrgPath(SingleRequest)`, `departmentTreeExtensionList(SingleRequest)` |
| `OrgSelectPeopleForInstAppService` | 2 | 2 | `selectFirstChildrenUnits(SingleRequest)`, `searchInstitution(SingleRequest)` |
| `OrgSelectPeopleForMemberAppService` | 2 | 2 | `searchMemberByGroup(SingleRequest)`, `selectMembersByOrg(PageRequest)` |
| `TenantManageAppService` | 1 | 1 | `selectEnableUnitNumIgnoreTenant()` |
| `WorkFlowMatchService` | 0 | 2 | — |
| `ConditionCache` | 0 | 1 | — |
| `SelectPeopleListService` | 0 | 9 | — |
| `SelectPeopleService` | 0 | 37 | — |
| `OrgAuditLog` | 0 | 4 | — |

## com.seeyon.app（30）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `ApprovalAppService` | 0 | 4 | — |
| `ApprovalFrameApiTransportAppService` | 1 | 1 | `exportApprovalFrameInfo(SingleRequest)` |
| `ApprovalInvokeAppService` | 0 | 19 | — |
| `AppFeatureHandler` | 0 | 4 | — |
| `ApprovalInitExtInterface` | 0 | 3 | — |
| `ApprovalTransportOperation` | 0 | 2 | — |
| `AgentCommonAppService` | 9 | 9 | `selectByAgentUserId(SingleRequest, Object>>)`, `hasAgent(SingleRequest)`, `selectByUserIdAndTemplate(SingleRequest)`, `selectById(SingleRequest)`, `create(SingleRequest)` …+4 |
| `AgentCoreAppService` | 9 | 10 | `selectListByCondition(SingleRequest, Object>>)`, `create(SingleRequest)`, `update(SingleRequest)`, `selectById(SingleRequest)`, `selectByIds(SingleRequest)` …+4 |
| `AssociateCommonAppService` | 2 | 3 | `selectEntityConfigByConditions(ListRequest)`, `selectAssociateCompleteByAppName(SingleRequest)` |
| `MyAttentionCommonAppService` | 7 | 9 | `create(SingleRequest)`, `deleteByObjectIdOrPageUrl(SingleRequest, Object>>)`, `isAttention(SingleRequest, Object>>)`, `getAttentionByObjectIds(SingleRequest)`, `getAttentionUserIdsByObjectIds(SingleRequest)` …+2 |
| `CategoryCommonAppService` | 8 | 12 | `create(SingleRequest)`, `update(SingleRequest)`, `deleteById(SingleRequest)`, `selectById(SingleRequest)`, `selectListByConditions(ListRequest)` …+3 |
| `FileTransfer` | 0 | 5 | — |
| `ImageAppService` | 4 | 4 | `create(SingleRequest)`, `update(SingleRequest)`, `selectImage(PageRequest)`, `deleteImage(SingleRequest)` |
| `ImageCategoryAppService` | 4 | 4 | `save(SingleRequest)`, `selectImageCategory(SingleRequest)`, `deleteCategory(SingleRequest)`, `selectCountByCategoryId(SingleRequest)` |
| `ImageStoreAppService` | 4 | 4 | `save(SingleRequest)`, `selectImageStore()`, `deleteStore(SingleRequest)`, `selectStoreAndCategory()` |
| `IntegralPermission` | 0 | 1 | — |
| `IntegralLedgerOprateAppService` | 4 | 4 | `create(SingleRequest)`, `createBatch(SingleRequest)`, `selectPageByConditions(PageDtoRequest)`, `selectRankById(SingleRequest)` |
| `LabelAppService` | 3 | 3 | `updateReferenceCount(SingleRequest)`, `batchUpdateReferenceCount(SingleRequest)`, `batchSelectLabelDtos(SingleRequest)` |
| `MgnAggDataInitAppService` | 4 | 4 | `selectListByConditions(ListRequest)`, `selectListByMap(SingleRequest, Object>>)`, `create(SingleRequest)`, `update(SingleRequest)` |
| `QrCodeCommonAppService` | 2 | 2 | `create(SingleRequest)`, `selectByJson(SingleRequest)` |
| `SealCommonAppService` | 3 | 3 | `selectUsableList(ListRequest)`, `checkSealPassword(SingleRequest)`, `selectListByCondition(ListRequest)` |
| `SensitiveResultService` | 0 | 2 | — |
| `StyleFileAppService` | 1 | 1 | `getCurrentTenantPortalFile()` |
| `SystemConfigCommonAppService` | 3 | 4 | `getI18nConfig(SingleRequest, Object>>)`, `getSystemConfig(SingleRequest, Object>>)`, `saveSystemConfig(SingleRequest, Object>>)` |
| `ThemeAppService` | 4 | 4 | `selectById(SingleRequest)`, `create(SingleRequest)`, `selectPagePropertiesByConditions(PageRequest)`, `publishById(SingleRequest)` |
| `ThemeConstants` | 0 | 0 | — |
| `VideoMeetingRoomCommonAppService` | 2 | 2 | `selectById(SingleRequest)`, `selectAuthedVideoMeetingRoomList()` |
| `WaterMarkCommonAppService` | 1 | 1 | `getWaterMarkConfig(SingleRequest, Object>>)` |
| `WorktimeAppService` | 12 | 12 | `selectWorktimeByOrgIdAndYear(SingleRequest)`, `selectByOrgIdAndYear(SingleRequest)`, `getByParentOrgIdAndYear(SingleRequest)`, `getWorkTimeByYear(SingleRequest)`, `getWorkTimeBetweenYear(SingleRequest)` …+7 |
| `FestivalService` | 0 | 4 | — |

## antlr.v4.runtime（23）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `ANTLRErrorListener` | 4 | 4 | `syntaxError(Recognizer, ?>, Object, int, int, String, RecognitionException)`, `reportAmbiguity(Parser, DFA, int, int, boolean, BitSet, ATNConfigSet)`, `reportAttemptingFullContext(Parser, DFA, int, int, BitSet, ATNConfigSet)`, `reportContextSensitivity(Parser, DFA, int, int, int, ATNConfigSet)` |
| `ANTLRErrorStrategy` | 7 | 7 | `reset(Parser)`, `recoverInline(Parser)`, `recover(Parser, RecognitionException)`, `sync(Parser)`, `inErrorRecoveryMode(Parser)` …+2 |
| `CharStream` | 1 | 1 | `getText(Interval)` |
| `IntStream` | 8 | 8 | `consume()`, `LA(int)`, `mark()`, `release(int)`, `index()` …+3 |
| `Token` | 10 | 10 | `getText()`, `getType()`, `getLine()`, `getCharPositionInLine()`, `getChannel()` …+5 |
| `TokenFactory` | 2 | 2 | `create(Pair, CharStream>, int, String, int, int, int, int, int)`, `create(int, String)` |
| `TokenSource` | 7 | 7 | `nextToken()`, `getLine()`, `getCharPositionInLine()`, `getInputStream()`, `getSourceName()` …+2 |
| `TokenStream` | 7 | 7 | `LT(int)`, `get(int)`, `getTokenSource()`, `getText(Interval)`, `getText()` …+2 |
| `Vocabulary` | 4 | 4 | `getMaxTokenType()`, `getLiteralName(int)`, `getSymbolicName(int)`, `getDisplayName(int)` |
| `WritableToken` | 6 | 6 | `setText(String)`, `setType(int)`, `setLine(int)`, `setCharPositionInLine(int)`, `setChannel(int)` …+1 |
| `LexerAction` | 3 | 3 | `getActionType()`, `isPositionDependent()`, `execute(Lexer)` |
| `EqualityComparator` | 2 | 2 | `hashCode(T)`, `equals(T, T)` |
| `IntSet` | 13 | 13 | `add(int)`, `addAll(IntSet)`, `and(IntSet)`, `complement(IntSet)`, `or(IntSet)` …+8 |
| `NotNull` | 0 | 0 | — |
| `Predicate` | 1 | 1 | `test(T)` |
| `ErrorNode` | 0 | 0 | — |
| `ParseTree` | 6 | 8 | `getParent()`, `getChild(int)`, `setParent(RuleContext)`, `accept(T>)`, `getText()` …+1 |
| `ParseTreeListener` | 4 | 4 | `visitTerminal(TerminalNode)`, `visitErrorNode(ErrorNode)`, `enterEveryRule(ParserRuleContext)`, `exitEveryRule(ParserRuleContext)` |
| `ParseTreeVisitor` | 4 | 4 | `visit(ParseTree)`, `visitChildren(RuleNode)`, `visitTerminal(TerminalNode)`, `visitErrorNode(ErrorNode)` |
| `RuleNode` | 1 | 1 | `getRuleContext()` |
| `SyntaxTree` | 1 | 1 | `getSourceInterval()` |
| `TerminalNode` | 1 | 1 | `getSymbol()` |
| `Tree` | 5 | 5 | `getParent()`, `getPayload()`, `getChild(int)`, `getChildCount()`, `toStringTree()` |

## com.seeyon.m5（15）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `TeamworkCoreAppService` | 13 | 13 | `launch(SingleRequest)`, `dismiss(SingleRequest)`, `join(SingleRequest)`, `quit(SingleRequest)`, `rename(SingleRequest)` …+8 |
| `TeamworkMessageAppService` | 2 | 2 | `sendCard(SingleRequest)`, `createNotification(SingleRequest)` |
| `TeamworkTabAppService` | 5 | 5 | `createTab(SingleRequest)`, `createTabs(SingleRequest)`, `updateTab(SingleRequest)`, `updateTabs(SingleRequest)`, `deleteTab(SingleRequest)` |
| `TeamworkTabGeneralizeAppService` | 1 | 1 | `deleteTabs(SingleRequest)` |
| `AppManageCoreAppService` | 3 | 3 | `check(SingleRequest)`, `getLatestDownloadUrl(SingleRequest)`, `getLatestApp(SingleRequest)` |
| `EnterpriseCoreAppSerivce` | 6 | 6 | `createEnterprise(SingleRequest)`, `updateEnterprise(SingleRequest)`, `deleteEnterprise(SingleRequest)`, `selectEnterprise(PageRequest)`, `selectsEnterprise(PageRequest)` …+1 |
| `CacheKeyConstants` | 0 | 0 | — |
| `ArtifactVersionDto` | 0 | 6 | — |
| `CacheKeyConstants` | 0 | 0 | — |
| `CardMessageConstansts` | 0 | 0 | — |
| `PluginConstants` | 0 | 0 | — |
| `ProviderNameConstants` | 0 | 0 | — |
| `QrcodeKeyConstants` | 0 | 0 | — |
| `RobotConstants` | 0 | 0 | — |
| `RCloudNativeProxy` | 0 | 3 | — |

## com.seeyon.portal（15）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `PortalConfigAppService` | 2 | 2 | `config(SingleRequest)`, `about()` |
| `PortalPortletAppService` | 11 | 11 | `createCategory(SingleRequest)`, `updateCategory(SingleRequest)`, `deleteCategoryByCodes(SingleRequest)`, `createPortlet(SingleRequest)`, `deletePortletByIds(SingleRequest)` …+6 |
| `PortalSetAppService` | 11 | 11 | `createPortal(SingleRequest)`, `updatePortal(SingleRequest)`, `exportPortalDesignInfo(SingleRequest)`, `importPortalDesignInfo(SingleRequest)`, `publishPortalDesignInfo(SingleRequest)` …+6 |
| `PortalShortcutAppService` | 6 | 6 | `create(SingleRequest)`, `update(SingleRequest)`, `deleteById(SingleRequest)`, `selectById(SingleRequest)`, `selectListByConditions(ListRequest)` …+1 |
| `PortalSpaceAppService` | 5 | 6 | `deleteSpaceById(SingleRequest)`, `createSpace(SingleRequest)`, `updateSpace(SingleRequest)`, `selectDesignSpaceList(SingleRequest)`, `saveAsPortalSpaceCopy(SingleRequest)` |
| `GlobalLockConstant` | 0 | 0 | — |
| `PluginConstant` | 0 | 0 | — |
| `PortalCacheKey` | 0 | 0 | — |
| `PortalResourceConstant` | 0 | 0 | — |
| `RoleConstant` | 0 | 0 | — |
| `PortalConstants` | 0 | 0 | — |
| `PortalNavServiceStrategy` | 0 | 7 | — |
| `PortalRecycleServiceStrategy` | 0 | 2 | — |
| `AppFacadeMethod` | 0 | 1 | — |
| `AbstractHolidayReminderService` | 2 | 4 | `remind(String, String, List)`, `record(String, String, List)` |

## com.seeyon.devops（10）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `ICompressHandler` | 1 | 1 | `handle(CompressContext)` |
| `ICompressResult` | 2 | 2 | `fileInfo()`, `compressError()` |
| `IFileInfo` | 2 | 2 | `path()`, `directory()` |
| `IUncompressHandler` | 1 | 1 | `handle(CompressContext)` |
| `IUncompressResult` | 1 | 1 | `fileInfos()` |
| `Const` | 0 | 0 | — |
| `ArtifactService` | 8 | 19 | `getMavenType()`, `upload(ArtifactDto)`, `download(ArtifactDto)`, `download(ArtifactDto, Supplier)`, `delete(ArtifactDto)` …+3 |
| `Const` | 0 | 0 | — |
| `AbstractArtifactManager` | 14 | 14 | `getAppType()`, `getModuleList()`, `exist(ArtifactDto)`, `download(ArtifactDto)`, `upload(ArtifactDto)` …+9 |
| `NpmService` | 4 | 5 | `getNpmType()`, `getInputStream(String)`, `parsePackage(FrontPackageDto)`, `downloadTarFileByHostApp(String, String)` |

## graphql.execution.instrumentation（9）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `DeferredFieldInstrumentationContext` | 0 | 1 | — |
| `ExecutionStrategyInstrumentationContext` | 0 | 2 | — |
| `Instrumentation` | 8 | 19 | `beginExecution(InstrumentationExecutionParameters)`, `beginParse(InstrumentationExecutionParameters)`, `beginValidation(InstrumentationValidationParameters)`, `beginExecuteOperation(InstrumentationExecuteOperationParameters)`, `beginExecutionStrategy(InstrumentationExecutionStrategyParameters)` …+3 |
| `InstrumentationContext` | 2 | 2 | `onDispatched(CompletableFuture)`, `onCompleted(T, Throwable)` |
| `InstrumentationState` | 0 | 0 | — |
| `FieldAndArguments` | 7 | 7 | `getField()`, `getFieldDefinition()`, `getParentType()`, `getParentFieldAndArguments()`, `getPath()` …+2 |
| `FieldValidation` | 1 | 1 | `validateFields(FieldValidationEnvironment)` |
| `FieldValidationEnvironment` | 5 | 5 | `getExecutionContext()`, `getFields()`, `getFieldsByPath()`, `mkError(String)`, `mkError(String, FieldAndArguments)` |
| `Instrumentation` | 0 | 8 | — |

## graphql.schema.idl（5）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `EnumValuesProvider` | 1 | 1 | `getValue(String)` |
| `SchemaDirectiveWiring` | 0 | 10 | — |
| `SchemaDirectiveWiringEnvironment` | 14 | 14 | `getElement()`, `getDirective()`, `getDirectives()`, `getDirective(String)`, `containsDirective(String)` …+9 |
| `SchemaGeneratorPostProcessing` | 1 | 1 | `process(GraphQLSchema)` |
| `WiringFactory` | 0 | 13 | — |

## com.seeyon.ai（2）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `NotNull` | 0 | 1 | — |
| `ICoMiPageParse` | 0 | 1 | — |

## graphql.execution.batched（2）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `Batched` | 0 | 0 | — |
| `BatchedDataFetcher` | 0 | 0 | — |

## graphql.execution.nextgen（2）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `BatchedDataFetcher` | 0 | 0 | — |
| `ExecutionStrategy` | 1 | 1 | `execute(ExecutionContext, FieldSubSelection)` |

## graphql.parser.antlr（2）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphqlListener` | 150 | 150 | `enterDocument(GraphqlParser$DocumentContext)`, `exitDocument(GraphqlParser$DocumentContext)`, `enterDefinition(GraphqlParser$DefinitionContext)`, `exitDefinition(GraphqlParser$DefinitionContext)`, `enterTypeSystemDefinition(GraphqlParser$TypeSystemDefinitionContext)` …+145 |
| `GraphqlVisitor` | 75 | 75 | `visitDocument(GraphqlParser$DocumentContext)`, `visitDefinition(GraphqlParser$DefinitionContext)`, `visitTypeSystemDefinition(GraphqlParser$TypeSystemDefinitionContext)`, `visitTypeSystemExtension(GraphqlParser$TypeSystemExtensionContext)`, `visitSchemaDefinition(GraphqlParser$SchemaDefinitionContext)` …+70 |

## graphql.schema.transform（2）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `VisibleFieldPredicate` | 1 | 1 | `isVisible(VisibleFieldPredicateEnvironment)` |
| `VisibleFieldPredicateEnvironment` | 2 | 2 | `getSchemaElement()`, `getParentElement()` |

## graphql.DeferredExecutionResult（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `DeferredExecutionResult` | 1 | 1 | `getPath()` |

## graphql.ErrorClassification（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `ErrorClassification` | 0 | 1 | — |

## graphql.ExecutionResult（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `ExecutionResult` | 5 | 5 | `getErrors()`, `getData()`, `isDataPresent()`, `getExtensions()`, `toSpecification()` |

## graphql.GraphQLError（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLError` | 3 | 6 | `getMessage()`, `getLocations()`, `getErrorType()` |

## graphql.Internal（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `Internal` | 0 | 0 | — |

## graphql.PublicApi（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `PublicApi` | 0 | 0 | — |

## graphql.PublicSpi（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `PublicSpi` | 0 | 0 | — |

## graphql.ThreadSafe（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `ThreadSafe` | 0 | 0 | — |

## graphql.TrivialDataFetcher（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `TrivialDataFetcher` | 0 | 0 | — |

## graphql.VisibleForTesting（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `VisibleForTesting` | 0 | 0 | — |

## graphql.analysis.FieldComplexityCalculator（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `FieldComplexityCalculator` | 1 | 1 | `calculate(FieldComplexityEnvironment, int)` |

## graphql.analysis.QueryReducer（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `QueryReducer` | 1 | 1 | `reduceField(QueryVisitorFieldEnvironment, T)` |

## graphql.analysis.QueryVisitor（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `QueryVisitor` | 3 | 7 | `visitField(QueryVisitorFieldEnvironment)`, `visitInlineFragment(QueryVisitorInlineFragmentEnvironment)`, `visitFragmentSpread(QueryVisitorFragmentSpreadEnvironment)` |

## graphql.analysis.QueryVisitorFieldArgumentEnvironment（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `QueryVisitorFieldArgumentEnvironment` | 8 | 8 | `getSchema()`, `getFieldDefinition()`, `getGraphQLArgument()`, `getArgument()`, `getArgumentValue()` …+3 |

## graphql.analysis.QueryVisitorFieldArgumentInputValue（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `QueryVisitorFieldArgumentInputValue` | 5 | 5 | `getParent()`, `getInputValueDefinition()`, `getName()`, `getInputType()`, `getValue()` |

## graphql.analysis.QueryVisitorFieldArgumentValueEnvironment（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `QueryVisitorFieldArgumentValueEnvironment` | 6 | 6 | `getSchema()`, `getFieldDefinition()`, `getGraphQLArgument()`, `getArgumentInputValue()`, `getVariables()` …+1 |

## graphql.analysis.QueryVisitorFieldEnvironment（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `QueryVisitorFieldEnvironment` | 10 | 10 | `getSchema()`, `isTypeNameIntrospectionField()`, `getField()`, `getFieldDefinition()`, `getParentType()` …+5 |

## graphql.analysis.QueryVisitorFragmentDefinitionEnvironment（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `QueryVisitorFragmentDefinitionEnvironment` | 3 | 3 | `getSchema()`, `getFragmentDefinition()`, `getTraverserContext()` |

## graphql.analysis.QueryVisitorFragmentSpreadEnvironment（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `QueryVisitorFragmentSpreadEnvironment` | 4 | 4 | `getSchema()`, `getFragmentSpread()`, `getFragmentDefinition()`, `getTraverserContext()` |

## graphql.analysis.QueryVisitorInlineFragmentEnvironment（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `QueryVisitorInlineFragmentEnvironment` | 3 | 3 | `getSchema()`, `getInlineFragment()`, `getTraverserContext()` |

## graphql.execution.DataFetcherExceptionHandler（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `DataFetcherExceptionHandler` | 1 | 1 | `onException(DataFetcherExceptionHandlerParameters)` |

## graphql.execution.ExecutionIdProvider（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `ExecutionIdProvider` | 1 | 2 | `provide(String, String, Object)` |

## graphql.execution.ValueUnboxer（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `ValueUnboxer` | 1 | 1 | `unbox(Object)` |

## graphql.execution.directives（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `QueryDirectives` | 3 | 3 | `getImmediateDirectivesByName()`, `getImmediateDirective(String)`, `getImmediateDirectivesByField()` |

## graphql.execution.preparsed（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `PreparsedDocumentProvider` | 1 | 1 | `getDocument(ExecutionInput, Function, PreparsedDocumentEntry>)` |

## graphql.introspection.IntrospectionQuery（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `IntrospectionQuery` | 0 | 0 | — |

## graphql.language.Definition（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `Definition` | 0 | 0 | — |

## graphql.language.DescribedNode（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `DescribedNode` | 1 | 1 | `getDescription()` |

## graphql.language.DirectivesContainer（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `DirectivesContainer` | 1 | 3 | `getDirectives()` |

## graphql.language.ImplementingTypeDefinition（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `ImplementingTypeDefinition` | 2 | 2 | `getImplements()`, `getFieldDefinitions()` |

## graphql.language.NamedNode（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `NamedNode` | 1 | 1 | `getName()` |

## graphql.language.Node（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `Node` | 10 | 10 | `getChildren()`, `getNamedChildren()`, `withNewChildren(NodeChildrenContainer)`, `getSourceLocation()`, `getComments()` …+5 |

## graphql.language.NodeBuilder（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `NodeBuilder` | 5 | 5 | `sourceLocation(SourceLocation)`, `comments(List)`, `ignoredChars(IgnoredChars)`, `additionalData(Map, String>)`, `additionalData(String, String)` |

## graphql.language.NodeDirectivesBuilder（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `NodeDirectivesBuilder` | 1 | 1 | `directives(List)` |

## graphql.language.NodeVisitor（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `NodeVisitor` | 36 | 36 | `visitArgument(Argument, TraverserContext)`, `visitArrayValue(ArrayValue, TraverserContext)`, `visitBooleanValue(BooleanValue, TraverserContext)`, `visitDirective(Directive, TraverserContext)`, `visitDirectiveDefinition(DirectiveDefinition, TraverserContext)` …+31 |

## graphql.language.SDLDefinition（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `SDLDefinition` | 0 | 0 | — |

## graphql.language.ScalarValue（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `ScalarValue` | 0 | 0 | — |

## graphql.language.Selection（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `Selection` | 0 | 0 | — |

## graphql.language.SelectionSetContainer（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `SelectionSetContainer` | 1 | 1 | `getSelectionSet()` |

## graphql.language.Type（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `Type` | 0 | 0 | — |

## graphql.language.TypeDefinition（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `TypeDefinition` | 0 | 0 | — |

## graphql.language.Value（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `Value` | 0 | 0 | — |

## graphql.relay.Connection（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `Connection` | 2 | 2 | `getEdges()`, `getPageInfo()` |

## graphql.relay.ConnectionCursor（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `ConnectionCursor` | 1 | 1 | `getValue()` |

## graphql.relay.Edge（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `Edge` | 2 | 2 | `getNode()`, `getCursor()` |

## graphql.relay.PageInfo（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `PageInfo` | 4 | 4 | `getStartCursor()`, `getEndCursor()`, `isHasPreviousPage()`, `isHasNextPage()` |

## graphql.schema.Coercing（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `Coercing` | 3 | 4 | `serialize(Object)`, `parseValue(Object)`, `parseLiteral(Object)` |

## graphql.schema.DataFetcher（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `DataFetcher` | 1 | 1 | `get(DataFetchingEnvironment)` |

## graphql.schema.DataFetcherFactory（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `DataFetcherFactory` | 1 | 1 | `get(DataFetcherFactoryEnvironment)` |

## graphql.schema.DataFetchingEnvironment（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `DataFetchingEnvironment` | 27 | 27 | `getSource()`, `getArguments()`, `containsArgument(String)`, `getArgument(String)`, `getArgumentOrDefault(String, T)` …+22 |

## graphql.schema.DataFetchingFieldSelectionSet（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `DataFetchingFieldSelectionSet` | 9 | 10 | `get()`, `getArguments()`, `getDefinitions()`, `contains(String)`, `containsAnyOf(String)` …+4 |

## graphql.schema.GraphQLCompositeType（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLCompositeType` | 0 | 0 | — |

## graphql.schema.GraphQLDirectiveContainer（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLDirectiveContainer` | 1 | 3 | `getDirectives()` |

## graphql.schema.GraphQLFieldsContainer（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLFieldsContainer` | 2 | 2 | `getFieldDefinition(String)`, `getFieldDefinitions()` |

## graphql.schema.GraphQLImplementingType（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLImplementingType` | 1 | 1 | `getInterfaces()` |

## graphql.schema.GraphQLInputFieldsContainer（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLInputFieldsContainer` | 2 | 2 | `getFieldDefinition(String)`, `getFieldDefinitions()` |

## graphql.schema.GraphQLInputType（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLInputType` | 0 | 0 | — |

## graphql.schema.GraphQLInputValueDefinition（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLInputValueDefinition` | 1 | 1 | `getType()` |

## graphql.schema.GraphQLModifiedType（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLModifiedType` | 1 | 1 | `getWrappedType()` |

## graphql.schema.GraphQLNamedInputType（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLNamedInputType` | 0 | 0 | — |

## graphql.schema.GraphQLNamedOutputType（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLNamedOutputType` | 0 | 0 | — |

## graphql.schema.GraphQLNamedSchemaElement（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLNamedSchemaElement` | 3 | 3 | `getName()`, `getDescription()`, `getDefinition()` |

## graphql.schema.GraphQLNamedType（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLNamedType` | 0 | 0 | — |

## graphql.schema.GraphQLNullableType（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLNullableType` | 0 | 0 | — |

## graphql.schema.GraphQLOutputType（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLOutputType` | 0 | 0 | — |

## graphql.schema.GraphQLSchemaElement（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLSchemaElement` | 1 | 4 | `accept(TraverserContext, GraphQLTypeVisitor)` |

## graphql.schema.GraphQLType（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLType` | 0 | 0 | — |

## graphql.schema.GraphQLTypeVisitor（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLTypeVisitor` | 14 | 24 | `visitGraphQLArgument(GraphQLArgument, TraverserContext)`, `visitGraphQLInterfaceType(GraphQLInterfaceType, TraverserContext)`, `visitGraphQLEnumType(GraphQLEnumType, TraverserContext)`, `visitGraphQLEnumValueDefinition(GraphQLEnumValueDefinition, TraverserContext)`, `visitGraphQLFieldDefinition(GraphQLFieldDefinition, TraverserContext)` …+9 |

## graphql.schema.GraphQLUnmodifiedType（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphQLUnmodifiedType` | 0 | 0 | — |

## graphql.schema.GraphqlTypeComparatorRegistry（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphqlTypeComparatorRegistry` | 1 | 1 | `getComparator(GraphqlTypeComparatorEnvironment)` |

## graphql.schema.SelectedField（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `SelectedField` | 5 | 5 | `getName()`, `getQualifiedName()`, `getFieldDefinition()`, `getArguments()`, `getSelectionSet()` |

## graphql.schema.TypeResolver（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `TypeResolver` | 1 | 1 | `getType(TypeResolutionEnvironment)` |

## graphql.schema.diff（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `DifferenceReporter` | 2 | 2 | `report(DiffEvent)`, `onEnd()` |

## graphql.schema.validation（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `SchemaValidationRule` | 2 | 2 | `check(GraphQLFieldDefinition, SchemaValidationErrorCollector)`, `check(GraphQLType, SchemaValidationErrorCollector)` |

## graphql.schema.visibility（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `GraphqlFieldVisibility` | 2 | 4 | `getFieldDefinitions(GraphQLFieldsContainer)`, `getFieldDefinition(GraphQLFieldsContainer, String)` |

## graphql.util.NodeAdapter（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `NodeAdapter` | 3 | 3 | `getNamedChildren(T)`, `withNewChildren(T, Map, List)`, `removeChild(T, NodeLocation)` |

## graphql.util.TraverserContext（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `TraverserContext` | 24 | 24 | `thisNode()`, `originalThisNode()`, `changeNode(T)`, `deleteNode()`, `isDeleted()` …+19 |

## graphql.util.TraverserVisitor（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `TraverserVisitor` | 2 | 3 | `enter(TraverserContext)`, `leave(TraverserContext)` |

## graphql.validation.DocumentVisitor（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `DocumentVisitor` | 2 | 2 | `enter(Node, List)`, `leave(Node, List)` |

## it.sauronsoftware.jave（1）

| 接口 | abstract | 方法 | 必实现方法（abstract） |
|---|---|---|---|
| `EncoderProgressListener` | 0 | 3 | — |
