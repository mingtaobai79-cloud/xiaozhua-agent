"""docs/operation-contracts/udc/role/ 的域入口必须与磁盘和证据实况一致。

这个域是本仓库**唯一一份「声称能自验、而且真的能自验」的契约**：
它给了仓内一条命令复算「15 个端点」，产物已入仓，我实测跑过 —— 15/1/16 与文档完全一致。

闸门要做的是把这次复算**固化**：一旦 javap 被重新生成（比如用 JDK 8），
计数会变成 0，此时闸门必须红，而不是让后人得出「这份契约是编的」。
文档自己写了这个前置：JDK 8 的 javap 不展开注解类名，`annotation.(Post|Get)Mapping(` 会得 0。

另两件必须守住：
① 「覆盖式机制」是 LIVE，「47→1」是推算 —— 入口必须分栏，不许合并成一句。
② 已撤回的「409 条与 DB 互证」必须保持撤回状态，不许有人把它恢复成结论。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "docs" / "operation-contracts" / "udc" / "role"
ART = ROOT / "docs" / "audit" / "artifacts" / "udc-user-5.3.517-contracts"
CONTRACT = D / "write-chain.contract.md"

ROW = re.compile(r"^\|\s*`([\w.-]+)`\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|", re.M)


def _readme():
    p = D / "README.md"
    assert p.is_file(), "缺 docs/operation-contracts/udc/role/README.md（域入口）"
    return p.read_text(encoding="utf-8")


def test_table_matches_disk():
    """表里的字节/行数必须与磁盘一致，且 1 份不漏。"""
    rows = ROW.findall(_readme())
    assert len(rows) == 1, "规模表解析出 %d 行（本域只有 1 份契约，不含 README）" % len(rows)
    name, size_s, lines_s = rows[0]
    f = D / name
    assert f.is_file(), "表里登记的 %s 不存在" % name
    raw = f.read_bytes()
    assert len(raw) == int(size_s.replace(",", "")), (
        "%s: 表写 %s B 磁盘 %d B" % (name, size_s, len(raw)))
    assert len(raw.decode("utf-8").splitlines()) == int(lines_s), (
        "%s: 表写 %s 行 磁盘 %d 行" % (name, lines_s, len(raw.decode("utf-8").splitlines())))


def test_fifteen_endpoints_still_recomputable():
    """把「15 个端点可复算」这件事固化 —— 这是本域唯一的核心卖点。"""
    j = ART / "UdcRoleController.javap.txt"
    assert j.is_file(), "javap 产物不见了：%s（入口 §二 的复算说明失效）" % j
    t = j.read_text(encoding="utf-8", errors="replace")

    method_mappings = len(re.findall(r"annotation\.(?:Post|Get)Mapping\(", t))
    class_mappings = len(re.findall(r"annotation\.RequestMapping\(", t))
    value_literals = len(re.findall(r'value=\["[^"]*"\]', t))

    assert method_mappings == 15, (
        "方法级映射数变成 %d（应为 15）。"
        "若刚重新生成过 javap：**必须用 JDK 21**，JDK 8 不展开注解类名会得 0。" % method_mappings)
    assert class_mappings == 1, "类级 RequestMapping 变成 %d（应为 1，别混入方法级）" % class_mappings
    assert value_literals == 16, (
        "value=[\"...\"] 总数变成 %d（应为 16 = 1 类级基路径 + 15 方法级）" % value_literals)

    # 双向完备性：15 个方法路径各出现 1 次
    paths = re.findall(r'value=\["([^"]*)"\]', t)
    from collections import Counter
    c = Counter(paths)
    base = "udc/ctp-user/role"
    assert c[base] == 1, "类级基路径 %s 出现 %d 次（应为 1）" % (base, c[base])
    dup = {p: n for p, n in c.items() if p != base and n != 1}
    assert not dup, "这些方法路径出现了不止一次（不再无重复）：%s" % dup
    assert len([p for p in c if p != base]) == 15, (
        "方法级路径种类数不是 15：%d" % len([p for p in c if p != base]))

    text = _readme()
    for token in ("可复算", "15 / 1 / 16", "JDK 21", "无重复、无遗漏", "双向完备性"):
        assert token in text, "入口 §二 缺「%s」" % token


def test_mechanism_vs_arithmetic_separated():
    """「覆盖式机制」是 LIVE，「47→1」是推算 —— 两栏必须分开。"""
    t = CONTRACT.read_text(encoding="utf-8", errors="replace")
    assert "覆盖式" in t and "全删全建" in t, "契约里「覆盖式 / 全删全建」的说法被改掉了"
    assert "47 → 1" in t or "47→1" in t, "契约里的「47→1」推算段落被删了"
    assert "推算，不是实测" in t, (
        "契约里「47→1 是推算，不是实测」这句被删了 —— 那是这条判据的地基")

    text = _readme()
    assert "推算，不是实测" in text, "入口 §三① 没保留「推算不是实测」"
    # 入口必须把两栏分开，而不是合并成一句
    assert "机制可以是 LIVE 的，而解释机制的那个数字是推算的" in text, (
        "入口没把「机制 LIVE / 数字推算」的分栏判据写出来")


def test_withdrawn_conclusion_stays_withdrawn():
    """已撤回的「409 条与 DB 互证」必须保持撤回。"""
    t = CONTRACT.read_text(encoding="utf-8", errors="replace")
    assert "已撤回" in t, "契约里「已撤回」的段落被删了"
    i = t.find("409")
    assert i > 0, "「409 条与 DB 互证」的记录不见了 —— 撤回记录比结论本身值钱"
    seg = t[max(0, i - 200):i + 200]
    assert "撤回" in seg, "409 附近没有「撤回」字样，可能被恢复成结论了"
    assert "已撤回" in _readme(), "入口 §三② 没保留「已撤回」这件事"


def test_danger_zone_and_auto_trigger_recorded():
    """两条高危：func-auth 覆盖式 + 进页面自动触发 create-system-admin。"""
    t = CONTRACT.read_text(encoding="utf-8", errors="replace")
    assert "DANGER-ZONE" in t, "契约里的 DANGER-ZONE 风险登记面被删了"
    assert "自动触发" in t and "create-system-admin" in t, (
        "契约里「进角色权限页自动触发 create-system-admin」的记录被删了")

    text = _readme()
    for token in ("覆盖式", "自动触发", "DANGER-ZONE", "「只读观测」在这个页面上不存在"):
        assert token in text, "入口 §三 缺「%s」" % token
    assert "resource_type" in text and "恒为 MENU" in text, (
        "入口没记 func-auth 的已知缺陷（resource_type 恒为 MENU）")
    assert "disabled" in text and "查看模式" in text, (
        "入口没记「31/31 disabled 不是只读」这个陷阱")


def test_evidence_dir_intact():
    """javap + class 必须都在仓，否则「可自验」无从谈起。"""
    assert ART.is_dir(), "证据目录不见了：%s" % ART
    for f in ("UdcRoleController.javap.txt", "UdcRoleController.class"):
        assert (ART / f).is_file(), "缺 %s" % f


def test_no_customer_identifiers():
    text = _readme()
    bad = [w for w in ("xiangmuguanli", "znxmglpt", "datamigration") if w in text]
    assert not bad, "域入口 README 出现客户标识词根：%s" % bad
    # 保留段代号可以出现，但必须是 9000… 开头
    for m in re.finditer(r"\b9\d{18}\b", text):
        assert m.group(0).startswith("9000000000000000"), (
            "入口出现了非保留段的 19 位数字：%s" % m.group(0))
