# 创建变量 7×7 落库契约

探针流程实测（每次点确认 → `udcMicroflowUpdatePost` → `read_schema` 回读）。

## 一、7 种 paramType 的表单差异

| paramType | radio 文案 | 表单字段（* 必填） | 联动 dataType |
|---|---|---|---|
| `BASIC` | 基本类型 | 变量类型* / 数据类型* / 默认值 / 节点出参名称* | 用户选（7 选 1） |
| `ENTITY_OBJECT` | 实体对象 | 变量类型* / 选择应用* / 实体对象* / 节点出参名称* | 自动 DTO |
| `DEFAULT_OBJECT` | 自定义对象 | 变量类型* / 选择应用* / 自定义对象* / 节点出参名称* | 自动 DTO |
| `ENUM` | 选项集 | 变量类型* / 选择应用* / 选项集* / 默认值 / 节点出参名称* | 自动 ENUM |
| `METADATA` | 元数据 | 变量类型* / 选择应用* / 元数据类型* / 选择元数据* / 节点出参名称* | 自动 METADATA |
| `MESSAGE` | 事件对象 | 变量类型* / 选择应用* / 事件对象* / 节点出参名称* | 自动 DTO |
| `OTHER` | 其他 | 变量类型* / 其他类型* / 选择应用* / 自定义对象* / 排序规则* / 节点出参名称* | 自动 DTO |

**只有 BASIC 让用户选 dataType，其余 6 种由 paramType 决定。**

## 二、落库结构

### BASIC
```json
{"paramType":"BASIC","dataType":"STRING","title":"objVar2",
 "value":{"type":"Simple","simple":"abc","desc":"abc"}}
```
`value = {type:"Simple", simple:<原值>, desc:<同值>}`。
**切换 dataType 会清空 value**（控件带 `setemptybeforechanged="value"`），切完要重填。

### ENTITY_OBJECT
```json
{"paramType":"ENTITY_OBJECT","dataType":"DTO","value":null,
 "structure":{"key":"com.seeyon.<app>.domain.entity.XzhExp950795",
   "id":"com.seeyon.<app>.dto.XzhExp950795Dto","label":"小爪实验实体950795V2",
   "dataType":"DTO","entity":"com.seeyon.<app>.domain.entity.XzhExp950795",
   "dtoType":"MASTER_ENTITY","udcApp":true,
   "fullName":"com.seeyon.<app>.dto.XzhExp950795Dto","relationEntity":"474806313816300867",
   "methodLegal":{"available":true,"complexCondition":true,"seniorMethod":true,
     "serviceType":"NONE","interfaceClassFullName":null}},
 "output":{"id":"com.seeyon.<app>.dto.XzhExp950795Dto","javaType":"com.seeyon.<app>.dto.XzhExp950795Dto",
   "dataType":"DTO","type":"OBJECT","dtoType":"MASTER_ENTITY","udcApp":true}}
```

### DEFAULT_OBJECT
`structure.key/fullName` 带 `.dto.microflow.` 段，`dtoType:"CUSTOM"`：
```json
{"paramType":"DEFAULT_OBJECT","dataType":"DTO","value":null,
 "structure":{"key":"com.seeyon.<app>.dto.microflow.XzhOutItemDto",
   "fullName":"com.seeyon.<app>.dto.microflow.XzhOutItemDto","label":"出参明细对象",
   "dataType":"DTO","dtoType":"CUSTOM"},
 "output":{"name":"_CREATE_VARIABLE_3kwr4G","dataType":"DTO","dtoType":"CUSTOM",
   "javaType":"com.seeyon.<app>.dto.microflow.XzhOutItemDto",
   "id":"com.seeyon.<app>.dto.microflow.XzhOutItemDto"}}
```

### ENUM
```json
{"paramType":"ENUM","dataType":"ENUM","value":null,
 "structure":{"label":"小爪扣减单据状态",
   "key":"com.seeyon.<app>.enums.XzhDedBillbillStatus",
   "value":"com.seeyon.<app>.enums.XzhDedBillbillStatus",
   "fullName":"com.seeyon.<app>.enums.XzhDedBillbillStatus"}}
```
`key/value/fullName` 三者相同，都在 `.enums.` 下。

### METADATA（唯一 structure:null）
```json
{"paramType":"METADATA","dataType":"METADATA","value":null,"structure":null,
 "output":{"id":"8643109752427203840","javaType":"java.lang.String",
   "dataType":"METADATA","type":"OBJECT","udcApp":true,
   "name":"_CREATE_VARIABLE_oAFOMN"}}
```
元数据信息全在 `output.id`（数字 id）+ 表单两段式选择（元数据类型：页面/表单… → 选择元数据）。

### MESSAGE
```json
{"paramType":"MESSAGE","dataType":"DTO","value":null,
 "structure":{"key":"com.seeyon.<app>.dto.YsEvtData2","label":"验收新增事件2",
   "id":"com.seeyon.<app>.dto.YsEvtData2","value":"com.seeyon.<app>.dto.YsEvtData2",
   "dataType":"DTO","dtoType":"CUSTOM","udcApp":false,
   "fullName":"com.seeyon.<app>.dto.YsEvtData2"}}
```
注意 `udcApp:false`（事件 DTO 不在 UDC 应用层）。

### OTHER（系统排序对象）
```json
{"paramType":"OTHER","otherType":"SYSTEM_SORT_OBJECT","dataType":"DTO","value":null,
 "structure":{...自定义对象...},
 "sortParams":[{"sortType":"ASC","attrType":{"validate":true,
   "id":"com.seeyon.<app>.dto.microflow.XzhOutItemDto.concatText","name":"concatText",
   "fullName":"...concatText","md5":"..."}}],
 "output":{"name":"_CREATE_VARIABLE_aRjsCh","dataType":"DTO","dtoType":"CUSTOM",
   "javaType":"com.seeyon.boot.transport.Sort","id":"com.seeyon.boot.transport.Sort"}}
```
**独有 `sortParams`**，`output.javaType` 固定 `com.seeyon.boot.transport.Sort`。

「排序规则」不是 select，是「**添加规则**」按钮：点击后出现 `[选择字段▾][升序▾][添加规则]`，可加多行。
字段选项来自所选自定义对象的属性（显示为 `拼接文本 [文本]` 这种「caption [dataType]」格式）。

## 三、7 种 dataType（BASIC）

下拉顺序固定：`文本 STRING / 整数 INTEGER / 长整数 BIGINTEGER / 小数 DECIMAL / 布尔 BOOLEAN / 日期 DATE / 日期时间 DATETIME`，7 种全部落库确认。

## 四、DOM 定位要点

- 读表单字段名用 `.ant-form-item > .ant-col > .ant-form-item-label label`——直接 `.ant-form-item label` 会把 radio 的 `<label class="ant-radio-button-wrapper">` 也算进来，得到 7 个假字段。
- 「排序规则」行内的 select 属于子 form-item（label 为空），要按 `placeholder === '选择字段'` 定位。
- 实体/自定义对象下拉选项显示 **caption 中文名**（`出参明细对象`），不是 DTO 类名（`XzhOutItemDto`）；按类名匹配必然 `no match`。

## 五、实体型「赋值方式」三形态（发布链实证，G30 管键位）

ENTITY_OBJECT / DEFAULT_OBJECT / OTHER 必须显式带 `mappingType: attrs|value|mapping`（语料 100%）；BASIC 无 mappingType。**键位纪律：value/mapping 形态连 `attrs` 键都不能存在（`attrs:null` 也触发另一分支校验 → DATA_INVALID）；`otherType` 仅 OTHER 形态可带。**

### value（对象引用，语料 36 条）

`value = {"type":"SelectParam", "selectParam":{...}}`，节点上**无 attrs 键**。引用 RETRIEVE 单条出参（position=parent）时 selectParam 完整真实键集（照抄语料，别手拼）：

```json
{"description":"...", "dataType":"DTO", "outputName":"_RETRIEVE_xxx",
 "position":"parent", "udcApp":true, "dtoType":"MASTER_ENTITY", "appName":"<app>",
 "path":"<DtoFullName去点>", "id":"<DtoFullName>", "name":"<DtoFullName去点>",
 "type":"OBJECT", "javaType":"<DtoFullName>",
 "relationEntity":"<实体id>", "relationEntityFullName":"<domain.entity.X>",
 "nodeInfo":{"nodeId":"RETRIEVE_xxx","type":"ACTIVITY","actionType":"RETRIEVE","entityCaption":"<实体名>"},
 "key":"<outputName><DtoFullName>", "iconKey":"LinedSearch", "parentLabel":"", "disabled":false}
```

注意是 `description` 不是 `desc`；`name` 是 path 形态不是 outputName。字段级引用（position=children）时 key=`<outputName>_<app>.<field>`、path=`<DtoFullName去点>.<field>`。

### mapping（自动映射，语料 35 条）

节点带 `selectParam`（源对象引用，形态同上）+ `mapping[]` 行集 + **无 attrs 键**。每行：

```json
{"attrType":<16键字段元数据,用 field_attr()>,
 "value":{"type":"SelectParam", "desc":"<字段名> [<dataType>]", "selectParam":<字段级引用,position=children>}}
```

**行 value.type 恒 `SelectParam`（语料 2374/2374）**——写成 OBJECT 报 `创建变量.mapping.value.type DATA_INVALID`。字段与实体 attributes 同名配对，不在属性表的字段直接 raise。

### 构造器入口

`create_variable(b, title, entity=ent, value_ref=<selectParam>)` / `create_variable(b, title, entity=ent, auto_map_from={"selectParam":..., "fields":{字段名: 字段级selectParam}})`（`microflow_nodes_v2.py`）。attrs 形态沿用 `attrs=[...]`。闸门判据在 G30（`gates.py`）。

## 六、★ 引用 BASIC 变量的 SelectParam 形态（G17 管）

把 BASIC 标量变量填进实体字段（如 `create_entity(fields={"f01text": {"ref": "mark"}})`）时，
生成的 selectParam **必须**是：

```json
{"type":"SelectParam","selectParam":{
  "id":"", "dtoType":"", "javaType":"java.lang.String", "dataType":"STRING",
  "type":"OBJECT", "desc":"<变量出参名>",
  "name":"_CREATE_VARIABLE_xxx", "key":"_CREATE_VARIABLE_xxx",
  "path":"_CREATE_VARIABLE_xxx", "outputName":"_CREATE_VARIABLE_xxx",
  "position":"parent"}}
```

`id` / `dtoType` 空串是硬要求（标量没有 DTO 身份），四个名字字段全等于 `outputName`。

**陷阱**：`parse_expr` 有时把输出名塞进 `field`，于是 `fname == outputName`，
代码走「字段级引用」分支生成 `id=<输出名>`、`name=<输出名>.<输出名>` 的畸形引用。
G17 报的是「PageInfo 模板残留」，**完全指不到真正原因**，很容易去查模板。

判据：只要目标节点的 `output.dataType` 属于
`BOOLEAN/STRING/BIGINTEGER/DECIMAL/INTEGER/DATETIME` 且 `dtoType` 为空，
就是标量，**强制 `fname=None` 走 `_out_ref`**，不要去取字段元数据。
