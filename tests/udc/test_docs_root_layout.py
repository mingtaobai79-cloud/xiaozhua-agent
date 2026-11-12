"""docs/ 根入口 README 必须与磁盘一致。

背景：`docs/` 是整个文档树的根，2026-11-07 前**没有 README.md**。
顶层 10 份几乎全是"规则"文档（东西该放哪、怎么算合格），不是"内容"，
其中 6 份 `git grep` 零命中——不是没用，是没人链接规则。
补入口的目的就是让"我要找 X 该去哪"有唯一答案。

判据：
- §一 表每行字节/行数 == 磁盘
- 「合计 N 份 / X B」== 实算
- 每份顶层 .md 都在 README 里出现
- §二 每个子目录的 md 数 == 实算（含子目录）
- §二 里标 ✅ 的子目录必须真有 README/INDEX
- 规则文档零引用但不能删：REPO-INCIDENT 等仍在盘
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs"

ROW = re.compile(r"^\|\s*`([^`]+\.md)`\s*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|", re.M)
# 第三列是入口状态：✅ 有入口 / ❌ 刻意无入口（1 份，加 README 是过度设计）/
# ⚙ 图例（归档区不当导读入口，但需要一份说明"四个前缀是什么意思"，见 docs/ledger/README.md）。
# 2026-11-07 加 ⚙：ledger/ 补的是图例不是入口，用 ✅ 会谎称它成了导航起点。
SUBDIR_ROW = re.compile(
    r"^\|\s*`([a-z0-9\-]+)/`\s*\|\s*([\d,]+)\s*\|\s*(✅|❌|⚙)[^|]*\|", re.M)

# 顶层必须存在的规则文档（零引用也不许删）
PROTECTED = [
    "ARCHITECTURE.md",
    "REPO-LAYOUT.md",
    "KNOWLEDGE-GOVERNANCE.md",
    "KNOWLEDGE-LANDING-RULES.md",
    "SKILL-DISTRIBUTION.md",
    "REPO-INCIDENT-20261018.md",
]


def _readme() -> str:
    p = D / "README.md"
    assert p.exists(), "缺 docs/README.md（文档树根入口）"
    return p.read_text(encoding="utf-8")


def _md_count(d: Path) -> int:
    return sum(1 for _ in d.rglob("*.md"))


def test_top_level_table_matches_disk():
    rows = ROW.findall(_readme())
    assert len(rows) == 10, "顶层表只解析出 %d 行（应有 10 行）" % len(rows)
    bad = []
    for name, size_s, lines_s in rows:
        p = D / name
        if not p.exists():
            bad.append("%s: 表里登记了但文件不存在" % name)
            continue
        size = p.stat().st_size
        nlines = p.read_bytes().count(bytes([10]))
        if size != int(size_s.replace(",", "")):
            bad.append("%s: 表写 %s B 磁盘 %d" % (name, size_s, size))
        if nlines != int(lines_s.replace(",", "")):
            bad.append("%s: 表写 %s 行 磁盘 %d" % (name, lines_s, nlines))
    assert not bad, "docs/ 顶层规模表已腐坏：\n  " + "\n  ".join(bad)


def test_total_matches_disk():
    m = re.search(r"合计 \*\*(\d+) 份 / ([\d,]+) B\*\*", _readme())
    assert m, "README 里找不到「合计 N 份 / X B」声明"
    claimed_n, claimed = int(m.group(1)), int(m.group(2).replace(",", ""))
    files = sorted(p for p in D.glob("*.md") if p.name != "README.md")
    assert len(files) == claimed_n, "声称 %d 份，磁盘 %d 份" % (claimed_n, len(files))
    real = sum(p.stat().st_size for p in files)
    assert real == claimed, "声称合计 %d B，磁盘实算 %d B" % (claimed, real)


def test_readme_mentions_every_top_level_doc():
    text = _readme()
    missing = sorted(
        p.name for p in D.glob("*.md") if p.name != "README.md" and p.name not in text
    )
    assert not missing, "顶层文档没在根入口里出现：%s" % missing


def test_subdir_counts_match_disk():
    """§二 每个子目录的 md 数（含子目录）必须与磁盘一致。"""
    rows = SUBDIR_ROW.findall(_readme())
    assert len(rows) == 7, "子目录表只解析出 %d 行（应有 7 行）" % len(rows)
    bad = []
    for name, count_s, _mark in rows:
        p = D / name
        if not p.is_dir():
            bad.append("%s/: 表里登记了但目录不存在" % name)
            continue
        real = _md_count(p)
        if real != int(count_s.replace(",", "")):
            bad.append("%s/: 表写 %s 份 磁盘 %d 份" % (name, count_s, real))
    assert not bad, "docs/ 子目录计数已漂移：\n  " + "\n  ".join(bad)


def test_subdir_entry_marks_are_truthful():
    """§二 标 ✅ 的子目录必须真有入口文件，标 ❌ 的必须真没有。"""
    rows = SUBDIR_ROW.findall(_readme())
    bad = []
    for name, _count, mark in rows:
        p = D / name
        has = any((p / f).is_file() for f in ("README.md", "INDEX.md"))
        if mark == "✅" and not has:
            bad.append("%s/: README 标 ✅ 但没有入口文件" % name)
        if mark == "❌" and has:
            bad.append("%s/: README 标 ❌ 但有入口文件（该更新标注）" % name)
    assert not bad, "入口标注与磁盘不符：\n  " + "\n  ".join(bad)


def test_protected_rule_docs_still_exist():
    """零引用的规则文档不许删：零引用是因为没人链接规则，不是因为规则没用。"""
    missing = [f for f in PROTECTED if not (D / f).is_file()]
    assert not missing, "这些规则文档被删了（它们零引用但是规则，不能删）：%s" % missing
