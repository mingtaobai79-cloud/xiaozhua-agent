"""P3.1 循环作用域与循环项引用（离线，真假元数据）。

平台实证 2026-11-01：RETRIEVE_ARRAY → FOR_EACH → RETRIEVE(IDS, item.id) → CHANGE_ENTITY
save PASS + readback PASS；循环项引用落库为 position=parent / nodeInfo.type=FOR_EACH /
name=<字段名>（语料 37/37 一致），G20 仍然守住（操作对象来自 RETRIEVE）。
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.construction.expression_dsl import DslError, parse_expr  # noqa: E402
from components.construction.logic_graph import ExecScope  # noqa: E402
from components.construction.loop_scope import (  # noqa: E402
    LoopFrame, LoopScopeStack, ScopeError, is_loop_item_ref, loop_frame_from,
    parse_loop_item_ref,
)
from components.udc.microflow.expression_model import (  # noqa: E402
    Compare, Const, ExpressionCompiler, check_types,
)

DTO = "com.seeyon.app.dto.PlanDto"
FIELDS = {
    "id": {"dataType": "BIGINTEGER", "id": DTO + ".id",
           "javaType": "java.lang.Long", "caption": "ID"},
    "code": {"dataType": "STRING", "id": DTO + ".code",
             "javaType": "java.lang.String", "caption": "编码"},
}


def frame(alias="eachDs", elem="DTO", fields=None):
    return LoopFrame(alias=alias, node_id="ForEach_x", output_name="_FOR_EACH_x",
                     elem_type=elem, elem_dto=DTO if elem == "DTO" else "",
                     elem_fields=FIELDS if fields is None else fields,
                     caption="循环项")


def stack(*frames):
    s = LoopScopeStack()
    for f in frames:
        s.push(f)
    return s


def sc(*aliases):
    s = ExecScope()
    for a in aliases:
        s.mark(a)
    return s


# ---------------------------------------------------------------- 元素类型推导
def test_loop_frame_dto_element():
    f = loop_frame_from({"dataType": "DTO", "type": "ARRAY", "name": "_RETRIEVE_x"},
                        {"id": DTO, "attributes": FIELDS},
                        alias="e", node_id="ForEach_1", output_name="_FOR_EACH_1")
    assert f.is_dto and f.elem_dto == DTO
    assert f.field_meta("id")["dataType"] == "BIGINTEGER"


def test_loop_frame_scalar_element():
    f = loop_frame_from({"dataType": "BIGINTEGER", "type": "ARRAY"},
                        {}, alias="e", node_id="ForEach_1", output_name="_FOR_EACH_1")
    assert not f.is_dto and f.elem_type == "BIGINTEGER"


# ---------------------------------------------------------------- 作用域隔离
def test_outside_loop_blocked():
    with pytest.raises(DslError, match="不在任何循环体内"):
        parse_expr({"item": "eachDs", "field": "id"}, scope=sc("arr"),
                   loops=LoopScopeStack())


def test_loops_none_blocked():
    with pytest.raises(DslError, match="不在任何循环体内"):
        parse_expr({"item": "eachDs", "field": "id"}, scope=sc("arr"))


def test_undeclared_loop_var_blocked():
    with pytest.raises(DslError, match="不在当前作用域"):
        parse_expr({"item": "ghost", "field": "id"}, scope=sc(), loops=stack(frame()))


def test_misspelled_alias_blocked():
    with pytest.raises(DslError, match="不在当前作用域"):
        parse_expr({"item": "eachDss", "field": "id"}, scope=sc(), loops=stack(frame()))


def test_inner_sees_outer():
    ast = parse_expr({"item": "outer", "field": "id"}, scope=sc(),
                     loops=stack(frame("outer"), frame("inner")))
    assert ast.dtype == "BIGINTEGER"


def test_outer_cannot_see_inner():
    s = LoopScopeStack()
    s.push(frame("outer"))
    s.push(frame("inner"))
    s.pop()
    with pytest.raises(ScopeError):
        s.require("inner")


def test_duplicate_alias_blocked():
    s = LoopScopeStack()
    s.push(frame("eachDs"))
    with pytest.raises(ScopeError, match="已存在"):
        s.push(frame("eachDs"))


def test_pop_empty_blocked():
    with pytest.raises(ScopeError):
        LoopScopeStack().pop()


# ---------------------------------------------------------------- 字段解析
def test_missing_field_blocked():
    with pytest.raises(DslError, match="没有字段"):
        parse_expr({"item": "eachDs", "field": "nope"}, scope=sc(), loops=stack(frame()))


def test_scalar_element_field_blocked():
    """★ 元素是 BIGINTEGER 时取 .id 非法（平台无此字段）。"""
    with pytest.raises(DslError, match="不是 DTO"):
        parse_expr({"item": "eachId", "field": "id"}, scope=sc(),
                   loops=stack(frame("eachId", "BIGINTEGER")))


def test_whole_item_type_is_element_type():
    assert parse_expr({"item": "eachDs"}, scope=sc(), loops=stack(frame())).dtype == "DTO"
    assert parse_expr({"item": "eachId"}, scope=sc(),
                      loops=stack(frame("eachId", "BIGINTEGER"))).dtype == "BIGINTEGER"


def test_field_type_mismatch_blocked():
    ast = parse_expr({"op": "GT", "left": {"item": "eachDs", "field": "code"},
                      "right": {"const": 1}}, scope=sc(), loops=stack(frame()))
    assert check_types(ast)


def test_ref_collected_for_context():
    ast = parse_expr({"item": "eachDs", "field": "id"}, scope=sc(), loops=stack(frame()))
    assert ast._refs and ast._refs[0]["outputName"] == "_FOR_EACH_x"
    assert ast._refs[0]["position"] == "parent"


# ---------------------------------------------------------------- DSL 形态
def test_parse_loop_item_ref_forms():
    assert parse_loop_item_ref({"item": "e"}) == ("e", None)
    assert parse_loop_item_ref({"item": "e", "field": "id"}) == ("e", "id")
    assert parse_loop_item_ref({"field": {"source": "e", "path": "id"}}) == ("e", "id")


def test_item_must_be_string():
    with pytest.raises(ScopeError):
        parse_loop_item_ref({"item": 123})


def test_suffix_guess_not_accepted():
    """★ {"field":"eachDs.id"} 不认作循环项 —— 普通节点引用同形，猜会冲突。"""
    assert is_loop_item_ref({"field": "eachDs.id"}) is False
    assert is_loop_item_ref({"item": "eachDs"}) is True
    assert is_loop_item_ref({"field": {"source": "eachDs", "path": "id"}}) is True


def test_unknown_shape_blocked():
    with pytest.raises(ScopeError, match="无法识别"):
        parse_loop_item_ref({"whatever": 1})


# ---------------------------------------------------------------- G20 语义（行为约束）
def test_loop_item_ref_never_becomes_write_target():
    """G20：写操作对象必须来自活动节点出参，不能直引 FOR_EACH。

    直引会让平台生成 int→Dto 的代码，Java 编译失败。
    这里用真实 G20 行为验证：把 CHANGE_ENTITY 的操作对象指向 FOR_EACH 必须被拦。
    """
    from components.udc.microflow.gates import run_gates

    schema = {
        "trigger": {"type": "MANUAL", "paramType": "NONE", "nodeId": "MFStartNode"},
        "input": None,
        "endNode": {"nodeId": "MFEndNode", "type": "END", "actionType": "END_NODE",
                    "input": None, "output": None},
        "nodes": [
            {"nodeId": "ForEach_1", "type": "FOR_EACH", "caption": "循环",
             "output": {"name": "_FOR_EACH_1", "dataType": "DTO", "type": "OBJECT"},
             "nodes": [
                 {"nodeId": "CHANGE_ENTITY_1", "actionType": "CHANGE_ENTITY",
                  "caption": "更新",
                  "selectParam": {"outputName": "_FOR_EACH_1", "name": "_FOR_EACH_1",
                                  "dataType": "DTO", "type": "OBJECT",
                                  "nodeInfo": {"nodeId": "ForEach_1", "type": "FOR_EACH"}},
                  "attrs": [{"attrType": "field", "value": {"type": "Simple", "simple": 1}}],
                  "output": {"name": "_CHANGE_ENTITY_1"}},
             ]},
        ],
    }
    problems = run_gates(schema)
    assert any("G20" in p for p in problems), problems
