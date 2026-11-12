# 通过 UI 驱动表达式编辑器（点表达式 / 分支条件 / 变量值）

适用：必须在真实前端里写表达式、并要它真的落库时。与「手拼 JSON 直接 POST」是两条独立路线：
UI 路线拿得到服务端生成的 `executableExpr`，且走完前端校验；JSON 路线快但拼错就静默降级。

## 0. 四道门禁，少一道就白干

```
1) ensure_visible  : document.hidden == false
2) ensure_editable : redux.readonly == false
3) 按钮直调        : React props.onClick，不要 el.click()
4) 落库            : 抽屉确定只写 store，还要点「暂存草稿」
```

### 门禁1：document.hidden

页面被遮挡/最小化时 `hidden=true`，后果不是报错而是**渲染缺失**：CSS 动画卡死、下拉坐标 -9999、
抽屉底部「确定」按钮根本不渲染、`contenteditable` 拿不到焦点。`Page.bringToFront` / 激活 tab /
Win32 置顶窗口都不稳定。

```python
d.cmd("Emulation.setFocusEmulationEnabled", enabled=True)
```

一行让 `document.hidden` 变 false，不需要窗口在前台。每次进页面、每次开抽屉前都调。

**但 `setFocusEmulationEnabled` 治不了视口宽度不够**。另一种静默失败：抽屉明明 `ant-drawer-open`，
`aside.udc-microflow-editor-node-settings` 也在 DOM 里，但 `getBoundingClientRect().x` 等于 `innerWidth`
（完全在视口右侧外），`elementFromPoint` 返回 `null`。此时点卡片、点抽屉内按钮全部无效，
而 `document.querySelectorAll('.ant-drawer-open').length` 仍是 1，看起来像“开了但没反应”。

排查与处置（按顺序）：

```js
innerWidth, innerHeight                      // 视口真实宽度
document.querySelector('.ant-drawer-content-wrapper').style.transform   // matrix(1,0,0,1,680,0) = 卡在入场动画帧
document.querySelector('.ant-drawer').getBoundingClientRect().x         // 父容器基准偏移
```

- 手改 `transform:none` / `translateX(0)` **无效**——如果父容器本身就在视口外，位移怎么改都露不出来。
- `windowState:'minimized'` 的窗口 `innerWidth` 会是固定的小值（与屏幕宽无关），恢复窗口也未必变。
- **不要跟 CSS 硬碰**：抽屉不可达就改走接口路线（`references/expression-api-validation.md` +
  `references/expression-bulk-fill.md`），`/check` + `/transform` + GraphQL 写回完全不需要抽屉。

### 点击前必须验坐标在视口内

`Input.dispatchMouseEvent` 用的是 **CSS 像素**（`devicePixelRatio` 不用乘），越界不会报错，只是点空。
所以定位卡片时**不能只看 `textContent` 命中**，必须同时满足四个条件：

```python
0 < cx < innerWidth and 0 < cy < innerHeight   # 在视口内
c['w'] > 20                                     # 不是隐藏层
```

节点卡片常在横向画布上排到 x 上千、或分支子画布在 y>500 处——只按文本找、不按视口筛，
就会反复得到“坐标很大但点不到”的结果。滚到目标后再取一次 rect，不要复用旧坐标。

### 门禁2：readonly（静默失败的真正来源）

```js
window.appReduxStore.getState().appDesign.microflowEditorReducer.readonly
window.appReduxStore.getState().appDesign.microflowEditorReducer.flowBasicInfo.state
```

`state == "RELEASE"` ⇔ `readonly == true`。此时：

- 所有 UI 编辑照常生效，画布正常变化，节点抽屉正常确认
- 「保存并提交」只走只读路径，**不写库**
- 唯一提示是打开页面时那个「您现在处于查看模式」modal，点掉后 DOM 里查不到任何标记
- 更坑：**保存成功后 state 又变回 RELEASE**，所以是「每次保存完就自动锁上」

恢复：点顶栏「编辑」按钮（`y < 120` 的那个），或查看模式 modal 里的「进行编辑」。
恢复后 `state` 变 `DRAFT`、`readonly` 变 false，但 **frame 会重载，nodeId 会变**（`BRANCH_uCjtD5` → `BRANCH_CGZ2GI`）。

### 门禁3：`el.click()` 对 React 按钮静默失败

按钮的 onClick 挂在 fiber 的 `memoizedProps` 上，DOM 原生 `click()` 不触发 React 合成事件。
症状极隐蔽：不报错、不抛异常、UI 全正常，但 store 不动。

```js
const b = [...document.querySelectorAll('button')]
  .filter(x => (x.textContent||'').replace(/\s+/g,' ').trim() === '确定')
  .filter(x => x.getBoundingClientRect().width > 0).pop();
const pk = Object.keys(b).find(k => k.startsWith('__reactProps$'));
b[pk].onClick({preventDefault(){}, stopPropagation(){},
               target:b, currentTarget:b, nativeEvent:{}});
```

实测对比（同一节点、同一份表单，只换点击手法）：
`el.click()` → store `attrs` 仍为 `[]`；`props.onClick()` → `attrs` 3 条、`flowChanged=true`。
**任何「点了但没存」的现象，先换成 props.onClick 再排查别的。**

兜底：若 `onClick` 撞 antd `outOfDate` 竞态（`errorFields: []` 但 `outOfDate: true`），
再用 Enter 三连（表单最后个可编辑输入框发 `keyDown/char/keyUp` 带 `\r`）。

### 门禁4：抽屉确定不覆盖画布内联配置

节点抽屉的「确定」会即时落库（`udcMicroflowUpdatePost`）。
**但分支条件表达式不走抽屉**，它只有流程级保存才会落库——见 SKILL.md「存草稿，不要发版」。
`flowChanged` 变 true 只说明 store 变了，不代表任何一层进了后端。
收工前必须点「暂存草稿」，然后回读后端 `dataSchema` 才算完。

### 修复一条已失效的表达式（清空重选，不要试图在原地改）

表达式引用了已删除节点的旧输出名时，没有任何局部修补手段——
变量树里点不动、展开箭头无反应、键盘也无反应（节点被标成 `leaf-last` 但显示展开箭头，
前端自身状态就矛盾）。唯一可靠路径是**清空重建**：

```
1) props.onClick('清空')         ← 错误提示立即消失，证明清空生效
2) 展开变量树到字段（必要时用搜索框过滤，别靠逐层展开）
3) 真实鼠标 click_mouse 点字段（React 直调在参数位场景反而会丢上下文）
4) 需要常量时点编辑区末尾再 Input.insertText
5) props.onClick('验证') → 必须看到「验证成功」
6) props.onClick('确定')        ← 只进 store
7) props.onClick('暂存草稿')    ← 真正落库
8) 回读 dataSchema 比对 tokens
```

第 2 步展开失败不影响修复：变量树支持搜索框直接过滤字段名，比展开父节点可靠得多
（展开后子行不回显是虚拟列表的已知行为）。

**验证「验证通过」不等于修复**：清空后输入单个 `0`，验证也报成功（合法常量表达式），
但语义上是错的——分支永远是常量。审核时要同时看 tokens 结构与业务语义。

## 1. 打开表达式面板的三条入口

| 入口 | 操作 | 面板标题 |
|---|---|---|
| 分支条件（未配置） | 点条件卡片上的「条件设置」 | `表达式设置` |
| 分支条件（已配置） | **「条件设置」按钮消失**，点条件卡片里的表达式文本块 | `表达式设置` |
| 变量值 / 字段值 | 点表单项右侧 `+` 按钮 → popover → 点「高级模式」 | `表达式设置` |

`+` 按钮点了后是 `.ant-popover`（宽 630），含搜索框 + 变量树 + `空值[系统预制]` + `高级模式`。
**普通模式只是选变量，只有「高级模式」才进表达式面板**，并会自动请求 `expression/schema`、`expression/list`。

## 2. 面板坐标（1000×791，从 modal 自身 rect 推算，别写死屏幕坐标）

```
顶部按钮   全量复制 / 部分复制 / 粘贴 / 清空 / 验证
运算符区   + - × ÷ mod = != > < >= <= and or not true false ( ) 为空 不为空 包含(全部) 属于
.optionalScope   左：变量树（antd Tree）
.funcScope       中：函数树
.explainScope    右：函数说明（这里能拿到 UI 中文名 ↔ 服务端英文名的对照）
[data-elm=editor-wrapper]  编辑区，内含 [data-elm=cursor] 与 [data-elm=token-wrapper]
.verifyMessage   底部左侧的校验消息
```

## 3. 插入变量 / 函数

- **React `onClick` 直调，一次即可**：
  ```js
  const el = n.querySelector('.ant-tree-node-content-wrapper') || n;
  el[Object.keys(el).find(x => x.startsWith('__reactProps$'))].onClick({...});
  ```
  坐标点击要两次（第 1 次只选中），React 直调一次。
- **搜索框必须先清空再输入**：相同值 setter 不触发 React 更新，树不刷新 → 点到旧节点。
- 变量树的节点直挂 `.optionalScope .ant-tree-list-holder-inner` 的**直接子元素**；
  展开父节点后**不回显子行**（虚拟列表），用搜索框过滤字段最可靠。
- **函数名是中文**（`按长度截取字符串`、`为空`、`按指定符号分割文本`），搜 `substring` 永远搜不到。
  服务端英文名只在 `.explainScope` 说明区里（如 `substring(字符串, 起始位置, 截取长度)`）。
- 函数树根节点「函数」默认收起；展开一个分类再展开下一个会因行位移点错，每次先收起。

## 4. 函数参数位（最容易翻车的一段）

插入函数后编辑器显示 `按长度截取字符串(选择,选择,选择)`。

| 坑 | 现象 | 正确做法 |
|---|---|---|
| 选择器 | `.paramPlaceholder` 只找到 2 个，第 1 个漏掉 | 用 `[class*=functionParamElem]` 取最外层（父级不含同位类名） |
| 填参数走 React 直调 | 变量被插到表达式**最前面**，跑到函数外 | **必须真实鼠标**点变量树，React 直调丢失「当前参数位」上下文 |
| 点得太快 | 占位符还是 `选择`，变量没进去 | 点完参数位等 2s，并确认 `document.activeElement.className` 含 `cursorElem` |
| 坐标失效 | 填完一个参数后 y 从 208 变 257（表达式换行） | **每次填参数都重新取坐标** |
| 假成功 | 返回 ok 但参数没填 | 判定用「目标变量出现次数增加」，不能比 text 差异——点参数位本身就会把 `(,选择)` 变成 `(选择,选择)` |

正确顺序：**先搜索好变量（树刷新）→ 点参数位激活游标 → 点变量**。
反了的话点参数位会触发树重置，`_pos()` 取到的坐标已过期。

## 5. 运算符顺序

```
变量 → 运算符 → 变量     ✓
运算符 → 变量            ✗  验证报 `操作符:+ , 输入错误!`
```

插入位置靠「游标是否在末尾」：插变量前把游标移到 `[data-elm=cursor]` 的最后一个。

## 6. 数字字面量不要用键盘

`Input.insertText` 插的数字位置不可控：会粘到前一个参数后面变 `02`，或跑到表达式最前面。
参数全部用变量；非要字面量就先 `placeholders()` 定位、点进去再 `insertText`。

## 7. 校验消息判读

| `.verifyMessage` | 含义 |
|---|---|
| `验证成功` | 语法合法 + 类型匹配 |
| `操作符:X , 输入错误!` / `操作符: + , 不合法` | 运算符缺左操作数 |
| `变量: X 后只能拼接操作符` | 变量后面跟了不合法内容 |
| `计算结果为: 整数 类型, 无法赋值给: 布尔 类型` | **语法合法**，只是目标类型不匹配 |
| `函数:【X】 第 N 个参数类型不匹配 , 期望类型:STRING , 实际类型: INTEGER` | 参数位填错类型 |
| `函数: X , 参数个数不匹配` | 还有参数位没填 |

**`验证` 就是后端校验**：点它发 `POST /service/udc/expression/check`，body 是 `ExpressionSaveDto`
（resultTypeInfo / schemas / tokens / isMultiSelect / terminalSupportType）。上表所有 `.verifyMessage`
文案都是该接口 `message` 的回显。**编辑器为空时点验证不发请求**（前端先拦），别据此判断按钮坏了。

弹窗内按钮不要用 CDP 坐标点：`验证` 的坐标落在同一行的 `.btns` 工具栏 div 上，点击静默无效。
按文案找 `button` 再原生 `b.click()` 即可（与抽屉底部按钮必须走 `props.onClick` 不同）。

## 8. 落库后的结构

`value.expression.title` 外层包 `{...}`；分支条件 `node.expression.title` **不包**。

`executableExpr` 两种形态（手拼必错，只能走 `POST /service/udc/expression/transform`）：

```
单 token → `<加密串>` + URL编码(token)（加密串是 transform 接口的返回，形态见下）
多 token → 同上前缀 + "+%28+" + 编码表达式 + "+%29+"
```

函数 token 形制：`{type:"FUNCTION", value:"substring", desc:"按长度截取字符串", subOps:[[arg1],[arg2],[arg3]]}`
——`subOps` 是**数组的数组**，每格一个参数位，格内可放多个 token。

## 9. 验收：永远不要相信 UI 提示

「数据保存成功！」+ 接口全 200 + 画布正常 + 抽屉无红字 ≠ 落库。

判据按可信度排序，只有最后一个算数：

| 判据 | 可信度 |
|---|---|
| UI 无红色错误 | 低（只说明前端解析通过）|
| 点「验证」返回「验证成功」 | 中（前端校验器过了）|
| `store.flowNodes[id].expression` | 中（只证明 L1）|
| **后端 `dataSchema` 回读 tokens** | **高，唯一真判据** |

前三项全绿而后端仍旧的情况已实测遇到：带抽屉确认的节点（RETRIEVE）进了，
画布内联配置的分支表达式没进——后者只靠流程级保存，而那次点的是 `microflow_save`
（发版 → 自锁 → 写不进），或根本没点「暂存草稿」。

最小完整闭环：

```
ensure_visible → ensure_editable → 开抽屉 → 填表 → props.onClick(确定)
→ props.onClick(暂存草稿) → udcMicroflowFindByIdGet 回读 dataSchema 逐字段比对
```

回读要逐节点比 `actionType` / `output.name` / `expression.tokens` / `attrs[].value`，
不是只看 `code=BOOT_0000`。

## 10. 批量推进节奏

```
ensure_visible → ensure_editable → 开抽屉 → 填表 → props.onClick(确定)
→ 回读比对 → （下一个节点）→ 表达式单独改完后点一次暂存草稿
```

节点抽屉可批量做完；**画布内联的表达式不行**，它只认流程级保存。
若中途误点 `microflow_save`（发版自锁），后面所有节点都会白填——察觉到抽屉打不开
先查 `readonly`，别怀疑坐标。
