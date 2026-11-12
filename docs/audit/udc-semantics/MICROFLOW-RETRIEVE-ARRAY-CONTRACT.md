# RETRIEVE_ARRAY（查询多条数据）节点契约

取证：前端 addNode → 每种查询方式逐个切换 + 点确认走校验 → 回读 dataSchema。
工具：`components/udc/microflow/live/`（cdp/env/ui）。证据：`scratch/array-evidence/`。
与 RETRIEVE（查询单条）的差异逐条标注；未闭环项明确标 UNVERIFIED，不冒充完成。

## 1. 默认必填（addNode 后默认态直接点确认得到）

```
structure      请输入选择实体
pageInfo       请输入分页数据
variableTitle  请输入节点出参名称
```

出参名字段是 **`variableTitle`**（RETRIEVE 是 `title`）。

## 2. 查询方式 4 种与字段联动

radio：`条件查询 CONDITION` / `ID集合查询 IDS` / `查询总数 COUNT` / `其他聚合查询 OTHERS`。

| 查询方式 | 出现的字段（除查询方式/选择应用/选择实体/节点出参名称外） | 专属必填 |
|---|---|---|
| CONDITION | 筛选条件、排序规则、分页查询、分页数据/最多获取条数 | — |
| COUNT | 筛选条件（**排序/分页/最多条数全部消失**） | — |
| OTHERS | **聚合方法、计算字段**、筛选条件 | `aggFunction`、`countAttrs` |
| IDS | **选择该记录的ID集合**（**筛选条件也消失**） | `value` |

**切换查询方式会清空 `structure`（选择实体）**，必须重选，否则提交报 `structure:请输入选择实体`。

## 3. 分页查询（仅 CONDITION）

- `分页查询=是` → 出现 **分页数据**（tree-select，必填 `pageInfo`）
- `分页查询=否` → 分页数据消失，改出现 **最多获取条数**（数字输入）

后端对应：
```json
{"pageSearch": "false", "size": 100}
```
- `pageSearch` 是**字符串** `"true"/"false"`，不是布尔
- `size` = 最多获取条数
- 分页=是 时 `pageInfo` 为分页对象参数（见 §6 依赖项）

抽屉文案提示：平台限制单次查询最大 999 条。

## 4. 后端结构（已回读确认）

CONDITION 叶子（分页=否 + size=100）：
```json
{"actionType":"RETRIEVE_ARRAY","fetchType":"CONDITION","selectType":"DTO","scope":"ARRAY",
 "variableTitle":"查询列表","size":100,"pageSearch":"false","sortParams":[],
 "output":{"id":"<Dto全名>","javaType":"<Dto全名>","dataType":"DTO","type":"ARRAY",
   "desc":"查询列表","dtoType":"MASTER_ENTITY","udcApp":true,
   "appName":"<appName>","name":"_RETRIEVE_ARRAY_xxxxxx"},
 "structure":{...同 RETRIEVE...}}
```
**`scope="ARRAY"`、`output.type="ARRAY"`**（RETRIEVE 是 OBJECT/OBJECT）。

顶层 22 键：`actionType, aggFunction, app, caption, condition, countAttrs, description,
fetchType, input, isCompleted, methodLegal, name, nodeId, output, pageSearch, runAfter,
scope, selectType, size, sortParams, structure, type, variableTitle`

COUNT：
```json
{"fetchType":"COUNT","scope":"ARRAY",
 "output":{"type":"OBJECT","dataType":"INTEGER"}}
```
**计数结果 output 变 `OBJECT` + `INTEGER`**，不再是 DTO/ARRAY。

## 5. OTHERS：4 种聚合方法 × 计算字段 × output 类型

聚合方法下拉只有 4 项：`求和 SUM` / `求平均值 AVG` / `求最大值 MAX` / `求最小值 MIN`。

**计算字段可选范围随聚合方法变化（联动，实测）**：

| 聚合方法 | 可选计算字段类型 | 本环境实测可选数 |
|---|---|---|
| 未选方法 | 全部类型（日期/实体/文本/数值/枚举） | 10 |
| SUM / AVG | **仅数值**（长整数/整数/小数） | 3 |
| MAX / MIN | **数值 + 日期时间** | 6 |

**output 类型（已逐个回读）**：

| aggFunction | output.dataType | output.javaType |
|---|---|---|
| SUM | 随字段（BIGINTEGER） | java.lang.Long |
| **AVG** | **恒 DECIMAL**（即使字段是长整数） | **java.math.BigDecimal** |
| MAX | 随字段（BIGINTEGER） | java.lang.Long |
| MIN | 随字段（BIGINTEGER） | java.lang.Long |

`countAttrs` 是**数组**，每项：
```json
{"id":"<Dto>.<field>","fullName":"<Dto>.<field>","name":"<field>",
 "javaType":"...","dataType":"...","type":"OBJECT","desc":"<字段中文>",
 "relationApp":"<appName>","refApp":"<appName>","multiSelect":false,
 "dtoType":"CUSTOM","label":"<字段中文> [<类型中文>]"}
```
`scope` 节点级仍 `ARRAY`，`output.type` 为 `OBJECT`。

## 6. 前置参数形态（已建真实前置节点并回读）

**CONDITION 分页=是**：
```json
{"pageSearch":"true","size":null,
 "pageInfo":{"type":"SelectParam","selectParam":{
   "id":"com.seeyon.boot.transport.PageInfo","javaType":"com.seeyon.boot.transport.PageInfo",
   "dataType":"DTO","type":"OBJECT","outputName":"<分页变量输出名>",
   "nodeInfo":{"nodeId":"<CREATE_VARIABLE节点>","actionType":"CREATE_VARIABLE"}}}}
```
前置：`CREATE_VARIABLE paramType=OTHER / otherType=SYSTEM_PAGE_INFO`，
output.javaType=`com.seeyon.boot.transport.PageInfo`。

**IDS**：
```json
{"fetchType":"IDS","pageSearch":null,"pageInfo":null,"size":null,"scope":"ARRAY",
 "value":{"type":"SelectParam","selectParam":{
   "javaType":"java.lang.Long","dataType":"BIGINTEGER","type":"ARRAY",
   "outputName":"<列表输出名>","position":"parent",
   "nodeInfo":{"nodeId":"<CREATE_LIST节点>","actionType":"CREATE_LIST"}}}}
```
前置：`CREATE_LIST BASIC / dataType=BIGINTEGER`，output.type=ARRAY。
分页/IDS 下拉为空表示流程里没有对应类型参数，补前置后可选，不是平台不支持。

## 7. 排序规则 / 筛选条件（LIVE PASS，已回读）

排序 UI 与 RETRIEVE 相同：添加规则 → 字段 + 升序/降序。
实测后端：
```json
"sortParams":[{"sortType":"DESC","attrType":{...字段完整属性含md5...}}]
```

筛选弹窗标题「筛选条件」（RETRIEVE 为「过滤条件」）。实测 `ID = 123` 后端：
```json
"condition":[{"type":"GROUP","uuid":"...","conditions":[{
  "type":"CONDITION","leftParam":{"id":"<Dto>.id","field":"id","dataType":"BIGINTEGER",...},
  "operator":{"value":"EQ","desc":"="},
  "rightParams":[{"type":"CONSTANT","value":123,"desc":123}],
  "logicalOperator":"AND"}]}]
```

### ★ 确定按钮自动保存的真实条件（前端源码证实）

通用 NodeConfig 的确定 `Y`：先跑动态控件 validators → `form.validateFields()` →
上层 `onSubmit(values)`。上层 `J` 更新 store 后，**只有 `configChanged(V)=true` 才调用
`saveMicroflowSchema({stateType:"DRAFT"})`**，否则只更新 store、不发 UpdatePost。

所以正确操作：填完业务后通过真实 UI 改动任一普通字段（如出参名），再点确定。
实测接口：`FindCustomDtoPost → UpdatePost → FindByIdGet → Search → ...`，
后端 sort/condition 均落库。**只改某些自定义控件可能不置 configChanged，不能据此判断保存失败。**

抽屉空壳判据仍是 `items` 非空而不是标题，用 `ui.ensure_node_drawer`。
本节点 forms=2，直接 `Form.onFinish` 可能命中内层 form，返回 ok 也不代表保存。

## 8. 一致性检查

页面点「检查」→ `udcApplicationDoDetectionPost` + `udcApplicationSearchDetectionPost`。
本节点完成后实测：**ERROR=0，WARN=5**；警告为未保存提示、循环中服务调用提示、
其他模块生单/选项集提示，不是本节点结构错误。

## 9. 回读方式的坑

本机 `urllib + CDP cookie` 回读可能 403（cookie 只取到少数、认证 cookie 不全），
**页面内 fetch 自动带会话更可靠**；会话整体失效时页面内同样 403（nginx HTML）。
`dataSchema.nodes` 只列顶层，目标节点可能嵌在 `conditions[].nodes`，必须递归回读。
接口 403、GraphQL 语法错误、节点字段为空要分开判定，不能混为"未保存"。
