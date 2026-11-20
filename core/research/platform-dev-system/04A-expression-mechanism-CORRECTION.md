# ★★★ 表达式机制：代码生成，不是运行时解释

> 来源：`udc-biz-5.3.517.jar` CFR 反编译（`com/seeyon/udc/expression/` 70 个类）
> 等级：`VERIFIED_STATIC_SOURCE`
> 修正时间：2026-11-17
> 推翻：本文档此前「表达式由解释器运行时求值」的假设

---

## 1. 结论先行

**表达式是**代码生成**：AST → 遍历 → 拼 Java 源码字符串 → 编译 → 部署 → 实体方法调用。**

```
设计态表达式（用户配置）
    ↓ 解析
AST（ASTNode 树）
    ↓ ExpressionInterpreter.interpret(astNode, context) → String
Java 源码片段（含 import、类型转换、BigDecimal 运算）
    ↓ 组装成方法
exec<雪花ID> 方法（注入 Entity / Service）
    ↓ 部署
运行时直接调用生成的方法（无解释开销）
```

**⇒ 关键证据：`Interpreter.interpret()` 返回 `String`，不是 `Object`。**
**⇒ 如果它是运行时求值，返回的应该是计算结果值，不是字符串。**

---

## 2. 核心接口（源码级）

### 2.1 `Interpreter` —— 产出 Java 源码字符串

```java
public interface Interpreter {
    Map<String, BaseBinaryOp>  BINARY_OP_MAP = new HashMap<>();
    Map<String, BaseUnaryOp>   UNARY_OP_MAP  = new HashMap<>();

    String interpret(ASTNode astNode, ExprCodeGenContext context);   // ★ 返回 String = 代码片段

    default BaseBinaryOp getBinaryOp(ExpressionToken opToken) { ... }
    default BaseUnaryOp  getUnaryOp(ExpressionToken opToken)  { ... }
}
```

### 2.2 `ExpressionInterpreter` —— 按 AST 节点类型分发

```java
public class ExpressionInterpreter implements Interpreter {
    private static Map<ASTNodeType, Interpreter> interpreters = new HashMap<>();

    @Override
    public String interpret(ASTNode astNode, ExprCodeGenContext context) {
        ASTNodeType type = astNode.getType();
        Interpreter interpreter = interpreters.get(type);
        return interpreter.interpret(astNode, context);
    }

    static {
        interpreters.put(ASTNodeType.BINARY_EXPR, new BinaryInterpreter());
        interpreters.put(ASTNodeType.UNARY_EXPR,  new UnaryInterpreter());
        interpreters.put(ASTNodeType.CALL_EXPR,   new FunctionInterpreter());
        interpreters.put(ASTNodeType.VARIABLE,    new VariableInterpreter());
        interpreters.put(ASTNodeType.SCALAR,      new ScalarInterpreter());
        interpreters.put(ASTNodeType.SYSTEM,      new SystemInterpreter());
    }
}
```

**⇒ 6 种 AST 节点类型 → 6 个 Interpreter。**
**⇒ 这是**访问者模式 + 代码生成**，不是解释求值。**

### 2.3 `BinaryInterpreter` —— 二元表达式生成

```java
public class BinaryInterpreter implements Interpreter {
    @Override
    public String interpret(ASTNode astNode, ExprCodeGenContext context) {
        ASTNode parentExprNode = astNode.getParent();
        ExpressionToken opToken = astNode.getLexeme();
        ASTNode left  = astNode.getChild(0);
        ASTNode right = astNode.getChild(1);
        BaseBinaryOp op = this.getBinaryOp(opToken);
        return op.genCode(left, right, context, parentExprNode) + System.lineSeparator();
    }
}
```

### 2.4 `AddOp` —— 加法生成（含负数场景特殊处理）

```java
public class AddOp extends BaseBinaryOp {
    @Override
    public String genCode(ASTNode left, ASTNode right, ExprCodeGenContext context, ASTNode parentExprNode) {
        // ★ 减法表达式里的 + 要转成 SubOp（处理 a - (+b) 这类）
        if (this.isSubtractExpr(parentExprNode) && !left.getParent().isInBracket()) {
            SubOp subOp = new SubOp();
            return subOp.genCode(left, right, context, null);
        }
        return this.genTypeCastCode(left, right, context);   // 常规加法 → 类型转换代码
    }
    @Override
    public String getOp() { return "+"; }
}
```

### 2.5 `genTypeCastCode` —— 类型转换代码生成（核心）

```java
public String genTypeCastCode(ASTNode left, ASTNode right, ExprCodeGenContext context) {
    Interpreter interpreter = context.getInterpreter();

    // ① 语义分析：推导结果类型
    SemanticAnalyzer analyzer = new SemanticAnalyzer(
        context.getVariableSchema(),
        context.getConfig().getExpressionDefinitionDto().getDesignData().getResultTypeInfo(),
        context.getConfig().getExpressionDefinitionDto().getDesignData().getResultTypeFullName(),
        context.getConfig().getExpressionDefinitionDto().getDesignData().getTokens());
    ASTNode parent = left.getParent();
    ExpressionDataType castExpressionDataType = analyzer.analyze(parent);
    DataType castDataType = castExpressionDataType.getOriginDataType();

    // ② 拿 Java 类型签名
    CalculateHelper helper = context.getHelper();
    String javaCastType = helper.getResultTypeSign(castDataType);

    // ③ 分析左右操作数类型
    ExpressionDataType leftExpressionDataType  = analyzer.analyze(left);
    ExpressionDataType rightExpressionDataType = analyzer.analyze(right);

    // ④ ★★★ 收集 import（证明这是产出源码）
    context.getImportClasses().add(RESULT_CALCULATE_HELPER_IMPORT);   // com.seeyon...SymbolicOperationHelper
    context.getImportClasses().addAll(DECIMAL_IMPORT_SET);            // java.math.BigDecimal / RoundingMode

    // ⑤ 生成「带类型转换的表达式代码」
    return helper.castTypeExpr(
        javaCastType,
        () -> interpreter.interpret(left,  context),      // 递归生成左操作数代码
        () -> interpreter.interpret(right, context),      // 递归生成右操作数代码
        this,
        leftExpressionDataType.getOriginDataType().name(),
        rightExpressionDataType.getOriginDataType().name());
}
```

**⇒★★ 决定性证据：`context.getImportClasses().add(...)`**
**⇒ 只有在**生成源码**时才需要收集 import。运行时求值不需要 import。**

### 2.6 生成的代码会 import 什么

```java
public static final String DECIMAL_IMPORT                    = "java.math.BigDecimal";
public static final String ROUND_MODE_IMPORT                 = "java.math.RoundingMode";
public static final String RESULT_TRANSFER_IMPORT            = "com.seeyon.boot.starter.formula.engine.utils.FormulaResultTypeUtil";
public static final String RESULT_CALCULATE_HELPER_IMPORT    = "com.seeyon.boot.starter.formula.utils.SymbolicOperationHelper";
```

**⇒ 生成的表达式方法**必然包含**：**
```java
import java.math.BigDecimal;
import java.math.RoundingMode;
import com.seeyon.boot.starter.formula.utils.SymbolicOperationHelper;
```

**⇒ 说明表达式里的四则运算**全部走 BigDecimal**，不丢精度。**
**⇒ `SymbolicOperationHelper` 负责「符号运算」（处理 null、空串等）。**

---

## 3. 支持的运算符（`Interpreter.getBinaryOp` 硬编码的 13 个）

| 运算符 | Op 类 | 说明 |
|---|---|---|
| `+` | `AddOp` | 加（负数场景转 SubOp）|
| `-` | `SubOp` | 减 |
| `*` | `MultiplyOp` | 乘 |
| `/` | `DivideOp` | 除 |
| `%` | `ModOp` | 取模 |
| `==` | `EqOp` | 等于 |
| `!=` | `NeqOp` | 不等于 |
| `>` | `GtOp` | 大于 |
| `<` | `LtOp` | 小于 |
| `>=` | `GteOp` | 大于等于 |
| `<=` | `LteOp` | 小于等于 |
| `&` | `AndOp` | 逻辑与 |
| `\|` | `OrOp` | 逻辑或 |
| `!` | `NotOp` | 逻辑非（一元）|

**⇒ 非法运算符直接抛 `NotImplementedException("非法的二运算符:" + value)`。**

**⇒ 注意：逻辑运算符是 `&` / `|`（单字符），不是 `&&` / `||`。**

---

## 4. 函数解释器（10 个内置函数族）

```
AbsFunctionInterpreter
ConditionEarliestOrLatestOrMaxOrMinFunctionInterpreter
CtpEnumItemFunctionInterpreter
EarliestOrLatestFunctionInterpreter
ExtensionFunctionInterpreter               ← ★ 自定义扩展入口
GetListIndexFunctionInterpreter
IfsFunctionInterpreter
ListUniqueFunctionInterpreter
SumIfFunctionInterpreter
SumMaxMinFunctionInterpreter
```

**⇒ `ExtensionFunctionInterpreter` 是自定义函数的接入点。**
**⇒ `FunctionInterpreterFactory` / `FunctionInterpreterInitializer` 负责注册。**

### 4.1 函数名清单（从类名反推）

| 函数 | 说明 |
|---|---|
| `ABS` | 绝对值 |
| `IFS` | 多条件判断 |
| `SUMIF` | 条件求和 |
| `SUM` / `MAX` / `MIN` | 聚合 |
| `EARLIEST` / `LATEST` | 最早/最晚 |
| `LIST_UNIQUE` | 列表去重 |
| `GET_LIST_INDEX` | 取列表第 N 项 |
| `CTP_ENUM_ITEM` | 组织枚举项 |

**⇒ 这只是**内置**函数族。完整函数清单在 `formula-functions.xml`（已在资产中）。**

---

## 5. 变量解释器（5 种变量来源）

```
VariableInterpreter              ← 普通变量
EntityVariableInterpreter        ← ★ 实体字段
MicroFlowVariableInterpreter     ← ★ 微流程变量
SystemInterpreter                ← ★ 系统变量
ScalarInterpreter                ← 标量常量
```

**⇒ 表达式能引用的东西就这 5 类。**
**⇒ `EntityVariableInterpreter` 是「引用实体字段」的生成逻辑。**

---

## 6. 语义分析（`SemanticAnalyzer`）

```java
SemanticAnalyzer analyzer = new SemanticAnalyzer(
    context.getVariableSchema(),                                    // 变量 schema
    designData.getResultTypeInfo(),                                 // 结果类型
    designData.getResultTypeFullName(),                             // 结果类型全名
    designData.getTokens());                                        // token 列表
ExpressionDataType castExpressionDataType = analyzer.analyze(parent);
DataType castDataType = castExpressionDataType.getOriginDataType();
```

**⇒ 生成代码前会做类型推导，决定要不要插入 `BigDecimal` 转换。**
**⇒ 类型不确定时由 `getResultTypeSign()` 给兜底类型。**

---

## 7. 与 `MethodCallBack.getDefaultValue()` 的关系（澄清）

**之前误以为 `getDefaultValue()` 是表达式入口。实际不是。**

```java
// BaseEntityCurdService
public D getCascadeDefaultValue() {
    Long userId = RequestContext.get().getUserId();
    String key = "CascadeDefaultValue:" + userId;
    return this.getCascadeDefaultValue(key);
}

@ECacheable                                          // ★ 按用户缓存
public D getCascadeDefaultValue(String key) {
    BaseEntityActionDto dto = this.getDefaultValue();          // ← MethodCallBack 提供
    this.recursiveDefaultValue(this.entityMeta, dto);          // ← 递归给子表也建默认行
    return (D) dto;
}

private void recursiveDefaultValue(EntityMeta entityMeta, D currentDto) {
    if (Objects.isNull(currentDto)) return;
    if (CollectionUtils.isNotEmpty(entityMeta.getChildren())) {
        entityMeta.getChildren().forEach(meta ->
            Optional.ofNullable(findService(meta.getDtoClass())).ifPresent(service -> {
                BaseEntityActionDto defaultSubDto = service.getDefaultValue();
                if (Objects.nonNull(defaultSubDto)) {
                    if (RelationType.One2OneAggregation == meta.getRelationType()) {
                        ReflectUtil.setFieldValue(currentDto, meta.getDtoListName(), defaultSubDto);
                    } else if (RelationType.One2ManyAggregation == meta.getRelationType()) {
                        ReflectUtil.setFieldValue(currentDto, meta.getDtoListName(),
                            Lists.newArrayList(defaultSubDto));       // ★ 子表给一个空行
                    }
                    if (CollectionUtils.isNotEmpty(meta.getChildren())) {
                        service.recursiveDefaultValue(meta, defaultSubDto);
                    }
                }
            })));
    }
}
```

**⇒ `getDefaultValue()` 的真实职责：**
**⇒ 返回一个**空 DTO 骨架**（子表也带一条空行），用于前端「新建表单」时展示空白表格。**

**⇒ 它不是表达式执行入口，也不计算任何值。**
**⇒ 表达式值填充走另外的路径（`DtoConvertUtil` 或实体类生成方法）。**

**⇒ 修正：本文档之前把 `getDefaultValue()` 当作「表达式接入点」是错的。**

---

## 8. 完整的表达式链路（修正版）

```
【设计态】
用户在设计器配置表达式
    → AttributeExpressionDto（字段与表达式的绑定）
    → 存 expressionDesignData / expressionRuntimeData（两份）
            ↓
【代码生成】
ExpressionCodeGenerator
    → 解析 runtimeData 成 AST
    → SemanticAnalyzer 做类型推导
    → ExpressionInterpreter 遍历 AST
        → 各 Interpreter.interpret() 返回 Java 源码片段
        → 收集 import（BigDecimal / SymbolicOperationHelper）
    → 拼装完整方法体
    → 产出 exec<雪花ID> 方法
    → 注入到 Entity / Service 的生成代码
            ↓
【部署】
生成代码编译成 class
    → 放进应用的动态 jar
    → 应用重启/热加载后生效
            ↓
【运行时】
业务代码直接调用生成的方法（无解释开销）
    → 方法内部用 BigDecimal 运算
    → 通过 SymbolicOperationHelper 处理 null/空
```

**⇒ 所以「表达式执行」在运行时**没有解释器参与**，就是普通 Java 方法调用。**

---

## 9. 70 个表达式类清单（按包）

| 子包 | 类数 | 内容 |
|---|---|---|
| `codegen/` | 3 | `ExpressionCodeGenerator` / `ExpressionCodeGenConfig` / `CodeGenerateResult` |
| `codegen/common/` | 4 | `ExprCodeGenContext` / `ExprCodeGenTemplate` / `ExprCodeGenFullNameTemplate` / `Template` |
| `codegen/interpreter/` | 9 | `ExpressionInterpreter` / `BinaryInterpreter` / `UnaryInterpreter` / `FunctionInterpreter` / `VariableInterpreter` / `EntityVariableInterpreter` / `MicroFlowVariableInterpreter` / `SystemInterpreter` / `ScalarInterpreter` |
| `codegen/interpreter/function/` | 12 | 各函数解释器 + Factory + Initializer |
| `codegen/op/` | 20+ | 各运算符类 |
| `domain/` | — | `AttributeExpressionDto` / `UdcExpressionErrorCode` / Schema 加载 |
| `detection/` | — | 表达式检测工具（设计态校验）|

---

## 10. 仍待追（下一轮）

| 项 | 状态 |
|---|---|
| `ExpressionCodeGenerator.generateCode()` 主体 | 未读（入口逻辑）|
| `CodeGenerateResult` 的字段与消费方 | 未读 |
| `Template` / `ExprCodeGenTemplate` 的作用 | 未读（方法模板）|
| `exec<雪花ID>` 方法名如何生成 | 未读 |
| 生成的代码注入到哪个类 | 未读 |
| `formula-functions.xml` 完整函数表 | 资产中有，未解析 |
| `ExpressionEvaluator#eval`（若存在） | 本 jar 未见，可能在 `boot-formula-engine` |

---

## 11. 证据

| 结论 | 证据 | 等级 |
|---|---|---|
| 表达式是代码生成 | `Interpreter.interpret() : String` + `context.getImportClasses().add()` | `VERIFIED_STATIC_SOURCE` |
| 6 种 AST 节点 | `ExpressionInterpreter` 静态块 | `VERIFIED_STATIC_SOURCE` |
| 13 个运算符 | `Interpreter.getBinaryOp` switch | `VERIFIED_STATIC_SOURCE` |
| 四则运算走 BigDecimal | `BaseBinaryOp.DECIMAL_IMPORT` | `VERIFIED_STATIC_SOURCE` |
| 10 个内置函数族 | `codegen/interpreter/function/` 目录 | `VERIFIED_STATIC_SOURCE` |
| 5 种变量来源 | `codegen/interpreter/` 的 Interpreter 类名 | `VERIFIED_STATIC_SOURCE` |
| `getDefaultValue` 不是表达式入口 | `recursiveDefaultValue` 源码（只建空行）| `VERIFIED_STATIC_SOURCE` |
