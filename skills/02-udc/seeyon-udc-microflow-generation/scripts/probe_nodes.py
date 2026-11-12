#!/usr/bin/env python
"""批量节点取证探针：对 UDC 微流程右侧面板里每个节点走完整链。

每个节点记录：
  step0_clean       清残留抽屉（不清会遮住加号，后续全部误判「不在面板」）
  step1_init        加号坐标 + 右侧面板完整项清单 + 控制台 + 网络
  step2_pick        抽屉标题 / 表单项+required / 可点击处（无抽屉时记画布结构）
  step3_required    空提交后的 antd errorFields
  step4_clickables  全部可点击处（类型/文本/中心坐标/尺寸/class）

用法：
  python probe_nodes.py                    # 跑全部
  python probe_nodes.py --only 类型转换,数据转换
  python probe_nodes.py --from 5           # 从第 6 个开始
  python probe_nodes.py --submit           # 额外做空提交抓 errorFields

依赖：components.udc.microflow.live 的 cdp / ui（需 websockets 解释器）。
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.udc.microflow.live import cdp, ui  # noqa: E402

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'node-evidence')

# 右侧面板 24 项（实测顺序）
PANEL = [
    '分支', '列表循环', '计数循环', '自定义错误', '创建变量', '修改变量',
    '创建映射组', '映射操作', '创建列表', '修改列表', '列表操作',
    '查询单条数据', '查询多条数据', '插入数据', '批量插入数据',
    '更新数据', '批量更新数据', '删除数据', '自定义服务', '事件投递',
    '子微流程', '执行生单规则', '类型转换', '数据转换',
]

CONSOLE_HOOK = r"""
(() => {
  if (window.__clog_installed) return 'already';
  window.__clog = [];
  ['log','warn','error','info','debug'].forEach(k => {
    const o = console[k];
    console[k] = function() {
      try {
        window.__clog.push({k: k, t: Date.now(),
          a: [...arguments].map(x => {
            try { return typeof x === 'object' ? JSON.stringify(x).slice(0,400)
                                                : String(x).slice(0,400); }
            catch (e) { return '?'; }
          })});
        if (window.__clog.length > 800) window.__clog.shift();
      } catch (e) {}
      return o.apply(this, arguments);
    };
  });
  window.__clog_installed = true;
  return 'installed';
})()
"""

# 抽屉内全部可点击处
CLICKABLE_JS = r"""
(() => {
  const d = document.querySelector('.ant-drawer-open');
  if (!d) return JSON.stringify({open: false});
  const body = d.querySelector('.ant-drawer-body') || d;
  const vis = el => {
    const q = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    return q.width > 2 && q.height > 2 && st.display !== 'none'
           && st.visibility !== 'hidden' && st.opacity !== '0';
  };
  const out = []; const seen = new Set();
  const push = (kind, el, extra) => {
    if (!el || !vis(el)) return;
    const q = el.getBoundingClientRect();
    const txt = (el.textContent || '').replace(/\s+/g,' ').trim().slice(0,60);
    const cx = Math.round(q.x + q.width/2), cy = Math.round(q.y + q.height/2);
    const key = kind + '|' + cx + ',' + cy + '|' + txt;
    if (seen.has(key)) return;
    seen.add(key);
    out.push(Object.assign({kind: kind, text: txt,
      cls: (el.className||'').toString().slice(0,70), tag: el.tagName,
      disabled: !!el.disabled, x: Math.round(q.x), y: Math.round(q.y),
      w: Math.round(q.width), h: Math.round(q.height), cx: cx, cy: cy}, extra || {}));
  };
  body.querySelectorAll('button').forEach(e => push('button', e));
  body.querySelectorAll('.ant-select').forEach(e => push('select', e));
  body.querySelectorAll('.ant-radio-wrapper, .ant-radio-button-wrapper')
    .forEach(e => push('radio', e));
  body.querySelectorAll('.ant-checkbox-wrapper').forEach(e => push('checkbox', e));
  body.querySelectorAll('input').forEach(e =>
    push('input', e, {ph: e.placeholder || '', val: (e.value||'').slice(0,40)}));
  body.querySelectorAll('textarea').forEach(e =>
    push('textarea', e, {val: (e.value||'').slice(0,40)}));
  body.querySelectorAll('.ant-switch').forEach(e => push('switch', e));
  body.querySelectorAll('.anticon-plus, .anticon-minus, .anticon-delete, .anticon-close')
    .forEach(e => push('icon', e));
  body.querySelectorAll('[class*=selector], [class*=Selector]').forEach(e => {
    if (e.children.length < 6) push('selector', e);
  });
  body.querySelectorAll('.ant-collapse-header, .ant-tabs-tab')
    .forEach(e => push('tab', e));
  return JSON.stringify({open: true, count: out.length, items: out});
})()
"""

# 表单项 + required 标记 + 错误文本
REQUIRED_JS = r"""
(() => {
  const d = document.querySelector('.ant-drawer-open');
  if (!d) return JSON.stringify({open: false});
  const body = d.querySelector('.ant-drawer-body') || d;
  return JSON.stringify([...body.querySelectorAll('.ant-form-item')].map(fi => {
    const lbl = fi.querySelector('label');
    const ctrl = fi.querySelector('.ant-form-item-control');
    const err = ctrl && ctrl.querySelector('.ant-form-item-explain-error');
    return {
      label: (lbl ? lbl.textContent : '').replace(/\s+/g,' ').trim().slice(0,40),
      required: fi.classList.contains('ant-form-item-required')
        || !!(lbl && lbl.classList.contains('ant-form-item-required')),
      errorText: err ? err.textContent.trim().slice(0,80) : null,
      id: (fi.querySelector('[id]') || {}).id || null,
      cls: (fi.className||'').toString().slice(0,70)
    };
  }).filter(x => x.label || x.id));
})()
"""

# 控制节点无抽屉时：记画布结构
CANVAS_JS = r"""
(() => {
  const out = {branches: [], cards: []};
  document.querySelectorAll('.branches').forEach((b, i) => {
    const q = b.getBoundingClientRect();
    out.branches.push({i: i, cls: (b.className||'').toString().slice(0,70),
      x: Math.round(q.x), y: Math.round(q.y),
      w: Math.round(q.width), h: Math.round(q.height),
      text: (b.textContent||'').replace(/\s+/g,' ').trim().slice(0,100)});
  });
  document.querySelectorAll('[class*=node-card], .udc-microflow-editor-node-container')
    .forEach((c, i) => {
      const q = c.getBoundingClientRect();
      if (q.width < 20) return;
      out.cards.push({i: i, cls: (c.className||'').toString().slice(0,60),
        x: Math.round(q.x), y: Math.round(q.y),
        w: Math.round(q.width), h: Math.round(q.height),
        text: (c.textContent||'').replace(/\s+/g,' ').trim().slice(0,80)});
    });
  return JSON.stringify(out);
})()
"""


def js(d, expr):
    r = d.eval(expr)
    try:
        return json.loads(r) if isinstance(r, str) else r
    except Exception:
        return r


def as_list(v):
    """无抽屉时 REQUIRED_JS 返回 {'open': False}，必须归一成 list。"""
    return v if isinstance(v, list) else []


def as_dict(v):
    return v if isinstance(v, dict) else {}


def unlock_view_mode(d):
    """查看模式弹窗可叠多层，必须循环点掉。"""
    for _ in range(8):
        if not d.eval("(()=>document.querySelectorAll('.ant-modal-wrap').length)()"):
            return True
        d.eval("""(()=>{const ws=[...document.querySelectorAll('.ant-modal-wrap')]
          .filter(w=>w.getBoundingClientRect().width>0); if(!ws.length)return;
          const b=[...ws[ws.length-1].querySelectorAll('button')]
            .find(b=>(b.textContent||'').trim()==='进行编辑'); if(b)b.click();})()""")
        time.sleep(2.6)
    return False


def close_all_drawers(d):
    """批量探测必做：不关会遮住加号，后续全部误判「不在面板」。"""
    for _ in range(6):
        if not d.eval("(()=>document.querySelectorAll('.ant-drawer-open').length)()"):
            return True
        r = d.eval("""(()=>{const ds=[...document.querySelectorAll('.ant-drawer-open')];
          if(!ds.length) return 'none';
          const dd=ds[ds.length-1];
          const b=[...dd.querySelectorAll('button')]
            .find(b=>(b.textContent||'').trim()==='取消');
          if(b){b.click();return 'cancel';}
          const c=dd.querySelector('.ant-drawer-close');
          if(c){c.click();return 'close';}
          const m=document.querySelector('.ant-drawer-mask');
          if(m){m.click();return 'mask';}
          return 'stuck';})()""")
        time.sleep(1.5)
        if r == 'stuck':
            d.cmd("Input.dispatchKeyEvent", type="keyDown", key="Escape",
                  windowsVirtualKeyCode=27, nativeVirtualKeyCode=27)
            d.cmd("Input.dispatchKeyEvent", type="keyUp", key="Escape",
                  windowsVirtualKeyCode=27, nativeVirtualKeyCode=27)
            time.sleep(1.5)
    return d.eval("(()=>document.querySelectorAll('.ant-drawer-open').length)()") == 0


def reset_canvas(d):
    """滚到最右。用 95% 避免超出可滚范围（直接设 scrollWidth 会滚过头）。"""
    d.eval("""(()=>{const el=document.querySelector(
      '.udc-microflow-editor-node.branch.flex1');
      if(!el) return 'no canvas';
      el.scrollLeft = Math.floor(el.scrollWidth * 0.95);})()""")
    time.sleep(2.4)


def open_add_panel(d):
    reset_canvas(d)
    plus = as_list(js(d, """JSON.stringify([...document.querySelectorAll('.anticon.add-button')]
      .map(el=>{const q=el.getBoundingClientRect();
        return {x:Math.round(q.x+q.width/2),y:Math.round(q.y+q.height/2)};})
      .filter(b=>b.x>150&&b.x<1680&&b.y>250&&b.y<560))"""))
    if not plus:
        return None, []
    b = plus[-1]
    d.click_mouse(b['x'], b['y'])
    time.sleep(2.8)
    items = as_list(js(d, """JSON.stringify([...document.querySelectorAll(
      '.ant-drawer-body span.add-node-title')].map(e=>(e.textContent||'').trim()))"""))
    return b, items


def probe_one(name, do_submit=False):
    d = cdp.Driver()
    d.attach()
    ev = {'node': name, 'ts': time.strftime('%Y-%m-%dT%H:%M:%S')}
    try:
        ui.ensure_visible(d)
        d.eval(CONSOLE_HOOK)
        ev['page_url'] = d.eval('location.href')[:150]
        ev['unlock'] = unlock_view_mode(d)
        ev['step0_clean'] = close_all_drawers(d)

        d.eval("(()=>{window.__clog=[];return 1})()")
        net0 = len(d.net)
        plus, panel = open_add_panel(d)
        ev['step1_init'] = {'plus_btn': plus, 'panel_count': len(panel),
                            'panel_items': panel,
                            'console': as_list(js(d, "JSON.stringify((window.__clog||[]).slice(-30))"))}
        if name not in panel:
            ev['error'] = 'PANEL_MISSING: %r 不在面板中' % name
            return ev

        d.eval("(()=>{window.__clog=[];return 1})()")
        net1 = len(d.net)
        d.pick_node_type(name)
        time.sleep(4.5)

        drawer = as_dict(js(d, """(()=>{const dd=document.querySelector('.ant-drawer-open');
          if(!dd)return JSON.stringify({open:false});
          return JSON.stringify({open:true,
            title:((dd.querySelector('.ant-drawer-title')||{}).textContent||'').trim()});})()"""))
        ev['step2_pick'] = {'drawer': drawer,
                            'form_items': as_list(js(d, REQUIRED_JS)),
                            'clickables': as_dict(js(d, CLICKABLE_JS))}
        if not drawer.get('open'):
            ev['step2_pick']['canvas_after_add'] = as_dict(js(d, CANVAS_JS))
            ev['step2_pick']['note'] = '控制节点：无配置抽屉，直接落到画布'

        if do_submit:
            d.eval("(()=>{window.__clog=[];return 1})()")
            ui.submit(d, wait=6.0)
            time.sleep(1.5)
            ev['step3_required'] = {
                'form_items': as_list(js(d, REQUIRED_JS)),
                'errors': js(d, "JSON.stringify((((window.__probe||{}).errors)||[]).slice(-5))"),
                'console': as_list(js(d, "JSON.stringify((window.__clog||[]).slice(-50))"))}

        ev['step4_clickables'] = as_dict(js(d, CLICKABLE_JS))
        return ev
    finally:
        try:
            d.close()
        except Exception:
            pass


def main():
    args = sys.argv[1:]
    targets = PANEL
    if '--only' in args:
        targets = args[args.index('--only') + 1].split(',')
    elif '--from' in args:
        targets = PANEL[int(args[args.index('--from') + 1]):]
    do_submit = '--submit' in args

    os.makedirs(OUT_DIR, exist_ok=True)
    summary_path = os.path.join(OUT_DIR, 'SUMMARY.json')
    summary = {'nodes': {}}

    ok, fail = 0, []
    for i, name in enumerate(targets, 1):
        print('[%d/%d] %s ...' % (i, len(targets), name), flush=True)
        try:
            ev = probe_one(name, do_submit)
            summary['nodes'][name] = ev
            if 'error' in ev:
                fail.append((name, ev['error']))
                print('  FAIL: %s' % ev['error'])
            else:
                dr = as_dict(as_dict(ev.get('step2_pick')).get('drawer'))
                fis = as_list(as_dict(ev.get('step2_pick')).get('form_items'))
                cl = as_dict(ev.get('step4_clickables'))
                req = sum(1 for x in fis if isinstance(x, dict) and x.get('required'))
                print('  OK  drawer=%r 表单项=%d 必填=%d 可点击=%d'
                      % (dr.get('title'), len(fis), req, cl.get('count', 0)))
                ok += 1
        except Exception as e:
            fail.append((name, '%s: %s' % (type(e).__name__, e)))
            print('  EXC: %s' % e)
        summary['updated'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=1)
        time.sleep(1.5)

    print('\n=== 汇总 ===\n成功 %d / %d' % (ok, len(targets)))
    for n, e in fail:
        print('  %-10s %s' % (n, str(e)[:120]))
    print('证据: %s' % summary_path)
    sys.exit(0 if not fail else 1)


if __name__ == '__main__':
    main()
