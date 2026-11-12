# 基本变量引用 / 查询条件 的真实结构（实测，来自 小爪全节点24-V16 与 1.10删除方案数据）

> 这轮"全错"的根因：我手写 selectParam 和 condition，字段形态全错。下面是平台真实结构，
> 生成器必须照抄，只替换指向值。

## 一、CHANGE_VARIABLE 引用「基本类型(文本)变量」的 selectParam（正确形态）

```json
{
  "id": null,                                  // 基本变量 id 是 null（实体才是 DTO fullName）
  "javaType": "java.lang.String",
  "dataType": "STRING",
  "type": "OBJECT",
  "desc": "vText",                             // 变量标题(title)，不是 nodeId
  "name": "_CREATE_VARIABLE_3eLmAb",           // = outputName（带下划线前缀）
  "position": "parent",
  "outputName": "_CREATE_VARIABLE_3eLmAb",
  "description": "vText",
  "nodeInfo": {                                // ← 我之前漏了这个，导致「变量」下拉空白
    "nodeId": "CREATE_VARIABLE_3eLmAb",        // nodeId 不带下划线
    "type": "ACTIVITY",
    "actionType": "CREATE_VARIABLE"
  }
}
```

关键约定：
- `output.name` = `"_" + nodeId`（下划线前缀）；`nodeInfo.nodeId` = 不带下划线的 nodeId。
- 基本变量引用**没有** `key` / `path` 字段；实体变量引用才有 `dtoType/udcApp/relationEntity/id=DTO`。
- 我之前错误：`name="vKey"`（应为 outputName）、`id="_CREATE_VARIABLE_minv1"`（应为 null）、缺 nodeInfo。

## 二、CREATE_VARIABLE（基本类型）节点

```json
{ "nodeId":"CREATE_VARIABLE_xxx", "paramType":"BASIC", "title":"vKey", "dataType":"STRING",
  "mappingType":null, "attrs":null,
  "value":{"type":"Simple","simple":"PAY-1","desc":"PAY-1"},
  "output":{"id":null,"javaType":"java.lang.String","dataType":"STRING","type":"OBJECT",
            "desc":"vKey","name":"_CREATE_VARIABLE_xxx"} }
```
基本变量**不要** structure / app / otherType / nodeRemark。

## 三、RETRIEVE 查询条件（正确形态，条件组数组）

```json
"condition":[{
  "type":"GROUP","uuid":"...","conditions":[{
    "type":"CONDITION",
    "leftParam":{"id":"com.seeyon...YsFull6956Dto.f01text","type":"OBJECT",
                 "javaType":"java.lang.String","dto":"_f01text","field":"f01text",
                 "desc":"文本字段","dataType":"STRING","multiSelect":false},
    "operator":{"value":"EQ","desc":"="},
    "rightParams":[{"type":"CONTEXT_VARIABLE","value":"{\"key\":\"_FLOW_INPUT_...\",...}"}],
    "logicalOperator":"AND"
  }]
}]
```

致命坑：模板（1.10）的 RETRIEVE 带 5 条条件（targetDatasourceId/enabled/targetTable/ID…）。
我只改 conditions[0] 就留了 4 条旧条件 → 面板里出现一堆不相干字段。必须**整组替换** conditions。

## 四、结论

生成器铁律：节点 JSON 一律来自 `fixtures/microflow/node_templates/<ACTION>.json`，
**引用/条件/值只做整块替换**，绝不逐字段手写；每改一个指向，都要和上面真实形态对齐。

## 五、checkSchema 的完整请求体契约（来自前端「保存并提交」抓包）

URL: POST /service/udc/graphql?udcMicroflowCheckSchemaUpdatePost
body.variables.params0 必须带这些字段（我之前的 REST body 全缺，所以 参数错误/静默草稿）：

```json
{
  "appId":"9000000000000000001",
  "businessEventCaption":"-", "scheduleCaption":"-",
  "caption":"...", "description":"...", "name":"minV1", "type":"SERVICE",
  "guid":"-2841894774839228897",          // ← 必须，流程 guid
  "id":"-5386647105876167671",
  "publishState":"UNPUBLISH", "state":"RELEASE", "triggerType":"MANUAL",
  "groupType":"DEFAULT", "versionCode":0, "sourceType":"PAGE",
  "creationMethod":"MANUAL", "serviceInterface":"CustomMicroFlowAppService",
  "openApi":"STOP", "microFlowGroupId":"0", "restApi":"DISABLED", "restPath":"",
  "lastVersionMetadataState":"DISABLED", "lastEnableTime":null, "lastEnableVersion":null,
  "sourceId":null, "dataSchema":"<整段字符串>"
}
```

响应 content{check, errors, errorMessage[{errorCode,errorType,level,message,nodeCaption,nodeId,path,propertyKey}]}。
用这个 body 重放，能拿到 errorMessage 明细（不再是 BOOT_1001）。

## 六、流程输入（参数页）才是引用根，不能拿实体 DTO 冒充

- 流程 input（`_FLOW_INPUT_xxx`）是**参数页签定义的 CUSTOM 微流程入参 DTO**，
  不是实体 DTO。1.10 的 input 是 `ScfasjrcjSKa`（desc=方案id, dtoType=CUSTOM）。
- 查询条件的 rightParams 引用 `_FLOW_INPUT_xxx.<真实字段>`，字段必须来自该入参 DTO；
  我引用 `_FLOW_INPUT_minv1.f01text`，但 input 实际是 `_FLOW_INPUT_CAVQVZ`（方案id），
  字段不存在 → UI 显示「值不能为空」。
- 教训：要么先定参数页的入参字段再引用；要么查询条件右值用常量（不引用输入），
  先验证条件能渲染，再谈入参引用。

## 七、条件校验接口 udcConditionCheckPost（用户贴 body）

「填过滤条件后走校验」就是它。body 的 params0 是**条件组数组**（整组校验）：

```json
URL: POST /service/udc/graphql?udcConditionCheckPost
{"query":"mutation graphqlLoader ($params0: [udcConditionCheckPostInputBody]) {
  data0: udcConditionCheckPost(body: $params0) { code data { content } message status } }",
 "variables":{"params0":[{
   "type":"GROUP","uuid":"6dc4fba1-...","conditions":[{
     "type":"CONDITION",
     "leftParam":{"id":"com.seeyon...dto.XzhExp950795Dto.createTime","type":"OBJECT",
                  "javaType":"java.util.Date","dto":"_createTime","field":"createTime",
                  "desc":"创建时间","dataType":"DATETIME","multiSelect":false},
     "operator":{"value":"NEQ","desc":"!="},
     "rightParams":[{"type":"CONSTANT","value":"1792671653000","desc":"1792671653000"}],
     "uuid":"af98c8c6-...","logicalOperator":"AND"
   }]
 }]}}
```

要点：
- `params0` 是数组（多组条件可同时校验）。
- `operator.value` 用短码：EQ/NEQ/GT/LT/GE/LE（desc 显示 =/!=/>/</>=/<=）。
- `rightParams[].type` = CONSTANT（常量，value=时间戳毫秒）/ CONTEXT_VARIABLE（引用变量）。
- GROUP 和 CONDITION 各带 `uuid`；CONDITION 带 `logicalOperator`(AND/OR)。
- 校验返回 `content`（不通过时的错误说明）。

## 八、选实体接口 udcMicroflowSearchTreeEntityPost 完整 body（含 methodLegal 查询能力元数据）

```json
URL: POST /service/udc/graphql?udcMicroflowSearchTreeEntityPost
variables.params1:
{"appId":"9000000000000000001","appName":"datamigration9000000000000000001",
 "needChildren":true,"needThirdEntity":false,
 "serviceType":"SELECT_LIST_BY_COMPLEX_CONDITIONS"}
```
返回 content（递归 children）每层实体：
```json
{"caption":"实体名","fullName":"...domain.entity.Xxx","dtoFullName":"...dto.XxxDto",
 "dtoType":"CUSTOM","udcApp":true,"relationEntity":...,
 "customs":{"entityCategory":"..."},
 "methodLegal":{"available":true,"complexCondition":true,"seniorMethod":"...",
                 "serviceType":"...","interfaceClassFullName":"..."},
 "children":[...]}
```

关键：`methodLegal` 是实体的「查询能力」元数据——`available`(是否可查)/`complexCondition`(是否支持复杂条件)/
`seniorMethod`(高级方法)/`serviceType`/`interfaceClassFullName`(查询服务接口类)。
生成器选实体后要按 methodLegal 判断该实体支持哪种查询方式（条件/ID/总数/聚合）。

## 九、出入参 + 表达式（定义驱动生成器验证通过，2026-10-25）

### 出参：endNode.value = SelectParam 绑定来源（活体 xzhAllNodesV16）
```json
"output": {"id":null,"javaType":"java.lang.String","dataType":"STRING","type":"OBJECT",
           "desc":"出参","dtoType":null,"udcApp":null,"name":"_FLOW_OUTPUT_xxx"},
"endNode": {"...基础键...",
  "output": <同 output>,
  "value": {"type":"SelectParam","selectParam":{
      "id":"_CREATE_VARIABLE_3eLmAb",   // ★ 变量名(带下划线)，不是 null
      "javaType":"java.lang.String","dataType":"STRING","type":"OBJECT",
      "desc":"vText","dtoType":"",
      "name":"_CREATE_VARIABLE_3eLmAb","key":"_CREATE_VARIABLE_3eLmAb",
      "path":"_CREATE_VARIABLE_3eLmAb","outputName":"_CREATE_VARIABLE_3eLmAb",
      "description":"vText","position":"parent"},
    "desc":"vText [文本]"},
  "paramType":"BASIC","basic":"STRING","isArray":false,
  "desc":"出参","outPutDesc":null,"isCompleted":true}
```
关键：endNode.value 的 selectParam.id/key/path/outputName 都 = 出参来源变量名（带下划线）。

### 引用入参字段（CONTEXT_VARIABLE，条件右值）
```json
{"type":"CONTEXT_VARIABLE",
 "value":"{\"key\":\"_FLOW_INPUT_8EkIDO_<入参DTOfullName>.字段名\",\"name\":\"字段名\",
   \"id\":\"<入参DTOfullName>.字段名\",\"appName\":\"...\",\"description\":\"字段中文\",
   \"position\":\"children\",\"path\":\"<去点DTOfullName>.字段名\",
   \"outputName\":\"_FLOW_INPUT_8EkIDO\",\"dataType\":\"BIGINTEGER\",\"type\":\"OBJECT\",
   \"javaType\":\"java.lang.Long\",\"dtoType\":\"CUSTOM\",\"udcApp\":false,
   \"multiSelect\":false,\"customs\":{\"basicType\":false,\"inApp\":true,
     \"dataType\":\"BIGINTEGER\",\"name\":\"字段名\",\"id\":\"<字段真实id>\"},
   \"parentLabel\":\"<入参DTO标题>\"}",
 "desc":"字段中文"}
```
入参必须是**参数页签定义的 CUSTOM DTO**（非基本类型），字段从 FindCustomDto 拿。

### 表达式（value type=Expression，活体 expression.sample.json）
tokens 三元组：VARIABLE(`_节点id._节点id`)/OPERATOR/SYSTEM(`system.currentDateTime`)；
runtimeData.executableExpr = base64前缀 + token.value 拼接；context 三级含 uniformityParams。

## 十、实体入参 vs 自定义对象入参（区别，活体 xzhAllNodesV16）

入参/出参是「实体」还是「自定义对象」，形态不同：

| 维度 | 自定义对象入参(ScfasjrcjSKa) | 实体入参(YsFull6956Dto/XzhExp950795Dto) |
|---|---|---|
| dtoType | CUSTOM | **null** |
| udcApp | true | **null** |
| 额外字段 | (无) | **dtoFullName + isArray + dto=true** |
| id | dtoFullName | dtoFullName |

出参是实体时：`output.id`=实体DTO fullName，`dtoType`=MASTER_ENTITY，`udcApp`=true；
`endNode.value.selectParam` 绑定来源节点，`id`=实体DTO fullName，`nodeInfo`=来源节点(RETRIEVE等)，
带 `relationEntity`。基本类型出参则是 `id=null` + `paramType=BASIC`。

教训：入参/出参用实体时，不要套自定义对象的 CUSTOM/udcApp=true 形态；
实体要带 dtoFullName/isArray/dto 三键，dtoType/udcApp 置 null。

## 十一、出入参定义的真正载体：trigger/endNode 的 paramType（纠正第十节）

第十节抓的是 xzhAllNodesV16 顶层 input（dtoType=null+dtoFullName），那是旧形态，**不是参数页签读的源**。

真相（docs/audit/udc-semantics/MICROFLOW-PARAMS-TAB-DATACHAIN.md + LIVE）：
- **入参定义面板读 `dataSchema.trigger`（不是顶层 input）**；**出参读 `endNode`**
- 关键字段 `paramType` 挂在 trigger/endNode 节点上：`NONE`/`BASIC`/`ENTITY_OBJECT`(实体对象)/`DEFAULT_OBJECT`(自定义对象)
- trigger 形态：`input=null`，入参 DTO 在 `trigger.output`，另有 `desc`(参数名称,required)、`app`、`isArray`、`hasPagination`、`entityObject`/`defaultObject`(选中的对象引用)、`basic`(BASIC 时)
- ENTITY_OBJECT 的 entityObject 引用：`{key,label,title,id,value,dataType:'DTO',dtoType:'MASTER_ENTITY',udcApp,fullName,dtoId:关系实体id,filterTitle}`
- endNode 同样挂 paramType + entityObject + desc + value(绑定出参来源节点)
- 顶层 input/output 是 runtime 的 DTO 结构（引擎执行用），与 paramType 是两回事

教训：要"入参/出参是实体"，改的是 trigger.paramType=ENTITY_OBJECT + entityObject 引用 + desc，不是顶层 input 的 dtoType。

## 十二、entityObject 引用 10 键权威结构（用户手动选实体保存，LIVE 真结构）

写实体入参/出参前，查 udcMicroflowSearchTreeEntityPost（body: {appId,appName,needChildren,needThirdEntity,serviceType:'SELECT_LIST_BY_COMPLEX_CONDITIONS'}）拿实体 fullName(domain)/dtoFullName(DTO)/relationEntity。

entityObject 引用（10 键，用户 tree-select 选实体保存后读回）：
```json
{"key":"<domain.entity.X>","entity":"<domain.entity.X>",
 "id":"<dto.XDto>","fullName":"<dto.XDto>",
 "label":"<实体名>","dataType":"DTO",
 "dtoType":"MASTER_ENTITY","udcApp":true,
 "relationEntity":"<关系实体id>",
 "methodLegal":{"available","complexCondition","seniorMethod","serviceType","interfaceClassFullName"}}
```
关键（易错）：
- key/entity = domain.entity.X（domain 类）；id/fullName = dto.XDto（DTO）——两者不能互换
- 无 dtoFullName/customs/filterTitle/title/value 字段（那是自定义对象 defaultObject 的形态）
- methodLegal 无 validate

★教训：CDP 用 DOM dispatchEvent 点 tree-select 不触发 React 选实体，读回的 entityObject 是残留假结构（14 键）；
必须让用户真实点选，或直接以「用户手动保存后读回」为准。判断"已失效"即 entityObject.key/fullName 拼反或塞了多余字段。
