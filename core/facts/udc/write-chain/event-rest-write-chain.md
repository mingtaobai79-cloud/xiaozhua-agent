# 事件域（udc_event）REST 写链 —— 全链打通

> 领域：规则 → 事件（`udc/event` ，`EventController` @ udc-web，类级映射 `udc/event`）
> 状态：**三类事件全部 LIVE PASS**（实体事件 / 事件总线 / 微流程事件）
> 证据：CFR 反编译 `udc-plugin-api-5.3.517.jar` + REST 实测 + DB 回读

## 1. 端点面

| 写 | 路径 | 入参 → 出参 |
|---|---|---|
| W | `POST /udc/event` | `EventDto` → `SingleResponse<Long>` |
| W | `POST /udc/event/create-with-data` | `EventAndDataDto` → `Long` |
| W | `POST /udc/event/update` | `EventDto` → `Integer` |
| W | `POST /udc/event/update-with-data` | `EventAndDataDto` → `Integer` |
| W | `POST /udc/event/delete` / `delete-batch` | |
| | `POST /udc/event/search`、`list`、`search/term`、`search/term` | 读 |
| | `GET /udc/event/{id}`、`select-with-data/{id}` | 读 |
| | `POST /udc/event/list/business-event`、`list/events` | 事件源选择（`EventQueryParamDto`）|

角色：`udcAppDesigner` / `udcSystemAdmin`。

## 2. `EventDto` 契约（CFR，`com.seeyon.udc.common.dto` @ udc-plugin-api）

```jsonc
{
  name*,            // @NotBlank @Length(1,30) 编码
  caption*,         // @NotBlank @Length(1,50) 名称
  source,           // EventSourceEnum，默认 ENTITY
  messageType,      // MessageTypeEnum，默认 DEFAULT
  sourceId,         // ★ 非 ENTITY 来源必填（微流程事件/消息的微流程 id）
  appId, appName,
  expDesignData, expRuntimeData,
  actionType,       // EventActionTypeEnum，默认 UPDATE
  triggerType,      // EventTriggerTypeEnum，默认 AFTER
  enabled,          // 默认 true
  type,             // EventTypeEnum，默认 BUSINESS_EVENT
  eventDataType,    // ObjectTypeEnum，默认 OBJECT
  eventData,        // ★ 业务事件必填（实体 id / 对象 id）
  eventDataFullName,
  numberFiredOnce,  // @Pattern ALL|^[0-9]{1,9}$，默认 "1"
  description,      // @Length(max=80)
  messageTopic, messageTags,   // @Length(max=127)，消息类来源用
  className
}
```

## 3. ★ 实测三例（LIVE PASS）

```jsonc
// ① 实体事件（应用内实体事件）
{"name":"xzhEntityEvent","caption":"小爪实体事件","appId":APP,"appName":APPNAME,
 "source":"ENTITY","sourceId":<实体id>,"type":"ENTITY_EVENT","actionType":"CREATE",
 "triggerType":"AFTER","enabled":true,"eventDataType":"OBJECT","eventData":<实体id>,
 "eventDataFullName":"<entityFullName>","numberFiredOnce":"1"}
→ {"code":"BOOT_0000","data":{"content":"-444632295362079470"}}

// ② 事件总线（微流程消息）
{"name":"xzhBusListener","caption":"小爪事件总线监听","source":"MICRO_FLOW",
 "sourceId":<微流程id>,"type":"BUSINESS_EVENT","eventDataType":"OBJECT","eventData":<实体id>,
 "eventDataFullName":"<fullName>","messageTopic":"xzh.topic","messageTags":"xzh",...}
→ content = "-3437981976735970258"

// ③ 微流程事件监听
{"name":"xzhMfEventListener","caption":"小爪微流程事件监听","source":"MICRO_FLOW_EVENT",
 "sourceId":<微流程id>,"type":"BUSINESS_EVENT","eventDataType":"LIST","eventData":<实体id>,...}
→ content = "-5205652932986844860"
```

DB 回读 `udc_event`（`source`: 0=ENTITY / 1=MICRO_FLOW / 2=MICRO_FLOW_EVENT）：
```
-444632295362079470  xzhEntityEvent     source=0 source_id=<实体id>  event_data_type=0
-3437981976735970258 xzhBusListener     source=1 source_id=<微流程id> event_data_type=0
-5205652932986844860 xzhMfEventListener source=2 source_id=<微流程id> event_data_type=1
```

## 4. 校验错误链（复现顺序）

```
sourceId must not be null              ← 非 ENTITY 来源（MICRO_FLOW / MICRO_FLOW_EVENT）必须给 sourceId
event_data cannot be empty (BOOT_4101) ← 业务事件必须给 eventData / eventDataFullName
caption must not be blank (BOOT_1001)  ← caption 必填（我漏传）
→ BOOT_0000 SUCCESS
```

## 5. 枚举真值（CFR 实测）

| 枚举 | 值 |
|---|---|
| `EventSourceEnum` | `ENTITY(0,实体)` / `MICRO_FLOW(1,微流程消息)` / `MICRO_FLOW_EVENT(2,微流程事件)` |
| `EventActionTypeEnum` | `CREATE(0)` / `UPDATE(1)` / `DELETE(2)` / `SELECT(3)` |
| `EventTriggerTypeEnum` | `BEFORE(0)` / `AFTER(1)` / `TRANSACTION_SUCCESS(2)` / `TRANSACTION_EXCEPTION(3)` |
| `EventTypeEnum` | `ENTITY_EVENT(0,实体事件)` / `BUSINESS_EVENT(1,业务事件)` |
| `ObjectTypeEnum` | `OBJECT(0)` / `LIST(1)` |
| `MessageTypeEnum` | `DEFAULT(0,普通消息)` / `DELAY(1,延时消息)` |

## 6. `udc_event` 表列（实测）

`id, create_time, tenant_id, update_time, version, guid, publish_state, action_type, app_id,
caption, description, enabled, event_data, event_data_type, exp_design_data, exp_runtime_data,
message_tags, message_topic, name, number_fired_once, source, source_id, owner_code,
backup_code, message_type, original_id`

注意：**`trigger_type` 不是表列**（`EventDto.triggerType` 落到 `exp_design_data`/`exp_runtime_data`）。

## 7. 边界（未做）

- `create-with-data` / `EventAndDataDto`（带数据的事件）未实测。
- `expDesignData` / `expRuntimeData`（事件表达式）未构造 —— 事件"已设置"但**条件未配**。
- 事件**运行时触发**未验（未真实触发一次实体事件）。
- `EventQueryParamDto`（`list/business-event` 的事件源选择）未测。

## 8. 检测面复核

事件创建后触发重算：**2 WARN / 0 ERROR**（`UDC_CE_MICRO_FLOW_04003` × 2：小爪标品事件监听、小爪标品服务定义，均为草稿微流程 state=10，不阻塞）。
