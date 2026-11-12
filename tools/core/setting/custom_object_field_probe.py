"""自定义对象字段：单行真实 UI 提交 + 抓包（定位字段属于哪个 operation）。

背景：`udcDataTransferObjectUpdatePost` 的 body 里塞 attributes/dtoAttributes/fields
等各种 key 都返回 BOOT_0000 但**字段不落库**（udc_dto_attribute 无新增行）——
说明字段不是由 UpdatePost 承载的，必须找到真实的组装端点。

本脚本：打开编辑器 → 加 1 行 → 填名 → 真实鼠标选类型 → 点确定 → 读拦截器捕获。
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

CAPTURE = r"""
(() => {
  window.__CAP3__ = [];
  const rec=(u,b)=>{try{window.__CAP3__.push({url:String(u),body:b?String(b):null});}catch(e){}};
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


def click_rect(c, js_rect):
    r = c.evaluate(js_rect)
    if not r or r == "null":
        return False
    x, y = json.loads(r)
    c.send("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
    c.send("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button="left", clickCount=1)
    c.send("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left", clickCount=1)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--target", default="A886072E39FD374937FE966D008AABC5")
    ap.add_argument("--object-name", default="zxjAllTypeProbe")
    ap.add_argument("--label", default="整数")
    ap.add_argument("--code", default="probeInt")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\co-type-probe")
    a = ap.parse_args()

    import urllib.request
    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    tgt = [t for t in tgts if t.get("id") == a.target][0]
    c = CdpClient(a.port, allow_network=True, timeout=90)
    c.connect(target=tgt)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    print("1 capture:", j(c, CAPTURE))
    # 切 tab + 打开编辑
    j(c, r"""(()=>{const t=[...document.querySelectorAll('.ant-tabs-tab')].find(e=>(e.textContent||'').trim()==='自定义对象');
      if(t){t.dispatchEvent(new MouseEvent('mousedown',{bubbles:true})); t.click();} return 'ok';})()""")
    time.sleep(2)
    print("2 edit:", j(c, r"""(()=>{const rows=[...document.querySelectorAll('tr')].filter(tr=>tr.offsetParent!==null);
      const t=rows.find(tr=>(tr.innerText||'').includes(%s)); if(!t) return 'no-row';
      const b=[...t.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='编辑');
      if(!b) return 'no-btn'; b.click(); return 'ok';})()""" % json.dumps(a.object_name)))
    time.sleep(2)
    print("3 add:", j(c, r"""(()=>{const d=document.querySelector('.ant-modal-content');
      if(!d) return 'no-dlg';
      const b=[...d.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='添加一行');
      if(!b) return 'no-add'; b.click(); return 'ok';})()"""))
    time.sleep(1)

    # 填名（先编码后显示名）
    print("4 fill:", j(c, r"""(()=>{const d=document.querySelector('.ant-modal-content');
      const rows=[...d.querySelectorAll('tbody tr')].filter(x=>x.querySelector('input.ant-input'));
      const r=rows[rows.length-1]; if(!r) return 'no-row';
      const set=(el,v)=>{const p=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value');
        p.set.call(el,v); el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true}));};
      const nm=r.querySelector('input[id$="name"]'), cap=r.querySelector('input[id$="caption"]');
      set(nm,%s); set(cap,%s);
      return JSON.stringify({n:nm.value,c:cap.value});})()""" % (json.dumps(a.code), json.dumps(a.label + "字段"))))

    # 选类型（真实鼠标）
    idx = None
    print("5 open type:", click_rect(c, r"""
    (() => {const d=document.querySelector('.ant-modal-content');
      const rows=[...d.querySelectorAll('tbody tr')].filter(x=>x.querySelector('input.ant-input'));
      const r=rows[rows.length-1]; if(!r) return 'null';
      r.scrollIntoView({block:'center'});
      const s=r.querySelector('.ant-tree-select .ant-select-selector'); if(!s) return 'null';
      const b=s.getBoundingClientRect();
      return JSON.stringify([b.x+b.width/2, b.y+b.height/2]);})()
    """))
    time.sleep(1.2)
    print("6 pick:", click_rect(c, r"""
    (() => {const d=[...document.querySelectorAll('.ant-select-dropdown')].filter(x=>x.offsetParent!==null)[0];
      if(!d) return 'null';
      const t=[...d.querySelectorAll('.ant-select-tree-title')].find(x=>x.innerText.trim()===%s);
      if(!t) return 'null';
      const b=t.getBoundingClientRect();
      return JSON.stringify([b.x+b.width/2, b.y+b.height/2]);})()
    """ % json.dumps(a.label)))
    time.sleep(1)
    print("7 row:", j(c, r"""(()=>{const d=document.querySelector('.ant-modal-content');
      if(!d) return 'no-dlg';
      const rows=[...d.querySelectorAll('tbody tr')].filter(x=>x.querySelector('input.ant-input'));
      const r=rows[rows.length-1];
      return JSON.stringify({types:[...r.querySelectorAll('.ant-select-selection-item')].map(e=>e.innerText.trim())});})()"""))

    # 清拦截器 → 点确定 → 读捕获
    j(c, "window.__CAP3__ && (window.__CAP3__.length=0)")
    print("8 submit:", j(c, r"""(()=>{const d=document.querySelector('.ant-modal-content');
      if(!d) return 'no-dlg';
      const b=[...d.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='确定');
      if(!b) return 'no-ok'; b.click(); return 'clicked';})()"""))
    time.sleep(3.5)
    caps = j(c, "JSON.stringify(window.__CAP3__ || [])")
    after = j(c, r"""(()=>{const d=document.querySelector('.ant-modal-content');
      return JSON.stringify({dlgOpen:!!d,
        errors: d?[...d.querySelectorAll('.ant-form-item-explain-error')].map(e=>e.innerText.trim()).slice(0,10):[],
        msg: (document.querySelector('.ant-message')||{}).innerText||''});})()""")
    print("9 after:", after)

    data = {"label": a.label, "code": a.code, "captured": json.loads(caps) if caps else []}
    (out / "single-row-submit.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    for cap in data["captured"]:
        print("   URL:", cap["url"])
        if cap["body"]:
            print("   BODY:", cap["body"][:900])
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
