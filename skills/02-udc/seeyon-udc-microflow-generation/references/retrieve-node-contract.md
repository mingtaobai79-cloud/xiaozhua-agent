# RETRIEVE（查询单条数据）节点契约

取证：前端逐个真操作 → 点确认 → `udcMicroflowFindByIdGet` 回读对比。

## 表单项全集

| label | 控件 | 说明 |
|---|---|---|
| 查询方式 | radio | `CONDITION` 条件查询 / `IDS` ID查询 |
| 选择应用 | select | |
| 选择实体 | tree-select | **改实体会清空 condition 并重写 structure** |
| 过滤条件 | 点击区 | 仅 CONDITION，开独立 modal |
| 选择该记录的ID | tree-select | 仅 IDS，必填，**只能选参数不能填常量** |
| 排序规则 | 按钮 + 行 | |
| 查询聚合对象 | radio | → `needCascade` |
| 节点出参名称 | input | → `title` |
| 未查到数据时 | radio | → `nullHandling` |
| 提示内容 | textarea#nullPromptMessage | 仅 TERMINATION 出现且必填 |

## 两条联动铁律

1. **切 IDS 隐藏过滤条件、显示「选择该记录的ID」tree-select**。IDS 下直接提交报
   `structure:请输入选择实体` + `value:请输入选择该记录的ID`。
   切换后 `condition` **自动清空**，`value` 变成 `SelectParam` 对象（引用入参，不是常量）。
2. **改「选择实体」= 清空 condition 与 structure**。实测把 A 换成 B 再保存，`condition` 变 `null`、
   `structure` 换成 B。所以**调实体必须在配条件之前**，顺序反了会白做。

### IDS 的 value 落库形态

`value` 是 tree-select，下拉只列入参（如「入参对象」「记录ID」），**没有常量输入框**。选完落库：

```json
{"type":"SelectParam","selectParam":{"description":"记录ID","key":"_FLOW_INPUT_xxxx",
 "name":"recordId","id":"<dto全名>.recordId","appName":"..."}}
```

所以 RETRIEVE 的 IDS 模式**必须有入参**才能用，纯常量 ID 查询走不了 UI（只能直接改 dataSchema）。

## 落库字段

```json
{"actionType":"RETRIEVE","fetchType":"CONDITION",
 "nullHandling":"TERMINATION","nullPromptMessage":"...",
 "needCascade":false,"title":"查询结果",
 "selectType":"DTO","scope":"OBJECT",
 "structure":{"key":"<domain全名>","id":"<dto全名>","label":"<实体中文名>",
   "dataType":"DTO","entity":"<domain全名>","dtoType":"MASTER_ENTITY",
   "udcApp":true,"fullName":"<dto全名>","relationEntity":"<实体数字id>"},
 "condition":[{"type":"GROUP","uuid":"...","conditions":[...]}],
 "sortParams":[{"sortType":"ASC","attrType":{...字段完整属性...}}],
 "output":{"id":"<dto全名>","javaType":"<dto全名>","dataType":"DTO","type":"OBJECT",
   "dtoType":"MASTER_ENTITY","udcApp":true,"name":"_RETRIEVE_xxxxxx"}}
```

**健康判据：`output.id` 必须等于 structure 的 `dto` 全名。** 写成 null / `""` 说明节点已损坏。

## 过滤条件弹窗（独立 `.ant-modal`，标题「过滤条件」）

DOM 类名（跨应用稳定）：
- 字段 `.ant-col-8 .ant-select.ant-tree-select`
- 运算符 `.condition-item__operator .ant-select`
- 右值区 `.condition-item__rightParams`

### 打开弹窗前：先等抽屉「过滤条件」区的 ant-spin 遮罩消失

实体/条件数据未就绪时，抽屉里「过滤条件」form-item 会渲染 `.ant-spin` 遮罩（文本「加载中...」），
此时点它命中的是 `ant-spin-text` 而非点击区 → 弹窗打不开。轮询 `.ant-spin` 消失（或 `Page.reload` 编辑器）再点。

### 关闭弹窗用 ESC，不点「取消」

点「取消」常被 React 动画/遮罩吞掉（click 落到遮罩层、onClick 不触发，弹窗关不掉）。
ESC（CDP `Input.dispatchKeyEvent` key=Escape，keyDown + keyUp 各一次）一发就关，可靠。
清残留弹窗也用它：循环「发 ESC → 查 `.ant-modal` width>0 的数量 → 为 0 即清空」。

### 右值必须选完运算符才可编辑

**只选字段时右值 input 是 `readOnly=true`，setInput 被静默忽略。**
必须「字段 + 运算符」都选完才解锁——这是最容易被误判成「填不进去」的坑。

### 运算符随 dataType 变化（4 种全集，实测枚举）

```
长整数 BIGINTEGER：= != 在 不在 < <= > >= 介于 不介于
日期时间 DATETIME ：= != < <= > >= 介于 不介于 为空 不为空
文本    STRING    ：= != 包含 不包含 在 不在 开头为 结尾为 为空 不为空
枚举    CTPENUM   ：= != 在 不在 为空 不为空
```

不能写死全集，每次打开下拉现取。注意：枚举字段只有 6 个运算符，没有比较符。

### 右值三种形态（rightParams[].type）

| type | 落库 value | 触发方式 |
|---|---|---|
| `CONSTANT` | 原始字符串 | 选完字段+运算符后直接输入 |
| `CONTEXT_VARIABLE` | SelectParam 对象 | 点右值区「+」→ popover 选变量 |
| `EXPRESSION` | `{designData:{expressionTranslation,resultTypeInfo,...}}` | 「+」→ 高级模式 → 表达式编辑器 |

**CONTEXT_VARIABLE 的坑**：popover 里的参数节点可能全部是 disabled（`cursor:not-allowed`，
灰字）——当入参对象本身不可引用时，只能走「高级模式」写 EXPRESSION。

### 表达式编辑器（「高级模式」打开，标题「表达式设置」）

- 「+」按钮的 popover 有 3~4 秒动画，固定 sleep 后可能还没可见。轮询 `.ant-popover`
  （width>200 且 opacity>0.9）确认可见，再点「高级模式」。
- token **必须点左侧「可选范围」变量树插入**（插入后是 `data-elm=variable-element` 的块），
  直接 `Input.insertText` / `dispatchKeyEvent` 只产生纯文本、**不产生 token**，验证返回空结果
- 运算符是 `.item` 类 DIV（在编辑区下方 y≈354 那一排：`+ - × ÷ mod = != > < >= <= and or not true false ( ) 为空 不为空 属于`），**不是 button**
- 验证按钮在 footer `.btns` 里，验证结果写在 `.verifyMessage .success`（文本「验证成功」）
- 类型不兼容时显示「计算结果为: X 类型, 无法赋值给: Y 类型」
- 落库：`value` 是 JSON 字符串，`designData.resultTypeInfo` 是结果类型（如 `BIGINTEGER`）

### 「添加条件组」不产生嵌套

`添加` 是 dropdown trigger，菜单 `添加条件` / `添加条件组`。
两者产生的 DOM **完全一样**：同一个 `conditionGroupHorizontal` 追加一行，行首出现「且」。
→ 多条件是「平铺 + AND」，UI 层不提供嵌套 GROUP。要嵌套只能直接改 `condition[]` 走 REST。

## 排序规则

- 「添加规则」= `button.ant-btn-block`（在「排序规则」form-item 内），可重复点加行
- 每行 `[选择字段] [升序/降序]` + `sy-icon.lined-remove-circle` 删除
- 字段选项格式 `<中文名> [<dataType 中文>]`，如 `实验数量 [整数]`
- `attrType` 落字段**完整属性**（md5 / customs.id / javaType / sort），不是仅名字
- 升序 `ASC` / 降序 `DESC`

**行定位必须按子行索引**：前一行填好后「选择字段」占位文本消失，按占位文本筛的数组长度会变，索引立刻错位。
第 2 行常被抽屉固定底栏遮挡，需要手动滚 `.udc-microflow-editor-node-settings`。

## errorFields 文案

| 场景 | errorFields |
|---|---|
| IDS 未选实体 | `structure: 请输入选择实体` |
| IDS 未填 ID | `value: 请输入选择该记录的ID` |
| 排序规则未选字段 | `sortParams[i].attrType: 请选择字段` |
