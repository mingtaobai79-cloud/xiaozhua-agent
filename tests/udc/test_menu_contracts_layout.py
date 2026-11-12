"""docs/operation-contracts/udc/menu/ 的域入口必须与磁盘和 registry.py 一致。

这个域有三件必须被守住的事：

① 菜单域**没有自己的类**（6 件 UDC jar × 5 个关键词 = 0 命中），5 条契约全是借来的。
   入口第一屏就要写清，否则后人会在 UDC 里搜 "menu"，搜不到就判"这域是空的"。

② registry-entries.md 只列 3 条，但 5 条都落库了（P2 换了名字）。
   把 registry-entries.md 当全集会得出"缺 2 条"的错误结论。

③ P5 头部写「HYPOTHESIS，不入 registry」，而它**已经进去了**（带 UNVERIFIED 挂载）。
   别照「不入 registry」去删它或当未完成项。

另：本域 2 条路径是**重复注册**（全库 6 条 / 12 条契约，两套命名风格）。
不属文档整理范围 —— 闸门只锁"已记录"，不许有人顺手去改 registry.py。
"""
import collections
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "operation-contracts" / "udc" / "menu"
REG = ROOT / "components" / "platform_operations" / "registry.py"

ROW = re.compile(r"^\|\s*`([\w.-]+)`\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|", re.M)
CONTRACT = re.compile(
    r'contracts\["([a-z0-9_.]+)"\]\s*=\s*UdcOperationContract\(\s*'
    r'"[a-z0-9_.]+",\s*"(GET|POST|PUT|DELETE)",\s*"([^"]+)"')


def _readme():
    p = D / "README.md"
    assert p.is_file(), "缺 docs/operation-contracts/udc/menu/README.md（域入口）"
    return p.read_text(encoding="utf-8")


def _registry_contracts():
    return CONTRACT.findall(REG.read_text(encoding="utf-8", errors="replace"))


def _contracts():
    return sorted(f for f in D.glob("*.md") if f.name != "README.md")


def test_table_matches_disk():
    """表里的字节/行数必须与磁盘一致，且 7 份一份不漏。"""
    rows = ROW.findall(_readme())
    assert len(rows) == 7, "规模表解析出 %d 行（应有 7 份契约，不含本 README）" % len(rows)
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


def test_no_menu_class_negative_evidence_intact():
    """负证据（6 jar × 5 关键词 = 0）是本域立域的理由，不许被删。"""
    scan = (D / "SCAN.md").read_text(encoding="utf-8", errors="replace")
    assert "menutree" in scan and "0 命中" in scan, "SCAN.md 的 menu 负证据被删了"
    text = _readme()
    for token in ("没有\"菜单\"这个类", "0 命中", "借来的"):
        assert token in text, "入口 §一 缺「%s」——后人会搜 menu 搜不到就判这域是空的" % token


def test_scan_exclusion_list_preserved():
    """排除清单（GET 其实是写）比候选清单更值钱，必须留在入口里。"""
    text = _readme()
    for token in ("delete-all", "clear-runtime-data-source-cache", "enable-log/{enable}",
                  "cache-evict/{appName}", "GET 就是只读"):
        assert token in text, "入口 §七 缺排除项「%s」" % token
    # 跨域边界那句话
    assert "selectFunctionNodeTreeMetaData" in text and "微流程" in text, (
        "入口丢了「C1 已被微流程域占用」这条唯一的跨域边界记录")


def test_all_five_landed_despite_entries_listing_three():
    """5 条全落库，而 registry-entries.md 只列 3 条 —— 两个数都要锁住。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    entries = (D / "registry-entries.md").read_text(encoding="utf-8", errors="replace")
    listed = sorted(set(re.findall(r'contracts\["([a-z0-9_.]+)"\]', entries)))
    assert len(listed) == 3, "registry-entries.md 列了 %d 条（应为 3：P1/P3/P4）" % len(listed)

    # P2 换名字：文档叫 datalog_get_by_id，registry 叫 select_by_id
    assert '"udc.applog.datalog_get_by_id"' not in reg, (
        "registry.py 里出现了 udc.applog.datalog_get_by_id —— 入口 §三 的「换了名字」说明已过期")
    assert '"udc.applog.select_by_id"' in reg, "registry.py 里没有 udc.applog.select_by_id"

    for pfile, oid in [
        ("P1-udc-role-has-system-admin.md", "udc.role.has_system_admin"),
        ("P3-udc-applog-datalog-list-by-data-id.md", "udc.applog.datalog_list_by_data_id"),
        ("P4-udc-serial-config-entity-list.md", "udc.serial_config.entity_list"),
    ]:
        assert (D / pfile).is_file(), "缺 %s" % pfile
        assert '"%s"' % oid in reg, "%s 的 op_id %s 不在 registry.py 里" % (pfile, oid)

    text = _readme()
    for token in ("只 3 条", "udc.applog.select_by_id", "不是本域的完整清单"):
        assert token in text, "入口 §三 缺「%s」" % token


def test_p5_hypothesis_already_landed_with_unverified():
    """P5 头部写「不入 registry」，而它已入库且挂着 UNVERIFIED —— 双向锁。"""
    p5 = (D / "P5-udc-database-query-data.md").read_text(encoding="utf-8", errors="replace")
    assert "不入 registry" in p5, "P5 头部那句「不入 registry」被改了——它是历史记录，不该动"

    reg = REG.read_text(encoding="utf-8", errors="replace")
    assert '"udc.database.query_data"' in reg, (
        "udc.database.query_data 不在 registry.py 里了——入口 §四 写的「已经进去了」已过期")
    i = reg.find('contracts["udc.database.query_data"]')
    seg = reg[i:i + 900]
    assert "VERIFIED_STATIC_BYTECODE" in seg, "P5 入库时没标 VERIFIED_STATIC_BYTECODE"
    assert "LIVE 复核" in seg, "P5 入库时丢了「GET 带请求体语义需 LIVE 复核」这句 UNVERIFIED 挂载"

    text = _readme()
    assert "已经进去了" in text and "过去时" in text, (
        "入口 §四 没写「P5 已入库、标题已过期」——后人会照「不入 registry」把它删掉")


def test_duplicate_registrations_recorded_not_fixed():
    """全库重复注册的实测数必须与入口一致，且不许有人顺手把它"修好"。"""
    by_path = collections.defaultdict(list)
    for oid, method, path in _registry_contracts():
        by_path[path].append((oid, method))
    dup = {p: v for p, v in by_path.items() if len(v) > 1}

    total = len(_registry_contracts())
    assert len(by_path) == 111, (
        "registry.py 现在有 %d 条不同路径（入口写 111 条——若已去重，需同步改入口）" % len(by_path))
    assert total == 117, "registry.py 现在有 %d 条契约（入口写 117 条）" % total
    assert len(dup) == 6, "重复注册的路径现在是 %d 条（入口写 6 条）" % len(dup)

    # 本域这两条必须在重复集里
    for path in ("udc-runtime/app-log/datalog/list-by-dataid/{dataId}",
                 "udc-runtime/serial-config/select-entity-list"):
        assert path in dup, "%s 不再重复注册——入口 §五 已过期" % path

    text = _readme()
    for token in ("重复注册", "117", "111", "6 条", "待裁决"):
        assert token in text, "入口 §五 缺「%s」" % token
    assert "不属文档整理范围" in text, (
        "入口没写「不属文档整理范围」——后人会顺手改 registry.py 去重，那会动到其他会话的契约")


def test_no_customer_identifiers():
    text = _readme()
    bad = [w for w in ("xiangmuguanli", "znxmglpt", "datamigration") if w in text]
    assert not bad, "域入口 README 出现客户标识词根：%s" % bad
