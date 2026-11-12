"""docs/operation-contracts/udc/runtime/ 的域入口必须与磁盘和 registry.py 一致。

runtime 是 14 个子域里**唯一一个 13 条建议全部未落库**的目录，
同时是**证据最完整、方法论最可复用**的一个。三件事必须守住：

① "13 条全部 0 命中"这个结论**会漂移**（文档自己写了"落库前必须重新实测"）。
   闸门直接实测，不用文档里的旧数字。

② B 组 4 条是"同族内补齐"，不是新概念：
   registry 里 app-log/search/microflow 三条已落库，app-log/search/dataflow 四条没有。
   同一控制器、同一 URL 族、只差一个分母词。判"要不要落库"必须看兄弟端点。

③ registry.py 里有 udc-runtime/data//query（双斜杠），与 udc-runtime/data/query 是同一端点的两个身份。
   **按 path 查重前必须归一化**，否则这种缺陷永远查不出来。
   不属文档整理范围 —— 闸门只锁"已记录"，不许有人顺手去改 registry.py。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "operation-contracts" / "udc" / "runtime"
REG = ROOT / "components" / "platform_operations" / "registry.py"
ART = ROOT / "docs" / "audit" / "artifacts" / "udc-runtime-5.3.517"

ROW = re.compile(r"^\|\s*`([\w.-]+)`\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|", re.M)
# registry-entries.md 里的构造行：id, method, path
ENTRY = re.compile(
    r'contracts\["([a-z0-9_.]+)"\]\s*=\s*UdcOperationContract\('
    r'"[a-z0-9_.]+",\s*"(GET|POST)",\s*"([^"]+)"')


def _readme():
    p = D / "README.md"
    assert p.is_file(), "缺 docs/operation-contracts/udc/runtime/README.md（域入口）"
    return p.read_text(encoding="utf-8")


def _entries():
    return ENTRY.findall((D / "registry-entries.md").read_text(encoding="utf-8", errors="replace"))


def _norm(path):
    """归一化 path：折叠重复斜杠。查重前必须做，否则 data//query 这类缺陷查不出来。"""
    return re.sub(r"/{2,}", "/", path)


def test_table_matches_disk():
    """表里的字节/行数必须与磁盘一致，且 3 份一份不漏。"""
    rows = ROW.findall(_readme())
    assert len(rows) == 3, "规模表解析出 %d 行（应有 3 份契约，不含本 README）" % len(rows)
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


def test_thirteen_still_zero_hit():
    """13 条建议仍全部 0 命中——这是本域最反直觉的事实（唯一整域 pending）。

    文档自己写了「0 命中会漂移，落库前必须重新实测」。所以这里直接实测，
    一旦有人把它们落了库，这条会红，提示同步改入口。
    """
    entries = _entries()
    assert len(entries) == 13, "registry-entries.md 解析出 %d 条（应为 13）" % len(entries)

    reg = REG.read_text(encoding="utf-8", errors="replace")
    reg_norm = _norm(reg)
    hit_ids, hit_paths = [], []
    for oid, _method, path in entries:
        if '"%s"' % oid in reg:
            hit_ids.append(oid)
        if _norm(path) in reg_norm:
            hit_paths.append(path)
    assert not hit_ids, (
        "这些 op_id 已落库：%s——入口 §一 的「13 条全部未落库」已过期，必须同步改" % hit_ids)
    assert not hit_paths, (
        "这些建议 path 已出现在 registry：%s——入口 §一 已过期" % hit_paths)

    text = _readme()
    for token in ("全部未落库", "唯一一个", "13 条", "盘面漂移警示", "重新实测"):
        assert token in text, "入口 §一 缺「%s」" % token


def test_sibling_coverage_gap_recorded():
    """B 组 4 条是同族补齐：microflow 三条已落库，dataflow/deduction 四条没有。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    for landed in ("udc-runtime/app-log/search/microflow",
                   "udc-runtime/app-log/search-details/microflow",
                   "udc-runtime/app-log/search-details/microflow/flowLog"):
        assert '"%s"' % landed in reg, (
            "%s 不在 registry 里——入口 §二 的「microflow 三条已落库」已过期" % landed)
    for missing in ("udc-runtime/app-log/search/dataflow",
                    "udc-runtime/app-log/search-details/dataflow",
                    "udc-runtime/app-log/search/deduction",
                    "udc-runtime/app-log/search-details/deduction"):
        assert '"%s"' % missing not in reg, (
            "%s 已落库——入口 §二 的「dataflow/deduction 四条没有」已过期" % missing)

    # serial / jar 同族的已落库条目
    for landed in ("udc-runtime/serial-config/select-entity-list",
                   "udc-runtime/dynamic/jar/download"):
        assert '"%s"' % landed in reg, "%s 不在 registry 里，入口 §二 的兄弟端点论据失效" % landed

    text = _readme()
    for token in ("同族内补齐", "兄弟端点", "只差一个分母词"):
        assert token in text, "入口 §二 缺「%s」" % token


def test_effective_gate_counts():
    """5 条 .effective=True / 8 条 POST 只读 .effective=False。"""
    entries = _entries()
    get_n = sum(1 for _o, m, _p in entries if m == "GET")
    post_n = sum(1 for _o, m, _p in entries if m == "POST")
    assert (get_n, post_n) == (5, 8), (
        "13 条里 GET=%d / POST=%d（入口写 5 / 8）——门控表已过期" % (get_n, post_n))

    entries_doc = (D / "registry-entries.md").read_text(encoding="utf-8", errors="replace")
    assert "A1–A4、B6" in entries_doc or "A1-A4、B6" in entries_doc, (
        "registry-entries.md 的门控提示段被改了")
    text = _readme()
    assert "8 条会被 `.effective` 判成 False" in text, (
        "入口 §四 没写「13 条里 8 条会被判 False」这个后果")


def test_double_slash_defect_recorded():
    """registry 里有 udc-runtime/data//query（双斜杠），同端点两个身份。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    assert '"udc-runtime/data//query"' in reg, (
        "registry.py 里的 data//query 双斜杠已消失（可能被修了）——入口 §六 需同步")
    assert '"udc-runtime/data/query"' in reg, (
        "registry.py 里没有 udc-runtime/data/query——入口 §六 的对照失效")
    # 归一化后两者相同 —— 这正是按 path 查重会漏的原因
    assert _norm("udc-runtime/data//query") == _norm("udc-runtime/data/query")

    text = _readme()
    for token in ("双斜杠", "归一化", "不属文档整理范围"):
        assert token in text, "入口 §六 缺「%s」" % token


def test_three_layer_scan_methodology_recorded():
    """三层扫描 + 差分的实测计数必须与入口一致。"""
    text = _readme()
    for token in ("346", "307", "27", "131", "133", "38,646", "47", "106"):
        assert token in text, "入口 §三 缺差分实测计数：%s" % token
    # Layer C 反证 B 层的 3 条字面量
    for token in ("/package.json", "/proxy/", "/app/lock/.lock"):
        assert token in text, "入口 §三 缺「%s」——那是「B 层已经够了」的证明" % token
    assert "用独立口径互证" in text, "入口没写负证据的正确形状（独立口径互证，不是重复同一口径）"
    assert "按映射注解描述符" in text, (
        "入口没写「筛类必须按映射注解描述符」——按 @RestController 筛会漏 8 个类")


def test_evidence_dir_intact():
    """证据目录必须还在，且脚本可复跑。"""
    assert ART.is_dir(), "证据目录 docs/audit/artifacts/udc-runtime-5.3.517/ 不见了"
    for script in ("r2_diff.py", "r2_scan_runtime.py", "r2_layerAC.py"):
        assert (ART / script).is_file(), "缺可复跑脚本 %s" % script
    for out in ("r2_registry_key_check.txt", "r2_summary.json"):
        assert (ART / out).is_file(), "缺结论文件 %s" % out


def test_no_customer_identifiers():
    text = _readme()
    bad = [w for w in ("xiangmuguanli", "znxmglpt", "datamigration") if w in text]
    assert not bad, "域入口 README 出现客户标识词根：%s" % bad
