"""lineage_audit 单元测试：7 种来源分类 + 嵌套遍历 + 孤立节点 + 硬编码提示。"""
import pytest

from components.construction.lineage_audit import (
    SOURCE_CONSTANT, SOURCE_TRIGGER_INPUT, SOURCE_PREVIOUS_NODE,
    SOURCE_PREVIOUS_NODE_FIELD, SOURCE_LOOP_ITEM, SOURCE_EXPRESSION,
    SOURCE_SYSTEM_VALUE, classify_value, audit_lineage,
)


@pytest.mark.parametrize("value,loop,expected", [
    ({"const": "X"}, set(), SOURCE_CONSTANT),
    ({"const": 3}, set(), SOURCE_CONSTANT),
    ("裸字面量", set(), SOURCE_CONSTANT),
    ({"input": "requestId"}, set(), SOURCE_TRIGGER_INPUT),
    ({"field": "$input"}, set(), SOURCE_TRIGGER_INPUT),
    ({"field": "$input.id"}, set(), SOURCE_TRIGGER_INPUT),
    ({"field": "reqId"}, set(), SOURCE_PREVIOUS_NODE),
    ({"field": "req.totalAmount"}, set(), SOURCE_PREVIOUS_NODE_FIELD),
    ({"item": "loop", "field": "materialId"}, set(), SOURCE_LOOP_ITEM),
    ({"field": "loop.materialId"}, {"loop"}, SOURCE_LOOP_ITEM),
    ({"arith": "ADD", "items": []}, set(), SOURCE_EXPRESSION),
    ({"fn": "containsText"}, set(), SOURCE_EXPRESSION),
    ({"op": "EQ"}, set(), SOURCE_EXPRESSION),
    ({"system": "now"}, set(), SOURCE_SYSTEM_VALUE),
])
def test_classify_value(value, loop, expected):
    assert classify_value(value, loop) == expected


def test_audit_lineage_sources_and_nesting():
    draft = {
        "nodes": [
            {"id": "req", "kind": "retrieve", "entity": "采购申请",
             "by_id_from": "$input"},
            {"id": "reqId", "kind": "create_variable", "value": {"field": "req.id"}},
            {"id": "loop", "kind": "for_each", "list": "items", "body": [
                {"id": "w1", "kind": "create_entity", "entity": "明细", "fields": {
                    "materialId": {"field": "loop.materialId"},
                    "qty": {"const": 1},
                }},
            ]},
            {"id": "chk", "kind": "branch",
             "condition": {"op": "GE", "left": {"field": "req.totalAmount"},
                           "right": {"const": 0}},
             "then": [
                 {"id": "w2", "kind": "create_entity", "entity": "结果", "fields": {
                     "requestId": {"field": "reqId"},
                     "totalAmount": {"field": "req.totalAmount"},
                     "note": {"const": "OK"},
                 }},
             ],
             "else": []},
        ],
    }
    rep = audit_lineage(draft)
    srcs = rep["metrics"]["sources"]
    assert srcs[SOURCE_CONSTANT] == 2      # qty + note
    assert srcs[SOURCE_LOOP_ITEM] == 1     # materialId
    assert srcs[SOURCE_PREVIOUS_NODE] == 1  # requestId <- reqId
    assert srcs[SOURCE_PREVIOUS_NODE_FIELD] == 1  # totalAmount <- req.totalAmount
    assert srcs[SOURCE_TRIGGER_INPUT] == 0


def test_isolated_node_detected():
    # items 查了但没被任何下游引用 → 孤立；req 被引用 → 不孤立
    draft = {
        "nodes": [
            {"id": "req", "kind": "retrieve", "entity": "采购申请", "by_id_from": "$input"},
            {"id": "items", "kind": "retrieve_array", "entity": "明细",
             "cond_field": "requestId", "right": {"field": "req"}},
            {"id": "w", "kind": "create_entity", "entity": "结果", "fields": {
                "requestId": {"field": "req"},
            }},
        ],
    }
    rep = audit_lineage(draft)
    assert rep["metrics"]["isolated_nodes"] == ["items"]


def test_hardcoded_link_hint():
    draft = {
        "nodes": [
            {"id": "req", "kind": "retrieve", "entity": "采购申请", "by_id_from": "$input"},
            {"id": "w", "kind": "create_entity", "entity": "结果", "fields": {
                "requestId": {"field": "req"},
                "bizKey": {"const": "REQ-001"},  # 同节点有引用，却硬编码 key
            }},
        ],
    }
    rep = audit_lineage(draft)
    hints = rep["metrics"]["hardcoded_links"]
    assert len(hints) == 1
    assert hints[0]["field"] == "bizKey"


def _import_score_case():
    from components.construction.lineage_audit import score_case
    return score_case


def test_score_case_crud_heap_scores_low():
    score_case = _import_score_case()
    # 全 const、无引用、无孤立 → 引用率 0，扣 30 分 → 70（B）
    draft = {"nodes": [
        {"id": "w", "kind": "create_entity", "entity": "结果", "fields": {
            "a": {"const": "x"}, "b": {"const": 1}, "c": {"const": "y"}}},
    ]}
    r = score_case(draft)
    assert r["ref_rate"] == 0.0
    assert r["score"] < 75
    assert r["grade"] in ("B", "C")


def test_score_case_isolated_deducts_20():
    score_case = _import_score_case()
    # 有引用（ref_rate 高）但有 1 个孤立节点 → 扣 20
    draft = {"nodes": [
        {"id": "req", "kind": "retrieve", "entity": "采购申请", "by_id_from": "$input"},
        {"id": "items", "kind": "retrieve_array", "entity": "明细",
         "cond_field": "requestId", "right": {"field": "req"}},  # 孤立（没被用）
        {"id": "w", "kind": "create_entity", "entity": "结果", "fields": {
            "requestId": {"field": "req"}, "total": {"field": "req.totalAmount"}}},
    ]}
    r = score_case(draft)
    assert r["isolated_nodes"] == ["items"]
    assert r["score"] == 80  # 100 - 20（孤立），ref_rate=1 不扣


def test_score_case_clean_read_only_scores_s():
    score_case = _import_score_case()
    draft = {"nodes": [
        {"id": "req", "kind": "retrieve", "entity": "采购申请", "by_id_from": "$input"},
    ]}
    r = score_case(draft)
    assert r["score"] == 100
    assert r["grade"] == "S"


def test_score_case_full_dynamic_scores_s():
    score_case = _import_score_case()
    # 全字段引用 + 无孤立 + 无硬编码 → 100 S
    draft = {"nodes": [
        {"id": "req", "kind": "retrieve", "entity": "采购申请", "by_id_from": "$input"},
        {"id": "w", "kind": "create_entity", "entity": "结果", "fields": {
            "requestId": {"field": "req"},
            "totalAmount": {"field": "req.totalAmount"}}},
    ]}
    r = score_case(draft)
    assert r["ref_rate"] == 1.0
    assert r["score"] == 100
    assert r["grade"] == "S"
