# UDC_MICRO_FLOW_04004「依赖应用已删除」= input/output 的 appName 未跨接依赖应用表

> 领域：微流程一致性检测（`UDC_MICRO_FLOW_04004` = `UDC_MICRO_FLOW_NODE_DATA_ERROR`）
> 状态：**LIVE PASS**（test2 app 8704025620829192834）+ **VERIFIED_STATIC_BYTECODE**（udc-biz 5.3.517）
> 代码：`components/udc/microflow_constraints.py`（`validate_input_output_dependency` /
> `input_output_detection_branch` / `LIVE_R44_ARMS`）；护栏 `tests/udc/test_microflow_constraints.py`（+6）
> 关联：`draft-warn-masking-mechanism.md`（04003 掩蔽）、`appname-key-npe-and-connector-target.md`
> （`trigger.output.appName` 缺键的**另一**分支）、`consistency-detection-workflow.md`

## 0. 一句话

`input` / `output` 参数里写着 `appName = <本应用>` **但没写 `inApp`** 时，该参数会被当**外部应用**参数，
拿本应用名去 `udc_dependent_application`（**只登记外部应用**）里查 ⇒ 查不到 ⇒ **ERROR 04004「依赖应用已删除」**。
把 `inApp` 显式置 `true` 即清零（LIVE 1→0，可逆）。**appName 必须落在依赖应用表内；本应用资源必须用 inApp 表达。**

## 1. 字节码权威（CFR，`com/seeyon/udc/microflow/util/CheckUtils.java`）

```
check():282-287   if triggerType == MANUAL  ->  NodeInfo "微流程入参" -> detectionInputOutput(context, input, ni)
check():294-297   **无条件** -> NodeInfo "微流程出参" -> detectionInputOutput(context, output, ni)

detectionInputOutput():315-341
    boolean inApp = parameterDefDto.getInApp().booleanValue();        // ← 分支只由 inApp 决定
    inApp == true  -> detectionStructure(...)                          // 本应用资源；此处不查 appName
    inApp == false -> detectionApp(parameterDefDto.getAppName(), ..., "app")   // ← ERROR 抛点
                      + isRealGlobalDetection 时再走 checkOpenApi

detectionApp():543-556   detectionEnum == GLOBAL:
    if appNameSet.contains(appName) break;   // 表内 -> 放行
    else error(... APP_DELETE)               // 表外 -> '依赖应用已删除'

appNameSet 来源: ImmutableNodeContext.from():174
    appDtoMap = MetadataUtils.getUdcDependentApp(ctx)   // "com.seeyon.udc.entity.domain.entity.DependentApplication"
    appNameSet = appDtoMap.values().map(DependentApplicationDto::getDepAppName)
```

两条推论：

1. **`inApp` 是 `Boolean` 包装类型**（`MicroFlowParameterDefDto:27`）⇒ 键缺失 = `null`
   ⇒ `getInApp().booleanValue()` 若被走到即 NPE；实测**键缺失走的是非 inApp 分支**（与显式 false 同结论，见 §2 臂 B/E0）。
2. `toStructure()`（`:61-71`）把 `appName` 原样带进 Structure，`udcApp` 默认 true ⇒ 结构面与依赖面是**两条独立判据**。

## 2. LIVE 单变量臂矩阵（app 8704025620829192834，对象 `-1014184770817921434`）

对象：微流程「小爪标准微流程-全节点流转(最终)」（当时 `state=RELEASE`、`triggerType=MANUAL`、`type=3 CUSTOM`）。
检测范式：`do/detection` → 轮询 `do/detection-state` 到 `status!=doing` → `search/detection`；DB 以 `state`/`data_schema` 回读。

| 臂 | 变更（单变量） | 检测面（本对象） | DB state |
|---|---|---|---|
| **E0** 原状 | `input.inApp` **键缺失**；`appName=本应用` | **ERROR 04004「微流程入参:依赖应用已删除」** | 20 |
| **E1** 修复 | `input.inApp=true`（appName 不动） | **ERROR 清除（err 1→0）** | **20 ✅** |
| **B** 负控 | `input.inApp=false` | ERROR 复现「依赖应用已删除」 | 20 |
| **C** 负控 | `inApp=false` + `appName='bpm'`（已注册依赖） | 换码：04004「所选应用与当前微流程的 OpenApi标识不匹配」 | 20 |
| **D** 陷阱 | `inApp` 键缺失 + `appName=null` | **假干净**：ERROR=0，但 state 被压回 **10**（04003 掩蔽） | 10 |
| **R** 还原 | 回到 E0 原 `dataSchema` | ERROR 复现（err=1） | 20 |

要点：

- **E1 与 B 只差一个 `inApp` 的取值，结论相反** ⇒ 一元判据；R 臂证明可逆。
- **键缺失 ≠ 安全**：E0 与 B 同分支同结论（多次复现，E0 两次、R 一次）。
- **C 臂是「换病不治病」**：跨过 `detectionApp` 后又撞 `checkOpenApi`；`isRealGlobalDetection` + `type∈{SERVICE,CUSTOM}`
  才做该判定（实测）⇒ 改 `appName` 不是修复路径。
- **D 臂是「假干净」**：`checkSchema/update` 返回 `check:true,errors:0` 且检测面 `errorCount=0`，
  但 DB `state=10` ⇒ 04003 短路取代 04004。**`errorCount=0` 单独不可作修复证据**（第 5 个独立实例）。
- **`checkSchema` 对 E1/B 两臂都是 `check:true,errors:0`** ⇒ 浅校验完全看不到本判据。

## 3. 为什么「更新 API 文档 20-30 次」也改不动（并发写入者）

本轮探测期间，该对象被**并发本地工作流**改写（git `91b9d9e` 16:42:39「微流程 update 禁硬编码
type/state，恢复全节点流转为标准微流程(SERVICE/0)」）：

```
data_schema 149955 字节 -> 123702 字节 ; type 3 -> 0 (SERVICE) ; state 20 -> 10 (DRAFT)
```

后续每轮重读该对象都是「原始形态」⇒ 表现为「我改了又不动」。**根因是并发写入，不是判据失效。**
⇒ 处置：本任务**不再回写该对象**，结论只以**臂级即时读数**（每臂当场 REST+DB 双面）为准；
已登记 `LIVE_R44_CONCURRENT_WRITER`。**排查此类现象先看 `git log` 与该行的 `update_time`/`version`。**

## 4. 可复用判据（无需 RELEASE，零风险）

```python
from components.udc.microflow_constraints import validate_input_output_dependency
dep = {r["dep_app_name"] for r in udc_dependent_application WHERE app_id=<appId>}
validate_input_output_dependency(ds["input"], dep)    # [] = 不会触发 APP_DELETE
validate_input_output_dependency(ds["output"], dep, label="output")
```

- `inApp=true` ⇒ 直接通过（不查 appName）。
- `inApp` 缺失/`false` ⇒ `appName` 必须是**表内**的外部应用名；写本应用名 = 必报 04004。

## 5. 诚实边界

1. `checkOpenApi` 的完整真值面**未取到**（`isRealGlobalDetection` + SERVICE/CUSTOM 已实测，
   内部判据字节码未闭合）⇒ `validate_input_output_dependency` 对「表内 appName」只放行、**不承诺**不撞 OpenApi。
2. `inApp` 键缺失时 `getInApp().booleanValue()` 的精确执行路径（是否另有 null 保护）**UNVERIFIED**；
   实测结论「键缺失 == 非 inApp 分支」是行为级事实，非行级定位。
3. 本轮对**目标对象**的多次写均为探测，已确认不会破坏其历史（E0/R/E1 三面一致）；但该对象随后被
   并发工作流改写并压回 DRAFT ⇒ **本轮不主张该对象的最终配置状态**。
4. 本文件不登记任何客户业务明细；对象均为本任务自建实验对象。
