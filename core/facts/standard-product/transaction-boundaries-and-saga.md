# 事务边界：本地事务、事件发布时机、Saga/TCC

## Capability

**三件事，按发生顺序判断：**
①我的代码在不在事务里（平台 AOP 给的边界）；②事件该在事务内发还是事务后发；
③跨服务要不要上 Saga/TCC（平台确有这套，但默认关）。

## Version

`boot-starter-transaction` 5.3.600、`boot-starter-eventbus` 5.3.600（jar 在盘）。

## Input

无。分布式事务需配置协调器（见第五节）。

## Required

本地事务：写在 `@AppService`/`@Service` 方法上即可（框架 AOP 已织入）。
分布式事务：`TransactionProperties.enable=true` + `coordinatorServers`。

## ★ 一、本地事务边界在哪

- 标品与生成物的事务边界在 **AppService 方法级**（`appservice-usage.md` §事务已记：事务切面存在=`VERIFIED_STATIC_BYTECODE`，**织入顺序未证**）。
- UDC 生成的微流程事件监听类上是 `@Transactional(propagation = REQUIRED)`（本仓生成物原文实测，LIVE）——
  即**监听器里抛异常，事件处理整体回滚**；这是我们做 BeforeUpdate 实验时的一条硬事实。
- 你在 ext 里写的实现类：**不要自己开新事务**（`REQUIRES_NEW`）除非明确要「主流程回滚、这段也不回滚」。

## ★ 二、事件：事务内发 vs 事务后发（最容易错的地方）

`EventBus` 只有两个发布口（字节码原文）：

```java
void publish(Serializable event);                 // 立刻发，在调用者事务内
void publishAfterTransaction(Serializable event);  // 事务提交后再发
```

判据：

```
业务失败要连带取消的副作用（发消息/通知/外部调用）  → publishAfterTransaction
必须在同一事务里可见的数据变更                     → publish
拿不准                                            → publishAfterTransaction（宁可晚发，不要错发）
```

**反例（真实踩法）**：事务里 `publish` 发消息，随后业务抛异常回滚 → 消息已经发出去了，收件人看到一条不存在的单子。

## ★ 三、分布式事务（Saga / TCC）——平台有，默认关

```java
class TransactionProperties {
    boolean  enable;                     // ★ 总开关
    String[] coordinatorServers;         // ★ 协调器地址（alpha）
}
```

组件（都在 `com.seeyon.boot.starter.transaction`，字节码原文）：

```
SagaAspect                     extends org.apache.servicecomb.pack.omega.transaction.TransactionContextHelper
TccParticipatorAspect
CompensableAnnotationProcessor implements BeanPostProcessor   // 扫 @Compensable 方法
ParticipateAnnotationProcessor
CompensableInterceptor / CompensableMethodCheckingCallback / ParticipateMethodCheckingCallback
DefaultRecovery / RecoveryPolicyTimeoutWrapper
TransactionAutoConfiguration / TransactionComponentInitializer
```

⇒ 平台接的是 **ServiceComb Pack（Omega）**，注解来自 `org.apache.servicecomb.pack.omega.transaction.annotations`。

用法形态（注解属性 **UNVERIFIED**：omega jar 未在盘，只有引用证据）：

```java
@Compensable(confirmMethod = "confirmX", cancelMethod = "cancelX")
public void doX(...) { ... }

@Participate
public void doSub(...) { ... }
```

## Side Effects

- `publishAfterTransaction` 在事务提交后执行，**提交后异常不会回滚已提交数据**（只影响副作用本身）。
- Saga 的补偿方法必须幂等，且要能在「上游没成功」时被安全调用。
- 开启 `enable` 后所有 `@Compensable` 方法都要走协调器，协调器不可用会拖慢甚至阻塞调用。

## Known Constraints

1. `@Transactional` 自调用失效（同类内部 `this.xxx()` 不走代理）——这是 Spring 通病，平台上一样。
2. `try/catch` 吞掉异常 = 不回滚；要回滚就 `throw`（或 `TransactionAspectSupport.currentTransactionStatus().setRollbackOnly()`）。
3. 事件监听器若是 `REQUIRED`，监听器抛异常会把**发布方事务**一起标记回滚。
4. Saga/TCC 注解类不在随包 jar 里（`org.apache.servicecomb.pack.omega.*` 未解析到本地仓库）⇒
   属性名/行为 **UNVERIFIED**，只能用「平台确实接了 Omega」这一层事实。
5. 分布式事务与「消息最终一致」是两种方案，别混用：要么 Saga 补偿，要么 outbox + `publishAfterTransaction`。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `EventBus.publish` / `publishAfterTransaction` 两方法 | `javap -p` boot-starter-eventbus 5.3.600 | VERIFIED_STATIC_BYTECODE |
| `TransactionProperties{enable, coordinatorServers}` | `javap -p` boot-starter-transaction 5.3.600 | VERIFIED_STATIC_BYTECODE |
| 7 个 Saga/TCC 组件类 + 实现 BeanPostProcessor | 同上 | VERIFIED_STATIC_BYTECODE |
| 平台接 ServiceComb Pack（常量池引用 `OmegaContext`/`CallbackContext`/`TransactionContextHelper`） | `javap -v` 常量池 | VERIFIED_STATIC_BYTECODE |
| 生成物监听类 `@Transactional(REQUIRED)` | 本仓生成物原文（p0 探针构建） | LIVE |
| `@Compensable`/`@Participate` 注解属性 | omega jar 未在盘 | UNVERIFIED |

## Verified

- ✅ 平台确有 Saga/TCC 组件与开关（类与属性都在）
- ✅ 事件有两个发布口，事务后发的 API 存在
- ⚠️ 未跑过真实 Saga 事务（协调器未部署）

## 给 Agent 的判据

```
问「我这个方法在事务里吗」     → AppService/@Service 方法级 AOP 内；监听器 REQUIRED
问「事件什么时候发」           → 副作用用 publishAfterTransaction；同事务可见才用 publish
问「要不要上分布式事务」        → 先看能否用 outbox+publishAfterTransaction 解决；真要跨服务补偿才开 Saga
问「为什么改了没生效/报了没回滚」→ 查自调用、try/catch 吞异常、监听器事务传播
```
