"""自定义对象字段：一次组装全部 12 种数据类型，捕获平台真实请求体。

目标（2026-10-21 用户要求）：
  「任何的数据类型的格式，和类别你都得试一下，你看他是怎么组装的」

做法（真实 UI 驱动 + 网络捕获）：
  1. 打开「编辑自定义对象」弹窗
  2. 一次性铺 12 行（文本/整数/长整数/小数/日期/日期时间/布尔/附件/枚举/选项集/对象/关联实体）
  3. 逐行填显示名/编码，用**真实鼠标事件**在类型树上选类型
  4. 点一次「确定」，捕获平台发出的 GraphQL body —— 这就是组装形态

为什么必须用真实鼠标：antd tree-select 只认真实 Input 事件序列，
合成 DOM click 改不动它的受控状态（2026-10-21 实测，JS click 后 selection-item 不变）。

输出：<out>/assembly.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from providers.cdp import CdpClient  # noqa: E402

TYPE_SPEC = [
    ("文本", "str"),
    ("整数", "int"),
    ("长整数", "bigint"),
    ("小数", "dec"),
    ("日期", "date"),
    ("日期时间", "dt"),
    ("布尔", "bool"),
    ("附件", "att"),
    ("枚举", "enum"),
    ("选项集", "optset"),
    ("对象", "obj"),
    ("关联实体", "rel"),
]

CAPTURE_JS = r"""
(() => {
  window.__CAP2__ = [];
  const rec = (u, b) => { try { window.__CAP2__.push({url: String(u), body: b ? String(b) : null}); } catch(e){} };
  const of = window.fetch;
  window.fetch = function(i, ini) { try { rec(i && i.url ? i.url : i, ini && ini.body); } catch(e){} return of.apply(this, arguments); };
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function(m, u) { this.__u = u; return oo.apply(this, arguments); };
  XMLHttpRequest.prototype.send = function(b) { try { rec(this.__u, b); } catch(e){} return os.apply(this, arguments); };
  return 'installed';
})()
"""

ROW_COUNT_JS = ("(()=>{const d=document.querySelector('.ant-modal-content');"
                " return d? [...d.querySelectorAll('tbody tr')].filter(r=>r.querySelector('input.ant-input')).length : 0})()")


def click_rect(c, js_rect):
    r = c.evaluate(js_rect)
    if not r or r == "null":
        return False
    x, y = json.loads(r)
    c.send("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
    c.send("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button="left", clickCount=1)
    c.send("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left", clickCount=1)
    return True


def open_editor(c, object_name="zxjAllTypeProbe"):
    c.evaluate(r"""
    (() => {
      const t=[...document.querySelectorAll('.ant-tabs-tab')].find(e=>(e.textContent||'').trim()==='自定义对象');
      if(t){t.dispatchEvent(new MouseEvent('mousedown',{bubbles:true})); t.click();}
      return 'ok';
    })()
    """)
    time.sleep(2)
    c.evaluate(r"""
    (() => {
      const rows=[...document.querySelectorAll('tr')].filter(tr=>tr.offsetParent!==null);
      const t=rows.find(tr=>(tr.innerText||'').includes(%s));
      if(!t) return 'no row';
      const btn=[...t.querySelectorAll('button')].find(b=>(b.innerText||'').trim()==='编辑');
      if(!btn) return 'no edit';
      btn.click(); return 'ok';
    })()
    """ % json.dumps(object_name))
    time.sleep(2)
    return bool(c.evaluate("!!document.querySelector('.ant-modal-content')"))


def ensure_rows(c, n):
    have = c.evaluate(ROW_COUNT_JS)
    guard = 0
    while have < n and guard < n + 5:
        c.evaluate(r"""
        (() => {const d=document.querySelector('.ant-modal-content');
          const a=[...d.querySelectorAll('button')].find(b=>(b.innerText||'').trim()==='添加一行');
          if(a) a.click(); return 'ok';})()
        """)
        time.sleep(0.6)
        have = c.evaluate(ROW_COUNT_JS)
        guard += 1
    return have


def fill_row(c, idx, caption, code):
    return c.evaluate(r"""
    (() => {
      const dlg=document.querySelector('.ant-modal-content');
      const rows=[...dlg.querySelectorAll('tbody tr')].filter(r=>r.querySelector('input.ant-input'));
      const r=rows[%d];
      if(!r) return 'no-row';
      const set=(el,v)=>{
        const d=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value');
        d.set.call(el,v);
        el.dispatchEvent(new Event('input',{bubbles:true}));
        el.dispatchEvent(new Event('change',{bubbles:true}));
      };
      const cap=r.querySelector('input[id$="caption"]'), nm=r.querySelector('input[id$="name"]');
      if(!cap||!nm) return 'missing-input';
      set(nm, %s);
      set(cap, %s);
      return JSON.stringify({i:%d, cap:cap.value, name:nm.value});
    })()
    """ % (idx, json.dumps(code), json.dumps(caption), idx))


def _drop_open(c):
    return bool(c.evaluate(
        "JSON.stringify([...document.querySelectorAll('.ant-select-dropdown')].map(d=>d.offsetParent!==null))"
    ).count("true"))


def _row_sel_text(c, idx):
    r = c.evaluate(r"""
    (() => {const dlg=document.querySelector('.ant-modal-content');
      if(!dlg) return '[]';
      const rows=[...dlg.querySelectorAll('tbody tr')].filter(r=>r.querySelector('input.ant-input'));
      const r=rows[%d];
      if(!r) return '[]';
      return JSON.stringify([...r.querySelectorAll('.ant-select-selection-item')].map(e=>e.innerText.trim()));})()
    """ % idx)
    try:
        return json.loads(r)
    except Exception:
        return []


def set_type(c, idx, label):
    """真实鼠标选类型。三重兜底：普通点击 → JS mousedown → 点节点容器。"""
    # 1) 把该行滚进视野，再取选择器中心
    ok = click_rect(c, r"""
    (() => {
      const dlg=document.querySelector('.ant-modal-content');
      const rows=[...dlg.querySelectorAll('tbody tr')].filter(r=>r.querySelector('input.ant-input'));
      const r=rows[%d];
      if(!r) return 'null';
      r.scrollIntoView({block:'center'});
      const sel=r.querySelector('.ant-tree-select .ant-select-selector');
      if(!sel) return 'null';
      const b=sel.getBoundingClientRect();
      if(b.bottom<0 || b.top>innerHeight) return 'null';
      return JSON.stringify([b.x+b.width/2, b.y+b.height/2]);
    })()
    """ % idx)
    if not ok:
        return "no-selector"
    time.sleep(1.0)
    if not _drop_open(c):
        # 兜底：JS 直接派发 mousedown+click
        c.evaluate(r"""
        (() => {
          const dlg=document.querySelector('.ant-modal-content');
          const rows=[...dlg.querySelectorAll('tbody tr')].filter(r=>r.querySelector('input.ant-input'));
          const sel=rows[%d].querySelector('.ant-tree-select .ant-select-selector');
          sel.dispatchEvent(new MouseEvent('mousedown',{bubbles:true}));
          sel.click();
          return 'ok';
        })()
        """ % idx)
        time.sleep(1.0)
    if not _drop_open(c):
        return "no-dropdown"

    # 2) 点 title（文字本体），失败换节点容器
    for target in ("title", "wrapper"):
        js = (r"""
        (() => {
          const d=[...document.querySelectorAll('.ant-select-dropdown')].filter(x=>x.offsetParent!==null)[0];
          if(!d) return 'null';
          let el=null;
          for (const t of d.querySelectorAll('.ant-select-tree-title')) {
            if (t.innerText.trim()===%s) { el=%s; break; }
          }
          if(!el) return 'null';
          const b=el.getBoundingClientRect();
          return JSON.stringify([b.x+b.width/2, b.y+b.height/2]);
        })()
        """ % (json.dumps(label),
               "t" if target == "title" else "(t.closest('.ant-select-tree-treenode')||t)"))
        picked = click_rect(c, js)
        time.sleep(0.8)
        cur = _row_sel_text(c, idx)
        if cur and cur[0] == label:
            return "picked " + str(cur)
        if picked and target == "title":
            continue
        break
    return "NOT-PICKED " + str(_row_sel_text(c, idx))


def row_dump(c, idx):
    r = c.evaluate(r"""
    (() => {
      const dlg=document.querySelector('.ant-modal-content');
      if(!dlg) return null;
      const rows=[...dlg.querySelectorAll('tbody tr')].filter(r=>r.querySelector('input.ant-input'));
      const r=rows[%d];
      if(!r) return null;
      return JSON.stringify({
        i:%d,
        text:(r.innerText||'').replace(/\s+/g,' ').trim(),
        inputs:[...r.querySelectorAll('input')].map(i=>({id:i.id, ph:i.placeholder||'', v:i.value||'', ro:!!i.readOnly})),
        selects:[...r.querySelectorAll('.ant-select')].map(s=>({
          v:(s.querySelector('.ant-select-selection-item')||{}).innerText||'',
          ph:(s.querySelector('input')||{}).placeholder||'',
          cls:(s.className||'').slice(0,70)})),
        checks:[...r.querySelectorAll('.ant-checkbox-input')].map(x=>x.checked)
      });
    })()
    """ % (idx, idx))
    try:
        return json.loads(r) if r else None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--target", default="A886072E39FD374937FE966D008AABC5")
    ap.add_argument("--object-name", default="zxjAllTypeProbe")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\co-type-probe")
    ap.add_argument("--submit", action="store_true", help="填完后点确定（真写平台）")
    a = ap.parse_args()

    import urllib.request
    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    tgt = [t for t in tgts if t.get("id") == a.target][0]
    c = CdpClient(a.port, allow_network=True, timeout=90)
    c.connect(target=tgt)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    print("capture:", c.evaluate(CAPTURE_JS))
    print("open editor:", open_editor(c, a.object_name))
    print("rows:", ensure_rows(c, len(TYPE_SPEC)))

    rows = []
    for i, (label, code0) in enumerate(TYPE_SPEC):
        code = "f%d_%s" % (i, code0)
        fill = fill_row(c, i, label + "字段", code)
        typ = set_type(c, i, label)
        dump = row_dump(c, i)
        print(f"[{i:>2}] {label:<5} {fill} | {typ}")
        rows.append({"i": i, "type": label, "code": code,
                     "fill": fill, "pick": typ, "dump": dump})

    assembly = {"rows": rows, "captured": []}
    if a.submit:
        c.evaluate("window.__CAP2__ && (window.__CAP2__.length=0)")
        r = c.evaluate(r"""
        (() => {const dlg=document.querySelector('.ant-modal-content');
          const b=[...dlg.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='确定');
          if(!b) return 'no-ok';
          b.click(); return 'clicked';})()
        """)
        time.sleep(3)
        caps = c.evaluate("JSON.stringify(window.__CAP2__ || [])")
        assembly["captured"] = json.loads(caps) if caps else []
        assembly["submit"] = r
        assembly["after"] = c.evaluate(r"""
        (() => {const dlg=document.querySelector('.ant-modal-content');
          return JSON.stringify({dlgOpen: !!dlg,
            errors: dlg ? [...dlg.querySelectorAll('.ant-form-item-explain-error')].map(e=>e.innerText.trim()).slice(0,20) : [],
            toast: (document.querySelector('.ant-message')||{}).innerText || ''});})()
        """)
        print("submit:", r, "| after:", assembly.get("after"))

    (out / "assembly.json").write_text(json.dumps(assembly, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n-> " + str(out / "assembly.json"))
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
