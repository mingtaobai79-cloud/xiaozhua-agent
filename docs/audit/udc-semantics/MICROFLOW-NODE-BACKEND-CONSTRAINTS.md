# UDC 活动节点 —— 后端权威解析约束（反编译 udc-biz 5.3.517）

**证据源**：`udc-biz-5.3.517.jar` 反编译（CFR 0.152）
`com.seeyon.udc.microflow.domain.bo.flow.activity.*` + `com.seeyon.udc.microflow.util.MicroFlowParserUtils` +
`com.seeyon.udc.microflow.common.MicroFlowParser`
运行时版本：pod `udc-*` / `datamigration*`（lowcode-test，`udc-*-5.3.517`）。
提取方法：每个 Activity 类 `parseActivityNode()` 里 `NodeUtils.getXxx("field", node, required, ...)` 的 required 标志。

★ 后端解析器 = 节点字段的**权威约束源**（比前端推断精确），生成前以此为准。

---

## 1. 节点必有键（MicroFlowParserUtils.buildBaseNode）
`type` `caption` `nodeId` `output`（后端统一补；活动节点另需 `actionType`）

## 2. 活动节点字段约束（★required=true 为后端强制）

| actionType | 必填字段（后端 required） | 选填 |
| --- | --- | --- |
| RETRIEVE（查询单记录） | `nullPromptMessage`(仅 nullHandling=STOP 时) | fetchType, needCascade, nullHandling, mappingType |
| RETRIEVE_ARRAY（查询多记录） | （分 fetchType，见 §3） | pageSearch, mappingType |
| CREATE_ENTITY（插入） | mappingType | — |
| CHANGE_ENTITY（更新） | mappingType | — |
| DELETE_ENTITY（删除） | **deleteType**(SELECT_PARAM/CONDITION/IDS) | — |
| CREATE_VARIABLE（创建变量） | metaDataType, otherType | paramType, mappingType, value |
| CHANGE_VARIABLE（修改变量） | — | mappingType |
| CREATE_LIST（创建列表） | dataType | value |
| CHANGE_LIST（修改列表） | action | — |
| LIST_OPERATION（列表操作） | indexValue | sortType |
| MAP_OPERATION（映射操作） | operationType, **nullPromptMessage** | nullHandling |
| DATA_MAPPING（数据转换） | targetType, **mappingRows**, uuid, targetField, mappingMode, value, subobjects | — |
| CONVERT_DATA（类型转换） | regex | — |
| CALL_DATA_FLOW（生单规则） | dataFlowMappingId, structure, entityId | dataSourceType |
| CALL_APP_SERVICE（自定义服务） | — | mappingType |
| PUBLISH_BUSINESS_EVENT（事件投递） | mappingType | eventType, messageType |
| SUB_MICROFLOW（子微流程） | mappingType | — |
| BranchNode（分支） | conditions | — |
| ConditionNode（条件） | nodes | — |
| ForNode（计数循环） | operator, forStep | errorMsg |
| CustomErrorNode（自定义错误） | — | errorType |

## 3. ★RETRIEVE_ARRAY 分 fetchType 的必填（最有价值，推翻前端推断）

后端 `parseActivityNode`（RetrieveEntityArrayActivity.java）逐分支：
```
fetchType 缺省 = CONDITION
CONDITION:  pageSearch=true  → 必填 pageInfo（分页）
            pageSearch=false → 必填 size（int，缺省 20）；必填 condition
IDS:        必填 value（ID 集合 AttrValue）；不需要 condition
COUNT:      必填 condition
OTHERS:     必填 aggFunction（枚举）+ countAttrs（AttrType 数组）；必填 condition
output:     必填（buildOutPut(... requiredJavaType)）
```
- `RETRIEVE_ARRAY` 的分页开关字段是 **`pageSearch`**（"true"/"false" 字符串），**不是**我先前写的 `pageSearch:"N"`
- `aggFunction` 在 OTHERS 分支才是 required；CONDITION 分支不需要
- `size` 在 CONDITION+非分页时 required（默认 20）

## 4. ★RETRIEVE（查询单记录）
- `fetchType` 缺省 = CONDITION；`CONDITION` 需 condition；`IDS` 需 value；`COUNT`/`OTHERS` 需 condition
- `nullHandling` ∈ `CONTINUE|STOP`；STOP 时 `nullPromptMessage` required
- `needCascade` 布尔

## 5. ★DATA_MAPPING（数据转换）—— 真实结构
后端 `DataMappingActivity`：`mappingRule` 里是 **`mappingRows`**（不是我先前写的 `mappings`）：
```
必填: targetType(枚举) + mappingRule{uuid, mappingRows:[{uuid, targetField, mappingMode(枚举), value, subobjects}]}
```
- `mappingMode` 值域见 `DataMappingActivity$DataMappingTargetTypeEnum` + mappingMode 枚举
- 每条 row：`{uuid, targetField(目标字段), mappingMode, value(源值 AttrValue), subobjects[]}`

### LIVE 实证真实形态（test2 标品，字节级一致）
```json
"mappingRule": {"uuid":"6730ec...","targetType":"ENTITY","mappingRows":[
  {"uuid":"b7eefd...",
   "targetField":{"path":[{"id":"<DTO>.expText","name":"expText","caption":"实验文本(已改)",
                           "dataType":"STRING","javaType":"java.lang.String",
                           "entityId":"474806313816300867","entityFullName":"<EntityFull>"}]},
   "mappingMode":"REFERENCE",
   "value":{"reference":{"path":[{...同上 path 元素...}]}}}]}
```
**path 元素权威字段**：`id`(全限定 DTO.field) / `name`(字段名) / `caption`(显示名) / `dataType` /
`javaType` / `entityId` / `entityFullName`。REFERENCE 分支 `value.reference.path`；CONSTANT 分支 `value.constant`。

## 6. 关键枚举（后端权威）
- `ActivityNodeTypeEnum`：RETRIEVE / RETRIEVE_ARRAY / CREATE_ENTITY / CREATE_BATCH_ENTITY / CHANGE_ENTITY /
  CHANGE_BATCH_ENTITY / DELETE_ENTITY / CREATE_VARIABLE / CHANGE_VARIABLE / CREATE_LIST / CHANGE_LIST /
  LIST_OPERATION / CREATE_MAP / MAP_OPERATION / DATA_MAPPING / CONVERT_DATA / CALL_APP_SERVICE /
  SUB_MICROFLOW / CALL_DATA_FLOW / PUBLISH_BUSINESS_EVENT / CONNECTOR / Rule activities
- `RetrieveEntityArrayActivity$FetchType`：CONDITION / IDS / COUNT / OTHERS
- `DataMappingActivity$DataMappingTargetTypeEnum`：ENTITY / DTO / METADATA ...
- `ConvertDataActivity` convertType：11 值（MultiAssociation2List / String2Integer / GetEnumCode / Split ...）
- `CallDataFlowActivity$DataSourceTypeEnum`：dataSourceType 值域

## 7. 待补挖（下一批）
- `DataMappingActivity$DataMappingTargetTypeEnum` + mappingMode 枚举全值域
- `RetrieveEntityArrayActivity$FetchType` 各分支的 AttrValue 内部结构
- `MicroFlowComponentUtils.buildConditionInfo` / `checkConditionInfo`（condition 校验细则）
- `RetrieveSortParam` / `ObjectSortParam`（排序结构）
- 条件过滤器（where）操作符与 dataType 映射（前端 xiaozhua-biz-where，已另档）

## 8. 与前端推断的差异（修正记录）
| 项 | 先前（前端推断，误） | 后端权威（修正） |
| --- | --- | --- |
| DATA_MAPPING 映射 | `mappingRule.mappings[]` | `mappingRule.mappingRows[]` |
| DATA_MAPPING mappingMode | `FieldCopy` | `REFERENCE`(0) / `CONSTANT`(1) |
| DATA_MAPPING targetType | `ENTITY_OBJECT` | `ENTITY`(0) / `DTO`(1) |
| RETRIEVE_ARRAY 分页 | `pageSearch:"N"` | `pageSearch:"false"`（字符串布尔） |
| RETRIEVE 空值 | — | `nullHandling ∈ TERMINATION|CONTINUE`；TERMINATION 才需 nullPromptMessage |

## 9. 枚举全值域（后端权威，机器可读模型见 components/udc/microflow_constraints.py）

- **ActivityNodeTypeEnum**（48 码）：CONNECTOR 0 / CREATE_VARIABLE 1 / CHANGE_VARIABLE 2 / CREATE_LIST 3 /
  CHANGE_LIST 4 / PUBLISH_BUSINESS_EVENT 5 / ATTRIBUTE_REQUIRED 6 / ASSIGN_VALUE 7 / SHOW_MESSAGE 8 /
  ATTRIBUTE_UNIQUE 9 / RETRIEVE 10 / RETRIEVE_ARRAY 11 / CHANGE_ENTITY 12 / CREATE_ENTITY 13 /
  DELETE_ENTITY 14 / LIST_OPERATION 15 / SUB_MICROFLOW 16 / CALL_MICRO_FLOW 17 / CALL_APP_SERVICE 18 /
  CALL_DATA_FLOW 19 / DEFAULT_VALUE 21 / CONVERT_DATA 40 / CREATE_BATCH_ENTITY 41 / CHANGE_BATCH_ENTITY 42 /
  CREATE_MAP 43 / MAP_OPERATION 44 / DATA_MAPPING 45 / CALL_DATA_FLOW_FRONT 46 / EXTEND_ACTION 47 / SET_DATASOURCE 48
- **MicroFlowNodeTypeEnum**：CONDITION/FOR_EACH/BRANCH/CUSTOM_ERROR/END/ACTIVITY/FOR/BREAK
- **RETRIEVE_ARRAY FetchType**：CONDITION/IDS/COUNT/OTHERS
- **DataMappingTargetTypeEnum**：ENTITY/DTO；**DataMappingMode**：REFERENCE/CONSTANT；
  **ConstantValueType**：SIMPLE/JAVA_ENUM/CTP_ENUM
- **MappingTypeEnum**：attrs/value/mapping；**AttrValueTypeEnum**：Expression/SelectParam/CtpEnum/Simple/
  System/SelectPeopleData/Enum/CONTEXT_VARIABLE
- **NullHandlingEnum**：TERMINATION/CONTINUE；**CronTypeEnum**：FIRST/LAST/ANY；
  **RotationTypeEnum**：DAY/HOUR/MINUTE
- **MicroFlowDtoTypeEnum**：MASTER_ENTITY/SUB_ENTITY/CUSTOM/THIRD/MESSAGE/MICRO_FLOW_EVENT
- **ChangeListActionTypeEnum**：ADD/REMOVE/CLEAR/REPLACE；**MapOperationTypeEnum**：GET/PUT/REMOVE/KEY_SET
- **ListOperationTypeEnum**（19 种）：sum/size/max/min/filter/find/sort/union/intersect/subtract/contains/
  equals/groupAndSum/firstOne/lastOne/pickOne/distinct/subList/map
- **AppServiceTypeEnum**（20 种平台服务）：selectPageByComplexConditions/create/createBatch/update/.../deleteByComplexConditions
- **CallDataFlowActivity$DataSourceTypeEnum**：CONDITION/SELECT_PARAM
- **MetaDataTypeEnum**：ENTITY/PAGE；**CustomErrorTypeEnum**：USER；**DtoParserTypeEnum**：JSON/XML
- **事件**：MicroFlowEventTypeEnum AMONG_APP/IN_APP；MicroFlowGroupTypeEnum BACKEND_SERVICE/FRONTEND_FUNCTION/PAGE_RULE

## 10. 校验错误码（MicroFlowParseErrorEnum，68 项精选）——"限制条件"文案与落点
`PROPERTY_IS_REQUIRED`=必填参数未配置；`NOT_MATCH`=数据类型不匹配；`NOT_RELEASE`=调用微流程非正式态；
`WITHOUT_OUTPUT`=没定义出参；`LOOP_CALL`=循环调用；`ENTITY_DELETE`=实体已删除；`METADATA_DELETE`=元数据已删；
`SCHEDULE_NOT_EXIST`=定时任务在调度中心不存在；`CONNECTOR_*_DELETED`=连接器不存在；`MQ_DELETE`=MQ 消息不存在；
`EVENT_USED`=业务事件已被其他微流程使用；`LIST_OPERATION_SUB_LIST_INDEX_LESS_THAN_ONE` 等。
