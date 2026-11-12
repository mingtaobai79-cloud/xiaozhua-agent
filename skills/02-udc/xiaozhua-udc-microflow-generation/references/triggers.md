# 触发方式契约（MANUAL / SCHEDULE / EVENT）

> 由 SKILL.md 拆分而来，按需读取。

## ★ 出入参定义必须先单独保存（用户实测规则 2026-10-31）

- 「参数」页签的入参/出参定义是**独立的保存动作**：右上「保存修改」按钮，保存成功弹「数据保存成功！」。
- 改了出入参后**必须先点「保存修改」，再保存/发布画布**；直接保存画布不会带上参数页签的未保存改动。
- API 路径等价规则：修改已有流程出入参时，`dataSchema` 里 `trigger.output`（入参）与
  `endNode.output`（出参）必须同步改并整体提交——只改一头会出现「画布引用的出参」
  与「参数页签定义」不一致，下游节点引用失效。
- 改出入参后，引用旧出参的下游节点（SelectParam）要回读核对；出参改名/改型等同子微流程
  变更场景，引用节点可能红字。

## ★ MANUAL+BASIC 入参/出参命名铁律

- 入参 trigger.output.name 恒为 `_FLOW_INPUT_xxxxxx`（随机6位），**标量业务名放 `desc`**，
  如「数据源ID」。把 name 写成业务名前端引用不认。
- ★ BASIC 入参 trigger.output 是 **9 键 `desc`**（2026-11-04 纠错）：`id:null / javaType /
  dataType / type:OBJECT / desc:业务名 / dtoType:null / udcApp:null / hasPagination:null /
  name:_FLOW_INPUT_xxx`。只有 DTO 入参（dataType=DTO）才用 12 键 `description`
  （inApp/required/appName）。曾误套 DTO 的 description 到 BASIC → desc=None，
  前端表达式编辑器/「参数名称」读 desc 显示 name（编码）。读 output 业务名一律
  `o.get("desc") or o.get("description")` 双兼容（两型都要能读）。
- 出参 endNode.output.name 恒为 `_FLOW_OUTPUT_xxxxxx`。basic_param/make_end_basic
  已改自动生成，调用方别再传业务名当 name。
- BASIC 型节点（BASIC 变量）被引用时：name=key=path=outputName、id=""、dtoType=""、
  无 nodeInfo——绝不能带 entity structure 的 DTO 全名（CREATE_VARIABLE BASIC 的
  structure 是 PageInfo 模板残留，_out_ref 已加 is_basic 分支处理）。
- 引用完整性闸门 _outputs() 必须含 trigger.output.name（MANUAL 入参真名所在地）。

## 类型×触发 6 组合矩阵（权威：反编译 MicroFlowTypeEnum + 用户原生样本实测）

`type`：SERVICE(0)=标准微流程（有节点）/ CUSTOM(3)=自定义微流程（无节点，只有首节点+出入参）。
`triggerType`：MANUAL(2)=服务定义（有出入参）/ BUSINESS_EVENT(0)=事件监听（无出入参）/ SCHEDULE(1)=定时任务（无出入参）。

| 组合 | trigger.nodeId | 节点链 | 出入参 |
|---|---|---|---|
| SERVICE + MANUAL | `MFStartNode` | **有** | 有（input/output + paramType + entityObject/defaultObject） |
| CUSTOM + MANUAL | `MFStartNode` | **无（nodes=[]）** | 有 |
| SERVICE + BUSINESS_EVENT | `SERVICE_xxx`，caption「事件监听」 | 有 | **无**（endNode.output=null） |
| CUSTOM + BUSINESS_EVENT | `CUSTOM_xxx`，caption「自定义事件监听」 | **无** | **无** |
| SERVICE + SCHEDULE | `SERVICE_xxx`，caption「定时任务」 | 有 | **无** |
| CUSTOM + SCHEDULE | `CUSTOM_xxx`，caption「自定义定时任务」 | **无** | **无** |

**关键铁律（v8 全错在这里，污染了事实）**：
- CUSTOM 微流程**不能加节点链**，只有首节点 + 出入参（标准 SERVICE 才有节点）。
- 事件监听/定时任务**无出入参**，标准和自定义都一样；首节点只选事件（messageInfo）/定时规则（scheduleCronRule）。
- 只有 SERVICE + MANUAL 是「有节点链 + 有出入参」的完整形态。

## MANUAL trigger 契约（照用户原生流程 MFSERVICEHbICrp 实测，错一处检测就报错）

```
trigger = {
  "id": "", "nodeId": "MFStartNode",   # ← 固定值！变量表按它注册入参，写随机名→"前序节点发生变更请重新选择"
  "name": null, "caption": null, "description": null,
  "type": "MANUAL", "input": null,
  "output": {"id": DTO, "javaType": DTO, "inApp": true, "appName": 当前应用名,
             "dataType": "DTO", "type": "OBJECT", "desc": 入参名称, "dtoType": "MASTER_ENTITY",
             "udcApp": true, "hasPagination": false, "name": "_FLOW_INPUT_xxxxxx"},
  "paramType": "ENTITY_OBJECT",
  "app": {"appId": APP, "appName": APP_NAME, "caption": 应用标题, "inApp": true, "udcApp": true, "dynamicDependency": false},
  "hasPagination": false, "isArray": false, "desc": 入参名称,
  "entityObject": {"key": 实体 domain 全名, "label": 实体标题, "title": 同, "id": DTO, "value": DTO,
                   "dataType": "DTO", "dtoType": "MASTER_ENTITY", "udcApp": true, "fullName": DTO,
                   "relationEntity": 实体 id, "entityId": 实体 id, "tableName": 物理表名},
}
schema["input"] = trigger["output"]   # 顶层 input 同步
```

## endNode 出参契约（有节点链 vs 无节点链，错一个就报 root.endNode.value 必填）

- **SERVICE + MANUAL（有节点链）**：endNode 除了 `output` + `paramType` + `entityObject/defaultObject`，还必须带
  `mappingType:"value"` + `value:{type:"SelectParam", selectParam:{...}}`，selectParam 的 `outputName` 指向**节点链最后一个节点的 output.name**、`nodeInfo.nodeId` 指向该节点 nodeId、`id/javaType/position:"parent"` 用该节点出参 DTO。
  漏 `value` 报 `root.endNode.value.value` `PROPERTY_IS_REQUIRED`「必填参数未配置」——因为出参得从节点链引用，不是凭空声明。
- **CUSTOM + MANUAL（无节点链）**：endNode **不需要 value**，只 `output` + `paramType` + `defaultObject/entityObject`（出参直接定义，无前序节点可引用）。照 MFCUSTOM9dn28n 实测。
- **`paramType=BASIC`（标量出参：布尔/文本/整数，生产 244 条）**：endNode 是 17 键，
  `basic` 必须写具体类型字符串，它决定 `javaType`：
  `BOOLEAN→java.lang.Boolean` / `INTEGER→java.lang.Integer` / `BIGINTEGER→java.lang.Long` /
  `STRING→java.lang.String` / `DECIMAL→java.math.BigDecimal`。写错检测报类型不匹配。
  `output` 是**标量形态**（注意 `id:null`、`dtoType:null`、`udcApp:null`，跟 DTO 出参不同）：
  ```
  {id:null, javaType:"java.lang.Boolean", dataType:"BOOLEAN", type:"OBJECT",
   desc:<出参名>, dtoType:null, udcApp:null, hasPagination:null, name:"_FLOW_OUTPUT_xxxxxx"}
  ```
  `value` 引 `CREATE_VARIABLE` 的出参，且 `selectParam` 带 `dtoType:""`、`key`/`path` 都等于出参名：
  ```
  {type:"SelectParam", selectParam:{id:"", javaType, dataType, type:"OBJECT", desc,
     dtoType:"", name:<出参名>, key:<出参名>, path:<出参名>,
     outputName:<出参名>, description:<出参名>, position:"parent"}, desc:"<出参名> [布尔]"}
  ```
  242 条真实 BASIC 出参的 `value` 形态分布：`SelectParam` 183 / `Expression` 6 / `Simple` 4 / `None` 51。
  组装器 `finish()` 已支持三种出参：MANUAL DTO 出参传 `end_from=<末节点别名>`；
  BASIC 标量出参传 `basic_out="BOOLEAN"` + `end_from=<变量别名>`（会校验引用节点的
  `output.dataType` 与 `basic_out` 一致，不符直接抛 ComposeError）；
  SCHEDULE/EVENT 走 9 键形态，不需要出参参数。
- **SCHEDULE / BUSINESS_EVENT：endNode 是 9 键最小形态，`output:null`，且没有 `value` 键**。
  生产 24 条定时任务 **24/24** 的 endNode 只有：
  `{id:"", name:"", type:"END", actionType:"END_NODE", nodeId:"MFEndNode", caption:"结束", description:"", input:null, output:null}`；
  顶层 `output`/`input` 也都是 `null`（**仅 SCHEDULE**；BUSINESS_EVENT 顶层 `output=null` 但
  `input` 必须等于 `trigger.output`，见「事件监听：拉事件清单 + 引用事件数据」节）。
  给定时/事件流程套 MANUAL 那套 13 键 endNode（带 `mappingType/paramType/basic/value/attrs`）会被 checkSchema 判
  `root.endNode.value.value PROPERTY_IS_REQUIRED`——**哪怕你把 nodes 全删光也一样报**，很容易误判成「节点链有问题」。
  判据：endNode 键数 **9 = 无出入参流程，13 = MANUAL 有出参流程**，构造时按 trigger.type 分支，不要一套 code 走到底。
  组装器 `MicroflowComposer.finish()` 已按 `trigger.type` 分流（`_has_out_param()` / `_is_nodeless()`）。
- 通用：endNode 恒为 `{id:"", name:"", type:"END", actionType:"END_NODE", nodeId:"MFEndNode", caption:"结束", description:"", input:null, output:...}`，另带 `desc/hasPagination/app/isArray/outPutDesc`。
- **漏 `type` / `actionType` 会让画布把结束节点渲染成「节点开发中...」**：只给 `nodeId:"MFEndNode"` + `output` 时，画布上是灰头白底的「节点开发中...」占位卡，右侧还会多出一个无标题同款占位——用户会直接质问「结束节点被你改成什么了」。权威键位（前端 bundle 保存链实测）：`{id:"", name:null, type:"END", actionType:"END_NODE", nodeId:"MFEndNode", caption:"结束", description:null, input:null, output:<流程出参>, outPutDesc:null, mappingType:"BASIC", paramType:"BASIC", basic:"STRING", isArray:false, desc:"出参", value:<SelectParam>, attrs:[], isCompleted:true}`。
- **END 绝不能放进 `nodes` 数组**：前端保存时 `endNode = flowNodes[END]`、`nodes = flowFrame.slice(1)`，END 天然在数组之外。塞进 `nodes` 会让顶层 `endNode` 变 `{}`，发布报 `[结束]:无效的数据 / MFEndNode.type DATA_INVALID`。

## EVENT / SCHEDULE trigger 契约（无出入参，别给它们加 output）

**先看仓库成品再动手**：`components/construction/microflow_triggers.py` 的
`manual_trigger` / `schedule_trigger` / `event_trigger` / `mq_trigger` / `mf_event_trigger` + `make_create_body` / `make_update_body`；
权威事实在 `core/facts/udc/microflow/trigger-and-type-mapping.md`、`schedule-structure.md`、`event-listener-structure.md`。

**构造器要用生产样本校准，别只信「结构看着对」**：按 `triggerType` 过滤某应用全部 RELEASE 流程，逐键比对构造器产物
（trigger 顶层键 / `scheduleCronRule` 键 / `cronRules[].` 键三层的频次表），零差异才算过。
实测 `schedule_trigger` 与 24 条生产定时任务**三层键全部一致、零差异**；`cycleType` 分布 `DAY 19 / SIMPLE 3 / HOUR 2`
——**默认给 DAY**，别默认 SIMPLE。

- **SCHEDULE trigger 真实结构**（照 MigrationScheduler 实测）：`scheduleCronRule: {jobCode, jobCaption, cronRules:[{cycleType,startTime,endTime,rotationType,type,value}]}` + `isCompleted: true`；**`output` 为 null**（定时无数据出参）。写 `scheduleInfo` 或给 output 必报 `scheduleCronRule` 属性缺失。
  注意 `type` 字段（FIRST/LAST/ANY）在 `cycleType=SIMPLE` 时**也要填**（生产 24/24 都有，反编译 SIMPLE 分支没体现这一点）。
- **EVENT trigger**（照 MFEVtest655 实测）：`trigger.output` 是事件数据（内部用，id=eventMfCustomDtoName），但 **endNode.output=null**、顶层 output=null（事件监听无对外出入参）。
- **CUSTOM + EVENT/SCHEDULE**：`nodeId=CUSTOM_xxx`，caption「自定义事件监听」/「自定义定时任务」，**nodes=[] 无节点链**。
- **SERVICE + EVENT/SCHEDULE**：`nodeId=SERVICE_xxx`，可搭节点链，但首节点出参不注册进 MANUAL 变量表，节点条件用 CONSTANT 或按事件数据展开。

### 事件监听：拉事件清单 + 引用事件数据（实测通路）

- **事件清单是 REST，不是 GraphQL**：`POST /service/udc/microflow/filter/event`，
  body `{appId, entityId:<实体 relationEntityId>, sourceTypes:["ENTITY"]}` → `data.content[]` 每项带
  `name`（BeforeCreateEvent / AfterCreateEvent / TransactionSuccessCreateEvent …）、`caption`、
  `eventClassName`（= eventFullName）、`eventDataFullName`（实体 DTO）、
  `eventMfCustomDtoName`（`<tableName>.<事件类全名>`）、`sourceId`（= 实体 id）。
  少了 `udc` 前缀的 `/service/microflow/filter/event` 会回 `server_404 microflow 服务不存在，请重启服务或重新发布应用后再试`——
  **那是路径写错，不是应用没发版**，别按那个提示去重启/重发布。
- **事件数据要取 `info` 子对象**：事件 trigger 出参下挂着 `info`（实体 DTO）。引用形态：
  `key = <出参名>+<DTO全名>+"info"`、`id = <eventMfCustomDtoName>+".info"`、
  `path = <eventMfCustomDtoName 去点>+".info"`、`dtoType="MASTER_ENTITY"`。
  取新增记录的 id 走 `<该引用>.id`；不要拿 trigger 出参名当实体对象直接用。
- **BUSINESS_EVENT 顶层 `input` = `trigger.output`**（调度才是 input=null）。
  `MicroflowComposer.finish()` 已按 trigger 类型分流，别看别的流程抄。
- **REST 发布体要带 `scheduleCaption` / `businessEventCaption`**：真实抓包 body 恒有这两个键，
  不适用的填 `"-"`；`deploy.publish` 已补，手写 body 的路径别漏。

**未解决（下次别重走一遍）**：SCHEDULE / BUSINESS_EVENT 流程发布到 RELEASE 后，
DELTA 构建在部署阶段报 `Business Error[一致性检测未通过]`（`AbstractDeployService.doParallel`），
上面这些字段补齐后仍复现；同环境 MANUAL 流程构建正常，差异落在触发方式这一层。
服务端只回这一句、不给明细项，唯一能看明细的是设计器右上「检查」面板——
先拿面板截图再改，不要盲改 schema。

