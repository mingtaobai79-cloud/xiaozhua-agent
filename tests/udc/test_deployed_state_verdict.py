# -*- coding: utf-8 -*-
"""部署态裁定护栏（第十轮 · 候选 (iv) 收口）。

**钉死三件事**（全部据已落盘的部署态字节码 / LIVE 证据件，不联网）：

1. `MicroFlowGroupController` 的**部署态**映射字面 = `udc/micro-flow-group`；
   `selectByAppId` 的 `@PostMapping` 值 = **`select-by-type`**、方法体调 `MicroFlowGroupAppService.selectByType`
   ⇒ `/udc/micro-flow-group/select-by-appid/**` 必然 404（方法存在、映射字面不存在）；
   该类常量池里 **无** `select-by-appid`、**无** `search-list`。
2. 平台构件部署 tag 证据件（LIVE，K8s API 只读）里 **`udc` = 5.3.517**
   ⇒ 第九轮「部署版本 ≠ 5.3.517」假设**证伪**；且 19 个构件 tag 全为 `x.y.z`、无 6 位以上数字串（清洗门）。
3. 第九轮的 LIVE 证据件仍记录那两条契约外模板（防证据件腐化），
   且 `DEPLOYED-STATE-VERDICT.md` 与两者一致（防文档与证据分叉）。

本文件不含客户业务明细；只引平台路由字面量与平台构件名。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPLOYED = ROOT / "docs" / "audit" / "artifacts" / "udc-assemble-5.3.517-deployed" / "MicroFlowReadPlane.javap.txt"
TAGS = ROOT / "docs" / "audit" / "udc-semantics" / "DEPLOYED-COMPONENT-TAGS.json"
VERDICT = ROOT / "docs" / "audit" / "udc-semantics" / "DEPLOYED-STATE-VERDICT.md"
SURFACE = ROOT / "docs" / "audit" / "udc-semantics" / "RUNTIME-URL-SURFACE.json"
CONTRACT = ROOT / "docs" / "audit" / "artifacts" / "udc-web-5.3.517-contracts" / "_api_full.json"


def _group_class_section() -> str:
    txt = DEPLOYED.read_text(encoding="utf-8", errors="replace")
    start = txt.index("public class com.seeyon.udc.controller.MicroFlowGroupController")
    nxt = txt.find("Classfile jar:", start)
    return txt[start:nxt if nxt > 0 else len(txt)]


def test_group_controller_mapping_is_micro_flow_group():
    sec = _group_class_section()
    assert "#90 = Utf8               udc/micro-flow-group" in sec
    assert "RequestMapping" in sec


def test_select_by_appid_is_mapped_to_select_by_type():
    sec = _group_class_section()
    assert "#85 = Utf8               select-by-type" in sec
    assert "selectByAppId" in sec
    assert "MicroFlowGroupAppService.selectByType" in sec   # 方法体（复制粘贴瑕疵的第三处）


def test_select_by_appid_and_search_list_literals_absent_in_deployed_group_controller():
    sec = _group_class_section()
    assert "select-by-appid" not in sec
    assert "search-list" not in sec
    assert "search-list" not in DEPLOYED.read_text(encoding="utf-8", errors="replace")


def test_contract_has_same_seven_routes_and_no_search_list():
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    full = [m["full_path"] for v in data.values() for m in v["methods"] if m.get("full_path")]
    group = sorted(p for p in full if "micro-flow-group" in p)
    assert len(group) == 7, group
    assert all("select-by-appid" not in p and "search-list" not in p for p in group)


def test_deployed_udc_tag_is_5_3_517_and_hypothesis_refuted():
    d = json.loads(TAGS.read_text(encoding="utf-8"))
    tags = d["deployed_tags"]
    assert len(tags) == 19
    assert tags["udc"] == "5.3.517"
    assert d["findings"]["hypothesis_deployed_udc_neq_5_3_517"].startswith("REFUTED")
    for comp, ver in tags.items():
        assert re.fullmatch(r"[a-z][a-z0-9-]*", comp), comp
        assert re.fullmatch(r"\d+\.\d+\.\d+", ver), (comp, ver)
    assert not re.search(r"\d{6,}", TAGS.read_text(encoding="utf-8"))   # 清洗门


def test_documented_runtime_facade_versions_match_live_tags():
    tags = json.loads(TAGS.read_text(encoding="utf-8"))["deployed_tags"]
    assert tags["bpm"] == "5.3.374"
    assert tags["organization"] == "5.3.368"
    assert tags["ctp-user"] == "5.3.429"


def test_live_surface_still_records_the_two_contract_absent_templates():
    d = json.loads(SURFACE.read_text(encoding="utf-8"))
    blob = json.dumps(d, ensure_ascii=False)
    assert "micro-flow-group/select-by-appid" in blob
    assert "micro-flow-group/search-list" in blob
    # 清洗门与第九轮同口径：`source` 子树只放聚合计数，其余子树不得有 6 位以上数字串
    def _walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                yield from _walk(v, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from _walk(v, path + "/" + str(i))
        elif isinstance(o, str):
            yield path, o
    bad = [(pp, ss) for pp, ss in _walk({k: v for k, v in d.items() if k != "source"})
           if re.search(r"\d{6,}", ss)]
    assert not bad, bad[:3]


def test_verdict_doc_agrees_with_evidence():
    s = VERDICT.read_text(encoding="utf-8")
    assert "5.3.517" in s
    assert "证伪" in s
    assert "select-by-type" in s
    assert "search-list" in s
