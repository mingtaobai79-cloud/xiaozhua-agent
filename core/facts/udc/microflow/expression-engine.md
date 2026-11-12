# 微流程表达式引擎：中间模型与传输链（P2 实证）

> 2026-11-01。P2-1/P2-2 落地实证。全部结论来自真实平台
> `/service/udc/expression/check` + `/transform`，或 643 条发布语料统计。
> 代码：`components/udc/microflow/expression_model.py`（AST+编译器）、
> `expression_transport.py`（传输后端）、`tools/core/expression/scan_capability_matrix.py`（矩阵扫描）。

## 一、传输链：为什么必须用 curl

| 通路 | 结果 |
|---|---|
| Python `urllib` → `/service/udc/expression/check` | ✗ `SSL: UNEXPECTED_EOF_WHILE_READING`（稳定复现 3/3） |
| 改 UA（curl / Mozilla） | ✗ 仍 EOF → 不是 header 层 |
| `curl` 同 DTO 同 cookie | ✓ `{"code":"BOOT_0000","data":{"content":true}}` |
| 页面内 `fetch` + CDP `awaitPromise` | ✓ 仅在激活 tab；后台 tab 节流 → 挂死 300s 无返回 |

结论：本环境网关对 urllib 的 TLS/ALPN 指纹直接断链（HTTP/1.1），
curl（HTTP/2）正常。**表达式接口默认走 `CurlBackend`**；
`PageBackend` 只在前台 tab 场景用。

## 二、context 树：字段层 type 必须是 dataType

自拼 context 把字段 `type` 写成 `DTO` → 平台回：

```
FORMULA_6033  Context property: expNum Unsupported data type: DTO
```

正确形态（唯一实现 `expression_build.node_context_entry`）：

```
顶层    type=OBJECT, selectable=false, paramCategory=DTO, ext={id:<DTO>,javaType:<DTO>}
出参    type=OBJECT|ARRAY, selectable=true, paramCategory=OBJECT, ext={id:<DTO>}
字段    type=<dataType>, selectable=true, paramCategory=<dataType>,
        ext={id:<字段全类名>,relationType:NONE,javaType:<javaType>}
```

★ 也就是说：**不允许在表达式引擎里重新拼 context 层级**——
`ExpressionCompiler.register_node_output()` 内部直接调 `node_context_entry`。

## 三、FUNCTION token 形态：subOps，不是平铺

```
{"type":"FUNCTION","value":"len","desc":"...","subOps":[[{VARIABLE...}]]}
```

- 参数在 `subOps` 二维数组（外层=参数组，内层=token 序列）
- 把参数平铺进顶层 tokens → 平台 `BOOT_3000`（无 message，难定位）
- 函数名必须在 88 目录内（`expression_fill.FUNCTION_CATALOG`）：
  `len` ✓ / `stringLength` ✗（不存在的名字会被目录校验直接拦）

## 四、★ 语义保真：嵌套必须显式加括号

平台 transform **只做 token 平铺翻译，不还原 AST**：

```
AST:  Logic("AND", A, Logic("OR", B, C))
无括号 tokens → "A && B || C"     ← 被解析成 (A&&B)||C，静默语义漂移
带括号 tokens → "A && ( B || C )"  ← 正确
```

实测 OPERATOR `(` `)` 平台接受且翻译保留括号（三种写法全 PASS）。

编译规则：
- 子项是复合表达式且 op 不同 → 加括号
- op 相同但**不满足结合律**（SUB/DIV）且非首项 → 加括号
  （`a-(b-c)` ≠ `a-b-c`，左结合陷阱）
- AND/OR/ADD/MUL 同 op 嵌套不加（结合律成立）

## 五、VARIABLE token 三级

```
<_出参名>.<_出参名>.<字段名>      ← 三级，写两级报 FORMULA_6058
```

## 六、平台实证结果（2026-11-01）

6 场景全 PASS（check `content:true` + transform 出 executableExpr）：

| 场景 | translation |
|---|---|
| s1 常量比较 | `1 > 0` |
| s2 前序出参引用 | `查询结果.expNum > 0` |
| s3 函数 | `len(查询结果.expText)> 0` |
| s4 AND 内嵌 OR | `查询结果.expNum > 0 && ( ... = 1 \|\| ... = 2 )` |
| s6 FOR 停止条件 | `查询结果.expNum * 1 <= 999` |
| s7 变量赋值算术 | `查询结果.expNum + 1` |

## 七、能力矩阵（P2-1）

643 条发布语料 → **38 个真实槽位组合**（宿主节点×槽位路径，子节点递归时宿主切到最内层）。

- 值槽 35 个：Simple / SelectParam 两态为主
- 条件右值槽 3 个：CONSTANT / CONTEXT_VARIABLE / EXPRESSION 三态
  （RETRIEVE rightParams 1096 条：CV 743 / CONST 220 / EXPR 133）
- `FOR.forStart` 恒 Simple；`CREATE_LIST.value[]` 全 SelectParam

矩阵落在 `core/facts/udc/microflow/expression-capability-matrix.json`，
扫描器 `tools/core/expression/scan_capability_matrix.py`（语料更新后重跑即可）。

## 八、值槽包装：表达式对象必须包三层

表达式引擎产物 `{title, schema}` 直接塞进 `value` / `forEnd` 等槽位，平台报：

```
value.type PROPERTY_IS_REQUIRED     ← 缺 type 判别键
value.type DATA_INVALID
```

真实形态（语料 **1073 条** `value.type=Expression` 样本）：

```json
{"type": "Expression", "simple": null, "desc": "...",
 "expression": {"title": "...", "schema": "<JSON字符串>"}}
```

统一入口 `expression_model.to_value_slot(expr)`；
构造器（`create_variable`/`change_variable`）入口用 `_as_slot()` 自动归一 ——
**调用点不再各自包装**（重复实现会漂移，`new` 与 `old` 包装差一个键就是一次 DATA_INVALID）。

## 九、BASIC 变量的 structure 必须 None（模板残留陷阱）

```python
create_variable(b, "nCount", data_type="INTEGER", value=simple(0))
# 修复前 structure = {"id":"com.seeyon.boot.transport.PageInfo","label":"分页对象", ...}
```

语料裁决：**429/429** BASIC `CREATE_VARIABLE` 的 `structure` 恒 `None`；
**1053/1053** `CHANGE_VARIABLE` 同样。模板基座带的 PageInfo 会让引用解析
把基本变量当实体去查（查不到 → G7 误杀，或引用到错误的 DTO 上下文）。

## 十、`branch()` 的 conditions 入参语义

旧实现只认 `{"type":"Expression","expression":{...}}` 一种包装；
传 `{"expression": <expr对象>, "nodes": [分支体]}` 时把**整个 dict** 当表达式塞进去 →
落库成 `{"expression":..., "nodes":[...]}` → checkSchema `PROPERTY_IS_REQUIRED`
（条件表达式未配置）。现在两种写法都认，分支体正确挂到 `conditions[i].nodes`。

## 十一、保存链编排（P2-4）

`components/udc/microflow/save_pipeline.py`：

```
save（create → checkSchema/update）
  → readback（DP.get → dataSchema 与提交对象做节点签名比对）
  → expression_verify（对**回读对象**跑 check/transform/roundtrip）
  → l2_check（read_state + check_state）
```

- 状态机：`CONSTRUCTED` → `SCHEMA_VERIFIED` → `UI_VERIFIED`（L2 通过才升）
- ★ 表达式校验只认**回读**对象：平台保存会归一（casing/默认值），本地 delta ≠ 库里对象
- roundtrip：库里已有 `executableExpr` 与本次 transform 不一致 = 表达式已变质
- L2 打开的正确 URL：`/main/child-frame/udc/app-design/rule?appId=<app>&id=<mid>`
  （开 `.../rule/microflow/editor/<mid>` 会 `chrome-error://chromewebdata/`）

实测 2026-11-01（真业务流 RETRIEVE + BRANCH 条件 + 变量赋值 + 引用变量）：
`save PASS / readback PASS / expression_verify PASS（2 条表达式）`；
L2 阶段因**浏览器到平台的网络通路故障**未执行：
Chrome 内 `net::ERR_TIMED_OUT`（同机 curl 正常、baidu 正常）→ BLOCKED，非代码问题。

## 十二、传输层统一

`deploy._req` 与 `LiveRefs._gql` 都改走 curl（`_req` 内部实现），
urllib 仅作 curl 缺失时的回退。原因见 §一（网关 TLS 指纹）。

## 十三、`/expression/check|transform` 不能离线校验字段引用（重要修正）

实测（2026-11-01）：把**平台自己保存过的真实表达式**（语料 designData.context + tokens）
原样重发 `/service/udc/expression/check`，同样报：

```
FORMULA_6058 CVariable :微流程.查询单条数据(1).投标报备申请_1 [投标报备申请].本部实体
              does not exist in context, please confirm!
```

而同一表达式的 `runtimeData.executableExpr` 明明是
`entityIsNotNull(_RETRIEVE_PjOUCi._RETRIEVE_PjOUCi.benbushiti)` —— 结构完全正确。

结论（修正 P2 的一个过度结论）：

| 场景 | `/check` 结果 |
|---|---|
| 纯常量表达式（无 VARIABLE token） | 通过 —— P2 六场景里的常量/算术/函数都属于这类 |
| 含 VARIABLE token 的字段引用 | **必失败**，即使 context 与 tokens 完全正确 |

原因：这两个接口按 `context` 里的**显示路径**（`微流程.查询单条数据(1).xxx`）解析，
而这条路径由**设计器运行期**根据完整流程树生成，离线拼不出来。

所以：
- **不要**用 `/expression/check` 作为"字段引用是否正确"的校验手段。
- 字段引用的真校验只有两条：①`ExpressionCompiler` 的静态类型检查（本地）；
  ②**落库后 `checkSchema`**（平台按真实流程树解析）。
- `save_pipeline.expression_verify` 里对含 VARIABLE 的表达式，`check` 失败
  **不构成阻断**——应以 checkSchema 为准。这一点早期实现是错的。

## 十四、`executableExpr` 平台不会自补（P4 的核心边界）

三个决定性实验（2026-11-01）：

| 提交内容 | checkSchema | 回读 executableExpr |
|---|---|---|
| designData + runtimeData{executableExpr: 真实值} | PASS | 原样保留（278 字） |
| designData + runtimeData{}（缺 executableExpr） | **BOOT_3000 拒绝** | — |
| 只有 designData（无 runtimeData） | PROPERTY_IS_REQUIRED | — |
| designData + runtimeData{executableExpr: "PLACEHOLDER"} | **PASS** | PLACEHOLDER 原样保留 |
| designData + runtimeData{executableExpr: ""} | **PASS** | 空 |

结论（必须记住）：

1. **checkSchema 不校验 executableExpr 的内容**——占位串、空串都能过。
2. **平台绝不自己补 executableExpr**——提交什么就存什么。
3. executableExpr 是**运行时真正执行的代码**（`entityIsNotNull(_X._X.f)` 这类），
   它由 `/expression/transform` 生成，而 transform 对含 VARIABLE 的表达式
   **离线不可用**（§十三）。
4. 语料 1040/1040 表达式都有 executableExpr——即真实落库的全部是 transform 产物。

**所以：含字段引用的表达式，executableExpr 只能由设计器运行期生成。**
全自动 P4 生成这类节点时，必须：

- 本地生成正确的 `designData`（translation / resultTypeInfo / context / tokens）
- `executableExpr` 填占位串让 checkSchema 过
- **标记 `needs_ui_finalize=True`**，交付时明确告知：该节点必须进设计器
  点一次「确定」由平台重算 executableExpr，否则运行期表达式为空

把这条写死成断言，不要在 P4 里假装全自动。

## 十五、★ 结论反转：`/check` 与 `/transform` 对含 VARIABLE 的表达式**完全可用**

**（2026-11-01 P5 实测推翻 §十三/§十四 的判断）**

### 15.1 决定性证据

从设计器点击「确定」时抓到的真实请求（`/service/udc/expression/transform`），
**原样离线重放**（curl + Cookie，无浏览器参与）：

```
POST /service/udc/expression/transform
→ {"status":0,"code":"BOOT_0000","message":"SUCCESS"}
```

返回的 `executableExpr` 与设计器当场生成的**逐字节一致**。

同一请求体发 `/service/udc/expression/check` → `{"status":0,"data":{"content":true}}`。

**即：含 VARIABLE token 的表达式，两个接口都能离线调用。**

### 15.2 真实请求体（5 字段，缺一不可）

```json
{
  "resultTypeInfo": "BOOLEAN",
  "schemas": [ {schemas 树，见 15.3} ],
  "tokens": [ {VARIABLE/OPERATOR/CONSTANT/FUNCTION token} ],
  "isMultiSelect": false,
  "terminalSupportType": "BACKEND"
}
```

### 15.3 schemas 树结构（transform 需要完整三层）

```
schemas[0] = {
  type: "OBJECT", description: "<节点 caption>", name: "<outputName>",
  selectable: false, skip: true,
  uniformityParams: {paramId: "<DTO 全名>", paramCategory: "DTO",
                     extensionProperties: "{\"id\":...,\"javaType\":...}"},
  properties: [ {                        ← 第二层：输出名
    name: "<outputName>", description: "<实体名>_1 [<实体名>]",
    type: "OBJECT",
    uniformityParams: {paramId: "<DTO>", paramCategory: "OBJECT", ...},
    properties: [ {                       ← 第三层：字段
      name: "jdbcUrl", type: "STRING", description: "JDBC URL", sort: 11,
      uniformityParams: {paramId: "<DTO>.jdbcUrl", paramCategory: "STRING",
                         extensionProperties: "{\"id\":...,\"relationType\":\"NONE\",\"javaType\":\"java.lang.String\"}"}
    } ]
  } ]
}
```

★ `paramCategory` 三层分别是 `DTO` / `OBJECT` / `<字段 dataType>`；
★ 字段层必须带 `sort`（设计器按实体属性顺序给）。

### 15.4 tokens（与 P4 已修正的形态一致）

| type | value | desc |
|---|---|---|
| VARIABLE | `<out>.<out>.<field>` | `微流程.<节点名>.<实体>_1 [<实体>].<字段中文名>` |
| OPERATOR | `==` / `&` / `\|` | `=` / `and` / `or` |
| CONSTANT | `true` | `true` |
| FUNCTION | `containsText` | `文本包含` |

### 15.5 `executableExpr` 的真实格式

```
<44 字符 Base64> + <URL 编码的表达式>
```

例：
```
93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=+%28++%28+_X._X.enabled+%3D%3D+%27true%27+%29...
```

解码后 = `( _X._X.enabled == 'true' ) && containsText(_X._X.jdbcUrl,'mysql')`

★ 前缀 44 字符（Base64 解 32 字节）在**不同表达式之间完全相同**——
单变量表达式 `_X._X.enabled` 也是同一前缀。说明它是**固定标记/签名**，
不随表达式内容变化，**不需要逆向，也不需要生成它**：由 transform 返回。

### 15.6 为什么 P4 当时判定"不可用"

P4 时期报 `FORMULA_6058 xxx does not exist in context`，真实原因是
**DTO 的 schemas/context 结构不对**（`_field_meta` 把 RETRIEVE 误判 BASIC、
同一节点第二个字段未进 context、token 缺 uid/desc）。这些 bug 在 P4 后期
逐个修完后，`_dto_has_variable` 的跳过分支就变成了**多余的 workaround**，
但没人回头复查它是否还需要。

**工程教训：临时绕过（workaround）必须在根因修复后复查。**
`build_remote` 现已删除该跳过分支，含 VARIABLE 的表达式统一走
`/check` → `/transform`，`needs_ui_finalize` 恒为空。

### 15.7 对 P5 的影响

**P5.2 的 CDP 设计器最终化不再是必需路径。**
`ExpressionFinalizer` 保留作为兜底（平台改版/异常时可用），
但正常交付链不需要打开浏览器。

这直接改变了 P5 的交付形态：全自动 API 交付成立。

## 十六、★ 两种 CONSTANT 形态不同（2026-11-01 实测 + 语料裁决）

**别把这两处当成同一套规则。**

### 16.1 查询条件 `rightParams[].value` → 原生类型

语料裁决（`scratch/pmp_schemas.json`，全部 CONDITION 的 CONSTANT 右值 240 条）：

| 左值 dataType | value 类型 | desc 类型 | 条数 |
|---|---|---|---|
| BOOLEAN | **bool** | **bool** | 15（15/15）|
| DECIMAL | **float** | float | 1 |
| STRING / ENUM / CTPENUM | str | str | 224 |

即：`是否启用 = true` 必须落成

```json
{"type": "CONSTANT", "value": true, "desc": true}
```

**不是** `{"value": "true"}`。写成字符串时：
- 前端设计器按**文本**渲染该值（弹窗里下拉给的明明是「是/否」）
- 后端按布尔校验拿不到布尔值

### 16.2 表达式 `tokens[].value` → 字符串

设计器真实抓包（`/expression/transform` 请求体）里，布尔常量 token 是：

```json
{"type": "CONSTANT", "value": "true", "desc": "true"}
```

**就是字符串**。所以表达式侧保持字符串，不要"顺手统一"成布尔。

### 16.3 为什么容易搞错

两处都叫 `CONSTANT`，都是「条件/表达式里的字面量」，
但一个是**查询节点的值槽**（按字段类型强校验），
一个是**表达式编辑器的 token**（一律字符串文本）。

统一成一套必然错一边。修这类问题时：
**先确认改的是 rightParams 还是 tokens，再决定用哪种形态。**

## 十七、mapping 行 vs attrs 行：selectParam 键集不同（2026-11-01 实测报错）

**同一份 selectParam 不能两种场景复用。**

### 17.1 平台真实报错（拿草稿去保存才暴露）

```
[创建变量] CREATE_VARIABLE_xxx,创建变量.mapping.value.type
                                                    → DATA_INVALID
[创建变量] CREATE_VARIABLE_xxx,创建变量.mapping.value.selectParam.dtoType
                                                    → PROPERTY_IS_REQUIRED
```

### 17.2 语料（2392 个 mapping 行）

| 项 | 事实 |
|---|---|
| `value.type` | SelectParam **2392** / Expression 68 / Simple 15 / Enum 2 / CtpEnum 3 / 空 3 |
| | ★ **没有 OBJECT**，写成 OBJECT 直接 DATA_INVALID |
| `selectParam.dtoType` | **2392/2392 = 100%**，缺了直接 PROPERTY_IS_REQUIRED |
| `selectParam` 基础 10 键 | 100%（key/name/id/description/position/path/outputName/dataType/type/javaType）|
| `appName/udcApp/multiSelect/customs/parentLabel` | 2391/2392（1 条例外，平台未报必填）|

`dtoType` 取值与 `udcApp` 的配对：
- `CUSTOM`(2187) + `udcApp=false`
- `SUB_ENTITY`(204) + `udcApp=true`

### 17.3 attrs 与 mapping 的键差异

| 只在 attrs 出现 | 只在 mapping 出现 |
|---|---|
| nodeInfo / iconKey / title / generics / disabled / hasPagination / relationEntityFullName | enums |

**mapping 行绝不能带 UI 键**（nodeInfo/iconKey/title/…），语料里一个都没有。
代码走 `_to_mapping_select_param()` 规范化：保留必填键 + 补默认值 + 剥离 UI 键。

### 17.4 验证记录

构造 `auto_map_from` 形态 → create → 回读 `mapping[0].value.type=SelectParam`
→ publish `ok=True state=RELEASE errors=0`。

历史流程 `verifyCvMapping5618` 的同类报错是早期版本产物，当前代码重新生成可通过。

## 十八、BASIC 变量引用：两级 vs 三级（语料 319 条全量核对）

| 形态 | 条数 | 含义 | 特征 |
|---|---|---|---|
| `X.X`（两级）| 292 | BASIC 变量整节点引用 | 两段**同名** |
| `X.X.<字段>`（三级）| 27 | 实体型变量的字段引用 | 三段，末段是字段名 |

判据：`field == outputName` → 两级；否则三级。
写错成三级 `X.X.X` 平台回
`FORMULA_6058 CVariable :xxx does not exist in context`。

## 七、运行时验证（2026-11-03，P6EX01 / P6EX03）

表达式第一次拿到**运行期**证据：在 FILTER 里挂表达式，用 SIZE 数命中行、写库回读。

| 能力 | 表达式 | 期望 | 实测 |
|---|---|---|---|
| 算术 ADD | `processedRows + 3 > 5` | 3 | **3** |
| 逻辑 AND | `pr > 2 && pr < 9` | 2 | **2** |
| 逻辑 OR | `pr < 2 || pr > 8` | 2 | **2** |
| 比较 NE | `taskId != '…-S3'` | 4 | **4** |
| 日期函数 | `year(createTime) == 2026` | 5 | **5** |
| 条件表达式 | `IF(pr > 5, 1, 0) == 1` | 2 | **2** |
| 文本函数 | `containsText(taskId, '-S3')` | 1 | **1** |
| 布尔函数 | `isNotNull(taskId)` | 5 | **5** |

### ★★ 两个真坑

1. **布尔函数不能包 `== true`**。`containsText(a,b) == true` 恒为 false（实测 0 条），
   裸函数才对（1 条）。`parse_filter_spec` 已自动解包 `{op:EQ, right:{const:true}}`。
2. **`containsText` 参数顺序是 (被查文本, 子串)**。反过来恒 0 —— 已用反例流程
   （T4 实测 0）钉死，别再按「先模式后文本」猜。

### FILTER 支持任意布尔表达式

```json
{"kind":"list_operation","op_type":"FILTER","list_node":"ra",
 "filter":{"expr":{"logic":"AND","items":[
   {"op":"GT","left":{"arith":"ADD","items":[{"field":"processedRows"},{"const":3}]},
    "right":{"const":5}},
   {"op":"EQ","left":{"fn":"containsText","args":[[{"field":"taskId"}],[{"const":"-S3"}]]},
    "right":{"const":true}}]}}}
```

字段按**实体字段**解析（同一 DTO），不是按节点别名 —— 见
`microflow_filter.parse_filter_spec`。

### 尚未验证

`SUB/MUL/DIV`、`addDay/dateDiff/dateToString` 等日期函数、聚合函数（需明细表上下文）、
枚举/变化/组织隶属类。函数目录只给 `paramCount` 和 `argDescs`，**不给参数类型**，
所以自动生成函数调用时必须按中文描述推类型，或直接拿真实字段试编译。

### 函数目录生成覆盖率（2026-11-03 扫描）

在真实实体 context 下（`build_ast_expression`），88 个函数逐个试编译：

| 类别 | 可生成 | 总数 |
|---|---|---|
| 日期函数 | 16 | 24 |
| 文本函数 | 10 | 17 |
| 数学函数 | 9 | 10 |
| 基础函数 | 9 | 15 |
| 变化函数 | 1 | 1 |
| 条件函数 | 1 | 1 |
| 聚合函数 | 0 | 18 |
| 枚举函数 | 0 | 2 |

**46 / 88 可自动生成并被平台接受。** 剩余 42 个分两类：

1. **聚合函数 18 个 + 枚举 2 个**：需要「明细表（子实体列表）」字段做参数 ——
   当前测试实体 `迁移断点` 没有子实体字段，无法构造，不是能力缺失。
2. **约 24 个**：参数类型不符。函数目录只有 `paramCount` + `argDescs`（中文），
   **没有参数类型**，自动生成时只能按关键词猜类型，猜错就 `FORMULA_6158`
   `the N parameter type does not match`。

结论：要「全自动生成 88 个函数」还差两件事 —— ①给目录补参数类型（可从
argDescs 中文人工标定，或反编译前端 bundle 里的函数签名）；②拿一个含子实体
字段的实体做聚合函数验证。
