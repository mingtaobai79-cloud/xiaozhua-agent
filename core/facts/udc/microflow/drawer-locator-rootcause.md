# Drawer Locator 根因与 CREATE_ENTITY 规范化结论（P5-R1，2026-11-01）

> 证据等级：**LIVE**（真实编辑器 DOM + 真实保存回读）

## 一、`open_node` 返回 `empty drawer` 的根因（三个叠加）

### 1. 编辑器默认「查看模式」，必须先点「进行编辑」

RELEASE 状态的流程打开编辑器时弹出确认框：

```
提示
您现在处于查看模式，所有的修改都无法被保存
[进行编辑] [继续查看]
```

**只要不点「进行编辑」，节点点击一律无效，抽屉永不打开。**
`open_node` 从未处理这个弹窗，所以一直拿到空抽屉。

### 2. ★ 用 `offsetParent !== null` 判断可见性，对 `position:fixed` 元素恒为 false

这是本次最坑的一条。`.ant-modal-wrap` 是 `position:fixed`，按 CSSOM 规范
**fixed 元素的 offsetParent 恒为 null**。于是：

```js
[...document.querySelectorAll('.ant-modal-wrap')].filter(x => x.offsetParent !== null)
// → []   明明 1699×935 的全屏遮罩、z-index 1000 就在那儿
```

用这个判据写的诊断脚本，会把遮挡弹窗整个漏掉，得出「没有弹窗」的错误结论。
**正确判据**：

```js
const VIS = el => { if(!el) return false;
  const s = getComputedStyle(el), r = el.getBoundingClientRect();
  return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 1 && r.height > 1; };
```

### 3. 多个编辑器 target 同时打开，`connect()` 连到后台那个

实测 `Target.getTargets` 里有两个 page 打开了同一个 editor URL。
按 URL 子串 `connect('microflow/editor')` 会命中第一个，而它可能在后台
（`document.hidden === true`），点击全部无效。
**必须按 targetId 精确连接，或先关闭多余 target。**

## 二、验证过的可用路径

```
打开 editor → 点「进行编辑」（Modal 内按钮）
→ 抽屉自动打开上次选中的节点 → 改字段 → 确定 → 保存并提交
```

关键事实：
- 点「进行编辑」后，抽屉会**自动打开**上次选中的节点，不需要再点节点
- 「确定」生效后抽屉进入关闭动画（body 已清空，只剩不可见的 close 按钮）
- 「保存并提交」后流程变 **DRAFT**，需要重新 publish 才能构建

## 三、★★ CREATE_ENTITY：设计器产物与构造器产物**逐字段完全一致**

这是本轮最重要的结论，推翻了「构造器形态有缺陷」的假设。

流程：在临时验收流程里，用设计器把 `f01text` 从 `P5R1` 改成 `P5R1X`，
点确定、保存并提交，然后回读节点 JSON，与保存前逐字段对比。

```
键集差异     : 设计器新增 [] / 删除 []
output       : 完全一致
            {"id":null,"javaType":"java.lang.Long","dataType":"BIGINTEGER",
             "type":"OBJECT","desc":"新增数据的ID","name":"_CREATE_ENTITY_472cc2"}
attrs        : 一致，值形态一致
            f01text => {"type":"Simple","simple":"P5R1X","desc":"P5R1X"}
变化字段     : 无（只有业务值 P5R1 → P5R1X）
```

**结论：构造器产出的 CREATE_ENTITY 就是平台规范形态。**
publish / build / UI 三层全绿而运行时 attrs 不生效，
**不是结构问题**。

## 五、★ 平台限制：关闭抽屉会卡死（不是 locator 的问题）

连续开合验收时暴露：**抽屉一旦被关闭，就再也打不开**。

卡死特征（实测 DOM）：

```
.ant-drawer 宽度 1383、height 795   ← 仍然「打开」
.ant-drawer-body innerHTML.length = 0   ← 内容已清空
.ant-drawer-close rect = [0, 0]         ← 关闭按钮不可见，点不到
className 含 no-mask / ant-drawer-in
React props 只有 onKeyDown             ← 没有 onClose，关闭由父状态控制
```

试过全部无效：

| 手段 | 结果 |
|---|---|
| `click_react` 调 `.ant-drawer-close` 的 onClick | 返回 `ok`，抽屉不动 |
| 真实鼠标点 close（坐标来自 rect） | rect 0×0，无从点起 |
| `Escape` 键 | 无效 |
| 点画布空白处 | 无效 |

**因此拆成两个独立结论，不混为一谈：**

- **打开是否可靠** → 每轮重新加载页面后打开，单独验收
- **关闭是否可靠** → 平台限制，不假装通过

工程含义：**验收脚本不能依赖「关闭后重开」**，要么每轮重载页面，
要么一次会话只打开一个节点。`close_drawer` 保留但标注为「平台侧不可靠」。

## 六、剩下的可疑点：值形态 Simple vs SelectParam

真实样本 `fixtures/microflow/create_entity_node.sample.json` 里：

```json
"value": {"type": "SelectParam", "selectParam": {
  "key": "_CREATE_VARIABLE_uX6yClcom.seeyon...YsFull6956Dto.f01text",
  "name": "f01text", "id": "...Dto.f01text", ...}}
```

即真实样本用 **SelectParam（引用变量）**，而构造器用 **Simple（字面量）**。

设计器输入字面量后保存，回读**仍然是 Simple** —— 说明 Simple 形态本身合法。
因此当前假设是：**运行时可能不应用 Simple 值，只认 SelectParam**。
这一点尚未验证，需要做对照实验（见下）。

## 五、下一步（阶段 D/E）

对照实验：
```
A. create_variable(mark = "RTV3xxx")
   → create_entity(f01text = Simple "RTV3xxx")        ← 已知会失败
B. create_variable(mark = "RTV3xxx")
   → create_entity(f01text = SelectParam 引用 mark)   ← 待验证
```

若 B 成功、A 失败 ⇒ 根因确认：**CREATE_ENTITY 的 attrs 只认 SelectParam 引用，
字面量 Simple 在运行时被忽略**。这是平台行为，不是构造器缺陷，
但构造器必须据此调整默认策略（字面量先落变量再引用）。

## 六、其它确认

- 实体 `<ENTITY_CAPTION>` 有运行时校验：`f05dec ≤ 999.99`、`f03int ≤ 100`、
  `f02multi` 非空；平台给未赋值字段填「当年」（2026），会直接撞这三条。
- `CREATE_ENTITY` 的 output 是 `BIGINTEGER`（新增数据 ID），
  不是 `INTEGER`——`basic_out` 写 INTEGER 会被组装闸门拦。
- `change_variable` 的 `output` 是 null，**不能作为 end 节点引用源**。

## 七、节点定位的补充实测（2026-11-02）

### ★ 更正：节点卡片的 title 是 caption，body 才是实体名

早前记录「节点卡片显示的是实体名，不是 caption」——**这条是错的**。

实测卡片 DOM：

```json
{"title": "插入-UI观察",                      // ← caption
 "body":  "小爪验收实体全量 [长整数] [单条]",   // ← 实体名在这里
 "remark": ""}
```

所以定位关键词**用 caption 更准**。用实体名匹配虽然也能命中（body 里含实体名），
但 trigger 节点也绑同一个实体，容易匹配错节点（实测点开过「创建变量」节点）。

### 多 tab：localhost 和正式域名会同时开编辑器

`/json/list` 里可能同时存在：
```
https://lowcode-test2.<HOST>/.../microflow/editor/<mid>   ← 目标
http://localhost:3000/.../app-basic-info/testVersion      ← 本地开发，也可能被选中
```
`connect()` 靠 URL 里的 `/microflow/editor/` 匹配，正常情况下选得对；
但连上后仍要 `Page.bringToFront`（已内置），否则 `document.hidden=true` 时
antd 浮层渲染 0 宽。

### 查看模式 Modal 会在刷新后重新出现

`ensure_edit_mode()` 点掉 Modal 后，**如果随后 `Page.reload()`，Modal 会再来一次**。
所以顺序必须是「navigate → reload → 等渲染 → `ensure_edit_mode`」，
不能在 reload 之前调。调完要回读 `document.querySelectorAll('.ant-modal-wrap').length === 0`
再点节点，不要只信函数返回值。

### 单节点流程的编辑器交互异常（未解决）

只有 1 个业务节点的流程（trigger + ce），画布渲染 1 个节点时，
`body_click` / 真实鼠标 / `onClick` 直调**全部无效**（`locator=1` 但抽屉不开）。
加到 3 个节点（`create_variable` + `change_variable` + `create_entity`）后
画布正常渲染 3 个，但点击仍未打开抽屉。

**现象未定性，暂记为「UI 观察路径受阻」**，不影响 API 侧的任何结论。
后续若要在设计器里观察节点配置，建议先在**已有业务流程的节点**上做（那些流程 UI 正常），
而不是新造的临时流程。
