# 24 类微流程节点结构要点 + 依赖关系

节点清单/actionType/必填项台账见 `references/24-node-contracts.md`；逐节点操作与真实表单值见 `references/frontend-node-authoring-cdp.md`。本文件只讲**节点间的结构要点与依赖**：哪些节点要先造别的东西、哪些节点有前置资源要求。

## 无外部依赖（可独立构造）

| actionType | 关键字段/结构 | 注意 |
|---|---|---|
| RETRIEVE | fetchType=CONDITION + condition + structure + output | leftParam.id = 属性数字 id（不是 DTO 全名） |
| RETRIEVE_ARRAY | 同 RETRIEVE，output.type=ARRAY + sortParams + size | 列表源 |
| CREATE_ENTITY | structure + mappingType=attrs + attrs[{attrType,value}] | value 用 SelectParam/Simple/Expression |
| CHANGE_ENTITY | selectParam(引用实体变量) + attrs | selectParam.outputName 指向 CREATE_VARIABLE 出参 |
| CREATE_BATCH_ENTITY | selectParam 引用 ARRAY 源 + output.type=ARRAY | |
| CHANGE_BATCH_ENTITY | 同 CREATE_BATCH | |
| DELETE_ENTITY | deleteType=CONDITION + condition + output(INTEGER) | |
| CREATE_VARIABLE | paramType=BASIC/ENTITY + output | ENTITY 型必须带 `app`（见 SKILL.md） |
| CHANGE_VARIABLE | selectParam(引用变量) + mappingType=attrs + attrs | |
| CREATE_LIST | paramType=BASIC + output.type=ARRAY | 无其他必填 |
| CHANGE_LIST | selectParam(引用列表) + action=ADD + dataSource | |
| CREATE_MAP | generics{keyType,valueType} + entries | |
| MAP_OPERATION | selectMap(引用 Map) + operationType=PUT + entries | |
| LIST_OPERATION | selectParam(引用列表) + operationType=SIZE | selectParam 必须带 dtoType（见 SKILL.md） |
| CONVERT_DATA | convertType{desc,value} + selectParam + regex | Split 等 |
| DATA_MAPPING | mappingRule{mappingRows[{targetField,mappingMode,value}]} + selectParam | |
| CUSTOM_ERROR | error{type,simple,desc} + errorType=GLOBAL | 终止节点必填「提示消息」= error.simple |
| BRANCH | conditions[{nodeId,name=ifBranch,expression,nodes[]}, {name=elseBranch,nodes[]}] | 分支内嵌子节点 |
| FOR | foreach/forStart+forEnd+forStep+operator+output+nodes[] | 循环内嵌子节点；BREAK 只能放循环内 |
| BREAK | 空结构 | 必须在 FOR 内 |
| PUBLISH_BUSINESS_EVENT | eventType=IN_APP + selectEvent(事件 DTO) + mappingType=attrs + attrs | 事件投递，非 EVENT_DELIVERY |

## 依赖型节点（必须先有真实前置资源，不能凭空写 id）

| actionType | 前置资源 | 取证接口 |
|---|---|---|
| CALL_DATA_FLOW（执行生单规则） | 一条「手动映射」生单规则，且来源实体 = 目标实体 | `udcDataFlowListManuallyMappingPost`，variables `{appId, sourceEntityId}`；返回空 = 该实体下没配规则，需先建 |
| SUB_MICROFLOW（子微流程） | 一条现成 SERVICE+MANUAL 流程作目标 | `udcMicroflowSearch`（IN_type=[SERVICE,CUSTOM]，筛 type=SERVICE & triggerType=MANUAL） |
| CALL_APP_SERVICE（跨应用自定义服务） | 一个可调用的服务接口（如 organization 的 selectMemberMetadataInfo） | selectMethod{interfaceClass,fullName,parameter,returnValue,attrs} |

## 节点引用契约（所有「引用前序节点」的节点通用）

- `selectParam` / `selectMap` / `selectParam.nodeInfo` 里的 `outputName`、`nodeInfo.nodeId` 必须等于**回读后**的前序节点真实 output.name / nodeId。
- 值编辑器三种 `value`：`{type:"Simple", simple:...}`（常量）、`{type:"SelectParam", selectParam:{...}}`（引用）、`{type:"Expression", expression:{title,schema}}`（表达式）。schema 内嵌 `designData.context` 描述变量树，`tokens` 描述表达式 token。
- 表达式 schema 是长 JSON 字符串（转义层多），引用字段时 tokens 的 VARIABLE.value 形如 `_RETRIEVE_xxx._RETRIEVE_xxx.<field>`，desc 形如「查询单条数据(1).文本字段」。

## 表达式不能用「最小形态」凑（旧写法已废弃）

曾经用「BOOLEAN 常量 true」这类最小形态让 BRANCH/FOR 过 checkSchema——**这是错的，不要再做**。checkSchema 只校验结构，塞真值也能过，但前端可视化编辑器里看不到真实表达式，用户一眼判定「糊 check」并删流程。

所有表达式（分支条件、修改变量、循环终止值、默认值、条件右值）必须：
1. 组 tokens（CONSTANT/VARIABLE/SYSTEM/FUNCTION/OPERATOR）
2. 走 `/service/udc/expression/check`
3. 走 `/service/udc/expression/transform` 产出 `{designData, runtimeData}`
4. 两列都落库

引用前序节点字段时 `schemas` 必须传该节点的三级出参变量树（否则 FORMULA_6058），VARIABLE token 的 value 是三级 `<节点出参名>.<节点出参名>.<字段名>`。详见 SKILL.md「表达式必须走 transform 接口」节。

修改变量必须真的做业务计算：`字段A + 字段B`、`textToDecimal(文本)+5`、`substring(文本,0,3) + '拼接串'`——只填常量等于没做。

## 数据源顺序依赖（部分节点要先建 BASIC 变量）

- MAP_OPERATION 的 entries[].key/value 若引用变量，需先 CREATE_VARIABLE（paramType=BASIC）建 vText(STRING)/vNum(BIGINTEGER) 作数据源，再用 SelectParam 引用其 output.name。
- CHANGE_LIST 的 dataSource 是 SelectParam 引用，同样需要先有数据源变量（或引用列表本身）。
- 造节点时按「先建源变量 → 再建消费节点」的顺序追加，避免引用落空。
