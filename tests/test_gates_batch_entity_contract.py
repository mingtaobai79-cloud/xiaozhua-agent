"""批量写节点契约：形态必须与真实样本一致。

2026-11-02 实测：全仓 95 个 CREATE_BATCH_ENTITY / CHANGE_BATCH_ENTITY 样本，
**带 attrs 的是 0 个**；真实业务流（r44_e1_orig）的出参是
`dataType=INTEGER / type=OBJECT / desc="批量更新…成功的数量_1"`。

历史错误有两处，都在这条测试的射程内：
  1. node_contracts 里 CHANGE_BATCH_ENTITY 的 required 写了 "attrs"
     → 生成时被自己的闸门拦死（C-CHANGE_BATCH_ENTITY 缺 attrs），
       而平台样本根本没有这个键。
  2. microflow_nodes_batch.py 自己实现了一套 attrs + DTO 数组出参
     → 与 microflow_nodes_extra 的正确实现并存，导入哪个模块决定生成对不对。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.udc.microflow.node_contracts import NODE_CONTRACTS  # noqa: E402


def _contract(action):
    c = NODE_CONTRACTS.get(action)
    assert c, "契约缺 %s" % action
    return c


def test_batch_nodes_do_not_require_attrs():
    """批量节点不做字段映射，required 里不能出现 attrs。"""
    for action in ("CREATE_BATCH_ENTITY", "CHANGE_BATCH_ENTITY"):
        required = " ".join(_contract(action).get("required") or [])
        assert "attrs" not in required, (
            "%s 的 required 不能含 attrs（95 个真实样本 0 个带 attrs）" % action)


def test_batch_nodes_require_list_and_output_name():
    """两个必填项：列表引用 + 出参名。"""
    for action in ("CREATE_BATCH_ENTITY", "CHANGE_BATCH_ENTITY"):
        required = " ".join(_contract(action).get("required") or [])
        assert "selectParam" in required
        assert "output.name" in required


def test_batch_output_is_scalar_count():
    """出参是影响行数（标量），不是 DTO 数组。"""
    for action in ("CREATE_BATCH_ENTITY", "CHANGE_BATCH_ENTITY"):
        note = _contract(action).get("note") or ""
        assert "INTEGER" in note, "%s 的出参应说明是 INTEGER 计数" % action


def test_batch_module_reexports_extra_impl():
    """microflow_nodes_batch 只能是转发，不能再有第二套实现。"""
    from components.construction import microflow_nodes_batch as B
    from components.construction import microflow_nodes_extra as X

    assert B.create_batch_entity is X.create_batch_entity
    assert B.change_batch_entity is X.change_batch_entity


def test_builder_output_has_no_attrs_and_integer_out():
    """真造一个节点验证：无 attrs、出参 INTEGER。"""
    from components.construction.node_builder import NodeBuilder
    from components.construction import microflow_nodes_extra as X

    b = NodeBuilder(app_id="1", app_name="app1")
    entity = {"caption": "实体A", "fullName": "com.x.EntityADto",
              "refApp": "app1", "relationEntityId": "-1", "attributes": {}}
    src = {"nodeId": "RETRIEVE_ARRAY_x", "actionType": "RETRIEVE_ARRAY",
           "output": {"name": "_RETRIEVE_ARRAY_x"}, "title": "列表"}
    for fn in (X.create_batch_entity, X.change_batch_entity):
        node = fn(b, entity, src, [])
        assert "attrs" not in node or not node["attrs"]
        assert node["output"]["dataType"] == "INTEGER"
        assert node["selectParam"]["type"] == "ARRAY"
