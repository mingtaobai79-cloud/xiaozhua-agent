# 微流程「业务事件」触发（事件监听）——候选来源与 messageInfo 契约

结论来源：设计器前端 bundle（module-76440 事件选择弹窗、module-18640 aT、module-30269 ZK/lZ、module-89647 lZ）
+ LIVE 对照（test2 app=8704025620829192834，微流程 xzhEvtAhN7 = -1516089433318810738）。
状态：**FOCUSED VERIFIED（前端静态 + LIVE 读写回读一致）**。

## 1. 触发类型总表（module-30269 `ZK`，创建表单 microlfowType + type）

| 表单值 | type | triggerType | caption |
| --- | --- | --- | --- |
| servicedefinition | SERVICE | MANUAL | 服务定义 |
| eventmonitor | SERVICE | BUSINESS_EVENT | 事件监听 |
| timingtask | SERVICE | SCHEDULE | 定时任务 |
| frontend | FRONTEND | MANUAL | 页面规则 |
| frontendparam | FRONTEND | FRONTEND_PARAM | 子规则 |
| frontendfunction | FUNCTION | MANUAL | 公共页面规则 |
| entityrule | ENTITYRULE | MANUAL | 实体规则 |
| **customServicedefinition** | CUSTOM | MANUAL | 自定义微流程 |
| **customEventmonitor** | CUSTOM | BUSINESS_EVENT | 自定义事件监听 |
| **customTimingtask** | CUSTOM | SCHEDULE | 自定义定时任务 |

表单字段：`microlfowType ∈ {service 标准微流程, custom 自定义微流程}`；`type ∈ {servicedefinition, eventmonitor, timingtask}`
（`timingtask` 仅在非 FORM 模式可选）；`name`（编码，字母开头+数字，≤20）、`caption`（≤100）、
`serviceInterface`（仅 custom+servicedefinition 必填）、`microFlowGroupId`、`desc`（≤200）。

创建模型 `lZ()`（module-89647）：
```js
{ id:"", appId, sourceId, version:"0", versionCode:0,
  name: name || `MF${type}${nanoid6}`, description:"", type, triggerType,
  entityId:"", eventId:"", input:null, output:null,
  trigger:{ nodeId:`${type}_${nanoid6}`, name:同, caption, description:"", type:triggerType,
            input:null, output:null },
  nodes:[] }
```
前置校验 `udcMicroflowCheckMicroFlowCaptionPost`（重名 → content=true）。创建 op `udcMicroflowCreatePost`。

## 2. 事件选择器两个 tab（module-76440，`eventSelector` 组件）

弹层标题「事件选择」，两个 tab：

### 2.1 应用内（INTERNAL）→ 实体事件
```json
op  = udcMicroflowFilterEventPost
body= { "appId":"<app>", "id":"<微流程id>",
        "sourceTypes":["ENTITY"], "eventTypes":["ENTITY_EVENT"] }   // 前端硬编码
返回 content[{ id, name, appId, caption, appName, sourceId, appCaption, description,
                sourceCaption, eventClassName, eventDataFullName, eventMfCustomDtoName }]
```
- `EventSourceEnum` **只接受 ENTITY**（BPM/表单/页面 均报 No enum constant）
- `EventTypeEnum` 只接受 `ENTITY_EVENT`
- 每条实体 × 9 个事件（resources/presetData/event/defaultevent.json 模板）：
  `{Before,After,TransactionSuccess} × {Create,Update,Delete}Event`，即 操作前 / 操作后 / 操作成功
- `eventClassName = com.seeyon.udc.common.event.{类名}`
- `eventMfCustomDtoName = {实体短名}.{eventClassName}`（如 `xzhExp950795.com.seeyon.udc.common.event.AfterCreateEvent`）
- `MicroFlowEventTypeEnum = { IN_APP 应用内, AMONG_APP 应用间 }`

选中（onConfirm INTERNAL）→ messageInfo：
```js
{ caption, messageSource: currentType==="microflow" ? "MICRO_FLOW_EVENT" : "EVENT",
  eventFullName: eventClassName, eventDataFullName, eventMfCustomDtoName,
  eventName: name, currentId, currentType,
  output:{ id: eventDataFullName, dataType:"DTO", type:"OBJECT",
           javaType: eventMfCustomDtoName, appName } }
```

### 2.2 应用间（EXTERNAL）→ MQ 消息（含 BPM / 组织 / 消息中心 / 连接器回调）
先选「应用」，应用列表：
```json
op  = udcMicroflowSearchAppsPost          // 前端别名 searchUdcApplication
body= { "appId":"<app>", "needBootStarter":true, "needConnectorApp":true }
返回 content[{ appId, name, caption, description, fullName, inApp, id, udcApp, appType, dynamicDependency }]
```
再取该应用消息：
```json
op  = udcMicroflowFilterMqPost
body= { "appId":"<app>", "appName":"<app.name>", "microFlowId":"<微流程id>" }
返回 content[{ caption, description, fullName, topic, available, customs,
                contentDto{ type, item{ enums, itemType, item{ enums, itemType } } } }]
```
LIVE 实测各应用消息数（app=8704025620829192834）：
```
bpm            29 条  topic=BPM        流程发起/结束/终止/回退/撤销/挂起/催办/移交/取回/复活/删除…
                                       + 审核结果/BPM vip督办…（dto.message.* 与 dto.message.event.*）
organization   18 条  topic=ORGANIZATION  创建/更新 人员/职务/职级/岗位/角色人员…
ctp-message     2 条  topic=MESSAGE_CENTER 读消息 / 给消息中心推送消息
cip-capability  7 条  topic=CONNECTOR_CALLBACK 支付结果/印章/日程/签署/商旅/视频会议 回调
（应用列表共 30 个：入口服务 9 + boot-starter 18 + udc-starter 3）
```
映射（module-76440 `h()`）：`javaType = contentDto.item{?}.itemType || contentDto.type`；
`arrayOrObject = contentDto.type==="java.util.List" ? "ARRAY" : "OBJECT"`。

选中（onConfirm EXTERNAL）→ messageInfo：
```js
{ caption, messageSource:"MESSAGE", eventDataFullName: javaType,
  topic, tags, currentId: fullName, currentType: appName,
  output:{ id: javaType, dataType, type: arrayOrObject, javaType, appName } }
```
若 `appName==="cip-connector" || dynamicDependency==="INTEGRATION"`：
  额外 `connectorMessageInfo: customs||null`，`messageSource:"CONNECTOR"`，output.dataType="DTO", type="OBJECT"。

## 3. trigger 在 dataSchema 中的最终形态（BUSINESS_EVENT）

```json
"trigger": {
  "nodeId":"CUSTOM_xxxxxx", "name":"CUSTOM_xxxxxx", "caption":"事件监听",
  "description":"", "type":"BUSINESS_EVENT", "input":null, "output":{...事件数据 DTO...},
  "messageInfo":{...见上...}, "expression":null, "title":"节点出参名称(默认 事件数据)"
}
```
- 节点配置面板字段（LIVE 页面实证）：**事件选择**（eventSelector，required，placeholder「请选择业务事件」）、
  **触发条件**（filterExpression，需先选事件，placeholder「请先选择前置数据」）、**节点出参名称**（title，默认「事件数据」）
- `BUSINESS_EVENT.output` 模板（module-83128）：`{ id:"$messageInfo.output.javaType", name:"$nanoid",
  javaType:"$messageInfo.output.javaType", dataType:"$messageInfo.output.dataType",
  type:"$messageInfo.output.type", desc:"$title", appName:"$messageInfo.output.appName", dtoType:"" }`
- aT 读取时 endNode/MFStartNode 走 §参数 tab 数据链（见 MICROFLOW-PARAMS-TAB-DATACHAIN.md）

## 4. 定时任务 trigger（SCHEDULE）形态

```json
"trigger": { "nodeId":"CUSTOM_xxxxxx", "name":同, "caption":"定时任务", "description":"",
  "type":"SCHEDULE", "input":null, "output":null,
  "scheduleCronRule":{ "jobCode":"<19位>", "jobCaption":"<任务名>",
    "cronRules":[{ "cycleType":"DAY|WEEK|MONTH|YEAR|HOUR|SIMPLE",
                   "startTime":null, "endTime":null,
                   "rotationType":"MINUTE|DAY|...", "type":"FIRST|LAST|ANY", "value":"5" }] },
  "isCompleted": true }
```
- 面板（module-83128 SCHEDULE）：`scheduleCronRule`(scheduleCronRule 组件) 或 `scheduleRule`(scheduledTask)
- 周期 cycleList：YEAR 每年 / MONTH 每月 / WEEK 每周 / DAY 每天 / HOUR 每小时 / SIMPLE 自定义
- 执行方式 type：FIRST（第一个）/ LAST（最后一天，仅 MONTH）/ ANY（指定第 N 个）
- 列表字段 `scheduleCaption`（如「每天 00:05」）
- 定时任务**无入参/出参**（前端不给），dataSchema 顶层只有 endNode/sourceType/trigger/nodes
