# 实体规则域（微流程）—— 写入链 LIVE

> 状态：**create / checkSchema / update / findById / list / delete 全 LIVE**
> 证据：test2 实测（2026-10-23），实体 `ysFull6956`，规则 id `1026598281682062368`
> 工具：`tools/core/entity/write_entity_rule.py`

## 1. 契约面

| 动作 | 方法 | 路径 | body / 参数 | 返回 |
|---|---|---|---|---|
| 列表 | GraphQL | `udcMicroflowSearchEntityRulePost` | `{pageInfo, params:{sourceId:<实体id>}}` | rows[] |
| 详情 | GET | `/service/udc/microflow/findById/{id}` | — | 完整 DTO（含 dataSchema） |
| 校验 | POST | `/service/udc/microflow/checkSchema` | 与 create 同 body | `{check, errors, errorMessage[]}` |
| 建 | POST | `/service/udc/microflow/create` | MicroFlowDto | `content = 新 id` |
| 改 | POST | `/service/udc/microflow/update` | MicroFlowDto（**须 findById 完整回读后改**） | `content = 1` |
| 删 | GraphQL | `udcMicroflowDeletePost` | `{appId, id}`（逐条，非数组） | BOOT_0000 |

## 2. ★ 最坑的一条：checkSchema 的 BOOT_0000 不可信

```
{checkSchema} 首版（expression 格式猜错）
  code=BOOT_0000  ← 平台成功码
  但 content = {"check": false, "errors": 1, "errorMessage":[{nodeId:"CONDITION_QMtiZD", ...}]}

{create}  ← 校验失败**不阻塞创建**
  code=BOOT_0000  content=<新id>
  库里确实多了一条规则，但条件节点是空的，页面打开看不到条件
```

⇒ 判据必须是 **`content.check == true` 且 `errors == 0`**，
   不是 `code == BOOT_0000`。这与「成功码不可信、判据是回读」是同一族纪律。

## 3. 条件表达式的真实形状

```jsonc
"expression": {
  "title": "小爪验收实体全量.整数字段 > 100 ",     // 展示用翻译
  "schema": "{\"designData\":{...},\"runtimeData\":{\"executableExpr\":\"...\"}}"
}
```

两个要点：

1. **`schema` 是 JSON 字符串，不是对象。** 传对象进去 checkSchema 直接不认。
2. `schema` 解开后是 `{designData, runtimeData}` —— **与表达式域
   `POST /service/udc/expression/transform` 的返回完全同构**。

⇒ 所以规则条件不需要另写一套表达式构造器：调 transform，
   把 `{designData, runtimeData}` 包成 `{"title": translation, "schema": dumps(...)}` 即可。

客户真实配置印证（`udc_microflow_info` 抽样，页面正常的规则）：
`expression.title` 为完整中文路径，`schema` 为字符串，内含 `designData.expressionTranslation`
`/resultTypeInfo=BOOLEAN/terminalType/context(OBJECT 树)/tokens`。

## 4. dataSchema 结构（开始→条件分支→结束）

```jsonc
{
  "id": "", "appId": "...", "sourceId": "<实体id>",
  "version": "0", "versionCode": 0,
  "type": "ENTITY_RULE", "triggerType": "MANUAL",
  "name": "ruleLZ762041", "description": "",
  "nodes": [{
    "nodeId": "BRANCH_xxx", "name": "userBranch", "type": "BRANCH",
    "caption": "BRANCH", "description": "BRANCH",
    "conditions": [
      {"nodeId":"CONDITION_ifxxx","name":"ifBranch","type":"CONDITION",
       "caption":"符合条件即进入该分支","expression":{...},"isCompleted":true,"nodes":[]},
      {"nodeId":"CONDITION_elxxx","name":"elseBranch","type":"CONDITION",
       "caption":"不符合条件即进入该分支","expression":null,"isCompleted":true,"nodes":[]}
    ]}],
  "input": {"dataType":"ENTITY","type":"OBJECT","name":"dto","id":"<实体id>"},
  "output": null, "trigger": {}, "sourceType": "PAGE", "caption": "..."
}
```

- `isCompleted` 不设 true，页面会显示条件未配置
- `elseBranch` 的 `expression` 恒为 `null`（默认分支无条件）
- `input.id` 必须是实体 id，`sourceType` 为 `PAGE`（实体规则也用它）

## 5. 三类规则的 groupType

| UI 类型 | 新建弹窗 radio 值 | groupType | 初始 state | 说明 |
|---|---|---|---|---|
| 校验 | `VALIDATE` | `DEFAULT_VALUE` | `RELEASE`（保存并提交后） | — |
| 计算 | `ASSIGN_VALUE` | `ASSIGN_VALUE` | `DRAFT` | 本工具默认建这类 |
| 页面默认值 | `DEFAULT_VALUE` | `ASSIGN_VALUE` | `DRAFT`（列表显示"计算"） | 与计算同 groupType，靠 schema 内容区分 |

列表 `groupType` **不能反推 UI 类型**（计算和页面默认值同值；且"页面默认值"列表里显示成"计算"）。
类型差异在 microflow schema 内部。radio 值与初始 state 来自 2026-10-23 UI 新建实测
（原记于 `rules-microflow.md`，已并入本节）。

## 6. 验证结论（可复算）

```
create    → id 1026598281682062368 / 小爪规则-生产验证
checkSchema → check=True errors=0
列表接口  → udcMicroflowSearchEntityRulePost 能查到（页面列表数据源）
回读      → expression.title = "小爪验收实体全量.整数字段 > 500"
            schema.designData.expressionTranslation 一致
            schema.runtimeData.executableExpr 带签名
```

## 7. 未做 / 待证

- **执行态**：规则 DRAFT 状态，未启用、未跑过运行时；`RELEASE` 需要走「保存并提交」
- **动作节点**（给字段赋值的 ASSIGN 节点）：本次只做条件分支，`conditions[].nodes` 仍为空
- 页面 UI：实体 tab 里的「规则」子 tab 在自动化里宽度为 0（被隐藏），
  **列表靠接口验证**，UI 渲染需人工点开确认

## 8. ★★ 更正（2026-10-23 用户截图）：token desc 必须带实体标题前缀

首版把条件写成 `desc: "整数字段"`（只有字段标题），结果页面「表达式设置」弹窗红字：

```
变量 整数字段 在上下文中不存在，请确认！
```

**而 `checkSchema` 返回 `check=True, errors=0`** —— 后端校验通过，页面照样报错。

正确形态（与 `schema_binding` 的「实体树 + 点路径」是同一条规则）：

```jsonc
tokens: [
  {"type":"VARIABLE", "paramId":"<字段id>",
   "value":"ysFull6956.f03int",                    // 实体 name . 字段 code
   "desc":"小爪验收实体全量.整数字段",              // ★ 实体标题 . 字段标题
   "g_l_index":"1"},
  {"type":"OPERATOR","value":">","desc":">"},
  {"type":"CONSTANT","value":"500","desc":"500"}
]
```

客户真实规则样本印证：`desc = "微流程.查询单条数据(1).投标报备申请_1 [投标报备申请].流程类型"`
—— 也是完整路径，不是裸字段名。

★ 我在表达式域（`f04bigint`）已经修过一次这个坑，在规则域又犯了一次。
现已用 `tests/udc/test_entity_rule_shape.py` 钉死。

## 9. 三个节点：结束节点必须显式写进 schema

画布上是「开始 → 条件分支 → 结束」。其中：

- **开始**：隐式，不出现在 dataSchema 里（实测客户规则样本 `startNode` 为 null 或不存在）
- **条件分支**：`nodes[0]`，`type=BRANCH`，`conditions=[ifBranch, elseBranch]`
- **结束**：顶层 `endNode` 字段

```jsonc
"endNode": {"id":"", "name":"", "type":"END", "actionType":"END_NODE",
            "nodeId":"MFEndNode", "caption":"结束", "description":"",
            "input":null, "output":null}
```

缺 `endNode` 时画布少「结束」一环。实测客户样本（`-9205305882361576511`、
`-9196582754851490168`）全都带这个字段。

节点还应带 `runAfter: null`（真实样本都有）。

## 10. 页面验收（2026-10-23，修复后）

```
URL  /udc/app-design/entity-rule/editor/<规则id>?appId=<appId>
页面  开始 → 条件分支（① 符合条件即进入该分支 / ② 不符合条件即进入该分支）→ 结束
红字  无
弹窗「表达式设置」显示：小爪验收实体全量.整数字段 > 500
```

## 11. 仍未做

- **动作节点**：if 分支里还没有「给字段赋值」的 ACTIVITY 节点，
  页面显示「从右侧面板选择要执行的动作」。这是下一步。
- 规则仍为 DRAFT，未启用。

## 12. ★★ 分支动作节点：实体规则用 ASSIGN_VALUE（设置值）

规则只有条件、两边都空 = 没意义。分支要挂动作节点，实体规则的「设置值」是：

```jsonc
{
  "nodeId": "ASSIGN_VALUE_<nanoid6>",
  "type": "ACTIVITY",            // ★ 不是 ASSIGN_VALUE
  "actionType": "ASSIGN_VALUE",  // ★ 不是 SET_VALUE
  "caption": "设置值", "runAfter": null,
  "input": null, "output": null, "isCompleted": true,
  "param": {
    "name": "f01text",
    "caption": "文本字段",        // ★ 必填，只给 desc 会报 param.caption 缺
    "path": [{"fieldId":"<字段id>", "entity":{"id":"<实体id>","appName":null}}],  // ★ 必须数组
    "id": "com.seeyon.<appName>.dto.<Entity>Dto.<field>",
    "dataType": "STRING", "javaType": "java.lang.String", ...
  },
  "value": {"type":"Expression","expression":{"schema":"<json>","title":"超限"},"desc":"超限"}
}
```

### 逐个试出来的必填序列（checkSchema 会一项项报缺）

| 写法 | 结果 |
|---|---|
| `type:"ASSIGN_VALUE"` | `[设置值]:无效的数据`（DATA_INVALID / PARSE） |
| `type:"ACTIVITY"` + `actionType:"ASSIGN_VALUE"` + 只有 `desc` | `param.caption` 缺 |
| 补 `caption`，`path` 给**字符串** | `param.path` 缺（给任何字符串都报缺） |
| 补 `path` 为**数组** | ✅ `check=True errors=0` |
| `type:"ACTIVITY"` + `actionType:"SET_VALUE"` | ⚠ `check=True` 但**假绿**：页面按「页面规则版」定义渲染（`element` 语义），描述变成"给所选控件设置值，并在页面中实时更新。" |

### 权威依据：前端 bundle，不是后端 DTO

右侧面板「请选择一个活动节点」是**纯前端组件**（用户指出：没有后端请求）。
节点定义在 `udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js`：

```js
// @1137924 页面规则版（ez）
{group:"base", name:"设置值", type:"ASSIGN_VALUE", settings:[{items:e=>[
  {key:"element", label:"设置元素", type:"datasourceElementSelector"},   // 页面控件
  {key:"value",   label:"值",     type:"valueComponent"}]}]}

// @1216316 实体规则版（t8）
{group:"base", name:"设置值", type:"ASSIGN_VALUE", settings:[{items:e=>[
  {type:"descriptionInfo", value:"注意，【设置值】将在实体字段的默认值和计算值被应用之后执行。"},
  {key:"param", label:"字段", type:"entityFieldSelector", required:true},  // 实体字段
  {key:"value", label:"值",   type:"valueComponent", required:true}]}]}
```

★ 同一个 `type:"ASSIGN_VALUE"` 有两份定义：**跑在哪个规则里就用哪份的 key**
  —— 实体规则 `param`，页面规则 `element`。用错 key 会 check 通过但页面不认。

另有一份**基础节点总表**（同文件模块 1198，26 项 JSON）：
`分支/列表循环/计数循环/自定义错误/跳出循环/创建变量/修改变量/创建映射组/映射操作/创建列表/修改列表/列表操作/查询单条数据/查询多条数据/插入数据/批量插入数据/更新数据/批量更新数据/删除数据/自定义服务/事件投递/连接器/子微流程/执行生单规则/类型转换/数据转换`
—— **不含「设置值」**，它是按规则类型动态附加的（`tag=ATTRIBUTE` 参数操作）。

### ✗ 为什么不能用 CHANGE_ENTITY（更新数据）

`CHANGE_ENTITY` 在总表里（tag=ENTITY），语义是"更新检索到的某条数据"，
需要 `selectParam` 指向目标 DTO + `attrs[]` 批量改字段。
计算规则是给**当前记录**的字段赋值，用 ASSIGN_VALUE。

### 页面验收（2026-10-23）

```
规则 1026598281682062368
画布  开始 → 条件分支
        ① 符合条件即进入该分支 → 设置值
        ② 不符合条件即进入该分支 → 设置值
      结束
红字  无
```

工具：`tools/core/entity/write_entity_rule.py --action set-condition --cond "f03int > 500" --set-field f01text --if-value 超限 --else-value 正常`
