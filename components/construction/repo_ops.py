# -*- coding: utf-8 -*-
"""components/construction/repo_ops.py — 客开仓库的读取面。

**分工**：
  本模块   只读 —— 分支、remote、脏文件、ahead/behind、最近提交
  写操作   commit / push / pull **不在这里**。写操作要显式确认，另走单独入口。

为什么把读和写分开：agent 需要频繁问「我现在在哪个分支、有没有未提交改动、
远端有没有新提交」，这类调用一天几十次，不该每次都要凭据；而 push 一次就够
把人坑了。读放前面，写必须显式。

★ 不含任何域名 —— git_base 由调用方传或从 remote 反推。
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

TIMEOUT = 30


def _git(repo_dir: str, *args: str) -> Dict[str, Any]:
    """跑一条 git 命令，返回 {ok, out, err}。不抛异常给调用方。"""
    try:
        p = subprocess.run(
            ["git", "-C", repo_dir, *args],
            capture_output=True, text=True, timeout=TIMEOUT,
            encoding="utf-8", errors="replace",
            env={**_clean_env()},
        )
        return {"ok": p.returncode == 0,
                "out": (p.stdout or "").strip(),
                "err": (p.stderr or "").strip(),
                "code": p.returncode}
    except subprocess.TimeoutExpired:
        return {"ok": False, "out": "", "err": "git 超时（%ds）" % TIMEOUT, "code": -1}
    except FileNotFoundError:
        return {"ok": False, "out": "", "err": "找不到 git 可执行文件", "code": -1}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "out": "", "err": "%s: %s" % (type(e).__name__, e), "code": -1}


def _clean_env() -> Dict[str, str]:
    """禁用交互式凭据弹窗 —— 无 tty 环境下 GCM 会卡住或报 /dev/tty 不可用。"""
    import os
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "never"
    return env


def is_repo(repo_dir: str) -> bool:
    d = Path(repo_dir)
    if not d.exists():
        return False
    return (d / ".git").exists() or _git(repo_dir, "rev-parse", "--git-dir")["ok"]


def repo_state(repo_dir: str, recent: int = 5) -> Dict[str, Any]:
    """只读：这个仓库现在是什么状态。

    返回字段都来自 git 原生命令，不推断：
      branch / upstream / ahead / behind / remote
      dirty（未提交改动文件）/ untracked / recentCommits
      projectShape（如果是后端仓，顺带给出五模块/单模块）

    ★ 拿不到就返回 ok=False + reason，不要静默返回空壳。
    """
    if not repo_dir:
        return {"ok": False, "reason": "repo_dir 必填"}
    if not Path(repo_dir).exists():
        return {"ok": False, "reason": "目录不存在: %s" % repo_dir}
    if not is_repo(repo_dir):
        return {"ok": False, "reason": "不是 git 仓库: %s" % repo_dir}

    out: Dict[str, Any] = {"ok": True, "repoDir": str(Path(repo_dir).resolve())}

    br = _git(repo_dir, "rev-parse", "--abbrev-ref", "HEAD")
    out["branch"] = br["out"] if br["ok"] else None
    out["detached"] = out["branch"] == "HEAD"

    rem = _git(repo_dir, "remote", "get-url", "origin")
    out["remote"] = rem["out"] if rem["ok"] else None

    up = _git(repo_dir, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if up["ok"] and up["out"]:
        out["upstream"] = up["out"]
        ab = _git(repo_dir, "rev-list", "--left-right", "--count", "@{u}...HEAD")
        if ab["ok"]:
            parts = ab["out"].split()
            if len(parts) == 2:
                out["behind"], out["ahead"] = int(parts[0]), int(parts[1])
    else:
        out["upstream"] = None
        out["ahead"] = out["behind"] = None
        out["upstreamNote"] = "无上游分支（还没 push 过，或本地新建）"

    st = _git(repo_dir, "status", "--porcelain")
    if st["ok"]:
        lines = [l for l in st["out"].splitlines() if l.strip()]
        out["dirty"] = [l[3:] for l in lines if not l.startswith("??")]
        out["untracked"] = [l[3:] for l in lines if l.startswith("??")]
        out["clean"] = not lines
    else:
        out["dirty"] = out["untracked"] = []
        out["clean"] = None
        out["statusError"] = st["err"]

    lg = _git(repo_dir, "log", "--oneline", "-%d" % max(1, min(recent, 20)))
    out["recentCommits"] = lg["out"].splitlines() if lg["ok"] else []

    # 后端仓顺带给形态，省一次调用
    if (Path(repo_dir) / "pom.xml").exists():
        try:
            from components.construction.code_targets import detect_project_shape
            sh = detect_project_shape(repo_dir)
            out["projectShape"] = sh.get("shape")
            out["basePackage"] = sh.get("base_package")
        except Exception:  # noqa: BLE001
            out["projectShape"] = None

    # 前端仓特征
    pkg = Path(repo_dir) / "package.json"
    if pkg.exists():
        out["side"] = "frontend"
        out["hasPagesDir"] = (Path(repo_dir) / "src" / "pages").is_dir()

    return out


# ---------------------------------------------------------------------------
# 写操作：pull / commit / push
#
# 设计原则（不是保守，是踩过的）：
#   ① 不 git add -A。必须显式给 paths —— 一个 -A 就能把别的会话的未提交改动
#      一起带进提交，事后很难拆。
#   ② pull 只允许 --ff-only。自动 merge 会在客开仓里造出一堆冲突提交。
#   ③ commit / push 必须调用方传 confirm=True，且无默认值 —— 写能力不得默认可用。
#   ④ push 前校验 ahead > 0 且有上游分支，避免推到错的 remote。
# ---------------------------------------------------------------------------

def _run(repo_dir: str, *args: str) -> Dict[str, Any]:
    return _git(repo_dir, *args)


def repo_pull(repo_dir: str) -> Dict[str, Any]:
    """拉取远端（仅 --ff-only）。

    ★ 不允许自动 merge：客开仓里自动 merge 产生的冲突提交极难收拾。
    ★ 无上游分支时直接拒绝，不猜该拉哪个远端。
    """
    st = repo_state(repo_dir)
    if not st["ok"]:
        return st
    if not st.get("upstream"):
        return {"ok": False, "reason": "无上游分支，先 push -u 建立跟踪再 pull",
                "branch": st.get("branch")}
    r = _run(repo_dir, "pull", "--ff-only")
    st2 = repo_state(repo_dir)
    return {"ok": r["ok"], "action": "pull", "before": {
                "branch": st.get("branch"), "behind": st.get("behind"),
                "ahead": st.get("ahead")},
            "after": {"behind": st2.get("behind"), "ahead": st2.get("ahead")},
            "out": r["out"][-800:], "err": r["err"][-800:]}


def repo_commit(repo_dir: str, message: str, paths: List[str],
                confirm: bool) -> Dict[str, Any]:
    """提交指定路径。★ paths 必填且不能用 '.'/-A 全量。

    paths 是相对仓库根的路径列表。传 ["."] 会被拒。
    """
    if not confirm:
        return {"ok": False, "reason": "写操作需显式 confirm=True"}
    msg = (message or "").strip()
    if not msg:
        return {"ok": False, "reason": "message 必填"}
    if not paths:
        return {"ok": False, "reason": "paths 必填 —— 不允许 git add -A"}
    bad = [p for p in paths if p.strip() in (".", "-A", "--all", "*")]
    if bad:
        return {"ok": False, "reason": "paths 不允许全量通配 %s" % bad,
                "hint": "逐条列你本轮真正改过的文件"}

    st = repo_state(repo_dir)
    if not st["ok"]:
        return st

    add = _run(repo_dir, "add", "--", *paths)
    if not add["ok"]:
        return {"ok": False, "stage": "add", "err": add["err"][-500:]}

    staged = _run(repo_dir, "diff", "--cached", "--name-only")
    files = [l for l in staged["out"].splitlines() if l.strip()]
    if not files:
        return {"ok": False, "reason": "暂存区为空，路径没有实际改动", "paths": paths}

    ci = _run(repo_dir, "commit", "-m", msg)
    if not ci["ok"]:
        return {"ok": False, "stage": "commit", "err": ci["err"][-500:],
                "out": ci["out"][-400:]}
    head = _run(repo_dir, "rev-parse", "--short", "HEAD")
    st2 = repo_state(repo_dir)
    return {"ok": True, "action": "commit", "commit": head["out"],
            "files": files, "ahead": st2.get("ahead"),
            "next": "需要推到远端就调 action=push"}


def repo_push(repo_dir: str, confirm: bool) -> Dict[str, Any]:
    """推送到上游。★ 要求 confirm=True，且 ahead > 0。

    ★ 没有上游分支时拒绝 —— 不自动 push -u origin <branch>，那是猜远端。
    """
    if not confirm:
        return {"ok": False, "reason": "写操作需显式 confirm=True"}
    st = repo_state(repo_dir)
    if not st["ok"]:
        return st
    if not st.get("upstream"):
        return {"ok": False,
                "reason": "无上游分支，拒绝猜测远端。先手工 push -u origin <branch>"}
    if st.get("ahead") == 0:
        return {"ok": False, "reason": "没有待推送提交（ahead=0）",
                "behind": st.get("behind")}

    r = _run(repo_dir, "push")
    st2 = repo_state(repo_dir)
    return {"ok": r["ok"], "action": "push",
            "before": {"ahead": st.get("ahead")},
            "after": {"ahead": st2.get("ahead"), "behind": st2.get("behind")},
            "out": r["out"][-600:], "err": r["err"][-600:]}
