# standard-product｜Dubbo 跨服务调用与注入（环境无关）

> 本格只讲**包内怎么用**：怎么拿标品服务的代理、怎么把自己的实现暴露出去、注解与后处理器。
> 不涉及任何具体工程/环境/地址。
> 适用：扩展代码要调标品 Dubbo 服务，或要把自己的能力导出成 Dubbo 服务。

分级：`VERIFIED_STATIC_BYTECODE`（javap 逐类，见 §8）。

## 1. Capability

- **消费侧**：不写 `@DubboReference` 也能拿到标品服务代理（`DubboFactory`）
- **生产侧**：把自己的实现按注解扫描导出去（`@ServiceBeanPostProcessor` + 导出后处理器）
- **跨应用 AppService**：`AppServiceProxy`（含可靠版 + 回调）
- **鉴权/上下文透传**：`DubboContextFilter` + 灰度上下文

不证：注册中心地址、分组/版本的现网取值（那是环境配置）；也不证运行期路由结果。

## 2. Version

`com.seeyon:boot-starter-dubbo` 5.3.358（48 类 / 4 接口 / 220 方法）

## 3. Input

`boot-starter-dubbo-<ver>.jar`，包前缀 `com/seeyon/boot/starter/dubbo/`。

## 4. Required

应用已引入该 starter 且开启 Dubbo（`DubboProperties.enable`）。

## 5. Execution

按「消费 / 生产 / 跨应用 / 上下文」四组取签名。见 §7。

## 6. Side Effects

消费侧发起远程调用（业务副作用由被调方决定）；生产侧注册服务到注册中心。

## 7. Known Constraints

### 7.1 ★ 拿标品服务代理：用 `DubboFactory`，不要自己写 `@DubboReference`

```java
public interface DubboFactory {
    <T> T getProxy(Class<T> clazz);
    <T> T getProxy(Class<T> clazz, String group);
    <T> T getProxy(Class<T> clazz, String group, String version);
    <T> T getProxy(Class<T> clazz, String group, int timeout);
    <T> T getProxy(Class<T> clazz, String group, String version, int timeout);
}
```

五个重载是**同一件事的不同精度**：仅类名 → 只按接口找；再加 group → 按分组；再加 version →
按版本；最后可加 timeout（毫秒）。

⇒ 调标品接口时**注入 `DubboFactory` 再 `getProxy(标品接口.class)`**。
自己写 `@DubboReference` / `@Reference` 会绕过平台的注册中心与 group/version 约定，
在灰度与多环境下取到错误实例。

### 7.2 为什么「注入即可用」而不是「手工注册」——平台的后处理器链

实测四段（都在本 starter 内，无需你写）：

```
DubboImportBeanDefinitionRegistrar    扫描注解 → 注册 ServiceAnnotationBeanPostProcessor
SeeyonServiceClassPostProcessor       postProcessBeanDefinitionRegistry：按包扫描注册
ServiceBeanPostProcessor              postProcessBefore/AfterInitialization：处理灰度 tag
SeeyonDubboExportBeanPostProcessor    exportServiceBean(appName, interfaceClass, ref)：真正导出
```

`DubboProperties` 的扫描面由这几项控制（实测字段）：

```java
Set<String> getPackagesToScan();                  // 扫描哪些包
Map<String, ...> customPackagesToScan;             // 额外自定义包
boolean isEnable();  boolean isRegister();  boolean isMockEnable();  boolean isEnableNacos();
String getName();  String getProtocol();  String getVersion();
String getZookeeperUrl();  String getTsfUrl();
Integer getQosPort();  Integer getPayload();
boolean isConsumerLog();  boolean isProviderLog();
```

⇒ **你的实现落在 `packagesToScan` 覆盖的包下 + 带上平台的导出注解，就会自动导出**；
不需要手写 `ServiceConfig`。导不出去时先查两件事：包是否在扫描面内、注解是否被扫描到。

### 7.3 跨应用调 AppService：`AppServiceProxy`（不是 Dubbo 直连）

```java
public interface AppServiceProxy {
    SingleResponse<Object>          invokeAppService(SingleRequest<AppServiceInvokeDto>);
    ListResponse<Object>            invokeAppServiceForList(SingleRequest<AppServiceInvokeDto>);
    PageResponse<Object>            invokeAppServiceForPage(SingleRequest<AppServiceInvokeDto>);
    <T> SingleResponse<T>           reliableInvokeAppService(SingleRequest<AppServiceReliableInvokeDto<T>>);
}
public interface AppServiceProxyCallback {
    SingleResponse<String> callback(SingleRequest<CommandCallbackDto>);
}
```

⇒ 三种返回形态各有一个入口（单对象 / 列表 / 分页），按目标方法的返回类型选，**不要一律用单对象再从里挖**。
需要「一定送达/失败可续」用 `reliableInvokeAppService`，并实现 `AppServiceProxyCallback` 接回调。
`AppServiceInvokeDto` 有 18 个字段、`AppServiceReliableInvokeDto` 8 个、`AppServiceAsyncInvokeDto` 10 个 ——
拼参数时对照字段，不要猜。

### 7.4 上下文与灰度：`DubboContextFilter` / `GrayContext`

```java
public class DubboContextFilter {
    public Result invoke(Invoker<?> invoker, Invocation invocation);
}
public class GrayContext {
    public static String getGroupValue();
    public static void setGroupValue(String);
    public static void removeAll();
}
```

⇒ 请求上下文（租户/用户/traceId）由 `DubboContextFilter` 在 RPC 边界自动透传，**不必手动塞 header**；
灰度分组用 `GrayContext`，用完 `removeAll()` 清（它会串到同线程后续调用）。
`ProviderLogFilter` / `ConsumerLogFilter` / `MDCFilter` 负责两侧日志与 MDC，也不需自己写。

### 7.5 非 Nacos 环境：注册中心是可替换的

```java
public class NacosRegistryFactory { ... createRegistry(URL); createNamingService(URL); }
public class DynamicRouterFactory     { ... createRouter(Class, URL); }
public class GrayStateRouterFactory   { ... createRouter(Class, URL); }
```

⇒ 换注册中心 = 换 `RegistryFactory` 实现，不改业务代码；路由同理（`DynamicRouter` / `GrayStateRouter`）。
`DubboDynamicRegister` 提供运行时注册/反注册（`register(appName, List)` / `unregister(appName)`）与
provider model 管理（`addProviderModel` / `clearProviderModule`）。

## 8. Evidence

```
① 路径  docs/audit/artifacts/extension-surface-20261029/batch2/boot-starter-dubbo.json
        （48 类 / 4 接口 / 220 方法）
        文件内只有 artifact 名与版本，无工程/环境信息
② 复现  uv run --no-project python tools/core/platform/extract_jar_symbols.py \
          --jar "<按 Maven 坐标 com.seeyon:<artifact>:<ver> 解析出的 jar>" \
          --include com/seeyon/boot/starter/dubbo/ \
          --javap <javap 原生路径> --limit 1000 --emit <out.json>
③ 校验  本格每个类名/方法/字段都能在 out.json 的 classes[].symbols 里逐字命中；
        `DubboProperties` 的 20 个字段在 fields[] 里逐个可核。
```

## 9. Verified

| 项 | 等级 |
|---|---|
| `DubboFactory` 5 个重载 | `VERIFIED_STATIC_BYTECODE` |
| 四段后处理器链（注册/扫描/灰度/导出） | `VERIFIED_STATIC_BYTECODE`（类与方法存在） |
| `DubboProperties` 扫描与开关字段 | `VERIFIED_STATIC_BYTECODE`（fields 逐字） |
| `AppServiceProxy` 三种返回形态 + 可靠版 | `VERIFIED_STATIC_BYTECODE` |
| `GrayContext` 与 `DubboContextFilter` | `VERIFIED_STATIC_BYTECODE` |
| 注册中心/路由工厂可替换 | `VERIFIED_STATIC_BYTECODE` |
| 运行期实际取到的实例与路由结果 | **UNVERIFIED** |

## 铁律

- 拿标品服务代理用 `DubboFactory.getProxy(...)`，不要自己写 `@DubboReference`/`@Reference`。
- 五个重载按精度选：类名 → +group → +version → +timeout；多环境/灰度必须带 group。
- 自己的实现要导出：放在 `DubboProperties.packagesToScan` 覆盖的包下并带平台导出注解，不要手写 `ServiceConfig`。
- 跨应用调 AppService 用 `AppServiceProxy`，按目标返回类型选单对象/列表/分页入口；要可靠送达用 `reliableInvokeAppService` + 回调。
- 上下文透传由 `DubboContextFilter` 完成，不要手动塞 header；灰度用 `GrayContext` 且用完 `removeAll()`。
- 换注册中心/路由换对应 `*Factory`，不要在业务代码里判断环境。
