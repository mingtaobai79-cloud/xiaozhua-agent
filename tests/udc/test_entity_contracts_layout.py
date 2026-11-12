"""docs/operation-contracts/udc/entity/ 的域入口必须与磁盘和 registry.py 一致。

这个域有两件必须被守住的事：

① 16 条只读契约**全部落库**，但 3 条换了名字。
   按 op_id 字面量 grep registry.py 只命中 13/16 —— 看上去"缺 3 条"。
   按 path 再查一遍，16/16 全在。**按 key 字符串判"落没落库"会误判**。
   若后人照"缺 3 条"去补条目，会在 registry 里造出重复注册。

② 本目录是 P3「重复文档降级」在本仓库唯一走完三件事的完成样本：
   内容并入主文档 + 原文件加 superseded 指针 + 主文档补反向指针。
   registry-entries-code.md 是留痕，不是垃圾。删了它，registry.py 里那 16 条
   就只剩结论没有构造依据。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "operation-contracts" / "udc" / "entity"
REG = ROOT / "components" / "platform_operations" / "registry.py"

ROW = re.compile(r"^\|\s*(?:\u26a0\ufe0f\s*)?\*?\*?`([\w.-]+)`\*?\*?\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|", re.M)


def _readme():
    p = D / "README.md"
    assert p.is_file(), "缺 docs/operation-contracts/udc/entity/README.md（域入口）"
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


def test_all_16_landed_by_path_not_by_name():
    """16 条全部落库——按 path 核实，不是按 op_id 字面量。

    这是本目录最容易误判的地方：3 条换了名字，按 key grep 只得 13/16。
    """
    reg = REG.read_text(encoding="utf-8", errors="replace")
    code = (D / "registry-entries-code.md").read_text(encoding="utf-8", errors="replace")

    # 从文档里抽 (op_id, method, path)
    triples = re.findall(
        r'contracts\["([a-z0-9_.]+)"\] = UdcOperationContract\(\s*'
        r'"[^"]+",\s*"(GET|POST)",\s*"([^"]+)"',
        code)
    assert len(triples) == 16, "registry-entries-code.md 里解析出 %d 条（应为 16）" % len(triples)

    by_name, by_path = [], []
    for oid, method, path in triples:
        if '"%s"' % oid in reg:
            by_name.append(oid)
        else:
            # 路径必须能在 registry 里找到，且 method 一致
            found = False
            for m in re.finditer(re.escape(path), reg):
                seg = reg[max(0, m.start() - 400):m.start() + 200]
                if re.search(r'"%s"' % method, seg):
                    found = True
                    break
            if found:
                by_path.append(oid)
    assert len(by_name) == 13, (
        "按 op_id 字面量应命中 13 条（另 3 条换了名字），实测 %d：%s" %
        (len(by_name), sorted(by_name)))
    assert len(by_name) + len(by_path) == 16, (
        "16 条里有 %d 条两种方式都找不到（既无同名、path 也对不上）：%s" %
        (16 - len(by_name) - len(by_path),
         [o for o, _, _ in triples if o not in by_name and o not in by_path]))

    # 入口必须把"换名字"这件事写成表
    text = _readme()
    for token in ("udc.applog.select_by_id", "udc.page_info.check_exists",
                  "udc.page_info.select_host_and_only_page", "按路径再查一遍", "16/16"):
        assert token in text, "入口 §一 缺「%s」——后人会按 key grep 判定「缺 3 条」去补，造成重复注册" % token


def test_duplicate_registration_recorded_not_touched():
    """那两条路径在 registry 里各被注册了两次——入口必须点出来，但本目录不改它。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    for path, names in [
        ("udc-runtime/meta-data/check-page-exists",
         ("udc.page_info.check_exists", "udc.metadata.page_exists_check")),
        ("udc-runtime/meta-data/select-host-and-only-page-pages",
         ("udc.page_info.select_host_and_only_page", "udc.metadata.page_tree")),
    ]:
        assert reg.count('"%s"' % path) >= 2, (
            "%s 在 registry.py 里不再重复注册——入口 §一 的说明已过期" % path)
        for n in names:
            assert '"%s"' % n in reg, "%s 不在 registry.py 里，入口的别名表过期" % n
    text = _readme()
    assert "重复注册" in text and "待裁决" in text, (
        "入口没把「重复注册 + 不属文档整理范围 + 待裁决」写清——后人会以为该由文档轮次去修")


def test_p3_downgrade_sample_intact():
    """P3 降级三件事必须都还在：superseded 指针 + 主文档反向指针 + 不删。"""
    code = (D / "registry-entries-code.md").read_text(encoding="utf-8", errors="replace")
    assert "已并入" in code and "registry-entries.md" in code, (
        "registry-entries-code.md 头部丢了「已并入 registry-entries.md」指针")
    assert "保留作历史" in code, "丢了「保留作历史记录」声明"
    assert "不再作为入库依据" in code, "丢了「不再作为入库依据」声明"

    main = (D / "registry-entries.md").read_text(encoding="utf-8", errors="replace")
    assert "registry-entries-code.md" in main, (
        "主文档丢了指向 code 变体的反向指针——读者会看不出还有个变体")

    text = _readme()
    assert "完成样本" in text, "入口没把本目录标成 P3 降级的完成样本"
    assert "留痕" in text, "入口没写「code 文件是留痕、不要清理」"


def test_no_customer_identifiers():
    text = _readme()
    bad = [w for w in ("xiangmuguanli", "znxmglpt", "datamigration") if w in text]
    assert not bad, "域入口 README 出现客户标识词根：%s" % bad
