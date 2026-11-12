# 节点字段形态契约（LIVE 实证）

来源：2026-10-29 逐节点抽屉实测 + 前端 bundle `src_redux_store_ts.14dc061e.js`。
本文件只记 **checkSchema 通过但 UI 仍报错/空着** 的那类缺陷——这类 checkSchema
完全不拦，只有打开抽屉才看得见，是生成器最容易漏的一层。

## 判据分层

| 层 | 谁拦 | 拦什么 |
|---|---|---|
| checkSchema/update | 后端 | 字段**是否存在**（PROPERTY_IS_REQUIRED） |
| 前端抽屉 | 前端表单 | 字段**形态是否合法**（能否回显） |
| checkSchema | 不拦 | 引用**是否指向真实节点**（悬空引用照样发布成功） |

所以「checkSchema errors=0」**不等于**节点可用。

---

## 1. MAP_OPERATION — `basic` 必须是对象

```js
// 前端定义（bundle）
{key:"basic", label:"数据类型", type:"treeListSelector",
 defaultval:{key:"STRING", dataType:"STRING"},
 dataListInfo:[{label:"文本",value:"STRING",key:"STRING",dataType:"STRING"}, ...]}
```

- **错误形态**：`"basic": "STRING"`
  - 抽屉「* 数据类型」显示空占位「选择数据类型」
  - 前端 `dataSchema()` 执行 `structure:{...basic}` 时把字符串展开成字符下标：
    `{"0":"S","1":"T","2":"R","3":"I","4":"N","5":"G","fullName":""}` ← 垃圾数据
- **正确形态**：
  ```json
  "basic": {"label":"文本","value":"STRING","key":"STRING","dataType":"STRING"},
  "structure": {"label":"文本","value":"STRING","key":"STRING","dataType":"STRING",
                "fullName":"java.lang.String"}
  ```
- `structure` 由 `basic` 推导：`{...basic, fullName: javaType}`
- GET 必填：`selectMap / operationType / theKey / basic / arrayOrObject / loop nullPromptMessage`
- `entries` 只对 `PUT` 需要；GET 模式必须**删掉**（留 `entries:[]` 会被当 PUT 处理）
- `paramType` 取 `BASIC | ENTITY_OBJECT | DEFAULT_OBJECT | ENUM | MAP`
- 抽屉字段 → 字段名：选择映射=`selectMap`、操作类型=`operationType`、
  该值的映射键=`theKey`、映射值类型=`paramType`、数据类型=`basic`、
  是否列表=`arrayOrObject`（`OBJECT`=单条 / `ARRAY`=列表）、节点出参名称=`title`

## 2. CREATE_LIST — `value` 是默认值

前端 `dataSchema()`：`"BASIC"` 分支返回 `{paramType, app, title, dataType, value}`。
`value` 走 `valueComponent`，形态同其它值槽：`{type:"Simple", simple, desc}`。
母版 `CREATE_LIST_U7yqmc` 无 `value` 也能发布（默认值可选），
但需要「列表有初值」时必须显式给。

## 3. END_NODE — 必须在顶层 `endNode`，绝不能进 `nodes`

前端保存逻辑（bundle）：

```js
o.trigger = flowNodes[TRIGGER节点]
u(flowFrame.slice(1), o.nodes)              // nodes 只放 flowFrame 里除 trigger 外的
o.endNode = {...flowNodes[END节点]}          // END 单独抽出
```

权威结构（`fixtures/microflow/node_templates/END.json`）：

```json
{"id":"", "name":null, "type":"END", "actionType":"END_NODE",
 "nodeId":"MFEndNode", "caption":"结束", "description":null,
 "input":null, "output":{...}, "outPutDesc":null,
 "mappingType":"BASIC", "paramType":"BASIC", "basic":"STRING",
 "isArray":false, "desc":"出参", "value":{...}, "attrs":[], "isCompleted":true}
```

- 漏 `type`/`actionType` → 画布渲染成 **「节点开发中...」** 灰卡片
- `endNode={}` 或 END 出现在 `nodes` 数组 → 同样渲染成占位符
- 正常渲染的 DOM：`<div id="MFEndNode" class="end-node"><span class="end-title">结束</span></div>`

## 4. FOR_EACH — `foreach` 与 `selectParam` 并存

前端创建模板：

```js
{nodeId:"ForEach_"+nanoid(6), type:"FOR_EACH", caption:"列表循环",
 description:"", runAfter:null, nodes:[],
 foreach:{sourceItemes:[]}, isCompleted:false}
```

表单项（`settings.items`）：`selectParam`（选择列表，`filter: type=='ARRAY'`，必填）
+ `targetName`（循环对象名称，必填）→ 见 `NODE_REQUIRED_FIELDS["FOR_EACH"]`。

- `foreach.sourceItemes` 放被遍历列表的引用（前端容器用）
- `selectParam` 才是保存校验认的字段
- `selectParam` 若是实体列表必须带 `dtoType`（否则 checkSchema 报
  `PROPERTY_IS_REQUIRED ...selectParam.dtoType`）
- 计数循环 `FOR` 的 `foreach` 为 `null`；列表循环 `FOR_EACH` 有 `foreach` 对象
- 无 `forStart/forEnd/forStep/operator`（那是 FOR 的）
- 画布卡片文本是 **「循环列表：」**（不是「列表循环」），
  按文本匹配节点时别用错方向

## 5. CHANGE_LIST — `action` 必填，`dataSource` 不能留模板值

保存校验必填：`("action", "selectParam")`。

模板 `CHANGE_LIST.json` 里的 `dataSource.name` 指向模板自己的兄弟节点
（如 `_CREATE_VARIABLE_3eLmAb`）。直接复制不改 → 前端报
**「引用的参数 vText 已失效，请重新配置！」** 并给节点加红框。

必须重写 `dataSource` 指向本流程真实节点。

## 6. CREATE_ENTITY — `value` 应为 null

母版 `CREATE_ENTITY_UuKpNp` 的 `value` 是 `null`，赋值走 `attrs`。
写成 `value:{type:"SelectParam", selectParam:{outputName:"_<relationEntityId>"}}`
是错的：`_<relationEntityId>` 是实体关系 id 不是节点输出名，
闸门会判悬空引用。

## 7. 表达式 tokens 顺序

必须按书写顺序 `[左值, 算子, 右值]`。写成 `[OPERATOR, 1, 1]` 前端渲染成 `"1 1"`，
报红字 **「变量: 1 后只能拼接操作符」**。

`executableExpr` 前缀（`93gDaq3/nXB1+...=`）是服务端 `/expression/transform`
的产物，**不能手拼**。正确流程：`POST /expression/check` → `POST /expression/transform`，
取返回的 `designData` + `runtimeData`。

---

## 闸门对照（已实现于 components/udc/microflow/gates.py）

| 闸门 | 拦什么 | 误报基线 |
|---|---|---|
| G9 MAP_OPERATION | `basic` 非对象 / structure 有字符下标 / nullPromptMessage 空 | 母版 0 |
| G9 CREATE_ENTITY | `value` SelectParam 指向不存在 output 且无 nodeInfo | 母版 0 |
| G9 END 位置 | END_NODE 出现在 nodes 数组 | 母版 0 |
| G10 引用泄漏 | SelectParam.nodeInfo.nodeId 不在本流程节点表 | 母版 0 |
| G11 endNode | 顶层 endNode 空 / type / actionType / caption 缺 | 母版 0 |

误报基线用 `fixtures/microflow/backup/xzhAllNodesV16.schema.json` 回归：
必须 **0 问题**，否则闸门过严会挡住真实业务流。
