"""G40：CHANGE_LIST 四种动作形态必须与真实枚举一致（317 条样本）。

  ADD     266  selectParam + dataSource
  REPLACE  28  selectParam + dataSource
  CLEAR    15  只有 selectParam（**没有 dataSource**）
  REMOVE    8  selectParam + dataSource + countAttrs

早期构造器无条件写 dataSource 且默认 action=ADD，CLEAR 会带上非法 dataSource。
"""
from components.udc.microflow.gates import run_gates


def _schema(node):
    return {"nodes": [node], "endNode": {"nodeId": "MFEndNode", "type": "END",
                                         "actionType": "END_NODE", "caption": "结束"}}


def _node(action, **extra):
    n = {"nodeId": "CHANGE_LIST_1", "type": "ACTIVITY", "actionType": "CHANGE_LIST",
         "caption": "改列表", "action": action,
         "selectParam": {"name": "_LIST_1", "outputName": "_LIST_1", "type": "ARRAY",
                         "dataType": "DTO", "dtoType": "MASTER_ENTITY"}}
    n.update(extra)
    return n


DS = {"outputName": "_X", "id": "a.B", "dataType": "DTO", "type": "OBJECT"}
CA = [{"id": "a.B.id", "name": "id", "dataType": "BIGINTEGER"}]


def test_clear_without_datasource_ok():
    assert not [p for p in run_gates(_schema(_node("CLEAR"))) if p.startswith("G40")]


def test_clear_with_datasource_rejected():
    p = run_gates(_schema(_node("CLEAR", dataSource=DS)))
    assert any(x.startswith("G40") for x in p), p


def test_add_requires_datasource():
    p = run_gates(_schema(_node("ADD")))
    assert any(x.startswith("G40") for x in p), p


def test_add_with_datasource_ok():
    assert not [p for p in run_gates(_schema(_node("ADD", dataSource=DS))) if p.startswith("G40")]


def test_remove_requires_count_attrs():
    p = run_gates(_schema(_node("REMOVE", dataSource=DS)))
    assert any(x.startswith("G40") for x in p), p


def test_remove_with_count_attrs_ok():
    assert not [p for p in run_gates(_schema(_node("REMOVE", dataSource=DS, countAttrs=CA)))
                if p.startswith("G40")]


def test_delete_is_not_a_real_action():
    p = run_gates(_schema(_node("DELETE", dataSource=DS)))
    assert any(x.startswith("G40") for x in p), p
