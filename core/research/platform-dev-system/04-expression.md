# 专题 4：表达式与运行时体系

> 状态：**研究中（第一轮·静态）** · 未审计
> 平台版本：`udc-platform-5.3.517`
> 最近更新：2026-11-17
> ★ 本轮**找到了运行时主动执行入口**，这是 v4 计划里的核心缺口

---

## 1. 研究目标

分三阶段：**定义与解析** → **代码生成** → **运行时调用**。
重点回答：**业务代码如何主动执行表达式**，与平台自动执行有什么区别。

---

## 2. 三阶段总览（已证）

```
阶段 A：定义与解析（设计态）
  ExpressionSaveDto
    ├─ getTokens(): List<ExpressionToken>       ← token 序列
    ├─ getSchemas(): List<SchemaStructureDto>   ← 变量 schema
    ├─ getResultTypeInfo() / getResultTypeFullName()
    ├─ getTerminalSupportType(): TerminalSupportTypeEnum
    ├─ getIsMultiSelect()
    ├─ getResultRange(): ResultRangeDto
    ├─ getSourceAppName()
    └─ getVersion()
        ↓
  ExpressionAppService#check(ExpressionSaveDto)     ← 校验
  ExpressionAppService#transform(ExpressionSaveDto) ← ★ 编译成 executableExpr

阶段 B：代码生成（生成态）
  ExpressionCodeGenConfig
    ├─ getExpressionDefinitionDto()
    ├─ getVariableType(): ExpressionVariableTypeEnum
    ├─ getParamMapName(): String
    ├─ getDecimalScale(): Integer
    ├─ getUdcEnumFullNameMap()
    ├─ getRefPath()
    └─ getSourceAppName()
        ↓
  ExpressionCodeGenerator#generateCode(config): CodeGenerateResult
        ↓
  CodeGenerateResult
    ├─ getMethodName(): String      ← exp<雪花ID>
    ├─ getMethodBody(): String
    ├─ getCodeFragment(): String
    ├─ getImportClasses(): Set<String>
    └─ getParamEntityMap(): List<Map<Long,Object>>
        ↓
  Expression4EntityUtil（桥接）
    ├─ sortComputeExpression(...)
    ├─ expressionImportPackages(...)
    └─ getValueScopeMethodExpression(...)
        ↓
  注入到实体生成的 Java 代码

阶段 C：运行时执行
  EvalContextDto
    ├─ getExpression(): String              ← executableExpr
    ├─ getExpressionTranslation(): String   ← 中文翻译
    ├─ getResultType(): String              ← 结果类型
    └─ getContextMap(): Map<String,Object>  ← 变量上下文
        ↓
  ExpressionEvaluator#eval(EvalContextDto): Object    ← ★★ 运行时入口
```

---

## 3. 阶段 A：定义与解析

### 3.1 `ExpressionSaveDto`（9 字段）

| getter | 类型 | 说明 |
|---|---|---|
| `getTokens()` | `List<ExpressionToken>` | **token 序列（表达式本体）** |
| `getSchemas()` | `List<SchemaStructureDto>` | **变量 schema（上下文定义）** |
| `getResultTypeInfo()` | `String` | 结果类型（如 `BIGINTEGER`） |
| `getResultTypeFullName()` | `String` | 结果类型全名 |
| `getIsMultiSelect()` | `Boolean` | 是否多选 |
| `getTerminalSupportType()` | `TerminalSupportTypeEnum` | **端支持类型** |
| `getResultRange()` | `ResultRangeDto` | 结果范围 |
| `getSourceAppName()` | `String` | 源应用 |
| `getVersion()` | `String` | 版本 |

**⇒ 设计态表达式的完整输入是「token 序列 + 变量 schema + 结果类型 + 端类型」。**

### 3.2 `ExpressionToken`（最小单元，★ 结构丰富）

**字段（7 个）：**

| getter | 类型 | 说明 |
|---|---|---|
| `getUid()` | `String` | 唯一 ID |
| `getType()` | `String` | token 类型（`SYSTEM` / `FUNCTION` / …） |
| `getValue()` | `String` | 值 |
| `getDesc()` | `String` | 描述 |
| **`getSubOps()`** | **`List<List<ExpressionToken>>`** | **★ 嵌套子表达式** |
| **`getControlData()`** | `ControlData` | **★ 控件数据绑定** |
| **`getIsAggregationProperty()`** | `Boolean` | **★ 聚合属性标记** |

**18 个类型判定方法（`currentIs*`）：**

```
currentIsLogicOperator()          逻辑运算符
currentIsBooleanOperator()        布尔运算符
currentIsLeftBracket() / RightBracket()   括号
currentIsNotOperator()            NOT
currentIsTrueFalseToken()         true/false
currentIsEqToken()                等值
currentIsArithmeticToken()        算术
currentIsVariable()               变量
currentIsConstant()               常量
currentIsFunction()               函数
currentIsSystemVariable()         系统变量
currentIsCallFactor()             调用因子
currentIsSingleEntityConstant()   单实体常量
currentIsMultiEntityConstant()    多实体常量
currentIsSingleCtpEnumConstant()  单 CTP 枚举
currentIsMultiCtpEnumConstant()   多 CTP 枚举
currentIsSingleUdcEnumConstant()  单 UDC 枚举
currentIsMultiUdcEnumConstant()   多 UDC 枚举
```

**★ 另有：`getSystemFunctionName()` / `getUdcEnumFullName()`**

**⇒ token 类型体系覆盖 18 类，其中「单/多」× 「实体/CTP枚举/UDC枚举」= 6 种常量类型。**
**⇒ `subOps` 是 `List<List<Token>>`（二维），说明支持「函数多组参数」或「子表达式列表」。**

**★★ `getIsAggregationProperty()` 是主子表表达式的关键标记。**
**⇒ 聚合属性（子表字段汇总到主表）的表达式 token 会带这个标记。**

### 3.3 `ExpressionAppService`（11 方法，★ 对外 API）

| 方法 | 说明 |
|---|---|
| `check(SingleRequest<ExpressionSaveDto>)` | **校验表达式** |
| **`transform(SingleRequest<ExpressionSaveDto>)`** | **★ 设计态 → 可执行** |
| `getQuickSymbols()` | 快捷符号 |
| `loadSystemPresetVariableByCondition(...)` | 加载系统预置变量 |
| `loadSystemVariable(SingleRequest<String>)` | 加载系统变量 |
| `listSystemVariable()` | 列系统变量 |
| `listSystemVariableByCondition(...)` | 条件列 |
| `selectSchemaByParamType(...)` | 按参数类型选 schema |
| `getSystemVariableResult()` | **取系统变量值（全量）** |
| `getSystemVariableResult(SingleRequest<String>)` | 取指定变量值 |
| `getSystemVariableResultBySystemFunctionName(SingleRequest<String>)` | **按函数名取变量值** |

**⇒ 这是表达式的**服务端 API**，走 `SingleRequest`/`SingleResponse`（标准 AppService 契约）。**

**⇒ `transform` 就是「设计态 → executableExpr」的编译入口。**

---

## 4. 阶段 B：代码生成

### 4.0 ★ 自定义函数注册机制（本轮新增）

来源：`surface-index.tar.gz` → `annotations.md`

**三个函数相关注解（全部 `@Retention(RUNTIME)`）：**

| 注解 | 全限定名 | 元素 | Target | 构件 |
|---|---|---|---|---|
| **`@FunctionClass`** | `com.seeyon.boot.starter.formula.engine.annotation.FunctionClass` | **0** | **TYPE** | `boot-formula-engine-5.3.603.jar` |
| **`@Function`** | `com.seeyon.boot.starter.formula.engine.annotation.Function` | **7** | **METHOD** | `boot-formula-engine-5.3.603.jar` |
| `@FunctionSupporter` | `com.seeyon.boot.starter.formula.init.FunctionSupporter` | 1 | TYPE | `boot-starter-formula-5.3.603.jar` |
| `@ReturnValue` | `com.seeyon.boot.starter.formula.engine.annotation.ReturnValue` | 4 | METHOD | `boot-formula-engine` |
| `@Parameter` | `com.seeyon.boot.starter.formula.engine.annotation.Parameter` | 3 | — | `boot-formula-engine` |
| `@ParameterInfo` | `com.seeyon.boot.annotation.ParameterInfo` | 3 | PARAMETER | `boot-core` |

**⇒ 自定义表达式函数的注册姿势（推断）：**

```java
@FunctionClass                        // 贴在类上，标记"这是函数集合"
public class MyCustomFunctions {

    @Function(name = "...", ...)      // 贴在方法上，7 个参数
    public static Object myFunc(
        @Parameter(...) Object arg1,  // 3 个参数
        @Parameter(...) Object arg2
    ) { ... }

    // @ReturnValue(4 元素) 声明返回值类型
}
```

**⚠️ 这是从注解 `@Target` 推断的用法，7 个元素的具体名称未提取。标 `UNVERIFIED`。**

**⇒ 与 `FunctionInterpreterFactory#getAnalyzerInstance(String)` 的对应关系：**
- `@Function(name=...)` 的 name 很可能就是 `getAnalyzerInstance(String)` 的 key
- **待证。**

**⇒ 这也解释了「88 函数清单」为什么不在 `formula-functions.xml`：**
**函数是通过注解注册的，不在 XML 里。**
**⇒ 要拿到真实清单，需要扫描所有标了 `@Function` 的方法（当前签名库不含注解实例数据）。**

**证据等级：** `STATIC_RULE`（注解存在与 Target）
**⚠️ 未证：** 元素名、实际注册流程、与 `getAnalyzerInstance` 的 key 映射

### 4.1 `ExpressionCodeGenConfig`（9 字段）

| getter | 说明 |
|---|---|
| `getExpressionDefinitionDto()` | 表达式定义 |
| `getVariableType()` | `ExpressionVariableTypeEnum` |
| `getParamMapName()` | 参数 Map 名 |
| `getDecimalScale()` | 小数精度 |
| `isCustomDecimalPlace()` | 自定义小数位 |
| `getUdcEnumFullNameMap()` | UDC 枚举全名映射 |
| `getRefPath()` | 引用路径 |
| `getSourceAppName()` | 源应用 |
| `isEnableClassImport()` | 是否允许 import |

### 4.2 `ExpressionCodeGenerator`（10 方法）

```java
getInstance(): ExpressionCodeGenerator                    ← 单例
generateCode(ExpressionCodeGenConfig): CodeGenerateResult ← ★ 主入口
doGenerateCode(ExpressionCodeGenConfig): CodeGenerateResult
getScriptBuildContext(ExpressionDesignDataDto, ...)
buildMethodBody(String, String, ExprCodeGenContext)
buildCodeFragment(ExprCodeGenContext, String)
buildReturnFragment(...)
buildCustomDecimalScaleFragment(String, Integer)
getMethodParamMap(List<SchemaStructureDto>)
getEntityMethodParamMap(List<SchemaStructureDto>)
resolveImports(Set<String>): Set<String>
```

**⇒ `buildMethodBody` / `buildCodeFragment` / `buildReturnFragment` 说明产出是「Java 方法体 + 代码片段 + return 片段」。**

### 4.3 `CodeGenerateResult`（5 字段）

| getter | 类型 | 说明 |
|---|---|---|
| `getMethodName()` | `String` | **★ 方法名（`exp<雪花ID>`）** |
| `getMethodBody()` | `String` | **★ 方法体** |
| `getCodeFragment()` | `String` | **★ 代码片段** |
| `getImportClasses()` | `Set<String>` | **★ 需要的 import** |
| `getParamEntityMap()` | `List<Map<Long,Object>>` | 参数实体映射 |

**⇒ `exp<雪花ID>` 的命名来源就在 `getMethodName()`（具体生成算法需反编译）。**

### 4.4 解释器体系（AST → 代码）

```java
com.seeyon.udc.expression.codegen.interpreter.Interpreter     ← 接口
  # interpret(ASTNode, ExprCodeGenContext): String
  # getBinaryOp(ExpressionToken): ...
  # getUnaryOp(ExpressionToken): ...
  # isMultiCtpEnumAssign(ASTNode, ...): boolean
```

**9 个实现：**

```
BinaryInterpreter               二元运算
UnaryInterpreter                一元运算
ScalarInterpreter               标量（含 escapeString / hashEscapeCharacter）
VariableInterpreter             变量（含 isApplicationSystemParam）
EntityVariableInterpreter       实体变量
MicroFlowVariableInterpreter    微流程变量
SystemInterpreter               系统变量（getSystemVariableFunctionName）
FunctionInterpreter             函数（★ 最复杂）
ExpressionInterpreter           表达式根
```

**`FunctionInterpreter` 的方法（最丰富）：**
```
interpret(ASTNode, ExprCodeGenContext)
buildDefaultNullValueFunction(...)
getFunctionBegin(FunctionCall, ...)
getNormalParams(...)
getNormalAggFunctionParams(...)      ← 聚合函数
getListMatchParams(...)              ← 列表匹配
getConditionAggParams(...)           ← 条件聚合
getExpressionSaveDto(...)
isEnumConstantOrVariableNode(...)
```

**★ 7 个具体函数解释器：**
```
AbsFunctionInterpreter
ConditionEarliestOrLatestOrMaxOrMinFunctionInterpreter
CtpEnumItemFunctionInterpreter
EarliestOrLatestFunctionInterpreter
GetListIndexFunctionInterpreter
IfsFunctionInterpreter
ListUniqueFunctionInterpreter
SumIfFunctionInterpreter
SumMaxMinFunctionInterpreter
```

**`FunctionInterpreterFactory`：**
```
getAnalyzerInstance(String): ExtensionFunctionInterpreter
init(): void
```

**⇒ 函数解释器是**工厂 + 扩展点**模式，支持自定义函数（`ExtensionFunctionInterpreter` 是接口）。**

### 4.5 模板类（生成代码的字符串模板）

```
com.seeyon.udc.expression.codegen.common.Template          ← 接口（37 个方法）
com.seeyon.udc.expression.codegen.common.ExprCodeGenTemplate      ← 实现
com.seeyon.udc.expression.codegen.common.ExprCodeGenFullNameTemplate  ← 实现（全名版）
```

**37 个模板方法（部分）：**
```
valueOpValue / stringOpNumber / numberOpString / longResult
numberOpDecimal / decimalOpNumber / decimalOpDecimal
andOrOp / newInteger / newLong / newDecimal / newString
unaryOpExpr / numberToDecimalOpExpr / typeCastExpr
sumParams / listMatchFunctionParams / listConditionAggFunctionParams
variableExtractParams / variableExtractParamsWithoutTypeConvert
dataI18nVariableExtractParams / multiDataVariableExtractParams
decimalDividePrecision / decimalMultiplyPrecision
basicHiddenFunction / standardMethodParam / formulaResultTypeUtil
buildJavaEnum / getDtoFromContextMap / emptyList
buildMultiControlData / buildDefaultValueNullFunction
buildAppSystemParam / systemVariableCall / ternaryOperation
singleCtpEnumIdTransform / multiCtpEnumIdTransform / buildMultiCtpEnumAssign
```

**⇒ 每个模板方法对应一类代码生成场景（如 `stringOpNumber` = 字符串与数字运算）。**
**⇒ `basicHiddenFunction` 暗示有「隐藏函数」机制。**

### 4.6 `Expression4EntityUtil`（★ 表达式 → 实体的桥）

```java
com.seeyon.udc.utils.Expression4EntityUtil
  # parseExpressionToken(List<AttributeDto>, Function<...>)          ← 解析 token
  # sortComputeExpression(LinkedHashMap<String, CodeGenerateResult>) ← ★ 依赖排序
  # expressionImportPackages(LinkedHashMap<String, CodeGenerateResult>) ← 汇总 import
  # defaultValueIsChangeAttributeDtoList(EntityDto): List<String>    ← ★ 默认值变更字段
  # filterEntityDtoWithComputeAttributeDto(EntityDto): List<AttributeDto>  ← 筛选计算字段
  # filterComputeAttributeDto(List<AttributeDto>): List<AttributeDto>
  # resolveAggInfiniteLoop(EntityDto): void                          ← ★ 聚合死循环保护
  # getValueScopeMethodExpression(EntityDto, String, ApplicationDto) ← 值域表达式
  # checkSystemVariable(AttributeDto): void
  # resolveExpressionParam(List<AttributeDto>, Map<String, Hutool...>)
  # getSubEntityTokenValue(ExpressionToken, List<...>)
```

**★★ 三个关键方法：**

1. **`sortComputeExpression(LinkedHashMap<String, CodeGenerateResult>)`**
   ⇒ **表达式之间有依赖，需要拓扑排序**（A 依赖 B，B 先算）
   ⇒ 这解释了「计算字段引用另一个计算字段」的处理

2. **`resolveAggInfiniteLoop(EntityDto)`**
   ⇒ **聚合（主子表）表达式可能死循环，平台有保护**
   ⇒ 典型场景：子表汇总到主表，主表又影响子表

3. **`defaultValueIsChangeAttributeDtoList(EntityDto): List<String>`**
   ⇒ **找出「默认值会变化」的字段**
   ⇒ **极可能与 `copyNeedResetNull` 相关**（需重置为 null 才能重算默认值）
   ⇒ **⚠️ 但 `copyNeedResetNull` 零调用者，关联未证**

### 4.7 `ExpressionVariableTypeEnum` 与端类型

```java
ExpressionCodeGenConfig#getVariableType(): ExpressionVariableTypeEnum
ExpressionSaveDto#getTerminalSupportType(): TerminalSupportTypeEnum
```

**⇒ 表达式区分「变量类型」和「端支持类型」（BACKEND / FRONTEND）。**
**⇒ 样本中 `terminalType: "BACKEND"` 证实。**

---

## 5. 阶段 C：运行时执行（★ 核心突破）

### 5.1 执行入口

```java
com.seeyon.boot.starter.formula.ExpressionEvaluator
  # eval(com.seeyon.boot.starter.formula.dto.runtime.EvalContextDto): java.lang.Object
```

**⇒ 这是**唯一**的运行时执行入口，参数只有 4 样东西。**

### 5.2 `EvalContextDto`（4 字段）

| getter | 类型 | 说明 |
|---|---|---|
| `getExpression()` | `String` | **可执行表达式（executableExpr）** |
| `getExpressionTranslation()` | `String` | 中文翻译（用于日志/报错） |
| `getResultType()` | `String` | 结果类型（如 `BIGINTEGER`） |
| **`getContextMap()`** | **`Map<String,Object>`** | **★ 变量上下文** |

**⇒ 业务代码主动执行表达式的完整姿势（推断，待实测）：**

```java
EvalContextDto ctx = new EvalContextDto();
ctx.setExpression(attrDto.getExpressionRuntimeData());   // 运行态数据
ctx.setResultType("BIGINTEGER");
ctx.setContextMap(vars);                                  // 变量 Map
Object result = expressionEvaluator.eval(ctx);
```

**证据等级：** `VERIFIED_STATIC_BYTECODE`（签名）
**⚠️ 未证：** 异常行为、上下文 Map 的键名约定、是否需 Spring 注入

### 5.3 两条执行路径对比

| 维度 | 路径 A：平台自动 | 路径 B：业务主动 |
|---|---|---|
| 触发点 | `preCreateBatch` / 实体 CRUD | 业务代码显式调用 |
| 入口 | 生成的 `executeExpression<实体>` | `ExpressionEvaluator#eval` |
| 表达式来源 | 实体的 `AttributeDto.getExpressionRuntimeData()` | 调用方提供 |
| 上下文 | 平台自动构建（实体 + 系统变量） | 调用方提供 `contextMap` |
| 结果处理 | 自动 set 到 DTO 字段 | 调用方处理 |
| 事务关系 | 在写入事务内 | 取决于调用位置 |
| 证据等级 | 部分 `LIVE_RULE`（历史实测） | `VERIFIED`（签名） |

**⇒ 核心区别：路径 A 是「声明式」（配了表达式就自动算），路径 B 是「命令式」（代码里显式调）。**

---

## 6. 实际样本（executableExpr 格式）

来源：`udc-expression-samples.json`（25 个样本，21 个含 designData）

**样本 1：系统变量**
```json
{
  "title": "{登录人员ID}",
  "designData": {
    "expressionTranslation": "登录人员ID ",
    "resultTypeInfo": "BIGINTEGER",
    "terminalType": "BACKEND",
    "tokens": [{"type": "SYSTEM", "value": "system.currentUserId"}]
  },
  "executableExpr": "93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=currentUserId%28%29"
}
```

**样本 2：函数**
```json
{
  "title": "{唯一标识()}",
  "tokens": [{"type": "FUNCTION", "value": "uniqueMark"}],
  "executableExpr": "93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=uniqueMark%28%29"
}
```

**样本 3：微流程变量（带上下文）**
```json
{
  "title": "{微流程.自定义服务(1).ty [人员信息].编号}",
  "designData": {"context": [{"name": "_CALL_APP_SERVICE_39mTFV", ...}]},
  "executableExpr": "_CALL_APP_SERVICE_39mTFV._CALL_APP_SERVICE_39mTFV.code"
}
```

**⇒ 关键观察：**

1. **`executableExpr` 有两种形态：**
   - **带前缀**：`<base64-ish 前缀>=<URL编码表达式>`
   - **纯路径**：`_CALL_APP_SERVICE_39mTFV._CALL_APP_SERVICE_39mTFV.code`

2. **前缀 `93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=` 在多个样本中相同**
   ⇒ 可能是应用级密钥或加密盐（`=` 结尾像 base64）
   ⇒ **⚠️ 不得断言是加密。可能是版本标记或签名。标记 `UNVERIFIED`。**

3. **URL 编码**：`%28` = `(`，`%29` = `)`
   ⇒ 说明 executableExpr 会经过 URL 传输

4. **token type 实测值**：`SYSTEM` / `FUNCTION`
   ⇒ 与 `ExpressionToken.currentIsSystemVariable()` / `currentIsFunction()` 对应

---

## 7. 表达式与实体写入的关系

### 7.1 已证部分

```java
AttributeDto
  # getExpressionDesignData(): String            ← 设计态
  # getExpressionRuntimeData(): String           ← 运行态
  # getDefaultValueExpressionDesignData(): String
  # getDefaultValueExpressionRuntimeData(): String
  # getDefaultValueIsChange(): Boolean           ← 默认值是否变化
  # getValueScopeExpression()                    ← 值域表达式
  # getCalculate()                               ← 计算标记
```

**⇒ 字段级表达式有 4 份数据：普通表达式的设计态/运行态 + 默认值表达式的设计态/运行态。**

### 7.2 触发时机（部分已证）

```java
EntityDto
  # getHasValidateRule(): Boolean
  # getHasAssignValueRule(): Boolean
  # getHasDefaultValueRule(): Boolean
  # getHasDefaultValueSystemVariable(): Boolean
```

**⇒ 三类规则：校验 / 赋值 / 默认值。**

**生成侧：**
```
resources/entityrule/DefaultValueActivity.ftl      默认值
resources/entityrule/AssignValueActivity.ftl       赋值
resources/entityrule/AttributeRequiredActivity.ftl 必填
resources/entityrule/AttributeUniqueActivity.ftl   唯一
resources/entityrule/ShowMessageActivity.ftl       提示
```

**⇒ 5 个 Activity 模板对应 5 类规则。**

### 7.3 未证部分（关键）

| 问题 | 状态 |
|---|---|
| 哪些实体方法会调用生成的 `exp*` 方法 | `BLOCKED` |
| 创建/更新/查询是否都触发 | `BLOCKED` |
| 传入值 vs 表达式值冲突时谁赢 | `BLOCKED`（`requireNull` 参数是线索） |
| 表达式异常是否中断事务 | `BLOCKED` |
| 主子表是否重复执行 | `BLOCKED`（`resolveAggInfiniteLoop` 是线索） |

---

## 8. `requireNull` 与 `copyNeedResetNull`（★ 专项澄清）

### 8.1 已知事实

**`requireNull` 参数（来自 `executeExpression*` 调用）：**
```java
executeExpression<实体名>(list, requireNull, getter, expFn, setter, null)
```
- `requireNull = true` → 只在字段为 null 时填
- `requireNull = false` → **无条件覆盖**（历史实测 `LIVE_RULE`）

**`copyNeedResetNull(AttributeDto): boolean`：**
- 声明在 `EntityFileTemplate`
- **全签名库零调用者**

**`getDefaultValueIsChange(): Boolean`：**
- 声明在 `AttributeDto`
- 语义「默认值是否变更」

**`defaultValueIsChangeAttributeDtoList(EntityDto): List<String>`：**
- 声明在 `Expression4EntityUtil`
- 找出默认值会变的字段

### 8.2 三者关系（⚠️ 全部为假设，不得作为结论）

```
假设链：
getDefaultValueIsChange() 标记字段默认值会变
  → defaultValueIsChangeAttributeDtoList() 收集这些字段
  → copyNeedResetNull() 判断某字段是否需要「重置为 null 再算」
  → requireNull 参数决定生成代码里是否覆盖
```

**⇒ 这条链**看起来**自洽，但每一环都缺证据：**
1. `getDefaultValueIsChange` 的赋值处未见
2. `defaultValueIsChangeAttributeDtoList` 的调用方未见
3. `copyNeedResetNull` **零调用者**
4. `requireNull` 的实际生成逻辑未见

**⇒ 结论：`UNVERIFIED`。**
**⇒ 必须满足以下全部条件才能下结论：**
- [ ] 反编译 `EntityFileTemplate#copyNeedResetNull` 方法体
- [ ] 反编译 `Expression4EntityUtil#defaultValueIsChangeAttributeDtoList`
- [ ] 找到 `copyNeedResetNull` 的调用方（可能在模板里，不在 Java 签名库）
- [ ] 实测：设默认值表达式 + 传非空值，看结果

**★ 特别注意：`copyNeedResetNull` 零调用者，可能是「模板里调用」——**
**Freemarker 模板可以直接调 Java 方法，这类调用不会出现在 Java 签名库！**
**⇒ 这解释了为什么零调用者，也说明「必须看 .ftl」才能闭环。**

---

## 9. 修正的旧结论

| # | 旧结论 | 修正 |
|---|---|---|
| 1 | `formula-functions.xml` 是 88 函数注册表 | **只有 584 字节、2 个函数（`memberBelongsTo` / `unitBelongsTo`），是帮助提示文件** |
| 2 | 「runtime 主动执行入口未知」 | **已找到：`ExpressionEvaluator#eval(EvalContextDto)`** |
| 3 | 表达式只是运行时解释 | **有完整的「编译成 Java 方法」子系统**（`ExpressionCodeGenerator`） |
| 4 | `copyNeedResetNull` 零调用者 = 死代码 | **可能在 Freemarker 模板中调用，Java 签名库看不到** |

---

## 10. 证据清单

| # | 结论 | 等级 | 来源 |
|---|---|---|---|
| 1 | 表达式三阶段：定义→生成→运行 | `VERIFIED` | 签名综合 |
| 2 | `ExpressionSaveDto` 9 字段（token + schema + 类型） | `VERIFIED` | 签名 |
| 3 | `ExpressionToken` 7 字段 + 18 个类型判定 | `VERIFIED` | 签名 |
| 4 | token 支持嵌套（`subOps` 二维） | `VERIFIED` | 签名 |
| 5 | token 有聚合标记（`isAggregationProperty`） | `VERIFIED` | 签名 |
| 6 | `ExpressionAppService#transform` 是编译入口 | `VERIFIED` | 签名 |
| 7 | `ExpressionCodeGenerator#generateCode` 产出方法名+方法体 | `VERIFIED` | 签名 |
| 8 | `CodeGenerateResult` 5 字段 | `VERIFIED` | 签名 |
| 9 | 9 个 Interpreter 实现 | `VERIFIED` | 签名 |
| 10 | 函数解释器工厂 + 扩展点 | `VERIFIED` | 签名 |
| 11 | 37 个代码模板方法 | `VERIFIED` | 签名 |
| 12 | `Expression4EntityUtil` 依赖排序 | `VERIFIED` | 签名 |
| 13 | `resolveAggInfiniteLoop` 聚合死循环保护 | `VERIFIED` | 签名 |
| 14 | **`ExpressionEvaluator#eval(EvalContextDto)` 运行时入口** | `VERIFIED` | 签名 |
| 15 | `EvalContextDto` 仅 4 字段 | `VERIFIED` | 签名 |
| 16 | executableExpr 两种形态（带前缀 / 纯路径） | `STATIC` | 样本 |
| 17 | 5 个 entityrule Activity 模板 | `STATIC` | 清单 |
| 18 | `formula-functions.xml` 只是帮助文件 | `STATIC` | 逐字解析 |
| 19 | requireNull 语义 | `LIVE` | 历史实测 |
| 20 | copyNeedResetNull 用途 | **UNVERIFIED** | — |

---

## 11. 未解决问题

| # | 问题 | 严重度 | 阻塞 |
|---|---|---|---|
| 1 | `exp<雪花ID>` 的 ID 生成算法 | 中 | 需反编译 |
| 2 | executableExpr 前缀的语义 | 中 | 需反编译/实测 |
| 3 | 哪些实体方法调用 `exp*` | **高** | 需产物 |
| 4 | 传入值 vs 表达式值冲突规则 | **高** | 需实测 |
| 5 | 表达式异常是否中断事务 | **高** | 需实测 |
| 6 | `copyNeedResetNull` 是否在 .ftl 中调用 | **高** | 需 .ftl |
| 7 | 上下文 Map 的键名约定 | 中 | 需实测 |
| 8 | 自定义函数如何注册 | 中 | 需反编译 `FunctionInterpreterFactory#init` |
| 9 | 88 函数的真实清单 | 中 | 不在 formula-functions.xml |

---

## 12. 下一轮任务

1. **`ExpressionAppService` 的 REST 路径**（从 controller 契约反查）
2. **88 函数真实来源**（查 `FunctionConstant` / 前端资源 / `udc-expression-schema-full.json`）
3. **`EvalContextDto` 的 contextMap 键名**（从 `getSystemVariableResult` 反推）
4. 转专题 5：接口调用体系

---

## ★★★ A. 机制修正：表达式是代码生成（2026-11-17，源码级）

**完整内容见：`04A-expression-mechanism-CORRECTION.md`**

### A.1 核心结论

**表达式不是运行时解释求值，是 AST → Java 源码字符串 → 编译部署 → 方法调用。**

**决定性证据：**
```java
public interface Interpreter {
    String interpret(ASTNode astNode, ExprCodeGenContext context);   // ← 返回 String
}
```

**如果是运行时求值，返回值应该是计算结果，不是字符串。**

### A.2 生成的代码长什么样

```java
import java.math.BigDecimal;
import java.math.RoundingMode;
import com.seeyon.boot.starter.formula.utils.SymbolicOperationHelper;
```

**⇒ 证据：`context.getImportClasses().add(DECIMAL_IMPORT_SET)` —— 只有生成源码才需要收集 import。**

### A.3 6 种 AST 节点 / 13 个运算符

```
节点：BINARY_EXPR / UNARY_EXPR / CALL_EXPR / VARIABLE / SCALAR / SYSTEM

运算符：+ - * / % == != > < >= <= & | ! 
⚠️ 逻辑运算符是单字符 & 和 |，不是 && ||
```

### A.4 10 个内置函数族

```
ABS / IFS / SUMIF / SUM / MAX / MIN
EARLIEST / LATEST / LIST_UNIQUE / GET_LIST_INDEX / CTP_ENUM_ITEM
ExtensionFunctionInterpreter  ← ★ 自定义扩展入口
```

### A.5 5 种变量来源

```
VariableInterpreter            普通变量
EntityVariableInterpreter      实体字段
MicroFlowVariableInterpreter   微流程变量
SystemInterpreter              系统变量
ScalarInterpreter              标量常量
```

### A.6 ★ 修正：`getDefaultValue()` 不是表达式入口

```java
public D getCascadeDefaultValue(String key) {
    BaseEntityActionDto dto = this.getDefaultValue();       // 返回空 DTO 骨架
    this.recursiveDefaultValue(this.entityMeta, dto);       // 递归给子表建空行
    return (D) dto;
}
```

**⇒ 它只负责**新建表单时给子表一条空行**，不计算任何值。**
**⇒ 之前把 `getDefaultValue()` 当表达式接入点是错的，已修正。**

### A.7 完整链路

```
设计态表达式 → AST → SemanticAnalyzer 类型推导
    → ExpressionInterpreter 遍历（返回 Java 源码片段 + 收集 import）
    → 拼装 exec<雪花ID> 方法
    → 注入生成的 Entity/Service
    → 编译进动态 jar
    → 运行时直接方法调用（无解释开销）
    → 内部用 BigDecimal + SymbolicOperationHelper
```
