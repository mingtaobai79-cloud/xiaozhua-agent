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