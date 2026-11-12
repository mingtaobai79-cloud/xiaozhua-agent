"""docs/capability/ 的入口 README 必须与磁盘一致。

背景：这是目标架构目录本身（ROADMAP-v2 + A1–A8 + STATUS），2026-11-07 前没有入口文件。
补了 README.md 后，10 份的字节数/行数是人工维护的表，改任一份就会腐坏。
A1–A8 的 sha256 已由 tests/udc/test_capability_status_snapshot.py 守着（STATUS 表），
本文件只守「入口 README 说的规模和清单对不对」。

判据：
- §一 表里每行的字节数 / 行数 == 磁盘
- 正文「合计 N 份 / X B」== 磁盘实算
- 目录下每个 .md（除 README）都在 README 里出现
- A1–A8 八件套齐全（少一件说明有人搬走了架构文档）
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAP = ROOT / "docs" / "capability"

# `| \`file.md\` | A1 | 16,843 | 228 | ... |`
ROW = re.compile(r"^\|\s*`([^`]+\.md)`\s*\|\s*[^|]*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|", re.M)

A_SERIES = [
    "ARCHITECTURE.md",
    "MODULE-INVENTORY.md",
    "CAPABILITY-MODEL.md",
    "EVIDENCE-MODEL.md",
    "VERSION-COMPATIBILITY.md",
    "SANDBOX-CONTRACT.md",
    "TOOL-SKILL-MODULE.md",
    "AGENT-ADAPTER.md",
]


def _readme() -> str:
    p = CAP / "README.md"
    assert p.exists(), "缺 docs/capability/README.md（目标架构目录的入口）"
    return p.read_text(encoding="utf-8")


def test_readme_size_table_matches_disk():
    """§一 表的字节数与行数必须与磁盘一致。"""
    rows = ROW.findall(_readme())
    assert len(rows) == 10, "规模表只解析出 %d 行（应有 10 行）" % len(rows)
    bad = []
    for name, size_s, lines_s in rows:
        p = CAP / name
        if not p.exists():
            bad.append("%s: 表里登记了但文件不存在" % name)
            continue
        size = p.stat().st_size
        nlines = p.read_bytes().count(b"\n")
        if size != int(size_s.replace(",", "")):
            bad.append("%s: 表写 %s B 磁盘 %d" % (name, size_s, size))
        if nlines != int(lines_s.replace(",", "")):
            bad.append("%s: 表写 %s 行 磁盘 %d" % (name, lines_s, nlines))
    assert not bad, "docs/capability 规模表已腐坏：\n  " + "\n  ".join(bad)


def test_readme_total_matches_disk():
    """正文「合计 10 份 / 103,894 B」必须等于实算。"""
    m = re.search(r"合计 \*\*(\d+) 份 / ([\d,]+) B\*\*", _readme())
    assert m, "README 里找不到「合计 N 份 / X B」声明"
    claimed_n, claimed = int(m.group(1)), int(m.group(2).replace(",", ""))
    files = sorted(p for p in CAP.glob("*.md") if p.name != "README.md")
    assert len(files) == claimed_n, "声称 %d 份，磁盘 %d 份" % (claimed_n, len(files))
    real = sum(p.stat().st_size for p in files)
    assert real == claimed, "声称合计 %d B，磁盘实算 %d B" % (claimed, real)


def test_readme_mentions_every_doc():
    """目录下每个 .md（除 README）都必须在入口里出现。"""
    text = _readme()
    missing = sorted(
        p.name for p in CAP.glob("*.md") if p.name != "README.md" and p.name not in text
    )
    assert not missing, "这些架构文档没在入口 README 里出现：%s" % missing


def test_a_series_is_complete():
    """A1–A8 八件套必须齐全——少一件说明有人把目标架构搬走了。"""
    missing = [n for n in A_SERIES if not (CAP / n).exists()]
    assert not missing, "A1-A8 八件套缺：%s" % missing
