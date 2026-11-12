"""P5.4 交付报告持久化与断点恢复。

★ 设计要点（任务书）：
  1. 每次执行生成结构化报告，落盘可审。
  2. 断点恢复**必须核对平台真实状态**，不能盲目重跑：
     - mid 还在不在？
     - state 是 DRAFT 还是 RELEASE？
     - 已发布的不重复发布，已构建的不重复构建。
  3. 恢复失败要能定位到具体阶段。

★ 恢复原则：
  平台真实状态 > 本地记录。两者冲突时以平台为准，并把冲突写进报告。
"""

from __future__ import annotations

import json
import os
import time


class ResumeError(RuntimeError):
    pass


#: 从「本地记录 + 平台实况」推算该从哪继续
def plan_resume(report: dict, *, platform_state: str | None = None,
                platform_exists: bool = True) -> dict:
    """返回 {action, from_stage, reasons[], conflicts[]}。

    action:
        "DONE"          已完成，无需动作
        "RESTART"       从头开始（无可用中间产物）
        "RESUME"        从 from_stage 继续
        "NEED_HUMAN"    需人工介入（失败/阻断/状态冲突）
    """
    reasons: list[str] = []
    conflicts: list[str] = []
    state = (report or {}).get("state")
    mid = (report or {}).get("mid")

    # ① 平台上的流程不存在了 → 本地记录作废
    if mid and not platform_exists:
        reasons.append("平台已无 mid=%s（被删除或环境重置）" % mid)
        return {"action": "RESTART", "from_stage": "DRAFT_READY",
                "reasons": reasons, "conflicts": ["平台无此流程"]}

    # ② 已成功
    if state == "BUILD_SUCCESS":
        return {"action": "DONE", "from_stage": None,
                "reasons": ["已 BUILD_SUCCESS"], "conflicts": []}

    # ③ 失败/阻断 → 不自动重试
    if state in ("FAILED", "BLOCKED"):
        reasons.append("上次止于 %s：%s"
                       % (state, ((report or {}).get("failure") or {}).get("message", "")))
        return {"action": "NEED_HUMAN", "from_stage": None,
                "reasons": reasons, "conflicts": []}

    if not state:
        return {"action": "RESTART", "from_stage": "DRAFT_READY",
                "reasons": ["无阶段记录"], "conflicts": []}

    # ④ 状态与平台实况交叉核对
    order = ["DRAFT_READY", "GRAPH_VALIDATED", "CONSTRUCTED", "SAVED",
             "PLATFORM_VALIDATED", "NEEDS_UI_FINALIZE", "UI_FINALIZED",
             "READBACK_VERIFIED", "PUBLISHED", "BUILD_SUCCESS"]
    if state not in order:
        return {"action": "RESTART", "from_stage": "DRAFT_READY",
                "reasons": ["未知阶段 %r" % state], "conflicts": []}

    i = order.index(state)

    # 已 SAVED 之后，平台必须真有这个流程
    if i >= order.index("SAVED") and platform_state is None:
        conflicts.append("本地记录已到 %s，但平台读不到流程状态" % state)
        return {"action": "NEED_HUMAN", "from_stage": None,
                "reasons": reasons, "conflicts": conflicts}

    # 已发布但平台是 DRAFT → 平台回退了
    if i >= order.index("PUBLISHED") and platform_state == "DRAFT":
        conflicts.append("本地记录已 PUBLISHED，平台实际是 DRAFT")
        return {"action": "NEED_HUMAN", "from_stage": None,
                "reasons": reasons, "conflicts": conflicts}

    nxt = order[i + 1] if i + 1 < len(order) else None
    reasons.append("本地止于 %s，平台 state=%s" % (state, platform_state))
    return {"action": "RESUME", "from_stage": nxt,
            "reasons": reasons, "conflicts": conflicts}


# ---------------------------------------------------------------- 落盘


def report_path(base_dir: str, app_id: str, flow_name: str,
                stamp: float | None = None) -> str:
    ts = time.strftime("%Y%m%d-%H%M%S", time.localtime(stamp or time.time()))
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (flow_name or "flow"))
    return os.path.join(base_dir, "%s-%s-%s.json" % (app_id, safe, ts))


def save_report(report: dict, path: str) -> str:
    """原子写（先写临时文件再 replace），避免半截 JSON。"""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1, default=str)
    os.replace(tmp, path)
    return path


def load_report(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- 人读摘要


def render_summary(report: dict) -> str:
    """给使用者看的一页纸摘要（纯文本，CLI 友好）。"""
    r = report or {}
    lines: list[str] = []
    ok = r.get("ok")
    lines.append("交付结果：%s" % ("✅ BUILD_SUCCESS" if ok else "❌ " + str(r.get("state"))))
    lines.append("流程：%s（%s）" % (r.get("flow_caption") or "-", r.get("flow_name") or "-"))
    lines.append("应用：%s" % r.get("app_id"))
    lines.append("耗时：%ss" % r.get("elapsed"))
    lines.append("")
    lines.append("阶段：")
    for s in r.get("stages") or []:
        mark = "✓" if s.get("ok") else "✗"
        lines.append("  %s %-20s %6ss" % (mark, s.get("stage"), s.get("elapsed")))
        for p in (s.get("problems") or [])[:3]:
            lines.append("      · %s" % p)
        if s.get("error"):
            lines.append("      ! %s" % s["error"])
    if r.get("needs_ui_finalize"):
        lines.append("")
        lines.append("待 UI 最终化节点：%s" % ", ".join(r["needs_ui_finalize"]))
    b = r.get("build") or {}
    if b:
        lines.append("")
        lines.append("构建：state=%s progress=%s totalTime=%ss"
                     % (b.get("state"), b.get("progress"), b.get("total_time")))
        sem = (b.get("detail") or {}).get("semantics")
        if sem:
            lines.append("说明：%s" % sem)
    if r.get("failure"):
        lines.append("")
        f = r["failure"]
        lines.append("失败阶段：%s" % f.get("stage"))
        lines.append("原因：%s" % f.get("message"))
    if r.get("human_interventions"):
        lines.append("")
        lines.append("人工介入：")
        for h in r["human_interventions"]:
            lines.append("  · %s" % h)
    return "\n".join(lines)
