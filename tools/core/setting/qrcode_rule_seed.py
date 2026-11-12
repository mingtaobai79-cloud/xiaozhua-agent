"""二维码规则：三种类型全量创建 + DB 回读（可复用脚本）。

对应事实格 core/facts/udc/setting/qrcode/create.md
契约     docs/operation-contracts/udc/setting/qrcode-contracts.md
实现     components/udc/setting/qrcode_constraints.py

★ 协议是 REST（/service/udc/qrcode-rule/*），不是 GraphQL。

用法：
  python tools/core/setting/qrcode_rule_seed.py --list
  python tools/core/setting/qrcode_rule_seed.py --run \
      --app-id <appId> --entity-full-name <实体全类名> --field-code <字段name> \
      --page-path <udc_page_info.page_url> --i-have-write-authorization
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from components.udc.setting.qrcode_constraints import (  # noqa: E402
    build_qr_rule_body, build_search_body, validate_qr_rule_body,
    validate_link_page_path)

# 页面只提供三种（QRCODE(3) 枚举有值但 UI 不给选）
TYPES = [
    {"name": "FIELDQRCODE", "label": "字段二维码", "need_field": True},
    {"name": "BARCODE",     "label": "条形码",     "need_field": True},
    {"name": "LINKQRCODE",  "label": "链接二维码", "need_field": False},
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9250)
    ap.add_argument("--target-prefix", default=None,
                    help="CDP 标签页 id 前缀（不传则取第一个低代码页）")
    ap.add_argument("--app-id", default=None)
    ap.add_argument("--app-guid", default=None)
    ap.add_argument("--entity-full-name", default=None)
    ap.add_argument("--field-code", default=None,
                    help="实体字段 name（如 code / long_url）")
    ap.add_argument("--page-path", default=None,
                    help="udc_page_info.page_url（链接码用；禁止自编 URL）")
    ap.add_argument("--name-prefix", default="qrProbe")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    a = ap.parse_args()

    if a.list or not a.run:
        print("二维码规则：页面只提供三种类型\n")
        for t in TYPES:
            print(f"  {t['name']:<14} {t['label']:<10} "
                  f"{'需 valueFieldCode' if t['need_field'] else '需 pcPagePath/mobilePagePath'}")
        print("\n⚠ 链接码的 pcPagePath = udc_page_info.page_url，禁止自编 URL")
        if not a.run:
            return 0

    missing = [k for k in ("app_id", "app_guid", "entity_full_name")
               if not getattr(a, k)]
    if missing:
        print("必须给:", ", ".join("--" + m.replace("_", "-") for m in missing))
        return 1
    if not a.i_have_write_authorization:
        print("写操作需显式确认：--i-have-write-authorization")
        return 1

    from providers.cdp import CdpClient

    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    pages = [t for t in tgts if t.get("type") == "page"
             and "lowcode" in t.get("url", "")]
    if a.target_prefix:
        pages = [t for t in pages if str(t.get("id", "")).startswith(a.target_prefix)]
    if not pages:
        print("无可用的低代码标签页")
        return 2
    c = CdpClient(a.port, allow_network=True, timeout=120)
    c.connect(target=pages[0])

    def post(path, body):
        js = (f"fetch('{path}',{{method:'POST',credentials:'include',"
              "headers:{'Content-Type':'application/json'},"
              f"body:{json.dumps(json.dumps(body, ensure_ascii=False))}}})"
              ".then(r=>r.text())")
        try:
            return json.loads(c.evaluate(js, await_promise=True))
        except Exception as e:
            return {"err": type(e).__name__}

    created = []
    for t in TYPES:
        kw = {}
        if t["need_field"]:
            if not a.field_code:
                print(f"  {t['label']:<10} 跳过（缺 --field-code）")
                continue
            kw["value_field_code"] = a.field_code
        else:
            if not a.page_path:
                print(f"  {t['label']:<10} 跳过（缺 --page-path）")
                continue
            kw["link_type"] = "APP"
            kw["pc_page_path"] = a.page_path
        body = build_qr_rule_body(
            a.app_id, a.app_guid,
            name=f"{a.name_prefix}{t['name'][:6]}",
            entity_full_name=a.entity_full_name,
            type_=t["name"], **kw)
        errs = validate_qr_rule_body(body)
        if t["name"] == "LINKQRCODE" and a.page_path:
            errs += validate_link_page_path(body, {a.page_path})
        if errs:
            print(f"  {t['label']:<10} 本地校验: {errs[:1]}")
            continue
        r = post("/service/udc/qrcode-rule/create", body)
        code = r.get("code")
        ok = code == "BOOT_0000"
        nid = (r.get("data") or {}).get("content")
        print(f"  {t['label']:<10} {'✅' if ok else '❌'} {code} id={nid}")
        created.append({"type": t["name"], "ok": ok, "code": code, "id": nid})

    # DB 回读
    print("\n=== search 复查 ===")
    body = build_search_body(app_id=a.app_id)
    r = post("/service/udc/qrcode-rule/search", body)
    items = (r.get("data") or {}).get("content") or []
    if isinstance(items, dict):
        items = items.get("content") or items.get("list") or []
    print(f"  规则数 {len(items)}")
    for x in items[:10]:
        print(f"    {x.get('name'):<20} type={x.get('type')}")

    out = Path(r"<HERMES_HOME>\cache\scratch\qrcode")
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(
        json.dumps({"created": created, "search": items},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n-> {out / 'result.json'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
