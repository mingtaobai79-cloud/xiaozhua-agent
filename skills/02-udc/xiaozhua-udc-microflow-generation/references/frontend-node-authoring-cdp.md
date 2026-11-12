# 通过前端 CDP 逐个搭建 UDC 微流程节点

节点由前端 `addNode` 造，不是后端拼 JSON。本文是逐节点操作手册 + 实测表单值 + CDP 坑。

## 0. 节点清单以 store 为准

```js
appReduxStore.getState().appDesign.microflowEditorReducer.nodeTypeList
```

抽屉「动作场景」实际只有 24 个可添节点（7 组）：

| 组 | 节点 | actionType | nodeId 前缀 |
|---|---|---|---|
| 逻辑 | 分支 | *(无 actionType，type=BRANCH)* | `BRANCH_` |
| 逻辑 | 列表循环 | *(无)* `type=FOR_EACH` | `ForEach_` |
| 逻辑 | 计数循环 | *(无)* `type=FOR` | `For_` |
| 逻辑 | 自定义错误 | *(无)* `type=CUSTOM_ERROR` | `CUSTOM_ERROR_` |
| 变量 | 创建变量 / 修改变量 | `CREATE_VARIABLE` / `CHANGE_VARIABLE` | 同名 |
| 映射 | 创建映射组 / 映射操作 | `CREATE_MAP` / `MAP_OPERATION` | 同名 |
| 列表 | 创建列表 / 修改列表 / 列表操作 | `CREATE_LIST` / `CHANGE_LIST` / `LIST_OPERATION` | 同名 |
| 数据 | 查询单条 / 查询多条 / 插入 / 批量插入 / 更新 / 批量更新 / 删除 | `RETRIEVE` / `RETRIEVE_ARRAY` / `CREATE_ENTITY` / `CREATE_BATCH_ENTITY` / `CHANGE_ENTITY` / `CHANGE_BATCH_ENTITY` / `DELETE_ENTITY` | 同名 |
| 基础服务 | 自定义服务 / 事件投递 / 子微流程 / 执行生单规则 | `CALL_APP_SERVICE` / `PUBLISH_BUSINESS_EVENT` / `SUB_MICROFLOW` / `CALL_DATA_FLOW` | 同名 |
| 数据加工 | 类型转换 / 数据转换 | `CONVERT_DATA` / `DATA_MAPPING` | 同名 |

- `BREAK`（跳出循环）**不在抽屉里**（`noCompleted:true`），只在循环内部加。
- `CONNECTOR` 在 store 的 nodeTypeList 里但抽屉不列出。
- `FOR_EACH` 与 `FOR` 是两个类型，nodeId 前缀分别是 `ForEach_` / `For_`。

## 1. 七步节奏（每个节点都走，一步不省）

```
添加节点 → 抓默认 → 逐项选择(每个 radio 值/每个 select 选项) → 点确认走校验
→ 看必填 → 填必填 → 填业务 → 再确认 → 回读 store 与后端 dataSchema → 抓全链路接口
```

添加节点本身**不产生任何接口调用**（纯前端 redux）。点确认后才触发：

```
udcMicroflowUpdatePost → udcMicroflowFindByIdGet → udcMicroflowSearch
→ udcMicroflowDisableNodePost + udcMicroflowFindCustomDtoPost
→ udcMicroFlowGroupSelectByTypePost
```

## 2. 确认后的真实节点（后端回读，可复用）

### 创建变量（BASIC/文本）

```json
{"paramType":"BASIC","title":"变量_1","dataType":"STRING",
 "value":{"type":"Simple","simple":"测试值","desc":"测试值"},
 "nodeId":"CREATE_VARIABLE_P3SPbN","actionType":"CREATE_VARIABLE",
 "caption":"创建变量(1)","description":null,"type":"ACTIVITY",
 "output":{"id":"","javaType":"java.lang.String","dataType":"STRING","type":"OBJECT",
   "desc":"变量_1","dtoType":"","name":"_CREATE_VARIABLE_d3ZScR"},
 "isCompleted":true}
```

关键：出参名的**表单字段叫 `title`**，但 `output.name` 是前端另生成的 `_CREATE_VARIABLE_<nanoid>`，两者不等。`output` 永远由前端按 paramType/dataType 生成，不要手写。

### 查询单条数据（RETRIEVE，TERMINATION + 过滤条件）

```json
{"nodeId":"RETRIEVE_CRwMB9","type":"ACTIVITY","caption":"查询单条数据(1)",
 "actionType":"RETRIEVE","isCompleted":true,
 "fetchType":"CONDITION",
 "app":{"appId":"...","appName":"...","caption":"数据迁移","inApp":true,"udcApp":true,"dynamicDependency":false},
 "structure":{"key":"<domain 全名>","id":"<DtoFullName>","label":"<实体标题>","dataType":"DTO",
   "entity":"<domain 全名>","dtoType":"MASTER_ENTITY","udcApp":true,"fullName":"<DtoFullName>",
   "relationEntity":"<实体数字 id>",
   "methodLegal":{"available":true,"complexCondition":true,"seniorMethod":true,"serviceType":"NONE","interfaceClassFullName":null}},
 "condition":[ /* 见下 */ ],
 "sortParams":[],"needCascade":false,
 "title":"<节点出参名>",
 "nullHandling":"TERMINATION",
 "nullPromptMessage":"未查询到对应记录，流程终止",
 "selectType":"DTO","scope":"OBJECT",
 "output":{"appName":"...","id":"<DtoFullName>","javaType":"<DtoFullName>","dataType":"DTO",
   "type":"OBJECT","desc":"<节点出参名>","dtoType":"MASTER_ENTITY","udcApp":true,"name":"_RETRIEVE_xxxxxx"},
 "methodLegal":{...同 structure.methodLegal}}
```

### 查询单条的另外三组字段（都实测落库）

**未查到数据时**：`nullHandling:"CONTINUE"` 保存后 `nullPromptMessage` **自动变 null**（不是空串），前端连「提示内容」这一项都不渲染。只有 `TERMINATION` 才带文案。

**排序规则**（`sortParams`，可多行、可逐行删）：

```json
[{"sortType":"ASC",
  "attrType":{"validate":true,"id":"<DtoFullName>.expNum","name":"expNum","fullName":"<DtoFullName>.expNum",
    "md5":"<md5>","dataType":"INTEGER","type":"OBJECT","javaType":"java.lang.Integer",
    "refApp":"<appName>","refType":"NONE","multiSelect":false,"caption":"实验数量","description":"",
    "customs":{"basicType":false,"sourceType":"ENTITY","dataType":"INTEGER","name":"expNum","id":"<属性数字 id>"},
    "sort":14,"dtoType":"CUSTOM","udcApp":false,"dataI18n":false}}]
```

- `sortType` 只有 `ASC` / `DESC`。
- UI：「添加规则」按钮加行 → 出现 `[选择字段▾][升序▾]`，行尾删除图标是 `.sy-icon.lined-remove-circle`。
- 字段下拉选项显示 `caption [dataType]`（如 `实验数量 [整数]`），**按 caption 匹配，不能按字段名**。
- 加行后表达式换行，后续行的 select 坐标会变，**每行重新取坐标**。

**右值是表达式**（`rightParams[0].type = "EXPRESSION"`）：

```json
{"type":"EXPRESSION","value":"{\"designData\":{\"expressionTranslation\":\"应用参数.分页大小 + 应用参数.分页大小 \",\"resultTypeInfo\":\"BIGINTEGER\",\"tokens\":[{\"type\":\"VARIABLE\",\"value\":\"__SYSTEM_PARAMS.zxjPageSize\"},{\"type\":\"OPERATOR\",\"value\":\"+\"}]},\"runtimeData\":{...}}"}
```

- 注意与 `CONTEXT_VARIABLE` 不同：`value` 是 **designData/runtimeData 整包**（和节点 `value.expression.schema` 同构），`resultTypeInfo` 必须与 `leftParam.dataType` 一致。
- 系统变量走 `__SYSTEM_PARAMS.*` 命名空间（`应用参数.分页大小` → `__SYSTEM_PARAMS.zxjPageSize`）。

### 过滤条件弹窗的真实 DOM（点不开/选不中时看这里）

在抽屉里点「过滤条件」区域（不是点「添加」按钮）才打开宽 1100 的 `.ant-modal`（标题「过滤条件」）。

```
whereWrapper
└── conditionGroupHorizontal
    └── row.xiaozhua-condition-expression-row
        ├── .ant-col-8           字段 tree-select
        ├── .ant-col-4.condition-item__operator   运算符 select
        └── .ant-col-12.condition-item__rightParams  右值：input + 「+」按钮
```

- **运算符随字段 dataType 变化，没有统一全集**：长整数多 `在/不在`，文本另有 `包含/不包含/开头为/结尾为`，枚举只有 6 个且无比较符。**每次打开下拉现取，不要写死 10 个**。四类全集、右值三形态与 IDS 分支的落库结构见 `references/retrieve-node-contract.md`（本文不重复）。
- row 的类是 `condition-item__rightParam**s**`（复数），少写 s 取到 null。
- 右值「+」→ `.ant-popover`（宽约 460，含入参变量树 + 「高级模式」）→ 「高级模式」→ 「表达式设置」modal。同修改变量那套，用 `expr_editor` 库。
- 弹窗底部 `[取消][确定]`；`确定` 未填完时**不报错也不关**（无红字），只停留在原地。判成功看 modal 宽度变 0 或抽屉里条件摘要文本变化。
- 右值输入框 contenteditable 语义等同修改变量的变量值：确认后显示 `{应用参数.分页大小 + 应用参数.分页大小}`（带花括号）。

### condition 结构（GROUP → CONDITION → 右值三态）

```json
[{"type":"GROUP","uuid":"<uuid>","conditions":[
   {"type":"CONDITION",
    "leftParam":{"id":"<DtoFullName>.id","type":"OBJECT","javaType":"java.lang.Long",
                 "dto":"_id","field":"id","desc":"ID","dataType":"BIGINTEGER","multiSelect":false},
    "operator":{"value":"EQ","desc":"="},
    "rightParams":[
      {"type":"CONSTANT", "value":true, "desc":true},
      {"type":"CONTEXT_VARIABLE", "value":"<JSON 字符串>", "desc":"..."}
    ],
    "uuid":"<uuid>","logicalOperator":"AND"}
 ]}]
```

- `leftParam.id` = `<DtoFullName>.<字段名>`（前端编辑路径）；`dto` = `_<字段名>`（下划线前缀）。
- `CONTEXT_VARIABLE.value` 是**JSON 字符串**（不是对象），键位 `{key,name,id,appName,description,position:"children",path,outputName,dataType,type,javaType,dtoType,udcApp,multiSelect,customs:{basicType,inApp,dataType,name,id},parentLabel}`。
- **条件组嵌套**：`conditions` 里再嵌一个 `type:"GROUP"` 元素才是真嵌套。但**UI 的「添加」下拉里「添加条件组」与「添加条件」产生的 DOM 完全一样**——都是往 `conditionGroupHorizontal` 里追加一个同级 `xiaozhua-condition-expression-row`，行首用「且」连接，没有多出嵌套容器。所以要测嵌套只能走 `form.setFieldValue('condition', ...)` / REST 构造，UI 点不出来。
- 表达式右值不是 CONTEXT_VARIABLE，走 `/service/udc/expression/transform`。
- `operator.value`：`EQ`(=) / `NEQ`(!=) / 区间与包含类另有取值，按前端 operator/list 取。

### 分支 BRANCH（无 actionType，配置在画布内联不在抽屉）

```json
{"nodeId":"BRANCH_xxxxxx","name":"userBranch","type":"BRANCH","caption":"分支(1)",
 "description":"","runAfter":null,
 "conditions":[
   {"nodeId":"CONDITION_a","name":"ifBranch","type":"CONDITION",
    "caption":"符合条件即进入该分支","description":"","runAfter":null,
    "expression":{"title":"","schema":null},"nodes":[],"isCompleted":false},
   {"nodeId":"CONDITION_b","name":"elseBranch","type":"CONDITION",
    "caption":"不符合条件即进入该分支","description":"","runAfter":null,
    "expression":null,"nodes":[]}]}
```

- 点卡片上的「条件设置」打开的是**表达式设置」面板**（非抽屉，宽约 1000）。编辑器是 `contenteditable` 的 `span.index-module_cursorElem`，不是 textarea/monaco。
- **条件写成后「条件设置」按钮会消失**，要重新编辑只能点卡片里的表达式文本块（`.node-body-title`），不是点按钮。
- 表达式面板的完整操作契约（变量/函数树点两次、占位符填参、运算符顺序、数字字面量坑、函数中文名清单、确认后的 schema 结构）见 `references/expression-editor-ui.md`。
- `elseBranch` 的 `expression:null`，不要给它塞空壳表达式。
- 后端回读时 `conditions[].actionType` 可能是 `None`，这是正常的；判据看 `conditions[].expression.schema` 是否有值。

## 3. 各节点 radio / 枚举取值
| 节点 | 字段 | 取值 |
|---|---|---|
| 创建变量 | paramType | `BASIC` / `ENTITY_OBJECT` / `DEFAULT_OBJECT` / `ENUM` / `METADATA` / `MESSAGE` / `OTHER` |
| 创建列表 | paramType | `BASIC` / `ENTITY_OBJECT` / `DEFAULT_OBJECT` / `ENUM` / `MESSAGE`（无 METADATA/OTHER） |
| 映射操作 | paramType | `BASIC` / `ENTITY_OBJECT` / `DEFAULT_OBJECT` / `ENUM` / `METADATA` / `MESSAGE` / `OTHER` |
| 创建变量/创建列表 | dataType(BASIC 下) | 文本 / 整数 / 长整数 / 小数 / 布尔 / 日期 / 日期时间 |
| 查询单条 | 查询方式 | `CONDITION` / `IDS` |
| 查询多条 | 查询方式 | `CONDITION` / `IDS` / `COUNT` / `OTHERS` |
| 查询单条 | 未查到数据时 | `TERMINATION` / `CONTINUE` |
| 查询单条 | 查询聚合对象 | `false` 关闭 / `true` 开启 |
| 插入/更新数据 | 赋值方式 | `attrs`（字段映射）/ `value`（对象引用） |
| 删除数据 | 删除规则 | `SELECT_PARAM` / `CONDITION` / `IDS` |
| 事件投递 | 事件类型 | `IN_APP`（应用内）/ `AMONG_APP`（应用间） |
| 数据转换 | 目标数据对象类型 | `ENTITY` / `DTO` |
| 计数循环 | 执行条件 | 默认「小于等于」 |
| 修改列表 | 操作类型 | 默认「增加」 |
| 映射操作 | 操作类型 | 默认「获取」 |

`DATA_MAPPING` 切 `ENTITY` 后表单第 5 项 label 是「实体对象」，切 `DTO` 后是「自定义对象」。

### paramType 权威值域：后端 8 种，UI radio 7 种

节点级 `paramType` 以**后端 `ParamTypeEnum`** 为准（CFR 反编译 `com/seeyon/udc/enums/microflow/ParamTypeEnum.java`），共 8 个带 code 的常量：

| paramType | code | 中文 | needFullName | 后端读取字段 |
|---|---|---|---|---|
| `DEFAULT_OBJECT` | 0 | 自定义对象 | ✓ | `app` `structure` `mappingType` |
| `BASIC` | 1 | 基本类型 | — | `dataType` |
| `ENTITY_OBJECT` | 2 | 实体对象 | ✓ | `app` `structure` |
| `ENUM` | 3 | 选项集 | ✓ | `app` `structure` `value` |
| `MAP` | 4 | 映射 | — | `dataType` |
| `METADATA` | 5 | 元数据 | — | `app` `metaDataType` |
| `MESSAGE` | 6 | 事件对象 | — | `dataType` |
| `OTHER` | 7 | 其他 | — | `otherType` |

- 前端「选择数据」radio 只给 7 项，**唯一缺口是 `MAP`**（`MAP` 在前端以 `java.util.Map<String,Object>` 出现在下拉的 `COMPOSITE` 分组里，不走 radio）。
- 别把节点级 `paramType` 和流程级入参混：`MicroFlowParamDataTypeEnum` 只有 `DTO`/`Entity` 两个值；参数页 radio 是 4 类（无参数/基本类型/实体对象/自定义对象，对应 `TRIGGER_PARAM_TYPES`）。三者不同层。
- `needFullName()` 只对 `DEFAULT_OBJECT`/`ENTITY_OBJECT`/`ENUM` 返回 true —— 这三类必须带完整 javaType/fullName。
- `METADATA` 分支强校验：`PAGE` 型必须有 `guid`、实体型必须有 `entityFullName`，否则 `PROPERTY_IS_REQUIRED`。`ENUM` 分支校验 `value.selectParam.javaType` 与 structure 一致，否则 `ENUM_NOT_MATCH`。

### 级联/动态表单（很容易只测到第一层就以为完了）

- **类型转换 CONVERT_DATA 的两个 select（变量类型、选择数据）是级联的**：不先选「变量类型」，第二个下拉打不开（报 dropdown timeout）。先切类型再选数据。
- **子微流程 SUB_MICROFLOW 的「参数映射」行数随被调流程动态生成**：选中不同的目标微流程，映射行数从 2 行到 10 行不等（按目标流程的入参个数）。选完目标流程后必须重新读 DOM 取实际行数，不能写死。
- **执行生单规则 CALL_DATA_FLOW 的 `数据来源方式` 是 radio `SELECT_PARAM` / `CONDITION`**：只有选 `CONDITION` 才出现「过滤条件」行。另选完来源实体后会自动多出「来源实体数据」行。
- **删除数据 DELETE_ENTITY 的删除规则** `SELECT_PARAM` / `CONDITION` / `IDS`，每种切完表单结构不同，都要各走一遍确认。
- 枚举时注意：某些节点的 select 报 `dropdown timeout` / `no item` 是**未满足前置条件**（上一个字段没选），不是真的没选项；不能记为「已覆盖 0 个选项」。

## 4. 抽屉必填项（各节点）

> 下表是 **UI 表单层**（打开抽屉时看得见的红星）。它与**保存校验层**不一致，生成时必须两套都满足。
> 保存校验层的 26 类权威清单与两者分歧见 `references/required-fields-two-layers.md`。

提交时前端抛的 `errorFields` 要分清两种：
- `errorFields:[]` + `outOfDate:true` → 纯 antd 时序断言，可走 onSubmit 兜底
- `errorFields:[{name:["structure"],errors:["请输入选择实体"]}]` → **真业务校验未过，禁止直接调 onSubmit**

不守这条会静默写坏节点：`structure:null` / `condition:null` / `sortParams:null` / `output.id:null` 写进 dataSchema，`udcMicroflowUpdatePost` 仍返 200。下一轮再从抽屉读，字段已经空了，很容易误判成「下拉点不开」而去查完全无关的方向。

**每次提交（200）后立即回读 `structure` / `condition` / `output.id` 非空**，再进下一步。

| 节点 | 必填 label |
|---|---|
| 创建变量 | 变量类型、数据类型、节点出参名称 |
| 修改变量 | 变量 |
| 创建映射组 | 节点出参名称 |
| 映射操作 | 选择映射、操作类型、该值的映射键、映射值类型、数据类型、是否列表、节点出参名称、提示内容 |
| 创建列表 | 列表类型、数据类型、节点出参名称 |
| 修改列表 | 选择列表、操作类型、列表/对象 |
| 列表操作 | 选择列表、操作类型、操作数据、节点出参名称 |
| 查询单条 | 选择应用、选择实体、节点出参名称、提示内容 |
| 查询多条 | 选择应用、选择实体、分页数据、节点出参名称 |
| 插入数据 | 选择应用、选择实体、赋值方式、节点出参名称 |
| 批量插入 | 选择插入的记录列表、节点出参名称 |
| 更新数据 | 选择更新的数据、节点出参名称 |
| 批量更新 | 选择更新的记录列表、节点出参名称 |
| 删除数据 | 删除规则、选择节点、节点出参名称 |
| 自定义服务 | 选择应用、选择服务、节点出参名称 |
| 事件投递 | 选择应用、可投递的事件 |
| 子微流程 | 选择微流程服务 |
| 执行生单规则 | 来源实体、生单规则、数据来源方式、过滤条件、节点出参名称 |
| 类型转换 | 变量类型、选择数据、节点出参名称 |
| 数据转换 | 来源数据、目标数据对象类型、目标数据对象所属应用、实体对象、节点出参名称、映射关系 |
| 列表循环 | 选择列表、循环对象名称 |
| 计数循环 | 循环起始值、循环终止值、步长、循环变量名称 |
| 自定义错误 | 填写错误 |
| 分支 | 无抽屉（画布内联） |

## 5. CDP 操作要点（点不动/看不到时的判别）

| 现象 | 机制 | 做法 |
|---|---|---|
| 点「+」无反应 | 画布 `+` 只认真实鼠标；且依赖 `currentSelected` 被置 | CDP `Input.dispatchMouseEvent` mouseMoved→mousePressed→mouseReleased，带 `buttons`；点完校验 `currentSelected.renderType==='ADD'` 与抽屉里 `span.add-node-title` 数量 > 0，否则重点 |
| 点「+」面板不打开（抽屉数 0，或 `add-node-title` 数量 0） | `.anticon.add-button` 是 `.add-node-btn button` 内部的 **span 图标**，点中图标中心不触发 button 的 onClick | 定位 `.add-node-btn button`（不是 `.anticon.add-button`），点它的 getBoundingClientRect 中心；判据看 `.ant-drawer-body span.add-node-title` 数量是否 24 |
| **批量探测时第二个节点起全部报「不在面板中」** | 上一个节点的抽屉没关，遮住了加号；点击落到遮罩上，面板根本没打开 | 每个节点开始前强制 `close_all_drawers(d)`：循环点「取消」→ 点 `.ant-drawer-close` → 点 `.ant-drawer-mask` → ESC 兑底，直到 `.ant-drawer-open` 数为 0。不清理就判成「节点不存在」会完全跑偏 |
| **画布滚过头，加号跑出视口** | `el.scrollLeft = el.scrollWidth` 会超出可滚范围（实测滚到 16850/17353），加号定位到视口外 | 用 `scrollLeft = Math.floor(scrollWidth * 0.95)`；滚完先校验可见加号数 > 0 再点 |
| **控制节点（分支）点选后无抽屉，误判为探测失败** | `BRANCH`/`CONDITION` 不走配置抽屉，直接落到画布；`REQUIRED_JS` 返回 `{open:false}`（dict 而非 list） | 先判 `drawer.open`，为 false 时改记画布结构（`.branches` 容器 + `.udc-microflow-editor-node-container` 卡片，均带坐标）。不要把「无抽屉」当成失败 |
| 汇总打印 `'str' object has no attribute 'get'` | `form_items` 在无抽屉节点上是 `{'open': False}`，对它 `for x in dict` 迭代出的是字符串 key | 采集时就归一：`as_list()` / `as_dict()` 包一层 `isinstance`；打印前也判一次类型，否则一个控制节点就中断整批 |
| 点「确定」报 `outOfDate:true` | rc-field-form 时序断言，不是业务校验（`errorFields` 恒空）；动态行/自绘控件使 values 与 Field 列表不同步 | 三级兜底：① 最后输入框 Enter ② 点「确定」 ③ 直调 Form 的 `onSubmit(getFieldsValue(true))`。含动态行（排序规则/映射/条件行）的抽屉前两级常双双失效，直接上第三级 |
| 下拉/浮层坐标为 `-9999`、`opacity:0`，或 dropdown 存在但宽 0 | 页面 `document.hidden=true` 时 CSS 动画不推进，停在 `ant-slide-up-enter` 首帧；抽屉底部按钮也整个不渲染 | **`Emulation.setFocusEmulationEnabled(enabled=True)`** 一行解决，不需窗口在前台。它**会反复变回 true**，封装 `ensure_visible(d)` 在每次点击前调用，点完校验 dropdown 宽度>0，为 0 就重试。仍 hidden 就新开同 URL 的 tab 绑定 |
| 点完下拉，选项数正确但 `w=0 opacity=0`，读出来是 `null` | `document.hidden` 在**点击过程中**又翻回 true。只在 click 前修一次不够 | click 前 ensure_visible → click → **再 ensure_visible** → sleep 1.5s → 才读选项。顺序错就得到假失败 |
| 按 select 文本定位「选择实体」永远 `nf` | select 显示的是**已选值**（如实体名「迁移字段映射」），不含 label 文字 | 按 form-item 定位：`.ant-form-item-label > label` 文本 === label 名，再取它下面的 `.ant-select` |
| **实体/列表选择器选不中**（点后 selection-item 仍空，或 `pick_option` 找 `.ant-select-item-option` 返回空） | 实体/列表是 **ant-select-tree 树形下拉**，选项在 `.ant-select-tree-treenode`，不是普通 `.ant-select-item-option` | 用树节点定位：`.ant-select-tree-treenode` 里按 textContent 匹配（`filter(n=>n.getBoundingClientRect().height>2)` 去测量节点），点它。选不中会静默失败——selection-item 空，后续 onfinish 回填时读 null 引用报 `reading 'appName'`（如 LIST_OPERATION 的「选择列表」） |
| 用 `.ant-form-item > .ant-col > .ant-form-item-label label` 读字段名得到 None | 中间还有 `ant-form-item-row` 层，链式选择器不相邻 | 用后代选择器 `.ant-form-item-label > label`，不要写死层级 |
| 下拉第一次能读、第二次空 | 跨进程期间失焦自动关闭 | 「打开 → 读选项 → 点选项」必须在同一个进程调用内完成；用 Python 侧轮询而非 JS `await`（后台 tab 的 `setTimeout` 被节流，promise 不 resolve） |
| 下拉显示「暂无数据」 | 之前输入过的搜索词残留 | 先清空 `input.ant-select-selection-search-input` 再展开 |
| 树节点全在 `-9999` | 取到了隐藏的测量容器 | 只接受 `getBoundingClientRect().width>0 && x>0 && !className.includes('leave')` 的 dropdown |
| 表单赋值不生效 | React 受控组件不认直接改 `.value` | 原生 setter + 派发 `input`/`change`；或从 `form` DOM 的 `__reactFiber$` 向上找 `memoizedProps.form`（antd form 实例），用 `setFieldsValue` |
| 删节点按钮点不动 | `.remove-btn` 被 `.node-top-line` 连线层遮挡 | `Page.reload` 复位：未确认的节点消失，已确认的保留 |
| 提交失败后节点消失 | 前端校验不过会回滚 `flowFrame` | 从头再来，先看 `unhandledrejection` 里的 `values` 判断缺哪项 |
| 连点多个节点后画布撑到视口外 | `+` 位置随节点数右移 | 每抓完一个节点就 `Page.reload` 复位，再抓下一个 |
| 打开节点配置抽屉 | 坐标点击 `.node-body` 经常无效（连线层遮挡/节点在视口外） | 直接调 React onClick：`node.querySelector('.node-body')` 的 `__reactProps$.onClick({currentTarget,target,preventDefault(){},stopPropagation(){},nativeEvent:{},type:'click'})`，调完校验 `currentSelected.nodeId` 已置 |
| 查不到已打开的抽屉 | 部分抽屉不带 `ant-drawer-open` 类 | 用 `.ant-drawer` 且 `getBoundingClientRect().width>200` 过滤，不要依赖 `ant-drawer-open` |
| 抽屉里元素坐标在视口外（如 `x=2015`，视口宽 1699） | 抽屉 `content-wrapper` 带 transform 偏移，实际渲染在视口右侧之外 | 坐标点击全部落空 → 一律改走 React `onClick` / `form.setFieldsValue` / 原生 setter 派发事件 |
| 抽屉宽 1383 但 `body.textContent` 长度为 0 | 关闭动画中的 DOM 残留，看着像抽屉在、实际内容已卸载 | `Page.reload` 复位；不要在这上面继续点 |
| 所有操作都不生效，`document.hidden=true` | 同一浏览器只有**一个** tab 是 `hidden:false`，其余全部 hidden，且 CSS 动画/下拉不推进 | 先 `Emulation.setFocusEmulationEnabled(enabled=True)`（首选，不挑窗口状态）；实在不行再逐个 tab 探 `document.hidden`，或 `PUT /json/new?<同 URL>` 开新 tab 并同步 `tabId`（editor tab id 会变，`probe_tab.json` 要更新） |

| 弹窗「取消」点了没反应，之后几轮读到同一个旧节点 | React 动画/遮罩吃掉 click，modal 残留没关掉 | **用 ESC 关弹窗**（`Input.dispatchKeyEvent` rawKeyDown+keyUp，key=Escape，windowsVirtualKeyCode=27），比点「取消」可靠；每轮操作前断言可见 modal 数为 0 |
| 抽屉靠后的行点不中（排序第 2 行、后续表单项） | 固定底栏 `.node-config-bottom` 遮挡；滚动容器是 `.udc-microflow-editor-node-settings`，`scrollIntoView` 对它不生效 | 手动设该容器 `scrollTop` 再取坐标；**弹窗内部容器反过来不要 scrollIntoView**，会把内容滚走、坐标全异 |
| 点「过滤条件」没反应，区域显示「加载中...」 | 实体/条件数据未就绪时该区域是 `ant-spin` 遮罩，点击命中的是遮罩不是入口 | 先等遮罩消失再点；一直不消失就 `Page.reload` 后重开抽屉，别在遮罩上反复点 |

| reload / 换域名后 CDP 连不上 | 旧 `webSocketDebuggerUrl` 随页面 reload 失效，缓存的 wsUrl 会被拒 | 每次连接从 `/json/list` 重取：先按 tabId，再按 URL 含 `/microflow/editor/`，最后兜底任一非 chrome:// page；**不缓存 wsUrl** |

其他：抽屉节点名是 `span.add-node-title`，`.click()` 有效。

### ★ 抽屉「确定」按钮：`el.click()` 会静默失败，必须调 `props.onClick`

**`.compid_node-config-submit-btn` 的 `.click()` 不是可靠路径。** 同节点、同表单、只换点击手法，结果完全不同：

```
el.click()        表单已填 3 行 → 点确定 → store attrs 仍 []，后端读不到
props.onClick()   表单已填 3 行 → 点确定 → store attrs = 3，flowChanged=true
```

不报错、不抛异常、无红点、抽屉正常关闭。根因是 antd Button 的 `onClick` 挂在 fiber 的 `memoizedProps` 上，DOM 原生 click 不保证走 React 合成事件链。

统一用 `components/udc/microflow/live/react_click.py`（CDP 驱动库，不是 scratch 脚本）：

```python
from components.udc.microflow.live.react_click import (
    react_click, set_controlled_input, open_antd_select, pick_option,
)
DRAWER = 'aside.udc-microflow-editor-node-settings'
react_click(d, '确定', root=DRAWER)          # props.onClick 优先，fiber 树回退
react_click(d, '添加字段', root=DRAWER)
set_controlled_input(d, 'input.ant-input', 'AUTO', DRAWER)   # 原型 setter 绕 value tracker
open_antd_select(d, '.form-list-item .ant-select-selector', DRAWER)
pick_option(d, want='方案编码')
```

**推论：任何点击 helper 的返回值都不能当成功判据。** `{'ok': True}` 只证明点击发生了。动态行类抽屉（参数映射、排序规则、映射关系）尤其要每次以 `store.flowNodes[id].attrs` 或后端 `dataSchema` 回读为准，否则脚本会一路打印「picked 成功 / set 成功 / 确定 ok」而一条数据都没进——这种假成功极难自查，因为每一步都返回 ok。

### 5.1 批量探测（一条流程里连跑 24 个节点）的四个必做

单节点脚本能跑通不代表批量能跑通。下面四条任缺一条，都会让后续节点全部失败或误判：

1. **每个节点开始前强制关残留抽屉。** 上一个节点的抽屉不关就遮住画布加号，点击落到遮罩上，面板根本没打开 → 后续全部报「不在面板中」。按 取消 → `.ant-drawer-close` → `.ant-drawer-mask` → ESC 依次兜底，直到 `.ant-drawer-open` 数为 0。**不要把这种失败报成「节点不存在」。**

2. **画布滚动用 `scrollWidth * 0.95`，不要直接设 `scrollWidth`。** 直接设会超出可滚范围（实测滚到 16850/17353），加号被推到视口外，取到的候选坐标为空。

3. **控制节点（分支/条件）点选后没有抽屉，这不是失败。** `BRANCH`/`CONDITION` 直接落到画布，`REQUIRED_JS` 返回 `{open:false}`。先判 `drawer.open`，为 false 时改记画布结构（`.branches` 容器 + `.udc-microflow-editor-node-container` 卡片，都带坐标）。

4. **采集时就做类型归一。** 无抽屉节点让 `form_items` 是 dict、有抽屉是 list；后续 `for x in form_items` 迭代 dict 得到字符串 key，抛 `'str' object has no attribute 'get'` 并中断整批。采集处统一 `as_list()` / `as_dict()` 包 `isinstance`，打印处再判一次。

成品脚本：`scripts/probe_nodes.py`（已含上述四条）。

## 6. 读表单内部值（判断真实字段名的最快路径）

```js
// 把当前抽屉的 antd form 实例挂到 window.__FORM__
const formEl = document.querySelector('.ant-drawer-open form');
const fkey = Object.keys(formEl).find(k => k.startsWith('__reactFiber$'));
let fiber = formEl[fkey];
while (fiber) {
  const mp = fiber.memoizedProps;
  if (mp && mp.form && typeof mp.form.getFieldsValue === 'function') { window.__FORM__ = mp.form; break; }
  fiber = fiber.return;
}
window.__FORM__.getFieldsValue(true);   // ← 真实字段名与结构全在这
```

`getFieldsValue(true)` 会多出一个字面量键 `"undefined"`，是前端表单未命名的值的占位，忽略即可。

## 7. 驱动脚本的依赖

CDP 驱动用到 `websockets`。用装有该包的解释器运行（Hermes 自带 `python` 有；某些项目 venv 没装）。

## 8. 网络抓包：响应体不能在回调线程取

`Network.loadingFinished` 事件在 WebSocket 回调线程里分发。在该回调里同步调 `Network.getResponseBody` **会死锁**（等待自己所在的事件循环返回）。

正确做法：回调里只登记 `n['_needBody'] = True`，主线程事后批量补取：

```python
def fetch_bodies(self, limit=40):
    pending = [n for n in self.net if n.get('_needBody') and n.get('body') is None]
    for n in pending[:limit]:
        r = self.cmd("Network.getResponseBody", requestId=n["reqId"])
        n['body'] = (r.get('body') or '')[:4000]
        n.pop('_needBody', None)
```

另外**过滤条件不要太窄**：只收 `/service/udc/` 会漏掉保存链路里的其它 service 接口。改成收 `/service/` 或 `graphql`，再排除静态资源扩展名（`.js/.css/.png/.svg/.woff*/.ttf/.ico`）。
