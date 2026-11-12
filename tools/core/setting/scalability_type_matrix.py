"""设置域 · 扩展实体：预留组的类型 × 配置矩阵实测。

用户要求：先把字段集测完，再测扩展实体。
预留组比字段集简单（只有 dataType / prefix / count / dataTypeProperties），
所以这里测「哪些 dataType 平台接受」+「dataTypeProperties 的结构」。

用法：
  python tools/core/setting/scalability_type_matrix.py --list
  python tools/core/setting/scalability_type_matrix.py --run \
      --option-id <方案id> --i-have-write-authorization
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from components.udc.setting.scalability_constraints import (  # noqa: E402
    build_scalability_group_body, validate_scalability_group_body,
)

# 页面上「字段类型」下拉通常只给基础类型（扩展实体是预留物理字段，
# 关联型/自定义型语义上不适用）
CANDIDATE_TYPES = (
    "STRING", "MULTILINESTRING", "INTEGER", "BIGINTEGER", "DECIMAL",
    "CURRENCY", "DATE", "TIME", "DATETIME", "BOOLEAN",
)

# dataTypeProperties 按类型的合理取值（字符串化 JSON）
TYPE_PROPS = {
    "STRING": '{"minLength":"0","maxLength":50}',
    "MULTILINESTRING": '{"minLength":"0","maxLength":2000}',
    "INTEGER": '{"min":"0","max":"9999"}',
    "BIGINTEGER": '{"min":"0","max":"999999"}',
    "DECIMAL": '{"min":"0","max":"99999","decimalDigits":"2"}',
    "CURRENCY": '{"min":"0","max":"999999","decimalDigits":"2"}',
    "DATE": "{}",
    "TIME": "{}",
    "DATETIME": "{}",
    "BOOLEAN": "{}",
}


def call_gql(c, op, body):
    q = ("mutation graphqlLoader ($params0: %sInputBody) { \n"
         "  data0: %s(body: $params0) { code message status data { content } } }" % (op, op))
    payload = {"query": q, "variables": {"params0": body}}
    js = ("(async()=>{const r=await fetch('/service/udc/graphql?%s',{method:'POST',credentials:'include',"
          "headers:{'Content-Type':'application/json'},body:%s});return await r.text();})()"
          % (op, json.dumps(json.dumps(payload, ensure_ascii=False))))
    return json.loads(c.evaluate(js, await_promise=True))["data"]["data0"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--app-id", default=None)
    ap.add_argument("--option-id", default="")
    ap.add_argument("--prefix", default="sx")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\scal-matrix")
    a = ap.parse_args()

    if a.list or not a.run:
        print(f"候选 dataType（{len(CANDIDATE_TYPES)} 种）与 dataTypeProperties：\n")
        for t in CANDIDATE_TYPES:
            print(f"  {t:<16} {TYPE_PROPS.get(t, '{}')}")
        if not a.run:
            return 0

    if not a.option_id:
        print("--run 需要 --option-id <方案 id>")
        return 2
    if not a.i_have_write_authorization:
        print("写操作需显式确认：加 --i-have-write-authorization")
        return 1

    import urllib.request
    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    pages = [t for t in tgts if t.get("type") == "page"
             and f"appId={a.app_id}" in t.get("url", "")]
    if not pages:
        pages = [t for t in tgts if t.get("type") == "page" and "lowcode-test2" in t.get("url", "")]
    from providers.cdp import CdpClient
    c = CdpClient(a.port, allow_network=True, timeout=120)
    c.connect(target=pages[0])

    results = []
    for i, tname in enumerate(CANDIDATE_TYPES, 1):
        prefix = f"{a.prefix}{i:02d}{tname[:6].lower()}"
        body = build_scalability_group_body(
            a.option_id, app_id=a.app_id, prefix=prefix,
            caption=f"{tname}类型",
            count=a.count,
            data_type=tname,
            data_type_properties=TYPE_PROPS.get(tname, "{}"))
        errs = validate_scalability_group_body(body, option_id=a.option_id)
        if errs:
            print(f"  {tname:<16} 本地校验: {errs[:1]}")
            results.append({"type": tname, "ok": False, "errors": errs})
            continue
        r = call_gql(c, "udcScalabilityPost", body)
        ok = r.get("code") == "BOOT_0000"
        print(f"  {i:>2}. {tname:<16} {'✅' if ok else '❌'} {r.get('code')} "
              f"{str((r.get('data') or {}).get('content') or r.get('message'))[:46]}")
        results.append({"type": tname, "ok": ok, "prefix": prefix,
                        "id": (r.get("data") or {}).get("content") if ok else None,
                        **({} if ok else {"resp": r})})

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    print(f"\n成功 {sum(1 for x in results if x['ok'])}/{len(results)}  -> {out/'result.json'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
