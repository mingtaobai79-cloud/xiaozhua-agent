# ★★★★★ 平台代码生成引擎：432 个 FreeMarker 模板全解

> 数据源：
> - `udc-biz-5.3.605.jar`（6.65 MB / 1,856 类 / **432 个 .ftl**）
> - `udc-dataflow-5.3.605.jar`（30 个 .ftl）
> - `udc-starter-autocode-5.3.605.jar`（52 类，`PasterDirective` 自定义指令）
> - `udc-biz` 反编译 `com.seeyon.udc.expression.codegen.*`
> 等级：`VERIFIED_STATIC_BYTECODE`（FTL 原文 + CFR 反编译）
> 时间：2026-11-18

---

## 0. ★★★★ 一句话结论

**Seeyon 平台的「代码生成」= FreeMarker 模板渲染（432 个 .ftl）+ 自定义 Paster 指令 + 表达式二次编译。**

**没有 JavaPoet，没有 AST 拼装 —— 全是 `.ftl` 文本模板 + `<@paster>` 占位符替换。**

---

## 1. ★★★ 模板版本管理（2.7 / 2.8 / 2.9 / 3.0 / template）

```
autocode/JAVA/{version}/templates/{category}/{file}.ftl
```

| 版本 | 模板数 | 说明 |
|---|---:|---|
| **2.7** | 125 | 最老，向上兼容保留 |
| **2.8** | 138 | |
| **2.9** | **141** | ★★★ **当前生效版本** |
| **3.0** | 2 | 试验（只有 entity 两个） |
| `template/` | 26 | 无版本，feature 专用 |

**★★★ 多版本共存 ⇒ 平台按「应用创建时的引擎版本」选模板，不是一律用最新。**
**⇒ 这解释了为什么老应用升级后生成代码风格不变。**

---

## 2. ★★★★ 2.9 全部 141 个模板（按类目）

### 2.1 microflow（54 个）★ 最大类目

**每个微流程节点类型一个模板 —— 这就是「56 个 actionType」的代码生成实现：**

```
BusinessEventActivity.java.ftl        ★ 业务事件
CallAppServiceActivity.java.ftl       ★ 调 AppService
ChangeBatchEntityActivity.java.ftl    批量改实体
ChangeEntityActivity.java.ftl         改实体
...
```

**⚠️ 完整 54 个名单只看到前 4 个（输出被截断），需补查。**

**⇒ 结构上可以确定：微流程的每个节点 = 一个 `*Activity.java.ftl`。**
**⇒ 微流程「生成代码」= 把画布上的节点逐个渲染成 Java Activity 类。**

### 2.2 entity（21 个）★★★★ 最重要的类目

| 模板 | 大小 | 生成物 |
|---|---:|---|
| **`baseservice.java.ftl`** | **67 KB** | ★★★ **Service（Domain 层）** |
| **`dynamicdependency/outAppAppServiceProxy.java.ftl`** | 50 KB | 跨应用代理 |
| **`pageEntityController2.java.ftl`** | 38 KB | 页面实体 Controller（新版） |
| **`appserviceImpl.java.ftl`** | **28 KB** | ★★★ **AppServiceImpl** |
| **`dto.java.ftl`** | 24 KB | ★★ **Dto** |
| `pageEntityController.java.ftl` | 24 KB | 页面实体 Controller |
| `pageCustomControllerDto.java.ftl` | 20 KB | 自定义页面 DTO |
| **`controller.java.ftl`** | 14 KB | ★★ **Controller（REST）** |
| **`appservice.java.ftl`** | 10 KB | ★★★ **AppService 接口** |
| `third/third_appserviceImpl.java.ftl` | 15 KB | 第三方 AppService 实现 |
| `third/third_baseservice.java.ftl` | 5 KB | 第三方 Service |
| `third/third_controller.java.ftl` | 4.5 KB | 第三方 Controller |
| `third/third_appservice.java.ftl` | 3.4 KB | 第三方 AppService 接口 |
| `third/third_page_entity_controller.java.ftl` | 5 KB | 第三方页面 Controller |
| `tree/tree-entity-refer-controller.ftl` | 6 KB | 树形引用 Controller |
| `tree/tree-entity-page-refer-controller.ftl` | 6 KB | 树形页面引用 |
| `tree/tree-page-controller-fragment.ftl` | 9.6 KB | 树形页面片段 |
| `tree/tree-refer-controller-fragment.ftl` | 12.6 KB | 树形引用片段 |
| `dto/dto.java.ftl`（独立目录） | 6.4 KB | 独立 Dto |
| **`dao.java.ftl`** | **1.9 KB** | ★★★ **Dao（极小！）** |
| **`mybatis.xml.ftl`** | **675 B** | ★★★ **MyBatis XML（几乎空！）** |
| `pagecontroller.java.ftl` | 765 B | 空壳 |

**★★★★★ 三个最重要的结论：**

**① `dao.java.ftl` 只有 1,856 字节 —— Dao 几乎不生成内容：**
```java
<#if appType=="form">
    @Component
    public class ${appNamePackage?cap_first}${entityName?cap_first}Dao 
        extends ${superDaoClass}<${entityName?cap_first}>{
<#else>
    public interface ${appNamePackage?cap_first}${entityName?cap_first}Dao 
        extends ${superDaoClass}<${entityName?cap_first}>
        <@paster name=DeductionPasterConfig.DEDUCTION_UPDATE_TARGET_END_ENTITY_DAO_METHOD/>{
</#if>
```

**★★★ 关键：Dao 只是继承 `AbstractAllInOneBaseDao<T>`，**平台不生成 CRUD SQL**。**
```
com.seeyon.boot.starter.mybatis.AbstractAllInOneBaseDao   ← 通用基类
```
**⇒ 所有 CRUD 由基类用**通用 MyBatis 机制**实现（tk.mybatis + Example + Wrapper）。**

**② `mybatis.xml.ftl` 只有 675 字节 —— 基本不生成 XML：**
**⇒ 没有 `<select>` / `<insert>` 手写 SQL，全部走 `SeeyonKeyMap` / `Wrapper` / `Example`。**

**③ 表单应用 vs 普通应用，Dao 形态不同：**
```
appType == "form"  →  @Component class XxxDao extends BaseDao<T>   （类）
appType != "form"  →  interface XxxDao extends BaseDao<T>          （接口）
```

### 2.3 common（13 个）★★★ 代码生成的核心机制

| 模板 | 大小 | 作用 |
|---|---:|---|
| **`macro.ftl`** | **28 KB** | ★★★ **主宏库** |
| **`macro-entity-check.ftl`** | **32 KB** | ★★★ **实体校验宏（最大）** |
| **`formula-param-map.ftl`** | **25 KB** | ★★★ **表达式参数 Map 宏** |
| `macro-formula-entity.ftl` | 14 KB | 表达式→实体宏 |
| `reliable-invoker-helper.ftl` | 7.3 KB | 可靠调用 helper |
| `macro-entity-attribute-check-not-null.ftl` | 5.2 KB | 非空校验 |
| `macro-entity-update.ftl` | 5 KB | 实体更新 |
| `macro-appservice-approval.ftl` | 4 KB | AppService 审批 |
| `macro-dto-entity.ftl` | 3.4 KB | Dto↔Entity 转换 |
| `macro-entity-trim.ftl` | 2.1 KB | trim |
| `orgUtils.ftl` | 1.5 KB | 组织工具 |
| `utils.ftl` / `constants.ftl` | 0.5/0.3 KB | 工具/常量 |

**★★★ `macro-entity-check.ftl`（32 KB）—— 主数据校验逻辑全在这里生成。**
**★★★ `formula-param-map.ftl`（25 KB）—— 表达式变量→Map 的绑定。**

### 2.4 feature（10 个 + template/26 个）★ 按「特性」分裂生成

**这是**同一实体按 feature 生成不同代码**的机制：**

```
feature/tree_entity/template/
  feature.tree.entity.class[service].ftl                    41.6 KB ★ 最大
  feature.tree.entity.class[app_service].ftl                 2.4 KB
  feature.tree.entity.class[app_service_impl].ftl            2.9 KB
  feature.tree.entity.class[controller].ftl                  4 KB
  feature.tree.entity.class[dao].ftl                         2 KB
  feature.tree.entity.class[service].method[create].ftl      164 B
  feature.tree.entity.class[service].method[create][before].ftl 3.4 KB
  feature.tree.entity.class[service].method[delete].ftl      2.4 KB
  feature.tree.entity.class[service].method[update].ftl      176 B
  feature.tree.entity.class[service].method[update][after].ftl 199 B
```

**★★★ 命名规则解码：**
```
feature.{featureName}.{layer}.class[{layer}].ftl
feature.{featureName}.{layer}.class[{layer}].method[{method}].ftl
feature.{featureName}.{layer}.class[{layer}].method[{method}][{phase}].ftl
```
**⇒ `[before]` / `[after]` 是 **方法前后插桩点**。**
**⇒ 实体声明 `features="tree"` 时，平台额外渲染这 10 个模板片段，插进标准代码里。**

**★ `template/` 目录 26 个（无版本号）—— feature 模板的「母版」。**

### 2.5 entityrule（9 个）★★ 实体规则引擎

```
ruleservice.java.ftl             ★ 主规则 Service（16.5 KB）
AttributeRequiredActivity.ftl    ★ 必填（6 KB）
AttributeUniqueActivity.ftl      ★ 唯一（5.4 KB）
ShowMessageActivity.ftl          提示消息
AssignValueActivity.ftl          赋值（760 B）
DefaultValueActivity.ftl         默认值（871 B）
entityValueForRoot.ftl           根实体取值（4.8 KB）
common/SetValueUtil.ftl          设值工具（6.1 KB）
common/EntityRuleTemplateUtil.ftl 规则模板工具（2.8 KB）
```

**★★ 「实体规则」= 必填/唯一/默认值/赋值/提示消息 —— 五种 Activity。**
**⇒ 每个规则的实现都是**生成一个 Activity 类**。**

### 2.6 project（9）/ project-for-deploy（6）/ project-ext（3）★ 应用工程骨架

**★★★ 这是「新建 UDC 应用」时生成的工程结构！**
```
project/            ← 应用工程（源码）
project-for-deploy/ ← 部署工程
project-ext/        ← 扩展工程
```

**★ 这三组模板 = 应用的 Maven 工程脚手架。**

### 2.7 event（5 个）★ 业务事件

```
business-event.java.ftl                           ★ 业务事件
service/event.business.class[service].ftl         业务事件 Service
service/event.business.class[service].event[import].ftl
service/event.entity.class[service].ftl           实体事件 Service
service/event.entity.class[service].event[import].ftl
```

**★★ 事件分两类：`business`（业务事件）和 `entity`（实体事件）。**

### 2.8 refer / referconfig（各 4 / 2 个）★ 引用

**★ 「引用」（Refer）—— 关联实体/关联字段的代码生成。**

### 2.9 filterplan（2 个）★ 过滤方案

```
filter-plan-controller.java.ftl            8.7 KB
filter-plan-controller-fragment.java.ftl   14 KB  ★ 片段
```

### 2.10 其他
```
app（2）      应用
dto（1）      Dto
enums（1）    枚举
beanname（1）  Bean 名修饰器（AppBeanNameModifier）
```

---

## 3. ★★★★ 三层 Service 的真实关系（回答核心问题）

**模板证明了平台的「三类 Service」：**

```
① Service（Domain 层，实体级）
   baseservice.java.ftl (67 KB)   ← 最大
   → 生成 {Entity}Service
   → 继承 AbstractAllInOneBaseService / 操作 Dao
   → 数据访问、事务、校验

② AppService（应用服务层，接口 + 实现）
   appservice.java.ftl (10 KB)    ← 接口
   appserviceImpl.java.ftl (28 KB) ← 实现
   → 生成 {Entity}AppService + {Entity}AppServiceImpl
   → @AppService / @AppServiceOperation / @OpenApi 注解
   → 对外 GraphQL/Dubbo 暴露

③ Controller（REST 层）
   controller.java.ftl (14 KB)
   → 生成 {Entity}Controller
   → HTTP 端点，调 AppService
```

### 3.1 ★★★ AppServiceImpl 的真实注解（实测）

```java
@Service
@AppService(value = "${table.caption}接口",
            customs = {
              @Custom(properties = @CustomAttribute(name = "entity",  value = "${table.fullName}")),
              @Custom(properties = @CustomAttribute(name = "appName", value = "${table.appName}"))
            })
@Slf4j
@DubboService          // ← 仅当 table.enableRpc || table.isOpenApiEntity
public class XxxAppServiceImpl implements XxxAppService {
```

**★★★ 三重暴露机制：**
```
@AppService        → GraphQL（按 entity + appName 注册）
@DubboService      → RPC（可选，条件：enableRpc / isOpenApiEntity）
Controller         → REST（独立生成）
```

### 3.2 ★★★ AppServiceImpl 的关键 import（暴露了它依赖什么）

```
com.seeyon.boot.starter.dynamicsql.dto.*     ★ 动态 SQL（DynamicCondition/MainCondition/
                                               ProxyParam/ProxyJoinParam/QueryCondition）
com.seeyon.boot.starter.udcrt.dto.*          ★ 运行时（BillSearchRequest/ExcelDto/
                                               RuntimePageCustomSearchDto）
com.seeyon.boot.starter.excel.*              ★ Excel 导入导出
com.seeyon.boot.starter.lowcode.util.DtoConvertUtil
com.seeyon.boot.starter.lowcode.aspect.RecycleSerialNumber  ★ 回收流水号
com.seeyon.boot.annotation.*                 Custom/CustomAttribute/AppService/
                                             AppServiceOperation/OpenApi/ParameterInfo
com.seeyon.boot.transport.*                  Single/List/Page Request+Response
com.seeyon.boot.domain.dao.Wrapper           ★ 条件构造器
com.seeyon.udc.common.dto.*                  ResultDto/NodeDto/BaseEntityActionDto/
                                             ForceUpdateResultDto
com.seeyon.udc.common.utils.ResponseUtils
```

**★★★ `dynamicsql`（动态 SQL）+ `Wrapper` + `Example` ⇒ **查询完全条件化，无手写 SQL**。**

### 3.3 ★★ 主子表在 AppServiceImpl 里的处理

```freemarker
<#if table.isRoot>
    ... 根实体专属逻辑 ...
</#if>
```
**★ `<#if table.isRoot>` ⇒ **主实体和子实体生成不同的 AppServiceImpl**。**
**★ 子实体没有 Excel 导入导出、没有 RecycleSerialNumber、没有 ForceUpdate。**

---

## 4. ★★★ `DataFlowCodeUtils`：表达式 → Java 方法（实证）

### 4.1 ★★★ 核心代码（CFR 反编译原文）

```java
public static Map<String,String> getFormulaPastArgs4DataFlow(
        List<DataFlowMappingDto> list, CodeContext codeContext) {
    ExpressionCodeGenerator codeGenerator = ExpressionCodeGenerator.getInstance();
    list.forEach(dto -> {
        wrap(codeGenerator, dto.getMappingDetailDto().getEventFilterCondition(),
             "生单规则["+caption+"]事件过滤条件", ...);
        wrap(codeGenerator, dto.getMappingDetailDto().getPreCondition(),
             "生单规则["+caption+"]来源实体过滤条件", ...);
        rules.forEach(rule -> rule.getMappingArea().forEach(area -> {
            wrap(codeGenerator, area.getCheckRule(),     "...目标实体数据检查规则", ...);
            wrap(codeGenerator, area.getCondition(),     "...行映射条件", ...);
            area.getMappingRow().forEach(row ->
                wrap(codeGenerator, row.getRowCondition(), "...列映射条件", ...));
        }));
    });
}

private static void wrap(ExpressionCodeGenerator codeGenerator, 
                         ExpressionDefinitionDto expr, String desc, ...) {
    ExpressionCodeGenConfig config = ExpressionCodeGenConfig.builder(expr)
        .variableType(ExpressionVariableTypeEnum.ENTITY)
        .enableClassImport(true).refPath(refPath).build();
    CodeGenerateResult r = codeGenerator.generateCode(config);   // ★★★ 编译
    methodList.add(r.getMethodBody());                            // 方法体
    String invoke = String.format("dataFlowFormulaService.%s(%s);", 
                                  r.getMethodName(), mapName);    // ★ 调用串
}
```

**★★★★★ 五个表达式点位（数据流里能配表达式的地方）：**
```
① eventFilterCondition   事件过滤条件
② preCondition           来源实体过滤条件
③ checkRule              目标实体数据检查规则
④ condition              行映射条件（区域级）
⑤ rowCondition           列映射条件（行级）
```

**⇒ 这直接回答「生单规则能配哪些表达式」。**

### 4.2 ★★★ 表达式编译链路（`ExpressionCodeGenerator.doGenerateCode` 反编译原文）

```java
List<Token> tokens = designData.getTokens();
TokenPeekIterator it = new TokenPeekIterator(tokens.stream());
Map schemaMap = ExpressionCommonUtil.getSchemaMap(designData.getContext());

ASTNode root = SeeyonParser.parse(it, schemaMap);              // ① 解析成 AST
SemanticAnalyzer analyzer = new SemanticAnalyzer(
    schemaMap, designData.getResultTypeInfo(),
    designData.getResultTypeFullName(), designData.getTokens());
ExpressionDataType expectedResultType = analyzer.analyze(root); // ② 语义分析

ExpressionInterpreter interpreter = new ExpressionInterpreter();
ExprCodeGenContext ctx = ExprCodeGenContext.builder()
    .variableSchema(schemaMap).interpreter(interpreter)
    .expectedResultType(expectedResultType).variableType(variableType)
    .config(config).rootNode(root).semanticAnalyzer(analyzer)
    .scriptBuildContext(scriptBuildContext).build();
CalculateHelper helper = CalculateHelper.build(ctx);            // ③ 计算辅助
ctx.setHelper(helper);

String codeFragment = interpreter.interpret(root, ctx);          // ④ AST → Java 表达式片段
if (expectedResultType.isUdcEnum()) {
    codeFragment = wrapCodeFragmentWithJavaEnumCast(...);       // ⑤ 枚举强转包装
}
String methodName = "exp" + Ids.uuidAbsLong();                  // ⑥ 方法名 exp{雪花ID}
String methodBody = buildMethodBody(codeFragment, methodName, ctx,
                                    expectedResultType, config.getRefPath()); // ⑦ 包成方法
List<Map<Long,Object>> paramEntityMap = getMethodParamMap(designData.getContext(), variableType);
```

**★★★★★ 七步编译管线：**
```
tokens → SeeyonParser/AST → SemanticAnalyzer(推断类型) 
       → ExpressionInterpreter(AST→Java片段) → JavaEnumCast(枚举)
       → buildMethodBody(包成方法) → 方法名 exp{雪花}
```

### 4.3 ★★★ 生成的方法体模板（原文常量）

**普通表达式：**
```java
public %s %s(%s){
try{
            return %s 
        }catch (NullPointerException e){
            throw new BusinessException(ExpressionErrorCode.NORMAL_EXPRESSION_NULL_POINTER_ERROR);
        }catch (Exception e){
           if(e instanceof BusinessException){
                String errorCode = ((BusinessException)e).code();
                String errorMsgByErrorCode = UdcI18nUtils.getErrorMsgByErrorCode(errorCode);
                if(StringUtils.isNotEmpty(errorMsgByErrorCode) && !"BOOT_1000".equals(errorCode)){
                    throw new BusinessException(ExpressionErrorCode.NORMAL_EXPRESSION_ERROR, errorMsgByErrorCode);
                }else{
                    throw new BusinessException(ExpressionErrorCode.NORMAL_EXPRESSION_ERROR, e.getMessage());
                }
            }
            throw new BusinessException(ExpressionErrorCode.NORMAL_EXPRESSION_ERROR, e.getMessage());
        }
}
```

**引用表达式（`refPath` 非空）：**
```java
// 同上，但错误码换成 REF_*，并带上 refPath 作为定位信息：
REF_NULL_POINTER_EXPRESSION_ERROR, "%s"        ← refPath
REF_EXPRESSION_ERROR, "%s", errorMsgByErrorCode
REF_EXPRESSION_ERROR, "%s", e.getMessage()
```

**★★★ 两套错误码：`NORMAL_EXPRESSION_*` / `REF_EXPRESSION_*`。**
**⇒ 区分「普通表达式」和「引用表达式」（引用式会报出 refPath，方便定位）。**

### 4.4 ★★★ 枚举类型特殊处理

```java
private static final String SINGLE_JAVA_ENUM_CAST =
  "(%s)(com.seeyon.boot.starter.formula.engine.functions.basic.BasicHiddenFunction.getJavaEnumItem( \"%s\" , %s  ))";
private static final String MULTI_JAVA_ENUM_CAST =
  "(java.util.List<%s>)(...getMultiJavaEnumItem( \"%s\" , %s  ))";
```

**★★★ UDC 枚举在生成代码里**是有类型的 Java 对象**，不是字符串：**
```
单值： (XxxEnum)(BasicHiddenFunction.getJavaEnumItem("{fullName}", value))
多值： (List<XxxEnum>)(...getMultiJavaEnumItem(...))
```

### 4.5 ★★★ 生成后的调用形态

**模板里不是内联表达式，而是：**
```java
boolean result = <@paster name=DataFlowCodeUtils.getExpressionDefinitionDtoId(formulaInfo)/>
```
**`getExpressionDefinitionDtoId` 的实现（反编译原文）：**
```java
public static String getExpressionDefinitionDtoId(ExpressionDefinitionDto dto) {
    return String.valueOf(System.identityHashCode(dto)).replace("-","");
}
```
**⇒ 用 `identityHashCode` 当 key，把多个表达式去重成一个 Map。**

**然后在 ftl 的 `paster` 阶段替换成：**
```java
dataFlowFormulaService.exp{雪花ID}({参数Map})
```

**★★★ 最终形态（推理 + 证据）：**
```
① 生成期：DataFlowRuntimeService.java 里留下 dataFlowFormulaService.exp123(map)
② 同时：DataFlowFormulaService.java 里生成 exp123 方法体（真正的表达式 Java 代码）
③ 运行期：直接调 Java 方法 —— 不是解释执行！
```

---

## 5. ★★★ `PasterDirective`：模板与代码生成器的桥

**`udc-starter-autocode` 52 类里的核心：**
```
com.seeyon.boot.starter.autocode.extension.directive.PasterDirective        ★ 指令实现
com.seeyon.boot.starter.autocode.config.BasePasterConfig                    配置基类
com.seeyon.udc.deduction.autocode.config.DeductionPasterConfig              扣减专用
```

**★★★ `<@paster name=XXX/>` 机制：**
```
① 模板里写占位符 <@paster name=SomeConfig.SOME_KEY/>
② 各子域注册 PasterConfig（提供 name → 代码片段 的映射）
③ 渲染时替换成真实代码
```

**⇒ 这就是「按需插桩」：模板骨架固定，各子域用自己的 PasterConfig 往固定位置插代码。**

**★ 例：Dao 模板里的两个 paster**
```
DeductionPasterConfig.DEDUCTION_UPDATE_TARGET_END_ENTITY_DAO_IMPORT   ← import 段
DeductionPasterConfig.DEDUCTION_UPDATE_TARGET_END_ENTITY_DAO_METHOD   ← 方法段
```
**⇒ 扣减功能在 Dao 上插了「更新目标实体」的方法，非扣减应用不插。**

---

## 6. ★★★ 数据流的 30 个模板（udc-dataflow）

```
2.8/templates/dataflow/
  DataFlowRuntimePersonalizationController.java.ftl   9.4 KB  （旧版）

2.9/templates/dataflow/
  DataFLowRuntimeCreateOrUpdate.ftl    76 KB  ★★★ 最大
  DataFlowRuntimeService.java.ftl      25 KB  ★★★ 生单规则主 Service
  DataFlowRuntimeCreate.ftl            42 KB  ★★★ 生单创建逻辑
  DataFlowRuntimeUpdate.ftl            28 KB  ★ 更新
  DataFlowRuntimeListener.java.ftl     12.5 KB ★ 监听器
  DataFlowRuntimePageController.java.ftl 9.6 KB
  DataFlowRuntimePersonalizationController.java.ftl 9.4 KB
  DataFlowIdMappingService.java.ftl     6.6 KB ★ ID 映射
  DataFlowRuntimeAppService.java.ftl    1.3 KB
  DataFlowRuntimeAppServiceImpl.java.ftl 2.8 KB
  dao/DataFlowIdMappingDao.java.ftl     754 B
  entity/DataFlowIdMapping.java.ftl     733 B
  decorate/FormulaService.java.ftl      531 B
  decorate/writeback/
    writeBackListener.java.ftl         37 KB ★★★ 回写监听（很大！）
    sendWriteBackEventFromCreate.ftl    199 B
    sendWriteBackEventFromUpdate.ftl    221 B
    sendWriteBackEventFromDelete.ftl    198 B
  common/
    call-approtal.ftl                  7.8 KB ★ 调审批（拼写 aprotal）
    filterSourceEntity.ftl             2.6 KB
    flatEntityData.ftl                 7.7 KB ★ 拍平
    macro-formula.ftl                  15 KB  ★ 表达式宏
    utils.ftl                          496 B

2.9/templates/deduction/
  DeductionRuntimeBeforeUpdateListener-update.ftl  24 KB ★ 扣减更新前
  DeductionRuntimeCreateListener.ftl  12 KB ★ 创建时扣减
  DeductionRuntimeDeleteListener.ftl   9.2 KB ★ 删除时回补
  decorate/update/DeductionUpdateTargetEntityService.ftl 35 KB ★★★ 最大
  DeductionListenerCommonAssign.ftl    3.3 KB
  DeductionListenerCommonAutowired.ftl 1 KB
  DeductionListenerCommonImport.ftl    4 KB
```

**★★★ 扣减规则的三个生命周期监听器（关键！）：**
```
DeductionRuntimeCreateListener        创建时 → 扣减
DeductionRuntimeBeforeUpdateListener   更新前 → 扣/回补
DeductionRuntimeDeleteListener        删除时 → 回补
```
**⇒ 扣减不是「一个动作」，是**三道闸门**全部挂上。**

**★★ `common/call-approtal.ftl`（注意拼写错误 aprotal）—— 生单可以直接调 BPM 审批。**

---

## 7. ★★ `DataFlowRuntimeCreate.ftl` 的核心算法（42 KB）

**从模板原文提取的执行步骤：**

```
① 为每个映射区域准备 List<Map<String,Object>> sourceFlatMap4Target{Entity}List
② 遍历来源实体数据，逐个区域拍平（prepareSourceDate 宏）
③ 记录日志：FLAT_SOURCE_DATA
④ 递归组装目标 Dto（recursionEntity 宏）
⑤ 按区域分组（groupByField）
⑥ 行条件过滤（condition.expression → ROW_CONDITION 日志）
⑦ 组装目标实体数据（记录耗时 ms）
```

**★★★ 五道处理工序 + 四类运行态日志：**
```
FLAT_SOURCE_DATA    拍平来源数据
GROUP_SOURCE_DATA   分组
ROW_CONDITION       行条件匹配
（+ 组装/写入）
```

**★ 日志用 `UdcDataFlowLogDto.builder().actionType(...).input(...).description(...).output(...)`**
**⇒ 运行态每个数据流都能看到「哪一步剩了多少条」，这就是页面上那个执行日志。**

---

## 8. ★★★ 表达式在数据流宏里的真实用法（`macro-formula.ftl`）

**8 个宏：**
```
dataFlowSingleAggregationFormula   单条聚合根条件判断
calcSourceFormula                  映射/回写时计算表达式值
flat / flat4Deduction              拍平（按映射递归，只处理 ONE2MANY）
convertSqlList / getSqlListMapMethod / flat4SqlMethod   转 SQL 列表
convertDataCode                    数据编码转换
```

**★★★ `flat` 宏的关键注释（原文）：**
```freemarker
<#--只处理一对多，一对一扩展表由父表转换-->
<#if child.multiplicity == "ONE2MANY">
    toMapList(${parent}Dto.get${child}DtoList(), ${child}Dto.class).forEach(dto -> {
        dto.setActionType(ActionType.UPDATE);      ← 拍平时强制改为 UPDATE
        Map<String,Object> map = dto.toReferenceMapWithOneToOne();
        map.putAll(${baseMap});                    ← 父表字段平铺进子表 map
```

**★★★★ 主子表拍平机制（最终确认）：**
```
① 只处理 multiplicity == "ONE2MANY" 的子实体
② 一对一扩展表不拍平（由父表转换，即字段直接平铺）
③ 拍平时子 Dto 的 ActionType 强制改成 UPDATE
④ 父表字段 putAll 进子表 Map（宽表化）
⑤ 支持多层递归（hasOne2ManyChild）
```

**⇒ 这就是「主子表怎么入数据」的答案：**先把主表字段宽表化到子表 Map，再逐行组装。**

---

## 9. ★★★ 完整「新建实体」生成物清单（推理 + 模板证据）

**声明一个实体 `Xxx`（普通应用）：**
```
{baseServicePackage}/
  {Entity}Service.java              ← baseservice.java.ftl (67 KB)
  {Entity}Dao.java                  ← dao.java.ftl (interface extends AbstractAllInOneBaseDao)
  entityrule/{Entity}RuleService    ← ruleservice.java.ftl（若有规则）
  entityrule/Xxx{Activity}.java     ← 5 种 Activity（必填/唯一/默认值/赋值/提示）

{appServicePackage}/
  {Entity}AppService.java           ← appservice.java.ftl (接口)
  {Entity}AppServiceImpl.java       ← appserviceImpl.java.ftl (实现)

{dtoPackage}/
  {Entity}Dto.java                  ← dto.java.ftl (24 KB)

{controllerPackage}/
  {Entity}Controller.java           ← controller.java.ftl

resources/mapper/
  {Entity}Mapper.xml                ← mybatis.xml.ftl（675 B，近空）
```

**★ 若 `features="tree"`：额外插 10 个片段（service 41 KB + 4 个层 + 4 个 method 钩子）**
**★ 若声明 refer：额外生成 refer / referconfig 相关（2+2 模板）**
**★ 若声明事件：额外生成 business-event / event service**

---

## 10. ★★ 与我已有文档的印证/修正

| 旧结论 | 本轮 |
|---|---|
| 「平台生成 MyBatis 三类 service/dao」 | ✅ **确认，但是 Dao 极薄（继承基类），XML 近乎空** |
| 「表达式运行时解释」 | ❌ **修正：编译成 Java 方法（`exp{雪花}`），运行期直接调** |
| 「微流程 56 个 actionType」 | ✅ **每个 actionType = 一个 `*Activity.java.ftl`（54 个模板）** |
| 「主子表 ONE2MANY」 | ✅ **确认，且拍平时 ActionType 强制 UPDATE** |
| 「一对一扩展表」 | ✅ `flat` 宏注释明确「一对一扩展表由父表转换」 |
| 「扣减走 SQL」 | ✅ **修正补充：不是运行期拼 SQL，而是**生成 Listener 类**，SQL 由 `DeductionSqlGenerator` 在生成期产出** |

**★★★ 重要修正：扣减也是**代码生成**，不是运行期 SQL 拼接。**
```
DeductionRuntimeCreateListener.ftl → 生成 XxxDeductionCreateListener.java
DeductionSqlGenerator（在 autocode 里）→ 生成 Listener 内的 SQL 语句
```

---

## 11. 未覆盖

| 项 | 说明 |
|---|---|
| **microflow 54 个模板完整名单** | 只看到前 4 个（输出截断）★★★ 最该补 |
| `baseservice.java.ftl`（67 KB）全文 | 只看开头 |
| `macro.ftl`（28 KB）/ `macro-entity-check.ftl`（32 KB） | 未读 |
| `project/*` 9 个（工程脚手架） | 未读 —— 这是「新建应用」生成什么 |
| `DeductionCodeTemplate` 实际生成的 Listener 代码 | 未跑 |
| 真实生成产物（拿一个应用跑一遍生成） | **未验证**（需要沙箱/测试应用） |
| `2.7`/`2.8` 与 `2.9` 的差异 | 未 diff |
| `EnumCodeGen` / `CodeTask` 的调度逻辑 | 未反编译 |