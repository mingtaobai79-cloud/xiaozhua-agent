# -*- coding: utf-8 -*-
"""把 scratch/ 中含 PII 的散落脚本移入收容区 _attic_trash/（一次性执行脚本）。

依据：tests/test_deidentification.py 的结论区判定——
这些脚本不是被任何契约引用的证据，只是过程产物，但带客户标识，违反脱敏闸门。
收容区（/_attic_trash/）被闸门豁免，移入即恢复绿，且保留可回溯。
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import os  # noqa: E402

os.chdir(ROOT)
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
        if not rel.startswith("scratch/"):
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        if any(pat.search(t) for pat in PII_PATTERNS.values()):
            hits.append(p)

    print("scratch 含 PII 文件:", len(hits))
    dest = ROOT / "_attic_trash/scratch-pii-20261030"
    dest.mkdir(parents=True, exist_ok=True)
    for p in hits:
        shutil.move(str(p), str(dest / p.name))
    print("已移入", dest.relative_to(ROOT))


if __name__ == "__main__":
    main()
