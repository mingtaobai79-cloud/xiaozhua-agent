"""docs/audit/role/ 的入口 README 必须与磁盘一致，且推翻链登记完整。

背景：这 9 份是角色域审计的阶段链（P0→P1→P2→P3→P3b→S5）。2026-11-07 前没有入口，
而这条链里**有三处结论被后续文件推翻**——按序号直线读会读到已被证伪的判断。
入口 README 的核心价值就是把这些推翻点标出来。

判据：
- §一 表每行字节/行数 == 磁盘
- 「合计 N 份 / X B」== 实算
- 每份 .md 都在 README 里出现
- 三处已知推翻的关键词仍在原文里（README 说"原文保留就地标注"，若有人删了原文这条会红）
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "audit" / "role"

ROW = re.compile(r"^\|\s*`([^`]+\.md)`\s*\|\s*[^|]*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|", re.M)

PHASES = [
    "P0-role-object-model.md",
    "P1-role-frontend-call-chain.md",
    "P1-LIVE-GAP-MATRIX.md",
    "P1-STRUCTURE-SUPPLEMENT.md",
    "P1-FUNCAUTH-BRANCH-TRACE.md",
    "P2-role-live-readback.md",
    "P3-role-write-chain.md",
    "P3b-permission-panel-recheck.md",
    "S5-role-write-chain-closure.md",
]

# README §二 声称的三处推翻，锚在原文里的关键词
OVERRIDES = [
    ("P3-role-write-chain.md", "23:57 总更正"),      # 推翻①+② 的就地标注块
    ("P3-role-write-chain.md", "permissionLook"),    # 推翻① 更正后的真因
    ("P1-STRUCTURE-SUPPLEMENT.md", "不能"),          # 推翻③ javap sha 不能自证来源
]


def _readme() -> str:
    p = D / "README.md"
    assert p.exists(), "缺 docs/audit/role/README.md（阶段链入口）"
    return p.read_text(encoding="utf-8")


def test_readme_table_matches_disk():
    rows = ROW.findall(_readme())
    assert len(rows) == 9, "阶段表只解析出 %d 行（应有 9 行）" % len(rows)
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
    assert not bad, "阶段表已腐坏：\n  " + "\n  ".join(bad)


def test_readme_total_matches_disk():
    m = re.search(r"合计 \*\*(\d+) 份 / ([\d,]+) B\*\*", _readme())
    assert m, "README 里找不到「合计 N 份 / X B」声明"
    claimed_n, claimed = int(m.group(1)), int(m.group(2).replace(",", ""))
    files = sorted(p for p in D.glob("*.md") if p.name != "README.md")
    assert len(files) == claimed_n, "声称 %d 份，磁盘 %d 份" % (claimed_n, len(files))
    real = sum(p.stat().st_size for p in files)
    assert real == claimed, "声称合计 %d B，磁盘实算 %d B" % (claimed, real)


def test_readme_mentions_every_report():
    text = _readme()
    missing = sorted(
        p.name for p in D.glob("*.md") if p.name != "README.md" and p.name not in text
    )
    assert not missing, "这些阶段报告没在入口 README 里出现：%s" % missing


def test_override_annotations_still_present():
    """README 说「原文保留、错误处就地标注」——标注块若被清理掉，推翻链就断在入口里。"""
    bad = []
    for name, needle in OVERRIDES:
        p = D / name
        if not p.exists():
            bad.append("%s: 文件不存在" % name)
            continue
        if needle not in p.read_text(encoding="utf-8", errors="replace"):
            bad.append("%s: 找不到 %r（推翻链的就地标注被删了？）" % (name, needle))
    assert not bad, "推翻链标注缺失：\n  " + "\n  ".join(bad)


def test_phase_chain_is_complete():
    """P0→S5 阶段链必须齐全——少一份说明有人把证据底搬走了。"""
    missing = [n for n in PHASES if not (D / n).exists()]
    assert not missing, "阶段链缺：%s" % missing
