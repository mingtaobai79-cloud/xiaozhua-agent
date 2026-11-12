# 微流程「参数」tab 数据链（入参/出参定义面板读写源）

结论来源：设计器前端 5.3.496 bundle（module-83128 / module-64734 / module-37302 / module-18640 / module-70857）
+ LIVE 对照（微流程 xzhMf953182 / SyncNowData 732255149534301888）。
状态：**FOCUSED VERIFIED（前端静态 + 数据回读一致）**；UI 显示待用户刷新确认。

## 1. 读链路（后端 → 面板表单值）

```
getMicroFlowSchemaById  [op=udcMicroflowFindByIdGet, path id]
  → content.{...rest, dataSchema:"<JSON 字符串>", jsonSchema}
  → B = JSON.parse(dataSchema)
  → aT 变形：
       B.endNode = { ...B.endNode, desc: B.output?.desc, hasPagination: B.output?.hasPagination }
       if (!(B.trigger?.type && B.trigger?.nodeId))
            B.trigger = { ...B.trigger, id:"", nodeId:"MFStartNode", caption:"开始",
                          description:"", type: triggerType, input:null, output: B.input }
  → Uu(B)（module-37302）解析成画布三件套：
       flowNodes[trigger.nodeId] = clone(trigger)          ← 键就是 "MFStartNode"
       if (endNode) nodes.push(endNode) → flowNodes["MFEndNode"] = clone(endNode)
```

参数 tab 渲染（module-64734）：

```
入参 Card  formData = flowNodes["MFStartNode"]  去掉 {id,nodeId,type,actionType,canRollback,runAfter}
出参 Card  formData = flowNodes["MFEndNode"]    同上
```

⇒ **入参定义面板 = `dataSchema.trigger`**（不是 `dataSchema.input`）
⇒ **出参定义面板 = `dataSchema.endNode`**，而 endNode.desc 被 **`dataSchema.output.desc`** 覆盖

## 2. 字段 schema（module-83128，权威）

面板 settings 是配置驱动（`{key,label,type,required,defaultval,props,ishidden}`）：

入参/出参 items 公共字段：

| key | label | 类型 | 说明 |
| --- | --- | --- | --- |
| paramType | 入参配置 / 出参配置 | radio(button) | `NONE` 无参数 / `BASIC` 基本类型 / `ENTITY_OBJECT` 实体对象 / `DEFAULT_OBJECT` 自定义对象；defaultval="NONE" |
| basic | 数据类型 | select | 仅 paramType=BASIC 显示；defaultval=`STRING` |
| app | 选择应用 | selector | 仅 DEFAULT_OBJECT（跨应用）显示 |
| entityObject | 实体对象 | treeListSelector | 仅 paramType=ENTITY_OBJECT |
| defaultObject | 自定义对象 | customObjectSelector / treeListSelector | 仅 paramType=DEFAULT_OBJECT；`beforeDtoCreate` 会用它 title 回填 desc |
| hasPagination | 是否分页 | checkBoxButton | paramType∈{ENTITY_OBJECT,DEFAULT_OBJECT} 时显示；与 isArray 互斥 |
| isArray | 是否列表 | checkBoxButton | paramType≠NONE |
| **desc** | **参数名称** | input | **required，placeholder「请输入显示名称」**；前端校验错误即 `errorFields:[{name:['desc'],errors:['请输入参数名称']}]` |

数据类型值域（module-65420 `pe`，LIVE 实证）：

```
STRING 文本 | INTEGER 整数 | LONG 长整数 | BIGINTEGER 大整数 | DECIMAL 小数
BOOLEAN 布尔 | DATE 日期 | DATETIME 日期时间 | OBJECT | DTO | ARRAY | MULTILINESTRING
```

## 3. 写链路（面板 → 后端）

```
保存修改（H，module-64734）
  validateFields() 入参/出参各一次
  o = G.d(flowNodes["MFStartNode"], formValues, "FLOW_INPUT",  FLOW_INPUT,  flowNodes["MFStartNode"])
  u = G.d(flowNodes["MFEndNode"],   formValues, "FLOW_OUTPUT", FLOW_OUTPUT, flowNodes["MFEndNode"])
  dispatch(OK({nodeId, objectInfo}))              // 写回节点态
  await RF({stateType:"DRAFT", slience:true})     // 触发保存
  RF：dataSchema = JSON.stringify(画布 state，含 trigger/endNode/nodes)
      → updateMicroflowSchema(有 id)  [op=udcMicroflowUpdatePost]
      → 或 saveMicroflowSchema     [op=udcMicroflowCreatePost]
      → 非 DRAFT 走 checkAndUpdateMicroflowSchema [op=udcMicroflowCheckSchemaUpdatePost]
```

`G.d`/`OK` 的产出结构（module-83128 `FLOW_OUTPUT.settings[].items` 的 return）：

```js
// paramType=BASIC
{ id:null, javaType: V_1(basic), inApp, appName, dataType: basic,
  type: isArray ? "ARRAY" : "OBJECT", desc, dtoType:null, udcApp:null, hasPagination }
// paramType=ENTITY_OBJECT
{ id: entityObject.id, javaType: entityObject.id, dataType:"DTO", type:"ARRAY"|"OBJECT",
  desc, dtoType: entityObject.dtoType, udcApp: entityObject.udcApp, hasPagination }
// paramType=DEFAULT_OBJECT 同上，取 defaultObject.*
// hasPagination=true → javaType = `PageDtoRequest.${javaType}`
```

## 4. 微流程列表查询（LIVE 打通）

```
op = udcMicroflowSearch, 参数类型 udcMicroflowSearchInputBody
body = {
  pageInfo: { needTotal:true, pageNumber:1, pageSize:999, pages:0, total:0 },
  params:   { appId, IN_type:["SERVICE","CUSTOM"] },        // 页面规则: {appId,type:"FRONTEND",sourceId}
  sort:     { orders:[{direction:"ASC", property:"caption"}] }
}
```

## 5. 对照实证

| 微流程 | paramType 载体 | input.desc | output.desc | dataSchema 顶层键 |
| --- | --- | --- | --- | --- |
| SyncNowData（真实） | trigger.paramType=DEFAULT_OBJECT | 立即同步入参 | 任务ID | endNode,output,input,sourceType,trigger,nodes |
| MigrationScheduler（定时 SERVICE） | trigger 无 paramType | 无 input 键 | 无 output 键 | endNode,sourceType,trigger,nodes |
| xzhMf953182（修正后） | **trigger.paramType=BASIC, basic=STRING** | **同步任务ID** | **执行结果** | input,output,endNode,sourceType,trigger,nodes |
