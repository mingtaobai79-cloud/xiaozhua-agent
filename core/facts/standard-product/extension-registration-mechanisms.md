# 扩展点注册机制：写了代码平台怎么发现

## 1. Capability

回答一个问题：**在 `-ext` 里写完实现类，凭什么被平台加载？**

UDC 扩展点有 128 个真接口，但「实现接口」只是第一步。平台发现实现的通路只有三条，
走错通路 = 代码编译通过、运行时静默不生效。

本格给出：91 个标品 jar 的实测注册面（`META-INF/services` / `spring.factories`）、
8 个平台自有 SPI 键的完整契约、以及自定义表达式函数必须成对注册的三件套。

## 2. Version

不适用（机制层，跨版本稳定）。实测样本见 §9。

## 3. Input

```
- ext 工程里手写的实现类（implements 某个扩展点接口）
- ext 工程 src/main/resources/META-INF/spring.factories（注册声明）
```

## 4. Required

| 要素 | 说明 |
|---|---|
| 实现类全限定名 | 与 spring.factories 里写的必须逐字一致 |
| 键名 | 必须是平台声明的接口全名（§7.2 的 8 个之一，或 Spring 官方键） |
| 无参构造 | 平台用 Spring 反射实例化，不保证注入 |

## 5. Execution

```
应用启动
  → Spring Boot 读所有 jar 的 META-INF/spring.factories
  → 按键合并（同名键的多个 jar 的值合并成一个列表）
  → 对每个 com.seeyon.* 键，实例化列出的类
  → 逐个回调接口方法（initialize / init / register / build …）
```

## 6. Side Effects

- 注册失败不会抛异常打断启动，多数是**静默跳过**（键名拼错、类名拼错都无声）。
- `LogInitializer` 在日志系统初始化阶段跑，实现里抛异常会导致**日志配置残缺**，不是启动失败。
- `ComponentDynamicRegister.register` 会往 Spring 容器里动态塞 Bean，注册错类会污染容器。

## 7. Known Constraints

### 7.1 四条通路，接口型走第一条、注解型走第四条

| 通路 | 平台用法 | 证据 |
|---|---|---|
| **`META-INF/spring.factories`（平台自有键）** | **接口型扩展点的主通路**，48/91 个 jar 有，85 个键 | §7.2 |
| `META-INF/spring.factories`（Spring 官方键） | EnableAutoConfiguration 41 个 jar | 自动装配入口 |
| `META-INF/services`（Java SPI） | **几乎不用**，91 个 jar 只有 2 个有，且都是第三方 | §7.4 |
| **注解自带 `@Component`/`@Service`** | **注解型扩展点的主通路**，9 个注解读这条，贴了即注册；`@BootApp` 的 `basePackages="com.seeyon"` 已证实覆盖 ext 包 | §7.6 |
| 子类型反射扫描（`BeanReflections.getSubTypesOf`） | 只有 2 个类型走这条（`AppBeanNameModifier` / `UdcBaseEntity`），**不是给业务扩展点用的** | §7.7 |

**结论：**
- **实现接口型扩展点** → 注册走 `spring.factories`，不要写 `META-INF/services`
- **用注解型扩展点**（`@Importer`/`@ConsistencyDetection` 等）→ **贴上注解就完了**，
  不写任何注册文件；但忘贴就静默失效

### 7.2 平台自有 SPI 键全表（8 个）

| 键（接口全名） | 必实现方法（逐字） | 平台实现数 | 来源 jar |
|---|---|---|---|
| `com.seeyon.boot.init.ComponentInitializer` | `default void initialize(org.springframework.context.ConfigurableApplicationContext)` | 15 | 15 个 boot-starter-* |
| `com.seeyon.boot.log.init.LogInitializer` | `void init(com.seeyon.boot.log.LogbackConfigurator)` | 18 | 11 个 jar（boot-core / mq / es / dubbo…） |
| `com.seeyon.boot.loader.ComponentDynamicRegister` | `void register(java.lang.String, java.util.List<java.lang.String>)`<br>`void unregister(java.lang.String)` | 6 | dubbo / eventbus / mq / web |
| `com.seeyon.boot.loader.ComponentDynamicLoader` | `boolean isComponent(java.lang.Class)` | 2 | boot-core / boot-starter-mybatis |
| `com.seeyon.boot.starter.formula.parser.semantic.function.FunctionSemanticAnalyzer` | `ExpressionDataType analyze(ASTNode, SemanticAnalyzer)` | 19 | boot-starter-formula / organization-facade |
| `com.seeyon.boot.starter.formula.parser.scriptbuilder.ExtensionFunctionScriptBuilder` | `String build(ASTNode, ScriptBuildContext)`（继承自 `ExpressionScriptBuilder`） | 10 | boot-starter-formula |
| `com.seeyon.udc.expression.codegen.interpreter.function.ExtensionFunctionInterpreter` | `String interpret(ASTNode, ExprCodeGenContext)`（继承自 `Interpreter`） | 9 | udc-biz |
| `com.seeyon.boot.starter.formula.parser.semantic.caller.CallerSemanticAnalyzer` | `analyze(ASTNode, SemanticAnalyzer)`<br>`String getOperatorName()`<br>`default CallerAnalyzeStrategy getAnalyzeStrategy()` | 1 | boot-starter-formula |

`ComponentInitializer` 的两个方法都是 `default`（含父接口 `AutoConfigExclude.excludeAutoConfigClassNames()` 也是 default），
所以实现类**只覆写 `initialize`** 就够，不会因为漏实现而编译失败——反过来说，漏覆写也不会报错，只是什么都不做。

### 7.3 自定义表达式函数：三件套必须同时注册

这是「表达式 / 变量」域最容易踩的坑。平台把表达式函数拆成三个阶段，每个阶段一个 SPI 键：

```
① 语义分析    FunctionSemanticAnalyzer.analyze(ASTNode, SemanticAnalyzer) → ExpressionDataType
                 ↓ 决定这个函数返回什么类型（不注册 → 类型推断失败）
② 脚本生成    ExtensionFunctionScriptBuilder.build(ASTNode, ScriptBuildContext) → String
                 ↓ 生成前端可执行的 JS 片段（不注册 → 前端拿到空函数）
③ 代码解释    ExtensionFunctionInterpreter.interpret(ASTNode, ExprCodeGenContext) → String
                 ↓ 生成后端 Java 代码（不注册 → 后端算不出值）
```

**只注册其中一个的后果**：表达式能保存但跑不对；或前端能跑后端报错。三件套全注册才闭环。

注册写法（`src/main/resources/META-INF/spring.factories`）：

```properties
com.seeyon.boot.starter.formula.parser.semantic.function.FunctionSemanticAnalyzer=\
  com.example.ext.function.MyFuncSemanticAnalyzer
com.seeyon.boot.starter.formula.parser.scriptbuilder.ExtensionFunctionScriptBuilder=\
  com.example.ext.function.MyFuncScriptBuilder
com.seeyon.udc.expression.codegen.interpreter.function.ExtensionFunctionInterpreter=\
  com.example.ext.function.MyFuncInterpreter
```

参考实现（平台自带的 9 个 Interpreter）：`EarliestOrLatestFunctionInterpreter` 只覆写 `interpret`，
私有方法 `buildFunctionCode` 做实际拼接——这就是最小实现形态。

### 7.4 平台不用 Java SPI（反证）

91 个标品 jar 里，`META-INF/services/` 只有 3 个文件、全在 2 个 jar：

```
org.apache.shardingsphere.spi.database.type.DatabaseType    [boot-starter-sharding] 2 个实现
com.seeyon.boot.starter.nacos.spi.RegisterServiceSPI        [boot-starter-nacos]   1 个实现
com.seeyon.boot.starter.nacos.spi.ConfigServiceSPI          [boot-starter-nacos]   1 个实现
```

前一个是第三方（ShardingSphere），后两个是 nacos 集成内部用。
**128 个 UDC 扩展点里，没有一个通过 `META-INF/services` 注册。**

### 7.5 27 个纯扩展位怎么注册

27 个「零平台实现」的接口（`ApplicationInnerReference` / `LimitCountCheck` / `PluginExecutor` …）
在 91 个 jar 里既没有实现类、也没有 services 条目。它们的发现方式只能靠：

| 可能通路 | 状态 |
|---|---|
| `spring.factories` 自定义键 | 未发现对应键（8 个键里没有） |
| Spring 组件扫描（`@Component` + basePackages 覆盖 ext 包） | **UNVERIFIED**，需构建后看容器 |
| 平台元数据注册（设计态配置 / 数据库记录） | **UNVERIFIED** |

⇒ 选这 27 个之前，先在测试环境做一次最小验证：写一个空实现 + 打日志，看启动时有没有被实例化。

### 7.6 第三条通路：注解自带 @Component（9 个注解走这条）

`spring.factories` 和「纯扩展位元数据注册」之外，还有一条**最容易被忽略**的通路：

```
注解自身带 @Component / @Service 元注解
  → 实现类贴上这个注解
  → Spring 组件扫描到 → 自动成 Bean → 平台拿来用
```

实测 109 个注解里 9 个自带 Spring 组件元注解：

| 注解 | 元注解 | 说明 |
|---|---|---|
| `AppService` | @Service, @Primary | 类实现自动成为 AppService Bean |
| `Importer` | @Component | **导入扩展，贴了就被注册** |
| `ConsistencyDetection` | @Component, @Order | 一致性检测项 + 执行顺序 |
| `TypeMapping` | @Component, @Order | 类型映射 |
| `ParamLoadService` | @Service | 参数加载 |
| `ExpressionFilter` | @Component | 表达式过滤 |
| `EventHandler` | @Component | 事件处理 |
| `ImportUpgradeHandler` | @Component | 导入升级 |

**推论（重要）**：这几个注解型的扩展点**不需要写任何注册文件**，贴注解就算注册；
**忘了贴 = 完全不被调用，且零报错**——这是比 `spring.factories` 漏写更隐蔽的坑，
因为漏写 spring.factories 至少类还在，漏贴注解连日志都没有。
详见 `platform-annotations.md` §7.1。

#### 证据链：ext 包确实在扫描范围内（javap -v 解 @BootApp）

`com.seeyon.boot.annotation.BootApp` 的元注解逐字：

```java
@SpringBootApplication
@EntityScan("com.seeyon")
@ComponentScan(
    basePackages = "com.seeyon",
    nameGenerator = SeeyonBeanNameGenerator.class,
    excludeFilters = @Filter(type = ANNOTATION, classes = SpringBootApplication.class)
)
@EnableScheduling @EnableAsync
@EnableAspectJAutoProxy(proxyTargetClass = true)
@EnableTransactionManagement(proxyTargetClass = true, order = 10)
@Import(BootAutoConfigurationImportSelector.class)
```

三条结论：

| 项 | 值 | 对客开的意义 |
|---|---|---|
| `basePackages` | **`com.seeyon`** | ext 工程根包是 `com.seeyon.<应用标识>` → **落在扫描范围内** |
| `excludeFilters` | 仅排除 `@SpringBootApplication` 注解的类 | 只防启动类重复注册，**不影响 ext 里的 `@Component`** |
| `nameGenerator` | `SeeyonBeanNameGenerator` | Bean 名不是默认规则，见下 |

#### Bean 名不是默认的「类名首字母小写」

`SeeyonBeanNameGenerator.buildDefaultBeanName()` 末尾调用：

```java
return APP_BEAN_NAME_MODIFIER.modifyBeanName(definition, Introspector.decapitalize(shortClassName));
```

而 `CtpAppBeanNameModifier.modifyBeanName` 的第一句就是：

```java
if (!Apps.isMonolithic()) {
    return beanName;          // 非单体：不改，就是类名首字母小写
}
// 单体：遍历所有 AppBeanNameModifier 实现逐个改写（可能加应用前缀）
```

⇒ **按类型注入（`@Autowired`）永远安全；按名字注入（`@Resource(name="xxx")`）在单体模式下
Bean 名可能被改写成带前缀的形式**，别硬编码 Bean 名。多应用共存时同名类不会冲突，
靠的就是这层改写。

### 7.7 子类型扫描：只有 2 个类型走这条，不是通用通路

平台里有个工具：

```java
BeanReflections.getSubTypesOf(T.class)
  → BeanReflections.getReflections("com.seeyon").getSubTypesOf(type)
```

即用 Reflections 库扫整个 `com.seeyon` 包下所有子类型，**不写注册文件、不贴注解也能被发现**。

全量扫 109 个 jar 的字节码，**只有 4 个 class 调它，覆盖 2 个类型**：

| 被扫的类型 | 用途 |
|---|---|
| `com.seeyon.boot.common.AppBeanNameModifier` | Bean 名修饰器扩展（§7.6 末尾那条链） |
| `com.seeyon.udc.domain.entity.UdcBaseEntity` | UDC 实体基类（实体发现/元数据注册） |

**结论：这条路只服务于 Bean 名改写和 UDC 实体发现两件事，不是给业务扩展点用的通用注册机制。**
之前把 27 个纯扩展位猜成"可能走子类型扫描"是不成立的——它们要么走 `spring.factories`，
要么走注解 + 组件扫描，要么确实是死代码。这条实测把猜测排除掉了。

### 7.8 ext 工程的 spring.factories 是否生效

静态证据只能证明「平台自己用 spring.factories 加载这些键」。
`-ext` 模块的 `src/main/resources/META-INF/spring.factories` 会被打进最终产物、
并在启动时被 Spring Boot 合并——**这是标准行为，但本仓库尚未做端到端实测**。
标 `UNVERIFIED`，验证方法见 §8。

## 8. Evidence

```
docs/audit/artifacts/extension-surface-20261029/registration-scan.json
  91 个 jar 的 META-INF/services + spring.factories + spring/*.imports 全量
  summary: jars 91 / with_services 2 / with_spring_factories 48 / service_entries 3
           spring_factories_keys 85 / imports_files 0

生成器 tools/core/platform/scan_registration.py
  jar 路径解析：sources 里只存文件名，按 <repo>/<pkg>/<version>/<jar> 递归解析，
  记录 resolve 字段说明是否命中同一版本
```

实测 jar 版本：udc 族 `5.3.517`，boot 族 `5.3.345`，udc-facade `5.3.477`（仓库现有版本，
与用户截图 pom 里的 `5.3.605` 不同，机制层不受影响）。

## 9. Verified


| 断言 | 怎么验 |
|---|---|
| 平台用 spring.factories 而非 Java SPI | 重跑 `scan_registration.py`，看 `jars_with_services` 是否仍 <= 2 |
| 8 个键的接口签名 | 查 `interfaces.json`，逐字比对 §7.2 |
| 自定义表达式函数三件套 | 写一个函数，只注册 Interpreter → 观察前端/后端分别报什么错；再补另两个 |
| ext 的 spring.factories 生效 | 在 ext 里注册一个 `LogInitializer` 打一行日志，构建部署后看启动日志 |
