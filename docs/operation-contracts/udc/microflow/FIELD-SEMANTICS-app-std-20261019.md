# FIELD-SEMANTICS｜标准域 ACTIVITY 字段语义（P2 · D157 返工）

> ℹ️ **同批三件之一（P2 · D157 返工）**：本文件 = 标准域 ACTIVITY。另两件：
> `FIELD-SEMANTICS-ctl-frontend-20261019.md`（CONTROL 3 种 + 前端域分层）、
> `FIELD-SEMANTICS-final-20261019.md`（type=2 VACUUM + 组装映射 + 落点互证 = P2 收官）。
> 三件共用同一数据快照戳 `MAX(update_time)=2026-10-17 15:41:03`。

> `datamigration9000000000000000001` / test2 ｜ 输入：`field_keys_by_actionType` + NODE-CENSUS-app §五 + `NODE_REQUIRED_FIELDS`
> 证据：**LIVE**（DB 只读逐节点）｜约束侧 **STATIC**（字面量 + `required_fields()`）｜0 `/service`、0 写库
> **快照戳 MAX(update_time)=2026-10-17 15:41:03**

## 一、范围

`type IN (0,3)` **20 条**流程（47 条中）／ **56 个** ACTIVITY 实例 ／ 实测 **18 种**；`NODE_REQUIRED_FIELDS` 21 键，16 种有声明（含 2 种 `()`），`CHANGE_BATCH_ENTITY`、`CREATE_MAP` 未收录。
★ 18≠20 不矛盾：20 全库口径、18 本应用实测。**「缺」= 缺该字段的实例数（逐实例）**，非「类内是否出现过该键」。

## 二、差集总表（逐实例）

| actionType | 实例 | 缺实例 | 定性 |
|---|---|---|---|
| CALL_APP_SERVICE | 2 | 0 | 一致 |
| CHANGE_BATCH_ENTITY | 2 | — | 缺口① |
| CHANGE_ENTITY | 2 | 2/2 | 过宽② |
| CHANGE_LIST | 2 | 0 | 一致 |
| CHANGE_VARIABLE | 4 | 0 | 一致 |
| CONVERT_DATA | 2 | 0 | 一致 |
| CREATE_ENTITY | 2 | 0 | 一致（`attrs`） |
| CREATE_LIST | 2 | 0 | 一致 |
| CREATE_MAP | 1 | — | 缺口① |
| CREATE_VARIABLE | 4 | 4/4 | 过宽③ |
| DATA_MAPPING | 6 | 0 | 一致（④） |
| DELETE_ENTITY | 3 | **2/3** | 过宽② |
| LIST_OPERATION | 2 | 2/2 | 过宽⑤ |
| MAP_OPERATION | 2 | 2/2 | 过宽⑥ |
| PUBLISH_BUSINESS_EVENT | 2 | 0 | 一致 |
| RETRIEVE | 7 | 0 | 一致（⑥） |
| RETRIEVE_ARRAY | 6 | **2/6** | 条件缺失⑦ |
| SUB_MICROFLOW | 5 | 5/5 | 过宽② |

约束侧必填集见 §三 各类（均引自 `required_fields()` 实际返回值，非注释）。

**汇总：完全匹配 9 种 ／ 差集非空 7 种 ／ 未收录 2 种 ＝ 18 种**（差集 7 = 过宽 6 + 条件缺失 1）。
→ **无脏数据**：`validate_node_fields()` 共报 23 条，逐条可归因。

## 三、逐类定性

**① 契约缺口**：`CHANGE_BATCH_ENTITY`/`CREATE_MAP` 未收录但各有实例 → 欠声明。

**② 模式选择器写成无条件必填**（`CHANGE_ENTITY`/`SUB_MICROFLOW`/`DELETE_ENTITY`）
`MAPPING_TYPES=("attrs","value","mapping")`(:179)。`CHANGE_ENTITY_x10` 无键但有 `attrs[]`+`selectParam`=attrs(2/2)；`SUB_MICROFLOW_x15` 无键但有 `mfService`+`value`=value(5/5)；`DELETE_ENTITY` 仅 `ccc333="CONDITION"`，`x13`/`n13`=null(2/3)。
→ 只在**无法从结构推断**时落地；5/5、2/2 一致=稳定模式。DELETE_ENTITY 同型不同机制：`deleteType` 无结构替代键，属「枚举值非空才需要」。
→ **③⑤ 同类**：`CREATE_VARIABLE` 的 metaDataType/otherType 依附 `paramType`(4/4)；`LIST_OPERATION.indexValue` 依附 `operationType`(2/2)。

**④ DATA_MAPPING → 取值层级，非缺失（P4）**：`mappingRule` 是 **dict 不是 JSON 字符串**（6/6），键含 `{uuid,targetType,mappingRows,…}`；`validate` 判据即其 `.targetType/.mappingRows` → 6/6 全过 → **完全匹配**。★ 勿 `json.loads`。

**⑥ 同语义两结局（P5）**：`required_fields()` 对 RETRIEVE 判 `nullHandling=="TERMINATION"` 才加 `nullPromptMessage` → app 7/7 CONTINUE → 不报 → **完全匹配 ✅**；`MAP_OPERATION.nullPromptMessage` 却硬写在 `NODE_REQUIRED_FIELDS` → app 2/2 → 报 2 条 → 过宽。全库：CONTINUE 1618 全无 prompt／TERMINATION 219 全带。
→ ★ **枚举是 `TERMINATION` 不是 `STOP`**（源码 L35 注释写 STOP 是注释错，代码用 TERMINATION）。可复用判据：同语义一处实现一处漏。

**⑦ RETRIEVE_ARRAY → 缺 pageSearch 维度（条件必填被写成无条件）**
两维（`fetchType` × `pageSearch`）：
- `CONDITION`×`'N'`(3)／`'false'`(1) → size=100、无 pageInfo、aggFunction=null → **size 必填 ✅**
- `CONDITION`×`'true'`(2) → size=null、aggFunction=null；`_x3` 的 pageInfo=None、`_n3` 有内容 → **size 不该必填**

★ 源码实测：`required_fields()` 只按 fetchType 过滤 size/aggFunction，**无 pageSearch 维度**；`pageSearch` 仅在 **L61 注释**出现，未实现。
→ ★ **constraints 对 `pageSearch=true` 会误报缺 size —— 源码缺口，非数据问题。**
→ ★ **下一个人跑 `validate_node_fields()` 会得 2 条假失败（`_x3`、`_n3` 缺 size），先减掉再统计**；本切片不改 `required_fields()`。
→ ★ `pageSearch` 三写法（布尔字符串化、大小写不一），**统计须先归一**，否则 `'false'` 被当真值。`aggFunction` **0/6**（非 1/6）。

## 四、三条建议

1. **补欠声明**：`CHANGE_BATCH_ENTITY`、`CREATE_MAP` 进 `NODE_REQUIRED_FIELDS`。
2. **无条件→条件必填**：`mappingType`、`metaDataType`/`otherType`、`indexValue`、`MAP_OPERATION.nullPromptMessage`（照 RETRIEVE 分支改）。
3. **补 pageSearch 分支**：`size` 仅 `pageSearch≠true` 必填；判据是「size 或 pageInfo 至少其一」。

## 五、抽样证据

`WHERE app_id='…' AND type IN (0,3)` → 递归 ACTIVITY → 逐实例逐键判空。

```
DELETE_ENTITY_x13       -3790333238868911627  xzhStdReal31046  deleteType=null
DELETE_ENTITY_n13       -1014184770817921434  xzhFinalAllNodes deleteType=null
RETRIEVE_ARRAY_x3       -3790333238868911627  xzhStdReal31046  pageSearch='true' size=null pageInfo=None
RETRIEVE_ARRAY_n3       -1014184770817921434  xzhFinalAllNodes pageSearch='true' size=null pageInfo=有内容
DATA_MAPPING_n8         -1014184770817921434  xzhFinalAllNodes mappingRule=dict
CHANGE_BATCH_ENTITY_x11 -3790333238868911627  xzhStdReal31046
CREATE_MAP_n6a          -1014184770817921434  xzhFinalAllNodes
```

## 六、未覆盖

- type=1 前端域 27 种（另一套枚举）、type=2 的 3 种；取值级语义仅分支级核对
- 21 种面板节点类型（P0 独立分支）；`required_fields()` 的 pageSearch 缺口仅记录未修
