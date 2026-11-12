# 表达式四种形态的真实后端结构（已落库验证）

在节点抽屉的表达式面板里建好后，`udcMicroflowFindByIdGet` 回读的真实结构。

## 两种 executableExpr 形态

```
单 token：  前缀 + URL编码(token)
多 token：  前缀 + "+%28+" + URL编码(表达式) + "+%29+"
前缀：      93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=
```

前缀是服务端固定产物，**手拼必错**，只能走 `POST /service/udc/expression/transform`。

## 四种形态

### 1. 单变量
```json
tokens=[{"type":"VARIABLE","value":"_RETRIEVE_Ltqgzz._RETRIEVE_Ltqgzz.expText"}]
resultTypeInfo="STRING"
exec=93gDaq3/...GvQ=_RETRIEVE_Ltqgzz._RETRIEVE_Ltqgzz.expText
```

### 2. 变量 + 运算符 + 变量
```json
tokens=[VARIABLE expNum, OPERATOR "+", VARIABLE expNum]
tokens=3，复合式加括号：exec=93gDaq3/...GvQ=+%28+<expr>+%29+
```

### 3. 函数（三参数）
```json
tokens=[{"type":"FUNCTION","value":"substring","desc":"按长度截取字符串",
  "subOps":[[expText],[expNum],[expNum]]}]
tokens=1，subOps 是「数组的数组」，每格 = 一个参数位（每参数位可放多个 token）
```
UI 显示中文函数名，服务端 token 存英文函数名：
`按长度截取字符串`→`substring`、`为空`→`isNull`、`不为空`→`isNotNull`。

### 4. 混合（变量 + 运算符 + 函数）
```json
tokens=[VARIABLE expText, OPERATOR "+", FUNCTION substring(subOps×3)]
tokens=3，exec 同形态 2 加括号包裹
```

分支条件（BOOLEAN）同形态 2，只是 tokens 用 `>` 之类比较运算符。

## 落点差异

| 位置 | 字段 | title 外层 |
|---|---|---|
| 修改变量 | `node.value = {type:"Expression", expression:{title,schema,desc}}` | **包 `{...}`** |
| 分支条件 | `node.conditions[i].expression = {title,schema}` | 不包 |

## UI 操作铁律（函数参数位最容易翻车）

1. **搜索框先清空再输入**：相同值 setter 不触发 React 更新，树不刷新。
2. **插入变量/函数用 React `onClick` 直调，一次即可**（点两次会重复插入）。
3. **参数位选择器用 `[class*=functionParamElem]`**，不能用 `.paramPlaceholder`——游标停在第 1 个参数位时它的「选择」文字被隐藏，会漏掉。
4. **填参数必须用真实鼠标点变量树**：React `onClick` 直调会丢失「当前参数位」上下文，把变量插到表达式最前面。
5. 点完参数位等 **2 秒**，校验 `document.activeElement.className` 含 `cursorElem`。
6. 每填一个参数就重新取坐标（表达式换行后参数位 y 从 208 → 257）。
7. **成功判定用「变量出现次数增加」**，不能比 text 差异——点参数位本身就会把 `(,选择)` 变成 `(选择,选择)`，造成假成功。
8. 运算符顺序严格：`变量 → 运算符 → 变量`。先点运算符得到 `+变量`，验证报 `操作符:+ , 输入错误!`。
