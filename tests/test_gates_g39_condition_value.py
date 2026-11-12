"""G39：条件右值必须是平台认识的槽。

2026-11-02 实测（P5-S2）：把 DSL 的 {"const": "X"} 原样塞进 rightParams 后，
平台解析出 value=""、desc=""，条件**静默失效** —— RETRIEVE_ARRAY 返回整张表，
构建 SUCCESS、运行 success=true，只有读侧数据不对（SIZE 三个查询全返回同一个数）。
"""
from components.udc.microflow.gates import run_gates


def _schema(cond):
    return {
        "nodes": [{
            "nodeId": "RETRIEVE_ARRAY_1", "type": "ACTIVITY",
            "actionType": "RETRIEVE_ARRAY", "caption": "查多条",
            "fetchType": "CONDITION",
            "condition": [{"type": "GROUP", "conditions": [cond]}],
            "output": {"name": "_RETRIEVE_ARRAY_1", "type": "ARRAY",
                       "dataType": "DTO", "id": "x.Dto", "javaType": "x.Dto"},
        }],
        "endNode": {"nodeId": "MFEndNode", "type": "END",
                    "actionType": "END_NODE", "caption": "结束"},
    }


LEFT = {"id": "x.Dto.taskId", "type": "OBJECT", "javaType": "java.lang.String",
        "dto": "_taskId", "field": "taskId", "desc": "任务ID",
        "dataType": "STRING", "multiSelect": False}
OP = {"value": "EQ", "desc": "="}


def _cond(rp):
    return {"type": "CONDITION", "leftParam": LEFT, "operator": OP,
            "rightParams": [rp], "logicalOperator": "AND"}


def test_g39_rejects_raw_const_dict():
    p = run_gates(_schema(_cond({"const": "P5RA1-M"})))
    assert any(x.startswith("G39") for x in p), p


def test_g39_rejects_constant_without_value():
    p = run_gates(_schema(_cond({"type": "CONSTANT", "desc": "x"})))
    assert any(x.startswith("G39") for x in p), p


def test_g39_accepts_platform_constant():
    p = run_gates(_schema(_cond({"type": "CONSTANT", "value": "P5RA1-M",
                                 "desc": "P5RA1-M"})))
    assert not any(x.startswith("G39") for x in p), p
