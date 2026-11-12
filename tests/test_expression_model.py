"""P2 表达式中间模型：AST → tokens 结构 + 静态类型检查 + 语义保真（离线，不碰平台）。

平台实证另见 skill/事实：/expression/check + /transform 6 场景全过（2026-11-01）。
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.udc.microflow.expression_model import (  # noqa: E402
    Arithmetic, Compare, Cond, Const, ExpressionCompiler, ExpressionError,
    Func, Logic, NodeField, SysVar, check_types,
)

APP = "datamigration9000000000000000001"
DTO = "com.seeyon.%s.dto.PlanDto" % APP
REF = {"outputName": "_RETRIEVE_t1", "title": "查询结果", "dto_id": DTO,
       "fields": {"expNum": {"dataType": "INTEGER", "id": DTO + ".expNum", "caption": "实验数量"},
                  "expText": {"dataType": "STRING", "id": DTO + ".expText", "caption": "文本"}}}


def nf(f, dt="INTEGER"):
    return NodeField(dict(REF, field=f), dtype=dt)


def toks(ast, result_type="BOOLEAN"):
    c = ExpressionCompiler(result_type=result_type)
    return c, c.compile(ast)


# ---------------------------------------------------------------- tokens 形态
def test_variable_token_is_three_level():
    """VARIABLE 必须三级 <出参>.<出参>.<字段>；两级报 FORMULA_6058。"""
    _, t = toks(Compare("GT", nf("expNum"), Const(0, "INTEGER")))
    var = [x for x in t if x["type"] == "VARIABLE"][0]
    assert var["value"] == "_RETRIEVE_t1._RETRIEVE_t1.expNum"
    assert var["value"].count(".") == 2


def test_constant_token_str():
    _, t = toks(Compare("GT", Const(1, "INTEGER"), Const(0, "INTEGER")))
    assert [x["value"] for x in t if x["type"] == "CONSTANT"] == ["1", "0"]


def test_compare_operator_mapping():
    """★ 相等是 `==` 不是 `=`（语料 1040 条：'==' 325 次，'=' 从不作 value）。
    写成 '=' 平台 checkSchema 回 BOOT_3000（无 message）。"""
    for op, sym in (("EQ", "=="), ("NE", "!="), ("GT", ">"), ("GE", ">="),
                    ("LT", "<"), ("LE", "<=")):
        _, t = toks(Compare(op, Const(1, "INTEGER"), Const(2, "INTEGER")))
        assert [x["value"] for x in t if x["type"] == "OPERATOR"] == [sym]


def test_logic_or_maps_to_double_pipe():
    """★ 逻辑运算符是单字符 `|` / `&`，不是 `||` / `&&`
    （语料 OPERATOR 只有 '&' '|'，写成双字符平台回 BOOT_3000）。"""
    _, t = toks(Logic("OR", Const(True, "BOOLEAN"), Const(False, "BOOLEAN")))
    assert [x["value"] for x in t if x["type"] == "OPERATOR"] == ["|"]


def test_function_uses_subops_not_flat_tokens():
    """★ 函数参数必须在 subOps 二维数组里；平铺成顶层流平台回 BOOT_3000。"""
    _, t = toks(Compare("GT", Func("len", [[nf("expText", "STRING")]], dtype="INTEGER"),
                        Const(0, "INTEGER")))
    fn = [x for x in t if x["type"] == "FUNCTION"]
    assert len(fn) == 1
    assert fn[0]["value"] == "len"
    assert isinstance(fn[0]["subOps"], list) and fn[0]["subOps"]
    inner = fn[0]["subOps"][0]
    assert isinstance(inner, list) and inner[0]["type"] == "VARIABLE"
    # 函数参数不能出现在顶层流
    assert not [x for x in t if x["type"] == "VARIABLE"]


def test_unknown_function_rejected():
    with pytest.raises(ExpressionError):
        ExpressionCompiler().compile(Compare("GT", Func("stringLength", [[Const("a")]],
                                                        dtype="INTEGER"),
                                             Const(0, "INTEGER")))


# ---------------------------------------------------------------- 语义保真
def test_nested_logic_gets_parentheses():
    """AND 内嵌 OR 必须括号，否则被翻译成 (A&&B)||C —— 静默语义漂移。"""
    _, t = toks(Logic("AND",
                      Compare("GT", nf("expNum"), Const(0, "INTEGER")),
                      Logic("OR", Compare("EQ", nf("expNum"), Const(1, "INTEGER")),
                            Compare("EQ", nf("expNum"), Const(2, "INTEGER")))))
    ops = [x["value"] for x in t if x["type"] == "OPERATOR"]
    assert "(" in ops and ")" in ops
    assert ops.index("(") < ops.index("|") < ops.index(")")


def test_same_op_nesting_not_over_parenthesized():
    _, t = toks(Logic("AND",
                      Compare("GT", nf("expNum"), Const(0, "INTEGER")),
                      Compare("LT", nf("expNum"), Const(9, "INTEGER"))))
    ops = [x["value"] for x in t if x["type"] == "OPERATOR"]
    assert "(" not in ops and ops.count("&") == 1


def test_arithmetic_div_nesting_grouped():
    """a - (b - c) 左结合陷阱：不同 op 嵌套必须括号。"""
    _, t = toks(Compare("GT",
                        Arithmetic("SUB", nf("expNum"), Arithmetic("SUB", nf("expNum"), Const(1, "INTEGER"))),
                        Const(0, "INTEGER")))
    ops = [x["value"] for x in t if x["type"] == "OPERATOR"]
    assert ops.count("(") == 1 and ops.count(")") == 1


# ---------------------------------------------------------------- 静态类型
def test_logic_requires_boolean_children():
    probs = check_types(Logic("AND", Const("x", "STRING"), Const("y", "STRING")))
    assert probs and "BOOLEAN" in probs[0]


def test_compare_type_mismatch_rejected():
    with pytest.raises(ExpressionError):
        ExpressionCompiler().compile(Compare("GT", Const("a", "STRING"), Const(1, "INTEGER")))


def test_compare_numeric_family_ok():
    assert not check_types(Compare("GT", Const(1, "INTEGER"), Const(1, "BIGINTEGER")))


def test_arithmetic_requires_numeric():
    probs = check_types(Arithmetic("ADD", Const("a", "STRING"), Const(1, "INTEGER")))
    assert probs


def test_cond_branches_type_consistent():
    ok = Cond(Compare("GT", Const(1, "INTEGER"), Const(0, "INTEGER")),
              Const(1, "INTEGER"), Const(2, "INTEGER"))
    assert not check_types(ok)
    bad = Cond(Compare("GT", Const(1, "INTEGER"), Const(0, "INTEGER")),
               Const(1, "INTEGER"), Const("x", "STRING"))
    assert check_types(bad)


def test_sysvar_token_uses_full_name():
    _, t = toks(Compare("GT", SysVar("currentTime", dtype="DATETIME"), Const(0, "DATETIME")))
    assert [x["value"] for x in t if x["type"] == "VARIABLE"] == ["currentTime"]


# ---------------------------------------------------------------- context
def test_context_reuses_node_context_entry_shape():
    """context 必须复用 expression_build.node_context_entry 三层形态：
    顶层 OBJECT / 出参 OBJECT|ARRAY / 字段 type=dataType（不是 DTO）。"""
    c, _ = toks(Compare("GT", nf("expNum"), Const(0, "INTEGER")))
    top = c.context[0]
    assert top["type"] == "OBJECT" and top["selectable"] is False
    out = top["properties"][0]
    assert out["type"] == "OBJECT"
    fields = {f["name"]: f for f in out["properties"]}
    assert fields["expNum"]["type"] == "INTEGER"      # ★ 不是 DTO
    assert fields["expNum"]["uniformityParams"]["paramCategory"] == "INTEGER"


def test_context_registered_once_per_output_name():
    c = ExpressionCompiler(result_type="BOOLEAN")
    ast = Logic("AND", Compare("GT", nf("expNum"), Const(0, "INTEGER")),
                Compare("LT", nf("expNum"), Const(9, "INTEGER")))
    c.compile(ast)
    assert len(c.context) == 1


def test_to_save_dto_strips_to_schema_whitelist():
    dto = ExpressionCompiler(result_type="BOOLEAN").to_save_dto(
        Compare("GT", nf("expNum"), Const(0, "INTEGER")))
    assert dto["resultTypeInfo"] == "BOOLEAN"
    assert dto["terminalSupportType"] == "BACKEND"
    assert dto["isMultiSelect"] is False
    assert dto["schemas"][0]["skip"] is True
    assert all(t.get("type") for t in dto["tokens"])


def test_basic_scalar_variable_uses_two_level_context():
    """BASIC 标量出参（SUM/SIZE/MIN/MAX）→ 两级 context，不是三级 DTO 树。

    回归：曾把标量出参 context 硬编码成 dataType=DTO 三级树，branch condition
    引用 SUM 出参时报 FORMULA_6161「operator not Math」。
    """
    ref = {"outputName": "_LIST_OPERATION_x", "title": "失败总数",
           "field": "_LIST_OPERATION_x", "dto_id": "",
           "node_dtype": "BIGINTEGER", "fields": {}}
    c = ExpressionCompiler(result_type="BOOLEAN")
    c.register_node_output(ref)
    top = c.context[0]
    assert top["type"] == "OBJECT" and top["selectable"] is False
    out = top["properties"][0]
    assert out["type"] == "BIGINTEGER"          # 标量类型，不是 OBJECT/DTO
    assert "properties" not in out               # 无字段层（两级，不是三级）
    assert out["uniformityParams"]["paramId"] == "java.lang.Long"
