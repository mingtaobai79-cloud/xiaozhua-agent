# P3 声明式逻辑图：JSON → 节点 → schema

> 代码：`components/construction/logic_graph.py`（执行器）、`expression_dsl.py`（JSON→AST）。
> 平台实证 2026-11-01：数据源有效校验（9 节点 / 嵌套 BRANCH / 多条件查询 / 函数）save+readback+表达式全 PASS。

## 什么时候用它

只要要生成微流程（不是改一个现成节点），就走逻辑图，**不要**写命令式 `comp.step(...)`：
控制流一旦嵌套，Python 代码结构就不可靠，而且用户看不到方案、审计员没法只审方案。

## 图格式

```json
{
  "nodes": [
    {"id": "ds", "kind": "retrieve", "entity": "数据源配置信息",
     "by_id_from": "$input", "caption": "查询-数据源",
     "null_handling": "TERMINATION", "null_message": "数据源不存在"},

    {"id": "res", "kind": "create_variable", "title": "isValid",
     "data_type": "BOOLEAN", "value": false, "caption": "结果-默认无效"},

    {"id": "br", "kind": "branch", "caption": "判断-是否启用",
     "condition": {"op": "EQ", "left": {"field": "ds.enabled"}, "right": {"const": true}},
     "then": [
        {"id": "others", "kind": "retrieve_array", "entity": "数据源配置信息",
         "conditions": [
            {"field": "enabled", "op": "EQ", "right": {"const": true}},
            {"field": "id", "op": "NE", "right": {"field": "ds.id"}}]},
        {"id": "br2", "kind": "branch", "condition": {
            "fn": "containsText",
            "args": [[{"field": "ds.jdbcUrl"}], [{"const": "mysql"}]]},
         "then": [{"id": "setT", "kind": "change_variable", "target": "res",
                   "value": true}]}
     ]}
  ],
  "end": {"from": "res", "desc": "数据源是否有效", "basic_out": "BOOLEAN"}
}
```

表达式 DSL **十种**形态：`const` / `sys` / `ref`（整节点连出）/ `field`（`ds.jdbcUrl`）/
`input`（流程入参）/ `item`（循环项，见下）/ `op`（比较）/ `logic` / `arith` / `fn` / `cond`。
（数数的时候别漏 `item` —— 它是 P3.1 加的。）

## 运行

```python
from components.construction.logic_graph import LogicGraphRunner, validate_graph
from components.udc.microflow.expression_refs import ReferenceResolver

validate_graph(graph)                       # 纯结构体检，先跑，避免白查元数据
res = ReferenceResolver(APP, APP_NAME, live_refs=lr)
res.bind_flow_input(inp_out, fields=ent["attributes"])   # 有入参时必须绑
schema = LogicGraphRunner(comp, resolver=res, backend=CurlBackend(host, ck)).run(graph)
```

## 循环体内引用（P3.1）：循环项 = FOR_EACH 自身出参

**语料事实（526 个 FOR_EACH + 37 条循环体内引用）：不存在独立的「循环变量」对象。**
循环项就是 FOR_EACH 节点自己的出参 `_FOR_EACH_xxx`，`targetName` 只是显示名。

```json
{"id": "eachDs", "kind": "for_each", "list": "arr", "caption": "循环-逐个停用",
 "body": [
   {"id": "cur", "kind": "retrieve", "entity": "实体",
    "by_id_from": "eachDs", "from_field": "id"},
   {"id": "upd", "kind": "change_entity", "entity": "实体",
    "from_node": "cur", "fields": {"enabled": false}}
 ]}
```

表达式里引用循环项：`{"item": "eachDs", "field": "id"}` 或
`{"field": {"source": "eachDs", "path": "id"}}`。

**循环项字段引用的落库形态**（37/37 一致，与普通节点引用不同）：
`position=parent` + `nodeInfo={nodeId: ForEach_xxx, type: "FOR_EACH"}` + `name=字段名`
（不是 `节点名.字段`）。走 `LogicGraphRunner._retrieve_by_loop_item`，**不要**走
`composer._id_ref`（它造 `children` + `ACTIVITY`，与语料全不符）。

三条硬规则：

- **作用域只在 body 内**。出循环必须 `loops.pop()`，循环外引用直接报错。
- **元素类型决定能不能取字段**：源列表 `dataType=DTO` 才能 `item.<字段>`；
  `BIGINTEGER`/`STRING` 取 `.id` 平台无此字段。
- **G20 不变**：写操作对象必须是活动节点出参，循环项只能进 `RETRIEVE(IDS, item.id)` 中转。
  直接拿循环项当写操作对象 → 平台生成 `int→Dto`，Java 编译失败。

嵌套循环：内层可见外层，外层不可见内层，同名别名禁止（会歧义）。
元素字段元数据优先取**实体模型**（RETRIEVE_ARRAY 的 structure 通常没有 attributes，
直接读会得到空字段表 → 每次 `item.x` 都报「字段不存在」）。

### mapping 行的 selectParam 比 attrs 严（实测保存报过错）

平台真实报错（拿草稿去保存）：

```
[创建变量] CREATE_VARIABLE_xxx,创建变量.mapping.value.type        → DATA_INVALID
[创建变量] CREATE_VARIABLE_xxx,创建变量.mapping.value.selectParam.dtoType
                                                    → PROPERTY_IS_REQUIRED
```

语料（2392 个 mapping 行）：

| 项 | 事实 |
|---|---|
| `value.type` | SelectParam 2392 / Expression 68 / Simple 15 / Enum 2 / **无 OBJECT** |
| `selectParam.dtoType` | **2392/2392 = 100%**（唯一真必填，缺了直接报错）|
| `selectParam` 其余 9 键 | 100%（key/name/id/description/position/path/outputName/dataType/type/javaType）|
| `appName/udcApp/multiSelect/customs/parentLabel` | 2391/2392（有 1 条例外，平台未报必填）|

`dtoType` 取值：`CUSTOM`(2187) 配 `udcApp=false`；`SUB_ENTITY`(204) 配 `udcApp=true`。

★ **attrs 和 mapping 的 selectParam 键集不同**：
attrs 带 `nodeInfo/iconKey/title/generics/disabled`，mapping **一个都不能带**。
同一份 selectParam 直接复用必错，要过 `_to_mapping_select_param()` 规范化。

## ★★ 值形态审计法（2026-11-01 全类型复查）

改任何一个「值」之前，先跑一遍这个审计，不要只修用户看到的那一个：

```python
# 语料 → (左值dataType, 右值type, value 的 Python 类型) → 条数
# 语料 → 各 actionType 的键集与取值类型
# 我方构造器 → 同结构，两边摊开逐键比
```

### 已定死的三条（语料 240 条 CONSTANT 条件）

| 左值 dataType | value | desc |
|---|---|---|
| BOOLEAN | **bool** | **bool** |
| DECIMAL | **float** | float |
| INTEGER/BIGINTEGER | **int** | int |
| STRING | str | str |
| ENUM / CTPENUM | str（枚举码或雪花 ID，多选逗号拼）| **str（显示名，逗号拼）** |

ENUM 的 desc 写标识不阻断功能，但设计器里就是一串数字，人没法读。

### BASIC 变量整节点引用是**两级**，不是三级

语料 319 个 BASIC 变量引用 token：两级 `X.X` 292 个，三级 `X.X.<字段>` 27 个。
BASIC 变量值槽就是它自己，写三级平台回
`FORMULA_6058 CVariable :xxx does not exist in context`。
判据：`field == outputName` → 两级。

### 控制节点不带 actionType

语料：BRANCH(941) / FOR_EACH(526) / FOR(32) **全部无 `actionType` 键**，
只有 END(643) 有。审计脚本只按 actionType 统计会把控制节点全漏掉，
误以为「我方多出 actionType=None」——那是自己的口径错。

## ★★ 条件右值类型必须匹配左值字段 dataType（2026-11-01 用户肉眼发现）

语料裁决（`pmp_schemas.json`，全部 CONSTANT 条件 240 条）：

| 左值 dataType | rightParams[].value 类型 | 条数 |
|---|---|---|
| BOOLEAN | **bool** | 15（15/15）|
| DECIMAL | **float** | 1 |
| STRING / ENUM / CTPENUM | str | 224 |

BOOLEAN 条件写成 `value: "true"`（字符串）→ 前端设计器按**文本**渲染
（下拉给的明明是「是/否」），后端按布尔校验也拿不到布尔值。

### ⚠ 两种 CONSTANT 形态不同，绝别当一回事

```
查询条件  rightParams[].value   → 原生类型：BOOLEAN → true(bool)
表达式    tokens[].value         → 字符串：BOOLEAN → "true"(str)
```

设计器实测：表达式 token 里就是字符串 `"true"`（抓包原文如此），
但查询条件的 rightParams 是真布尔。**两套不能统一成一套。**

代码位置：`logic_graph._constant(v, data_type)`，dataType 由
`_cond_value(..., entity=, field=)` 从实体模型查出，三处调用点
（retrieve 单条件 / retrieve_array 单条件 / 多条件）都要传左值字段。

## 两个构造期硬约束（2026-11-01 验收 6 场景踩到）

### 1. `retrieve_array` 必须带条件

```json
{"kind": "retrieve_array", "entity": "X",
 "conditions": [{"field": "enabled", "op": "EQ", "right": {"const": true}}]}
```

不给 `conditions` 也不给 `cond_field` → 报「字段 '' 不存在于实体」。
全量查询也要至少一条恒真条件，构造器不会替你造空条件。

### 2. 单元素 `logic` 已解包（不再是错误）

`{"logic":"AND", "items":[单条]}` → 直接返回那条表达式本身。
语义上 AND 一个条件 == 那个条件；编译器/图天然产出这种形态，
报错只会逼调用方写两种形状、容易漏。空 `items:[]` 仍报 `DslError`。

## 六个坑（平台全不给明细或静默错）
1. **分支体节点不能留顶层**。`composer._st_*` 已 `_add()` 进 `self.c.nodes`；执行器再 append
   就成了两份，分支体是空壳。在 `_stack` 非空时先 `self.c.nodes.remove(node)` 再进栈。

2. **`finish` 必须显式传 `trigger`**。默认 `trigger=None` 会回落 `trigger_manual()`，
   丢注入的入参 DTO → `schema.trigger.trigger` 变空 → G2 把 `_FLOW_INPUT_*` 全判悬空。

3. **查询条件运算符必须显式传**。`condition_group(...)` 默认 `operator="EQ"`，漏传会把
   「id != 入参」写成「id == 入参」—— 语义反转，平台**不报错**。

4. **多条件必须是「1 个 GROUP 含 N 个 CONDITION」**（语料 170/170）。写成多个 GROUP 并列
   平台回 `BOOT_1001 Parameter Error`，无任何明细。

5. **条件右值只能是三态**：`CONTEXT_VARIABLE`(470) / `CONSTANT`(193) / `EXPRESSION`(136)。
   **SelectParam 在 799 条语料里出现 0 次**，塞进去就是 BOOT_1001。
   用 `microflow_fields.to_context_variable(ref)` 转换（`value` 是 **JSON 字符串**，
   且不能带 `nodeInfo`/`iconKey` 这类 UI 键）。

6. **函数参数组数 = 函数目录的 `paramCount`**。`containsText(参数,被包含文本)` 要两组：
   `args: [[a], [b]]`。写成 `[[a, b]]` 平台回 `FORMULA_6049 parameter number does not match`。

## CUSTOM_ERROR：让运行结果可断言

构造器 `microflow_nodes_extra.custom_error` 早就存在，但执行器
（`LogicGraphRunner._do_custom_error`）和组装器（`MicroflowComposer._st_custom_error`）
是后补的——**两者必须成对存在**，只补一边会在 `step()` 或
`getattr(self, "_do_" + kind)` 那里才炸，构造期看不出来。
现有单测锁住这个配对（`tests/test_custom_error_node.py`）。

```json
{"id": "err", "kind": "custom_error", "message": "标记不存在", "caption": "校验-标记缺失"}
```

用途只有一个：**让流程在设计好的条件下主动失败**。查询结果为空就抛错，
于是运行日志的 `success=false` 本身就是一票否决的证据，不必再依赖外部查询接口
去核对业务数据——这是目前唯一能自证「跑出来的东西对不对」的手段。

★ 带 CUSTOM_ERROR 的完整流程**尚未 publish / 真跑验证过**（只验了构造与接线）。
第一次用它之前先走一遍最小闭环，别默认它已经通了。

## 排查 BOOT_1001（无 message）的顺序

1. 先确认走的是 `deploy.publish`（自拼 body 少一个键就是 1001）
2. 再二分 schema：单节点 → +变量 → +BRANCH → +多条件查询 → +嵌套
3. 条件类节点盯两件事：GROUP 数（必须 1）、右值 type（不能 SelectParam）

## 执行器的三个隐蔽坑（都踩过）

- **`_st_*` 已 `_add()` 过节点，执行器不能再 append**。顶层节点直接交回，分支体内才需要
  `self.c.nodes.remove(node)` 后进栈，否则要么重复两份，要么分支空壳。
- **循环体内 RETRIEVE 要自己落位**。`_retrieve_by_loop_item` 必须把节点 append 进当前容器，
  否则节点不在流程节点表：G10「引用的参数已失效」+ G2/G31 悬空，而且循环体是空壳。
- **必须走 `composer.entity()` 拿实体模型**。绕过它会把实体漏登记进 `composer._entities`，
  后续 `refs_field`（attrs 字段引用）反查不到 → attrs 落成悬空引用。

## G31 的字段级引用判据：用 `name==outputName`，不要用 position

语料：`position=parent` 且 `dataType=字段类型` 的有 1646 条（循环项字段、部分实体字段都用 parent）。
所以 `position` 不能当「是不是字段引用」的判据 —— 用它会把合法引用误判成类型不一致。
可靠判据：**整节点引用的 `name` 恒等于 `outputName`**（2301+19 条），字段引用的 `name` 是字段名（7951 条）。

## `_field_meta` 的 BASIC 分支只能用 `paramType=="BASIC"` 判

早期还加了「有 dataType 且 structure 无 entityId」，结果 RETRIEVE 节点（dataType 在 output 里、
structure 只有 id/caption）被误判成 BASIC，返回 `id=字段名`，生成 context 时子节点名变成实体 caption
→ 平台报 `FORMULA_6058 xxx.field does not exist in context`。

