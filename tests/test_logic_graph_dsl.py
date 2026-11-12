"""P3 逻辑图 DSL：JSON → AST 翻译 + 顺序裁决（离线）。"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.construction.expression_dsl import DslError, parse_expr  # noqa: E402
from components.construction.logic_graph import (  # noqa: E402
    GraphError, ExecScope, LogicGraphRunner, validate_graph,
)
from components.udc.microflow.expression_model import (  # noqa: E402
    Arithmetic, Compare, Const, Func, Logic, NodeField, SysVar,
)

DTO = "com.seeyon.app.dto.PlanDto"


class FakeResolver:
    """最小引用解析：只为 DSL 服务，不查平台。"""

    def __init__(self, nodes=None, input_fields=None):
        self._nodes = nodes or {}
        self._input = input_fields

    def find_executed(self, alias):
        return self._nodes.get(alias)

    def register_alias(self, alias, node):
        self._nodes[alias] = node

    def bind_scope(self, scope):
        self.scope = scope

    def field_ref_from_node(self, node, field):
        out = node.get("output") or {}
        dto = (node.get("structure") or {}).get("id") or ""
        return NodeField({"outputName": out.get("name"), "field": field,
                          "title": node.get("title") or field, "dto_id": dto,
                          "fields": {field: {"dataType": "STRING", "id": dto + "." + field,
                                             "caption": field}}},
                         dtype="STRING")

    def input_ref(self, field=None, dtype="STRING"):
        if self._input is None:
            raise ValueError("没有入参")
        return NodeField({"outputName": "_FLOW_INPUT_x", "title": "入参",
                          "field": field or "id",
                          "dto_id": "", "fields": {field or "id": {
                              "dataType": dtype, "id": field or "id", "caption": "ID"}}},
                         dtype=dtype)


def scope_of(*aliases):
    s = ExecScope()
    for a in aliases:
        s.mark(a)
    return s


# ---------------------------------------------------------------- 叶子
def test_const_infers_dtype():
    assert isinstance(parse_expr({"const": True}).value, bool)
    assert parse_expr({"const": True}).dtype == "BOOLEAN"
    assert parse_expr({"const": 3}).dtype == "INTEGER"
    assert parse_expr({"const": "x"}).dtype == "STRING"
    assert parse_expr({"const": 1.5}).dtype == "DECIMAL"


def test_const_explicit_dtype_wins():
    assert parse_expr({"const": 1, "dtype": "BIGINTEGER"}).dtype == "BIGINTEGER"


def test_sysvar_requires_name():
    assert isinstance(parse_expr({"sys": "currentTime", "dtype": "DATETIME"}), SysVar)
    with pytest.raises(DslError):
        parse_expr({"sys": ""})


# ---------------------------------------------------------------- 复合
def test_compare_with_aliases():
    r = FakeResolver()
    ast = parse_expr({"op": "==", "left": {"const": 1}, "right": {"const": 2}})
    assert isinstance(ast, Compare) and ast.op == "EQ"      # == 归一成 EQ


def test_operator_alias_normalized():
    for raw, want in (("==", "EQ"), ("!=", "NE"), (">", "GT"), (">=", "GE"),
                      ("<", "LT"), ("<=", "LE"), ("=", "EQ")):
        assert parse_expr({"op": raw, "left": {"const": 1},
                           "right": {"const": 1}}).op == want


def test_unknown_operator_blocked():
    with pytest.raises(DslError):
        parse_expr({"op": "~=", "left": {"const": 1}, "right": {"const": 1}})


def test_logic_single_item_unwraps():
    """★ 单元素 AND/OR 解包为元素本身（AND 一个条件 == 那个条件）。

    编译器/逻辑图天然会产出 {logic:AND, items:[单条]}，为此报错会逼调用方
    写两种形态，容易漏。语义上单元素逻辑组合就等于该元素。
    """
    ast = parse_expr({"logic": "AND", "items": [
        {"op": "GT", "left": {"const": 1}, "right": {"const": 0}},
        {"op": "LT", "left": {"const": 1}, "right": {"const": 9}}]})
    assert isinstance(ast, Logic) and len(ast.items) == 2

    single = parse_expr({"logic": "AND", "items": [{"const": True}]})
    assert not isinstance(single, Logic)
    assert single.__class__.__name__ == "Const"

    # 空 items 仍然报错
    with pytest.raises(DslError):
        parse_expr({"logic": "AND", "items": []})


def test_arith_maps_and_requires_two():
    ast = parse_expr({"arith": "+", "items": [{"const": 1}, {"const": 2}]})
    assert isinstance(ast, Arithmetic) and ast.op == "ADD"
    with pytest.raises(DslError):
        parse_expr({"arith": "SUB", "items": [{"const": 1}]})


def test_function_groups_are_arrays():
    """★ 参数组按函数 paramCount 计：containsText(参数, 被包含文本) → 2 组。
    写成 [[a, b]]（1 组）平台报 FORMULA_6049 parameter number does not match。"""
    ast = parse_expr({"fn": "containsText",
                      "args": [[{"const": "abc"}], [{"const": "b"}]]})
    assert isinstance(ast, Func) and ast.name == "containsText"
    assert len(ast.arg_groups) == 2
    with pytest.raises(DslError):
        parse_expr({"fn": "containsText", "args": [{"const": "abc"}]})
    with pytest.raises(DslError):        # 组数不够也要拦
        parse_expr({"fn": "containsText", "args": [[{"const": "a"}, {"const": "b"}]]})


def test_unknown_shape_blocked():
    with pytest.raises(DslError):
        parse_expr({"whatever": 1})


def test_non_dict_blocked():
    with pytest.raises(DslError):
        parse_expr("1 > 0")


# ---------------------------------------------------------------- 引用 + 顺序
def test_field_ref_requires_executed_alias():
    r = FakeResolver({"ds": {"output": {"name": "_RETRIEVE_ds"},
                             "structure": {"id": DTO}, "title": "查询"}})
    ast = parse_expr({"field": "ds.jdbcUrl"}, resolver=r, scope=scope_of("ds"))
    assert isinstance(ast, NodeField) and ast.ref["outputName"] == "_RETRIEVE_ds"


def test_referencing_not_yet_executed_blocked():
    """★ 平台不拦这种错（context 有名字就过），运行期才空 —— 必须 DSL 期拦。"""
    r = FakeResolver({"later": {"output": {"name": "_L"}}})
    with pytest.raises(DslError) as ei:
        parse_expr({"field": "later.x"}, resolver=r, scope=scope_of("earlier"))
    assert "尚未执行" in str(ei.value)


def test_ref_to_missing_node_blocked():
    r = FakeResolver({})
    with pytest.raises(DslError):
        parse_expr({"field": "ghost.x"}, resolver=r, scope=scope_of("ghost"))


def test_input_ref_uses_resolver():
    r = FakeResolver(input_fields=True)
    ast = parse_expr({"input": "id", "dtype": "BIGINTEGER"}, resolver=r,
                     scope=scope_of())
    assert ast.ref["outputName"] == "_FLOW_INPUT_x"
    assert ast.dtype == "BIGINTEGER"


def test_input_ref_without_flow_input_raises():
    r = FakeResolver(input_fields=None)
    with pytest.raises(Exception):
        parse_expr({"input": "id"}, resolver=r, scope=scope_of())


def test_refs_collected_on_ast():
    r = FakeResolver({"ds": {"output": {"name": "_RETRIEVE_ds"},
                             "structure": {"id": DTO}}})
    ast = parse_expr({"field": "ds.jdbcUrl"}, resolver=r, scope=scope_of("ds"))
    assert ast._refs and ast._refs[0]["outputName"] == "_RETRIEVE_ds"


# ---------------------------------------------------------------- 图结构校验
def _g(nodes, end=None):
    return {"nodes": nodes, "end": end}


def test_validate_ok_minimal():
    assert validate_graph(_g([{"id": "a", "kind": "retrieve", "entity": "E"}])) == []


def test_validate_empty_nodes():
    assert validate_graph({"nodes": []})


def test_validate_unknown_kind():
    p = validate_graph(_g([{"id": "a", "kind": "teleport"}]))
    assert any("不支持" in x for x in p)


def test_validate_duplicate_id():
    p = validate_graph(_g([{"id": "a", "kind": "retrieve", "entity": "E"},
                           {"id": "a", "kind": "retrieve", "entity": "E"}]))
    assert any("重复" in x for x in p)


def test_validate_branch_requires_condition():
    p = validate_graph(_g([{"id": "b", "kind": "branch"}]))
    assert any("condition" in x for x in p)


def test_validate_non_control_rejects_block_keys():
    p = validate_graph(_g([{"id": "a", "kind": "retrieve", "entity": "E",
                            "then": []}]))
    assert any("分支体" in x for x in p)


def test_validate_walks_nested_blocks():
    p = validate_graph(_g([{"id": "b", "kind": "branch", "condition": {"const": True},
                            "then": [{"id": "x", "kind": "nope"}]}]))
    assert any("nope" in x for x in p)


def test_validate_end_from_must_exist():
    p = validate_graph(_g([{"id": "a", "kind": "retrieve", "entity": "E"}],
                          end={"from": "zzz"}))
    assert any("end.from" in x for x in p)


def test_validate_body_not_array():
    p = validate_graph(_g([{"id": "f", "kind": "for_each", "list": "a", "body": {}}]))
    assert any("必须是数组" in x for x in p)


# ---------------------------------------------------------------- 执行器前置
def test_runner_rejects_invalid_graph_before_touching_platform():
    class C:
        nodes: list = []
        by_alias: dict = {}
        refs = None

    with pytest.raises(GraphError):
        LogicGraphRunner(C()).run({"nodes": []})


def test_scope_has_input_always():
    s = ExecScope()
    assert s.has("$input") and not s.has("x")
    s.mark("x")
    assert s.has("x") and s.available() == ["x"]
