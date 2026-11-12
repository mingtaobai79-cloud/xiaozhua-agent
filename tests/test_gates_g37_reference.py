"""G37：引用槽必须指向前序节点的出参。

2026-11-02 实测：把 CHANGE_LIST 节点当列表源传给 CREATE_BATCH_ENTITY，
而 CHANGE_LIST 真实样本 `output` 恒为 null（它原地改列表、不产出新列表），
于是 batch 的 `selectParam.outputName` 为空。

本地全部闸门放行，直到 publish 才被拒：
    check=false errors=[('[4-批量插入]', '….selectParam.outputName', 'PROPERTY_IS_REQUIRED')]

代价是一次完整构建（4 分钟）。G37 把它变成生成期一句话。

语料核查：fixtures 里 10 种节点共 22 个 selectParam，空 outputName 的 0 个 ——
所以「必须非空」不会误伤真实样本。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.udc.microflow.gates import run_gates  # noqa: E402

TRIG = {"type": "SCHEDULE", "nodeId": "MFStartNode",
        "scheduleCronRule": {"jobCode": "a", "jobCaption": "b",
                             "cronRules": [{"cycleType": "SIMPLE", "startTime": "1",
                                            "rotationType": "MINUTE", "type": "FIRST",
                                            "value": "1"}]}}


def _list_node(nid="CREATE_LIST_a"):
    return {"actionType": "CREATE_LIST", "caption": "列表", "nodeId": nid,
            "type": "ACTIVITY", "paramType": "BASIC", "title": "t",
            "dataType": "STRING", "structure": None, "value": [],
            "output": {"dataType": "STRING", "type": "ARRAY", "name": "_" + nid}}


def _batch(out_name, src="", src_action="CREATE_LIST"):
    return {"actionType": "CREATE_BATCH_ENTITY", "caption": "批量插入",
            "nodeId": "CREATE_BATCH_ENTITY_x", "type": "ACTIVITY",
            "selectParam": {"type": "ARRAY", "outputName": out_name,
                            "nodeInfo": {"nodeId": src, "actionType": src_action} if src else {}},
            "output": {"dataType": "INTEGER", "type": "OBJECT",
                       "name": "_CREATE_BATCH_ENTITY_x"},
            "title": "列表"}


def _g37(*nodes):
    return [p for p in run_gates({"nodes": list(nodes), "trigger": TRIG}) if p.startswith("G37")]


def test_empty_output_name_blocked():
    problems = _g37(_list_node(), _batch(""))
    assert problems, "空 outputName 必须被 G37 拦"
    assert "PROPERTY_IS_REQUIRED" in problems[0]


def test_空白_output_name_blocked():
    """只有空格也算空（平台同样拒）。"""
    assert _g37(_list_node(), _batch("   "))


def test_dangling_reference_blocked():
    problems = _g37(_list_node(), _batch("_X", "NOT_EXIST"))
    assert problems and "悬空" in problems[0]


def test_valid_reference_passes():
    assert not _g37(_list_node(), _batch("_CREATE_LIST_a", "CREATE_LIST_a"))


def test_change_list_as_source_is_caught():
    """真实踩坑场景：引用了没有出参的 CHANGE_LIST 节点。"""
    cl = {"actionType": "CHANGE_LIST", "caption": "加入列表",
          "nodeId": "CHANGE_LIST_b", "type": "ACTIVITY", "action": "ADD",
          "selectParam": {"outputName": "_CREATE_LIST_a", "type": "ARRAY",
                          "nodeInfo": {"nodeId": "CREATE_LIST_a"}},
          "output": None}
    problems = _g37(_list_node(), cl, _batch("", "CHANGE_LIST_b"))
    assert problems and "CHANGE_LIST" in problems[0], "应指出引用了没有出参的节点"


def test_trigger_reference_allowed():
    """引用触发器的入参出参是合法的，不能误拦。"""
    assert not _g37(_list_node(), _batch("_MFStartNode", "MFStartNode"))
