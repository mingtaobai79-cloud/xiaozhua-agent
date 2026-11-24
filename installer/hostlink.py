"""把 xiaozhua MCP 注册进宿主（hermes / codex / claude-code）。

设计要点
--------
* **用宿主自己的 CLI**（`hermes mcp add` / `codex mcp add` / `claude mcp add`）而不是
  手改 config.yaml / config.toml / .claude.json：
  宿主自己负责 schema、作用域和校验，写坏了是宿主的问题不是我们的。
* **先 remove 再 add**，天然幂等；安装目录变了（换机器、换家目录）也能刷新。
* CLI 不存在 → `skipped`，不算失败（很多人只装其中一两个宿主）。
* `--dry-run` 只打印将执行的命令。

对外只有两个函数：`link()` / `unlink()`，都返回逐宿主的报告 dict 列表。
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess

SERVER_NAME = "xiaozhua"
CLI_TIMEOUT = 90

HOST_ORDER = ("hermes", "codex", "claude-code")


def cli_for(host: str) -> str | None:
    """宿主对应的可执行文件名；装了才返回。"""
    exe = {"hermes": "hermes", "codex": "codex", "claude-code": "claude"}.get(host)
    if not exe:
        return None
    return shutil.which(exe)


def detect() -> list[str]:
    """本机装了哪些宿主（能连的就连）。"""
    return [h for h in HOST_ORDER if cli_for(h)]


# `hermes mcp add` 会列一遍工具再问 "Enable all N tools? [Y/n/select]"，
# 没有 stdin 时它回 "Cancelled." 并且**退出码仍然是 0** —— 只看 returncode 会
# 误判成功，把宿主里原有的 server 删掉却装不回来（真踩过）。
_CANCELLED_HINTS = ("cancelled", "canceled", "已取消", "取消")


def _run(cmd: list[str], dry_run: bool, stdin_text: str | None = None) -> tuple[int, str]:
    if dry_run:
        return 0, "DRY-RUN: " + " ".join(cmd)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=CLI_TIMEOUT, input=stdin_text)
    except FileNotFoundError:
        return 127, "%s 不存在" % cmd[0]
    except subprocess.TimeoutExpired:
        return 124, "%s 超时（%ss）" % (" ".join(cmd[:3]), CLI_TIMEOUT)
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    code = proc.returncode
    low = out.lower()
    if code == 0 and any(h in low for h in _CANCELLED_HINTS):
        code = 1
    return code, out


def _remove_cmd(host: str, exe: str) -> list[str] | None:
    if host == "hermes":
        return [exe, "mcp", "remove", SERVER_NAME]
    if host == "codex":
        return [exe, "mcp", "remove", SERVER_NAME]
    if host == "claude-code":
        return [exe, "mcp", "remove", SERVER_NAME, "--scope", "user"]
    return None


def _add_cmd(host: str, exe: str, python_exe: str, server_py: str) -> list[str] | None:
    if host == "hermes":
        return [exe, "mcp", "add", SERVER_NAME, "--command", python_exe,
                "--args", server_py, "--connect-timeout", "60"]
    if host == "codex":
        return [exe, "mcp", "add", SERVER_NAME, "--", python_exe, server_py]
    if host == "claude-code":
        return [exe, "mcp", "add", SERVER_NAME, "--scope", "user", "--",
                python_exe, server_py]
    return None


def link(hosts, python_exe: str, server_py: str, dry_run: bool = False) -> list[dict]:
    """把 MCP 注册进每个宿主；返回 [{host, action, ok, detail}]。"""
    report: list[dict] = []
    for host in hosts:
        exe = cli_for(host)
        if not exe:
            report.append({"host": host, "action": "skipped",
                           "ok": False, "detail": "宿主 CLI 未安装"})
            continue

        rm = _remove_cmd(host, exe)
        add = _add_cmd(host, exe, python_exe, server_py)
        if not rm or not add:
            report.append({"host": host, "action": "skipped", "ok": False,
                           "detail": "不支持的宿主"})
            continue

        # 顺序：先 remove（已存在时 claude 会直接报 "already exists"，hermes 走
        # remove+add 才能刷新路径），再 add；add 若被判失败（含 Cancelled）重试一次。
        # 注意 remove 成功后 add 必须成功，所以失败要显式报出来，别静默。
        _run(rm, dry_run)
        code, out = _run(add, dry_run, stdin_text="Y\n" * 5)
        if code != 0 and not dry_run:
            # 某些宿主第一次 add 会因为残留提问/竞态失败，立刻再试一次
            code, out = _run(add, dry_run, stdin_text="Y\n" * 5)
        ok = code == 0
        detail = out.splitlines()[-1].strip() if out else ""
        if not ok:
            detail = ("exit %s: " % code) + (out.splitlines()[-1].strip() if out else "无输出")
        report.append({"host": host, "action": "linked", "ok": ok, "detail": detail})
    return report


PROBE_TIMEOUT = 30


def probe(host: str, root: str) -> bool:
    """宿主配置里那条 xiaozhua 是否指向 root（当前这份安装）。

    读各宿主自己的 list/get 输出，而不是猜配置文件格式 —— 版本间格式变过。
    """
    exe = cli_for(host)
    if not exe:
        return False
    cmd = {
        "hermes": [exe, "mcp", "list"],
        "codex": [exe, "mcp", "get", SERVER_NAME],
        "claude-code": [exe, "mcp", "list"],
    }.get(host)
    if not cmd:
        return False
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=PROBE_TIMEOUT)
    except Exception:
        return False
    out = ((proc.stdout or "") + (proc.stderr or "")).replace("\\", "/")
    root_norm = root.replace("\\", "/").rstrip("/")
    if host == "hermes":
        # `hermes mcp list` 会把 transport 列截断成 "C:/Users/.../ve..."，
        # 子串匹配永远失败；直接读配置文件里 xiaozhua 那一段。
        return _hermes_entry_matches(exe, root_norm)
    if SERVER_NAME not in out:
        return False
    return root_norm in out


def _hermes_entry_matches(exe: str, root_norm: str) -> bool:
    try:
        which = subprocess.run([exe, "config", "path"], capture_output=True,
                               text=True, encoding="utf-8", errors="replace",
                               timeout=PROBE_TIMEOUT)
        cfg = (which.stdout or "").strip().splitlines()[-1].strip()
        text = pathlib.Path(cfg).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    lines = text.replace("\\", "/").splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(SERVER_NAME + ":"):
            block = []
            for nxt in lines[i:i + 8]:
                if nxt.startswith("  ") and not nxt.startswith("    ") and nxt.strip().endswith(":"):
                    if block:
                        break
                block.append(nxt)
            if root_norm in "".join(block):
                return True
    return False


def unlink(hosts, dry_run: bool = False) -> list[dict]:
    report: list[dict] = []
    for host in hosts:
        exe = cli_for(host)
        if not exe:
            report.append({"host": host, "action": "skipped", "ok": False,
                           "detail": "宿主 CLI 未安装"})
            continue
        cmd = _remove_cmd(host, exe)
        code, out = _run(cmd, dry_run)
        report.append({"host": host, "action": "unlinked", "ok": code == 0,
                       "detail": (out.splitlines()[-1] if out else "")})
    return report


def summary(report: list[dict]) -> str:
    """一行摘要，给 CLI 和 doctor 用。"""
    linked = [r["host"] for r in report if r["ok"]]
    failed = [r["host"] for r in report if r["action"] == "linked" and not r["ok"]]
    skipped = [r["host"] for r in report if r["action"] == "skipped"]
    parts = []
    if linked:
        parts.append("已连接 " + ",".join(linked))
    if failed:
        parts.append("失败 " + ",".join(failed))
    if skipped:
        parts.append("跳过 " + ",".join(skipped))
    return "；".join(parts) or "无"