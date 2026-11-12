"""从 Hermes skills/seeyon 单向镜像到 xiaozhua-agent/skills。

规则：
  权威 = <HERMES_HOME>/skills/seeyon/<层>/<skill>/
  镜像 = <XIAOZHUA_AGENT_ROOT>/skills/<层>/<skill>/

- 只复制 SKILL.md / references / scripts / assets / templates / config*
- 目标多余项删除（保持结构一致，防止两处漂移）
- --check 只比对不写，用于 CI / 测试

用法：
  python tools/core/_meta/sync_skills_from_hermes.py            # 执行同步
  python tools/core/_meta/sync_skills_from_hermes.py --check    # 只报告差异
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

SRC = Path(r"<HERMES_HOME>\skills\xiaozhua")
DST = Path(r"<XIAOZHUA_AGENT_ROOT>\skills")

# 不镜像的内容（Hermes 侧的运行期产物）
IGNORE_DIRS = {"__pycache__", ".pytest_cache", "node_modules", "backups"}

# ★ 凭据红线：这些永不进仓库（仓库铁律：凭据 0 入件）
DENY_NAMES = {
    ".env", ".env.local", "kubeconfig-zhiyuan", "shared-credentials",
    "ctp-user-login.json", "scratch_credential.json",
    ".live-credential.json", "config.yaml",
}
DENY_SUFFIX = {".pem", ".p12", ".pfx", ".key", ".jks", ".crt", ".cer",
               ".sqlite", ".db"}


def denied(rel: str) -> bool:
    p = Path(rel)
    if p.name in DENY_NAMES:
        return True
    if p.suffix.lower() in DENY_SUFFIX:
        return True
    # 目录名命中（如 07-office-collaboration/config.yaml 属共用配置，含凭据风险）
    if any(part in DENY_NAMES for part in p.parts):
        return True
    return False


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def walk(root: Path):
    """返回 root 下所有需镜像的文件（相对路径集合），凭据类一律排除。"""
    out = {}
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        rel = p.relative_to(root).as_posix()
        if denied(rel):
            continue
        out[rel] = p
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只报告差异，不写")
    a = ap.parse_args()

    if not SRC.is_dir():
        print(f"源目录不存在: {SRC}", file=sys.stderr)
        return 2

    same, added, updated, removed = [], [], [], []

    src_dirs = {p.relative_to(SRC).as_posix() for p in SRC.rglob("*")
                if p.is_dir() and any(part not in IGNORE_DIRS for part in p.parts)}
    src_dirs = {d for d in src_dirs if (SRC / d / "SKILL.md").exists()
                or any((SRC / d).glob("*.md"))}

    for rel_dir in sorted(src_dirs):
        s_dir, d_dir = SRC / rel_dir, DST / rel_dir
        s_files = walk(s_dir)
        d_files = walk(d_dir) if d_dir.is_dir() else {}

        for rel, s_path in sorted(s_files.items()):
            d_path = d_dir / rel
            key = f"{rel_dir}/{rel}"
            if not d_path.exists():
                added.append(key)
                if not a.check:
                    d_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(s_path, d_path)
            elif sha(s_path) != sha(d_path):
                updated.append(key)
                if not a.check:
                    shutil.copy2(s_path, d_path)
            else:
                same.append(key)

        for rel in sorted(set(d_files) - set(s_files)):
            key = f"{rel_dir}/{rel}"
            removed.append(key)
            if not a.check:
                d_files[rel].unlink()

    print(f"源 {SRC}")
    print(f"同 {len(same)}  补 {len(added)}  更 {len(updated)}  删 {len(removed)}")
    for label, items in (("新增", added), ("漂移", updated), ("多余", removed)):
        if items:
            print(f"\n[{label}]")
            for i in items:
                print("  ", i)
    if a.check and (added or updated or removed):
        print("\n镜像不一致 —— 请跑一次不带 --check 的同步", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
