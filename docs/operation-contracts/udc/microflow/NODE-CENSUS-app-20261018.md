# NODE-CENSUS｜微流程节点全量事实清单（B-1R）

> ℹ️ **两份 NODE-CENSUS 不是重复**：本文件 scope=**app**（47 流程 / 251 节点，快照 2026-10-17 15:41:03）；
> `NODE-CENSUS-all-20261018.md` scope=**all**（4755 流程 / 55670 节点，快照 2026-10-19 10:24:32）。
> **引用数字必须连快照戳一起引，不可跨文件混用。**

> 生成：2026-10-19T11:11:10 ｜ 脚本：`tools/core/b10_node_census.py`（**已移入 `_attic_pending/legacy-audit/b10_node_census.py`**，仓库内已无此路径）（可重跑，只读）
> **数据快照戳 MAX(update_time)=2026-10-17 15:41:03**（引用本文件任何数字时必须连此戳一起引）
> scope=**app** ｜ 证据：**LIVE（DB 只读回读）** ｜ 覆盖缺失：**VACUUM**

## 一、总量

| 项 | 值 |
|---|---|
| flows | 47 |
| nodes | 251 |
| activity_instances | 155 |
| control_instances | 96 |
| zero_node_flows | 1 |
| null_schema | 0 |
| bad_json | 0 |
| trigger 分布 | {'SCHEDULE': 4, 'MANUAL': 39, 'BUSINESS_EVENT': 3} |
| endNode.actionType | {'END_NODE': 46} |

### 口径分解（**数字对账用；引用数字必须带口径**）

| 口径 | 含义 | 数量 |
|---|---|---|
| t0 | 顶层 `nodes[]`（= main D142 的 136 口径） | 136 |
| t1 | `endNode`（END / actionType=END_NODE） | 46 |
| t2 | 分支体内节点（`conditions[].nodes[]`，可嵌套） | 35 |
| t3 | `CONDITION` 条目（`BRANCH.conditions[]` 每项） | 34 |
| **合计** | **= 本脚本 nodes 口径** | **251** |

| SQL 独立对拍 | t0 | endNode | flows |
|---|---|---|---|
| SQL（JSON_LENGTH / JSON_CONTAINS_PATH） | 136 | 46 | 47 |
| 解析器（本脚本） | 136 | 46 | 47 |

| 第二遍历（结构盲扫，按 nodeId 去重） | — | — | — |
| 四口径合计 t0+t1+t2+t3 | 251 | 第二遍历 uniq | 251 |

> ★ 136 与 251 不是矛盾，是口径不同：136=t0，251=t0+t1+t2+t3。**未标口径的数字不得跨文档比较。**

> ★ t2/t3 无 SQL 表达式（嵌套任意深度），改用「第二遍历盲扫」独立对拍；t0/t1 仍走 SQL JSON 函数。两条路径都不经过对方。


## 二、按流程类型分层（type=1 是前端域，另一套枚举）

| type | 含义 | 流程数 | 节点数 | ACTIVITY 种类 | CONTROL 种类 |
|---|---|---|---|---|---|
| 0 | SERVICE(标准) | 10 | 74 | 18 | 3 |
| 1 | FRONT(前端域) | 27 | 164 | 27 | 3 |
| 3 | CUSTOM(自定义) | 10 | 13 | 3 | 1 |

## 三、标准域（type=0/3）覆盖 vs constraints

> ★ **范围声明**：本章「缺失」= **标准域 type=0/3 下 0 实例**，**不是全库 0 实例**。`CALL_MICRO_FLOW` 等在全库确有实例（见 type=1/2 分层）。引用 VACUUM 必须连范围一起引。

| 域 | 声明 | 实测 | 缺失(VACUUM) | 越界 |
|---|---|---|---|---|
| ACTIVITY | 30 | 18 | 12 | 0 |
| CONTROL | 8 | 3 | 5 | 0 |

**ACTIVITY 缺失 — VACUUM（标准域 type=0/3 内 0 实例；完备负证据，非缺陷）**

```
ASSIGN_VALUE
ATTRIBUTE_REQUIRED
ATTRIBUTE_UNIQUE
CALL_DATA_FLOW
CALL_DATA_FLOW_FRONT
CALL_MICRO_FLOW
CONNECTOR
CREATE_BATCH_ENTITY
DEFAULT_VALUE
EXTEND_ACTION
SET_DATASOURCE
SHOW_MESSAGE
```

**CONTROL 缺失 — VACUUM（标准域 type=0/3 内 0 实例；完备负证据，非缺陷）**

```
ACTIVITY
BREAK
CUSTOM_ERROR
FOR
FOR_EACH
```

### 标准域 ACTIVITY 实例分布（18 种）

| actionType | 实例数 |
|---|---|
| RETRIEVE | 7 |
| RETRIEVE_ARRAY | 6 |
| DATA_MAPPING | 6 |
| SUB_MICROFLOW | 5 |
| CREATE_VARIABLE | 4 |
| CHANGE_VARIABLE | 4 |
| DELETE_ENTITY | 3 |
| CREATE_LIST | 2 |
| CHANGE_LIST | 2 |
| LIST_OPERATION | 2 |
| MAP_OPERATION | 2 |
| CHANGE_ENTITY | 2 |
| CHANGE_BATCH_ENTITY | 2 |
| CREATE_ENTITY | 2 |
| CONVERT_DATA | 2 |
| CALL_APP_SERVICE | 2 |
| PUBLISH_BUSINESS_EVENT | 2 |
| CREATE_MAP | 1 |

### 标准域 CONTROL 实例分布（3 种）

| type | 实例数 |
|---|---|
| END | 20 |
| CONDITION | 7 |
| BRANCH | 4 |

## 四、异常项

| 项 | 数 | 样本 |
|---|---|---|

## 五、每种 actionType 的字段键（P2 输入）

> 「实际出现过哪些键」≠「必填哪些」。必填集见 `components/udc/microflow_constraints.py:NODE_REQUIRED_FIELDS`。

| actionType | 键数 | 键 |
|---|---|---|
| ATTACHMENT_DOWNLOAD | 12 | `actionType`, `attachment`, `caption`, `description`, `input`, `isCompleted`, `microwPreout`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| ATTACHMENT_UPLOAD | 17 | `actionType`, `caption`, `description`, `fileFormatSetting`, `fileSizeType`, `input`, `isCompleted`, `isEdit`, `isImgCompress`, `multiple`, `name`, `nodeId`, `output`, `outputName`, `runAfter`, `type`, `uploadType` |
| CALL_APP_SERVICE | 17 | `actionType`, `app`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `mappingType`, `name`, `nodeId`, `outPutDesc`, `output`, `outputName`, `pageInfo`, `runAfter`, `selectMethod`, `type` |
| CALL_DATA_FLOW_FRONT | 14 | `action`, `actionName`, `actionType`, `caption`, `dataflow`, `dataflowPull`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| CALL_FRONT_FLOW | 13 | `actionType`, `caption`, `description`, `input`, `isCompleted`, `microFlow`, `name`, `nodeId`, `outPutDesc`, `output`, `outputName`, `runAfter`, `type` |
| CALL_MICRO_FLOW | 16 | `actionType`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `mappingType`, `mfService`, `name`, `nodeId`, `outPutDesc`, `output`, `outputName`, `runAfter`, `type`, `value` |
| CHANGE_BATCH_ENTITY | 13 | `actionType`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `title`, `type` |
| CHANGE_ENTITY | 13 | `actionType`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `title`, `type` |
| CHANGE_LIST | 13 | `action`, `actionType`, `caption`, `dataSource`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `type` |
| CHANGE_LIST_FRONT | 13 | `action`, `actionType`, `caption`, `dataSource`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `type` |
| CHANGE_VARIABLE | 14 | `actionType`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `mappingType`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `type`, `value` |
| CHANGE_VARIABLE_FRONT | 12 | `actionType`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `type`, `value` |
| CONFIRM_CLOSE_PAGE | 10 | `actionType`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| CONTROL_ACTION | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| CONTROL_STATUS | 14 | `actionType`, `caption`, `description`, `disabled`, `editable`, `input`, `invisible`, `isCompleted`, `name`, `nodeId`, `output`, `readOnly`, `runAfter`, `type` |
| CONVERT_DATA | 14 | `actionType`, `caption`, `convertType`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `regex`, `runAfter`, `selectParam`, `title`, `type` |
| CONVERT_DATA_FRONT | 13 | `actionType`, `caption`, `convertType`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `title`, `type` |
| CREATE_ENTITY | 16 | `actionType`, `app`, `attrs`, `caption`, `description`, `input`, `isCompleted`, `mappingType`, `methodLegal`, `name`, `nodeId`, `output`, `runAfter`, `structure`, `title`, `type` |
| CREATE_LIST | 14 | `actionType`, `app`, `caption`, `dataType`, `description`, `isCompleted`, `nodeId`, `output`, `paramType`, `runAfter`, `structure`, `title`, `type`, `value` |
| CREATE_LIST_FRONT | 14 | `actionType`, `app`, `caption`, `dataSource`, `dataType`, `description`, `isCompleted`, `nodeId`, `output`, `paramType`, `runAfter`, `structure`, `title`, `type` |
| CREATE_MAP | 13 | `actionType`, `caption`, `description`, `entries`, `generics`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `title`, `type` |
| CREATE_VARIABLE | 17 | `actionType`, `app`, `attrs`, `caption`, `dataType`, `description`, `input`, `isCompleted`, `mappingType`, `nodeId`, `output`, `paramType`, `runAfter`, `structure`, `title`, `type`, `value` |
| CREATE_VARIABLE_FRONT | 15 | `actionType`, `app`, `attrs`, `caption`, `dataType`, `description`, `isCompleted`, `mappingType`, `nodeId`, `output`, `paramType`, `runAfter`, `structure`, `title`, `type` |
| DATA_MAPPING | 16 | `actionType`, `app`, `caption`, `description`, `input`, `isCompleted`, `mappingRule`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `structure`, `targetType`, `title`, `type` |
| DELETE_ENTITY | 15 | `actionType`, `app`, `caption`, `condition`, `deleteType`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `selectParam`, `structure`, `type` |
| ENTITY_EXPORT | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| ENTITY_IMPORT | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| ENTITY_REFRESH | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| ENTITY_SAVE | 12 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `outputName`, `runAfter`, `type` |
| ENTITY_SAVE_DRAFT | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| FED_LIST_OPERATION | 14 | `actionType`, `caption`, `description`, `expression`, `input`, `isCompleted`, `name`, `nodeId`, `operationType`, `output`, `runAfter`, `selectParam`, `title`, `type` |
| FLOW_ACTION | 15 | `actionName`, `actionType`, `bpmSelectPeopleContent`, `bpmSelectPeopleWayOptions`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `popBpmSelectPeople`, `runAfter`, `target`, `type` |
| LIST_OPERATION | 14 | `actionType`, `caption`, `countAttrs`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `operationType`, `output`, `runAfter`, `selectParam`, `title`, `type` |
| MAP_OPERATION | 21 | `actionType`, `arrayOrObject`, `basic`, `caption`, `dataType`, `description`, `generics`, `input`, `isCompleted`, `name`, `nodeId`, `nullHandling`, `operationType`, `output`, `paramType`, `runAfter`, `selectMap`, `structure`, `theKey`, `title`, `type` |
| MESSAGE_INFO | 14 | `actionType`, `caption`, `closeType`, `description`, `element`, `input`, `isCompleted`, `messageType`, `name`, `nodeId`, `output`, `runAfter`, `showInfo`, `type` |
| MODAL | 15 | `actionType`, `cancelText`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `okText`, `output`, `runAfter`, `scenario`, `showInfo`, `title`, `type` |
| OPEN_LINK | 11 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| OPEN_PAGE | 12 | `actionType`, `caption`, `config`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `outputName`, `runAfter`, `type` |
| PUBLISH_BUSINESS_EVENT | 14 | `actionType`, `attrs`, `caption`, `description`, `eventType`, `input`, `isCompleted`, `mappingType`, `name`, `nodeId`, `output`, `runAfter`, `selectEvent`, `type` |
| RELOAD_PAGE | 10 | `actionType`, `caption`, `description`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| RETRIEVE | 22 | `actionType`, `app`, `caption`, `condition`, `description`, `fetchType`, `input`, `isCompleted`, `methodLegal`, `name`, `needCascade`, `nodeId`, `nullHandling`, `output`, `runAfter`, `scope`, `selectType`, `sortParams`, `structure`, `title`, `type`, `value` |
| RETRIEVE_ARRAY | 27 | `actionType`, `aggFunction`, `app`, `caption`, `condition`, `countAttrs`, `description`, `fetchType`, `input`, `isCompleted`, `mappingType`, `methodLegal`, `name`, `nodeId`, `nullHandling`, `output`, `pageInfo`, `pageSearch`, `runAfter`, `scope`, `selectType`, `size`, `sortObject`, `sortParams`, `structure`, `type`, `variableTitle` |
| SUB_MICROFLOW | 14 | `actionType`, `caption`, `description`, `input`, `isCompleted`, `mfService`, `name`, `nodeId`, `outPutDesc`, `output`, `outputName`, `runAfter`, `type`, `value` |
| THROW_EVENT | 11 | `actionType`, `caption`, `description`, `event`, `input`, `isCompleted`, `name`, `nodeId`, `output`, `runAfter`, `type` |
| VALUE_HANDLE | 11 | `actionType`, `caption`, `description`, `input`, `isCompleted`, `items`, `name`, `nodeId`, `output`, `runAfter`, `type` |