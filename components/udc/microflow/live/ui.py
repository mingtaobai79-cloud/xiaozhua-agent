"""mf.ui —— 节点抽屉 / 下拉 / 提交的通用操作。

所有函数都接 Driver（cdp_probe.Driver），不绑定任何具体应用或节点。

设计原则（全部来自实测踩坑）：
  * 每次交互前 ensure_visible —— document.hidden 会反复变回 true，
    一旦为 true 所有 antd 浮层渲染成 width=0，看起来像「下拉打不开」。
  * 抽屉用「宽度 > 200」定位，不要用 .ant-drawer-open（不可靠）。
  * 节点卡片要直调 React onClick，鼠标点击会被连线层挡住。
  * 提交三级兜底：Enter → 确定 → 直接调 Form.onFinish。
  * 表单字段名用 .ant-form-item > .ant-form-item-label > label，
    直接 .ant-form-item label 会把 radio 的 label 也算进来。
"""
import json
import time

DRAWER_JS = ("[...document.querySelectorAll('.ant-drawer')]"
             ".filter(x => x.getBoundingClientRect().width > 200).pop()")


# ------------------------------------------------------------------ 基础

def ensure_visible(d):
    """document.hidden 修复。幂等，每次交互前都可调。"""
    try:
        if d.eval("document.hidden") is True:
            d.cmd("Emulation.setFocusEmulationEnabled", enabled=True)
            time.sleep(0.8)
        return d.eval("document.hidden") is False
    except Exception:
        return False


def click(d, x, y, wait=0.3):
    ensure_visible(d)
    d.cmd("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y, button="none", buttons=0)
    time.sleep(wait)
    d.cmd("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button="left",
          buttons=1, clickCount=1)
    time.sleep(wait)
    d.cmd("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left",
          buttons=0, clickCount=1)


def center(d, js_selector_expr):
    """把元素表达式求值成 {x,y} 中心点（会先 scrollIntoView）。"""
    r = d.eval("""(() => {
      const el = %s;
      if (!el) return 'nf';
      el.scrollIntoView({block: 'center', inline: 'center'});
      const q = el.getBoundingClientRect();
      if (q.width === 0) return 'invisible';
      return JSON.stringify({x: Math.round(q.x + q.width/2),
                             y: Math.round(q.y + q.height/2)});
    })()""" % js_selector_expr)
    if isinstance(r, str) and r.startswith("{"):
        return json.loads(r)
    return None


def click_react(d, js_selector_expr):
    """直调元素的 React onClick —— 鼠标事件常被遮挡层吃掉。"""
    return d.eval("""(() => {
      const el = %s;
      if (!el) return 'nf';
      const k = Object.keys(el).find(x => x.startsWith('__reactProps$'));
      if (!k || !el[k].onClick) return 'no onClick';
      el[k].onClick({currentTarget: el, target: el, preventDefault(){},
                     stopPropagation(){}, nativeEvent: {}, type: 'click'});
      return 'ok';
    })()""" % js_selector_expr)


def set_input(d, js_selector_expr, value):
    """给受控 input/textarea 赋值（必须走原生 setter + 派发事件）。"""
    proto = "HTMLTextAreaElement" if "textarea" in js_selector_expr.lower() else "HTMLInputElement"
    return d.eval("""(() => {
      const el = %s;
      if (!el) return 'nf';
      const s = Object.getOwnPropertyDescriptor(window.%s.prototype, 'value').set;
      s.call(el, %s);
      el.dispatchEvent(new Event('input', {bubbles: true}));
      el.dispatchEvent(new Event('change', {bubbles: true}));
      return el.value;
    })()""" % (js_selector_expr, proto, json.dumps(value)))


def type_text(d, text):
    """往当前焦点插入文本（给表达式编辑器用，能正确触发 token 解析）。"""
    d.cmd("Input.insertText", text=text)
    time.sleep(0.35)


# ------------------------------------------------------------------ 流程状态

STATE_JS = """JSON.stringify((() => {
  const st = appReduxStore.getState().appDesign.microflowEditorReducer;
  const fb = st.flowBasicInfo || {};
  return {readonly: !!st.readonly, state: fb.state, mid: fb.id,
          appId: fb.appId, type: fb.type, triggerType: fb.triggerType,
          caption: fb.caption, name: fb.name,
          frame: (st.flowFrame || []).map(n => n && n.nodeId),
          configChanged: !!st.configChanged, flowChanged: !!st.flowChanged};
})())"""


def state(d):
    r = d.eval(STATE_JS)
    return json.loads(r) if isinstance(r, str) and r.startswith("{") else {}


def ensure_editable(d):
    """保证处于可编辑态。返回 (ok, how)。

    readonly=true 时一切编辑静默失效（接口全 200 但后端零写入）。
    保存并提交会自动把 state 打回 RELEASE，所以每个节点闭环前都要调这个。
    """
    ensure_visible(d)
    st = state(d)
    if not st.get("readonly"):
        return True, "already editable"
    # 点顶栏「编辑」
    for sel in ["[...document.querySelectorAll('.ant-btn')].find(b => (b.textContent||'').trim() === '编辑')",
                "[...document.querySelectorAll('[class*=edit]')].find(b => (b.textContent||'').trim() === '编辑')"]:
        pos = center(d, sel)
        if pos:
            click(d, pos["x"], pos["y"])
            time.sleep(3.5)
            if not state(d).get("readonly"):
                return True, "clicked 编辑"
    # 兜底：重载编辑器
    mid = st.get("mid")
    app = st.get("appId")
    if mid and app:
        d.cmd("Page.navigate", url="%s/main/child-frame/udc/app-design/rule/microflow/editor/%s?appId=%s"
              % ("http://localhost:3000", mid, app))
        time.sleep(8)
        return (not state(d).get("readonly")), "reloaded"
    return False, "failed"


# ------------------------------------------------------------------ 节点

def node_card_js(keyword):
    """按卡片文本关键词定位节点卡片（关键词 = 节点 title 或 caption 残片）。"""
    return ("[...document.querySelectorAll('.udc-microflow-editor-node-container')]"
            ".find(c => (c.textContent || '').indexOf(%s) >= 0)" % json.dumps(keyword))


def close_drawer(d, timeout=8.0):
    """关抽屉并等**抽屉真正消失**（宽度归零），不只是 body 变空。

    ★ 只等 body.innerHTML 为空是不够的：关闭动画期间抽屉元素仍在、宽度仍 >200，
      下次 open 会复用这个空壳，表现为「标题对但 body 长度 0」的假加载态。
      2026-11-01 连续开合验收时 3/10 之后全挂在这上面。
    """
    click_react(d, "[...%s.querySelectorAll('.ant-drawer-close')][0]" % DRAWER_JS)
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(0.5)
        w = d.eval("(() => { const ds = [...document.querySelectorAll('.ant-drawer')]"
                   " .filter(x => x.getBoundingClientRect().width > 200);"
                   " return ds.length ? Math.round(ds[ds.length-1].getBoundingClientRect().width) : 0; })()")
        if not isinstance(w, (int, float)) or w == 0:
            return True
    return False


def _clear_stale_drawer(d):
    """点击前清掉残留的空壳抽屉（宽度>200 但 body 为空）。"""
    w = d.eval("(() => { const ds = [...document.querySelectorAll('.ant-drawer')]"
               " .filter(x => x.getBoundingClientRect().width > 200);"
               " if (!ds.length) return -1;"
               " const b = ds[ds.length-1].querySelector('.ant-drawer-body');"
               " return b ? b.innerHTML.length : 0; })()")
    if isinstance(w, (int, float)) and 0 <= w <= 100:
        close_drawer(d, timeout=10)
        return True
    return False


# ---------------------------------------------------------------- 可见性
# ★★ 不要用 offsetParent 判可见：按 CSSOM，position:fixed 元素的 offsetParent
#    恒为 null。全屏 Modal（.ant-modal-wrap，fixed + z-index 1000）会被整个漏掉，
#    于是「有弹窗遮挡」被误判成「没有弹窗」——2026-11-01 在编辑器上踩实过。
VIS_JS = ("const VIS = el => { if (!el) return false;"
          " const s = getComputedStyle(el), r = el.getBoundingClientRect();"
          " return s.display !== 'none' && s.visibility !== 'hidden'"
          " && r.width > 1 && r.height > 1; };")

# 抽屉状态枚举
OPENED = "OPENED"
NODE_NOT_FOUND = "NODE_NOT_FOUND"
NODE_NOT_SELECTED = "NODE_NOT_SELECTED"
DRAWER_NOT_VISIBLE = "DRAWER_NOT_VISIBLE"
DRAWER_LOADING = "DRAWER_LOADING"
DRAWER_CONTENT_EMPTY = "DRAWER_CONTENT_EMPTY"
DRAWER_IDENTITY_MISMATCH = "DRAWER_IDENTITY_MISMATCH"
TIMEOUT = "TIMEOUT"


def edit_mode_prompt(d):
    """返回「查看模式」确认框是否存在及其按钮（存在=需要先切编辑模式）。

    RELEASE 流程打开编辑器时必定弹出：
        提示 / 您现在处于查看模式，所有的修改都无法被保存 / [进行编辑][继续查看]
    不点「进行编辑」，节点点击一律无效、抽屉永不打开。
    """
    r = d.eval("""(() => {%s
      const ms = [...document.querySelectorAll('.ant-modal-wrap')].filter(VIS);
      for (let i = ms.length - 1; i >= 0; i--) {
        const m = ms[i];
        const t = (m.innerText || '');
        if (t.indexOf('查看模式') >= 0) {
          const b = [...m.querySelectorAll('button')]
            .find(x => (x.textContent || '').indexOf('进行编辑') >= 0);
          return JSON.stringify({prompt: true, hasBtn: !!b});
        }
      }
      return JSON.stringify({prompt: false});
    })()""" % VIS_JS)
    try:
        return json.loads(r) if isinstance(r, str) else {"prompt": False}
    except Exception:
        return {"prompt": False}


def ensure_edit_mode(d, timeout=6.0):
    """若处于「查看模式」，点「进行编辑」切到编辑模式。

    返回 True = 已是编辑模式（无需切换或切换成功）。
    ★ 切换后抽屉会自动打开上次选中的节点，调用方不必再点节点。
    """
    info = edit_mode_prompt(d)
    if not info.get("prompt"):
        return True
    r = d.eval("""(() => {%s
      const ms = [...document.querySelectorAll('.ant-modal-wrap')].filter(VIS);
      for (let i = ms.length - 1; i >= 0; i--) {
        const m = ms[i];
        if ((m.innerText || '').indexOf('查看模式') < 0) continue;
        const b = [...m.querySelectorAll('button')]
          .find(x => (x.textContent || '').indexOf('进行编辑') >= 0);
        if (!b) return 'NO_BTN';
        const k = Object.keys(b).find(x => x.startsWith('__reactProps$'));
        if (k && b[k].onClick) {
          b[k].onClick({currentTarget: b, target: b, preventDefault(){},
                        stopPropagation(){}, nativeEvent: {}, type: 'click'});
          return 'OK';
        }
        b.click(); return 'DOM';
      }
      return 'NO_MODAL';
    })()""" % VIS_JS)
    if r not in ("OK", "DOM"):
        return False
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(0.6)
        if not edit_mode_prompt(d).get("prompt"):
            return True
    return False


def _drawer_snapshot(d):
    """当前最上层抽屉的状态（宽度>200 视为已打开）。"""
    r = d.eval("""(() => {%s
      const ds = [...document.querySelectorAll('.ant-drawer')]
        .filter(x => x.getBoundingClientRect().width > 200);
      if (!ds.length) return JSON.stringify({visible: false});
      const dr = ds[ds.length - 1];
      const body = dr.querySelector('.ant-drawer-body');
      return JSON.stringify({
        visible: true,
        width: Math.round(dr.getBoundingClientRect().width),
        title: ((dr.querySelector('.ant-drawer-title') || {}).textContent || '').trim(),
        bodyLen: body ? body.innerHTML.length : 0,
        bodyText: body ? (body.innerText || '').trim().slice(0, 120) : ''
      });
    })()""" % VIS_JS)
    try:
        return json.loads(r) if isinstance(r, str) else {"visible": False}
    except Exception:
        return {"visible": False}


def open_node_report(d, keyword, expected_title=None, timeout=18.0):
    """打开节点抽屉，返回**结构化诊断结果**（阶段 B 要求）。

    状态：OPENED / NODE_NOT_FOUND / NODE_NOT_SELECTED / DRAWER_NOT_VISIBLE /
          DRAWER_LOADING / DRAWER_CONTENT_EMPTY / DRAWER_IDENTITY_MISMATCH / TIMEOUT
    附带：expected_node_id / selected_node_id / drawer_visible / drawer_title /
          drawer_node_type / locator_count / diagnostic / screenshot_path

    ★ 返回 OPENED 之前一定校验抽屉标题与目标节点一致，空抽屉绝不返回成功。
    """
    rep = {"status": TIMEOUT, "expected_node_id": expected_title,
           "selected_node_id": None, "drawer_visible": False, "drawer_title": None,
           "drawer_node_type": None, "locator_count": 0, "diagnostic": [],
           "screenshot_path": None}

    # ① 查看模式必须先切编辑，否则点击无效
    if not ensure_edit_mode(d):
        rep["diagnostic"].append("未能切到编辑模式（查看模式弹窗未消失）")

    # ①b 清掉残留空壳抽屉（否则点击会复用空壳，表现为 body 长度 0）
    if _clear_stale_drawer(d):
        rep["diagnostic"].append("清掉残留空壳抽屉")

    # ② 定位节点（不依赖 nth-child / 页面顺序）
    loc = d.eval("""(() => {%s
      const kw = %s;
      const all = [...document.querySelectorAll('.udc-microflow-editor-node-container')];
      const hit = all.filter(c => (c.textContent || '').indexOf(kw) >= 0);
      return JSON.stringify({total: all.length, matched: hit.length,
        texts: hit.map(c => (c.textContent || '').trim().slice(0, 40))});
    })()""" % (VIS_JS, json.dumps(keyword)))
    try:
        loc = json.loads(loc) if isinstance(loc, str) else {"matched": 0}
    except Exception:
        loc = {"matched": 0}
    rep["locator_count"] = loc.get("matched", 0)
    if not rep["locator_count"]:
        rep["status"] = NODE_NOT_FOUND
        rep["diagnostic"].append("画布 %d 个节点中无文本含 %r 者" % (loc.get("total", 0), keyword))
        return rep

    # ③ 点节点：**node-body 的 React onClick 才是唯一有效路径**（实测）
    #    card.onMouseDown 能调用但抽屉不动；真实鼠标/more-btn 同样无效。
    #    2026-11-01 重构时误把主路径换成 onMouseDown，导致连续 10 轮全挂。
    #    这里按优先级依次尝试，谁先让抽屉出现就用谁。
    TRIGGERS = [
        ("body_click", """const body = card.querySelector('.node-body') || card;
          const bk = Object.keys(body).find(x => x.startsWith('__reactProps$'));
          if (bk && body[bk].onClick) {
            body[bk].onClick({currentTarget: body, target: body, preventDefault(){},
              stopPropagation(){}, persist(){}, nativeEvent: {}, type: 'click'});
            return 'BODY_CLICK';
          }"""),
        ("card_mousedown", """const k = Object.keys(card).find(x => x.startsWith('__reactProps$'));
          if (k && card[k].onMouseDown) {
            card[k].onMouseDown({currentTarget: card, target: card, button: 0, buttons: 1,
              preventDefault(){}, stopPropagation(){}, persist(){},
              nativeEvent: {button: 0, buttons: 1}, type: 'mousedown'});
            return 'CARD_MOUSEDOWN';
          }"""),
    ]
    for tname, tjs in TRIGGERS:
        clicked = d.eval("""(() => {%s
          const kw = %s;
          const card = [...document.querySelectorAll('.udc-microflow-editor-node-container')]
            .find(c => (c.textContent || '').indexOf(kw) >= 0);
          if (!card) return 'NODE_NOT_FOUND';
          %s
          return 'NO_HANDLER';
        })()""" % (VIS_JS, json.dumps(keyword), tjs))
        rep["diagnostic"].append("trigger[%s]=%s" % (tname, clicked))
        if clicked in ("NODE_NOT_FOUND", "NO_HANDLER"):
            continue
        # 该方式触发后等抽屉；没出来就换下一种
        t0 = time.time()
        got = False
        while time.time() - t0 < min(8.0, timeout):
            time.sleep(0.6)
            snap = _drawer_snapshot(d)
            if snap.get("visible") and snap.get("bodyLen", 0) > 100:
                got = True
                break
        if got:
            break

    # ④ 状态等待（不固定长 sleep）：抽屉出现且内容非空
    t0 = time.time()
    last = {"visible": False}
    while time.time() - t0 < timeout:
        time.sleep(0.6)
        snap = _drawer_snapshot(d)
        last = snap
        if snap.get("visible"):
            rep["drawer_visible"] = True
            rep["drawer_title"] = snap.get("title")
            if snap.get("bodyLen", 0) <= 0:
                rep["status"] = DRAWER_LOADING
                continue
            if snap.get("bodyLen", 0) <= 100:
                rep["status"] = DRAWER_CONTENT_EMPTY
                continue
            # 身份校验：标题或正文必须出现关键词
            hay = "%s %s" % (snap.get("title") or "", snap.get("bodyText") or "")
            want = expected_title or keyword
            if want and want not in hay and keyword not in hay:
                rep["status"] = DRAWER_IDENTITY_MISMATCH
                rep["diagnostic"].append("抽屉内容与目标不符：期望含 %r，实际标题 %r"
                                         % (want, snap.get("title")))
                return rep
            rep["status"] = OPENED
            rep["drawer_node_type"] = snap.get("title")
            return rep

    if last.get("visible"):
        rep["status"] = DRAWER_LOADING if last.get("bodyLen", 0) <= 0 else rep["status"]
    else:
        sel = d.eval("""(() => {%s
          return JSON.stringify([...document.querySelectorAll('.udc-microflow-editor-node-container')]
            .filter(x => /selected|active/i.test(x.className))
            .map(x => (x.textContent || '').trim().slice(0, 30)));
        })()""" % VIS_JS)
        try:
            sels = json.loads(sel) if isinstance(sel, str) else []
        except Exception:
            sels = []
        rep["selected_node_id"] = sels[0] if sels else None
        rep["status"] = NODE_NOT_SELECTED if not sels else DRAWER_NOT_VISIBLE
        rep["diagnostic"].append("选中态=%s，抽屉未出现" % (sels or "无"))
    return rep


def open_node(d, keyword, tries=2):
    """打开节点抽屉（兼容旧返回：成功 'ok' / 失败 'empty drawer'）。

    ★ 内部已改用 open_node_report：先切编辑模式，再按 onMouseDown 选中，
      最后校验抽屉身份。需要诊断信息请直接调 open_node_report。
    """
    for _ in range(max(1, tries)):
        rep = open_node_report(d, keyword)
        if rep.get("status") == OPENED:
            return "ok"
        # 空壳抽屉先关干净再重试
        if rep.get("status") in (DRAWER_LOADING, DRAWER_CONTENT_EMPTY):
            close_drawer(d)
    return "empty drawer"


def drawer(d):
    """当前可见抽屉的元素表达式。"""
    return DRAWER_JS


DRAWER_INFO_JS = """JSON.stringify((() => {
  const dr = %s;
  if (!dr) return null;
  return {title: (dr.querySelector('.ant-drawer-title') || {}).textContent,
          items: [...dr.querySelectorAll('.ant-form-item')].map(f => ({
            lab: ((f.querySelector('.ant-form-item-label > label')
                   || f.querySelector('label') || {}).textContent || '').trim(),
            val: ((f.querySelector('.ant-form-item-control-input-content') || {}).textContent || '')
                   .replace(/\\s+/g, ' ').trim().slice(0, 60)
          })).filter(x => x.lab),
          btns: [...dr.querySelectorAll('button')].map(b => {
            const q = b.getBoundingClientRect();
            return {t: (b.textContent || '').trim(), x: Math.round(q.x + q.width/2),
                    y: Math.round(q.y + q.height/2), w: Math.round(q.width)};
          }).filter(b => b.t && b.w > 0)};
})())""" % DRAWER_JS


def drawer_info(d):
    r = d.eval(DRAWER_INFO_JS)
    return json.loads(r) if isinstance(r, str) and r.startswith("{") else None


def ensure_node_drawer(d, keyword, tries=3):
    """确保节点配置抽屉**打开且有表单内容**，不是空壳。

    实测坑：抽屉可能只剩标题（`title` 正常但 `.ant-form-item` 数为 0、
    store.nodeConfigObj 为空、currentSelected 为空）。只看 drawer_info().title
    会误判"已打开"，后续所有表单操作拿到 null / no item。
    判据必须是 `items` 非空（真实表单项），不是标题。
    """
    for _ in range(tries):
        info = drawer_info(d)
        if info and info.get("items"):
            return True
        open_node(d, keyword)
        time.sleep(1.5)
    return False


def save_and_wait(d, timeout=8.0):
    """触发流程级「保存并提交」并等接口回来。"""
    d.clear_log()
    r = click_react(d, "[...document.querySelectorAll('.ant-btn')]"
                       ".find(b => (b.textContent||'').trim() === '保存并提交')")
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(1.0)
        if any("CheckSchema" in (n.get("url") or "") for n in d.net):
            break
    time.sleep(1.5)
    return {"clicked": r,
            "net": [(n["status"], n["url"].rsplit("/", 1)[-1][:36]) for n in d.net]}


# ------------------------------------------------------------------ 下拉

def _select_by_label_js(label, idx=-1):
    """按 form-item 的 label 定位它下面的 ant-select。

    不能用 select 自身的文本 —— select 显示的是「已选值」（如实体名），
    不是 label（如“选择实体”）。这是最容易踩的定位错误。
    """
    return ("""(() => { const dr = %s; if (!dr) return null;
      const fis = [...dr.querySelectorAll('.ant-form-item')].filter(f => {
        const l = f.querySelector('.ant-form-item-label > label');
        return l && (l.textContent || '').trim() === %s;
      });
      if (!fis.length) return null;
      const fi = fis[%d < 0 ? fis.length - 1 : %d] || fis[0];
      const all = [...fi.querySelectorAll('.ant-select')].filter(s => s.offsetParent);
      return all.length ? all[all.length - 1] : null;
    })()""" % (DRAWER_JS, json.dumps(label), idx, idx))


def scroll_to(d, js_selector_expr, offset=160):
    """把元素滚到「最近可滚动祖先」的视口内，避开固定底栏遮挡。

    实测：节点抽屉的滚动容器是 `.udc-microflow-editor-node-settings`（overflow:auto），
    `scrollIntoView({block:'center'})` 对它无效 —— 元素被 `.node-config-bottom`（absolute）
    盖住时仍然点不到。必须手动算 scrollTop。
    """
    return d.eval("""(() => {
      const el = %s;
      if (!el) return 'nf';
      let p = el.parentElement;
      while (p) {
        const cs = getComputedStyle(p);
        if (/auto|scroll/.test(cs.overflowY) && p.scrollHeight > p.clientHeight + 5) break;
        p = p.parentElement;
      }
      if (!p) return 'no container';
      const er = el.getBoundingClientRect(), pr = p.getBoundingClientRect();
      p.scrollTop += (er.top - pr.top) - %d;
      return 'ok scrollTop=' + Math.round(p.scrollTop);
    })()""" % (js_selector_expr, offset))


def click_el(d, js_selector_expr, verify=True):
    """点元素中心点并校验命中；未命中先滚动重试一次。

    两个实测坑合起来才是完整的：
      * 无条件 scrollIntoView 会把弹窗内部容器滚走，坐标从 y=347 变 y=459
      * 抽屉固定底栏 `.node-config-bottom` 会盖住后面的行，不滚动永远点到底栏
    所以：先试原始坐标 → 没命中 → 手动滚到视口内 → 再试。
    """
    ensure_visible(d)

    def probe():
        return d.eval("""(() => {
          const el = %s;
          if (!el) return null;
          const q = el.getBoundingClientRect();
          if (q.width === 0 || q.height === 0) return null;
          const cx = Math.round(q.x + q.width/2), cy = Math.round(q.y + q.height/2);
          const top = document.elementFromPoint(cx, cy);
          return {x: cx, y: cy, hit: top ? el.contains(top) : false,
                  top: top ? (top.className||'').toString().slice(0,40) : null};
        })()""" % js_selector_expr)

    info = probe()
    if isinstance(info, dict) and info.get("hit"):
        click(d, info["x"], info["y"])
        return True

    scroll_to(d, js_selector_expr)
    time.sleep(1.0)
    info = probe()
    if isinstance(info, dict) and info.get("hit"):
        click(d, info["x"], info["y"])
        return True

    if isinstance(info, dict) and not verify:
        click(d, info["x"], info["y"])
        return True
    return False


def wait_dropdown(d, timeout=9.0, want=1):
    """等 antd 下拉真正可见。

    实测时序（tree-select，弹窗内）：
      t+1s  .ant-select-open=true，dropdown w=0 op=0
      t+3s  dropdown w=305 op=0      ← 宽度出来了，还透明
      t+4s  dropdown w=305 op=1      ← 这时才能点
    hidden 期间动画被推迟，所以必须轮询，不能固定 sleep。
    """
    t0 = time.time()
    while time.time() - t0 < timeout:
        n = d.eval("""(() => {
          const dd = [...document.querySelectorAll('.ant-select-dropdown')]
            .filter(x => x.getBoundingClientRect().width > 0
                      && parseFloat(getComputedStyle(x).opacity) > 0.9).pop();
          if (!dd) return 0;
          return dd.querySelectorAll('.ant-select-item-option-content,.ant-select-tree-title').length;
        })()""")
        if isinstance(n, int) and n >= want:
            return n
        time.sleep(0.5)
    return 0


def open_select(d, label, idx=-1):
    """点开 label 对应的 ant-select，返回选项文本列表（失败 None）。

    实测三条必须遵守：
      1. 定位必须按 form-item label，不能按 select 文本（select 显示的是已选值）
      2. click 前后都要 ensure_visible —— hidden 会让浮层动画停住
      3. 点完必须**轮询等 dropdown 真正可见**，固定 sleep 会在 w=0/op=0 时读到空
    """
    for _ in range(3):
        ensure_visible(d)
        pos = center(d, _select_by_label_js(label, idx))
        if not pos:
            return None
        click(d, pos["x"], pos["y"])
        ensure_visible(d)
        if wait_dropdown(d):
            opts = d.eval("""JSON.stringify((() => {
              const dd = [...document.querySelectorAll('.ant-select-dropdown')]
                .filter(x => x.getBoundingClientRect().width > 0
                          && parseFloat(getComputedStyle(x).opacity) > 0.9).pop();
              if (!dd) return null;
              return [...dd.querySelectorAll('.ant-select-item-option-content,.ant-select-tree-title')]
                .map(n => String(n.textContent || '').trim());
            })())""")
            lst = json.loads(opts) if isinstance(opts, str) and opts.startswith("[") else None
            if lst:
                return lst
        d.eval("document.body.click()")
        time.sleep(1.0)
    return None


def pick_option(d, text, exact=True):
    """在已展开的下拉里点某个选项。"""

    if exact:
        cond = "String(n.textContent||'').trim() === %s" % json.dumps(text)
    else:
        cond = "String(n.textContent||'').indexOf(%s) >= 0" % json.dumps(text)
    for _ in range(2):
        ensure_visible(d)          # 下拉也要在 visible 状态下才有坐标
        time.sleep(0.6)
        pos = center(d, "[...[...document.querySelectorAll('.ant-select-dropdown')]"
                        ".filter(x => x.getBoundingClientRect().width > 0).pop()"
                        ".querySelectorAll('.ant-select-item-option-content,.ant-select-tree-title')]"
                        ".find(n => %s)" % cond)
        if pos:
            click(d, pos["x"], pos["y"])
            time.sleep(2.0)
            return True
    return False


def select_by(d, marker, option, idx=-1):
    """一步到位：开下拉 → 选选项。"""
    lst = open_select(d, marker, idx)
    if not lst:
        return "no dropdown for %r" % marker
    if option not in lst:
        return "no option %r in %s" % (option, lst[:10])
    return "ok" if pick_option(d, option) else "pick failed"


# ------------------------------------------------------------------ 抽屉提交

def confirm_node(d, expect="udcMicroflowUpdatePost", wait=10.0):
    """点节点配置的真实「确定」并等 DRAFT 自动保存。

    前端源码契约：onSubmit 更新 store 后，只有 configChanged=true 才发 UpdatePost。
    调用前若只改了自定义控件，应再通过真实 UI 修改任一普通字段（如出参名）置位。
    判据同时看接口与抽屉关闭，返回后不以后端 store 代替 dataSchema 回读。
    """
    ensure_visible(d)
    btn = "(() => { const dr = %s; return dr ? dr.querySelector('.compid_node-config-submit-btn') : null; })()" % DRAWER_JS
    d.clear_log()
    clicked = click_el(d, btn)
    t0 = time.time()
    while time.time() - t0 < wait:
        d.eval("1")  # 冲刷 CDP 事件，避免 net 延迟假阴性
        if expect in str([n.get("url") for n in d.net]):
            return {"clicked": clicked, "saved": True, "net": _net(d), "errors": d.probe_errors()}
        if not d.eval("(() => !!%s)()" % DRAWER_JS):
            return {"clicked": clicked, "saved": False, "closed": True, "net": _net(d), "errors": d.probe_errors()}
        time.sleep(0.8)
    return {"clicked": clicked, "saved": False, "closed": False, "net": _net(d), "errors": d.probe_errors()}


def submit(d, expect="udcMicroflowUpdatePost", wait=6.0, strategy="auto"):
    """提交节点抽屉（三级兜底）。返回 {via, net, errors, closed}。

    strategy:
      auto      默认，Enter → 确定 → onFinish 逐级兜底。
      onfinish  跳过前两级，直接 Form.onFinish。**含动态行（排序规则/映射行/条件行）
                的抽屉必须用它**：前两级会因 rc-field-form 的 outOfDate 时序断言
                静默失败（点确定后零写入、抽屉 body 被卸载成空壳）。
    """
    def sent():
        return expect in str([n.get("url") for n in d.net])

    def wait_sent_or_closed(timeout=wait):
        """轮询：等 UpdatePost 出现 或 抽屉关闭。

        实测坑：Enter 成功后抽屉立刻关闭，但 d.net 的网络日志有延迟，
        只看 net 会误判失败，然后继续走 B/C 去点已经不存在的按钮 → 返回 FAILED，
        而实际上后端已经写入。必须把「抽屉关闭」也当成成功信号。
        """
        t0 = time.time()
        while time.time() - t0 < timeout:
            time.sleep(0.8)
            if sent():
                return "net"
            if not d.eval("(() => !!%s)()" % DRAWER_JS):
                return "closed"
        return None

    def done(via, how):
        return {"via": via, "how": how, "closed": not d.eval("(() => !!%s)()" % DRAWER_JS),
                "net": _net(d), "errors": d.probe_errors()}

    if strategy != "onfinish":
        # A) Enter —— 走完整 onChange 链
        ok = d.eval("""(() => {
          const dr = %s; if (!dr) return 'no drawer';
          const ins = [...dr.querySelectorAll('input.ant-input, textarea')]
            .filter(i => !i.readOnly && !i.disabled && i.offsetParent);
          if (!ins.length) return 'no input';
          ins[ins.length - 1].focus();
          return 'ok';
        })()""" % DRAWER_JS)
        if ok == "ok":
            time.sleep(0.4)
            for t in ("keyDown", "char", "keyUp"):
                d.cmd("Input.dispatchKeyEvent", type=t, key="Enter", code="Enter",
                      windowsVirtualKeyCode=13, nativeVirtualKeyCode=13,
                      **({"text": "\r"} if t == "char" else {}))
                time.sleep(0.12)
        r = wait_sent_or_closed()
        if r:
            return done("enter", r)

        # B) 点「确定」
        click_react(d, "[...%s.querySelectorAll('button')]"
                       ".find(b => (b.textContent||'').trim() === '确定')" % DRAWER_JS)
        r = wait_sent_or_closed()
        if r:
            return done("confirm", r)

    # C) 直调 Form.onFinish(values) —— 绕过 antd outOfDate 时序断言
    #    **前置闸门**：errorFields 非空时绝不提交。
    #    这个兜底会绕过前端校验，直接调 onFinish 会把「校验没过的半成品」写进后端
    #    （实测把 RETRIEVE 的 structure / condition 写成了 null）。
    fields = d.eval("""(() => {
      const dr = %s; if (!dr) return 'no drawer';
      const formEl = dr.querySelector('form'); if (!formEl) return 'no form';
      const fk = Object.keys(formEl).find(k => k.startsWith('__reactFiber$'));
      let fib = formEl[fk], dep = 0, fi = null;
      while (fib && dep < 40) {
        const mp = fib.memoizedProps || {};
        if (mp.form && typeof mp.form.getFieldValue === 'function') { fi = mp.form; break; }
        fib = fib.return; dep++;
      }
      if (!fi) return 'no form';
      const errs = fi.getFieldsError().filter(e => e.errors.length);
      return JSON.stringify(errs.map(e => ({name: e.name, errors: e.errors})));
    })()""" % DRAWER_JS)
    try:
        err_list = json.loads(fields) if isinstance(fields, str) and fields.startswith("[") else []
    except Exception:
        err_list = []
    if err_list:
        return {"via": "BLOCKED", "reason": "errorFields 非空，拒绝 onFinish 兜底",
                "errorFields": err_list, "net": _net(d), "errors": d.probe_errors()}
    if fields in ("no drawer", "no form"):
        return {"via": "FAILED", "reason": fields, "net": _net(d), "errors": d.probe_errors()}

    d.eval("""(() => {
      const dr = %s; if (!dr) return 'no drawer';
      const formEl = dr.querySelector('form'); if (!formEl) return 'no form';
      const fk = Object.keys(formEl).find(k => k.startsWith('__reactFiber$'));
      let fib = formEl[fk], dep = 0, fn = null, fi = null;
      while (fib && dep < 20) {
        const mp = fib.memoizedProps || {};
        if (mp.form && typeof mp.form.getFieldsValue === 'function') fi = mp.form;
        if (dep >= 5 && typeof mp.onSubmit === 'function') { fn = mp.onSubmit; break; }
        fib = fib.return; dep++;
      }
      if (!fn || !fi) return 'nf';
      window.__SUBMIT__ = 'pending';
      Promise.resolve(fn(fi.getFieldsValue(true)))
        .then(() => { window.__SUBMIT__ = 'ok'; })
        .catch(e => { window.__SUBMIT__ = 'err:' + String(e && e.message || e).slice(0, 160); });
      return 'called';
    })()""" % DRAWER_JS)
    time.sleep(5)
    closed = d.eval("%s ? 0 : 1" % DRAWER_JS)
    return {"via": "onFinish", "res": d.eval("String(window.__SUBMIT__)"),
            "closed": closed == 1, "net": _net(d), "errors": d.probe_errors()}


def _net(d):
    return [(n["status"], n["url"].rsplit("/", 1)[-1][:36]) for n in d.net]


def form_values(d):
    """取抽屉 antd Form 的完整 values（含不渲染的隐藏字段）。"""
    r = d.eval(_FORM_VALUES_JS)
    return json.loads(r) if isinstance(r, str) and r.startswith("{") else None


_FORM_VALUES_JS = """JSON.stringify((() => {
  const dr = %s; if (!dr) return null;
  const formEl = dr.querySelector('form'); if (!formEl) return null;
  const fk = Object.keys(formEl).find(k => k.startsWith('__reactFiber$'));
  let fib = formEl[fk], dep = 0;
  while (fib && dep < 40) {
    const mp = fib.memoizedProps || {};
    if (mp.form && typeof mp.form.getFieldsValue === 'function') return mp.form.getFieldsValue(true);
    fib = fib.return; dep++;
  }
  return null;
})())""" % DRAWER_JS


def set_form_field(d, field, value):
    """直接改 antd Form 的字段值（用于嵌套结构，如 sortParams / condition）。"""
    return d.eval("""(() => {
      const dr = %s; if (!dr) return 'no drawer';
      const formEl = dr.querySelector('form'); if (!formEl) return 'no form';
      const fk = Object.keys(formEl).find(k => k.startsWith('__reactFiber$'));
      let fib = formEl[fk], dep = 0;
      while (fib && dep < 40) {
        const mp = fib.memoizedProps || {};
        if (mp.form && typeof mp.form.setFieldsValue === 'function') {
          mp.form.setFieldsValue({%s: %s});
          return 'ok';
        }
        fib = fib.return; dep++;
      }
      return 'nf';
    })()""" % (DRAWER_JS, json.dumps(field), json.dumps(value, ensure_ascii=False)))
