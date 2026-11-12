"""微流程节点/动作模型 + dataSchema 校验器测试（证据驱动，全离线）。

证据来源：docs/audit/udc-semantics/microflow-source-audit.md
  §1 节点类型 MicroFlowNodeTypeEnum（8 值）
  §2 活动节点 ActivityNodeTypeEnum 四组 + 输入输出矩阵
  §2 ConvertDataActivity.convertType 11 值受控值域
  §4 前端创建类型 → (type, triggerType) 映射 10 项
  §5 checkSchema 入口（校验通过 ≠ 发布）
"""
import json

import pytest

from components.udc.microflow_model import (
    ACTIVITY_TYPES,
    BASE_SERVICES,
    CONVERT_DATA_TYPES,
    DATA_ACTIVITIES,
    FRONTEND_CREATE_TYPE_MAP,
    NODE_TYPES,
    RULE_ACTIVITIES,
    VARIABLE_COLLECTION_TRANSFORM,
    classify_microflow_type,
    parse_data_schema,
)


# ---------------------------------------------------------------- 值域自检

def test_node_types_cover_control_enum():
    assert set(NODE_TYPES) == {
        "CONDITION", "FOR_EACH", "BRANCH", "CUSTOM_ERROR", "END",
        "ACTIVITY", "FOR", "BREAK",
    }


def test_activity_groups_are_disjoint_and_covered():
    assert DATA_ACTIVITIES | BASE_SERVICES | VARIABLE_COLLECTION_TRANSFORM | RULE_ACTIVITIES == ACTIVITY_TYPES
    # 四组互斥（无交叉）
    assert not (DATA_ACTIVITIES & BASE_SERVICES)
    assert not (DATA_ACTIVITIES & VARIABLE_COLLECTION_TRANSFORM)
    assert not (BASE_SERVICES & VARIABLE_COLLECTION_TRANSFORM)
    assert not (RULE_ACTIVITIES & VARIABLE_COLLECTION_TRANSFORM)


def test_convert_data_values_from_source():
    # ConvertDataActivity.java:35-50 逐字 11 值
    assert "MultiAssociation2List" in CONVERT_DATA_TYPES
    assert "GetEnumCode" in CONVERT_DATA_TYPES
    assert "Split" in CONVERT_DATA_TYPES
    assert len(CONVERT_DATA_TYPES) == 11


def test_frontend_create_type_map_10_items():
    assert len(FRONTEND_CREATE_TYPE_MAP) == 10
    assert classify_microflow_type("eventmonitor") == ("SERVICE", "BUSINESS_EVENT")
    assert classify_microflow_type("timingtask") == ("SERVICE", "SCHEDULE")
    assert classify_microflow_type("frontend") == ("FRONTEND", "MANUAL")
    assert classify_microflow_type("entityrule") == ("ENTITYRULE", "MANUAL")
    # 未知类型返回 None（不臆造）
    assert classify_microflow_type("nonsense") is None


# ---------------------------------------------------------------- 解析 + 校验

def _ok_schema():
    return json.dumps({
        "nodes": [
            {"type": "ACTIVITY", "nodeId": "n1", "caption": "取数", "actionType": "RETRIEVE",
             "condition": {}, "output": "v1"},
            {"type": "CONDITION", "nodeId": "n2", "caption": "判断",
             "expression": "x>0",
             "nodes": [
                 {"type": "ACTIVITY", "nodeId": "n3", "caption": "改数", "actionType": "CHANGE_ENTITY",
                  "attrs": {}, "output": "v2"},
             ]},
            {"type": "END", "nodeId": "n4", "caption": "结束", "output": ""},
        ],
    })


def test_parse_valid_schema_pass():
    g = parse_data_schema(_ok_schema())
    assert g.status() == "PASS", g.to_dict()
    assert g.activity_ids() == ["n1", "n3"]
    assert g.activity_count == 2


def test_missing_root_nodes_is_error():
    g = parse_data_schema(json.dumps({}))
    assert g.status() == "FAIL"
    assert any("nodes" in e for e in g.errors)


def test_bad_json_string_is_error():
    g = parse_data_schema("{not json")
    assert g.status() == "FAIL"


def test_unknown_node_type_is_error():
    schema = json.dumps({"nodes": [{"type": "BOGUS_NODE", "nodeId": "x1"}]})
    g = parse_data_schema(schema)
    assert g.status() == "FAIL"
    assert any("BOGUS_NODE" in e for e in g.errors)


def test_convert_data_bad_value_is_error():
    # 多选人员转列表正确受控值是 MultiAssociation2List；写 ToList 无证据应报错
    schema = json.dumps({
        "nodes": [
            {"type": "ACTIVITY", "nodeId": "c1", "caption": "转列表",
             "actionType": "CONVERT_DATA", "convertType": "ToList", "selectParam": {}},
        ],
    })
    g = parse_data_schema(schema)
    assert g.status() == "FAIL"
    assert any("CONVERT_DATA" in e and "ToList" in e for e in g.errors)


def test_convert_data_correct_value_passes():
    schema = json.dumps({
        "nodes": [
            {"type": "ACTIVITY", "nodeId": "c1", "caption": "转列表",
             "actionType": "CONVERT_DATA", "convertType": "MultiAssociation2List", "selectParam": {}},
        ],
    })
    g = parse_data_schema(schema)
    assert g.status() in {"PASS", "UNVERIFIED"}  # 缺 recommended 键最多警告
    assert not any("convertType" in e for e in g.errors)


def test_expected_activity_scope_check_is_soft():
    g = parse_data_schema(_ok_schema(), expected=["n1", "n9"])
    # n9 未出现 → 软警告（不判硬错：保存成功 ≠ 功能成立）
    assert g.status() == "UNVERIFIED"
    assert any("n9" in w for w in g.warnings)
    assert not g.errors


def test_branch_recursive_children():
    schema = json.dumps({
        "nodes": [
            {"type": "BRANCH", "nodeId": "b1", "caption": "分支",
             "conditions": [
                 {"expression": "a==1",
                  "nodes": [{"type": "ACTIVITY", "nodeId": "a1", "actionType": "SHOW_MESSAGE", "output": "m"}]},
                 {"expression": "a==2",
                  "nodes": [{"type": "ACTIVITY", "nodeId": "a2", "actionType": "DELETE_ENTITY", "output": "d"}]},
             ]},
        ],
    })
    g = parse_data_schema(schema)
    assert g.status() in {"PASS", "UNVERIFIED"}
    assert set(g.activity_ids()) >= {"a1", "a2"}


def test_call_data_flow_missing_mapping_warns():
    schema = json.dumps({
        "nodes": [
            {"type": "ACTIVITY", "nodeId": "f1", "actionType": "CALL_DATA_FLOW", "output": "r"},
        ],
    })
    g = parse_data_schema(schema)
    assert any("CALL_DATA_FLOW" in w and "dataFlowMappingId" in w for w in g.warnings)


# ---------------------------------------------------------------- 与 construction builder 的衔接

def test_classify_matches_create_builder_trigger_values():
    # create REST 的 triggerType 字符串值域（microflow.py TRIGGER_TYPE_VALUES）
    from components.construction.microflow import TRIGGER_TYPE_VALUES
    triggers_used = {v[1] for v in FRONTEND_CREATE_TYPE_MAP.values()}
    # 前端映射用到的 trigger 全部落在 create REST 合法值域或前端专用域
    assert triggers_used <= set(TRIGGER_TYPE_VALUES) | {"FRONTEND_PARAM"}
