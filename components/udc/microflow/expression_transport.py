"""表达式接口传输层：两种后端，统一 .check(dto) / .transform(dto) 契约。

## 为什么需要两种

1. **CurlBackend（默认）** —— 直发 HTTP。
   ★ 本环境网关对 Python urllib 的 TLS 指纹回 `SSL: UNEXPECTED_EOF_WHILE_READING`
   （HTTP/1.1 + OpenSSL 指纹被拒），curl（HTTP/2）正常。
   实测 2026-11-01：同一 DTO、同一 cookie，urllib 两次全 EOF，curl `BOOT_0000`。
   改 UA 无效 → 是 TLS/ALPN 层，不是 header 层。

2. **PageBackend** —— 走浏览器页面内 fetch（CDP Runtime.evaluate + awaitPromise）。
   仅当 curl 不可用或需要页面上下文时用。★ 后台 tab 会被节流，
   `awaitPromise` 可能永不 resolve（实测挂死 300s），必须在激活 tab 上用。

统一返回 {'ok','code','message','content','status','raw'}，
ok = code==BOOT_0000（check 还要求 content is True）。
"""
from __future__ import annotations

import json
import subprocess


class TransportError(RuntimeError):
    pass


def _verdict(code, message, content, status=None, raw=None, need_content_true=False):
    ok = code == "BOOT_0000"
    if need_content_true:
        ok = ok and content is True
    return {"ok": ok, "code": code, "message": message, "content": content,
            "status": status, "raw": raw}


class CurlBackend:
    """curl 直发（本环境唯一稳定的 HTTP 通路）。"""

    def __init__(self, host: str, cookie: str, timeout: int = 60,
                 prefix: str = "/service/udc/expression"):
        if not host or not cookie:
            raise ValueError("CurlBackend 需要 host 与 cookie")
        self.host = host.rstrip("/")
        self.cookie = cookie
        self.timeout = timeout
        self.prefix = prefix

    def _post(self, path: str, body: dict) -> dict:
        cmd = ["curl", "-sS", "--max-time", str(self.timeout), "-X", "POST",
               self.host + self.prefix + path,
               "-H", "Content-Type: application/json",
               "-H", "Cookie: " + self.cookie,
               "--data-binary", "@-"]
        p = subprocess.run(cmd, input=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                           capture_output=True, timeout=self.timeout + 15)
        out = (p.stdout or b"").decode("utf-8", "replace")
        if p.returncode != 0:
            raise TransportError("curl 退出码 %s: %s"
                                 % (p.returncode, (p.stderr or b"").decode("utf-8", "replace")[:300]))
        try:
            return json.loads(out)
        except Exception:
            raise TransportError("响应非 JSON: %s" % out[:300])

    def check(self, dto: dict) -> dict:
        j = self._post("/check", dto)
        d = (j.get("data") or {})
        return _verdict(j.get("code"), j.get("message"), d.get("content"),
                        raw=json.dumps(j, ensure_ascii=False)[:400], need_content_true=True)

    def transform(self, dto: dict) -> dict:
        j = self._post("/transform", dto)
        d = (j.get("data") or {})
        content = d.get("content")
        v = _verdict(j.get("code"), j.get("message"), content,
                     raw=json.dumps(j, ensure_ascii=False)[:400])
        if isinstance(content, dict):
            v["executableExpr"] = (content.get("runtimeData") or {}).get("executableExpr") or ""
            v["designData"] = content.get("designData")
        return v


class PageBackend:
    """页面内 fetch（需已 connect 的 cdp.Driver）。"""

    _JS = r"""(async () => {
  const r = await fetch(%(url)s, {method:'POST',
    headers:{'Content-Type':'application/json'}, body: %(body)s});
  const t = await r.text();
  return JSON.stringify({status: r.status, raw: t.slice(0, 4000)});
})()"""

    def __init__(self, driver, prefix: str = "/service/udc/expression"):
        self.d = driver
        self.prefix = prefix

    def _post(self, path: str, body: dict) -> dict:
        js = self._JS % {"url": json.dumps(self.prefix + path),
                         "body": json.dumps(json.dumps(body, ensure_ascii=False))}
        raw = self.d.eval(js, await_promise=True)
        if not isinstance(raw, str):
            raise TransportError("页面 eval 无返回: %r" % (raw,))
        env = json.loads(raw)
        return json.loads(env.get("raw") or "{}")

    def check(self, dto: dict) -> dict:
        j = self._post("/check", dto)
        return _verdict(j.get("code"), j.get("message"), (j.get("data") or {}).get("content"),
                        need_content_true=True)

    def transform(self, dto: dict) -> dict:
        j = self._post("/transform", dto)
        content = (j.get("data") or {}).get("content")
        v = _verdict(j.get("code"), j.get("message"), content)
        if isinstance(content, dict):
            v["executableExpr"] = (content.get("runtimeData") or {}).get("executableExpr") or ""
            v["designData"] = content.get("designData")
        return v
