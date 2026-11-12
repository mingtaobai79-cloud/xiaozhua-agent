# -*- coding: utf-8 -*-
"""统计脱敏闸门命中的分布（只读，不改文件）。

为什么单独写：`tests/test_deidentification.py` 只报前 25 条，
看不清「问题集中在哪个目录」。本脚本把命中按顶层目录 / PII 类型汇总。
"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tests.test_deidentification import (  # noqa: E402
    PII_PATTERNS, _rel_files, CONCLUSION_SUFFIX, EVIDENCE_DATA_DIRS,
)


def main() -> None:
    hits = []
    for p, rel in _rel_files():
        if p.suffix not in CONCLUSION_SUFFIX:
            continue
        if any(d in "/" + rel for d in EVIDENCE_DATA_DIRS):
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, pat in PII_PATTERNS.items():
            for m in pat.finditer(t):
                hits.append((rel, name, m.group(0)[:40]))

    print(f"违规命中总数: {len(hits)}")
    print(f"涉及文件数: {len({h[0] for h in hits})}\n")

    bydir = Counter(rel.split("/")[0] if "/" in rel else "(root)" for rel, _, _ in hits)
    print("按顶层目录:")
    for k, v in bydir.most_common():
        print(f"  {v:5}  {k}/")

    print("\n按 PII 类型:", dict(Counter(k for _, k, _ in hits)))

    print("\n前 12 个文件:")
    for rel, c in Counter(h[0] for h in hits).most_common(12):
        print(f"  {c:4}  {rel}")


if __name__ == "__main__":
    main()
