# 自定义微流程 · 三种触发方式的 Java 契约（真机版）

> 证据等级：**模板 STATIC_RULE ＋ 生成物 LIVE ＋ 运行期 LIVE（EVENT / SCHEDULE）**
> CUSTOM+EVENT / CUSTOM+SCHEDULE 在 test2 真建、真构建、真部署、真触发
> 已验：事件监听全链路 + 定时调度全链路（第八节，日志原文）
> 未验：MANUAL 运行期调用、MESSAGE 源入参 DTO 约束（第四节）
> 用途：P0 结论，喂知识方案 D1

环境：test2 / app `datamigration163126498398523384`（数据迁移）
生成物取证：`1.0.279`，git `d1a8f95`；运行期取证：`1.0.282`；清理后：`1.0.283`
生成物原件：`docs/audit/p0-custom-trigger/build2-d1a8f95/`
（`build1-20261121T0348/` 是修复前对照）

---

## 一、结论（真机实证）

**三种触发最终都落到同一个接口 `CustomMicroFlowService`**，平台只生成调用方：

```
CUSTOM + MANUAL           DefaultCustomMicroFlowAppServiceImpl → service.<flow>(request.getData())
CUSTOM + BUSINESS_EVENT    {Flow}Listener(@EventSubscribe)      → appService.<flow>(SingleRequest.from(event))
CUSTOM + SCHEDULE          {Flow}Schedule(@CtpSchedule)         → appService.<flow>()
```

真机生成物（逐字，见 `build2-d1a8f95/`）：

```java
// facade/.../custom/service/microflow/CustomMicroFlowService.java   ← 我要实现的接口
public interface CustomMicroFlowService {
    default void p0CustomScheduleProbe( ) { throw new BusinessException(UDC_MICROFLOW_UNIMPLEMENTED_METHOD); }

    default void p0CustomEventProbe(
        com.seeyon.udc.common.event.BeforeCreateEvent<com.seeyon.datamigration163126498398523384.dto.AeProbeEntityDto>
        _BUSINESS_EVENT_ka3rXs) { throw new BusinessException(UDC_MICROFLOW_UNIMPLEMENTED_METHOD); }
}

// facade/.../api/microflow/CustomMicroFlowAppService.java           ← 平台对外契约
default SingleResponse<Void> p0CustomScheduleProbe() { ... }
default SingleResponse<Void> p0CustomEventProbe(SingleRequest<BeforeCreateEvent<AeProbeEntityDto>> request) { ... }

// biz/.../custom/appservice/microflow/DefaultCustomMicroFlowAppServiceImpl.java
public SingleResponse<Void> p0CustomEventProbe(@ParameterInfo("事件数据") SingleRequest<...> request){
    if(customMicroFlowService == null) throw new BusinessException(UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED);
    customMicroFlowService.p0CustomEventProbe(request.getData());
}

// biz/.../domain/event/listener/microflow/P0CustomEventProbeListener.java
@EventSubscribe
public void onBeforeCreateEvent(BeforeCreateEvent<AeProbeEntityDto> e) {
    if(customMicroFlowAppService == null) throw new BusinessException("自定义微流程还未开发，请联系开发人员！");
    customMicroFlowAppService.p0CustomEventProbe(SingleRequest.from(e));
}

// biz/.../schedule/P0CustomScheduleProbeSchedule.java
@CtpSchedule(jobName = "PcSpL2lTP5Xq1FGj", description = "P0-自定义定时验证")
public class P0CustomScheduleProbeSchedule implements SeeyonJob {
    public SingleResponse<?> exec() {
        if(customMicroFlowAppService == null) throw new BusinessException("自定义微流程还未开发，请联系开发人员！");
        customMicroFlowAppService.p0CustomScheduleProbe();
        return SingleResponse.ok();
    }
}
```

三条可直接落 D1 的判据：

1. **监听注入 `CustomMicroFlowAppService`，不是 `CustomMicroFlowService`。**
2. **定时无参**：`appService.<flow>()`；要传时间范围只能走 `SUB_MICROFLOW.attrs` 或读上下文。
3. **未实现的错误面两种**：MANUAL（DefaultImpl）抛 `UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED`；
   监听/定时 各自的 null 检查抛 `BusinessException("自定义微流程还未开发，请联系开发人员！")`。

设计态字段与签名对应（模板＋生成物双证）：

| 触发 | 设计态必须有 | 缺了会怎样 |
|---|---|---|
| MANUAL | `trigger.output.paramType` + 出参 | 无出参 → `void`，AppService 仍 `SingleResponse.ok()` |
| BUSINESS_EVENT | `messageInfo` + **顶层 `dataSchema.input`** | input 缺 → 监听带参、AppService 无参，下一轮构建编译失败 |
| SCHEDULE | `jobCaption`/`jobCode`/`scheduleCronRule` | 能生成；`jobCode` 即 `@CtpSchedule(jobName=…)`，空跑不可追踪 |

---

## 二、★ 这次踩到的真坑（build1 → build2）

**`CUSTOM + BUSINESS_EVENT` 必须把入参写进 `dataSchema` 顶层 `input`，只配 `trigger.output` 不够。**

```
build1  03:40 SUCCESS(1.0.278)  这一轮还没编到新生成物（平台是构建结束后才把生成代码 push 回 git）

错版    03:48 FAIL(20261121034832)  ← 编到了，直接炸在 javac：
        P0CustomEventProbeListener.java:[42,38] 无法将接口
        CustomMicroFlowAppService 中的方法 p0CustomEventProbe 应用到给定类型;
          需要: 没有参数
          找到: SingleRequest<BeforeCreateEvent<AeProbeEntityDto>>
        （dataSchema.input = null，AppService 无参，Listener 带参）

build2  补 schema["input"] = schema["trigger"]["output"] → update(state=20)
        03:57 SUCCESS / 04:01 SUCCESS（1.0.279），生成物签名对齐：
        AppService.p0CustomEventProbe(SingleRequest<BeforeCreateEvent<..Dto>> request)
        Service.p0CustomEventProbe(BeforeCreateEvent<..Dto> _BUSINESS_EVENT_ka3rXs)
        DefaultImpl: customMicroFlowService.p0CustomEventProbe(request.getData())
```

REST 直建的可靠顺序（否则埋一颗下一轮必炸的雷）：

```python
schema["input"] = trigger["output"]     # 顶层 input 必须显式给
# create → update(state=20) → deploy-normal → 轮询 build-info → git 拉生成物核对
```

方法名 = 流程 `name`；入参变量名 = `trigger.output.name`（形如 `_BUSINESS_EVENT_ka3rXs`，不是业务名）。
`MESSAGE` 源另有坑：根 `input` 缺 `javaType`/`name` 时构建期在
`BusinessEventListener.java.ftl` 约 117 行抛 `InvalidReferenceException`，`checkSchema` 兜不住。

---

## 三、构建状态怎么判（本轮实测，build-info 会滞后）

同一个 app 连续构建 5 次，`GET /service/udc/sandbox/build-info/{appId}` **一直停留 03:40 那次**
（1.0.278 SUCCESS），后面 4 次构建它的 `buildTime` 一个字没变。三处接口的可靠性排序：

| 判定面 | 可信度 | 说明 |
|---|---|---|
| `udc_deploy_record`（DB） | **权威** | `state` 0=未完成/排队, 1=成功, 2=失败；带 jar_version / build_version / msg |
| `udcRuntimeSearchDeployStatusDeployIdPost`（path `{deployId}`） | 权威（同一记录） | `state` SUCCESS/FAIL/RUNNING，失败时 `msg` 里带 backBuild.log 链接与 javac 原文 |
| `sandbox/build-info/{appId}` | **滞后** | 只反映最近一次「已写入」的构建，排队/刚完成时不可信 |

失败时 `msg` 里直接给原因（本轮实例）：

```
[ERROR] .../P0CustomEventProbeListener.java:[42,38] 无法将接口
CustomMicroFlowAppService 中的方法 p0CustomEventProbe 应用到给定类型; 需要: 没有参数
[ERROR] 详情链接: /service/app-sandbox/file/download?storageKey=compile-info/{appId}/{ts}/backBuild.log
```

判据：**不要用 build-info 判「这次构建成功没」**；本轮就因为只看 build-info，把一次 FAIL 误读成 SUCCESS。

## 四、仍未验证（下一轮）

1. **MANUAL 运行期**：三种触发里只有 MANUAL 没跑过端到端。需建一条 MANUAL 型 CUSTOM 流程
   （`restApi=1` 或 Dubbo 开放），调用 `…/{appName}/{flow}/…` 看是否落进手写实现。
   ⚠️ MANUAL 是**唯一允许改 `serviceInterface`** 的类型（第六节），改名这条路也只有它还没真跑。
2. `MESSAGE` 源的入参 DTO 是否必须与 `eventDataFullName` 一致。
3. `@CtpSchedule` 生成的类在**多租户**下是否每租户各跑一次（本轮日志见两个 tenantId 各一次，未拆解机制）。

> 已闭合（原列在这里，现已有实证）：监听真被触发 ✔、定时真被调度 ✔、biz jar 含生成类 ✔。

## 五、本轮创建的测试对象（已删除，留档在第九节）

```text
udc_microflow_info id=4620867461310390367  p0CustomEventProbe     CUSTOM + BUSINESS_EVENT  (RELEASE) → 已删
udc_microflow_info id=7674299753416331984  p0CustomScheduleProbe  CUSTOM + SCHEDULE         (RELEASE) → 已删
构建序列（供复现对照）：
  20261121034003 SUCCESS 1.0.278（未编到生成物）
  20261121034832 FAIL    1.0.278 ← 签名不一致，javac 原文见上
  20261121035659 SUCCESS 1.0.279
  20261121040103 SUCCESS 1.0.279
  20261121174700 SUCCESS 1.0.282 ← 运行期取证（EVENT）
  20261122         SUCCESS 1.0.282（重建，SCHEDULE 取证）
  20261122         SUCCESS 1.0.283 ← 清理后
```

---

## 六、`serviceInterface` 可自定义，但只对 MANUAL 成立（本轮真机实证）

字段：`udc_microflow_info.service_interface`（create/update body 同名）。默认 `CustomMicroFlowAppService`。

命名规则来自字节码 `MicroFlowCodeUtil.buildServiceClassName`（udc-biz 5.3.605）：

```
capitalize(name) → 按 "AppService" 切成两段 → 在第 1 段后插 "Service" → 拼回
  MigrationProbeAppService   -> MigrationProbeService            ✅
  CustomMicroFlowAppService  -> CustomMicroFlowService           ✅
  MigrationService           -> MigrationServiceService          ❌ 多一个后缀
```

生成三件套随名字走：

```
facade/api/microflow/{serviceInterface}                 对外契约（AppService 接口）
facade/custom/service/microflow/{buildServiceClassName}  业务接口 ← 手写实现它
biz/custom/appservice/microflow/Default{serviceInterface}Impl  兜底（按类型注入手写实现）
```

**但 EVENT / SCHEDULE 的模板把 `CustomMicroFlowAppService` 写死了**：

```
event/BusinessEventListener.java.ftl:16      import ${customMicroFlowPackage}.CustomMicroFlowAppService;
schedule/MicroFlowSchedule.java.ftl:10,37    import …CustomMicroFlowAppService; private CustomMicroFlowAppService …
```

⇒ **带事件/定时触发的流程改 serviceInterface 必编译失败**（本轮两次构建 FAIL 原文：
`找不到符号 类 CustomMicroFlowAppService 位置 程序包 …api.microflow`）。
结论：自定义接口名只适用于 MANUAL（REST / Dubbo）型自定义微流程。

## 七、手写实现类的落点：扩展工程 git，不是生成工程 git

| 仓 | 地址 | 性质 |
|---|---|---|
| 生成工程（五模块） | `autocode-test2/backend/datamigration<appId>` | **产物仓**：每次构建 force push 一个**无父提交**，历史只剩「发布应用:时间戳」 |
| 扩展工程（`-ext` 源码） | `extend-test2/backend/datamigration<appId>` | **源码仓**：手写代码写这里，构建时被拉进 `-ext` 模块 |

实测：往产物仓推过两次实现类，下一次构建后 `git log` 里我的提交消失、`find` 也找不到文件；
往扩展仓推一次后，构建产物 `…-ext-1.0.281.jar` 里能 `jar tf` 到
`com/seeyon/<app>/extend/microflow/MigrationProbeServiceImpl.class`。

## 八、运行期实证：监听与定时都已跑通（LIVE PASS）

**监听（CUSTOM + BUSINESS_EVENT）——全链路 LIVE PASS（1.0.282，2026-11-21 17:51）**

```
EventHandlerBeanPostProcessor:57 类[…P0CustomEventProbeListener$$EnhancerBySpringCGLIB$$…],
监听方法[onBeforeCreateEvent],是否异步[false],监听dto[…dto.AeProbeEntityDto]
P0CustomEventProbeListener:38  接收到“接口验证实体新增事件(操作前)”事件，触发“P0-自定义事件监听验证”微流程执行
MigrationProbeServiceImpl:39   [MF-PROBE][EVENT] 自定义微流程被事件触发 flow=p0CustomEventProbe id=null
                               name=P0-EVENT-PROBE eventType=BeforeCreateEvent
P0CustomEventProbeListener:43  成功执行微流程：P0-自定义事件监听验证
Subscriber:183                 …onBeforeCreateEvent…消费事件…耗时298
```

触发方式：探针实体没有页面/REST，外部造不出一条 create，所以在 ext 里加
`MicroFlowEventProbeRunner implements ApplicationRunner`，启动后用 `EventBus.publish(new BeforeCreateEvent<>(dto))`
发同类事件。⇒ 证明「监听器 → AppService → 手写 Service」接线正确；
**不证明**「平台在实体 create 时确实发这个事件」（那一步仍需真实 create）。

**定时（CUSTOM + SCHEDULE）——1.0.282 复验：登记了但被「停用」，且平台禁止 @Component**

启动失败实证（这就是为什么不能用 @Component 绕过）：

```
SeeyonApplicationRunListener:248 启动失败,datamigration163126498398523384-1.0.282
com.seeyon.boot.exception.BootException:
  调度类：[class …extend.microflow.ExtScheduleProbeJob]不能使用[Component]注解
```

⇒ 生成类**不加 @Component 是设计如此**，平台自己扫描 `@CtpSchedule` 注册 bean。之前「生成器漏注解」的推断作废。

DB 实况（1.0.282，18:02:44 建）：

```
ctp_job_info: job_name=PcSpL2lTP5Xq1FGj  job_caption=P0-自定义定时验证  status=0(停用)
ctp_job_log : 0 条
redis simple: test2:datamigration…::simple → PcSpL2lTP5Xq1FGj repeatInterval=5
```

**但同一版本里自写的 ext Job 跑通了**（`@CtpSchedule(jobName="P0ExtJobProbe0001", cron="0 */5 * * * ?")`，不加 @Component）：

```
18:27:40 本次创建初始化定时任务信息[{jobName:ExtScheduleProbeJob, jobCaption:P0ExtJobProbe0001, status:true}]
18:30:00 ExtScheduleProbeJob:31        [MF-PROBE][EXT-JOB] 外部 Job 被执行 job=P0ExtJobProbe0001
18:30:00 MigrationProbeServiceImpl:48  [MF-PROBE][SCHEDULE] 自定义微流程被定时触发 flow=p0CustomScheduleProbe
18:30:00 ExtScheduleProbeJob:38        [MF-PROBE][EXT-JOB] appService.p0CustomScheduleProbe() 调用完成
```

⇒ 结论（两条路径都实测过，均已 LIVE PASS）：

0. **把 `ctp_job_info.status` 置 1 后，平台生成的类真的跑起来了**（2026-11-22 16:27，同一 pod）：

```
16:27:00 CustomSchedule:106 读到redis中Simple[test2:…::simple][29922267]的job数据：
         [{jobName:PcSpL2lTP5Xq1FGj, repeatInterval:5, tenantId:-8112660841495312922, jobInfoId:8618752333562220226}]
16:27:00 P0CustomScheduleProbeSchedule:32  jobClass:[P0CustomScheduleProbeSchedule] jobName:[PcSpL2lTP5Xq1FGj] start!
16:27:00 MigrationProbeServiceImpl:48      [MF-PROBE][SCHEDULE] 自定义微流程被定时触发 flow=p0CustomScheduleProbe
16:27:00 ScheduleMetrics:39                Metric timer registered: schedule.ctp.success,PcSpL2lTP5Xq1FGj
16:30:00 MigrationProbeServiceImpl:48      （下一周期，两个租户各一次）
```

⇒ 生成类本身没问题，**缺的只是「启用」**；`status=0` 时 execute-onetime 也拒绝执行。
    注意 redis 里的 `jobInfoId`(8618752333562220226) 与 DB 行的 `id`(-1715330898652018468) 不一致，
    说明 redis simple 条目来自另一处缓存映射，改状态要改 DB 行、再由启动同步刷新 redis。

1. **平台生成的 schedule 类**：注解只带 jobName/description，**没有 cron**；调度时间来自 `ctp_job_info` + redis 记录，而记录默认 `status=0`（停用），所以永不执行。要跑得在「定时任务」里启用，或让发布环节带启用标志。
2. **ext 自写 Job**：只要 `@CtpSchedule` 上直接给 `cron`，启动即注册并在到点执行，链路和生成类完全相同（都走 appService → 兜底 impl → 手写 Service）。

REST 探针（说明停用是真的拦住了执行）：

```
POST /service/udc/jobInfo/execute-onetime {param1:id,param2:tenant}
  → BOOT_3000 "当前定时任务不存在或已删除或停用，无法执行"
POST /service/udc/jobInfo/update-status {param1:id,param2:true,param3:tenant}
  → BOOT_0000 SUCCESS 但 data.content=0，DB status 仍为 0（未改成功）
```

**事件触发入口缺失（本轮 BLOCKED）**：探针实体 `AeProbeEntity` 没有可用的对外入口——
生成的 `AbstractAeProbeEntityController` 上 `@RestController`/`@RestApi` 被注释掉，
`udc_entity.open_api_data` 为空，RestApi 元数据（redis `test2:Metadata:RestApi:<appName>`）里 0 条命中。
⇒ 要真正触发事件，得先给实体建页面（或用已有页面的实体）再走页面 create。

## 九、清理记录（2026-11-22）

删的是探针，不是结论；结论全在上面。

| 对象 | 处理 | 证据 |
|---|---|---|
| `p0CustomEventProbe` id=4620867461310390367 (RELEASE) | 设计态删除 | `udcMicroflowDeletePost` → code=BOOT_0000，回读 `get={}` |
| `p0CustomScheduleProbe` id=7674299753416331984 (RELEASE) | 设计态删除 | 同上 |
| 两条流程 data_schema | 先备份再删 | `docs/audit/p0-custom-trigger/cleanup-backup/flows.json` |
| ext `MigrationProbeServiceImpl` | 删除（流程删了，接口不再生成，留着编译失败） | commit `07f0d0e` |
| ext `MicroFlowEventProbeRunner` | 删除（每次启动发事件） | 同上 |
| ext `ExtScheduleProbeJob` | 删除（每 5 分钟触发） | 同上 |
| `ctp_job_info.PcSpL2lTP5Xq1FGj`（流程删后成孤儿任务） | 整行删除 | 整行先备份到 `cleanup-backup/ctp_job_info_row.txt`；DELETE `AFFECTED 1`，回读 COUNT=0 |
| `p0ManualProbe` id=2161771347477002763（CUSTOM+MANUAL，出入参取证用） | 设计态删除 | 整行先备份到 `cleanup-backup/manual_probe_flow.json`；`delete=True`，回读 `get={}` |
| 1.0.286 产物（Pod f5cbf7b8c-x5vqs，19:31 起） | 无探针类残留 | 4 个 jar（biz/ext/facade/web）`jar tf` 中 `p0Manual*`/`p0Custom*`/`CustomMicroFlowService` 全 0 命中 |

未删：`AeProbeEntity`（id=4308140192425942217，建于 2026-11-09）——早于本轮，属既有的「接口验证实体」，不是本次探针产物。

---

## 十、Agent 调用配方（看到「自定义微流程」需求就按这张表做）

### 10.1 三种触发 → 我要写的代码

| 触发 | 我实现什么 | 谁调我 | 我怎么被调到 |
|---|---|---|---|
| MANUAL | `CustomMicroFlowService` 里对应方法 | `DefaultCustomMicroFlowAppServiceImpl` | REST `@RestApi` 或 Dubbo 直接调 appService 方法 |
| BUSINESS_EVENT | 同上，入参是 `BeforeCreateEvent<XxxDto>` | 生成的 `{Flow}Listener`（`@EventSubscribe`） | 平台发事件时自动 |
| SCHEDULE | 同上，无入参 | 生成的 `{Flow}Schedule`（`@CtpSchedule`） | 定时器到点（需启用，见 10.4） |

```java
package com.seeyon.<appId>.extend.microflow;

@Slf4j
@Service                                  // ← 实现类必须能被注入（@Service/@Component 都行）
public class XxxMicroFlowServiceImpl implements CustomMicroFlowService {

    @Override
    public void p0CustomScheduleProbe() {          // 签名照抄接口 default 方法
        log.info("[MF] schedule 触发");
    }

    @Override
    public void p0CustomEventProbe(
            BeforeCreateEvent<AeProbeEntityDto> _BUSINESS_EVENT_ka3rXs) {   // 参数名带 hash 后缀，照抄
        log.info("[MF] event 触发 id={}", _BUSINESS_EVENT_ka3rXs.getData().getId());
    }
}
```

三条铁律：

1. **接口方法都是 `default` 且抛 `UDC_MICROFLOW_UNIMPLEMENTED_METHOD`** ——不实现不会编译失败，只会在运行时抛。所以「编译过了」不等于「实现了」。
2. **返回类型是 `void`**；`SingleResponse<Void>` 由 appService 兜底 impl 包，别自己 return。
3. **方法名/入参一字不改**：方法名 = 流程 `name`；事件入参 = `BeforeCreateEvent<实体Dto>`，参数名带 `_BUSINESS_EVENT_xxxx` 后缀（换名照样编译过，但别动，后续版本可能是判据）。

### 10.2 代码放哪：只放扩展工程

```
extend-test2/backend/<appId>   ← 手写实现写这里（构建会拉进 -ext jar）
autocode-test2/backend/<appId> ← 产物仓，每次构建 force push 无父提交，手写代码必被覆盖
```

落地验证（不看构建状态，看产物）：

```bash
jar tf /app/libs/BOOT-INF/lib/<appId>-ext-<ver>.jar | grep XxxMicroFlowServiceImpl
```

### 10.3 三处命名/注解，动之前先看这张表

| 想改 | 能不能改 | 证据 |
|---|---|---|
| `serviceInterface`（接口名） | **只有 MANUAL 能改** | EVENT/SCHEDULE 模板硬编码 `CustomMicroFlowAppService`（`.ftl:16` / `.ftl:10,37`），改了两轮构建都 `找不到符号` |
| 调度类加 `@Component` | **绝对不能** | 启动直接崩：`BootException: 调度类：[…]不能使用[Component]注解` |
| 生成物里的 `{Flow}Listener` / `{Flow}Schedule` | 别手改，改了下次构建覆盖 | 产物仓特性 |

改接口名的命名规则（`MicroFlowCodeUtil.buildServiceClassName`）：

```
XxxAppService → XxxService        （按 "AppService" 切两段，第一段后插 "Service"）
Xxx          → XxxServiceService  （不带 AppService 后缀会多一个 Service，别这么命名）
```

### 10.4 定时型必做的一步：启用

生成的 schedule 类**注解里没有 cron**，调度时间来自 `ctp_job_info` + redis，而新登记的任务默认停用：

```sql
SELECT id, job_name, status FROM ctp_job_info WHERE job_name='<jobName>';   -- status=0 ⇒ 永不执行
```

- 启用：`UPDATE ctp_job_info SET status=1 WHERE id=<id>`，再重启 pod 让 `CtpJobSyncService` 刷新 redis；
- 或用平台接口：`POST /service/udc/jobInfo/update-status`（实测传 `param1=id,param2=true,param3=tenantId` 返回 SUCCESS 但影响 0 行，**不可靠**，优先改库+重启）；
- 或干脆在 ext 里自写 `@CtpSchedule(jobName=…, cron="0 */5 * * * ?")` 的 `SeeyonJob` 调 `appService.<flow>()`——**这条路已 LIVE 验证**，但要记住 10.3 的禁 `@Component`。

### 10.5 怎么判断真的通了（只认日志）

```bash
# 事件
grep "接收到.*事件，触发.*微流程执行" <app>-info.log
grep "\[MF\] event 触发" <app>-info.log

# 定时
grep "jobClass:\[<Flow>Schedule\] jobName:\[<jobName>\] start" <app>-info.log
grep "\[MF\] schedule 触发" <app>-info.log
```

构建 SUCCESS、Pod Running、`udc_deploy_record.state=1` **都不算通**；只认上面这几行 + 你的实现里那句日志。

### 10.6 一次性对照清单（写需求前扫一眼）

```
□ 流程 name 与接口方法名一致？
□ 实现类在 ext 仓、有 @Service/@Component？
□ 事件型：入参类型 == BeforeEvent<源实体 DTO>？
□ 定时型：jobName 已启用（ctp_job_info.status=1）？
□ 定时型：调度类没加 @Component？
□ 改过 serviceInterface 吗？改过就只能用于 MANUAL
□ 部署后 jar 里有实现类？（jar tf 查，别信构建状态）
```

### 10.7 出入参：定义在哪、Java 侧长什么样

**定义**在设计器「参数」tab（入参/出参），写入 `dataSchema`；面板读写链路已实证
（`MICROFLOW-PARAMS-TAB-DATACHAIN.md`：`udcMicroflowFindByIdGet` → `dataSchema` → `jsonSchema`）。

三型在 Java 侧的入参（生成物原文，`build2-d1a8f95/`）：

```
MANUAL          appService  <Flow>(SingleRequest<XxxDto> request)   → 实现里 request.getData()
                service     <Flow>(XxxDto xxx)                      ← 生成签名待 MANUAL 实跑确认，UNVERIFIED
EVENT           appService  <Flow>(SingleRequest<BeforeCreateEvent<XxxDto>> request)
                service     <Flow>(BeforeCreateEvent<XxxDto> _BUSINESS_EVENT_xxxx)   ← listener 里 SingleRequest.from(event)
SCHEDULE        appService  <Flow>()
                service     <Flow>()                                 ← 无入参
```

取数据只用两个方法（`boot-core` 字节码）：

```java
SingleRequest.from(T data)     // 包装
request.getData()              // 取值
```

**出参只在 MANUAL 有意义**，因为只有它有"调用方"：

```
MANUAL     调用方是外部（REST/Dubbo/其他服务）→ 需要回值 → 生成签名带出参   ← 正在验（见下）
EVENT      监听器触发完只写日志，不消费返回值  → 生成 void        ⇒ 天然无出参
SCHEDULE   调度器只要一个 ok                   → 生成 void        ⇒ 天然无出参
```

（此前本文写成"整体没有出参回传通道"，是拿 EVENT/SCHEDULE 的生成物当成了三型共性，已更正。）

MANUAL 出参 **已实证**（`p0ManualProbe`，id=2161771347477002763，入参 BASIC STRING「P0入参」／
出参 BASIC STRING「P0出参」，构建 `发布应用:20261122192211435`）：

```java
// facade/custom/service/microflow/CustomMicroFlowService.java   ← 我要实现的
default java.lang.String p0ManualProbe(java.lang.String _FLOW_INPUT_P0IN01)

// facade/api/microflow/CustomMicroFlowAppService.java           ← 对外契约
default SingleResponse<java.lang.String> p0ManualProbe(SingleRequest<java.lang.String> request)

// biz/custom/appservice/microflow/Default…Impl.java
public SingleResponse<java.lang.String> p0ManualProbe(
        @ParameterInfo("P0入参") SingleRequest<java.lang.String> request) {
    if (customMicroFlowService == null) throw …UDC_MICROFLOW_INTERFACE_NOT_IMPLEMENTED;
    return SingleResponse.from(customMicroFlowService.p0ManualProbe(request.getData()));
}
```

⇒ **入参 = 方法形参，出参 = 方法返回值**，appService 再包一层 `SingleResponse.from(...)`。
参数名 `_FLOW_INPUT_xxx` 是面板生成的内部名，`desc` 才是业务名（进 `@ParameterInfo`）。

★ **写 `dataSchema` 必须镜像到顶层**：`trigger.output` → `dataSchema.input`、`endNode.output` → `dataSchema.output`。
只写 trigger/endNode 时生成器视作无参（实测：同样一条 MANUAL 流程，只写 trigger+endNode →
生成 `void p0ManualProbe()`；补上顶层 input/output 并重新发布后 → 才生成 `String p0ManualProbe(String)`）。

### 10.8 UDC 生成物清单：哪些能引用、哪些碰不得

`<app>-facade` / `<app>-biz` 里与自定义微流程相关的就这几类（路径来自 `build2-d1a8f95/`）：

| 生成物 | 我能做什么 |
|---|---|
| `facade/api/microflow/{serviceInterface}.java` | **调**：注入它调流程（事件/定时就是走这里） |
| `facade/custom/service/microflow/{XxxService}.java` | **实现**：手写类 implements 它 |
| `facade/dto/{Entity}Dto.java` | **引用**：事件入参、对象读写都用它 |
| `facade/api/{Entity}AppService.java` | **引用**：创建/更新自定义对象 |
| `biz/custom/appservice/microflow/Default{...}Impl.java` | 别改：兜底 + 注入我的手写实现（`@Autowired(required=false)`） |
| `biz/domain/event/listener/microflow/{Flow}Listener.java` | 别改：`@EventHandler` + `@Transactional(REQUIRED)`，`success` 日志也在里面 |
| `biz/schedule/{Flow}Schedule.java` | 别改：`@CtpSchedule` + `MicroFlowRuntimeUtil.saveDefaultValue4RequestContext()` |

依赖不用自己加：手写实现只 import facade 的包（`<app>.custom.service.microflow`、`<app>.dto`、
`<app>.api.microflow`），而 ext 模块本来就依赖 facade。

### 10.9 自定义对象：建、拿、用

实体一经创建，应用里就有三件（`AeProbeEntity` 实例）：

```
facade/dto/AeProbeEntityDto.java           字段驼峰（probeAmount / probeStatus / createTime …）
facade/api/AeProbeEntityAppService.java    读写入口
facade/enums/…                             实体带枚举时才有
```

`{Entity}AppService` 的方法（字节码原文，全部 `SingleRequest<…>` 包一层）：

```java
SingleResponse<Long>            create(SingleRequest<Dto>)
SingleResponse<Dto>             createWithResult(SingleRequest<Dto>)
SingleResponse<Integer>         createBatch(SingleRequest<List<Dto>>)
SingleResponse<Integer>         update(SingleRequest<Dto>)
SingleResponse<Integer>         updateWithFields(SingleRequest<Map<String,Object>>)
SingleResponse<Dto>             updateWithResult(SingleRequest<Dto>)
SingleResponse<ResultDto>       create4Bpm / update4Bpm     // 走流程时用
```

写进自定义微流程里最长这样：

```java
@Autowired(required = false) private AeProbeEntityAppService aeProbeEntityAppService;

AeProbeEntityDto dto = new AeProbeEntityDto();
dto.setProbeName("from-microflow");
SingleResponse<Long> r = aeProbeEntityAppService.create(SingleRequest.from(dto));
```

两条路二选一，别混：**代码里调 AppService**（上面）｜**编排里用「插入数据」节点**（`CREATE_ENTITY`，
必填 `structure`/`mappingType`/`title`，见 `MICROFLOW-CREATE-ENTITY-CONTRACT.md`）。
DTO 字段是驼峰、库里是下划线（`shortName ↔ short_name` 已实测对照过 organization）。

### 10.10 这块还欠什么（写需求前心里有数）

```
VERIFIED    MANUAL 生成签名（入参=形参、出参=返回值、SingleResponse.from 包装）
UNVERIFIED  MANUAL 的 REST 端到端调用（需 restApi 开启；生成物已证明契约，调用链未跑）
UNVERIFIED  MESSAGE 源入参 DTO 是否必须等于 eventDataFullName
UNVERIFIED  @CtpSchedule 多租户分发机制（只见两租户各跑一次）
```