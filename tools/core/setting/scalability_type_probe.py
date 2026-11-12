"""B-2 实证：扩展实体到底支不支持关联型/自定义型（旧结论说只 10 种基础型）。

平台元数据 data-type 端点返回 18 种且全部 validate=true，
但元数据 ≠ 能写。必须逐个实发 udcScalabilityPost 验证。

本脚本只建预留组（写 udc_scalability 一行），不改实体结构，可逆。

用法：
  python tools/core/setting/scalability_type_probe.py --list
  python tools/core/setting/scalability_type_probe.py --run \
      --app-id <appId> --option-id <方案id> --i-have-write-authorization
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

# 旧结论说「不适用」的 8 种（关联型 + 业务自定义型）
DISPUTED = ["CTPENUM", "ENUM", "ATTACHMENT", "ENTITY",
            "DOCUMENTNUMBER", "Serial", "OPINION", "CONTENT"]
# 旧结论认可、已实测通过的 10 种基础型
BASELINE = ["STRING", "MULTILINESTRING", "INTEGER", "BIGINTEGER", "DECIMAL",
            "CURRENCY", "DATE", "TIME", "DATETIME", "BOOLEAN"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9250)
    ap.add_argument("--target-prefix", default="13AF8487")
    ap.add_argument("--app-id", default=None)
    ap.add_argument("--option-id", default=None)
    ap.add_argument("--port-set", default=None, help="会话探测用字段集 id")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    a = ap.parse_args()

    if a.list or not a.run:
        print("扩展实体类型探针：验证旧结论「只支持 10 种基础类型」是否成立\n")
        print(f"  基线（已实测通过）{len(BASELINE)} 种: {', '.join(BASELINE)}")
        print(f"  争议（旧结论说不支持）{len(DISPUTED)} 种: {', '.join(DISPUTED)}")
        if not a.run:
            return 0

    if not (a.app_id and a.option_id):
        print("必须给 --app-id 和 --option-id")
        return 1
    if not a.i_have_write_authorization:
        print("写操作需显式确认：--i-have-write-authorization")
        return 1

    import time
    import urllib.request
    from providers.cdp import CdpClient

    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    cand = [t for t in tgts if t.get("type") == "page"
            and str(t.get("id", "")).startswith(a.target_prefix)]
    if not cand:
        print(f"找不到 {a.target_prefix}")
        return 2
    c = CdpClient(a.port, allow_network=True, timeout=120)
    c.connect(target=cand[0])

    def gql(op, body, to=30):
        q = ("mutation graphqlLoader ($params0: %sInputBody) { "
             "  data0: %s(body: $params0) { code message status data { content } } }"
             % (op, op))
        js = (f"fetch('/service/udc/graphql?{op}',{{method:'POST',credentials:'include',"
              "headers:{'Content-Type':'application/json'},"
              f"body:{json.dumps(json.dumps({'query': q, 'variables': {'params0': body}}, ensure_ascii=False))}}})"
              ".then(r=>r.text())")
        try:
            return json.loads(c.evaluate(js, await_promise=True))
        except Exception as e:
            return {"err": type(e).__name__}

    results = []
    for i, dt in enumerate(DISPUTED, start=1):
        prefix = f"ztd{i:02d}"          # ≤20 字
        body = {
            "appId": a.app_id, "optionId": a.option_id,
            "caption": f"{dt}测试", "prefix": prefix, "count": 1,
            "dataType": dt,
            "dataTypeProperties": "{}",
            "publishState": 1,
        }
        r = gql("udcScalabilityPost", body)
        d0 = (r.get("data") or {}).get("data0") or {}
        code = d0.get("code") or r.get("err")
        ok = code == "BOOT_0000"
        print(f"  {dt:<16} {'PASS' if ok else 'FAIL'}  {code}  {str(d0.get('message'))[:40]}")
        results.append({"dataType": dt, "ok": ok, "code": code,
                        "msg": str(d0.get("message"))[:80]})
        time.sleep(0.4)

    p = Path(r"<HERMES_HOME>\cache\scratch\scalability-probe")
    p.mkdir(parents=True, exist_ok=True)
    (p / "type-probe.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")

    passed = [r["dataType"] for r in results if r["ok"]]
    failed = [r["dataType"] for r in results if not r["ok"]]
    print(f"\n可写 {len(passed)}/{len(DISPUTED)}: {passed}")
    print(f"不可写: {failed}")
    print(f"-> {p / 'type-probe.json'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
