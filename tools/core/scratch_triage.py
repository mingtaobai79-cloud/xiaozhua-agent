# -*- coding: utf-8 -*-
"""对 scratch/ 根目录的散落脚本做「一次性 vs 有证据价值」分类（只读）。

判定不看文件名第一印象，看三条硬信号：
  ① 是否被 tests/ components/ core/ tools/ scripts/ 按路径引用（引用则保留）
  ② 是否含 PII（客户 appId / 组织 / 实例名）——含 PII 的一次性脚本必须处理
  ③ 是否含「证据产出」动作（写 json 到 *-evidence/、抓包、反编译）
     —— 这类即便没人引用也可能被事实格当出处，需人工确认

输出三组：KEEP_WITH_EVIDENCE / DELETE_CANDIDATE / NEEDS_REVIEW
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tests.test_deidentification import PII_PATTERNS  # noqa: E402

SCAN_DIRS = ["tests", "components", "core", "tools", "scripts"]


def referenced_names() -> set[str]:
    """收集代码里出现的 scratch/xxx.py 名字。"""
    names = set()
    pat = re.compile(r"scratch/([\w\-.]+\.py)")
    for d in SCAN_DIRS:
        for p in (ROOT / d).rglob("*.py"):
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            names.update(pat.findall(t))
    return names


def main() -> None:
    scratch = ROOT / "scratch"
    refd = referenced_names()
    keep_evi, delc, review = [], [], []

    for p in sorted(scratch.glob("*.py")):
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        has_pii = any(pat.search(t) for pat in PII_PATTERNS.values())
        writes_evidence = bool(re.search(r"-evidence/|evidence/|\.json['\"]", t))
        is_referenced = p.name in refd

        if is_referenced:
            keep_evi.append((p.name, "被引用"))
        elif writes_evidence and has_pii:
            review.append((p.name, "产证据+含PII"))
        elif writes_evidence:
            review.append((p.name, "产证据"))
        else:
            delc.append((p.name, "含PII" if has_pii else "一次性"))

    print(f"scratch 根脚本: {len(keep_evi) + len(delc) + len(review)}")
    print(f"  被引用(保留):      {len(keep_evi)}")
    print(f"  产证据(需确认):    {len(review)}")
    print(f"  删除候选:          {len(delc)}  其中含PII {sum(1 for _, r in delc if 'PII' in r)}")

    print("\n被引用的:", [n for n, _ in keep_evi][:20])
    print("\n删除候选样例:", [n for n, _ in delc][:25])


if __name__ == "__main__":
    main()
