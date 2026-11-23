# 监控 · Prometheus 指标 · 环境标识 · Tomcat 定制

## Capability

平台可观测与运行时定制的四块：

```
boot-starter-monitor       /health、JVM、线程、模块 jar 信息
boot-starter-prometheus    @MetricMethod* 注解 + AOP 自动埋点
boot-starter-environment   环境/系统模式（test/uat/prod，方向参数）
boot-starter-tomcat        Tomcat 定制（无 Session、线程池监控）
```

## Version

均 5.3.600（`prometheus` 5.3.600）。

## ★ 一、监控端点（monitor）

```java
HealthController extends BaseController
  SingleResponse<String> healthCheck(HttpServletResponse);
  SingleResponse         jvmCheck(HttpServletResponse);

MonitorCollectorController extends BaseController
  Map<String, BuildInfo>      jarInfo();               // 每个模块 jar 的构建信息
  Map<String, Object>         jvm();
  Map<String, Object>         getJvmMonitoringInfo();
  Map<String, Object>         threadInfo(HttpServletResponse);
```

⇒ **排查「线上是不是这个版本」用 `jarInfo()`**（BuildInfo 里就有版本与构建时间），
比翻镜像 tag 可靠。`HealthProperties` 控制健康检查细节。

## ★ 二、Prometheus 埋点（prometheus）

```java
@MetricMethodCounter(metricType=..., metricName=...)
@MetricMethodGauge(metricType=..., metricName=...)
@MetricMethodHistogram(...)
@MetricMethodSummary(...)
public void myBiz() { ... }
```

注解只有两个属性（`metricType` / `metricName`）；底层四个 Aspect：
`MethodCounterAspect` / `MethodGaugeAspect` / `MethodHistogramAspect` / `MethodSummaryAspect`
（共同基类 `AbstractMetricMethodAspect`）。

⇒ 客开要给自己的方法加指标，就贴注解，不要自己注册 `MeterRegistry`。

## ★ 三、环境标识（environment）

```java
CtpSystemAppService.depends(SingleRequest<Void>) → ListResponse<BuildInfo>   // 依赖模块清单

CtpSystemEnvController extends BaseComponentController
  SingleResponse<Boolean>          isTargetEnvironment(CtpSystemModelType);
  SingleResponse<CtpSystemEnvDto>  select();
  SingleResponse<Boolean>          save(CtpSystemEnvDto, Boolean);
  SingleResponse<CtpSystemDirectionAllDto> selectDirection(CtpSystemEnvDto);

配置：CtpSystemEnvProperties
枚举：CtpSystemModelType / CtpSystemEnvEnum
```

⇒ **代码里判环境用 `isTargetEnvironment`，不要自己读 host 或 profile**。

## ★ 四、Tomcat 定制（tomcat）

```java
TomcatMonitorController.threadPoolInfo(HttpServletResponse)   // Tomcat 线程池
NoSessionManager extends org.apache.catalina.session.ManagerBase   // ★ 不用 Session
TomcatCustomizer / TomcatComponentInitializer / TomcatAutoConfiguration
```

⇒ 平台**默认不依赖 HttpSession**（`NoSessionManager`），所以别在客开里放东西进 Session。

## Side Effects

- `@MetricMethod*` 会为每个方法生成指标，方法级高频调用会带来可观开销。
- `CtpSystemEnvController.save` 会改环境配置（谨慎，属运维操作）。
- `threadInfo` 会 dump 线程栈，频率高会 STW。

## Known Constraints

1. 四个指标注解的属性只有 `metricType` / `metricName`，没有 bucket/quantile 细粒度配置。
2. `isTargetEnvironment` 参数是 `CtpSystemModelType`（系统模式），不是字符串。
3. `NoSessionManager` 意味着 **Session 不可用**——这是平台设计，不是 bug。
4. `jarInfo()` 返回的是 `BuildInfo`（含构建时间），与镜像 tag 可能不一致时以它为准。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `HealthController` 2 方法 / `MonitorCollectorController` 4 方法 | `javap -p` | VERIFIED_STATIC_BYTECODE |
| 4 个指标注解（2 属性）+ 4 个 Aspect | 同上 | VERIFIED_STATIC_BYTECODE |
| `CtpSystemEnvController` 4 方法 + `CtpSystemAppService.depends` | 同上 | VERIFIED_STATIC_BYTECODE |
| `NoSessionManager extends ManagerBase`、`TomcatMonitorController` | 同上 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 类与签名可复核
- ⚠️ 未真机打指标/查健康端点

## 给 Agent 的判据

```
线上跑的是哪个版本   → MonitorCollectorController.jarInfo()（BuildInfo）
给方法加指标        → @MetricMethodCounter/Gauge/Histogram/Summary
判当前环境          → CtpSystemEnvController.isTargetEnvironment(CtpSystemModelType)
别用 HttpSession    → 平台是 NoSessionManager，会话靠 token
```
