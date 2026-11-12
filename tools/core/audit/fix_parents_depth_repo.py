# -*- coding: utf-8 -*-
"""fix_parents_depth_repo.py — 全仓修正因目录移动而失效的 parents[N]

判定：按当前 N 算出的 ROOT 若不含仓库标志物，但上溯一层含 → N 少 1。
标志物：docs/audit、components、tests 三者同时存在 = 仓库根。
"""
import re
from pathlib import Path

REPO = Path(r"<XIAOZHUA_AGENT_ROOT>")
MARKERS = ["docs/audit", "components", "tests"]


def is_root(p: Path) -> bool:
    try:
        return all((p / m).exists() for m in MARKERS)
    except OSError:
        return False


fixed = []
for p in list(REPO.rglob("*.py")):
    sp = p.as_posix()
    if "node_modules" in sp or "/.venv/" in sp or "/.git/" in sp:
        continue
    if "artifacts/decompiled" in sp or "artifacts/scratch-migrated" in sp:
        continue
    try:
        t0 = p.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        continue
    lines = t0.split("\n")
    changed = False
    for i, line in enumerate(lines):
        m = re.search(r"parents\[(\d+)\]", line)
        if not m:
            continue
        n = int(m.group(1))
        rp = p.resolve()
        if n >= len(rp.parents):
            continue
        cur = rp.parents[n]
        if is_root(cur):
            continue
        for delta in range(1, 4):
            if n + delta >= len(rp.parents):
                break
            cand = rp.parents[n + delta]
            if is_root(cand):
                lines[i] = line.replace(f"parents[{n}]", f"parents[{n+delta}]")
                changed = True
                fixed.append((str(p.relative_to(REPO)), n, n + delta, line.strip()[:70]))
                break
    if changed:
        p.write_text("\n".join(lines), encoding="utf-8", newline="")

print(f"=== 修正 {len(fixed)} 处 ===")
for f, a, b, snippet in fixed:
    print(f"  {f:<54} parents[{a}]→parents[{b}]   {snippet}")
