"""构建 → 循环监听 → 拉日志（error / 设计）。

## 解决什么

平台侧的真实闭环是「改代码 → 提交 → 构建 → 起应用 → 看日志」。前三步各自有工具
（`repo_sync` / `PlatformBuilder`），但**构建完到「知道为什么失败」之间是断的**：
构建 FAILED 后还得人再去 Loki / k8s 面板里翻日志。

本模块把断点接上：

    build_and_watch()
      ├─ 触发构建（PlatformBuilder.trigger，deployType 默认 RELEASE）
      ├─ 轮询到终态（PlatformBuilder.wait，BUILDING 不算成功）
      └─ 拉日志
           FAILED  → 拉最近 minutes 的错误行，先把「为什么失败」摆出来
           SUCCESS → 按 rounds × interval_s 循环拉，抓启动期的 error / 设计日志

## 两条红线

1. **构建是写操作**：调用方必须显式 `confirm=True`，本模块自己不发请求。
2. **日志判读不外推**：只做「按行归类 + 去重 + 计数」，不下「业务成功/失败」的结论。
   日志里没有 error 行 ≠ 业务没问题（日志可能没采到），报告里必须保留原始计数。

## 复用而非重写

- 构建/轮询：`components.construction.p5_builder.PlatformBuilder`（已有，含 deployId 精确查询、
  陈旧快照判定）
- 日志：`components.logs.loki.search`（已有，LogQL 透传 + namespace/app/pod/grep 拼装）
"""
from __future__ import annotations

import re
import time
from typing import Any, Callable

#: 错误行判据。只认「日志级别/异常栈」这些硬信号，不猜业务语义。
ERROR_RE = re.compile(
    r"\b(ERROR|FATAL|SEVERE)\b|Exception|Caused by:|"
    r"^\s*at\s+[\w.$]+\(|Error:|Failed to|BUILD FAILURE|BUILD FAILED",
    re.IGNORECASE,
)
WARN_RE = re.compile(r"\b(WARN|WARNING)\b", re.IGNORECASE)


def classify_lines(lines: list[str]) -> dict[str, Any]:
    """把日志行分成 error / warn / other，并去重。

    返回：{total, errorCount, warnCount, errors[], warnings[]}
    ★ errors 只保留**前 40 条去重后的行**，避免把上下文全塞回去。
    """
    errs: list[str] = []
    warns: list[str] = []
    seen: set[str] = set()
    for raw in lines:
        line = (raw or "").rstrip()
        if not line:
            continue
        key = line.strip()
        if key in seen:
            continue
        seen.add(key)
        if ERROR_RE.search(line):
            errs.append(line)
        elif WARN_RE.search(line):
            warns.append(line)
    return {"total": len(lines), "errorCount": len(errs), "warnCount": len(warns),
            "errors": errs[:40], "warnings": warns[:20]}


def watch_logs(*, env: str = "", namespace: str = "", app: str = "", pod: str = "",
               grep: str = "", minutes: int = 10, limit: int = 300,
               rounds: int = 1, interval_s: float = 15.0,
               search: Callable[..., dict] | None = None,
               sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """循环拉日志并按级别归类。

    - rounds=1 → 只拉一次（构建失败时用这个）
    - rounds>1 → 每 interval_s 拉一次，**按行去重**后合并，抓启动期滚动出现的错
    """
    if search is None:
        from components.logs import loki as _loki
        search = _loki.search

    rounds = max(1, int(rounds))
    merged: list[str] = []
    seen: set[str] = set()
    per_round: list[dict[str, Any]] = []
    failed_rounds: list[str] = []

    for i in range(rounds):
        try:
            r = search(env=env, namespace=namespace, app=app, pod=pod,
                       grep=grep, minutes=minutes, limit=limit) or {}
        except Exception as e:                      # 网络/凭据问题不能吞成「没问题」
            failed_rounds.append(f"#{i + 1}: {type(e).__name__}: {e}")
            r = {}
        st = str(r.get("status") or "").upper()
        if st in ("BLOCKED", "SKIPPED", "ERROR") or r.get("error"):
            # 拉不到 ≠ 没有错误：必须记成失败轮次，别让它冒充「0 error」
            failed_rounds.append("#%d: %s %s" % (i + 1, st or "ERR",
                                                 r.get("reason") or r.get("error") or ""))
        lines = r.get("lines") or r.get("data") or []
        if isinstance(lines, dict):
            lines = lines.get("lines") or []
        new = 0
        for ln in lines:
            s = str(ln).strip()
            if s and s not in seen:
                seen.add(s)
                merged.append(str(ln))
                new += 1
        per_round.append({"round": i + 1, "lines": len(lines), "new": new})
        if i + 1 < rounds:
            sleep(interval_s)

    cls = classify_lines(merged)
    out: dict[str, Any] = {
        "rounds": per_round,
        "mergedLines": len(merged),
        "errorCount": cls["errorCount"],
        "warnCount": cls["warnCount"],
        "errors": cls["errors"],
        "warnings": cls["warnings"],
        "hint": ("日志里 0 条 error ≠ 业务正常：先确认 namespace/app/pod 选对、"
                 "容器日志路径默认 /var/logs/webappck/<应用>。"),
    }
    if failed_rounds:
        out["failedRounds"] = failed_rounds
        out["note"] = "有轮次没拉到日志（网络/凭据/selector），别把 0 error 当结论。"
    return out


def build_and_watch(*, host: str, cookie: str, app_id: str, app_name: str = "",
                    deploy_type: str = "RELEASE", poll_interval: float = 8.0,
                    timeout_s: float = 900.0,
                    env: str = "", namespace: str = "", app: str = "", pod: str = "",
                    minutes: int = 10, rounds: int = 3, interval_s: float = 15.0,
                    grep: str = "", limit: int = 300,
                    builder: Any = None, search: Callable[..., dict] | None = None,
                    sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """构建一次，轮询到终态，然后按状态拉日志。

    FAILED  → 立刻拉最近 minutes 的日志（1 轮），把失败原因摆出来
    SUCCESS → 按 rounds × interval_s 循环拉，抓启动期滚动错误
    """
    from components.construction.p5_builder import BuildError, PlatformBuilder

    if builder is None:
        from components.construction.p5_pipeline import _HttpAdapter
        builder = PlatformBuilder(http=_HttpAdapter(host=host, cookie=cookie),
                                  app_id=str(app_id), poll_interval=poll_interval,
                                  timeout_s=timeout_s, sleep=sleep)

    out: dict[str, Any] = {"appId": str(app_id), "deployType": deploy_type, "ok": False}

    # ① 触发
    try:
        deploy_id = builder.trigger(deploy_type=deploy_type)
    except BuildError as e:
        out.update({"phase": "trigger", "state": "TRIGGER_FAILED", "error": str(e)})
        return out
    out["deployId"] = deploy_id
    out["phase"] = "wait"

    # ② 轮询
    try:
        res = builder.wait(deploy_id)
    except Exception as e:
        out.update({"state": "WAIT_ERROR", "error": f"{type(e).__name__}: {e}"})
        return out
    build = res.to_dict() if hasattr(res, "to_dict") else dict(res or {})
    out["build"] = build
    state = str(build.get("state") or "").upper()
    out["state"] = state
    out["ok"] = bool(build.get("ok"))

    # ③ 拉日志（只读；失败不影响构建结论）
    try:
        if state in ("FAILED", "FAIL", "ERROR"):
            out["phase"] = "logs-failure"
            out["logs"] = watch_logs(env=env, namespace=namespace, app=app or app_name,
                                     pod=pod, grep=grep, minutes=minutes, limit=limit,
                                     rounds=1, search=search, sleep=sleep)
        elif state == "SUCCESS":
            out["phase"] = "logs-watch"
            out["logs"] = watch_logs(env=env, namespace=namespace, app=app or app_name,
                                     pod=pod, grep=grep, minutes=minutes, limit=limit,
                                     rounds=max(1, int(rounds)), interval_s=interval_s,
                                     search=search, sleep=sleep)
        else:
            out["phase"] = "done"
            out["note"] = ("未到终态（BUILDING/TIMEOUT）：不算成功，也不拉日志 —— "
                           "BUILDING 不是结论，继续轮询或调大 timeout_s。")
    except Exception as e:
        out["logsError"] = f"{type(e).__name__}: {e}"
    return out