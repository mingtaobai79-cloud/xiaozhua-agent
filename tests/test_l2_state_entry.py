"""l2_state 的入口 URL 契约。

★ 真实事故：read_state 用 .../app-design/rule?appId=X&id=<mid> 打开，
  现在落到**列表页**，redux 里只有 microFlowList/microFlowMenuData，
  flowNodes 永远为空。read_state 返回 {"nodes": {}} 且**不报错**，
  于是 UI 复测静默变成「0 个未完成节点 → 通过」——假绿。
"""
import inspect

from components.udc.microflow.live import l2_state


def test_read_state_uses_microflow_editor_path():
    """入口必须是 rule/microflow/editor/<mid>?appId=<app>。"""
    src = inspect.getsource(l2_state.read_state)
    assert "rule/microflow/editor/" in src, \
        "read_state 必须用 microflow/editor 入口，否则会落到列表页"
    assert "app-design/rule?appId=" not in src, \
        "旧的 rule?appId=&id= 入口会落到列表页，flowNodes 恒空"


def test_read_state_raises_when_nodes_unreadable():
    """读不到 flowNodes 必须抛错，不许返回空 dict 冒充成功。"""
    src = inspect.getsource(l2_state.read_state)
    assert "raise RuntimeError" in src, \
        "读不到必须抛 RuntimeError；静默返回空会让 UI 复测假通过"


def test_check_state_on_empty_nodes_is_not_evidence():
    """空 nodes 上 check_state 返回 [] 是「没数据」不是「没问题」。

    这条测试锁定语义：调用方必须自己判 nodes 非空，
    不能把 check_state([]) == [] 当验收通过。
    """
    assert l2_state.check_state({}) == []
    # 所以调用方约定：nodes 为空 → 必须先判空再决定是否可信
    assert not l2_state.check_state({}), \
        "空输入返回空列表是预期行为，调用方需自行判空"
