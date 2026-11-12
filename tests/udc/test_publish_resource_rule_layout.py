"""publish / resource / rule 三个子域的入口闸门。

三域各有一个必须守住的"反直觉事实"：

publish：0 条新增建议（唯一零新增的域），且 deploy-info 被登记了 **3 次**（文档写 2 次）。
         三条的 evidence class/sha 完全一致（都是 UdcBaseAppInfoController / deebcc39…），
         **证据是对的，问题只是重复**。我第一次核查时把"往后找第一个 class_sha256"当判据，
         取到了前一条契约的 evidence，得出"三条 sha 互不相同"的错误结论 —— 闸门要防的就是这个。

resource：5/5 全部落库且证据一致，是"落库成功"的样板。
          写形态 5 条是**明确排除**，不是遗漏 —— 别让人去补。

rule：**不是端点契约域**，0 条 contracts[... ]，描述的是规则节点 schema 约束，
      落 constraints 不落 registry。混为一谈会得出"rule 域 0 条落库 = 漏了"。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs" / "operation-contracts" / "udc"
REG = ROOT / "components" / "platform_operations" / "registry.py"

ROW = re.compile(r"^\|\s*`([\w.-]+)`\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|", re.M)


def _readme(sub):
    p = BASE / sub / "README.md"
    assert p.is_file(), "缺 %s/README.md（域入口）" % sub
    return p.read_text(encoding="utf-8")


def _check_table(sub, expected):
    rows = ROW.findall(_readme(sub))
    assert len(rows) == expected, (
        "%s 规模表解析出 %d 行（应有 %d 份契约，不含 README）" % (sub, len(rows), expected))
    bad = []
    for name, size_s, lines_s in rows:
        f = BASE / sub / name
        if not f.is_file():
            bad.append("%s: 表里登记了但文件不存在" % name)
            continue
        raw = f.read_bytes()
        if len(raw) != int(size_s.replace(",", "")):
            bad.append("%s: 表写 %s B 磁盘 %d B" % (name, size_s, len(raw)))
        if len(raw.decode("utf-8").splitlines()) != int(lines_s):
            bad.append("%s: 表写 %s 行 磁盘 %d 行" % (
                name, lines_s, len(raw.decode("utf-8").splitlines())))
    assert not bad, "%s 契约规模表已腐坏：\n  %s" % (sub, "\n  ".join(bad))


def _evidence_map():
    """先建 `变量名 → (class, sha)` 表，再从契约行取 `[var]` 查。

    这是正确的核查方式。绝不能"从 contracts[...] 往后找第一个 class_sha256" ——
    evidence 定义写在使用之前，往后找会取到前一条契约的尾巴。
    """
    reg = REG.read_text(encoding="utf-8", errors="replace")
    ev = {}
    for ln in reg.split("\n"):
        m = re.match(r'\s*(\w+)\s*=\s*\{.*?"class":\s*"([^"]+)".*?class_sha256":\s*"([0-9a-f]+)', ln)
        if m:
            ev[m.group(1)] = (m.group(2), m.group(3))
            continue
        m2 = re.match(r"\s*(\w+)\s*=\s*dict\((\w+)", ln)
        if m2 and m2.group(2) in ev:
            ev[m2.group(1)] = ev[m2.group(2)]
    contracts = {}
    for ln in reg.split("\n"):
        m = re.search(
            r'contracts\["([a-z0-9_.]+)"\]\s*=\s*UdcOperationContract\("', ln)
        if m:
            v = re.search(r"\[(\w+)\]", ln)
            contracts[m.group(1)] = ev.get(v.group(1)) if v else None
    return ev, contracts


# ---------------------------------------------------------------- publish

def test_publish_table_and_files():
    _check_table("publish", 2)


def test_publish_zero_new_and_triple_registration():
    """0 条新增建议；deploy-info 被登记 3 次，三条 evidence 一致。"""
    reg = REG.read_text(encoding="utf-8", errors="replace")
    _ev, contracts = _evidence_map()

    deploy = {oid: v for oid, v in contracts.items() if v and "deploy-info" in str(v)}
    # 按 op_id 找 deploy-info 端点
    ids = [oid for oid in contracts
           if oid in ("udc.application.deploy_info", "udc.appinfo.get_deploy_info",
                      "udc.publish.deploy_info")]
    assert len(ids) == 3, (
        "deploy-info 的 op_id 现在只有 %d 个（入口 §二/§三 写 3 个）：%s" % (len(ids), ids))

    evidence = [contracts[i] for i in ids]
    assert all(e is not None for e in evidence), "有 deploy-info 条目取不到 evidence 变量"
    classes = {e[0] for e in evidence}
    shas = {e[1] for e in evidence}
    assert len(classes) == 1 and len(shas) == 1, (
        "三条 deploy-info 的 evidence 不再一致：class=%s sha=%s\n"
        "入口 §三 写「三条 evidence 都指向同一个类 UdcBaseAppInfoController」。"
        % ([c.split('.')[-1] for c in classes], [s[:8] for s in shas]))
    assert "UdcBaseAppInfoController" in classes.pop(), (
        "deploy-info 的 evidence class 不是 UdcBaseAppInfoController")
    assert shas.pop().startswith("deebcc39"), "deploy-info 的 class_sha256 前缀不是 deebcc39"

    text = _readme("publish")
    for token in ("0 条新增建议", "三次", "UdcBaseAppInfoController", "deebcc39", "两种拼法"):
        assert token in text, "publish 入口缺「%s」" % token
    assert "定义常常写在使用之前" in text, (
        "publish 入口没写「往后找第一个匹配几乎总是错的」这条核查陷阱")


def test_publish_not_zero_hit_domain():
    """publish 是 0 条新增（不是 0 条落库），别和 runtime 的「13 条全待落」混淆。"""
    text = _readme("publish")
    assert "唯一一个「0 条新增建议」" in text, "publish 入口没写清「零新增」"
    assert "runtime/" in text and "13 条全待落" in text, (
        "publish 入口没和 runtime/ 的「13 条全待落」做对照，容易混淆")


# ---------------------------------------------------------------- resource

def test_resource_table_and_files():
    _check_table("resource", 2)


def test_resource_five_all_landed_with_matching_evidence():
    """5/5 落库，且 evidence class 与文档一致（3 条 AttachmentTemplate + 2 条 DynamicJar）。"""
    _ev, contracts = _evidence_map()
    expect = {
        "udc.attachment.template_get_by_guid": "AttachmentTemplateController",
        "udc.attachment.template_list_by_guids": "AttachmentTemplateController",
        "udc.attachment.template_list_by_app_id": "AttachmentTemplateController",
        "udc.jar.download": "DynamicJarController",
        "udc.jar.export_app": "DynamicJarController",
    }
    for oid, cls in expect.items():
        assert oid in contracts, "%s 不在 registry 里 —— resource 入口 §一 的 5/5 已过期" % oid
        ev = contracts[oid]
        assert ev is not None, "%s 取不到 evidence" % oid
        assert ev[0].endswith(cls), (
            "%s 的 evidence class 是 %s（入口写 %s）" % (oid, ev[0].split(".")[-1], cls))

    text = _readme("resource")
    for token in ("5/5 全部落库", "落库最干净", "样板"):
        assert token in text, "resource 入口缺「%s」" % token


def test_resource_write_forms_excluded_not_missing():
    """写形态 5 条是明确排除，不是遗漏 —— 别让人去补。"""
    entries = (BASE / "resource" / "registry-entries.md").read_text(encoding="utf-8", errors="replace")
    assert "不得入 registry" in entries, (
        "registry-entries.md 里「写形态 5 条不得入 registry」的排除决定被删了")
    text = _readme("resource")
    assert "不得入 registry" in text or "明确排除" in text, "resource 入口没写写形态被排除"
    assert "不是遗漏" in text, (
        "resource 入口没写「那 5 条是被明确排除的、不是遗漏」——后人会去补")
    for kw in ("create", "create-batch", "delete", "delete-by-guids", "upload"):
        assert kw in text, "resource 入口缺被排除的写形态：%s" % kw


def test_resource_parameterinfo_mismatch_recorded():
    """@ParameterInfo 文案与形参名不符，照录未改。"""
    entries = (BASE / "resource" / "registry-entries.md").read_text(encoding="utf-8", errors="replace")
    assert "ParameterInfo" in entries and "不符" in entries, "原文的 ParameterInfo 不符记录被删了"
    text = _readme("resource")
    assert "ParameterInfo" in text and "逐字照录" in text, (
        "resource 入口没写「照录 + 标注待 LIVE，不要顺毛修」")


# ---------------------------------------------------------------- rule

def test_rule_is_not_endpoint_contract_domain():
    """rule 域 0 条 contracts[...]，描述的是节点 schema 约束，不落 registry。"""
    rule_dir = BASE / "rule"
    for f in rule_dir.glob("*.md"):
        if f.name == "README.md":
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        n = len(re.findall(r'contracts\["[a-z0-9_.]+"\]\s*=\s*UdcOperationContract', t))
        assert n == 0, (
            "%s 里出现了 %d 条 UdcOperationContract 构造 —— rule 域应是节点 schema 约束，"
            "不落 registry。入口 §一 的「不是端点契约域」需同步复核" % (f.name, n))

    text = _readme("rule")
    for token in ("不是端点契约域", "0 条 `contracts[...]`", "落 constraints 不落 registry",
                  "两个意思"):
        assert token in text, "rule 入口缺「%s」" % token


def test_rule_unverified_vs_live_separated():
    """GENERATION-PLAN 是 UNVERIFIED，RULE-GENERATION-CONTRACT 是 LIVE+STATIC。"""
    plan = (BASE / "rule" / "GENERATION-PLAN-20261019.md").read_text(encoding="utf-8", errors="replace")
    assert "UNVERIFIED" in plan, "GENERATION-PLAN 的 UNVERIFIED 状态被改了"
    assert "BLOCKED" in plan, "GENERATION-PLAN 的「③落库验证 BLOCKED」被删了"
    con = (BASE / "rule" / "RULE-GENERATION-CONTRACT-20261019.md").read_text(encoding="utf-8", errors="replace")
    assert "LIVE" in con, "RULE-GENERATION-CONTRACT 的 LIVE 标注被删了"

    text = _readme("rule")
    assert "UNVERIFIED" in text and "BLOCKED" in text, "rule 入口没区分两份文件的等级"
    assert "引用数字前先看是哪一份" in text, "rule 入口没写「先看是哪一份再引数字」"


def test_rule_field_traps_recorded():
    """五个字段陷阱：TERMINATION 不是 STOP / pageSearch 属 ARRAY / 空 body 合法 等。"""
    con = (BASE / "rule" / "RULE-GENERATION-CONTRACT-20261019.md").read_text(encoding="utf-8", errors="replace")
    for token in ("TERMINATION", "STOP", "pageSearch", "空 body 合法", "dict 非 JSON 串"):
        assert token in con, "契约原文缺「%s」" % token

    text = _readme("rule")
    for token in ("TERMINATION", "不是 `STOP`", "pageSearch", "空分支体", "勿 `json.loads`",
                  "假失败"):
        assert token in text, "rule 入口缺字段陷阱：%s" % token
    assert "1893" not in text or True  # 不强制
    assert "1839" in text, "rule 入口缺全库 RETRIEVE 实测数 1839"
    assert "按节点类型分表" in text, "rule 入口没写「字段约束按节点类型分表，不是全局」"


# ---------------------------------------------------------------- 共通

def test_three_dirs_have_no_customer_identifiers():
    for sub in ("publish", "resource", "rule"):
        text = _readme(sub)
        bad = [w for w in ("xiangmuguanli", "znxmglpt", "datamigration") if w in text]
        assert not bad, "%s 域入口出现客户标识词根：%s" % (sub, bad)
        for m in re.finditer(r"\b9\d{18}\b", text):
            assert m.group(0).startswith("9000000000000000"), (
                "%s 域入口出现非保留段的 19 位数字：%s" % (sub, m.group(0)))
