# UDC 微流程节点 —— 字段约束规范（生成前必查）

来源：设计器前端权威 schema
- 节点定义：`module-83128`（90 个 `export const X = {group,name,type,settings,output,dataSchema,nodeDesc}`）
- 过滤条件组件：`chunks/vendors-node_modules_xiaozhua_biz-where_dist_chunks_index-*.js`（操作符值域 + dataType 映射 + 控件映射 + 校验）
- 参数面板：`module-64734`（入参/出参定义）
- 数据链：`module-37302`(Uu) / `module-18640`(aT) / `module-89647`(lZ) / `module-30269`(ZK)

★ 原则：**每个节点的每个字段都有"值域 + 依赖 + 是否必填 + 联动清空"约束**。生成前逐字段核对，不能靠形状猜。

---

## 1. 触发节点 trigger（按 triggerType）

| triggerType | nodeId | 特有字段 | 入参/出参 |
| --- | --- | --- | --- |
| MANUAL（服务定义） | **`MFStartNode`**（必须） | `paramType`(NONE/BASIC/ENTITY_OBJECT/DEFAULT_OBJECT), `basic`, `isArray`, `desc`, `output` | 有（由 paramType 决定） |
| SCHEDULE（定时任务） | `${type}_${nanoid6}` | `scheduleCronRule{jobCode,jobCaption,cronRules[]}`, `isCompleted` | 无 |
| BUSINESS_EVENT（事件监听） | `${type}_${nanoid6}` | `messageInfo{...}`, `expression`, `title` | 出参=事件数据 |

- `paramType=BASIC` 时 `basic` ∈ `STRING|INTEGER|LONG|BIGINTEGER|DECIMAL|BOOLEAN|DATE|DATETIME|OBJECT|DTO|ARRAY`
- SCHEDULE `cronRules[0]`：`cycleType` ∈ `YEAR|MONTH|WEEK|DAY|HOUR|SIMPLE`；`type` ∈ `FIRST|LAST(仅MONTH)|ANY`；`rotationType` ∈ `MINUTE|DAY|...`；`value`(string)
- **★入参面板只在 nodeId="MFStartNode" 时读得到**（aT: `flowNodes[trigger.nodeId]=clone(trigger)`）

## 2. 活动节点公共字段
`nodeId`(唯一) `name` `type:"ACTIVITY"`(分支"BRANCH") `caption` `description` `runAfter` `input` `output` `isCompleted`

## 3. 条件过滤 condition（RETRIEVE / RETRIEVE_ARRAY / DELETE_ENTITY 等）

结构：`[{type:"GROUP", uuid, logicalOperator:"AND"|"OR", conditions:[CONDITION...]}]`
CONDITION：`{type:"CONDITION", uuid, logicalOperator, leftParam, operator, rightParams}`

### 3.1 操作符值域（`xiaozhua-biz-where` 枚举，**中文即 desc**）
```
EQ="="  NEQ="!="  GT=">"  GE=">="  LT="<"  LE="<="
BETWEEN="介于"  NOTBETWEEN="不介于"
LIKE="包含"  NOTLIKE="不包含"  IN="在"  NOTIN="不在"
RLIKE="开头为"  LLIKE="结尾为"  NULL="为空"  NOTNULL="不为空"
INCLUDEALL="包含全部"  NOTINCLUDEALL="不包含全部"  INCLUDEANY="包含任一个"  NOTINCLUDEANY="不包含任一个"
```
（英文内部名→服务端：like / not like / in / not in / include all / isNull = isNotNull）

### 3.2 ★dataType → 允许的操作符（映射表 `I`，写错=非法）
```
STRING        : EQ NEQ LIKE NOTLIKE IN NOTIN RLIKE LLIKE NULL NOTNULL
MULTILINESTRING: EQ NEQ LIKE NOTLIKE RLIKE LLIKE NULL NOTNULL
INTEGER       : EQ NEQ LT LE GT GE BETWEEN NOTBETWEEN NULL NOTNULL
BIGINTEGER    : EQ NEQ IN NOTIN LT LE GT GE BETWEEN NOTBETWEEN
  （LONG→BIGINTEGER，FLOAT/DOUBLE/DECIMAL/CURRENCY→INTEGER）
BOOLEAN       : EQ NEQ                    ← 只有两个！
ENUM/CTPENUM  : EQ NEQ IN NOTIN NULL NOTNULL
DATETIME      : EQ NEQ LT LE GT GE BETWEEN NOTBETWEEN NULL NOTNULL
  （DATE/TIME→DATETIME）
ENTITY/OBJECT/DTO: EQ NEQ IN NOTIN NULL NOTNULL
ATTACHMENT    : NULL NOTNULL
MULTIENUM / MULTIENTITY / MULTICTPENUM : EQ NEQ INCLUDEALL NOTINCLUDEALL INCLUDEANY NOTINCLUDEANY NULL NOTNULL
```

### 3.3 leftParam
```json
{"id":"<Dto全名>.<字段name>","type":"OBJECT","javaType":"java.lang.String","dto":"_<字段name>",
 "field":"<字段name>","desc":"<字段中文>","dataType":"<见上>","multiSelect":false}
```

### 3.4 rightParams（值）
- `{"type":"CONSTANT","value":"<字面量>","desc":"<显示>","dataType":"<字段同型>"}`
  - BOOLEAN：value 用 `"true"|"false"`；ENUM：value 用枚举项 **id**
- `{"type":"CONTEXT_VARIABLE","value":"<JSON字符串>","desc":"..."}`（前序节点变量）
- `{"type":"EXPRESSION", ...}`
- 无右值操作符（NULL / NOTNULL）→ `rightParams: []`
- BETWEEN/NOTBETWEEN → 两个 rightParams

### 3.5 控件映射（值输入器，供参考）
```
Input(STRING/MULTILINESTRING/RichText/ATTACHMENT)  InputNumber(INTEGER/BIGINTEGER/...)
BooleanSelect(BOOLEAN)  EnumSelect(ENUM/CTPENUM/MULTIENUM/MULTICTPENUM)
DatePicker(DATETIME/DATE/TIME)  Reference(ENTITY/OBJECT/DTO/MULTIENTITY)
```

## 4. 排序 sortParams
```json
[{"field":"<字段name>","id":"<Dto全名>.<字段name>","dataType":"<dataType>","desc":"<中文>","direction":"ASC|DESC"}]
```

## 5. RETRIEVE（查询单记录）
必填：`app` `structure` `selectType` `scope` `fetchType` `output` `isCompleted`
- `fetchType` ∈ `CONDITION`(条件查询) | `IDS`(ID集合查询) | `COUNT`(查询总数) | `OTHERS`(其他聚合查询)
- `selectType:"DTO"`；`scope:"OBJECT"`（单条）
- `fetchType=IDS` 时用 `value:{"type":"SelectParam","selectParam":{...}}`
- `fetchType=CONDITION` 时用 `condition:[...]`
- `nullHandling` ∈ `CONTINUE`(继续执行,自行处理空值) | `STOP`(终止流程,并显示提示)
- `title`（节点出参名称）；`output.type="OBJECT"`

## 6. RETRIEVE_ARRAY（查询多记录）
必填：`app` `structure` `variableTitle`(**不是 title！**) `size` `pageSearch` `fetchType` `output`
- `scope:"ARRAY"`；`output.type="ARRAY"`
- `fetchType` ∈ `CONDITION|COUNT|OTHERS`；`aggFunction`(求和/求平均/最大/最小)、`countAttrs`
- `pageSearch` ∈ `Y|N`；`size` 最多获取条数

## 7. CREATE_VARIABLE（创建变量）
必填：`app` `structure` `paramType` `title` `output`
- `paramType` ∈ `ENTITY_OBJECT|DEFAULT_OBJECT`
- `mappingType:"attrs"` 时 `attrs:[{value:{...},attrType:{name,id,fullName,javaType,dataType,...}}]`

## 8. CHANGE_VARIABLE（修改变量）
`selectParam`(目标变量) + `mappingType` ∈ `value|attrs` + `value/attrs`

## 9. DATA_MAPPING（数据转换）
必填：`selectParam`(ARRAY 源) `targetType` `app` `structure` `mappingRule` `title` `output`
- `targetType` ∈ `ENTITY`(实体对象) | `DTO`(自定义对象)
- `mappingRule:{"type":"Simple","mappings":[{"mappingMode":"FieldCopy|REFERENCE","source":"<源属性id>_<源实体id>","target":"<目标属性id>","targetEntityId":"<目标实体id>","uuid","personalization":false,"rowConditionJson":null}]}`
- **空 mappings 不报错但不转换（空转）**；`output.type` 恒为 `"ARRAY"`

## 10. SUB_MICROFLOW（子微流程）
`mfService:{id,appId,caption,name,path:/microflow/<name>,method:POST|GET,hasInput,hasOutput,triggerType,type,restType}`

## 11. 字段来源接口
- 实体清单：`GET /service/udc/entity/select-all-by-appid/{appId}`
- 实体字段：`GET /service/udc/entity/attribute/select-all-by-entity-id/{entityId}`
- DTO 全名：`com.seeyon.<appName>.dto.<EntityName>Dto`；实体：`com.seeyon.<appName>.domain.entity.<EntityName>`
- 系统字段（设计时通常剔除）：creator/updater/createTime/updateTime/tenantId/draft/version/creatorDepartment/creatorPost/creatorInstitution/id

## 12. 已知踩坑（生成时必避）
1. `IS_NOT_NULL` 非法 → 用 `NOTNULL`；`IS_NULL` → `NULL`
2. RETRIEVE_ARRAY 用 `variableTitle`，写 `title` 无效（画布仍显"设置节点数据"）
3. MANUAL 触发 nodeId 必须 `MFStartNode`
4. 事件选择的 `entityId` 传实体 id（Long），传中文 caption 报「属性entityId反序列化为Long失败」
5. 出参 ENTITY_OBJECT 必须带 `entityObject`（与 structure 同构）+ `app` + `paramType`
6. BOOLEAN 只能 EQ/NEQ
7. ENUM 的 rightParam value 用枚举项 id（不是 label）
