"""表达式层审计的契约测试（不连浏览器）。"""
from __future__ import annotations

import json

import pytest

from components.udc.microflow.expression_audit import (
    EXPR_SIGNATURE_KEYS,
    TOKEN_TYPES,
    audit_node_expressions,
    check_expression,
    check_three_layers,
    collect_known_vars,
    is_expression,
    iter_expressions,
    parse_expression,
    variable_roots,
)


def _expr(title, tokens, result="BOOLEAN"):
    schema = {
        "designData": {
            "expressionTranslation": title,
            "resultTypeInfo": result,
            "terminalType": "BACKEND",
            "context": [],
            "tokens": tokens,
        },
        "runtimeData": {"executableExpr": "SIG(" + title + ")"},
    }
    return {"title": title, "schema": json.dumps(schema, ensure_ascii=False)}


def _tok(tp, val, desc=""):
    return {"type": tp, "value": val, "desc": desc}


# ---------------------------------------------------------------- 识别

def test_is_expression_recognises_real_shape():
    """expression 是 {title, schema}，schema 含 designData"""
    e = _expr("a > 0", [_tok("VARIABLE", "x.f"), _tok("OPERATOR", ">"),
                        _tok("CONSTANT", "0")])
    assert is_expression(e)


def test_is_expression_rejects_plain_string():
    """★ 关键：expression 不是字符串，字符串判定必须为 False

    这正是历史审计漏检的根因 —— 只匹配字符串字段会跳过整个表达式层。
    """
    assert not is_expression("微流程.查询单条数据(1).实验数量 > 0")


def test_is_expression_rejects_dict_without_schema():
    assert not is_expression({"title": "x", "value": "y"})


def test_iter_expressions_finds_nested_in_conditions():
    """BRANCH → conditions[].expression 必须能找到"""
    node = {
        "nodeId": "BRANCH_1",
        "actionType": "BRANCH",
        "conditions": [
            {"nodeId": "C1",
             "expression": _expr("a > 0", [_tok("VARIABLE", "v.f"),
                                           _tok("OPERATOR", ">"),
                                           _tok("CONSTANT", "0")])},
        ],
    }
    found = list(iter_expressions(node))
    assert len(found) == 1
    assert "conditions[0].expression" in found[0][0]


def test_iter_expressions_stops_at_expression():
    """命中 expression 后不再往里钻（避免把 token 当表达式）"""
    node = {"expression": _expr("a", [_tok("CONSTANT", "1")])}
    found = list(iter_expressions(node))
    assert len(found) == 1


# ---------------------------------------------------------------- 解析

def test_parse_expression_extracts_all_fields():
    e = _expr("a > 0", [_tok("VARIABLE", "v.f"), _tok("OPERATOR", ">"),
                        _tok("CONSTANT", "0")])
    info = parse_expression(e)
    assert info["title"] == "a > 0"
    assert info["resultType"] == "BOOLEAN"
    assert info["terminalType"] == "BACKEND"
    assert len(info["tokens"]) == 3
    assert info["executableExpr"].startswith("SIG(")


def test_variable_roots_only_from_variable_tokens():
    e = _expr("a > 0", [_tok("VARIABLE", "_RETRIEVE_MSwqDF._RETRIEVE_MSwqDF.expNum"),
                        _tok("OPERATOR", ">"), _tok("CONSTANT", "0")])
    assert variable_roots(e) == ["_RETRIEVE_MSwqDF"]


# ---------------------------------------------------------------- 体检

def test_dangling_variable_detected():
    """引用的变量根不在流程输出中 → 悬空"""
    e = _expr("a > 0", [_tok("VARIABLE", "_RETRIEVE_Ltqgzz.x.expNum"),
                        _tok("OPERATOR", ">"), _tok("CONSTANT", "0")])
    probs = check_expression(e, {"_RETRIEVE_MSwqDF"})
    assert any("悬空引用" in p["issue"] for p in probs)
    assert any("_RETRIEVE_Ltqgzz" in p["issue"] for p in probs)


def test_valid_variable_passes():
    e = _expr("a > 0", [_tok("VARIABLE", "_RETRIEVE_MSwqDF._RETRIEVE_MSwqDF.expNum"),
                        _tok("OPERATOR", ">"), _tok("CONSTANT", "0")])
    assert check_expression(e, {"_RETRIEVE_MSwqDF"}) == []


def test_identity_expression_detected():
    """x > x 恒等式必须被检出"""
    v = "_RETRIEVE_MSwqDF._RETRIEVE_MSwqDF.expNum"
    e = _expr("a > a", [_tok("VARIABLE", v), _tok("OPERATOR", ">"),
                        _tok("VARIABLE", v)])
    probs = check_expression(e, {"_RETRIEVE_MSwqDF"})
    assert any("恒等式" in p["issue"] for p in probs)


def test_two_different_variables_not_identity():
    e = _expr("a > b", [_tok("VARIABLE", "v.a"), _tok("OPERATOR", ">"),
                        _tok("VARIABLE", "w.b")])
    probs = check_expression(e, {"v", "w"})
    assert not any("恒等式" in p["issue"] for p in probs)


def test_empty_tokens_detected():
    e = _expr("", [])
    probs = check_expression(e, set())
    assert any("tokens 为空" in p["issue"] for p in probs)


def test_invalid_token_type_detected():
    """token.type 只允许五型"""
    e = _expr("a", [_tok("SYSTEM_VARIABLE", "x")])
    probs = check_expression(e, {"x"})
    assert any("五型值域" in p["issue"] for p in probs)
    assert "SYSTEM_VARIABLE" not in TOKEN_TYPES


def test_token_type_domain_is_five():
    assert TOKEN_TYPES == ("CONSTANT", "VARIABLE", "SYSTEM", "FUNCTION", "OPERATOR")


# ---------------------------------------------------------------- 节点级

def test_audit_node_expressions_carries_context():
    node = {
        "nodeId": "CONDITION_MMPEJO",
        "actionType": "CONDITION",
        "expression": _expr("a > a", [_tok("VARIABLE", "bad.x"),
                                      _tok("OPERATOR", ">"),
                                      _tok("VARIABLE", "bad.x")]),
    }
    probs = audit_node_expressions(node, {"good"})
    assert probs
    for p in probs:
        assert p["nodeId"] == "CONDITION_MMPEJO"
        assert p["action"] == "CONDITION"
        assert "where" in p


# ---------------------------------------------------------------- 变量收集

def test_collect_known_vars_includes_nested_and_input():
    schema = {
        "input": {"name": "_FLOW_INPUT_x1"},
        "nodes": [
            {"output": {"name": "_A"}, "nodes": [
                {"output": {"name": "_B"}},
            ]},
            {"conditions": [
                {"output": {"name": "_C"}, "nodes": [
                    {"output": {"name": "_D"}},
                ]},
            ]},
        ],
    }
    names = collect_known_vars(schema)
    assert names == {"_FLOW_INPUT_x1", "_A", "_B", "_C", "_D"}


# ---------------------------------------------------------------- 三层一致

def test_three_layers_inconsistent_detected():
    """★ 核心场景：L1 改了，L3 没变"""
    l1 = {"title": "实验数量 > 0"}
    l3 = {"title": "实验数量 > 实验数量"}
    r = check_three_layers(l1, l3)
    assert r["same"] is False
    assert "不一致" in r["verdict"]
    assert "暂存草稿" in r["verdict"]


def test_three_layers_consistent():
    same = {"title": "实验数量 > 0"}
    r = check_three_layers(same, same)
    assert r["same"] is True
    assert r["verdict"] == "一致"


def test_three_layers_l3_empty():
    r = check_three_layers({"title": "a"}, None)
    assert r["same"] is False
    assert "从未保存" in r["verdict"]
