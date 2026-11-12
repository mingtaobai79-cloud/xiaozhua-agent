# 节点结构与出入参契约

> 由 SKILL.md 拆分而来，按需读取。

## ★ FOR_EACH 循环改实体的唯一真实形态（实测 643 条）

「遍历列表并逐条更新实体」在真实数据里**只有一种写法**：

```
FOR_EACH(selectParam=RETRIEVE_ARRAY 出参, targetName=xxx, foreach=null)
  └ CREATE_VARIABLE(ENTITY_OBJECT, mappingType=attrs)
       attrs[].value ← _FOR_EACH_* 出参逐字段（position=children）
  └ CHANGE_ENTITY(selectParam 引用上面那个变量)
```

「CHANGE_ENTITY 直接引用 FOR_EACH 出参」真实出现 **0 次**。
写这种形态 G2 会正确拦住（FOR_EACH 出参是 DTO 循环项，不是可更新的实体引用）。

关键形态细节：
- `FOR_EACH.foreach` 真实 **384/384 为 null**，不是 `{sourceItemes:[]}`
- `FOR_EACH.output` 必须带 `id=DTO全名` + `relationEntity`（缺 id 报 PROPERTY_IS_REQUIRED）
- 循环项字段引用：`key="<_FOR_EACH_out>_<字段id>"`、`position="children"`、`dtoType="CUSTOM"`
- `CHANGE_ENTITY` 真实 103/103 **无 structure/app 键**，只有 selectParam+attrs+title
- `CONDITION.isCompleted`：带 expression 的恒 true（1040/1981），elseBranch 为 null

## ★ END 布尔/基本类型出参（244 条真实样本）

```
endNode.paramType="BASIC" + basic="BOOLEAN"
value 引用一个 BASIC 变量节点（其 output.dataType 必须 == basic，否则类型不匹配）
output.name 必须真实（_FLOW_OUTPUT_xxx，前端按它注册变量表）
```

「是则 true 否则 false」的正确骨架（变量不能在两个分支里各建一个同名）：
先 `CREATE_VARIABLE vResult=false`（前置默认）→ BRANCH if 里 `CHANGE_VARIABLE vResult=true`（else 留空）→ END 引用 vResult。

## ★ 循环项不能直引写操作节点（发布/UI 全过，平台构建时仍编译失败）

CHANGE_ENTITY 的 selectParam 直引 FOR_EACH 循环项（`nodeInfo.type="FOR_EACH"`）时：
checkSchema 绿、发布 RELEASE、逐节点抽屉无红字——全部通过，但**应用构建生成 Java 时
平台把循环下标(int)当对象传**，报 `int 无法转换为 ...Dto`，构建 FAILURE。
真实语料 103/103 写操作都引活动节点出参，0 例直引循环项。

循环内改数据一律走中转：`FOR_EACH → RETRIEVE(IDS, 引循环项.id) → CHANGE_ENTITY(引该 RETRIEVE 出参)`。
循环项**整体**引用（`dtoType=SUB_ENTITY`，`key=出参名+DTO全名`）只在 CHANGE_VARIABLE/CREATE_VARIABLE
赋值场景合法（101 例真实样本），不能喂给写操作节点。

「不符合条件即进入该分支（默认分支）」的珊瑚红边框/红字是编辑器固定配色
（rgb(255,120,117) 只出现在默认分支的 node-body span），不是校验错误。
交付带 else 分支的流程时**主动说一句这是固定配色**——不主动说，用户就会在下一轮问「这个分支怎么是红的」。
elseBranch isCompleted=None 是 643 条真实样本 100% 常态；空子节点 649/941 合法。

## ★ 组合查询条件（排除自己等）BOOT_3000「源对象不能为空」定位

多条件组合（如 enabled==true && id != 入参）在 condition[0].conditions 数组里并列两条，
每条内部：leftParam(实体字段) + operator({value:EQ/NEQ,desc}) + rightParams + uuid + logicalOperator:AND。

右值引用流程入参 = rightParams[0] = {type:CONTEXT_VARIABLE, desc, value:"<json串>"}，
内层 json 是入参 SelectParam（name=_FLOW_INPUT_xxx, position=parent, key=name_name）。
真实样本：-85004964440（id != 入参 同实体查询）。

★ 顶层 condition[0] 的 type 必须是 "GROUP"（构造器 condition_group 正确）。
  手写成 "CONDITION" → 发布报 BOOT_3000「源对象不能为空」，checkSchema 还全绿——
  这是 2026-10-30 实测 15 轮二分定位出的坑，闸门不报，只有发布拒。
  单条件也要套 GROUP 外壳（conditions 数组里挂一条）。

★ RETRIEVE_ARRAY 的 output 无 relationEntity 键（RETRIEVE 单条才有）。
  size=999/pageSearch="false" 是真实标配；删 size 报 PROPERTY_IS_REQUIRED。

## ★ 宿主流程技巧

需要页面上下文（表达式接口、UI 验收）但没有现成编辑器 tab 时：
create 一条空 DRAFT（trigger+endNode 骨架即可）→ 导航编辑器 URL → 用完 delete。


```
1. create  : GraphQL udcMicroflowCreatePost        state=DRAFT
2. 取 guid : GraphQL udcMicroflowFindByIdGet       （create 返回不含 guid）
3. 发布    : REST  POST /service/udc/microflow/checkSchema/update
             ★ 必须带 appId，少它 → BOOT_1001「appId must not be null」
             ★ 15 字段：appId id name caption type triggerType state dataSchema
               serviceInterface sourceType creationMethod groupType versionCode
               openApi restApi microFlowGroupId
4. 回读    : FindByIdGet 确认 state=RELEASE
```

不能走 GraphQL `udcMicroflowUpdatePost` 发布（提交 RELEASE 后回读仍 DRAFT）。
副作用：在 UI 编辑器里打开已发布流程会把状态打回 DRAFT，需重新发布。
代码：`components/udc/microflow/deploy.py` 的 `deploy()`（失败自动删半成品）。

**`create` 与 `FindByIdGet` 的 `content` 形态不同**：create 返回**裸 id 字符串**（`"8849229208645378355"`），
FindByIdGet 返回对象 `{id,state,guid,...}`。解析函数只对 dict 取 `.content`，
否则把整个 `data` dict 当成 id，表现为「create 未返回 id」这种误导性报错——**实际已经建成功了**。
同类：`trigger_type` 传空串会让 create 失败，而失败又被折成 `None`，同样报「未返回 id」。
所以 `create` 失败时必须把真实 `code`/`message` 打出来，并把 `triggerType` 从 `schema.trigger.type` 推导，

**`deploy.get()` 的 GraphQL 查询必须查全 `triggerType` 和 `dataSchema`**，不能只查 `id/state/guid/name/caption` 这 5 个轻量字段：
`publish()` 要用回读的 `triggerType` 拼发布体，查不到就传 `None`；而 `trigger_type` 参数**默认值不能写死 `MANUAL`**——
定时/事件流程用 MANUAL 发出去会丢触发方式或直接被拒。正确写法是 `trigger_type = trigger_type or cur.get("triggerType")`，
并把 `triggerType, type, dataSchema, serviceInterface, groupType, microFlowGroupId` 一并纳入回读，
这样发布后的复核（`trigger.type`/`scheduleCronRule`/`endNode.output`/节点数）才有数据可对，不用再发一次请求。

### ★ 单节点合规 ≠ 能组装发布

构造器逐个测通过，不代表组装起来能发布。必须有一条「编排 → 提交」的链路测试：
`components/construction/microflow_composer.py`（组装器）+ `tests/test_composer.py`。
实测：组装路径首次真发布一次性暴露 4 个单节点测试盖不住的问题
（CONSTANT 语境 / dtoType / 模板残留 / 服务签名读磁盘）。

**组装器是对外入口，直接用 `MicroflowComposer`，不要每次重写主轴脚本**：

```python
comp = MicroflowComposer(builder, live_refs, app_id=APP, app_name=APP_NAME)
comp.step("RETRIEVE_ARRAY", alias="ra", entity="实体标签", cond_field="字段", right="k")
comp.step("CHANGE_VARIABLE", alias="mv", target="v", field="字段", from_node="ra")
trg  = comp.trigger_schedule(job_caption="任务名", cycle_type="DAY", value="1")
schema = comp.finish(trigger=trg)      # 内部跑 G1-G14 + 引用完整性 + 契约闸门，不合规抛 ComposeError
```

它把三个反复踩的坑收进了接口层，自己写主轴脚本时容易漏：
- 对外只收**标签/名字**（实体标签、子流程名、服务全名），不收 id —— 接口能传 id 就一定有人写死
- `_val()` / `_cond_val()` 自动分流 Simple / CONSTANT，调用方不会记错语境
- `finish()` 按 `trigger.type` 决定 endNode 形态（9 键无出参 / 13 键 MANUAL）
失败一律抛 `ComposeError`，不产出可发布的违规 schema。

### ★ 外部引用只收标签，不收 id

组装器的对外接口只接受「实体标签 / 子流程名 / 服务全名」，内部走 LiveRefs 取 id。
一旦接口能传 id，调用方就会写死，换应用必崩。
实测典型：`call_app_service` 原来从磁盘 `definitions/services/*.json` 读签名，
跨应用直接 `FileNotFoundError` → 改为必传活引用签名。

### 实体模型适配：dto/domain 极易搞反

`LiveRefs.find_entity` 返回的是**实体树节点**（9 键），构造器要的是**实体模型**（6 键 + attributes）：

```
LiveRefs 的 fullName        = domain 全名（...domain.entity.YsFull6956）
构造器的 entity["fullName"]  = **DTO 全名**（entity_structure 当 dto 用）
构造器的 entity["entity"]    = domain 全名
```

直接喂会造出 dto=domain 的错引用。用 `LiveRefs.entity_model()` 转换，
断言 `.dto.` 在 fullName 里、`.domain.entity.` 在 entity 里。
attributes 要另调 `udcMicroflowFindCustomDtoPost` 拉（树节点不含属性表）。

## 创建自定义 DTO（出入参自定义对象，建单前先建）

接口 `udcDataTransferObjectCreateDtoWithAttrsPost`，**body 是数组**（GraphQL 变量类型 `[udcDataTransferObjectCreateDtoWithAttrsPostInputBody]`），不是单个对象。字段驼峰：

```
body = [{appId, name, caption, source:"MICRO_FLOW", sourceType:"PART",
         attributes:[{name, caption, dataType, dataTypeCategory:"PRIMITIVE", type:"OBJECT"}]}]
```

- `source="MICRO_FLOW"` + `sourceType="PART"` 必写，否则依次报 `source cannot be empty` / `app_id cannot be empty`（字段名在报错里显示 snake_case 但 body 里写驼峰 appId）。
- 每个 attribute 必须带 `dataTypeCategory:"PRIMITIVE"`，否则报 `dataTypeCategory must not be null`。
- dataType 用 `BIGINTEGER`/`STRING`/`DECIMAL` 等，生成 fullName 形如 `com.seeyon.<app>.dto.microflow.<name>`。
- name 重复报 `UDC_DTO_0001`（残留同名 DTO 会占位），换名或先查重。
- 创建成功返回字符串 id（不是对象）。查已建 DTO 用 `udcDataTransferObjectSearchListPost`（params.appId）。

## 节点必填字段契约（check 报「必填参数未配置」时先查这里）

- **CREATE_VARIABLE（ENTITY 型）必须带 `app`**：`app: app_ref()`（appId/appName/caption/inApp/udcApp/dynamicDependency）。缺了报 `CREATE_VARIABLE.app PROPERTY_IS_REQUIRED`。BASIC 型不需要 app。
- **LIST_OPERATION 的 selectParam 必须带 `dtoType`（+ appName/udcApp/relationEntity）**：引用实体列表时写 `dtoType:"MASTER_ENTITY"`。缺了报 `selectParam.dtoType PROPERTY_IS_REQUIRED`。
- **caption 必须唯一**：`udcMicroflowCreatePost` 对重复 caption 报 `UDC_MICROFLOW_0002 [caption] already exists`。批量生成给 caption 加短随机后缀（如时间戳后 3 位）避免撞名。
- **手写构造器（整包 POST）会漏「隐藏必填字段」，前端 addNode 自动回填、手写必漏**：`CREATE_ENTITY` 缺 `title`+`methodLegal`+`value:null`；`CHANGE_ENTITY` 缺 `title`（=实体 label）；`CREATE_MAP` 缺 `paramType:null`+`dataType:null`+`title`+顶层 `generics`；`MAP_OPERATION` 缺顶层 `generics`（从上游 MAP 继承）。这些字段后端 `checkSchema`（草稿态浅校验）查不出，只有前端「保存并提交」深度校验才报 `firstErrorNode` 且静默零请求。判据：点「保存并提交」前注入 console 钩子，抓 `值为空的必填属性=> <字段名>` 逐条看缺哪个；补齐后对照 `fixtures/microflow/node_templates/<ACTION>.json` 的顶层键核对，别靠手写记忆。
- **写操作类节点的 `output` 必须是「影响行数」标量，不是实体 DTO**（`checkSchema` 报 `PROPERTY_IS_REQUIRED` 只说明不能为 null，填 DTO 它照样放行）：`CHANGE_ENTITY` / `CHANGE_BATCH_ENTITY` / `DELETE_ENTITY` / `CREATE_BATCH_ENTITY` 一律 `dataType=INTEGER` + `javaType=java.lang.Integer` + 无 `dtoType`；`CREATE_ENTITY` 是 `BIGINTEGER` + `java.lang.Long`（新增记录 id）。出参键集只有 6 个：`{id:null, javaType, dataType, type:"OBJECT", desc:<更新成功的数量>, name:_<节点>}`。填 DTO 会让构建期生成 `SingleResponse<Integer>` 赋给 DTO 而编译失败（643 条真实样本 100% 是标量）。`MAP_OPERATION` 才要 DTO/STRING 型 output。
- **`CREATE_MAP.generics` 是对象 `{keyType:{...}, valueType:{...}}`，不是二元数组**：写成 `[a, b]` 报 `NOT_OBJECT [创建映射组]:右值的数据不是单条数据`。
- **`MAP_OPERATION.nullPromptMessage` 在 UI 上是必填文本**：写空串 `""` 时抽屉报「请输入提示内容」红字，必须给真实文案（如「未找到映射键 k1」）。`checkSchema` 不拦这一项，只有逐节点点「确定」才暴露。
- **`CREATE_LIST`（BASIC）必须带 `value`（默认值）**：前端 `dataSchema()` 对 BASIC 列表返回 `{paramType, app, title, dataType, value}`。只写 `paramType/title/dataType/output` 会让列表没有初始值，用户第一眼就是「列表节点你没赋值」。给真实初值 `value: simple_val("INIT")`。
- **`CHANGE_LIST.action` 是必填**（`ADD` 增加 / 全量替换 / 删除），模板已给合法值，**不要 pop 掉**。缺了 `checkSchema` 报 `CHANGE_LIST.action PROPERTY_IS_REQUIRED`。`action` 与 `operationType` 是两个字段，都要留。
- **`MAP_OPERATION` 的 `selectMap` 与 `selectParam` 是两个独立字段，都要指向本流程真实节点**；`entries` 只对 `PUT` 需要，GET 模式删掉。**`basic`（「数据类型」）必须是选项对象 `{label,value,key,dataType}`，不能是裸字符串**——前端该字段是 `treeListSelector`，`dataListInfo:[{label,value,key,dataType}]`；传 `"STRING"` 时下拉渲染成空占位「选择数据类型」，且前端 `dataSchema()` 的 `structure:{...basic}` 会把字符串迭代成 `{"0":"S","1":"T",...}` 垃圾。正确形态：`basic:{label:"文本",value:"STRING",key:"STRING",dataType:"STRING"}` + `structure:{...basic, fullName:"java.lang.String"}`（`fullName` = 该 dataType 的 java 类型）。
- **`SUB_MICROFLOW.mfService` 除 id/name/caption/type 外还要 `path`/`method`/`hostPath`**，缺了报 `mfService.path PROPERTY_IS_REQUIRED`。
- **`FOR_EACH`（列表循环）必填 `selectParam` + `targetName`**：`selectParam` 必须 `type:"ARRAY"` **且带 `dtoType`**（漏了报 `selectParam.dtoType PROPERTY_IS_REQUIRED`），`targetName` 是循环对象显示名，容器字段 `foreach:{sourceItemes:[]}`。用 `FOR` 模板打底改 `type/actionType` 可行，但必须 `pop` 掉 `forStart`/`forEnd`/`forStep`/`operator` 四个计数循环专有字段。
- **必填自检清单不许按 UI 表单字段名猜，要拿生产样本比对。** 实测 `RETRIEVE_ARRAY` **217/217 没有 `title`、217/217 没有 `selectParam`**——它的「节点出参名称」落在 `output.name` / `output.desc`，不在顶层 title。按「RETRIEVE 要 title」类推到 RETRIEVE_ARRAY 会写出假缺陷、然后去「修」一个本来正确的构造器。
  通用判据：写自检脚本前先 `Counter` 一遍该 actionType 在生产样本里的字段频次（`core/facts/udc/microflow/node-contract-from-samples.json` 已备好 MUST/USUAL/OPT），自检只查 MUST 项；**跨节点类推字段名是本类任务最常见的假缺陷来源**。

### ★ 必填有两套且不一致：UI 表单层 vs 保存校验层

同一个节点有两份必填清单，来源不同、内容不同，生成时**两套都要满足**：

| 层 | 来源 | 存于 | 用途 |
|---|---|---|---|
| UI 表单层 | 抽屉里 `.ant-form-item-required` 标记 | `NODE_REQUIRED_FIELDS` | 生成节点时填什么 |
| 保存校验层 | 点「保存并提交」后前端逐节点 `console.log("X 的所有必填属性=> [...]")` | `SAVE_REQUIRED_FIELDS` | 提交前最终闸门 |

**保存校验层是运行时权威**——前端真实执行的全量校验，含条件必填，优先于任何反编译静态推断。两者实测分歧（`UI_VS_SAVE_DIVERGENCE`）：

| 节点 | UI 表单要 | 保存校验要 |
|---|---|---|
| CUSTOM_ERROR | `error` | `sourceData/selectParam/attrType/attrError`（POSITION 模式并集） |
| CREATE_ENTITY | `value` | `attrs` |
| DELETE_ENTITY | `condition` | `value` |
| DATA_MAPPING | `mappingRows` | 整个 `mappingRule` 对象 |

条件必填字段在并集里出现但不恒需（`SAVE_CONDITIONAL_FIELDS`）：`RETRIEVE.nullPromptMessage` 仅 TERMINATION；`MAP_OPERATION.theKey` 仅 GET、`basic` 仅 BASIC；`CREATE_VARIABLE.otherType` 仅 paramType=其他。

**不要把保存校验清单直接覆盖 UI 表**——它会引入条件必填字段，覆盖后离线构造路径全挂（`CREATE_VARIABLE` 被要求 `otherType`、`RETRIEVE` 无条件要求 `nullPromptMessage`）。两表并存，各管一段。

26 类完整清单、提取方法与空提交的 `errorFields` 形态见 `references/required-fields-two-layers.md`。

## 24 类节点覆盖（按业务分组，不是塞进一条流程）


### 26 类真实清单（`nodeTypeList` 运行时读，不是 24）

前端 redux 里 `appDesign.microflowEditorReducer.nodeTypeList` 是**权威清单，26 项**：

| # | 中文名 | actionType | tag |
|---|---|---|---|
| 1 | 分支 | BRANCH | LOGIC |
| 2 | 列表循环 | FOR_EACH | LOGIC |
| 3 | 计数循环 | FOR | LOGIC |
| 4 | 自定义错误 | CUSTOM_ERROR | LOGIC |
| 5 | 跳出循环 | BREAK | LOGIC |
| 6 | 创建变量 | CREATE_VARIABLE | VARIABLE |
| 7 | 修改变量 | CHANGE_VARIABLE | VARIABLE |
| 8 | 创建映射组 | CREATE_MAP | MAP |
| 9 | 映射操作 | MAP_OPERATION | MAP |
| 10 | 创建列表 | CREATE_LIST | LIST |
| 11 | 修改列表 | CHANGE_LIST | LIST |
| 12 | 列表操作 | LIST_OPERATION | LIST |
| 13 | 查询单条数据 | RETRIEVE | ENTITY |
| 14 | 查询多条数据 | RETRIEVE_ARRAY | ENTITY |
| 15 | 插入数据 | CREATE_ENTITY | ENTITY |
| 16 | 批量插入数据 | CREATE_BATCH_ENTITY | ENTITY |
| 17 | 更新数据 | CHANGE_ENTITY | ENTITY |
| 18 | 批量更新数据 | CHANGE_BATCH_ENTITY | ENTITY |
| 19 | 删除数据 | DELETE_ENTITY | ENTITY |
| 20 | 自定义服务 | CALL_APP_SERVICE | TRANSFER |
| 21 | 事件投递 | PUBLISH_BUSINESS_EVENT | TRANSFER |
| 22 | 连接器 | CONNECTOR | TRANSFER |
| 23 | 子微流程 | SUB_MICROFLOW | TRANSFER |
| 24 | 执行生单规则 | CALL_DATA_FLOW | TRANSFER |
| 25 | 类型转换 | CONVERT_DATA | DATA_FACTORY |
| 26 | 数据转换 | DATA_MAPPING | DATA_FACTORY |

**「24 节点」是旧口径**（不含事件投递/连接器）。另外 `CONDITION`（分支条件）**不在清单里**——
它永远内嵌在 `BRANCH.conditions[]`，`type:"CONDITION"`、`actionType` 为 `null`。

### 真实使用频次（643 条 RELEASE 流程统计，决定实现优先级）

| 节点 | 覆盖流程数 | 优先级 |
|---|---|---|
| RETRIEVE | 357 | 极高 |
| CONDITION | 326 | 极高 |
| BRANCH | 326 | 极高 |
| CREATE_VARIABLE | 302 | 极高 |
| CHANGE_VARIABLE | 292 | 极高 |
| FOR_EACH | 199 | 高 |
| LIST_OPERATION | 176 | 高 |
| SUB_MICROFLOW | 156 | 高 |
| CREATE_LIST | 138 | 高 |
| CHANGE_LIST | 135 | 高 |
| RETRIEVE_ARRAY | 126 | 高 |
| CHANGE_ENTITY | 78 | 中 |
| CALL_APP_SERVICE | 65 | 中 |
| CONVERT_DATA | 58 | 中 |
| CHANGE_BATCH_ENTITY | 37 | 中 |
| FOR | 31 | 中 |
| CREATE_ENTITY | 24 | 中 |
| CUSTOM_ERROR | 15 | 低 |
| DELETE_ENTITY | 13 | 低 |
| DATA_MAPPING | 10 | 低 |
| PUBLISH_BUSINESS_EVENT | 9 | 低 |
| MAP_OPERATION | 8 | 低 |
| BREAK | 8 | 低 |
| CREATE_BATCH_ENTITY | 6 | 低 |
| CREATE_MAP | 4 | 低 |
| CALL_DATA_FLOW | 1 | 低 |
| CONNECTOR | **0** | 无生产样本 |

**CONNECTOR 在 643 条生产流程里 0 次使用**——它是真实节点但本项目全量未用，
契约无数据可反推，要用必须现场开抽屉验证。别假设它等同「事件投递」。

全节点清单 + 必填项台账见 `references/24-node-contracts.md`；逐节点操作步骤、真实表单值、CDP 坑见 `references/frontend-node-authoring-cdp.md`。
单节点契约：查询单条 `references/retrieve-node-contract.md`；**查询多条 `references/retrieve-array-node-contract.md`**（4 种查询方式、聚合方法与计算字段联动、分页 pageSearch/size、IDS 与分页对象的前序依赖）；**循环/错误/映射/服务类 `references/node-contracts-logic-and-map.md`**（FOR 五字段默认值、FOR_EACH 降维解包、BREAK 只能循环体内加、CUSTOM_ERROR 的 type 名陷阱、CREATE_MAP 的 MAP 出参、MAP_OPERATION 四种操作、CALL_APP_SERVICE 方法元数据、PUBLISH_BUSINESS_EVENT 双「事件类型」陷阱）。

**铁律：24 类不是一条流程塞满 24 个节点。** 一条真实业务流程自然只用 5~10 类；要覆盖全部 24 类，按业务拆成多条各自自洽的流程（数据加工型 / 数据维护型 / 逻辑控制型 / 数据结构型 / 服务编排型）。只为通过 checkSchema 而拼装的痕迹——查询→插入→更新→批量→删除串成一条链（刚插就删）、CUSTOM_ERROR 摆在主链上（跑到必报错）、出参引用从未被赋值的空实体变量、列表/Map 里塞占位垃圾——用户会直接判定为垃圾流程并删除，前功尽弃。搭之前先问清这条流程要完成什么业务，节点顺序必须能跑通。

三条要点：
- 24 类 = 23 模板 + `PUBLISH_BUSINESS_EVENT`（事件投递，不是 EVENT_DELIVERY）。
- **依赖型节点必须先有真实前置资源，不能凭空写 id**：CALL_DATA_FLOW 要生单规则（`udcDataFlowListManuallyMappingPost` 按 sourceEntityId 查，空=该实体没配规则）、SUB_MICROFLOW 要现成 SERVICE+MANUAL 流程、CALL_APP_SERVICE 要服务接口。
- CUSTOM_ERROR（终止节点）必填「提示消息」= `error.simple`；BRANCH/FOR 是容器节点，子节点内嵌在 conditions[].nodes / nodes[]。

## 硬契约（错一个就是前端空白/报错）

- **回读节点必须按 `actionType` 过滤，`type` 恒为 `ACTIVITY`**：`CREATE_MAP` / `MAP_OPERATION` / `CALL_APP_SERVICE` / `LIST_OPERATION` / `CHANGE_LIST` / `RETRIEVE` / `CREATE_ENTITY` 等所有活动节点，后端 `type` 都是 `"ACTIVITY"`，`actionType` 才是业务类型。用 `n['type'] == 'CREATE_MAP'` 过滤会**永远命中 0 条**，然后误判成「没落库」。只有 `BRANCH` / `FOR` / `FOR_EACH` / `BREAK` / `CUSTOM_ERROR` / `END` 是 `type` 直取（它们的 `actionType` 为 `null`）。
- **trigger.title 必写**：前端「节点出参名称」回显绑 `key:"title"`，保存写 `output.desc="$title"`。只写 output.desc 前端显示空。
- **trigger.output 必带 inApp + hasPagination**：前端「选择参数」树按 `{id,javaType,inApp,appName,dataType,type,desc,dtoType,udcApp,hasPagination}` 构建；缺 inApp/hasPagination 时参数树展开不出字段，用户只能手填。
- **trigger.nodeId 前缀跟类型走**：SERVICE → `SERVICE_xxxxx` + caption「事件监听」；CUSTOM → `CUSTOM_xxxxx` + caption「自定义事件监听」。CUSTOM 用 SERVICE_ 前缀会让自定义监听选不了事件（前端按类型认节点）。
- **节点内 CONTEXT_VARIABLE/CV 引用必须与 trigger.output.name 同步**：重建 trigger 后旧引用（如 `_FLOW_IN_yKU7`）不自动更新，前端一致检测报「前序节点发生变更请重新选择(ID)」。checkSchema 查不出这个。
- **MQ（应用间消息）监听：eventDataFullName 用不带 topic 前缀的 DTO 全名**（`com.seeyon.<app>.dto.YsEvtData2`）。带前缀 `UDC_<APP>_MQ.` 会让 GLOBAL 检测的 dtoMap.containsKey 失败 → 「消息的参数已被删除」。同一条流程的 output.id/javaType 一并写不带前缀名。
- **自定义服务常量值字段是 `simple` 不是 `value`**：`{type:"Simple", simple:"...", desc:...}`；写 value 键后端 `setSimple("")` → 前端空白。
- **`CALL_APP_SERVICE.mappingType` 由入参形态决定，不是恒为 `attrs`**：看 `selectMethod.parameter.item.itemType`——以 `java.` 开头的**标量**入参用 `mappingType:null` + 顶层 `value:{type:"Simple",simple:"...",desc:"..."}` + `attrs:[]`；DTO 入参才用 `mappingType:"attrs"` + `attrs[{}]` 且 `attrType.id` 必须以 itemType 为前缀。标量入参错配 `attrs` 时抽屉报「参数：值不能为空」，而 `checkSchema` 全绿。
- **事件投递两种模式**：对象引用（`mappingType:"value"`）要求引用节点出参 javaType == 事件 DTO 全名，实体节点引用必然报「所选已变更」；实体字段只能走字段映射（`mappingType:"attrs"`），且 value.selectParam 必须是字段级（javaType=字段 java 类型 + dataType=字段类型 + field/path/position=children）。对象级 selectParam 对 STRING 型 attrType 报「不是文本类型」。
- **GraphQL 变量用平台类型**：`$p: udcMicroflowSearchInputBody` 这类，传 `"Unknown type JSON"` 就是 variables 类型名写错；GET 型 path 接口 id 是 Long 不是 fullName。
- **事件唯一占用**：同一事件只能被一个微流程订阅（「已被其他微流程使用」），且**已占用的事件会从 FilterEventPost 返回中消失**、同参数两次调用返回集可能不同——这是「选择事件」下拉显示空的正常机制，不是数据缺失。
- **`BOOT_1001 Parameter Error` 有两个根因，且都不给明细**（`errorMessage` 为 null，常规错误码定位法失效）：
  1. **`guid` 是猜的**——必须从 `udcMicroflowFindByIdGet` 回读的完整 DTO 里取 DB 真值，`guid != id`，手填 id 当 guid 必报；
  2. **条件右值写成了值槽位的包装形态**。同一个 `0`，在条件里是裸形态 `{type:"CONSTANT", value:0, desc:"0"}`，在值槽位里是 `{type:"Simple", simple:0, desc:0}`。混用 → 1001 且无任何明细。`rightParams[]` 只认 `CONSTANT` / `CONTEXT_VARIABLE` / `EXPRESSION` 三种**裸形态**，不认 `Simple`；`Simple` 只用于节点自身值槽位（`attrs[].value`、`theKey`、`forStart`）。
  定位方法：把节点逐个单独装进最小 schema（endNode/trigger 保持不变）提交，报 `BOOT_1001` 或 `check=false` 的那个就是元凶；`check=true` 的节点可以先排除。

## RETRIEVE 终止提示（未查到=终止 → 必填提示消息）

查询单条 RETRIEVE 节点有两个真实字段名（前端 form 实测，**不是** `nullHandlingMessage`）：

- `nullHandling`：`"TERMINATION"`（终止流程并显示提示，**不是 `TERMINATE`**）/ `"CONTINUE"`（继续执行，自行处理空值判断）
- `nullPromptMessage`：提示文案，`textarea#nullPromptMessage`，仅 `nullHandling=TERMINATION` 时显示（DOM 上带 `ishidden="nullHandling != &quot;TERMINATION&quot;"`），此时为必填。

写错值（如 `TERMINATE`）会让抽屉里「未查到数据时」单选回显为空、提示框不出现，用户看到的就是「终止流程没配提示消息」。

## 实体字段映射（XzhExp950795 实测，含大小写坑）

字段名来自 `udcMicroflowFindDtoByEntityPost`（body `{appId,appName,entityFullName}`）返回的 `content.attributes`（dict，key=字段名）。**注意大小写**：`b1wenbenyanzheng` 是全小写 b（不是 B1wenbenyanzheng），写错大小写会让数据转换/字段映射行显示成 DTO 完整路径而非字段名。业务字段（sourceType=ENTITY）含数字属性 id（customs.id）：
```
id(BIGINTEGER,4308968111076641698) expText(STRING,8016904624316689195)
expNum(INTEGER,5752607439097763430) expFlag(BOOLEAN,5268019261289674045)
expEnum(CTPENUM,2166766729287798468) expDate(DATETIME,7756131932705656129)
b1wenbenyanzheng(STRING,1021739412060058618) b2IntField(INTEGER,7734018642261617786)
```

## RETRIEVE 过滤条件的 leftParam.id 两种形态（别混用）

同一条流程里 `leftParam.id` 存在两种写法：

- **前端编辑后保存的**（`__FORM__.getFieldsValue(true)` 与后端回读一致，**优先沿用这种**）：`id` = `<DtoFullName>.<字段名>`，`dto` = `_<字段名>`，`field` = 字段名。
- **早期 REST 手拼的样本**：`id` = 属性数字 id（如 `4308968111076641698`）。

不要把 `id` 写成裸字段名或去点的 fullName。手拼报「实体属性已删除」时，先看已有原生流程里同位置条件的写法照抄，不要自己猜。

- **CV 的 id/key 可以写成任意标识**，但 `outputName` 必须等于回读后的前序节点输出名。
- 节点必须带 `output`（`{id,javaType,dataType,type,desc,dtoType,udcApp,name,appName}`），漏了 check 报「必填参数未配置」。



## 基础服务类节点（子微流程 / 类型转换）

**子微流程 SUB_MICROFLOW**：`mfService` 必须齐 `id`（目标流程 id）、`name`（流程 name，如 `stdBigMid3004`）、
`path`=`/microflow/{name}`、`appId`、`method=POST`、`triggerType=MANUAL`、`type=SERVICE`、`restType=POST`。
缺 `id` 组装闸门直接拦（`C-SUB_MICROFLOW: 缺 mfService.id`）。
服务清单来源：`udcMicroflowSearchRestExcludeBootPost`，body `{appId, appName}`，按 caption 匹配取
`methodList[0].path` 尾段的方法名。**不要凭界面猜服务名。**

**类型转换 CONVERT_DATA**：用仓库既有 `convert_data(builder, src_node, convert_type, title, caption)`
（内部 `_basic_ref` 生成 selectParam）。
- `convert_type` 只有 5 种：`Split / multiAssociation2List / List2multiAssociation /
  BasicData2String / String2Long`；传裸字符串会让「转换方式」下拉回显空。
- 自己手拼 `selectParam`（尤其 `key` 是空串）会被服务端报
  `selectParam.outputName PROPERTY_IS_REQUIRED`；直接引用节点标量出参就没问题；
  转换的源必须是**字段级或标量**引用，拿整个节点出参硬塞会被拒。
- `mfService.output` 必须写（`{inApp,udcApp,hasPagination,dataType,javaType,type,name,description,required}`）。
  只写 id/name/path 时发布全绿，但一致性检测报 `UDC_MICRO_FLOW_04004 微流程已更改` —— 平台拿这个块
  跟当前服务定义比对，缺了就判「引用已失效」。节点本体还要带 `outPutDesc` + `outputName`（真实 19 键）。

**自定义服务 CALL_APP_SERVICE**：`app` + `selectMethod` 必须**原样取自接口**，按顺序三次调用：
`udcMicroflowSearchAppsPost`（`{appId,needDependency:true}`，11 个应用）→
`udcMicroflowSearchAppServiceByAppNamePost`（`{appId,appName,needDynamicConnector}`，标品如 `organization` 有 25 个服务）→
`udcMicroflowSearchMethodByNamePost`（`{appId,appName,dtoFullName,methodFullName}`，拿 `md5`/`parameter`/`returnValue`）。
- 把接口返回的 `parameter`/`returnValue` 收成最小形态
  `{caption,type,item:{enums:null,itemType,item:null}}`；原样灌进去会让 G6 把展开 DTO 里的
  嵌套字段当成必填参数（报「必填参数未配置」）。
- `builder.build` 给该类节点预置了 `attrs`，里面带死引用（`_CREATE_VARIABLE_xxx`）→ 必领 `node["attrs"]=[]`，
  否则 G10 报「引用的参数已失效」。
- `mappingType` 由入参形态定：标量入参用 `mappingType:null` + 顶层 `value`；DTO 入参才 `attrs`。

**事件投递 PUBLISH_BUSINESS_EVENT（应用内）**：`eventType:"IN_APP"` + **`selectEvent`**（不是 `selectMq`）+
`mappingType:"attrs"` + `attrs`，**没有** `app`/`messageType`。事件对象来源
`udcMicroflowSearchEventListPost`（`{appId,appName}`）；`selectEvent` 取 `{key,label,value,fullName,caption,source,dtoType,udcApp}`。
attrs 是字段级映射（`attrType` 用 `field_attr` 按事件 DTO 属性生成，`value` 可用 `Simple` 常量）。
没有可投递的事件时先到「对象定义 → 应用内事件对象」建一个，别以为节点不可用。

**执行生单规则 CALL_DATA_FLOW**：`structure`(源实体) + `dataFlow` + `condition` + `output`(CallDataFlowResultDto)。
- 规则来源 `udcDataFlowListManuallyMappingPost`，body 必须是 **`{appId, sourceEntity:{relationEntityId}}`**；
  直接传 `sourceEntityId` 返回空数组 —— 会让人误判「应用里没配规则」。
- `dataSourceType:"CONDITION"` 的条件形态未完全验完（手拼条件被 `BOOT_1001` 拒）；
  要快速跑通用 `dataSourceType:"ALL"`（全量）+ `condition:[]`。
- 规则绑定的源实体往往不是你当前实体（规则表是全应用共享），`structure` 必须按规则的 `sourceEntityId` 建。

## ★ 前端绑定类缺陷：后端全绿、只有抽屉里看得见

这三类错误 `checkSchema` 与发布全都不报，但用户打开抽屉就是红字 / 空黄框：

| 现象 | 根因 | 正确形态 |
|---|---|---|
| 创建变量 → 字段映射左侧全列「所选数据已失效，请重新选择」 | `attrs[].attrType` 少了 `refId/relationEntity/relationEntityId/filterRelationEntity`（非关联字段也要空串） | 恒 20 键：`field_attr` 已修，`refApp`/`filterDataType`/`filterType`/`filterFullName`/`dataI18n`/`sort` 也必须在 |
| 更新数据 → 「选择更新的数据」空白黄框 | `selectParam` 缺 `key`；事件来源还写错了 `id`/`position` | 引用变量/循环项：`key=outputName+实体DTO全名`、`relationEntityFullName`��`path`；事件来源：`id=<eventMfCustomDtoName>.info`、`name="info"`、`position="children"`、不带 `relationEntity`/`nodeInfo`（带了判「所选已变更」） |
| 子微流程 → 一致性检测「微流程已更改」 | `mfService` 缺 `output` 块 | 见上方 SUB_MICROFLOW 段 |

这三类已固化成闸门 G24（CHANGE_ENTITY selectParam）/ G25（CREATE_VARIABLE attrType 20 键）。
批量生成后必须跑一次逐节点抽屉探针（`scratch/ui_drawer_probe.py <mid>`）：读
`.ant-select-selection-placeholder`（空下拉）与文本「所选数据已失效」，两项都为 0 才算过。

## 节点命名：出参必须带业务语义

设计器卡片只显示 actionType + 出参 `desc`。多个节点都叫「匹配数量 [整数]」时，
下游选参数根本分不清取哪个。规则：
`caption` = `动作-业务对象`（如「统计-启用数据源数量」），出参 `desc` = 业务名（「启用数据源数量」）。
禁止 `匹配数量 / 结果 / 数量` 这类占位名。

## ★ 被调用流程一改，调用处必须刷新（否则 04004「微流程已更改」）

被调用微流程重新发布后，前端在调用节点里存的是**它自己的属性指纹**。
API 侧把 `mfService` 快照（name/path/output）回写再 `checkSchema/update` 重发**不足以清除**该阻断
（实测：重发成功 errors=0，检测仍报 `UDC_MICRO_FLOW_04004 微流程已更改`）。
必须在抽屉里点「属性已更新，点击刷新」并**重新选择**服务，让前端重写指纹。

生成器侧规则：任何「被调流程变更」都要把引用它的流程标记为不可信，交回 UI 刷新一次，不要假装修好。

## CALL_DATA_FLOW（执行生单规则）必填

契约（1 个真实样本，100%）：`dataFlowMappingId` 是 MUST，且
- `dataFlowMappingId` = 规则列表行 `id`（`udcDataFlowListManuallyMappingPost` 返回的 id）
- `dataFlow.id` = `dataFlowId`（真正的规则 id，不是列表行 id；用错报「生单规则已被删除」）
- `dataSourceType`：`CONDITION`（界面=查询数据）/ `SELECT_PARAM`（界面=选择数据）；
  写 `ALL` 能发布但界面两个单选都是空 → 检查直接阻断
- 服务端另外要求 `outputName`（`PROPERTY_IS_REQUIRED`），但在样本节点里没有该键，
  位置尚未确定；遇到时以 UI 保存一次后的回读形态为准。
