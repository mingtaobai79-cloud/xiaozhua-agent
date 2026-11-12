"""FILTER 过滤条件表达式的构造契约（离线编译，不依赖设计器）。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.construction import microflow_filter as MF


class FakeBackend:
    """记录调用；返回与平台同形的成功响应。"""

    def __init__(self):
        self.calls = []

    def check(self, dto):
        self.calls.append(("check", dto))
        return {"ok": True, "code": "BOOT_0000", "message": "SUCCESS"}

    def transform(self, dto):
        self.calls.append(("transform", dto))
        return {"ok": True, "code": "BOOT_0000",
                "content": {"designData": {"expressionTranslation": "x"},
                            "runtimeData": {"executableExpr": "EXEC"}}}


EM = {"fullName": "com.seeyon.app.dto.DemoDto",
      "attributes": {"processedRows": {"name": "processedRows", "label": "已处理行数",
                                       "dataType": "INTEGER"},
                     "taskId": {"name": "taskId", "label": "任务ID", "dataType": "STRING"}}}


def test_operator_tokens_are_flat():
    """OPERATOR 必须是平铺的 [VARIABLE, OPERATOR, CONSTANT]，不能带 subOps。

    按带 subOps 构造，平台会报 FORMULA_6070 Operator: =, input error!。
    """
    toks = MF.build_tokens("com.seeyon.app.dto.DemoDto", "列表", "processedRows",
                           "已处理行数", "GT", 2)
    assert [t["type"] for t in toks] == ["VARIABLE", "OPERATOR", "CONSTANT"]
    assert all("subOps" not in t for t in toks)
    assert toks[1]["value"] == ">"
    assert toks[2]["value"] == "2"


def test_function_tokens_use_subops():
    toks = MF.build_tokens("com.seeyon.app.dto.DemoDto", "列表", "taskId",
                           "任务ID", "CONTAINS", "abc")
    assert len(toks) == 1
    assert toks[0]["type"] == "FUNCTION"
    assert toks[0]["subOps"][0][0]["type"] == "VARIABLE"


def test_variable_value_repeats_dto_nodots():
    toks = MF.build_tokens("com.seeyon.app.dto.DemoDto", "列表", "processedRows",
                           "已处理行数", "EQ", 1)
    var = toks[0]
    assert var["value"] == ("comseeyonappdtoDemoDto."
                            "comseeyonappdtoDemoDto.processedRows")
    assert var["desc"] == "微流程.过滤条件.列表.已处理行数"


def test_context_has_two_levels_and_dotted_param_id():
    ctx = MF.build_context("com.seeyon.app.dto.DemoDto", "列表", EM)
    root = ctx[0]
    assert root["description"] == "过滤条件"
    assert root["selectable"] is False
    assert root["uniformityParams"]["paramId"] == "com.seeyon.app.dto.DemoDto"
    inner = root["properties"][0]
    assert inner["description"] == "列表"
    assert inner["selectable"] is True
    names = [p["name"] for p in inner["properties"]]
    assert "processedRows" in names


def test_build_filter_expression_calls_platform_and_returns_schema():
    be = FakeBackend()
    e = MF.build_filter_expression(dto_full="com.seeyon.app.dto.DemoDto", list_desc="列表",
                                   entity_model=EM, field="processedRows", op="GT",
                                   const=2, backend=be)
    assert [c[0] for c in be.calls] == ["check", "transform"]
    assert e["title"].startswith(">")
    sd = json.loads(e["schema"])
    assert sd["runtimeData"]["executableExpr"] == "EXEC"
    assert sd["designData"]["expressionTranslation"] == "x"


def test_unknown_field_rejected():
    try:
        MF.build_filter_expression(dto_full="com.seeyon.app.dto.DemoDto", list_desc="列表",
                                   entity_model=EM, field="nope", op="EQ", const=1,
                                   backend=FakeBackend())
    except KeyError:
        return
    raise AssertionError("不存在的字段必须拒绝")
