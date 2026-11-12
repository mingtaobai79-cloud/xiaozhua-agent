"""P2-4 保存链编排：回读比对 / 阶段状态机 / 表达式校验（离线，假 backend）。"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.udc.microflow.save_pipeline import (  # noqa: E402
    CONSTRUCTED, SCHEMA_VERIFIED, UI_VERIFIED, StageResult, _state_of,
    readback_compare, verify_schema_expressions,
)

DTO = "com.seeyon.app.dto.PlanDto"


def expr_obj(tokens, result="BOOLEAN"):
    import json
    return {"title": "微流程.测试", "schema": json.dumps({"designData": {
        "resultTypeInfo": result, "terminalType": "BACKEND",
        "context": [], "tokens": tokens}, "runtimeData": {"executableExpr": "OLD"}})}


def schema_with(nodes):
    return {"trigger": {"type": "MANUAL"}, "nodes": nodes, "endNode": {"nodeId": "END"}}


def branch_node(inner):
    return {"nodeId": "BRANCH_1", "actionType": "BRANCH",
            "conditions": [{"expression": None, "nodes": inner}]}


# ---------------------------------------------------------------- 回读比对
def test_readback_identical_is_ok():
    s = schema_with([{"nodeId": "A", "actionType": "RETRIEVE",
                      "output": {"name": "_A", "dataType": "DTO"}}])
    r = readback_compare(s, s)
    assert r.ok and not r.problems


def test_readback_detects_missing_node():
    stored = schema_with([{"nodeId": "A", "actionType": "RETRIEVE", "output": {"name": "_A"}}])
    expected = schema_with([{"nodeId": "A", "actionType": "RETRIEVE", "output": {"name": "_A"}},
                            {"nodeId": "B", "actionType": "CHANGE_VARIABLE", "output": None}])
    r = readback_compare(stored, expected)
    assert not r.ok and any("缺节点" in p for p in r.problems)


def test_readback_detects_shape_drift():
    stored = schema_with([{"nodeId": "A", "actionType": "RETRIEVE", "output": {"name": "_A"}}])
    expected = schema_with([{"nodeId": "A", "actionType": "RETRIEVE", "output": {"name": "_OTHER"}}])
    r = readback_compare(stored, expected)
    assert not r.ok and any("形态差异" in p for p in r.problems)


def test_readback_walks_nested_nodes():
    inner = [{"nodeId": "IN1", "actionType": "CHANGE_VARIABLE", "output": None}]
    s = schema_with([branch_node(inner)])
    assert readback_compare(s, s).ok


# ---------------------------------------------------------------- 表达式校验
class FakeBackend:
    def __init__(self, check_ok=True, transform_ok=True, exec_expr="OLD"):
        self.check_ok, self.transform_ok, self.exec_expr = check_ok, transform_ok, exec_expr
        self.calls = 0

    def check(self, dto):
        self.calls += 1
        return {"ok": self.check_ok, "code": "BOOT_0000" if self.check_ok else "FORMULA_6058",
                "message": None if self.check_ok else "变量不存在", "content": True}

    def transform(self, dto):
        return {"ok": self.transform_ok,
                "code": "BOOT_0000" if self.transform_ok else "BOOT_3000",
                "message": None, "executableExpr": self.exec_expr,
                "designData": {"tokens": dto["tokens"]}}


TOKENS = [{"type": "VARIABLE", "value": "_A._A.expNum", "desc": "数量"},
          {"type": "OPERATOR", "value": ">"},
          {"type": "CONSTANT", "value": "0", "desc": "0"}]

# ★ 不含 VARIABLE 的表达式：只有这类才走远端 /check（facts §十三）
TOKENS_CONST = [{"type": "CONSTANT", "value": "1", "desc": "1"},
                {"type": "OPERATOR", "value": ">"},
                {"type": "CONSTANT", "value": "0", "desc": "0"}]


def test_verify_passes_with_consistent_exec():
    s = schema_with([{"nodeId": "A", "actionType": "BRANCH",
                      "expression": expr_obj(TOKENS_CONST)}])
    r = verify_schema_expressions(FakeBackend(exec_expr="OLD"), s)
    assert r.ok and r.detail["checked"] == 1


def test_verify_skips_variable_expressions():
    """★ 含 VARIABLE 的表达式不走 /check（连平台自己的真实表达式都报 6058），
    改由 checkSchema 校验。"""
    s = schema_with([{"nodeId": "A", "actionType": "BRANCH", "expression": expr_obj(TOKENS)}])
    be = FakeBackend()
    r = verify_schema_expressions(be, s)
    assert r.ok and r.detail["checked"] == 0
    assert r.detail["skipped_variable"] == 1 and be.calls == 0


def test_verify_detects_roundtrip_drift():
    """库中 executableExpr 与本次 transform 不一致 = 表达式已变质。"""
    s = schema_with([{"nodeId": "A", "actionType": "BRANCH",
                      "expression": expr_obj(TOKENS_CONST)}])
    r = verify_schema_expressions(FakeBackend(exec_expr="NEW"), s)
    assert not r.ok and any("不一致" in p for p in r.problems)


def test_verify_reports_check_failure():
    s = schema_with([{"nodeId": "A", "actionType": "BRANCH",
                      "expression": expr_obj(TOKENS_CONST)}])
    r = verify_schema_expressions(FakeBackend(check_ok=False), s)
    assert not r.ok and any("FORMULA_6058" in p for p in r.problems)


def test_verify_skips_empty_expression():
    s = schema_with([{"nodeId": "A", "actionType": "BRANCH",
                      "expression": {"title": "空", "schema": '{"designData":{"tokens":[]}}'}}])
    be = FakeBackend()
    r = verify_schema_expressions(be, s)
    assert r.ok and r.detail["checked"] == 0 and be.calls == 0


def test_verify_covers_nested_branch_expressions():
    inner = [{"nodeId": "IN", "actionType": "CHANGE_VARIABLE",
              "value": expr_obj(TOKENS_CONST, result="INTEGER")}]
    s = schema_with([branch_node(inner)])
    be = FakeBackend()
    r = verify_schema_expressions(be, s)
    assert r.detail["checked"] == 1 and be.calls >= 1


# ---------------------------------------------------------------- 状态机
def test_state_constructed_when_save_fails():
    assert _state_of([StageResult("save", False)]) == CONSTRUCTED


def test_state_schema_verified_without_l2():
    assert _state_of([StageResult("save", True), StageResult("readback", True),
                      StageResult("expression_verify", True)]) == SCHEMA_VERIFIED


def test_state_ui_verified_with_l2():
    assert _state_of([StageResult("save", True), StageResult("readback", True),
                      StageResult("expression_verify", True),
                      StageResult("l2_check", True)]) == UI_VERIFIED


def test_state_never_skips_to_ui_when_l2_failed():
    assert _state_of([StageResult("save", True), StageResult("readback", True),
                      StageResult("expression_verify", True),
                      StageResult("l2_check", False)]) == SCHEMA_VERIFIED
