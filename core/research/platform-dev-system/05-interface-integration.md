# 专题 5：接口调用体系

> 状态：**研究中（第一轮·静态）** · 未审计
> 平台版本：`udc-platform-5.3.517`
> 最近更新：2026-11-17

---

## 1. 研究目标

分清五种调用方式（Dubbo / @Autowired / 泛化 / 微流程 / 第三方），给出决策树与约束。

---

## 2. 五种调用方式总览

```
① Dubbo 远程调用
   DubboFactory#getProxy(Class[, group[, version[, timeout]]])
   适用：跨应用/跨服务，需注册中心
   
② @Autowired 本地注入
   Spring 容器内的 Bean 直接注入
   适用：同 JVM 内，同类加载器

③ 泛化调用（Generic Invocation）
   AppServiceProxy#invokeAppService(...)
   适用：调用方没有目标接口的 Class（动态场景）

④ 微流程调用
   微流程「调用应用服务」节点
   受 9 个黑白名单约束

⑤ 第三方集成
   HttpClientUtil / CipConnector
   适用：外部 HTTP/API
```

---

## 3. 接口资产（已核实口径）

### 3.1 AppService 830 个

| 口径 | 数量 |
|---|---|
| 唯一 owner 类 | **830** |
| 名字以 `AppService` 结尾 | **830**（全部） |
| 名字以 `AppServiceImpl` 结尾 | **0** |
| 声明方法总数 | **9343** |

**⇒ 830 全是接口，零实现类。这是「对外暴露的 AppService 接口清单」。**
**⇒ 平均每接口 11.3 个方法。**

### 3.2 平台服务依赖 17 项

来源：`presetData/dependencyGraph.json`

| name | caption | type |
|---|---|---|
| `organization` | 组织机构 | SERVICE |
| `ctp-user` | 用户中心 | SERVICE |
| `bpm` | BPM引擎 | SERVICE |
| `ctp-affair` | 事项中心 | SERVICE |
| `ctp-message` | 消息中心 | SERVICE |
| `cip-connector` | 连接器 | SERVICE |
| `cdp-data` | 数据中台 | SERVICE |
| `portal` | 门户 | SERVICE |
| `app-common` | 基础设置 | SERVICE |
| `cip-capability` | 基础能力接入 | SERVICE |
| `udc` | 低代码平台 | SERVICE |
| `FRONTEND` | 前端控件 | FRONTEND |
| `starter` | starter组件 | STARTER |
| `boot-extend` | 平台拓展组件 | STARTER |
| `udc-starters` | udc运行态组件 | STARTER |
| `boot-starter-file` | 文件组件 | STARTER |
| `boot-starter-opinion` | 意见组件 | STARTER |

**⇒ 这是「UDC 应用可依赖哪些平台服务」的权威清单。**

---

## 4. Dubbo 调用

### 4.0 ★★ 注解体系（本轮最大发现，109 个注解）

来源：`surface-index.tar.gz` → `annotations.md`（来自 `javap -v` 的 RuntimeVisibleAnnotations）

**平台有 109 个 `@interface`，其中 108 个 `@Retention(RUNTIME)`。**

#### 4.0.1 `@AppService`：AppService 的注册机制

```
注解：com.seeyon.boot.annotation.AppService
元素数：4
@Target：TYPE
元注解：@Service, @Primary        ← ★★ 关键
构件：boot-core / boot-core-5.3.600.jar
```

**⇒ 这是「@Autowired 能注什么」的直接答案：**

1. **标了 `@AppService` 的类型 = Spring `@Service`**（自动被扫描注册）
2. **同时是 `@Primary`**（同类型多实现时优先注入这个）
3. **所以业务代码可以直接 `@Autowired` 注入 `*AppService` 接口**

**⇒ 推论（待证）：`@Autowired` 与 `DubboFactory` 的分工**
- 同 JVM 内（同应用/同 classpath）→ `@Autowired` 走本地 Bean
- 跨应用/跨服务 → `DubboFactory.getProxy()` 走远程

**⚠️ 但「什么时候必须用 getProxy」仍需证据。`@AppService` 的 `@Primary` 只证明本地注入可行，不证明跨应用可行。**

#### 4.0.2 `@DubboComponent`：Dubbo 注册

```
注解：com.seeyon.boot.starter.dubbo.annotation.DubboComponent
元素数：0（纯标记）
@Target：TYPE
构件：boot-starter-dubbo / boot-starter-dubbo-5.3.600.jar
```

**⇒ 这是 Dubbo 服务注册的标记注解（0 参数）。**
**⇒ 标了它的类才会被暴露为 Dubbo 服务（待证）。**

#### 4.0.3 `@AppServiceOperation`：方法级操作声明

```
注解：com.seeyon.boot.annotation.AppServiceOperation
元素数：9
@Target：METHOD
构件：boot-core
```

**⇒ 方法级 9 个参数，可能声明：操作名、权限、日志、幂等等。**
**⚠️ 9 个元素的具体名称未提取（需 javap -v 详情）。**

#### 4.0.4 ★ 修正：`@PublicApi` / `@Internal` / `@PublicSpi` **不是**平台三分类

```
注解：graphql.PublicApi / graphql.Internal / graphql.PublicSpi
构件：boot-starter-graphql
```

**⇒ 这三个是 **GraphQL 库**的注解，与 Seeyon 的「公开/内部/扩展接口」三分类**无关**。**

**⚠️ 这是一个典型的「类名陷阱」——差点误判成平台能力分类。**
**⇒ 平台的三分类判定仍需另找依据（黑白名单 + 包路径 + `@AppService` 是否标注）。**

#### 4.0.5 幂等与并发控制注解（★ 专题 3 缺口的部分答案）

| 注解 | 元素 | Target | 构件 | 说明 |
|---|---|---|---|---|
| **`@Idempotent`** | **0** | METHOD | `boot-starter-appservice` | **★ 幂等标记（纯标记）** |
| **`@AntiReCommit`** | 2 | METHOD | `boot-starter-web` | **★ 防重复提交** |
| **`@ExclusivePermit`** | 2 | METHOD | `udc-biz` | 互斥许可 |
| **`@LimitCountOperation`** | 2 | METHOD | `udc-biz` | 限流 |

**⇒ 平台有 4 种并发/幂等控制注解，不需要自己实现。**
**⚠️ `@Idempotent` 是 0 元素纯标记 → 幂等策略（key 从哪来、多久失效）由框架内部决定，未证。**

#### 4.0.6 事件注解

| 注解 | 元素 | Target | 元注解 | 构件 |
|---|---|---|---|---|
| `@EventHandler` | **0** | TYPE | **`@Component`** | `boot-starter-eventbus` |
| `@EventSubscribe` | 2 | METHOD | — | `boot-starter-eventbus` |
| `@MessageListener` | — | — | — | （消息） |

**★★ `@EventHandler` 的元注解是 `@Component`**
**⇒ 贴了 `@EventHandler` 的类会自动注册为 Spring Bean。**
**⇒ 这是「写了代码怎么被平台发现」的暗线（annotations.md 自己点明了这一点）。**

#### 4.0.7 其他关键注解（按专题归类）

**元数据（专题 1）：**
```
@EntityInfo      | 12 元素 | TYPE  | boot-core
@DtoInfo         |  5      | TYPE  | boot-core
@EntityAttribute | 19      | FIELD | boot-core
@DtoAttribute    | 13      | FIELD, METHOD | boot-core
@EnumInfo        |  6      | TYPE  | boot-core
@EnumAttribute   |  6      | FIELD | boot-core
@MessageInfo     |  6      | TYPE  | boot-core
@EntityIndex     |  4      | —     | boot-core
@TypeMapping     |  3      | TYPE  | udc-common（元注解 @Component, @Order）
@Custom          |  2      | —     | boot-core
@CustomAttribute |  2      | —     | boot-core
```

**⇒ `@TypeMapping` 带 `@Component` + `@Order` → 类型映射器可插拔且有顺序。**

**表达式（专题 4）：**
```
@Function           | 7 元素 | METHOD | boot-formula-engine   ← ★ 函数注册
@FunctionClass      | 0      | TYPE   | boot-formula-engine   ← ★ 函数类
@FunctionSupporter  | 1      | TYPE   | boot-starter-formula  ← 函数支持者
@ReturnValue        | 4      | METHOD | boot-formula-engine
@Parameter          | 3      | —      | boot-formula-engine
@Parameters         | —      | —      | boot-formula-engine
@ParameterInfo      | 3      | PARAMETER | boot-core
@ExpressionFilter   | —      | —      | —
@ExprConsistency    | —      | —      | —（表达式一致性检测）
```

**★★ 自定义表达式函数的注册方式已找到：**
```java
@FunctionClass                    // 贴在类上
public class MyFunctions {
    @Function(...)                // 贴在方法上，7 个参数
    public static Object myFunc(@Parameter ... args) { ... }
}
```

**持久化（专题 3）：**
```
@CountSql        | 1 元素 | METHOD | boot-starter-mybatis   ← ★ COUNT SQL 控制
@DataChangeAware | 1      | METHOD | udc-cicd
@ComparedSchema  | —      | —      | —
@ConsistencyDetection | — | —      | —
```

**★★ `@CountSql`（METHOD，1 元素，mybatis 注解）**
**⇒ 这极可能与 `PageInfo#isNeedTotal(false)` 是同一套「避免全量 COUNT」机制的注解侧。**

**缓存：**
```
@ECacheable / @ECachePut / @ECacheEvict / @ENoCache / @RCacheable / @PriorityCache
```

**权限：**
```
@HasRole / @AuthModel / @AuthOperation / @ResourcePermission / @AppOpsAuth
```

**流程/调度：**
```
@CtpSchedule (13 元素) / @IsolatorExecutor (5, 线程池) / @BootApp (8)
```

**★★ `@BootApp` 元注解含 `@EnableTransactionManagement`**
**⇒ 平台开启了注解式事务 → 事务边界由 Spring `@Transactional` 控制。**
**⇒ 这是专题 3「事务边界」的部分答案（机制存在，但具体范围仍未证）。**

**其他：**
```
@Safety / @OpenApi / @Maskable / @OperationLog / @LogDefault / @UpgradeMethod
@RecycleSerialNumber / @ModuleEnhance / @AsyncTrace / @IgnoredException
@ValidationGroup / @ImportUpgradeHandler / @Trace / @TraceTags
@Crypto...（加密相关）
```

### 4.1 `DubboFactory`（4 重载）

```java
com.seeyon.boot.dubbo.DubboFactory
  # getProxy(Class<T>)
  # getProxy(Class<T>, String group)
  # getProxy(Class<T>, String group, String version)
  # getProxy(Class<T>, String group, String version, int timeout)
```

**⇒ 4 个重载（不是 5），逐层增加：group / version / timeout。**

### 4.1A ★★ 扩展点体系（第二证据源，交叉验证）

来源：`surface-index.tar.gz` → `extension-points.md`

**规模（逐字）：**
```
151 个带 abstract 的 UDC 接口
├─ 128 个是真接口
│   ├─ 101 个平台已有实现（可继承或参照）
│   └─ 27 个纯扩展位（零实现，自己全写）
└─ 23 个是注解（@interface），不是 implements 的对象
```

**★★ 这独立验证了专题 2 的统计（第二证据源）：**

| 接口 | abstract | **impl** | 我的统计 | 一致性 |
|---|---|---|---|---|
| `CodeTask` | 1 | **52** | 52 实现 | ✅ 完全吻合 |
| `TransportHandler` | 1 | **32** | 30+ | ✅ 修正为 32 |
| `Interpreter` | 1 | **9** | 9 | ✅ 完全吻合 |

**⇒ 这是「重要结论寻找第二证据来源」的成功案例。**
**⇒ `CodeTask` 52 个实现从此有双源确认，不再是单源结论。**

#### 4.1A.1 实现最多的 10 个接口（族主）

| 接口 | abstract | impl | 包 |
|---|---|---|---|
| `CodeTask` | 1 | **52** | `com.seeyon.udc.common.autocode` |
| `TransportHandler` | 1 | **32** | `...autocode.transport` |
| `Importable` | 1 | **29** | `...transport.upgrade` |
| `AppMetaDataContextPostProcess` | 1 | **27** | `com.seeyon.udc.common.metadata` |
| `ElementRepository` | 3 | **21** | `com.seeyon.udc.model` |
| `SaveAsHandler` | 1 | **17** | `...transport.saveas` |
| `BaseDesignMetadataQueryService` | 6 | **11** | `com.seeyon.udc.metadata.query` |
| `DetectionMetadataAware` | 1 | 9 | `...detection.context.metadata` |
| `Interpreter` | 1 | 9 | `...expression.codegen.interpreter` |
| `LastVersionMetadataManagerService` | 3 | 8 | `com.seeyon.udc.api` |

**⇒ 「impl 多的就是族主」——这些接口是平台的核心扩展骨架。**

#### 4.1A.2 ★ 27 个纯扩展位（零平台实现，必须自己写）

| 接口 | abstract | 包 |
|---|---|---|
| **`PluginDefinition`** | **2** | `com.seeyon.udc` |
| `ApplicationInnerReference` | 3 | `com.seeyon.udc.autocode` |
| `DataFlowCodeService` | 1 | `com.seeyon.udc.autocode` |
| `DependencyAnalysisService` | 1 | `com.seeyon.udc.autocode` |
| `BaseNode` | 18 | `...v27.microflow.bo` |
| `BaseTrigger` | 18 | `...v27.microflow.bo` |
| `UdcTreeQueryService` | 1 | `com.seeyon.udc.common.api` |
| `ApplicationInnerReference` | 14 | `...common.autocode` |
| `Recoverable` | 1 | `...common.autocode` |
| `ConfigurableCodeContext` | 5 | `...autocode.config` |
| `Lifecycle` | 3 | `...autocode.context` |
| `Compatible` | 1 | `...transport.compare` |
| `SchemaFilter` | 2 | `...common.transport` |
| `Functor` | 1 | `com.seeyon.udc.common.utils` |
| `ConsistenceDetection` | 3 | `com.seeyon.udc.detection` |
| `WidgetExpressionDetectionFunction` | 1 | `...detection.task.util` |
| `OperationLogSchema` | 1 | `com.seeyon.udc.domain` |
| `Functor` | 1 | `...expression.codegen.util` |
| `ConvertorTypeDeterminer` | 1 | `...metadata.convert` |
| `ComponentIdentity` | 1 | `...microflow.cascade` |
| `MicroFlowComponentHandler` | 8 | `...microflow.cascade` |
| `FullNameExtractor` | 1 | `...activity.base` |
| `SFunction` | 1 | `...microflow.util` |
| `MicroflowNodeParser` | 1 | `...model.parser` |
| `MigrateCallback` | 1 | `com.seeyon.udc.repo` |
| `TaskCallable` | 1 | `com.seeyon.udc.task` |
| `Consumer3` | 1 | `com.seeyon.udc.utils` |

**★★ `PluginDefinition`（2 abstract，零实现）**
**⇒ 这是**唯一**的插件定义扩展位 → 客户实现它来注册自己的 `CodeTask`。**
**⇒ 与专题 2 的 `PluginDefinition#getCodeTasks(): Collection<CodeTask>` 完全对应。**
**⇒ 这是「如何给平台加自定义生成任务」的唯一入口。**

**⇒ 其余 26 个纯扩展位说明：**
- `BaseNode`(18) / `BaseTrigger`(18) — 微流程节点的抽象（v27 包）
- `MicroFlowComponentHandler`(8) — 微流程组件级联
- `ConfigurableCodeContext`(5) — 可配置代码上下文
- `Lifecycle`(3) — 生命周期
- 等

#### 4.1A.3 ★ 注册机制：`spring.factories`

来源：`registration-scan.json`

```json
{
  "jars": 91,
  "jars_with_services": 2,
  "jars_with_spring_factories": 48,
  "jars_with_imports": 0,
  "service_entries": 3,
  "spring_factories_keys": 85,
  "imports_files": 0
}
```

**⇒ 91 个 jar 里：**
- **48 个用 `spring.factories`**（自动配置，占 53%）
- 只有 **2 个**用 `META-INF/services`（标准 SPI）
- **0 个**用 Spring Boot 3 的 `AutoConfiguration.imports`

**⇒ 结论：平台用 Spring Boot 2 风格（`spring.factories`），不是 3.x 风格。**
**⇒ 「写了代码怎么被平台发现」的三条路：**
1. `spring.factories`（48 个 jar，主流）
2. `META-INF/services`（2 个 jar，SPI）
3. **注解自动扫描**（`@Component` / `@AppService` / `@EventHandler` 等元注解带 `@Component`）

**证据等级：** `STATIC_RULE`

### 4.1B ★ 接口三分类的判定依据（修正 §4.0.4 的空缺）

**⚠️ 之前说「三分类判定依据待找」，现在有了部分答案。**

| 分类 | 判定依据 | 证据等级 |
|---|---|---|
| **公开 API** | 标 `@AppService`（元注解 `@Service` + `@Primary`） | `STATIC` |
| **扩展点** | 在 `extension-points.md` 的 128 个真接口里 | `STATIC` |
| **纯扩展位** | 128 个里 impl=0 的 27 个 | `STATIC` |
| **内部实现** | 不在上述两类，且不在黑白名单白名单里 | `STATIC` |

**⇒ 这比「按包名猜」可靠得多。**
**⚠️ 但 `@AppService` 的实际标注率未统计（需注解实例数据）。**

### 4.2 泛化调用（`AppServiceProxy`）

```java
com.seeyon.boot.starter.dubbo.api.AppServiceProxy        ← 接口
  # invokeAppService(SingleRequest<AppServiceInvokeDto>): SingleResponse<Object>
  # invokeAppServiceForList(...): ListResponse<Object>
  # invokeAppServiceForPage(...): PageResponse<Object>
  # reliableInvokeAppService(SingleRequest<AppServiceReliableInvokeDto<T>>): ...

com.seeyon.boot.starter.proxy.api.CustomerProxyAppService   ← 客户代理接口
  # invokeAppService / ForList / ForPage / reliableInvokeAppService
  # schedulePendingServiceInvoke(): void          ← ★ 定时处理待办
  # scheduleCallbackProcessResult(): void         ← ★ 定时处理回调
  # scheduleRecoveryMisProcess(): void            ← ★ 定时恢复未处理
```

### 4.2.1 ★ `AppServiceInvokeDto` 实际只有 **9 个字段**

**⚠️ 修正：v4 计划写的「18 字段」是错的，实测 9 个。**

| getter | 类型 | 说明 |
|---|---|---|
| `getInterfaceName()` | `String` | **接口全限定名** |
| `getMethodName()` | `String` | **方法名** |
| `getParamType()` | `String` | 参数类型 |
| `getGenericType()` | `String` | 泛型类型 |
| `getSubGenericType()` | `String` | 子泛型类型 |
| `getParamJson()` | `String` | **参数 JSON** |
| `getBeanName()` | `String` | Bean 名 |
| `getReturnJson()` | `Boolean` | 是否返回 JSON |
| `getBodyZip()` | `Boolean` | body 是否压缩 |

**⇒ 泛化调用的最小信息集：接口名 + 方法名 + 参数类型 + 参数 JSON。**
**⇒ `getBodyZip()` 说明支持压缩传输（大报文场景）。**

### 4.2.2 ★ 泛化调用的完整实现链（v4 未记录）

```
AppServiceProxy（接口）
  ↓
AppServiceProxyApiImpl（实现）
  # invokeAppService / ForList / ForPage / reliableInvokeAppService
  # loadDynamicModuleIfNecessary(String, String): void    ← ★ 动态模块加载
  ↓
CtpCustomerProxyAppServiceImpl（客户代理实现，最完整）
  # invokeAppService / ForList / ForPage
  # asyncInvokeAppService(AppServiceAsyncInvokeDto, Class): BaseResponse  ← ★ 异步调用
  # processServiceInvoke(AppServiceInvokeDto): BaseResponse
  # wrapResponse(Object, boolean): SingleResponse<Object>
  # processOpenInvoke(ProxyInvokeInfo): void
  # feedbackResult(Long): void
  # doServiceInvoke(Long): void
  # selectPendingList(): List<ProxyInvokeInfo>
  # selectPendingCallbackList(): List<ProxyInvokeInfo>
  # selectRecoveryList(): List<ProxyInvokeInfo>
  # recoveryMisProcessTask(): void
  ↓
AppServiceReliableInvoker（可靠调用器）
  # invoke(SingleRequest<AppServiceInvokeDto>, String): ...
  # invokeForList / invokeForPage
  # reliableInvoke(SingleRequest<AppServiceReliableInvokeDto<T>>, String): ...
  # doInvoke(...)
  # getProxy(String, Integer): AppServiceProxy            ← ★ 带超时取代理
  # processServiceReliableInvoke(AppServiceReliableInvokeDto, String): boolean
  # compensateReliableInvoke(List<ReliableInvokeInfo>): void   ← ★ 补偿
  # scheduleProcessServiceInvoke(): void
  # scheduleTask(): void
```

**★★ 关键结论：泛化调用不是「一次性 RPC」，而是有完整的可靠性机制：**

1. **异步调用**：`asyncInvokeAppService(AppServiceAsyncInvokeDto, Class)`
2. **可靠投递**：`reliableInvoke` + `ReliableInvokeInfo` 实体
3. **补偿**：`compensateReliableInvoke(...)`
4. **定时任务**：3 个 `schedule*` 方法（待办/回调/恢复）
5. **动态模块加载**：`loadDynamicModuleIfNecessary`
6. **超时控制**：`getProxy(String, Integer)`

**⇒ 这是「事务性消息」模式的实现：先落库，再投递，失败补偿。**

**证据等级：** `VERIFIED_STATIC_BYTECODE`（签名）
**待证：** `ReliableInvokeInfo` 表结构、补偿触发条件

### 4.2.3 高层封装（其他模块各自实现）

| 类 | 说明 |
|---|---|
| `com.seeyon.bpm.domain.service.dubboProxy.AppServiceInvoke` | BPM 侧的调用封装（15 方法） |
| `com.seeyon.ctp.affair.domain.db.proxy.AffairServiceProxy` | 事项侧封装 |
| `com.seeyon.boot.starter.udcrt.dto.UdcReferInvokeDto` | 引用选择器封装（带 appName/hostAppName） |
| `com.seeyon.cip.plug.domain.service.OrgQueryService` | 组织查询封装（`dealProxyParam` 构建 DTO） |
| `com.seeyon.cdp.common.manager.metadata.MetadataCdpDesignService` | 元数据查询封装（`buildInvokeDto`） |

**⇒ 各业务模块都封装了自己的泛化调用入口，不直接 new `AppServiceInvokeDto`。**
**⇒ `UdcReferInvokeDto` 的字段（appName / hostAppName / currentAppName / currentHostAppName / returnValueClassName）说明跨应用调用需要**应用上下文**。**

### 4.3 版本与灰度

```java
com.seeyon.udc.common.transport.VersionControl
  # getSourceDesignerVersion(): String
  # getAppVersion(): String
  # getAppCopVersion(): String
  # getDownloadUserId(): Long
  # getDownloadClientIp(): String
  # getDownloadTime(): String
  # getDownloadEnvironment(): String
```

**⇒ `VersionControl` 是**下载/传输**的版本上下文，不是 Dubbo 版本。**
**⇒ 之前 `dubbo-cross-service.md` 里说的「灰度上下文」可能指别的类，需核对。**

**⚠️ 修正：`VersionControl` 的 7 个字段全是「下载」相关（userId/ip/time/environment），
是**代码下载**的审计信息，不是 Dubbo 调用上下文。**

---

## 5. 微流程调用约束（★ 9 个名单文件全部解析）

### 5.1 `appServiceMethodBlackList.json`（3 项，禁止调用）

```json
[
  "com.seeyon.cip.capability.appservice.sms.ShortMessageTemplateAppService...",
  "com.seeyon.cip.capability.appservice.sms.ShortMessageSignAppService...",
  "com.seeyon.cip.capability.appservice.sms.ShortMessageSignAppService..."
]
```

**⇒ 只有短信相关的 3 个方法被禁止。**
**⇒ 推论（待证）：防止业务微流程滥发短信。**

### 5.2 `bootStarterServiceWhiteList.json`（1 项，允许调用）

```json
["com.seeyon.boot.starter.file.appservice.FileAppService"]
```

**⇒ 文件服务是唯一被显式允许的 boot starter 服务。**

### 5.3 `bootStarterWhiteList.json`（1 项）

```json
["boot-starter-ganttchart"]
```

**⇒ 甘特图组件被允许。**

### 5.4 `systemPackageWhiteList.json`（4 项，包级白名单）

```json
["com.seeyon.udc.", "com.seeyon.boot.", "PageDtoRequest", "PageResponse"]
```

**⇒ 两个包前缀 + 两个类型名。**
**⇒ 微流程可调用 `com.seeyon.udc.*` 和 `com.seeyon.boot.*` 下的服务。**

### 5.5 `entityEventWhiteList.json`（9 项）

```json
[
  "com.seeyon.udc.common.event.AfterCreateEvent",
  "com.seeyon.udc.common.event.AfterDeleteEvent",
  "com.seeyon.udc.common.event.AfterUpdateEvent",
  "com.seeyon.udc.common.event.BeforeCreateEvent",
  "com.seeyon.udc.common.event.BeforeDeleteEvent",
  "com.seeyon.udc.common.event.BeforeUpdateEvent",
  "com.seeyon.udc.common.event.TransactionSuccessCreateEvent",
  "com.seeyon.udc.common.event.TransactionSuccessDeleteEvent",
  "com.seeyon.udc.common.event.TransactionSuccessUpdateEvent"
]
```

**⇒ 与 `presetData/event/defaultevent.json` 的 9 个事件**完全对应**（含包名）。**
**⇒ 这给出了事件的全限定类名，可直接在代码里引用。**

### 5.6 `deprecatedEntityEventWhiteList.json`（9 项，旧包名）

```json
[
  "com.seeyon.boot.starter.udcrt.event.AfterCreateEvent",
  "com.seeyon.boot.starter.udcrt.event.AfterDeleteEvent",
  "com.seeyon.boot.starter.udcrt.event.AfterUpdateEvent",
  "com.seeyon.boot.starter.udcrt.event.BeforeCreateEvent",
  "com.seeyon.boot.starter.udcrt.event.BeforeDeleteEvent",
  "com.seeyon.boot.starter.udcrt.event.BeforeUpdateEvent",
  "com.seeyon.boot.starter.udcrt.event.TransactionSuccessCreate",
  "com.seeyon.boot.starter.udcrt.event.TransactionSuccessDelete",
  "com.seeyon.boot.starter.udcrt.event.TransactionSuccessUpdate"
]
```

**★★ 这证明事件包发生了迁移：**
```
旧：com.seeyon.boot.starter.udcrt.event.*       （已废弃，仍兼容）
新：com.seeyon.udc.common.event.*               （推荐）
```

**⚠️ 注意旧包名少了 `Event` 后缀（`TransactionSuccessCreate` vs `TransactionSuccessCreateEvent`）。**

**⇒ 写代码时应使用**新包名**。**

### 5.7 `otherEntityAppServiceMethodNameList.json`（9 个方法名）

```json
[
  "selectByIds",
  "selectCascadeByIds",
  "selectCountByConditions",
  "selectPageByConditions",
  "selectListByComplexConditions",
  "selectPageByComplexConditions",
  "selectCountByComplexConditions",
  "deleteByComplexConditions",
  "selectListFuncByComplexConditions"
]
```

**⇒ 这是「跨实体 AppService 可调用的方法名白名单」。**
**⇒ 微流程可以调用其他实体的这 9 个方法（只读 + 一个 delete）。**

**★ 注意 `selectCascadeByIds` 在列——级联查询被允许跨实体调用。**

### 5.8 `microFlowNameBlackList.json`（4 个保留名）

```json
["AffairCommonApp", "CtpEnumItem", "MicroFlowOrgPeople", "App"]
```

**⇒ 微流程名不能叫这 4 个（与平台内置对象冲突）。**

### 5.9 `mqMetaDataBlackList.json`（5 项）

```
ORGANIZATION.com.seeyon.organization.message.core.OrgBaseMes...
ORGANIZATION.com.seeyon.organization.message.core.metadata.O...
CTP_TASK_DELAY_TOPIC.com.seeyon.boot.starter.mq.support.dto...
CONNECTOR_CALLBACK.com.seeyon.cip.connector.dto.execute.Even...
CMD_MSG.M...
```

**⇒ 5 个 MQ 主题被禁止（平台内部消息）。**

---

## 6. 决策树（基于已证约束）

```
需要调用某个能力
  │
  ├─ 是外部系统（HTTP/API）？
  │    └─ 是 → HttpClientUtil（平台已提供）
  │             或 CipConnector（连接器，需配置）
  │
  ├─ 是同 JVM 内的 Bean？
  │    ├─ 是 → @Autowired 直接注入
  │    │        ⚠️ 前提：接口在 classpath 且同类加载器
  │    │
  │    └─ 否（跨服务）→ 有目标接口 Class？
  │         ├─ 有 → DubboFactory.getProxy(Class[, group[, version[, timeout]]])
  │         └─ 无 → AppServiceProxy.invokeAppService(...) 泛化调用
  │
  └─ 是在微流程里？
       ├─ 是 → 受 9 个名单约束：
       │        · 不能用 appServiceMethodBlackList 里的（3 个短信）
       │        · boot starter 只能用 FileAppService / ganttchart
       │        · 包前缀只能 com.seeyon.udc. / com.seeyon.boot.
       │        · 跨实体只能用 9 个方法
       └─ 否 → 走上面分支
```

**⚠️ 这张决策树是**基于约束推导**，不是平台官方文档。**
**⇒ 每个分支的依据都在 §5 的名单文件里。**
**⇒ 但「@Autowired 能注什么」缺少直接证据（见 §7）。**

---

## 7. 未证部分（关键）

### 7.1 `@Autowired` 能注什么

**已知：**
- `AppService` 是接口（830 个）
- `DubboFactory#getProxy` 可拿代理
- 平台大量使用 `@Autowired`（从 `feature/tree_entity/template/config.json` 的字段定义可见）

**实测证据（来自 feature template config）：**
```java
@Autowired private DynamicSelectValidateService dynamicSelectValidateService;
@Autowired private DynamicSelectService dynamicSelectService;
@Autowired private DynamicSelectAppService dynamicSelectAppService;
@Autowired private UdcArchiveTreeEntityRuntimeAppService udcArchiveTreeEntityRuntimeAppService;
```

**⇒ 生成代码里直接用 `@Autowired` 注入 `*Service` / `*AppService`。**

**⚠️ 但「什么时候必须用 DubboFactory 而不是 @Autowired」未证。**
**⇒ 需要：查 `consumers.json`（183 接口 → 调用者）看真实用法。**

### 7.2 泛化调用的完整链路

**已知：**
```
AppServiceProxy#invokeAppService / ForList / ForPage / reliable
AppServiceInvokeDto（18 字段，未提取）
GenericInvocationAuthService#invokeAppService(String, String, ...)
```

**⚠️ 未证：**
- `AppServiceInvokeDto` 18 字段含义
- 鉴权如何做
- 泛化调用的权限是否与直接调用相同

### 7.3 权限 / 异常 / 事务

**⚠️ 全部未证。** 需反编译或查 `boot-starter-security`。

---

## 8. 第三方集成

### 8.1 已证

```
HttpClientUtil（93 方法，来自 platform_class_index）
CipConnector（连接器，17 个平台服务之一）
microflow/ConnectorActivity.ftl（微流程连接器节点）
```

**⇒ 平台有两条第三方集成路径：**
1. **代码级**：`HttpClientUtil`
2. **配置级**：`CipConnector` + 微流程 `ConnectorActivity`

### 8.2 未证

| 问题 | 状态 |
|---|---|
| `CipConnector` 的配置方式 | 需查 cip 域 facts |
| 微流程连接器节点怎么用 | 需实测 |
| 超时/重试/幂等 | 需查 |

---

## 9. 证据清单

| # | 结论 | 等级 | 来源 |
|---|---|---|---|
| 1 | AppService 830 全为接口，零实现 | `STATIC` | 脚本统计 |
| 2 | `DubboFactory` 4 个重载 | `VERIFIED` | 签名 |
| 3 | 泛化调用 4 形态（普通/列表/分页/可靠） | `VERIFIED` | 签名 |
| 4 | `VersionControl` 是下载审计，不是 Dubbo 版本 | `VERIFIED` | 签名（修正） |
| 5 | 短信 3 个方法被禁 | `STATIC` | 黑名单 |
| 6 | FileAppService / ganttchart 被允许 | `STATIC` | 白名单 |
| 7 | 包白名单 2 前缀 + 2 类型 | `STATIC` | `systemPackageWhiteList` |
| 8 | 9 个事件的全限定名 | `STATIC` | `entityEventWhiteList` |
| 9 | 事件包已迁移（旧 `udcrt.event` → 新 `udc.common.event`） | `STATIC` | 两份白名单对比 |
| 10 | 跨实体可调 9 个方法 | `STATIC` | `otherEntityAppServiceMethodNameList` |
| 11 | 微流程 4 个保留名 | `STATIC` | `microFlowNameBlackList` |
| 12 | 5 个 MQ 主题被禁 | `STATIC` | `mqMetaDataBlackList` |
| 13 | 生成代码用 `@Autowired` 注入 Service | `STATIC` | feature template config |
| 14 | `@Autowired` vs `DubboFactory` 判定 | **无** | — |
| 15 | 权限/异常/事务 | **无** | — |

---

## 10. 下一轮任务

1. **提取 `AppServiceInvokeDto` 18 字段**
2. **分析 `consumers.json`（183 接口 → 调用者），找 `@Autowired` vs `getProxy` 的真实分布**
3. **`GenericInvocationAuthService` 的鉴权参数**
4. 转专题 6：基础组件
