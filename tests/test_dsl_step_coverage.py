"""DSL 入口完整性：声明 / 执行器 / composer step 三者必须一一对上。

2026-11-02 核对发现 DSL 是**双向不一致**的：
  - 声明了但没执行器：call_app_service / data_mapping / delete_entity
    → validate_graph 放行，跑到一半 GraphError「还没接执行器」
  - 有执行器但没声明：custom_error
    → validate_graph 直接拒，执行器永远用不到

「DSL 缺 6 种入口」这个说法低估了问题：真正坏掉的是 3 个已声明的 + 1 个孤儿。
本文件的 introspection 测试就是防它再退化——加 kind 必须同时加执行器和 step。
"""
from __future__ import annotations

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.construction.logic_graph import (  # noqa: E402
    GraphError, LogicGraphRunner, _STEP_KINDS, validate_graph,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 分支类由 _exec_branch / _exec_loop 特殊处理，不走 _do_*
CONTROL = {"branch", "for_each", "for_count"}


def _read(rel):
    return open(os.path.join(ROOT, rel), encoding="utf-8").read()


def _executors():
    return set(re.findall(r"def _do_(\w+)\(", _read("components/construction/logic_graph.py")))


def _composer_steps():
    return set(re.findall(r"def _st_(\w+)\(",
                          _read("components/construction/microflow_composer.py")))


# ---------------------------------------------------------------- 一致性
def test_every_declared_kind_has_executor():
    missing = sorted(set(_STEP_KINDS) - CONTROL - _executors())
    assert not missing, "这些 kind 声明了但没执行器，用了就 GraphError: %s" % missing


def test_every_executor_is_declared():
    orphan = sorted(_executors() - set(_STEP_KINDS))
    assert not orphan, "这些执行器没在 _STEP_KINDS 里，validate_graph 会直接拒: %s" % orphan


def test_every_executor_has_composer_step():
    missing = sorted(_executors() - _composer_steps())
    assert not missing, "执行器没有对应 composer step: %s" % missing


def test_six_target_kinds_present():
    """本轮要补的六种入口。"""
    for kind in ("create_batch_entity", "change_batch_entity", "publish_business_event",
                 "custom_error", "call_data_flow", "break"):
        assert kind in _STEP_KINDS, "%s 不在 DSL 里" % kind


# ---------------------------------------------------------------- 结构校验
def _graph(*nodes):
    return {"nodes": list(nodes), "out_desc": "结果", "basic_out": "INTEGER"}


def test_validate_accepts_all_new_kinds():
    problems = validate_graph(_graph(
        {"id": "a", "kind": "custom_error", "message": "x"},
        {"id": "b", "kind": "create_batch_entity", "entity": "E", "list_node": "c"},
        {"id": "c", "kind": "change_batch_entity", "entity": "E", "list_node": "c"},
        {"id": "d", "kind": "publish_business_event", "event": {"fullName": "x"}},
        {"id": "e", "kind": "call_data_flow", "entity": "E", "rule": {"id": "r"}},
        {"id": "f", "kind": "delete_entity", "entity": "E", "from_node": "c"},
    ))
    assert not problems, problems


def test_unknown_kind_still_rejected():
    problems = validate_graph(_graph({"id": "a", "kind": "no_such_kind"}))
    assert problems and "不支持" in problems[0]


# ---------------------------------------------------------------- 执行器行为
class FakeBuilder:
    """最小 builder：循环构造器要用 build()。"""

    app_name = "app"

    def build(self, action, caption="", **kw):
        node = {"nodeId": action + "_x", "type": "ACTIVITY", "caption": caption}
        node.update(kw)
        return node

    def output_name(self, node):
        return (node.get("output") or {}).get("name") or "_out"


class RecComposer:
    """记录每次 step 的 kwargs，用于断言 DSL → composer 的映射。"""

    def __init__(self):
        self.nodes = []
        self.by_alias = {}
        self.calls = []
        self.trigger = {"nodeId": "MFStartNode", "type": "MANUAL"}
        self.refs = None
        self.b = FakeBuilder()

    def entity(self, label):
        """假实体模型（retrieve_array 等执行器会调 composer.entity）。"""
        return {"caption": label, "attributes": {}, "fullName": "com.x.Dto",
                "relationEntityId": "-1", "refApp": "app1"}

    def step(self, kind, alias, **kw):
        self.calls.append((kind, alias, kw))
        node = {"nodeId": kind.upper() + "_x", "actionType": kind.upper(),
                "type": "ACTIVITY", "caption": kw.get("caption") or alias,
                "output": {"name": "_" + alias, "dataType": "DTO", "type": "OBJECT"}}
        self.nodes.append(node)
        self.by_alias[alias] = node
        return node

    def finish(self, *, end_from="", trigger=None, out_desc="", basic_out=None):
        return {"trig": trigger, "nodes": self.nodes}


def _run(*nodes):
    c = RecComposer()
    r = LogicGraphRunner(c, resolver=None, backend=None)
    r.run(_graph(*nodes))
    return c


def test_delete_entity_from_node_uses_select_param():
    c = _run({"id": "ra", "kind": "retrieve_array", "entity": "E"},
             {"id": "d", "kind": "delete_entity", "entity": "E", "from_node": "ra"})
    kind, alias, kw = [x for x in c.calls if x[0] == "delete_entity"][0]
    assert kw["from_node"] == "ra"
    assert "cond_field" not in kw


def test_delete_entity_without_from_node_uses_condition():
    c = _run({"id": "d", "kind": "delete_entity", "entity": "E",
              "cond_field": "id", "right": 1})
    _, _, kw = [x for x in c.calls if x[0] == "delete_entity"][0]
    assert kw["cond_field"] == "id" and "from_node" not in kw


def test_batch_nodes_pass_entity_and_list_alias():
    c = _run({"id": "ra", "kind": "retrieve_array", "entity": "E"},
             {"id": "b1", "kind": "change_batch_entity", "entity": "E", "list_node": "ra"},
             {"id": "b2", "kind": "create_batch_entity", "entity": "E", "list_node": "ra"})
    for k in ("change_batch_entity", "create_batch_entity"):
        _, _, kw = [x for x in c.calls if x[0] == k][0]
        assert kw["entity"] == "E" and kw["list_node"] == "ra"


def test_batch_node_rejects_unknown_list():
    c = RecComposer()
    r = LogicGraphRunner(c, resolver=None, backend=None)
    with pytest.raises(GraphError) as e:
        r.run(_graph({"id": "b", "kind": "change_batch_entity", "entity": "E",
                      "list_node": "nope"}))
    assert "list_node" in str(e.value)


def test_break_outside_loop_rejected():
    c = RecComposer()
    r = LogicGraphRunner(c, resolver=None, backend=None)
    with pytest.raises(GraphError) as e:
        r.run(_graph({"id": "br", "kind": "break"}))
    assert "循环体" in str(e.value)


def test_break_inside_for_count_allowed():
    """★ FOR_COUNT 没有循环项 frame（loops 栈里没有它），
    所以 BREAK 的合法性不能靠 loops 判——曾因此把合法 BREAK 误拒。"""
    c = _run({"id": "lp", "kind": "for_count", "start": 1, "end": 3,
              "body": [{"id": "br", "kind": "break"}]})
    assert [x[0] for x in c.calls].count("break") == 1


def test_break_inside_branch_but_not_loop_rejected():
    """BRANCH 里也不算循环体。"""
    c = RecComposer()
    r = LogicGraphRunner(c, resolver=None, backend=None)
    with pytest.raises(GraphError):
        r.run(_graph({"id": "if", "kind": "branch", "when": "1==1",
                      "then": [{"id": "br", "kind": "break"}]}))


def test_publish_event_requires_live_event_object():
    c = RecComposer()
    r = LogicGraphRunner(c, resolver=None, backend=None)
    with pytest.raises(GraphError) as e:
        r.run(_graph({"id": "ev", "kind": "publish_business_event", "event": {}}))
    assert "fullName" in str(e.value)


def test_call_data_flow_requires_rule_object():
    c = RecComposer()
    r = LogicGraphRunner(c, resolver=None, backend=None)
    with pytest.raises(GraphError) as e:
        r.run(_graph({"id": "df", "kind": "call_data_flow", "entity": "E"}))
    assert "rule" in str(e.value)


def test_custom_error_reaches_composer():
    c = _run({"id": "ce", "kind": "custom_error", "message": "标记不存在"})
    kind, _, kw = [x for x in c.calls if x[0] == "custom_error"][0]
    assert kw["message"] == "标记不存在"
