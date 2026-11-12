# 表达式公用层（Expression Common Layer）事实格

> **域归属：跨域公用**。不属于实体域、不属于设置域、也不属于流程域。
> 它在多处出现，但引擎只有一套 —— 本件记录的是那一套。
>
> 证据等级：**VERIFIED_STATIC_BYTECODE**（CFR，boot-starter-formula 5.3.318 全量）
> ＋ **LIVE PASS**（test2，2026-10-23 实测）
> 实现：`components/udc/expression/`
> 权威字节码：`<MAVEN_REPO>\com\xiaozhua\boot-starter-formula\5.3.318\boot-starter-formula-5.3.318.jar`
> 反编译件：`docs/audit/artifacts/decompiled/r38_full`（202 个 .java）

---

## 〇、本目录 4 份（先看这张表）

本目录此前只有本文一篇事实格，另外 3 份（引擎 / 函数 / 系统变量）**没有索引** ——
读者只能平铺 `grep`。这张表就是入口。

| 文件 | 字节 | 行 | 证据等级 | 讲什么 |
|---|---:|---:|---|---|
| **`README.md`（本文）** | — | — | STATIC_BYTECODE + LIVE | 公用层事实格：跨域归属、引擎语义、token 形态、字节码锚点 |
| `engine.md` | 18,018 | 421 | STATIC（bundle 反编译） | 前端调用链与组成：定位模块 → 解导出表 → 逐层展开被调函数 |
| `functions.md` | 22,530 | 800 | LIVE（`preset/list`） | **88 个函数 / 8 组**，生成器 `gen_function_catalog.py` 产出，**勿手改** |
| `system-variables.md` | 16,528 | 189 | LIVE（`preset/list`） | **131 项系统变量 / 4 组**，生成器 `parse_preset_full.py` 产出，**勿手改** |

后 3 份合计 **57,076 B / 1,410 行**（不含本文）。

> **为什么不写本文自己的字节**：这张表在本文内部，写完它本文就变大了 ——
> 自我引用的数字必然过期。要看本文大小直接 `wc -c`。
>
> **同目录另有 INDEX 吗**：没有。`udc/microflow/` 因为 60 份才单独建 `INDEX.md`；
> 本目录只有 4 份，这张表就是索引，不另起文件。

---

## R-E1 Capability — 它到底是什么

表达式设置在设计器里出现于至少五处：

| 出现位置 | 域 | 用途 |
|---|---|---|
| 字段「默认值」 | 实体 | 新建时自动填值 |
| 字段「计算值」 | 实体 | 由其它字段推导 |
| 字段「取值范围」 | 实体 | 值域约束 |
| 字段集 / 参数 | 设置 | 默认值、参数取值 |
| 页面规则 / 页面事件 | 菜单 | 条件、赋值 |
| 微流程节点入参 / 条件分支 | 流程 | 取值、分支判断 |
| 实体规则 / 生单扣减规则 | 规则 | 条件 |

**但端点只有一个 Controller**：`ExpressionController`（10 个方法）。
**校验只有一条链**：`ExpressionValidator → FilterChain → 4 个 Filter 实现`。
**函数只有一套**：88（BACKEND）/ 81（FRONTEND）。

⇒ 各模块的差别**不在引擎**，只在两处，且都在本层注册表里：

```
paramType            变量面（变量从哪来）      @ParamLoadService(type=...)
terminalSupportType  函数面（前端还是后端跑）  preset/list 的 body
```

## R-E2 Version

| 项 | 值 |
|---|---|
| 引擎 | `boot-starter-formula` 5.3.318 |
| 端点前缀 | `/service/udc/expression` |
| 端点总数 | 10（`ExpressionController` 逐方法数，见 `endpoints.py`） |
| 函数组数 | BACKEND 8 组 / FRONTEND 6 组 |

本机同族 JAR：5.3.308 / 5.3.309 / 5.3.313 / 5.3.318。**跨版本引用前先确认版本**——
`ExprParamTypeEnum` 的尾空格坑在 5.3.308~5.3.318 一致，但函数计数可能随版本变。

## R-E3 Input — 三个必调接口的真实 body

### 3.1 运算符（GET，无 body）

```
GET /service/udc/expression/operator/list
→ { operators: [18 个], functions: [4 个] }
```

★ 只接受 GET。POST 返回 **405**（实测，不是参数问题）。
★ `functions` 只有 4 个（isNull / isNotNull / contains / thereIn），**不是**完整函数目录。

18 个运算符按 opType 分布：ARITHMETIC 5 / COMPARE 6 / LOGIC 3 / BOOLEAN 2 / SYMBOL 2。

### 3.2 函数树 + 系统变量（POST）

```
POST /service/udc/expression/preset/list
body = {"terminalSupportType": "BACKEND"}
→ { presetVariableInfo: [4 组 131 项], functionInfo: [8 组 88 个] }
```

**这个接口最重**——完整的函数与系统变量都在这里。

变量分组：organization 95 / date 33 / env 2 / plugin 1。

### 3.3 变量面（POST）

```
POST /service/udc/expression/schema
body = {"appId": <appId>, "extension": "", "ids": [], "idsStr": [],
        "idsTuple": [], "paramType": "CONFIG_PARAM"}
```

⚠ body 形态**随 paramType 变**：
- `CONFIG_PARAM` → 要 `appId`，`ids` 空即可（实测返回 3 个应用参数）
- `ENTITY` 系 → 要 `ids=[实体id]`，缺则 `UDC_EXPRESSION_7005`
- 既有事实另记：`ENTITY` 场景带 `appId` 反而报 `BOOT_3000`（见
  `attribute_expression_constraints.py` 注释，2026-10-16 实测）
  → **两种口径并存，按 paramType 分组验证，不要互相套用**

## R-E4 Required — 变量链接（本层最核心的一条）

`schema` 返回的每个节点都带 `uniformityParams`：

```jsonc
// 实体根
{"name":"ysBill4081","type":"OBJECT",
 "uniformityParams":{"paramId":"-8472597639301749281","paramCategory":"Entity"}}
// 字段
{"name":"id","type":"BIGINTEGER",
 "uniformityParams":{"paramId":"-9128484922878356860","paramCategory":"Attr"}}
// 应用参数
{"name":"zxjPageSize","type":"INTEGER",
 "uniformityParams":{"paramId":"9045320026154749411","paramCategory":"CONFIG_PARAM",
                     "extensionProperties":"{\"dataType\":\"INTEGER\"}"}}
```

`paramCategory` 值域实测 3 类：`Entity` / `Attr` / `CONFIG_PARAM`。

**变量 token 必须带 `paramId`**，否则 `VariableCheckFilter` 在
`NODE_NOT_FOUND_IN_SCHEMA_ERROR` 处失败（`FORMULA_6058` 一族）。

⇒ 这就是「每个函数变量、实体、参数都需要通过参数链接」的实体。
- 函数本身可以不链接（纯函数调用，参数是常量也行）
- **但只要牵扯到变量/字段，一定走 paramId**

## R-E4.1 变量必须绑定 schemas（FORMULA_6058 的唯一正解）

只给 token 带 `paramId` **不够**。`VariableCheckFilter` 是拿 token 去
`ExpressionSaveDto.schemas` 这棵**树**里找，不是拿 paramId 去库里查。

LIVE 实测（test2，2026-10-23，实体 ysFull6956 / 字段 f03int）：

| schemas 内容 | check 结果 |
|---|---|
| `[]` | `FORMULA_6058` 变量:整数字段 在上下文中不存在 |
| `[实体根节点]` | `FORMULA_6058` ← **放根没用** |
| `[字段节点原样]` | `BOOT_0000` content=True ✅ |
| `[精简字段节点]` | `BOOT_0000` content=True ✅ |

精简节点只需 5 个键：
`name / description / type / selectable / uniformityParams`

⇒ 规则：**变量用到的每个字段，都要把它自己的节点放进 `schemas`**。
实体根不能替代——根节点的 `properties` 不会被当成可引用变量表。

系统变量不需要绑定：SYSTEM 走 `ExpressionPresetRunner.loadSystemVariable`
的全局表，不在 schemas 里查。

实现：`components/udc/expression/schema_binding.py`
（`bind_schemas` / `check_binding` / `required_param_ids`）

## R-E4.2 两条值链互斥 + 落位映射

`components/udc/expression/mapping.py` 把「写哪两列、用哪个 paramType」集中声明：

| 域 | 用途 | paramType | design 列 | runtime 列 |
|---|---|---|---|---|
| entity | default_value | ATTR_DEFAULT_VALUE | default_value_expr_design | default_value_expr_runtime |
| entity | calculated_value | ENTITY | expression_design_data | expression_runtime_data |
| entity | scope | ATTRIBUTE_SCOPE | —（单列） | value_scope_expression |
| setting | default_value | CONFIG_PARAM | default_value_expr_design | default_value_expr_runtime |

**已知不存在的落位点**（显式登记，防未来臆造）：

```
setting / calculated_value   字段集只有「默认值」入口，没有计算值
setting / scope              字段集没有取值范围入口
```

★ 写计算值时必须把 default 对**显式清空**（空字符串）。
`update` 是 IGNORE_NULL 语义，传 null 清不掉。

★ **清空 default 表达式不会回滚 `default_value_caption`**（实测）：
caption 是服务端在写 default 对时派生的，清空后它保留上一次的文本。
需要干净就重新写一次 default 对（写空也算一次写），或接受该残值。

## R-E5 Execution — 写一条表达式的正确顺序

```
1  schema(paramType, ids)          取变量面，拿 paramId
2  preset/list(terminal)           取函数树，拿函数名与参数说明
3  组 tokens[]                     用 token.py 的构造器
4  check(ExpressionSaveDto)        纯校验，无落库副作用
5  transform(ExpressionSaveDto)    设计态 → 运行态双态
6  落到目标域的写接口               设计域自己管（见各行「落库」事实件）
```

**第 5 步不可跳**：平台要的是 designData + runtimeData 两态；
只写 design 不写 runtime，代码生成拿不到可执行表达式。

`ExpressionSaveDto` 键（LIVE 全过）：
`resultTypeInfo / schemas / tokens / isMultiSelect / terminalSupportType / sourceAppName / version`

## R-E5.5 前端侧扩展（bundle 实证）

后端靠 `@ParamLoadService`，前端靠**注入 customSchema**。两者叠加才是面板里那棵树。

### 5.5.1 customSchema —— 前端扩展点

```js
initialState: {
  customSchema: (() => {
    if (flowBasicInfo?.type === "FUNCTION")
      return [{type:"FRONT_NODE", name:"udc", description:"公共页面规则", schemas:[...]}]
    return isPageCtx ? [{type:"FRONT_NODE", name:"udc", description:"页面规则", schemas:[...]}]
                     : defaultSchemas
  })()
}
```

- 节点 `type` **只有 `FRONT_NODE`** 一种
  （bundle 计数：FRONT_NODE 20，BACK_NODE / ENTITY_NODE / MICRO_FLOW_NODE 全 0）
- `name` 固定 `"udc"`
- `description` 是模块标签：`公共页面规则` / `页面规则` / `页面设计`

### 5.5.2 terminal 由微流程节点 type 决定（不是模块等级）

```js
mode = ["FRONTEND","FUNCTION"].includes(flowBasicInfo?.type) ? "FRONTEND" : "BACKEND"
```

⇒ `type ∈ {FRONTEND, FUNCTION}` → FRONTEND；其余（SERVICE 等）→ BACKEND。
这才是「同一模块能力不同」的真相。

### 5.5.3 APP_PARAM 默认不加载

```js
serverParams: { appId, unLoadPresetSchema: ["APP_PARAM"] }
```

「应用参数」分组默认不出现在变量树里，需要时显式放开。**不是 bug。**

### 5.5.4 resultType 归一化（最容易漏）

```js
N = e => (e === Enum || e === CtpEnum) ? Long : e
```

⇒ 枚举 / 选项集的结果类型一律按 **LONG** 提交。
自己写 `resultTypeInfo` 时写 `Enum` 会被类型兼容检查拒。

### 5.5.5 bundle 里的 `DESIIGN` 拼写

```js
mode: "DESIIGN | ".concat(y, " | BACKEND")
```

平台前端原文就是这个拼写。见到别当 bug 去"修"。

## R-E6 Side Effects + 回滚

| 端点 | 副作用 |
|---|---|
| `operator/list`、`preset/list`、`schema`、`system-variable/*`、`system/values` | **无**（纯读） |
| `check` | **无**（纯校验，可反复调） |
| `transform` | **无落库**（只算双态，返回 DTO） |
| 落到域写接口（如 `udc/entity/attribute/update`） | 有 —— 由各域事实件负责 |

★ `check` 与 `transform` 都是无副作用的，可以放心当探针反复调。

## R-E7 Known Constraints

1. **token.type 值域恰 5 值**：`CONSTANT / VARIABLE / SYSTEM / FUNCTION / OPERATOR`。
   值域外（如 `SYSTEM_VARIABLE`）⇒ `BOOT_3000` **message 为 null** —— 几乎无法定位，
   必须在本地结构校验拦掉。
2. **两套 paramType 枚举不要混**：
   - `ExprParamTypeEnum`（formula 层）= ENTITY / BPM / BPMAUTO / PARAM_CONFIG / EVENT_ATTR
     其中 `BPMAUTO`、`PARAM_CONFIG` 的 code 字面量**带尾空格**
   - `@ParamLoadService` 注册表（真正生效）= CONFIG_PARAM / ENTITY / ATTR_DEFAULT_VALUE /
     ATTRIBUTE_SCOPE / EVENT_ATTR
   ⇒ 传 `PARAM_CONFIG` 报 BOOT_3000，传 `CONFIG_PARAM` 才通。
3. **terminalSupportType 缺失即 BOOT_3002**；`DESIGN` / `RUNTIME` 也报 3002。
4. **系统变量两条解析通路不等价**：全名（`system.currentDateTime`）取其 resultType，
   短名（`currentDateTime`）只要同名于某函数就被当函数调用、取函数返回类型。
   已知分裂：`currentTime`（STRING vs TIME）、`currentDateTime`（DATE vs DATETIME）。
   要稳定类型走全名。
5. **函数面只受 terminal 影响，不受模块影响**：同一模块配 BACKEND/FRONTEND 拿到不同函数集。
   别把「页面规则弱、微流程强」当模块等级，那是 terminal + paramType 的组合结果。

## R-E8 Evidence（逐条实测，禁转述）

```
LIVE 2026-10-23 test2 appId=8704025620829192834

operator/list          GET  200  BOOT_0000  operators=18 functions=4
                       POST 405  ← 只接受 GET
preset/list BACKEND    POST 200  BOOT_0000  函数 88 / 8 组   变量 131 / 4 组
preset/list FRONTEND   POST 200  BOOT_0000  函数 81 / 6 组   变量 131 / 4 组
preset/list ALL        POST 200  BOOT_0000  函数 81           变量 131
preset/list ""         POST 200  BOOT_3002
preset/list DESIGN     POST 200  BOOT_3002
preset/list RUNTIME    POST 200  BOOT_3002

schema CONFIG_PARAM           BOOT_0000  3 项（fujian / zxjApiBaseUrl / zxjPageSize）
schema ENTITY + ids           BOOT_0000  实体根 1 项，46 个 children
schema ATTR_DEFAULT_VALUE     BOOT_0000
schema ATTRIBUTE_SCOPE        BOOT_0000
schema EVENT_ATTR             UDC_EXPRESSION_7005  ← 已注册但实体上下文传法未定
schema MICROFLOW / BPM / BPMAUTO / PARAM_CONFIG  BOOT_3000  ← 未注册

schema ENTITY 节点 paramId 实证：
  ysBill4081  OBJECT     paramId=-8472597639301749281  cat=Entity  children=46
  id          BIGINTEGER paramId=-9128484922878356860  cat=Attr
```

## R-E9 Verified

| 项 | 状态 |
|---|---|
| 10 个端点签名与 method | **VERIFIED_STATIC**（ExpressionController 逐方法） ＋ LIVE 4/10 |
| 18 运算符 / 5 类 | LIVE PASS |
| 88 / 81 函数、8 / 6 组 | LIVE PASS（三档 terminal 实测） |
| 131 系统变量 / 4 组 | LIVE PASS |
| token 5 值域 | **VERIFIED_STATIC**（TokenTypeEnum）+ LIVE（值域外 BOOT_3000） |
| 5 段校验链 | **VERIFIED_STATIC**（类职责）；单段行为未逐条构造反例 |
| paramId 链接机制 | LIVE PASS（schema 节点实证） |
| 4 个 @ParamLoadService 注册 | **VERIFIED_STATIC**（全库 grep）+ LIVE 3/4 |
| `EVENT_ATTR` | **UNVERIFIED** —— 已注册但实体上下文怎么传没定 |
| `system/values`、`system/list` 等 4 个端点 | **UNVERIFIED** —— 签名已知，未实调 |
| 实体域 默认值 / 计算值 端到端写库 | **LIVE PASS**（见 R-E10） |
| 取值范围（ATTRIBUTE_SCOPE）端到端 | **UNVERIFIED** —— paramType 已验，写库链未跑 |
| 页面规则 / 微流程规则的表达式落库 | **UNVERIFIED** —— 各自落位列未摸 |

## R-E10 本轮端到端实测记录（2026-10-23，可复算）

实体 `ysFull6956`（id=-2537349473285092530），test2，appId `8704025620829192834`。

### 10.1 默认值 → `f12doc`（DOCUMENTNUMBER → resultTypeInfo=STRING）

```
表达式  dateToString(system.currentDate, "yyyy-MM-dd")
tokens  FUNCTION:dateToString[ SYSTEM:system.currentDate , CONSTANT:yyyy-MM-dd ]
schemas 绑定 0 个（无变量）
check       BOOT_0000  content=true
transform   translation='日期转文本(系统日期,yyyy-MM-dd)'  runtime 98 字符
写库        udcEntityAttributeUpdatePost → BOOT_0000 status=0
回读
  default_value                  ''
  default_value_caption          '日期转文本(系统日期,yyyy-MM-dd)'   ← 服务端派生
  default_value_expr_design      584 字符  translation 同上  context=[]
  default_value_expr_runtime     120 字符
  expression_design_data         空   ← 计算值列未被污染
  expression_runtime_data        空
```

### 10.2 计算值 → `f04bigint`（BIGINTEGER → resultTypeInfo=BIGINTEGER）

```
表达式  f03int + f03int
tokens  VARIABLE:f03int(paramId=-6040618203145140416) / OPERATOR:+ / VARIABLE:f03int
schemas 绑定 1 个 → [{'name':'f03int','type':'INTEGER',...}]
check       BOOT_0000  content=true      ← 不绑 schemas 时是 FORMULA_6058
transform   translation='整数字段 + 整数字段 '  runtime 71 字符
写库        calculate=COMPUTE + expression 对 + default 对清空（""）
回读
  calculate                      1（= COMPUTE）
  default_value                  '0'
  default_value_caption          '整数字段 + 整数字段 '   ← 上一轮误写的残值，未回滚
  default_value_expr_design      空   ← 已按互斥清空
  default_value_expr_runtime     空
  expression_design_data         766 字符  translation='整数字段 + 整数字段 '
                                          context=[{f03int 节点}]
  expression_runtime_data        93 字符
```

### 10.3 本轮踩到的两个错（都已修正并写进上头事实）

1. `schemas=[]` 就提交 → `FORMULA_6058`。**变量必须绑 schemas**。
2. 第一版把 default 对和 expression 对**同时写**给计算值字段
   → `default_value_caption` 被填成计算值表达式。两条值链必须互斥写。

### 10.4 执行器

`tools/core/expression/write_attribute_expression.py`

```bash
# 只校验不写（check + transform 无副作用）
python tools/core/expression/write_attribute_expression.py \
  --app-id <id> --entity-id <eid> --field f04bigint \
  --purpose calculated_value --expr 'f03int + f03int' --dry-run

# 写库需显式确认
... --i-have-write-authorization
```

内置闸门：变量绑定校验 / resultType 类型匹配 / design 缺 context 拒写 /
两条值链互斥清空 / 写后回读。

## 与既有资产的关系（避免重复造）

| 既有件 | 内容 | 本层的关系 |
|---|---|---|
| `components/udc/attribute_expression_constraints.py` | 实体字段级别的表达式写链（落库列、三态计算、不变量） | **保留**。它是 entity 域的落库实现，本层是它依赖的公用底座 |
| `core/facts/udc/write-chain/expression-token-type-domain.md` | token 值域 + SYSTEM 两通路 + 类型分裂 | 本层 token.py 的权威来源，勿两处各写一份 |
| `core/facts/udc/setting/expression-component/component.md` | 设置域「默认值 + → 高级模式」的 CDP 链路 | 设置域的 UI 链路，本层是它的接口底座 |

⇒ 本层**不搬**上述文件的内容，只做「公用契约 + 扩展点」的收敛；
  落库细节仍归各域事实件。

## R-E11 计算值/默认值的 schemas 形态：实体树 + 点路径（2026-10-23 更正）

**旧结论是错的，已作废。** 早期记的是「变量用到的每个字段，把字段节点放进 schemas，
实体根不能替代」—— 那条能过 `check` / `transform` / DB 回读，但**页面回显直接报错**：

```
FORMULA_6058   变量:整数字段 在上下文中不存在，请确认!
```

### 三维对照实验（test2，实体 ysFull6956 / 字段 f03int，表达式 `f03int + f03int`）

| 组合 | check | transform 产物 | 页面 |
|---|---|---|---|
| A 扁平字段节点 + `value="f03int"` | BOOT_0000 | context 扁平 / type=INTEGER | **报错** |
| B 实体树 + `value="f03int"` | **FORMULA_6058** | — | — |
| C 实体树 + `value="ysFull6956.f03int"` | BOOT_0000 | context OBJECT 树 / 点路径 | **正常** |

只有 **C** 可用。B 的报错文案与页面报错**一字不差**，说明页面回显走的是
「树 + 点路径」这条解析通路。

### 正确形态

```jsonc
// schemas：实体 OBJECT 树，字段挂在 properties 下
[{"name": "ysFull6956", "description": "小爪验收实体全量", "type": "OBJECT",
  "selectable": true, "enableDataI18n": false,
  "uniformityParams": {"paramId": "<实体id>", "paramCategory": "Entity"},
  "properties": [{"name": "f03int", "description": "整数字段", "type": "INTEGER",
                  "selectable": true,
                  "uniformityParams": {"paramId": "<字段id>", "paramCategory": "Attr"}}]}]

// tokens：value 带实体前缀，desc 带实体标题前缀
[{"uid": "<uuid>", "type": "VARIABLE",
  "value": "ysFull6956.f03int", "desc": "小爪验收实体全量.整数字段"}]
```

客户真实配置印证：`context=[{name:"税率配置表",type:"OBJECT",properties:[...]}]`、
`tokens[].value="shuilvpeizhibiao.shuilv"`、`desc="税率配置表.税率"`。

系统变量（SYSTEM）不受影响：仍走全局变量表，不需要 schemas 树。

### 代码入口

```
components/udc/expression/schema_binding.py::bind_schemas(tokens, schema_nodes)   # 默认 as_tree=True
components/udc/expression/token.py::build_variable_token(..., entity_name=, entity_desc=)
```

`check_binding` 现在会主动咬住两种假绿：schemas 里没有 OBJECT 树节点、
token.value 缺实体前缀。

### ★★ 最贵的教训

**check=BOOT_0000 + transform 成功 + DB 回读正确 ≠ 功能可用。**
这三步全过，页面照样报错。表达式类改动**必须看页面渲染**才叫验收。
本条以前的「LIVE PASS」就是这么误判的。

### 已 LIVE 验证的组合（页面列表 + 弹窗均正常）

```
f04bigint = f03int + f03int                                       变量 + 运算符
f06cur    = ifs(f03int > 100, f03int * 2, f03int)                 条件函数 + 比较 + 乘法
f02multi  = substring(dateToString(system.currentDate,"yyyyMMdd"),1,4)   三层嵌套 + 系统变量
```

翻译结果分别为：
`小爪验收实体全量.整数字段 + 小爪验收实体全量.整数字段` /
`条件返回(...>100,...*2,...)` / `按长度截取字符串(日期转文本(系统日期,yyyyMMdd),1,4)`
