"""应用内功能页被动抓包 + 只读点击导航（CDP）。

只做两件事：
  1) Network.enable 被动记录（不发任何业务请求）；
  2) 用 Runtime.evaluate 点击「左侧功能菜单 / 底部日志 tab」的文本节点，让页面自己去请求。

严禁点击：测试、检查/重新检查、发布、更多→发布类动作、清除应用数据、添加/移除依赖、移交应用。

用法：
  python tools/core/application/cdp_click_capture.py --port 9250 --match appId=8704... \
      --labels 页面测试 沙箱测试 发布版本 --seconds 4 --out <dir>
"""
from __future__ import annotations

import argparse
import json
import os
import time

import websocket

CLICK_JS = """
(() => {
  // 安全说明：本表达式由本脚本静态拼接，@@LABEL@@ 处只注入 json.dumps(label) 后的字符串字面量，
  // 不含任何来自网络的输入；不使用 eval/new Function，仅在页面里做 DOM 查找 + click。
  const want = @@LABEL@@;
  const all = [...document.querySelectorAll('*')].filter(e => {
    const t = (e.textContent || '').trim();
    if (t !== want) return false;
    if (e.children.length > 2) return false;
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) return false;
    return true;
  });
  if (!all.length) return 'NOT_FOUND';
  const el = all[all.length - 1];
  el.scrollIntoView({block: 'center'});
  el.click();
  return 'clicked:' + el.tagName + ':' + (el.className || '').toString().slice(0, 40);
})()
"""


class Sess:
    def __init__(self, ws_url: str):
        self.ws = websocket.create_connection(ws_url, timeout=60, max_size=None, suppress_origin=True)
        self.id = 0
        self.pending: dict[int, dict] = {}

    def send(self, method: str, params: dict | None = None) -> int:
        self.id += 1
        self.ws.send(json.dumps({"id": self.id, "method": method, "params": params or {}}))
        return self.id

    def drain(self, seconds: float) -> list[dict]:
        out, t0 = [], time.time()
        self.ws.settimeout(0.5)
        while time.time() - t0 < seconds:
            try:
                raw = self.ws.recv()
            except Exception:
                continue
            if not raw:
                continue
            m = json.loads(raw)
            if m.get("method") in ("Network.requestWillBeSent", "Network.responseReceived",
                                   "Network.loadingFailed"):
                out.append(m)
        return out

    def eval(self, expr: str, timeout: float = 20.0):
        mid = self.send("Runtime.evaluate",
                        {"expression": expr, "returnByValue": True, "awaitPromise": True})
        t0 = time.time()
        self.ws.settimeout(1.0)
        while time.time() - t0 < timeout:
            try:
                raw = self.ws.recv()
            except Exception:
                continue
            if not raw:
                continue
            m = json.loads(raw)
            if m.get("id") == mid:
                r = m.get("result", {}).get("result", {})
                return r.get("value", r.get("description"))
        return "TIMEOUT"


def pick_tab(port: int, match: str) -> dict:
    import urllib.request

    tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5))
    cands = [t for t in tabs if t.get("type") == "page" and match in (t.get("url") or "")]
    if not cands:
        raise SystemExit(f"no tab matching {match!r}")
    return cands[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9250)
    ap.add_argument("--match", required=True)
    ap.add_argument("--labels", nargs="+", required=True)
    ap.add_argument("--seconds", type=float, default=4.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    tab = pick_tab(args.port, args.match)
    s = Sess(tab["webSocketDebuggerUrl"])
    s.send("Network.enable", {"maxTotalBufferSize": 20000000, "maxPostDataSize": 2000000})
    s.drain(0.6)

    os.makedirs(args.out, exist_ok=True)
    report = {"tab_url": tab["url"], "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "labels": {}}

    for label in args.labels:
        clicked = s.eval(CLICK_JS.replace("@@LABEL@@", json.dumps(label, ensure_ascii=False)))
        events = s.drain(args.seconds)
        reqs: dict[str, dict] = {}
        fails = []
        for e in events:
            if e["method"] == "Network.requestWillBeSent":
                r = e["params"]["request"]
                url = r["url"]
                if "/service/" not in url and "/udc/" not in url:
                    continue
                reqs[url.split("?")[0] + "|" + r["method"]] = {
                    "method": r["method"],
                    "url": url.split("?")[0],
                    "query": url.split("?", 1)[1] if "?" in url else "",
                    "postData": (r.get("postData") or "")[:1500],
                    "type": e["params"].get("type"),
                }
            elif e["method"] == "Network.loadingFailed":
                fails.append(e["params"].get("errorText"))
        report["labels"][label] = {"click": clicked, "requests": list(reqs.values()),
                                   "failures": fails}
        print(f"--- {label}: {clicked} | reqs={len(reqs)} fails={len(fails)}")
        for r in reqs.values():
            print(f"    {r['method']:4s} {r['url'][:110]} {('body=' + r['postData'][:90]) if r['postData'] else ''}")

    path = os.path.join(args.out, "click-capture.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print("->", path)


if __name__ == "__main__":
    main()
