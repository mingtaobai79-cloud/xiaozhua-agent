# -*- coding: utf-8 -*-
"""plan_deident.py — 规划脱敏：区分「结论区」与「证据区」

原则（见 skill §4）：
  证据区  docs/audit/artifacts/  → 保留原文（删了就无法复核）
  结论区  事实格 / 契约 / skill / README / STATUS / 代码注释 → 必须脱敏

先量化每个区的命中量，再决定处理方式。
"""
import json
import re
from collections import Counter
from pathlib import Path

REPO = Path(r"D:\work\chit\seeyon-agent")
TEXT_EXT = {".py", ".md", ".yaml", ".yml", ".json", ".txt", ".js", ".sh", ".bat", ".toml"}

EVIDENCE_MARKERS = ("/artifacts/", "/artifacts\\")
CONCLUSION_MARKERS = (
    "core/facts/", "docs/operation-contracts/", "skills/", "adapters/",
    "README.md", "STATUS.md", "pyproject.toml", "SKILL.md",
)

PATTERNS = {
    "工号": re.compile(r"\bchjh\d{3}\b"),
    "人名": re.compile(r"白" + "明" + "涛"),
    "客户应用": re.compile(r"datami" + r"gration\d{6,}"),
    "客户实例": re.compile(r"\bznxm" + r"glpt\d{6,}\b"),
    "客户组织": re.compile(r"chang" + r"hongit|" + "长虹" + "|" + "佳华"),
}

zones = {"evidence": Counter(), "conclusion": Counter()}
zone_files = {"evidence": set(), "conclusion": set()}
detail = []

for p in REPO.rglob("*"):
    if not p.is_file() or p.suffix not in TEXT_EXT:
        continue
    sp = p.as_posix()
    if "node_modules" in sp or "/.venv/" in sp or "/.git/" in sp:
        continue
    rel = str(p.relative_to(REPO)).replace("\\", "/")
    is_evidence = any(m in rel for m in EVIDENCE_MARKERS)
    is_conclusion = any(rel.startswith(m) or rel == m or f"/{m}" in rel
                        for m in CONCLUSION_MARKERS)
    if not is_evidence and not is_conclusion:
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue
    zone = "evidence" if is_evidence else "conclusion"
    for name, pat in PATTERNS.items():
        n = len(pat.findall(t))
        if n:
            zones[zone][name] += n
            zone_files[zone].add(rel)
            if zone == "conclusion":
                detail.append((rel, name, n))

print("=== 证据区（artifacts/，保留原文）===")
for k, v in zones["evidence"].items():
    print(f"  {k:<10} {v:>6} 处  {len(zone_files['evidence'])} 个文件")
print("\n=== 结论区（必须脱敏）===")
for k, v in zones["conclusion"].items():
    print(f"  {k:<10} {v:>6} 处")
print(f"  涉及文件: {len(zone_files['conclusion'])}")

print("\n=== 结论区明细（按文件）===")
byfile: dict[str, Counter] = {}
for rel, name, n in detail:
    byfile.setdefault(rel, Counter())[name] += n
for rel in sorted(byfile, key=lambda r: -sum(byfile[r].values())):
    c = byfile[rel]
    print(f"  {rel}")
    print(f"      {dict(c)}  合计 {sum(c.values())}")

Path(r"D:\software\hermes\cache\scratch\deident-plan.json").write_text(
    json.dumps({"byfile": {k: dict(v) for k, v in byfile.items()}},
               ensure_ascii=False, indent=1), encoding="utf-8")
