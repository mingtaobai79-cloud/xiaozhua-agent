"""按 dataType 修正字段的 widgetConfig（用真实默认控件）。

问题：之前所有字段一律用 Input，导致
  日期字段用 Input 装不了、枚举用 Input 选不了、附件用 Input 传不了。
修正：按 DB 真实样本统计出的 DEFAULT_WIDGETS 逐个类型设置。

用法：
  python tools/core/setting/attribute_widget_fix.py --dump --set-id <id>
  python tools/core/setting/attribute_widget_fix.py --fix-all --set-id <id> \
      --i-have-write-authorization
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from components.udc.setting.attribute_set_constraints import (  # noqa: E402
    DEFAULT_WIDGETS, build_widget_config, validate_sysvar,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--app-id", default=None, help="UDC 应用 id（默认读 SEEYON_APP_ID）")
    ap.add_argument("--target-prefix", default="BCD2D805")
    ap.add_argument("--set-id", default="-3410968647846163890")
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--fix-all", action="store_true")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    a = ap.parse_args()

    import urllib.request
    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    cand = [t for t in tgts if t.get("type") == "page"
            and str(t.get("id", "")).startswith(a.target_prefix)]
    if not cand:
        print(f"找不到 {a.target_prefix} 标签页")
        return 2
    from providers.cdp import CdpClient
    c = CdpClient(a.port, allow_network=True, timeout=120)
    c.connect(target=cand[0])

    def post(path, body, to=25):
        c.evaluate("window.__R__=null;window.__D__=false;", await_promise=False)
        c.evaluate("""(function(){fetch('%s',{method:'POST',credentials:'include',
          headers:{'Content-Type':'application/json'},body:%s})
          .then(r=>r.text()).then(t=>{window.__R__=t;window.__D__=true;})
          .catch(e=>{window.__R__='ERR:'+e.message;window.__D__=true;});return 'ok';})()""" % (
          path, json.dumps(json.dumps(body, ensure_ascii=False))), await_promise=False)
        end = time.time() + to
        while time.time() < end:
            time.sleep(0.3)
            try:
                if c.evaluate("window.__D__===true", await_promise=False) == True:
                    raw = c.evaluate("window.__R__", await_promise=False)
                    try:
                        return json.loads(raw)
                    except Exception:
                        return {"raw": str(raw)[:300]}
            except Exception:
                pass
        return {"err": "TIMEOUT"}

    def get_dto(fid):
        g = ("(async()=>{const r=await fetch('/service/udc/entity/attribute/%s',"
             "{credentials:'include'});return await r.text();})()" % fid)
        return json.loads(c.evaluate(g, await_promise=True))["data"]["content"]

    rd = post("/service/udc/attributeSet/select-attribute-list",
              {"attributeSetId": a.set_id})
    attrs = (rd.get("data") or {}).get("content") or []
    print(f"字段集 {a.set_id} 共 {len(attrs)} 个字段\n")

    need_fix = []
    print(f"{'字段':<16}{'类型':<16}{'当前 pc/mobile':<36}{'应为':<36}")
    for x in attrs:
        dt = x.get("dataType") or ""
        cur = x.get("widgetConfig") or ""
        try:
            curpc = json.loads(cur).get("pc", "?") if cur else "?"
            curmo = json.loads(cur).get("mobile", "?") if cur else "?"
        except Exception:
            curpc, curmo = "?", "?"
        dpc, dmo = DEFAULT_WIDGETS.get(dt, ("Input", "Input"))
        flag = "" if (curpc == dpc and curmo == dmo) else "  ← 需修"
        print(f"{(x.get('caption') or '')[:14]:<16}{dt:<16}"
              f"{curpc + '/' + curmo:<36}{dpc + '/' + dmo:<36}{flag}")
        if flag:
            need_fix.append((x.get("name"), x.get("id"), dt, curpc, curmo, dpc, dmo))

    if not need_fix:
        print("\n✅ 所有字段的控件都正确")
        c.close()
        return 0

    print(f"\n需修正 {len(need_fix)} 个")
    if a.dump or not a.fix_all:
        print("加 --fix-all --i-have-write-authorization 执行修正")
        c.close()
        return 0
    if not a.i_have_write_authorization:
        print("写操作需显式确认：加 --i-have-write-authorization")
        c.close()
        return 1

    for name, fid, dt, _cp, _cm, dpc, dmo in need_fix:
        dto = get_dto(fid)
        dto["widgetConfig"] = build_widget_config(dt)
        # runtime 必须空（上一轮已定性：非空会被拒 BOOT_3000）
        dto["expressionRuntimeData"] = None
        # sysvar 必须合法 JSON
        if validate_sysvar(dto.get("defaultValueSystemVariable")):
            dto["defaultValueSystemVariable"] = None
        r = post("/service/udc/entity/attribute/update", dto)
        print(f"  {name:<16} -> {dpc}/{dmo}   {r.get('code')}")

    # 回读
    rd2 = post("/service/udc/attributeSet/select-attribute-list",
               {"attributeSetId": a.set_id})
    print("\n回读：")
    for x in ((rd2.get("data") or {}).get("content") or []):
        w = json.loads(x.get("widgetConfig") or "{}")
        dt = x.get("dataType") or ""
        dpc, dmo = DEFAULT_WIDGETS.get(dt, ("Input", "Input"))
        ok = (w.get("pc") == dpc and w.get("mobile") == dmo)
        print(f"  {(x.get('caption') or '')[:14]:<16}{dt:<16}"
              f"{w.get('pc','?'):<18}{w.get('mobile','?'):<18}{'✅' if ok else '❌'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
