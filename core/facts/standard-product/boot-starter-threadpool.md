# boot-starter-threadpool：隔离线程池与执行器

## Capability

**平台不让业务直接 `new ThreadPoolExecutor`**，给的是两套：

```
SeeyonExecutorService.implements ExecutorService   三档优先级：普通 / submitMiddle / submitHigh
IsolatorExecutorService                            命名隔离池 + @IsolatorExecutor 注解
```

## Version

`boot-starter-threadpool` 5.3.600（jar 在盘，javap 全量抽取）。

## Input

无（`IsolatorExecutorProperties` + `IsolatorConfigItem` 配置项）。

## ★ 一、最常用：三档执行器

```java
@Autowired private SeeyonExecutorService executor;

executor.submit(() -> doFastWork());            // 普通
executor.submitMiddle(() -> doNormalWork());    // 中优先级
executor.submitHigh(() -> doUrgentWork());      // 高优先级
Future<T> f = executor.submit(() -> compute()); // 有返回值
```

签名原文：

```java
public class SeeyonExecutorService implements java.util.concurrent.ExecutorService {
    SeeyonExecutorService(ThreadPoolTaskExecutor, TraceMonitorService);
    SeeyonExecutorService(ThreadPoolTaskExecutor, ThreadPoolTaskExecutor, ThreadPoolTaskExecutor, TraceMonitorService);  // ★ 三档构造
    <T> Future<T> submit(Callable<T>);
    <T> Future<T> submitMiddle(Callable<T>);
    <T> Future<T> submitHigh(Callable<T>);
    <T> Future<T> submit(Runnable, T);
    // + ExecutorService 标准方法（shutdown/awaitTermination...）
}
```

⇒ 三档是**三个独立 ThreadPoolTaskExecutor**（构造器三个池参数），互不饿死。

## ★ 二、隔离池：一个业务一个池

```java
@Autowired private IsolatorExecutorService isolator;

Future<?> f = isolator.submit(task, "myIsolatorName");   // 指定池名
isolator.execute(task, "myIsolatorName");
```

```java
public class IsolatorExecutorService {
  static final String DEFAULT_ISOLATOR;
  void registerExecutor(String name, ThreadPoolTaskExecutor executor);
  Future<?> submit(Runnable, String isolatorName);
  <T> Future<T> submit(Callable<T>);
  <T> Future<T> submit(Callable<T>, String isolatorName);
  void execute(Runnable, String isolatorName);
  ThreadPoolTaskExecutor getThreadPoolExecutor(String isolatorName);
}
```

### 注解形态（方法级 AOP）

```java
@IsolatorExecutor(isolatorName = "reportPool", coreSize = 4, maxSize = 8,
                  queueSize = 200, rejectionPolicy = RejectionPolicyEnum.CallerRunsPolicy)
public void buildReport() { ... }
```

注解属性（字节码原文 5 个）：

```java
String isolatorName(); int coreSize(); int maxSize(); int queueSize();
RejectionPolicyEnum rejectionPolicy();
```

拒绝策略只有四种（`RejectionPolicyEnum`）：`AbortPolicy` / `CallerRunsPolicy` /
`DiscardPolicy` / `DiscardOldestPolicy`。

## 三、监控

`CtpThreadPoolMetrics` 暴露池指标（配合 `boot-starter-prometheus`）。

## Side Effects

- 线程池里的代码**没有请求上下文**（ThreadLocal 不继承）：`SystemVariableUtils.currentUserId()` 之类会拿不到。
  需要上下文就自己把参数传进去。
- `DiscardPolicy` 会**静默丢任务**，业务上用 `CallerRunsPolicy` 或 `AbortPolicy` 更安全。
- 隔离池名字打错不会报错，会落到 `DEFAULT_ISOLATOR`（或新建），任务量就串了。

## Known Constraints

1. 三档 `submitXxx` 只接受 `Callable`，无返回值的用 `submit(Runnable)`（`submitMiddle(Runnable)` 不存在）。
2. `IsolatorExecutorService.registerExecutor` 是运行期注册，配置池一般走 `IsolatorExecutorProperties`。
3. 线程池不传播事务：池内任务不在调用方事务里。
4. `shutdown()` 别在业务代码里调——那是容器生命周期方法。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `SeeyonExecutorService` 三档方法 + 三池构造 | `javap -p` 5.3.600 | VERIFIED_STATIC_BYTECODE |
| `IsolatorExecutorService` 10 方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| `@IsolatorExecutor` 5 属性 | 同上 | VERIFIED_STATIC_BYTECODE |
| `RejectionPolicyEnum` 四值 | 同上 | VERIFIED_STATIC_BYTECODE |
| 调度器用它跑任务（`IsolatorExecutorService` 注入 `CustomSchedule`） | `CustomSchedule` 字段 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 全部签名可复核；平台调度器确实用它做隔离执行
- ⚠️ 未跑过真机并发

## 给 Agent 的判据

```
要异步跑一段         → SeeyonExecutorService.submit(Runnable) / submitHigh / submitMiddle
要按业务隔离         → IsolatorExecutorService.submit(task, "poolName") 或 @IsolatorExecutor
池里拿不到当前用户    → 线程池不继承 ThreadLocal，参数显式传
任务莫名丢了         → 查 rejectionPolicy（DiscardPolicy 静默丢）
```
