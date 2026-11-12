# MigrationScheduler 调度关系契约（B-9）

> 目标应用：`datamigration9000000000000000001`（appId `8704025620829192834`），环境 test2
> 证据基准（三个 jar 的**绝对路径**，须原样可复算；外部复现缺一不可）：
> ```
> BIZ = <MAVEN_REPO>/com/seeyon/datamigration9000000000000000001-biz/1.0.7/
>       datamigration9000000000000000001-biz-1.0.7.jar          (176015 B, 39 class)
> FAC = <MAVEN_REPO>/com/seeyon/datamigration9000000000000000001-facade/1.0.7/
>       datamigration9000000000000000001-facade-1.0.7.jar
> SCH = <MAVEN_REPO>/com/seeyon/boot-starter-schedule/5.3.345/
>       boot-starter-schedule-5.3.345.jar                       (113580 B, 53 class)
> ```
> 存在性自检：`[ -f "$BIZ" ] && [ -f "$FAC" ] && [ -f "$SCH" ]`。
> **注意**：应用生成类在 BIZ（不是平台 `udc-biz-5.3.517`）；平台 jar 内
> `MigrationScheduler` 命中 0（main 扫 59 个 udc-* jar 确认）。这一点曾让 B-8 遗留项
> 误判为「需读 fatjar」，实际本地 biz jar 即可取证。
> 证据等级：**STATIC + DB-READ**（javap 字节码 + 只读 DB；**不是 LIVE** —— 无真实执行回读）
> 0 次 /service、0 次写库、未 push

---

## 0. 结论（TL;DR）

**`MigrationScheduler` 定时任务在 test2 当前配置下永不触发，根因是 `ctp_job_cron.run_millis = -1`，
不是 cron 表达式、不是流程状态、不是生成类缺失。**

一句话判据：调度器发事件前有一条 `runMillis > 0` 的判断（`CustomSchedule.lambda$null$0` 偏移 9 的
`ifle 40`），`run_millis = -1` 直接走 40 分支，**只更新 run_millis、不发布 JobEvent**。
没有 JobEvent 就没有 `JobListener` 调用，`MigrationSchedulerSchedule.exec()` 连被看到的机会都没有。

这与 B-8 的结论互补而非重复：B-8 证的是「执行链三层无解释器、state 列不可达」，
本契约证的是**在到达执行链之前，调度层就已把它拦掉了**。

---

## 1. 调度链（三段式：类.方法 → 调用者 → 触发条件）

### 1.1 链总览（自上而下，5 跳）

```
①CustomSchedule.exec()                    [每分钟，框架内置]
    ↳ 读 Redis: cron:<appName>:<分钟戳> → List<CtpCacheCronDto>
      判据：runMillis > 0            ← 偏移 9: ifle 40    ★ 本 job 死在这里
    ↳ EventBus.publish(JobEvent)      ← 偏移 37
②JobListener.processJob(JobEvent)        [事件监听]
    ↳ TenantChangeFunction.apply(tenantId, → lambda$processJob$0)
③JobListener.lambda$processJob$0
    ↳ jobMap.get(jobName)            ← 偏移 48-60
      未命中则 getDyJobBean(jobName)  ← 偏移 67（beanFactory.getBean，异常吞掉返 null）
    ↳ if (job == null) → 写 CtpJobLog status=0「未找到」并 return   ← 偏移 190/194-266
    ↳ job.exec()                     ← 偏移 434-435
④MigrationSchedulerSchedule.exec()
    ↳ migrationSchedulerService.migrationScheduler()   ← 偏移 17
⑤MigrationSchedulerService.migrationScheduler()
    ↳ migrationService.executeAll()   ← 偏移 149
      判据：SingleResponse.success() 为 false → 抛 UDC_MICROFLOW_RUNTIME_0001  ← 偏移 158/161/204
⑥DefaultMigrationServiceImpl.executeAll()
    ↳ migrationServiceService.executeAll()   ← 偏移 21
⑦MigrationServiceService.executeAll()   [接口，实现类不在本应用任何 jar 内]
```

### 1.2 逐跳证据（javap 偏移）

#### ① `CustomSchedule.exec()` — 框架每分钟驱动
- 类：`com.seeyon.boot.starter.schedule.CustomSchedule`
- 实现 `SeeyonJob`，被框架自身以 cron 驱动（`SyncJobToRedisSchedule` 把 `ctp_job_*` 镜像进 Redis）
- `exec()` 偏移 0-16：取 `Instant.now().truncatedTo(MINUTES).getEpochSecond()/60` 作为分钟戳
- 偏移 37/54：两次 `isolatorExecutorService.submit(...)`，分别跑 **cron 侧** 与 **simple 侧**
- 段行数：exec 体 `javap -p -c` 之 `exec()` 段 = 87 行

#### ② 关键判据：`CustomSchedule.lambda$null$0` — **run_millis > 0 才发事件**
- 签名：`private void lambda$null$0(CtpCacheCronDto, String)`
- 偏移 0-9：`CtpCacheCronDto.getRunMillis()` → `Long.longValue()` → `lcmp` vs `0`
- **偏移 9：`ifle 40`** ← `runMillis <= 0` 跳到 40（跳过事件发布）
- 偏移 12-28：`new JobEvent(tenantId, jobName, jobInfoId)`
- 偏移 32-37：`eventBus.publish(jobEvent)`
- 偏移 40-44：`ScheduleUtil.cronParser(cron)` → 算下次时间
- 偏移 48+：`ctpJobCronService.updateRunMillis(...)`（**即使不发事件也会推进 run_millis**）

> 这是本契约的核心判据。`ifle`（≤ 则跳）不是 `iflt`（< 则跳）：`run_millis == 0` 也**不发**。

#### ③ `JobListener.lambda$processJob$0` — 从 jobMap 取 bean 再 exec
- 类：`com.seeyon.boot.starter.schedule.event.listener.JobListener`
- 偏移 42-46：`jobEvent.getJobName()`
- 偏移 47-60：`jobMap.get(jobName)`（**偏移 52** 是 `Map.get`）→ checkcast `SeeyonJob`
- **偏移 61-70：`if (job == null) getDyJobBean(jobName)`** —— 兜底从 Spring beanFactory 按**字符串 getBean**
  - `getDyJobBean` 偏移 0-10：`Apps.getBeanFactory().getBean(name)` → checkcast
  - 异常表 `0→10 target 11 Class java/lang/Throwable`；偏移 11-13：`astore_2; aconst_null; areturn`
    → **getBean 抛异常时静默返回 null，不传播**
- 偏移 190-266：`job == null` 分支 → `CtpJobLog.setStatus(0)`、remark 写「未找到[xxx]的定时任务」、落库后 `return`
- **偏移 435：`SeeyonJob.exec()`**（`invokeinterface` 在 435，`aload_3` 在 434）← 决定性一跳

#### ④ `MigrationSchedulerSchedule.exec()` — 应用侧入口
- 类：`com.seeyon.datamigration9000000000000000001.schedule.MigrationSchedulerSchedule`
- 实现 `com.seeyon.boot.starter.schedule.api.SeeyonJob`（`SingleResponse<?> exec()`）
- 类级注解 `@CtpSchedule(jobName="4975531884502076979", description="...")` ← 常量池 #36/#37/#38/#39
- 注：`@CtpSchedule` **未设 cron、未设 fixedDelay/fixedRate**（默认 `fixedDelay=-1`），
  所以 cron 只能来自 DB 的 `ctp_job_cron` 行，不能来自注解
- 字段 `migrationSchedulerService` 带 `@Autowired`（常量池 #18）
- `exec()` 偏移 0：`MicroFlowRuntimeUtil.saveDefaultValue4RequestContext()`
- `exec()` 偏移 6-8：`log.info("jobClass:[MigrationSchedulerSchedule] jobName:[4975531884502076979] start!")`
- **`exec()` 偏移 14-17：`getfield migrationSchedulerService` → `invokevirtual migrationScheduler()`**
- 偏移 20：`SingleResponse.ok()`；偏移 23：`areturn`

#### ⑤ `MigrationSchedulerService.migrationScheduler()` — 转调 executeAll
- 类：`...domain.service.microflow.MigrationSchedulerService`
- 字段 `private MigrationService migrationService`（接口，`api.microflow.MigrationService`）
- 偏移 0-17：`UdcAppLogHelper.buildMfLogV2("migrationScheduler", MICRO_FLOW_SCHEDULE,
  "1.4 数据迁移同步定时任务", "2274146594523136239", appId, appName)`
- 偏移 20-32：`buildInputLog(...)`（入参 null）
- 偏移 97-99：`log.info("nodeId:SUB_MICROFLOW_4rGf5E caption:子流程(1) start SubMicroFlow")`
  → **该微流程含 1 个子流程节点，nodeId = `SUB_MICROFLOW_4rGf5E`**
- 偏移 104-120：`migrationService == null` → 抛 `BusinessException("UDC_MICROFLOW_RUNTIME_0006")`
- 偏移 121-142：`buildSubMfStartLog(...)`
- **偏移 145-149：`getfield migrationService` → `invokeinterface MigrationService.executeAll()`**
- 偏移 154-161：`astore 10` → `invokevirtual SingleResponse.success()` → **`ifne 226`**
  （success == true 跳到 226 直接 return）
- 偏移 164-225：失败分支 → `log.error` + 抛 `BusinessException("UDC_MICROFLOW_RUNTIME_0001", message)`
- 偏移 226：`return`

#### ⑥ `DefaultMigrationServiceImpl.executeAll()` — 接口到实现
- 类：`...custom.appservice.microflow.DefaultMigrationServiceImpl implements api.microflow.MigrationService`
- 偏移 0-16：`migrationServiceService == null` → 抛 `UDC_MICROFLOW_RUNTIME_0006`
- **偏移 17-21：`invokeinterface MigrationServiceService.executeAll()V`**
- 偏移 26-29：`SingleResponse.ok()`

#### ⑦ `MigrationServiceService.executeAll()` — 契约终点（实现类缺失）
- 接口：`...custom.service.microflow.MigrationServiceService`（在 **facade** jar）
- 方法：`public void executeAll();` —— 返回 `void`
- **实现类在 biz/facade/web 三个 jar 内均不存在**（实测 `unzip -l | grep -c MigrationServiceServiceImpl` = 0/0/0）
- 该接口由 `DefaultCustomMicroFlowConfig.exportDefaultCustomMicroFlowAppService()` 经
  `MicroFlowDubboExportBeanPostProcessor.exportServiceBean(appName, MigrationService.class, bean)` 导出
- 判据：它由平台在**微流程运行态**注入（dubbo 导出），不是编译期类 → 无法从静态 jar 继续下钻
- **此跳标 BLOCKED**（见 §4）

---

## 2. 触发条件：谁在什么条件下调度

### 2.1 完整条件式

```
触发 = @CtpSchedule 已注册            （启动期扫描，见 2.2）
     ∧ ctp_job_info.status = 1        （job 级启用）
     ∧ ctp_job_cron.status = 1        （cron 行启用）
     ∧ ctp_job_cron.run_millis > 0    （★ 决定今晚是否发 JobEvent）
     ∧ 当前分钟戳命中 run_millis       （Redis hash 以分钟戳为 field）
     ∧ bean 能在 jobMap / beanFactory 中按 jobName 取到
```

任一条不满足即不执行；**`run_millis <= 0` 时连日志都不会写**（`ifle 40` 在写 log 之前）。

### 2.2 注册链（`@CtpSchedule` → 数据库行）

- `ScheduleBeanRegistryPostProcessor` 偏移 0-2：
  `BeanReflections.getTypesAnnotatedWith(CtpSchedule.class)` → 遍历每个类
  → 偏移 184-204：`getAnnotation(CtpSchedule.class).jobName()` 作为 bean 名注册
- `ScheduleBeanPostProcessor` 偏移 51-66：`processScheduled(annotation, method, bean)`
- `CtpJobInfoService.initJobInfo(...)` 偏移 41-146：
  为每个 `@CtpSchedule` 类造 `CtpJobInfo`，其中
  - 偏移 95-100：**`setStatus(Boolean.TRUE)`** ← 代码里写死 TRUE
  - 偏移 122-126：`setJobName(beanClass.getSimpleName())`
  - 偏移 129-138：`setJobCaption(annotation.jobName())`
  - 偏移 152-162：`annotation.cron()` 非空才造 `CtpJobCron`
  - 偏移 202-210：**`setRunMillis(-1L)`** ← 代码里写死 -1
- 结论：**`initJobInfo` 造出来的跑线默认是「启用 + run_millis=-1」**，
  即「注册了但不会被调度」。run_millis 只由「用户启用动作」推进 >0。

### 2.3 本应用的真实配置（DB-READ）

```
ctp_job_info : id=1435599342859489182
               job_name=4975531884502076979
               status=0
               app_name=datamigration9000000000000000001
               job_caption=1.4 数据迁移同步定时任务

ctp_job_cron : id=1216258722862285836
               job_info_id=1435599342859489182
               cron=0 0 2 * * ?
               status=0
               run_millis=-1
               is_delete=0
               update_time=2026-10-14 14:41:57

ctp_job_simple: 0 行
ctp_job_log  : 该 job 0 行
```

→ **`run_millis = -1` → 命中 `ifle 40` → 永不 publish JobEvent → 永不执行。**

### 2.4 与「未启用」的区分（负控制）

`run_millis<=0` 是**独立于 status 的第二个闸门**，实测：

```
ctp_job_cron 全表 214 行，run_millis<=0 的有 214 行（100%）
  其中 status=0 : 191 行
       status=1 : 23 行   ← 即使 status=1，run_millis 仍 <=0，照样不发事件
ctp_job_cron 中 run_millis>0 的行：0 行
```

**这张表没有任何一行的 run_millis>0。** 说明 test2 这套调度配置整体处于「已注册、未点火」状态，
不是本应用单独的问题。`status` 与 `run_millis` 是两个独立条件，不能互推。

### 2.5 执行痕迹的负证据（DB-READ）

```
ctp_job_log 全表 148960 行
  app_name 分布：{'udc': 148960}          ← 全部属于平台自身
  start_time 范围：2026-03-02 15:03:58 ~ 2026-03-19 16:05:01
  status 分布：{'1': 148960}              ← 全为成功
本应用（datamigration9000000000000000001）：0 行
本 job（4975531884502076979）：0 行
```

判据：log 表**确实在被写**（14.9 万行平台任务），但**时间止于 2026-03-19**，
且本应用一条都没有。所以「本 job 没执行过」不是「log 表坏了」或「查错表」，
是真实的零执行。

---

## 3. 与 B-8 的关系（不重复、互补）

| 问题 | 答案来源 | 结论 |
|---|---|---|
| 运行时执行链是否读 `state` 列？ | B-8（本契约不复述） | 不读，state 不可达 |
| `state=10` 的流程能不能跑？ | B-8 | 不能——构建产物无生成类 + BaseInfo.json 无条目 |
| **谁调度迁移任务？** | **本契约 §1** | 平台 cron → JobEvent → JobListener → SeeyonJob.exec |
| **什么条件下会调度？** | **本契约 §2** | 六条同时成立；当前 `run_millis=-1` → 不触发 |
| **MigrationScheduler 与 udc_microflow_info 的关系？** | **本契约 §3.1** | 仅**设计态同行**，运行时链不读该表 |

### 3.1 与 `udc_microflow_info` 的实际关系

- 设计态：`udc_microflow_info` 里 flow `MigrationScheduler`（state=20、2 节点）对应生成类
  `MigrationSchedulerService`，jar 内有该类（B-8 §6.1 已配对）
- 运行态：调度链（§1）**全程不触碰** `udc_microflow_info` —— 它读的是 `ctp_job_info` /
  `ctp_job_cron` / Redis，以及 `MigrationSchedulerService` 这个编译期类
- 即：**`udc_microflow_info` 的 state 与「这个定时任务跑不跑」无关**；
  state=20 只是发布态标记，调度与否由 `ctp_job_cron.run_millis` 决定

### 3.2 一个必须记录的细节

`MigrationSchedulerService.migrationScheduler()` 偏移 97-99 打的是
`nodeId:SUB_MICROFLOW_4rGf5E caption:子流程(1) start SubMicroFlow`。

即「`MigrationScheduler` 流程 = 1 个**子流程节点**，它调 `MigrationService.executeAll()`」。
这与 `udc_microflow_info` 里 flow `MigrationScheduler` 记录 **2 节点**一致
（2 节点 = 1 子流程节点 + 1 结束/其他），是独立互证。

---

## 4. BLOCKED 与所需输入

| # | 阻塞项 | 所需输入 | 为什么本地拿不到 |
|---|---|---|---|
| 1 | `MigrationServiceService.executeAll()` 实现类 | test2 部署态 fatjar 的 `custom/service/microflow/` entry | 三个发布 jar（biz/facade/web）均无该实现；它是平台按微流程模型动态导出的 dubbo 服务，实现体在运行态 |
| 2 | `SUB_MICROFLOW_4rGf5E` 子流程定义 | `udc_microflow_info` 中 id=4rGf5E 的 `data_schema`，或页面导出 | 需按 nodeId 反查流程定义；本轮未展开（1 次只读查询可做，但属另一片） |
| 3 | 该 job 是否有历史执行 | `ctp_job_log` 归档表或删除行 | 表内 0 行且无归档表；只能证「当前无」，不能证「历史上从未」 |

**这三项都不影响 §0 的结论**：`run_millis=-1` 是当前配置的确定事实，
`ifle 40` 是字节码的确定事实，两者相乘即「不触发」。阻塞项只影响「更深一层能做什么」。

---

## 5. 边界与红线

- 0 次 `/service`、0 次写库、未 push
- DB 只读 5 次（`ctp_job_info` / `ctp_job_cron` / `ctp_job_simple` / `ctp_job_log`），
  全部 `SELECT`，无 `UPDATE`/`INSERT`/`DELETE`
- 证据等级 **STATIC + DB-READ**，不是 LIVE —— 没有触发一次真实调度（那需要改 `run_millis`，是写操作，超授权）
- 未改 B-6/B-7/B-8 已结项内容
- 版本口径：调度框架实测 `boot-starter-schedule-5.3.345` 与 `5.3.358`，两者
  `JobListener.lambda$processJob$0` 的 `exec()` 调用偏移同为 **434-435**、`ifle 40` 同在偏移 9；
  本契约引用 5.3.345 行号，两版无实质差异

---

## 6. 复现命令

### 6.0 复现纪律（两条，都是实测踩出来的）

**① 副本目录并发隔离。** 注入器与反向验证器各自建带 `pid + 时间戳` 后缀的副本目录
（`b9inj-<pid>-<ts>` / `b9rev-<pid>-<ts>`），也支持 `B9_OUTDIR` / `B9_REVDIR` 显式指定。
原因：早期版本用固定路径 `scratch/impl/b9inj`。两人同时跑同一注入器时共写 `inj.md`，
后跑者会读到先跑者的**在途注入残留**，基线变成 EXIT=1，看起来像「闸门基线就不通」。
实测发生过一次（main D71/D72 记录）。B-9 注入器跑得久（多次 javap），并发窗口比 B-7 大得多。

**② 变异锚点必须硬失败。** `b9_gate_reverse.py` 的 `variant()` 在锚点
不存在（MUT-NOT-FOUND）或不唯一（MUT-AMBIGUOUS）时 **`sys.exit(3)` 直接退出**，
不允许记一行「作废」继续跑。
原因：静默作废会让「变异没执行」看起来像「变异执行了但闸门没抓到」，
把「测试没跑」伪装成「测试结论」。这比断言写错更隐蔽——报告上只是一行 MUT-NOT-FOUND。
（D72 实测：D4 的锚点在我删掉 CRLF 死代码后失效，脚本当时记了「作废」而不是报错。）

```bash
# 解包
BIZ=<MAVEN_REPO>/com/seeyon/datamigration9000000000000000001-biz/1.0.7/datamigration9000000000000000001-biz-1.0.7.jar
FAC=<MAVEN_REPO>/com/seeyon/datamigration9000000000000000001-facade/1.0.7/datamigration9000000000000000001-facade-1.0.7.jar
SCH=<MAVEN_REPO>/com/seeyon/boot-starter-schedule/5.3.345/boot-starter-schedule-5.3.345.jar

JV=<USER_HOME>/...

# ④ 应用入口（看 @CtpSchedule jobName + 偏移 17 调 migrationScheduler）
$JV -p -c -v <biz>/com/seeyon/datamigration9000000000000000001/schedule/MigrationSchedulerSchedule.class

# ⑤ 转调 executeAll（偏移 149）+ 子流程 nodeId
$JV -p -c <biz>/.../domain/service/microflow/MigrationSchedulerService.class

# ⑥ 接口到实现
$JV -p -c <biz>/.../custom/appservice/microflow/DefaultMigrationServiceImpl.class

# ⑦ 接口无实现（三个 jar 都应输出 0）
unzip -l <biz> | grep -c MigrationServiceServiceImpl

# ① ② 关键判据 ifle 40
$JV -p -c <sch>/com/seeyon/boot/starter/schedule/CustomSchedule.class   # lambda$null$0 偏移 9

# ③ 决定性一跳 exec()
$JV -p -c <sch>/com/seeyon/boot/starter/schedule/event/listener/JobListener.class  # 偏移 434
```

DB 复现见 `<HERMES_HOME>/cache/scratch/impl/b9/q_cron.py` / `q5.py`（只读）。
