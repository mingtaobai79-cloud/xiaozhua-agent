# 06 · 监听更新前事件改数据：可直接抄的代码

## Capability

**回答「我要监听更新前事件改数据，注解怎么标、类怎么写、改哪个字段会生效」。**

给 Agent 用：这是 `transaction-beforeupdate-semantics.md`（第 7 格）的**代码落地版**。
第 7 格讲「为什么能生效」；本格讲「代码长什么样」。

**一句话：类上 `@EventHandler`，方法上 `@EventSubscribe`，方法参数收 `BeforeUpdateEvent<T>`，
   改 `event.getInfo()` 的字段 —— 不用再调 update。**

## Version

| 构件 | jar | 证据 |
|---|---|---|
| `@EventHandler` / `@EventSubscribe` | `boot-starter-eventbus-5.3.600.jar` | `javap -v` 注解定义 |
| `SubscriberRegistry` 匹配逻辑 | 同上 | `javap -p -c` |
| `BeforeUpdateEvent` / `BeforeUpdateBatchEvent` | `udc-common` | `javap -p` |
| 真实订阅方 | `udcrt` / `udc` jar 内的 Listener | `javap -v` 实测 |

---

## 一、★★★★★ 两条铁律（缺一不可）

```
① 类上必须有 @EventHandler        ← 它等于 @Component，负责被 Spring 扫到
② 方法上必须有 @EventSubscribe    ← 它无参数，负责把方法登记为订阅者
```

**只有 ①** → 被 Spring 管理，但不会订阅任何事件。
**只有 ②** → 方法标了注解，但类不在容器里，订阅永远不会被注册。

**验证依据**：
- `@EventHandler` 的 `RuntimeVisibleAnnotations` 里有 `org.springframework.stereotype.Component`（常量池 #15），`@Target(TYPE)`
- `@EventSubscribe` 的 `RuntimeVisibleAnnotations` 是 `#162()` —— **空属性**，不带事件类名
- 真实订阅方 `ApprovalStateChangeListener` 类级 `#215 = @EventHandler`，方法级 `@EventSubscribe()` 空

---

## 二、怎么匹配到事件：靠方法参数类型，不靠注解参数

`SubscriberRegistry.getSubscribers(Object event)`：

```
  1: event.getClass()
  4: flattenHierarchy(Class)        ← 取「类自身 + 父类 + 所有接口」
 46: subscribers.get(clazz.getName())← 按【类名】查
```

**⇒ 三件事：**

| # | 事实 |
|---|---|
| 1 | **订阅 key 是「事件类的全限定名」，不是泛型参数** |
| 2 | **`flattenHierarchy` 会展开父类与接口** —— 监听父类型也能收到子类型事件 |
| 3 | **所以 `BeforeUpdateEvent<OrderDto>` 和 `BeforeUpdateEvent<?>` 都能收到 `BeforeUpdateEvent<OrderDto>`** |

**★ 但要注意第 2 条的反面**：如果你写 `@EventSubscribe void on(Object event)`，你会收到**所有**事件 ——
平台里几百种事件全进你的方法。**不要图省事写 `Object`。**

---

## 三、最小可用代码（★ 直接抄）

### 3.1 监听单条更新前事件

```java
package com.seeyon.zzprobe.custom.listener;

import com.seeyon.boot.starter.eventbus.annotation.EventHandler;
import com.seeyon.boot.starter.eventbus.annotation.EventSubscribe;
import com.seeyon.udc.common.event.BeforeUpdateEvent;
import com.seeyon.zzprobe.dto.OrderDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

// ★ 类上必须 @EventHandler（= @Component）
@EventHandler
public class OrderBeforeUpdateListener {

    private static final Logger log = LoggerFactory.getLogger(OrderBeforeUpdateListener.class);

    // ★ 方法上必须 @EventSubscribe（无参数）
    // ★ 参数类型决定订阅哪个事件
    @EventSubscribe
    public void onBeforeUpdate(BeforeUpdateEvent<OrderDto> event) {

        // ★ getInfo() = current = 请求 DTO 本身（改它落库）
        OrderDto dto = event.getInfo();

        // ★ getOldInfo() = previous = 库里旧值（改它不落库，只用来比对）
        OrderDto old = event.getOldInfo();

        if (dto == null) return;

        // 你的业务逻辑
        if (old != null && !old.getStatus().equals(dto.getStatus())) {
            log.info("订单 {} 状态 {} -> {}", dto.getOrderNo(), old.getStatus(), dto.getStatus());
        }

        // ★ 直接改 dto 字段 = 改待落库数据，不用再 update
        dto.setAuditRemark("系统自动标记");
    }
}
```

### 3.2 监听批量更新前事件（一次改多条）

```java
import com.seeyon.udc.common.event.BeforeUpdateBatchEvent;
import com.seeyon.udc.common.event.ChangeEventData;

@EventHandler
public class OrderBeforeUpdateBatchListener {

    @EventSubscribe
    public void onBeforeUpdateBatch(BeforeUpdateBatchEvent<OrderDto> event) {

        // ★ getEventData() 返回 Collection<ChangeEventData<OrderDto>>
        Collection<ChangeEventData<OrderDto>> changes = event.getEventData();
        if (changes == null) return;

        for (ChangeEventData<OrderDto> cd : changes) {
            OrderDto current  = cd.getCurrent();    // 更新后（改它落库）
            OrderDto previous = cd.getPrevious();   // 更新前（改它不落库）

            if (current != null) {
                current.setAuditRemark("批量处理");
            }
        }
    }
}
```

**★★★ 单条和批量都会发 —— 两个都挂会执行两次。选一个。**
（`EntityEventHelper.beforeEvent` case2 先逐个 publish 单事件，再 publish batch）

---

## 四、★ 更早、更省事的钩子：覆写 `preUpdateBatch`

如果你自己的实体（能改 `{E}Service` 源码），**不要挂事件，直接覆写钩子**：

```java
package com.seeyon.zzprobe.domain.service;

import com.seeyon.boot.starter.lowcode.service.BaseEntityCurdService;
import com.seeyon.zzprobe.dto.OrderDto;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class OrderService extends BaseEntityCurdService<OrderDto> implements PreUpdateCallBack<OrderDto> {

    // ★ 偏移 458 —— merge 补全之后、事件发出之前、写库之前
    @Override
    public void preUpdateBatch(List<OrderDto> dtoList) {
        if (dtoList == null) return;
        for (OrderDto dto : dtoList) {
            // dto 此时已是「合并后的完整对象」
            dto.setAuditRemark("钩子里设的");
        }
    }
}
```

**四条对比：**

| 方式 | 时机 | 能改吗 | 适合 |
|---|---|---|---|
| `preUpdateBatch` | **最早（458）** | ✅ | **能改实体源码时，首选** |
| `@EventSubscribe` 单条 | 582 之前 | ✅ | 不能改源码 / 跨实体 |
| `@EventSubscribe` 批量 | 582 之前 | ✅ | 同上，批量场景 |
| `selectListByConditions` 后自己 update | 最晚 | ✅ | 不推荐（二次写、重复链路） |

**⇒ 判断顺序：能改 `{E}Service` → 用 `preUpdateBatch`；不能 → 用 `@EventSubscribe`。**

---

## 五、★★★★★ 改哪个字段会生效（三条死规则）

### 规则 1：只改 `getInfo()`，不碰 `getOldInfo()`

```
写库源 = aload_1 = 请求 DTO 本身
事件 current = 同一个 aload_1 引用
事件 previous = oldDto（只做比对和留痕，从不进写库路径）
```

**⇒ 改 `getOldInfo()` 里对象的字段，库里的值不会变。这是个静默失败。**

### 规则 2：你改的字段必须在 `__updatedFields` 里，否则会被 merge 覆盖

`mergeMapData` 的 `copyValueIfTargetFieldIsNull` 过滤规则：

| 字段情况 | merge 行为 |
|---|---|
| 字段名 = `version` | **一定回填**（乐观锁） |
| 在 `__updatedFields` 里 | **不回填**，保留你的值 ✅ |
| 在 `__emptyFields` 里 | **不回填**，保留 null |
| 其它 + 请求值为 null | **回填库里旧值** ⚠️ 你的改动会被覆盖 |

**⇒ 你要改的字段，要么在请求的 `__updatedFields` 里，要么在 `preUpdateBatch` 里改（那个时机 merge 已完成）。**

### 规则 3：改完不要再调 `update`

会二次写库、触发第二次完整链路（含第二次 `preUpdateBatch` → 可能死循环）。

---

## 六、子表（明细）能改吗

```java
@EventSubscribe
public void onBeforeUpdate(BeforeUpdateEvent<OrderDto> event) {
    OrderDto dto = event.getInfo();
    // ★ 子表在 DTO 的 List 字段里，跟着主表一起递归落库
    if (dto.getOrderDetailDtoList() != null) {
        dto.getOrderDetailDtoList().forEach(d -> d.setRemark("子表也改了"));
    }
}
```

**约束**：
- **只有 `isMasterEntity = true` 才发事件**（偏移 517），子实体容器为 null
- 但 `recursiveUpdate`（偏移 741）在写库（768）**之前** —— 改子表 DTO 仍会落库

---

## 七、完整可用的"审计字段"例子

**需求**：所有订单更新时，自动记「谁在什么时候改的」。

```java
package com.seeyon.zzprobe.custom.listener;

import com.seeyon.boot.starter.eventbus.annotation.EventHandler;
import com.seeyon.boot.starter.eventbus.annotation.EventSubscribe;
import com.seeyon.udc.common.event.BeforeUpdateEvent;
import com.seeyon.zzprobe.dto.OrderDto;
import com.seeyon.boot.starter.systemvariable.util.SystemVariableUtils;
import java.util.Date;

@EventHandler
public class OrderAuditListener {

    @EventSubscribe
    public void onBeforeUpdate(BeforeUpdateEvent<OrderDto> event) {

        OrderDto dto = event.getInfo();
        OrderDto old = event.getOldInfo();
        if (dto == null) return;

        // 记审计
        dto.setLastModifiedTime(new Date());
        dto.setLastModifiedBy(currentUserId());

        // 状态变化留痕
        if (old != null && !java.util.Objects.equals(old.getStatus(), dto.getStatus())) {
            dto.setStatusChangeLog(
                (dto.getStatusChangeLog() == null ? "" : dto.getStatusChangeLog())
                + old.getStatus() + "->" + dto.getStatus() + ";");
        }
        // ★ 到此结束，不要再 orderService.update(dto)
    }

    private Long currentUserId() {
        // ★ 平台真实 API（已核对字节码，不是 ContextUtil）
        return com.seeyon.boot.starter.systemvariable.util.SystemVariableUtils.currentUserId();
    }
}
```

---

## 八、Side Effects

| 写法 | 是否会落库 | 时机 |
|---|---|---|
| `@EventSubscribe` 单条事件里改 `getInfo()` | **会** | 写库（768）之前 |
| `@EventSubscribe` 批量事件里改 `cd.getCurrent()` | **会**（同批引用） | 同上 |
| 改 `getOldInfo()` / `cd.getPrevious()` | **不会** | —— |
| 覆写 `preUpdateBatch` | **会** | 最早（458） |
| `afterUpdate` / After 事件里改 | **不会**（已落库） | —— |

---

## 九、Known Constraints

| # | 约束 |
|---|---|
| 1 | **类上 `@EventHandler` 和方法上 `@EventSubscribe` 缺一不可** |
| 2 | **`@EventSubscribe` 不带参数** —— 订阅靠方法参数类型 |
| 3 | **不要写 `Object` 作参数** —— 会收到所有事件 |
| 4 | **单条和批量事件都会发** —— 两个都挂会执行两次，选一个 |
| 5 | **改 `getOldInfo()` 不落库** —— 静默失败，最难查 |
| 6 | **改完不要再调 `update`** —— 二次写 + 可能死循环 |
| 7 | **改的字段必须在 `__updatedFields` 里**，否则被 merge 覆盖；用 `preUpdateBatch` 可绕过 |
| 8 | **`updateNoEvents` 完全不发事件** —— 挂监听器的改不到 |
| 9 | **只有 `isMasterEntity = true` 才发事件** —— 子实体容器为 null |
| 10 | **`flattenHierarchy` 会展开父类和接口** —— 监听父类型也会收到子类型事件 |

---

## 十、Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `@EventHandler` = `@Component`，`@Target(TYPE)` | `javap -v EventHandler`：常量池 #15 `Lorg/springframework/stereotype/Component;`，Retention/Retarget | **VERIFIED_STATIC_BYTECODE** |
| `@EventSubscribe` 只有 `threadModel()` / `order()`，无 `value()` | `javap -v EventSubscribe`：`#162()` 空属性 | **VERIFIED_STATIC_BYTECODE** |
| 真实用法：类 `@EventHandler` + 方法 `@EventSubscribe` | `javap -v ApprovalStateChangeListener`：类级 `#215 @EventHandler`，`onBillUpdate` 上 `RuntimeVisibleAnnotations: 0: #162() EventSubscribe` | **VERIFIED_STATIC_BYTECODE** |
| 匹配靠类名不靠泛型 | `javap -p -c SubscriberRegistry.getSubscribers`：`event.getClass()` → `flattenHierarchy` → `subscribers.get(clazz.getName())` | **VERIFIED_STATIC_BYTECODE** |
| `flattenHierarchy` 展开父类+接口 | 同上方法调用链 | **VERIFIED_STATIC_BYTECODE** |
| `BeforeUpdateEvent(T info, T oldInfo)` / `getInfo` / `getOldInfo` | `javap -p` | **VERIFIED_STATIC_BYTECODE** |
| `BeforeUpdateBatchEvent.getEventData()` → `Collection<ChangeEventData<T>>` | `javap -p` | **VERIFIED_STATIC_BYTECODE** |
| 改 `getInfo()` 会落库 | 第 7 格字节偏移 385/506/768 | **VERIFIED_STATIC_BYTECODE** |
| 真实运行效果 | 未实测 | **UNVERIFIED** |

---

## 十一、Verified

- ✅ **VERIFIED_STATIC_BYTECODE**：注解定义、真实用法、订阅匹配逻辑、事件类结构、落库链路（全部 javap 逐条核对）
- ⚠️ **UNVERIFIED**：上面代码在真实工程里跑一遍，看库里值是否变（需 LIVE 环境）
- ✅ **VERIFIED_STATIC_BYTECODE**：当前用户 API 是 `SystemVariableUtils.currentUserId()`（最初写错成 `ContextUtil`，已按字节码更正）
- ⚠️ **UNVERIFIED**：上面代码在真实工程里跑一遍（需 LIVE 环境）

### 10.1 当前用户 / 系统上下文 API（真实全表）

```java
import com.seeyon.boot.starter.systemvariable.util.SystemVariableUtils;

Long   userId = SystemVariableUtils.currentUserId();          // 当前人员 id
String name   = SystemVariableUtils.currentUserName();        // 姓名
String code   = SystemVariableUtils.currentUserCode();        // 编码
String login  = SystemVariableUtils.currentUserLoginName();   // 登录名
String type   = SystemVariableUtils.currentUserType();        // 类型
```

**★ 不是 `ContextUtil` / `UserContext` —— 平台里没有这两个类。**

---

## 十二、给 Agent 的判据

```
问「我要监听更新前事件改数据，注解怎么写」
  → 类上 @EventHandler（= @Component），方法上 @EventSubscribe（无参数）
  → 只标一个不生效：只有 Handler 不订阅，只有 Subscribe 不被 Spring 扫到

问「方法参数写什么」
  → BeforeUpdateEvent<{E}Dto>
  → 匹配靠参数类型的【类名】，泛型写 <?> 也能收到
  → 千万别写 Object（会收到所有事件）

问「改哪个入参生效」
  → getInfo()（= current = 请求 DTO）。改它落库
  → getOldInfo()（= previous = 库值）改它不落库 ← 静默失败

问「单条和批量选哪个」
  → 两个事件都会发，都挂会执行两次。选一个
  → 能改实体源码时，别挂事件，直接覆写 preUpdateBatch（更早、更省事）

问「改了要不要再 update」
  → 不要。会二次写库 + 可能死循环

问「我改的字段没生效」
  → 三条排查：
     ① 是不是改了 getOldInfo()？
     ② 字段在 __updatedFields 里吗？不在会被 merge 回填覆盖
     ③ 是不是挂了 updateNoEvents？那条路不发事件

问「子表明细能改吗」
  → 能。改主表 DTO 里的 List，recursiveUpdate(741) 在写库(768)之前
  → 但只有 isMasterEntity=true 才发事件

问「有没有示例代码」
  → 见本格 §三（最小可用）、§七（审计字段完整例）
```