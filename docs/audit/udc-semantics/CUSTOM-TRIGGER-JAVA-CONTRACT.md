# 自定义微流程 · 三种触发方式的 Java 契约（真机版）

> 证据等级：**模板 STATIC_RULE ＋ 真机生成物 LIVE**
> CUSTOM+EVENT / CUSTOM+SCHEDULE 在 test2 真建、真构建、真拉产物
> 未验：运行期触发（发事件 / 跑定时）→ 第三节
> 用途：P0 结论，喂知识方案 D1

环境：test2 / app `datamigration163126498398523384`（数据迁移）
构建：`1.0.279`，git `d1a8f95`
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

1. **监听是否真被触发**：需实现 `CustomMicroFlowService` 并部署，再对该实体做一次 create，
   看 `<app>-info.log` 有「接收到…事件，触发…微流程执行」且 `success=true`。
2. **定时是否真被调度**（`@CtpSchedule` 是否被扫到；可走 `jobInfo/execute-onetime` 手工触发）。
3. build2 的 biz jar 是否已含 `custom/service/microflow` 类（本轮只验了 git 生成物，未复查 jar）。
4. `MESSAGE` 源的入参 DTO 是否必须与 `eventDataFullName` 一致。

## 五、本轮创建的测试对象（验完运行期再删）

```
udc_microflow_info id=4620867461310390367  p0CustomEventProbe     CUSTOM + BUSINESS_EVENT  (RELEASE)
udc_microflow_info id=7674299753416331984  p0CustomScheduleProbe  CUSTOM + SCHEDULE         (RELEASE)
构建记录：
  20261121034003 SUCCESS 1.0.278（未编到生成物）
  20261121034832 FAIL    1.0.278 ← 签名不一致，javac 原文见上
  20261121035659 SUCCESS 1.0.279
  20261121040103 SUCCESS 1.0.279（当前运行版本）
  20261121040716 state=0 未收敛（重复触发的那次，app 本身不受影响；待它自己收敛或作废）
删除前先备份两行 data_schema
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

## 八、运行期：监听已注册，定时未注册

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
| `ctp_job_info.PcSpL2lTP5Xq1FGj.status` | 1 → 0（恢复停用） | `AFFECTED 1`，回读 status=0 |

未删：`AeProbeEntity`（id=4308140192425942217，建于 2026-11-09）——早于本轮，属既有的「接口验证实体」，不是本次探针产物。