"""设置域 · 流水号：建两个样本（给用户页面验收）。

走 xiaozhua-agent 自己的构造器 + 校验器（字段名来自反编译 SerialSchemeDto）。

用法：
  python tools/core/setting/serial_seed.py --port 9231 [--i-have-write-authorization]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from components.udc.setting.serial_constraints import (  # noqa: E402
    build_serial_scheme_body, build_serial_section, validate_serial_scheme_body,
)

APP_ID = None  # ★ 由 --app-id / XIAOZHUA_APP_ID 提供
APP_ID = __import__("os").environ.get("XIAOZHUA_APP_ID") or APP_ID

APP_GUID = "2275741415570096882"

# 两个样本，展示不同段组合
SAMPLES = [
    {
        "code": "ZxjOrderNo",
        "name": "验收订单号",
        "sort_num": 1,
        "contain_flow": True,
        "sections": [
            dict(type_="CONSTANT", size=2, value="DD", section_rank=1,
                 fill_type="NONE", cut_type="NONE"),
            dict(type_="CONTEXT", size=8, value="currentDate", section_rank=2,
                 date_type=True, date_pattern="yyyyMMdd",
                 fill_type="LEFT", cut_type="NONE", flow=True),
            dict(type_="SERIAL", size=4, section_rank=3, flow=True,
                 increase=True, start_value=1, end_value=9999,
                 fill_type="NONE", cut_type="NONE"),
        ],
    },
    {
        "code": "ZxjContractNo",
        "name": "验收合同编号",
        "sort_num": 2,
        "contain_flow": True,
        "sections": [
            dict(type_="CONSTANT", size=2, value="HT", section_rank=1,
                 fill_type="NONE", cut_type="NONE"),
            dict(type_="CONTEXT", size=6, value="currentDate", section_rank=2,
                 date_type=True, date_pattern="yyyyMM", fill_type="LEFT", cut_type="NONE",
                 flow=True),
            dict(type_="SERIAL", size=5, section_rank=3, flow=True,
                 increase=True, start_value=1, end_value=99999,
                 fill_type="NONE", cut_type="NONE"),
        ],
    },
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--i-have-write-authorization", action="store_true")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\serial-seed")
    a = ap.parse_args()

    plan = []
    for s in SAMPLES:
        secs = [build_serial_section(**x) for x in s["sections"]]
        body = build_serial_scheme_body(
            APP_ID, APP_GUID, code=s["code"], name=s["name"], sections=secs,
            sort_num=s["sort_num"], contain_flow=s["contain_flow"])
        errs = validate_serial_scheme_body(body)
        print(f"[{s['name']}] 本地校验: {errs or '✅ 通过'}  "
              f"（{len(secs)} 段，总长 {body['totalSize']}）")
        plan.append({"body": body, "errors": errs})

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")

    if not a.i_have_write_authorization:
        print(f"\n只构造未写入 -> {out/'plan.json'}")
        return 0
    if any(p["errors"] for p in plan):
        print("有本地校验错误，拒绝提交")
        return 2

    import urllib.request
    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    pages = [t for t in tgts if t.get("type") == "page" and "lowcode-test2" in t.get("url", "")]
    from providers.cdp import CdpClient
    c = CdpClient(a.port, allow_network=True, timeout=90)
    c.connect(target=pages[0])

    def gql(op, body):
        q = ("mutation graphqlLoader ($params0: %sInputBody) { \n"
             "  data0: %s(body: $params0) { code message status data { content } } }" % (op, op))
        payload = {"query": q, "variables": {"params0": body}}
        js = ("(async()=>{const r=await fetch('/service/udc/graphql?%s',{method:'POST',credentials:'include',"
              "headers:{'Content-Type':'application/json'},body:%s});return await r.text();})()"
              % (op, json.dumps(json.dumps(payload, ensure_ascii=False))))
        return json.loads(c.evaluate(js, await_promise=True))["data"]["data0"]

    results = []
    for p in plan:
        r = gql("udcSerialSchemeCreatePost", p["body"])
        ok = r.get("code") == "BOOT_0000"
        rec = {"code": p["body"]["code"], "name": p["body"]["name"], "ok": ok,
               "id": (r.get("data") or {}).get("content") if ok else None,
               "totalSize": p["body"]["totalSize"],
               "sections": len(p["body"]["serialSectionDtoList"])}
        results.append(rec if ok else {**rec, "resp": r})
        print(f"\n{'✅' if ok else '❌'} {p['body']['name']}")
        if ok:
            print(f"   id={rec['id']}  code={rec['code']}  总长={rec['totalSize']}  "
                  f"{rec['sections']} 段")
        else:
            print(f"   {json.dumps(r, ensure_ascii=False)[:250]}")
            break

    (out / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n结果 -> {out/'result.json'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
