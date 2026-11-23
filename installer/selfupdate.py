"""xiaozhua-agent 自更新 / 自检 CLI（Windows · macOS · Linux 通用）。

    xiaozhua update          拉代码 → 装依赖 → 重装宿主配置 → 自检
    xiaozhua doctor          只诊断，不改任何东西
    xiaozhua version         版本与来源信息
    xiaozhua install ...     转发给 installer/install.py

设计约束（都是踩过的坑定的）：

* 只用标准库，**不 import 仓库其它模块**——update 时仓库正在被替换，
  任何 import 都可能加载到半旧半新的状态。
* 失败要说清「哪一步、为什么、怎么修」，不吞异常、不假装成功。
* 脏工作区不自动 stash：本地改动可能是没提交的证据，宁可停下让用户决定。
* macOS 没有 `readlink -f` / bash 4，路径一律 Path.resolve()。
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_SLUG = "mingtaobai79-cloud/xiaozhua-agent"
REPO_URL = f"https://github.com/{REPO_SLUG}.git"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO_SLUG}/main"

MIN_PY = (3, 12)
ROOT = Path(__file__).resolve().parents[1]
def _default_state_path() -> Path:
    """state 跟着安装根走：<home>/state.json（一键安装布局），否则 ~/.xiaozhua/state.json。

    放在 src 的同级而不是用户主目录，多份安装（测试/正式）才不会互相覆盖。
    """
    env = os.environ.get("XIAOZHUA_STATE")
    if env:
        return Path(env)
    home = ROOT.parent
    if (home / "venv").exists() or (home / "pkg").exists():
        return home / "state.json"
    return Path.home() / ".xiaozhua" / "state.json"


STATE_PATH = _default_state_path()

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
if os.name == "nt" and not os.environ.get("WT_SESSION"):
    GREEN = RED = YELLOW = DIM = RESET = ""          # 老 cmd.exe 不乱码


# ---------------------------------------------------------------- 基础工具

def run(cmd, cwd=None, check=True, timeout=600):
    """跑子进程，返回 CompletedProcess。失败时把 stderr 一起抛出来。"""
    proc = subprocess.run(
        cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True,
        timeout=timeout, encoding="utf-8", errors="replace",
    )
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"{' '.join(map(str, cmd))}\n{detail}")
    return proc


def git(*args, cwd=None, check=True):
    return run(["git", *args], cwd=cwd or ROOT, check=check)


def read_version(root: Path) -> str:
    try:
        return (root / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


def head_sha(root: Path) -> str:
    try:
        return git("rev-parse", "--short", "HEAD", cwd=root).stdout.strip()
    except Exception:
        return "unknown"


def current_branch(root: Path) -> str:
    try:
        return git("rev-parse", "--abbrev-ref", "HEAD", cwd=root).stdout.strip()
    except Exception:
        return "unknown"


def is_git_repo(root: Path) -> bool:
    try:
        return git("rev-parse", "--is-inside-work-tree", cwd=root, check=False).returncode == 0
    except Exception:
        return False


def load_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(data: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def mark(ok: bool) -> str:
    return f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"


# ---------------------------------------------------------------- 依赖

def missing_deps() -> list[str]:
    missing = []
    for mod, spec in (("yaml", "pyyaml>=6.0"), ("websocket", "websocket-client>=1.6")):
        try:
            __import__(mod)
        except ImportError:
            missing.append(spec)
    return missing


def install_deps(root: Path) -> str:
    """优先 `pip install -e .`（会同时注册 xiaozhua 命令），失败退回单包安装。"""
    pip = [sys.executable, "-m", "pip", "install", "--quiet"]
    if (root / "pyproject.toml").exists():
        try:
            run([*pip, "-e", str(root)], timeout=900)
            return "pip install -e ."
        except Exception as exc:
            reason = (str(exc).splitlines() or ["-"])[0]
        run([*pip, "pyyaml>=6.0", "websocket-client>=1.6"], timeout=900)
        return f"pip install 单包（-e 失败：{reason}）"
    run([*pip, "pyyaml>=6.0", "websocket-client>=1.6"], timeout=900)
    return "pip install 单包（无 pyproject.toml）"


# ---------------------------------------------------------------- 自检

def mcp_selfcheck(root: Path) -> tuple[bool, str]:
    """真起一次 MCP 服务数工具——只有真跑过才算通过。"""
    server = root / "adapters" / "mcp" / "server.py"
    if not server.exists():
        return False, "找不到 adapters/mcp/server.py"
    payload = (
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":'
        '{"protocolVersion":"2024-11-05","capabilities":{},'
        '"clientInfo":{"name":"xiaozhua-update","version":"1"}}}\n'
        '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n'
    )
    try:
        proc = subprocess.run(
            [sys.executable, str(server)], input=payload, capture_output=True,
            text=True, timeout=180, encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        return False, "MCP 服务 180s 未返回"
    tools, name = 0, None
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        res = obj.get("result") or {}
        if "serverInfo" in res:
            name = res["serverInfo"].get("name")
        if "tools" in res:
            tools = len(res["tools"])
    if tools:
        return True, f"serverInfo={name} tools={tools}"
    tail = (proc.stderr or "").strip().splitlines()
    return False, f"没数到工具{('：' + tail[-1]) if tail else ''}"


def check_python() -> tuple[bool, str]:
    v = sys.version_info
    ok = v[:2] >= MIN_PY
    return ok, f"Python {v.major}.{v.minor}.{v.micro}（要求 ≥ {'%d.%d' % MIN_PY}）"


def host_targets() -> list[tuple[str, Path]]:
    """目标目录回退链：环境变量 → state.json → 与 src 同级的 pkg → ~/.xiaozhua/pkg。

    一键安装把仓库放在 <home>/src、宿主配置放 <home>/pkg，不是 ~/.xiaozhua/pkg；
    没有 state 时若直接取 home 默认值，doctor 会指向一个不存在的目录（假红）。
    """
    state = load_state()
    sibling = ROOT.parent / "pkg"
    fallback = sibling if sibling.exists() else (Path.home() / ".xiaozhua" / "pkg")
    target = Path(os.environ.get("XIAOZHUA_TARGET") or state.get("target") or fallback)
    hosts = os.environ.get("XIAOZHUA_HOSTS")
    host_list = hosts.split(",") if hosts else (state.get("hosts") or ["all"])
    return [(h, target) for h in host_list]


def reinstall_hosts(root: Path) -> str:
    installer = root / "installer" / "install.py"
    if not installer.exists():
        return "跳过（无 installer/install.py）"
    done = []
    for host, target in host_targets():
        run([sys.executable, str(installer), "--host", host, "--target", str(target),
             "--write", "--force"], timeout=600)
        done.append(f"{host} → {target}")
    return "; ".join(done)


# ---------------------------------------------------------------- 命令

def cmd_version(_args) -> int:
    state = load_state()
    print(f"xiaozhua-agent {read_version(ROOT)}  ({head_sha(ROOT)}, {current_branch(ROOT)})")
    print(f"  root    {ROOT}")
    print(f"  python  {platform.python_version()} · {platform.system()} {platform.machine()}")
    if state:
        print(f"  target  {state.get('target', '-')}")
        print(f"  hosts   {', '.join(state.get('hosts', [])) or '-'}")
    return 0


def cmd_doctor(args) -> int:
    print(f"xiaozhua-agent doctor · {platform.system()} {platform.release()}")
    print()
    failures = 0

    ok, detail = check_python()
    failures += 0 if ok else 1
    print(f" {mark(ok)} {detail}")

    missing = missing_deps()
    ok = not missing
    failures += 0 if ok else 1
    print(f" {mark(ok)} 依赖 {'齐' if ok else '缺 ' + ', '.join(missing)}")

    in_git = is_git_repo(ROOT)
    if in_git:
        dirty = bool(git("status", "--porcelain", cwd=ROOT, check=False).stdout.strip())
        if getattr(args, "fetch", False):
            git("fetch", "--quiet", "origin", cwd=ROOT, check=False)
        behind = "未比（加 --fetch 拉远端再比）"
        try:
            counts = git("rev-list", "--left-right", "--count",
                         f"HEAD...origin/{current_branch(ROOT)}", cwd=ROOT, check=False).stdout.split()
            back = int(counts[1])
            behind = "最新" if back == 0 else f"落后 {back} 个提交"
            if back:
                failures += 1
        except Exception:
            pass
        print(f" {mark(not dirty and '落后' not in behind)} git {head_sha(ROOT)} · "
              f"{'有未提交改动' if dirty else '工作区干净'} · {behind}")
    else:
        print(f" {DIM}·{RESET} 非 git 检出（压缩包安装），无法自动更新")

    ok, detail = mcp_selfcheck(ROOT)
    failures += 0 if ok else 1
    print(f" {mark(ok)} MCP {detail}")

    for host, target in host_targets():
        ok = target.exists()
        failures += 0 if ok else 1
        print(f" {mark(ok)} 宿主 {host} → {target}")

    print()
    if failures:
        print(f"{YELLOW}{failures} 项待处理{RESET}（`xiaozhua update` 可修复依赖/落后/宿主配置）")
    else:
        print(f"{GREEN}全部通过{RESET}")
    return 0 if not failures else 1


def cmd_update(args) -> int:
    started = time.time()
    if not is_git_repo(ROOT):
        print(f"{RED}不是 git 检出，无法 update{RESET}。请改用一键安装：")
        print(f"  Windows  irm {RAW_BASE}/scripts/install.ps1 | iex")
        print(f"  macOS    curl -fsSL {RAW_BASE}/scripts/install.sh | bash")
        return 2

    before_version, before_sha = read_version(ROOT), head_sha(ROOT)
    print(f"更新前 {before_version} ({before_sha})")

    dirty = git("status", "--porcelain", cwd=ROOT, check=False).stdout.strip()
    if dirty and not args.force:
        print(f"{RED}工作区有未提交改动，已停止{RESET}（这些可能是没提交的证据，不自动 stash）：")
        for line in dirty.splitlines()[:10]:
            print(f"  {line}")
        print(f"\n处理：先 commit / 清理，或 `xiaozhua update --force`（丢弃改动）")
        return 3

    branch = args.branch or current_branch(ROOT)
    try:
        git("fetch", "--prune", "origin", cwd=ROOT)
        merge = git("merge", "--ff-only", f"origin/{branch}", cwd=ROOT, check=False)
        if merge.returncode != 0:
            print(f"{RED}无法快进合并（本地有分叉提交或分支不存在）{RESET}")
            print((merge.stderr or merge.stdout).strip())
            print(f"处理：`git log --oneline HEAD..origin/{branch}` 看清楚后再决定 rebase/reset")
            return 4
    except RuntimeError as exc:
        print(f"{RED}拉取失败{RESET}\n{exc}")
        print("处理：确认网络与 git 凭据（`git -C {} fetch origin` 手动跑一次）".format(ROOT))
        return 4

    after_version, after_sha = read_version(ROOT), head_sha(ROOT)
    if after_sha == before_sha:
        print(f"代码已是最新（{after_sha}）")
    else:
        print(f"代码 {before_sha} → {after_sha}  版本 {before_version} → {after_version}")

    print("装依赖 …", end="", flush=True)
    try:
        how = install_deps(ROOT)
    except Exception as exc:
        print(f"\r{RED}✗ 依赖安装失败{RESET}\n{exc}")
        return 5
    print(f"\r{mark(True)} 依赖 {how}")

    print("重装宿主配置 …")
    try:
        detail = reinstall_hosts(ROOT)
    except Exception as exc:
        print(f"{RED}✗ 宿主配置失败{RESET}\n{exc}")
        return 6
    print(f"  {detail}")

    ok, detail = mcp_selfcheck(ROOT)
    print(f" {mark(ok)} 自检 {detail}")
    if not ok:
        return 7

    state = load_state()
    state.update({
        "version": after_version,
        "sha": after_sha,
        "root": str(ROOT),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    save_state(state)

    print(f"\n{GREEN}更新完成{RESET} {after_version} ({after_sha})  用时 {time.time() - started:.1f}s")
    if after_sha == before_sha:
        print("提示：本次没有新提交，只刷新了依赖与宿主配置。")
    return 0


def cmd_install(args) -> int:
    installer = ROOT / "installer" / "install.py"
    if not installer.exists():
        print(f"{RED}找不到 {installer}{RESET}")
        return 2
    cmd = [sys.executable, str(installer), "--host", args.host, "--target", args.target]
    if args.write:
        cmd.append("--write")
    if args.portable:
        cmd.append("--portable")
    if args.force:
        cmd.append("--force")
    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode == 0:
        state = load_state()
        hosts = sorted(set(state.get("hosts", [])) | set(args.host.split(",")))
        state.update({"hosts": hosts, "target": str(Path(args.target).expanduser()),
                      "version": read_version(ROOT), "sha": head_sha(ROOT)})
        save_state(state)
    return proc.returncode


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="xiaozhua", description="xiaozhua-agent 安装 / 更新 / 自检")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("update", help="拉代码 → 装依赖 → 重装宿主配置 → 自检")
    p.add_argument("--branch", default=None, help="跟哪个分支（默认当前分支）")
    p.add_argument("--force", action="store_true", help="丢弃本地未提交改动（默认拒绝）")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("doctor", help="只诊断，不改东西（默认不联网）")
    p.add_argument("--fetch", action="store_true", help="顺带 git fetch 比较落后多少提交")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("version", help="版本与来源")
    p.set_defaults(func=cmd_version)

    p = sub.add_parser("install", help="转发 installer/install.py")
    p.add_argument("--host", default="all")
    p.add_argument("--target", default=str(Path.home() / ".xiaozhua" / "pkg"))
    p.add_argument("--write", action="store_true", help="真正落盘（默认 dry-run）")
    p.add_argument("--portable", action="store_true")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_install)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n已中断")
        return 130
    except Exception as exc:                       # 兜底：失败必须看得懂
        print(f"{RED}失败{RESET}：{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
