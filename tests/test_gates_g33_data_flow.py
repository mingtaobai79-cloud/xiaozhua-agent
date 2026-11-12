"""G33 / CALL_DATA_FLOW 定案回归。

2026-11-02 用两条独立证据解掉了「dataFlow.id 到底存 dataFlowId 还是 mapping id」：

① 前端 bundle（设计器）保存时执行 `merge:{dataFlowMappingId:"dataFlow.id"}`
   → 两者必然相等，平台自己的节点不可能出现「规则 id + 行 id」这种分离写法。
② 运行时 `CallDataFlowActivity.parseActivityNode` 只读 `dataFlowMappingId`，
   `dataFlow` 对象根本不参与解析；存在性校验用的集合键名是
   `data-flow-mapping-id-used-by-micro-flow`，由 `DataFlowMappingDto.getId()` 填充
   → 值必须是 DataFlowMapping 主键，即 udcDataFlowListManuallyMappingPost 的列表行 id。

同时修掉一个闸门缺陷：G33 曾被复制进 `run_end_gate` 和 `run_leak_gate`，
同一处违规会重复报 3 次（实际见到「G33 拦 6 项」= 2 条 × 3）。
"""
import io
import re
from pathlib import Path

import pytest

from components.construction.microflow_nodes_extra import call_data_flow
from components.udc.microflow.gates import run_end_gate, run_gates, run_leak_gate

ROOT = Path(__file__).resolve().parents[1]
PARSER = (ROOT / "docs/audit/artifacts/decompiled/cfr-r31b/com/seeyon/udc/"
          "microflow/domain/bo/flow/activity/CallDataFlowActivity.java")
FRONTEND = (ROOT / "docs/audit/artifacts/udc-frontend-5.3.496/chunks/"
            "src_redux_store_ts.14dc061e.js")


class _Builder:
    """最小 NodeBuilder 替身：只要 build() 返回模板字典。"""

    app_name = "app"

    def build(self, action_type, caption=None):
        return {"nodeId": "CALL_DATA_FLOW_test", "type": "ACTIVITY",
                "actionType": action_type, "caption": caption}


RULE = {"id": "5304545611384242198", "dataFlowId": "7621688506670924729",
        "appId": "1", "appUrl": "app", "caption": "1", "name": "asd",
        "sourceEntityId": "-2537349473285092530"}
STRUCT = {"entityId": "-2537349473285092530", "entityName": "E"}


def _node(**over):
    n = call_data_flow(_Builder(), STRUCT, RULE, [{"type": "GROUP"}], "结果")
    n.update(over)
    return n


def _schema(node):
    return {"nodes": [node],
            "endNode": {"nodeId": "MFEndNode", "type": "END",
                        "actionType": "END_NODE", "caption": "结束"}}


# ── 构造器不变量 ────────────────────────────────────────────────────────────

def test_data_flow_id_equals_mapping_id_and_row_id():
    n = _node()
    assert n["dataFlowMappingId"] == RULE["id"]
    assert n["dataFlow"]["id"] == RULE["id"], "dataFlow.id 必须是列表行 id（前端 merge 强制）"
    assert n["dataFlow"]["id"] == n["dataFlowMappingId"]


def test_rule_id_is_not_used_as_data_flow_id():
    n = _node()
    assert n["dataFlow"]["id"] != RULE["dataFlowId"]
    # dataFlowId 仍作为行内 FK 保留（便于追溯规则本体）
    assert n["dataFlow"].get("dataFlowId") == RULE["dataFlowId"]


def test_built_node_passes_g33():
    assert [p for p in run_gates(_schema(_node())) if "G33" in p] == []


# ── 闸门行为 ────────────────────────────────────────────────────────────────

def test_g33_flags_mismatch_once_not_thrice():
    bad = _node(dataFlow={"id": RULE["dataFlowId"]})
    hits = [p for p in run_gates(_schema(bad)) if "G33" in p]
    assert len(hits) == 1, f"同一违规应只报一次，实际 {len(hits)} 次：{hits}"


def test_g33_requires_condition():
    hits = [p for p in run_gates(_schema(_node(condition=[]))) if "G33" in p]
    assert len(hits) == 1
    assert "condition" in hits[0]


def test_g33_not_emitted_by_other_gates():
    """G33 只属于 run_gates；混进门禁/泄漏闸门会导致重复计数。"""
    bad = _node(dataFlow={"id": RULE["dataFlowId"]})
    assert [p for p in run_end_gate(_schema(bad)) if "G33" in p] == []
    assert [p for p in run_leak_gate(_schema(bad)) if "G33" in p] == []


# ── 静态契约（证据文件在才跑）──────────────────────────────────────────────

@pytest.mark.skipif(not PARSER.exists(), reason="反编译解析器不在盘")
def test_parser_reads_only_data_flow_mapping_id():
    src = PARSER.read_text(encoding="utf-8", errors="replace")
    assert 'NodeUtils.getString("dataFlowMappingId", node, true' in src
    # dataFlow 对象不参与解析：不得有 getObject("dataFlow" ...)
    assert not re.search(r'get(Object|JsonNode)?\(\s*"dataFlow"\s*,', src)


@pytest.mark.skipif(not FRONTEND.exists(), reason="前端 bundle 不在盘")
def test_designer_merges_mapping_id_from_data_flow_id():
    txt = FRONTEND.read_text(encoding="utf-8", errors="replace")
    assert 'merge:{dataFlowMappingId:"dataFlow.id"}' in txt, \
        "设计器不再强制 dataFlowMappingId = dataFlow.id，G33 等值校验需重新取证"
