# NODE-CENSUS｜微流程节点全量事实清单（B-1R）

> ℹ️ **两份 NODE-CENSUS 不是重复**：本文件 scope=**all**（4755 流程 / 55670 节点，快照 2026-10-19 10:24:32）；
> `NODE-CENSUS-app-20261018.md` scope=**app**（47 流程 / 251 节点，快照 2026-10-17 15:41:03）。
> **引用数字必须连快照戳一起引，不可跨文件混用。**

> 生成：2026-10-19T11:11:09 ｜ 脚本：`tools/core/b10_node_census.py`（**已移入 `_attic_pending/legacy-audit/b10_node_census.py`**，仓库内已无此路径）（可重跑，只读）
> **数据快照戳 MAX(update_time)=2026-10-19 10:24:32**（引用本文件任何数字时必须连此戳一起引）
> scope=**all** ｜ 证据：**LIVE（DB 只读回读）** ｜ 覆盖缺失：**VACUUM**

## 一、总量

| 项 | 值 |
|---|---|
| flows | 4755 |
| nodes | 55670 |
| activity_instances | 28616 |
| control_instances | 27054 |
| zero_node_flows | 226 |
| null_schema | 0 |
| bad_json | 0 |
| trigger 分布 | {'MANUAL': 4121, 'BUSINESS_EVENT': 254, 'SCHEDULE': 136} |
| endNode.actionType | {'END_NODE': 4528} |

### 口径分解（**数字对账用；引用数字必须带口径**）

| 口径 | 含义 | 数量 |
|---|---|---|
| t0 | 顶层 `nodes[]`（= main D142 的 136 口径） | 10876 |
| t1 | `endNode`（END / actionType=END_NODE） | 4528 |
| t2 | 分支体内节点（`conditions[].nodes[]`，可嵌套） | 25617 |
| t3 | `CONDITION` 条目（`BRANCH.conditions[]` 每项） | 14649 |
| **合计** | **= 本脚本 nodes 口径** | **55670** |

| SQL 独立对拍 | t0 | endNode | flows |
|---|---|---|---|
| SQL（JSON_LENGTH / JSON_CONTAINS_PATH） | 10876 | 4528 | 4755 |
| 解析器（本脚本） | 10876 | 4528 | 4755 |

| 第二遍历（结构盲扫，按 nodeId 去重） | — | — | — |
| 四口径合计 t0+t1+t2+t3 | 55670 | 第二遍历 uniq | 55670 |

> ★ 136 与 251 不是矛盾，是口径不同：136=t0，251=t0+t1+t2+t3。**未标口径的数字不得跨文档比较。**

> ★ t2/t3 无 SQL 表达式（嵌套任意深度），改用「第二遍历盲扫」独立对拍；t0/t1 仍走 SQL JSON 函数。两条路径都不经过对方。


## 二、按流程类型分层（type=1 是前端域，另一套枚举）

| type | 含义 | 流程数 | 节点数 | ACTIVITY 种类 | CONTROL 种类 |
|---|---|---|---|---|---|
| 0 | SERVICE(标准) | 1401 | 22671 | 20 | 7 |
| 1 | FRONT(前端域) | 2840 | 32355 | 37 | 6 |
| 2 | OTHER(2) | 25 | 158 | 3 | 3 |
| 3 | CUSTOM(自定义) | 489 | 486 | 3 | 1 |

## 三、标准域（type=0/3）覆盖 vs constraints

> ★ **范围声明**：本章「缺失」= **标准域 type=0/3 下 0 实例**，**不是全库 0 实例**。`CALL_MICRO_FLOW` 等在全库确有实例（见 type=1/2 分层）。引用 VACUUM 必须连范围一起引。

| 域 | 声明 | 实测 | 缺失(VACUUM) | 越界 |
|---|---|---|---|---|
| ACTIVITY | 30 | 20 | 10 | 0 |
| CONTROL | 8 | 7 | 1 | 0 |

**ACTIVITY 缺失 — VACUUM（标准域 type=0/3 内 0 实例；完备负证据，非缺陷）**

```
ASSIGN_VALUE
ATTRIBUTE_REQUIRED
ATTRIBUTE_UNIQUE
CALL_DATA_FLOW_FRONT
CALL_MICRO_FLOW
CONNECTOR
DEFAULT_VALUE
EXTEND_ACTION
SET_DATASOURCE
SHOW_MESSAGE
```

**CONTROL 缺失 — VACUUM（标准域 type=0/3 内 0 实例；完备负证据，非缺陷）**

```
ACTIVITY
```

### 标准域 ACTIVITY 实例分布（20 种）

| actionType | 实例数 |
|---|---|
| CHANGE_VARIABLE | 2741 |
| CREATE_VARIABLE | 1976 |
| RETRIEVE | 1839 |
| LIST_OPERATION | 1229 |
| CHANGE_LIST | 895 |
| SUB_MICROFLOW | 823 |
| RETRIEVE_ARRAY | 603 |
| CREATE_LIST | 552 |
| CHANGE_ENTITY | 403 |
| CALL_APP_SERVICE | 347 |
| CONVERT_DATA | 232 |
| CREATE_ENTITY | 218 |
| CHANGE_BATCH_ENTITY | 96 |
| MAP_OPERATION | 75 |
| PUBLISH_BUSINESS_EVENT | 72 |
| DELETE_ENTITY | 43 |
| CREATE_BATCH_ENTITY | 34 |
| CREATE_MAP | 30 |
| DATA_MAPPING | 26 |
| CALL_DATA_FLOW | 9 |

### 标准域 CONTROL 实例分布（7 种）

| type | 实例数 |
|---|---|
| CONDITION | 5408 |
| BRANCH | 2516 |
| END | 1867 |
| FOR_EACH | 923 |
| CUSTOM_ERROR | 123 |
| FOR | 66 |
| BREAK | 11 |

## 四、异常项

| 项 | 数 | 样本 |
|---|---|---|
| control_with_actionType | 66 | [(-8837454891007579330, 'BREAK_cVarTH', 'BREAK', 'BREAK'), (-8737046466134762263, 'BREAK_SZR3aj', 'BREAK', 'BREAK'), (-8737046466134762263, 'BREAK_8FEumA', 'BREAK', 'BREAK'), (-873 |

## 五、每种 actionType 的字段键（P2 输入）

> 「实际出现过哪些键」≠「必填哪些」。必填集见 `components/udc/microflow_constraints.py:NODE_REQUIRED_FIELDS`。

| actionType | 键数 | 键 |
|---|---|---|
| ADVANCED_PROPERTIES | 11 | `actionType`, `caption`, `description`, `input`, `isCompleted`, `items`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| ATTACHMENT_DOWNLOAD | 12 | `actionType`, `attachment`, `caption`, `description`, `input`, `isCompleted`, `microwPreout`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| ATTACHMENT_PREVIEW | 12 | `actionType`, `attachment`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| ATTACHMENT_UPLOAD | 20 | `actionType`, `caption`, `countLimitType`, `description`, `fileFormat`, `fileFormatSetting`, `fileSize`, `fileSizeType`, `input`, `isCompleted`, `isEdit`, `isImgCompress`, `multiple`, `name`, `nodeId`, `output`, `outputName`, `runAfter`, `type`, `uploadType` |
| ATTRIBUTE_REQUIRED | 12 | `actionType`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `params`, `runAfter`, `type`, `value` |
| CALL_APP_SERVICE | 18 | `actionType`, `app`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `mappingType`, `name`, `nodeId`, `outPutDesc`, `output`, `outputName`, `pageInfo`, `runAfter`, `selectMethod`, `type`, `value` |
| CALL_DATA_FLOW | 17 | `actionType`, `caption`, `condition`, `dataFlow`, `dataFlowMappingId`, `dataSourceType`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `structure`, `title`, `type` |
| CALL_DATA_FLOW_FRONT | 14 | `action`, `actionName`, `actionType`, `caption`, `dataflow`, `dataflowPull`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| CALL_FRONT_FLOW | 16 | `actionType`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `mappingType`, `microFlow`, `name`, `nodeId`, `outPutDesc`, `output`, `outputName`, `runAfter`, `type`, `value` |
| CALL_MICRO_FLOW | 18 | `actionType`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `mappingType`, `mfService`, `name`, `nodeId`, `outPutDesc`, `output`, `outputCustomFields`, `outputName`, `pageInfoSourceElement`, `runAfter`, `type`, `value` |
| CHANGE_BATCH_ENTITY | 13 | `actionType`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `title`, `type` |
| CHANGE_ENTITY | 13 | `actionType`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `title`, `type` |
| CHANGE_LIST | 14 | `action`, `actionType`, `caption`, `countAttrs`, `dataSource`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `type` |
| CHANGE_LIST_FRONT | 15 | `action`, `actionType`, `caption`, `countAttrs`, `dataSource`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `nodeRemark`, `output`, `runAfter`, `selectParam`, `type` |
| CHANGE_VARIABLE | 17 | `actionType`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `mapping`, `mappingType`, `name`, `nodeId`, `nodeRemark`, `output`, `runAfter`, `selectMappingParam`, `selectParam`, `type`, `value` |
| CHANGE_VARIABLE_FRONT | 14 | `actionType`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `mappingType`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `type`, `value` |
| CLOSE_PAGE | 12 | `actionType`, `caption`, `confirmSwitch`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `showInfo`, `type` |
| CONFIRM_CLOSE_PAGE | 10 | `actionType`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| CONTROL_ACTION | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| CONTROL_STATUS | 14 | `actionType`, `caption`, `description`, `disabled`, `editable`, `input`, `invisible`, `isCompleted`, `name`, `nodeId`, `output`, `readOnly`, `runAfter`, `type` |
| CONVERT_DATA | 14 | `actionType`, `caption`, `convertType`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `regex`, `runAfter`, `selectParam`, `title`, `type` |
| CONVERT_DATA_FRONT | 14 | `actionType`, `caption`, `convertType`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `regex`, `runAfter`, `selectParam`, `title`, `type` |
| CREATE_BATCH_ENTITY | 12 | `actionType`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `title`, `type` |
| CREATE_ENTITY | 17 | `actionType`, `app`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `mappingType`, `methodLegal`, `name`, `nodeId`, `output`, `runAfter`, `structure`, `title`, `type`, `value` |
| CREATE_LIST | 14 | `actionType`, `app`, `caption`, `dataType`, `description`, `isCompleted`, `nodeId`, `output`, `paramType`, `runAfter`, `structure`, `title`, `type`, `value` |
| CREATE_LIST_FRONT | 14 | `actionType`, `app`, `caption`, `dataSource`, `dataType`, `description`, `isCompleted`, `nodeId`, `output`, `paramType`, `runAfter`, `structure`, `title`, `type` |
| CREATE_MAP | 13 | `actionType`, `caption`, `description`, `entries`, `generics`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `title`, `type` |
| CREATE_VARIABLE | 23 | `actionType`, `app`, `attrs`, `caption`, `connector`, `connectorMethod`, `dataType`, `description`, `input`, `isCompleted`, `mapping`, `mappingType`, `nodeId`, `nodeRemark`, `otherType`, `output`, `paramType`, `runAfter`, `selectParam`, `structure`, `title`, `type`, `value` |
| CREATE_VARIABLE_FRONT | 17 | `actionType`, `app`, `attrs`, `caption`, `dataType`, `description`, `isCompleted`, `mappingType`, `nodeId`, `output`, `paramType`, `runAfter`, `selectParam`, `structure`, `title`, `type`, `value` |
| DATA_MAPPING | 17 | `actionType`, `app`, `caption`, `dataType`, `description`, `input`, `isCompleted`, `mappingRule`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `structure`, `targetType`, `title`, `type` |
| DELETE_ENTITY | 18 | `actionType`, `app`, `caption`, `condition`, `deleteType`, `description`, `input`, `isCompleted`, `methodLegal`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `structure`, `title`, `type`, `value` |
| ENTITY_DELETE | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| ENTITY_EXPORT | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| ENTITY_IMPORT | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| ENTITY_REFRESH | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| ENTITY_SAVE | 12 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `outputName`, `runAfter`, `type` |
| ENTITY_SAVE_DRAFT | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| ENTITY_SUBMIT | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| FED_LIST_OPERATION | 18 | `actionType`, `caption`, `countAttrs`, `description`, `expression`, `index`, `input`, `isCompleted`, `name`, `nodeId`, `operationParam`, `operationType`, `output`, `runAfter`, `selectParam`, `sortParams`, `title`, `type` |
| FLOW_ACTION | 16 | `actionName`, `actionType`, `bpmSelectPeopleContent`, `bpmSelectPeopleWayOptions`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeAfterAction`, `nodeId`, `output`, `popBpmSelectPeople`, `runAfter`, `target`, `type` |
| FORM_CONVERT | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| FRONT_CUSTOM_ERROR | 11 | `actionType`, `caption`, `description`, `error`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| LIST_OPERATION | 22 | `actionType`, `caption`, `countAttrs`, `description`, `expression`, `groupByAttrs`, `indexValue`, `input`, `isCompleted`, `name`, `nodeId`, `nodeRemark`, `operationParam`, `operationType`, `output`, `runAfter`, `selectParam`, `sortParams`, `subEndIndex`, `subStartIndex`, `title`, `type` |
| LOCATION_CMP | 11 | `actionType`, `caption`, `controlId`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| MAP_OPERATION | 24 | `actionType`, `app`, `arrayOrObject`, `basic`, `caption`, `dataType`, `description`, `entries`, `generics`, `input`, `isCompleted`, `name`, `nodeId`, `nullHandling`, `nullPromptMessage`, `operationType`, `output`, `paramType`, `runAfter`, `selectMap`, `structure`, `theKey`, `title`, `type` |
| MESSAGE_INFO | 14 | `actionType`, `caption`, `closeType`, `description`, `element`, `input`, `isCompleted`, `messageType`, `name`, `nodeId`, `output`, `runAfter`, `showInfo`, `type` |
| MODAL | 18 | `actionType`, `cancelText`, `caption`, `configBtn`, `coustom`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `okText`, `outPutName`, `output`, `runAfter`, `scenario`, `showInfo`, `title`, `type` |
| OPEN_LINK | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| OPEN_PAGE | 12 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `outputName`, `runAfter`, `type` |
| PUBLISH_BUSINESS_EVENT | 19 | `actionType`, `app`, `attrs`, `caption`, `description`, `eventType`, `executeTime`, `input`, `isCompleted`, `mappingType`, `messageType`, `name`, `nodeId`, `output`, `runAfter`, `selectEvent`, `selectMq`, `type`, `value` |
| RELOAD_PAGE | 10 | `actionType`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| RETRIEVE | 24 | `actionType`, `app`, `caption`, `condition`, `description`, `fetchType`, `input`, `isCompleted`, `methodLegal`, `name`, `needCascade`, `nodeId`, `nodeRemark`, `nullHandling`, `nullPromptMessage`, `output`, `runAfter`, `scope`, `selectType`, `sortParams`, `structure`, `title`, `type`, `value` |
| RETRIEVE_ARRAY | 28 | `actionType`, `aggFunction`, `app`, `caption`, `condition`, `countAttrs`, `description`, `fetchType`, `input`, `isCompleted`, `mappingType`, `methodLegal`, `name`, `nodeId`, `nullHandling`, `output`, `pageInfo`, `pageSearch`, `runAfter`, `scope`, `selectType`, `size`, `sortObject`, `sortParams`, `structure`, `type`, `value`, `variableTitle` |
| SET_VALUE | 12 | `actionType`, `caption`, `description`, `element`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type`, `value` |
| SHOW_MESSAGE | 13 | `actionType`, `caption`, `description`, `input`, `isCompleted`, `level`, `name`, `nodeId`, `output`, `param`, `runAfter`, `type`, `value` |
| SUB_MICROFLOW | 17 | `actionType`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `mappingType`, `mfService`, `name`, `nodeId`, `outPutDesc`, `output`, `outputName`, `pageInfo`, `runAfter`, `type`, `value` |
| THROW_EVENT | 11 | `actionType`, `caption`, `description`, `event`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| VALUE_HANDLE | 11 | `actionType`, `caption`, `description`, `input`, `isCompleted`, `items`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| VISIBLE | 12 | `actionType`, `caption`, `description`, `input`, `invisible`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type`, `visible` |