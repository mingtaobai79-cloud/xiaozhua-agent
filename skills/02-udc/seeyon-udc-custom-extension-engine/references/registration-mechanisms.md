# 扩展点注册机制：平台怎么发现你写的类

配套事实格 `core/facts/standard-product/extension-registration-mechanisms.md`、
证据 `docs/audit/artifacts/extension-surface-20261029/registration-scan.json`。

本文件是深度参照：SKILL.md 里只留「三条铁律」，键名全表与三件套写法在这里。

## 一、三条通路，平台主用第一条

| 通路 | 平台用法 | 实测 |
|---|---|---|
| `META-INF/spring.factories`（平台自有键） | **主通路** | 91 jar 中 48 个有此文件，85 个键 |
| `META-INF/spring.factories`（Spring 官方键） | 自动装配入口 | EnableAutoConfiguration 41 个 jar |
| `META-INF/services`（Java SPI） | **几乎不用** | 只有 2 个 jar、3 个文件，全是第三方 |

那 3 个 Java SPI 文件：

```
org.apache.shardingsphere.spi.database.type.DatabaseType   [boot-starter-sharding] 2 实现
com.seeyon.boot.starter.nacos.spi.RegisterServiceSPI       [boot-starter-nacos]   1 实现
com.seeyon.boot.starter.nacos.spi.ConfigServiceSPI         [boot-starter-nacos]   1 实现
```

前一个是 ShardingSphere，后两个是 nacos 集成内部用。**128 个 UDC 扩展点没有一个走 Java SPI。**
给 ext 工程注册扩展，一律写 `src/main/resources/META-INF/spring.factories`。

## 二、8 个平台自有 SPI 键（逐字）

```
com.seeyon.boot.init.ComponentInitializer
  default void initialize(org.springframework.context.ConfigurableApplicationContext)
  default void setPropertyIfMissing(java.lang.String, java.lang.Object)
  extends com.seeyon.boot.init.AutoConfigExclude（default List<String> excludeAutoConfigClassNames()）
  平台实现 15 个，分布在 15 个 boot-starter-*

com.seeyon.boot.log.init.LogInitializer
  void init(com.seeyon.boot.log.LogbackConfigurator)          ← 唯一 abstract
  平台实现 18 个，来自 11 个 jar（boot-core / mq / es / dubbo / datasource …）

com.seeyon.boot.loader.ComponentDynamicRegister
  void register(java.lang.String, java.util.List<java.lang.String>)
  void unregister(java.lang.String)
  平台实现 6 个（dubbo / eventbus / mq / web / …）

com.seeyon.boot.loader.ComponentDynamicLoader
  boolean isComponent(java.lang.Class)                        ← 唯一 abstract
  default boolean loader(String, Class)
  default BeanDefinitionHolder buildBeanDefinitionHolder(String, Class)
  default void finishLoad()
  平台实现 2 个（boot-core / boot-starter-mybatis）

com.seeyon.boot.starter.formula.parser.semantic.function.FunctionSemanticAnalyzer
  ExpressionDataType analyze(ASTNode, SemanticAnalyzer)
  平台实现 19 个（boot-starter-formula 18 + organization-facade 1）

com.seeyon.boot.starter.formula.parser.scriptbuilder.ExtensionFunctionScriptBuilder
  自身 0 方法，extends ExpressionScriptBuilder
  → String build(ASTNode, ScriptBuildContext)
  平台实现 10 个（boot-starter-formula）

com.seeyon.udc.expression.codegen.interpreter.function.ExtensionFunctionInterpreter
  自身 0 方法，extends com.seeyon.udc.expression.codegen.interpreter.Interpreter
  → String interpret(ASTNode, ExprCodeGenContext)          ← 唯一必修
  → default BaseBinaryOp getBinaryOp(ExpressionToken)
  → default BaseUnaryOp getUnaryOp(ExpressionToken)
  → default boolean isMultiCtpEnumAssign(ASTNode, SchemaStructureDto, ExprCodeGenContext)
  平台实现 9 个（udc-biz）

com.seeyon.boot.starter.formula.parser.semantic.caller.CallerSemanticAnalyzer
  analyze(ASTNode, SemanticAnalyzer)
  String getOperatorName()
  default CallerAnalyzeStrategy getAnalyzeStrategy()
  平台实现 1 个（boot-starter-formula）
```

## 三、自定义表达式函数：三件套必须同时注册

平台把表达式函数拆成三个阶段，一个阶段一个键。**只注册一个 → 能保存、跑不对。**

```
① 语义分析  FunctionSemanticAnalyzer.analyze() → ExpressionDataType
              不注册 → 类型推断失败
② 脚本生成  ExtensionFunctionScriptBuilder.build() → String
              不注册 → 前端拿到空函数
③ 代码解释  ExtensionFunctionInterpreter.interpret() → String
              不注册 → 后端算不出值
```

`src/main/resources/META-INF/spring.factories`：

```properties
com.seeyon.boot.starter.formula.parser.semantic.function.FunctionSemanticAnalyzer=\
  com.example.ext.function.MyFuncSemanticAnalyzer
com.seeyon.boot.starter.formula.parser.scriptbuilder.ExtensionFunctionScriptBuilder=\
  com.example.ext.function.MyFuncScriptBuilder
com.seeyon.udc.expression.codegen.interpreter.function.ExtensionFunctionInterpreter=\
  com.example.ext.function.MyFuncInterpreter
```

最小实现形态：照抄平台自带的 9 个 Interpreter —— 只覆写 `interpret`，
私有方法 `buildFunctionCode` 做实际拼接（如 `EarliestOrLatestFunctionInterpreter`）。

## 四、全 default 接口的静默漏实现

`ComponentInitializer` 两个方法都是 default（含父接口 `AutoConfigExclude`），
所以**漏覆写 `initialize` 不报编译错，运行时静默什么都不做**。

这条推广开：遇到「方法块全是 default」的接口，编译通过 ≠ 实现正确。
判定法：看 `interfaces.json` 里该接口的 `methods[].modifiers`，全是 default 就要自己确认
有没有覆写对的那个方法名。

## 五、仍未闭合

| 项 | 状态 | 验证法 |
|---|---|---|
| 27 个纯扩展位（`ApplicationInnerReference` / `LimitCountCheck` / `PluginExecutor` …）的发现方式 | **UNVERIFIED** —— 91 jar 里无实现、无 services 条目、8 个键里也没有对应项 | 写空实现 + 打日志，构建部署看启动有没有被实例化 |
| ext 模块自己的 spring.factories 是否被合并加载 | **UNVERIFIED**（标准 Spring Boot 行为，未端到端实测） | ext 里注册一个 `LogInitializer` 打一行日志，看启动日志 |

## 六、工具与证据

```
python tools/core/platform/scan_registration.py \
    --interfaces docs/audit/artifacts/extension-surface-20261029/interfaces.json \
    --emit docs/audit/artifacts/extension-surface-20261029/registration-scan.json
```

产出：每个 jar 的 `services` / `spring_factories` / `imports` 三段 + `resolve` 字段说明
jar 路径怎么解析到的。

**第二个坑：`sources[].jar` 只存文件名，不是路径。** 直接 `Path(jar).exists()` 对 91 个
全部 False，脚本会安静地把每个 jar 记成 error（summary 里 `jars: 91` 看着正常，
`jars_with_services: 0` 才是破绽）。要按仓库布局 `<repo>/<pkg>/<version>/<jar>` 递归解析，
找不到同名就取该构件目录下最新的一版，并把差异写进 `resolve` 字段。
闸门见 `test_registration_mechanism_fact`：8 个键必须同时满足「在 spring.factories 实测里出现过」
+「在事实格里写过」+「interfaces.json 里是 interface」+「方法名能查到（沿 extends 找父接口）」，
外加反证断言 `services 条目 <= 4 且不含 com.seeyon.udc`。
