"""设置域 · 参数：建两个样本（给用户页面验收）。

走 xiaozhua-agent 自己的构造器 + 校验器。

用法：
  python tools/core/setting/parameter_seed.py --port 9231 [--i-have-write-authorization]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from components.udc.setting.parameter_constraints import (  # noqa: E402
    build_parameter_body, validate_parameter_body,
)

APP_ID = None  # ★ 由 --app-id / XIAOZHUA_APP_ID 提供
APP_ID = __import__("os").environ.get("XIAOZHUA_APP_ID") or APP_ID

APP_GUID = "2275741415570096882"

SAMPLES = [
    {"name": "zxjApiBaseUrl", "caption": "接口基地址", "data_type": "STRING",
     "value": "https://api.example.test", "order_no": 1,
     "description": "验收参数一：接口基地址"},
    {"name": "zxjPageSize", "caption": "分页大小", "data_type": "INTEGER",
     "value": "50", "order_no": 2,
     "description": "验收参数二：分页大小"},
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--i-have-write-authorization", action="store_true")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\param-seed")
    a = ap.parse_args()

    bodies = []
    for s in SAMPLES:
        b = build_parameter_body(APP_ID, APP_GUID, **s)
        errs = validate_parameter_body(b)
        print(f"[{s['caption']}] 本地校验: {errs or '✅ 通过'}")
        bodies.append({"body": b, "errors": errs})

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "plan.json").write_text(json.dumps(bodies, ensure_ascii=False, indent=1), encoding="utf-8")

    if not a.i_have_write_authorization:
        print(f"\n只构造未写入 -> {out/'plan.json'}")
        return 0
    if any(b["errors"] for b in bodies):
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
    for b in bodies:
        r = gql("udcCtpParameterDefinitonPost", b["body"])
        ok = r.get("code") == "BOOT_0000"
        rec = {"name": b["body"]["name"], "caption": b["body"]["caption"],
               "ok": ok, "id": (r.get("data") or {}).get("content") if ok else None,
               "resp": None if ok else r}
        results.append(rec)
        print(f"\n{'✅' if ok else '❌'} {b['body']['caption']}")
        if ok:
            print(f"   id={rec['id']}  name={rec['name']}  dataType={b['body']['dataType']}")
        else:
            print(f"   {json.dumps(r, ensure_ascii=False)[:200]}")
            break

    (out / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n结果 -> {out/'result.json'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
