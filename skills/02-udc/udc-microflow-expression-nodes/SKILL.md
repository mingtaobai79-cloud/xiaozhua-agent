---
name: udc-microflow-expression-nodes
category: devops
description: Use when 给 UDC 微流程节点写点表达式/分支条件/子微流程传参或落库丢失时.
---

# UDC 微流程点表达式写链（全部 LIVE PASS，test2 5.3.517）

## ★ 三条路线：UI 驱动 / 接口校验 / 手拼 JSON

| 路线 | 何时用 | 关键约束 |
|---|---|---|
| UI 驱动（CDP 点前端） | 要在真实编辑器里验证渲染（变量树能否插入、面板是否红字） | 三道门禁 + 末尾暂存草稿，见下 |
| **接口校验（`/check` + `/transform`）** | **判表达式对不对、批量查、生成 `executableExpr`** | 见下「表达式可完全走接口校验」 |
| 手拼 JSON 直接 POST | 批量造流程、生成器 | 下文闸门 + 表达式形制 |
| **批量值槽位表达式化** | **「每个节点的每个值都要用上表达式」** | 执行顺序 + 系统变量 + 15 值域，见 `references/expression-bulk-fill.md` |

### ★ 写数据必须走 UI 确认链，不能直接改 dataSchema 落库

用户明确要求：**填完就点「确定」，并抓后台校验接口；不抓就等于没存上、没记录**。
批量走 GraphQL 直写 `dataSchema` 虽然能让 `/check` 全绿、后端回读也对，但它绕过了
前端的控件绑定与回显。实测后果：值槽位被改成 `Expression` 后，节点抽屉里这些必填项
**显示为空**（控件不会渲染 Expression 回显），于是「数据在库里、面板是空的」。

所以：

- 需要改**节点值字段**（attrs / entries / forStart / theKey / attrError 这类）时，走 UI：
  开抽屉 → 填值 → 点「确定」→ 点「暂存草稿」→ 后端回读。
- 只在**批量生成/造流程**且不关心面板回显时才用直写 `dataSchema`，并在交付时声明这一点。
- 不要用「`/check` 全绿 + 后端回读 `type=="Expression"`」当作 UI 可用——这两个判据都看不见面板。
- 用户明确要求「一个一个点」时，**批量直写不能替代**：每个节点都要有一条对应的
  `udcMicroflowUpdatePost` 抓包才算做过，事后补一次全量 POST 不满足。做完先回滚再重做，
  比在被污染的状态上继续点更省时间。

**UI 自动化必须单进程独占同一个 CDP target**：另有一个脚本（抓包/巡检/后台遗留进程）
同时在驱动这个页面时，抽屉会被对端反复关掉，表现为「卡片定位正确、抽屉偶尔开偶尔不开」，
且两次 dump 出来的字段数不同。开工前先确认没有别的东西在操作该浏览器，
不要把这个现象误判成「元素被遮挡」或「点击方式不对」。

### ★ 表达式弹窗的「验证」才是后端校验入口；空表达式不发请求

表达式设置弹窗的 `验证` = `POST /service/udc/expression/check`，code 非 0 时弹窗内红字回显 `message`
（例：`计算结果为: 整数 类型, 无法赋值给: 日期时间 类型` = `FORMULA_6901`）。
**编辑器为空时点验证不发任何请求**（前端先拦），抓到 0 请求先确认编辑区真有内容，别判成按钮失效。
弹窗内按钮按文案找 `button` 再原生 `b.click()`；用 CDP 坐标点会命中同一行的 `.btns` 工具栏 div，静默无效。

### ★ 开得出表达式弹窗 ≠ 该字段存得下表达式

值字段带 `+` 只说明「可以选值」，不代表控件支持表达式绑定。`CREATE_VARIABLE.默认值`
（`dataType=DATETIME`，渲染成 `ant-picker`）能完整走通 `+ → 高级模式 → 表达式设置 → 验证 → 确定`，
但保存后后端 `value` 仍是 `null`。

所以**批量前必须先做单字段闭环**，唯一判据：

```
改一个值字段 → 节点抽屉确定 → 暂存草稿 → findById 回读该字段 value 非 null 且 type=="Expression"
```

闭环不过就是该类控件不吃表达式，换字段或换做法；**没有成功样本之前不许批量刷**。
同一抽屉的字段数随状态变化（3 / 4 / 9 个都出现过），每次都重新 dump，不要复用上一次的索引。

### 这类改动卡住时的处置顺序

按顺序走，不要在原地换姿势重试：

1. 先盘清「哪些字段真能写表达式」——逐节点开抽屉 dump（标签 / 必填 / 控件类型 / 有无 `+` / 有无红字），
   拿到清单再动手；不要凭字段名或 `Simple→Expression` 的可替换性推断。
2. 取一个用户已经手填成功的节点/字段复刻，比自创路径快得多。
3. 两条都不通就要目标清单或样本位置，**不要继续盲试**：盲试既不产出证据，还会把已污染的数据搅得更乱。

### 前置：视口宽度决定 UI 路线能不能用

开抽屉前先读 `innerWidth`。抽屉宽 680px，**`innerWidth < 抽屉宽度 + 画布最小宽` 时
抽屉整体落在 x=innerWidth 之外**（`aside.getBoundingClientRect().x` 等于视口宽），
此时 `elementFromPoint` 返回 null、所有点击静默失败、`ant-drawer-content-wrapper`
的 transform 永远停在 `matrix(1,0,0,1,680,0)`（进入动画未完成）。

```python
vp = json.loads(d.eval("JSON.stringify({w:innerWidth,h:innerHeight})"))
# 实测：1088 不可用；1680 可用（aside x=1000, w=680，完整在视口内）
```

窗口本身是 `windowState:normal` 但 `innerWidth` 仍很小时，说明是窗口尺寸而非最小化问题，
用 `Browser.setWindowBounds` 调大后重读，不要靠改 CSS transform 硬拉。

**卡片点击必须保证目标真在视口内**：横向滚动容器要滚到卡片落入
`0 < cx < innerWidth && 0 < cy < innerHeight`，否则 CDP `click_mouse` 打在空白处。
CDP 的 `Input.dispatchMouseEvent` 用 **CSS 像素**，DPR 不为 1 时也不要乘系数。

**卡片定位、抽屉字段读取、保存链路抓包、重载编辑器、面板空值判读见
`references/ui-editor-operations.md`。**

**别把「某个端点不可用」推广成「整组接口不可用」**：`/expression/schema` 对 `paramType=MICROFLOW`
返回 `BOOT_3000`（该域未注册 `ParamLoadService`），但这**只影响取变量面**。`/check` 与 `/transform`
只吃 `schemas`，不吃 `paramType`，微流程完全能用 —— 前端也从不调 `/schema`，它自己拼 `schemas`。
遇到某端点报「未注册/不支持」时，先查前端实际调的是哪几个端点，再下结论。

## ★ 表达式可完全走接口校验（不依赖 UI，可批量）

`POST /service/udc/expression/check` → `BOOT_0000` 且 `data.content === true`；
`POST /service/udc/expression/transform` → `BOOT_0000`，回 `designData` + `runtimeData.executableExpr`。

`ExpressionSaveDto` 的 `schemas` 直接由表达式自带的 `designData.context` 转成，**唯一差异是每层加 `skip:true`**
（`pageNodeExtension: null` 保留）。`executableExpr` 前缀（`93gDaq3/...`）是**服务端固定产物、不是逐次签名**——
对已落库表达式调 `/transform`，产物与库中值逐字节相同，所以可离线生成，不必过 UI。

完整契约、`context→schemas` 转换函数、四档判据与 `verify_expression` 流水线见
`references/expression-api-validation.md`。

**UI 路线三道门禁，任一不过都是静默失败（画布看着正常，库里没东西）**：

1. `document.hidden` 必须 false。页面被遮挡时下拉坐标 -9999、抽屉底部按钮**根本不渲染**、
   `contenteditable` 拿不到焦点。用 `d.cmd("Emulation.setFocusEmulationEnabled", enabled=True)`
   一行解决；`Page.bringToFront` / 激活 tab / 置顶窗口都不稳定。
2. `microflowEditorReducer.readonly` 必须 false。`flowBasicInfo.state=="RELEASE"` ⇒ 只读：
   UI 编辑照常生效、节点抽屉照常确认，但什么都写不进库，唯一提示是进页面时那个
   「您现在处于查看模式」modal（点掉后 DOM 里再无标记）。
   **`readonly` 多半是自己造成的**：点顶栏「保存并提交」(`id=microflow_save`) 就是把流程
   发成 RELEASE，保存完立刻自锁。恢复要「编辑」+ `location.reload()`，且 **frame 重载后 nodeId 全变**。
   见下面「存草稿，不要发版」——用对按钮这个门禁基本不会再触发。
3. 提交抽屉：`el.click()` 对 React 按钮是**静默失败**（不报错、store 不动），必须直调
   `__reactProps$` 上的 `onClick`。`onClick` 撞 antd `outOfDate` 竞态时再用 Enter 三连兜底
   （表单最后个输入框发 `keyDown/char/keyUp` 带 `\r`）。成功标志是立刻出现 `udcMicroflowUpdatePost`。

变量树/函数树插入、函数参数位填充、校验消息判读、`executableExpr` 两种拼接形态、
逐节点回读验收见 `references/expression-editor-ui-driving.md`。

## ★ 存草稿，不要发版：三层数据 + 三个保存按钮

表达式/节点配置在编辑器里存在**三层**，只会自动同步前一层：

| 层 | 位置 | 何时更新 |
|---|---|---|
| L1 | `store.flowNodes[<nodeId>].expression` / `.attrs` | 抽屉点「确定」立即更新 |
| L2 | `store.oldFlowSchema.flowNodes[<nodeId>]` | 加载/保存时 |
| L3 | 后端 `dataSchema` | 节点抽屉「确定」即时写；**画布内联配置（分支表达式/出入参/首节点）只认「暂存草稿」** |

**点「确定」写 L1；画布内联配置（分支条件表达式、出入参、首节点）到此为止，不会再往 L3 走。**

**不要假定节点抽屉的「确定」会落库。** 实测 `CONVERT_DATA` 节点抽屉点「确定」后是
**0 个网络请求**（只写 store，`flowChanged` 仍为 true）；其他节点个别情况会顺带发
`udcMicroflowUpdatePost`。判定只看一件事：点完有没有抓到 `udcMicroflowUpdatePost`。
没抓到就说明这层没落库，一律靠末尾「暂存草稿」。
无论哪种，收工前都要点一次「暂存草稿」并回读后端确认，不要按类型猜测哪条链要保存。

验收第一件事：读 `flowChanged`，再对比 L1 与 L3 的 `expression.title` / `attrs` 长度。
只看到 `flowChanged=true` 不能说明任何一层已落库。

顶栏两个按钮语义完全不同，选错就得重做一轮：

| 按钮 | 语义 | 后果 |
|---|---|---|
| `暂存草稿` | 只存不发布 | `state=DRAFT` / `publish=UNPUBLISH` / `readonly=false`。**默认用这个** |
| `保存并提交`（`id=microflow_save`） | 存 + 发版 | `state=RELEASE` / `readonly=true`，之后所有节点操作失效 |

节点抽屉「确定」**不保证**即时落库（见上表「三层」），**画布内联的表达式配置更是只靠流程级保存**。
所以别把「改了几个节点都没事」推广到表达式：表达式必须末尾单独走一次「暂存草稿」。
误点 `microflow_save` 的恢复：点顶栏「编辑」→ **再 `location.reload()`**；
只点「编辑」不 reload，残留 `aside.udc-microflow-editor-node-settings` 会让抽屉再也打不开。

## ★ 审计必须先认表达式：`expression` 是对象不是字符串

`expression` 形如 `{title, schema}`，`schema` 是含 `designData`/`runtimeData` 的 JSON **字符串**。
按字段名扫 `outputName`/`name` 这类字符串的体检脚本会**整层跳过表达式**，然后给出
「全部健康」的假绿——这是本项目审计返工的头号原因。判定用特征：`isinstance(dict) and "schema" in obj and ("designData" in schema or "expressionTranslation" in schema)`。

每层都要查，别只查一层：

| 层 | 查什么 | 典型错 |
|---|---|---|
| 节点字段 | `SAVE_REQUIRED_FIELDS` / `SAVE_CONDITIONAL_FIELDS` | 空白字符（`'\n\n'` 为 truthy，前端放行、运行时弹空白框）|
| paramType | 8 值域 + 每类的联动必填 | 只记了 5 类，漏 METADATA/MESSAGE/OTHER |
| 表达式 tokens | 变量根 ∈ 流程 `output.name`；左右不同源 | 悬空旧名 + `x > x` 恒等式 |
| 引用 | `selectParam`/`attrs` 指向的出参真实存在 | 整节点克隆带进别人的变量 |

**悬空判定**：`tokens[].value` 第一段去比对本流程所有 `output.name`。节点删后重建会保留
`nodeId` 但换 `output.name`，表达式里的旧名不会跟着变 → 报「变量 X 在上下文中不存在」。
**恒等式判定**：两个 VARIABLE token 的 `value` 相同（`x > x` 永假）——校验能过、不报错、分支永远进不去，最难发现。

静态审计只能抓「语义明显错」，**类型/结构不合法它抓不到**。收工前再对每条表达式跑一次
`/expression/check` + `/transform`（见 `references/expression-api-validation.md`）——
`content:true` 才代表真过。两者互补，只跑一个方向会在实战里漏掉真错。

判定表**引用 `components/udc/microflow_constraints.py` 的权威定义**（`SAVE_REQUIRED_FIELDS` /
`SAVE_CONDITIONAL_FIELDS` / `MAP_PARAM_TYPES` / `PARAM_TYPE_REQUIRED_FIELDS`）。
在审计脚本里另写一份「我觉得必填」的表会成片产假阳性——如 `RETRIEVE_ARRAY` 用 `variableTitle`
不是 `title`、`CALL_APP_SERVICE` 的 `title` 非必填、`DATA_MAPPING` 用 `selectParam` 不是 `dataSource`。

## ★ 先选对节点类型：数据活动 / 数据加工 / 基础服务

写节点前先按语义选域，选错域参数映射永远配不对（面板出参显示「未命名的参数 / 长整数」）：

| 域 | actionType | 用途 |
|---|---|---|
| 数据活动 | CREATE_ENTITY / CHANGE_ENTITY / DELETE_ENTITY / CREATE_BATCH_ENTITY / RETRIEVE / RETRIEVE_ARRAY | 应用内实体 CRUD。**建档写库只用这里** |
| 数据加工 | CONVERT_DATA / DATA_MAPPING | 类型转换、字段映射 |
| 基础服务 | CALL_APP_SERVICE / SUB_MICROFLOW / CALL_DATA_FLOW / EVENT_DISPATCH | 自定义服务 = 对外开放的 dubbo 接口 / 基础组件接口 |

用 `XxxAppService.create` 干建档是错的：面板能选中，但入参 DTO 与出参契约对不上。
建流程/节点一律用仓库里的声明式生成器（`components/udc/microflow/build.py` +
`components/udc/microflow_constraints.py`），**不要从库里扒一条真实微流程当模板克隆**——
样本会把别人的语义带进来，且样本一删就失去依据。生成器契约、`all_nodes_demo` 调用方式、
`required_fields` 实测清单见 `references/microflow-schema-generator.md`。
就地替换既有节点时改 `actionType` 并**保留 nodeId**（拓扑按 id 关联，换 id 断链）。
CREATE_ENTITY 形制要点：`structure.entityId`/`relationEntity`=实体 id（字符串）、
`output.name=_CREATE_ENTITY_<nodeId 尾段>`、`output.id=<app>.dto.<Cap>Dto`、
`attrs[].attrType.customs.id`=udc_attribute.id（校验查这个）、`mappingType="attrs"`。

### 引用类型必须配对（UI 检查 04004 的一大半来自这里）

平台校验会逐节点核对「引用的对象类型 vs 节点要求的类型」，错配报 `UDC_MICRO_FLOW_04004`：

| 节点 | 可接 | 接错的报错 |
|---|---|---|
| CREATE_ENTITY | 单个实体对象变量（DTO OBJECT） | `[新增数据]:对象类型不匹配(vText)` |
| CREATE_BATCH_ENTITY | 实体对象列表（DTO ARRAY） | `[批量新增]:不是根实体对象(vRows)` |
| CHANGE_LIST | 只收**基础类型**列表（STRING 等） | `[修改变量(列表)]:不是文本类型(<实体>列表)` |

推论：字符串列表与实体列表是两个不同的变量，别复用同一个 `CREATE_LIST`；
推广到跨域引用一律按“类型 + 单条/多条”两个维度配对，别只看名字像。

### 整节点克隆的传染性

把别人流程里的 `CALL_APP_SERVICE` 整节点搬过来，`attrs` 里引用的 `caseId` / `事项id` / `本部实体` 是**源流程的变量**，
在本流程不存在 → UI 检查逐条报 `[自定义服务跨应用(x)]:前序节点发生变更请重新选择(<字段名>)`。
只有 `selectMethod`（含 `returnValue`/`parameter`）与 `output`（必须带 `id`，否则 checkSchema 报
`output.id PROPERTY_IS_REQUIRED`）可以从真实契约复制；`attrs` 必须按本流程上下文逐条重绑。


### 分页查询（RETRIEVE_ARRAY）的参数形态

分页不是给个 `size` 就完了：平台把分页参数当成**一个自定义对象**传给查询节点。

```jsonc
// 节点侧
"pageSearch": "true",
"pageInfo": {"type":"SelectParam","selectParam":{
  "outputName":"<CREATE_VARIABLE_xxx>",           // 指向一个建该对象的 CREATE_VARIABLE 节点
  "id":"com.seeyon.boot.transport.PageInfo",       // 分页参数 DTO（dtoType=CUSTOM, udcApp=true）
  "javaType":"com.seeyon.boot.transport.PageInfo",
  "name":"comseeyonboottransportPageInfo","position":"parent","description":"分页参数对象"}}
```

顺序必须是「先 `CREATE_VARIABLE`(PageInfo 自定义对象) → 再 `RETRIEVE_ARRAY(pageSearch=true, pageInfo=该变量)`」，
`pageInfo=null` 时节点只返回单页，翻页逻辑无从谈起。分页 + “算页数 → 外层 FOR 遍历页 → 内层 FOR 遍历行”
的嵌套写法见 `references/microflow-generation-gates.md`。

## ★ 生成即正确：闸门先于生成，绝不生成完再补

**节点形制只能来自前端「添加 → 确认」后的快照，不能手拼 JSON**：前端会回填 `nodeConfig`（`description`/`foreach`/`isCompleted`）、
给实体字段下发带 `md5` 的 `attrType`、并由 `ExpressionComponent` 生成右值。整包 POST `dataSchema` 绕过这三步，
结果就是「所选‘数据’已变更」「请选择」「分支面板空白」「节点开发中…」。取模板与逐节点验收见
`references/microflow-node-authoring.md`；每类节点模板存 `fixtures/microflow/node_templates/<ACTION>.json`，生成器只换引用与右值。

**纪律**：不允许“先生成、再拿脚本修”。每踩到一个平台报错，就把它变成构造期的可判定规则；
规则不过就不生成、不提交。**批量之前必须先单条跑到 UI 零异常**：一条流程逐节点点开无红字、发布后
`state=RELEASE`，才允许扩到 N 条；同一业务做多个变体只允许改过滤条件/分支走向/实体，
节点组合与取值必须真的不同 —— 拷贝出来的变体会被判定为空壳直接打回。分支条件写死 `true`、
循环边界写死常量、修改变量不赋值、循环体 `nodes` 空、列表循环用计数循环(fori)顶替该用的 foreach、参数映射 `attrs` 空或不引用前序出参，同样算空壳。仓库落点 `components/udc/microflow/gates.py::run_gates(schema, dep_apps=..., app_name=...)`，
返回问题清单（空列表才算过），必须在 `build_schema` 之后、提交之前调用。

| 闸门 | 拦的报错 | 判定 |
|---|---|---|
| G1 表达式段/token 数不等 | `04000 ArrayList.rangeCheck` | **先剥节点显示名 `名称(1).`**，再按 `2*运算符数+1` 计段（`a+b`=3）；含括号（函数调用）口径未证实，闸门直接拒收 |
| G2 悬空引用 | `04004 前序节点发生变更请重新选择` | 每个 `SelectParam.outputName` 必须命中本流程某节点 `output.name` 或 `_FLOW_INPUT_*` |
| G3 类型错配 | `不是根实体对象` / `不是文本类型` / `对象类型不匹配` | CREATE_ENTITY/批量只收 DTO；CHANGE_LIST 只收基础类型列表 |
| G4 数据映射缺名 | 提交门禁 `mappingRule 缺 'name'` | `mappingRule.name/caption` 必写 |
| G5 依赖未声明 | `依赖应用已删除` | 跨应用 `app.appName` 必须在 `udc_dependent_application` 里或 `inApp=true` |
| G6 服务参数不属于契约 | `必填参数未配置` | `attrs[].attrType.id` 必须以 `selectMethod.parameter.item.itemType` 为前缀 |
| G7 分页缺 pageInfo | `propertyKey=pageInfo, PROPERTY_IS_REQUIRED` | `pageSearch=true` ⇒ `pageInfo` 必须指向 PageInfo 自定义对象变量，`null` 一律拦下 |
| G8 引用顺序错 | 同样报 `04004 前序节点发生变更请重新选择`（G2 拦不住） | 引用只能指向**它前面**已出现的节点出参；分页变量建在 `RETRIEVE_ARRAY` 之后就属此类 |

构造顺序固定为：先声明上下文（`input` / 变量 / PageInfo）并收集全部 `output.name` → 再建引用型节点，
一切 `SelectParam` 从已收集的集合里取（禁止手写名字）→ 表达式按段生成 token → 跨应用先加依赖再按 `itemType` 生成 attrs →
`run_gates` 返回空才提交。**字段赋值/值编辑器选项跟随前序节点出参的实体类型（元数据重载），节点必须按顺序生成、
从它引用的实体取字段，不能整包并行写、不能拿别的实体字段硬填**。节点全量 24 类、每类弹窗必填契约、分页对象创建路径见
`references/microflow-node-authoring.md` §7–8。批量造流程（多业务 × 多变体）时同样跑这条链，并把闸门结果写进交付目录的索引表。
详见 `references/microflow-generation-gates.md`。

### 定义驱动：字段 md5 从接口抓，不手写、不靠前端快照

字段定义（attributes 含 md5/id/fullName/dataType/javaType）有比前端快照更稳的来源：
**直接调接口抓，落定义库，生成器从定义库取**。脚本 `scripts/harvest_definitions.py`
（CDP 页面内 fetch + `credentials:'include'`，连 target 与 query 格式坑见 udc-trace-to-api）抓四类：

- 实体 attributes → `udcMicroflowFindCustomDtoPost`（`dtoFullName` → `attributes` 是 dict，key=字段名，值含 md5/id/fullName/javaType/dataType）
- 服务参数 → `udcMicroflowSearchMethodByNamePost`（`methodFullName` → parameter/returnValue 递归 + 方法 md5）
- 枚举/枚举项 → `udcMicroflowSearchEnumByAppNamePost` + `udcMetaDataSelectJavaEnumItemPost`
- 事件 → `udcMicroflowSearchEventListPost`（应用内）/ `udcMicroflowSearchSendMqListPost`（应用间 MQ）

落 `definitions/entities/<Dto>.json` 等。生成器只做三类替换（实体引用/字段引用/表达式），字段一律从定义库取 md5，
**绝不手写 id/md5**（手写 = 引用失效 + 前端渲染空 + state 静默 DRAFT）。
端到端验收（3 节点最小流程活样例 `scripts/gen_min.py` + `scripts/verify_min.py`）：
`create → checkSchema errors=0 → 读回 state=RELEASE` 才算生成即正确，缺一步都不是。

**发布是静默的，读回只走接口**：`POST /udc/microflow/update` 传 `state=20` 常返回 `BOOT_0000 SUCCESS`
但流程仍停在 `DRAFT`（深度校验失败不报错，只降级保存）。判断发布成功只能 `GET /service/udc/microflow/findById/{id}`
读 `state`（仓库 `components/udc/microflow/read.py::find_service/state_of/is_release`）；
不要给提交脚本加 `--db-env` 回读——DB 只是取证便利，客户环境通常没有 DB 权限，也不是平台契约。

## ★ `UDC_CE_MICRO_FLOW_04000 未知异常 ArrayList.rangeCheck`

栈：`MicroFlowComponentUtils.checkExpressionNode:1716 → ArrayList.get → checkAttrValue:357 →
checkSelectObjectAttrs:695/775 → CreateEntityActivity.activityNodeLogicCheck:109`。

根因：手写 Expression 的 `tokens` 段数与 `expressionTranslation` 解析出的段数不一致，校验器按段索引取 token 越界。
**第二个根因（修改变量 CHANGE_VARIABLE 也报 04000，栈尾是 `ChangeVariableActivity.activityNodeLogicCheck`）**：
表达式 `context[]` 里的**基本变量（非 DTO 变量）必须扁平一层**，即 `{"name":"_CREATE_VARIABLE_x","description":"vX","type":"STRING","selectable":true,"enableDataI18n":false}`，
**不要**套成 OBJECT+properties 两层嵌套。
精确机制（反编译 `MicroFlowComponentUtils.checkExpressionNode` 证实，越界点在 `list.get(1)`）：
每个 VARIABLE token 解析成一个 `resultList` 条目——DTO 字段条目有 2 个元素 `[字段, DTO信息]`，
基本变量条目只有 1 个 `[变量]`（无 DTO 层）；校验器对 `isInApp(attrName)==true` 的条目执行 `list.get(1)` 取 DTO 信息，
基本变量条目 size==1 就 `ArrayList.get` 越界。
推论：**表达式操作数尽量用前序 DTO 字段（实体字段），不要拿基本变量去拼**——基本变量作操作数其 resultList 条目无 DTO 层，
配合 isInApp 判定直接越界；能用 `SelectParam` 引用前序出参就先引用。
DTO 字段才用三级（节点出参 OBJECT → DTO OBJECT → 字段），普通变量与 DTO 字段的 context 层级不同。
基本变量 token 的 `value` 直接写 outputName（`_CREATE_VARIABLE_x`），不是 `_节点id._节点id` 三段式（那是 DTO 字段的写法）。
**处置顺序**：① 该字段能用 `SelectParam` 引用前序出参就先用引用（改完 04000 立即消失）；
② 必须写表达式时，tokens 段数严格对齐翻译段数；③ 布尔字段不要用 Expression 写 `true`
（报「计算结果为 文本 类型，无法赋值给 布尔 类型」），用 `{"type":"Simple","simple":true}`。

## ★ 跨应用「自定义服务」节点必须先有应用依赖

节点里 `app.inApp=false` 只表示“不属本应用”，**不等于依赖已声明**。平台校验 `UDC_MICRO_FLOW_04004 依赖应用已删除`
指的是 `udc_dependent_application` 里没有这条依赖记录，不是节点 JSON 写错。写节点前先查：

```sql
SELECT dep_app_name, dep_app_caption, dep_app_version, source_type
FROM udc_dependent_application WHERE app_id=<appId>;
```

`source_type=1` 是平台应用（`dep_app_name` 如 `organization`、`bpm`），`source_type=2` 是组件包；UDC 应用按应用名
（如 `<app名><id>`）。节点 `app` 块：UDC 目标应用给 `{appId:"<目标appId>", appName, caption, inApp:false, udcApp:true}`；
平台应用给 `{appId:null, appName:"organization", caption:"组织模型", inApp:false, udcApp:false}`。
依赖缺失时两条路：界面「应用设置-依赖」加（走发布链），或把节点换成本应用/已依赖应用的基础组件接口。

**选服务的完整链路（不是一步到位）**：`udcMicroflowSearchAppsPost`（body 带 `needBootStarter/needConnectorApp/needDependency=true` 才返回完整应用列表）→ `udcMicroflowSearchAppServiceByAppNamePost`（body 带 `appId+appName+needDynamicConnector`）→ `udcMicroflowSearchMethodByNamePost`（`methodFullName` 拿 parameter/returnValue/md5 完整契约）。
本应用自建 AppService 在 SearchAppServiceByAppNamePost 里 **methods 全 null**（应用级类条），必须用 SearchMethodByNamePost 另行按类取方法；只有平台级「容器条」（`FileAppService`/`FormServiceProxy`）才直接带 `methods[]`。
**优先用本应用自建服务**（如 `XxxAppServiceImpl.selectById`）：平台级服务（FileAppService.copy 等）依赖的 starter 应用（boot-starter-file）可能在依赖列表里已被删，检测报「依赖应用已删除」——不是节点 JSON 写错。

## Expression 落库形态（attr / 分支条件通用）

```jsonc
{"type":"Expression","expression":{"title":"{<翻译>}","schema":"<JSON 字符串>"}}
// schema = {"designData":{expressionTranslation,resultTypeInfo,resultTypeFullName:null,
//   terminalType:"BACKEND",isMultiSelect:false,context:[...],tokens:[...],sourceAppName:null},
//  "runtimeData":{"executableExpr":"93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=<token value 平铺拼接>"}}
```

- token 值域恰 5 个：CONSTANT/VARIABLE/SYSTEM/FUNCTION/OPERATOR（写 SYSTEM_VARIABLE ⇒ BOOT_3000）。
- VARIABLE 点取路径格式：`节点输出名.节点输出名.属性名`（三段，outputName 重复两遍）。
- 字符串拼接用平铺 tokens：VARIABLE + OPERATOR"+" + SYSTEM（`concat` 函数名不存在，BOOT_3000）。
- 已验证函数：`roundOff`（subOps=[[token]] 双层数组）。已验证系统变量：`system.currentDateTime`(DATETIME)/`currentUserName`/`currentUserId`。
- **`+` 运算要求两侧类型兼容**：STRING + DATETIME（`system.currentDateTime`）报「操作符类型不匹配」(`UDC_MICRO_FLOW_04004`)，
  要用 STRING + STRING（两个文本字段拼接，或同类型组合）才对。别拿某条「已保存但 state=DRAFT 未检测」的样本流程当「合法」依据——
  未保存/未发布流程的节点不参与应用检测，它的表达式类型错误根本不会被报出来，照抄它的 `文本字段+当前时间` 到正式流程就炸。
- resultTypeInfo 用 DataType 枚举名：DATETIME 不是 DATE_TIME（FORMULA_6003）。
- **`resultTypeInfo` 只有 15 个合法值**：`INTEGER BIGINTEGER DECIMAL STRING MULTILINESTRING
  DATETIME DATE TIME BOOLEAN CURRENCY ATTACHMENT ARRAY ENTITY CTPENUM ENUM`。
  `OBJECT` **不在值域** → `FORMULA_6003`。DTO 场景用 `ENTITY` 且**必须带 `resultTypeFullName`**
  （取该 DTO 变量的 `output.id`，不是变量名），缺则 `FORMULA_6901`。
- **后端类型名必须归一化再比对**：`String`（小写 s）≡ `STRING`、`Long` ≡ `BIGINTEGER`、
  `Object`/`Dto` ≡ `DTO`。按 `STRING` 去比 `String` 会漏配，一处漏配就成片误判成「无可用变量」。
- **系统变量 token 是 `SYSTEM` 不是 `VARIABLE`**，`schemas` 可为空，值用全名 `system.currentUserName`；
  它**不占执行顺序位**——任何节点位置都能引用，是「前面没有合适类型变量」时的唯一出路。
- 校验端点：`udcExpressionCheckPost`（body=ExpressionSaveDto：resultTypeInfo/schemas/tokens/isMultiSelect/terminalSupportType/sourceAppName），先 check 后落库。

## ★ 「应用元数据处理类[MicroFlowMetaDataPostProcessor]执行异常: null」——真根因

手写 Expression 的 `designData.context[]` **必须带 `uniformityParams`**（真实 UI 生成的每条 context 都有）。
缺它时链路：`MicroFlowParser.addNodeDependency` → `RelationshipResolverUtil.findReferencedNodeInfoSet`
→ `ExpressionReferenceDataResolver.convertExpressionSchema` →
`structureDto.getUniformityParams().getExtensionProperties()` **NPE**，整个应用检测 FAIL。

正确 context 形态（三级，逐字照真实样本）：

```jsonc
// 一级：节点出参（OBJECT, selectable:false）
{"name":"_RETRIEVE_x","description":"查询单条数据(1)","type":"OBJECT","selectable":false,"enableDataI18n":false,
 "properties":[{ /* 二级 */ }],
 "uniformityParams":{"paramId":"<DTO>","paramCategory":"DTO",
   "extensionProperties":"{\"id\":\"<DTO>\",\"javaType\":\"<DTO>\"}","pageNodeExtension":null}}
// 二级：可选的 DTO 对象（OBJECT, selectable:true）uniformityParams paramCategory="OBJECT" extensionProperties {"id":"<DTO>"}
// 三级：字段（STRING/BIGINTEGER…）uniformityParams paramId="<DTO>.<字段>" paramCategory=<同 type>
//   extensionProperties="{\"id\":\"<DTO>.字段\",\"relationType\":\"NONE\",\"javaType\":\"java.lang.X\"}"
// 普通变量（非 DTO）：两级同型，uniformityParams {"paramId":"","paramCategory":"<type>","extensionProperties":""}
```

注意：`extensionProperties` 是 **JSON 字符串**（内层再转义）。

### 取真实栈（NPE 无栈时）

JIT fast-throw 会让重复 NPE 只打 `java.lang.NullPointerException: null` 无帧。去 udc pod
`/var/log/webapps/udc/udc-error.log` 找**最早**几条（JIT 编译前），`grep -n "autocode.metadata.config.MicroFlowMetaDataPostProcessor"`
即可拿到完整帧；按帧定位到具体 getter，不要凭猜。

字段消失先分两层排查，不要一上来就二分 JSON：
① **UI 侧 readonly**（见开头门禁 2）——只读态下 `udcMicroflowUpdatePost` 根本不会发，自然什么都消失；
② 排除① 后才是反序列化，按下文逐项二分。

`udcMicroflowUpdatePost` BOOT_0000 但 Expression/attrs 消失 = 后端反序列化失败丢弃该字段。已证实的坑：
- attrType 里**多余的键本身不致命**（T1 用含全部真实键+Simple 过了）。
- **全量提交的前提是「全量回传」**：`read_schema_page` 只给 `{id, dataSchema}`，直接当提交体会报
  `BOOT_1001 微流程名称所属应用ID 不能为null`。提交前必须再 `udcMicroflowFindByIdGet` 取全量 DTO
  （实测 34 字段），改 `dataSchema` 后整体回传。GraphQL 变量名是 **`body`**，不是仓库 `gql_page()`
  硬编码的 `p`——签名是 `update(body: $body)`。
- 稳妥路径：先 update 一版全 Simple 的 attrs（拿到 attrType 键集被接受的基线），再逐个把 value 换成
  Expression，每次 update 后回读确认。批量做法（含执行顺序、系统变量、15 值域、结构自检与六档验收）
  见 `references/expression-bulk-fill.md`。

## ★ 微流程类型 × 触发方式（创建 body 的两组正交字段，不是节点层面）

`type` 与 `triggerType` 是两个独立枚举，组合成 6 类微流程（标准/自定义 × 服务定义/事件监听/定时任务）。反编译 `MicroFlowTypeEnum` / `MicroFlowTriggerTypeEnum`（cfr-r31）：

| 字段 | 枚举 | 值 |
|---|---|---|
| `type` | MicroFlowTypeEnum | SERVICE(0 标准，有节点) / CUSTOM(3 自定义，**无节点**只有开始/结束+出入参) / FRONTEND / ENTITY_RULE / FUNCTION |
| `triggerType` | MicroFlowTriggerTypeEnum | MANUAL(2 服务定义，可有出入参) / BUSINESS_EVENT(0 事件监听，无出入参) / SCHEDULE(1 定时任务，无出入参) / FRONTEND_PARAM |

- 自定义微流程（CUSTOM）独有 `serviceInterface`（所属接口=业务分类名，如 MigrationService），`name`(编码)即方法名；标准微流程无此字段。
- trigger 节点的 `type` 字段 = triggerType 的字符串值（MANUAL/BUSINESS_EVENT/SCHEDULE），**不是节点的 type**（parse 时由 `determiner.getTriggerType().name()` 回填）。
- 事件监听/定时任务**无出入参**：trigger/endNode 不设 BASIC/ENTITY_OBJECT/DEFAULT_OBJECT，paramType 走 NONE。

### 事件监听 trigger 结构（triggerType=BUSINESS_EVENT）

trigger 节点 = 基类字段（id/nodeId=MFStartNode/caption/description/type/input/output）+ 子类字段（反编译 `BusinessEventTrigger`）：
- `messageInfo`：`messageSource`(EVENT/MESSAGE/CONNECTOR/MICRO_FLOW_EVENT) + `eventName` + `eventDataFullName` + `caption`；EVENT 源额外 `eventFullName` + `eventMfCustomDtoName`，MESSAGE 源额外 `topic`，CONNECTOR 源额外 `connectorMessageInfo`。
- `expression`：触发条件（过滤，可选，不一定全收）。

事件列表接口用 `udcMicroflowFilterEventPost`（不是 udcDataFlowListEventsPost，后者只返回 3 种事件）：
body `{appId, sourceTypes:["ENTITY"|"MICRO_FLOW_EVENT"], eventTypes:["ENTITY_EVENT"], entityId:<实体id或0>, id:<微流程id或0>}`，
直接返回每事件的 `name`(事件名)/`caption`/`sourceId`(来源实体id)/`eventClassName`(=eventFullName)/
`eventDataFullName`(实体 DTO 全名)/`eventMfCustomDtoName`(DTO 未首大写名+"."+事件类全名)，**无需自行推导**。
实体事件 9 种（Before/After/TransactionSuccess × Create/Update/Delete）× 实体数；微流程事件（sourceTypes=["MICRO_FLOW_EVENT"]）无 eventClassName。

**messageSource 四源必填字段不同**（反编译 `BusinessEventTrigger.parse` 权威）：
- 公共必填：`messageSource` / `eventDataFullName` / `caption`。
- `EVENT`（应用内实体事件）：另必填 `eventFullName` + `eventMfCustomDtoName`；currentType=来源实体id，currentId=事件名。
- `MICRO_FLOW_EVENT`（应用内微流程事件）：另必填 `eventMfCustomDtoName`，**不要写 eventFullName**（写 null）；currentType=sourceId(0)。
- `MESSAGE`（应用间）：另必填 **`topic`**（来自 udcMicroflowFilterMqPost，body {appId, appName, microFlowId}）；
  currentType=来源应用 appName；eventName 缺省时平台由 eventDataFullName 末段 lowerFirst 推导。
- `CONNECTOR`：另必填 `connectorMessageInfo` 对象。
写错源的必填集（如 MF 事件套 EVENT 源字段、MQ 漏 topic）→ checkSchema 报 `[事件监听]:必填参数未配置`。
trigger.output（事件数据出参）照填：id=javaType=eventMfCustomDtoName、dataType=DTO、**name 必写**（`_BUSINESS_EVENT_xxx` 随机码，漏写校验失败）。★ 前端「节点出参名称」的**回显绑定是 `trigger.title`**（bundle 证据：`{key:"title",label:"节点出参名称"}`，保存时 `output.desc="$title"`）——只写 output.desc 而不写 trigger.title，checkSchema 不报错但前端面板显示空占位。构造器必须两个都写：`trigger.title` 与 `output.desc` 填同一个用户可读出参名（如「事件数据」）；name 是平台自动码（`_BUSINESS_EVENT_xxx`）不要动。SERVICE 类型 endNode 的 `value` 必填（反编译 `MicroFlowOutputValueBo.parse`：buildAttrValue required=true），CUSTOM 可空——缺 value 报 `[root]:必填参数未配置`。

### 定时任务 trigger 结构（triggerType=SCHEDULE）

trigger 节点额外字段（反编译 `ScheduleTrigger`）：`jobCaption`(任务名) + `jobCode`(任务编码，前端 nanoid(16) 随机码) + `scheduleCronRule`。
`scheduleCronRule.cronRules[]`：`cycleType`(SIMPLE=固定周期轮换)；SIMPLE 时带 `rotationType` + `startTime`(毫秒时间戳**字符串**) + `endTime`(null=不结束) + `value`(数字字符串) + `type:"FIRST"`（**SIMPLE 也必须有 type:"FIRST"**，反编译 parse 分支看不出，抓包证实）。
★ `rotationType` 合法值只有 **DAY/HOUR/MINUTE**（`RotationTypeEnum` 仅此三项），WEEK/MONTH 会让 checkSchema 返回 `check=null` 静默拒绝、update 后停在 DRAFT；「每周/每月」不能用 WEEK/MONTH 填 rotationType，用 CRON 类 cycleType 或换算 DAY。MINUTE 最小值 5。非 SIMPLE 的 cycleType 才用 `type`(FIRST/LAST/ANY) + `value`。

### CALL_APP_SERVICE 的常量参数：值字段是 `simple` 不是 `value`

反编译 `buildAttrValue` default 分支：`NodeUtils.getValue("simple", valueObj, ...)` → `attrValue.setSimple(...)`。
写 `{"type":"Simple","value":"x"}` BOOT_0000 照过但 simple=null → setSimple("") → 前端参数区显示空。
正确形制 `{"type":"Simple","simple":"<常量值>","desc":"..."}`。

### 事件投递（PUBLISH_BUSINESS_EVENT）的赋值方式选型

`mappingType` 三值（`MappingTypeEnum`）：attrs 字段映射 / value 对象引用 / mapping 自动映射。
**对象引用（value）要求被引节点出参 javaType 与事件 DTO 全名完全一致**——引用实体节点（javaType=实体 DTO）前端必报「所选‘xx’已变更」，checkSchema 不拦。
无同型 DTO 节点时必须走 attrs 字段映射，且事件字段从 DTO 定义接口取真实字段：`udcMicroflowSearchMessageDtoPost`（body {appId, appName}）拿事件 DTO 的 `id` → `udcDataTransferObjectSelectDtoWithAttrsGet`（path {id}）拿 attributes（含 name/dataType）。映射行要求两侧 dataType 同型（STRING←STRING、BIGINTEGER←BIGINTEGER），attrType.id=`<事件DTO全名>.<字段名>`，value.selectParam 指向前序实体节点出参（name/outputName=`_<节点id>`，带 nodeInfo.actionType）。

### 监听/定时类微流程也搭节点链（用户要求的完整度标准）

事件监听与定时任务不是「trigger+结束」空壳：trigger 后接标准节点链（RETRIEVE→CREATE_VARIABLE→CHANGE_VARIABLE(表达式)→CREATE_ENTITY），出参 endNode.value 引用 CREATE_ENTITY 节点（make_end_entity 形制）。出入参全对象化：入参禁 BASIC（用户明确要求），事件 trigger.output 本身是 DTO，定时 trigger.output 填实体 DTO。参考生成器 `scripts/gen_30_v4.py`（`build_common_chain` 公共节点链 + `evt_schedule_schema`）。

### 删除微流程接口

GraphQL `udcMicroflowDeletePost`（mutation），body `{id: <mid>}`，返回 `content=true`（BOOT_0000）。删测试流程用这个，不是 REST（registry 的微流程写面只有 create/update/checkSchema/findById，无 delete）。

## ★ 出入参定义（「参数」页签）读 trigger/endNode 的 paramType，不是顶层 input/output

「参数」页签入参面板 = `dataSchema.trigger`（MFStartNode），出参面板 = `dataSchema.endNode`（MFEndNode）。
顶层 `input`/`output` 只是 runtime 的 DTO 结构（引擎执行用），改了它参数页签仍显示「无参数」。

`paramType` 四值（挂在 trigger/endNode 节点上）：`NONE` 无参数 / `BASIC` 基本类型(带 `basic` 子字段) / `ENTITY_OBJECT` 实体对象 / `DEFAULT_OBJECT` 自定义对象。

实体对象入参（trigger）形态：
```jsonc
{"id":"","nodeId":"MFStartNode","caption":null,"description":null,"type":"MANUAL",
 "input":null,                          // 入参 DTO 在 output，不在 input
 "output":{实体DTO(id/dataType:DTO/dtoType:MASTER_ENTITY/desc/name:_FLOW_INPUT_xxx)},
 "paramType":"ENTITY_OBJECT",
 "entityObject":{key:<domain.entity.X>,entity:<domain.entity.X>,   // key/entity 是 domain 类
                 id:<dto.XDto>,fullName:<dto.XDto>,               // id/fullName 是 DTO
                 label:<实体名>,dataType:"DTO",dtoType:"MASTER_ENTITY",udcApp:true,
                 relationEntity:<关系实体id>,
                 methodLegal:{available,complexCondition,seniorMethod,serviceType,interfaceClassFullName}},  // 共 10 键
 "desc":"参数名称",                       // required，空则面板报「请输入参数名称」
 "app":{...},"isArray":false,"hasPagination":false,"basic":null}
```

BASIC 入参/出参的 `javaType` 必须按 dataType 精确映射（`_JAVA_TYPE`，已在 components/construction/microflow_triggers.py 落地）：
STRING→java.lang.String、INTEGER→java.lang.Integer、BIGINTEGER→java.lang.Long、BOOLEAN→java.lang.Boolean、
DATETIME/DATE→java.util.Date、DECIMAL→java.math.BigDecimal、DOUBLE→java.lang.Double。
全部写 Long 会让含非 Long 类型的入参 checkSchema 偶发失败。

出参（endNode）同挂 `paramType` + `entityObject` + `desc`，另加 `value` 指定运行时出参来源：
```jsonc
"value":{"type":"SelectParam","selectParam":{   // 基本类型出参：id=变量名(带下划线), paramType=BASIC, basic=STRING
  "id":"<实体DTO fullName>","name":"_<来源节点id>","outputName":"_<来源节点id>",
  "nodeInfo":{"nodeId":"<来源节点id>","type":"ACTIVITY","actionType":"RETRIEVE"},
  "relationEntity":"<关系实体id>","position":"parent"}}
```

引用入参字段/前序实体字段（条件右值）用 `CONTEXT_VARIABLE`，value 是 JSON 字符串，`position:"children"`：
`key=<outputName><入参DTOfullName>.<字段名>`（outputName 与 DTO 之间**无分隔符**）、
`path=<DTOfullName去点><字段名>`（去点后与字段名**无点分隔**）、
`id=<DTOfullName>.<字段名>`、`name=<字段名>`、`customs.id`=字段真实 id、`parentLabel`=入参 DTO 标题。
key 写成 `<outputName>_<DTO>.<字段名>`（多下划线）或 path 写成 `<DTO去点>.<字段名>`（多点分隔）都会让右值被判「不是单条数据」，报 `UDC_MICRO_FLOW_04004`。

教训：要「入参/出参是实体」，改的是 trigger/endNode 的 `paramType=ENTITY_OBJECT` + `entityObject` 引用 + `desc`；不是顶层 input 的 dtoType（`dtoType=null+dtoFullName+isArray+dto=true` 是旧版 V16 顶层形态，参数页签不读）。

★ `entityObject` 引用必须查 `udcMicroflowSearchTreeEntityPost`（body: {appId,appName,needChildren,needThirdEntity,serviceType:'SELECT_LIST_BY_COMPLEX_CONDITIONS'}）拿实体真实结构，**禁止手拼元数据**。接口返回的 `fullName`=domain 类（`domain.entity.X`）、`dtoFullName`=DTO（`dto.XDto`）、`relationEntity`=关系实体 id；但 **entityObject 引用里字段映射不同**：`key`/`entity`=domain 类，`id`/`fullName`=DTO。把两者搞反（DTO 塞进 key/entity、或 domain 塞进 id/fullName）前端参数页签报「所选实体对象已失效，请重新选择」——**checkSchema 不拦这个**，只有前端树选择器（ant-tree-select）校验。★ CDP 用 `dispatchEvent` 点 tree-select 选项**不触发 React 的 onChange**，读回的 entityObject 是残留假结构（14 键带 title/value/dtoFullName/customs/filterTitle）；必须以「用户真实点选后保存、再读回」为准，或直接让用户在编辑器重选实体看是否还红字。自定义对象（DEFAULT_OBJECT）同理走 `udcMicroflowSearchNonEntityDtoPost`，defaultObject 的 fullName=DTO（自定义对象无 domain 类）、标识用 `dtoId`（=接口返回的 `id`）。

## 子微流程传参（mappingType=attrs）

```jsonc
{"mappingType":"attrs","attrs":[{"attrType":{"name":字段名,"id":"<DTO全名>.<字段>","fullName":同id,
  "dataType":"BIGINTEGER","type":"OBJECT","desc":caption,"javaType":"java.lang.Long",
  "dataI18n":false,"filterDataType":null,"filterFullName":null,"filterType":null,
  "multiSelect":false,"refApp":"udc","relationApp":"udc","sort":null},
 "value":{"type":"Expression"|"Simple",...}}],"value":{"type":"Simple","simple":"","desc":""}}
```
- 入参 DTO 字段从 `udc_dto_attribute`（按 caption/name 找 dto_id 聚集）确认；微流程入参 output.name=`_FLOW_INPUT_xxx`。
- mfService.input 必须声明为目标流程 schema.input 原文，否则应用检测报「微流程已更改」（code 27）。

## 分支条件

`conditions[].expression` **与 attr.value.expression 不同构**：前者是**裸** `{title, schema}`（无 `type:"Expression"` 包装），
后者是 `{type:"Expression", expression:{title, schema}}`。resultTypeInfo=BOOLEAN。
分支必须带 `elseBranch`（`expression:null, nodes:[], isCompleted:true` 默认出口）——只建 ifBranch 且塞满自定义错误时，
检测报「所有分支中都配置了自定义错误节点，无法正常返回」。
自定义错误（CUSTOM_ERROR）要放进「永远不成立」的分支（ifBranch expression=`false`）以覆盖节点类型，
不能放在正常流程路径/出参（endNode）之前——否则检测报「自定义错误不可以作为出参」且中断流程使出参无法返回。

## 节点形制的 checkSchema 必填字段（生成器逐节点踩平的坑）

全量 24 类节点生成器已落地：`components/construction/node_builder.py`（NodeBuilder：模板骨架 + 符号表 + nodeId 唯一化）、
`microflow_fields.py`（实体/字段/条件/引用，字段从 definitions/ 取 md5）、`microflow_nodes_v2/extra/svc.py`（各域节点构造）、
`microflow_params.py`（出入参 trigger/endNode）。定义驱动 + 链路顺序，checkSchema 逐节点踩平的必填字段：

| 节点 | 必填/易错 | 正确形制 |
|---|---|---|
| DATA_MAPPING 数据转换 | mappingRow | `{targetField, mappingMode:"REFERENCE", value:{reference:{字段}}}`，不是 sourceValue |
| CONVERT_DATA 类型转换 | convertType 是对象 | `{desc,value:"Split",dataType,type}`（value=枚举），不是字符串；另带 value/regex 字段 |
| 所有数据节点 structure | entityId | `structure.entityId`=relationEntity，CALL_DATA_FLOW 缺它报「entityId 必填」 |
| FOR 计数循环 | forStep 是数字 | forStep=1（裸数字），forStart/forEnd 才是 Simple/Expression 对象；`type:"FOR"`，foreach=null |
| FOR_EACH 列表循环 | type 必须是 FOR_EACH | `type:"FOR_EACH"`+`actionType:"FOR_EACH"`（**不是 FOR**！前端据此区分两种循环，套 FOR 模板会渲染成「计数循环」），`selectParam`=选择列表（checkSchema 必填），`foreach:{sourceItemes:[...]}`，`entityCaption`=循环对象标题，且必须删掉 forStart/forEnd/forStep/operator（计数循环标志） |
| CALL_DATA_FLOW 生单规则 | 来源实体必须匹配 | structure/selectParam 必须用 `dataFlow.sourceEntityId` 对应的实体（如 YsFull6956），不能随意换实体 |

### 生单规则的 dataFlow 字段与「生单规则已被删除」

`dataFlow` 字段**不是可选**——缺了它前端找不到规则，检测报 `DATA_FLOW_NOT_EXIST`「生单规则已被删除」。全 11 键照模板（`fixtures/microflow/node_templates/CALL_DATA_FLOW.json`）：

```jsonc
"dataFlow":{"id":"<生单规则id>","key":"<同id>","value":"<同id>","title":"<caption>",
  "appId":"<appId>","appUrl":"<appName>","caption":"<caption>","name":"<name>",
  "sourceEntityId":"id_<来源实体relationEntity>","g_l_index":"1"},
"dataSourceType":"SELECT_PARAM",
"dataFlowMappingId":"<生单规则id>"   // 判定键，必须与 dataFlow.id 一致
```

判定（反编译 `CallDataFlowActivity.activityNodeLogicCheck`）：检测取 `nodeContext.getDataFlowIds()`（应用元数据里实际存在的生单规则 id 集合，来自 `MetadataUtils.getDataFlowIdSet(detectionContext)`），
`!dataFlowIds.contains(dataFlowMappingId)` 就报「生单规则已被删除」。所以规则真被删（或 id 写错）时只能换 id，不是节点 JSON 结构问题。

**查生单规则列表**：GraphQL `udcDataFlowListManuallyMappingPost`（body `{appId}`），返回 `[{id, caption, name, sourceEntityId}]`。`sourceEntityId`（裸 id，不带 `id_` 前缀）必须匹配 structure 的 relationEntity，对不上就是规则选错实体。

24 类节点落库 actionType 与面板语义名不同：映射组=CREATE_MAP（面板 CREATE_MAPPING_GROUP）、
自定义服务=CALL_APP_SERVICE（面板 CUSTOM_SERVICE）、类型转换=CONVERT_DATA（面板 TYPE_CONVERT，8 种写死类型走 convertType.value 区分）、
数据转换=DATA_MAPPING（面板 DATA_CONVERSION）、修改列表=CHANGE_LIST（面板 MODIFY_LIST）。计数循环/分支的 actionType 是 null、用 `type` 字段区分（FOR/BRANCH）；列表循环是 `type:"FOR_EACH"`+`actionType:"FOR_EACH"`。别拿 actionType 判重，也别拿 FOR 模板套列表循环——`type` 才是前端区分计数/列表循环的唯一字段。

## 应用检测是权威关卡

checkSchema/update 只做单流程浅校验；跨流程引用（子微流程/生单规则）只有 `udcApplicationSearchDetectionPost` 能暴露，TEST 构建（deploy-normal）硬门同源。修完必须跑检测确认 ERROR=0。

★ **检测读的是实时微流程，但异步执行——必须等它跑完再读结果**：`udcApplicationDoDetectionPost` 触发后走 `CompletableFuture.runAsync` 后台执行，`detection-state` 从 EXECUTING 变 SUCCESS 才代表本轮跑完、结果已写入。
**触发后第一次轮询（5 秒）就 break，读到的是上次检测的旧缓存**（errorCount/count 不变、报错文案是修复前的旧内容）——不是「检测读快照」，而是「检测还没跑完」。
正确做法：触发后轮询 `do/detection-state`，等到 status 稳定在 SUCCESS（连续两轮同值，`sig` 不再变）再读 `udcApplicationSearchDetectionPost`，此时才是实时微流程的最新结果。
前端顶部「检查」按钮触发的就是这同一个接口对（DoDetectionPost + SearchDetectionPost，无额外的保存/刷新步骤），读的也是最新数据。
所以「修完→update→立即读检测」出错时：先读回 `findById` 确认新 schema 已落库，再重触发检测并**等 EXECUTING→SUCCESS 完成**——不要误判成「需要构建刷新快照」去跑 `udcRuntimeDeployNormalPost`。

★ **报错处置纪律**：用户贴出平台报错文案（`业务异常[...执行异常: null]` 这类）时，第一步是去 udc pod 的 `/var/log/webapps/udc/udc-error.log` 取栈定位到具体 getter，**不要先猜着改 schema**。改前猜错方向、改后只看 `udcMicroflowUpdatePost`/`checkSchema` 返回 BOOT_0000 就宣布修好，都会被打回——引擎终态（`do/detection` → 轮询 `do/detection-state` 到 SUCCESS/FAIL）与节点面板红字才是验收面。UI 侧同源入口是顶部「检查」按钮：草稿态下点完读 `.ant-table-body tr`，每行给出 `类型|模块元素|错误代码|错误信息`，是判断「还有几条错」最快的口径（徽标数字会随之变化）。要逐个节点看「面板里到底显示了什么」——参数映射有没有值、出参是不是「未命名」——见 `references/ui-node-panel-audit.md`：**单击节点不会弹面板，必须 scrollIntoView 后用 CDP 真实鼠标事件双击**（节点在画布视口外时坐标为负，合成事件全部无效）。

★ 本 skill 只管表达式的 `tokens`/`context`。**节点本身的数据形制**（自定义服务 `selectMethod` 13 键 / `attrType` 带 `refApp:"udc"` / 出参 desc；执行生单规则 `dataFlow` 必须指向 `udc_data_flow_mapping` 行而非规则 id）在**另一个 skill** `seeyon-low-code-environment` 的 `references/udc-microflow-authoring.md` §8.1 与 `references/udc-deduction-and-dataflow-rules.md`（不在本 skill 目录下，用 `skill_view(name='seeyon-low-code-environment', file_path=...)` 读）。手写节点前先查那两份，别只对齐表达式。