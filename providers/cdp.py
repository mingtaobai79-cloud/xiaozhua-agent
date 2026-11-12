"""Minimal CDP client for driving the xiaozhua low-code designer.

xiaozhua-agent 原来完全没有浏览器能力（全仓库 0 处 ``webSocketDebuggerUrl``），
所以"页面点击"类验证只能靠一次性脚本，无法被 agent 自己复现。本模块补上这一层。

设计边界（与仓库既有 provider 约定一致）：
  - **只连本机回环端口**，不连远程调试端点。
  - 不做登录、不注入 cookie、不读 token —— 会话由人在页面上建立，
    agent 只操作"已经登录好的那个标签页"。
  - 每个动作返回可复算证据：操作前后的 DOM 快照摘要、请求/响应捕获。
  - 默认 ``allow_network=False``：不显式开启则拒绝任何网络动作（保持仓库 fail-closed）。

实测环境（本机 Edge 155）：
  - ``Network`` 域不可用（``Network.enable`` / ``setCookie`` 全 -32601），
    只有 ``Storage`` 域可用 → 抓包用 ``Storage`` + 页面内 fetch 拦截，不用 Network 域。
  - ``Runtime.enable`` 在部分 target 上不可用，但 ``Runtime.evaluate`` 可用。
  - websocket 握手必须去掉 Origin 头（``suppress_origin=True``），
    否则 403（需 ``--remote-allow-origins``）。
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any
from urllib.parse import urlparse


class CdpError(Exception):
    """CDP 层错误（端口不可达、target 缺失、求值失败）。"""

    def __init__(self, kind: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.details = details or {}


def _http_get_json(url: str, timeout: float = 5.0) -> Any:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


class CdpClient:
    """一个 target（标签页）上的 CDP 会话。

    用法::

        client = CdpClient(9230, allow_network=True)
        client.connect(url_substr="/main/portal")
        client.evaluate("document.title")
        client.navigate("https://.../app-design/...")
        client.close()
    """

    def __init__(self, port: int = 9222, *, allow_network: bool = False,
                 host: str = "127.0.0.1", timeout: float = 30.0):
        self.port = port
        self.host = host
        self.allow_network = allow_network
        self.timeout = timeout
        self._ws = None
        self._id = 0
        self._target: dict[str, Any] | None = None

    # ---------------------------------------------------------------- 端口与 target
    @property
    def base(self) -> str:
        return f"http://{self.host}:{self.port}"

    def version(self) -> dict[str, Any]:
        try:
            return _http_get_json(f"{self.base}/json/version")
        except Exception as exc:
            raise CdpError("unavailable", f"CDP 端口 {self.port} 不可达",
                           {"port": self.port, "exception": type(exc).__name__}) from exc

    def list_pages(self) -> list[dict[str, Any]]:
        targets = _http_get_json(f"{self.base}/json/list")
        return [t for t in targets if t.get("type") == "page"]

    def find_page(self, url_substr: str = "") -> dict[str, Any]:
        pages = self.list_pages()
        if not pages:
            raise CdpError("not_found", "没有 page target", {"port": self.port})
        if not url_substr:
            return pages[0]
        for p in pages:
            if url_substr in p.get("url", ""):
                return p
        raise CdpError("not_found", f"没有 URL 含 {url_substr!r} 的标签页",
                       {"pages": [p.get("url") for p in pages]})

    # ---------------------------------------------------------------- 连接
    def connect(self, url_substr: str = "", *, target: dict | None = None) -> dict[str, Any]:
        """连到指定标签页。``url_substr`` 为空则取第一个 page。"""
        if self._ws is not None:
            self.close()
        tgt = target or self.find_page(url_substr)
        ws_url = tgt.get("webSocketDebuggerUrl")
        if not ws_url:
            raise CdpError("unavailable", "target 无 webSocketDebuggerUrl", {"target": tgt})
        try:
            from websocket import create_connection
        except ImportError as exc:
            raise CdpError("unavailable", "websocket-client 未安装",
                           {"exception": repr(exc)}) from exc
        self._ws = create_connection(ws_url, timeout=self.timeout, suppress_origin=True)
        self._target = tgt
        self._id = 0
        return tgt

    def close(self) -> None:
        if self._ws is not None:
            try:
                self._ws.close()
            except Exception:
                pass
        self._ws = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
        return False

    # ---------------------------------------------------------------- 命令
    def send(self, method: str, **params) -> dict[str, Any]:
        if self._ws is None:
            raise CdpError("unavailable", "未连接（先调用 connect()）")
        self._id += 1
        mid = self._id
        self._ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            msg = json.loads(self._ws.recv())
            if msg.get("id") == mid:
                if "error" in msg:
                    raise CdpError("cdp_error",
                                   f"{method} 失败: {msg['error'].get('message')}",
                                   {"method": method, "error": msg["error"]})
                return msg.get("result", {})

    def evaluate(self, expression: str, *, await_promise: bool = False) -> Any:
        """在页面上下文求值，返回 JSON 化的值。

        ``Runtime.enable`` 在部分 target 上不可用，故不预先 enable —— 直接 evaluate
        在本机 Edge 155 上可正常工作。
        """
        res = self.send("Runtime.evaluate",
                        expression=expression,
                        returnByValue=True,
                        awaitPromise=await_promise)
        if "exceptionDetails" in res:
            det = res["exceptionDetails"]
            raise CdpError("evaluate_error",
                           str(det.get("text") or det.get("exception", {}).get("description"))[:300],
                           {"expression": expression[:200]})
        return res.get("result", {}).get("value")

    # ---------------------------------------------------------------- 页面动作
    def navigate(self, url: str, *, settle_seconds: float = 8.0) -> dict[str, Any]:
        """导航并等待。返回导航后的 URL / readyState / 文本长度。

        用 ``location.href`` 而非 ``Page.navigate``：后者在本机 Edge 的某些 target 上
        会超时不返回，前者虽然会让 websocket 断开，但页面跳转是真实发生的。
        """
        if not self.allow_network:
            raise CdpError("permission", "allow_network=False，拒绝导航",
                           {"allow_network": False})
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise CdpError("permission", f"只允许 http/https，实际 {parsed.scheme!r}")
        try:
            self.send("Runtime.evaluate",
                      expression=f"setTimeout(()=>{{location.href={json.dumps(url)}}},60); 'scheduled'",
                      returnByValue=True)
        except CdpError:
            pass  # 跳转导致连接中断属预期
        import time
        time.sleep(settle_seconds)
        self.close()
        # 重新连到（可能已换 URL 的）标签页。
        # ⚠ 不能盲取 pages[0]：Edge 首次启动会有 edge://sync-confirmation-dialog 这类
        #   内部 target 排在前面，连上去会拿到错误页面（实测导致 navigate 后
        #   page_state 报 edge:// 域名）。优先选与目标同源/同前缀的 target。
        pages = self.list_pages()
        if not pages:
            raise CdpError("not_found", "导航后无 page target")
        origin = f"{parsed.scheme}://{parsed.netloc}"
        same_origin = [p for p in pages
                       if p.get("url", "").startswith(origin)]
        pick = same_origin[0] if same_origin else next(
            (p for p in pages if p.get("url", "").startswith("http")), pages[0])
        self.connect(target=pick)
        return self.page_state()

    def page_state(self) -> dict[str, Any]:
        """当前页面状态摘要（每次验证都带上这个，便于复算）。"""
        return self.evaluate("""(() => ({
          url: location.href,
          ready: document.readyState,
          title: document.title,
          textLen: document.body ? (document.body.innerText || '').length : -1,
          head: document.body ? (document.body.innerText || '').slice(0, 240) : ''
        }))()""")

    # ---------------------------------------------------------------- 元素操作
    def find_inputs(self) -> list[dict[str, Any]]:
        """列出页面输入控件（id/type/placeholder/当前值）。"""
        return self.evaluate("""(() => [...document.querySelectorAll('input,textarea,select')]
          .map((el, i) => ({i, tag: el.tagName, type: el.type || '',
                            id: el.id || '', name: el.name || '',
                            ph: el.placeholder || '',
                            cls: String(el.className || '').slice(0, 60),
                            value: String(el.value ?? '').slice(0, 60)})))()""")

    def find_buttons(self, limit: int = 40) -> list[dict[str, Any]]:
        """列出可点击按钮（文本/类名/可见性）。"""
        return self.evaluate("""(() => [...document.querySelectorAll('button,[role=button],.ant-btn,a')]
          .map((el, i) => ({i, tag: el.tagName,
                            txt: (el.innerText || '').trim().slice(0, 24),
                            cls: String(el.className || '').slice(0, 60),
                            visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)}))
          .filter(b => b.txt && b.visible))()""")[:limit]

    def set_input(self, selector: str, value: str) -> dict[str, Any]:
        """用原生 setter + input/change 事件填值（绕过 React 受控组件）。

        先清空再输入：直接赋值到已有默认值的输入框会产生拼接
        （历史事故：'字1' + 输入 → '字1xx'）。
        """
        expr = f"""(() => {{
          const el = document.querySelector({json.dumps(selector)});
          if (!el) return {{ok: false, reason: 'selector not found'}};
          const desc = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el), 'value');
          const set = (v) => {{
            if (desc && desc.set) desc.set.call(el, v); else el.value = v;
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
          }};
          el.focus(); set(''); set({json.dumps(value)});
          return {{ok: el.value === {json.dumps(value)}, actual: el.value}};
        }})()"""
        out = self.evaluate(expr)
        if not out or not out.get("ok"):
            raise CdpError("action_failed", f"填值失败: {selector}",
                           {"result": out, "expected": value})
        return out

    def click(self, selector: str, *, require_visible: bool = True) -> dict[str, Any]:
        """点击元素（DOM click）。返回点击后是否元素仍在、元素文本。"""
        expr = f"""(() => {{
          const el = document.querySelector({json.dumps(selector)});
          if (!el) return {{ok: false, reason: 'selector not found'}};
          const vis = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
          if ({str(require_visible).lower()} && !vis) return {{ok: false, reason: 'not visible'}};
          const txt = (el.innerText || '').trim().slice(0, 40);
          el.click();
          return {{ok: true, txt}};
        }})()"""
        out = self.evaluate(expr)
        if not out or not out.get("ok"):
            raise CdpError("action_failed", f"点击失败: {selector}", {"result": out})
        return out

    def click_by_text(self, text: str, *, tag: str = "button") -> dict[str, Any]:
        """按可见文本点击（优先精确匹配，其次包含）。"""
        expr = f"""(() => {{
          const want = {json.dumps(text)};
          const cands = [...document.querySelectorAll({json.dumps(tag + ',[role=button],.ant-btn,a')})];
          const exact = cands.find(el => (el.innerText || '').trim() === want);
          const partial = cands.find(el => (el.innerText || '').trim().includes(want));
          const el = exact || partial;
          if (!el) return {{ok: false, reason: 'no button with that text',
                            available: cands.map(c => (c.innerText||'').trim()).filter(Boolean).slice(0, 20)}};
          const vis = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
          if (!vis) return {{ok: false, reason: 'matched but not visible'}};
          el.click();
          return {{ok: true, txt: (el.innerText || '').trim().slice(0, 40), matched: !!exact}};
        }})()"""
        out = self.evaluate(expr)
        if not out or not out.get("ok"):
            raise CdpError("action_failed", f"按文本点击失败: {text}", {"result": out})
        return out

    # ---------------------------------------------------------------- 请求捕获
    def install_fetch_recorder(self) -> dict[str, Any]:
        """在页面装 fetch/XHR 记录器（Network 域不可用时的替代）。

        记录最近 50 条请求的 method/url/status/请求体(截断)/响应体(截断)，
        供后续 read_captured 取用。**不修改请求内容**，只旁观。
        """
        expr = """(() => {
          if (window.__CDP_CAP__) return {already: true};
          const cap = [];
          window.__CDP_CAP__ = cap;
          const origFetch = window.fetch;
          window.fetch = async function(...args) {
            const rec = {kind: 'fetch', ts: Date.now(), url: '', method: 'GET', reqBody: null};
            try {
              const input = args[0];
              rec.url = typeof input === 'string' ? input : (input && input.url) || '';
              rec.method = (args[1] && args[1].method) || (input && input.method) || 'GET';
              const b = args[1] && args[1].body;
              if (b) rec.reqBody = String(b).slice(0, 4000);
            } catch (e) {}
            try {
              const resp = await origFetch.apply(this, args);
              try {
                const clone = resp.clone();
                const txt = await clone.text();
                rec.status = resp.status;
                rec.respBody = txt.slice(0, 6000);
              } catch (e) { rec.status = resp.status; }
              return resp;
            } catch (e) {
              rec.error = String(e).slice(0, 200);
              throw e;
            } finally {
              cap.push(rec);
              if (cap.length > 50) cap.shift();
            }
          };
          const origOpen = XMLHttpRequest.prototype.open;
          const origSend = XMLHttpRequest.prototype.send;
          XMLHttpRequest.prototype.open = function(method, url, ...rest) {
            this.__cap = {kind: 'xhr', ts: Date.now(), method, url: String(url)};
            return origOpen.call(this, method, url, ...rest);
          };
          XMLHttpRequest.prototype.send = function(body) {
            const rec = this.__cap || {kind: 'xhr'};
            if (body) rec.reqBody = String(body).slice(0, 4000);
            this.addEventListener('loadend', () => {
              try { rec.status = this.status; rec.respBody = String(this.responseText || '').slice(0, 6000); } catch (e) {}
              cap.push(rec); if (cap.length > 50) cap.shift();
            });
            return origSend.call(this, body);
          };
          return {installed: true};
        })()"""
        return self.evaluate(expr)

    def read_captured(self, *, url_contains: str = "", limit: int = 20) -> list[dict[str, Any]]:
        """读捕获记录（可按 URL 片段过滤）。"""
        expr = f"""(() => {{
          const cap = window.__CDP_CAP__ || [];
          const want = {json.dumps(url_contains)};
          return cap.filter(r => !want || (r.url || '').includes(want)).slice(-{limit});
        }})()"""
        return self.evaluate(expr) or []

    def clear_captured(self) -> None:
        self.evaluate("(() => { if (window.__CDP_CAP__) window.__CDP_CAP__.length = 0; return true; })()")


__all__ = ["CdpClient", "CdpError"]
