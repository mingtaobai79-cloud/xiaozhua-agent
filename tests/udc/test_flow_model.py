"""生单/扣减域模型测试（证据驱动，全离线）。

证据来源：docs/audit/udc-semantics/flow-excel-source-audit.md
"""
import pytest

from components.udc.flow_model import (
    DATA_FLOW_OPERATION_TYPES,
    DATAFLOW_ENDPOINTS,
    DEDUCTION_ENDPOINTS,
    DEDUCTION_LIFECYCLE,
    DEDUCTION_LIFECYCLE_DO_UNDO,
    TRIGGER_POINTS,
    DataFlowGraph,
    DataFlowLine,
    DeductionRule,
    assert_object_boundary_facts,
)


# ---------------------------------------------------------------- 值域

def test_trigger_points_enum():
    assert TRIGGER_POINTS == {"MANUALLY", "EVENT_SUBSCRIBE"}


def test_operation_types_enum():
    assert DATA_FLOW_OPERATION_TYPES == {"CREATE", "UPDATE", "CREATE_OR_UPDATE"}


def test_deduction_lifecycle_do_undo_mapping():
    assert DEDUCTION_LIFECYCLE == {"BeforeCreate", "BeforeUpdate", "BeforeDelete"}
    assert DEDUCTION_LIFECYCLE_DO_UNDO["BeforeCreate"] == ("DO",)
    assert DEDUCTION_LIFECYCLE_DO_UNDO["BeforeUpdate"] == ("UNDO", "DO")
    assert DEDUCTION_LIFECYCLE_DO_UNDO["BeforeDelete"] == ("UNDO",)


def test_controller_literal_paths_not_gateway_prefixed():
    # 字面路径，不拼 Gateway 前缀（证据纪律）
    for paths in (DATAFLOW_ENDPOINTS, DEDUCTION_ENDPOINTS):
        for p in paths.values():
            assert p.split(" ")[1].startswith("/udc/")
            assert "/service/" not in p


# ---------------------------------------------------------------- DataFlow 图校验

def test_valid_graph_passes():
    g = DataFlowGraph(
        graph_id="g1", app_id="8704",
        lines=[DataFlowLine("e1", "e2", operation_type="CREATE_OR_UPDATE", trigger_point="EVENT_SUBSCRIBE")],
    )
    r = g.validate()
    assert r["status"] == "PASS"
    assert r["can_execute"] is False


def test_self_loop_rejected():
    g = DataFlowGraph(graph_id="g1", lines=[DataFlowLine("e1", "e1")])
    r = g.validate()
    assert r["status"] == "FAIL"
    assert any("自身" in e for e in r["errors"])


def test_bad_operation_type_rejected():
    g = DataFlowGraph(graph_id="g1", lines=[DataFlowLine("e1", "e2", operation_type="DELETE")])
    r = g.validate()
    assert any("DELETE" in e for e in r["errors"])


def test_bad_trigger_point_rejected():
    g = DataFlowGraph(graph_id="g1", lines=[DataFlowLine("e1", "e2", trigger_point="CRON")])
    r = g.validate()
    assert any("CRON" in e for e in r["errors"])


def test_empty_graph_is_unverified_not_fail():
    g = DataFlowGraph(graph_id="g1")
    r = g.validate()
    assert r["status"] == "UNVERIFIED"
    assert any("不代表功能未启用" in w for w in r["warnings"])


def test_bill_target_rejected_on_deduction_graph():
    g = DataFlowGraph(
        graph_id="g2", note="deduction_graph",
        raw_entities={"e9": {"category": "bill"}},
        lines=[DataFlowLine("e1", "e9")],
    )
    r = g.validate()
    assert r["status"] == "FAIL"
    assert any("bill" in e for e in r["errors"])


# ---------------------------------------------------------------- Deduction 规则

def test_valid_rule_passes_with_lifecycle_do_undo():
    r_ = DeductionRule(
        rule_id="r1", map_id="m1",
        source_root_entity="order", target_root_entity="stock",
        lifecycle="BeforeCreate",
        algorithms=[{"id": "a1"}],
    )
    out = r_.validate()
    assert out["status"] == "PASS"
    assert out["lifecycle_do_undo"] == ("DO",)


def test_rule_missing_root_entities_fails():
    out = DeductionRule(rule_id="r1", lifecycle="BeforeDelete").validate()
    assert out["status"] == "FAIL"
    assert any("source/target 根实体" in e for e in out["errors"])


def test_rule_bad_lifecycle_fails():
    out = DeductionRule(source_root_entity="a", target_root_entity="b",
                        lifecycle="AfterCreate").validate()
    assert any("AfterCreate" in e for e in out["errors"])


def test_rule_without_algorithm_warns_not_fails():
    # §3: DeductionCodeTask 只有非空规则元数据才生成代码——保存≠生成，软警告
    out = DeductionRule(source_root_entity="a", target_root_entity="b",
                        lifecycle="BeforeUpdate").validate()
    assert out["status"] == "UNVERIFIED"
    assert any("保存≠生成" in w for w in out["warnings"])


# ---------------------------------------------------------------- 对象边界（防混用回归）

def test_object_boundaries_are_registered():
    facts = assert_object_boundary_facts()
    blob = " ".join(facts)
    assert "CALL_DATA_FLOW" in blob
    assert "CHANGE_ENTITY" in blob
    assert "VALIDATE_ENTITY" in blob
    assert "udc_filter_plan" in blob
    # 六条边界全在（与 flow-excel-source-audit §1/§6 + UDC-MAINLINE §2 一致）
    assert len(facts) == 6


def test_dataflow_model_not_confused_with_deduction():
    # 边界测试：生单结果只暴露 targetIds/updateIds；模型不得有"直接调扣减"的字段
    from components.udc.flow_model import DataFlowLine
    assert not any("deduction" in f.name.lower() for f in DataFlowLine.__dataclass_fields__.values())
