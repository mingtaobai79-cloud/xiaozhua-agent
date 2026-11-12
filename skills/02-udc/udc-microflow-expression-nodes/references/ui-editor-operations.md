# 微流程编辑器 UI 操作配方（视口 / 定位 / 抽屉 / 保存链路）

用途：当用户要求「一个一个点」「填完点确定看后台校验」时，走 UI 而不是直写 dataSchema。
本文件只管**怎么把 UI 点对**；表达式怎么拼见 `expression-editor-ui-driving.md`，
批量直写见 `expression-bulk-fill.md`。

## 1. 开工前三个检查（任一不对，后面全白做）

```python
inner = json.loads(d.eval("JSON.stringify({w:innerWidth,h:innerHeight})"))
win = d.cmd('Browser.getWindowForTarget')
```

**a. 视口宽度 ≥ 1680 才能开抽屉。**
抽屉宽 680px，画布 `MAIN` 有自己的宽度。视口 1088 时 `aside.getBoundingClientRect().x`
等于 1088（刚好在右边界外），`document.elementFromPoint(cx, cy)` 返回 `null`，
所有点击静默失败。表现是 `ant-drawer-open` 计数为 0、或计数为 1 但字段数读不到。

**b. `windowState` 与 `innerWidth` 要一起看。**
窗口 normal 但 innerWidth 仍小 = 窗口尺寸问题，用
`Browser.setWindowBounds(windowId, {'windowState':'normal'})` 再设 `{left,top,width,height}`，
重读 `innerWidth`。**不要**用改 CSS `transform` / `Emulation.setPageScaleFactor` 硬拉——
实测两者都不改变 `innerWidth`。

**c. `readonly=false` 且无残留抽屉。**

```python
try:
    d.cmd("Emulation.setFocusEmulationEnabled", enabled=True)
except Exception:
    pass
```

## 2. 定位节点卡片：必须真的落在视口内

节点卡片在可横向滚动的画布容器里，大部分时候都不在视口内（x 可为负，也可远大于视口宽）。

```python
def in_view(c, vp):
    return 0 < c['cx'] < vp['w'] and 0 < c['cy'] < vp['h']

def locate(d, caption, step=240, max_scroll=30000):
    vp = json.loads(d.eval("JSON.stringify({w:innerWidth,h:innerHeight})"))
    for sl in range(0, max_scroll, step):
        d.eval("""(()=>{document.querySelectorAll('*').forEach(e=>{
          const s=getComputedStyle(e);
          if((s.overflowX==='auto'||s.overflowX==='scroll') && e.scrollWidth>e.clientWidth+50){
            e.scrollLeft=%d;}});})()""" % sl)
        time.sleep(0.3)
        for c in cards(d):                     # .udc-microflow-editor-node-container
            if caption in c['t'] and in_view(c, vp) and c['w'] > 20:
                return c
    return None
```

**CDP `Input.dispatchMouseEvent` 用 CSS 像素**，DPR=1.5 时也不要乘系数。
坐标超出 `innerWidth` 就等于点在视口外，不会有任何报错。

### 定位后必须验证命中，不能直接点

`locate()` 返回坐标后到真正点击之间，布局可能已变（另一个滚动容器动了、页面重排），
这时点下去会静默落在别的节点上——store 不变、抽屉不开，看起来像「点击方式不对」。
真实症状：`locate` 报告 `创建变量(1)` 在 (658,440)，但 `elementFromPoint(658,440)`
命中的是另一个节点（`更新后的ID集合`）。

所以点击前先自检，命中的卡片文字必须包含目标 caption：

```python
def hit_card(d, x, y):
    return js(d, """(()=>{const e=document.elementFromPoint(%d,%d);
      if(!e) return null;
      const c=e.closest('.udc-microflow-editor-node-container');
      return c ? (c.textContent||'').replace(/\s+/g,' ').trim().slice(0,60) : null})()""" % (x, y))

if not hit_card(d, c['cx'], c['cy']) or caption not in hit_card(d, c['cx'], c['cy']):
    continue          # 换下一个滚动位置，别硬点
```

点击后**必须验证结果**：`ant-drawer-open` 计数为 0 就是没开，当作失败重试（先在卡片内
换几个纵向偏移 `dy = -18 / +14 / +26` 再试），不要当成「已经开过了」。

### 一次只有一个进程驱动该页面

抽屉打不开的第二种原因是**别的脚本也在操作同一个 CDP target**（遗留的抓包/巡检脚本、
后台没退的自动化）。症状和布局问题很像：卡片能定位、`elementFromPoint` 命中正确，
但抽屉开了又关、前后两次 dump 字段数不一样（4 个 vs 9 个）。
遇到「同样代码时好时坏」先查有没有并发驱动者，再怀疑点击方式。

## 3. 抽屉结构

打开后读：

```javascript
const a = document.querySelector('aside.udc-microflow-editor-node-settings');
const items = [...a.querySelectorAll('.ant-form-item')].filter(fi => {
  const q = fi.getBoundingClientRect();
  return q.width > 0 && q.height > 0;      // 滤掉未渲染的
});
```

- 必填标记是 **`fi.className.includes('required-item')`**，不是 antd 的
  `.ant-form-item-required`（后者取不到）。
- 错误文案在 `.ant-form-item-explain-error`。
- **读当前值要分控件**，否则会把选项列表误读成值：
  - 下拉：`.ant-select-selection-item` 的 textContent（不是 `.ant-select` 的全文）
  - 输入：`input:not([type=hidden])` 的 value
  - 无 `.ant-select-selection-item` 而有占位符 = 真空
- 底部按钮 `确定` / `取消` 在 `.ant-drawer-open` 里，用 `__reactProps$.onClick` 直调
  （`el.click()` 对 React 按钮静默失败）。

### 怎么判定某个字段有没有表达式入口

不要按「有输入框就能填表达式」假设。表达式入口是独立按钮，DOM 判据：

```javascript
const btns = [...fi.querySelectorAll('button')];
const hasExpr = !!fi.querySelector('.expressionIcon, .conditionIcon')
  || btns.some(b => /LinedFunction|lined-function/.test(
       ((b.querySelector('[class*=sy-icon]')||{}).className || '')));
```

`expressionIcon` 是「表达式」下拉，`conditionIcon` 是「条件表达式」按钮。
页面设计器另有一套 `supportExpression()`（`designer.expression` feature flag）控全局开关，
和微流程节点抽屉**不是同一套机制**，别把页面设计器的结论套到微流程节点上。

枚举时同时记录 `required`、`val`、`hasExpr` 三列，才能区分「字段必填但空」和
「字段有表达式入口但没填」——这两类修法完全不同。

## 4. 保存链路：只有「暂存草稿」会发请求

实测（`CONVERT_DATA` 节点，干净 DRAFT 态）：

| 动作 | 网络请求 | 结果 |
|---|---|---|
| 抽屉点「确定」 | **0 个** | 只写 store，`flowChanged` 仍 true |
| 点「暂存草稿」 | `udcMicroflowUpdatePost` | `BOOT_0000` / `content:1`，`flowChanged` → false |

点「暂存草稿」后还会连发 `udcMicroflowSearch` / `udcMicroflowFindByIdGet` / 组查询，
这属于保存后的刷新，不是额外校验。

**判定标准只有一条：有没有抓到 `udcMicroflowUpdatePost`。**
没抓到就是没落库，不要按节点类型去推断。

抓包钩子（页面内覆写 `fetch`，保留 req/resp）：

```javascript
window.__net = [];
const orig = window.fetch;
window.fetch = async function(...args) {
  let url='', req=null;
  try { url = (typeof args[0]==='string') ? args[0] : args[0].url;
        if (args[1] && typeof args[1].body==='string') req = args[1].body; } catch(e){}
  const rec = {url, req};
  try {
    const r = await orig.apply(this, args);
    rec.status = r.status;
    try { rec.resp = (await r.clone().text()).slice(0, 4000); } catch(e){}
    window.__net.push(rec); return r;
  } catch(e) { rec.err = String(e); window.__net.push(rec); throw e; }
};
```

注意：钩子装在**页面**上，`location.reload()` 后会丢，刷新后要重装。

## 5. 重载编辑器

```python
d.eval('location.href=%s' % json.dumps(EDITOR_URL))
time.sleep(16)
# 等 flowNodes 就位，而不是靠固定 sleep
for _ in range(20):
    n = js(d, """(()=>{try{return Object.keys(appReduxStore.getState()
      .appDesign.microflowEditorReducer.flowNodes||{}).length}catch(e){return -1}})()""")
    if isinstance(n, int) and n > 5: break
    time.sleep(2)
```

frame 重载后旧 CDP 会话可能失效，`d.reconnect(wait=4.0)` 兜一下。

## 6. 面板显示为空 ≠ 数据没存

节点值字段被写成 `Expression` 对象后，抽屉里的控件**不会回显**，显示为空。
这时要区分：

- `read_schema_page` 回读：字段是 `{type:"Expression", ...}` ⇒ 数据在，是回显问题
- 回读也是空 / `type:"Simple", simple:""` ⇒ 真没存

回显问题只能靠「改回 UI 原生可编辑形态」解决，不是重跑保存。
