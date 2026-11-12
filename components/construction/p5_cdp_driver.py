"""P5.2 的 CDP 驱动实现（ExpressionFinalizer 的 driver 适配器）。

★ 本模块是**唯一**允许碰页面 DOM 的地方（P5.2 边界）：
  NodeBuilder / Expression DSL / 编排器都不许直接操作设计器。

★ 复用 `components/udc/microflow/live/ui.py` 已有实现，不重写：
  open_node / drawer / confirm_node / close_drawer / click_el。

★ 设计器事实（需实测确认的部分用 probe() 输出，不要猜）：
  - 节点抽屉：`.ant-drawer`（width>200 的最上层）
  - 节点「确定」按钮：`.compid_node-config-submit-btn`
  - 表达式编辑器：条件行里的表达式控件（**待实测**，见 probe_expression_ui）
"""

from __future__ import annotations

import json
import time


class CdpDesignerDriver:
    """用 CDP 驱动 UDC 微流程设计器。

    参数：
        cdp        : 已连接的 CdpClient（或实现 eval/click 的同形对象）
        node_caption: {nodeId: caption} 映射 —— 设计器只能按 caption 找卡片，
                      所以必须由编排器提供，不能靠顺序猜
        probe_only : True 时只探测 DOM 不点击（安全模式）
    """

    #: 表达式控件选择器候选（按优先级）。★ 需实测确认，不确认不要写死。
    EXPR_SELECTORS = (
        ".compid_expression-editor",
        ".expression-editor",
        "[class*='expression'][class*='editor']",
        ".ant-drawer-body [class*='expression']",
    )

    def __init__(self, cdp, *, node_caption: dict[str, str] | None = None,
                 probe_only: bool = False):
        self.cdp = cdp
        self.node_caption = dict(node_caption or {})
        self.probe_only = probe_only
        self._node_id: str | None = None
        self._cond_index = -1

    # ---------------- 探测（先跑这个，再谈自动化） ----------------
    def probe(self) -> dict:
        """探测当前页面：抽屉状态、确定按钮、表达式控件候选。"""
        from components.udc.microflow.live import ui

        d = self.cdp
        out: dict = {"drawer": None, "submit_btn": False,
                     "expr_candidates": {}, "url": None}
        try:
            out["url"] = d.eval("location.href")
        except Exception as e:
            out["url_error"] = str(e)
        try:
            out["drawer"] = ui.drawer_info(d)
        except Exception as e:
            out["drawer_error"] = str(e)
        try:
            out["submit_btn"] = bool(d.eval(
                "(() => { const dr = %s; return !!(dr && "
                "dr.querySelector('.compid_node-config-submit-btn')); })()"
                % ui.DRAWER_JS))
        except Exception as e:
            out["submit_error"] = str(e)
        for sel in self.EXPR_SELECTORS:
            try:
                n = d.eval("document.querySelectorAll(%s).length" % json.dumps(sel))
                if n:
                    out["expr_candidates"][sel] = n
            except Exception:
                pass
        return out

    # ---------------- driver 接口 ----------------
    def open_node(self, node_id: str) -> dict:
        """按 caption 打开节点抽屉，并校验身份。"""
        from components.udc.microflow.live import ui

        cap = self.node_caption.get(node_id)
        if not cap:
            return {"ok": False, "reason": "没有 nodeId=%s 的 caption 映射" % node_id}
        if self.probe_only:
            return {"ok": False, "reason": "probe_only 模式不点击"}

        r = ui.open_node(self.cdp, cap)
        if r == "empty drawer":
            return {"ok": False, "reason": "抽屉是空壳（渲染未完成或定位失败）"}

        info = ui.drawer_info(self.cdp) or {}
        # ★ 身份校验：抽屉标题/内容里必须出现该 caption
        title = str(info.get("title") or "")
        if cap and cap not in title and cap not in json.dumps(info, ensure_ascii=False):
            return {"ok": False,
                    "reason": "抽屉身份不符：期望含 %r，实际标题 %r" % (cap, title)}
        self._node_id = node_id
        return {"ok": True, "node_id": node_id, "caption": cap,
                "title": title}

    def open_expression(self, cond_index: int) -> dict:
        """打开第 cond_index 个条件的表达式编辑器。"""
        if self.probe_only:
            return {"ok": False, "reason": "probe_only 模式不点击"}
        self._cond_index = cond_index
        # ★ 表达式控件选择器尚未实测确认：先探测，找不到就明确失败，不猜着点。
        found = None
        for sel in self.EXPR_SELECTORS:
            n = self.cdp.eval("document.querySelectorAll(%s).length"
                              % json.dumps(sel))
            if n:
                found = sel
                break
        if not found:
            return {"ok": False,
                    "reason": "未找到表达式编辑器（候选选择器全部未命中，"
                              "需先跑 probe 确认真实 DOM）"}
        self._expr_sel = found
        return {"ok": True, "selector": found}

    def read_expression(self) -> str:
        """读表达式编辑器当前文本（用于身份校验）。"""
        sel = getattr(self, "_expr_sel", None)
        if not sel:
            return ""
        try:
            return str(self.cdp.eval(
                "(() => { const e = document.querySelector(%s);"
                " return e ? (e.innerText || e.value || '') : ''; })()"
                % json.dumps(sel)) or "")
        except Exception:
            return ""

    def confirm(self) -> dict:
        """点「确定」并等 UpdatePost。"""
        from components.udc.microflow.live import ui

        if self.probe_only:
            return {"ok": False, "reason": "probe_only 模式不点击"}
        try:
            r = ui.confirm_node(self.cdp)
        except Exception as e:
            return {"ok": False, "reason": str(e)}
        ok = bool(r.get("saved"))
        return {"ok": ok, "saved": ok, "net": r.get("net"), "closed": r.get("closed")}

    def close(self) -> None:
        from components.udc.microflow.live import ui

        if self.probe_only:
            return
        try:
            ui.close_drawer(self.cdp)
        except Exception:
            pass


def read_schema_via_api(host: str, cookie: str):
    """返回 callable(mid) -> 已解析的 dataSchema dict。"""
    from components.udc.microflow import deploy as DP

    def _read(mid: str) -> dict:
        back = DP.get(host, cookie, str(mid))
        raw = back.get("dataSchema") or "{}"
        return json.loads(raw) if isinstance(raw, str) else raw
    return _read
