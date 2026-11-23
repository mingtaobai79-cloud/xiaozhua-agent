# boot-formula-engine：公式求值引擎（Aviator）

## Capability

**在 Java 里直接求值一段业务公式，或把「命名公式」注册成可复用函数。**
引擎基于 Aviator（`com.googlecode.aviator`），平台在其上加了函数注册与聚合函数机制。

## Version

`boot-formula-engine` 5.3.603（jar 在盘，javap 全量抽取）。

## Input

无。

## Required

无。求值入口是单例，不需要 Spring 注入。

## ★ 一、求值（最常用）

```java
FormulaEvaluator ev = FormulaEvaluator.getInstance();

Map<String,Object> env = Map.of("amount", 1000, "rate", 0.13);
Object r1 = ev.eval("amount * rate", env);            // 走日志
Object r2 = ev.evalWithoutLog("amount * rate", env);   // 不写日志（高频/敏感时用）
Object r3 = ev.eval("amount * rate", env, "bizKey");   // 带业务标识，日志可追
```

签名原文：

```java
Object eval(String expr, Map<String,Object> env);
Object eval(String expr, Map<String,Object> env, String bizKey);
Object evalWithoutLog(String expr, Map<String,Object> env);
Object evalWithoutLog(String expr, Map<String,Object> env, String bizKey);
FormulaValidateDto validate(String expr);
FormulaValidateDto validate(String expr, Map<String,Object> env);
```

## ★ 二、先验证再求值（用户输入公式时必做）

```java
FormulaValidateDto v = ev.validate("amount * ");       // 语法错在这里暴露
if (!v.isValid()) { throw new BusinessException(...); }
```

**不要拿 try/catch 包 `eval` 当校验**：`eval` 抛的是运行时异常，
而 `validate` 给的是结构化结果（能不能用、错在哪）。

## 三、注册自定义函数（三件套）

```java
// ① 操作符/函数：实现 Caller
public class MyCaller implements Caller {
    public Object call(Object[] args);                              // 参数
    public Object callWithType(Object[] args, String t1, String t2); // 带类型
    public String getOperator();                                    // 函数名
}

// ② 注册
FormulaEvaluator.getInstance().registerOperator("myFunc", new MyCaller());
FormulaEvaluator.getInstance().addAggFunction("myAgg", new MyCaller(), functionDto);

// ③ 查有哪些
List<FunctionDto> all = FormulaEvaluator.getInstance().getAllFunction();
```

引擎内的函数类型（字节码原文）：

```
CustomFunction   extends aviator AbstractVariadicFunction   (name, Caller)
ScriptFunction   extends aviator AbstractVariadicFunction   (name, script)
AggregationFunction extends aviator AbstractFunction        (name, Caller)
Caller           接口：call / callWithType / getOperator
```

注解（`engine/annotation/`）：`@Function` / `@FunctionClass` / `@Parameter(s)` / `@ParamLinkage` / `@ReturnValue`。

## 四、命名公式（存库的公式）

```java
// FormulaAppService（对外，包 SingleRequest）
SingleResponse<FormulaOpResultDto> validate(SingleRequest<FormulaDto>);
SingleResponse<FormulaOpResultDto> create(SingleRequest<FormulaDto>);
SingleResponse<FormulaOpResultDto> update(SingleRequest<FormulaDto>);
SingleResponse<Integer>            deleteById(SingleRequest<Long>);
SingleResponse<Integer>            deleteByIds(SingleRequest<List<Long>>);
SingleResponse<Boolean>            exists(SingleRequest<String>);
ListResponse<FormulaFunctionCategoryEnum> getFormulaCategoryList();
ListResponse<FormulaDataTypeEnum>         getFormulaDateTypeList();

// FormulaService（内部，裸 DTO）
FormulaOpResultDto validate(FormulaDto);
FormulaOpResultDto create(FormulaDto) / update(FormulaDto);
FormulaDto selectById(Long) / List<FormulaDto> selectByIds(List<Long>);
FunctionDto formula2function(FormulaDto);      // ★ 命名公式 → 可注册函数
```

⇒ 想复用「已存库的公式」当函数：`formula2function` + `registerOperator`。

## Side Effects

- `eval` 默认写日志（含表达式与入参），**敏感数据用 `evalWithoutLog`**。
- `registerOperator` 是全局注册（单例），同名会覆盖。
- 公式里能调到的函数越多，越要注意「表达式注入」——绝不把用户可控字符串直接当表达式跑。

## Known Constraints

1. 引擎是 Aviator 语法，**不是** SpEL / JS；平台表达式（表单默认值那套）与本文的公式引擎是两套东西，
   前端表达式面板见 `udc/setting/expression-component/component.md`。
2. `validate` 只校验语法与变量，**不保证业务可执行**（除零、空引用要自己兜）。
3. `addAggFunction` 需要 `FunctionDto`（描述元数据），不是只有名字。
4. 自定义函数注册后对所有应用可见，注意命名前缀。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `FormulaEvaluator` 10 方法 + 单例 `getInstance()` | `javap -p` 5.3.603 | VERIFIED_STATIC_BYTECODE |
| `Caller` 3 方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| `CustomFunction/ScriptFunction/AggregationFunction` 继承 aviator 抽象类 | 同上 | VERIFIED_STATIC_BYTECODE |
| `FormulaAppService` 8 方法 / `FormulaService` 9 方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| 5 个注解（@Function 等） | 类清单 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 全部签名可逐字复核
- ⚠️ 未真机跑过求值（无样本表达式库）

## 给 Agent 的判据

```
要算一段公式        → FormulaEvaluator.getInstance().eval(expr, env)
要校验用户输入      → 先 validate(expr)，别看 eval 抛不抛
公式要复用          → FormulaService.formula2function(dto) + registerOperator
要新函数            → 实现 Caller（call/callWithType/getOperator）再 registerOperator
不想留日志          → evalWithoutLog
```
