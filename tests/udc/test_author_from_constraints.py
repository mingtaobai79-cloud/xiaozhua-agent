"""终态验证测试：用权威约束从零手写一个完整微流程，本地校验须 PASS。

这是"能自己完整写出一个需求且没问题"的验收测试——不依赖任何在线样本或前端抓包，
仅凭 components/udc 的约束模型（反编译权威）构造，须通过 parse_data_schema 校验。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.microflow_model import parse_data_schema
from components.udc.microflow_constraints import validate_node_fields

APP = "8704025620829192834"
APPNAME = f"datamigration{APP}"
ENT_ID = "474806313816300867"
ENT_FULL = f"com.seeyon.{APPNAME}.domain.entity.XzhExp950795"
DTO = f"com.seeyon.{APPNAME}.dto.XzhExp950795Dto"

APP_OBJ = {"appId": APP, "appName": APPNAME, "caption": "智能项目管理平台", "inApp": True,
           "udcApp": True, "dynamicDependency": False}
STRUCT = {"key": ENT_FULL, "id": DTO, "label": "小爪实验实体950795V2", "dataType": "DTO",
          "entity": ENT_FULL, "dtoType": "MASTER_ENTITY", "udcApp": True, "fullName": DTO,
          "relationEntity": ENT_ID,
          "methodLegal": {"available": True, "complexCondition": True, "seniorMethod": True,
                          "serviceType": "NONE", "interfaceClassFullName": None}}
OUT_ARR = {"dataType": "DTO", "type": "ARRAY"}
OUT_INT = {"dataType": "INTEGER", "type": "OBJECT"}


def _field(f):
    return {"id": f"{DTO}.{f}", "field": f, "desc": f, "dataType": "STRING",
            "entityId": ENT_ID, "entityFullName": ENT_FULL}


def _cond(field, op, value=None):
    """按真实样本结构（udc_microflow_info 4405407084014816629 实测）构造条件。"""
    rp = ([] if op in ("NULL", "NOTNULL", "ZERO", "NOTZERO")
          else [{"type": "CONSTANT", "value": value, "desc": value}])
    return [{"type": "GROUP", "uuid": "g1", "conditions": [{
        "type": "CONDITION",
        "leftParam": {"id": f"{DTO}.{field}", "type": "OBJECT", "javaType": "java.lang.String",
                      "dto": f"_{field}", "field": field, "desc": field,
                      "dataType": "STRING", "multiSelect": False},
        "rightParams": rp, "operator": {"value": op, "desc": op}, "uuid": "c1"}]}]


def _authored_schema():
    """仅凭权威约束从零构造的完整微流程。"""
    return {
        "trigger": {"nodeId": "MFStartNode", "caption": "入参定义", "type": "ACTIVITY",
                    "actionType": "FLOW_INPUT", "paramType": "BASIC", "desc": "同步任务ID",
                    "output": {"dataType": "STRING", "type": "OBJECT"}},
        "endNode": {"nodeId": "MFEndNode", "caption": "出参定义", "type": "ACTIVITY",
                    "actionType": "FLOW_OUTPUT", "paramType": "BASIC", "desc": "执行结果",
                    "output": {"dataType": "STRING", "type": "OBJECT"}},
        "nodes": [
            {"type": "ACTIVITY", "actionType": "RETRIEVE_ARRAY", "nodeId": "RETRIEVE_ARRAY_aaa111",
             "caption": "查询多条数据(1)", "isCompleted": True, "fetchType": "CONDITION",
             "pageSearch": "false", "size": 100, "condition": _cond("expText", "EQ", "x"),
             "selectType": "DTO", "scope": "OBJECT", "methodLegal": STRUCT["methodLegal"],
             "variableTitle": "实验列表", "output": OUT_ARR, "app": APP_OBJ, "structure": STRUCT},
            {"type": "ACTIVITY", "actionType": "DATA_MAPPING", "nodeId": "DATA_MAPPING_bbb222",
             "caption": "数据转换(1)", "isCompleted": True, "targetType": "ENTITY",
             "output": OUT_ARR, "app": APP_OBJ, "structure": STRUCT,
             "mappingRule": {"uuid": "mr1", "targetType": "ENTITY", "mappingRows": [
                 {"uuid": "r1", "targetField": {"path": [_field("expText")]}, "mappingMode": "REFERENCE",
                  "value": {"reference": {"path": [_field("expText")]}}},
                 {"uuid": "r2", "targetField": {"path": [_field("expNum")]}, "mappingMode": "CONSTANT",
                  "value": {"constant": {"constantType": "SIMPLE", "simple": "0"}}}]}},
            {"type": "ACTIVITY", "actionType": "DELETE_ENTITY", "nodeId": "DELETE_ENTITY_ccc333",
             "caption": "删除数据(1)", "isCompleted": True, "deleteType": "CONDITION",
             "condition": _cond("expFlag", "EQ", "false"),
             "title": "删除数据",   # ★ 前端权威必填
             "output": OUT_INT, "app": APP_OBJ, "structure": STRUCT},
        ],
    }


def test_authored_microflow_passes_validation():
    """从零手写的完整微流程必须本地校验 PASS（终态验收）。"""
    g = parse_data_schema(json.dumps(_authored_schema(), ensure_ascii=False))
    assert g.status() == "PASS", (g.errors, g.warnings)
    assert g.activity_count == 3
    assert g.activity_ids() == ["RETRIEVE_ARRAY_aaa111", "DATA_MAPPING_bbb222", "DELETE_ENTITY_ccc333"]


def test_authored_nodes_pass_backend_required_fields():
    for n in _authored_schema()["nodes"]:
        assert validate_node_fields(n["actionType"], n) == [], n["actionType"]


def test_authored_schema_uses_authoritative_enums_only():
    """DATA_MAPPING 用 mappingRows/REFERENCE/ENTITY（非 mappings/FieldCopy/ENTITY_OBJECT）。"""
    mr = _authored_schema()["nodes"][1]["mappingRule"]
    assert mr["targetType"] == "ENTITY"
    assert "mappingRows" in mr and "mappings" not in mr
    assert all(r["mappingMode"] in ("REFERENCE", "CONSTANT") for r in mr["mappingRows"])
