"""测试：微流程节点过滤条件 / 映射规则的约束校验器（前端 seeyon-biz-where 证据）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.microflow_model import (
    parse_data_schema, CONDITION_OPERATORS, CONDITION_TYPE_OPERATORS, MAPPING_MODES,
)


def _ds(nodes):
    return {"nodes": nodes, "trigger": {"nodeId": "MFStartNode", "type": "MANUAL"},
            "endNode": {"type": "END", "nodeId": "MFEndNode", "output": {"dataType": "STRING", "type": "OBJECT"}}}


def test_operator_enum_has_biz_where_values():
    assert "NOTNULL" in CONDITION_OPERATORS      # 真实值（不是 IS_NOT_NULL）
    assert "IS_NOT_NULL" not in CONDITION_OPERATORS
    for op in ("EQ", "NEQ", "LIKE", "NOTLIKE", "RLIKE", "LLIKE", "BETWEEN", "NOTBETWEEN",
               "IN", "NOTIN", "NULL", "ZERO", "NOTZERO"):
        assert op in CONDITION_OPERATORS
    # ★权威 OperatorEnum 共 22 个（前端 seeyon-biz-where 少 ZERO/NOTZERO）
    assert len(CONDITION_OPERATORS) == 22


def test_type_operator_matrix_matches_frontend():
    # 5.3.318 对账：BOOLEAN 支持 ZERO/NOTZERO（OperatorEnum size=0 全数值/布尔可用）
    assert CONDITION_TYPE_OPERATORS["BOOLEAN"] == frozenset({"EQ", "NEQ", "ZERO", "NOTZERO"})
    assert "BETWEEN" not in CONDITION_TYPE_OPERATORS["BOOLEAN"]
    assert "RLIKE" in CONDITION_TYPE_OPERATORS["STRING"]
    assert "LIKE" not in CONDITION_TYPE_OPERATORS["INTEGER"]
    assert "IN" in CONDITION_TYPE_OPERATORS["BIGINTEGER"]
    assert "NULL" in CONDITION_TYPE_OPERATORS["BIGINTEGER"]   # 5.3.318 补齐
    assert "ZERO" in CONDITION_TYPE_OPERATORS["INTEGER"]      # 5.3.318 补齐
    assert "ZERO" in CONDITION_TYPE_OPERATORS["DATETIME"]     # 5.3.318 补齐
    assert CONDITION_TYPE_OPERATORS["ATTACHMENT"] == frozenset({"NULL", "NOTNULL"})


def _cond_node(action, left_dt, op, right=None):
    """按真实样本结构（udc_microflow_info 4405407084014816629 实测）构造条件。"""
    rightParams = [] if right is None else right
    java = {"STRING": "java.lang.String", "BOOLEAN": "java.lang.Boolean",
            "INTEGER": "java.lang.Integer", "BIGINTEGER": "java.lang.Long",
            "DATETIME": "java.util.Date"}.get(left_dt, "java.lang.String")
    return {
        "type": "ACTIVITY", "nodeId": f"{action}_1", "caption": "查询", "actionType": action,
        "isCompleted": True, "output": {"dataType": "DTO", "type": "OBJECT"},
        "condition": [{"type": "GROUP", "uuid": "g1", "logicalOperator": "AND", "conditions": [
            {"type": "CONDITION", "uuid": "c1",
             "leftParam": {"id": f"X.Dto.f1", "type": "OBJECT", "javaType": java,
                           "dto": "_f1", "field": "f1", "desc": "f1",
                           "dataType": left_dt, "multiSelect": False},
             "operator": {"value": op, "desc": op},
             "rightParams": rightParams}]}],
    }


def test_valid_condition_passes():
    g = parse_data_schema(_ds([_cond_node("RETRIEVE", "STRING", "NOTNULL")]))
    assert g.status() == "PASS", g.errors


def test_invalid_operator_is_error():
    g = parse_data_schema(_ds([_cond_node("RETRIEVE", "STRING", "IS_NOT_NULL")]))
    assert g.status() == "FAIL"
    assert any("操作符非法" in e for e in g.errors)


def test_operator_type_mismatch_is_error():
    # BOOLEAN 不支持 LIKE
    g = parse_data_schema(_ds([_cond_node("RETRIEVE", "BOOLEAN", "LIKE",
                                          [{"type": "CONSTANT", "value": "true", "dataType": "BOOLEAN"}])]))
    assert g.status() == "FAIL"
    assert any("不匹配" in e for e in g.errors)


def test_notnull_with_rightparam_is_error():
    g = parse_data_schema(_ds([_cond_node("RETRIEVE", "STRING", "NOTNULL",
                                          [{"type": "CONSTANT", "value": "x", "dataType": "STRING"}])]))
    assert g.status() == "FAIL"
    assert any("无需 rightParams" in e for e in g.errors)


def test_between_needs_two_rightparams():
    g = parse_data_schema(_ds([_cond_node("RETRIEVE_ARRAY", "INTEGER", "BETWEEN",
                                          [{"type": "CONSTANT", "value": "1", "dataType": "INTEGER"}])]))
    assert g.status() == "FAIL"
    assert any("需 2 个 rightParams" in e for e in g.errors)
    ok = parse_data_schema(_ds([_cond_node("RETRIEVE_ARRAY", "INTEGER", "BETWEEN",
                                           [{"type": "CONSTANT", "value": "1", "desc": 1},
                                            {"type": "CONSTANT", "value": "9", "desc": 9}])]))
    assert ok.status() == "PASS", ok.errors


def test_mapping_mode_enum():
    assert MAPPING_MODES == frozenset({"REFERENCE", "CONSTANT"})
    assert "FieldCopy" not in MAPPING_MODES
    node = {
        "type": "ACTIVITY", "nodeId": "DATA_MAPPING_1", "caption": "数据转换", "actionType": "DATA_MAPPING",
        "isCompleted": True, "output": {"dataType": "DTO", "type": "ARRAY"},
        "mappingRule": {"uuid": "u0", "targetType": "ENTITY", "mappingRows": [
            {"uuid": "u1", "mappingMode": "REFERENCE", "targetField": {"path": [{"id": "b"}]},
             "value": {"reference": {"path": [{"id": "a"}]}}}]},
    }
    g = parse_data_schema(_ds([node]))
    assert g.status() == "PASS", g.errors


def test_empty_mappings_is_warning_not_error():
    node = {
        "type": "ACTIVITY", "nodeId": "DATA_MAPPING_1", "caption": "数据转换", "actionType": "DATA_MAPPING",
        "isCompleted": True, "output": {"dataType": "DTO", "type": "ARRAY"},
        "mappingRule": {"uuid": "u0", "targetType": "ENTITY", "mappingRows": []},
    }
    g = parse_data_schema(_ds([node]))
    assert g.status() == "UNVERIFIED"
    assert any("空转" in w for w in g.warnings)


def test_bad_mapping_mode_is_error():
    node = {
        "type": "ACTIVITY", "nodeId": "DATA_MAPPING_1", "caption": "数据转换", "actionType": "DATA_MAPPING",
        "isCompleted": True, "output": {"dataType": "DTO", "type": "ARRAY"},
        "mappingRule": {"uuid": "u0", "targetType": "ENTITY", "mappingRows": [
            {"uuid": "u1", "mappingMode": "FieldCopy", "targetField": {"path": [{"id": "b"}]},
             "value": {"reference": {"path": [{"id": "a"}]}}}]},
    }
    g = parse_data_schema(_ds([node]))
    assert g.status() == "FAIL"
    assert any("mappingMode" in e for e in g.errors)


def test_missing_mapping_rows_is_error():
    """后端权威：字段是 mappingRows，不是 mappings。"""
    node = {
        "type": "ACTIVITY", "nodeId": "DATA_MAPPING_1", "caption": "数据转换", "actionType": "DATA_MAPPING",
        "isCompleted": True, "output": {"dataType": "DTO", "type": "ARRAY"},
        "mappingRule": {"type": "Simple", "mappings": []},
    }
    g = parse_data_schema(_ds([node]))
    assert g.status() == "FAIL"
    assert any("mappingRows" in e for e in g.errors)
