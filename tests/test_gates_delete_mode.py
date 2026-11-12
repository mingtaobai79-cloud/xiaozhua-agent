"""G36：DELETE_ENTITY 模式与字段自洽。

背景（2026-11-02 实测）：DELETE_ENTITY 用 CONDITION 模式、条件右值填节点引用
（SelectParam）时，publish 被拒 `BOOT_1001 Parameter Error`，响应体 data=null，
没有任何字段级提示 —— 只能靠二分定位到「加了 DELETE 节点就挂」。

二分过程：1/2/3/4 节点全部 publish OK，加 DELETE 立刻 BOOT_1001；
把右值换成 CONSTANT 常量 → 立刻 OK。所以动态记录删除必须走 SELECT_PARAM。

这条闸门的价值：把「要 4 分钟构建 + 无提示的运行时拒绝」变成「生成期一句话」。
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.udc.microflow.gates import run_gates  # noqa: E402


def _flow(*nodes):
    return {"nodes": list(nodes), "trigger": {"type": "SCHEDULE"}}


def _del_node(**over):
    n = {
        "actionType": "DELETE_ENTITY", "caption": "删除", "nodeId": "DELETE_ENTITY_x1",
        "deleteType": "CONDITION",
        "condition": [{"type": "GROUP", "conditions": [
            {"type": "CONDITION",
             "leftParam": {"field": "id", "dataType": "BIGINTEGER"},
             "operator": {"value": "EQ"},
             "rightParams": [{"type": "CONSTANT", "value": 1}]}]}],
    }
    n.update(over)
    return n


def _g36(schema):
    return [p for p in run_gates(schema) if p.startswith("G36")]


def test_condition_with_node_ref_is_blocked():
    """CONDITION 模式右值引用节点 → 拦（真实后果是 BOOT_1001）。"""
    n = _del_node()
    n["condition"][0]["conditions"][0]["rightParams"] = [
        {"type": "SelectParam", "selectParam": {"name": "_CREATE_ENTITY_a"}}]
    problems = _g36(_flow(n))
    assert problems, "条件右值引用节点必须被 G36 拦"
    assert "BOOT_1001" in problems[0]


def test_condition_with_constant_passes():
    """CONDITION 模式右值常量 → 放行（实测 publish OK）。"""
    assert not _g36(_flow(_del_node()))


def test_select_param_without_select_param_field_is_blocked():
    """SELECT_PARAM 模式缺 selectParam → 拦（不知道删哪条）。"""
    n = _del_node(deleteType="SELECT_PARAM")
    n.pop("condition")
    problems = _g36(_flow(n))
    assert problems and "缺 selectParam" in problems[0]


def test_select_param_with_condition_mode_keys_is_blocked():
    """SELECT_PARAM 模式混带 CONDITION 的字段 → 拦（平台会拒）。"""
    n = _del_node(deleteType="SELECT_PARAM",
                  selectParam={"outputName": "_RETRIEVE_a"},
                  app={"id": "1"}, structure={"id": "x"})
    problems = _g36(_flow(n))
    assert problems, "混带 CONDITION 字段必须被拦"
    assert any("不应带" in p for p in problems)


def test_select_param_clean_passes():
    """SELECT_PARAM 模式只带 deleteType/title/selectParam → 放行（实测 publish OK）。"""
    n = _del_node(deleteType="SELECT_PARAM",
                  selectParam={"outputName": "_RETRIEVE_a"})
    n.pop("condition")
    assert not _g36(_flow(n))


def test_other_nodes_unaffected():
    """非 DELETE_ENTITY 节点不受 G36 影响（防止误拦）。"""
    assert not _g36(_flow({
        "actionType": "CHANGE_ENTITY", "caption": "改", "nodeId": "CHANGE_ENTITY_x",
        "selectParam": {"outputName": "_RETRIEVE_a"},
        "attrs": [{"attrType": {"name": "f"}, "value": {"type": "Simple"}}],
    }))
