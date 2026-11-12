# 操作契约 · 设置域 / 表达式组件（Expression Component）

> 事实格：`core/facts/udc/setting/expression-component/component.md`
> 默认值链：`core/facts/udc/setting/attribute-set/default-value-chain.md`
> 实现：`components/udc/attribute_expression_constraints.py`
> 脚本：`tools/core/setting/expression_component_probe.py`、
>       `tools/core/setting/attribute_default_expr_build.py`

## 这是什么

字段集 / 实体属性面板里，「默认值」输入框旁的 **`+` 号** → Popover
「系统变量 / 高级模式」→ 点 BUTTON「高级模式」→ **表达式设置对话框**。

对话框内三个面板：可选范围（系统变量 + 应用参数）／函数树／函数详情。

## 四个端点（全部 REST，不是 GraphQL）

| 端点 | 方法 | body | 用途 |
|---|---|---|---|
| `/service/udc/expression/operator/list` | **GET** | 无 | 运算符清单（`+ - * / % == != ...`） |
| `/service/udc/expression/schema` | POST | `VariableSchemaLoadDto` | 可选范围（应用参数 / 变量树） |
| `/service/udc/expression/preset/list` | POST | `{"terminalSupportType":"BACKEND"}` | 系统变量树 + 函数树 |
| `/service/udc/expression/check` | POST | `ExpressionSaveDto` | 校验（**必须读 `data.content===true`**） |
| `/service/udc/expression/transform` | POST | `ExpressionSaveDto` | 产出 `designData` + `runtimeData` |

⚠ **`operator/list` 是 GET。** 用 POST 返回 **405 Whitelabel Error Page**，
不是业务错误码——看到 405 先怀疑方法，不要怀疑能力。

## `schema` 的 body 有三种语义（别混）

```json
// ① 取「应用参数」（设置页默认值场景用这个）
{"appId": "<appId>", "extension": "", "ids": [], "idsStr": [],
 "idsTuple": [], "paramType": "CONFIG_PARAM"}
→ content: [{name:"fujian", description:"附件", type:"STRING",
             uniformityParams:{paramId:"...", paramCategory:"CONFIG_PARAM"}}]

// ② 取「某实体的字段清单」
{"ids": ["<udc_entity.id>"], "paramType": "ENTITY",
 "upsource": true, "serverName": "udc"}
→ ★ 不能带 appId（带上报 BOOT_3000）

// ③ 字段集 id + ENTITY  → BOOT_0000 但 content=[]（静默空，最易误判成功）
//     ↑ 本域「成功码 + 空」的 4 种成因之一（上下文不对），对照见 README.md §〇★
```

⚠ 字段集本身没有实体，用字段集 id 取 schema 拿不到字段清单是**正常的**。
函数的参数位置由平台按函数元数据校验，不依赖 schema 里的实体字段。

## `ExpressionSaveDto` 键集

```json
{
  "resultTypeInfo": "STRING|INTEGER|BIGINTEGER|DECIMAL|DATE|TIME|DATETIME|BOOLEAN|CTPENUM|ENTITY",
  "schemas": [ ... schema 返回的组 ... ],
  "tokens": [ ... token 数组 ... ],
  "isMultiSelect": false,
  "terminalSupportType": "BACKEND"
}
```

`resultTypeInfo` **必须等于目标字段的 dataType**，否则 `FORMULA_6901`。

## token 形状（恰 5 个 type）

```
CONSTANT / VARIABLE / SYSTEM / FUNCTION / OPERATOR
```

```json
{"uid":"<uuid>", "type":"SYSTEM", "value":"system.currentDateTime", "desc":"系统日期时间"}
{"uid":"<uuid>", "type":"VARIABLE", "value":"__SYSTEM_PARAMS.fujian", "desc":"应用参数.附件"}
{"uid":"<uuid>", "type":"FUNCTION", "value":"ifs", "desc":"条件返回",
 "subOps": [[子token...], [子token...], [子token...]]}
{"uid":"<uuid>", "type":"CONSTANT", "value":"'文本'", "desc":"常量"}
{"uid":"<uuid>", "type":"OPERATOR", "value":"true", "desc":"真"}
```

- `subOps` 是**二维数组**：外层 = 参数位置，内层 = 该位置的候选 token 组
- `SYSTEM_VARIABLE` **不存在**（会报 FieldUndefined）
- 布尔字面量必须用 `OPERATOR`，用 `CONSTANT "true"` 报 `FORMULA_6901 计算结果为文本`

## 函数元数据：类型在 `explain.example.argTypes`

`preset/list` 返回 88 个函数 / 8 大类：

```
基础15  日期24  数学10  文本17  条件1  聚合18  变化1  枚举2
```

⚠ **`parameters[].description` 只有自然语言描述，不是类型。**
真实参数类型在 `explain.example.argTypes`：

```
join                → ['集合', '文本']       ← 不是文本！
substringByIndex    → ['文本', '整数', '整数']
textToLong          → ['文本']               ← 传 INTEGER 报 FORMULA_6158
dateToString        → ['日期', '文本']
round               → ['对象', '整数']
getEnumItemValue    → ['长整数']             ← 不是枚举名
```

**动工前先抄 argTypes 再组 token**，别按描述猜。

## `transform` 返回（两列都必须落库）

```json
{
  "designData": {
    "expressionTranslation": "应用参数.附件 ",
    "resultTypeInfo": "STRING",
    "resultTypeFullName": null,
    "terminalType": "BACKEND",
    "isMultiSelect": false,
    "context": [ ... ],
    "tokens": [ ... ],
    "sourceAppName": null,
    "version": null
  },
  "runtimeData": {
    "executableExpr": "93gDaq3/nXB1+...=getSystemParameter('6762196059487749233')"
  }
}
```

⚠ **`runtimeData` 不许置空。** 前端执行靠它；只写 design 会页面空白。
`executableExpr` 的 base64 前缀是服务端产物，客户端不可造，只能整份照抄。

## 错误码

| 码 | 含义 |
|---|---|
| `FORMULA_6901` | 表达式结果类型 ≠ 目标字段类型（如文本→长整数） |
| `FORMULA_6158` | 函数参数类型不匹配（argTypes 不符） |
| `FORMULA_6058` | 变量不存在（`CVariable :<desc> does not exist in context`） |
| `BOOT_1000` | 业务拒绝（如 `函数获取枚举项值, 参数只能是单选枚举常量`） |
| `BOOT_3000` | schema 入参不合法（带 appId / idsStr） |
| `UDC_ATTR_0017` | `expressionDesignData` 缺 `resultTypeInfo` 或 tokens 空 |
| `UDC_ATTR_0018` | `defaultValueExpressionDesignData` 缺 `resultTypeInfo` 或 tokens 空 |
| `UDC_EXPRESSION_7005` | 实体信息为空 |
| `UDC_EXPRESSION_7008` | 表达式为空 |

## 闸门纪律

```
组装 token → check（data.content === true 才算过）→ transform → 落库 → DB 回读
任何一步失败即报错停，不兜底
```

⚠ `check` 只验语法与类型，**不验值语义**。实体字段塞文本参数能过 check，
但那是错的值——语义要人判断。

## 页面操作要点

```
「默认值」旁的 + 号必须用 CDP 真实鼠标事件（Input.dispatchMouseEvent
先 mouseMoved 再 mousePressed/mouseReleased）；JS .click() 与合成事件都不生效。
rea 在这个页面会 timeout。
```

关对话框：`ant-modal-close` 的 X 按钮同样是 React 受控，`.click()` 无效，
也要真实鼠标；关不掉就 Page.reload 重来。

## 未验证

```
paramType=ATTRIBUTE_SCOPE / BASIC       UNVERIFIED
函数 token 的完整嵌套层数（3 层以上）      UNVERIFIED
「验证」按钮的独立行为                    UNVERIFIED（与 check 端点是否同一逻辑未证）
聚合函数 18 个（需明细表属性，字段集无明细行） UNVERIFIED
```
