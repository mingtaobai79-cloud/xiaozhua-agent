# 事件监听微流程（BUSINESS_EVENT）准确结构（LIVE，CDP 抓包 2026-10-26）

来源：用户在前端编辑器新建「标准微流程 + 事件监听」，选「实体实验-base2 新增事件(操作前)」，
抓 `udcMicroflowCreatePost` + `udcMicroflowUpdatePost` 请求体。权威样本：
`scratch/captured_event_create.json` / `scratch/captured_event_update.json`。

## 创建（create）dataSchema 骨架
type=SERVICE, triggerType=BUSINESS_EVENT。trigger 初始只有骨架：
```json
"trigger": {"nodeId":"SERVICE_xxxx","name":"SERVICE_xxxx","caption":"事件监听",
            "description":"","type":"BUSINESS_EVENT","input":null,"output":null},
"nodes": [], "sourceType": "PAGE",
"entityId":"", "eventId":"", "input":null, "output":null
```

## 更新（update）完整 dataSchema（填好事件后）
顶层 body 字段（比服务定义多了 businessEventCaption/scheduleCaption/guid/publishState 等）：
```
appId, businessEventCaption("-"), caption, description, guid, id, name,
publishState(UNPUBLISH), scheduleCaption("-"), sourceId, type(SERVICE),
state(DRAFT), triggerType(BUSINESS_EVENT), groupType(DEFAULT), versionCode,
creationMethod(MANUAL), serviceInterface(CustomMicroFlowAppService),
openApi(STOP), microFlowGroupId, restApi(DISABLED), restPath,
lastVersionMetadataState(DISABLED), sourceType(PAGE), dataSchema
```

dataSchema 关键节点（trigger.type=BUSINESS_EVENT）：
```json
{
  "endNode": {"id":"","name":"","type":"END","actionType":"END_NODE","nodeId":"MFEndNode",
              "caption":"结束","description":"","input":null,"output":null},
  "input": {  // 顶层入参 = trigger.output（事件数据入参）
    "id": "expTypeBase2.com.seeyon.udc.common.event.BeforeCreateEvent",
    "name": "_BUSINESS_EVENT_o4KbTY",
    "javaType": "expTypeBase2.com.seeyon.udc.common.event.BeforeCreateEvent",
    "dataType": "DTO", "type": "OBJECT", "desc": "1",
    "appName": "datamigration9000000000000000001", "dtoType": ""
  },
  "sourceType": "PAGE",
  "trigger": {
    "nodeId": "SERVICE_rZtrzd", "name": null, "caption": "事件监听", "description": null,
    "type": "BUSINESS_EVENT", "input": null,
    "output": { /* 同顶层 input，name=_BUSINESS_EVENT_xxx */ },
    "messageInfo": {
      "caption": "实体实验-base2新增事件(操作前)",
      "messageSource": "EVENT",
      "eventFullName": "com.seeyon.udc.common.event.BeforeCreateEvent",
      "eventDataFullName": "com.seeyon.datamigration9000000000000000001.dto.ExpTypeBase2Dto",
      "eventMfCustomDtoName": "expTypeBase2.com.seeyon.udc.common.event.BeforeCreateEvent",
      "eventName": "BeforeCreateEvent",
      "currentId": "BeforeCreateEvent",
      "currentType": "1647498252896732631",
      "output": {
        "id": "com.seeyon.datamigration9000000000000000001.dto.ExpTypeBase2Dto",
        "dataType": "DTO", "type": "OBJECT",
        "javaType": "expTypeBase2.com.seeyon.udc.common.event.BeforeCreateEvent",
        "appName": "datamigration9000000000000000001"
      }
    },
    "expression": { /* 触发条件（可选，过滤消息） */ }
  },
  "title": "1", "isCompleted": true, "nodes": []
}
```

## messageInfo 字段生成规则（EVENT 源，应用内实体事件）
| 字段 | 值 | 生成规则 |
|---|---|---|
| messageSource | "EVENT" | 应用内 |
| caption | 事件标题 | = 事件列表的 caption |
| eventFullName | 事件类全名 | `com.seeyon.udc.common.event.{事件名}` |
| eventDataFullName | 实体 DTO 全名 | `...dto.{实体名}Dto`（= 事件列表 entityFullName 去掉 .domain.entity. 换 .dto. 加 Dto） |
| eventMfCustomDtoName | DTO未首大写名+事件类全名 | `{实体DTO unCapFirstName}.com.seeyon.udc.common.event.{事件名}` |
| eventName | 事件名 | BeforeCreateEvent/AfterCreateEvent/BeforeUpdateEvent/AfterUpdateEvent/BeforeDeleteEvent/AfterDeleteEvent |
| currentId | = eventName | |
| currentType | 来源实体 id | = 事件列表 sourceId |
| output.id | 实体 DTO 全名 | = eventDataFullName |

- 事件类全名固定前缀 `com.seeyon.udc.common.event.` + 事件名。
- eventMfCustomDtoName 前缀 = 实体 DTO 的 unCapFirstName（ExpTypeBase2Dto → expTypeBase2）。
- trigger.output / 顶层 input：id=javaType=eventMfCustomDtoName, dataType=DTO, name=_BUSINESS_EVENT_xxx(随机), appName=应用名。
- 事件监听无出入参（endNode.output=null），但 trigger.output 是事件数据（内部用）。
- 触发条件 expression 是可选过滤（用户填了「为空(应用参数.附件)」），不填则省略。

## 事件名与接口链路（本应用实测，权威）
- 事件名 **9 种**（Before/After/TransactionSuccess × Create/Update/Delete）：
  BeforeCreateEvent/AfterCreateEvent/TransactionSuccessCreateEvent/
  BeforeUpdateEvent/AfterUpdateEvent/TransactionSuccessUpdateEvent/
  BeforeDeleteEvent/AfterDeleteEvent/TransactionSuccessDeleteEvent。
- 正确的事件查询接口是 `udcMicroflowFilterEventPost`（不是 udcDataFlowListEventsPost，后者只返回 3 种）：
  - 实体事件：body `{appId, sourceTypes:["ENTITY"], eventTypes:["ENTITY_EVENT"], entityId:<实体id>, id:<微流程id>}`
  - 微流程事件：body `{appId, sourceTypes:["MICRO_FLOW_EVENT"], eventTypes:["ENTITY_EVENT"], entityId:0, id:<微流程id>}`
  - 返回每事件：name/caption/sourceId(来源实体id)/eventClassName(事件类全名=eventFullName)/
    eventDataFullName(实体DTO全名)/eventMfCustomDtoName(DTO未首大写名.事件类全名)/sourceCaption/appName。
- **eventFullName = eventClassName**（接口直接返回 `com.seeyon.udc.common.event.{事件名}`）。
- **eventDataFullName = 实体 DTO 全名**（接口直接返回）。
- **eventMfCustomDtoName**（接口直接返回）= DTO未首大写名 + "." + 事件类全名。
- currentType = sourceId（来源实体 id）；currentId = eventName。

## 应用内 vs 应用间（事件监听两种消息来源）
- **应用内 = 实体事件 + 微流程事件**：
  - 实体事件：选实体（udcEntityPrimarySelectByAppidAppGet 查实体列表）→ udcMicroflowFilterEventPost(sourceTypes=["ENTITY"], entityId)。
  - 微流程事件：udcMicroflowFilterEventPost(sourceTypes=["MICRO_FLOW_EVENT"])（如「小爪验收事件」xzhVerifyEvent）。
- **应用间 = 消息（MESSAGE 源）**：
  - 选应用：`udcMicroflowSearchAppsPost`（body {appId, needBootStarter:true, needConnectorApp:true}）。
  - 选应用后查消息：`udcMicroflowFilterMqPost`（body {appId, appName, microFlowId}）→ 返回 topic/caption/contentDto。
- 应用内 = messageSource "EVENT"（选实体/微流程事件）；应用间 = messageSource "MESSAGE"（选应用+消息 topic）。
