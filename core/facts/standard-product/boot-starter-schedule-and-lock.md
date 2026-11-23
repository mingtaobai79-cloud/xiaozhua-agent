# boot-starter-schedule + boot-starter-lock：定时任务与分布式锁

## Capability

**在客开代码里加一个能真正跑起来的定时任务，以及给并发写加锁。**
覆盖两件事：①`@CtpSchedule` 注解 + `SeeyonJob` 接口 + 平台调度表/服务；②`DistributedLockFactory` 分布式锁。

## Version

`boot-starter-schedule` 5.3.600 / `boot-starter-lock` 5.3.600（jar 在盘，javap 全量抽取）。

## Input

无前置。任务对象落库在 `ctp_job_info` / `ctp_job_cron` / `ctp_job_simple` / `ctp_job_log` 四张表
（本机 test2 实测存在这四张表，`ctp_job_info` 有启用列）。

## Required

定时类必须是 Spring Bean（`@Component`），并 `implements SeeyonJob`。

## ★ 一、最小可用：一条 cron 定时任务

```java
import com.seeyon.boot.starter.schedule.annotation.CtpSchedule;
import com.seeyon.boot.starter.schedule.api.SeeyonJob;
import com.seeyon.boot.transport.SingleResponse;
import org.springframework.stereotype.Component;

@Component
@CtpSchedule(jobName = "extMyJob", cron = "0 0/5 * * * ?", description = "每5分钟扫一次")
public class MyJob implements SeeyonJob {
    @Override
    public SingleResponse<?> exec() {
        // 业务；返回 SingleResponse.ok() 即可，调度器只看成败
        return SingleResponse.ok();
    }
}
```

**接口契约（字节码原文）：**

```java
public interface SeeyonJob {
    SingleResponse<?> exec();          // 整个接口只有这一个方法
}
```

**注解 13 个属性（字节码原文，无默认值信息靠不传即生效的实测口径）：**

```java
boolean  systemTenant();        // 系统租户也跑
boolean  isSingle();            // 全集群只跑一次（默认按租户分发）
String   jobName();             // 任务唯一名，落 ctp_job_info.job_name
String   cron();                // 6 段 Quartz cron
String   description();
long     fixedDelay();  String fixedDelayString();
long     fixedRate();   String fixedRateString();
long     initialDelay(); String initialDelayString();
TimeUnit timeUnit();
String   zone();
```

## ★ 二、平台怎么跑它（决定「配了不动」这类问题）

```
启动：CtpJobSyncService.onApplicationEvent(SystemStartedEvent) → syncToRedis()
      把 ctp_job_info（含 cronList/simpleList）同步到 Redis 缓存
执行：平台 Job → CustomSchedule.exec()
      → 从 Redis 取 ctp_cache_cron / ctp_cache_simple
      → 逐条交给线程池（IsolatorExecutorService）跑，并按租户分发
```

⇒ **任务是否真的在跑，取决于 `ctp_job_info.status`（启用）而不是注解有没有贴。**
`status` 是 `Boolean`，落库为停用即不执行——这与 UDC 微流程「定时型默认停用」是同一套开关。

## 三、用服务管理任务（CtpJobInfoService，不包 SingleRequest）

```java
Long  create(CtpJobInfoDto dto);
Integer update(CtpJobInfoDto dto);
Integer updateStatus(Long id, Boolean status);          // ★ 启用/停用
Integer delete(Long id);
CtpJobInfoDto selectDetail(Long id);
CtpJobInfo   selectById(Long id);
CtpJobInfo   selectByJobName(String jobName);
PageData<CtpJobInfoDto> selectPageByConditions(PageInfo pageInfo, Map<String,Object> params);
List<CtpJobLogDto>     selectLogByConditions(String jobName);
void  executeOnetime(Long id);                          // 立刻跑一次
void  initJobInfo(List<Object> jobs, Map<String, Runnable> runnableMap);
```

`CtpJobInfoDto` 9 个字段（字节码原文）：

```java
Long id; String jobCaption; String jobName; String appName; Long tenantId;
Boolean status;                                  // ★ 启用开关
List<CtpJobCronDto>   cronList;                  // cron 型
List<CtpJobSimpleDto> simpleList;                // fixedDelay/Rate 型
ScheduleMonitorDto scheduleMonitorDto;
```

`CtpJobCronService` / `CtpJobSimpleService` 对外只有 `updateRunMillis(Long, Long)`（记录上次耗时），
**不要拿它们当调度入口**。

## 四、REST 面（JobInfoController，带 tenantId）

```
POST   selectPageByConditions(PageInfo, Map)
POST   create(CtpJobInfoDto)
POST   update(CtpJobInfoDto, tenantId)
POST   selectDetail(id, tenantId)
POST   updateStatus(id, Boolean, tenantId)      ← 启用/停用
POST   delete(id, tenantId)
POST   cronValid(String cron)                  ← 校验 cron 表达式
POST   selectLogByConditions(String jobName, tenantId)
POST   executeOnetime(id, tenantId)            ← 手动触发一次
```

## ★ 五、分布式锁（DistributedLockFactory）

```java
@Autowired(required = false) private DistributedLockFactory lockFactory;

Lock lock = lockFactory.newLock("my-biz-key");        // 同租户内互斥
boolean got = lock.tryLock(3, TimeUnit.SECONDS);      // 拿不到就返回 false
try { if (got) { /* 临界区 */ } }
finally { if (got) lock.unlock(); }
```

```java
Lock newLock(String key);                            // 带租户前缀
Lock newLock(String key, Long expireTime);
Lock newLockIgnoreTenant(String key);                // 跨租户共用一把
Lock newLockIgnoreTenant(String key, Long expireTime);
```

底层 `RedisDistributedLock implements java.util.concurrent.locks.Lock`，
支持 `lock()/tryLock()/tryLock(long,TimeUnit)/tryLock(long,long,TimeUnit)/unlock()/getLockThreadName()`；
配置项在 `DistributedLockProperties`：`expireTime` / `address` / `engine`（前缀常量 `PREFIX`）。

## Side Effects

- 贴了 `@Component` 的任务类在**所有** pod 上都会注册；是否重复执行由 `isSingle` + 租户分发决定。
- `executeOnetime` 会真的执行业务逻辑，压测/验证时慎用。
- 锁的 `expireTime` 太短会在长事务里被提前释放，别把业务全塞在锁里。

## Known Constraints

1. **任务启用与否看 `ctp_job_info.status`**，不是看注解；新任务上线后没数据是常态（要么 `create` 建，要么平台同步）。
2. `CtpJobCronService`/`CtpJobSimpleService` 只有 `updateRunMillis`，别当 CRUD 用。
3. `initJobInfo(List<Object>, Map<String,Runnable>)` 是平台初始化路径，客开不要直接调。
4. 微流程「定时型」与 `@CtpSchedule` 是两条路：前者由 UDC 生成 Schedule 类（**不要在生成物里改**），
   后者是自己写 Bean；两者都受 `status` 开关约束。
5. 多租户分发机制（谁跑、跑几次）**UNVERIFIED**：只观测到两租户各跑一次，未拆解分发器。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `SeeyonJob.exec()` 单方法 | `javap -p` 5.3.600 原文 | VERIFIED_STATIC_BYTECODE |
| `@CtpSchedule` 13 属性 | 同上 | VERIFIED_STATIC_BYTECODE |
| `CtpJobInfoService` 11 方法签名 | 同上 | VERIFIED_STATIC_BYTECODE |
| `CtpJobInfoDto` 9 字段 | 同上 | VERIFIED_STATIC_BYTECODE |
| `JobInfoController` 9 个端点 | 同上 | VERIFIED_STATIC_BYTECODE |
| 四张表存在 + `status` 语义 | test2 库实测（`ctp_job_info` 行读改） | LIVE |
| 锁工厂 6 个方法 | `javap -p` 5.3.600 原文 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ `@CtpSchedule` + `SeeyonJob` 可编译可注册（ext 工程实测部署成功）
- ✅ 定时任务需 `status` 启用后才执行（UDC 侧 LIVE 实证，同表同列）
- ⚠️ 锁未在真机跑并发验证（只有字节码契约）

## 给 Agent 的判据

```
要写定时任务  → @Component + @CtpSchedule(jobName,cron) + implements SeeyonJob，exec() 返回 SingleResponse
配了不跑      → 先查 ctp_job_info.status 是否启用，再查 job_name 是否与注解一致
要手动跑一次  → CtpJobInfoService.executeOnetime(id) / REST executeOnetime(id, tenantId)
要加并发锁    → DistributedLockFactory.newLock(key).tryLock(timeout, unit)
跨租户互斥    → newLockIgnoreTenant(key)
```
