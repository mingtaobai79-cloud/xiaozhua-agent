# standard-product｜UDC 自定义微流程接口与传参（后端 extend 工程）

> 本格回答**「我要继承谁、覆写哪个方法、参数是什么类型」**。
> 数据来自 **91 个构件**的 javap 全量签名（84 个原始标品构件 + udc-biz / udc-web / udc-cicd /
> app-approval-facade / m5-facade + udc-extend + udc-plugin-api），
> 逐字结构化：**10457 类 / 106335 方法 / 41152 个方法名可反查**。只含类名与方法签名，不含应用/工程/环境与版本。

分级：`VERIFIED_STATIC_BYTECODE`（javap 逐字，见 §8）。

## 1. Capability

自定义微流程（后端 extend）能挂的三类东西，一处查全：
- **四族扩展点**：元数据后处理 / 另存为 / 导入 / 出站，覆盖 7 类低代码对象
- **微流程被调入口**：`invokeAppServiceMethod` 及其两个 DTO（字段名即 REST 字段名）
- **可调标品**：Entity / Attribute / MicroFlowInfo 的 AppService 方法签名 + 组织人员构造

## 2. Version

不记版本。构件版本随客户环境漂移，需要时查证据件 `sources[包].jar`。

## 3. Input

`docs/audit/artifacts/extension-surface-<日期>/` 下的 batch2 包签名件与 `symbols-udc-extend.json`
（每件含 `classes[].javap` 原文，本格是它的结构化归纳，不重新反编译）

## 4. Required

无前置（离线）。

## 5. Execution

```bash
python tools/core/platform/index_backend_interfaces.py \
    --artifacts docs/audit/artifacts/extension-surface-20261029 \
    --packages udc-extend udc-facade udc-starter-runtime udc-starter-lowcode udc-common udc-starter-dataflow \
    --emit docs/audit/artifacts/extension-surface-20261029/interfaces.json
```

## 6. Side Effects

只读既有签名件。

## 7. Known Constraints

### 7.1 传输族四接口：接口契约 + 7 类能力实现

> **先更正一处口径**：本节这 4 个接口只是「传输/导入导出」**一族**，不是 UDC 扩展点的全部。
> UDC 实际有 **10 族 68 个**带 abstract 的接口（部署生命周期、权限、应用特性、应用内引用、
> 类型系统、代码生成、一致性检测等），全表见 §7.9。别只盯着这 4 个写。

写扩展只有两条路：**完全自定义就 implements 接口**（每个接口只有一个 abstract 方法），
**在现有能力上改行为就继承实现类**（见 §7.1.2）。自己新造同名功能的钩子不会被平台调用。

```
① 元数据后处理  interface AppMetaDataContextPostProcess
   void postProcessAppMetaDataContext(AppContext)          ← abstract，唯一必实现

② 另存为        interface SaveAsHandler
   void saveAs(TransportData)                              ← abstract，唯一必实现
   default void before(TransportData)
   default void normalSaveAs(TransportData)

③ 导入          interface Importable                       （11 个方法）
   void in(TransportData)                                  ← abstract，唯一必实现
   default void before(TransportData)
   default void transfer(TransportData)
   default void importValidate(TransportDataExploration)
   default boolean matches(TransportData)
   default <T> boolean transferFilter(TransferData, String, Class<T>)

④ 出站          interface TransportHandler                  （6 个方法）
   List<SchemaInfo> out(CodeContext)                       ← abstract，唯一必实现
   default ComparisonResponse compare(SchemaComparisonSourcePool)
   default void buildDmlFileDto(List<? extends BaseEntity>, List<DmlFileDto>)
   default void buildDmlFileDto(String, String, List<DmlFileDto>)
   default boolean isFormDeploy(CodeContext)
   default String group()
```

**每个接口只有一个 abstract 方法**，其余全是 default —— 这就是平台留的可覆写面。

#### 7.1.2 实现类清单（`udc-extend`，7 类能力）

```
① 元数据后处理  <Capability>MetaDataPostProcessor
   void postProcessAppMetaDataContext(com.seeyon.udc.common.metadata.AppContext)
   实测 6 个：CtpEnum · CtpExcelExport · CtpQrCodeRule · FormConvert · GanttChart · SerialNumber

② 另存为        <Capability>SaveAsHandler        （包 transport.handler）
   void saveAs(TransportData)
   void normalSaveAs(TransportData)
   void execute(ApplicationDto)   /   void execute(Object)
   实测 6 个：CtpEnum(7 方法) · CtpExcelExport(5) · CtpFormConvert(4)
             CtpParameter(2) · CtpQrCodeRule(7) · CtpSerialNumber(5)
   另有 CtpExcelTemplateUpgradeHandler（模板升级，2 方法，不属于 SaveAs 族）

③ 导入          <Capability>ImporterBase         （包 transport.in）
   void before(TransportData)
   void transfer(TransportData)
   void in(TransportData)
   java.util.Set<java.lang.String> ignoreOnDefaultCopy()
   实测 7 个：CtpEnum(30) · CtpExcelExportTemplate(11) · CtpParameter(9)
             CtpQrCodeRule(10) · CtpSerialNumber(17) · FormConvert(6) · GanttChart(5)

④ 出站          <Capability>TransportHandler      （包 transport.out）
   java.util.List<com.seeyon.udc.common.transport.SchemaInfo> out(CodeContext)
   com.seeyon.udc.common.autocode.transport.compare.ComparisonResponse
       compare(SchemaComparisonSourcePool)        ← 只有 CtpEnum 有 compare
   实测 6 个：CtpEnum(5) · CtpExcelExportTemplate(1) · CtpQrCodeRule(1)
             FormConvert(1) · GanttChart(1) · SerialNumber(5)
```

**导入三段顺序是平台定的**：`before`（前置准备）→ `transfer`（转换）→ `in`（落库）。
覆写时只补自己那一段，别把逻辑全塞进 `in` —— 平台在 `before` 之后会做校验。

### 7.2 微流程被调入口（`udc-starter-runtime`）

```java
class MicroFlowProxyAppMicroFlow {
    Object invokeAppServiceMethod(MicroFlowRestRequestDto request);        // ← 自定义服务节点的最终落点
    Object wrapDisplayNameResponse(ListResponse<Map<String, ?>>, BaseResponse,
                                   InvokeMethodMetadata);                 // 显示名包装，别自己写
    RuntimeEntityDataSourceDto getRuntimeEntityDataSourceByJsonFileName(String jsonFileName);
}

class MicroFlowRestRequestDto {
    static MicroFlowRestRequestDto fromGet(MicroFlowRestPathMetadataDto meta);
    static MicroFlowRestRequestDto fromPost(Object body, MicroFlowRestPathMetadataDto meta);
    Object getRequestData();
    MicroFlowRestPathMetadataDto getRestMetadata();
    // 字段：requestData(Object) · restMetadata(MicroFlowRestPathMetadataDto)
}

class MicroFlowRestPathMetadataDto {
    String getMicroFlowId();        String getMicroFlowName();
    MicroFlowTypeEnum getMicroFlowType();     boolean isCustomMicroFlow();
    String getServiceInterface();   String getInvokeAppName();
    RequestMethod getReqMethod();   String getHostAppName();
    String getAppName();            boolean isFromCustomApp();
    Map<String, Object> getMicroFlowBaseInfo();
    static ReqMethod builder();
    // 字段：reqMethod · hostAppName · appName · fromCustomApp · microFlowBaseInfo
}
```

⇒ 想在「调用 AppService」这类节点上加行为，接 `invokeAppServiceMethod`；
返回值统一走 `wrapDisplayNameResponse`，自己再包一层会和平台的显示名逻辑打架。
`isCustomMicroFlow()` / `isFromCustomApp()` 是判断「当前这次调用是不是自定义微流程发起的」的唯二入口。

### 7.3 组织人员构造（`MicroFlowOrgPeopleService`，8 个方法逐字）

```java
OrgMemberPostCoreDto       buildMemberPostByMemberId(String memberId)
List<OrgMemberPostCoreDto> buildMemberPostByOrgTypeAndIds(String orgType, List<Long> ids)
List<OrgMemberPostCoreDto> buildMemberPostByOrgType(String orgType, String orgIds)
OrgMemberCoreDto           buildMemberCoreByUserId(String userId)
List<OrgMemberCoreDto>     buildMemberCoreByPeopleData(SelectPeopleDataDto)
List<OrgMemberCoreDto>     buildMemberCoreByPublishScope(String publishScope)
List<OrgMemberPostCoreDto> buildMemberPostCoreByPublishScope(String publishScope)
List<OrgMemberPostCoreDto> buildMemberPostByPeopleData(SelectPeopleDataDto)
```

⇒ 微流程里要做「选人结果 → 人员/岗位对象」的转换，用这组方法；
不要自己解析组织 id 字符串。`build*ByPeopleData(SelectPeopleDataDto)` 是拿到前端选人结果后的标准入口。

### 7.4 自定义错误

```java
class MicroFlowCustomErrorException {
    String code();
    String message();
}
```

⇒ 自定义微流程抛业务错误用这个类，`code()` 会进错误码，`message()` 进提示。
不要抛裸 `RuntimeException` —— 平台按 `code()` 做错误分类与前端提示映射。

### 7.5 可调的标品 AppService（`udc-facade`，入参恒为 `SingleRequest`）

```java
interface EntityAppService {          // 18 方法
  SingleResponse<Long>                   create(SingleRequest<EntityDto>);
  SingleResponse<Integer>                update(SingleRequest<EntityDto>);
  SingleResponse<Integer>                deleteById(SingleRequest<Long>);
  SingleResponse<Integer>                deleteByIds(SingleRequest<List<Long>>);
  SingleResponse<EntityDto>              selectById(SingleRequest<Long>);
  ListResponse<EntityDto>                selectByIds(SingleRequest<List<Long>>);
  // 另有 selectByName / selectPageByCondition / selectListByConditions /
  //      selectListByTerm / selectParentById / selectEntitiesByAppId4Tree
}

interface AttributeAppService {       // 15 方法
  SingleResponse<Long>                   create(SingleRequest<AttributeDto>);
  SingleResponse<Integer>                createBatch(SingleRequest<List<AttributeDto>>);
  SingleResponse<Integer>                update(SingleRequest<AttributeDto>);
  SingleResponse<AttributeDto>           selectById(SingleRequest<Long>);
  ListResponse<AttributeDto>             selectListByCondition(ListRequest);
  ListResponse<AttributeDto>             selectAllAttributeByEntityId(SingleRequest<Long>);
}

interface MicroFlowInfoAppService {   // 2 方法
  SingleResponse<Map<String, List<String>>>              findCallConnectorAppService(SingleRequest<Long>);
  SingleResponse<MicroFlowIntegrationAppInfoDto>         findCallIntegrationAppService(SingleRequest<Long>);
}
```

其余 facade 规模（按方法数）：`ApplicationManagerAppService` 53 · `DesignMetadataQueryAppService` 49 ·
`EntityAppService` 18 · `AttributeAppService` 15 · `AppCollaborativeAppService` 5 · `MicroFlowInfoAppService` 2。

### 7.6 传参四条铁律

1. **入参恒包 `SingleRequest<T>`**，返回 `SingleResponse<T>` 或 `ListResponse<T>`；
   不会出现裸参数（除 `*ByTerm` 那类多参数方法内部再包一层）。
2. **两层取值**：`resp.getData()` 是 `SingleData<T>`，还要再 `.getContent()`；
   `ListResponse` 则是 `.getData().getContent()` 拿到 `List<T>`。
3. **`Sort` 用 `com.seeyon.boot.transport.Sort`**，不是 Spring 的 `Sort`；混用编译不过或排序静默失效。
4. **DTO 字段名即 REST 字段名**：`MicroFlowRestPathMetadataDto` 的 `appName/hostAppName/fromCustomApp`
   就是请求里那几个键，不要自造别名。

### 7.7 传参对象：进方法后从哪取数据（`udc-plugin-api`）

`TransportData` 是导入 / 另存为 / 出站的**唯一入参**，它的父类是 `BaseTransportData`。

```
TransportData  (com.seeyon.udc.common.schema)
  字段  ApplicationSchemaDto appSchema                     ← 整个应用的 schema 树
       Map<String, List<FileDto>> attachmentFileDtoMap
       ApplicationDto originalApp                          ← 另存为时是「旧侧」
       Map<String, Object> params
  取值  List<FileDto> getCommonAttachmentFileDtoList(String)
       List<FileDto> getAttachmentFileDtoList(String, String)
       VersionControl getVersionControl()
       String getSourceDesignerVersion()
       boolean isForm()
       boolean exists(String, String)          /  existsUdcSchema(String)
       void udcDefaultCopy(String...)                          ← 默认拷贝，走平台替换链
  静态  String getEntityFullNamePrefix(ApplicationDto)
       String getEntity4DtoFullNamePrefix(ApplicationDto)
       String getEntity4EventFullNamePrefix(ApplicationDto)
       String getUdcEnumFullNamePrefix(ApplicationDto)
       String getBasePackage(ApplicationDto)

BaseTransportData  (父类：id 映射与候选池都在这里)
  字段  List<SchemaInfo> schemaAll
       Map<…, SchemaInfo> schemaGroupByModelAndDataId
       ImportConfig importConfig   /   ResetResult resetResult
  取值  Map<String,String> getIdMap()            ← 源 id → 目标 id，导入后重写关系全靠它
       Map<String,String> getNewToOldIdMap()
       String getSourceId(String)   /  String getTargetId(String)
       String getSourceGuid(String) /  String getTargetGuid(String)
       String getCandidate(String)  /  Object getCandidateObj(String)
       void putCandidate(String, String) / putCandidateObj(String, Object)
       TransportTypeEnum getTransportType()
       String getCurrentDesignerVersion()
       void unsafeNextStrReplace(String, String) / unsafeReplaceWithRecord(String, String, String)

AppContext  (元数据后处理的入参)
   ApplicationDto getAppInfo()                 ← 应用本体
   AppContextListener getAppContextListener()
   String getLogSuffix()   /   Long getTenantId()

CodeContext  (出站 out() 的入参)
   AutoCodeProperties getAutoCodeProperties()
   VersionControl getVersionControl()
   String getBasePackage() / getAppName4Package() / getAppName() / getBasePackagePathStr()
   String getModelJavaPath(String, String...) / getModelResourcePath(String, String...)
   String getAuthor() / getCreateTime()
   AppDbInfoDto getAppDbInfoDto() / I18nContext getI18nContext()
   default String getPackage(ApplicationDto, String...)

SchemaParam  (导入参数开关，决定这次导入是模板/另存为/传输)
   boolean isTemplate() / isSaveAs() / isTransportInfo() / isNeedValidateResult()
   ApplicationCopyDto getCopyInfo() / ApplicationSourceEnum getAppType()
   Set<String> getIgnoreDataIdSet() / ApplicationDto getApplicationDto()   (+ 对应 setter)
```

⇒ 三条实战口径：
- **拿 id 映射用 `getIdMap()` / `getNewToOldIdMap()`**，不要自己拼 guid —— 导入后所有关系重写都靠这张表。
- **另存为时 `originalApp` 是旧侧、`appSchema` 是新侧**，做差异比对就在这两者之间比。
- **不要直接改 `schemaAll` / `schemaGroupByModelAndDataId`**，平台靠它们做 reset 与去重。

### 7.8 运行时工具类速查（`udc-starter-runtime`，全 static，别重写）

```
写运行日志   UdcAppLogHelper (61 方法)
  static void buildMfLog(String, ModuleSubTypeEnum, String, String, Long)
  static void buildMfLogV2(String, ModuleSubTypeEnum, String, String, Long, …)
  static void buildInputLog(String, ModuleSubTypeEnum, Object, Long)
  static void buildEndLog(String, Object, Long)

计算规则     EntityRuleUtil (7)
  static boolean checkObjectOrString(Object)
  static boolean isNotDeleteActionType(Object)
  static Set<Long> getDeletedIds(List<? extends BaseEntityActionDto>)

表达式       ExpressionRuntimeUtil (1)
  static BigDecimal setDecimalScale(Object, int, RoundingMode)

微流程运行时 MicroFlowRuntimeUtil (5)
  static void saveDefaultValue4RequestContext()
  static <T, U> void setFieldValueInDataMappingActivity(Map<String,Object>, String, T, Function…)
  static DataFlowExecuteParamDto buildDataFlowExecuteParamDtoWithCondition(Map<String,Object>, …)
  static DataFlowExecuteParamDto buildDataFlowExecuteParamDtoWithSelectParam(List<? extends …>)

实体权限     EntityAuthHelper (12)
  void check(BaseDto)
  void checkBpmSummaryPermission(BaseDto)

JSON         UdcJsonUtils (8)
  static String toJson(Object)   /   toJson(Object, boolean)
  static Map<String,Object> toMap(String)
  static <K,V> Map<K,V> toMap(String, Class<K>, Class<V>)

反射         UdcReflectUtil (31)
  static Object getFieldValue(Object, String)
  static void setFieldValue(Object, String, Object)
  static boolean hasField(Object, String)
  static List<Field> getFiledList(Class)        ← 方法名原文就是 getFiledList（少个 l）
  static void clearCache()   /   clearCache(Class)

系统变量     SystemFunctionUtil (1)
  static Object getSystemValueByFunc(String)

日期         DateUtil (8)
  static Date getDateByTimeStampOrDateTimeString(String)
  static Date getDateByTimeStampOrDateString(String)
  static String getDateTimeFormatStringByTimeStampOrString(String)
  static String getDateFormatStringByTimeStampOrString(String)
  static int getSecondsByTimeString(String)

树实体       TreeEntityUtil (5)
  static String getCodePatternByLength(int)
  static void checkCurLevelCode(int, String)
  static List<Long> getTreeEntityIdsByTreePath(String)
```

⇒ 横切能力（写日志 / 查权限 / 翻译枚举 / 取表达式值 / JSON 转换）先在这里按名找，
平台已有实现；自己重写一份最容易在租户上下文、脱敏、日志格式上出问题。
注意 `getFiledList` 的拼写是原文，按 `getFieldList` 写会编译不过。

### 7.9 UDC 扩展点总账：151 个可 implements 接口

数据源 `interfaces.json`（91 个构件）：**1145 个接口** = **1036 个真接口** + **109 个注解**
（`@interface` 不能 implements）。真接口里 **755 个带 abstract** = 真正可 implements 的。
人读全量清单 `interface-inventory.md`；扩展点 × 平台实现落地表 `extension-points.md`。

**UDC 侧口径链（四个数别混）**：

```
274 个 UDC 接口 = 250 个真接口 + 24 个注解
250 个真接口   = 55 个 *AppService（调用面，你调它，不实现它）
               + 195 个其他
195 个其他     = 128 个带 abstract（= 扩展点，可实现）+ 67 个无 abstract（标记 / 纯 default）

⇒ 128 扩展点 + 23 注解 = 151 个带 abstract 的接口
   （55 个 AppService 也全带 abstract，但它们是调用面，不计入扩展点）
```

**151 个带 abstract 的接口**分两种性质：
**128 个是真接口**（101 个平台已有实现、27 个纯扩展位）+ **23 个是注解**（`@interface`，
如 `Importer` / `UpgradeMethod` / `OperationLog` / `LogDefault` / `DelDetection` / `UpdateDetection` /
`TypeMapping` / `AppOpsAuth` / `AuthModel` / `AuthOperation`——贴在代码上由平台读，**不 implements**）。

按平台自带实现数排（impl 多 = 该族主接口，先看它）：

| 扩展点 | abstract | 平台实现 | 干什么 |
|---|---|---|---|
| `CodeTask` | 1 | 50 | 代码生成任务，每个生成物一个 Task |
| `TransportHandler` | 1 | 32 | 导出：把 schema 某一段写成文件 |
| `Importable` | 1 | 29 | 导入 |
| `AppMetaDataContextPostProcess` | 1 | 27 | 元数据构建后处理 |
| `ElementRepository` | 3 | 21 | 元数据元素的统一读写口 |
| `SaveAsHandler` | 1 | 17 | 另存为 |
| `BaseDesignMetadataQueryService` | 6 | 11 | 设计态元数据查询 |
| `Interpreter` | 1 | 9 | 表达式 / 变量解释器 |
| `DetectionMetadataAware` | 1 | 9 | 一致性检测的元数据装配 |
| `LastVersionMetadataManagerService` | 3 | 8 | 上一版本元数据保留 |
| `CopyHandler` | 2 | 7 | 复制（应用 / 实体 / 属性） |
| `DeployBeforeService` | 1 | 7 | 部署前检查，能拦下发布 |
| `MicroFlowSimpleComponentCascadeHandler` | 1 | 6 | 微流程组件级联删除/更新 |
| `FrontDeployDetectionTask` | 1 | 5 | 前端部署检测 |
| `SplitHandler` | 1 | 5 | 导入时的模块拆分 |
| `TypeChangeSqlResolver` | 2 | 5 | 属性类型变更的 SQL |
| `SourceDetectionSupport` | 3 | 5 | 检测数据来源 |
| `OperationRecordService` | 6 | 5 | 操作日志明细构造 |
| `AppFeatureHandler` | 14 | 3 | 应用特性（hostAppName / AppUrl / DB 信息） |
| `Template` | 29 | 2 | 代码模板 |

完整 151 个（含 50 个纯扩展位与接口所在包）：`extension-points.md`。

⇒ 四条铁律：
- **AppService 是调用面**（26 个，入参恒 `SingleRequest`），不要 implements。
- 判断能否当扩展点：**是接口（不是注解）+ 有 abstract 方法 + 说得出平台在哪一步调它**。
  128 个真接口里有 101 个平台自己就实现了，那 101 个最安全——照着它的实现类写。
- 27 个纯扩展位零实现，写之前必须先确认注册方式（`META-INF/services` / `spring.factories` /
  Spring 包扫描）；**平台不带自动装配**，`udc-extend` 那套示例类跨 65 个 jar 零引用就是证明。
- 同名接口在不同包（`BaseNode` / `BaseTrigger` / `Functor` / `ApplicationInnerReference`），
  implements 时认全限定名。

## 8. Evidence

```
① 路径  docs/audit/artifacts/extension-surface-20261029/interfaces.json（55 MB）
        sources{包:{jar,classes,total_methods}} · classes{fqcn:{kind,decl,extends,implements,methods[],fields[]}}
        • method_index{方法名:["类#方法"]}（41152 个方法名可反查）
        • 覆盖 91 个构件 → 10457 类 / 106335 方法
        配套件 interface-inventory.md（1145 个接口全量）· extension-points.md（151 扩展点 × 平台实现）
② 复现  python tools/core/platform/extract_jar_symbols.py --jar <udc-plugin-api jar> \
            --include com/seeyon/udc/ --javap <javap> --limit 2000 --emit symbols-udc-plugin-api.json
        # ↑ --limit 默认 60，不加会按字母序静默截断
        python tools/core/platform/index_backend_interfaces.py --artifacts <dir> \
            --packages <batch2 全部 84 个构件名> udc-extend udc-plugin-api --emit interfaces.json
③ 校验  每个类的 methods[].signature 都是 javap 原文一行；method_index 里每个条目必须能在 classes 找到
④ 抽验  四族 4 个接口契约 + 21 个实现类 + MicroFlowProxyAppMicroFlow(5) +
        MicroFlowRestPathMetadataDto(14) + TransportData/BaseTransportData/AppContext/CodeContext
        与 javap 原文逐一对应
```

## 9. Verified

| 项 | 等级 | 说明 |
|---|---|---|
| 四族 4 个接口契约（各 1 个 abstract + default 面） | VERIFIED_STATIC_BYTECODE | javap 逐字，接口在 `udc-plugin-api` |
| 四族 21 个实现类的方法签名 | VERIFIED_STATIC_BYTECODE | javap 逐字，7 类能力全覆盖 |
| `TransportData` / `BaseTransportData` / `AppContext` / `CodeContext` / `SchemaParam` | VERIFIED_STATIC_BYTECODE | 字段与取值方法逐字，见 §7.7 |
| 微流程被调入口与两个 DTO 字段 | VERIFIED_STATIC_BYTECODE | javap 逐字 |
| Entity/Attribute/MicroFlowInfo 方法签名 | VERIFIED_STATIC_BYTECODE | javap 逐字 |
| 组织人员 8 个构造方法 | VERIFIED_STATIC_BYTECODE | javap 逐字 |
| 这些方法在运行时的真实行为 | 未验证 | 未在运行时断点/抓包验证调用链 |

## 铁律

- 加行为只在四族里继承/覆写，自己新造钩子不会被平台调用。
- 四族每个接口只有 **1 个 abstract 方法**（其余全是 default）：完全自定义就 implements 接口，
  只想改一小段就继承实现类覆写对应 default。
- 导入三段 `before → transfer → in` 顺序由平台控制，只补自己那一段。
- 拿 id 映射用 `getIdMap()` / `getNewToOldIdMap()`，不要自己拼 guid；另存为时 `originalApp` 是旧侧。
- 微流程返回包装一律用 `wrapDisplayNameResponse`，别自己拼显示名。
- 所有 facade 入参 `SingleRequest<T>`，取值 `getData().getContent()` 两层。
- `Sort` 认 `com.seeyon.boot.transport.Sort`；`MicroFlowRestPathMetadataDto` 字段名即 REST 键名。
- 业务错误抛 `MicroFlowCustomErrorException(code, message)`，不要抛裸 `RuntimeException`。
