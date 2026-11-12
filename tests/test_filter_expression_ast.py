"""FILTER 的任意布尔表达式（expr DSL）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.construction.microflow_filter import parse_filter_spec

DTO = "com.demo.dto.CheckpointDto"
EM = {"attributes": {"processedRows": {"dataType": "BIGINTEGER", "label": "处理行数"},
                     "taskId": {"dataType": "STRING", "label": "任务"},
                     "createTime": {"dataType": "DATETIME", "label": "创建时间"}}}


def _p(spec):
    return parse_filter_spec(spec, dto_full=DTO, list_desc="列表", entity_model=EM)


def test_field_ref_path_is_dto_twice():
    """token 路径必须是 <DTO去点>.<DTO去点>.<字段>，所以 outputName 取 DTO 去点。"""
    nf = _p({"field": "taskId"})
    assert nf.ref["outputName"] == DTO.replace(".", "")
    assert nf.ref["field"] == "taskId"
    assert nf.dtype == "STRING"


def test_arith_in_comparison():
    ast = _p({"op": "GT",
              "left": {"arith": "ADD", "items": [{"field": "processedRows"}, {"const": 3}]},
              "right": {"const": 5}})
    assert ast.op == "GT"
    assert ast.left.op == "ADD"


def test_logic_nests():
    ast = _p({"logic": "AND", "items": [
        {"op": "GT", "left": {"field": "processedRows"}, "right": {"const": 2}},
        {"op": "LT", "left": {"field": "processedRows"}, "right": {"const": 9}}]})
    assert ast.op == "AND" and len(ast.items) == 2


def test_cond_inherits_then_dtype():
    """Cond 没有 dtype 字段，必须从 then 分支继承，否则与数字比较报类型不一致。"""
    ast = _p({"op": "EQ",
              "left": {"cond": {"op": "GT", "left": {"field": "processedRows"},
                                "right": {"const": 5}},
                       "then": {"const": 1}, "else": {"const": 0}},
              "right": {"const": 1}})
    assert ast.left.dtype == "INTEGER"


def test_unknown_field_rejected():
    try:
        _p({"field": "noSuchField"})
    except ValueError as e:
        assert "noSuchField" in str(e)
        return
    raise AssertionError("未知字段必须拒绝")


def test_unknown_operator_rejected():
    try:
        _p({"op": "LIKE", "left": {"field": "taskId"}, "right": {"const": "x"}})
    except ValueError:
        return
    raise AssertionError("未知比较符必须拒绝")
