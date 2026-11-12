# 逻辑容器 / 映射 / 服务类节点落库契约

本文件补充 `references/24-node-contracts.md` 未展开的 6 类节点的**真实后端结构 + 字段陷阱**：
FOR / FOR_EACH / BREAK / CUSTOM_ERROR / CREATE_MAP / MAP_OPERATION / CALL_APP_SERVICE / PUBLISH_BUSINESS_EVENT。

全部来自 CDP 真实建节点 + 后端 dataSchema 回读，并与前端 bundle 的 settings 定义交叉验证。

---

## FOR（计数循环）

### 字段与默认值（全部有默认值 → 直接导致不落库，见 SKILL.md 的 configChanged 闸门）

| key | 标签 | 类型 | 必填 | 默认值 |
|---|---|---|---|---|
| `forStart` | 循环起始值 | valueComponent | ✅ | `{type:"Simple",simple:0,desc:0}` |
| `forEnd` | 循环终止值 | valueComponent | ✅ | `{type:"Simple",desc:0,simple:0}` |
| `forStep` | 步长 | inputNumber | ✅ | `1` |
| `operator` | 执行条件 | executionConditions | ❌ | `"<="` |
| `targetName` | 循环变量名称 | outputName | ✅ | `计数循环变量_1` |

- `forStart`/`forEnd` 的 `valueType: ["CONSTANT","EXPRESSION","CONTEXT_VARIABLE"]`，与 RETRIEVE 右值同构；上限 `max: 99999999`。
- `operator` UI 四项：`小于等于 / 小于 / 大于等于 / 大于` → 后端 `"<=" / "<" / ">=" / ">"`。
- 出参恒为 `{dataType:"INTEGER", type:"OBJECT", javaType:"java.lang.Integer", desc:targetName}`。
- `foreach: null`（计数循环不用 foreach，FOR_EACH 才有 `{sourceItemes:[]}`）。

### 后端结构

```json
{"nodeId":"For_xxx","type":"FOR","caption":"计数循环(1)",
 "forStart":{"type":"Simple","simple":0,"desc":0},
 "forEnd":{"type":"Simple","desc":0,"simple":0},
 "forStep":1,"operator":"<=","targetName":"计数循环变量_1",
 "output":{"id":"","dataType":"INTEGER","type":"OBJECT",
   "desc":"计数循环变量_1","javaType":"java.lang.Integer","name":"_FOR_xxxxxx"},
 "nodes":[],"isCompleted":true}
```

平台提示（bundle 原文）：SERVICE 型「请尽量避免在循环中使用插入数据、更新数据、自定义服务、子微流程等节点」；非 SERVICE 型「请尽量避免在循环中使用值操作、微流程等节点」。

### 根级容器节点卡片可能不渲染

FOR 建在**根级**（不在 BRANCH/CONDITION 内）时，`flowFrame` 与后端 `dataSchema` 都有它，但画布 `.udc-microflow-editor-node-container` 查不到对应 DOM —— `open_node` 返回 `empty drawer`，`flowNodes` 里结构完整。此时不要靠点击二次进入，重载页面后从 `flowNodes` 直接读结构。

---

## FOR_EACH（列表循环）

- 字段：`selectParam`（选择列表，filter `type == 'ARRAY'`）、`targetName`（循环对象名称，默认 `列表循环变量_1`）。
- **自动降维解包**：输入 `type:"ARRAY"`，`output` 自动降为 `type:"OBJECT"`，`dataType`/`javaType` 保持不变 —— 循环体内子节点可直接把迭代变量当单条实体用。
- 容器节点：`nodes: []` 子链，`foreach:{sourceItemes:[]}`。
- 渲染为 `.branches.loop`，循环体加号在 `.branches.loop .anticon.add-button`（不是根级的 `.anticon.add-button`）。

---

## CONDITION（分支条件，内嵌在 BRANCH.conditions[]）

### 它不在 nodeTypeList 里

26 项节点清单**没有** CONDITION。它永远内嵌在 `BRANCH.conditions[]`，`type:"CONDITION"`、`actionType` 为 `null`。画布上「分支」节点的各个分支口就是它。

### 三种 name（同一 type，靠 name 区分语义）

| name | caption | expression | 数量（643 条生产流程） |
|---|---|---|---|
| `ifBranch` | 符合条件即进入该分支 | **必填** | 952 |
| `elseBranch` | 不符合条件即进入该分支 | **必须为 null** | 941 |
| `elseIfBranch` | （第三分支口） | 必填 | 88 |

新建分支时前端只给 two 个：`ifBranch`（`expression:{title:"",schema:null}`）+ `elseBranch`（`expression:null`）。要三分支得自己插 `elseIfBranch`。

### ifBranch 真实结构

```json
{"nodeId":"CONDITION_xxx", "name":"ifBranch", "type":"CONDITION",
 "caption":"符合条件即进入该分支",
 "description":"<表达式中文原文，与 expression.title 相同>",
 "runAfter":null,
 "expression":{
   "title":"不为空(微流程.查询单条数据(1).xxx.yyy) && ...",
   "schema":"{\"designData\":{\"expressionTranslation\":\"...\",\n             \"resultTypeInfo\":\"BOOLEAN\", \"resultTypeFullName\":null,\n             \"terminalType\":\"BACKEND\", \"isMultiSelect\":false, \"context\":[...]},\n             \"runtimeData\":{...}}"
 },
 "isCompleted":true, "nodes":[]}
```

关键契约：

- **`expression.schema` 是 JSON 字符串**（内嵌 JSON），不是对象；内分 `designData` / `runtimeData` 两层。
- **`resultTypeInfo` 必须是 `"BOOLEAN"`**，`resultTypeFullName` 为 `null`。
- **`description` 写的是表达式的 `expressionTranslation` 中文原文**，不是业务描述。真机 952 个 ifBranch 全部如此——不写就是画布上分支标签空白。
- **`isCompleted:true`** 才被保存校验放行。

### elseBranch 真实结构（只有 6 个键）

```json
{"nodeId":"CONDITION_xxx", "name":"elseBranch", "type":"CONDITION",
 "caption":"不符合条件即进入该分支", "description":"", "runAfter":null,
 "expression":null}
```

**没有 `isCompleted`，没有 `expression` 对象。** 给 elseBranch 赋表达式是错的——会把 else 当条件分支处理。

### 生成规则

- 条件表达式必须走 `/expression/transform` 生成 `schema`，**不能手拼 `designData`**
- `description` 必须同步写 `expressionTranslation`
- 闸门 G12 就是查这三条：name 值域 / ifBranch 的 resultTypeInfo / elseBranch 的 expression 必须 null

---

## BREAK（跳出循环）

### 只能加在循环体内

根级/分支级节点面板**没有**「跳出循环」。实测根级面板 24 项不含 BREAK。
必须在 `FOR_EACH` / `FOR` 的循环体容器（DOM `.branches.loop`）内点加号才会出现。

### 零表单零出参

```json
{"nodeId":"BREAK_xxx","type":"BREAK","actionType":"BREAK","caption":"跳出循环(1)",
 "input":null,"output":null,"isCompleted":true,"name":null}
```

- `noCompleted: true` → 前端创建时直接置 `isCompleted = true`，不需要「配置完成」步骤。
- 抽屉只有 `[取消][确定]`，`items: []`。
- **`submit()` 三级兜底全部失效**：A 级要聚焦最后一个 `input.ant-input`，BREAK 没有输入框 → 返回 `via=FAILED`。正确做法是直接点抽屉里文本为「确定」的按钮。
- 自身不发 `udcMicroflowUpdatePost`，只有流程级「保存并提交」才落库。

---

## CUSTOM_ERROR（自定义错误）

### 类型名陷阱

| 场景 | 名字 |
|---|---|
| 节点面板显示 | 自定义错误 |
| 前端 nodeTypeList 的 actionType | `FRONT_CUSTOM_ERROR` |
| **后端 dataSchema 的实际 type** | **`CUSTOM_ERROR`** |

按 `FRONT_CUSTOM_ERROR` 回读会永远命中 0 条。

### 两种模式与联动

| key | 标签 | 必填 | 显示条件 |
|---|---|---|---|
| `errorType` | 错误提示方式 | ❌ | 恒显示，默认 `GLOBAL` |
| `sourceData` | 原始数据 | ✅ | `POSITION` |
| `selectParam` | 错误数据 | ✅ | `POSITION` |
| `attrType` | 定位字段（多选） | ✅ | `POSITION` |
| `error` | 填写错误 | ✅ | `GLOBAL` |
| `attrError` | 填写错误 | ✅ | `POSITION` |

- **`error` 和 `attrError` 的 label 都叫「填写错误」**，靠 `errorType` 区分，不能只按 label 定位。
- `errorType` 切换会清空 `sourceData/selectParam/attrType/error/attrError`（`setEmptyBeforeChanged`）；切回 GLOBAL 后 `error` 已空，必须重填。残留字段还可能继续触发「值不能为空」，先确认字段已收拢再填。
- `填写错误` 是 valueComponent，必须 `focus()` + `Input.insertText`（见 SKILL.md 对应坑）。

### GLOBAL 后端结构

```json
{"nodeId":"CUSTOM_ERROR_xxx","type":"CUSTOM_ERROR","caption":"自定义错误(1)",
 "input":null,"output":null,"isCompleted":true,
 "errorType":"GLOBAL",
 "error":{"type":"Simple","simple":"错误文案","desc":"错误文案"}}
```

### POSITION 后端结构

```json
{"nodeId":"CUSTOM_ERROR_xxx","type":"CUSTOM_ERROR","isCompleted":true,
 "errorType":"POSITION","error":null,
 "sourceData":{"description":"查询结果","dataType":"DTO","dtoType":"MASTER_ENTITY","outputName":"_RETRIEVE_xxx","nodeInfo":{...}},
 "selectParam":{...同 sourceData 形状...},
 "attrType":[{"id":"<DtoFullName>.<field>","fullName":"<DtoFullName>.<field>","name":"<field>",
   "javaType":"java.lang.String","dataType":"STRING","type":"OBJECT","desc":"<字段标题>",
   "relationApp":"<appName>","refApp":"<appName>","multiSelect":false,"dtoType":"CUSTOM",
   "label":"<字段标题> [文本]"}],
 "attrError":{"type":"Simple","simple":"字段错误文案","desc":"字段错误文案"}}
```

`sourceData` 只允许 `dtoType === "MASTER_ENTITY" && udcApp`；`selectParam` 允许 `MASTER_ENTITY` / `SUB_ENTITY`。
零出参：`output: null`、`input: null`、`name: null`。

---

## CREATE_MAP（创建映射组）

- 字段：`entries`（添加映射，动态行，选填）、`title`（节点出参名称，必填，默认 `映射组_1`）。
- **按钮文本是「添加键值对」**，不是「添加映射」（后者是 form-item 的 label）。点一次生成一行 `input[placeholder="请输入映射的键(key)"]` + 值输入框。
- 键只能是 String；值支持任意类型（valueComponent）。

```json
{"nodeId":"CREATE_MAP_xxx","type":"ACTIVITY","actionType":"CREATE_MAP",
 "caption":"创建映射组(1)","input":null,
 "output":{"dataType":"MAP","javaType":"java.util.Map","id":null,"type":"OBJECT",
   "desc":"映射组实测","appName":null,"dtoType":null,"udcApp":null,
   "generics":{"keyType":{"dataType":"String"},
               "valueType":{"dataType":"Object","javaType":"java.lang.Object"}},
   "name":"_CREATE_MAP_xxxxxx"},
 "isCompleted":true,
 "entries":[{"key":{"type":"Simple","simple":"key1","desc":"key1"},
             "value":{"type":"Simple","simple":"value1","desc":"value1"}}],
 "title":"映射组实测",
 "generics":{"keyType":{"dataType":"String"},
             "valueType":{"dataType":"Object","javaType":"java.lang.Object"}}}
```

`generics` 同时出现在 `output` 内和节点顶层。

---

## MAP_OPERATION（映射操作）

### 4 种 operationType 与联动字段

| UI | operationType | 触发字段 | 出参 |
|---|---|---|---|
| 获取 | `GET` | 该值的映射键、映射值类型、数据类型、是否列表、节点出参名称、未获取到数据时、提示内容 | 映射值本身 |
| 赋值 | `PUT` | 添加映射 | 无 |
| 删除 | `REMOVE` | 要删除的键 | 无 |
| 获取键列表 | `KEY_SET` | 节点出参名称 | 键列表 |

### 映射值类型 paramType（5 种）

`BASIC` 基本类型 / `ENTITY_OBJECT` 实体对象 / `DEFAULT_OBJECT` 自定义对象 / `ENUM` 选项集 / `MAP` 映射。

`output` 随 `paramType` 变化：`BASIC` → `basic` 指定的标量；`ENTITY_OBJECT`/`DEFAULT_OBJECT` → 对应 DTO；`ENUM` → 选项集；`MAP` → 嵌套 MAP。
**`generics` 恒存在**，即使输出是 String 也带 `{keyType:String, valueType:Object}`（从上游 MAP 继承）。

### GET + BASIC + STRING 后端结构

```json
{"nodeId":"MAP_OPERATION_xxx","type":"ACTIVITY","actionType":"MAP_OPERATION",
 "caption":"映射操作(1)","input":null,
 "output":{"javaType":"java.lang.String","dataType":"STRING","type":"OBJECT","desc":"映射值结果",
   "generics":{...},"name":"_MAP_OPERATION_xxxxxx"},
 "isCompleted":true,"paramType":"BASIC","title":"映射值结果",
 "basic":{"label":"文本","value":"STRING","key":"STRING","dataType":"STRING"},
 "selectMap":{"description":"映射组实测","dataType":"MAP","javaType":"java.util.Map",
   "outputName":"_CREATE_MAP_xxx","nodeInfo":{"nodeId":"CREATE_MAP_xxx","actionType":"CREATE_MAP"}, ...},
 "operationType":"GET",
 "theKey":{"type":"Simple","simple":"key1","desc":"key1"},
 "arrayOrObject":"OBJECT",
 "nullHandling":"TERMINATION","nullPromptMessage":"未找到映射键 key1",
 "generics":{...},"dataType":"STRING",
 "structure":{"label":"文本","value":"STRING","key":"STRING","dataType":"STRING","fullName":"java.lang.String"}}
```

`selectMap` 的 filter 是 `dataType == "MAP" && type == "OBJECT"` —— 上游必须是 CREATE_MAP 或另一个返回 MAP 的节点。

### 必填项（后端 checkSchema 与前端校验口径不同）

- **`output` 不可为 null**：缺了报 `MAP_OPERATION.output PROPERTY_IS_REQUIRED`「必填参数未配置」。
- **`paramType` 不可为 null**：缺了同样报必填。
- **GET 操作的 `nullPromptMessage`（提示内容）不能是空串**：后端 `checkSchema` 放行 `""`，但**新建节点**在抽屉里点「确定」时报红字「请输入提示内容」。填真实文案（如「未找到映射键 xxx」）。
  **但不要据此拦存量/生产流程**：643 条生产流程里 24 个 MAP_OPERATION 的 `nullPromptMessage` 全部为空且正常运行——它是后加的 UI 强校验，只作用于「新节点点确定」。闸门（G9）因此不查这一项，新建节点时手工填就行。
- **`basic`（「数据类型」）必须是选项对象，不能是裸字符串**：前端是 `treeListSelector`，`dataListInfo` 每项 `{label,value,key,dataType}`。写 `basic:"STRING"` 时抽屉里显示空占位「选择数据类型」（后端却有值），且 `structure:{...basic}` 被字符串迭代成 `{"0":"S","1":"T",...}`。正确：`basic:{label:"文本",value:"STRING",key:"STRING",dataType:"STRING"}`、`structure:{...basic, fullName:"java.lang.String"}`。

这几个字段是手写构造器最容易漏/写错形态的——后端浅校验查不出来，必须逐节点点开抽屉看渲染值（只读打开即可，别点「确定」，见 SKILL.md 的 endNode 破坏性副作用）。

---

## CALL_APP_SERVICE（自定义服务）

- 固定字段：`app`（选择应用，必填）、`selectMethod`（选择服务，必填）、`outputName`（节点出参名称，必填）。
- **出参名字段是 `outputName`，不是 `title`**；出参描述是 `outPutDesc`（P 大写）。

### 入参形态由服务签名决定（实测 4 种）

| 形态 | 触发字段 |
|---|---|
| 无入参 | 无参数字段，只配出参名 |
| 单参（非 DTO） | `参数`（valueComponent，必填） |
| DTO 入参 | `赋值方式`（radio，必填）+ `参数映射`（选填） |
| 列表入参 | `赋值方式` + `参数`（选填） |

`赋值方式` 选项：DTO 型 → `字段映射 attrs` / `对象引用 value` / `自动映射 mapping`；列表型只有 `对象引用 value`。

### `selectMethod` 存完整方法元数据

```json
{"caption":"获取当前应用文件中心配置","dubbo":false,
 "fullName":"com.seeyon.boot.starter.file.appservice.FileAppService.getFileConfig",
 "implClass":"com.seeyon.boot.starter.file.appservice.FileAppService",
 "md5":"<md5>","parameter":null,
 "returnValue":{"caption":"文件中心配置","type":"com.seeyon.boot.transport.SingleResponse",
   "item":{"enums":null,"itemType":"com.seeyon.boot.starter.file.dto.response.FileConfigDto","item":null}},
 "isCondition":false}
```

- **`returnValue` 是 `SingleResponse<T>` 包装**：`output` 的 `javaType` 取的是解包后的 `item.itemType`，不是 `returnValue.type`。
- 可选应用 = 当前应用 + 所有依赖应用。

---

## PUBLISH_BUSINESS_EVENT（事件投递）

### 双「事件类型」标签陷阱（最容易踩）

抽屉里有**两个 label 都叫「事件类型」**的 form-item，靠 DOM `id` 区分：

| 位置 | DOM id | key | 选项 | DOM 类名 |
|---|---|---|---|---|
| 第 1 个 | `#eventType` | `eventType` | `AMONG_APP` 应用间(异步) / `IN_APP` 应用内(同步) | `ant-radio-button-wrapper` |
| 第 2 个 | `#messageType` | `messageType` | `DEFAULT` 普通事件 / `DELAY` 延迟事件 | `ant-radio-wrapper` |

按 `.ant-radio-wrapper` 找 `eventType` 会拿到空文本（它是 button 型）。必须同时匹配两种类名，或直接用 `#eventType` / `#messageType` 定位。

### 联动矩阵

| eventType | messageType | 显示字段 |
|---|---|---|
| `AMONG_APP` | `DEFAULT` | 事件类型 / 选择应用 / 可投递的事件 / 事件类型 |
| `AMONG_APP` | `DELAY` | 上述 + **发送时间**（`executeTime`，DateTime，必填） |
| `IN_APP` | —（整块隐藏） | 事件类型 / 可投递的事件（**选择应用被隐藏**） |

### 两个不同的「可投递的事件」字段名

- `AMONG_APP` → **`selectMq`**
- `IN_APP` → **`selectEvent`**

label 相同，key 完全不同。

### 切换顺序必须从外到内

`setEmptyBeforeChanged` 清空链：切 `eventType` 清 `app/selectMq/messageType/attrs/mappingType`；切 `app` 清 `selectMq/messageType/attrs/mappingType`；切 `selectMq` 清 `value/attrs/mappingType/messageType`；切 `messageType` 清 `executeTime`。
顺序错（先填事件再切 messageType）前面填的会被清掉。

### 事件列表为空是应用侧配置缺失

`dataListInfo` 由 `app.appName` 决定。应用未定义业务事件时两个下拉都显示「暂无数据」，这是**应用侧缺配置，不是节点问题** —— 汇报时必须归入「未闭环/环境受限」，不能算已完成。

---

## CONNECTOR（连接器）——依赖集成平台前置配置，不是纯代码可构造

### 它在清单里，但生产 0 样本

`nodeTypeList` 第 22 项确实是「连接器 / `CONNECTOR` / tag:TRANSFER」，但在 643 条 RELEASE 生产流程里 **出现 0 次**。

### 为什么 0 样本（已查证，不是「没人用」）

`udcMicroflowSearchAppServiceByAppNamePost` 查 `cip-connector` 应用的可用服务，返回 **`content: []`**。即：

- `cip-connector`（`udcApp:false`，平台内置应用）在本环境没有任何已注册服务方法
- 连接器节点必须先到「集成平台」（`cip-manager`）里配置连接器与消息，应用侧才有选项
- 无前置配置时节点能拖出来，但抽屉里的下拉是空的

### 所以

- **生成器不应尝试构造 CONNECTOR**：无前置配置时生成的必然是空引用
- 要用按这个顺序：① 集成平台配连接器与消息 → ② 微流程里加节点从下拉选 → ③ 抓一次真实抽屉补 `SAVE_REQUIRED_FIELDS["CONNECTOR"]` 与 `selectConnector` 字段形态
- 闸门 G14 只查最基本的一条：出现 CONNECTOR 必须带 `app`（否则抽屉报「连接器依赖已移除，请在应用管理添加依赖后使用」）

### 已确认的前端事实

- 它与「事件投递」**共用同一个配置组件**（`type:"BusinessEvent"`）
- `messageSource:"CONNECTOR"` 属于外部消息源（`EXTERNAL`），与 `EVENT`/`MICRO_FLOW_EVENT`（`INTERNAL`）对立
- 代码里 `["CONNECTOR"]` 是一个特殊依赖检查列表
