# 微流程「标品」类型 + 活动节点（ACTIVITY）机制

结论来源：设计器前端 module-83128（节点 schema 权威）、module-30269（ZK 类型表）、module-89647（lZ 创建模型）
+ LIVE 对照（test2 app=8704025620829192834）。
状态：**FOCUSED VERIFIED（前端静态 + LIVE 创建/回读一致）**。

## 1. 标品 vs 自定义（type）

| 维度 | 标品 | 自定义 |
| --- | --- | --- |
| `type` | `SERVICE` | `CUSTOM` |
| 触发方式 | 服务定义 MANUAL / 事件监听 BUSINESS_EVENT / 定时任务 SCHEDULE | 同三种 |
| 创建入口 | 新建微流程 → 「标准微流程」 | 新建微流程 → 「自定义微流程」 |
| trigger.nodeId | **MANUAL 用 `MFStartNode`**；SCHEDULE/事件用 `${type}_${nanoid6}` | MANUAL 用 `MFStartNode`；其余 `${type}_${nanoid6}` |
| 活动节点 | SERVICE 用 `type:"ACTIVITY"` | 同 |
| 语义 | 平台内可视化编排（用活动节点） | 接入手工开发的后端微流程（type=CUSTOM 时出参走真实后端 DTO） |

★ **trigger.nodeId 决定入参面板能否显示**（aT: `flowNodes[trigger.nodeId]=clone(trigger)`；入参 Card `formData=flowNodes['MFStartNode']`）：
- MANUAL：**必须 `MFStartNode`**（真实 `getMigrationsource` 实证）。预置 `SERVICE_xxx` 会导致入参面板空白
  （aT 只在 `!(trigger.nodeId)` 时才补 MFStartNode）
- SCHEDULE/事件：用 `${type}_${nanoid6}`（真实 `MigrationScheduler` 即 `SERVICE_Et34XS`）

LIVE 已建（test2）：
```
标品 服务定义     id=862673936068342178  xzhSvcDefK4Ge  SERVICE/MANUAL   trigger.nodeId=SERVICE_RqUjZj
标品 事件监听     id=1524985498115296151  xzhSvcEvtBpDA  SERVICE/BUSINESS_EVENT  messageInfo=实体事件
标品 定时任务     id=-8675485534859429311 xzhSvcSchcHXa  SERVICE/SCHEDULE  scheduleCronRule(HOUR/FIRST)
自定义 微流程     id=5810815099733137875  xzhMf953182   CUSTOM/MANUAL
自定义 事件监听   id=-1516089433318810738 xzhEvtAhN7    CUSTOM/BUSINESS_EVENT  messageInfo=BPM消息
自定义 定时任务   id=-7551185604892573345 xzhSch1EFP    CUSTOM/SCHEDULE
```
三个标品均已挂载完整活动节点链（见 §7）。

## 2. dataSchema 节点模型（画布三件套）

```
dataSchema = { endNode, sourceType:"PAGE", trigger, nodes:[...] }
触发节点  = trigger（nodeId 见上；BUSINESS_EVENT 带 messageInfo；SCHEDULE 带 scheduleCronRule）
结束节点  = endNode（actionType:"END_NODE", nodeId:"MFEndNode"）
活动节点  = nodes[] 每项 type:"ACTIVITY"（或 "BRANCH" 分支）
```

节点公共字段（真实样本实证）：`nodeId, name, type, caption, description, runAfter, input, output, isCompleted, actionType`

## 3. 活动节点类型（actionType / type，90 个，module-83128）

关键业务节点（订单场景常用）：
```
查询单记录   RETRIEVE           { fetchType:"CONDITION", selectType, scope, structure, app, attrs, sortParams,
                                  condition, needCascade, nullHandling, output }
查询多记录   RETRIEVE_ARRAY     { selectType, scope, ... }
创建变量     CREATE_VARIABLE    { paramType, app, mappingType:"attrs", attrs:[{value,attrType}], dataType, structure }
创建列表     CREATE_LIST
修改变量     CHANGE_VARIABLE
插入数据     CREATE_ENTITY / 更新 CHANGE_ENTITY / 删除 DELETE_ENTITY
批量插入     CREATE_BATCH_ENTITY / 批量修改 CHANGE_BATCH_ENTITY
循环         FOR_EACH / 计数循环 FOR
条件分支     (type:"BRANCH" 内含 CONDITION 子节点，带 expression.schema 表达式串)
子微流程     SUB_MICROFLOW      { mfService:{id,name,caption,path,method,triggerType,type,hasInput,hasOutput} }
数据转换     DATA_MAPPING       (事件投递 PUBLISH_BUSINESS_EVENT / 消息推送 SEND_MQ_MESSAGE)
待办         CREATE_AFFAIR / 生单规则 CALL_DATA_FLOW / 自定义服务 CALL_APP_SERVICE
连接器       CONNECTOR / 类型转换 CONVERT_DATA / 创建映射组 CREATE_MAP / 映射操作 MAP_OPERATION
```
完整 90 个见 module-83128 `export const <NAME> = { group:"base", name, type, settings }`。

## 4. 活动节点真实结构样例（LIVE dump，SERVICE 服务定义 4405407084014816629）

```json
// RETRIEVE 查询单记录
{"nodeId":"RETRIEVE_umo5kh","name":null,"type":"ACTIVITY","caption":"查询单条数据(1)","description":null,
 "runAfter":null,"input":null,
 "output":{"appName":"datamigration...","id":"com.seeyon...dto.MigrationPlanDto","javaType":同,
           "dataType":"DTO","type":"OBJECT","desc":"迁移方案配置_1","dtoType":"MASTER_ENTITY",
           "udcApp":true,"name":"_RETRIEVE_rECxaA"},
 "isCompleted":true,"actionType":"RETRIEVE","fetchType":"CONDITION",
 "app":{...},"scope":null,"selectType":null,"structure":{...},"attrs":[...],"sortParams":...,
 "condition":..., "needCascade":..., "nullHandling":..., "methodLegal":...}

// CREATE_VARIABLE 创建变量
{"paramType":"DEFAULT_OBJECT","app":{...},"mappingType":"attrs",
 "attrs":[{"value":{"type":"Simple","simple":true,"desc":true},
           "attrType":{"name":"zhuangtai","id":"...Pddqqyfasfczzxtyzbcc.zhuangtai",
                       "fullName":同,"javaType":"java.lang.Boolean","dataType":"BOOLEAN","type":"OBJECT",
                       "desc":"状态","relationApp":"datamigration...","refApp":"..."}}],
 "dataType":"DTO","structure":{...},"caption":"创建变量(1)","actionType":"CREATE_VARIABLE","type":"ACTIVITY"}

// SUB_MICROFLOW 子微流程
{"nodeId":"SUB_MICROFLOW_00aU0V","type":"ACTIVITY","caption":"子微流程(1)","isCompleted":true,
 "actionType":"SUB_MICROFLOW",
 "mfService":{"id":"301785209408604048","appId":"...","caption":"1.2 枚举同步","hasInput":false,
              "hasOutput":false,"method":"GET","name":"SyncEnumData","path":"/microflow/SyncEnumData",
              "triggerType":"MANUAL","type":"CUSTOM","restType":"GET"}}

// BRANCH 分支（conditions 内嵌 CONDITION，expression.schema 是表达式 JSON 字符串）
{"nodeId":"BRANCH_TkpVqm","name":"userBranch","type":"BRANCH","caption":"分支(1)",
 "conditions":[{"nodeId":"CONDITION_jxFAX9","name":"ifBranch","type":"CONDITION",
                "caption":"符合条件即进入该分支",
                "expression":{"title":"为空(微流程.查询单条数据(1).迁移方案配置_1 [迁移方案配置])",
                              "schema":"{\"designData\":{...}}"}}]}
```

## 5. 写链

- 创建微流程：`udcMicroflowCreatePost`（body 见 §1 六种类别）
- 追加/修改活动节点：**findById 回读全量 → 改 dataSchema.nodes → `udcMicroflowUpdatePost`**
- 节点校验：`udcMicroflowCheckSchemaUpdatePost`（非 DRAFT，返回 errorMessage[].message）
- 节点目录（前端权威）：module-83128；后端 `udcMicroflowFindNodesGet`（GraphQL 内省已关，类型名需按实际 schema）

## 6. 注意

- dataSchema.nodes 里的 `desc`/`title` 由前端在选中数据源时回填，直接写空结构 `isCompleted:false` 时画布显示"未完成配置"
- 真实业务节点必须先选 `app`+`structure`（实体/DTO），再配 `attrs`/`condition`，否则节点不完整
- trigger 的事件/定时配置见 MICROFLOW-BUSINESS-EVENT-TRIGGERS.md

## 7. 节点填充真实结构（LIVE 实证，画布从"设置节点数据"变为完整展示）

**判定规则（module-64734 EwComponent + module-83128 nodeDesc）**：
- 节点卡片标题下描述 = `nodeDesc(node)`；为空则显示红色「设置节点数据」= 未完成
- RETRIEVE.nodeDesc 依赖：`e.title && e.output.dataType && e.output.type`
- RETRIEVE_ARRAY.nodeDesc 依赖：**`e.variableTitle`**（★不是 title！）+ `e.output.dataType` + `e.output.type`
- DATA_MAPPING.nodeDesc 依赖：`dataSchema.structure.id`（先取 `structure`，再 `dataSchema` 回退）

**RETRIEVE（查询单记录）完整字段**（对照真实 6526966460598601818）：
```json
{"nodeId":"RETRIEVE_xxxxxx","type":"ACTIVITY","caption":"查询单条数据(1)","isCompleted":true,
 "actionType":"RETRIEVE","fetchType":"IDS|CONDITION|COUNT|OTHERS","selectType":"DTO","scope":"OBJECT",
 "title":"<实体>_1","nullHandling":"CONTINUE","methodLegal":{...},
 "app":{"appId":"<app>","appName":"<appName>","caption":"<应用名>","inApp":true,"udcApp":true,"dynamicDependency":false},
 "structure":{"key":"<实体fullName>","id":"<实体Dto全名>","label":"<实体名>","dataType":"DTO",
              "entity":"<实体fullName>","dtoType":"MASTER_ENTITY","udcApp":true,"fullName":"<Dto>",
              "relationEntity":"<实体id>","methodLegal":{...}},
 "value":{"type":"SelectParam","selectParam":{"name":"<入参名>","dataType":"BIGINTEGER","javaType":"java.lang.Long",
          "nodeInfo":{"nodeId":"MFStartNode","type":"MANUAL"}, "position":"parent","outputName":"<入参名>", ...}},
 "output":{"appName":"<appName>","id":"<Dto>","javaType":"<Dto>","dataType":"DTO","type":"OBJECT",
           "desc":"<实体>_1","dtoType":"MASTER_ENTITY","udcApp":true,"name":"_RETRIEVE_xxxxxx"}}
```

**RETRIEVE_ARRAY（查询多记录）完整字段**：
```json
{"nodeId":"RETRIEVE_ARRAY_xxxxxx","type":"ACTIVITY","caption":"查询多条数据(1)","isCompleted":true,
 "actionType":"RETRIEVE_ARRAY","fetchType":"CONDITION","selectType":"DTO","scope":"ARRAY",
 "variableTitle":"<实体>列表",   // ★ 面板显示名，必须写
 "pageSearch":"N","size":100,    // 分页开关/最多条数（required）
 "aggFunction":null,"countAttrs":null,
 "app":{...},"structure":{...},"nullHandling":"CONTINUE","methodLegal":{...},
 "output":{"id":"<Dto>","javaType":"<Dto>","dataType":"DTO","type":"ARRAY","desc":"<实体>列表",
           "appName":"<appName>","dtoType":"MASTER_ENTITY","udcApp":true,"name":"_RETRIEVE_ARRAY_xxxxxx"}}
```

**DATA_MAPPING（数据转换）完整字段**：
```json
{"nodeId":"DATA_MAPPING_xxxxxx","type":"ACTIVITY","caption":"数据转换(1)","isCompleted":true,
 "actionType":"DATA_MAPPING","targetType":"ENTITY_OBJECT",
 "title":"<实体>转换","mappingRule":{"mappings":[],"type":"Simple"},
 "selectParam":{"description":"<源变量>","dataType":"DTO","outputName":"_RETRIEVE_ARRAY_xxx","type":"ARRAY",
                "id":"<Dto>","javaType":"<Dto>","dtoType":"MASTER_ENTITY","appName":"<appName>",...},
 "app":{...},"structure":{...},
 "output":{"id":"<Dto>","javaType":"<Dto>","dataType":"DTO","type":"ARRAY","desc":"<实体>转换",...}}   // 恒为 ARRAY
```

**SUB_MICROFLOW（子微流程）**：
```json
{"nodeId":"SUB_MICROFLOW_xxxxxx","type":"ACTIVITY","caption":"子微流程(1)","isCompleted":true,
 "actionType":"SUB_MICROFLOW",
 "mfService":{"id":"<目标微流程id>","appId":"<appId>","caption":"<目标caption>","name":"<目标name>",
              "path":"/microflow/<name>","method":"POST|GET","hasInput":true,"hasOutput":true,
              "triggerType":"MANUAL","type":"CUSTOM","restType":"POST"}}
```

**实体 DTO 命名**：`com.seeyon.<appName>.dto.<EntityName>Dto`（entity.fullName=`com.seeyon.<appName>.domain.entity.<EntityName>`）；
实体清单 `GET /service/udc/entity/select-all-by-appid/{appId}`；`relationEntity` = 实体 id。

**踩坑**：
- RETRIEVE_ARRAY 写 `title` 无效，必须 `variableTitle`，否则画布仍显示"设置节点数据"
- 节点 output.name 建议唯一（`_RETRIEVE_<nodeId尾6位>`）
- 实体事件选择的 `entityId` 必须传**实体 id（数字 Long）**，传 caption 字符串会报
  「属性entityId的反序列化为Long类型时失败」

## 8. 节点过滤条件 / 排序 / 映射规则（★"逻辑通顺"的核心，LIVE 写入）

### 8.1 RETRIEVE / RETRIEVE_ARRAY 的 `condition`（过滤条件）

结构（`[{type:"GROUP", uuid, logicalOperator:"AND", conditions:[...]}]`）：
```json
[{"type":"GROUP","uuid":"<hex>","logicalOperator":"AND",
  "conditions":[{"type":"CONDITION","uuid":"<hex>","logicalOperator":"AND",
    "leftParam":{"id":"<Dto全名>.<字段名>","type":"OBJECT","javaType":"java.lang.String",
                 "dto":"_<字段名>","field":"<字段名>","desc":"<字段中文>",
                 "dataType":"STRING|INTEGER|BIGINTEGER|BOOLEAN|DATETIME|CTPENUM|ENTITY",
                 "multiSelect":false},
    "operator":{"value":"EQ","desc":"="},          // EQ NE GT GE LT LE LIKE NOT_LIKE IN NOT_IN IS_NULL IS_NOT_NULL
    "rightParams":[{"type":"CONSTANT","value":"true","desc":"true","dataType":"BOOLEAN"}]
                /* 或 {"type":"CONTEXT_VARIABLE","value":"<JSON字符串>","desc":"..."} */}]}]
```
- `leftParam.id` 格式 = `<Dto全名>.<字段name>`；字段清单 `GET /service/udc/entity/attribute/select-all-by-entity-id/{entityId}`
- `rightParams[].type` ∈ `CONSTANT`(字面量) | `CONTEXT_VARIABLE`(前序节点变量，value 是 JSON 字符串) | `EXPRESSION`
- 无右值的操作符（IS_NULL / IS_NOT_NULL）→ `rightParams: []`

### 8.2 `sortParams`（排序）
```json
[{"field":"expNum","id":"<Dto全名>.expNum","dataType":"INTEGER","desc":"实验数量","direction":"DESC"}]
```

### 8.3 DATA_MAPPING 的 `mappingRule`（字段映射规则）
```json
{"type":"Simple","mappings":[
  {"uuid":"<hex>","mappingMode":"FieldCopy","personalization":false,"rowConditionJson":null,
   "source":"<源属性id>_<源实体id>","target":"<目标属性id>","targetEntityId":"<目标实体id>"}]}
```
- `mappingMode` ∈ `FieldCopy`(字段复制) | `REFERENCE`(引用/关联，仅目标字段 type=ARRAY 可选)
- `source` 格式 = `<源属性id>_<源实体id>`；`target` = 目标属性 id
- 来源数据 = `selectParam`（一个 ARRAY 变量，如 `_RETRIEVE_ARRAY_xxx`）；目标结构 = `structure`
- 空 `mappings:[]` 时不报错但**不做任何转换**（等于空转）——必须至少配一条才能"转换"

### 8.4 端到端逻辑链（LIVE 实证 test2，三个标品）
```
服务定义/事件监听/定时任务 的 nodes:
  [0] SUB_MICROFLOW   调用子流程
  [1] RETRIEVE        fetchType=CONDITION, condition=[expText IS_NOT_NULL], selectType=DTO/scope=OBJECT
  [2] RETRIEVE_ARRAY  fetchType=CONDITION, condition=[expFlag EQ true], sortParams=[expNum DESC], size=100
  [3] DATA_MAPPING    selectParam=_RETRIEVE_ARRAY_xxx(ARRAY), mappingRule.mappings=[expText/expNum/expFlag FieldCopy]
```
写后画布渲染：`查询单条数据(1) | 条件查询 | ...`、`查询多条数据(1) | 条件查询 | ...`，无"失效/错误"提示。
