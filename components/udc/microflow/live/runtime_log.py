"""微流程运行日志（RUNTIME 读侧）。

★★★ 前缀是**应用名**，不是 `udc`：

    POST /service/{appName}/udc-runtime/app-log/search/microflow   ✅
    POST /service/udc-runtime/app-log/search/microflow             ❌ server_404

后者会返回「udc-runtime 服务不存在，请重启服务或重新发布应用后再试！」——
这句话极具误导性，听起来像运行时服务挂了，实际只是前缀拼错。
运行态服务挂在应用专属网关下，每个应用一套。

实测（2026-11-01）：正确前缀一次拿到 211 行，success 211/211。
"""
from __future__ import annotations

import json
import subprocess
from typing import Any

# 微流程 / 生单规则 / 扣减规则三种日志，body 形态相同
LOG_KINDS = ("microflow", "dataflow", "deduction")


def _post(host: str, path: str, cookie: str, body: dict, timeout: int = 60) -> dict:
    cmd = ["curl", "-s", "-X", "POST", host.rstrip("/") + path,
           "-H", "Cookie: %s" % cookie,
           "-H", "Content-Type: application/json",
           "--max-time", str(timeout),
           "-d", json.dumps(body, ensure_ascii=False)]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    try:
        return json.loads(r.stdout or "{}")
    except Exception:
        return {"_raw": (r.stdout or "")[:400]}


def search_microflow_log(host: str, cookie: str, app_name: str,
                         page: int = 1, size: int = 20,
                         kind: str = "microflow", timeout: int = 60) -> dict:
    """读一页运行日志。返回 {rows, total, pages, code}。

    ★ 空列表是「无该类日志」，不是失败；`code != BOOT_0000` 才是失败。
    """
    path = "/service/%s/udc-runtime/app-log/search/%s" % (app_name, kind)
    body = {"pageInfo": {"needTotal": True, "pageNumber": page,
                         "pageSize": size, "pages": 0, "total": 0},
            "params": {}}
    d = _post(host, path, cookie, body, timeout=timeout)
    data = d.get("data") or {}
    rows = data.get("content") or []
    info = data.get("pageInfo") or {}
    return {"rows": rows, "total": info.get("total") or 0,
            "pages": info.get("pages") or 0,
            "code": d.get("code"), "message": d.get("message")}


def fetch_all(host: str, cookie: str, app_name: str,
              kind: str = "microflow", max_pages: int = 50) -> list[dict]:
    """翻页取全量。"""
    out: list[dict] = []
    for pn in range(1, max_pages + 1):
        r = search_microflow_log(host, cookie, app_name, page=pn, size=20, kind=kind)
        rows = r["rows"]
        if not rows:
            break
        out.extend(rows)
        if len(out) >= r["total"] > 0:
            break
    return out


def find_runs(rows: list[dict], code: str) -> list[dict]:
    """按流程编码/名称捞某条流程的运行记录。"""
    out = []
    for x in rows:
        hay = "%s%s" % (x.get("microFlowCode") or "", x.get("caption") or "")
        if code and code in hay:
            out.append(x)
    return out


def summarize(rows: list[dict]) -> dict:
    """汇总：成功率、耗时、按流程分布。"""
    by_flow: dict[str, int] = {}
    durs: list[int] = []
    ok = 0
    for x in rows:
        cap = str(x.get("caption") or "")
        by_flow[cap] = by_flow.get(cap, 0) + 1
        if str(x.get("success")).lower() == "true":
            ok += 1
        try:
            durs.append(int(x["logEndTime"]) - int(x["logStartTime"]))
        except Exception:
            pass
    return {"total": len(rows), "success": ok,
            "failed": len(rows) - ok, "by_flow": by_flow,
            "duration_ms": {"min": min(durs) if durs else None,
                            "max": max(durs) if durs else None,
                            "avg": (sum(durs) // len(durs)) if durs else None}}


def assert_ran(host: str, cookie: str, app_name: str, code: str,
               expect_success: bool = True) -> dict:
    """断言某条流程真的跑过（RUNTIME_VERIFIED 的判据）。

    ★ 只认日志里存在该流程的记录；读不到就抛错，不许当通过。
    """
    rows = fetch_all(host, cookie, app_name)
    mine = find_runs(rows, code)
    if not mine:
        raise RuntimeError(
            "运行日志里没有 %r 的记录（共 %d 行）——不能判 RUNTIME_VERIFIED"
            % (code, len(rows)))
    if expect_success:
        bad = [x for x in mine if str(x.get("success")).lower() != "true"]
        if bad:
            raise RuntimeError("%r 有 %d 次运行失败：%s"
                               % (code, len(bad),
                                  json.dumps(bad[0], ensure_ascii=False)[:300]))
    return {"runs": len(mine), "latest": mine[0]}
