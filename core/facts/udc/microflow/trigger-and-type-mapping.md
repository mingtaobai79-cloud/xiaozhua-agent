# 微流程类型 × 触发方式 字段映射（权威，反编译证实）

来源：`MicroFlowTypeEnum.java` / `MicroFlowTriggerTypeEnum.java` /
`ScheduleUnitEnum.java` / `RotationTypeEnum.java` / `CronTypeEnum.java` /
`MessageSourceEnum.java`（cfr-r31），`MicroFlowItemDto.java`（@DtoAttribute 注释）。

## 两个正交维度（用户拍板：2 类型 × 3 触发方式 = 6 组合）

### type（MicroFlowTypeEnum）——「标准 vs 自定义」
- `SERVICE(0)` = 标准微流程（有节点）
- `FRONTEND(1)` = 前端（不在本次范围）
- `ENTITY_RULE(2)` = 实体业务规则（不在本次范围）
- `CUSTOM(3)` = 自定义微流程（**无节点**，只有开始/结束 + 出入参）
- `FUNCTION(4)` = 函数（不在本次范围）

### triggerType（MicroFlowTriggerTypeEnum）——「触发方式」
- `BUSINESS_EVENT(0)` = 事件监听（无出入参，监听应用内/应用间事件）
- `SCHEDULE(1)` = 定时任务（无出入参，定时器）
- `MANUAL(2)` = 服务定义（可有出入参）
- `FRONTEND_PARAM(3)` = 前端参数（不在本次范围）

## 关键差异

| 维度 | 服务定义 MANUAL | 事件监听 BUSINESS_EVENT | 定时任务 SCHEDULE |
|---|---|---|---|
| 出入参 | 有（trigger/endNode paramType） | 无 | 无 |
| 开始节点 | 无要求 | messageInfo（监听事件） | jobCaption+jobCode+scheduleCronRule |
| 标准 SERVICE | 有节点 | 有节点 | 有节点 |
| 自定义 CUSTOM | **仅出入参，无节点** | 仅开始节点+标准配置 | 仅开始节点+标准配置 |

## 自定义微流程（CUSTOM）独有字段
- `serviceInterface`：所属接口（业务分类名，如 `MigrationService`），编码(name)即方法名。
- 标准微流程（SERVICE）**无** serviceInterface。

## 参数类型 paramType（trigger/endNode 的 output.paramType 四值）
- `NONE`：无参数
- `BASIC`：基本类型（STRING/BIGINTEGER/INTEGER/BOOLEAN/DATETIME…，配 `basic` 字段）
- `ENTITY_OBJECT`：实体对象（MASTER_ENTITY，配 `entityObject` 字段）
- `DEFAULT_OBJECT`：自定义对象（dtoType=CUSTOM，配 `defaultObject` 字段）

## BASIC 入参（trigger.output）结构规范（9 键 desc，2026-11-04 实测纠错）

★ **标量 BASIC 入参用 9 键 `desc`**，不是 DTO 入参的 12 键 `description`：

```json
{
  "id": null, "javaType": "java.lang.Long",
  "dataType": "BIGINTEGER", "type": "OBJECT", "desc": "业务名",
  "dtoType": null, "udcApp": null, "hasPagination": null,
  "name": "_FLOW_INPUT_xxxxxx"
}
```

★ **纠错（本次连踩的根因是方向反了）**：曾把 DTO 入参的 12 键 `description`
（inApp/required/appName）误套到 BASIC 入参，导致 `desc=None`。前端表达式编辑器
和「参数名称」读的是 `desc`，读不到就显示 `name`（编码 `_FLOW_INPUT_xxx`）。
用户「参数」页签保存后回读证实：BASIC 入参被平台规范化成 9 键 `desc`。
判据：`name` 是 `_FLOW_INPUT_` + 随机 6 位，标量业务名放 `desc`；
只有 DTO 入参（dataType=DTO，dtoType=CUSTOM/MASTER_ENTITY）才用 `description` 12 键。
读 output 业务名一律 `o.get("desc") or o.get("description")` 双兼容（两型都要能读）。

## 事件监听 trigger 结构（BusinessEventTrigger，type=BUSINESS_EVENT）
```
trigger = {
  type: "BUSINESS_EVENT",
  messageInfo: {
    messageSource: "EVENT" | "MESSAGE" | "CONNECTOR" | "MICRO_FLOW_EVENT",
    eventName: 事件名,
    eventDataFullName: 事件数据DTO全名,
    caption: 标题,
    // EVENT 源额外：eventFullName + eventMfCustomDtoName
    // MESSAGE 源额外：topic
    // CONNECTOR 源额外：connectorMessageInfo
  },
  expression: {...}  // 触发条件（过滤，可选，不一定全收）
}
```
MessageSourceEnum：EVENT(0 事件)/MESSAGE(1 消息)/CONNECTOR(2 连接器)/MICRO_FLOW_EVENT(3 微流程事件)。

## 定时任务 trigger 结构（ScheduleTrigger，type=SCHEDULE）
```
trigger = {
  type: "SCHEDULE",
  jobCaption: 任务名称,
  jobCode: 任务编码,
  scheduleCronRule: {
    cronRules: [{
      cycleType: "HOUR"|"MINUTE"|"DAY"|"WEEK"|"MONTH"|"YEAR"|"SIMPLE",
      // cycleType=SIMPLE 时：
      rotationType: "DAY"|"HOUR"|"MINUTE",
      startTime: 毫秒时间戳(字符串),
      endTime: 毫秒时间戳(字符串，可不填=2099),
      value: "数字"
      // cycleType≠SIMPLE 时：type: "FIRST"|"LAST"|"ANY" + value
    }]
  }
}
```
ScheduleUnitEnum：HOUR(0)/MINUTE(1)/DAY(2)/WEEK(3)/MONTH(4)/YEAR(5)/SIMPLE(6)。
RotationTypeEnum：DAY(0)/HOUR(1)/MINUTE(2)。
CronTypeEnum：FIRST(0)/LAST(1)/ANY(2)。

## 微流程创建字段（REST /service/udc/microflow/create + update）
body = {appId, name(编码=方法名), caption, type(SERVICE/CUSTOM), triggerType(MANUAL/BUSINESS_EVENT/SCHEDULE),
        state(20=RELEASE), creationMethod, description, serviceInterface(仅 CUSTOM), groupId, dataSchema}

## 关键坑（实测）
- trigger 节点的 `type` 字段 = triggerType 的字符串值（MANUAL/BUSINESS_EVENT/SCHEDULE），不是 node 的 type。
- 检测读最新数据，但需等 EXECUTING→SUCCESS 稳定后才读结果（异步检测，轮询第一次 SUCCESS 是旧缓存）。
- 生单规则/dataFlow 用 dataFlowMappingId 引用，检测检查 dataFlowIds 集合是否含它（DATA_FLOW_NOT_EXIST=77）。
