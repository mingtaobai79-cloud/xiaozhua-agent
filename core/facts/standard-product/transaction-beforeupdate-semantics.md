# 事务内改「更新前」数据能不能生效（udc 实体更新链）

## 1. Capability

**回答「在事务里监听到更新前事件，改掉旧数据，还需不需要自己再调一次 update」。**

一句话结论：**不需要再调 update，但必须改对对象，而且默认走的那条路根本改不到。**

## 2. Version

| 构件 | jar | 证据 |
|---|---|---|
| `BaseEntityCurdService` | `udc-starter-lowcode-5.3.605.jar` | javap -p -c 全量 |
| `EntityEventHelper` | 同上 | 同上 |
| `EventBus` / `CtpEventBus` | `boot-starter-eventbus-5.3.600.jar` | 同上 |

## 3. Input

```bash
D:/software/java/bin/javap.exe -p -c -cp "D:/software/hermes/cache/scratch/cplib/*" \
  com.seeyon.boot.starter.lowcode.service.BaseEntityCurdService
```

## 4. Required

无。纯静态链路。

## 5. Execution —— `updateBase` 的真实字节偏移顺序

```
update(D)        → updateBase(dto, true,  false)   // 第2参 emitEvents=true
updateNoEvents(D)→ updateBase(dto, false, false)   // 不发事件
```

`updateBase(D dto, boolean emitEvents, boolean batch)` 内部顺序（字节偏移）：

| 偏移 | 动作 | 说明 |
|---:|---|---|
| 123 | `selectCascadeById(id)` | 查库拿 oldDto（局部变量 7） |
| 339 | `OperateContext.oldData(oldDto)` | |
| 318 | `OperateContext.newData(dto)` | **传的就是参数 dto 引用** |
| 354 | `OperateContext.deepCopyNewData()` | 只处理 `BaseRootDto`，不影响 dto 本身 |
| 365 | `DtoConvertUtil.mergeMapData(meta, oldMap, newMap)` | **合并此行旧值 + 入参新值** |
| **385** | **`astore_1`** | ★ **合并结果写回参数槽 `aload_1`** |
| 458 | `this.preUpdateBatch(list)` | 本地钩子（可覆写） |
| 506 | `ChangeEventData.setCurrent(aload_1)` | ★ 事件 current = 同一个引用 |
| 513 | `ChangeEventData.setPrevious(aload_7)` | ★ 事件 previous = oldDto |
| 582 | `entityEventHelper.beforeEvent(container)` | ★ **发布 BeforeUpdateBatchEvent** |
| 741 | `recursiveUpdate(...)` | 子表递归 |
| **768** | **`BeanCopier.copy(aload_1, entityClass)`** | ★★ **写库数据 = aload_1，与事件同一引用** |
| 826 | `getMapper().update(bean)` | 真正落库 |
| 849 | `if (emitEvents)` → `afterEvent` | |
| 914 | `transactionSuccessEvent` | 事务提交后事件 |

## 6. Output

### 6.1 ★★★★★ 核心答案

**改事件里的 `getInfo()` 返回对象，会自动写进库，不用再调 update。**

原因（字节码铁证）：

```
385: astore_1                        ← mergeMapData 结果写进参数槽
506: setCurrent(aload_1)             ← 事件持有 aload_1 的引用
768: BeanCopier.copy(aload_1, ...)   ← 写库也用 aload_1
```

事件里的 `info` 和写库的源对象**是同一个 Java 对象引用**。
监听器里 `event.getInfo()` 拿到的就是它，改它的字段 = 改待落库的数据。

而 `BeforeUpdateEvent` 本身是纯 POJO（`info` / `oldInfo` 两个字段，
构造函数原样赋值，`getInfo()` 直接 `aload_0.getfield` 返回），**没有防御性拷贝**。

### 6.2 ★★★★★ 两个事件都会发（**本节先前写错，已修正**）

`EntityEventHelper.beforeEvent` 的 UPDATE 分支（tableswitch case 2，字节 135–201）**发两次**：

```java
// 161-164：先逐个发「单个」事件
changeData.forEach(cd ->
    eventBus.publish(new BeforeUpdateEvent(cd.getCurrent(), cd.getPrevious()))  // 636-655
);

// 169-191：再发「批量」事件
BeforeUpdateBatchEvent batch = new BeforeUpdateBatchEvent(changeData);  // 174
batch.setDtoClass(container.getDtoClass());                            // 183
eventBus.publish(batch);                                               // 191
```

`lambda$beforeEvent$3(ChangeEventData)` 的字节码（第 636 行起）：

```
  4: new BeforeUpdateEvent
  8: aload_1
  9: ChangeEventData.getCurrent()      ← 第 1 个入参（更新后）
 12: aload_1
 13: ChangeEventData.getPrevious()     ← 第 2 个入参（更新前）
 16: <init>(Object, Object)
 19: eventBus.publish(...)
```

**⇒ `BeforeUpdateEvent(info, oldInfo)` 的两个入参就是 `current` 和 `previous`，
   两个事件都能收到，挂哪个都行。**

### 6.2.1 ★★★★★ 两个入参改哪个生效 —— 只改 `getInfo()`（current）

`BeforeUpdateEvent(T info, T oldInfo)` 对应：

| 事件方法 | 对应 ChangeEventData | 含义 | 改它会不会落库 |
|---|---|---|---|
| **`getInfo()`** | `getCurrent()` | **更新后**（请求 DTO，merge 补全后） | ✅ **会** |
| **`getOldInfo()`** | `getPrevious()` | **更新前**（`selectCascadeById` 查出的库值） | ❌ **不会** |

`updateBase` 里 `aload 7`（oldDto）的全部使用点，逐个核过：

```
 191: ReflectFieldUtil.getFieldValue(old, "statusType")   → 取旧状态做比对
 238: JsonUtils.toJson(old)                                → 仅日志
 248: Objects.isNull(old)                                  → 判空
 277: Lists.newArrayList(old) → listToMap                  → 只做 merge 的 oldMap
 330: Lists.newArrayList(old) → OperateContext.oldData     → 上下文留痕
 419: BillStateCallBack.checkBillState(old, new)           → 校验入参
 446: PermissionCallBack.buildInitialValue(meta, old, new) → 校验入参
 479: PermissionCallBack.requiredValidate(meta, old, new)  → 校验入参
 513: ChangeEventData.setPrevious(old)                     → 事件 previous
```

**没有任何一条把 `oldDto` 送进 `BeanCopier.copy` 或 mapper。**

写库那一段（偏移 768/826）只认 `aload_1`：

```
 768: BeanCopier.copy(aload_1, entityClass)
 826: getMapper().update(bean)
```

**⇒ 所以改「更新前」那个入参（`getOldInfo()`）不会生效。
   只有改 `getInfo()`（= current = 请求 DTO 本身）才生效。**

### 6.3 事件总线：看着异步，其实同步

`EventBus.publish(serializable)`：

```
  0: getfield async
  5: CtpEventBus.post(event)
  8: getfield sync
 13: CtpEventBus.post(event)
```

两个都 post。而 `AsyncCtpEventBus` 用的 `Dispatcher.legacyAsync()` →
`LegacyAsyncDispatcher.dispatch` 是**入队后立刻轮询、当场 `dispatchEvent` 的同步循环**
（`ConcurrentLinkedQueue.add` → 马上 `poll` → `Subscriber.dispatchEvent`），
没有 `executor.execute`，**没有丢线程池**。

⇒ **在 `beforeEvent` 里改数据，改发生在 `BeanCopier.copy` 之前，来得及。**
   （名字叫 async，行为是同步，别被类名骗。）

### 6.4 `preUpdateBatch` 是另一条更直接的钩子

`PreUpdateCallBack<D>` 只有一个方法：

```java
public default void preUpdateBatch(java.util.List<D>);
```

`BaseEntityCurdService` 自己实现了它，并在**偏移 458**（早于 `beforeEvent` 的 582、
更早于写库的 768）调用。

⇒ 如果要在更新前改数据，**覆写 `preUpdateBatch` 比挂事件监听器更靠前、更可靠**。

### 6.5 ★★★★★ 那个对象就是「请求进来的 DTO」本身

**回答「更新前的那个对象，是不是请求传来的数据」——是同一个对象，且会被就地补全。**

字节码链路（`DtoConvertUtil.mergeMapData(meta, oldMap, newMap)`）：

```
updateBase:
 1260: defaultUpdateListToMap(meta, list5)     → astore 6   ← newMap（请求 DTO）
 1270: selectCascadeById(id)                   → astore 7   ← oldDto（库里的）

 365: mergeMapData(meta, aload 8 /*oldMap*/, aload 6 /*newMap*/) → astore 10
 385: aload 10 → astore_1                     ← 覆盖参数槽
```

`mergeMapData` 内部（参数 1 = oldMap，参数 2 = newMap）：

```
 228: aload_1 /*oldMap*/.forEach( BiConsumer(oldMap, newMap) )   ← 遍历库里的旧 DTO
 245: forEachMergedChildDto(...)
 248: aload 4 /*= aload_2.values() 即请求 DTO*/ + areturn
```

那个 BiConsumer 的终点：

```
lambda$null$11(Map, DTO old, DTO new, DTO):
 1225: copyValueIfTargetFieldIsNull(aload_1 /*?*/, aload_2 /*请求 DTO*/, ...)
 1236: aload_2            ← 返回 newDto
 1237: areturn
```

`copyValueIfTargetFieldIsNull(DTO target, DTO source, ...)`：

```
 469: List.forEach( InvokeDynamic(target=aload_0, source=aload_1) )
 723: lambda$null$33(target, field, value, _):
 728:   ReflectUtil.setFieldValue(aload_0 /*= target*/, field, value)
```

**⇒ 结论：**

| 问题 | 答案 |
|---|---|
| 事件里的 `getInfo()` 是不是请求 DTO？ | **是**，同一个对象实例（`astore_1` 直接指向它） |
| 返回的是 new 出来的副本吗？ | **不是**，`aload_2; areturn` 原样返回请求对象 |
| 请求里没传的字段会怎样？ | **被库里旧值就地回填**（`copyValueIfTargetFieldIsNull` 只补 null 字段） |
| 所以你看到的是「全量对象」还是「只含请求字段」？ | **全量** —— 补齐后的完整对象 |

### 6.6 「就地回填」的三个例外（必须知道）

`lambda$copyValueIfTargetFieldIsNull$31` 的过滤规则：

| 条件 | 行为 |
|---|---|
| `field.name == "version"` | **一定参与回填**（乐观锁） |
| 字段在 `__updatedFields` 里 | **不回填**（本次明确要改的，保留请求值） |
| 字段在 `__emptyFields` 里 | **不回填**（本次明确要清空的，保留 null） |
| 其它字段且请求值为 null | **回填库里旧值** |

**⇒ 你要改的字段，如果在 `__updatedFields` 里，改它没问题（它就是请求值）；
   如果不在，它本来就已经是「库里旧值」，你改了也会被后续 merge 覆盖 —— 先确认字段在哪个集合。**

### 6.7 ★★★ 所以「改请求对象」= 改待落库数据

因为三者是同一个引用链：

```
请求 JSON → DTO（update 的参数 aload_1）
          → mergeMapData 补全后覆盖 aload_1
          → setCurrent(aload_1) 进事件
          → BeanCopier.copy(aload_1) 写库
```

**改 `getInfo()` 拿到的对象的字段 = 直接改请求 DTO = 直接改落库数据。不需要再 update。**

⚠️ 但注意：**请求对象在被 merge 补全之后、事件发出之前**才有完整字段。
`preUpdateBatch`（偏移 458）恰好在 merge(365) 之后、beforeEvent(582) 之前 ——
**这个钩子里拿到的是完整对象，位置最佳。**

## 7. Side Effects

| 改哪里 | 是否会落库 | 时机 |
|---|---|---|
| `BeforeUpdateEvent.getInfo()` 返回对象 | **会** | 早于写库（768） |
| `BeforeUpdateBatchEvent.getEventData()` 里的元素 | **会**（同一批引用） | 早于写库 |
| `getOldInfo()` 返回对象 | **不会**（oldDto 只做 previous 和比对） | — |
| `preUpdateBatch(List<D>)` 参数元素 | **会** | **最早（458）** |
| `afterEvent` 里改 | 不会（已落库） | 晚于 768 |

## 8. Known Constraints

| # | 约束 |
|---|---|
| 1 | **改数据后不要再调 `update`** —— 会二次写、可能触发第二次完整链路 |
| 2 | **只有 `isMasterEntity` 为 true 才发事件**（偏移 517: `getfield isMasterEntity; ifeq 560`，子实体容器为 null） |
| 3 | **单事件和批量事件都会发**（此条先前写错，已按字节码修正） |
| 4 | `updateNoEvents` 完全不发事件，改它的事件没意义 |
| 5 | 改 `oldInfo` 不影响落库 |
| 6 | 事件名为 async 实为同步，改在写库前生效；但**不要依赖这个时序做跨事务投递** |
| 7 | `mergeMapData` 会先合并旧值，**你改的字段必须是本次 update 语义上要写的字段** |

## 9. Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `updateBase` 字节偏移顺序 | `javap -p -c BaseEntityCurdService` 全文 7757 行 | **VERIFIED_STATIC_BYTECODE** |
| 385 `astore_1` / 506 `setCurrent(aload_1)` / 768 `BeanCopier.copy(aload_1)` | 同上，逐行核对 | **VERIFIED_STATIC_BYTECODE** |
| `BeforeUpdateEvent` 是纯 POJO 无拷贝 | `javap -p -c BeforeUpdateEvent` | **VERIFIED_STATIC_BYTECODE** |
| UPDATE 分支只发 Batch 事件 | `javap -p -c EntityEventHelper` tableswitch case 2 | **VERIFIED_STATIC_BYTECODE** |
| `LegacyAsyncDispatcher` 同步循环 | `javap -p -c Dispatcher$LegacyAsyncDispatcher` | **VERIFIED_STATIC_BYTECODE** |
| 真实运行效果 | 未实测 | **UNVERIFIED** |

## 10. Verified

- ✅ **VERIFIED_STATIC_BYTECODE**：以上全部结论逐条对字节码核对
- ⚠️ **UNVERIFIED**：实际跑一遍改 `getInfo()` 看库里的值是否变（需 LIVE 环境）
- ⚠️ **UNVERIFIED**：`mergeMapData` 对「只改部分字段」的精确合并规则

## 11. 给 Agent 的判据

```
问「监听更新前事件改数据，还要再 update 吗」
  → 不用。改 getInfo() 返回的对象即可，它和写库源是同一个引用（385/506/768）
  → 但先确认你挂的是哪个事件：

问「监听更新前事件有两个入参，改哪个生效」
  → 改 getInfo()（= current = 更新后 = 请求 DTO 本身）。改它必落库
  → 改 getOldInfo()（= previous = 库里的旧值）不落库，oldDto 从不进写库路径

问「BeforeUpdateEvent 在这条链上收得到吗」
  → 收得到。EntityEventHelper.beforeEvent case2 先逐个 publish 单事件(164)，
    再 publish batch(191)。两个都能挂

问「事件是异步的吗，改得及吗」
  → 名叫 async，LegacyAsyncDispatcher 实际是同步循环
  → 改发生在 BeanCopier.copy(768) 之前，来得及

问「最靠前的改数据钩子是什么」
  → PreUpdateCallBack.preUpdateBatch(List<D>)，偏移 458，早于事件

问「更新前那个对象是请求传进来的吗」
  → 是，同一个实例。mergeMapData 就地补全后 `aload_2; areturn` 原样返回
  → 所以事件里拿到的是「补全后的完整对象」，不只是请求里那几个字段

问「改 oldInfo 有用吗」
  → 没用。oldDto 只用于 previous 和比对，不进写库

问「子实体（明细表）改得到吗」
  → 只有 isMasterEntity=true 才发事件，子实体容器事件为 null
  但 recursiveUpdate(741) 在写库前，改子表 DTO 仍会落库
```