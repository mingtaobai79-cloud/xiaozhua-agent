# -*- coding: utf-8 -*-
"""sync_test_counts.py — 同步 README / 审计文档里的测试计数

⚠️ 历史 bug（2026-11-07 修）：本脚本曾把 `<N> passed` 也替换成**收集数**。
于是 `docs/audit/code-reality-audit.md` 出现「收集 2714 / 通过 2714, skipped 23」
这种自相矛盾的写法（2714 != 2714+23），下一轮 P0 复核当场抓到。
根因：只跑 `--collect-only` 取得收集数，却用它同时替换两类数字。

现在：
- 收集数来自 `pytest tests --collect-only -q`
- 通过/跳过数来自**真实执行** `pytest tests -q`
- 两类数字分别替换；替换前断言 collected == passed + skipped，替换后回读校验

用法：
  python tools/core/audit/sync_test_counts.py            # 真跑一遍再同步
  python tools/core/audit/sync_test_counts.py --dry-run  # 只打印，不写盘
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FILES = ["README.md", "docs/audit/agent-version-audit.md", "docs/audit/code-reality-audit.md"]

PY = REPO / ".venv" / "Scripts" / "python.exe"
if not PY.exists():  # 非 Windows / 无 venv 时退回当前解释器
    PY = Path(sys.executable)


def run_pytest(*args: str) -> str:
    out = subprocess.run(
        [str(PY), "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", *args],
        cwd=str(REPO), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return out.stdout + out.stderr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    col_txt = run_pytest("--collect-only")
    m = re.search(r"(?m)^(\d+) tests collected", col_txt)
    if not m:
        raise SystemExit("无法取得收集数:\n" + col_txt[-800:])
    collected = int(m.group(1))

    run_txt = run_pytest()
    m2 = re.search(r"(?m)^(\d+) passed(?:, (\d+) skipped)?", run_txt)
    if not m2:
        raise SystemExit("无法取得通过数（有 failed/error？）:\n" + run_txt[-800:])
    passed = int(m2.group(1))
    skipped = int(m2.group(2) or 0)

    if collected != passed + skipped:
        raise SystemExit(
            "口径不自洽: collected=%d != passed=%d + skipped=%d（有 failed/error）"
            % (collected, passed, skipped)
        )
    print(f"collected={collected}  passed={passed}  skipped={skipped}")

    pat_collect = re.compile(rb"(\b\d{3,5}\b)(?= tests collected)")
    pat_pass = re.compile(rb"(\b\d{3,5}\b)(?= passed)")

    for rel in FILES:
        p = REPO / rel
        if not p.exists():
            print(f"  {rel}: 不存在，跳过")
            continue
        b = p.read_bytes()
        nb = pat_collect.sub(str(collected).encode(), b)
        nb = pat_pass.sub(str(passed).encode(), nb)
        if nb == b:
            print(f"  {rel}: 无需改")
            continue
        if args.dry_run:
            print(f"  {rel}: 【dry-run】将改 {len(b)}→{len(nb)} 字节")
            continue
        p.write_bytes(nb)
        check = p.read_bytes()
        ok_c = f"{collected} tests collected".encode() in check
        found = re.search(rb"(\b\d{3,5}\b)(?= passed)", check)
        ok_p = bool(found) and found.group(1) == str(passed).encode()
        print(f"  {rel}: 已同步为 collected={collected} passed={passed}"
              f"  回读 collected={ok_c} passed={ok_p}")
        if not (ok_c and ok_p):
            print(f"    ⚠️ {rel} 回读校验未通过，请人工检查")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
