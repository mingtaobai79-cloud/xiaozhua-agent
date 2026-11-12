# 微流程表达式 —— 四种类型全部实测通过

测试环境：探针流程 `xzhNodeProbe907792`（mid `-6371737850148111694`），
分支节点 CONDITION，目标类型 BOOLEAN（分支条件）。

## 一、变量 + 变量（算术/比较）

```
微流程.查询单条数据(1).查询结果 [小爪实验实体950795V2].实验数量
  >
微流程.查询单条数据(1).查询结果 [小爪实验实体950795V2].实验数量
```

验证：`验证成功`
resultTypeInfo：`BOOLEAN`

tokens：
```json
[{"type":"VARIABLE","value":"_RETRIEVE_Ltqgzz._RETRIEVE_Ltqgzz.expNum","desc":"微流程....实验数量"},
 {"type":"OPERATOR","value":">","desc":">"},
 {"type":"VARIABLE","value":"_RETRIEVE_Ltqgzz._RETRIEVE_Ltqgzz.expNum","desc":"..."}]
```

## 二、变量 + 变量（整数运算，类型不符会被拦）

```
...实验数量 + ...实验数量
```
验证：`计算结果为: 整数 类型, 无法赋值给: 布尔 类型`
→ 说明**表达式合法**，仅目标类型不匹配。挂到 DECIMAL/INTEGER 字段即可用。

## 三、函数调用（单函数三参数）

```
按长度截取字符串(查询结果.实验文本(已改), 查询结果.实验数量, 查询结果.实验数量)
```

等价服务端函数：`substring(字符串, 起始位置, 截取长度)`

验证：`计算结果为: 文本 类型, 无法赋值给: 布尔 类型` → 语法通过。

参数类型校验：
`函数:【按长度截取字符串】 第 1 个参数类型不匹配 , 期望类型:STRING , 实际类型: INTEGER`

→ **参数类型是强校验的**，报错会明确指出第几个参数、期望类型、实际类型。

## 四、函数嵌套 + 文本拼接（服务端函数名对照）

UI 显示名（中文） ↔ 服务端函数名（英文，见 `.explainScope` 说明区）：

| UI 中文名 | 服务端函数 |
|---|---|
| 按长度截取字符串 | `substring(字符串, 起始位置, 截取长度)` |
| 为空 | `isNull(对象)` |
| 不为空 | `isNotNull` 类 |
| 按指定符号分割文本 | split |
| 按指定符号合并文本数组 | join |
| 获取指定下标文本 | charAt / get |
| 获取字符串长度 | length |
| 按位置截取字符串 | substringByIndex |
| 按内容替换字符串 | replace |
| 查询文本位置 | indexOf |
| 人民币大写/小写 | — |

数字→小数转换用 `textToDecimal`、`textToInt`、`textToLong`（服务端侧，UI 里挂在「数学函数」）。

## 函数树完整清单（2026-10-27 实测）

**基础函数（17）**
为空 / 多维组织人员隶属 / 不为空 / 多维组织隶属 / 包含(全部) / 不包含(全部) /
包含任一 / 不包含任一 / 人员隶属 / 属于 / ID生成 / 组织隶属 / 唯一标识 /
随机数 / 指定范围随机数

**日期函数**（需展开）
**数学函数**（需展开）
**文本函数（18）**
开头为 / 开头不为 / 结尾为 / 结尾不为 / 文本包含 / 按指定符号分割文本 /
按指定符号合并文本数组 / 获取指定下标文本 / 获取字符串长度 / 按位置截取字符串 /
按位置替换字符串 / 查找文本位置 / 按长度截取字符串 / 按内容替换字符串 /
按内容位置替换字符串 / 人民币大写 / 人民币小写
**条件函数 / 聚合函数 / 变化函数 / 枚举函数**（需展开）

## 函数树操作要点

- 函数名是**中文**，`substring` 搜不到，要搜「截取」
- 「函数」根节点默认收起，必须先展开
- 展开一个分类后再展开下一个，会因行位移而点错 → 每次先收起
- 函数插入同样是 **点两次**
- 插入后编辑器显示 `按长度截取字符串(选择,选择,选择)`，`选择` 是 `.paramPlaceholder`
- 点击占位符后，变量/函数选择会填充到**该参数位**
- 填完一个参数后 `.paramPlaceholder` 列表会重排，**每次都要重新定位**

## 五个致命坑

1. **数字字面量插入位置不可控**
   `Input.insertText("2")` 会粘到前一个参数后面变成 `02`，
   或跑到表达式最前面。→ 全部参数改用变量，不用键盘敲数字。

2. **变量/函数必须点两次**
   第 1 次只选中树节点，第 2 次才插入编辑器。

3. **清空后要先点编辑器**
   `.editor-wrapper` 区域（约 x=395,y=285）点一下拿焦点，否则树点击空转。

4. **运算符顺序严格**
   `变量 → 运算符 → 变量`。先点运算符会得到 `+变量`，
   验证报 `操作符:+ , 输入错误!`。

5. **面板已配置后按钮消失**
   分支条件写成后，「条件设置」按钮变成表达式文本块。
   重新编辑要点表达式文本，不是点按钮。

## 表达式面板完整坐标参考（1600x900 视口）

```
面板       x=350  y=72   w=1000 h=791
顶部按钮   y=312  全量复制/部分复制/粘贴/清空/验证
运算符区   y=354  + - × ÷ mod = != > < >= <= and or not true false ( ) 为空 不为空 包含(全部) 属于
变量树     x=370~722  y=378~782
函数树     x=738~998  y=378~782
说明区     x=1014~1330
编辑区     x=370  y=265  w=960 h=400
底部       y=833  取消 / 确定
```

---

# 【2026-10-27 落库验证】四种表达式全部写入后端

之前只做到"验证成功"，本轮把四种类型**全部真实落库**并通过 `udcMicroflowFindByIdGet` 回读确认。

落库位置：修改变量节点 `CHANGE_VARIABLE_PBZj6Z`（elseBranch 内），目标类型 STRING。

## 后端结构（回读）

### 类型 1：单变量引用
```json
{"value":{"type":"Expression","expression":{
  "title":"{微流程.查询单条数据(1).查询结果 [小爪实验实体950795V2].实验文本(已改)}",
  "schema":{"designData":{"resultTypeInfo":"STRING","tokens":[
    {"type":"VARIABLE","value":"_RETRIEVE_Ltqgzz._RETRIEVE_Ltqgzz.expText"}]},
    "runtimeData":{"executableExpr":"93gDaq3/...GvQ=_RETRIEVE_Ltqgzz._RETRIEVE_Ltqgzz.expText"}}}}}
```
`tokens=1`，exec 前缀**直接拼接**，无括号。

### 类型 2：变量 + 变量
```
tokens = [VARIABLE expNum, OPERATOR +, VARIABLE expNum]
resultTypeInfo = STRING
exec = 93gDaq3/...GvQ=+%28+<expr>+%29+
```
`tokens=3`，复合表达式**加括号**。

### 类型 3：函数调用（substring 三参数）
```
tokens = [{
  type:"FUNCTION", value:"substring", desc:"按长度截取字符串",
  subOps:[ [expText], [expNum], [expNum] ]
}]
resultTypeInfo = STRING
exec = 93gDaq3/...GvQ=substring%28...expText%2C...expNum%2C...expNum%29
```
`tokens=1`，`subOps` 是**数组的数组**，每格一个参数位。

### 类型 4：混合（变量 + 运算符 + 函数）
```
tokens = [VARIABLE expText, OPERATOR +, FUNCTION substring(subOps×3)]
resultTypeInfo = STRING
exec = 93gDaq3/...GvQ=+%28+...expText+%2B+substring%28...%29+%29+
```
函数作为 token 参与运算，`subOps` 嵌套参数。

### 类型 5：分支条件
```
tokens = [VARIABLE expNum, OPERATOR >, VARIABLE expNum]
resultTypeInfo = BOOLEAN
```

## executableExpr 生成规则

| 形态 | 结果 |
|---|---|
| 单 token | `前缀` + `URL编码(token)` |
| 多 token | `前缀` + `+%28+` + 编码表达式 + `+%29+` |

前缀固定：`93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=`
**手拼必错**，只能走 `POST /service/udc/expression/transform`。

## UI 操作铁律（补充/修正）

1. **搜索框必须先清空再输入**
   相同值 setter 不触发 React 更新，导致树不刷新、点到旧节点。

2. **插入变量用 React `onClick` 直调，一次即可**
   点两次会插入两份。

3. **函数参数位选择器用 `[class*=functionParamElem]`**
   不能用 `.paramPlaceholder` —— 游标停在第 1 个参数位时它的「选择」文字被隐藏，会漏掉。

4. **填参数必须用真实鼠标点变量树**
   React `onClick` 直调会丢失"当前参数位"上下文，把变量插到全局位置（表达式最前面）。

5. **点完参数位等 2 秒**，并确认 `document.activeElement.className` 含 `cursorElem`。

6. **每次填参数都要重新取坐标**，填完后表达式换行，参数位 y 会变（208 → 257）。

7. **成功判定用「变量出现次数增加」**
   不能比 text 差异 —— 点参数位本身就会把 `(,选择)` 变成 `(选择,选择)`，造成假成功。

8. **提交抽屉：按 Enter，不要点「确定」**
   点「确定」必然撞 antd `outOfDate`（`errorFields:[]` 但 `outOfDate:true`），提交被拒。
   在变量值输入框按 Enter（`keyDown/char/keyUp` 三连带 `\r`）→ 发 `udcMicroflowUpdatePost` → store 立即更新。

9. **`Emulation.setFocusEmulationEnabled(enabled=True)` 解决 `document.hidden`**
   页面被遮挡时抽屉底部按钮不渲染、下拉坐标 -9999，一行搞定。

10. **每次保存后 state 变 RELEASE、readonly=true**
    必须点顶栏「编辑」再继续，否则所有编辑静默丢弃。

## 实测结果

| # | 表达式 | resultType | tokens | 落库 |
|---|---|---|---|---|
| 1 | `实验文本` | STRING | 1 VARIABLE | ✓ |
| 2 | `实验数量 + 实验数量` | STRING | 3 (V,OP,V) | ✓ |
| 3 | `按长度截取字符串(实验文本,实验数量,实验数量)` | STRING | 1 FUNCTION + subOps×3 | ✓ |
| 4 | `实验文本 + 按长度截取字符串(...)` | STRING | 3 (V,OP,FUNCTION) | ✓ |
| 5 | `实验数量 > 实验数量`（分支） | BOOLEAN | 3 (V,OP,V) | ✓ |
