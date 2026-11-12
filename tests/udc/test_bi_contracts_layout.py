"""docs/operation-contracts/udc/bi/ 的域入口必须与磁盘和 registry.py 一致。

这个域最容易误判的地方是「0 条 + 5 条同时成立」：
  · bi-vacuum-contract.md / bi-boundary-conclusion.md 说 5.3.517 单元真 BI = 0 条
  · registry.py 里 udc.bi.* 有 5 条（来自 5.3.260 的 Gantt 单元）
两者都对，因为**两个版本单元禁混写、禁互推**。入口若不把这件事写在第一屏，
后人一定会把「本域 0 条」判成过期文档，或者反过来把 5 条当「真空被打破」去删正文。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "operation-contracts" / "udc" / "bi"
REG = ROOT / "components" / "platform_operations" / "registry.py"

ROW = re.compile(r"^\|\s*`([\w.-]+)`\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|", re.M)


def _readme():
    p = D / "README.md"
    assert p.is_file(), "缺 docs/operation-contracts/udc/bi/README.md（域入口）"
    return p.read_text(encoding="utf-8")


def _contracts():
    return sorted(f for f in D.glob("*.md") if f.name != "README.md")


def test_table_matches_disk():
    """表里的字节/行数必须与磁盘一致，且 5 份一份不漏。"""
    rows = ROW.findall(_readme())
    assert len(rows) == 5, "规模表解析出 %d 行（应有 5 份契约，不含本 README）" % len(rows)
    bad = []
    for name, size_s, lines_s in rows:
        f = D / name
        if not f.is_file():
            bad.append("%s: 表里登记了但文件不存在" % name)
            continue
        raw = f.read_bytes()
        size, lines = len(raw), len(raw.decode("utf-8").splitlines())
        if size != int(size_s.replace(",", "")):
            bad.append("%s: 表写 %s B 磁盘 %d B" % (name, size_s, size))
        if lines != int(lines_s):
            bad.append("%s: 表写 %s 行 磁盘 %d 行" % (name, lines_s, lines))
    assert not bad, "契约规模表已腐坏：\n  " + "\n  ".join(bad)


def test_every_contract_is_listed():
    text = _readme()
    missing = [f.name for f in _contracts() if f.name not in text]
    assert not missing, "这些契约没在域入口 README 里出现：%s" % missing


def test_zero_and_five_both_true_and_explained():
    """「0 条」与「registry 有 5 条」必须同时为真，且入口必须解释它们是两个版本单元。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    landed = sorted(set(re.findall(r'"(udc\.bi\.[a-z0-9_.]+)"', reg)))

    # ① 磁盘事实：registry 里恰好 5 条 udc.bi.*
    assert len(landed) == 5, (
        "registry.py 里 udc.bi.* 是 %d 条（README 写 5 条，来自 5.3.260 单元）" % len(landed))

    # ② 5 条全部来自 registry-entries.md 末尾追加的 5.3.260 节
    entries = (D / "registry-entries.md").read_text(encoding="utf-8", errors="replace")
    doc_ids = sorted(set(re.findall(r'contracts\["(udc\.bi\.[a-z0-9_.]+)"\]', entries)))
    assert doc_ids == landed, (
        "registry-entries.md 列的 %s 与 registry.py 的 %s 不一致" % (doc_ids, landed))

    # ③ method / path 逐条一致（照抄时最容易一律写 POST）
    for oid in landed:
        i = reg.find('"%s"' % oid)
        seg = reg[i:i + 400]
        m_reg = re.search(r'"(GET|POST)",\s*"([^"]+)"', seg)
        j = entries.find('contracts["%s"]' % oid)
        seg2 = entries[j:j + 400]
        m_doc = re.search(r'"%s",\s*"(GET|POST)",\s*"([^"]+)"' % re.escape(oid), seg2)
        assert m_reg and m_doc, "解析不出 %s 的 method/path" % oid
        assert m_reg.group(1, 2) == m_doc.group(1, 2), (
            "%s: registry 是 %s %s，文档是 %s %s" % (
                oid, m_reg.group(1), m_reg.group(2), m_doc.group(1), m_doc.group(2)))

    # ④ 入口必须把「不矛盾」写在显眼处
    text = _readme()
    for token in ("不是矛盾", "5.3.517", "5.3.260", "禁混写"):
        assert token in text, "入口 §一 缺「%s」——后人会把 0 条判成过期，或把 5 条当真空被打破" % token


def test_vacuum_conclusion_not_deleted():
    """正文那两条「0 条」结论不许被删——它们是 5.3.517 单元的完备负证据。"""
    vac = (D / "bi-vacuum-contract.md").read_text(encoding="utf-8", errors="replace")
    assert "VACUUM" in vac and "0 条" in vac, "bi-vacuum-contract.md 的 VACUUM / 0 条结论被改掉了"
    bound = (D / "bi-boundary-conclusion.md").read_text(encoding="utf-8", errors="replace")
    assert "UDC 域内没有 BI" in bound, "bi-boundary-conclusion.md 的核心结论句被改掉了"
    # 入口自己也必须保留这条，而不是只写「registry 有 5 条」
    assert "VACUUM" in _readme(), "入口没保留 VACUUM 这条完备负证据"


def test_three_way_separation_intact():
    """三方分离地图是本目录唯一业务产出，入口必须转述它且禁止跨列合并。"""
    text = _readme()
    for token in ("cdp-bi", "gantt_chart_schema", "错误建模", "数据层引用"):
        assert token in text, "入口缺三方分离地图的关键判据：%s" % token
    bound = (D / "bi-boundary-conclusion.md").read_text(encoding="utf-8", errors="replace")
    assert "错误建模" in bound, "bi-boundary-conclusion.md 的「错误建模」警告被删了"


def test_negative_evidence_completeness_recorded():
    """负证据的「怎么证明找全了」四条必须在入口里，否则 VACUUM 只是句口号。"""
    text = _readme()
    for token in ("1217", "219", "38", "mismatch = 0", "@interface"):
        assert token in text, "入口 §五 缺完备性论据：%s" % token
    assert "映射注解描述符" in text, (
        "入口没写「筛类必须按映射注解描述符」——按 @RestController 筛会漏 53 行端点")


def test_no_customer_identifiers():
    text = _readme()
    bad = [w for w in ("xiangmuguanli", "znxmglpt", "datamigration") if w in text]
    assert not bad, "域入口 README 出现客户标识词根：%s" % bad
