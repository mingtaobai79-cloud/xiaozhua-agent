"""标品复用：反查索引 + 计划阶段拦截。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.construction.business_action_index import (  # noqa: E402
    CURATED, NO_REINVENT, render_markdown, search, suggest_for_capability,
)
from components.construction.business_plan import validate_plan  # noqa: E402


def test_business_term_finds_standard_capability():
    """★核心：中文业务词必须能查到标品能力（原来 0 命中）。"""
    r = search("发起流程")
    assert r["total"] >= 1, r
    svc = r["hits"][0]["service"]
    assert "BpmAppService" in svc, svc
    assert r["hits"][0]["method"] == "send"
    assert "BpmSendDto" in r["hits"][0]["inputDto"]


def test_people_query_by_business_word():
    r = search("查人")
    assert r["total"] >= 1
    assert "Org" in r["hits"][0]["service"]


def test_file_upload_by_business_word():
    r = search("上传文件")
    assert r["total"] >= 1
    assert "Storage" in r["hits"][0]["service"]


def test_class_name_still_works():
    """英文类名走签名库兜底。"""
    r = search("BpmAppService")
    assert r["total"] >= 1
    assert any("signature" in h or "service" in h for h in r["hits"])


def test_unknown_term_says_no_hit_not_fabricate():
    """查不到就明说，不许编方法名。"""
    r = search("量子纠缠审批器")
    assert r["total"] == 0
    assert "不要自己发明方法名" in r["note"]


def test_every_curated_entry_has_evidence():
    """★ CURATED 每条必须有证据，禁止臆造。"""
    for row in CURATED:
        assert row.get("evidence"), "缺证据: %s" % row.get("terms")
        assert row.get("terms"), "缺业务词"
        assert row.get("service"), "缺接口"


def test_no_reinvent_covers_key_domains():
    for d in ("organization", "bpm", "affair", "file", "enum", "systemvariable"):
        assert d in NO_REINVENT, d


def test_suggest_domain_from_capability():
    assert [x["domain"] for x in suggest_for_capability("把审批发起出去")] == ["bpm"]
    assert "organization" in [x["domain"] for x in suggest_for_capability("查询人员所在部门")]
    assert "connector" in [x["domain"] for x in suggest_for_capability("对接外部ERP")]


def test_plan_blocks_reinventing_bpm():
    """★能力描述命中标品域但没标记 → 必须反问。"""
    plan = {"elements": [{
        "key": "send", "capability": "把单据推到审批流程里发起",
        "purpose": "SYNC", "inputShape": "SINGLE_RECORD",
        "outputShape": "STATUS_ONLY", "persistTo": "表A",
        "persistMode": "INSERT", "trigger": "MANUAL"}]}
    blocking, asks = validate_plan(plan)
    assert blocking == []
    assert any("标品已有实现" in a for a in asks), asks
    assert any("reuseChecked" in a for a in asks), asks


def test_plan_accepts_after_reuse_checked():
    plan = {"elements": [{
        "key": "send", "capability": "把单据推到审批流程里发起",
        "purpose": "SYNC", "inputShape": "SINGLE_RECORD",
        "outputShape": "STATUS_ONLY", "persistTo": "表A",
        "persistMode": "INSERT", "trigger": "MANUAL",
        "reuseChecked": True}]}
    blocking, asks = validate_plan(plan)
    assert blocking == []
    assert not [a for a in asks if "标品" in a], asks


def test_plan_no_hint_for_non_standard_capability():
    """不涉标品域的能力不该被无端追问。"""
    plan = {"elements": [{
        "key": "calc", "capability": "按重量和体积算出运费",
        "purpose": "QUERY", "inputShape": "SINGLE_RECORD",
        "outputShape": "SINGLE_OBJECT", "trigger": "MANUAL"}]}
    blocking, asks = validate_plan(plan)
    assert not [a for a in asks if "标品" in a], asks


def test_render_markdown_lists_domains():
    md = render_markdown()
    assert "不要重复造轮子" in md
    assert "BpmAppService" in md
    assert "organization" in md


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(list(globals().items())):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print("PASS", name)
        except Exception as ex:  # noqa: BLE001
            fails += 1
            print("FAIL", name, "->", ex)
    print()
    print("FAILS", fails)
    sys.exit(1 if fails else 0)
