"""core/facts/udc/entity/ 的入口 README 必须与磁盘一致，且"静默成功"坑登记完整。

背景：这 9 份是 UDC 实体域事实格，2026-11-07 前没有入口。目录特征是两个：
1. **两种体裁混在一起**——`create.md` / `attribute-create.md` 是九段式能力事实文档，
   其余 7 份是取证长出来的坑清单。用同一套期待读会失望，入口必须点明。
2. **五处「静默成功」坑**（接口成功、DB 有行、页面 0 条）是本域最贵的知识。
   散落在正文里就等于没有，入口必须集中列。

判据：
- §一 表每行字节/行数 vs 磁盘
- 「合计 N 份 / X B」vs 实算
- 每份 .md 都在 README 里出现
- 五处坑的原文关键词仍在对应文件里（README 是二次表述，原文才是证据）
- `rules-microflow.md` 仍在盘且 README 里说明了它为什么不能删（P3 前提）
"""
import re
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _facts_dir_rules import count_top, lines_of  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "core" / "facts" / "udc" / "entity"

ROW = re.compile(r"^\|\s*`([^`]+\.md)`\s*\|\s*[^|]*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|", re.M)

# README §二 的五个「静默成功」坑，锚在原文里各自的关键词
PITFALLS = [
    ("entity-update-payload.md", "BOOT_3000"),
    ("event-dto-binding.md", "udc_data_transfer_object"),
    ("refer-event-index-tabs.md", "sourceId 过滤不生效"),
    ("scalability.md", "create（udcEntityPost）不触发"),
    ("refer-event-index-tabs.md", "反序列化为String类型时失败"),
]


def _readme() -> str:
    p = D / "README.md"
    assert p.exists(), "缺 core/facts/udc/entity/README.md（实体域入口）"
    return p.read_text(encoding="utf-8")


def test_readme_table_matches_disk():
    rows = ROW.findall(_readme())
    assert len(rows) == 9, "表只解析出 %d 行（应有 9 行）" % len(rows)
    bad = []
    for name, size_s, lines_s in rows:
        p = D / name
        if not p.exists():
            bad.append("%s: 表里登记了但文件不存在" % name)
            continue
        size = p.stat().st_size
        nlines = lines_of(p)
        if size != int(size_s.replace(",", "")):
            bad.append("%s: 表写 %s B 磁盘 %d" % (name, size_s, size))
        if nlines != int(lines_s.replace(",", "")):
            bad.append("%s: 表写 %s 行 磁盘 %d" % (name, lines_s, nlines))
    assert not bad, "实体域规模表已腐坏：\n  " + "\n  ".join(bad)


def test_readme_total_matches_disk():
    m = re.search(r"合计 \*\*(\d+) 份 / ([\d,]+) B\*\*", _readme())
    assert m, "README 里找不到「合计 N 份 / X B」声明"
    claimed_n, claimed = int(m.group(1)), int(m.group(2).replace(",", ""))
    real_n, real = count_top(D)          # 口径见 tests/udc/_facts_dir_rules.py
    assert real_n == claimed_n, "声称 %d 份，磁盘 %d 份（顶层，不含 README）" % (claimed_n, real_n)
    assert real == claimed, "声称合计 %d B，磁盘实算 %d B" % (claimed, real)


def test_readme_mentions_every_fact():
    text = _readme()
    missing = sorted(
        p.name for p in D.glob("*.md") if p.name != "README.md" and p.name not in text
    )
    assert not missing, "这些事实格没在入口 README 里出现：%s" % missing


def test_silent_success_pitfalls_still_documented():
    """入口把五处「静默成功」坑集中列了，原文必须还在——README 是导航，原文才是证据。"""
    bad = []
    for name, needle in PITFALLS:
        p = D / name
        if not p.exists():
            bad.append("%s: 文件不存在" % name)
            continue
        if needle not in p.read_text(encoding="utf-8", errors="replace"):
            bad.append("%s: 找不到 %r" % (name, needle))
    assert not bad, "「静默成功」坑的原文证据缺失：\n  " + "\n  ".join(bad)


def test_merged_rules_microflow_is_kept():
    """P3 的 rules-microflow -> rule-domain 合并已完成，但原文件被测试按文件名锁着，不能删。"""
    merged = D / "rules-microflow.md"
    main = D / "rule-domain.md"
    assert merged.exists(), "rules-microflow.md 被删了，但 test_fact_discoverability 的 CRITICAL 锁着它"
    assert main.exists(), "rule-domain.md（合并后的主文档）不见了"
    head = merged.read_text(encoding="utf-8", errors="replace")[:400]
    assert "已并入" in head, "rules-microflow.md 头部的「已并入」指针丢了"
    assert "rules-microflow" in main.read_text(encoding="utf-8", errors="replace"), \
        "rule-domain.md 里没有反向登记来源（第 16 轮补过的反向指针纪律）"
