"""CDP Network 抓包器（通用，读面/写面均可抓；只抓不发）。

用途：在已登录的真实浏览器页面上，记录「页面自己发出去」的全部请求，
      得到 method / url / postData / status / mimeType / 响应字节数。
      用于把前端真实调用（含 GraphQL operationName 与全量 query 文本）落成证据。

纪律：
  * 本脚本自身**不发起任何业务请求**，只被动监听；--reload 会重载页面（页面自己重放读面请求）。
  * 不对接网关凭据，不在页面上下文注入 fetch，不写 cookie。
  * 输出文件禁止含 cookie/token（CDP 事件里本就不含）。

用法：
  python tools/core/application/cdp_net_capture.py --match basic-setting --reload \
      --out <HERMES_HOME>/cache/scratch/app-design/net-basic-setting.json
"""
from __future__ import annotations

import argparse
import json
import threading
import time
import urllib.request

import websocket


def pick_tab(port: int, match: str) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5) as r:
        tabs = json.loads(r.read().decode("utf-8"))
    pages = [t for t in tabs if t.get("type") == "page"]
    hit = [t for t in pages if match in (t.get("url") or "")]
    if not hit:
        raise SystemExit(
            "no tab matching %r; pages=%s" % (match, [p.get("url", "")[:90] for p in pages])
        )
    return hit[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9250)
    ap.add_argument("--match", required=True, help="URL 子串，选中目标 tab")
    ap.add_argument("--out", required=True)
    ap.add_argument("--reload", action="store_true")
    ap.add_argument("--seconds", type=float, default=25.0)
    args = ap.parse_args()

    tab = pick_tab(args.port, args.match)
    print("tab:", tab["id"][:10], tab["url"][:110])

    ws = websocket.create_connection(
        tab["webSocketDebuggerUrl"], timeout=60, max_size=None, suppress_origin=True
    )
    mid = [0]

    def send(method: str, **params) -> None:
        mid[0] += 1
        ws.send(json.dumps({"id": mid[0], "method": method, "params": params}))

    send("Network.enable")
    send("Page.enable")
    time.sleep(0.4)
    if args.reload:
        send("Page.reload", ignoreCache=False)
        print("reload issued")

    reqs: dict[str, dict] = {}
    order: list[str] = []
    stop = time.time() + args.seconds
    ws.settimeout(1.0)
    while time.time() < stop:
        try:
            raw = ws.recv()
        except Exception:
            continue
        if not raw:
            continue
        try:
            msg = json.loads(raw)
        except Exception:
            continue
        m = msg.get("method")
        p = msg.get("params") or {}
        if m == "Network.requestWillBeSent":
            rid = p["requestId"]
            r = p["request"]
            url = r.get("url", "")
            if not url.startswith("http"):
                continue
            if rid not in reqs:
                order.append(rid)
                reqs[rid] = {
                    "method": r.get("method"),
                    "url": url,
                    "type": p.get("type"),
                    "postData": r.get("postData"),
                    "status": None,
                    "mimeType": None,
                    "bytes": None,
                    "failed": None,
                }
        elif m == "Network.responseReceived":
            it = reqs.get(p.get("requestId"))
            if it:
                resp = p.get("response") or {}
                it["status"] = resp.get("status")
                it["mimeType"] = resp.get("mimeType")
        elif m == "Network.loadingFinished":
            it = reqs.get(p.get("requestId"))
            if it:
                it["bytes"] = p.get("encodedDataLength")
        elif m == "Network.loadingFailed":
            it = reqs.get(p.get("requestId"))
            if it:
                it["failed"] = p.get("errorText")
    ws.close()

    items = [reqs[r] for r in order]
    api = [
        it
        for it in items
        if "/service/" in it["url"] or "/api/" in it["url"]
    ]
    out = {
        "port": args.port,
        "tab_url": tab["url"],
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "reloaded": args.reload,
        "seconds": args.seconds,
        "total_requests": len(items),
        "api_requests": api,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print(f"total={len(items)} api={len(api)} -> {args.out}")
    for it in api:
        body = " json" if it["postData"] else ""
        print(f"  {it['status']} {it['method']:5s} {it['url'][:150]}{body}")


if __name__ == "__main__":
    main()
