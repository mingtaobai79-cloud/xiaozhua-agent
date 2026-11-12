"""docs/operation-contracts/udc/page/ 的域入口必须与磁盘和 registry.py 一致。

这个域最重要的一件事，是 registry.py 里**有一条 path 是占位符**：
    <BASE-UNRESOLVED-in-5.3.517>/{entityAppName}/{entityName}/{referGuid}/{objectId}

这是全库 117 条契约里唯一一条 path 不是可调地址的。文档的原话是
「base 段逐字保留，**未臆造任何前缀**」—— 这是**正确的拒绝**：
宁可把不确定性原样留在契约里，也不猜一个前缀。

但后果必须写清楚：**「在 registry 里」不等于「可调用」**。
查可用端点时要过滤掉含 `<` 的 path，否则会拿一条调不通的地址去发请求。

另外本域占全库 6 条重复注册中的 2 条（page_info.* 与 metadata.* 别名），
其中 udc.metadata.page_tree 的名字与路径语义还对不上、并且来路不明。
不属文档整理范围 —— 闸门只锁"已记录"，不许有人顺手改 registry.py。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "operation-contracts" / "udc" / "page"
REG = ROOT / "components" / "platform_operations" / "registry.py"

ROW = re.compile(r"^\|\s*`([\w.-]+)`\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|", re.M)
ENTRY = re.compile(
    r'contracts\["([a-z0-9_.]+)"\]\s*=\s*UdcOperationContract\('
    r'"[a-z0-9_.]+",\s*"(GET|POST)",\s*"([^"]+)"')
CONTRACT = re.compile(
    r'contracts\["([a-z0-9_.]+)"\]\s*=\s*UdcOperationContract\(\s*'
    r'"[a-z0-9_.]+",\s*"(GET|POST|PUT|DELETE)",\s*"([^"]+)"')


def _readme():
    p = D / "README.md"
    assert p.is_file(), "缺 docs/operation-contracts/udc/page/README.md（域入口）"
    return p.read_text(encoding="utf-8")


def _entries():
    return ENTRY.findall((D / "registry-entries.md").read_text(encoding="utf-8", errors="replace"))


def test_table_matches_disk():
    """表里的字节/行数必须与磁盘一致，且 2 份一份不漏。"""
    rows = ROW.findall(_readme())
    assert len(rows) == 2, "规模表解析出 %d 行（应有 2 份契约，不含本 README）" % len(rows)
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
    missing = [f.name for f in sorted(D.glob("*.md")) if f.name != "README.md" and f.name not in text]
    assert not missing, "这些契约没在域入口 README 里出现：%s" % missing


def test_placeholder_path_in_registry_is_the_real_fact():
    """registry.py 里确实有一条占位符 path —— 这是"在 registry 里 ≠ 可调用"的唯一实证。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    assert '"<BASE-UNRESOLVED-in-5.3.517>' in reg, (
        "registry.py 里已没有 <BASE-UNRESOLVED-in-5.3.517> 占位符 path。"
        "若那是被修好了，入口 §二 必须同步改（改成真实的 base 段）。")

    # 含占位符的契约恰好一条
    with_ph = [c for c in CONTRACT.findall(reg) if "<" in c[2]]
    assert len(with_ph) == 1, (
        "含占位符的契约现在是 %d 条（入口 §二 写「全库唯一一条」）：%s"
        % (len(with_ph), [(c[0], c[2]) for c in with_ph]))
    assert with_ph[0][0] == "udc.page_refer.select_by_id", (
        "带占位符的契约不是 udc.page_refer.select_by_id 了：%s" % with_ph[0][0])

    text = _readme()
    for token in ("未臆造任何前缀", "正确的拒绝", "不等于", "含 `<` 的 path"):
        assert token in text, "入口 §二 缺「%s」" % token


def test_five_landed_two_deliberately_not():
    """8 条建议：5 条同名落库、2 条故意不落（base 未解析）、1 条待定。"""
    entries = _entries()
    assert len(entries) == 8, "registry-entries.md 解析出 %d 条（应为 8）" % len(entries)
    reg = REG.read_text(encoding="utf-8", errors="replace")

    landed = [o for o, _m, _p in entries if '"%s"' % o in reg]
    not_landed = [o for o, _m, _p in entries if '"%s"' % o not in reg]
    assert len(landed) == 5, (
        "同名落库 %d 条（入口写 5）：%s" % (len(landed), landed))
    assert sorted(not_landed) == sorted([
        "udc.page_general.get_cascade_default_value",
        "udc.page_refer.select_tree",
        "udc.page_refer.search_list_by_conditions",
    ]), "未落库的条目变了：%s——入口 §一 需同步" % sorted(not_landed)

    # 未落库的三条全都带占位符 base
    ph = [p for o, _m, p in entries if o in not_landed]
    assert all("<BASE-UNRESOLVED-in-5.3.517>" in p for p in ph), (
        "未落库的条目里有 base 已解析的 —— 那就不是「故意不落」而是遗漏：%s" % ph)

    text = _readme()
    assert "故意不落" in text and "base 来自 `BaseComponentController`" in text, (
        "入口没写清「5 条不是 8 条」的原因是 base 段能否解析")


def test_duplicate_registration_this_domain_two():
    """本域占全库 6 条重复注册中的 2 条，且 metadata.page_tree 名字与路径对不上。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    for path, names in [
        ("udc-runtime/meta-data/check-page-exists",
         ("udc.page_info.check_exists", "udc.metadata.page_exists_check")),
        ("udc-runtime/meta-data/select-host-and-only-page-pages",
         ("udc.page_info.select_host_and_only_page", "udc.metadata.page_tree")),
    ]:
        assert reg.count('"%s"' % path) >= 2, "%s 不再重复注册，入口 §四 已过期" % path
        for n in names:
            assert '"%s"' % n in reg, "%s 不在 registry.py 里" % n

    text = _readme()
    for token in ("udc.metadata.page_tree", "名字与路径语义对不上", "来路不明", "不属文档整理范围"):
        assert token in text, "入口 §四 缺「%s」" % token


def test_no_customer_identifiers():
    text = _readme()
    bad = [w for w in ("xiangmuguanli", "znxmglpt", "datamigration") if w in text]
    assert not bad, "域入口 README 出现客户标识词根：%s" % bad
