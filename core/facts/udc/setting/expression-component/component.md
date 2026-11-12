# 设置域 · 表达式组件（「默认值 +」→「高级模式」）链路事实

> 证据等级：**LIVE PASS**（2026-10-21 CDP 真实点击抓包）
> 探针：`tools/core/setting/expression_component_probe.py`

## 零、为什么必须抓这个

字段集右侧「默认值」输入框旁的 **`+` 号**是 Popover 触发器：

```html
<span class="ant-input-group ant-input-group-compact ant-popover-open">
  <div class="index-module_variableSelect__HaAx8">
    <input placeholder="请输入" ...>
    <span class="sy-icon lined-plus">    ← 点它
```

点开后 Popover 内容只有两项：**「系统变量」/「高级模式」**。
「高级模式」按钮打开真正的**表达式设置对话框**。

⚠ 那个 `+` 是 **hover 才显现**的，且 Popover 定位到 `(0,0)` 但元素可见。
JS `.click()` 和合成事件都不生效，必须用 CDP `Input.dispatchMouseEvent` 真实鼠标。

## 一、组件打开时并发三个接口

```
POST /service/udc/expression/operator/list    运算符清单
POST /service/udc/expression/schema           变量 schema（按 paramType）
POST /service/udc/expression/preset/list      系统变量 + 函数树
```

### 1.1 `expression/schema` 的真实 body（★ 与既有文档不同）

```json
{
  "appId": "8704025620829192834",
  "extension": "",
  "ids": [],
  "idsStr": [],
  "idsTuple": [],
  "paramType": "CONFIG_PARAM"
}
```

**三个数组都在**：`ids` / `idsStr` / `idsTuple`，且**要带 `appId`**。

⚠ `references/udc-expression-domain.md` 记的是「`paramType=ENTITY` 带 ids 时省略 appId」，
那是**另一种场景**。字段集这个面板走的是 `CONFIG_PARAM + appId`，两者不冲突但要分清。

`paramType` 值域：`ENTITY` / `ATTRIBUTE_SCOPE` / `CONFIG_PARAM` / `BASIC`

**实测 `CONFIG_PARAM` 返回 3 项（本应用的应用参数）：**

```
fujian          附件        STRING
zxjApiBaseUrl   接口基地址   STRING
zxjPageSize     分页大小     INTEGER
```

这三个正是弹窗里「应用参数」分组下显示的内容。

### 1.2 `expression/preset/list` 的真实 body 与产出

```json
{"terminalSupportType": "BACKEND"}
```

产出结构：

```jsonc
{
  "presetVariableInfo": [
    {"name":"organization","description":"组织机构","items":[
       {"type":"SYSTEM","name":"system.currentUserId","description":"登录人员ID",
        "functionName":"currentUserId","resultType":"BIGINTEGER",
        "relationEntity":"com.seeyon.organization.domain.core.entity.OrgMember",
        "hidden": false}
    ]},
    {"name":"date",  "description":"日期",   "items":[…33 项]},
    {"name":"env",   "description":"环境变量","items":[…2 项]},
    {"name":"plugin","description":"插件",   "items":[…1 项]}
  ],
  "functionInfo": [
    {"categoryName":"基础函数","icon":"LinedSum","functions":[
       {"name":"isNull","description":"为空",
        "parameters":[{"isAggregationProperty":null,"controlData":null,"description":"对象"}],
        "explain":{
          "description":"判断文本或属性是否为空",
          "useage":"判断文本或属性是否为空",
          "example":{"name":"isNull","args":["扣缴义务人"],"argTypes":["对象"],
                     "tips":"判定扣缴义务人是否为空","guideLink":""}},
        "sort":1}
    ]}
  ]
}
```

**本应用实测：变量 131 项 / 4 组，函数 88 个 / 8 组。**

变量分组：

```
organization 组织机构  95
date         日期      33
env          环境变量    2
plugin       插件       1
```

函数分组：

```
基础函数 15    日期函数 24    数学函数 10    文本函数 17
条件函数  1    聚合函数 18    变化函数  1    枚举函数  2
```

函数样例（含参数说明与示例，可据此构造 token）：

```
基础  isNull(对象) / isNotNull(对象) / contains(参数,被包含变量)
      multMemberBelongsTo(人员参数,被判断值) / multUnitBelongsTo(组织参数,被判断值)
日期  dateToString(日期,格式) / stringToDate(日期字符串,日期格式)
      dateDiff(日期1,日期2) / minuteDiff / hoursDiff
数学  roundOff(数字) / roundOffCeiling / roundOffFloor / quotient(被除数,除数)
      thousandBitSep(待转换字段)
文本  startsWith(字符串,开头字符串) / endsWith / containsText(参数,被包含文本)
条件  ifs(条件,结果1,结果2)
聚合  sum(明细表属性) / count(明细表对象) / avg / min / max
变化  changeTo(变化前的值,变化后的值,期望值)
枚举  getEnumItemName(枚举项id) / getEnumItemValue(枚举项id)
```

### 1.3 `expression/operator/list`

实测返回**空数组**（对 STRING 结果类型的字段）。

弹窗里实际显示的运算符是**前端硬编码**：

```
+  -  ×  ÷  mod  =  !=  >  <  >=  <=  and  or  not  true  false  ( )
为空  不为空  包含(全部)  属于  可选范围
```

## 二、表达式设置对话框的完整结构

```
标题：表达式设置  <字段显示名>
提示：= 在下方选择字段变量或者函数，且在英文输入法下编辑
按钮：[全量复制] [部分复制] [粘贴] [清空] [验证]
运算符行：见 §1.3
变量分组：系统变量 | 组织机构 | 日期 | 环境变量 | 插件 | 应用参数 | 附件
函数分组：基础 | 日期 | 数学 | 文本 | 条件 | 聚合 | 变化 | 枚举
底部：[取消] [确定]
```

## 三、`defaultValueSystemVariable` 的两种真实格式（★ 关键）

同一个字段位置，**存在两种完全不同的 JSON 形态**，用错会导致前端 `JSON.parse` 崩溃：

### 格式 A：单 token 对象（真实业务字段用这个）

```json
{"type":"SYSTEM_VARIABLE","value":"currentUserId","desc":"登录人员ID","dataType":"BIGINTEGER"}
```

来源：DB 真实业务字段（`creator` / `orgId` / `creatorInstitution` 等）。

⚠ 但这个格式用在**字段集的 STRING 字段**上报
`UDC_ATTR_0010 默认值选中的系统变量数据类型和当前属性数据类型不匹配`。

### 格式 B：ExpressionSaveDto 完整结构（字段集用这个）

```json
{
  "resultTypeInfo": "ENTITY",
  "schemas": [],
  "tokens": [{"value":"system.currentUserId","desc":"登录人员ID",
              "type":"SYSTEM","uid":"b1b9e5b6-e881-4796-b724-9931dd8d1fed"}],
  "isMultiSelect": false,
  "terminalSupportType": "BACKEND"
}
```

来源：**用户提供的真实报文**，实测落库成功。

### 两种格式的后果对照

| 写入内容 | 结果 |
|---|---|
| 纯文本 `"currentUser"` | ❌ **前端 `JSON.parse` 崩溃 → 整个字段集面板白屏** |
| 格式 A（单 token） | ❌ `UDC_ATTR_0010` 数据类型不匹配 |
| 格式 B（ExpressionSaveDto） | ✅ **BOOT_0000 落库成功** |

⚠ **铁律**：`defaultValueSystemVariable` 绝不能传纯文本。多花 10 秒确认 JSON 合法性，
否则前端白屏、整块面板不可用。

## 四、可用脚本

```bash
# 全量：变量 + 函数 + 4 种 paramType 的 schema
python tools/core/setting/expression_component_probe.py --all

# 只看某个 paramType
python tools/core/setting/expression_component_probe.py --schema CONFIG_PARAM
python tools/core/setting/expression_component_probe.py --schema ENTITY

# 只列变量 / 只列函数
python tools/core/setting/expression_component_probe.py --vars
python tools/core/setting/expression_component_probe.py --functions
```

## 五、页面操作要点（踩过的坑）

| 坑 | 现象 | 正解 |
|---|---|---|
| `+` 号是 hover 才显示 | `getBoundingClientRect().width === 0` | 先 `Input.dispatchMouseEvent(mouseMoved)` hover 到「默认值」行 |
| JS `.click()` 无效 | 点了、Popover 不开 | 用 CDP `Input.dispatchMouseEvent` 真实鼠标 |
| Popover 定位到 (0,0) | 坐标计算错 | Popover 在 `(0,0,279,128)`，但子元素 `getBoundingClientRect()` 给的是**屏幕坐标**（如 BUTTON 在 67,107） |
| 点了 DIV 不是 BUTTON | 无反应 | 「高级模式」是 `<button class="ant-btn ant-btn-default btn-solid-default">`，点 BUTTON 本体 |
| rea 在这个页面 timeout | `capture_browser_scenario` 300s 超时 | 改用 CDP 直连 + 页面内 fetch 拦截器（本脚本就是） |
| rea 的 `:nth-child(4)` 点错 tab | 抓到 `udcEnumCategorySearch` | tab 用文本匹配，不用位置匹配 |

## 六、未验证

| 项 | 状态 | 说明 |
|---|---|---|
| `paramType=ENTITY` 的 schema 真实 body | **UNVERIFIED** | 需要 `ids:["<实体id>"]`，本次只验了 CONFIG_PARAM |
| `paramType=ATTRIBUTE_SCOPE` / `BASIC` | **UNVERIFIED** | 同上 |
| `operator/list` 的非空返回 | **UNVERIFIED** | 对 STRING 返回空；需要找什么条件下有值 |
| 函数 token 的完整组装（subOps 层数/参数顺序） | **UNVERIFIED** | 只拿到函数元数据，未逐个验证 token 形态 |
| 「验证」按钮的行为 | **UNVERIFIED** | 对话框里有但未点 |
| 对话框确认后落的库字段 | **UNVERIFIED** | 推测写 `defaultValueExpressionDesignData`，未实证 |
