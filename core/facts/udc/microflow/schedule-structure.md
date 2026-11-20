# 定时任务微流程（SCHEDULE）准确结构（LIVE，CDP 抓包 2026-10-26）

来源：用户在前端新建「标准微流程 + 定时任务」，任务名"4"，循环周期「自定义/每5分钟」，
抓 `udcMicroflowCreatePost` + `udcMicroflowCheckSchemaUpdatePost` 请求体。
权威样本：`scratch/captured_schedule_raw.json`。

## 创建（create）dataSchema 骨架
type=SERVICE, triggerType=SCHEDULE。trigger 初始骨架：
```json
"trigger": {"nodeId":"SERVICE_HRoYUO","name":"SERVICE_HRoYUO","caption":"定时任务",
            "description":"","type":"SCHEDULE","input":null,"output":null},
"nodes": [], "sourceType": "PAGE"
```

## 更新（update）完整 dataSchema（填好定时任务后）
```json
"trigger": {
  "nodeId": "SERVICE_HRoYUO", "name": null, "caption": "定时任务", "description": null,
  "type": "SCHEDULE", "input": null, "output": null,
  "scheduleCronRule": {
    "jobCode": "cAJ0ib79HTvonKUm",   // 16 字符随机码（前端 nanoid(16)）
    "jobCaption": "4",                // 任务名称
    "cronRules": [{
      "cycleType": "SIMPLE",          // 自定义循环
      "startTime": "1792984462412",   // 毫秒时间戳字符串
      "endTime": null,                // 不填=不结束
      "rotationType": "MINUTE",       // 分钟
      "type": "FIRST",                // ★ SIMPLE 时也带 type=FIRST（反编译 SIMPLE 分支没体现）
      "value": "5"                    // 每 5 分钟
    }]
  },
  "isCompleted": true
}
"nodes": []
```

## cronRule 字段（权威，抓包为准）
| 字段 | 值 | 说明 |
|---|---|---|
| cycleType | SIMPLE/HOUR/MINUTE/DAY/WEEK/MONTH/YEAR | 循环周期 |
| startTime | 毫秒时间戳字符串 | 开始时间 |
| endTime | null 或 毫秒时间戳 | 不填=不结束 |
| rotationType | DAY/HOUR/MINUTE | SIMPLE 时的旋转单位（每天/每小时/每分钟） |
| type | FIRST/LAST/ANY | 非 SIMPLE 时的 cron 类型；SIMPLE 时也填 FIRST |
| value | 数字字符串 | 每 N 个 rotationType 为一周期 |

- 循环周期映射（截图 223）：每年=YEAR/每月=MONTH/每周=WEEK/每天=DAY/每小时=HOUR/自定义=SIMPLE。
- 自定义（SIMPLE）：每 N 分钟/小时/天 → rotationType=MINUTE/HOUR/DAY + value=N。
- jobCode 是 nanoid(16) 随机码，生成器可用随机 16 字符。
- 定时任务**自身**无出入参（endNode.output=null, trigger.output=null）。

### ★ 定时任务「空跑」的根因：自身无参 ≠ 链上无参

「SCHEDULE 无出入参」只说明**定时节点自己不声明参数**，不代表整条链路不需要参数。
定时流程的典型形态是「定时触发 → SUB_MICROFLOW 调业务子流程」，
此时**时间范围等参数必须由 SUB_MICROFLOW 节点的 `attrs` 传给被调子流程**。

```jsonc
// 定时流程里 SUB_MICROFLOW 节点的 attrs（不是 trigger.output！）
"attrs": [
  { "value": { "type": "Expression",
               "expression": { "schema": "<表达式 schema>",
                               "title": "{dateToString(addDay(系统日期,-7),yyyy-MM-dd)}" },
               "desc": "开始时间" },
    "attrType": { /* 子流程入参字段 beginCreateTime 的 field_attr 形态 */ } },
  { "value": { "type": "Expression", /* …dateToString(系统日期,yyyy-MM-dd)… */ },
    "attrType": { /* endCreateTime */ } }
]
```

- **判据**：`attrs: []` 是合法 JSON、publish 也能过，但调度触发后子流程收到空参 →
  外部接口拿到空时间范围，**静默返回全量或报错，不报配置错误**。这是最贵的坑。
- **不要靠 Java 代码兜底填时间**：参数属于流程契约，写在 `attrs` 里才能在设计器回读、
  才能被子流程的必填校验覆盖。
- 生成器侧口径：`microflow_trigger` 的 SCHEDULE **只造 trigger**，
  给子流程传参必须走 SUB_MICROFLOW 节点的 `attrs`（工具说明里「SCHEDULE 无出入参」
  不得再被读成「这条流程不需要准备参数」）。
- 常用时间表达式（走 `/service/udc/expression/check` + `/transform` 编译，不要手搓）：
  - 近 N 天：`dateToString(addDay(currentDate(), -N), 'yyyy-MM-dd')`
  - 当天：`dateToString(currentDate(), 'yyyy-MM-dd')`
  - 编译产物 `runtimeData.executableExpr` 由服务端返回。

## update 请求体额外字段（operationLog）
update 请求体里有 `operationLog`（操作日志：appId/actionType/domainId/elementRecords 等），
用于操作审计。生成器可省略（后端可能不要求），若 checkSchema/检测报错再补。

## body 顶层字段（比服务定义多 scheduleCaption）
appId, businessEventCaption("-"), caption, description, guid, id, name,
publishState(UNPUBLISH), scheduleCaption("-"), sourceId, type(SERVICE),
state(DRAFT/RELEASE), triggerType(SCHEDULE), groupType(DEFAULT), versionCode,
creationMethod(MANUAL), serviceInterface(CustomMicroFlowAppService),
openApi(STOP), microFlowGroupId, restApi(DISABLED), restPath,
lastVersionMetadataState(DISABLED), sourceType(PAGE), dataSchema
