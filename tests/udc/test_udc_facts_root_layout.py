"""core/facts/udc/ 的事实层总入口必须与磁盘一致。

本目录 157 份 / 1,388,079 B，8 个子域 + 5 份顶层文档，2026-11-07 前零入口。

最重要的两条结构事实，本测试守着不许被"顺手整理掉"：
1. **微流程内容散在三处**（core/facts 62 份 / operation-contracts 25 份 /
   docs/audit/udc-semantics 99 份，合计 1.86 MB，互相几乎不引用）。
   这不是重复写，是「取证 → 提炼 → 定契约」三个阶段。合并会丢追溯链。
2. **零引用 ≠ 可删**：`page/detail-page.md`（25,805 B）实测零外部引用，
   但它是 page/ 三份之一，另两份与它同主题。
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "core" / "facts" / "udc"

ROW = re.compile(r"^\|\s*`([a-z-]+)/`\s*\|\s*(\d+)\s*\|\s*([\d,]+)\s*\|\s*(✅|❌)\s*\|", re.M)
TOP = re.compile(r"^\|\s*`([A-Za-z0-9_-]+\.md)`\s*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|", re.M)


def _readme():
    p = D / "README.md"
    assert p.exists(), "缺 core/facts/udc/README.md（事实层总入口）"
    return p.read_text(encoding="utf-8")


def _subs():
    return sorted(d for d in D.iterdir() if d.is_dir())


def _stat(d, exclude_self=False):
    """exclude_self=True 时排除该目录自己的 README.md/INDEX.md——
    它们是导航，不是被登记的内容（否则每加一份入口就要重算所有合计）。"""
    files = [p for p in d.rglob("*.md")]
    if exclude_self:
        top = {d / "README.md", d / "INDEX.md"}
        files = [p for p in files if p not in top]
    return len(files), sum(p.stat().st_size for p in files)


def test_subdomain_table_matches_disk():
    rows = ROW.findall(_readme())
    assert len(rows) == 8, "子域表解析出 %d 行（应有 8 个子域）" % len(rows)
    bad = []
    for name, n_s, size_s, mark in rows:
        d = D / name
        if not d.is_dir():
            bad.append("%s/: 目录不存在" % name)
            continue
        n, size = _stat(d)
        if n != int(n_s):
            bad.append("%s/: 表写 %s 份 磁盘 %d 份" % (name, n_s, n))
        if size != int(size_s.replace(",", "")):
            bad.append("%s/: 表写 %s B 磁盘 %d B" % (name, size_s, size))
        has = (d / "README.md").is_file() or (d / "INDEX.md").is_file()
        if has != (mark == "✅"):
            bad.append("%s/: 表标 %s 但磁盘%s入口" % (
                name, mark, "有" if has else "无"))
    assert not bad, "子域规模表已腐坏：\n  " + "\n  ".join(bad)


def test_total_matches_disk():
    m = re.search(r"合计 \*\*(\d+) 份 / ([\d,]+) B\*\*", _readme())
    assert m, "README 里找不到「合计 N 份 / X B」"
    n, size = _stat(D, exclude_self=True)
    assert int(m.group(1)) == n, "声称 %s 份，磁盘 %d 份" % (m.group(1), n)
    assert int(m.group(2).replace(",", "")) == size, (
        "声称合计 %s B，磁盘实算 %d B" % (m.group(2), size))


def test_top_level_files_table_matches_disk():
    rows = TOP.findall(_readme())
    assert len(rows) == 5, "顶层文档表解析出 %d 行（应有 5 份）" % len(rows)
    bad = []
    for name, size_s, lines_s, refs_s in rows:
        p = D / name
        if not p.is_file():
            bad.append("%s 不存在" % name)
            continue
        if p.stat().st_size != int(size_s.replace(",", "")):
            bad.append("%s 字节表写 %s 磁盘 %d" % (name, size_s, p.stat().st_size))
        nl = p.read_bytes().count(bytes([10]))
        if nl != int(lines_s.replace(",", "")):
            bad.append("%s 行数表写 %s 磁盘 %d" % (name, lines_s, nl))
    assert not bad, "顶层文档表已腐坏：\n  " + "\n  ".join(bad)


def test_all_subdomains_named():
    text = _readme()
    missing = [d.name for d in _subs() if "`%s/`" % d.name not in text]
    assert not missing, "这些子域没在入口 README 里出现：%s" % missing


def test_three_way_microflow_split_is_declared():
    """微流程散在三处是本目录最大的结构性事实，入口必须说清 + 三处都还真实存在。"""
    text = _readme()
    for path in ("core/facts/udc/microflow/",
                 "docs/operation-contracts/udc/microflow/",
                 "docs/audit/udc-semantics/"):
        assert path in text, "README 没提到微流程所在的 %s" % path
    assert "三个阶段" in text or "取证" in text, (
        "README 没说明三处是不同阶段的产物，读者会以为可以合并")
    for path in ("core/facts/udc/microflow",
                 "docs/operation-contracts/udc/microflow",
                 "docs/audit/udc-semantics"):
        d = ROOT / path
        assert d.is_dir(), "%s 不见了" % path
        n = len(list(d.rglob("*.md")))
        assert n >= 20, "%s 只剩 %d 份 md，与 README 描述不符" % (path, n)


def test_zero_ref_file_not_deleted():
    """page/detail-page.md 零外部引用但不可删——README 明确解释了理由，文件必须还在。"""
    p = D / "page" / "detail-page.md"
    assert p.is_file(), (
        "page/detail-page.md 不见了。它实测零外部引用，但属 page/ 三份之一，"
        "另两份与它同主题——零引用 ≠ 可删")
    text = _readme()
    assert "detail-page.md" in text or "page/detail-page.md" in text, (
        "README 没登记 detail-page.md 的零引用情况")
    assert "零引用" in text and "可删" in text, (
        "README 没有「零引用 ≠ 可删」的判据")
