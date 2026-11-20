# 专题 2：代码生成体系

> 状态：**研究中（第一轮）** · 未审计
> 平台版本：`udc-platform-5.3.517`
> 统计脚本：`scripts/research/stats_registry.py`
> 最近更新：2026-11-17

---

## 1. 研究目标

建立 `CodeTask → Template → 模板资源 → 参数 → 输出文件 → 部署位置 → 实际生成代码` 的完整映射。

---

## 2. 生成主链（已证部分）

### 2.1 链路总览

```
CodeParam（生成参数）
  ├─ getCodeVersion(): String                    ★ 版本
  ├─ getCodeLanguage(): CodeLanguage
  ├─ getContextTypeEnum(): ContextTypeEnum
  ├─ isDeploy(): boolean                         ★ 是否部署
  ├─ getDeployId(): Long
  ├─ getCodeTaskList(): List<CodeTask>           ★ 任务列表
  ├─ getInterceptorList(): List<TemplateInterceptor>   ★ 模板拦截
  ├─ getTransportHandlerList(): List<TransportHandler> ★ 部署传输
  ├─ getContextAwareList(): List<CodeContextAware>
  ├─ getDynamicArgs(): Map<String,Object>
  └─ getComparedSchemaIdSet(): Set<String>       ★ 增量对比

        ↓ AutoCodeExecutor#execute(ApplicationDto, CodeParam)
        ↓ AutoCodeExecutor#executeSegment(ApplicationDto, CodeParam)

CodeContext（生成上下文，仅 13 个方法）
  ├─ getAutoCodeProperties(): AutoCodeProperties  ★ 模板目录/版本配置
  ├─ getVersionControl(): VersionControl
  ├─ getBasePackage() / getAppName4Package()
  ├─ getPackage(ApplicationDto, String...)        ★ 包名拼接
  ├─ getModelJavaPath(String...)                  ★ Java 输出路径
  ├─ getModelResourcePath(String...)              ★ 资源输出路径
  ├─ getBasePackagePathStr()
  ├─ getAuthor() / getCreateTime()
  ├─ getAppDbInfoDto() / getI18nContext()
  └─ (共 13 个方法)

        ↓ AutoCodeExecutor#runTask(CodeContext, List<CodeTask>)

CodeTask#code(CodeContext): String                ← 52 个实现
        ↓
<Template>#getTemplateOutMap(): Map<String,String>    ← 模板名 → 输出路径
<Template>#getArgumentMap(): Map<String,Object>       ← 渲染参数
        ↓
AbstractUdcFreemarkerTemplate#writeToString(Object, String): String
        ↓
TransportHandler#out(CodeContext): List<SchemaInfo>   ← 部署
```

### 2.2 关键结构说明

**`CodeContext` 只有 13 个方法，且不含实体元数据本身。**

⇒ 元数据不是从 `CodeContext` 直接取的，而是：
1. 通过 `CodeParam#getParentContext(): MetaDatable`
2. 或各 Task 内部从 `ApplicationDto` 重新加载

**⇒ 这是一个重要边界：`CodeContext` 是「路径 + 配置 + 上下文」，不是「元数据容器」。**
**证据等级：** `VERIFIED_STATIC_BYTECODE`（签名逐字）

**`CodeParam` 的 21 个方法揭示的生成控制维度：**

| 维度 | 方法 | 作用 |
|---|---|---|
| 版本 | `getCodeVersion()` / `setCodeVersion()` | 决定用哪套模板 |
| 语言 | `getCodeLanguage()` | 代码语言（Java？） |
| 上下文类型 | `getContextTypeEnum()` | 应用/页面/微流程 |
| 部署 | `isDeploy()` / `getDeployId()` | 是否走部署 |
| 任务 | `getCodeTaskList()` / `addTask()` / `addAllTask()` | **动态追加任务** |
| 拦截 | `getInterceptorList()` / `addTemplateInterceptor()` | **模板改写** |
| 传输 | `getTransportHandlerList()` / `addTransportHandler()` | **部署处理** |
| 感知 | `getContextAwareList()` / `addContextAware()` | 上下文注入 |
| 动态参数 | `getDynamicArgs()` / `putArgs()` | 扩展参数 |
| 增量 | `getComparedSchemaIdSet()` | 与上次对比 |
| 父上下文 | `getParentContext(): MetaDatable` | **元数据入口** |

**★ 结论：CodeTask 不是硬编码列表，由插件注册 + 调用方动态追加。**

```java
com.seeyon.udc.PluginDefinition#getCodeTasks(): Collection<CodeTask>
CodeParam#addTask(CodeTask)
CodeParam#addAllTask(List<CodeTask>)
```

**★★ 第二证据源确认（`extension-points.md`）：**

```
PluginDefinition | abstract=2 | impl=0 | 包 com.seeyon.udc
```

**⇒ `PluginDefinition` 是 27 个「纯扩展位」之一，平台零实现。**
**⇒ 客户必须自己实现它来注册自定义 `CodeTask`。**
**⇒ 这是「如何给平台加自定义生成任务」的**唯一**入口。**

**证据等级：** `VERIFIED_STATIC_BYTECODE`（签名）+ `STATIC_RULE`（扩展点表，双源）

### 2.3 ★ CodeTask 52 个实现的第二证据源确认

`extension-points.md` 独立统计：

```
CodeTask | abstract=1 | impl=52 | 包 com.seeyon.udc.common.autocode
```

**⇒ 与我脚本统计的 52 个实现完全吻合。**
**⇒ 这是双源确认，不再是单源结论。**

**同表还确认了：**
```
TransportHandler | abstract=1 | impl=32   ← 我此前说 30+，精确为 32
Interpreter      | abstract=1 | impl=9    ← 完全吻合
CodeContextAware | abstract=1 | impl=5
TenantDataFilter | abstract=1 | impl=2    ← ★ 租户数据过滤器（DefaultTenantDataFilter / PageTenantDataFilter）
```

**★ `TenantDataFilter`（2 实现）是租户隔离的扩展点**，包在 `com.seeyon.udc.common.autocode.transport`。
**⇒ 这印证了 `tenantAdd()` 的租户注入机制有扩展位。**

### 2.4 生成参数构建

---

## 3. CodeTask 全表（52 个实现）

### 3.1 按包分布

| 包 | 数量 | 性质 |
|---|---|---|
| `com.seeyon.udc.autocode.task` | 30 | 主生成任务 |
| `com.seeyon.udc.autocode.task.front` | 5 | 前端元数据任务 |
| `com.seeyon.udc.autocode.v27.task` | 9 | **版本化（v27）** |
| `com.seeyon.udc.autocode.v27.task.front` | 5 | **版本化前端（v27）** |
| `com.seeyon.udc.extend.task` | 1 | `CtpExcelJsonTask` |
| `com.seeyon.udc.extend.detection.associate.deploy` | 1 | `AssociateCodeTask` |
| `com.seeyon.udc.extend.domain.service.deploy` | 1 | `CtpEnumCodeTask` |
| `com.seeyon.udc.common.autocode` | 1 | **接口自身，非实现** |

### 3.2 主任务职责（基于方法名推断，标注证据等级）

| CodeTask | 方法数 | 关键方法 | 推断职责 | 等级 |
|---|---|---|---|---|
| `EntityTask` | 2 | `code`, `deployEntity(EntityFileTemplate, EntityDto)` | 生成实体全套 | `VERIFIED`（有 Template 参数） |
| `DtoTask` | 3 | `code`, `getCtpEnumMapByApp`, `deepFlatten` | 生成 DTO | `VERIFIED`（方法名+命名） |
| `EntityRuleTask` | 16 | `matches`, `code`, `generateAggregateRootEntityRule`, `generateRootEntityRuleCode`, `handleAttributeUniqueActivity`, `buildConditionMethodName`, `negateCondition` | **生成实体规则（含聚合）** | `VERIFIED` |
| `PageEntityControllerTask` | **67** | `deployResourceAuth`, `deployPageController`, `deployRunTimeDataSource`, `deployPageCustomDto`, `writeToFile(AbstractFreemarkerTemplate)`, `buildChildrenEntityMultimap`, `isBillEntity` | **页面实体 Controller（最复杂）** | `VERIFIED` |
| `PageControllerTask` | 24 | `handlerFilterPlan2AutoCode`, `changeEntity2AppServiceMetaDataDtoMap`, `changeEntity2EntityMetaDataDtoMap`, `changeEntity2DtoMetaDataDtoMap`, `handlerPageAutoCodeDto` | 页面 Controller + 元数据 DTO 转换 | `VERIFIED` |
| `MicroFlowCodeTask` | 16 | `writeToCustomRestApiMicroFlowControllerFile`, `buildInOutMap`, `scheduleTriggerCodeTask`, `buildOutputEntityService`, `buildRealInput`, `pretreatmentNode` | 微流程代码 | `VERIFIED` |
| `EnumTask` | 1 | `code` | 枚举 | `STATIC` |
| `EventTask` | 2 | `code`, `genBusinessEventClass` | **业务事件类** | `VERIFIED` |
| `SerialConfigTask` | 1 | `code` | 流水号配置 | `STATIC` |
| `StaticFileTask` | 1 | `code` | 静态文件 | `STATIC` |
| `StaticExtFileTask` | — | — | 扩展静态文件 | `STATIC` |
| `ReferConfigTask` | 2 | `code`, `copyReferConfig` | 引用配置 | `VERIFIED` |
| `ReferControllerTask` | 13 | `getEntityRefer2`, `getPageReferMap`, `getReferUrl`, `getRestMapping2`, `deployEntityReferConfigList` | 引用 Controller | `VERIFIED` |
| `FilterPlanTask` | 6 | `getFilterPlanRts`, `buildDmlFileDto`, **`getMasterEntity`**, **`getAggEntityAllAttribute`** | **过滤方案 + 聚合实体** | `VERIFIED` |
| `DynamicSearchTask` | 1 | `code` | 动态搜索 | `STATIC` |
| `OutAppAppServiceProxyTask` | 2 | `code`, `writeToFile(OutAppAppServiceProxyTemplate)` | 外部应用代理 | `VERIFIED`（有 Template 参数） |
| `CodeConfigTask` | 1 | `code` | 代码配置 | `STATIC` |
| `AppBuildInfoTask` | 1 | `code` | 构建信息 | `STATIC` |
| `AppDependenciesTask` | — | — | 依赖声明 | `STATIC` |
| `AppInitFileTask` | 3 | `code`, `matches`×2 | 初始化文件 | `VERIFIED` |
| `MgnInitFileTask` | — | — | 管理端初始化 | `STATIC` |
| `OssMetadataTask` | 14 | `writeJson2file`, `writeScalabilityFieldJson2file`, `writeIdFullName2File`, `writePageSchema2File`, `writeLayoutSchema2File`, `writeMicroFlowSchema2File` | **元数据 JSON 输出到 OSS** | `VERIFIED` |
| `PageInfoTask` | 8 | `replaceIdToFullName`, `replaceEnumIdToFullName`, `replaceCtpEnumIdToFullName`, `replaceMasterEntityInfoToFullName`, `toCamelCase` | **页面元数据 ID→FullName** | `VERIFIED` |
| `ReferenceMetaDataTask` | 1 | `code` | 引用元数据 | `STATIC` |
| `CtpJobTask` | 1 | `code` | 定时任务 | `STATIC` |
| `AttachmentTemplateTask` | 1 | `code` | 附件模板 | `STATIC` |
| `AppBeanNameModifyerTask` | — | — | Bean 名改写 | `STATIC` |
| `CtpEnumIdsMetadataTask` | — | — | CTP 枚举 ID 元数据 | `STATIC` |
| `TestDeployStaticFileTask` | — | — | 测试部署 | `STATIC` |

### 3.3 ★ 主子表相关的方法证据（跨 Task）

| 类 | 方法 | 说明 | 等级 |
|---|---|---|---|
| `EntityTask` | `deployEntity(EntityFileTemplate, EntityDto)` | 实体部署（含聚合） | `VERIFIED` |
| `EntityRuleTask` | `generateAggregateRootEntityRule(CodeContext, Map<String,Entity4CodeDto>, Set<String>)` | **聚合根规则生成** | `VERIFIED` |
| `EntityRuleTask` | `generateRootEntityRuleCode(List<Long>, Map<Long,EntityDto>, Map<String,Entity4CodeDto>, EntityRuleAggregateTemplate, Set<String>, Supplier<GroupTypeEnum>)` | **用 `EntityRuleAggregateTemplate`** | `VERIFIED` |
| `FilterPlanTask` | `getMasterEntity(Long, String, Map<Long,EntityDto>): EntityDto` | **找主实体** | `VERIFIED` |
| `FilterPlanTask` | `getAggEntityAllAttribute(EntityDto, Map<Long,AttributeDto>, List<...>)` | **聚合实体全部属性** | `VERIFIED` |
| `PageEntityControllerTask` | `buildChildrenEntityMultimap(Map<String,UdcEntityMetaDataDto>): Multimap` | **构建子实体多重映射** | `VERIFIED` |
| `PageEntityControllerTask` | `containOne2One(...)` / `buildOne2oneEntityInfo4Up/Down` | **一对一关联处理** | `VERIFIED` |
| `PageEntityControllerTask` | `isBillEntity(String): boolean` | **判断单据实体** | `VERIFIED` |
| `PageEntityControllerTask` | `mergeOne2OneReferCarry(...)` | 一对一引用携带合并 | `VERIFIED` |

**⇒ 主子表（聚合）在生成期的处理分布在 4 个 Task 里，不是单一 Task 负责。**
**⇒ 这解释了为什么 `EntityRuleAggregateTemplate` 只出现在 `EntityRuleTask` 里，但聚合逻辑散落多处。**

---

## 4. Template 全表（36 个，口径 A）

### 4.1 按包分布

| 包 | 数量 |
|---|---|
| `com.seeyon.udc.autocode.template` | 23 |
| `com.seeyon.udc.autocode.v27.template` | 13 |

### 4.2 主包 23 个 Template

| Template | 关键方法 | 用途推断 |
|---|---|---|
| `EntityFileTemplate` | **8 个 OutPath** + `resolveBpmProcess` / `resolveSerial` / `resolveDefaultValue` / `getEntityReferAgg4CodeDto` / `copyNeedResetNull` | **实体全套生成（核心）** |
| `EntityRuleTemplate` | `getBaseServiceOutPath`, `getDubboServiceMap`, `getSubMfList` | 实体规则 |
| `EntityRuleAggregateTemplate` | `getLayerMap`, `getCapRootEntityName`, `getTargetGroupType`, `getRootEntityAssignValueServiceOutPath` | **主子表聚合** |
| `DtoCodeTemplate` | — | DTO |
| `PageEntityControllerTemplate` | — | 页面实体 Controller |
| `PageControllerTemplate` | — | 页面 Controller |
| `PageCustomControllerDtoTemplate` | — | 页面自定义 DTO |
| `MicroFlowTemplate` | — | 微流程 |
| `MicroFlowWebTemplate` | — | 微流程 Web |
| `MicroFlowWebControllerTemplate` | — | 微流程 Web Controller |
| `MicroFlowTriggerTemplate` | — | 微流程触发器 |
| `MicroFlowScheduleTemplate` | — | 微流程调度 |
| `HostAppMicroFlowTemplate` | — | 宿主应用微流程 |
| `CustomMicroFlowControllerTemplate` | — | 自定义微流程 Controller |
| `CustomRestApiMicroFlowControllerTemplate` | — | 自定义 REST API |
| `CustomMicroFlowTemplateSupport` | — | 微流程模板支持 |
| `ReferTemplate` | — | 引用 |
| `EntityReferTemplate` | — | 实体引用 |
| `EntityReferTemplate2` | — | 实体引用 v2 |
| `DynamicSearchTemplate` | — | 动态搜索 |
| `FilterPlanTemplate` | — | 过滤方案 |
| `StaticFileTemplate` | — | 静态文件 |
| `OutAppAppServiceProxyTemplate` | — | 外部应用代理 |
| `ConnectorBusinessEventTemplate` | — | 连接器业务事件 |

**（注：上表 24 行，因 `CustomMicroFlowTemplateSupport` 是 Support 类不是模板载体，实际模板载体 23 个）**

### 4.3 `EntityFileTemplate` 的 8 个输出路径（核心）

```java
getEntityOutPath()          // 实体
getDtoOutPath()             // DTO
getAppServiceOutPath()      // AppService 接口
getAppServiceImplOutPath()  // AppService 实现
getControllerOutPath()      // Controller
getBaseServiceOutPath()     // Service（BaseService）
getMybatisXmlOutPath()      // Mapper XML
getDaoOutPath()             // DAO
```

**配套包路径方法：**
```java
getAppPacketName()  getEntityPackage()  getDtoPackage()  getEnumPackage()
```

**⇒ 这 8 个方法 = 「一个实体生成哪些文件」的权威答案（方法级）。**
**⚠️ 但方法体未见，拼接规则未知 → 需反编译或实测产物。**

---

## 5. Task → Template 直接证据（★ 本轮核心产出）

### 5.1 有签名级直接证据的 7 组

方法：检索「参数类型含 Template」的方法。

| CodeTask | 方法 | Template 参数 | 证据等级 |
|---|---|---|---|
| `EntityTask` | `deployEntity` | `EntityFileTemplate` | **`VERIFIED`** |
| `EntityTaskV27` | `deployEntity` | `EntityFileTemplate` | **`VERIFIED`** |
| `EntityTaskV27` | `deployOutEntity` | `EntityFileTemplate` | **`VERIFIED`** |
| `EntityTaskV27` | `deployEntityPageControllers` | `EntityFileTemplate` (+`TemplateBuilder`) | **`VERIFIED`** |
| `EntityRuleTask` | `generateRootEntityRuleCode` | `EntityRuleAggregateTemplate` | **`VERIFIED`** |
| `EntityRuleTaskV27V27` | `generateRootEntityRuleCode` | `EntityRuleAggregateTemplate` | **`VERIFIED`** |
| `OutAppAppServiceProxyTask` | `writeToFile` | `OutAppAppServiceProxyTemplate` | **`VERIFIED`** |
| `PageEntityControllerTask` | `writeToFile` | `AbstractFreemarkerTemplate`（基类） | **`VERIFIED`**（弱，基类） |
| `PageEntityControllerTaskV27` | `writeToFile` | `PageEntityControllerTemplateV27` | **`VERIFIED`** |

### 5.2 ★ 重要发现：v27 复用主模板

```java
com.seeyon.udc.autocode.v27.task.EntityTaskV27#deployEntity(
    com.seeyon.udc.autocode.template.EntityFileTemplate,   ← 注意：不是 v27.template
    com.seeyon.udc.common.dto.EntityDto): java.lang.String
```

**⇒ v27 任务用的是 `autocode.template.EntityFileTemplate`（主模板），不是 `v27.template.*`。**
**⇒ 「版本化」不等于「模板也版本化」。v27 只版本化了 Task 层。**

**证据等级：** `VERIFIED_STATIC_BYTECODE`

### 5.3 无直接证据的 43 个任务

**⚠️ 严格声明：以下任务没有签名级 Task→Template 证据，不得宣称对应关系。**

约 13 个有**命名候选**（如 `DtoTask → DtoCodeTemplate`），约 30 个**无候选**。

**⇒ 绝不能宣称「CodeTask 与 Template 一一对应」。**

### 5.4 待证清单

| # | 问题 | 验证方法 |
|---|---|---|
| 1 | 每个 Task 的 `code()` 实际 new 了哪个 Template | 反编译方法体 |
| 2 | `getTemplateOutMap()` 的 key 是模板路径还是逻辑名 | 反编译或实测 |
| 3 | `writeToString(Object, String)` 第二参是模板路径吗 | 反编译基类 |
| 4 | `matches()` 条件如何决定 Task 执行 | 反编译（`EntityRuleTask#matches` 已见签名） |
| 5 | v27 Task 的启用条件 | 查 `CodeParam#getCodeVersion` 取值来源 |

---

## 6. 模板加载与版本选择（★ v4 遗漏的机制）

### 6.1 模板路径适配

```java
com.seeyon.udc.cache.TemplateAdapter
  # adapt(String, AppCodeContext): String                          ← 路径适配
  # adapt(EarlyTemplate, AppCodeContext): EarlyTemplate            ← 对象适配
  # adaptTemplatePath(String, List<String>, String): String        ← ★ 路径解析（含候选列表）
  # lambda$adaptTemplatePath$2 / $1 / $0                           ← 3 个 lambda，说明有比较/排序逻辑
```

**⇒ `adaptTemplatePath(path, List<String> candidates, String ...)` 说明：**
**模板路径解析是「给一组候选，选最合适的」，不是单一固定路径。**
**⇒ 这是版本选择 + 回退机制的入口（待反编译确认）。**

**证据等级：** `VERIFIED_STATIC_BYTECODE`（签名）

### 6.2 模板缓存

```java
com.seeyon.udc.common.autocode.util.CacheUtils
  # generateAppTemplateCacheKey(long): String              ← 应用级模板缓存键
  # generateAppOutputTemplateCacheKey(long): String        ← 输出缓存键
  # generateTemplateCacheKey(EarlyTemplate): String        ← 模板级缓存键
  # generatorAppLevelCacheKey(String, String): String
  # getEnvironmentPrefix(): String                          ← ★ 环境前缀
```

**⇒ 模板有缓存层，且缓存键含环境前缀 ⇒ 很可能是 Redis（与已有记忆「运行态=Redis」吻合，待证）。**

**证据等级：** `VERIFIED_STATIC_BYTECODE`（签名）
**待证：** 缓存介质、失效策略

### 6.3 ★★ 模板内的版本分支指令（核心发现）

```java
com.seeyon.udc.common.autocode.extension.directive.PlatformVersionDirective
  # execute(freemarker.core.Environment, Map, TemplateModel[], TemplateDirectiveBody)
  # name(): String

com.seeyon.udc.common.autocode.extension.directive.UdcVersionDirective
  # execute(freemarker.core.Environment, Map, TemplateModel[], TemplateDirectiveBody)
  # name(): String
```

**⇒ 这是两个 Freemarker 自定义指令（`TemplateDirective`）。**

**⇒ 结论：模板文件内部可以用 `<@platformVersion>` / `<@udcVersion>` 指令做版本分支。**
**⇒ 这解释了 `_codegen_templates.json` 为什么按 2.7 / 2.8 / 2.9 / 3.0 分目录 —— 目录是一层，指令是另一层。**

**注册入口：**
```java
com.seeyon.udc.autocode.FreemarkerConfiguration
  # onApplicationEvent(ApplicationReadyEvent): void
  # lambda$onApplicationEvent$0(freemarker.template.Configuration,
  #                             com.seeyon.boot.starter.autocode.extension.directive.AutoCodeDirective): void
```

**⇒ 应用启动时（`ApplicationReadyEvent`）把自定义指令注册到 Freemarker `Configuration`。**

**证据等级：** `VERIFIED_STATIC_BYTECODE`（类与方法签名）
**⚠️ 未证：** 指令的具体语义、参数格式（需 .ftl 内容）

### 6.4 版本选择的完整机制（当前可证部分）

```
① CodeParam#getCodeVersion(): String           ← 调用方传入版本
② AutoCodeProperties#getCodeVersions(): List<String>   ← 平台支持版本列表
③ AutoCodeProperties#getTemplateDir(): String          ← 模板根目录
④ AutoCodeProperties#getDefaultTemplatePrefix(): String
⑤ TemplateAdapter#adaptTemplatePath(path, candidates)  ← 路径解析（含候选）
⑥ 模板内 <@platformVersion> / <@udcVersion> 指令        ← 模板级分支
```

**⇒ 版本选择是「四层叠加」，不是单一 if-else：**
1. 调用方指定版本（`CodeParam`）
2. 平台配置可用版本（`AutoCodeProperties`）
3. 目录路径解析（`TemplateAdapter`）
4. 模板内指令分支（2 个 Directive）

**证据等级：** ①-④ `VERIFIED_STATIC_BYTECODE`；⑤ `VERIFIED_STATIC_BYTECODE`；⑥ `VERIFIED_STATIC_BYTECODE`（存在性）

### 6.5 模板拦截（改写）

```java
// 引用点
CodeParam#addTemplateInterceptor(TemplateInterceptor)
CodeParam#addAllTemplateInterceptor(List<TemplateInterceptor>)
CodeParam#getInterceptorList(): List<TemplateInterceptor>
AppCodeContext#getInterceptorList(): List<TemplateInterceptor>
AutoCodeProperties#getNeedInterceptTemplate(): Boolean   ← 开关
com.seeyon.udc.autocode.interceptor.BaseAppCodeParamInterceptor

// 3 个客户实现（仅 4 个 getter 可见）
SanyTemplateInterceptor              getAppId/getNewAppName/getNewBasePackage/getTablePrefix
Sany2TemplateInterceptor             同上
SanyContractBasicDataTemplateInterceptor  同上
```

**⚠️ 证据边界：`TemplateInterceptor` 接口自身不在签名库（外部依赖 `boot.starter.autocode.template`），无法断言其方法签名。**

**⇒ 3 个实现的可见方法全是「重写应用名/包名/表前缀」的 getter。**
**⇒ 推断：拦截器用于「同一份设计在不同客户下生成不同命名」。**
**但改写逻辑本身未验证 → `UNVERIFIED`。**

---

## 7. 部署机制（★ v4 遗漏）

### 7.1 生成 ≠ 部署

```java
com.seeyon.udc.common.autocode.transport.TransportHandler    ← 接口
  # out(CodeContext): List<SchemaInfo>                       ← 输出 schema
  # compare(SchemaComparisonSourcePool)                      ← 对比
  # buildDmlFileDto(List<? extends BaseEntity>, List<...>)   ← 生成 DML
  # buildDmlFileDto(String, String, List<DmlFileDto>)        ← 生成 DML（重载）
  # isFormDeploy(CodeContext): boolean                       ← 是否表单部署
  # group(): String                                          ← 分组

com.seeyon.udc.common.autocode.transport.TransportHandlerAdapter
com.seeyon.udc.common.autocode.transport.DownloadTransportHandlerAdapter
com.seeyon.udc.common.transport.upgrade.AbstractUpgradeTransportHandler
```

### 7.2 已枚举的 30+ 个 TransportHandler

**元数据类：**
```
EntityTransportHandler            DtoTransportHandler
AttributeSetTransportHandler      AttributeGroupTransportHandler
EntityGroupTransportHandler       BasicDataTransportHandler
ExtendAttributeTransportHandler   ScalabilityTransportHandler
UdcEnumTransportHandler           CtpEnumTransportHandler
CtpParameterTransportHandler      CtpJobTransportHandler
ReferConfigTransportHandler       FilterPlanTransportHandler
FilterPlanFormalTransportHandler  BaseInfoTransportHandler
DependentApplicationTransportHandler
FormAppLastVersionTransportHandler
```

**页面类：**
```
PageTransportHandler  PageLayoutTransportHandler  PageTemplateTransportHandler
```

**流程类：**
```
MicroFlowTransportHandler  MicroFlowGroupTransportHandler  AppCollaborationTransportHandler
```

**其他：**
```
EventTransportHandler            SerialNumberTransportHandler
GanttChartTransportHandler       FormConvertTransportHandler
CtpQrCodeRuleTransportHandler    CtpExcelExportTemplateTransportHandler
```

**升级类：**
```
DeployRecordUpgradeTransportHandler      ServiceMetadataUpgradeTransportHandler
```

**⇒ 结论：**
1. **「生成文件」和「部署到平台」是两套机制**
2. `TransportHandler` 负责把 schema 部署进平台
3. `CodeParam#isDeploy()` 控制是否走部署
4. `AutoCodeManager#downloadAndZipLocal(ApplicationDto): File` 是下载路径（不走部署）

**证据等级：** `VERIFIED_STATIC_BYTECODE`（存在与签名）
**待证：** `out()` 的实际实现、部署顺序、失败回滚

### 7.3 元数据输出到 OSS

```java
com.seeyon.udc.autocode.task.OssMetadataTask
  # writeJson2file(...)
  # writeScalabilityFieldJson2file(...)
  # writeIdFullName2File(...)
  # writeReferIdFullName2File(...)
  # writeFilterPlanFormalJson2file(...)
  # writeFilterPlanRtJson2file(...)
  # writeFilterPlanJson2file(...)
  # writePageSchema2File(...)
  # writeLayoutSchema2File(...)
  # writeMicroFlowSchema2File(...)
  # writeMicroFlowGroupSchema2File(...)
  # (14 个方法)
```

**⇒ 元数据以 JSON 形式写到 OSS（与已有记忆「运行态=Redis→OSS」吻合）。**
**证据等级：** `VERIFIED_STATIC_BYTECODE`（方法名明确含 `2file`）

---

## 8. 生成参数构建

### 8.1 `getArgumentMap(): Map<String,Object>`

每个 Template 都声明这个方法（36 个全有）。
⇒ **渲染参数是 `Map<String,Object>`，键值语义未知。**

### 8.2 `EntityFileTemplate` 的参数构建方法（部分可见）

```java
getTableInfo(EntityDto): Map<String,Object>        ← 表信息
getTableInfoMap(): Map<String,Object>
getTableAttrList(EntityDto): Map<AttributeDto, Map<String,Object>>   ← 字段→属性
getTableAttrList4DbMap2Dto(Map<...>): List<...>
getJavaType(AttributeDto): String                  ← 字段→Java 类型
getDataType(AttributeDto): String
getDataTypeName(String): String
getDatabaseType(): DatabaseType                    ← 方言
```

**⇒ 参数构建的核心是「实体 + 字段 → 表信息 + 类型映射」。**
**⚠️ 拼接规则未见 → 需反编译。**

---

## 9. 生成 vs 手写边界

### 9.1 已证部分

| 机制 | 值/方法 | 含义 |
|---|---|---|
| `generator.properties` → `gg_isOverride` | `true` | 静态代码生成文件默认覆盖 |
| `AutoCodeProperties#getNeedInterceptTemplate()` | Boolean | 是否启用模板拦截 |
| `AutoCodeProperties#getCopyExtendCode()` | Boolean | 是否复制扩展代码 |
| `AutoCodeProperties#getTransportExtendCode()` | Boolean | 是否传输扩展代码 |
| `CodeParam#getComparedSchemaIdSet()` | Set | 增量对比范围 |
| `AutoCodeExecutor#compareToLast(...)` | void | 与上次对比 |

### 9.2 特性扩展的织入机制（来自专题 1）

```json
{"className": "$Class{entityName}Service", "classMode": "CLASS_SAME",
 "methods": [{"methodName": "createBatch", "methodType": "JOIN",
              "joinPoints": [{"joinPointName": "preCreateBatch", ...}]}]}
```

**⇒ 特性不重写整个类，而是在固定切点插入代码。**
**切点：`preCreateBatch` / `middle` / `preUpdateBatch` / `afterUpdate` / `after`**

**⇒ 这是「生成代码 vs 扩展代码」边界的机制级答案（对特性而言）。**

### 9.3 ⚠️ 未证

**`gg_isOverride = true` 不能推断「会覆盖用户手写代码」。**
用户手写代码通常在 `custom` 包（不受模板管），但**这一点未经证实**。
**标记 `UNVERIFIED`，需实测（审批项 B）。**

---

## 10. 证据清单

| # | 结论 | 等级 | 来源 |
|---|---|---|---|
| 1 | 生成主链 `AutoCodeExecutor#execute → runTask → CodeTask#code` | `VERIFIED` | 签名库 |
| 2 | `CodeContext` 仅 13 方法，不含元数据 | `VERIFIED` | 签名库 |
| 3 | `CodeParam` 21 方法控制 11 个维度 | `VERIFIED` | 签名库 |
| 4 | CodeTask 由 `PluginDefinition#getCodeTasks()` 注册 | `VERIFIED` | 签名库 |
| 5 | 任务可动态追加（`addTask`/`addAllTask`） | `VERIFIED` | 签名库 |
| 6 | 52 个 CodeTask 实现（14 v27 + 3 扩展） | `VERIFIED` | 脚本统计 |
| 7 | 36 个 Template（口径 A） | `VERIFIED` | 脚本统计 |
| 8 | `EntityFileTemplate` 8 个 OutPath | `VERIFIED` | 签名库 |
| 9 | **7 组 Task→Template 直接证据** | `VERIFIED` | 签名库（方法参数） |
| 10 | **v27 复用主 `EntityFileTemplate`** | `VERIFIED` | 签名库 |
| 11 | `TemplateAdapter#adaptTemplatePath` 含候选列表 | `VERIFIED` | 签名库 |
| 12 | 模板有缓存（`CacheUtils` 5 个键生成方法） | `VERIFIED` | 签名库 |
| 13 | **2 个 Freemarker 版本指令** | `VERIFIED` | 签名库 |
| 14 | `FreemarkerConfiguration` 启动时注册指令 | `VERIFIED` | 签名库 |
| 15 | 版本选择是四层叠加 | `VERIFIED` | 综合 |
| 16 | 模板拦截存在但逻辑未证 | `STATIC` | 签名库（仅接入点） |
| 17 | 部署由 30+ `TransportHandler` 承担 | `VERIFIED` | 签名库 |
| 18 | 元数据 JSON 输出到 OSS | `VERIFIED` | 方法名 |
| 19 | 特性用 joinPoints 织入 | `STATIC` | 配置 |
| 20 | `gg_isOverride=true` 默认覆盖 | `STATIC` | `generator.properties` |

---

## 11. 推翻/修正

| # | 旧结论 | 修正 |
|---|---|---|
| 1 | 「CodeTask 与 Template 一一对应」 | **仅 7 组有直接证据；43 个无证据** |
| 2 | 「v27 用 v27 模板」 | **v27 Task 复用主 `EntityFileTemplate`** |
| 3 | 「模板按版本目录选择」 | **目录是一层，模板内还有 `<@platformVersion>` 指令** |
| 4 | 「生成 → 产物」 | **生成 → 产物 → 部署（TransportHandler 两阶段）** |
| 5 | 「`CodeContext` 承载元数据」 | **只有路径+配置+上下文，元数据走 `CodeParam#getParentContext`** |

---

## 12. 未解决问题

| # | 问题 | 阻塞 |
|---|---|---|
| 1 | 各 Task 的 `code()` 实际 new 哪个 Template | 需反编译 |
| 2 | `getTemplateOutMap()` 返回值语义 | 需反编译/实测 |
| 3 | `adaptTemplatePath` 的候选选择算法 | 需反编译 |
| 4 | 2 个版本指令的参数格式 | 需 .ftl |
| 5 | `TemplateInterceptor` 接口定义 | 需 jar |
| 6 | `TransportHandler#out()` 实现 | 需反编译 |
| 7 | 重复生成的覆盖策略 | 需实测 |
| 8 | 8 个 OutPath 的拼接规则 | 需反编译/实测 |

---

## 13. 下一轮任务

1. **`EntityFileTemplate` 全方法语义梳理**（已有 100+ 方法签名，逐个归类）
2. **`EntityRuleTemplate` / `EntityRuleAggregateTemplate` 主子表链路**
3. **`TemplateAdapter` 与版本指令的调用方**
4. **转专题 3：DAO 持久化**（静态部分）
