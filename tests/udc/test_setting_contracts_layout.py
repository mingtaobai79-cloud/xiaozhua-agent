"""docs/operation-contracts/udc/setting/ 的入口 README 必须与磁盘一致。

背景：这一域 11 份契约全是同批交付的，没人给过入口。2026-11-07 补了 README.md，
把 11 份按协议分四组列表。表是人工维护的，改任一契约（或新增 tab）就会腐坏。

判据：
- 表里每行的字节数 / 行数 == 磁盘
- 目录下每个 .md（除 README）都被 README 提到，否则等于没入口
- 11 份合计字节数与正文声称的一致
- 被测试/skill 直接引用的 4 份仍然存在（路径常量不能被搬走）
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "operation-contracts" / "udc" / "setting"

# `| \`file.md\` | GraphQL | 枚举 | 表 | 4,112 | 90 |`
ROW = re.compile(
    r"^\|\s*`([^`]+\.md)`\s*\|[^|]*\|[^|]*\|[^|]*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|$",
    re.M,
)

# 被外部按精确路径引用的（tests / skills / tools），搬走就断链
PINNED = [
    "enum-contracts.md",
    "custom-object-contracts.md",
    "serial-contracts.md",
    "qrcode-contracts.md",
]


def _readme() -> str:
    p = D / "README.md"
    assert p.exists(), "缺 docs/operation-contracts/udc/setting/README.md（目录入口）"
    return p.read_text(encoding="utf-8")


def test_readme_table_matches_disk():
    """11 行表的字节数与行数必须与磁盘一致。"""
    rows = ROW.findall(_readme())
    assert len(rows) == 11, "契约表只解析出 %d 行（应有 11 行，格式被改坏了？）" % len(rows)
    bad = []
    for name, size_s, lines_s in rows:
        p = D / name
        if not p.exists():
            bad.append("%s: 表里登记了但文件不存在" % name)
            continue
        size = p.stat().st_size
        nlines = p.read_bytes().count(b"\n")
        if size != int(size_s.replace(",", "")):
            bad.append("%s: 表写 %s B 磁盘 %d" % (name, size_s, size))
        if nlines != int(lines_s):
            bad.append("%s: 表写 %s 行 磁盘 %d" % (name, lines_s, nlines))
    assert not bad, "契约表已腐坏：\n  " + "\n  ".join(bad)


def test_readme_total_bytes_matches_disk():
    """正文声称的合计字节数必须等于 11 份之和。"""
    text = _readme()
    m = re.search(r"合计 \*\*(\d+) 份 / ([\d,]+) B\*\*", text)
    assert m, "README 里找不到「合计 N 份 / X B」的声明"
    claimed_n = int(m.group(1))
    claimed = int(m.group(2).replace(",", ""))
    files = sorted(p for p in D.glob("*.md") if p.name != "README.md")
    assert len(files) == claimed_n, "声称 %d 份，磁盘上 %d 份" % (claimed_n, len(files))
    real = sum(p.stat().st_size for p in files)
    assert real == claimed, "声称合计 %d B，磁盘实算 %d B" % (claimed, real)


def test_readme_mentions_every_contract():
    """目录下每个 .md（除 README）都必须在入口里出现。"""
    text = _readme()
    missing = sorted(
        p.name for p in D.glob("*.md") if p.name != "README.md" and p.name not in text
    )
    assert not missing, "这些契约没在入口 README 里出现：%s" % missing


def test_externally_referenced_contracts_still_exist():
    """被测试/skill/tools 按精确路径引用的 4 份不能被搬走或改名。"""
    missing = [n for n in PINNED if not (D / n).exists()]
    assert not missing, "这些契约被外部按路径引用，不能删/搬：%s" % missing
