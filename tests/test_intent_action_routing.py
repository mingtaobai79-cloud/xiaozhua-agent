"""宿主任务路由与发现：意图 → 组件内只读 action。

背景：`XiaozhuaAgent.route` 只做域级路由，`dispatch` 对 udc 域固定执行
`inspect_application`。宿主拿到「微流程节点怎么配」这类请求时，只能得到应用级
报告，永远命中不到 `inspect_microflow`（该 action 已在 UdcComponent.capabilities()
里，但入口选不到它），也没有任何接口告诉宿主「哪些意图对应哪个 action」。

本文件用正反例固定最小契约：
  正例 —— 微流程意图在 udc 域选中 inspect_microflow，并真的返回微流程域证据；
  反例 —— 其他意图保持原默认 action、混合意图不静默归类、能力缺失时不臆造 action。
全部离线，不访问平台。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from core.agent import AgentRequest, XiaozhuaAgent  # noqa: E402
from components.udc.component import UdcComponent  # noqa: E402

AUDIT = ROOT / "tests" / "fixtures" / "udc-audit"


def _agent(audit: bool = False) -> XiaozhuaAgent:
    return XiaozhuaAgent({"udc": UdcComponent(audit_dir=AUDIT) if audit else UdcComponent()})


# ---------------------------------------------------------------- 正例


def test_microflow_intent_hits_inspect_microflow():
    result = _agent().dispatch(AgentRequest("微流程节点怎么配", {"target": "demo"}))
    assert result["component"] == "udc"
    assert result["action"] == "inspect_microflow"
    assert result["domain"] == "microflow"
    assert result["mode"] == "read-only"


def test_microflow_intent_returns_microflow_domain_evidence():
    result = _agent(audit=True).dispatch(AgentRequest("微流程 节点 actionType 有哪些", {"target": "demo"}))
    assert result["action"] == "inspect_microflow"
    assert result["status"] == "FACT"
    assert result["count"] == 9
    assert "dynamic_contract_fields" in result["unverified"]


def test_english_microflow_keyword_hits_same_action():
    result = _agent().dispatch(AgentRequest("inspect microflow node contract", {"target": "demo"}))
    assert result["action"] == "inspect_microflow"


# ---------------------------------------------------------------- 反例


def test_non_microflow_udc_intent_keeps_default_action():
    result = _agent().dispatch(AgentRequest("分析 UDC 实体", {"target": "demo"}))
    assert result["action"] == "inspect_application"


def test_mixed_domain_intent_is_not_routed():
    result = _agent().dispatch(AgentRequest("排查微流程运行态 Redis 缓存", {"target": "demo"}))
    assert result["component"] == "unknown"
    assert result["status"] == "UNAVAILABLE"
    assert "action" not in result


def test_english_keyword_inside_unrelated_word_does_not_select_action():
    # 域命中靠 udc，action 不能被 microflows（更长单词）带偏
    result = _agent().dispatch(AgentRequest("review the udc microflows report", {"target": "demo"}))
    assert result["component"] == "udc"
    assert result["action"] == "inspect_application"


def test_missing_capability_does_not_fabricate_action():
    """组件没登记 inspect_microflow 时退回它自己的默认 action，不猜。"""

    class _Stub:
        name = "udc"
        read_only = True

        def capabilities(self):
            return ["inspect"]

        def inspect(self, target):
            return {"component": "udc", "target": target, "status": "UNVERIFIED", "action": "inspect"}

    agent = XiaozhuaAgent({"udc": _Stub()})
    result = agent.dispatch(AgentRequest("微流程节点怎么配", {"target": "demo"}))
    assert result["action"] == "inspect"


# ---------------------------------------------------------------- 否定语境


def test_negated_microflow_intent_does_not_hit_inspect_microflow():
    """「不要分析微流程，分析实体」：微流程被否定，不能抢走 action。"""
    result = _agent().dispatch(AgentRequest("不要分析微流程，分析实体", {"target": "demo"}))
    assert result["component"] == "udc"
    assert result["action"] == "inspect_application"


def test_negation_in_trailing_clause_does_not_hit():
    result = _agent().dispatch(AgentRequest("分析实体字段，不要分析微流程", {"target": "demo"}))
    assert result["action"] == "inspect_application"


def test_negated_english_keyword_does_not_hit():
    result = _agent().dispatch(AgentRequest("skip microflow, inspect the entity", {"target": "demo"}))
    assert result["action"] == "inspect_application"


def test_post_posed_negation_excludes_object():
    """「微流程不用看了」是后置否定。"""
    result = _agent().dispatch(AgentRequest("微流程不用看了，给我实体字段", {"target": "demo"}))
    assert result["action"] == "inspect_application"


def test_object_level_negation_without_observation_verb_is_not_exclusion():
    """「微流程不需要重新部署」仍在问微流程，不算排除。"""
    result = _agent().dispatch(AgentRequest("微流程不需要重新部署吧？怎么配节点", {"target": "demo"}))
    assert result["action"] == "inspect_microflow"


def test_negation_does_not_leak_across_clauses():
    """否定只作用于同一分句；后半句的微流程仍应命中。"""
    result = _agent().dispatch(AgentRequest("不要分析实体，分析微流程节点", {"target": "demo"}))
    assert result["action"] == "inspect_microflow"


def test_positive_clause_after_negated_clause_still_hits():
    result = _agent().dispatch(AgentRequest("先不用看应用报告，直接看微流程节点怎么配", {"target": "demo"}))
    assert result["action"] == "inspect_microflow"


def test_not_only_phrase_is_not_a_negation():
    """「不只/不仅」是递进而非否定，微流程仍在询问范围内。"""
    result = _agent().dispatch(AgentRequest("不只看微流程，还要看实体字段", {"target": "demo"}))
    assert result["action"] == "inspect_microflow"


def test_word_containing_single_char_cue_is_not_a_negation():
    """「区别」里的「别」不是否定词。"""
    result = _agent().dispatch(AgentRequest("区别微流程和实体的差异", {"target": "demo"}))
    assert result["action"] == "inspect_microflow"


def test_only_negated_microflow_mention_keeps_default_action():
    """整句只提到被否定的微流程时，退回域默认 action，不猜。"""
    result = _agent().dispatch(AgentRequest("这次不需要微流程", {"target": "demo"}))
    assert result["component"] == "udc"
    assert result["action"] == "inspect_application"


def test_ambiguous_negation_cue_is_treated_as_hit():
    """「不是/not」既可能是排除也可能是疑问/限定，判不准时不吞掉真实意图。"""
    for intent in ("不是微流程问题吧，那是页面问题吗", "not only microflow but also entity"):
        result = _agent().dispatch(AgentRequest(intent, {"target": "demo"}))
        assert result["action"] == "inspect_microflow", intent


# ---------------------------------------------------------------- 发现面


def test_intent_index_exposes_only_registered_capabilities():
    index = _agent().intent_index()
    assert set(index) == {"udc"}
    assert "inspect_microflow" in index["udc"]
    assert "微流程" in index["udc"]["inspect_microflow"]


def test_intent_index_omits_action_when_component_lacks_it():
    class _Stub:
        name = "udc"
        read_only = True

        def capabilities(self):
            return ["inspect"]

        def inspect(self, target):
            return {"status": "UNVERIFIED"}

    assert XiaozhuaAgent({"udc": _Stub()}).intent_index() == {"udc": {}}
