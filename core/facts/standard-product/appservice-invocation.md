# AppService 调用通路：怎么把方法真正调起来

## 1. Capability

拿到「接口名 + 方法名 + 入参 DTO」只是纸面。本格回答**怎么真正调起来**，两条通路：

| 通路 | 适用 | 特点 |
|---|---|---|
| **Spring 注入** | ext 代码里已知接口类型 | 编译期类型检查，推荐 |
| **泛化调用** | 只知道接口名字符串 / 动态模块 / 跨构件 | 反射，运行时才报错 |

两条都要求目标实现是 **Spring Bean**（`@AppService` = `@Service` + `@Primary`）。

## 2. Version

同 `BASELINE.md`。

## 3. Input

```
interfaces.json        → 接口全名、方法签名、入参/返回 DTO
impl-map.json          → 接口 → 实现类（269 个）
service-flow-20261103/ → 实现类方法体调用链
```

## 4. Required

- 方式一：接口在编译期可见（`-facade` 或 `-biz` 依赖里有）
- 方式二：只要接口**全名**字符串 + 参数**类型全名**字符串

## 5. Execution

### 5.1 方式一：Spring 注入（推荐）

```java
@Autowired
private BpmAppService bpmAppService;

BpmSendDto dto = new BpmSendDto();
dto.setTemplateCode("xxx");
dto.setCurrentUserId(123L);

SingleResponse<BpmSendResultDto> r = bpmAppService.send(SingleRequest.from(dto));
BpmSendResultDto result = r.getData().getContent();
```

取值链固定：`response.getData().getContent()`。
构造固定：`SingleRequest.from(dto)`（静态工厂，不是 `new`）。

### 5.2 方式二：泛化调用

```java
AppServiceInvokeDto d = new AppServiceInvokeDto();
d.setInterfaceName("com.seeyon.bpm.api.common.BpmAppService");
d.setMethodName("send");
d.setParamType("com.seeyon.boot.transport.SingleRequest");     // 包装类型
d.setGenericType("com.seeyon.bpm.dto.operation.openapi.BpmSendDto");  // 泛型实参
d.setParamJson("{\"templateCode\":\"xxx\",\"currentUserId\":123}");
d.setReturnJson(Boolean.TRUE);                                  // 返回 JSON 字符串
SingleResponse<Object> r = appServiceProxy.invokeAppService(SingleRequest.from(d));
```

`AppServiceInvokeDto` 10 字段（逐字）：

| 字段 | 类型 | 作用 |
|---|---|---|
| `interfaceName` | String | 接口全名 |
| `methodName` | String | 方法名 |
| `paramType` | String | 参数类型全名（`SingleRequest` / `ListRequest`） |
| `genericType` | String | 泛型实参全名（入参 DTO） |
| `subGenericType` | String | 二级泛型（`List<List<X>>` 时用） |
| `paramJson` | String | `data` 的 JSON |
| `beanName` | String | 显式指定 Bean（同名多实现时） |
| `returnJson` | Boolean | true 时 content 变 JSON 字符串 |
| `bodyZip` | Boolean | 压缩大响应 |
| `serialVersionUID` | long | 别传 |

### 5.3 泛化调用怎么找到 Bean（6 层兜底）

反编译 `CtpCustomerProxyAppServiceImpl.processServiceInvoke` 实测顺序：

```
① getBean(接口名末段首字母小写)     BpmAppService → bpmAppService
② getBean(接口全名)
③ ModuleAppBeanCache.getBean(接口名)          动态模块
④ getBean(ModuleClassLoaderRepository 的动态 Bean 名)
⑤ getBean(dto.getBeanName())                  显式指定
⑥ getBeansOfType(loadClass(接口名))            按类型找，跳过含 mock 的
```

全找不到 → `throw new BusinessException("BOOT_4014")`，日志会打全
`interfaceName / methodName / paramType / genericType / subGenericType` 五个值。

调用前还会 `setBeanClassLoader(ModulesProxyClassLoader.getInstance())`，
所以**动态模块里的 Bean 也能找到**（`com.seeyon.dynamic` 开头的接口跳过 ①，直接 ②）。

## 6. Side Effects

- 方式一：走 Spring 代理，事务/权限注解正常生效
- 方式二：走 BeanFactory 直接取 Bean，**仍然是被代理的 Bean**（`AopTargetUtils.getTarget` 只用来换 ClassLoader），所以事务和切面同样生效
- `returnJson=true` 时返回的是 JSON **字符串**，不是对象，取到后要自己反序列化

## 7. Known Constraints

### 7.1 实现必须在容器里

`@AppService`（`com.seeyon.boot.annotation.AppService`）= `@Service` + `@Primary`。
biz 里的实现类同时带 `@DubboService`，但**泛化调用不走 Dubbo**，走本地 BeanFactory。

没有 `@AppService` 的类（普通 `domain/service/XxxService`）**不能**泛化调用——
它们不是 AppService Bean。要用只能注入。

### 7.2 命名不规则，别猜

`com.seeyon.bpm.api.common.BpmAppService` 的实现是 **`BpmApiAppServiceImpl`**，
不是 `BpmAppServiceImpl`。所以必须读 `impl-map.json`（字节码 implements 子句），
不能按 `XxxAppService → XxxAppServiceImpl` 推。

### 7.3 paramType 必须给包装类型

不能给 DTO 本身。`paramType` = `com.seeyon.boot.transport.SingleRequest`，
DTO 放 `genericType`。给错了会 `ClassUtils.getClass` 成功但反序列化失败。

### 7.4 同名接口多实现

`getBeansOfType` 那层会遍历所有实现，**跳过名字含 mock 的**，剩下的最后一个赢。
要精确指定用 `beanName`。

### 7.5 无实现的接口不能调

322 个 AppService 里 269 个有实现。剩下 53 个在 21 个 biz jar 里都没有实现类，
泛化调用会 BOOT_4014。

## 8. Evidence

```
反编译来源
  boot-starter-proxy/5.3.600
    com/seeyon/boot/starter/proxy/appservice/AppServiceProxyApiImpl.class
      → invokeAppService 转发给 CustomerProxyAppService
    com/seeyon/boot/starter/proxy/appservice/CtpCustomerProxyAppServiceImpl.class
      → processServiceInvoke(dto) 6 层 Bean 查找 + ClassUtils.getClass(paramType)
  boot-starter-dubbo/5.3.600
    com/seeyon/boot/starter/dubbo/dto/AppServiceInvokeDto.class   10 字段

注解证据
  javap -v bpm-biz-5.3.353.jar com.seeyon.bpm.appservice.BpmApiAppServiceImpl
    → @com.seeyon.boot.annotation.AppService(value="流程操作")
      @org.apache.dubbo.config.annotation.DubboService

映射
  docs/audit/artifacts/extension-surface-20261029/impl-map.json   269 接口
```

## 9. Verified

| 项 | 等级 |
|---|---|
| `AppServiceInvokeDto` 10 字段 | `VERIFIED_STATIC_BYTECODE` |
| `processServiceInvoke` 6 层 Bean 查找 | `VERIFIED_STATIC_BYTECODE`（cfr 反编译） |
| biz 实现带 `@AppService` + `@DubboService` | `VERIFIED_STATIC_BYTECODE`（javap -v） |
| 泛化调用实际跑通 | **UNVERIFIED**（无运行环境，只有静态证据） |
| `paramJson` 的 JSON 结构细节 | **UNVERIFIED**（`ClassUtils.getClass` 之后的反序列化分支未逐行读完） |
