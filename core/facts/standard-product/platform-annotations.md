# 平台注解速查（109 个 @interface）

## 1. Capability

回答「这个注解能贴在哪」「运行期能不能反射读到」「贴了会不会自动注册」。

注解不是接口，不能 implements——它是**贴在人写的类/方法/字段上的标记**，由平台在读的时候判断。
所以要会用注解，必须知道三件事：贴哪（@Target）、何时有效（@Retention）、谁来读（元注解/框架）。

## 2. Version

同 `BASELINE.md`。

## 3. Input

```
javap -v 每个注解类的输出
  RuntimeVisibleAnnotations 块（常量池引用，需解引用）
  → @Target(ElementType[]) / @Retention(RetentionPolicy) / 其他元注解
```

## 4. Required

无（查表）。

## 5. Execution

```
① 要贴注解 → 先查 §7.2 的 @Target 分组，确认能贴在你的目标位置
② 要靠注解让平台发现你 → 查 §7.1 带 Spring 元注解的 9 个（贴了自动注册）
③ 要知道填什么 → 查 §7.4 元素最多的注解
```

## 6. Side Effects

**贴了带 `@Service`/`@Component` 元注解的注解 = 这个类被 Spring 扫描注册为 Bean**。
这不是"加个说明"，是真的会实例化——写错了会启动报错或多实例。

## 7. Known Constraints

### 7.1 最重要的发现：9 个注解自带 Spring 组件元注解

| 注解 | 元注解 | 构件 | 含义 |
|---|---|---|---|
| `AppService` | **@Service, @Primary** | boot-core | 贴在类上 = 该类的接口实现自动成为 AppService Bean |
| `Importer` | **@Component** | udc-plugin-api | 贴了 = 导入扩展被扫描注册 |
| `ConsistencyDetection` | **@Component, @Order** | udc-plugin-api | 贴了 = 一致性检测项注册，@Order 定执行顺序 |
| `TypeMapping` | **@Component, @Order** | udc-common | 类型映射注册 |
| `ParamLoadService` | **@Service** | boot-starter-formula | 参数加载服务 |
| `ExpressionFilter` | **@Component** | boot-starter-formula | 表达式过滤器 |
| `EventHandler` | **@Component** | boot-starter-eventbus | 事件处理器 |
| `ImportUpgradeHandler` | **@Component** | udc-plugin-api | 导入升级处理器 |

**这是平台注册机制的第三条通路**（前两条是 `spring.factories` 和纯扩展位的元数据注册）：
**注解自带 `@Component` → Spring 组件扫描 → 自动成为 Bean**。
所以用 `@Importer` / `@ConsistencyDetection` 这类注解时，**不用写任何注册文件**，
贴上去就被发现——但反过来，忘了贴就完全不被调用，且不会有任何报错。

### 7.2 按 @Target 分组（能贴哪）

| @Target | 数量 | 典型注解 |
|---|---|---|
| `METHOD`（方法） | 55 | 大部分 `@XxxOperation`、`@Excel*` 列定义 |
| `TYPE`（类/接口） | 50 | `AppService`、`Importer`、`ConsistencyDetection`、`EntityInfo` |
| `FIELD`（字段） | 22 | `EntityAttribute`（19 元素）、`DtoAttribute`（13）、`Maskable` |
| `—`（无 @Target，可贴任意位置） | 9 | `OpenApi`、`Safety`、`LogDefault`、`AppIdRef`、`Custom` |
| `PARAMETER`（参数） | 9 | 参数校验类 |
| `CONSTRUCTOR`（构造器） | 7 | — |
| `ANNOTATION_TYPE`（元注解） | 5 | 只能贴在其他注解上 |
| `TYPE_USE` | 2 | 类型使用处（泛型参数里） |
| `LOCAL_VARIABLE` | 1 | — |

一个注解读数（如 `AppService` 是 `TYPE`）说明：它只能贴在类上，贴方法上编译就报错。

### 7.3 @Retention：108 个 RUNTIME，1 个不是

`RUNTIME` = 运行期能用反射读到 → **平台全靠反射读注解，所以扩展点类注解必须是 RUNTIME**。
`CLASS` = 只在字节码里，反射读不到（做不了运行时判断，只能给字节码工具/APT 用）。
`SOURCE` = 编译完就丢。

实测 109 个里 108 个 RUNTIME、1 个 `CLASS`＋其余。写扩展点时如果自己造注解，
**必须标 `@Retention(RUNTIME)`**，否则平台读不到，行为等于没贴。

### 7.4 元素最多的注解（贴之前先看要填什么）

| 注解 | 元素数 | @Target | 元素 |
|---|---|---|---|
| `EntityAttribute` | **19** | FIELD | value, description, hidden, changeId, dataI18n, dataType… |
| `ExcelContentStyle` | 17 | METHOD | dataFormat, hidden, locked, wrapped, verticalAlignment… |
| `ExcelHeadStyle` | 17 | METHOD | 同上 |
| `DtoAttribute` | 13 | FIELD | value, description, hidden, xssProcess, dataI18n, relationApp… |
| `AppServiceOperation` | 9 | METHOD | — |
| `BootApp` | 8 | TYPE | 组合了 8 个 Spring 启动注解 |

`EntityAttribute` 19 个元素是设计态真实字段（`dataType`/`hidden`/`changeId`/`dataI18n`），
和前端组件 props 里的 `dataType` 是同一套语义。

### 7.5 9 个无 @Target 的注解

`OpenApi`、`Safety`、`LogDefault`、`LogDefaultUpdate`、`EntityIndex`、`Parameter`、
`Custom`、`CustomAttribute`、`AppIdRef`。

无 `@Target` 在 Java 里表示**可以贴在任何声明上**（类/方法/字段/参数都行）。
实际用的时候看平台文档或参照实现，别因为"没限制"就乱贴。

### 7.6 拿不到的东西

- **注解的默认值**（`AnnotationDefault`）：javap -v 里有，本产物没解——要查默认值直接看 §8 的命令
- **注解元素之间的依赖关系**（如 A 元素存在时 B 必填）：字节码里没有，靠文档或实测
- **注解的实际生效时机**（启动时 / 每次请求 / 发布时）：@Retention 只说"能读到"，
  什么时候读要看消费方代码，本产物不覆盖

## 8. Evidence

```
docs/audit/artifacts/extension-surface-20261029/annotations.md   26 KB / 109 个
  按 @Retention 分组 → 元素最多的 15 个 → 全部逐个（全名 + Target + 构件 + jar）

生成器 tools/core/platform/scan_annotation_meta.py
  对每个注解类跑 javap -v，解常量池 + RuntimeVisibleAnnotations
  闸门：解析出的注解 < 90 个则 exit 5

单独查某个注解的原始输出：
  javap -v -cp <jar> com.seeyon.xxx.Yyy
```

## 9. Verified

| 项 | 等级 |
|---|---|
| 109 个注解的 @Target / @Retention / 元注解 | `VERIFIED_STATIC_BYTECODE`（javap -v 解引用） |
| 108 个 RUNTIME、9 个无 @Target | `VERIFIED_STATIC_BYTECODE` |
| 9 个注解自带 @Service/@Component | `VERIFIED_STATIC_BYTECODE` |
| 「贴了 @Component 元注解就自动注册」 | **推断**（Spring 组件扫描语义），本机未实测启动 |
| 注解元素的默认值 | **UNVERIFIED**（未解 AnnotationDefault） |
| 注解何时被读 | **UNVERIFIED**（需看消费方代码或实测） |
