# standard-product｜扩展点决策表：要干什么 → 实现哪个接口

> 本格回答**「我这个需求该挂哪个钩子」**。151 个带 abstract 的 UDC 接口里，
> **128 个是真接口**（101 有平台实现 / 27 纯扩展位）、**23 个是注解**。
> 接口全量签名见 `docs/audit/artifacts/extension-surface-20261029/extension-points.md`；
> 落位规则见 `extension-project-skeleton.md`（只有 ext 能写）；
> 入参对象见 `udc-microflow-extend-interfaces.md` §7.7。

分级：`VERIFIED_STATIC_BYTECODE`（javap 逐字签名 + implements 关系实算）。

## 1. Capability

从「我要让应用在某个时刻多做一件事」到「在 `-ext/extend/` 下新建哪个类、覆写哪个方法」。
每行给：场景 → 接口 → 必实现方法（逐字）→ 平台同族实现（照着抄）→ 它在什么时候被调。

## 2. Version

不含。接口签名随平台构件版本漂移时以 `interfaces.json` 重跑为准。

## 3. Input

你的需求描述 + 本表 + `extension-points.md`（看该接口平台有几个实现、在哪个包）。

## 4. Required

选钩子前必须先过三道：
1. 这是**接口**还是**注解**？注解（`Importer` / `UpgradeMethod` / `OperationLog` / `LogDefault` /
   `DelDetection` / `UpdateDetection` / `TypeMapping` / `AppOpsAuth` / `AuthModel` / `AuthOperation` …）
   是贴在代码上的，不是 implements 的对象。
2. 平台是否已有同族实现？101 个有实现的接口照着写，风险最低。
3. 这个钩子**平台是否真的会调**？纯扩展位（27 个）零实现，必须先确认注册方式。

## 5. Execution

在 `-ext/extend/` 下建类 → implements → 自己保证注册（平台无自动装配）→ 重新构建验证。

## 6. Side Effects

- 部署前类钩子（`DeployBeforeService`）返回 `false` 会**拦下整个发布**，写错等于封死发布。
- 元数据/代码生成类钩子（`CodeTask` / `TransportHandler`）产出物会进入最终包，错了要重新发布才能修。
- 检测类钩子（`DetectionTask` / `PartDetectionTask`）影响发布前校验，误报会挡住正常发布。

## 7. Known Constraints

**口径**：`interfaces.json` 里 UDC 有 274 个接口 = 250 真接口 + 24 注解；真接口里 55 个是 `*AppService` 调用面（你调它）、128 个带 abstract 是扩展点（你实现它）、67 个无 abstract 是标记/纯 default。本表只讲这 128 个。

### 7.1 不能 implements 的三类（先排除）

| 类别 | 例子 | 怎么用 |
|---|---|---|
| 注解 `@interface`（23 个） | `Importer` / `UpgradeMethod` / `OperationLog` / `LogDefault` / `LogDefaultUpdate` / `DelDetection` / `UpdateDetection` / `TypeMapping` / `AppOpsAuth` / `AuthModel` / `AuthOperation` / `AppIdRef` / `DataChangeAware` / `AttrTypeMatch` / `AttributeExist` / `EntityExist` / `DateValidation` / `TimeValidation` / `ExclusivePermit` / `ComparedSchema` / `ExprConsistency` / `LimitCountOperation` / `ConsistencyDetection` | 贴到类/字段/方法上，平台读注解做事 |
| 上下文（平台传给你） | `AppContext` / `CodeContext` / `ConfigurableCodeContext` / `DetectionContext` / `FrontDeployDetectionContext` / `BaseNodeContext` / `AppDeployContext` | 出现在别人方法的入参里，你只管取数据 |
| 函数式 | `Functor`（两个包各一个）/ `SFunction` / `Consumer3` / `TaskCallable` | 传 lambda |

### 7.2 场景 → 钩子（部署与发布）

| 我要干什么 | 实现 | 必实现方法（逐字） | 平台参照实现 | 什么时候被调 |
|---|---|---|---|---|
| 发布前校验，不合格拦下来 | `DeployBeforeService` | `boolean handle(AppContext)` | 7 个：`DependAppVersionCheckService` / `DeployMetadataCheckService` / `DeployEnumCheckService` / `DeployInspectionService` / `DeployOuterEntityCheckService` | 部署管线 pre 阶段，`false` = 拦 |
| 元数据构建后补一段 | `AppMetaDataContextPostProcess` | `void postProcessAppMetaDataContext(AppContext)` | 27 个：`DtoAttributePostProcessor` / `ScalabilityPostProcessor` / `BasicDataMetaDataPostProcessor` | 元数据装配完成、代码生成之前 |
| 元数据增减要处理 | `MetadataHandleService` | `boolean handle(AppContext)` | `DeltaPageMetadataTask` | 增量元数据处理 |
| 上下文加入/移除要回调 | `ContextListener` | `boolean onAdd(AppContext)` / `boolean onRemove(AppContext)` | `DeployContextListener` | 应用上下文生命周期 |
| 应用上架后要处理 | `ApplicationShelfService` | `void updateStateAfterAppShelf(ApplicationDto)` | `ApplicationShelf4UdcServiceImpl` | 应用上架 |
| 部署管线加一段/看阶段 | `PipeLineService` / `DeployService` / `ChannelPlugin` | `startPipeline(PipeLineContext)` / `start(PipeLineContext)` / `execute(PipeLineContext)` | `PipeLineManager` / `AbstractDeployService` / `AutoCodeHandler` | 对应管线阶段 |

### 7.3 场景 → 钩子（代码生成）

| 我要干什么 | 实现 | 必实现方法（逐字） | 平台参照实现 | 什么时候被调 |
|---|---|---|---|---|
| 多生成一个文件/配置类 | `CodeTask` | `String code(CodeContext)` | **50 个**：`AppInitFileTask` / `AppBuildInfoTask` / `AppDependenciesTask` / `AttachmentTemplateTask` | 代码生成，每个 Task 产出一份 |
| 导出时把某段 schema 写成文件 | `TransportHandler` | `List<SchemaInfo> out(CodeContext)` | **32 个**：`EntityTransportHandler` / `AttributeSetTransportHandler` / `BasicDataTransportHandler` | 导出 |
| 生成的类名/包名要改 | `CodeContextAware` / `CodeParamInterceptor` | `void setCodeContext(CodeContext)` / `void filter(ApplicationDto, CodeParam)` | `BaseInfoCodeContextAware` / `BaseAppCodeParamInterceptor` | 生成前装配上下文 |
| 输出静态资源 | `FileResolver` | `void outputStaticFile(CodeContext, List<StaticFileDto>)` | `StaticFileResolver` | 静态资源落盘 |
| 建表/改表出 SQL | `SqlResolver` / `UdcDataBaseSqlGenerator` | `outputInitSql(CodeContext, List<Change>)` / `outputUpdateSql(...)` / `outputDmlFile(...)`；`getChangeList(ApplicationDto, AppDbInfoDto, List)` | `CodeSqlResolver` / `UdcEntityDataBaseSqlGeneratorImpl` | DDL/DML 生成 |
| 属性类型 A→B 要迁数据 | `TypeChangeSqlResolver` | `boolean match(AttributeDto, AttributeDto, CodeContext)` + `void registrySql(AttributeDto, AttributeDto, EntityDto, …)` | 5 个：`Date2DateTimeSqlResolver` / `Decimal2CurrencySqlResolver` / `String2MultiLineStringSqlResolver` | 类型变更时注册 SQL |
| 类型变更要不要放行 | `TypeUpdateAuthChecker` | `boolean matchTypeChangeRule(AttributeDto, AttributeDto)` + `void doAttributeFieldChangeCheck(...)` | 4 个：`Date2DateTimeTypeUpdateAuthChecker` / `String2MultilineStringTypeUpdateChecker` | 设计态改字段类型 |
| 数据库方言适配 | `DbCodeHandler` | `String getDefaultValueString(UdcDataType, String)` | `Mysql57DbCodeHandler` | 生成默认值 SQL |
| 表达式编译成目标代码 | `Interpreter` / `Template` | `String interpret(ASTNode, ExprCodeGenContext)`；`valueOpValue()` 等 29 个模板方法 | 9 个解释器：`BinaryInterpreter` / `FunctionInterpreter` / `EntityVariableInterpreter` | 表达式代码生成 |
| i18n 文案生成 | `I18nHandler` | `void handle(T, I18nContext)` | `MicroFlowBoI18nHandler` / `UdcEnumDtoI18nHandler` | i18n 资源生成 |
| 查元数据元素 | `ElementRepository` | `ElementType getType()` / `T selectById(Long)` / `List<T> selectByAppId(Long)` | 21 个：`ApplicationRepository` / `AttributeRepository` / `CtpEnumRepository` | 全流程通用读口 |
| 按条件查设计态元数据 | `BaseDesignMetadataQueryService` | `selectByAppId(Long)` / `selectByCondition(UdcAppMetaDataQueryDto)` / `selectByFullName(Long, String)` | 11 个：`EntityDesignMetadataQueryService` / `DtoDesignMetadataQueryService` | 设计态查询 |

### 7.4 场景 → 钩子（导入导出与复制）

| 我要干什么 | 实现 | 必实现方法（逐字） | 平台参照实现 | 什么时候被调 |
|---|---|---|---|---|
| 导入时自己处理一段 | `Importable` | `void in(TransportData)`；default 另有 `before` / `transfer` / `importValidate` / `matches` / `transferFilter` | **29 个**：`AbstractXxxImporterBase` 系列 | 导入管线，平台控顺序 |
| 另存为时搬自定义数据 | `SaveAsHandler` | `void saveAs(TransportData)`；default `before` / `normalSaveAs` | 17 个：`PageSaveAsHandler` / `CollaborationSaveAsHandler` / `MicroFlowSaveAsHandler` | 应用另存为 |
| 导入模块拆分 | `SplitHandler` | `ModuleDependency getRelation(SplitContext)` | 5 个：`EntitySplitHandler` / `PageSplitHandler` / `MicroFlowSplitHandler` | 传输包按模块拆 |
| 导出要筛掉/改某段 | `SchemaFilter` | `boolean matches(String, String)` / `SchemaInfo filter(SchemaInfo, SchemaInfo)` | 0（纯扩展位） | 导出过滤 |
| 导出数据按租户过滤 | `TenantDataFilter` | `String filter(String, List<Object>)` | `DefaultTenantDataFilter` / `PageTenantDataFilter` | 导出 SQL 拼租户条件 |
| 复制单据带自定义子表 | `CopyHandler` / `EntityCopyResolver` | `String type()` + `List<SchemaInfo> out(EntityCopyContext)`；`Long copyEntity(EntityCopyContext)` | 7 个：`EntityCopyHandler` / `AttributeCopyHandler` / `ReferCopyHandler` | 应用/实体复制 |
| 删实体/微流程前查影响面 | `ApplicationInnerReference` | `getEntityBackwardRefPages(String)` / `getMicroFlowBackwardRefPages(Long)` / `getDataflowBackwardRefPages(Long)`（共 14 个） | 0（纯扩展位） | 删除前置检查 |
| 解析/存引用关系 | `ReferenceParser` / `ReferenceStore` | `Collection<Relation> parse(T)` / `scan(Long)`；`int save(Long, Collection<Relation>)` | `AbstractReferenceParser` / `DefaultReferenceStore` | 引用索引维护 |

### 7.5 场景 → 钩子（权限）

| 我要干什么 | 实现 | 必实现方法（逐字） | 平台参照实现 | 什么时候被调 |
|---|---|---|---|---|
| 扩展应用的操作权限 | `ExtendAppOperationAuthCheck` | `boolean hasRight(ExtendAppAuthCheckInfoDto)` | 3 个：`RoleResourceAndDataPermissionAuthCheck` / `FormAppHostAdminAuthCheck` / `UdcDefaultExtendAppOperationAuthCheck` | 操作鉴权 |
| 数据级权限校验 | `AuthCheck` | `AuthCheckResultDto check(AuthOperationType, UdcBaseEntityDto)` / `check(AuthOperationType, Long)` / `String getModelName()` | `AbstractAuthCheck` | 数据读写前 |
| 横向越权校验 | `LateralAuthChecker` | `void check(Supplier<Long>)` / `void checkByAppName(Supplier<String>)` | `UdcLateralAuthChecker` | 跨应用访问 |
| 数量上限校验 | `LimitCountCheck` | `LimitCountCheckResultDto check(BaseDto, Long)` / `String getModelName()` / `int getDbCount(Long)` | `AbstractLimitCountCheck` | 新建/导入前 |

### 7.6 场景 → 钩子（一致性检测）

| 我要干什么 | 实现 | 必实现方法（逐字） | 平台参照实现 | 什么时候被调 |
|---|---|---|---|---|
| 加一类整体检测 | `DetectionTask` | `Set<String> getDomainObjects()` / `boolean detection(DetectionContext)` | `AssociateDetectionTask` / `AbstractDetectionTask` | 设计器「检测」 |
| 分片检测（大数据量） | `PartDetectionTask` | `String getTargetDomainObject()` / `getSourceDomainObject()` / `setSelfIds(Set<Long>)`（共 14 个） | `AbstractPartDetectionTask` | 分片检测 |
| 前端部署前检测 | `FrontDeployDetectionTask` | `boolean detection(FrontDeployDetectionContext)` | 5 个：`CtpEnumFrontDeployDetectionTask` / `AbstractPageFrontDeployDetectionTask` | 前端发布前 |
| 检测前备元数据 | `DetectionMetadataAware` | `void init(DetectionContext, Set<String>)` | 9 个：`EntityDetectionMetadataAware` / `MicroFlowDetectionMetadataAware` | 检测启动 |
| 检测数据来源 | `SourceDetectionSupport` | `Set<String> getSourceMetaData(DetectionContext)` / `String getSourceDataType()` / `getSourceDomainObject()` | 5 个：`EntitySourceDetectionSupport` / `CtpEnumSourceDetectionSupport` | 差异比对 |
| 自定义检测规则 | `DetectionRuleSupport` | `Boolean detectionRule(DetectionContext, T)` / `ConsistenceDetectionCodeEnum getCodeEnum()` | 3 个：`AbstractAttributeSetPartDetection` 等 | 规则判定 |
| 表达式一致性 | `ExprConsistencyValidator` / `ExprConsistencyFilter` | `ConsistencyValidateResult validateConsistency(ConsistencyValidateConfig)`；`void doFilter(ConsistencyFilterContext, …)` | `EntityExprConsistencyValidationImpl` / `ExprConsistencyFilterChain` | 表达式校验 |

### 7.7 场景 → 钩子（微流程）

| 我要干什么 | 实现 | 必实现方法（逐字） | 平台参照实现 | 什么时候被调 |
|---|---|---|---|---|
| 删组件时清理关联 | `MicroFlowSimpleComponentCascadeHandler` | `void handleComponent(MicroFlowCascadeContext, JsonNode)` | 6 个：`EnumCascadeHandler` / `DataMappingFieldCascadeHandler` / `MappingRowCascadeHandler` | 微流程组件删除/变更 |
| 组件定位/子组件 | `MicroFlowSubComponentHandler` / `MicroFlowComponentHandler` | `initSubComponentLocators()` / `addSubLocator(Class, Function)`；`isArrayComponent()` / `addLocator(...)` | `BaseSimpleComponentCascadeHandler` | 微流程结构遍历 |
| 节点 JSON 解析成对象 | `NodeParser` / `MicroflowNodeParser` | `BaseNode parse(MicroFlowNodeParseContext, ObjectNode)`；`Collection<Relation> parse(T, MicroFlowDefinitionDto)` | `AbstractBaseNode` / 0 | 微流程加载 |
| 预设模板生成 | `PresetTemplateHandler` | `void generate(EntityDto)` / `generateByName(EntityDto, String)` / `getNextHandler()` / `setNextHandler(...)` | `AbstractPresetTemplateHandler`（责任链） | 建微流程时套模板 |
| 微流程 schema 判定 | `MicroFlowSchemaDeterminer` / `MicroFlowLastVersionMetadataEnabler` | `Long getAppId()` / `getName()` / `getCaption()` …（12 个）；`getType()` / `getTriggerType()` / `getState()` / `getLastVersionMetadataState()` | `MicroFlowEntity` / `MicroFlowDefinitionDto` | 维护上一版本元数据 |
| 引用节点重写 | `ReferenceComponentProcessor` | `convertPreorderNodeReference(List)` / `convertSuccessorNodeReference(List)` / `replaceReferenceComponents(List, …)` | `BaseReferenceComponentProcessor` | 微流程重构 |
| 全限定名收集/改写 | `ConnectorFullNameExtractor` / `DynamicDependencyFullNameModifier` / `FullNameExtractor` | `extractUdcAppDtoFullName(VirtualFullNameTable)`；`modifyFullNameInGeneration(...)` / `extractDynamicDependencyFullName(...)` | `BusinessEventActivity` / `CallAppServiceActivity` 等 | 跨应用引用改名 |

### 7.8 场景 → 钩子（日志与审计）

| 我要干什么 | 实现 | 必实现方法（逐字） | 平台参照实现 | 什么时候被调 |
|---|---|---|---|---|
| 操作日志明细要带业务信息 | `OperationRecordService` | `OperationLogDetailsDto buildOperationLogDetailsDto4Create(T)` / `…4CreateBatch(List<T>)` / `…4Update(T)` / `…4UpdateBatch(List<T>)` | 5 个：`Entity4RecordService` / `PageInfo4RecordService` / `Portlet4RecordService` | 写操作日志 |
| 删除类审计日志 | `UdcAuditLogService` | `void createLog4EntityDelete(List<EntityDto>)` / `createLog4AttributeDelete(...)` / `createLog4ApplicationDelete(ApplicationDto)` | `UdcAuditLogServiceImpl` | 元数据删除 |
| 远端日志查询 | `LogService` | `LogTypeEnum getLogType()` / `List<String> getLogs(String, int, long, long, String)` | `SLSService` | 拉部署日志 |

### 7.9 场景 → 钩子（应用特性与其他）

| 我要干什么 | 实现 | 必实现方法（逐字） | 平台参照实现 | 什么时候被调 |
|---|---|---|---|---|
| 判断应用类型 / 取宿主信息 | `AppFeature` / `AppFeatureHandler` | `ApplicationFeatureEnum getTypeEnum()` / `boolean isDynamicService()`；`getHostAppName(ApplicationDto)` / `getAppUrl(ApplicationDto)` / `getAppDbInfo(ApplicationDto)`（共 14 个） | `AbstractAppFeature` / 3 个 handler | 全流程取上下文 |
| 新增字段类型 | `UdcDataType` + `TypeHelper` | `getExtensionProperties()` / `getDefaultDataProperties()` / `getFrontComponent()`（共 20 个）；`getDatabaseDataType(BaseUdcAttributeDto)` / `getJavaType(...)` / `getLength(...)`（6 个） | `AbstractDataType` / `DefaultTypeHelper` / `DecimalDataTypeHelper` | 设计器选类型、生成 DDL/Java |
| 新增映射模式（下拉） | `MappingMode` / `DeductionSearchMethodType` | `getName()` / `getCaption()` / `getSupportOperationType()`（11 个）；`getDeductionSearchMethodTypeEnum()`（4 个） | `AbstractMappingMode` / `AbstractGroupingFunctionMappingMode` | 数据流/检索配置 |
| 保留上一版本元数据 | `LastVersionMetadataManagerService` | `prepareLastVersionAfterDeployed(ApplicationDto)` / `fetchLastVersionMetadataFromDbIfNotExist(LastVersionMetadataSearchDto)` / `getModule()` | 8 个：`EntityLastVersionMetadataService` / `MicroFlowLastVersionMetadataService` | 每次发布后 |
| 兼容性报告/输出 | `Compatible` / `CompatibilityOutput` / `SchemaGenerator` | `ComparisonResponse compare(CodeContext, List)`；`void output(List, CompatibilityContext)`；`List<CompatibilitySchemaDto> generate(CompatibilityContext)` | 0 / `AbstractCompatibilityOutput` / `AbstractSchemaGenerator` | 升级兼容检查 |
| 数据迁移扩展文件处理 | `MigrateCallback` | `boolean extendFilesHandle(Collection<File>)` | 0 | 迁移收尾 |
| 缓存包装 | `LazyCacheAdapter` | `O handle(I)` / `List<I> getArgs()` | `TemplateLazyCacheAdapter` | 缓存读取 |
| 系统数据同步（npm 等） | `NpmSyncDataService` | `getNpmSyncType()` / `readPackageData(String)` / `getPackageLocalPath(PackageInfoDto)` / `filterData(...)` | `AbstractNpmSyncDataService` | 制品同步 |
| 树数据查询 | `UdcTreeQueryService` | `PageResponse selectTreeData(SingleRequest<UdcTreeQueryDto>)` | 0（纯扩展位） | 树形控件取数 |
| 插件执行 | `PluginExecutor` / `PluginHandler` | `void execute(E)` / `executeAsync(E)`；`void execute(T)` | `AbstractPluginExecutor` / `CommonSchemaImportPluginHandlerAdapter` | 插件挂载点 |

### 7.10 选钩子的三条判断顺序

1. **先看平台有没有同族实现**。101 个有实现的接口，实现类就是最好的样板（`extension-points.md`
   按 impl 数排序，排前面的都是族主）。
2. **再看这钩子的返回值有没有杀伤力**。`boolean` 返回的（`DeployBeforeService` / `DetectionTask` /
   `Importable.matches` / `SchemaFilter.matches`）返回错会拦下发布或漏掉检测。
3. **最后看纯扩展位要不要注册**。27 个零实现接口平台不会自动发现，先把注册方式定下来再写。

## 8. Evidence

```
① 接口与实现关系  docs/audit/artifacts/extension-surface-20261029/interfaces.json（91 构件 / 10414 类）
② 落地表          docs/audit/artifacts/extension-surface-20261029/extension-points.md
                  （128 真接口：101 有实现 + 27 纯扩展位；23 注解）
③ 注解判定        extends 含 java.lang.annotation.Annotation → @interface
④ 落位规则        extension-project-skeleton.md（只有 -ext/extend/ 可写）
⑤ 入参对象        udc-microflow-extend-interfaces.md §7.7（TransportData / AppContext / CodeContext）
```

不含：具体应用名、appId、组织标识、版本号、本机路径。

## 9. Verified


- 每行的接口名、abstract 方法签名逐字来自 `interfaces.json`（javap 原文）
- 「平台参照实现」列的类名来自 `implements` 关系实算，不是按名字猜
- 注解/接口的区分依据 `extends java.lang.annotation.Annotation`
- 复现：`python tools/core/platform/emit_extension_points.py --interfaces <interfaces.json> --emit <out.md>`
- 抽验：`DeployBeforeService.handle(AppContext)`、`Importable.in(TransportData)`、
  `DetectionTask.detection(DetectionContext)`、`CodeTask.code(CodeContext)` 四条与 javap 原文一致
