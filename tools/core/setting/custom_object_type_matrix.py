"""自定义对象字段：12 种数据类型 × 类别 的真实组装抓包。

背景（2026-10-21 实测）：
  - **字段不由 `udcDataTransferObjectUpdatePost` 承载** —— 往它的 body 塞
    attributes/dtoAttributes/fields… 全返回 BOOT_0000 但 udc_dto_attribute 零新增。
  - 真实端点是 `udcDataTransferObjectUpdateDtoPost`（抓包实证）。
  - attribute 结构（平台自己发的 body 原文）：
      {name, caption, notNull, dataType, dataTypeCategory, type, relationApp, appId}
    dataTypeCategory / type 是**枚举字符串**（PRIMITIVE / OBJECT），不是数字。

做法：真实 UI 驱动（antd tree-select 只认真实鼠标事件），一次铺 12 行，
逐行选类型，最后点一次确定，捕获平台发出的完整 body。

用法：
  python tools/core/setting/custom_object_type_probe.py --submit
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

CAPTURE = r"""
(() => {
  window.__CAP4__ = [];
  const rec=(u,b)=>{try{window.__CAP4__.push({url:String(u),body:b?String(b):null});}catch(e){}};
  const of=window.fetch;
  window.fetch=function(i,ini){try{rec(i&&i.url?i.url:i,ini&&ini.body);}catch(e){}return of.apply(this,arguments);};
  const oo=XMLHttpRequest.prototype.open, os=XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open=function(m,u){this.__u=u;return oo.apply(this,arguments);};
  XMLHttpRequest.prototype.send=function(b){try{rec(this.__u,b);}catch(e){}return os.apply(this,arguments);};
  return 'installed';
})()
"""


def j(c, js):
    try:
        return c.evaluate(js)
    except Exception as e:
        return "ERR:" + str(e)[:150]


def click_xy(c, x, y):
    c.send("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
    c.send("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button="left", clickCount=1)
    c.send("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left", clickCount=1)


def click_rect(c, js_rect):
    r = c.evaluate(js_rect)
    if not r or r == "null":
        return None
    x, y = json.loads(r)
    click_xy(c, x, y)
    return (x, y)


def drop_open(c):
    r = j(c, "JSON.stringify([...document.querySelectorAll('.ant-select-dropdown')].map(d=>d.offsetParent!==null))")
    return r and "true" in r


def row_sel(c, idx):
    r = j(c, r"""
    (() => {const d=document.querySelector('.ant-modal-content');
      if(!d) return '[]';
      const rows=[...d.querySelectorAll('tbody tr')].filter(r=>r.querySelector('input.ant-input'));
      const r=rows[%d]; if(!r) return '[]';
      return JSON.stringify([...r.querySelectorAll('.ant-select-selection-item')].map(e=>e.innerText.trim()));})()
    """ % idx)
    try:
        return json.loads(r)
    except Exception:
        return []


SEL_RECT = r"""
(() => {
  const d=document.querySelector('.ant-modal-content'); if(!d) return 'null';
  const rows=[...d.querySelectorAll('tbody tr')].filter(r=>r.querySelector('input.ant-input'));
  const r=rows[%d]; if(!r) return 'null';
  r.scrollIntoView({block:'center'});
  const s=r.querySelector('.ant-tree-select .ant-select-selector'); if(!s) return 'null';
  const b=s.getBoundingClientRect();
  if(b.top<0||b.bottom>innerHeight) return 'null';
  return JSON.stringify([Math.round(b.x+b.width/2), Math.round(b.y+b.height/2)]);
})()
"""

TITLE_RECT = r"""
(() => {
  const d=[...document.querySelectorAll('.ant-select-dropdown')].filter(x=>x.offsetParent!==null)[0];
  if(!d) return 'null';
  const t=[...d.querySelectorAll('.ant-select-tree-title')].find(x=>x.innerText.trim()===%s);
  if(!t) return 'null';
  const b=t.getBoundingClientRect();
  return JSON.stringify([Math.round(b.x+b.width/2), Math.round(b.y+b.height/2)]);
})()
"""


def set_type(c, idx, label):
    """点开类型树 → 选 label。每一步都轮询确认，失败重试。"""
    for attempt in range(3):
        if not drop_open(c):
            click_rect(c, SEL_RECT % idx)
            for _ in range(10):
                time.sleep(0.3)
                if drop_open(c):
                    break
        if not drop_open(c):
            # 兜底：JS 派发 mousedown
            j(c, r"""
            (() => {const d=document.querySelector('.ant-modal-content');
              const rows=[...d.querySelectorAll('tbody tr')].filter(r=>r.querySelector('input.ant-input'));
              const s=rows[%d] && rows[%d].querySelector('.ant-tree-select .ant-select-selector');
              if(!s) return 'no-sel';
              s.dispatchEvent(new MouseEvent('mousedown',{bubbles:true}));
              s.click(); return 'ok';})()
            """ % (idx, idx))
            for _ in range(10):
                time.sleep(0.3)
                if drop_open(c):
                    break
        if not drop_open(c):
            continue
        click_rect(c, TITLE_RECT % json.dumps(label))
        for _ in range(8):
            time.sleep(0.3)
            cur = row_sel(c, idx)
            if cur and cur[0] == label:
                return "ok:" + str(cur)
        # 没选上，若下拉还开着再试下一轮
    return "FAIL:" + str(row_sel(c, idx))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--target", default="A886072E39FD374937FE966D008AABC5")
    ap.add_argument("--object-name", default="zxjAllTypeProbe")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\co-type-probe")
    ap.add_argument("--submit", action="store_true")
    a = ap.parse_args()

    import urllib.request
    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    tgt = [t for t in tgts if t.get("id") == a.target][0]
    c = CdpClient(a.port, allow_network=True, timeout=90)
    c.connect(target=tgt)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    print("capture:", j(c, CAPTURE))
    j(c, r"""(()=>{const t=[...document.querySelectorAll('.ant-tabs-tab')].find(e=>(e.textContent||'').trim()==='自定义对象');
      if(t){t.dispatchEvent(new MouseEvent('mousedown',{bubbles:true})); t.click();} return 'ok';})()""")
    time.sleep(2)
    print("edit:", j(c, r"""(()=>{const rows=[...document.querySelectorAll('tr')].filter(tr=>tr.offsetParent!==null);
      const t=rows.find(tr=>(tr.innerText||'').includes(%s)); if(!t) return 'no-row';
      const b=[...t.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='编辑');
      if(!b) return 'no-btn'; b.click(); return 'ok';})()""" % json.dumps(a.object_name)))
    time.sleep(2)

    # 铺 12 行
    for _ in range(12):
        j(c, r"""(()=>{const d=document.querySelector('.ant-modal-content');
          const b=d&&[...d.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='添加一行');
          if(b) b.click(); return 'ok';})()""")
        time.sleep(0.45)
    n = j(c, "(()=>{const d=document.querySelector('.ant-modal-content');return d?[...d.querySelectorAll('tbody tr')].filter(r=>r.querySelector('input.ant-input')).length:-1})()")
    print("rows:", n)

    results = []
    for i, (label, code0) in enumerate(TYPE_SPEC):
        code = "f%d_%s" % (i, code0)
        j(c, r"""
        (() => {const d=document.querySelector('.ant-modal-content');
          const rows=[...d.querySelectorAll('tbody tr')].filter(x=>x.querySelector('input.ant-input'));
          const r=rows[%d]; if(!r) return 'no-row';
          const set=(el,v)=>{const p=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value');
            p.set.call(el,v); el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true}));};
          const nm=r.querySelector('input[id$="name"]'), cap=r.querySelector('input[id$="caption"]');
          set(nm,%s); set(cap,%s); return 'ok';})()
        """ % (i, json.dumps(code), json.dumps(label + "字段")))
        st = set_type(c, i, label)
        print(f"[{i:>2}] {label:<5} {code:<12} {st}")
        results.append({"i": i, "type": label, "code": code, "set": st})

    data = {"rows": results, "captured": []}
    if a.submit:
        j(c, "window.__CAP4__ && (window.__CAP4__.length=0)")
        print("submit:", j(c, r"""(()=>{const d=document.querySelector('.ant-modal-content');
          if(!d) return 'no-dlg';
          const b=[...d.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='确定');
          if(!b) return 'no-ok'; b.click(); return 'clicked';})()"""))
        time.sleep(4)
        caps = j(c, "JSON.stringify(window.__CAP4__ || [])")
        data["captured"] = json.loads(caps) if caps else []
        data["after"] = j(c, r"""(()=>{const d=document.querySelector('.ant-modal-content');
          return JSON.stringify({dlgOpen:!!d,
            errors: d?[...d.querySelectorAll('.ant-form-item-explain-error')].map(e=>e.innerText.trim()).slice(0,20):[],
            msg: (document.querySelector('.ant-message')||{}).innerText||''});})()""")
        print("after:", data["after"])

    (out / "assembly.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("-> " + str(out / "assembly.json"))
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
