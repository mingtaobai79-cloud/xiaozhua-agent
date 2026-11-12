"""docs/audit/artifacts/api-usage/ 的入口 README 必须与磁盘一致。

10 个域文件 / 327 接口 / 2,101 方法 / 3,455,938 B（3.30 MB）——artifacts/ 下体量最大的取证目录，
2026-11-07 前零入口。自动生成物（tools/core/platform/emit_api_usage.py），勿手改。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "audit" / "artifacts" / "api-usage"

# 两处只有 `## \`Xxx\`` 才是接口卡；`## 怎么调` / `## 卡片怎么读` 不是
IFACE = re.compile(r"^## `([A-Za-z_][A-Za-z0-9_.]*)`\s*$", re.M)
METHOD = re.compile(r"^### `([A-Za-z_][A-Za-z0-9_]*)` → `", re.M)
ROW = re.compile(
    r"^\|\s*`([a-z0-9]+\.md)`\s*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|",
    re.M)


def _readme():
    p = D / "README.md"
    assert p.exists(), "缺 api-usage/README.md"
    return p.read_text(encoding="utf-8")


def _domain_files():
    return sorted(p for p in D.glob("*.md") if p.name != "README.md")


def _ifaces(p):
    return len(IFACE.findall(p.read_text(encoding="utf-8", errors="replace")))


def _methods(p):
    return len(METHOD.findall(p.read_text(encoding="utf-8", errors="replace")))


def test_counts_and_total():
    m = re.search(r"\*\*(\d+) 个域文件 / (\d+) 个接口 / ([\d,]+) 个方法 / ([\d,]+) B", _readme())
    assert m, "README 找不到「N 个域文件 / N 个接口 / N 个方法 / X B」声明行"
    files = _domain_files()
    assert int(m.group(1)) == len(files), "声称 %s 个域文件，磁盘 %d 个" % (m.group(1), len(files))
    real_if = sum(_ifaces(p) for p in files)
    real_me = sum(_methods(p) for p in files)
    real_by = sum(p.stat().st_size for p in files)
    assert int(m.group(2)) == real_if, "声称 %s 个接口，实测 %d" % (m.group(2), real_if)
    assert int(m.group(3).replace(",", "")) == real_me, (
        "声称 %s 个方法，实测 %d" % (m.group(3), real_me))
    assert int(m.group(4).replace(",", "")) == real_by, (
        "声称合计 %s B，实测 %d B" % (m.group(4), real_by))


def test_table_matches_disk():
    rows = ROW.findall(_readme())
    assert len(rows) >= 10, "域表只解析出 %d 行（应 10 行）" % len(rows)
    bad = []
    for name, size_s, lines_s, if_s, me_s in rows:
        p = D / name
        if not p.is_file():
            bad.append("%s 不存在" % name)
            continue
        if _ifaces(p) != int(if_s):
            bad.append("%s 接口写 %s 实测 %d" % (name, if_s, _ifaces(p)))
        if _methods(p) != int(me_s):
            bad.append("%s 方法写 %s 实测 %d" % (name, me_s, _methods(p)))
        if p.stat().st_size != int(size_s.replace(",", "")):
            bad.append("%s 字节写 %s 实测 %d" % (name, size_s, p.stat().st_size))
        nl = p.read_bytes().count(bytes([10]))
        if nl != int(lines_s.replace(",", "")):
            bad.append("%s 行数写 %s 实测 %d" % (name, lines_s, nl))
    assert not bad, "域规模表已腐坏：\n  " + "\n  ".join(bad)
    # 表内合计行
    tot = re.search(r"\|\s*\*\*合计\*\*\s*\|\s*\*\*([\d,]+)\*\*\s*\|\s*\*\*([\d,]+)\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|\s*\*\*([\d,]+)\*\*", _readme())
    assert tot, "域表缺「合计」行"
    assert int(tot.group(1).replace(",", "")) == sum(
        int(r[1].replace(",", "")) for r in rows), "合计字节 ≠ 各行之和"
    assert int(tot.group(2).replace(",", "")) == sum(
        int(r[2].replace(",", "")) for r in rows), "合计行数 ≠ 各行之和"
    assert int(tot.group(3)) == sum(int(r[3]) for r in rows), "合计接口 ≠ 各行之和"
    assert int(tot.group(4).replace(",", "")) == sum(int(r[4]) for r in rows), (
        "合计方法 ≠ 各行之和")


def test_no_orphan_files():
    """磁盘上每个域文件都必须在 README 表里出现（避免"偷偷多一个域"）。"""
    table = {r[0] for r in ROW.findall(_readme())}
    disk = {p.name for p in _domain_files()}
    assert disk == table, (
        "磁盘与 README 表不一致：磁盘多出 %s / 表多出 %s" % (sorted(disk - table), sorted(table - disk)))


def test_counterintuitive_invariants_documented():
    """三条最易误用的判据必须还在 README 里。"""
    text = _readme()
    # ① 生成器认识 14 个域名、只落盘 10 个 → 别去补第 11 个
    assert "DOMAIN_OF" in text and "14" in text, (
        "README 没说明生成器 DOMAIN_OF 认识 14 个域名而落盘 10 个（会误导人去补空文件）")
    # ② 数接口不能用 ^##  ——每份多两个非接口段
    assert "卡片怎么读" in text and "多算 2" in text, (
        "README 没写「用 ^## 数接口会多算 2」这条坑")
    # ③ 字段只有名字+类型，没有业务含义
    assert "没有注释" in text or "无注释" in text, "README 没写字段无注释这条诚实边界"


def test_generator_and_no_live_stated():
    text = _readme()
    assert "emit_api_usage.py" in text, "README 没给生成器路径（防手改）"
    assert "自动生成" in text, "README 没标明这是自动生成物"
    assert "没有一次 LIVE" in text or "无 LIVE" in text, "README 没写「无一次 LIVE 调用」"
    g = ROOT / "tools" / "core" / "platform" / "emit_api_usage.py"
    assert g.is_file(), "生成器 emit_api_usage.py 不见了（README 指向它会成为死引用）"
