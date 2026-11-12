# -*- coding: utf-8 -*-
"""UDC 微流程编辑器：节点抽屉操作的 CDP 交互原语

配合一个 CDP driver 使用（需要 d.eval(js) / d.cmd(method, **params) / d.net / d.probe_errors()）。
用法：
    import cdp_probe, cdp_drawer_ops as O
    d = cdp_probe.Driver(); d.attach()
    O.ensure_visible(d)
    O.open_node(d, "查询单条数据")
    O.pick_option(d, "排序规则", "实验数量")
    print(O.read_form(d))
    print(O.submit_drawer(d))

为什么需要这几个函数：
- ensure_visible  页面 hidden 时 antd 浮层宽 0、抽屉按钮不渲染，且会反复变回 true
- pick_option     「点开下拉→选选项」必须一次调完（跨调用会失焦关闭），且要重试
- submit_drawer   antd outOfDate 时序断言会让「点确定」静默失败，需三级兜底
- read_form       直接从 antd form 实例拿真实字段名与结构
"""
import json
import time

DRAWER = ("[...document.querySelectorAll('.ant-drawer')]"
          ".filter(x => x.getBoundingClientRect().width > 200).pop()")


def _js(d, expr):
    """eval 并尽量把 JSON 字符串解回对象。"""
    r = d.eval(expr)
    if isinstance(r, str) and r[:1] in "{[\"":
        try:
            return json.loads(r)
        except Exception:
            return r
    return r


def bring_to_front(d):
    """让 CDP Input 事件能落到页面。每次点击前都要调 —— 长时间批量点击过程中 tab 会重新失焦。

    和 ensure_visible 是两件事，别互相替代：
      ensure_visible  → Emulation.setFocusEmulationEnabled，管「渲染」（浮层宽 0、按钮不渲染）
      bring_to_front  → Page.enable + Page.bringToFront，管「派发」（Input 事件根本不落地）
    判据：点完读 currentSelected.nodeId，没变就是没派发。
    """
    d.cmd("Page.enable")
    d.cmd("Page.bringToFront")
    time.sleep(0.8)


def ensure_visible(d):
    """让 document.hidden 变 false。会反复变回 true，每次点击前都要调。"""
    if d.eval("document.hidden") is True:
        d.cmd("Emulation.setFocusEmulationEnabled", enabled=True)
        time.sleep(0.8)
    return d.eval("document.hidden") is False


def click(d, x, y):
    ensure_visible(d)
    d.cmd("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y, button="none", buttons=0)
    time.sleep(0.3)
    d.cmd("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button="left", buttons=1, clickCount=1)
    time.sleep(0.3)
    d.cmd("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left", buttons=0, clickCount=1)


def react_click(d, finder_js):
    """直接调 React onClick。finder_js 必须返回元素或 null。
    用于坐标不可靠的场景（抽屉 content-wrapper 带 transform 偏移、元素在视口外）。"""
    return d.eval("""(() => {
      const el = %s;
      if (!el) return 'nf';
      const k = Object.keys(el).find(x => x.startsWith('__reactProps$'));
      if (!k) return 'no fiber';
      const p = el[k];
      if (!p || typeof p.onClick !== 'function') return 'no onClick';
      p.onClick({currentTarget: el, target: el, preventDefault(){}, stopPropagation(){},
                 nativeEvent: {}, type: 'click'});
      return 'ok';
    })()""" % finder_js)


def open_node(d, caption_kw):
    """打开画布上某节点配置抽屉（按卡片文本匹配）。.node-body 必须走 React onClick。"""
    r = react_click(d, """(() => {
      const c = [...document.querySelectorAll('.udc-microflow-editor-node-container')]
        .find(x => (x.textContent||'').includes(%s));
      return c ? c.querySelector('.node-body') : null;
    })()""" % json.dumps(caption_kw))
    time.sleep(3)
    return r


def close_drawer(d):
    d.eval("(() => { [...document.querySelectorAll('.ant-drawer-close')].forEach(c => c.click()); return 1; })()")
    time.sleep(2.5)


def drawer_alive(d):
    """抽屉「看着在、其实内容已卸载」的判别：body 高 0 就是残留，只能 reload。"""
    info = _js(d, """JSON.stringify((() => {
      const dr = %s; if (!dr) return null;
      const b = dr.querySelector('.ant-drawer-body');
      return {title: (dr.querySelector('.ant-drawer-title')||{}).textContent,
              bodyH: b ? Math.round(b.getBoundingClientRect().height) : -1,
              scrollH: b ? b.scrollHeight : -1,
              items: dr.querySelectorAll('.ant-form-item').length};
    })())""" % DRAWER)
    return info if info and (info.get("bodyH", 0) > 0 or info.get("items", 0) > 0) else None


def pick_option(d, marker, opt_match=None, idx=-1, tries=3):
    """找到 label（或已选文本）含 marker 的 ant-select → 点开 → 选含 opt_match 的选项（None=第一个）。

    实测三条必须遵守的顺序，少一条就得到假失败：
      1. click 前 ensure_visible —— 否则点不动
      2. click 后**再** ensure_visible —— document.hidden 会在点击过程中翻回 true，
         下拉渲染成 w=0/opacity=0，看起来像「下拉打不开」
      3. 定位优先按 form-item 的 label —— select 自身文本是**已选值**（如实体名），
         不含 label 文字（如「选择实体」），只按 select 文本匹配必然 nf
    """
    for _ in range(tries):
        ensure_visible(d)
        box = _js(d, """JSON.stringify((() => {
          const dr = %s; if (!dr) return null;
          const all = [...dr.querySelectorAll('.ant-select')].filter(s => {
            const fi = s.closest('.ant-form-item');
            const label = fi ? ((fi.querySelector('.ant-form-item-label > label')||{}).textContent||'') : '';
            return label.trim() === %s || (s.textContent||'').indexOf(%s) >= 0;
          });
          if (!all.length) return null;
          const s = (%d < 0) ? all[all.length-1] : (all[%d] || all[all.length-1]);
          s.scrollIntoView({block:'center'});
          const q = s.getBoundingClientRect();
          return {x: Math.round(q.x+q.width/2), y: Math.round(q.y+q.height/2), n: all.length};
        })()""" % (DRAWER, json.dumps(marker), json.dumps(marker), idx, idx))
        if not isinstance(box, dict):
            return "nf(%s)" % box
        click(d, box["x"], box["y"])
        time.sleep(2.0)
        ensure_visible(d)          # ← 关键：点击后补一次，否则下拉宽 0
        time.sleep(1.5)
        r = _js(d, """JSON.stringify((() => {
          const dd = [...document.querySelectorAll('.ant-select-dropdown')]
            .filter(x => x.getBoundingClientRect().width > 0).pop();
          if (!dd) return null;
          const nodes = [...dd.querySelectorAll('.ant-select-item-option-content,.ant-select-tree-title')];
          if (!nodes.length) return null;
          const want = %s;
          const t = want === null ? nodes[0]
                  : nodes.find(n => String(n.textContent||'').indexOf(want) >= 0);
          if (!t) return {miss: true, have: nodes.slice(0,8).map(n=>String(n.textContent||'').trim())};
          const q = t.getBoundingClientRect();
          return {x: Math.round(q.x+q.width/2), y: Math.round(q.y+q.height/2),
                  text: String(t.textContent||'').trim()};
        })())""" % (json.dumps(opt_match) if opt_match else "null"))
        if isinstance(r, dict) and "x" in r:
            click(d, r["x"], r["y"])
            time.sleep(2.2)
            return "ok:" + r["text"][:24]
        d.eval("document.body.click()")
        time.sleep(1.0)
    return "failed"


def read_form(d):
    """把抽屉的 antd form 实例挂到 window.__FORM__，返回全量字段值。
    真实字段名/结构全在这，比看 DOM 靠谱。注意会多一个字面量键 "undefined"。"""
    ok = d.eval("""(() => {
      const dr = %s; if (!dr) return 'no drawer';
      const formEl = dr.querySelector('form');
      if (!formEl) return 'no form';
      const fk = Object.keys(formEl).find(k => k.startsWith('__reactFiber$'));
      let fib = formEl[fk], dep = 0;
      while (fib && dep < 60) {
        const mp = fib.memoizedProps;
        if (mp && mp.form && typeof mp.form.getFieldsValue === 'function') { window.__FORM__ = mp.form; return 'ok'; }
        fib = fib.return; dep++;
      }
      return 'nf';
    })()""" % DRAWER)
    if ok != "ok":
        return {"_error": ok}
    return _js(d, "JSON.stringify(window.__FORM__.getFieldsValue(true))")


def net_ops(d):
    return [(n.get("status"), (n.get("url") or "").rsplit("/", 1)[-1][:32]) for n in (d.net or [])]


def _last_error_fields(d):
    """读上一次提交抛的 unhandledrejection，返回 errorFields 列表。
    用来区分「纯时序断言」与「真业务校验未过」。"""
    errs = d.probe_errors() or []
    for e in errs:
        raw = e.get("msg") if isinstance(e, dict) else None
        if not (isinstance(raw, str) and "errorFields" in raw):
            continue
        try:
            i = raw.find("{")
            obj = json.loads(raw[i:])
        except Exception:
            continue
        if obj.get("errorFields"):
            return obj["errorFields"]
    return []


def submit_drawer(d):
    """三级兜底提交，以「是否发出 udcMicroflowUpdatePost」判成功。
    返回 {via, net, errors, blocked}，via 取 enter / confirm-btn / onFinish / blocked。

    第 3 级必须有闸门：errorFields 非空说明是真业务校验未过，
    此时直调 onSubmit 会把 structure/condition 为 null 的残缺节点静默写进后端（接口仍 200），
    下一轮读回就以为是「下拉点不开」，根本查不出是自己写坏的。
    """
    def sent():
        return any("udcMicroflowUpdatePost" in (n.get("url") or "") for n in (d.net or []))

    # 1) Enter 三连（只在最后一个是 input.ant-input 时有效）
    focused = d.eval("""(() => {
      const dr = %s; if (!dr) return 'no drawer';
      const ins = [...dr.querySelectorAll('input.ant-input, textarea')]
        .filter(i => !i.readOnly && !i.disabled && i.offsetParent);
      if (!ins.length) return 'no input';
      ins[ins.length-1].focus(); return 'ok';
    })()""" % DRAWER)
    if focused == "ok":
        time.sleep(0.4)
        for t in ("keyDown", "char", "keyUp"):
            kw = {"text": "\r"} if t == "char" else {}
            d.cmd("Input.dispatchKeyEvent", type=t, key="Enter", code="Enter",
                  windowsVirtualKeyCode=13, nativeVirtualKeyCode=13, **kw)
            time.sleep(0.12)
        time.sleep(3)
    if sent():
        return {"via": "enter", "net": net_ops(d), "errors": d.probe_errors()}

    # 2) 点「确定」
    react_click(d, """(() => {
      const dr = %s; if (!dr) return null;
      return [...dr.querySelectorAll('button')].find(b => (b.textContent||'').trim() === '确定') || null;
    })()""" % DRAWER)
    time.sleep(3.5)
    if sent():
        return {"via": "confirm-btn", "net": net_ops(d), "errors": d.probe_errors()}

    # 2.5) 闸门：真业务校验未过就别提交
    missing = _last_error_fields(d)
    if missing:
        return {"via": "blocked", "blocked": missing, "net": net_ops(d),
                "errors": d.probe_errors()}

    # 3) 直调 Form.onSubmit(values)：绕过 antd 时序断言，但仍是前端自己的提交链
    d.eval("""(() => {
      const dr = %s; if (!dr) return 'no drawer';
      const formEl = dr.querySelector('form'); if (!formEl) return 'no form';
      const fk = Object.keys(formEl).find(k => k.startsWith('__reactFiber$'));
      let fib = formEl[fk], dep = 0, fn = null, form = null;
      while (fib && dep < 20) {
        const mp = fib.memoizedProps || {};
        if (mp.form && typeof mp.form.getFieldsValue === 'function') form = mp.form;
        if (dep >= 5 && typeof mp.onSubmit === 'function') { fn = mp.onSubmit; break; }
        fib = fib.return; dep++;
      }
      if (!fn || !form) return 'nf';
      window.__SUBMIT_RES__ = 'pending';
      Promise.resolve(fn(form.getFieldsValue(true)))
        .then(() => { window.__SUBMIT_RES__ = 'ok'; })
        .catch(e => { window.__SUBMIT_RES__ = 'err:' + String(e && e.message || e).slice(0,200); });
      return 'called';
    })()""" % DRAWER)
    time.sleep(5)
    return {"via": "onFinish", "res": d.eval("String(window.__SUBMIT_RES__)"),
            "net": net_ops(d), "errors": d.probe_errors()}


def set_input(d, label, text, textarea=False):
    """按 form-item label 给输入框赋值（原生 setter + input/change 事件）。
    textarea=True 时优先用 #nullPromptMessage（RETRIEVE 提示内容）。"""
    tag = "HTMLTextAreaElement" if textarea else "HTMLInputElement"
    sel = "textarea#nullPromptMessage" if textarea else "input.ant-input"
    return d.eval("""(() => {
      const dr = %s; if (!dr) return 'no drawer';
      let el = null;
      if (%s) { el = dr.querySelector(%s); }
      if (!el) {
        const fi = [...dr.querySelectorAll('.ant-form-item')]
          .find(f => ((f.querySelector('label')||{}).textContent||'') === %s);
        if (!fi) return 'nf-item';
        el = fi.querySelector(%s);
      }
      if (!el) return 'nf-el';
      const setter = Object.getOwnPropertyDescriptor(window.%s.prototype, 'value').set;
      setter.call(el, %s);
      el.dispatchEvent(new Event('input', {bubbles: true}));
      el.dispatchEvent(new Event('change', {bubbles: true}));
      return el.value;
    })()""" % (DRAWER, "true" if textarea else "false", json.dumps(sel),
               json.dumps(label), json.dumps(sel), tag, json.dumps(text)))


# 控制节点没有独立「确定」抽屉（BRANCH 条件走内联条件面板，END 只有出参），
# 逐节点点确定时要排除，否则永远是 NO_DRAWER / 假失败。
CONTROL_KEYWORDS = ("分支条件", "符合条件即进入", "不符合条件即进入",
                    "跳出循环", "结束节点", "开始", "开发中")


def collect_cards(d):
    """横向滚动收集全部卡片文本（画布 scrollWidth 6000+，一屏看不完）。"""
    js = r"""(() => {
      const out = [];
      document.querySelectorAll('.udc-microflow-editor-node-container').forEach(el => {
        const t = (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 18);
        if (t) out.push(t);
      });
      return JSON.stringify(out);
    })()"""
    seen, names = set(), []
    for sl in range(0, 7000, 400):
        d.eval("(() => { const e = document.querySelector('.udc-microflow-editor-node.branch.flex1');"
               " if (e) e.scrollLeft = %d; })()" % sl)
        time.sleep(0.4)
        got = _js(d, js) or []
        for t in got:
            if t and t not in seen:
                seen.add(t)
                names.append(t)
    return names


def validate_all_nodes(d, mid):
    """逐节点触发前端校验（用户指定的验收方法）。

    每个节点：bring_to_front → 点卡片 → 点「确定」→ 收 .ant-form-item-explain-error / 红字 label / toast。
    返回三类计数 {ok, errors, skipped}，不要合并成「验证完成」。
      errors[i] = {node, field, red, msg}
      skipped  = 没点开（控制节点 / 视口外 / 抽屉未弹），单列为未覆盖

    前提：调用前已保证 readonly === false（RELEASE 流程必须先点「编辑」）。
    """
    bring_to_front(d)
    ERR_JS = r"""(() => {
      const dd = [...document.querySelectorAll('.ant-drawer')]
        .filter(x => x.className.indexOf('ant-drawer-open') >= 0)[0];
      const field = [], red = [], msg = [];
      if (dd) {
        dd.querySelectorAll('.ant-form-item-explain-error').forEach(x => {
          const t = (x.textContent || '').trim(); if (t) field.push(t); });
        dd.querySelectorAll('.ant-form-item-has-error label').forEach(x => {
          const t = (x.textContent || '').trim(); if (t) red.push(t); });
      }
      document.querySelectorAll('.ant-message-notice').forEach(x => {
        const t = (x.textContent || '').trim(); if (t) msg.push(t); });
      return JSON.stringify({field, red, msg,
        open: [...document.querySelectorAll('.ant-drawer')]
          .filter(x => x.className.indexOf('ant-drawer-open') >= 0).length});
    })()"""

    ok = errors = 0
    skipped, error_list = [], []
    for name in collect_cards(d):
        if any(k in name for k in CONTROL_KEYWORDS):
            skipped.append(name)
            continue
        opened = False
        for attempt in range(4):
            bring_to_front(d)
            loc = _js(d, r"""JSON.stringify((() => {
              const els = document.querySelectorAll('.udc-microflow-editor-node-container');
              for (const el of els) {
                const t = (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 18);
                if (t !== %s) continue;
                el.scrollIntoView({block: 'center', inline: 'center'});
                const q = el.getBoundingClientRect();
                const cx = Math.round(q.x + q.width / 2), cy = Math.round(q.y + q.height / 2);
                const hit = document.elementFromPoint(cx, cy);
                return {cx, cy, ok: hit ? el.contains(hit) : false,
                        inView: cx > 140 && cx < 1560 && cy > 110 && cy < 900};
              }
              return null;
            })())""" % json.dumps(name))
            if not (isinstance(loc, dict) and loc.get("ok") and loc.get("inView")):
                time.sleep(1.2)
                continue
            click(d, loc["cx"], loc["cy"])
            time.sleep(3.2 + attempt * 1.2)
            if _js(d, """(() => {
              const ds = [...document.querySelectorAll('.ant-drawer')]
                .filter(x => x.className.indexOf('ant-drawer-open') >= 0);
              if (!ds.length) return 'none';
              const b = [...ds[ds.length-1].querySelectorAll('button')]
                .find(b => (b.textContent || '').trim() === '确定');
              if (!b) return 'no_ok';
              b.click(); return 'clicked';
            })()""") == "clicked":
                opened = True
                break
        if not opened:
            skipped.append(name)
            continue
        time.sleep(3.0)
        err = _js(d, ERR_JS) or {}
        if err.get("open"):
            close_drawer(d)
        if err.get("field") or err.get("red") or err.get("msg"):
            errors += 1
            error_list.append({"node": name, **err})
        else:
            ok += 1
    return {"ok": ok, "errors": errors, "error_list": error_list, "skipped": skipped}
