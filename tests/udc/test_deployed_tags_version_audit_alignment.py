# -*- coding: utf-8 -*-
"""部署态构件 tag 入版本审计的护栏（第十四轮 · 候选 (vii)）。

**钉死的事**：`docs/audit/agent-version-audit.md` §2.1 登记的 19 个 LIVE 构件 tag，
必须与证据件 `docs/audit/udc-semantics/DEPLOYED-COMPONENT-TAGS.json#deployed_tags`
**双向逐条一致**（少一条 / 多一条 / 版本漂移都算失败），且两侧都不得出现客户标识。

对齐判定收敛到 `check_alignment()`；`test_alignment_checker_bites_on_mutation`
用**内存内突变**自证会咬（不写文件 ⇒ 失败不可能是并发会话造成的假象）。

本文件不含客户业务明细：只引平台构件名与平台版本号。
（本文件刻意不使用反斜杠转义：换行一律用 `chr(10)`，避免转义层降级。）
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "audit" / "agent-version-audit.md"
EVID = ROOT / "docs" / "audit" / "udc-semantics" / "DEPLOYED-COMPONENT-TAGS.json"

SECTION_HEAD = "### 2.1 部署态构件版本"
FACADES = {"bpm": "5.3.374", "organization": "5.3.368", "ctp-user": "5.3.429"}
NL = chr(10)


def _live_tags() -> dict:
    return json.loads(EVID.read_text(encoding="utf-8"))["deployed_tags"]


def _section(text: str) -> str:
    try:
        start = text.index(SECTION_HEAD)
    except ValueError:
        raise ValueError("audit doc 缺少小节: " + SECTION_HEAD)
    nxt = text.find(NL + "### ", start + 1)
    return text[start:nxt if nxt > 0 else len(text)]


def _table_pairs(section: str) -> dict:
    """把双列表格解析成 {构件: 版本}（只认 `comp`|`x.y.z` 形态的相邻单元格对）。"""
    out = {}
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        for i in range(len(cells) - 1):
            comp = re.fullmatch(r"`([a-z][a-z0-9-]*)`", cells[i])
            ver = re.fullmatch(r"`(\d+[.]\d+[.]\d+)`", cells[i + 1])
            if comp and ver:
                out[comp.group(1)] = ver.group(1)
    return out


def check_alignment(text: str) -> list:
    """返回问题清单；空列表 = 文档 §2.1 与证据件双向一致。"""
    try:
        sec = _section(text)
    except ValueError as exc:
        return [str(exc)]

    problems = []
    tags = _live_tags()
    declared = _table_pairs(sec)

    for comp in sorted(set(tags) - set(declared)):
        problems.append("§2.1 缺构件行: " + comp)
    for comp in sorted(set(declared) - set(tags)):
        problems.append("§2.1 多出证据件没有的构件: " + comp)
    for comp in sorted(set(tags) & set(declared)):
        if tags[comp] != declared[comp]:
            problems.append("§2.1 版本漂移 " + comp + ": 证据件=" + tags[comp] + " 文档=" + declared[comp])

    if len(declared) != 19:
        problems.append("§2.1 解析到的构件行数 != 19: " + str(len(declared)))
    if "LIVE" not in sec:
        problems.append("§2.1 未标注证据等级 LIVE")
    if "K8s API" not in sec:
        problems.append("§2.1 未登记取数通道（K8s API）")
    if "DEPLOYED-COMPONENT-TAGS.json" not in sec:
        problems.append("§2.1 未引证据件路径")
    if "REFUTED" not in sec:
        problems.append("§2.1 未保留第十轮证伪结论")
    if "不是部署集合" not in sec:
        problems.append("§2.1 未声明「静态样本集不是部署集合」")
    return problems


def test_audit_doc_registers_exactly_the_19_live_component_tags():
    assert check_alignment(DOC.read_text(encoding="utf-8")) == []


def test_live_tag_section_records_channel_date_and_evidence_level():
    sec = _section(DOC.read_text(encoding="utf-8"))
    assert "LIVE" in sec
    assert "K8s API" in sec and "pods" in sec
    assert "spec.containers[].image" in sec
    assert "2026-10-15" in sec
    assert "19/19" in sec


def test_evidence_json_reverification_is_recorded():
    data = json.loads(EVID.read_text(encoding="utf-8"))
    rev = data["reverification"]
    assert rev["matched"] == 19
    assert rev["components_seen"] == 19
    assert rev["differences"] == 0
    assert rev["not_seen"] == []
    assert rev["result"].startswith("19/19 identical")
    assert rev["channel"].startswith("K8s API read-only GET")


def test_evidence_json_still_pins_udc_and_three_runtime_facades():
    tags = _live_tags()
    assert tags["udc"] == "5.3.517"
    for comp, ver in FACADES.items():
        assert tags[comp] == ver, (comp, tags[comp], ver)
    assert len(tags) == 19
    for comp, ver in tags.items():
        assert re.fullmatch(r"[a-z][a-z0-9-]*", comp), comp
        assert re.fullmatch(r"\d+[.]\d+[.]\d+", ver), (comp, ver)


def test_static_sample_set_is_not_written_as_deployment_set():
    sec = _section(DOC.read_text(encoding="utf-8"))
    assert "sampled version set" in sec
    assert "不是部署集合" in sec
    assert "不得" in sec
    body = DOC.read_text(encoding="utf-8")
    for v in ("3.8.227", "3.12.124", "5.3.314", "5.3.380", "5.3.477", "5.3.517"):
        assert "`" + v + "`" in body, v


def test_no_client_identifiers_in_live_tag_section_nor_evidence():
    sec = _section(DOC.read_text(encoding="utf-8"))
    assert not re.search(r"\d{6,}", sec), "§2.1 出现 6 位以上数字串（疑似客户标识）"
    assert not re.search(r"\d{6,}", EVID.read_text(encoding="utf-8"))


def test_doc_keeps_round10_refutation_and_the_pods_exec_boundary():
    sec = _section(DOC.read_text(encoding="utf-8"))
    assert "REFUTED" in sec
    assert "唯一" in sec and "request url:/udc/**" in sec
    assert "pods/exec" in sec and "forbidden" in sec
    assert "BOOT-INF/lib" in sec


def _udc_row_index(lines, first_line):
    """§2.1 表格里 `udc` 那行的行号（必须在小节内，不能在 §2 事实版本表里）。"""
    for i, line in enumerate(lines):
        if i > first_line and line.startswith("|") and "`udc`" in line:
            return i
    raise AssertionError("§2.1 内找不到 udc 构件行")


def test_alignment_checker_bites_on_mutation():
    """内存内突变自证：改版本 / 删行 / 加幻影构件 / 删小节 都必须被抓到。"""
    orig = DOC.read_text(encoding="utf-8")
    assert check_alignment(orig) == []

    lines = orig.splitlines()
    first_line = orig[: orig.index(SECTION_HEAD)].count(NL)
    idx = _udc_row_index(lines, first_line)
    assert "`5.3.517`" in lines[idx]

    drifted = lines.copy()
    drifted[idx] = drifted[idx].replace("`5.3.517`", "`5.3.518`")
    assert check_alignment(NL.join(drifted)), "版本漂移未被抓到"

    dropped = lines.copy()
    dropped.pop(idx)
    assert check_alignment(NL.join(dropped)), "删行未被抓到"

    phantom = lines.copy()
    phantom.insert(idx + 1, "| `phantom-component` | `5.3.511` | — | — |")
    assert check_alignment(NL.join(phantom)), "幻影构件未被抓到"

    relabelled = orig.replace(SECTION_HEAD, "### 2.1 改了个标题")
    assert check_alignment(relabelled), "小节缺失未被抓到"
