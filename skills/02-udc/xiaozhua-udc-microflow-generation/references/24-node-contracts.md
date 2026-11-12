# UDC 微流程 24 类节点真实契约（台账）

本文件只做**台账**：节点清单、actionType、nodeId 前缀、必填项、默认模板形状。
**逐个节点的操作步骤、真实表单值（condition/structure/output）、CDP 坑**见 `references/frontend-node-authoring-cdp.md`，不要在本文件重复。

## 绝对铁律

1. **节点不是后端造的，是前端 addNode 造的。** 手拼节点 JSON 一定是错的。
2. 所有节点刚添加时：`output: null`、`isCompleted: false`，`caption` 由前端自动编号（`创建变量(1)`）。
3. **添加节点不产生任何接口调用**（实测 24 个节点全部 `接口=0`），是纯前端 redux 操作。
4. 点「确定」确认配置后才会调 `udcMicroflowUpdatePost` → `FindByIdGet` → `Search` → `DisableNodePost`+`FindCustomDtoPost` → `GroupSelectByTypePost`。

## 添加节点 payload（真实）

```json
{"type":"udc-microflow-edit/addNode",
 "payload":{"currentNodeId":"MFStartNode","addType":"OUTER",
   "newNodeTemplate":{"nodeId":"CREATE_VARIABLE_DI3Lpg","name":"","type":"ACTIVITY",
     "caption":"创建变量(1)","description":null,"runAfter":null,
     "input":null,"output":null,"isCompleted":false,"actionType":"CREATE_VARIABLE"}}}
```

回填日志：`回填 nodeConfig {name:'', description:null, input:null, output:null, isCompleted:false}`。

## 24 类节点对照表

| # | 节点 | actionType | nodeId 前缀 | 抽屉必填 |
|---|------|-----------|------------|---------|
| 1 | 分支 | *(无 actionType，type=BRANCH)* | `BRANCH_` | 画布内联，无抽屉 |
| 2 | 列表循环 | *(无)* `type=FOR_EACH` | `ForEach_` | 选择列表、循环对象名称 |
| 3 | 计数循环 | *(无)* `type=FOR` | `For_` | 循环起始值、循环终止值、步长、循环变量名称 |
| 4 | 自定义错误 | *(无)* `type=CUSTOM_ERROR` | `CUSTOM_ERROR_` | 填写错误 |
| 5 | 创建变量 | `CREATE_VARIABLE` | `CREATE_VARIABLE_` | 变量类型、数据类型、节点出参名称 |
| 6 | 修改变量 | `CHANGE_VARIABLE` | `CHANGE_VARIABLE_` | 变量 |
| 7 | 创建映射组 | `CREATE_MAP` | `CREATE_MAP_` | 节点出参名称 |
| 8 | 映射操作 | `MAP_OPERATION` | `MAP_OPERATION_` | 选择映射、操作类型、该值的映射键、映射值类型、数据类型、是否列表、节点出参名称、提示内容 |
| 9 | 创建列表 | `CREATE_LIST` | `CREATE_LIST_` | 列表类型、数据类型、节点出参名称 |
| 10 | 修改列表 | `CHANGE_LIST` | `CHANGE_LIST_` | 选择列表、操作类型、列表/对象 |
| 11 | 列表操作 | `LIST_OPERATION` | `LIST_OPERATION_` | 选择列表、操作类型、操作数据、节点出参名称 |
| 12 | 查询单条数据 | `RETRIEVE` | `RETRIEVE_` | 选择应用、选择实体、节点出参名称、提示内容 |
| 13 | 查询多条数据 | `RETRIEVE_ARRAY` | `RETRIEVE_ARRAY_` | 选择应用、选择实体、分页数据、节点出参名称 |
| 14 | 插入数据 | `CREATE_ENTITY` | `CREATE_ENTITY_` | 选择应用、选择实体、赋值方式、节点出参名称 |
| 15 | 批量插入数据 | `CREATE_BATCH_ENTITY` | `CREATE_BATCH_ENTITY_` | 选择插入的记录列表、节点出参名称 |
| 16 | 更新数据 | `CHANGE_ENTITY` | `CHANGE_ENTITY_` | 选择更新的数据、节点出参名称 |
| 17 | 批量更新数据 | `CHANGE_BATCH_ENTITY` | `CHANGE_BATCH_ENTITY_` | 选择更新的记录列表、节点出参名称 |
| 18 | 删除数据 | `DELETE_ENTITY` | `DELETE_ENTITY_` | 删除规则、选择节点、节点出参名称 |
| 19 | 自定义服务 | `CALL_APP_SERVICE` | `CALL_APP_SERVICE_` | 选择应用、选择服务、节点出参名称 |
| 20 | 事件投递 | `PUBLISH_BUSINESS_EVENT` | `PUBLISH_BUSINESS_EVENT_` | 选择应用、可投递的事件 |
| 21 | 子微流程 | `SUB_MICROFLOW` | `SUB_MICROFLOW_` | 选择微流程服务 |
| 22 | 执行生单规则 | `CALL_DATA_FLOW` | `CALL_DATA_FLOW_` | 来源实体、生单规则、数据来源方式、过滤条件、节点出参名称 |
| 23 | 类型转换 | `CONVERT_DATA` | `CONVERT_DATA_` | 变量类型、选择数据、节点出参名称 |
| 24 | 数据转换 | `DATA_MAPPING` | `DATA_MAPPING_` | 来源数据、目标数据对象类型、目标数据对象所属应用、实体对象、映射关系、节点出参名称 |

**抽屉只有这 24 个。** `BREAK(跳出循环)` 不在抽屉里（`noCompleted:true`，只在循环内部）；`CONNECTOR(连接器)` 在 store 的 nodeTypeList 里但不在抽屉里。

## 模板 / 构造器 覆盖台账

`fixtures/microflow/node_templates/` 共 26 个模板（24 类 + `PUBLISH_BUSINESS_EVENT` 之外的 `CUSTOM_ERROR`/`CALL_DATA_FLOW`，以及 `FOR_EACH`/`END`）。`components/construction/` 对 24 类均已有构造器。

| 缺口 | 现状 | 处置 |
|---|---|---|
| `END_NODE` 模板 | 已补，取自生产母版顶层 `endNode` | 直接用 |
| `FOR_EACH` 模板 | 已补，取自一条 LIVE 发布流程 | 直接用；仍要 `pop` 掉计数循环四字段 |
| `CONDITION` | 无独立模板/构造器 | 它是 BRANCH 的 `conditions[]` 子项，按 BRANCH 构造器的分支传 |
| `CONNECTOR` | 无模板、无构造器、未验证 | 动它之前先在抽屉里探出表单与必填，落 facts 再写构造器 |
| `PUBLISH_BUSINESS_EVENT` 字段映射 | 有构造器，但实体→事件 DTO 的字段映射未跑通 | 要它之前先做一次完整映射验证 |

**台账里的「有构造器」只代表结构能拼出来，不代表语义对**——构造器可能漏字段或写出前端不认的形态。用之前把产物过 `gates.py`（尤其 G9 字段形态闸门），发现漏就改构造器本身，不要在生成脚本里手改 dict。

## 各节点 radio 枚举（变量/对象类型）

- 创建变量 `paramType`: `BASIC` / `ENTITY_OBJECT` / `DEFAULT_OBJECT` / `ENUM` / `METADATA` / `MESSAGE` / `OTHER`
- 创建列表 `paramType`: `BASIC` / `ENTITY_OBJECT` / `DEFAULT_OBJECT` / `ENUM` / `MESSAGE`（无 METADATA/OTHER）
- 映射操作 `paramType`: `BASIC` / `ENTITY_OBJECT` / `DEFAULT_OBJECT` / `ENUM` / `MAP`
- 查询单条 `查询方式`: `CONDITION` / `IDS`
- 查询多条 `查询方式`: `CONDITION` / `IDS` / `COUNT` / `OTHERS`
- 查询单条 `未查到数据时`: `TERMINATION`（终止+提示）/ `CONTINUE`（继续，自行判空）
- 查询单条 `查询聚合对象`: `false` 关闭 / `true` 开启
- 插入数据 `赋值方式`: `attrs` / `value`
- 删除数据 `删除规则`: `SELECT_PARAM` / `CONDITION` / `IDS`
- 事件投递 `事件类型`: `AMONG_APP`（应用间）/ `IN_APP`（应用内）
- 数据转换 `目标数据对象类型`: `ENTITY` / `DTO`

## 特殊节点默认结构

### 分支 BRANCH（唯一有嵌套结构的节点）

```json
{"nodeId":"BRANCH_xxx","name":"userBranch","type":"BRANCH","caption":"分支(1)",
 "description":"","runAfter":null,
 "conditions":[
   {"nodeId":"CONDITION_xxx","name":"ifBranch","type":"CONDITION",
    "caption":"符合条件即进入该分支","description":"","runAfter":null,
    "expression":{"title":"","schema":null},"nodes":[],"isCompleted":false},
   {"nodeId":"CONDITION_yyy","name":"elseBranch","type":"CONDITION",
    "caption":"不符合条件即进入该分支","description":"","runAfter":null,
    "expression":null,"nodes":[]}]}
```

注意分支**没有 actionType 字段**，靠 `type:BRANCH` 区分。子节点挂在 `conditions[].nodes`。

### 循环节点（列表循环/计数循环）

```json
{"nodeId":"ForEach_xxx","type":"FOR_EACH","caption":"列表循环(1)","description":"",
 "runAfter":null,"nodes":[],"foreach":{"sourceItemes":[]},"isCompleted":false}
```

`FOR` 与 `FOR_EACH` 都有 `foreach:{sourceItemes:[]}`，都没有 actionType。循环体挂在 `nodes`。

### 其余 20 个 ACTIVITY 节点统一形状

```json
{"nodeId":"<ACTIONTYPE>_<6位>","name":"","type":"ACTIVITY","caption":"<中文名>(N)",
 "description":null,"runAfter":null,"input":null,"output":null,
 "isCompleted":false,"actionType":"<ACTIONTYPE>"}
```

例外：自定义错误 `type:"CUSTOM_ERROR"`（不是 ACTIVITY）、**没有 actionType 字段**。

## 确认后的真实 node（以创建变量为例）

```json
{"paramType":"BASIC","title":"变量_1","dataType":"STRING",
 "value":{"type":"Simple","simple":"测试值","desc":"测试值"},
 "nodeId":"CREATE_VARIABLE_P3SPbN","actionType":"CREATE_VARIABLE",
 "caption":"创建变量(1)","description":null,"type":"ACTIVITY",
 "output":{"id":"","javaType":"java.lang.String","dataType":"STRING",
   "type":"OBJECT","desc":"变量_1","dtoType":"",
   "name":"_CREATE_VARIABLE_d3ZScR"},
 "isCompleted":true}
```

关键：
- 出参名的表单字段叫 **`title`**，但 `output.name` 是前端另生成的 `_CREATE_VARIABLE_<nanoid>`（**不是 title**）。
- `output` 由前端根据 paramType/dataType 自动生成，后端不接受手写。
- `isCompleted:true` 才是配置完成。

## 前端表单校验（点确定时的 unhandledrejection）

未通过时抛出：
```json
{"values":{"paramType":"BASIC","dataType":"STRING","value":null,"title":"变量_1"},
 "errorFields":[],"outOfDate":true}
```

- `errorFields:[]` 表示没有字段级校验失败 → 缺的是 `value`（必填项在别的层校验）。
- `outOfDate:true` 是 antd 校验竞态。**在输入框内按 Enter 代替点「确定」可绕过**，走原生 form submit 路径。
- 提交失败会**回滚节点**（从 flowFrame 消失），要从头再来。

## CDP 操作要点

见 `references/frontend-node-authoring-cdp.md` 第 5 节（含 `document.hidden` 导致浮层停帧、跨进程失焦关下拉、antd form 实例取真实字段等）。

## 采集方法

驱动用 CDP：`Input.dispatchMouseEvent` 点画布 `+`，`span.add-node-title` 选节点，读 `appReduxStore` 取 `flowFrame`/`flowNodes`，`Network` 域抓接口，`Runtime` 装 console `unhandledrejection` 钩子收前端校验。每抓完一个节点 `Page.reload` 复位，避免画布撑出视口。

驱动依赖 `websockets`，用装有该包的解释器跑。
