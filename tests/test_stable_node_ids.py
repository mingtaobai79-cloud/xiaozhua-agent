"""节点 id 必须可重复：同一张逻辑图重复 compose，nodeId / 出参名完全一致。

背景（2026-11-02）：id 用 `uuid4().hex[:6]` 生成，每次重发都整图换节点，
设计器会报「所选 xxx 已变更」，页面规则等外部引用也会断链。
现在 nodeId 由 (action, 别名, 该别名下第几次) 派生。
"""
from components.construction.node_builder import NodeBuilder

APP, AN = "1", "demo"


def _b():
    return NodeBuilder(app_id=APP, app_name=AN)


def test_same_alias_same_id_across_builders():
    a, b = _b(), _b()
    a.node_key = b.node_key = "查"
    assert a.build("RETRIEVE_ARRAY")["nodeId"] == b.build("RETRIEVE_ARRAY")["nodeId"]


def test_output_name_follows_node_id():
    b = _b()
    b.node_key = "查"
    n = b.build("RETRIEVE_ARRAY")
    assert n["output"]["name"] == "_" + n["nodeId"]


def test_different_alias_different_id():
    b = _b()
    b.node_key = "查1"
    i1 = b.build("RETRIEVE_ARRAY")["nodeId"]
    b.node_key = "查2"
    i2 = b.build("RETRIEVE_ARRAY")["nodeId"]
    assert i1 != i2


def test_same_alias_twice_in_one_graph_still_unique():
    b = _b()
    b.node_key = "x"
    i1 = b.build("RETRIEVE_ARRAY")["nodeId"]
    i2 = b.build("RETRIEVE_ARRAY")["nodeId"]
    assert i1 != i2, "同一别名下第二个节点必须换 id"


def test_without_key_still_random():
    b = _b()
    assert b.build("RETRIEVE_ARRAY")["nodeId"] != b.build("RETRIEVE_ARRAY")["nodeId"]
