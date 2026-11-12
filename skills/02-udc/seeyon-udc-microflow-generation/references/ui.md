# 设计器 UI 自动化与验收

> 由 SKILL.md 拆分而来，按需读取。

## ★ 红节点只认 `isCompleted`，不要看颜色

设计态本来就有一堆红：**默认/不符合条件分支是珊瑚红（rgb≈255,120,117）**、**自定义错误节点本身是红色**、
选中的列表项带强调色。按颜色扫「红节点」会把这三类全部误报（实测 6 条流程 6 次误报、0 个真问题）。

权威判据在 redux：

```js
appReduxStore.getState().appDesign.microflowEditorReducer.flowNodes
// 逐个（含 conditions[].nodes 递归）看 isCompleted === false；elseBranch 的 null 是正常态
```

配套两个读文本的硬约束：
- `document.hidden === true` 时 **`innerText` 恒为空**（扫出 0 个节点、误判「页面没渲染」）→ 一律用 `textContent`；
- 节点卡点击直调 React fiber 的 `memoizedProps.onClick`，且必须写成 `(() => {...})()`；
  写成 `(i => {...})` 加下标拼字符串不会执行，静默返回 undefined。

成品函数：`components/udc/microflow/live/verify.py` 的 `verify_flow()`（扫红+开抽屉读红字+重新发布）与
`prove()`（发布/UI/参数名/检测四层）——直接调用，不要重写扫描循环。

## ★ 三个隐藏闸门：configChanged / document.hidden / outOfDate


### 0. `configChanged === false` 时点「确定」只关抽屉、零写入

**所有字段都有默认值的节点（FOR 计数循环最典型：`0/0/1/<=/计数循环变量_1`）如果一项都不改，`configChanged` 保持 `false`，点「确定」只关抽屉、不发 `udcMicroflowUpdatePost`。** 节点只活在 Redux store 里，后端零写入，而抽屉关闭看起来像成功。

- 判据：提交后查 `d.net` 里有没有 `udcMicroflowUpdatePost`；没有就是没落库。
- 解法：提交前**真实修改任一字段**（改出参名/循环变量名最省事）置位 `configChanged`。
- 这也是「改了自绘控件却没生效」的同一根因：自绘控件的改动不进 antd form 的 values，`configChanged` 不翻。

### 1. `document.hidden === true` 会让所有 antd 浮层静默失效

页面被遮挡/最小化时（CDP 多 tab 场景几乎必然发生）：

- `.ant-select-dropdown` 存在、选项数量正确，但 `getBoundingClientRect().width === 0`、`opacity:0` → 看起来「下拉打不开」
- 抽屉底部「确定」按钮**根本不渲染**（只剩右上 ×）
- 表达式编辑器 `[data-elm=cursor]` 拿不到焦点

```python
d.cmd("Emulation.setFocusEmulationEnabled", enabled=True)   # 一行解决，不需要窗口在前台
```

**它会反复变回 true**，不是修一次永久有效。所以封装成一个「每次交互前调用」的幂等函数：

```python
def ensure_visible(d):
    if d.eval("document.hidden") is True:
        d.cmd("Emulation.setFocusEmulationEnabled", enabled=True)
        time.sleep(0.8)
    return d.eval("document.hidden") is False
```

点下拉的封装必须「ensure_visible → 点击 → 校验下拉宽度>0 → 为 0 就重试」三件套，否则得到假结果。

**`setFocusEmulationEnabled` 管的是「渲染」，不是「派发」——两者是不同问题，别拿一个当另一个的替代。**
渲染类失效（下拉宽 0 / 确定按钮不渲染 / 光标拿不到焦点）必须用 `Emulation.setFocusEmulationEnabled`；
而 **CDP `Input.dispatchMouseEvent` 能不能落到页面，取决于该 tab 是不是当前活动 target**——`document.visibilityState` 一直是 `hidden` 也能点，只要先在同一 CDP 会话里发一次 `Page.enable` + `Page.bringToFront`。

症状是**静默无反应**：`click_mouse` 不报错，但 `currentSelected.nodeId` 仍为空、`sideSettingVisible:false`、抽屉数 0——看起来像「节点坏了 / 只读态」，实际是事件根本没派发。判据：点一次读 `currentSelected`，没变就是没派发。
`Page.bringToFront` 只用一次不够——**长时间批量点击过程中 tab 会重新失焦，每轮点击前都要补一次**。`/json/activate` 单发无效。

可直接复用 `scripts/cdp_drawer_ops.py`：`ensure_visible` / `bring_to_front` / `open_node` / `pick_option` / `read_form` / `submit_drawer` / `set_input` / `drawer_alive`，都是这套坑踩完后的成品。**逐节点验收直接调 `validate_all_nodes(d, mid)`**（已含控制节点排除、滚动收集、命中校验、重试，返回 `{ok, errors, error_list, skipped}` 四分类）——不要每次重写扫描循环，那种脚本极易在坐标/命中/只读态上反复翻车。

**项目侧交互原语（CDP 驱动库，在 `seeyon-agent` 仓库里）**：`components/udc/microflow/live/react_click.py`
提供 `react_click` / `set_controlled_input` / `open_antd_select` / `pick_option`。
所有 React 按钮（抽屉「确定」、「添加字段」、「编辑」）必须走 `react_click`，不要 `el.click()`。
配套交互契约文档：`core/facts/udc/microflow/react-interaction-contract.md`。

**`components/udc/microflow/live/ui.py` 是逐节点操作的高层封装，优先用它而不是自己拼坐标逻辑**：`ensure_visible(d)`（焦点仿真）/ `ensure_editable(d)`（清查看模式弹窗 + 点「编辑」进编辑态）/ `state(d)`（读 `readonly`、`flowBasicInfo.state`）/ `open_node(d, keyword, tries=2)` / `close_drawer(d)` / `confirm_node(d, wait=8.0)` / `submit(d, strategy="onfinish")`。
注意返回值语义：`open_node` 成功返回字符串 **`ok`**，失败返回 **`empty drawer`**——不要写 `if not opened or not opened.startswith("{")` 这类判据，那会把成功当失败（控制节点无抽屉时才真的是 `empty drawer`）。`confirm_node` 正常返回 dict，但内部走 `click_el` 时可能返回字符串，取值前先 `isinstance(res, dict)` 兜一层。

**仓库里有两个 CDP 客户端，API 不同，别混用**：`providers/cdp.py` 的 `CdpClient` 只有 `evaluate` / `click` / `click_by_text` / `send`（**没有** `eval` / `click_mouse` / `navigate`）；`components/udc/microflow/live/cdp.py` 的 `Driver` 才有 `eval` / `click_mouse` / `cmd` / `net`（**没有** `navigate`，跳页用 `eval("location.href=...")`）。要抓网络包、点画布坐标、读 store 就用 `Driver`。

`Driver` 依赖 `websockets`；项目的 `.venv` 里没有 pip，装依赖用 `uv pip install websockets --python .venv/Scripts/python.exe`。

### 2. 抽屉提交是三级兜底，不是「按 Enter 就行」

点 `.compid_node-config-submit-btn` 会抛：

```
{"values":{...完整正确...}, "errorFields":[], "outOfDate":true}
```

`errorFields` 空但 `outOfDate:true` → 提交被拒、抽屉不关、store 不更新、后端零写入。
**这是 rc-field-form 的时序断言，不是业务校验**：动态增删行（排序规则行、映射行）和 `settingkey` 自绘控件让 `values` 与 Field 列表不同步，于是 `validateFields` 认为表单 outOfDate。
`setFieldsValue` / `setFieldValue` / 手动调 `onValuesChange(changed, all)` / 内部 `updateValue` dispatch **全部无效**。

可靠做法是三级兜底，按序尝试、以「是否发出 `udcMicroflowUpdatePost`」判成功：

1. **Enter 三连**（keyDown/char/keyUp，char 带 `\r`）—— 只在最后一个是 `input.ant-input` 时有效。
2. **点「确定」**。
3. **直调 Form 的 `onSubmit(values)`**（从 `form` DOM 的 `__reactFiber$` 向上找到 dep≥5 的 `memoizedProps.onSubmit`，传 `form.getFieldsValue(true)` 的返回值）。

第 3 级仍是前端自己的提交链：构节点、发 `udcMicroflowUpdatePost` 照跑，只是绕过 antd 的时序断言。**含动态行的抽屉（排序规则、映射关系、条件行）前两级经常双双失效，直接上第 3 级，别在 Enter 上反复重试浪费时间。**

**但第 3 级必须设闸门：跳过 `errorFields` 非空的提交会把半成品写进后端。**

前两级点「确定」时前端会抛 `unhandledrejection`，`errorFields` 有两种形态，含义完全不同：

| 形态 | 含义 | 处置 |
|---|---|---|
| `errorFields:[]` + `outOfDate:true` | 纯时序断言，values 完整正确 | 可以上第 3 级 |
| `errorFields:[{name:["structure"],errors:["请输入选择实体"]}]` | **真业务校验未过** | **禁止提交**，回头补必填 |

所以进第 3 级之前先读一次上次的 `probe_errors()`，`errorFields` 非空就**直接返回失败并把缺失项报出来**，不要提交。

否则的后果是静默的数据损坏：`onSubmit` 不带校验地跑完，把 `structure:null` / `condition:null` / `sortParams:null` 的残缺节点写进 dataSchema，而 `udcMicroflowUpdatePost` 照样返回 200。下一轮再从抽屉里读，字段已经是空的，程序还以为是「下拉点不开」——真实因果关系完全错判，且要花很久才能发现是自己写坏的。

**安全顺序：先补齐必填 → 再提交。任何一轮「提交成功（200）」之后必须立即 `read_schema` 回读核心字段非空**，尤其 `structure` / `condition` / `output.id`。

推论：**抽屉是「关闭即丢弃」**（×/取消）× **「确定即保存」**，没有「关闭自动保存」。改完值后点右上 × 等于白改。

### 3. 自定义 setting 控件不认 setFieldValue

创建变量抽屉的 radio/select 是 `<div settingkey="dataType" ishidden="paramType != 'BASIC'">` 这类框架自绘控件，
`form.setFieldValue('paramType','ENTITY_OBJECT')` 只改 form 值，**不重算 ishidden、不重建子表单**。
必须真实点击 `label.ant-radio-button-wrapper`（`.click()` 可用）才能切换表单形态。

**反过来：简单 radio/tabs（非 settingkey）默认值错了，CDP 点 input/wrapper/圆点都切不动，但 `form.setFieldsValue` + onfinish 能落地。** 典型：查询多条的「分页查询」`pageSearch` 前端默认字符串 `"true"`（分页开，导致 pageInfo 变必填）；插入/更新的「赋值方式」`mappingType` 默认 null。点 radio 的 input（opacity:0）/wrapper/视觉圆点都不触发 onChange（onChange 在 rc-field-form 层，input 隐藏）。用 `ui.set_form_field(d,'pageSearch','false')`（即 `form.setFieldsValue`）再 `ui.submit(onfinish)`，回读立即正确。权威默认值查 `fixtures/microflow/node_templates/<ACTION>.json`（如 RETRIEVE_ARRAY.pageSearch="false"、CREATE_ENTITY.mappingType="attrs"）。

### 4. 7 种 paramType × 7 种 dataType 落库契约

见 `references/create-variable-7x7-contract.md`（含每种 paramType 完整后端结构、`sortParams`、`structure:null` 特例）。
表达式四种形态的真实后端结构见 `references/expression-4-types-landed.md`。

## ★ 判据铁律：只认 store 或后端回读，不认脚本返回值

本会话所有重大误判都源于同一件事：**脚本返回 `ok` 就当成成功了**。

```python
# 无效判据（会骗你）
r = react_click(d, '确定')
assert r['ok']            # 只证明点击发生了
assert drawer_closed      # 只证明 UI 关了
assert 'picked:天数' in log  # 只证明下拉项被点中

# 有效判据
n = js(d, "appReduxStore.getState().appDesign.microflowEditorReducer.flowNodes['<id>']")
assert len(n['attrs']) == 3

# 更强：后端回读
meta, ds = env.read_schema_page(d, MID)
assert len(find_node(ds, '<id>')['attrs']) == 3
```

三个真实失效场景，每一个的 UI 表现都完全正常：

| 手法 | UI 表现 | 实际结果 |
|---|---|---|
| `el.click()` 点确定 | 抽屉正常关、无报错 | store 未更新，后端零写入 |
| `configChanged=false` 时点确定 | 抽屉正常关 | 零写入（见上文闸门 0） |
| 只读态下改节点 | 抽屉正常关、提示「数据保存成功！」 | 后端一字节未变 |

**推论：报告「修好了」之前，必须贴出 store 或后端回读的实际值。** 不能说「已修复」而依据是脚本日志。体检脚本 `health_check_*` 必须从后端 `readSchema` 取数，不能读 store——store 是前端缓存，重载即失。

### ★ 反向陷阱：后端字段有值、前端显示空 —— 不是没填，是形态不对

前端每个表单项绑定一种控件类型，控件只认自己的值形态：`select` 要字符串、`treeListSelector` 要 `{label,value,key,dataType}` 对象、`valueComponent` 要 `{type:"Simple"|"SelectParam"|"Expression"}`。**后端 `checkSchema` 只看结构不看形态**，形态错了照样 errors=0。

判据：后端回读该字段非空，但抽屉里是灰色占位文案（「选择数据类型」「请选择映射」「请输入映射键」）而不是你写的值 → **换形态，不是重填**。

这条解释了最容易被误判的一类现象：用户说「这个必填你没写」，而你的脚本里明明赋了值。先回读确认值在，再看抽屉渲染成什么——值在但显示空，就是形态问题。

**每个控件的形态契约要落成事实文档，不要散在各处**：仓库维护 `core/facts/udc/microflow/node-field-shape-contract.md`，按节点记 `控件类型 → 期望值形态 → 传错时的连锁后果`（如 `MAP_OPERATION.basic` 是 `treeListSelector`，传裸字符串会被 `structure:{...basic}` 迭代成字符下标对象）。发现新的形态坑就追加到那篇，**不要只在会话里说一遍**——形态类缺陷 `checkSchema` 永不报，不落文档下次照样重犯。

### ★ 直写 dataSchema 把 Simple/SelectParam 换成 Expression 等于写坏

`udcMicroflowUpdatePost` 直接提交改好的 `dataSchema`（把值槽 `{type:"Simple"}` 换成 `{type:"Expression",expression:{title,schema}}`）后端照收：`BOOT_0000`、`content:1`、回读确实是 Expression、`/expression/check` 也全绿。**但前端控件不认这个形态**——抽屉里那些字段回显为空，用户看到的就是「必填项没填 / 数据没保存」，再一保存就被前端当空值覆盖回去。

判据盲区在于：所有「后端」证据都对，坏的是回显层，只有打开 UI 才看得见。所以**表达式必须走 UI 写**：值字段右侧 `+` → 变量选择器弹层 → 「高级模式」 → 表达式设置面板 → 填 → 「验证」（真打 `/expression/check`）→ 「确定」回填 → 抽屉「确定」/ 「暂存草稿」落库。用户对这条有明确要求，不接受绕过 UI 的批量写。

### 体检类脚本的自我欺骗：扫描器本身会漏层

「只认回读」管的是「写成功了没」，管不住「**扫描器根本没看到这一块**」。两者是不同的事故：

| 事故 | 表现 | 防法 |
|---|---|---|
| 写没进去 | 脚本返回 ok、抽屉关了 | 回读 store / 后端 |
| **扫没扫到** | 所有节点都「干净」，用户一开某个面板就是红字 | 对每种可配置形态都写一个结构特征发现器 |

第二种更危险：它让报告看起来完美。**报关前先自问「我这个扫描器靠字段名白名单走，那些结构不是字符串的字段（表达式、映射规则、嵌套条件）扫到了吗」**。能用结构特征（`dict` 且含某几个 key）递归发现的，就不要靠字段名枚举——靠枚举就一定会漏。

体检报告里「全部健康 / 0 问题」这类断言，下面必须附一行「已扫过的形态清单」（必填字段 / 空白字符 / 悬空引用 / **表达式 tokens** / 参数类型值域）。没有这份清单的「0 问题」不要发给用户。

## ★ 编辑前置闸门：每次进编辑器先确认 `readonly === false`

**这是所有 CDP 编辑的前提，不通过则后面全部白做。**

```js
const st = appReduxStore.getState().appDesign.microflowEditorReducer;
st.readonly          // true = 只读态，一切编辑不落库
st.flowBasicInfo.state   // "RELEASE" → readonly:true
```

### 解除查看模式：弹窗可叠多层，`readonly` 可能仍为 true

「您现在处于查看模式」的 `.ant-modal-wrap` **会叠 3 层以上**（多次进入/保存后累积）。
只点一次「进行编辑」不够——剩下的层继续遮挡画布，表现为所有点击落空、`open_node` 返回 `empty drawer`、`nodeConfigObj` 为空。

```python
def clear_view_mode(d):
    for _ in range(8):
        if not d.eval("(()=>document.querySelectorAll('.ant-modal-wrap').length)()"):
            break
        d.eval("""(()=>{const ws=[...document.querySelectorAll('.ant-modal-wrap')]
          .filter(w=>w.getBoundingClientRect().width>0); if(!ws.length)return;
          const b=[...ws[ws.length-1].querySelectorAll('button')]
            .find(b=>(b.textContent||'').trim()==='进行编辑'); if(b)b.click();})()""")
        time.sleep(2.8)
```

**`ensure_edit_mode()` / `ensure_editable()` 要在所有导航动作之后调，不能在此之前。**
`Page.navigate` → `Page.reload` 会让「查看模式」Modal 重新弹一次，把之前已经点掉的弹窗又叠回来。
正确顺序：`navigate → reload（需要时）→ 等画布渲染出节点 → ensure_edit_mode → 复查 `.ant-modal-wrap` 数量为 0 → 再点节点`。
调完要**回读 `.ant-modal-wrap` 数量**再往下走，不能只信函数返回值——它有可能返回 true 而弹窗又已重生。

弹窗清空后**仍要复查 `readonly`**：清完弹窗 `readonly` 仍可能是 `true`，此时顶栏会出现「编辑」按钮（约 `x=1448,y=56`），点它才真正进编辑态，之后 `#microflow_save` 才会出现且 `disabled:false`。
**`#microflow_save` 不存在 = 还在只读/日志态**，这是最快的判据，比读 store 直观。

只读态下的表现是**静默失败**：画布正常加节点、抽屉确认正常关闭、点「保存并提交」接口全 200（`CheckSchemaUpdate` → `FindByIdGet` → `Search` → `DisableNodePost` → `GroupSelectByType`），但后端 `dataSchema` 一个字节都没变。唯一提示是页面刚打开时的「您现在处于查看模式，所有的修改都无法被保存」modal，点掉后再也看不到，DOM 里也没有任何模式标记。

恢复：点顶栏「编辑」按钮（`state=RELEASE` 时第 44 行右侧才会出现，约 `x=1658,y=56`），等待后复查 `readonly===false`，此时会重新走一遍 `udcMicroflowUpdatePost` 并重新加载 frame（分支等节点 id 会变，如 `BRANCH_uCjtD5` → `BRANCH_CGZ2GI`）。

**保存会自动把 state 打回 RELEASE**——「保存并提交」成功后 `readonly` 立刻又变 `true`。所以逐节点闭环的正确节奏是：

```
确认编辑态 → 改一个节点 → 保存并提交 → 后端回读核对 → 重新点「编辑」进编辑态 → 下一个节点
```

不是「进一次编辑态连改十个节点再存一次」。跳过重进编辑态这一步，第二个节点起的所有改动都是静默失败，且前端表现完全正常（抽屉正常关、表达式卡片正常显示、保存提示「数据保存成功！」），只有后端回读能看出没写。把「检查 readonly」写成每个节点闭环的第一步，不要只在会话开头检查一次。

**`#microflow_save` 是「保存并提交」，不是保存草稿——不要用它存草稿态的节点改动。** 点它会发布成 RELEASE 并立刻 `readonly:true`，之后节点全不可编辑、抽屉打不开、`aside` 会残留 2 个。

**节点抽屉「确定」不一定发请求——先看 `flowChanged`，别急着判失败。** 未改动任何字段时点「确定」是 `configChanged=false`（闸门 0），抽屉正常关、`d.net` 为空，那是没改，不是坏了。改动过字段就是另一回事，仍必须回读 store / 后端确认。

**流程级保存用「暂存草稿」，不要用 `#microflow_save`。** 实测「暂存草稿」→ `udcMicroflowUpdatePost`，body 带整份 `dataSchema`（几十 KB），返回 `BOOT_0000 data.content=1`，`flowChanged` 由 true 翻 false，`state` 仍是 `DRAFT`。画布内联的分支条件、出入参、首节点都必须走这条才落库；`#microflow_save` 是「保存并提交」，会把流程打成 RELEASE 并锁死编辑。

从 RELEASE 回到可编辑态的正确恢复路径：

```python
react_click(d, '编辑')          # 工具栏「编辑」，转回 DRAFT
time.sleep(3)
d.eval('location.reload()')     # 必须 reload
```

**转 DRAFT 后不 reload 是常见的死路**：store 里 `readonly` 已变 `false`、`state` 已变 `DRAFT`，但画布仍处于旧渲染，`aside` 残留、抽屉打不开，会误判成「节点坏了」。判据看 `document.querySelectorAll('aside.udc-microflow-editor-node-settings').length`，非 0 就是没清干净，reload 一次。

**反过来也要记住：进编辑态会把 RELEASE 打回 DRAFT。** 只为跑 UI 逐节点验收而点「编辑」，流程就变回草稿；**验收完必须重新走 REST `checkSchema/update`（`state:"RELEASE"`）发布**，否则交付出去的是草稿。UI 验收与发布是两个独立动作，验收结束要复查 `state`，别把「抽屉里没红字」当成交付完成。

**画布内联配置的节点（BRANCH 的 condition 表达式）最容易中招**：它不走节点抽屉，只有流程级「保存并提交」才落库，被只读态吞掉后前端卡片仍显示完整表达式，极易误判成功。所以每个节点写完必须「后端回读 diff 前端 store」，不能看提示、不能看画布。

## ★★ 可见性判断：绝不能用 `offsetParent`

**按 CSSOM，`position:fixed` 元素的 `offsetParent` 恒为 `null`。** 而 antd 的
`.ant-modal-wrap` 正是 `position:fixed` + `z-index:1000` 的全屏遮罩。于是：

```js
[...document.querySelectorAll('.ant-modal-wrap')].filter(x => x.offsetParent !== null)
// → []          明明 1699×935 的「查看模式」弹窗就在画布上压着
```

后果极严重：诊断脚本会得出「没有弹窗、页面正常」的结论，然后花很久去怀疑
CSS 选择器、节点坏了、只读态、事件没派发——全部方向错误。

**正确判据（唯一）：**

```js
const VIS = el => { if (!el) return false;
  const s = getComputedStyle(el), r = el.getBoundingClientRect();
  return s.display !== 'none' && s.visibility !== 'hidden'
      && r.width > 1 && r.height > 1; };
```

同理，**「按钮存在」与「按钮可点」是两件事**：弹窗里的「进行编辑」按钮
`getBoundingClientRect()` 返回非零坐标（可点），但它所在的 wrap 会被
`offsetParent` 判成不可见。判可点只看 rect，不看 offsetParent。

## ★★ 打开节点抽屉：只有 `node-body` 的 React onClick 有效

节点卡上有多个看起来都能点的入口，实测只有一条能真正打开抽屉：

| 触发方式 | 调用结果 | 抽屉 |
|---|---|---|
| `.udc-microflow-editor-node-container` 的 `onMouseDown` | 能调通 | ❌ 不动 |
| CDP `Input.dispatchMouseEvent`（真实鼠标，命中已校验 insideCard=true） | 已派发 | ❌ 不动 |
| `.more-btn` 的 onClick | 能调通 | ❌ 不动 |
| **`.node-body` 的 `onClick`** | 能调通 | ✅ **打开** |

```js
const body = card.querySelector('.node-body') || card;
const k = Object.keys(body).find(x => x.startsWith('__reactProps$'));
body[k].onClick({currentTarget: body, target: body, preventDefault(){},
  stopPropagation(){}, persist(){}, nativeEvent: {}, type: 'click'});
```

**不要因为 card 上有 `onMouseDown` 就把它当主路径。** 命中测试、选中态、
`__reactProps$` 全都正常，点击也返回 CALLED，抽屉就是不开——会把人引向
「节点坏了 / 只读态 / 坐标漂了」这些错误方向。

做法：**按优先级回退**（body_click → card_mousedown），谁让抽屉出现就用谁，
并把实际生效的方式写进诊断结果，避免平台改交互后静默失效。

### ★ 问「节点里到底存了什么」不要去开抽屉，去读生成代码

上表是「在已有业务流程上」实测的。**新造的流程上它可能全部失效**：`body_click` 返回
`BODY_CLICK`、真实鼠标已派发、`elementFromPoint` 命中 `node-body`、无浮层遮挡、
`document.hidden=false`，抽屉就是不开。单节点流程与 3 节点流程都复现过。

遇到这种情况**不要继续换点击手法**（真实鼠标 / `onMouseDown` / `onClick` 直调 / 换节点
都已试过，是同一个无效方向）。先回答一个问题：**你开抽屉到底想拿什么信息？**

| 想确认的事 | 正确来源 |
|---|---|
| attrs 到底生效了没 | 生成代码 `Rtv…Service.java` 的 `assignValue2JavaBean…` |
| 字段值会被什么覆盖 | 实体 `XxxService.preCreateBatch` 的 `executeExpression` |
| 实体能不能写 | `api/XxxAppService.java` 有没有 `create` |
| 平台认不认这个节点形态 | 设计器改值后回读 diff（本文件末「设计器规范化取证」） |

四件里三件的答案都在构建产物 zip 里，而且**比 UI 快一个数量级、还不依赖登录态**。
UI 抽屉只在「形态是否被前端接受」这一件上不可替代。

推论：**要在设计器里观察节点配置，挑已有业务流程的节点做**，别拿刚造的临时流程当观察对象——
临时流程的 UI 行为不是可靠观测面，而它的生成代码一样能看。

## ★★ 节点卡片：`node-title` 是 caption，`node-body` 才是实体名

卡片有四层，各装不同东西：

```json
{"title":  "插入-UI观察",                      // ← .node-title = 节点 caption
 "body":   "小爪验收实体全量 [长整数] [单条]",   // ← .node-body = 实体 caption + 类型 + 基数
 "remark": ""}
```

**定位关键词必须打在 `node-title`（caption）上，不要用整卡的 `innerText`。**
整卡 `innerText` 是 title+body 拼接，按实体名去搜也会命中，但 **trigger 节点
绑的是同一个实体**，于是很容易点到别的节点（实测点开过「创建变量」），
或因为多个卡片同分而匹配到错位置。

排查时先 dump 每张卡的 `{i, x, y, title, body, remark}` 逐层看，
不要只拿 `innerText` 一刀切。

## ★ 结构化返回：空抽屉绝不能算成功

`open_node` 只回 `ok` / `empty drawer` 两个字符串，分不清「节点没找到」「点了没反应」
「抽屉在加载」「打开的是别的节点」。改用 `open_node_report()`，返回：

```
status            OPENED / NODE_NOT_FOUND / NODE_NOT_SELECTED / DRAWER_NOT_VISIBLE /
                  DRAWER_LOADING / DRAWER_CONTENT_EMPTY / DRAWER_IDENTITY_MISMATCH / TIMEOUT
expected_node_id  selected_node_id  drawer_visible  drawer_title
locator_count     diagnostic[]      screenshot_path
```

两条硬约束：
- 返回 `OPENED` 之前**必须校验抽屉标题与目标节点一致**，否则是「打开了别的节点」冒充成功。
- `bodyLen === 0` 一律判 `DRAWER_LOADING` / `DRAWER_CONTENT_EMPTY`，**不许当成功**。

等待用状态轮询（每次 0.5–0.6s 查一次），不要固定长 sleep——固定 sleep 既慢又不准。

### 给 CDP 封装写单测：假 Driver 按 JS 内容匹配，不按调用顺序

用「依次消费脚本数组」的假 Driver（`FakeDriver(script)` 每次 `pop(0)`）会在生产代码
多一次 `eval` 时集体错位，改一次实现就要重排一整套断言，而且错位后报的错是
`NODE_NOT_SELECTED` 这类下游状态，看不出是假件错位。

改成**按 JS 内容返回**：`查看模式` / `bodyLen` / `width > 200` / `matched` / `BODY_CLICK`
各返回预设值。实现加一次 `eval` 不会破坏已有用例。

两条顺序硬约束：
- **判据要从具体到宽泛**。`_drawer_snapshot` 的 JS 里也有 `width > 200`，如果先判
  「残留抽屉」分支就会被截胡，snapshot 永远拿到 `-1`，于是所有用例报抽屉没开。
- **快照栈空后要「保持最后状态」**，不能回 `visible:false`。真实环境里抽屉开着就一直开着；
  假件回 false 会让最终状态等待超时，表现为假阴性。

## ★★ 多个 target 开同一 URL，`connect()` 会连到后台那个

`Target.getTargets` 里可能有**两个 page 打开同一个编辑器 URL**（反复导航会累积）。
按 URL 子串 `connect('microflow/editor')` 只取第一个匹配，而它往往在后台：

```
document.hidden === true  → 点击全部静默失效
```

与「节点坏了」的表现完全一样。**排查顺序：先 `Target.getTargets` 数一遍同 URL 的 page，
多于一个就 `Target.closeTarget` 关掉多余的，再动手。** 不要先怀疑选择器。

## ★ 关闭抽屉会让抽屉卡死（平台侧，不是 locator 的问题）

点 `.ant-drawer-close`（含 React onClick 直调）后，抽屉会进入不可恢复状态：

```
宽度保持 1383   body.innerHTML 清空   .ant-drawer-close 的 rect = 0×0
ESC / 点画布空白 / React onClick / 再次点节点   全部无效
```

所以 **「连续开合 10 次」这类验收在关闭这一步必然失败**，且从第 2 轮起全部
报 `DRAWER_LOADING`（标题对、body 空），很容易误判成 locator 坏了。

对策：
- 验收拆成两个独立结论——「打开是否可靠」用**每轮重载页面**来测（`Page.navigate`
  后等 ~22s 再开），「关闭是否可靠」单独如实报告为平台限制。
- 不要用「关闭成功」当循环条件，那会陷入死循环。
- `close_drawer` 只等 body 变空是不够的：关闭动画期间抽屉元素仍在、宽度仍 >200，
  下次 open 会复用空壳。必须等**宽度归零**。

## 设计器规范化取证：判断「形态对不对」的标准做法

要回答「构造器产出的形态平台认不认」，不要靠读代码推断，走这条：

1. 记下修改前的节点 JSON（`udcMicroflowFindByIdGet` 回读，存一份）。
2. 打开该节点的抽屉，用**真实键盘输入**改一个业务字段：
   `focus()` → `Ctrl+A`（`Input.dispatchKeyEvent`，`modifiers=2`）→ `Input.insertText`。
   ★ 原生 setter + `input` 事件**只改 DOM value，不驱动 React state**，
   点「确定」提交的仍是旧值，回读后看不出任何变化——会误判成「设计器保存不改写」。
3. 点「确定」（生效后抽屉进入关闭动画，body 清空、只剩不可见的 close 按钮）。
4. 点「保存并提交」→ 流程变 **DRAFT**。
5. 回读节点 JSON，与第 1 步**逐字段 diff**（键集增/删、每个字段序列化对比）。

判读：
- **无差异** ⇒ 构造器产物就是平台规范形态，问题不在结构，停止改构造器。
- **有差异** ⇒ 按差异项分类（缺字段/错类型/错嵌套/错默认值），再改构造器与能力矩阵。

**不要为了通过单个用例把业务字段写死进构造器。**

## 点卡片没反应：先验证命中，再怀疑节点

`click_mouse` 拿到的坐标可能已经过期——画布有**多层**横向滚动容器（画布 / 分支主卡 / 节点列，实测 `scrollWidth 7517` vs `clientWidth 1383`），遍历式地把所有 `overflow-x` 容器一起改 `scrollLeft`，布局会持续漂移，定位时算出的坐标到点击时早已指向别的卡片。

症状：`elementFromPoint(x,y)` 命中的卡片文字与目标 caption 不符，或 `closest('.udc-microflow-editor-node-container')` 为 null（点到路径连线/空白）。此时抽屉不开、`sideSettingVisible` 保持 false，很容易误判成「节点坏了 / 只读态」。

```python
# 正确顺序：找唯一承载卡片的滚动容器 → 只滚它 → 点前验证命中
def find_target(d, caption):
    # 1) 选出 hasCard=True 的容器里 depth 最小（最外层）那个
    # 2) 用【完整 className】匹配（'.split(" ")[0]' 会撞到别的节点容器）
    # 3) 逐 pos 滚动，每次对候选卡片做 hit 校验：
    #    elementFromPoint(cx,cy) 得到的卡片文字必须包含 caption
    # 4) 命中不符就跳过，不要点
```

遍历收集卡片坐标时**必须把当时的 `scrollLeft` 一并记下，点击前先滚回该值**——画布是横向滚动的（实测 `scrollWidth` 6000+ vs `clientWidth` 1383），收集阶段滚到最后一屏后，前面各屏记下的坐标全部失效，表现为大批卡片打不开抽屉（`NO_DRAWER`），极易误判成「节点坏了 / 只读态」。

另外**视口宽度要够**：节点设置抽屉是 `aside.udc-microflow-editor-node-settings`，从 `x≈1000` 起宽 `680`，`innerWidth` 只有 1088 时整块落在视口外（`aside.getBoundingClientRect().x === innerWidth`），无论怎么点都打不开。开抽屉前先读 `innerWidth`，不足就先把窗口恢复成非最小化（最小化时 `Browser.getWindowBounds` 报 `windowState:minimized`，`innerWidth` 会被压到 1088 这种假宽度）。

## 前端校验是第一道闸门（addNode 默认 nodeConfig，不是空对象）

建节点的正确顺序不是「手写 JSON → checkSchema」，而是先走前端那条链：

1. 点画布「+」→ 前端 dispatch `addNode {currentNodeId, addType, newNodeTemplate}`，控制台打印 `添加节点 => addNode` 与 `回填 nodeConfig {name:'', description:null, input:null, output:null, isCompleted:false}`。**节点自带默认 nodeConfig，不是空对象**——先确认默认值再按业务改，不要凭空构造。
2. 选变量/对象类型 tab → 抽屉随之变形（基本类型出现数据类型下拉；实体对象出现「选择应用 + 选择实体 + 赋值方式 + 字段行」）。
3. 选实体走 `udcMicroflowSearchTreeEntityPost`（body `{appId,appName,needChildren:true,needThirdEntity:false,serviceType:"SELECT_LIST_BY_COMPLEX_CONDITIONS"}`），选中后前端回填含 md5 的 attributes。
4. 点「确认」时**前端立刻跑校验**：必填没填给红框 +「值不能为空 / 请选择 / 请输入」，控制台 `Uncaught (in promise) Error` 指向 `src_redux_store_ts`。这一步过了才算节点对；之后才回读 dataSchema 核对后端存了什么。
5. 后端 `checkSchema` 是最后一道，不是第一道。checkSchema 过 ≠ 节点对——结构合法但字段映射失效、引用丢失，它不报。

`CREATE_VARIABLE.paramType` 七个取值（tab 顺序）：`BASIC` 基本类型 / `ENTITY_OBJECT` 实体对象 / `DEFAULT_OBJECT` 自定义对象 / `ENUM` 选项集 / `METADATA` 元数据 / `MESSAGE` 事件对象 / `OTHER` 其他（`otherType` 另有 `SYSTEM_SORT_OBJECT` 系统排序对象 / `SYSTEM_PAGE_INFO` 系统分页对象）。

**抓默认值/默认行为时不要在正式流程上做实验**：在一条空白测试流程里点「+」逐个添加节点、抓 addNode payload 与前端校验报错，抓完删除。在已发布流程的画布上直接点，很容易误改并留下「创建变量(1)」这类残留节点。

## ★ 节点真实创建机制（前端 addNode，2026-10-27 实测，取代一切凭空拼 JSON）

**铁律：节点不是后端造的，是前端 addNode 造的。任何手拼节点 JSON 都是错的。**

### 1. 添加节点的真实 payload（控制台 `console.log("添加节点 => addNode", t)` 抓取）

```json
{"type":"udc-microflow-edit/addNode",
 "payload":{"currentNodeId":"MFStartNode","addType":"OUTER",
   "newNodeTemplate":{"nodeId":"CREATE_VARIABLE_DI3Lpg","name":"","type":"ACTIVITY",
     "caption":"创建变量(1)","description":null,"runAfter":null,
     "input":null,"output":null,"isCompleted":false,"actionType":"CREATE_VARIABLE"}}}
```

默认 nodeConfig 只有 8 个字段，**`output:null`、`isCompleted:false`**，caption 由前端自动编号。回填日志：`回填 nodeConfig {name:'', description:null, input:null, output:null, isCompleted:false}`。

### 2. 前端默认模板源码（bundle `src_redux_store_ts` @602487 附近）

```js
// 通用节点
d = ({type, actionType, caption, description}) => {
  const o = nanoid(6);
  const r = {nodeId: `${actionType}_${o}`, name:"", type, caption, description,
             runAfter:null, input:null, output:null, isCompleted:false};
  return ["CUSTOM_ERROR"].includes(actionType) ? r : {...r, actionType};
}
// BRANCH：conditions=[ifBranch(expression:{title:"",schema:null},nodes=[]), elseBranch(expression:null,nodes=[])]
// FOR_EACH：{nodeId:`ForEach_xxx`, type:"FOR_EACH", caption:"列表循环", nodes:[], foreach:{sourceItemes:[]}}
// FOR：{nodeId:`For_xxx`, type:"FOR", caption:"计数循环", nodes:[], foreach:{sourceItemes:[]}}
```

### 3. 真实节点清单从 store 读，不要背（25 类，含我之前漏掉的）

```js
appReduxStore.getState().appDesign.microflowEditorReducer.nodeTypeList
```

5 组分类（抽屉「动作场景」实际顺序）：
- 逻辑活动 LOGIC：分支 BRANCH / 列表循环 **FOR_EACH** / 计数循环 FOR / 自定义错误 CUSTOM_ERROR
- 变量活动 VARIABLE：创建变量 CREATE_VARIABLE / 修改变量 CHANGE_VARIABLE
- 映射活动 MAP：创建映射组 CREATE_MAP / 映射操作 MAP_OPERATION
- 列表活动 LIST：创建列表 CREATE_LIST / 修改列表 CHANGE_LIST / 列表操作 LIST_OPERATION
- 数据活动 ENTITY：查询单条 RETRIEVE / 查询多条 RETRIEVE_ARRAY / 插入 CREATE_ENTITY / 批量插入 CREATE_BATCH_ENTITY / 更新 CHANGE_ENTITY / 批量更新 CHANGE_BATCH_ENTITY / 删除 DELETE_ENTITY
- 基础服务 TRANSFER：自定义服务 CALL_APP_SERVICE / 事件投递 PUBLISH_BUSINESS_EVENT / **连接器 CONNECTOR** / 子微流程 SUB_MICROFLOW / 执行生单规则 CALL_DATA_FLOW
- 数据加工 DATA_FACTORY：类型转换 CONVERT_DATA / 数据转换 DATA_MAPPING

关键修正：**FOR_EACH(列表循环) 与 FOR(计数循环) 是两个类型**；**BREAK(跳出循环) 不出现在抽屉里**（`noCompleted:true`，只在循环内部）；**有 CONNECTOR(连接器)**；CUSTOM_ERROR 在部分代码路径下叫 `FRONT_CUSTOM_ERROR`。

### 4. 配置面板的真实字段（以「创建变量」为例，CDP 实测 DOM）

抽屉 `.ant-drawer-body`，标题「创建变量」：
```
变量类型(radio)  基本类型 | 实体对象 | 自定义对象 | 选项集 | 元数据 | 事件对象 | 其他
数据类型(select) 默认「文本」（paramType=BASIC 时才出现）
默认值(input) + 右侧 + 按钮 → 表达式编辑器
节点出参名称(input)
[取消] [确定]  → .compid_node-config-submit-btn
```

**提交时前端抛出的 form values（点确定校不过时的 unhandledrejection）**：
```json
{"values":{"paramType":"BASIC","dataType":"STRING","value":null,"title":"变量_1"},
 "errorFields":[],"outOfDate":true}
```
→ 出参名的表单字段叫 **`title`**（不是 name）；`value=null` 会被拦。

### 5. 选实体对象 tab 后（对应「请输入实体对象」红字）

`paramType=ENTITY_OBJECT` 时抽屉切换为：选择应用 → 选择实体 → 赋值方式（字段映射/对象引用/自动映射）→ 字段行。实体来自 `udcMicroflowSearchTreeEntityPost`。字段行未选报「请选择字段」。

### 6. CDP 操作要点（否则点不动）

- 抽屉是**常驻右侧**的 `ant-drawer-right ant-drawer-inline`（`addNodeConfigDrawer:true`），不是点击弹出。
- 点 `+` 必须用 **CDP `Input.dispatchMouseEvent`**（mouseMoved → mousePressed → mouseReleased，带 `buttons`），JS `.click()` 对画布无效。
- 抽屉内节点名是 `span.add-node-title`，`.click()` 有效。
- 提交按钮 `.compid_node-config-submit-btn`：**不要用 `.click()`**，改调 React `props.onClick`（见 `references/frontend-node-authoring-cdp.md` 的「el.click() 静默失败」节）。
- 表单赋值要用 `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set` + 派发 `input`/`change` 事件，直接改 `.value` React 不认。
- **`valueComponent` 复合控件（「填写错误」「默认值」「该值的映射键」「映射键/映射值」这类）不吃原生 setter**：它的 DOM 是 `input.ant-input` + `lined-plus` 按钮组合，原生 setter 写入后提交仍报「值不能为空」。必须 `input.focus()` + CDP `Input.insertText` 走真实输入路径：
  ```python
d.eval("...fi.querySelector('input.ant-input').focus()...")
d.cmd("Input.insertText", text="要填的值")
  ```
  判据：写完读回 `input.value` 非空还不够，要再看 store 里对应字段是否已变成 `{type:"Simple",simple:"...",desc:"..."}`。
- **提交失败会回滚节点**：点确定后如果校验不过，节点会从 flowFrame 里消失，要从头再来。

## 节点验收：每种可能性都要试，不能只试默认值

用户对「建节点」的验收标准是穷举，不是跑通一条：

> 每个节点先默认、再选择、再确认走校验；看必填、处理必填、处理业务填写、再确认；每步的接口和坑都要记录下来。

具体到必须覆盖的维度：

- **每个 radio 的每个值**都要切一遍（切换后抽屉会变形，必填集和子控件全变）
- **每个 select 的每个选项**都要选一遍（选中后常会多出/隐藏表单行）
- **每个操作都要真做**：查询单条的 `TERMINATION` 与 `CONTINUE` 都要走通（CONTINUE 保存后 `nullPromptMessage` 为 null，不是空串）；过滤条件要试单条件、多条件（AND/OR）、**GROUP 嵌套**、全部 10 个运算符、右值三种形态（常量 / 上下文变量 / 表达式拼接）；排序规则要加一条和多条、升/降序都试、试删除行；查询多条 `CONDITION`/`IDS`/`COUNT`/`OTHERS` 四种全走；删除数据三种删除规则全走；映射操作四种空值处理全走
- **修改变量必须用表达式**，且要覆盖多种修正：纯常量、引用前序出参、`字段A + 字段B`、`textToDecimal(文本)+5`、`substring(文本,0,3) + '拼接串'`。只填常量等于没做业务
- 每步都要点确认让前端走一遍校验，并记录抛出的 `unhandledrejection`（`{values, errorFields, outOfDate}`）
- 全链路接口必须抓（URL + graphql operation + body + status），写操作要回读确认
- **「下拉打不开」不等于「没选项」**：`dropdown timeout` / `no item` 通常说明前置字段没选（级联下拉）或组件被遮挡，必须回头补齐前置再测。把 timeout 记成「已覆盖 0 个选项」就是假覆盖，向用户汇报时会被当场拆穿——统计覆盖度要把这类单独列为「未覆盖」而不是「已完成」。

逐节点执行细节、各节点 radio 枚举、真实表单值与 CDP 坑见 `references/frontend-node-authoring-cdp.md`。

批量穷举探测直接跑 `scripts/probe_nodes.py`（已含清残留抽屉、画布 95% 滚动、控制节点无抽屉回退、类型归一四个坑的修正），不要重写：

```bash
python scripts/probe_nodes.py --only 类型转换,数据转换   # 指定节点
python scripts/probe_nodes.py --submit                  # 额外抓空提交 errorFields
```

输出 `SUMMARY.json`：每个节点的加号坐标 / 面板清单 / 抽屉表单项+required / 全部可点击处（含中心坐标、尺寸、class）。

### 用 DFS 而不是轮询默认值

每个节点从初始状态出发，按 `radio → 子字段 → select → 级联下拉 → 表达式` 的树状展开，**走到叶子就填完整并确认一次**，回读记录后回溯到上层换下一个值。只遍历第一层（只切 radio 不填子字段、只展开 select 不选选项）得到的只是「表单长什么样」，不是契约。

判据：一个节点算「已闭环」的必要条件，是它至少有一个叶子走到了「填完必填 + 填业务 + 点确认成功 + 后端回读拿到真实节点结构」。只拿到表单快照的节点在汇报时必须归入「未闭环」，不能算已完成。

## 保存点了没反应：先查 console，不是查网络

点「保存并提交」后 **零网络请求、零 message 提示**，最容易误判成按钮失效或页面卡死。真实原因是**流程级校验在发请求之前就 return 了**，报错只走两条通道：

1. `console.log("firstErrorNode", e)` —— 校验链 `W(flowNodes, nodeConfig)` 命中必填为空或 `isCompleted===false`
2. `message.error(...)` —— 悬空引用、参数失效等

**这条校验链在 return 之前会逐节点打印 `X 的所有必填属性=> [...]`**——所以一次保存的 console dump 同时是「错误定位」和「权威必填清单」。别只当错误信息扫一眼就丢，那是 26 类节点必填的真值来源（见 `references/required-fields-two-layers.md`）。

**`X 的所有必填属性=> [...]` 列的是「该节点全部必填字段名」，不是「空着的字段」。** 真正的阻塞在单独的 `值为空的必填属性=> <字段> null {node...}` 行。别把前者当空字段清单——看到 `RETRIEVE 的所有必填属性=> [app,structure,title,nullPromptMessage]` 就以为这些是空的，其实它们有值；真正缺的是另一行 `值为空的必填属性=> pageInfo null`。定位空字段只认「值为空」行。

**推论：必填没填满时前端一个请求都不发。** `HTTP 200`、`d.net` 有 `udcMicroflowUpdatePost` 才有意义；没有请求就是前端校验拦截，不是接口问题，也不是「按钮失效」。

典型报文：`节点"修改变量(1)"引用的参数"变量_1"已失效，请重新配置！` —— 某个节点引用的前序出参名对不上（改过 `CREATE_VARIABLE` 出参名后旧引用不自动更新）。**这不是当前节点的问题，是别处遗留的悬空引用阻塞了整条流程的保存。**

做法：保存前注入 console 钩子，保存后 dump。只监听 `Runtime.exceptionThrown` 或只看 `d.net` 会完全看不到。

```js
window.__clog=[];
['log','warn','error'].forEach(k=>{const o=console[k];console[k]=function(){
  try{window.__clog.push({k,a:[...arguments].map(x=>{
    try{return typeof x==='object'?JSON.stringify(x).slice(0,250):String(x)}catch(e){return '?'}})});}catch(e){}
  return o.apply(this,arguments);};});
```

**用 Python 拼这段 JS 时不要塞进三引号字符串**：里面的 `\s`（正则空白符）会被 Python 当转义序列吃掉，`[]` 展开和箭头函数也容易因转义漂移变成 `SyntaxError: Unexpected end of input`，而 `evaluate` 只回一个 `{'__error__': ...}` 字典，不抛异常——于是钩子没装上，后续 dump 全是空，又误判成「保存没报错」。两条解法：用 `r"""..."""` 原始字符串，或把 JS 改写成 `function(){}` 形式且不含正则。装完钩子先 `evaluate('typeof window.__clog')` 验证回来了再继续。

配套判据：`#microflow_save` 点击后 `d.net` 为空 + `__clog` 里有含「失效/必填/失败」的条目 → 定位到那个节点修引用，不要重试保存。

