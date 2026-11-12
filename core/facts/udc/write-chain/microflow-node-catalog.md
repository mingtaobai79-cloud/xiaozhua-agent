# 微流程节点契约目录 + data_schema 结构（真机/DB 取证）

> 来源：`udc_microflow_info.data_schema` 全库聚合（**500 条真实微流程**）+ CDP 真机编辑器
> 状态：**48 种节点类型 + 3 种触发类型 + 节点结构已实证**

## 1. `data_schema` 顶层结构（权威）

```jsonc
{
  "input":  { "name":"_FLOW_INPUT_xzh1", "javaType":"java.lang.String", "dataType":"STRING",
              "type":"OBJECT", "desc":"同步任务ID", "appName":"<appName>", "inApp":true, "udcApp":true,
              "id":null, "dtoType":null, "hasPagination":null },
  "output": { ... "_FLOW_OUTPUT_xzh1", "desc":"执行结果" ... },
  "trigger": { "nodeId":"MFStartNode", "type":"MANUAL", "caption":null,
               "output":{...}, "paramType":"BASIC", "app":null },
  "endNode": { "nodeId":"MFEndNode", "type":"END", "actionType":"END_NODE", "caption":"结束",
               "output":{...}, "paramType":"BASIC", "basic":"STRING", "isArray":false, "hasPagination":false },
  "nodes":  [ <node>, ... ],
  "sourceType": null
}
```

★ 固定节点 id：`trigger.nodeId = "MFStartNode"`，`endNode.nodeId = "MFEndNode"`。

## 2. 触发类型（500 条实测分布）

| type | 数量 | 说明 |
|---|---|---|
| `MANUAL` | 440 | 手工触发 |
| `BUSINESS_EVENT` | 26 | 业务事件触发 |
| `SCHEDULE` | 13 | 定时任务 |

## 3. ★ 节点类型全目录（48 种，actionType 实测）

```
BRANCH(259)                 分支
CALL_MICRO_FLOW(142)        调用微流程
RETRIEVE(109)               查询单条数据
VALUE_HANDLE(66)            值处理
CREATE_VARIABLE(56)         创建变量
FOR_EACH(54)                循环
CREATE_VARIABLE_FRONT(46)   创建变量(前端)
LIST_OPERATION(38)          列表操作
FED_LIST_OPERATION(35)      列表操作(前端)
RETRIEVE_ARRAY(33)          查询多条数据
CREATE_LIST(32)             创建列表
CHANGE_VARIABLE_FRONT(24)   改变量(前端)
SUB_MICROFLOW(21)           子微流程
CONTROL_ACTION(16)          控件动作
ENTITY_SAVE(15)             保存记录
CALL_APP_SERVICE(15)        调用应用服务
MESSAGE_INFO(14)            提示消息
CHANGE_VARIABLE(14)         改变量
CALL_FRONT_FLOW(13)         调用前端流程
ENTITY_REFRESH(13)          刷新实体
CONFIRM_CLOSE_PAGE(13)      确认关闭页面
CREATE_LIST_FRONT(12)       创建列表(前端)
MODAL(11)                   弹窗
CHANGE_LIST_FRONT(11)       改列表(前端)
CONVERT_DATA(9)             类型转换/数据转换
CHANGE_ENTITY(9)            变更实体
OPEN_PAGE(8)                打开页面
ATTACHMENT_UPLOAD(5)        附件上传
CHANGE_LIST(5)              改列表
CHANGE_BATCH_ENTITY(5)      批量变更实体
PUBLISH_BUSINESS_EVENT(4)   事件投递
FOR(4)                      遍历
CUSTOM_ERROR(4)             自定义错误
OPEN_LINK(4)                打开链接
ATTACHMENT_DOWNLOAD(4)      附件下载
THROW_EVENT(3)              抛出页面事件
ENTITY_SAVE_DRAFT(2)        保存草稿
CONVERT_DATA_FRONT(2)       类型转换(前端)
MAP_OPERATION(2)            映射操作
RELOAD_PAGE(1)              重新加载页面
ENTITY_EXPORT(1)            导出实体
DATA_MAPPING(1)             数据映射
DELETE_ENTITY(1)            删除实体
CALL_DATA_FLOW_FRONT(1)     调用生单规则(前端)
FLOW_ACTION(1)              流程动作
CONTROL_STATUS(1)           控件状态
```

## 4. 节点通用结构

```jsonc
{
  "nodeId": "RETRIEVE_Odg62G",        // <actionType>_<6位随机>
  "name": null, "title": null,
  "type": "ACTIVITY",                 // ACTIVITY | BRANCH
  "actionType": "RETRIEVE",
  "caption": "查询单条数据(1)",        // UI 标题
  "description": null,
  "runAfter": null,                   // 依赖的前置节点
  "isCompleted": true,
  "input": null,
  "output": { "name":"_RETRIEVE_x7jPXO", "dataType":"DTO", "type":"OBJECT",
              "javaType":"com.seeyon.<app>.dto.<Entity>Dto", "desc":"..._1",
              "dtoType":"MASTER_ENTITY", "udcApp":true, "appName":"<appName>",
              "id":"com.seeyon.<app>.dto.<Entity>Dto", "relationEntity":"<entityId>" }
}
```

### 4.1 RETRIEVE（查询单条数据）
```
fetchType: "IDS" | ...        条件查询方式
app: { appId, appName, caption, inApp, udcApp, dynamicDependency }
structure: { key:"com.seeyon.<app>.domain.entity.<E>", id:"com.seeyon.<app>.dto.<E>Dto",
             label:"<实体名>", dataType:"DTO", entity:"<entity fullName>",
             dtoType:"MASTER_ENTITY", udcApp:true,
             fullName:"com.seeyon.<app>.dto.<E>Dto", relation* }
selectType / conditions         筛选条件
sortParams                      排序
```

### 4.2 CALL_MICRO_FLOW（调用微流程）
```
mfService: { id:"<被调微流程 id>", appId, caption:"<微流程名>", hasInput, hasOutput,
             input:{ inApp,udcApp,hasPagination,dataType,javaType,type,name,description,required },
             method:"POST", name:"MFSERVICE...", output:{...} }
output: { appName, id:"<dtoFullName>", type:"ARRAY|OBJECT", dataType:"DTO",
          javaType, relationEntity:"<entityId>", desc:"..._1", name:"_CALL_MICRO_FLOW_xxx",
          dtoType:"SUB_ENTITY|MASTER_ENTITY", inApp }
```

### 4.3 ENTITY_SAVE（保存记录）
```
config: "{\"target\":\"udcForm_xI10_<ts>\",\"actionName\":\"ENTITY_SAVE\"}"   // JSON 字符串
outputName: "出参_ID"
output: { javaType:"java.lang.Long", dataType:"BIGINTEGER", type:"OBJECT", desc:"出参_ID", name:"_ENTITY_SAVE_xxx" }
```

### 4.4 MESSAGE_INFO（提示消息）
```
messageType: "SUCCESS" | ...
showInfo: { "type":"Simple", "simple":"作废成功", "desc":"作废成功" }
closeType: ["AUTO_CLOSE"]
```

### 4.5 CONVERT_DATA（数据转换/类型转换）
```
convertType: { "desc":"指定符号拆分文本", "value":"Split", "dataType":"STRING", "type":"ARRAY" }
selectParam: { 源字段（description/key/name/id/appName/position/path/outputName/dataType/type/javaType/dtoType/multiSelect/customs/iconKey/...） }
regex: "PERIOD" | ...          分隔规则
title: "<输出名>"
output: { name:"_CONVERT_DATA_xxx", dataType:"STRING", type:"ARRAY", javaType:"java.lang.String", desc }
```

### 4.6 PUBLISH_BUSINESS_EVENT（事件投递）
```
eventType: "IN_APP"
selectEvent: { key/label/value/fullName:"com.seeyon.<app>.dto.microflow.event.<Event>",
               caption, source:"MICRO_FLOW", dtoType:"CUSTOM", udcApp }
mappingType: "attrs"
attrs: [ { value:{ type:"SelectParam", selectParam:{...}, desc:"入参 [文本]" },
           attrType:{ name:"ziduan1", ... } } ]
```

### 4.7 THROW_EVENT（抛出页面事件）
```
event: { name:"内部结算列表", key:"eventDefinehoBLAQz44R",
         params:[ { key:"FORM  udcForm_Bn6i udcForm_Bn6i", title:"合同档案[单一记录]",
                    nodeType:"FORM", dataType:"DTO", isLeaf:false, selectable:false,
                    multiSelect:false, type:"OBJECT", relationEntity:"<entityId>",
                    componentId:"udcForm_Bn6i", children:[...] } ] }
```

### 4.8 BRANCH（分支）
```
type: "BRANCH", actionType: null 或 "BRANCH"
conditions: [ ... ]          分支条件
```

## 5. 节点通用字段集（node keys 全集）

```
actionType, app, attrs, caption, condition, conditions, dataType, description, fetchType,
input, isCompleted, mappingType, methodLegal, name, needCascade, nodeId, nullHandling,
output, paramType, runAfter, scope, selectType, sortParams, structure, title, type
```

## 6. 复现

```bash
# 全量拉取 + 聚合
python scripts/conn.py db "SELECT id, caption, data_schema FROM udc_microflow_info WHERE data_schema IS NOT NULL" --db=udc_test2 > all_mf.txt
python agg_nodes.py     # 48 actionTypes + trigger 分布
python one_node.py      # 各类型完整结构样例
```
