"""docs/audit/artifacts/service-flow-20261103/ 的入口 README 必须与磁盘一致。

17 份 / 5,377,950 B（5.13 MB）——本仓库单目录体量最大之一，2026-11-07 前零入口。
自动生成物（tools/core/platform/emit_service_flow.py），勿手改。

本测试守三件事：
1. 三张分组表的字节/行/类数 vs 磁盘（重新生成后会漂，必须同步）
2. **客户应用件只写"客户实例 A/B/C"，不许写真实文件名**（文件名含客户 ID，
   test_deidentification 的 KNOWN_NAME_VIOLATIONS 只冻结存量）
3. §一 那条"两层结构"的判据仍在——只扫 *Impl 会整个漏掉业务层，是本目录最易误用处
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "audit" / "artifacts" / "service-flow-20261103"

ROW = re.compile(r"^\|\s*`?([A-Za-z0-9_.-]*?(?:appservice|domain)\.md)`?\s*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|", re.M)
# 客户应用行只登记"字节/行/类"，文件名故意不写
CUST = re.compile(r"^\|\s*客户实例 ([ABC])（[^）]*）\s*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|\s*\**?(\d+)\**?\s*\|", re.M)


def _readme():
    p = D / "README.md"
    assert p.exists(), "缺 service-flow-20261103/README.md"
    return p.read_text(encoding="utf-8")


def _md():
    return sorted(p for p in D.glob("*.md") if p.name != "README.md")


def _classes(p):
    return len(re.findall(r"^## `", p.read_text(encoding="utf-8", errors="replace"), re.M))


def test_row_count_and_total():
    m = re.search(r"(\d+) 份 / \*\*([\d,]+) B", _readme())
    assert m, "README 找不到「N 份 / X B」"
    files = _md()
    assert int(m.group(1)) == len(files), "声称 %s 份 磁盘 %d 份" % (m.group(1), len(files))
    real = sum(p.stat().st_size for p in files)
    assert int(m.group(2).replace(",", "")) == real, (
        "声称合计 %s B 磁盘实算 %d B" % (m.group(2), real))


def test_platform_and_udc_tables_match_disk():
    rows = ROW.findall(_readme())
    assert len(rows) >= 14, "平台+UDC 表只解析出 %d 行（应 ≥14）" % len(rows)
    bad = []
    for name, size_s, lines_s, cls_s in rows:
        p = D / name
        if not p.is_file():
            bad.append("%s 不存在" % name)
            continue
        if p.stat().st_size != int(size_s.replace(",", "")):
            bad.append("%s 字节写 %s 磁盘 %d" % (name, size_s, p.stat().st_size))
        nl = p.read_bytes().count(bytes([10]))
        if nl != int(lines_s.replace(",", "")):
            bad.append("%s 行数写 %s 磁盘 %d" % (name, lines_s, nl))
        if _classes(p) != int(cls_s):
            bad.append("%s 类数写 %s 实测 %d" % (name, cls_s, _classes(p)))
    assert not bad, "分组规模表已腐坏：\n  " + "\n  ".join(bad)


def test_customer_rows_match_three_files():
    """客户应用 3 份按字节匹配（文件名不写在 README 里，只能按大小对位）。"""
    rows = CUST.findall(_readme())
    assert len(rows) == 3, "客户实例表解析出 %d 行（应有 3 行 A/B/C）" % len(rows)
    # 客户应用件的判据不是"最大三份"（udc-biz-domain.md 662 KB 比最小的客户件 161 KB 还大），
    # 而是文件头里 `jar = \`<xxx>-biz-1.0.<n>.jar\`` 且不属平台构件。
    cust_files = []
    for p in _md():
        head = p.read_text(encoding="utf-8", errors="replace")[:400]
        m = re.search(r"jar = `([^`]+)`", head)
        if not m:
            continue
        jar = m.group(1)
        if re.search(r"-1\.0\.\d+\.jar$", jar) and "appservice" not in jar and "domain" not in jar:
            cust_files.append(p)
    assert len(cust_files) == 3, "按 jar 头识别出 %d 份客户应用件（应有 3 份）" % len(cust_files)
    top3 = {p: (p.stat().st_size, _classes(p)) for p in cust_files}
    claimed = {}
    for tag, size_s, lines_s, cls_s in rows:
        claimed[int(size_s.replace(",", ""))] = (int(lines_s.replace(",", "")), int(cls_s))
    bad = []
    for p, (size, cls) in top3.items():
        if size not in claimed:
            bad.append("磁盘上 %.2f MB 的客户应用件在 README 客户表里对不上（表里字节 %s）"
                       % (size / 1048576, sorted(claimed)))
            continue
        want_lines, want_cls = claimed[size]
        nl = p.read_bytes().count(bytes([10]))
        if nl != want_lines:
            bad.append("%s 行数写 %d 磁盘 %d" % (p.name[:12], want_lines, nl))
        if cls != want_cls:
            bad.append("%s 类数写 %d 实测 %d" % (p.name[:12], want_cls, cls))
    assert not bad, "客户应用表已腐坏：\n  " + "\n  ".join(bad)


def test_no_customer_id_in_readme():
    """README 属结论区：不许出现客户应用 ID 或那三个真实文件名。"""
    text = _readme()
    bad = [p.name for p in D.glob("*.md")
           if re.search(r"(?:datamigration|znxmglpt|xiangmuguanli)\d{6,}", p.name)
           and p.name in text]
    assert not bad, (
        "README 里出现了含客户 ID 的真实文件名（应只写「客户实例 A/B/C」）：%s" % bad)
    assert not re.search(r"(?:datamigration|znxmglpt|xiangmuguanli)\d{6,}", text), (
        "README 正文出现了客户应用 ID")


def test_two_layer_structure_documented():
    """udc 的两层结构是本目录最易误用处，判据必须还在。"""
    text = _readme()
    assert "udc-biz-domain.md" in text and "udc-biz-appservice.md" in text, (
        "README 没同时提到 udc 的门面层与业务层")
    assert "只扫 `*Impl`" in text or "*Impl 会整个漏掉业务层" in text, (
        "README 没写「只扫 *Impl 会漏掉业务层」这条判据")
    # 两份都在盘
    for n in ("udc-biz-domain.md", "udc-biz-appservice.md"):
        assert (D / n).is_file(), "%s 不见了" % n


def test_no_sources_and_no_live_limits_documented():
    """「反编译 class 不是读源码」「纯静态无 LIVE」是本目录的能力边界，必须写明。"""
    text = _readme()
    assert "-sources.jar" in text, "README 没说明仓库无 sources.jar（这是反编译产物）"
    assert "LIVE" in text, "README 没说明这是纯静态反编译、无 LIVE 调用"
    assert "emit_service_flow.py" in text, "README 没给出生成器路径（防止有人手改）"
