# `output.appName` 缺键 = 检测面硬 NPE；CONNECTOR 监听目标 = 连接器动态 DTO

> 应用 `8704025620829192834`（test2）。权威字节码：`udc-biz-5.3.517`（本仓反编译件 `docs/audit/artifacts/scratch-migrated/cfr-r31b`）。
> 日期：2026-10-16（第四十三轮）。状态：**FOCUSED VERIFIED（CFR + LIVE 双侧）**。

## 0. 一句话

MESSAGE 源监听的 `output.appName` **键缺失或为 null** 会让整个应用的异步一致性检测
**中止并返回 `System Error[java.lang.NullPointerException]`**——`checkSchema` 四臂全绿，
唯一可分辨的观测面是 RELEASE 后的 `detection-state.status`。
另：CONNECTOR 源监听的**唯一合法目标**是 `cip.connector.dynamic.dto.*`，而该族 DTO
在 test2 的 `filter/mq` 读面上**恒不可见**（0 条）。

## 1. ★ 单变量 2×2（LIVE，每臂 REST + MySQL `state=20` 双面确认）

对象：微流程 `3832725036227491834`（`xzhMsgBusL1` / 小爪消息总线监听，SERVICE / BUSINESS_EVENT）。
原始 schema sha256 = `a6c6f9ebb632d92923c26ebde2e3544957cae9204d9f0f81df2fdf96bb7eede7`。

| 臂 | `output.appName` | `eventDataFullName` | checkSchema | detection-state | search/detection |
|---|---|---|---|---|---|
| A | 存在 = `bpm`（外部） | `...bpm.dto.message.event.BpmStartEvent` | `check:true, errors:0` | `SUCCESS` | 该对象 **0 条**（干净） |
| B | 存在 = 本应用 | `...bpm.dto...BpmStartEvent` | `check:true, errors:0` | `SUCCESS` | 0 条 |
| C | **`null`** | 同上（外部） | `check:true, errors:0` | **`FAIL` / NPE** | **0 条（整轮无结果）** |
| D | **键缺失** | 同上（外部） | `check:true, errors:0` | **`FAIL` / NPE** | 0 条 |
| E | 存在 = 本应用 | **本应用**微流程 DTO `...dto.microflow.Htxqcqrct7yk` | `check:true, errors:0` | `SUCCESS` | 0 条 |
| F | **键缺失** | **本应用**微流程 DTO | `check:true, errors:0` | **`FAIL` / NPE** | 0 条 |

⇒ **自变量只有「`output.appName` 是否存在且非 null」**；`eventDataFullName` 是外部 DTO
还是本应用 DTO **同结论**（C/D 与 F 三臂都 NPE，A/B/E 三臂都干净）。

NPE 原文（`detection-state` 原始返回）：
```json
{"validate":true,"appId":"8704025620829192834","status":"FAIL",
 "message":"System Error[java.lang.NullPointerException]",
 "count":"0","errorCount":"0","seriouCount":"0","warnCount":"0"}
```

## 2. 判据链（CFR，逐行）

| # | 位置 | 语义 |
|---|---|---|
| 1 | `CheckUtils.detectionTrigger:1388` | `boolean inApp = isInAppEventOrMessage(trigger, applicationDto)` |
| 2 | `CheckUtils.isInAppEventOrMessage:1496-1502` | `EVENT -> true`；否则 `Optional.ofNullable(output).map(getAppName).map(applicationDto.getName()::equals).orElse(true)` |
| 3 | 同 2 `orElse(true)` | **键缺失/null ⇒ 判为 inApp=true**（不是报错，是静默改道） |
| 4 | `CheckUtils.detectionTrigger:1389-1422` | `MESSAGE && inApp` ⇒ 走 `context.getDtoMap()` 支（GLOBAL 下查 dtoMap） |
| 5 | `CheckUtils.detectionTrigger:1412` | `MESSAGE && !inApp && GLOBAL` ⇒ `detectionApp(refAppName = trigger.getOutput().getAppName(), …)` |
| 6 | `CheckUtils.detectionApp:543-544` | `Set<String> appNameSet = context.getAppNameSet()` → `appNameSet.contains(appName)` |
| 7 | 实测 | 该调用路径在 `appName == null`（且键缺失）时抛 **NPE**，整轮 detection 中止 |

★ 注意第 3 与第 7 的组合反直觉：**`orElse(true)` 本应把 null 变成 inApp 支**，
但实测走进 NPE —— 说明抛点不在 `detectionApp`，而在 `isInAppEventOrMessage`
或其后置链（`trigger.getOutput()` 相关）。**精确抛点未定位（UNVERIFIED）**；
可断言的是**充分判定**：`appName` 键缺失/null ⇒ detection `FAIL/NPE`，四条臂 4/4 复现，确定性。

## 3. 这条与「不变量 3」并列：checkSchema 绿 ≠ 对

- 四臂 `checkSchema` **全部** `{"check": true, "errors": 0, "errorMessage": null}`；
- 唯一分辨面 = `POST /udc/application/do/detection` → 轮询 `do/detection-state` → `status`；
- ★ 附带陷阱：NPE 时 `search/detection` 返回 **0 条**。**「0 条」不等于「没问题」**，
  必须结合 `status=FAIL` 判为「中断」。历史上把「该对象在检测面消失」读成「修好了」的
  写法（第三十二轮 A 臂）在这里会得到**反向结论**。

## 4. CONNECTOR 源：合法目标 = 连接器动态 DTO

### 4.1 CFR 判据
| 位置 | 语义 |
|---|---|
| `MicroFlowUtil:134` | `CONNECTOR_DYNAMIC_DTO_MARKER = "cip.connector.dynamic.dto."` |
| `FullNameUtil.isConnectorDto:320` | `fullName.contains(marker)`（**contains**，非 startsWith） |
| `ConnectorDtoFullNameCollector.extractDtoFullNameByTrigger:98` | 只有 `isConnectorDto(output.javaType)` 为真的 output 才进 `connectorDtoMap` |
| `CheckUtils.detectionTrigger:1452-1459` | `if (!context.isRealGlobalDetection()) return;` 然后 `!connectorDtoMap.containsKey(output.javaType)` ⇒ `EVENT_DATA_DELETE`（propertyKey=`messageInfo`） |
| `MicroFlowDetectionMetadataAware.putDtoMetadata:125-137` | `connectorDtoMap` 用 `search.appName = depApp.getDepAppName()` 查 —— 依赖 `udc_dependent_application` 里存在该 `dep_app_name` 行 |

⇒ **硬结论**：`cip-capability` 的 7 条 `topic=CONNECTOR_CALLBACK`（支付/印章/日程/签署/商旅/会议）
是 connector **方法参数 DTO**（`cip.capability.dto.*`），**不是合法监听目标**
（第四十二轮负控 E 实测报 `04004 / propertyKey=messageInfo`）。

### 4.2 合法目标真身在另一条通道（存储面 LIVE）
```
DB   : cip_connector_test2.cip_linker_metadata_info       （54 行）
tokens: linker_type {0:33, 2:5, 3:2, 4:1, 5:13}
prefix: com.seeyon.cip.connector.dynamic.dto.<链路名>.<DTO名>
样本  : VDAIBANJICHENG=V5待办集成 / ZHJHZZTB=客户方_组织集成 /
        CESHIDANDIANDENGLU=测试单点登录 / JICHENGCESHI=集成测试 /
        CESHIYINGYONG=测试应用 / FASONGXIAOXI=发送消息
```
（另：本应用 `udc_dependent_application` 确有 `dep_app_name='cip-connector'`
`dep_app_version='5.3.286'` 一行，id=`8128767151459159276`。）

### 4.3 ★ 读面错配（诚实边界）
前端「事件选择 → 应用间」弹层走 `POST /udc/microflow/filter/mq`，实测（4 个应用 × 3 个应用名）：

| appName | 8704025620829192834 | 2378987216360786643 | 3289082814923688017 | 1656355078954763084 |
|---|---|---|---|---|
| `cip-connector` | **0** | **0** | **0** | **0** |
| `cip-manager` | **0** | **0** | **0** | **0** |
| `cip-capability` | 7 | 7 | 7 | 7 |

⇒ 平台面**取不到**合法 CONNECTOR 目标；旁证：500 条微流程里 `messageSource` 直方图
`{EVENT:12, MESSAGE:8, MICRO_FLOW_EVENT:3}` —— **CONNECTOR 0 条**（全租户）。

因此本轮**未能**给出 CONNECTOR 正例的「回读逐键一致」证据：第三十三轮那 4 条含
`cip.connector.dynamic.dto.*` 字样的微流程，其 `trigger.type` = `MANUAL`、`messageInfo` = `null`
（动态 DTO 出现在**节点参数**里，不是 trigger 监听目标）。合法目标需要先建连接器链路
（`cip_linker_*` 写链，不在本轮范围）⇒ 属**环境前置**，不是判据缺失。

## 5. 诚实边界

1. **NPE 精确抛点 UNVERIFIED**：可断言「appName 缺键/null ⇒ FAIL/NPE」（4/4 复现，确定性），
   未定位到具体行。
2. **WARN 计数是移动量**：`LIVE_DETECTION_WARN_COUNT_IS_MOVING_SNAPSHOT = True`。
   本文件记录那一轮 9；第四十三轮实测同应用为 **6**，构成是
   `{UDC_CE_MICRO_FLOW_04003: 5, UDC_MICRO_FLOW_04009: 1}`
   （标品事件监听 / 标品服务定义 / 标准微流程-真数据全节点 / 标准微流程-全节点流转(最终) /
   消息总线监听 + 页面规则-全前端节点）。
   ★ 与历史快照的 9 **不是同一批对象** ⇒ 只可比较「计数是否自洽」，不可比较「对象是否减少」。
   引用它做判据断言必须重新实测。
3. **CONNECTOR 正例未取得**（§4.3 的读面错配是环境前置）。
4. **未验证**：非 MESSAGE/CONNECTOR 源（EVENT / MICRO_FLOW_EVENT）的 `appName` 缺键行为
   —— CFR 上 `EVENT` 在 `isInAppEventOrMessage:1498` 直接 `return true`，不读 `appName`，
   故**推断**不受影响，但**未做 LIVE 负控**。
5. **收尾**：本轮所有臂发布后均以 `POST /udc/microflow/update` 还原为 DRAFT，
   双面确认 `REST state=DRAFT` + `MySQL state=10`，且 `schema JSON-equal to orig: True`、
   sha256 回到 `a6c6f9eb…`。**无结转状态变更。**

## 6. 复现

- `docs/audit/artifacts/scratch-migrated/root/r43_ab_keyabsent.py`（appName present/null/absent 三臂）
- `docs/audit/artifacts/scratch-migrated/root/r43_ab2x2.py`（补 absent×本应用 DTO / present×本应用 DTO）
- `docs/audit/artifacts/scratch-migrated/root/r43_b2diag.py`（抓 `detection-state` 原始 NPE 文本）
- `docs/audit/artifacts/scratch-migrated/root/r43_iso.py` / `docs/audit/artifacts/scratch-migrated/root/r43_arms.py`（隔离臂 + MESSAGE 正例复测）
- `docs/audit/artifacts/scratch-migrated/root/r43_conn_readplane.json`（filter/mq 读面矩阵）
- 还原：`docs/audit/artifacts/scratch-migrated/root/r41_restore.py`
