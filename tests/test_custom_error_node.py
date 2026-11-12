"""CUSTOM_ERROR 节点接线。

★ 为什么值得单测：这是「断言」能力的底座。
  没有它，流程只能证明「跑通了」；有了它，可以证明「跑出来的东西对不对」
  —— 查询为空就抛错，于是运行日志的 success=false 本身就是一票否决的证据。
"""
import pytest

from components.construction.logic_graph import GraphError, LogicGraphRunner


class _FakeComposer:
    """只记录 step 调用的最小 composer 替身。"""

    def __init__(self):
        self.calls = []
        self.by_alias = {}

    def step(self, kind, alias, **kw):
        self.calls.append((kind, alias, kw))
        node = {"nodeId": "N_" + alias, "actionType": kind.upper()}
        self.by_alias[alias] = node
        return node


def _runner(comp=None):
    r = LogicGraphRunner.__new__(LogicGraphRunner)
    r.c = comp or _FakeComposer()
    return r


def test_do_custom_error_dispatches_with_message():
    comp = _FakeComposer()
    r = _runner(comp)
    r._do_custom_error({"id": "err", "kind": "custom_error",
                        "message": "标记不存在", "caption": "校验-标记"})
    kind, alias, kw = comp.calls[0]
    assert kind == "custom_error" and alias == "err"
    assert kw["message"] == "标记不存在"
    assert kw["caption"] == "校验-标记"


def test_do_custom_error_defaults():
    comp = _FakeComposer()
    r = _runner(comp)
    r._do_custom_error({"id": "err", "kind": "custom_error"})
    assert comp.calls[0][2]["message"], "必须有默认文案，不能空消息"
    assert comp.calls[0][2]["error_type"] == "GLOBAL"


def test_do_custom_error_accepts_text_alias():
    """text/message 两种写法都认（不同构造路径用过不同键）。"""
    comp = _FakeComposer()
    r = _runner(comp)
    r._do_custom_error({"id": "e", "kind": "custom_error", "text": "从 text 来"})
    assert comp.calls[0][2]["message"] == "从 text 来"


def test_composer_has_st_custom_error():
    """★ 执行器和组装器必须成对存在，只补一边会在运行时才炸。"""
    from components.construction.microflow_composer import MicroflowComposer
    assert hasattr(MicroflowComposer, "_st_custom_error"), \
        "composer 缺 _st_custom_error → step('custom_error') 会抛 ComposeError"
