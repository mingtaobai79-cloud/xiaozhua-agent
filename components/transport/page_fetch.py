# -*- coding: utf-8 -*-
"""components/transport/page_fetch.py — 让浏览器自己发请求。

**为什么必须有这一层**

写类工具原来的签名是 `f(host, cookie, dto)`：调用方得把 cookie 字符串传进来。
但 session token 就是这个用户的身份 —— 导出它、在本地重放，等于把身份复制一份到
磁盘和进程内存里。红线是「通过 login 页面登录就行，不要自己获取 token」。

所以正确做法不是"少传点 cookie"，而是**根本不传**：请求由页面发出，
浏览器自己带 `credentials:'include'`，cookie 永远不离开浏览器进程。

**用在哪**

四个凭据工具（microflow_publish / expression_verify / expression_filter /
entity_rule_publish）以及后续所有需要真发请求的验证。

**怎么用**

```python
from components.transport.page_fetch import PageFetch
pf = PageFetch(9333, "lowcode-test2")        # 已登录的调试实例
r = pf.post("/service/udc/microflow/checkSchema", body)     # 相对路径，拼 origin
r = pf.post("/service/udc/graphql?udcXxxPost", {"query": q, "variables": v})
```

★ 只支持 POST（平台写链全是 POST）。需要 GET 再扩。
★ 拿不到页面就抛 PageUnavailable，不静默降级成"没网"。
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional


class PageUnavailable(RuntimeError):
    """调试端口上没有可用页面。"""


class PageFetch:
    def __init__(self, port: int = 9333, host_match: str = "lowcode-test2",
                 origin: str = "", timeout: int = 120):
        self.port = int(port)
        self.host_match = host_match
        self.origin = origin.rstrip("/")
        self.timeout = timeout
        self._ws = None
        self._id = 0
        self._page_url = ""
        self._connect()

    # ---------------- 连接 ----------------

    def _connect(self) -> None:
        import urllib.request

        try:
            import websocket  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise PageUnavailable(
                "需要 websocket-client（pip install websocket-client）: %s" % e)

        try:
            raw = urllib.request.urlopen(
                "http://127.0.0.1:%d/json/list" % self.port, timeout=10).read()
        except Exception as e:  # noqa: BLE001
            raise PageUnavailable(
                "调试端口 %d 不可达（浏览器没带 --remote-debugging-port 启动？）: %s"
                % (self.port, e))

        tabs = json.loads(raw)
        pages = [t for t in tabs
                 if t.get("type") == "page" and self.host_match in t.get("url", "")]
        # ★ 排除登录页：同一浏览器里常常既有 /login/ 又有真正的工作页。
        # 只按「含 host」取第一个，会正好挑中 /login/ —— 请求全部打到登录页，
        # 平台回 "Unknown type xxxInputBody"，看起来像类型名写错，其实压根没登录。
        work_pages = [t for t in pages if "/login" not in t.get("url", "")]
        if work_pages:
            pages = work_pages
        if not pages:
            raise PageUnavailable(
                "%d 上没找到含 %r 的页面；现有：%s"
                % (self.port, self.host_match,
                   [t.get("url", "")[:70] for t in tabs if t.get("type") == "page"]))

        page = pages[0]
        self._page_url = page["url"]
        if not self.origin:
            # 从页面 url 取 origin，比如 https://host/main/portal → https://host
            parts = self._page_url.split("/")
            if len(parts) >= 3:
                self.origin = "/".join(parts[:3])

        self._ws = websocket.create_connection(
            page["webSocketDebuggerUrl"], suppress_origin=True,
            max_size=64 * 1024 * 1024, timeout=self.timeout)

    # ---------------- 底层 ----------------

    def _call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        self._id += 1
        mid = self._id
        self._ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(self._ws.recv())
            if msg.get("id") == mid:
                return msg

    def _eval(self, expr: str) -> Any:
        r = self._call("Runtime.evaluate", {
            "expression": expr, "awaitPromise": True,
            "returnByValue": True, "timeout": self.timeout * 1000})
        res = r.get("result", {})
        if res.get("exceptionDetails"):
            return {"__error__": str(res["exceptionDetails"])[:800]}
        return res.get("result", {}).get("value")

    # ---------------- 对外的两个方法 ----------------

    def post(self, path: str, body: Any, *, limit: int = 200_000) -> Dict[str, Any]:
        """POST 到站点。path 可以是相对路径，也可以是完整 URL。

        返回 {status, len, body, json}；body 是截断后的文本，json 是解析结果（能解析才有）。
        """
        url = path if path.startswith("http") else self.origin + path
        payload = json.dumps(body, ensure_ascii=False)
        expr = (
            "fetch(%s, {method:'POST', credentials:'include',"
            "  headers:{'Content-Type':'application/json'}, body:%s})"
            "  .then(async r => { const t = await r.text();"
            "    return {status:r.status, len:t.length, body:t.slice(0,%d)}; })"
            "  .catch(e => ({status:-1, error:String(e)}))"
            % (json.dumps(url), json.dumps(payload, ensure_ascii=False), limit)
        )
        r = self._eval(expr)
        if not isinstance(r, dict):
            return {"status": -1, "error": "unexpected CDP reply: %r" % (r,)}
        if "body" in r:
            try:
                r["json"] = json.loads(r["body"])
            except ValueError:
                pass
        return r

    def close(self) -> None:
        try:
            if self._ws:
                self._ws.close()
        except Exception:  # noqa: BLE001
            pass

    # ---------------- 便捷属性 ----------------

    @property
    def page_url(self) -> str:
        return self._page_url
