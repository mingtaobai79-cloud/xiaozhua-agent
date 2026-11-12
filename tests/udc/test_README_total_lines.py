"""目录级「合计 N 份 / X B」声明的通用闸门。

**为什么需要它：** 本系列已经有 40+ 个入口 README，每个都在头部或表尾写一句
`合计 **N 份 / X B**`。此前只有 `test_entry_files_covered.py` 会核对**表格里的每一行**，
但**那句合计行不在它的扫描范围里** —— 于是出现一类沉默腐坏：
表内 9 行全对、合计行写着 8 份，闸门全绿，读的人却拿错总量。

本轮实测：8 处「合计 **N 份 / X B**」声明里 7 处正确、1 处（entity/）在加第 10 份文件时漏更新。
这说明**数字本身大体是可信的**，缺的是"每次加文件都会被提醒"的机制。

**口径（必须与写数字的人一致，否则会周期性误报）：**
- 默认 `不含本 README`：`N` 与 `X` 都不算 README 自身。这是全库主流写法。
- `含子目录 = False` 时只统计 `*.glob("*.md")`（顶层）。
- 若某个 README 明确写「含子目录」，用 `RECURSIVE` 白名单逐个登记；
  **不许自己猜**——猜错会把这个闸门变成误报源。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 「合计 **N 份 / X B**」
TOTAL = re.compile(r"合计\s*\*\*\s*(\d+)\s*份\s*/\s*([\d,]+)\s*B\s*\*\*")

# 这些 README 的合计口径是「含子目录」。加新条目要在此处登记 + 写明理由。
RECURSIVE = {
    # core/facts/udc/：8 子域 + 5 顶层文档，子域内部还有 README，必须递归
    "core/facts/udc/README.md": "8 子域 + 5 顶层文档，子域内还有 README",
    # core/facts/udc/setting/：15 份分散在 10 个 tab 子目录里，顶层只有 2 份
    "core/facts/udc/setting/README.md": "10 个 tab 子目录，顶层只有 2 份",
    # docs/README.md 的合计只算**顶层 10 份**（不含子目录），故意不递归
}

# 明确「不递归」的目录：合计只算顶层
TOPLEVEL_ONLY = {
    "docs/README.md": "顶层 10 份规则文档，子目录各自有自己的 README",
}

SKIP = ("_attic_pending", "_attic_trash", "node_modules", "/.venv/", "/.git/")


def _readmes():
    for f in ROOT.rglob("README.md"):
        rel = f.relative_to(ROOT).as_posix()
        if any(s in "/" + rel for s in SKIP):
            continue
        yield f, rel


def _measure(readme: Path, recursive: bool):
    d = readme.parent
    fs = [x for x in ((d.rglob("*.md") if recursive else d.glob("*.md"))) if x.is_file()]
    # 口径：不含本 README 自身
    fs = [x for x in fs if x != readme]
    return len(fs), sum(x.stat().st_size for x in fs)


def test_all_total_lines_match_disk():
    """每处「合计 N 份 / X B」都要与磁盘一致（去掉 README 自身）。"""
    bad, seen = [], []
    for readme, rel in _readmes():
        try:
            t = readme.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in TOTAL.finditer(t):
            n, b = int(m.group(1)), int(m.group(2).replace(",", ""))
            recursive = rel in RECURSIVE
            rn, rb = _measure(readme, recursive)
            seen.append(rel)
            if (n, b) != (rn, rb):
                scope = "含子目录" if recursive else "顶层"
                bad.append("%s: 声明 %d 份 / %s B，磁盘(%s, 不含本 README) %d 份 / %d B"
                           % (rel, n, f"{b:,}", scope, rn, rb))
    assert not bad, (
        "「合计」声明已漂移（加/删文件后忘了更新汇总行）：\n  " + "\n  ".join(bad))
    # 至少要有若干处被核对到，否则正则失效也能过
    assert len(seen) >= 6, "只核对到 %d 处合计声明，正则可能已失效" % len(seen)


def test_recursive_whitelist_entries_still_have_totals():
    """白名单里的 README 必须仍写着合计 —— 否则白名单就是死配置。"""
    for rel, why in RECURSIVE.items():
        f = ROOT / rel
        assert f.is_file(), "RECURSIVE 白名单里的 %s 不存在（%s）" % (rel, why)
        t = f.read_text(encoding="utf-8", errors="replace")
        assert TOTAL.search(t), "%s 已没有「合计 N 份 / X B」行，白名单该删（%s）" % (rel, why)


def test_toplevel_only_entries_do_not_recurse():
    """TOPLEVEL_ONLY 里的目录，其合计必须等于顶层（不含 README），不能等于递归值。"""
    for rel, why in TOPLEVEL_ONLY.items():
        f = ROOT / rel
        assert f.is_file(), "TOPLEVEL_ONLY 里的 %s 不存在（%s）" % (rel, why)
        t = f.read_text(encoding="utf-8", errors="replace")
        m = TOTAL.search(t)
        assert m, "%s 没有合计行（%s）" % (rel, why)
        n, b = int(m.group(1)), int(m.group(2).replace(",", ""))
        top_n, top_b = _measure(f, False)
        rec_n, rec_b = _measure(f, True)
        assert (n, b) == (top_n, top_b), (
            "%s 的合计不是顶层口径：声明 %d/%s，顶层 %d/%d，递归 %d/%d"
            % (rel, n, f"{b:,}", top_n, top_b, rec_n, rec_b))
        assert (rec_n, rec_b) != (top_n, top_b), (
            "%s 顶层与递归恰好相等，TOPLEVEL_ONLY 这条白名单已无意义，应删除" % rel)


def test_no_total_line_uses_count_newline_convention():
    """正文若自述「N 行」，必须与 splitlines() 一致 —— 不许用 count(b"\\n")。

    第 46 轮踩过：全库 16 份 md 没有结尾换行，count 与 splitlines 差 1。
    这里只查一个最容易出问题的位置：合计行紧邻的「合计 N 份 / X B / Y 行」写法。
    """
    pat = re.compile(r"合计\s*\*\*\s*\d+\s*份\s*/\s*[\d,]+\s*B\s*(?:/\s*([\d,]+)\s*行)?")
    bad = []
    for readme, rel in _readmes():
        t = readme.read_text(encoding="utf-8", errors="replace")
        for m in pat.finditer(t):
            if not m.group(1):
                continue
            claimed = int(m.group(1).replace(",", ""))
            d = readme.parent
            fs = [x for x in (d.rglob("*.md") if rel in RECURSIVE else d.glob("*.md"))
                  if x.is_file() and x != readme]
            real = sum(len(x.read_bytes().decode("utf-8", errors="replace").splitlines())
                       for x in fs)
            if claimed != real:
                bad.append("%s: 声明 %d 行，splitlines 实测 %d 行" % (rel, claimed, real))
    assert not bad, "合计行的行数口径不一致：\n  " + "\n  ".join(bad)
