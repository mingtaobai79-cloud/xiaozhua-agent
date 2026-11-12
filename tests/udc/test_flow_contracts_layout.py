"""docs/operation-contracts/udc/flow/ 的域入口必须与磁盘和 registry.py 一致。

这个域是本仓库**唯一一处「发现同路径重复、并且真的去重了」**的记录，
也是**唯一一处给了 `.effective` 门控表**的域。两件事都必须被守住：

① `udc.flow.function_node_tree` 被 MERGE 按「去重归一（删一留一）」处理成
   `udc.microflow.function_node_tree`。若有人照 flow 的建议条目去补
   `udc.flow.function_node_tree`，就**违背了本域自己写下的裁定**，
   并在全库造出第 7 条重复注册。

② `.effective` 门控表：6 条 POST 读型条目 `.effective=False`。
   谁按 method 或按 `.effective` 筛只读能力，会漏掉这 6 条，
   然后以为"流程域只有 3 条只读"。入口必须把这张表抄对。

③ 3 条写侧的 `verification_rules` 写「write=true 策略门控未放开」，
   而 registry.py 里已有 25 条 write=True —— 门控早已放开。
   措辞过期，但不许有人"顺手补上"（属策略决定）。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "operation-contracts" / "udc" / "flow"
REG = ROOT / "components" / "platform_operations" / "registry.py"

ROW = re.compile(r"^\|\s*`([\w.-]+)`\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|", re.M)
CONTRACT = re.compile(
    r'contracts\["([a-z0-9_.]+)"\]\s*=\s*UdcOperationContract\(\s*'
    r'"[a-z0-9_.]+",\s*"(GET|POST|PUT|DELETE)",\s*"([^"]+)",\s*"[^"]*",\s*"[^"]*",\s*'
    r'OperationStatus\.(\w+),\s*(True|False)')


def _readme():
    p = D / "README.md"
    assert p.is_file(), "缺 docs/operation-contracts/udc/flow/README.md（域入口）"
    return p.read_text(encoding="utf-8")


def _contracts():
    return sorted(f for f in D.glob("*.md") if f.name != "README.md")


def _reg_contracts():
    return CONTRACT.findall(REG.read_text(encoding="utf-8", errors="replace"))


def test_table_matches_disk():
    """表里的字节/行数必须与磁盘一致，且 4 份一份不漏。"""
    rows = ROW.findall(_readme())
    assert len(rows) == 4, "规模表解析出 %d 行（应有 4 份契约，不含本 README）" % len(rows)
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


def test_function_node_tree_dedupe_respected():
    """去重归一被 MERGE 执行了——不许有人照建议条目把它补回来。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    assert '"udc.flow.function_node_tree"' not in reg, (
        "registry.py 里出现了 udc.flow.function_node_tree！"
        "本域 registry-entries.md 明写「跨域重叠 → MERGE 去重归一（删一留一），勿新增重复 operation_id」，"
        "补回它就是第 7 条重复注册。")
    assert '"udc.microflow.function_node_tree"' in reg, (
        "udc.microflow.function_node_tree 不在 registry.py 里——去重留的是谁？")

    entries = (D / "registry-entries.md").read_text(encoding="utf-8", errors="replace")
    assert "去重归一" in entries and "删一留一" in entries, (
        "registry-entries.md 的「去重归一（删一留一）」裁定被删了——那是本域最值钱的记录")

    text = _readme()
    for token in ("去重归一", "删一留一", "唯一一处", "遗漏，不是设计"):
        assert token in text, "入口 §一 缺「%s」" % token


def test_effective_gate_table_correct():
    """`.effective` 门控表：3 GET=True / 6 POST 读型=False / 3 写型=False。

    谁按 method 或按 .effective 筛只读，都会漏掉那 6 条。这是本域最实用的表。
    """
    entries = (D / "registry-entries.md").read_text(encoding="utf-8", errors="replace")
    assert "GET 只读 → **True**（3 条）" in entries, "registry-entries.md 的门控表 True 段被改了"
    assert "POST 读型（write=False）→ **False**（6 条）" in entries, (
        "registry-entries.md 的门控表 POST 读型段被改了")

    text = _readme()
    # 6 条 POST 读型必须一个不漏地列在入口的表里
    post_read = ["bpm_node_info_search", "form_data_query", "data_flow_map_search",
                 "data_flow_mapping_search_original", "data_flow_mapping_init_data",
                 "data_flow_mapping_detail"]
    missing = [n for n in post_read if n not in text]
    assert not missing, "入口 §三 的 POST 读型清单漏了：%s" % missing
    assert "会漏掉这 6 条" in text, "入口没写「按 .effective 筛会漏掉这 6 条」这个后果"


def test_write_side_three_not_landed_and_gate_claim_is_stale():
    """3 条写侧未落库；而「策略门控未放开」在 registry.py 里已不成立（25 条 write=True）。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    for oid in ("udc.flow.bpm_fill_error_data", "udc.flow.data_flow_mapping_update",
                "udc.flow.data_flow_mapping_update_state"):
        assert '"%s"' % oid not in reg, (
            "%s 已被落库——入口 §二 的「写侧未落库」已过期，同步改入口" % oid)

    writes = [c for c in _reg_contracts() if c[4] == "True"]
    assert len(writes) == 25, (
        "registry.py 的 write=True 条目现在是 %d 条（入口写 25 条）" % len(writes))

    text = _readme()
    assert "在消费方不成立" in text, (
        "入口没指出「write=true 策略门控未放开」这句在 registry.py 里已不成立")
    assert "待裁决" in text and "别急着补" in text, (
        "入口没写「补进去属策略决定、已记待裁决」——后人会顺手补 3 条写契约")


def test_negative_evidence_40_controllers_intact():
    """40 controller 穷尽枚举是本域负证据的底座。"""
    neg = (D / "flow-domain-boundary-negative-evidence.md").read_text(encoding="utf-8", errors="replace")
    for token in ("40", "udc-starter-runtime", "OBSERVATION", "非推测"):
        assert token in neg, "负证据文件缺「%s」" % token
    text = _readme()
    for token in ("40", "34 个 non-flow", "OBSERVATION", "0 遗漏"):
        assert token in text, "入口 §四 缺负证据要素：%s" % token
    assert "未深挖" in text, "入口没写「未深挖任何 non-flow 方法体」——那是证据等级的边界"


def test_proxy_ruling_preserved():
    """R7/R8 裁定：proxy 层不算流程域。删了就会有人去补，然后与微流程域撞车。"""
    entries = (D / "registry-entries.md").read_text(encoding="utf-8", errors="replace")
    assert "UdcBaseGeneralController" in entries, "R7/R8 裁定的 proxy controller 记录被删了"
    text = _readme()
    for token in ("UdcBaseGeneralController", "不扩流程域边界", "撞车"):
        assert token in text, "入口 §五 缺「%s」" % token


def test_construct_check_14_vs_12_explained():
    """14 处提到 vs 12 条可构造，差额必须当场解释掉。"""
    entries = (D / "registry-entries.md").read_text(encoding="utf-8", errors="replace")
    assert "12/12" in entries and "14" in entries, "R5 可构造性核验的记录被删了"
    text = _readme()
    assert "12/12" in text and "别看到" in text, (
        "入口 §七 没解释「14 处 vs 12 条」的差额——后人会以为多写了 2 条")


def test_no_customer_identifiers():
    text = _readme()
    bad = [w for w in ("xiangmuguanli", "znxmglpt", "datamigration") if w in text]
    assert not bad, "域入口 README 出现客户标识词根：%s" % bad
