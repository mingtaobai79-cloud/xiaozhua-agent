"""React 受控组件的可靠交互原语（CDP 驱动）。

## 为什么需要这个模块

实测发现三类「看起来点了但没生效」的陷阱，都源于 React 合成事件机制：

1. **`el.click()` 触发不了 React onClick**
   DOM 原生 click 会冒泡到 React 根监听器，但 antd Button 的 onClick
   挂在 fiber 的 memoizedProps 上，`el.click()` 对某些场景不触发。
   实测：抽屉「确定」按钮 `el.click()` → attrs 不落库；改调
   `props.onClick()` → 立即生效（attrCount 0 → 3）。

2. **受控 input 直接赋值不更新 React state**
   必须用 `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set`
   绕过 React 的 value tracker，再派发 input/change 事件。

3. **antd Select 必须派发 mousedown+mouseup+click 序列**
   单独 click 打不开下拉。

## 用法

    from components.udc.microflow.live.react_click import (
        react_click, set_controlled_input, open_antd_select,
    )
"""
from __future__ import annotations

import json

# 在 React fiber 上找 onClick 并调用（props 优先，回退 fiber 树向上）
_REACT_CLICK_JS = r"""
(() => {
  const target = %(text)s;
  const root = %(root)s;
  const scope = root ? document.querySelector(root) : document;
  if (!scope) return JSON.stringify({err: 'no scope:' + String(root)});
  const btns = [...scope.querySelectorAll('button')].filter(b => {
    const t = (b.textContent || '').replace(/\s+/g, ' ').trim();
    if (t !== target) return false;
    const r = b.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  });
  if (!btns.length) return JSON.stringify({err: 'no btn:' + target});
  const b = btns[btns.length - 1];
  const pk = Object.keys(b).find(k => k.startsWith('__reactProps$'));
  if (pk && typeof b[pk].onClick === 'function') {
    b[pk].onClick({preventDefault(){}, stopPropagation(){},
                   target: b, currentTarget: b, nativeEvent: {}});
    return JSON.stringify({ok: true, via: 'props'});
  }
  const fk = Object.keys(b).find(k => k.startsWith('__reactFiber$'));
  if (fk) {
    let f = b[fk], d = 0;
    while (f && d < 40) {
      const p = f.memoizedProps || {};
      if (typeof p.onClick === 'function') {
        p.onClick({preventDefault(){}, stopPropagation(){},
                   target: b, currentTarget: b, nativeEvent: {}});
        return JSON.stringify({ok: true, via: 'fiber@' + d});
      }
      f = f.return; d++;
    }
  }
  return JSON.stringify({err: 'no onClick:' + target});
})()
"""

# 受控 input 赋值（绕过 React value tracker）
_SET_INPUT_JS = r"""
(() => {
  const scope = document.querySelector(%(root)s);
  if (!scope) return JSON.stringify({err: 'no scope'});
  const inp = scope.querySelector(%(selector)s);
  if (!inp) return JSON.stringify({err: 'no input'});
  const proto = inp.tagName === 'TEXTAREA'
    ? window.HTMLTextAreaElement.prototype
    : window.HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
  setter.call(inp, %(value)s);
  ['input', 'change', 'blur'].forEach(t =>
    inp.dispatchEvent(new Event(t, {bubbles: true})));
  return JSON.stringify({ok: true, value: inp.value});
})()
"""

# antd Select 打开下拉（mousedown+mouseup+click 序列）
_OPEN_SELECT_JS = r"""
(() => {
  const scope = document.querySelector(%(root)s);
  if (!scope) return JSON.stringify({err: 'no scope'});
  const sel = scope.querySelector(%(selector)s);
  if (!sel) return JSON.stringify({err: 'no selector'});
  const q = sel.getBoundingClientRect();
  ['mousedown', 'mouseup', 'click'].forEach(t => {
    sel.dispatchEvent(new MouseEvent(t, {bubbles: true, cancelable: true,
      view: window, clientX: q.x + q.width / 2, clientY: q.y + q.height / 2}));
  });
  return JSON.stringify({ok: true});
})()
"""

# 选下拉项
_PICK_OPTION_JS = r"""
(() => {
  const want = %(want)s;
  const idx = %(idx)s;
  const dds = [...document.querySelectorAll('.ant-select-dropdown')]
    .filter(x => !x.className.includes('hidden'));
  if (!dds.length) return JSON.stringify({err: 'no dropdown'});
  const dd = dds[dds.length - 1];
  let opts = [...dd.querySelectorAll('.ant-select-item-option')];
  if (!opts.length) opts = [...dd.querySelectorAll('.ant-select-tree-treenode')];
  if (!opts.length) return JSON.stringify({err: 'no options'});
  let t = null;
  if (want) t = opts.find(o => (o.textContent || '').indexOf(want) >= 0);
  if (!t) t = opts[Math.min(idx, opts.length - 1)];
  if (!t) return JSON.stringify({err: 'not found'});
  t.click();
  return JSON.stringify({ok: true,
    picked: (t.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40)});
})()
"""


def _js(d, expr):
    r = d.eval(expr)
    if isinstance(r, str):
        try:
            return json.loads(r)
        except Exception:
            return r
    return r


def react_click(d, text, root=None):
    """点击 React 按钮（走 props.onClick，非 DOM click）。

    text: 按钮可见文本（精确匹配，去空白）
    root: CSS 选择器，限定搜索范围（如 'aside.udc-microflow-editor-node-settings'）
    """
    return _js(d, _REACT_CLICK_JS % {
        'text': json.dumps(text, ensure_ascii=False),
        'root': json.dumps(root) if root else 'null',
    })


def set_controlled_input(d, selector, value, root):
    """给受控 input/textarea 赋值（绕过 React value tracker）。"""
    return _js(d, _SET_INPUT_JS % {
        'root': json.dumps(root),
        'selector': json.dumps(selector),
        'value': json.dumps(str(value), ensure_ascii=False),
    })


def open_antd_select(d, selector, root):
    """打开 antd Select 下拉。"""
    return _js(d, _OPEN_SELECT_JS % {
        'root': json.dumps(root),
        'selector': json.dumps(selector),
    })


def pick_option(d, want=None, idx=0):
    """选中当前打开的下拉里匹配 want 的项（无匹配则取 idx）。"""
    return _js(d, _PICK_OPTION_JS % {
        'want': json.dumps(want, ensure_ascii=False) if want else 'null',
        'idx': int(idx),
    })
