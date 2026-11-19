# 02 · 引用 UDC 生成的东西：包路径与调用方式

## Capability

**你在自定义微流程（或其他扩展代码）里，怎么引用 UDC 生成的 Service / DTO / Dao / AppService。**

给 Agent 用：写 `@Autowired` 之前先查本格，别猜包名、别猜类名。

## Version

- 包路径由 `Type` 枚举决定（`udc-biz-5.3.605.jar` → `com.seeyon.udc.entity.stereotype.generator.Type`）
- 类名规则由 `37-generated-artifacts-anatomy.md`（LIVE 产物）实证

## 生成物的真实包路径（权威）

| 产物 | 包 | 类名 | 模块 |
|---|---|---|---|
| `{E}AppService`（接口） | `{appPackagePath}.api` | `OrderAppService` | **facade** |
| `{E}Dto` | `{appPackagePath}.dto` | `OrderDto` | **facade** |
| `{E}AppServiceImpl` | `{appPackagePath}.appservice` | `OrderAppServiceImpl` | biz |
| `{E}`（实体） | `{appPackagePath}.domain.entity` | `Order` | biz |
| `{E}Service` | `{appPackagePath}.domain.service` | `OrderService` | biz |
| `{E}Dao` | `{appPackagePath}.domain.dao` | `{appPackagePath}OrderDao` ★ 带应用名前缀 | biz |
| `{E}Event` | `{appPackagePath}.domain.event` | `OrderEvent` | biz |
| `{E}Listener` | `{appPackagePath}.domain.event.listener` | `OrderListener` | biz |
| `{E}Controller` | `{appPackagePath}.controller` | `OrderController`（实际 `Abstract{E}Controller`） | web |

**★★★★★ 三条关键：**
1. **`{appPackagePath}` 是应用根包**（如 `com.seeyon.zzprobe` / `com.example.demo`）
2. **Dao 类名带应用名前缀**：`DemoOrderDao` 不是 `OrderDao` —— 因为 Dao 是 `{appNamePackage}{EntityName}Dao`
3. **AppService 和 Dto 在 `facade` 模块**，其余在 `biz` —— 跨模块引用的分界线

## 怎么注入（四种，按可控性排序）

```java
@Service
public class OrderCustomMicroFlowServiceImpl implements OrderCustomMicroFlowService {

    // ① UDC 生成的 Service —— 业务逻辑，最常用
    @Autowired private OrderService orderService;

    // ② UDC 生成的 AppService 接口 —— 走平台分发（有 AOP/事务/日志）
    @Autowired private OrderAppService orderAppService;

    // ③ 标品服务（跨进程）
    @DubboReference private OrgCommonAppService orgCommonAppService;

    // ④ 平台组件 Service（同 JVM）
    @Autowired private CtpEnumItemService ctpEnumItemService;
}
```

**★★★★★ 选哪个：**

| 场景 | 用哪个 | 为什么 |
|---|---|---|
| 本应用业务逻辑 | **`{E}Service`** | 直接调，无包装 |
| 需要平台 AOP / 事务 / 幂等 / 日志 | **`{E}AppService`** | `@AppService` 带 `@Service + @Primary` |
| 组织 / 流程 / 事项 / 消息 / 连接器 | **`@DubboReference` + 标品 AppService** | 跨进程 |
| 枚举 / 文件 / 缓存 / Excel / i18n / 元数据 | `@Autowired` + 组件 Service | 同 JVM Bean |

## 调用写法（Request/Response 必须包）

```java
// ① Service —— 直接传 DTO
OrderDto result = orderService.create(orderDto);

// ② AppService —— 必须包 SingleRequest
SingleResponse<OrderDto> resp = orderAppService.create(SingleRequest.from(orderDto));
OrderDto data = resp.getData().getContent();       // ★ 两层取值

// ③ Dubbo 标品 —— 同样包 SingleRequest
SingleResponse<XxxDto> r = orgCommonAppService.query(SingleRequest.from(param));
XxxDto d = r.getData().getContent();

// ④ 列表 —— ListRequest / PageRequest
ListResponse<OrderDto> list = orderAppService.selectList(ListRequest.from(queryMap, sort));
PageResponse<OrderDto> page = orderAppService.selectPage(
    PageRequest.from(pageInfo, queryMap));
```

**★★★★★ 四条铁律：**

| # | 铁律 |
|---|---|
| 1 | **AppService 入参必须 `SingleRequest.from(dto)` / `ListRequest.from(map, sort)` / `PageRequest.from(pageInfo, map)`** |
| 2 | **取值必须两层：`resp.getData().getContent()`** —— 不是 `resp.getData()` |
| 3 | **`ListRequest.from(map, sort)` 的 `sort` 只收平台 `com.seeyon.boot.transport.Sort`**，不是 MyBatis 的 `Sort` |
| 4 | **`{E}Service` 不需要包装** —— 直接传 DTO |

## 完整可编译示例

```java
package com.seeyon.zzprobe.custom.service.microflow;

import com.seeyon.zzprobe.domain.service.OrderService;
import com.seeyon.zzprobe.api.OrderAppService;
import com.seeyon.zzprobe.dto.OrderDto;
import com.seeyon.boot.transport.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.apache.dubbo.config.annotation.DubboReference;

@Service
public class OrderCustomMicroFlowServiceImpl implements OrderCustomMicroFlowService {

    @Autowired private OrderService orderService;          // 本应用业务
    @Autowired private OrderAppService orderAppService;    // 本应用契约
    @DubboReference private OrgCommonAppService orgCommonAppService;  // 标品

    @Override
    public OrderDto createOrder(OrderDto orderDto) {

        // ① 走生成 Service（直接传 DTO）
        orderService.create(orderDto);

        // ② 查单（走 AppService，包 Request）
        SingleResponse<OrderDto> resp = orderAppService.selectById(
            SingleRequest.from(orderDto.getId()));
        OrderDto loaded = resp.getData().getContent();

        // ③ 查组织（标品 Dubbo）
        // SingleResponse<Xxx> r = orgCommonAppService.query(SingleRequest.from(p));

        return loaded;
    }
}
```

## 生成物的类名/变量名规则（实证）

| 目标 | 规则 | 例子 |
|---|---|---|
| 实体 | `{Cap}{entityName}` | `Order` |
| DTO | `{Cap}{entityName}Dto` | `OrderDto` |
| AppService | `{Cap}{entityName}AppService` | `OrderAppService` |
| Service | `{Cap}{entityName}Service` | `OrderService` |
| Dao | `{appNamePackage}{Cap}{entityName}Dao` | `DemoOrderDao` ★ |
| 子表 DTO 列表变量 | `{uncap}{childName}DtoList` | `orderDetailDtoList` |
| 子表 getter | `get{Cap}{childName}DtoList` | `getOrderDetailDtoList` |

**★★★ `Dao` 是唯一带应用名前缀的产物 —— 因为多应用可能有同名实体，靠前缀隔离。**

## 子表（主子表）怎么访问

```java
OrderDto order = ...;
List<OrderDetailDto> details = order.getOrderDetailDtoList();   // 子表 DTO 列表
```

**⇒ 主子表在 DTO 层**展开成**列表字段**（`{child}DtoList`），不是嵌套对象。**

## 跨应用引用（依赖别的 UDC 应用）

**`pom.xml` 里加依赖：**

```xml
<dependency>
    <groupId>{对方的 groupId}</groupId>
    <artifactId>{对方 appName}-facade</artifactId>    <!-- 普通：只引契约 -->
    <version>{版本}</version>
</dependency>

<!-- 若对方是 dynamicService=true 才需要 biz -->
<dependency>
    <groupId>{对方 groupId}</groupId>
    <artifactId>{对方 appName}-biz</artifactId>
</dependency>
```

**代码里注入对方的 AppService：**

```java
@Autowired private TheirOrderAppService theirOrderAppService;   // 跨应用走接口
```

**★★★ 三条约束：**
1. **普通依赖只引 `-facade`** —— biz 不进你的 classpath
2. **`dynamicService=true` 才引 `-biz`** —— 这是「调服务」与「只调契约」的分界
3. **跨应用实体不参与特性注入**（`isOutter` 判定）—— 对方的 Service 已被生成好，你只调

## Side Effects

无（本格只讲引用方式）。

## Known Constraints

| # | 约束 |
|---|---|
| 1 | **Dao 类名带应用名前缀**（`DemoOrderDao`），不是 `OrderDao` |
| 2 | **AppService 必须包 `SingleRequest/ListRequest/PageRequest`** |
| 3 | **取值两层：`getData().getContent()`** |
| 4 | **`ListRequest.from` 的 sort 是 `com.seeyon.boot.transport.Sort`** |
| 5 | **`{E}Service` 直接传 DTO，不包装** |
| 6 | **`{E}Service` 是具体类不是 Impl**（`OrderService` 不是 `OrderServiceImpl`） |
| 7 | **子表是 DTO 列表字段**（`{child}DtoList`），不是嵌套对象 |
| 8 | **跨应用普通依赖只引 `-facade`** |

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| 9 个包路径 | CFR 反编译 `Type` 枚举，逐个 `classPackage` 字段 | **VERIFIED_STATIC_BYTECODE** |
| Dao 真实类名 `DemoOrderDao` | `rendered_go/` 真实渲染产物原文 | **LIVE** |
| Dao 包 `com.example.demo.domain.dao` | 同产物 `package` 行 | **LIVE** |
| 命名规则表 | `37-generated-artifacts-anatomy.md` §六（LIVE 产物实证） | **LIVE** |
| `SingleRequest.from` / 两层取值 | `standard-product/transport-usage.md`（独立事实格） | **VERIFIED_STATIC_BYTECODE** |
| 跨应用依赖粒度 | `01-project-skeleton.md` 的 pom 模板 `<#if dynamicService>` | **STATIC_RULE** |

## Verified

- ✅ **LIVE**：`rendered_go/` 真实产物确认 Dao 包路径与类名
- ✅ **VERIFIED_STATIC_BYTECODE**：`Type` 枚举 9 个包路径
- ⚠️ **未验证**：`{E}Service` 的真实渲染产物头部（本次未单独渲染该模板）
- ⚠️ **未验证**：`dynamicService` 的实际判定逻辑（模板里有分支，未见 DTO 定义）

## 给 Agent 的判据

```
问「怎么调 UDC 生成的业务逻辑」
  → @Autowired {E}Service，直接传 DTO

问「怎么调 UDC 的 AppService」
  → @Autowired {E}AppService，入参 SingleRequest.from(dto)，
    取值 resp.getData().getContent()

问「Dao 叫什么」
  → {appNamePackage}{EntityName}Dao（带应用名前缀，如 DemoOrderDao）

问「主子表怎么拿子表」
  → dto.get{Child}DtoList()

问「能用别的 UDC 应用吗」
  → 加 -facade 依赖 + @Autowired 对方 AppService

问「为什么 getData() 拿到的是包装体」
  → 必须 getData().getContent() 两层
```