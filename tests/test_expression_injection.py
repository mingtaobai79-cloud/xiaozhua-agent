"""P2-5 错误注入回归（固化为 pytest）。

正向 6 场景已在平台验证（见 facts/udc/microflow/expression-engine.md §六）；
这里锁住「错的东西必须拦住」，防止后续改动把闸门削弱。
"""
from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.udc.microflow.expression_model import (  # noqa: E402
    Arithmetic, Compare, Cond, Const, ExpressionCompiler, ExpressionError,
    Func, Logic, NodeField, check_types, to_value_slot,
)
from components.udc.microflow.expression_refs import (  # noqa: E402
    ReferenceError_, ReferenceResolver,
)
from components.udc.microflow.save_pipeline import (  # noqa: E402
    readback_compare, verify_schema_expressions,
)

APP = "app1"
DTO = "com.seeyon.%s.dto.PlanDto" % APP
REF = {"outputName": "_RETRIEVE_a", "title": "查询结果", "field": "n",
       "dto_id": DTO, "fields": {"n": {"dataType": "INTEGER", "id": DTO + ".n",
                                       "caption": "数量"}}}


def nf():
    return NodeField(dict(REF), dtype="INTEGER")


# ---------------------------------------------------------------- 类型层
def test_logic_non_boolean_child_blocked():
    assert check_types(Logic("AND", Const("a", "STRING"), Const(True, "BOOLEAN")))


def test_compare_cross_family_blocked():
    with pytest.raises(ExpressionError):
        ExpressionCompiler().compile(Compare("GT", Const("a", "STRING"), Const(1, "INTEGER")))


def test_arithmetic_non_numeric_blocked():
    assert check_types(Arithmetic("ADD", Const("a", "STRING"), Const(1, "INTEGER")))


def test_unknown_function_blocked():
    with pytest.raises(ExpressionError):
        ExpressionCompiler().compile(
            Compare("GT", Func("noSuchFn", [[Const(1)]], dtype="INTEGER"), Const(0, "INTEGER")))


def test_cond_branch_type_mismatch_blocked():
    ast = Cond(Compare("GT", Const(1, "INTEGER"), Const(0, "INTEGER")),
               Const(1, "INTEGER"), Const("x", "STRING"))
    assert check_types(ast)


# ---------------------------------------------------------------- tokens 形态层
def test_variable_is_three_level():
    c = ExpressionCompiler(result_type="BOOLEAN")
    t = c.compile(Compare("GT", nf(), Const(0, "INTEGER")))
    var = [x for x in t if x["type"] == "VARIABLE"][0]
    assert var["value"].count(".") == 2, "两级 VARIABLE 报 FORMULA_6058"


def test_function_args_not_flat():
    c = ExpressionCompiler(result_type="BOOLEAN")
    t = c.compile(Compare("GT", Func("len", [[NodeField(
        {"outputName": "_x", "title": "t", "dto_id": DTO,
         "fields": {"s": {"dataType": "STRING", "id": DTO + ".s", "caption": "s"}}},
        dtype="STRING")]], dtype="INTEGER"), Const(0, "INTEGER")))
    fn = [x for x in t if x["type"] == "FUNCTION"][0]
    assert fn.get("subOps"), "函数参数必须在 subOps"
    assert not [x for x in t if x["type"] == "VARIABLE"], "参数不能平铺进顶层"


def test_nested_logic_parenthesized():
    c = ExpressionCompiler(result_type="BOOLEAN")
    t = c.compile(Logic("AND", Compare("GT", nf(), Const(0, "INTEGER")),
                        Logic("OR", Compare("EQ", nf(), Const(1, "INTEGER")),
                              Compare("EQ", nf(), Const(2, "INTEGER")))))
    assert "(" in [x["value"] for x in t if x["type"] == "OPERATOR"]


def test_subtraction_nesting_parenthesized():
    c = ExpressionCompiler(result_type="INTEGER")
    t = c.compile(Arithmetic("SUB", nf(), Arithmetic("SUB", nf(), Const(1, "INTEGER"))))
    assert "(" in [x["value"] for x in t if x["type"] == "OPERATOR"]


# ---------------------------------------------------------------- 值槽
def test_value_slot_requires_type_key():
    slot = to_value_slot({"title": "t", "schema": "{}"})
    assert slot["type"] == "Expression"
    assert slot["expression"]["schema"] == "{}"
    assert "simple" in slot


def test_value_slot_idempotent():
    once = to_value_slot({"title": "t", "schema": "{}"})
    assert to_value_slot(once) == once


def test_value_slot_rejects_non_expression():
    with pytest.raises(ExpressionError):
        to_value_slot({"title": "t"})


# ---------------------------------------------------------------- 引用层
def test_referencing_later_node_blocked():
    nodes = [{"nodeId": "B", "actionType": "CHANGE_VARIABLE"},
             {"nodeId": "A", "actionType": "RETRIEVE", "output": {"name": "_A"}}]
    with pytest.raises(ReferenceError_):
        ReferenceResolver(APP, APP).ref_from_output_name(nodes, "_A", "n", "B")


def test_referencing_missing_output_blocked():
    nodes = [{"nodeId": "A", "actionType": "RETRIEVE", "output": {"name": "_A"}}]
    with pytest.raises(ReferenceError_):
        ReferenceResolver(APP, APP).ref_from_output_name(nodes, "_ZZZ", "n", "A")


def test_cache_is_app_scoped():
    class F:
        def __init__(self):
            self.calls = 0

        def entity_model(self, a, b, label="", dto_full=""):
            self.calls += 1
            return {"attributes": {"n": {"dataType": "INTEGER", "id": "x.n"}}}

    f = F()
    n = {"nodeId": "A", "output": {"name": "_A"},
         "structure": {"id": "com.seeyon.x", "caption": "E"}}
    ReferenceResolver("appA", "appA", live_refs=f).field_ref_from_node(n, "n")
    ReferenceResolver("appB", "appB", live_refs=f).field_ref_from_node(n, "n")
    assert f.calls == 2, "缓存串应用会生成指向错误 DTO 的表达式"


# ---------------------------------------------------------------- 保存链层
def test_readback_shape_drift_blocked():
    a = {"nodes": [{"nodeId": "A", "actionType": "RETRIEVE", "output": {"name": "_A"}}]}
    b = {"nodes": [{"nodeId": "A", "actionType": "RETRIEVE", "output": {"name": "_B"}}]}
    assert not readback_compare(a, b).ok


class _BadCheck:
    def check(self, dto):
        return {"ok": False, "code": "FORMULA_6058", "message": "变量不存在", "content": None}

    def transform(self, dto):
        return {"ok": False, "code": "BOOT_3000"}


class _Drift:
    def check(self, dto):
        return {"ok": True, "code": "BOOT_0000", "content": True}

    def transform(self, dto):
        return {"ok": True, "code": "BOOT_0000", "executableExpr": "NEW"}


def _expr_schema(exec_expr="OLD", variable=False):
    """variable=True 造含 VARIABLE 的表达式（这类不走远端 /check，facts §十三）。"""
    toks = ([{"type": "VARIABLE", "value": "_A._A.n", "desc": "n"}]
            if variable else
            [{"type": "CONSTANT", "value": "1", "desc": "1"}])
    return {"title": "t", "schema": json.dumps({
        "designData": {"tokens": toks},
        "runtimeData": {"executableExpr": exec_expr}})}


def test_expression_check_failure_reported():
    s = {"nodes": [{"nodeId": "A", "actionType": "BRANCH", "expression": _expr_schema()}]}
    r = verify_schema_expressions(_BadCheck(), s)
    assert not r.ok and any("FORMULA_6058" in p for p in r.problems)


def test_executable_expr_drift_reported():
    s = {"nodes": [{"nodeId": "A", "actionType": "BRANCH", "expression": _expr_schema()}]}
    r = verify_schema_expressions(_Drift(), s)
    assert not r.ok and any("不一致" in p for p in r.problems)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
