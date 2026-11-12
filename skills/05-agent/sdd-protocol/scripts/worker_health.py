"""按 collaboration.json 识别活跃 session，输出每组每角色的存活/静默/待处理三元组。

用法:
    python worker_health.py [BASE]

BASE 默认 <COLLAB_ROOT>/agent-collaboration。
判定口径见 SKILL.md 第 8.1 节：静默 <120s = WORKING；静默 ≥120s 且私 inbox 为空 = IDLE（正常待命）；
静默 ≥120s 且有未消费消息 = STALLED?（唯一真堵点信号）。
"""
import glob
import os
import sys
import time

import psutil

BASE = sys.argv[1] if len(sys.argv) > 1 else r"<COLLAB_ROOT>/agent-collaboration"
ROLES = ("main", "implementer", "auditor")
QUIET_WORKING = 120


def active_sessions(base):
    """只有带 collaboration.json 的目录才是活 session；同名空壳必须排除。"""
    out = []
    for p in glob.glob(os.path.join(base, "session-*")):
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "collaboration.json")):
            out.append(p)
    return sorted(out)


def worker_pids():
    """(root, role) -> pid。按 --root 参数精确配对，不靠 session 目录名后缀猜。"""
    index = {}
    for proc in psutil.process_iter(["pid", "cmdline"]):
        argv = proc.info["cmdline"] or []
        cmd = " ".join(argv)
        if "agent_worker.py" not in cmd:
            continue
        role = next((r for r in ROLES if f"--role {r}" in cmd), "?")
        root = ""
        for i, tok in enumerate(argv):
            if tok == "--root" and i + 1 < len(argv):
                root = argv[i + 1]
                break
        index[(os.path.normcase(root), role)] = proc.info["pid"]
    return index


def main():
    pids = worker_pids()
    now = time.time()
    sessions = active_sessions(BASE)
    if not sessions:
        print(f"no active session under {BASE}")
        return 1
    for d in sessions:
        print("=" * 12, os.path.basename(d))
        for role in ROLES:
            log = os.path.join(d, role, "worker.log")
            pid = pids.get((os.path.normcase(d), role))
            if not os.path.exists(log):
                print(f"  {role:11} pid={pid} no worker.log")
                continue
            quiet = int(now - os.path.getmtime(log))
            pending = len(glob.glob(os.path.join(d, role, "inbox", "*.json")))
            if quiet < QUIET_WORKING:
                state = "WORKING"
            elif pending == 0:
                state = "IDLE"
            else:
                state = "STALLED?"
            print(f"  {role:11} pid={str(pid):6} quiet={quiet:5}s pending={pending:2} {state}")
    print("now", time.strftime("%H:%M:%S"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
