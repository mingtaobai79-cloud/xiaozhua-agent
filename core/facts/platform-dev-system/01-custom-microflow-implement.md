# 01 · 自定义微流程：怎么实现、怎么被调用

## Capability

**你要写一个自定义微流程时 —— 改哪个类、签名怎么来、平台怎么找到你、怎么调别的服务。**

给 Agent 用：接到「写一个自定义微流程」需求时，照本格做，不需要理解生成器内部。

## Version

`udc-biz-5.3.605.jar` → `autocode/JAVA/2.9/templates/microflow/customflow/`（7 个 .ftl）

## 你只需要改一个接口

平台生成 7 个类，**只有 1 个是你写的**：

| 类 | 谁写 | 作用 |
|---|---|---|
| **`{App}CustomMicroFlowService`** | **← 你实现这个** | 你的业务逻辑 |
| `{App}CustomMicroFlowAppService` | 平台生成（接口） | 对外契约 |
| `Default{App}CustomMicroFlowAppServiceImpl` | 平台生成 | **调你的实现**（`required=false` 注入） |
| `CustomMicroFlow{Page}Controller` | 平台生成 | REST 入口 |
| `DefaultCustomMicroFlowConfig` | 平台生成 | Dubbo 导出 |
| `DefaultCustomMicroFlowBeanDefinitionRegistryPostProcessor` | 平台生成 | 你的实现生效后，**自动移除**默认实现 |
| `MicroFlowDubboExportBeanPostProcessor` | 平台生成 | Dubbo 导出工具 |

## 你实现的接口（真实模板）

```java
package com.seeyon.{app}.custom.service.microflow;

import com.seeyon.boot.transport.*;
import java.util.List;
import java.util.Map;

/**
 * 自定义微流程 AppService 接口
 */
public interface {App}CustomMicroFlowService {

    // 有分页时 —— 入参是整个 Request
    default {OutDto} {flowName}({Req}<{InDto}> request) {
        throw new UnsupportedOperationException(...);   // throwUnimplemented()
    }

    // 无分页时 —— 入参是裸 DTO
    default {OutDto} {flowName}({InDto} {inputName}) {
        throw new UnsupportedOperationException(...);
    }
}
```

**★★★★★ 三条关键（照抄即可）：**

| # | 事实 |
|---|---|
| 1 | **方法名 = 微流程名 uncap 首字母**（`CreateOrder` → `createOrder`） |
| 2 | **`default` 方法** —— 你不实现也能编译，运行时报「接口未实现」 |
| 3 | **有分页 → 入参 `{Req}<{InDto}>`；无分页 → 入参裸 `{InDto}`** |

**生成物是 `interface` + `default` 方法，不是抽象类。你写 `implements`，只覆盖你要的方法。**

## 平台怎么找到你的实现（决定性机制）

### `Default{App}CustomMicroFlowAppServiceImpl` 用 `required=false` 注入

```java
@AppService(value = "{defaultImplClassName}",
    customs = {
        @Custom(properties = @CustomAttribute(
            name = MicroFlowCommonConstant.APP_SERVICE_ANNOTATION_CUSTOM_KEY, value = "true")),
        @Custom(properties = @CustomAttribute(
            name = "{IS_DEFAULT_CUSTOM_MICRO_FLOW_APP_SERVICE_KEY}", value = "true"))
    })
public class {DefaultImpl} implements {AppService} {

    private {App}CustomMicroFlowService {service};

    @Autowired(required = false)                    // ★★★ 关键：找不到也不报错
    public void set{App}CustomMicroFlowService({App}CustomMicroFlowService {service}) {
        this.{service} = {service};
    }

    @Override
    @AppServiceOperation(value = "{流程caption}", returnValue = "{输出描述}",
        description = "{流程描述}",
        openApi = @OpenApi(isOpenApi = true),       // STOP → false
        customs = { ... })
    public SingleResponse<{OutDto}> {flowName}(
            @ParameterInfo("{输入描述}") SingleRequest<{InDto}> request) {

        if ({service} == null) {                     // ★ 你没实现时走这里
            throw new BusinessException(
                MicroFlowErrorCode.UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED);
        }

        // 有输出
        return SingleResponse.from({service}.{flowName}(request.getData()));

        // 无输出
        // {service}.{flowName}(request.getData());
        // return SingleResponse.ok();
    }
}
```

**★★★★★ 三层机制：**
1. **`@Autowired(required = false)`** —— 你不写实现，Spring 不报错，字段为 `null`
2. **`null` 时抛 `UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED`** —— 明确的错误码
3. **你写了实现 → 自动生效**，平台代码一行不用改

### 你实现后，平台自动移除默认实现

```java
// DefaultCustomMicroFlowBeanDefinitionRegistryPostProcessor
String[] beanNames = beanFactory.getBeanNamesForType({AppService}.class);
long distinctClassCount = Arrays.stream(beanNames)
        .map(beanFactory::getBeanDefinition)
        .map(BeanDefinition::getBeanClassName)
        .distinct().count();

if (distinctClassCount > 1 && ArrayUtils.contains(beanNames, "{defaultBeanName}")) {
    registry.removeBeanDefinition("{defaultBeanName}");     // ★ 移除默认实现
}
```

**⇒ 只要你的实现和默认实现同时存在（`distinctClassCount > 1`），默认实现被移除，你的生效。**

**★★ 这个是 `Ordered` 且 `getOrder() = Integer.MAX_VALUE` —— 最后执行，确保看到所有 Bean。**

## 方法签名怎么读（出入参 → Java）

平台按微流程配置生成签名，你照抄即可：

| 微流程配置 | 生成的方法签名 |
|---|---|
| 有输入（`hasPagination=false`） | `{OutDto} createOrder(OrderDto orderDto)` |
| 有输入 + 分页 | `{OutDto} createOrder(Request<OrderDto> request)` |
| 无输入 | `{OutDto} createOrder()` |
| 无输出 | `void createOrder(OrderDto orderDto)` |
| 输出是实体 | AppService 层返回 `SingleResponse<Map<String,?>>`（走 `DisplayNameAppService.toMapList`） |

**★★★ 命名细节（容易踩）：**
```
inputName     输入变量名（模板里 ${microFlowInOutParamBo.inputName}）
req           Request 包装类型（SingleRequest / PageRequest）
resp          Response 包装类型（SingleResponse / PageResponse）
```

## 怎么调平台其他服务（你能用的入口）

**你的实现类是普通 Spring Bean，直接 `@Autowired`：**

```java
@Service
public class {App}CustomMicroFlowServiceImpl implements {App}CustomMicroFlowService {

    // ① UDC 生成的 Service（同应用）
    @Autowired private OrderService orderService;

    // ② UDC 生成的 AppService（同应用）
    @Autowired private OrderAppService orderAppService;

    // ③ 标品服务（Dubbo）
    @DubboReference private OrgCommonAppService orgCommonAppService;

    // ④ 平台组件 Service
    @Autowired private CtpEnumItemService ctpEnumItemService;

    // ⑤ 工具类（静态）
    // JsonUtils / StringUtils / DateUtils / BeanCopier ...

    @Override
    public OrderDto createOrder(OrderDto orderDto) {
        // 你生成的 Service —— 直接用
        orderService.create(orderDto);

        // 标品 —— 包 Request/Response
        SingleResponse<Xxx> resp = orgCommonAppService.query(
            SingleRequest.from(param));
        Xxx data = resp.getData().getContent();

        return orderDto;
    }
}
```

**★★★★★ 四类可注入（按可控性排序）：**

| # | 类型 | 注解 | 来源 |
|---|---|---|---|
| 1 | **UDC 生成的 `{E}Service`** | `@Autowired` | 同应用（见 `02-udc-generated-reference.md`） |
| 2 | **UDC 生成的 `{E}AppService`** | `@Autowired` | 同应用 |
| 3 | **标品 AppService** | `@DubboReference` | 跨进程（org/bpm/affair/message/connector） |
| 4 | **平台组件 Service** | `@Autowired` | 同 JVM（enum/file/cache/excel/i18n/metadata） |

**★★ 第 5 类工具类静态调用**（`JsonUtils` / `HttpClientUtil` / `AES` 等，`boot-core` 177 类）—— 无状态，直接 `类名.方法`。

## 完整走一遍（最小可用）

**步骤 1**：平台已生成接口（你不动）
```java
public interface OrderCustomMicroFlowService {
    default OrderDto createOrder(OrderDto orderDto) { throw ...; }
}
```

**步骤 2**：你写实现（**这是唯一要写的**）
```java
package com.seeyon.zzprobe.custom.service.microflow;

@Service
public class OrderCustomMicroFlowServiceImpl implements OrderCustomMicroFlowService {

    @Autowired private OrderService orderService;

    @Override
    public OrderDto createOrder(OrderDto orderDto) {
        orderService.create(orderDto);
        return orderDto;
    }
}
```

**步骤 3**：什么配置都不用改 —— `required=false` 注入 + 后处理器自动移除默认实现。

## Side Effects

你的类被 Spring 扫描到后：
1. `set{App}CustomMicroFlowService` 被调用，`{service}` 不再为 `null`
2. 后处理器移除 `defaultBeanName`
3. 调 REST / GraphQL / Dubbo 时走你的逻辑

## Known Constraints

| # | 约束 |
|---|---|
| 1 | **只实现 `{App}CustomMicroFlowService` 接口，别动另外 6 个类** |
| 2 | **方法名必须与微流程名 uncap 后完全一致** |
| 3 | **有分页时入参是整个 `Request<Dto>`，不是裸 DTO** |
| 4 | **不实现也能编译**（`default` 方法），但运行时报 `UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED` |
| 5 | **`openApi=STOP` 时生成 `@OpenApi(isOpenApi=false)`** —— 不对外暴露 |
| 6 | **输出是实体时 AppService 层返回 `Map<String,?>`**（走 `DisplayNameAppService` 转换） |
| 7 | **别自己加 `@AppService` 到实现类** —— 平台已注册，你只是被注入 |
| 8 | **`MicroFlowErrorCode.UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED` 是「没写实现」的唯一错误码** |

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| 7 个模板全文 | `autocode/JAVA/2.9/templates/microflow/customflow/*.ftl` 逐行读完 | STATIC_RULE |
| 接口生成规则（分页/无分页） | `CustomMicroFlowService.java.ftl` 的 `<#if hasPagination>` | STATIC_RULE |
| `required=false` 注入 | `DefaultCustomMicroFlowAppServiceImpl.java.ftl` 第 38 行 | STATIC_RULE |
| `null` 时抛错误码 | 同模板 `if({service} == null) throw new BusinessException(...)` | STATIC_RULE |
| 默认实现移除逻辑 | `DefaultCustomMicroFlowBeanDefinitionRegistryPostProcessor.java.ftl` | STATIC_RULE |
| `getOrder() = Integer.MAX_VALUE` | 同模板末尾 | STATIC_RULE |
| Dubbo 导出 | `DefaultCustomMicroFlowConfig.java.ftl` + `MicroFlowDubboExportBeanPostProcessor.java.ftl` | STATIC_RULE |

## Verified

- ✅ **STATIC_RULE**：7 个模板全部逐行读完（987 B / 1313 B / 3924 B / 9147 B / 2646 B / 2282 B / 596 B）
- ⚠️ **未验证**：真实工程里生成出来的完整类（需容器跑一次 generate）
- ⚠️ **未验证**：`{App}CustomMicroFlowService` 的 bean 名规则（我按 `{App}CustomMicroFlowServiceImpl` 推断，未见约束）

## 给 Agent 的判据

```
接到「写自定义微流程」
  ① 找接口 {App}CustomMicroFlowService
  ② 照签名写 implements，只覆盖要用的方法
  ③ 需要什么服务就 @Autowired / @DubboReference
  ④ 不改任何配置

问「为什么不实现也能跑起来」
  → default 方法 + required=false 注入 + null 时抛 NOT_IMPLEMENTED

问「我实现了但没生效」
  → 查类是否 implements 了那个接口；后处理器按 distinctClassCount>1 移除默认实现

问「入参为什么是 Request<Dto> 不是 Dto」
  → 微流程配了分页（hasPagination=true）

问「能调标品吗」
  → 能，@DubboReference
```