# 表达式设置面板的 UI 操作（CDP 实测）

不走 REST、在页面上点选写表达式时的真实契约。要批量/脚本化写表达式仍优先走 `/service/udc/expression/transform`（见 SKILL.md）。

## 1. 面板结构

```
.ant-modal  标题=表达式设置  宽 1000
├─ 顶部按钮 y≈312   全量复制 / 部分复制 / 粘贴 / 清空 / 验证
├─ 运算符区 y≈354   + - × ÷ mod = != > < >= <= and or not true false ( )
│                   为空 不为空 包含(全部) 属于
├─ .optionalScope   x≈370 w≈352   变量树（antd Tree）
├─ .funcScope       x≈738 w≈260   函数树（antd Tree）+ 自带搜索框
├─ .explainScope    函数说明（含服务端函数签名与示例）
├─ [data-elm=editor-wrapper]  contenteditable 自研编辑器
│    [data-elm=cursor] 游标   [data-elm=token-wrapper] 已插入 token
└─ 底部 y≈833   取消 / 确定        .verifyMessage 在编辑器下方
```

打开方式：
- 未配置：分支 ifBranch 卡片上的「条件设置」
- 已配置：**「条件设置」按钮消失**，要点卡片里的表达式文本块（`.node-body-title`，含 `微流程.` 的最深元素）重新打开

## 2. 插入规则（用 React onClick 直调，不要靠坐标点）

坐标点击树节点不可靠：编辑器焦点抢不到、行位置漂移、抽屉横向偏移后整块跑到视口外。**直接调树节点的 React onClick**：

```js
const inner = modal.querySelector('.optionalScope .ant-tree-list-holder-inner');
const n = [...inner.children].find(x => (x.textContent||'').trim().startsWith('实验数量'));
const el = n.querySelector('.ant-tree-node-content-wrapper') || n;   // ← 这一层才有 onClick
const k = Object.keys(el).find(x => x.startsWith('__reactProps$'));
el[k].onClick({currentTarget: el, target: el, preventDefault(){}, stopPropagation(){}, nativeEvent:{}, type:'click'});
```

### ★ 不要在这三件事上浪费时间（已知全无效，直接跳过）

树节点展开不了的时候，下面三种手法一个都不会生效，连着试只会烧掉十几分钟：

| 手法 | 实际结果 |
|---|---|
| 真实鼠标 `click_mouse` 点 `.ant-tree-switcher` 箭头 | `collapsed` 始终不变，子行不出现 |
| `dispatchEvent(new MouseEvent('mousedown'/'click'))` 到 `.ant-tree-title` | 同上 |
| 选中节点后键盘 `ArrowRight` | 同上 |

**失败特征**：目标节点同时带 `ant-tree-treenode-leaf-last`（被判定为叶子）和 `ant-tree-switcher_close`（却显示展开箭头）——前端状态自相矛盾，懒加载永远不会触发。

**判据：连续两种展开手法都失败就停手**，改走两条路之一：

1. 用上面 `content-wrapper` + `props.onClick` 直调（这一层才有 onClick，`.ant-tree-title` 没有）
2. 绕开变量树，走 `/service/udc/expression/transform`（见 SKILL.md「表达式必须走 transform 接口」）

不要在同一轮里反复换坐标重试——坐标不是变量，换多少个都一样。

配套三条，缺一条就会得到「返回 ok 但编辑器是空的」：

1. **插入前把游标移到末尾**：取 `[data-elm=editor-wrapper]` 下最后一个 `[data-elm=cursor]` 并 `.focus()`。不聚焦则插入落到开头，`变量+` 会变成 `+变量`，验证报 `操作符:+ , 输入错误!`。
2. **插入后读 `editor-wrapper.textContent` 校验真的变了**，没变就重试（最多 4 次，每次重聚焦）。清空后第一次插入经常空转，这是常态不是异常。
3. **校验插入位置**：`after.startsWith(before)` 才算成功；否则是插到前面去了，要重来。

运算符同理加「点完读文本确认变了，没变重试」。

清空按钮点完后编辑器进入空态，必须先聚焦一次才能接受插入。

**点「清空」会让红字报错立刻消失——这不是修好了。** 清空只是把表达式变空，校验自然不报；判据仍是回读 `expression.schema` 里 `tokens` 的变量根是否命中本流程输出。把「红字没了」当成「表达式对了」是最容易误报的地方。

搜索框比展开树可靠（antd 虚拟列表，展开子节点不回显子行）：

```js
const inp = modal.querySelector('.optionalScope input[placeholder="请输入搜索关键词"]');
const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
setter.call(inp, '实验数量');
inp.dispatchEvent(new Event('input',{bubbles:true}));
```

搜索后树里直接出现「父级路径行 + 目标字段行」，按 `.ant-tree-list-holder-inner` 直接子元素定位。

## 3. 运算符顺序严格

`变量 → 运算符 → 变量`。先点运算符会得到 `+变量`，验证报 `操作符:+ , 输入错误!`。

## 4. 数字字面量不要用键盘输入

`Input.insertText("2")` 落到游标位置不可控：会粘到前一个参数后面变成 `02`，或跑到表达式最前面变成 `5变量>`。

替代：
- 参数全部改用变量（`变量 > 变量`、`变量 + 变量`），不掺字面量
- 实在要字面量：插完最后一个 token 后先点编辑器末尾游标再 insertText，并立即读 `editor-wrapper.textContent` 核对

## 5. 函数调用：占位符填参

插入函数后编辑器显示 `按长度截取字符串(选择,选择,选择)`，`选择` 是 `.paramPlaceholder`。

```js
[...modal.querySelectorAll('.paramPlaceholder')]   // 每次填完一个都要重新定位，列表会重排
```

流程：点第 1 个 `.paramPlaceholder` → 在变量/函数树里搜并点两次 → 该参数被填充 → 重新取 `.paramPlaceholder` 列表填下一个。

参数类型是**强校验**的，报错会明确到第几个参数：
```
函数:【按长度截取字符串】 第 1 个参数类型不匹配 , 期望类型:STRING , 实际类型: INTEGER
```

## 6. 验证结果怎么读

| 消息 | 含义 |
|---|---|
| `验证成功` | 语法合法 + 类型匹配 |
| `操作符:X , 输入错误!` | 运算符缺左操作数（点顺序反了） |
| `变量: X 后只能拼接操作符` | 变量后面接了不合法内容 |
| `计算结果为: 整数 类型, 无法赋值给: 布尔 类型` | 语法合法，只是目标类型不匹配；挂到对应类型字段即可用 |
| `函数: X , 参数个数不匹配` | 占位符没填全（数字粘连导致合并成一个参数也会这样报） |

「计算结果为 X 类型, 无法赋值给 Y 类型」是**表达式本身正确**的信号，不要当成失败重写。

## 7. 函数名是中文（搜英文永远搜不到）

函数树 8 大类。`.explainScope` 给出服务端签名：

| UI 中文名 | 服务端函数 |
|---|---|
| 按长度截取字符串 | `substring(字符串, 起始位置, 截取长度)` |
| 按位置截取字符串 | `substringByIndex(字符串, 起, 止)` |
| 为空 | `isNull(对象)` |
| 按指定符号分割文本 | split |
| 按指定符号合并文本数组 | join |
| 获取字符串长度 / 获取指定下标文本 / 查找文本位置 | length / charAt / indexOf |

**基础函数（17）**：为空 / 多维组织人员隶属 / 不为空 / 多维组织隶属 / 包含(全部) / 不包含(全部) / 包含任一 / 不包含任一 / 人员隶属 / 属于 / ID生成 / 组织隶属 / 唯一标识 / 随机数 / 指定范围随机数

**文本函数（18）**：开头为 / 开头不为 / 结尾为 / 结尾不为 / 文本包含 / 按指定符号分割文本 / 按指定符号合并文本数组 / 获取指定下标文本 / 获取字符串长度 / 按位置截取字符串 / 按位置替换字符串 / 查找文本位置 / 按长度截取字符串 / 按内容替换字符串 / 按内容位置替换字符串 / 人民币大写 / 人民币小写

日期 / 数学 / 条件 / 聚合 / 变化 / 枚举 六类需展开后抓（展开前先把已展开的收起，否则行位移点错）。

## 8. 确认后的节点结构（可复用）

```json
{"nodeId":"CONDITION_xxxxxx","name":"ifBranch","type":"CONDITION",
 "caption":"符合条件即进入该分支",
 "description":"<表达式明文>",
 "runAfter":null,
 "expression":{"title":"<表达式明文>","schema":"<JSON 字符串（二次编码）>"},
 "isCompleted":true}
```

`schema` 解一次 JSON：

```json
{"designData":{"expressionTranslation":"...","resultTypeInfo":"BOOLEAN",
   "resultTypeFullName":null,"terminalType":"BACKEND","isMultiSelect":false,
   "context":[ <前序节点出参三级变量树> ],
   "tokens":[{"uid":"...","type":"VARIABLE","value":"_RETRIEVE_x._RETRIEVE_x.expNum","desc":"微流程....实验数量"},
             {"uid":"...","type":"OPERATOR","value":">","desc":">"}, ...],
   "sourceAppName":null},
 "runtimeData":{"executableExpr":"93gDaq3/...+%28+<URL编码表达式>+%29+"}}
```

验收要点：`designData.resultTypeInfo` 必须等于目标位置期望类型（分支=BOOLEAN），`runtimeData.executableExpr` 必须带服务端前缀（手写不可能有）。

## 9. 分支节点的画布内联结构

分支**没有配置抽屉**，DOM 是三块 `.udc-microflow-editor-node-container`（主卡片 `.branch-main` + 两个条件卡片）。`flowFrame` 里：

```json
{"nodeId":"BRANCH_xxx","nodeType":"BRANCH","children":[
  {"nodeId":"CONDITION_a","nodeType":"CONDITION","children":[]},
  {"nodeId":"CONDITION_b","nodeType":"CONDITION","children":[]}]}
```

后端的 `conditions[].actionType` 回读可能是 `None`——这是正常的，不要据此判定没保存。判据看 `conditions[].expression.schema` 是否有值。

## 10. 「变量值」是两层入口，不是直接开表达式面板

修改变量、字段赋值等处的「变量值」输入框，右侧 `+` 按钮（`.sy-icon.lined-plus`）打开的不是表达式面板，而是一个 **ant-popover**（宽约 630）：

```
搜索框 + 变量树（入参对象 / 变量_x / 查询结果 / 空值[系统预制]）
底部 [高级模式]   ← 只有点这个才打开「表达式设置」modal
```

点「高级模式」后 modal 标题是 `表达式设置`（不是分支的「分支条件设置为」），工具栏 `全量复制 / 部分复制 / 粘贴 / 清空 / 验证`，变量树顶部是 `系统变量 / 组织机构 / 日期 / 环境变量 / 插件 / 应用参数 / 附件 / 微流程`，函数树是 `基础 / 日期 / 数学 / 文本 / 条件 / 聚合 / 变化 / 枚举`。打开时自动请求 `expression/schema` 与 `preset/list`。

确认后：输入框显示 `{微流程....字段}`，`form.getFieldsValue(true).value` = `{type:"Expression", expression:{schema, title}}`。**单变量表达式不加括号**，`executableExpr` 是 `前缀+VARIABLE路径`；复合表达式才加 `+%28+...+%29+`。

### ★ 「验证」按钮必须用 JS `click()`，坐标点击落不到它

工具栏那排按钮（`全量复制/部分复制/粘贴/清空/验证`）挤在一个 `.btns` 容器里，`elementFromPoint(验证按钮中心)` 拿到的常常是外层 `.btns`——`click_mouse` 和 `react_click('验证')` 都可能「返回 ok 但零反应」。

```js
const m = document.querySelector('.ant-modal-wrap');
[...m.querySelectorAll('button')].find(b => b.textContent.trim() === '验证').click();
```

**判据是网络请求，不是按钮点没点到。** 点中后会真打 `POST /service/udc/expression/check`，返回：

```json
{"status":2,"code":"FORMULA_6901","message":"计算结果为: 整数 类型, 无法赋值给: 日期时间 类型"}
```

- 表达式为空时点「验证」**不发请求**（前端就拦截），不能据「零请求」判定按钮坏了。先 `insertText` 写点内容再点。
- 目标字段类型定下来之前，`FORMULA_6901` 是正常反馈（表达式本身对，只是类型不匹配），换个类型匹配的字段或表达式即可。

### 值已经改成 Expression、UI 却回显为空

直写 `dataSchema` 把 `{type:"Simple"}` 换成 `{type:"Expression"}` 后端会收，但抽屉控件不认这个形态，字段显示空白、被当成「必填未填」。**结论是这类字段只能通过本节的 UI 路径写，不能后端直填**——直填之后前端一保存就会把空值覆盖回去。

## 11. 面板会进入不可恢复的坏状态

连续失败后会出现：树里有目标字段、搜索框值也对、游标 `focus()` 后 `document.activeElement` 也正确，但插入永远无效、编辑器恒为空。此时**取消面板重新打开**（`+` → 高级模式 / 条件设置）即可恢复，不要在同一次打开里反复重试。

编辑器矩形高度只有 110px 左右（`y≈184~294`），点 `y=285` 这种位置容易落到面板外——用 `getBoundingClientRect()` 现取，不要写死坐标。
