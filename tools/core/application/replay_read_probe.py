"""应用内功能页只读面重放探针。

思路：先用 cdp_click_capture.py 把「点击左侧功能菜单 / 底部日志 tab」产生的请求录成 plan，
再在这里按原样重放（只重放 query 类，遇 mutation 一律跳过），从而拿到后端真实回包形状。

为什么不在页面里重放：设计器页 window.fetch 打 /service/ 会被网关断链
（net::ERR_CONNECTION_CLOSED），但 Python 直发正常。cookie 走 CDP 临时取用，不落盘。

用法：
  python tools/core/application/replay_read_probe.py --port 9250 \
      --base https://<gateway-host> --plan <plan.json> --out <out.json> \
      --app-name <appCode> --app-id <appId>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gateway_readonly_probe as gw  # noqa: E402

# 日志面（推断 + 已验证）统一入口：/service/{appName}/udc-runtime/app-log/search/{kind}
# dataflow / deduction 由页面实测录得；design / microflow 为同类推导，用于探明命名规则
APP_LOG_KINDS = ("dataflow", "deduction", "design", "microflow", "page", "bizrule")


def applog_body(app_name: str, app_id: str, kind: str) -> dict:
    return {"params": {"appName": app_name, "appId": app_id, "logType": kind},
            "pageInfo": {"pageNumber": 1, "pageSize": 10, "needTotal": True, "total": 0}}


def graphql_call(cookie: str, path: str, body: dict, timeout: float = 25.0) -> dict:
    """GraphQL 不走 {code,data.content} 信封，单独取原始 JSON 判读。"""
    import urllib.error
    import urllib.request

    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(gw.BASE + path, data=data, method="POST",
                                 headers={"Cookie": cookie, "Content-Type": "application/json",
                                          "Accept": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw, status = r.read(), r.status
    except urllib.error.HTTPError as e:
        raw, status = e.read(), e.code
    except Exception as e:
        return {"http": None, "verdict": "NETWORK_ERROR",
                "error": type(e).__name__ + ":" + str(e)[:120], "ms": int((time.time() - t0) * 1000)}
    ms = int((time.time() - t0) * 1000)
    text = raw.decode("utf-8", "replace")
    try:
        env = json.loads(text)
    except Exception:
        return {"http": status, "verdict": "NON_JSON", "bytes": len(raw), "ms": ms,
                "content_head": text[:200]}
    if env.get("errors"):
        return {"http": status, "verdict": "GQL_ERRORS", "ms": ms, "bytes": len(raw),
                "content_head": json.dumps(env["errors"], ensure_ascii=False)[:400]}
    data_part = env.get("data") or {}
    keys = list(data_part.keys())
    return {"http": status, "verdict": "LIVE_PASS" if (status == 200 and keys) else "FAIL",
            "ms": ms, "bytes": len(raw), "content_type": "graphql",
            "content_size": len(keys), "content_head": json.dumps(data_part, ensure_ascii=False)[:400],
            "gql_keys": keys}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9250)
    ap.add_argument("--base", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--app-name", default="")
    ap.add_argument("--app-id", default="")
    ap.add_argument("--with-applog", action="store_true", help="附带 app-log/search/* 探明")
    args = ap.parse_args()

    gw.BASE = args.base.rstrip("/")
    plan = json.load(open(args.plan, encoding="utf-8"))
    cookie = gw.session_cookies(args.port)
    print("cookies loaded (names only):", [c.split("=")[0] for c in cookie.split("; ")])

    ops: list[dict] = []
    seen: set[str] = set()
    for label, items in plan.items():
        for it in items:
            pd = it.get("postData") or ""
            if "mutation " in pd:
                ops.append({"label": label, "method": it["method"], "url": it["url"],
                            "skipped": "MUTATION_NOT_REPLAYED"})
                continue
            key = it["method"] + " " + it["url"]
            if key in seen:
                continue
            seen.add(key)
            ops.append({"label": label, "method": it["method"], "url": it["url"], "postData": pd})

    if args.with_applog and args.app_name:
        for kind in APP_LOG_KINDS:
            ops.append({"label": "app-log/" + kind, "method": "POST",
                        "url": f"/service/{args.app_name}/udc-runtime/app-log/search/{kind}",
                        "postData": json.dumps(applog_body(args.app_name, args.app_id, kind),
                                               ensure_ascii=False),
                        "derived": kind not in ("dataflow", "deduction")})

    rows = []
    for op in ops:
        if "skipped" in op:
            rows.append({**op, "verdict": "SKIPPED"})
            print(f"  {'SKIPPED':14s} {op['method']:4s} {op['url'][:80]}")
            continue
        path = op["url"]
        if path.startswith(gw.BASE):
            path = path[len(gw.BASE):]
        body = None
        if op.get("postData"):
            try:
                body = json.loads(op["postData"])
            except Exception:
                body = None
        if "/graphql" in path:
            res = graphql_call(cookie, path, body or {})
        else:
            res = gw.call(cookie, op["method"], path, body)
        verdict = res.pop("verdict", None) or gw.verdict_of(res)
        if verdict == "CALLED_NO_DATA" and body is not None:
            verdict = "CALLED_EMPTY"  # 查询成功但结果集为空（示例应用无日志，属正常）
        res.update({"label": op["label"], "method": op["method"], "path": path,
                    "body_head": (op.get("postData") or "")[:300], "verdict": verdict,
                    "derived": op.get("derived", False)})
        rows.append(res)
        print(f"  {verdict:14s} {res.get('http')} {op['method']:4s} {path[:74]} "
              f"code={res.get('code')} ct={res.get('content_type')} n={res.get('content_size')}")

    summary: dict[str, int] = {}
    for r in rows:
        summary[r["verdict"]] = summary.get(r["verdict"], 0) + 1
    doc = {"captured_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "base": gw.BASE,
           "auth": "browser session cookie (not persisted)", "summary": summary, "probes": rows}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print("summary:", summary, "->", args.out)


if __name__ == "__main__":
    main()
