# -*- coding: utf-8 -*-
"""CDP 驱动：挂 Network 域抓接口 + console + store，驱动微流程编辑器逐个添加节点。

用法：
    from cdp_probe import Driver
    d = Driver()
    d.attach()                  # 挂 Network/Runtime/Log 域
    d.clear_log()               # 清空本次记录
    d.click_plus_after_start()  # 点开始节点后面的 +
    d.pick_node_type("创建变量")
    print(d.snapshot())         # 返回 addNode payload / nodeConfig / 抽屉表单 / 接口记录
    d.confirm()
    print(d.snapshot())
"""

import json
import os
import time
import asyncio
import urllib.request

import websockets


CDP = os.environ.get("UDC_CDP", "http://127.0.0.1:9222")


class Driver:
    def __init__(self, tab_state=None):
        """tab_state 可选：旧 wsUrl 缓存文件。默认 None = 完全运行时从 /json/list 发现。

        connect() 已内置多级兜底（tabId 匹配 → /microflow/editor/ 匹配 → 任一非 chrome:// page），
        所以 tab_state 只是加速首连的提示，不写死任何客户/环境路径。
        """
        self.state = {}
        if tab_state and os.path.exists(tab_state):
            try:
                self.state = json.load(open(tab_state, encoding="utf-8"))
            except Exception:
                self.state = {}
        self.ws = None
        self._mid = 0
        self.events = []          # 所有 CDP 事件
        self.net = []             # 接口记录 [{reqId, method, url, postData, status, response}]

    # ---------- 底层 ----------
    def connect(self):
        # Python 3.14 不再自动创建 event loop，显式建一个
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        self._loop = loop
        # 老的 wsUrl 可能失效（页面 reload 后 ws id 变化）→ 重新从 CDP 取
        # 老的 wsUrl 可能失效（页面 reload / 换域名后 ws id 变化）→ 重新从 CDP 取
        # 注意：不能只依赖 state 里缓存的 tabId —— 换了域名后那个 tab 已经不存在，
        # 直接用旧 wsUrl 会拿到 HTTP 500（server rejected WebSocket connection）。
        ws_url = self.state.get("wsUrl")
        try:
            tabs = json.loads(urllib.request.urlopen(CDP + "/json/list", timeout=10).read().decode())
            target = next((t for t in tabs if t.get("id") == self.state.get("tabId")), None)
            if not target:
                target = next((t for t in tabs
                               if t.get("type") == "page" and "/microflow/editor/" in (t.get("url") or "")), None)
            if not target:
                # 兜底：任一非 chrome:// 的 page（换域名后 path 也可能变）
                target = next((t for t in tabs
                               if t.get("type") == "page"
                               and not (t.get("url") or "").startswith("chrome")
                               and not (t.get("url") or "").startswith("edge")), None)
            if target:
                ws_url = target["webSocketDebuggerUrl"]
                self.state["wsUrl"] = ws_url
                self.state["tabId"] = target.get("id")
        except Exception:
            pass
        self.ws = loop.run_until_complete(
            websockets.connect(ws_url, max_size=80 * 1024 * 1024))
        # ★ 同一 URL 可能开了多个 tab，/json/list 的顺序不保证前台那个在前。
        #   连到后台 tab 时 document.hidden === true，antd 浮层渲染 0 宽、
        #   合成事件不派发，表现为「节点点不动、抽屉永不出现」——2026-11-01 踩实。
        #   连上后立刻拉到前台并开启焦点模拟，避免依赖 tab 顺序。
        try:
            self.send("Page.bringToFront")
            self.send("Emulation.setFocusEmulationEnabled", enabled=True)
        except Exception:
            pass

    def send(self, method, **params):
        """同步发一条 CDP 命令（不经事件队列），返回 result。"""
        if self.ws is None:
            raise RuntimeError("未连接，先 connect()")
        return self._loop.run_until_complete(self._cmd(method, **params))

    async def _cmd(self, method, **params):
        self._mid += 1
        mid = self._mid
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            raw = await self.ws.recv()
            msg = json.loads(raw)
            if msg.get("id") == mid:
                return msg
            if "method" in msg:
                self.events.append(msg)
                self._absorb_net(msg)

    def _absorb_net(self, msg):
        m = msg.get("method")
        p = msg.get("params") or {}
        if m == "Network.requestWillBeSent":
            req = p.get("request") or {}
            url = req.get("url", "")
            # ★ 放宽：除静态资源外全收（原来只收 /service/udc/ 与 graphql，
            #   漏掉了保存链路里的其它 service 接口）
            if ("/service/" in url or "graphql" in url) and not any(
                    url.endswith(ext) for ext in
                    (".js", ".css", ".png", ".jpg", ".svg", ".woff", ".woff2", ".ttf", ".ico")):
                self.net.append({
                    "reqId": p.get("requestId"), "method": req.get("method"),
                    "url": url, "postData": (req.get("postData") or "")[:8000],
                    "t": time.time(), "status": None, "resp": None, "body": None,
                })
        elif m == "Network.responseReceived":
            rid = p.get("requestId")
            for n in self.net:
                if n["reqId"] == rid:
                    n["status"] = (p.get("response") or {}).get("status")
                    n["mime"] = (p.get("response") or {}).get("mimeType")
                    break
        elif m == "Network.loadingFinished":
            rid = p.get("requestId")
            for n in self.net:
                if n["reqId"] == rid and n.get("body") is None:
                    # ★ 不能在回调线程里同步 cmd（会死锁），只登记待取
                    n["_needBody"] = True
                    break

    def cmd(self, method, **params):
        return self._loop.run_until_complete(self._cmd(method, **params))

    def fetch_bodies(self, limit=40):
        """在主线程补取响应体（回调线程不能同步 cmd，会死锁）。"""
        pending = [n for n in self.net if n.get("_needBody") and n.get("body") is None]
        for n in pending[:limit]:
            try:
                r = self.cmd("Network.getResponseBody", requestId=n["reqId"])
                body = r.get("body") or ""
                if r.get("base64Encoded"):
                    body = "<base64 %d bytes>" % len(body)
                n["body"] = body[:4000]
                n.pop("_needBody", None)
            except Exception:
                n.pop("_needBody", None)
        return len(pending)

    def eval(self, expr, by_value=True, await_promise=False):
        for attempt in range(2):
            try:
                r = self.cmd("Runtime.evaluate", expression=expr, returnByValue=by_value,
                             awaitPromise=await_promise)
                res = r.get("result", {})
                if res.get("exceptionDetails"):
                    return {"__error__": str(res["exceptionDetails"])[:500]}
                return res.get("result", {}).get("value")
            except Exception as e:
                if attempt == 0:
                    # 连接被 reload 打断 → 重连
                    try:
                        self.reconnect()
                        continue
                    except Exception:
                        pass
                return {"__error__": "conn: %s" % str(e)[:200]}

    def reconnect(self, wait=2.0):
        """重新建立 CDP 连接（reload 后 websocket 会失效）"""
        try:
            self._loop.run_until_complete(self.ws.close())
        except Exception:
            pass
        # 重新从 CDP 拿该 tab 的 wsUrl（同 url）
        try:
            tabs = json.loads(urllib.request.urlopen(CDP + "/json/list", timeout=10).read().decode())
            target = None
            for t in tabs:
                if t.get("id") == self.state.get("tabId"):
                    target = t
                    break
            if not target:
                for t in tabs:
                    if t.get("type") == "page" and "/microflow/editor/" in (t.get("url") or ""):
                        target = t
                        break
            if target:
                self.state["wsUrl"] = target["webSocketDebuggerUrl"]
                self.ws = self._loop.run_until_complete(
                    websockets.connect(self.state["wsUrl"], max_size=80 * 1024 * 1024))
                self.cmd("Runtime.enable")
                self.cmd("Network.enable")
                self.cmd("Log.enable")
                self._install_hooks()
        except Exception:
            raise

    # ---------- 初始化 ----------
    def attach(self):
        self.connect()
        self.cmd("Runtime.enable")
        self.cmd("Network.enable")
        self.cmd("Log.enable")
        self._install_hooks()

    def _install_hooks(self):
        hook = r"""
        (() => {
          if (window.__probe) { window.__probe.addNode=[]; window.__probe.nodeConfig=[];
                                window.__probe.errors=[]; window.__probe.rightValue=[]; return 'reset'; }
          window.__probe = { addNode: [], nodeConfig: [], errors: [], rightValue: [] };
          const origLog = console.log;
          console.log = function(...args){
            try {
              const s0 = typeof args[0] === 'string' ? args[0] : '';
              if (s0.includes('addNode') || s0.includes('添加节点'))
                window.__probe.addNode.push(JSON.parse(JSON.stringify(args)));
              if (s0.includes('回填 nodeConfig'))
                window.__probe.nodeConfig.push(JSON.parse(JSON.stringify(args)));
              if (s0.includes('右值组件表达式参数'))
                window.__probe.rightValue.push(JSON.parse(JSON.stringify(args)));
            } catch(e){}
            return origLog.apply(console, args);
          };
          window.addEventListener('unhandledrejection', function(ev){
            try {
              window.__probe.errors.push({ msg: String(ev.reason && ev.reason.message || ev.reason) });
            } catch(e){}
          });
          return 'hooked';
        })()
        """
        return self.eval(hook)

    def clear_log(self):
        self.net = []
        self.events = []
        return self.eval("(window.__probe.addNode=[] , window.__probe.nodeConfig=[], "
                         "window.__probe.errors=[], window.__probe.rightValue=[], 'cleared')")

    # ---------- 画布 ----------
    def frame(self):
        return self.eval("""JSON.stringify({
          frame: window.appReduxStore.getState().appDesign.microflowEditorReducer.flowFrame,
          nodes: Object.keys(window.appReduxStore.getState().appDesign.microflowEditorReducer.flowNodes||{}),
          sel: window.appReduxStore.getState().appDesign.microflowEditorReducer.currentSelected
        })""")

    def click_mouse(self, x, y):
        """派发真实 CDP 鼠标点击事件"""
        self.cmd("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y,
                 button="none", buttons=0)
        time.sleep(0.15)
        self.cmd("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y,
                 button="left", buttons=1, clickCount=1)
        time.sleep(0.1)
        self.cmd("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y,
                 button="left", buttons=0, clickCount=1)
        time.sleep(1.0)
        return True

    def click_plus_after_start(self):
        """点开始节点正下方的 + （CDP 真实鼠标）"""
        r = self.eval(r"""
        (() => {
          const btns = [...document.querySelectorAll('div.add-node-btn button')]
              .filter(b => b.getBoundingClientRect().width > 0)
              .map(b => { const r = b.getBoundingClientRect();
                          return {x: r.x + r.width/2, y: r.y + r.height/2}; });
          return JSON.stringify(btns);
        })()
        """)
        btns = json.loads(r) if isinstance(r, str) else []
        if not btns:
            return {"ok": False, "err": "no + button"}
        # 取最靠上的（开始节点后）
        b = sorted(btns, key=lambda o: o["y"])[0]
        self.cmd("Input.dispatchMouseEvent", type="mouseMoved", x=b["x"], y=b["y"],
                 button="none", buttons=0)
        time.sleep(0.2)
        self.cmd("Input.dispatchMouseEvent", type="mousePressed", x=b["x"], y=b["y"],
                 button="left", buttons=1, clickCount=1)
        time.sleep(0.1)
        self.cmd("Input.dispatchMouseEvent", type="mouseReleased", x=b["x"], y=b["y"],
                 button="left", buttons=0, clickCount=1)
        time.sleep(1.2)
        return {"ok": True, "at": b}

    def pick_node_type(self, name):
        """在「动作场景」抽屉里点节点名"""
        r = self.eval(r"""
        (() => {
          const drawer = document.querySelector('.ant-drawer-body');
          if (!drawer) return JSON.stringify({err: 'no drawer'});
          const el = [...drawer.querySelectorAll('span.add-node-title')]
              .find(e => (e.textContent||'').trim() === %s);
          if (!el) {
            return JSON.stringify({err: 'not found',
              avail: [...drawer.querySelectorAll('span.add-node-title')].map(e=>(e.textContent||'').trim())});
          }
          el.click();
          return JSON.stringify({ok: true});
        })()
        """ % json.dumps(name, ensure_ascii=False))
        time.sleep(1.8)
        return json.loads(r) if isinstance(r, str) else r

    def drawer_form(self):
        """抓当前抽屉的表单结构"""
        return self.eval(r"""
        (() => {
          const d = document.querySelector('.ant-drawer-open');
          if (!d) return JSON.stringify({open: false});
          const body = d.querySelector('.ant-drawer-body');
          const out = {
            open: true,
            title: ((d.querySelector('.ant-drawer-title')||{}).textContent||'').trim(),
            labels: [...body.querySelectorAll('label')].map(l => (l.textContent||'').trim()).filter(Boolean),
            // 表单项的 key（antd form item name）
            formItems: [...body.querySelectorAll('.ant-form-item')].map(fi => ({
              label: (fi.querySelector('label')||{}).textContent || '',
              cls: (fi.className||'').toString().slice(0, 80),
              id: (fi.querySelector('[id]')||{}).id || null
            })),
            radios: [...body.querySelectorAll('.ant-radio-wrapper')].map(r => (r.textContent||'').trim()),
            selects: [...body.querySelectorAll('.ant-select')].map(s => (s.textContent||'').trim().slice(0, 40)),
            inputs: [...body.querySelectorAll('input')].map(i => ({
              cls: (i.className||'').toString().slice(0, 50), ph: i.placeholder || '',
              val: i.value || ''
            })),
            buttons: [...body.querySelectorAll('button')].map(b => (b.textContent||'').trim()).filter(Boolean),
            text: (body.textContent||'').replace(/\s+/g, ' ').trim().slice(0, 700)
          };
          return JSON.stringify(out);
        })()
        """)

    def confirm(self):
        r = self.eval("""(() => {
          const b = document.querySelector('.compid_node-config-submit-btn');
          if (!b) return 'no btn';
          b.click(); return 'clicked';
        })()""")
        time.sleep(1.8)
        return r

    def probe_errors(self):
        # 页面重载后 window.__probe 会丢失，必须容错（否则整个调用抛 TypeError）
        return self.eval("JSON.stringify((((window.__probe||{}).errors)||[]).slice(-3))")

    def probe_addnode(self):
        return self.eval("JSON.stringify({addNode:(((window.__probe||{}).addNode)||[]).slice(-2),"
                         "nodeConfig:(((window.__probe||{}).nodeConfig)||[]).slice(-2)})")

    def snapshot(self):
        return {
            "frame": json.loads(self.frame()) if isinstance(self.frame(), str) else None,
            "addNode": json.loads(self.probe_addnode() or "{}"),
            "form": json.loads(self.drawer_form() or "{}"),
            "errors": json.loads(self.probe_errors() or "[]"),
            "net": [{"status": n["status"], "url": n["url"][:120]} for n in self.net[-12:]],
        }

    def close(self):
        try:
            self._loop.run_until_complete(self.ws.close())
        except Exception:
            pass
