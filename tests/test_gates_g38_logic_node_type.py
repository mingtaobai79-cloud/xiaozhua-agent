"""G38：逻辑节点的 type 必须等于 actionType（BREAK / CUSTOM_ERROR）。

★★ 2026-11-02 实测 + 字节码双证 —— 这是最难查的一类错：

  BREAK 写成 `type="ACTIVITY"` 时，
  - 构建 SUCCESS
  - publish 通过
  - 运行 success=true
  - **但循环照跑 3 次**（对照也是 3 次）——节点被静默丢弃，全程零报错

机制（反编译 + 代码生成模板）：
  `MicroFlowParser.node()` → `MicroFlowNodeTypeEnum.valueOf(type.toUpperCase())` 选解析器。
  枚举只有 CONDITION/FOR_EACH/BRANCH/CUSTOM_ERROR/END/ACTIVITY/FOR/BREAK。
  `type="ACTIVITY"` → 解析成普通 Activity；`ActivityNodeTypeEnum` 里没有 BREAK（0 处），
  代码生成模板 `MicroFlowDomainService.java.ftl` 按 `node.type` 分发，
  BREAK 的 case 是 `<#case "Break">` → `break;`，Activity 分支里没有这个 case。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.construction.microflow_nodes_v2 import break_node  # noqa: E402
from components.construction.node_builder import NodeBuilder  # noqa: E402
from components.udc.microflow.gates import run_gates  # noqa: E402

TRIG = {"type": "SCHEDULE", "nodeId": "MFStartNode",
        "scheduleCronRule": {"jobCode": "a", "jobCaption": "b",
                             "cronRules": [{"cycleType": "SIMPLE", "startTime": "1",
                                            "rotationType": "MINUTE", "type": "FIRST",
                                            "value": "1"}]}}


def _node(ty, at, caption="跳出"):
    return {"nodeId": "BREAK_x", "type": ty, "actionType": at, "caption": caption}


def _g38(*nodes):
    return [p for p in run_gates({"nodes": list(nodes), "trigger": TRIG})
            if p.startswith("G38")]


def test_break_with_activity_type_blocked():
    """实测踩过的错法：type=ACTIVITY + actionType=BREAK。"""
    problems = _g38(_node("ACTIVITY", "BREAK"))
    assert problems, "type=ACTIVITY 的 BREAK 必须被拦"
    assert "静默丢弃" in problems[0]


def test_break_with_correct_type_passes():
    assert not _g38(_node("BREAK", "BREAK"))


def test_break_type_without_action_type_blocked():
    """反向：type=BREAK 但缺 actionType。"""
    assert _g38(_node("BREAK", None))


def test_custom_error_same_rule():
    assert _g38(_node("ACTIVITY", "CUSTOM_ERROR"))
    assert not _g38(_node("CUSTOM_ERROR", "CUSTOM_ERROR"))


def test_custom_error_without_action_type_passes():
    """真实样本 CUSTOM_ERROR 无 actionType（node-contract keys 不含），只有 type。"""
    assert not _g38(_node("CUSTOM_ERROR", None))


def test_ordinary_activity_not_affected():
    """普通活动节点（type=ACTIVITY + 各种 actionType）不能被误伤。"""
    for at in ("CREATE_ENTITY", "RETRIEVE", "CHANGE_VARIABLE", "CALL_APP_SERVICE"):
        assert not _g38(_node("ACTIVITY", at)), at


def test_builder_emits_break_type():
    """构造器必须直接产出 type=BREAK（不能指望调用方改）。"""
    b = NodeBuilder(app_id="1", app_name="a")
    n = break_node(b)
    assert n["type"] == "BREAK"
    assert n["actionType"] == "BREAK"
    assert not _g38(n)


def test_template_file_is_fixed():
    """模板骨架也必须是 BREAK（曾经是 ACTIVITY，构造器从它取骨架）。"""
    import json
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "fixtures/microflow/node_templates/BREAK.json")
    assert json.load(open(p, encoding="utf-8"))["type"] == "BREAK"
