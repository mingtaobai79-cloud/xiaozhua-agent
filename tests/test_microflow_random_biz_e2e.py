"""随机业务场景端到端：生成 → 双层校验 → 反向注入。

场景：设备巡检单
  查询待巡检设备 → 分支(已超期/未超期) → 创建映射组 → 映射操作取键
  → 计数循环(内含类型转换) → 自定义错误
"""
from __future__ import annotations

import copy
import json
import random
import string
from pathlib import Path

import pytest

from components.udc.microflow.build import build_schema, make_node, param, validate_schema
from components.udc.microflow_constraints import validate_node_fields
from components.udc.microflow_ui_constraints import validate_schema_ui

ROOT = Path(__file__).resolve().parents[1]
APP_ID = "9000000000000000001"
APP_NAME = "datamigration9000000000000000001"
ENTITY_DTO = "com.seeyon.%s.dto.XzhInspectDto" % APP_NAME


def _rid(n=6):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(n))


def _ref(node_id, action, name, desc, data_type="DTO", java_type=None):
    return {
        "description": desc, "dataType": data_type, "type": "OBJECT",
        "javaType": java_type or ENTITY_DTO, "name": name, "outputName": name,
        "position": "parent",
        "nodeInfo": {"nodeId": node_id, "type": "ACTIVITY", "actionType": action},
        "key": "%s_%s" % (name, action), "iconKey": "LinedSearch",
        "parentLabel": "", "disabled": False, "isLeaf": True,
    }


@pytest.fixture(scope="module")
def schema():
    """设备巡检单流程（真实生成器产出）。"""
    nodes = []

    ret_out = "_RETRIEVE_" + _rid()
    n_retrieve = make_node(
        "RETRIEVE", caption="查询待巡检设备",
        output=param(ret_out, "DTO", "待巡检设备", java_type=ENTITY_DTO),
        app={"appId": APP_ID, "appName": APP_NAME, "caption": "设备巡检",
             "inApp": True, "udcApp": True, "dynamicDependency": False},
        structure={"key": ENTITY_DTO, "id": ENTITY_DTO, "label": "XzhInspect",
                   "dataType": "DTO", "dtoType": "MASTER_ENTITY", "udcApp": True,
                   "fullName": ENTITY_DTO},
        selectType="CONDITION", scope="ONE", title="待巡检设备", methodLegal=None,
        condition={"items": [{"leftParam": {"field": "inspectStatus"}, "operator": "=",
                              "rightParams": {"type": "Simple", "simple": "PENDING",
                                              "desc": "PENDING"}}]},
    )
    nodes.append(n_retrieve)

    branch = {"nodeId": "BRANCH_" + _rid(), "name": None, "type": "BRANCH",
              "caption": "是否超期", "description": None, "runAfter": None,
              "input": None, "output": None, "isCompleted": True,
              "actionType": "BRANCH", "conditions": []}

    cond_overdue = {"nodeId": "CONDITION_" + _rid(), "type": "CONDITION",
                    "caption": "已超期", "description": None, "isCompleted": True,
                    "nodes": []}
    cond_overdue["nodes"].append(make_node(
        "CHANGE_ENTITY", caption="标记已超期",
        output=param("_CHANGE_ENTITY_" + _rid(), "BOOLEAN", "更新结果",
                     java_type="java.lang.Boolean"),
        selectParam=_ref(n_retrieve["nodeId"], "RETRIEVE", ret_out, "待巡检设备"),
        mappingType="attrs", title="更新结果",
        attrs=[{"attrType": {"id": ENTITY_DTO + ".inspectStatus",
                             "name": "inspectStatus", "desc": "巡检状态",
                             "dataType": "STRING", "type": "OBJECT",
                             "javaType": "java.lang.String"},
                "value": {"type": "Simple", "simple": "OVERDUE", "desc": "OVERDUE"}}],
    ))

    cond_normal = {"nodeId": "CONDITION_" + _rid(), "type": "CONDITION",
                   "caption": "未超期", "description": None, "isCompleted": True,
                   "nodes": []}
    cond_normal["nodes"].append(make_node(
        "CREATE_ENTITY", caption="插入巡检记录",
        output=param("_CREATE_ENTITY_" + _rid(), "DTO", "新增记录", java_type=ENTITY_DTO),
        app={"appId": APP_ID, "appName": APP_NAME, "caption": "设备巡检",
             "inApp": True, "udcApp": True, "dynamicDependency": False},
        structure={"key": ENTITY_DTO, "id": ENTITY_DTO, "label": "XzhInspect",
                   "dataType": "DTO", "dtoType": "MASTER_ENTITY", "udcApp": True,
                   "fullName": ENTITY_DTO},
        mappingType="attrs", title="新增记录",
        attrs=[{"attrType": {"id": ENTITY_DTO + ".inspectStatus",
                             "name": "inspectStatus", "desc": "巡检状态",
                             "dataType": "STRING", "type": "OBJECT",
                             "javaType": "java.lang.String"},
                "value": {"type": "Simple", "simple": "NORMAL", "desc": "NORMAL"}}],
    ))

    branch["conditions"] = [cond_overdue, cond_normal]
    nodes.append(branch)

    map_out = "_CREATE_MAP_" + _rid()
    n_map = make_node(
        "CREATE_MAP", caption="巡检结果摘要",
        output={"dataType": "MAP", "javaType": "java.util.Map", "id": None,
                "type": "OBJECT", "desc": "巡检摘要", "appName": None,
                "dtoType": None, "udcApp": None,
                "generics": {"keyType": {"dataType": "String"},
                             "valueType": {"dataType": "Object",
                                           "javaType": "java.lang.Object"}},
                "name": map_out},
        title="巡检摘要",
        entries=[{"key": {"type": "Simple", "simple": "deviceNo", "desc": "deviceNo"},
                  "value": {"type": "Simple", "simple": "DEV-001", "desc": "DEV-001"}}],
        generics={"keyType": {"dataType": "String"},
                  "valueType": {"dataType": "Object", "javaType": "java.lang.Object"}},
    )
    nodes.append(n_map)

    n_mapop = make_node(
        "MAP_OPERATION", caption="取设备编号",
        output=param("_MAP_OPERATION_" + _rid(), "STRING", "设备编号",
                     java_type="java.lang.String"),
        selectMap=_ref(n_map["nodeId"], "CREATE_MAP", map_out, "巡检摘要",
                       data_type="MAP", java_type="java.util.Map"),
        operationType="GET",
        theKey={"type": "Simple", "simple": "deviceNo", "desc": "deviceNo"},
        paramType="BASIC", basic={"key": "STRING", "dataType": "STRING"},
        structure={"key": "STRING", "dataType": "STRING",
                   "fullName": "java.lang.String"},
        arrayOrObject="OBJECT", nullHandling="TERMINATION",
        nullPromptMessage={"type": "Simple", "simple": "未取到设备编号",
                           "desc": "未取到设备编号"},
        title="设备编号", dataType="STRING",
        generics={"keyType": {"dataType": "String"},
                  "valueType": {"dataType": "Object", "javaType": "java.lang.Object"}},
    )
    nodes.append(n_mapop)

    for_out = "_FOR_" + _rid()
    n_for = {"nodeId": "For_" + _rid(), "type": "FOR", "caption": "重试3次",
             "description": None, "runAfter": None, "foreach": None,
             "isCompleted": True,
             "forStart": {"type": "Simple", "simple": 1, "desc": 1},
             "forEnd": {"type": "Simple", "simple": 3, "desc": 3},
             "forStep": 1, "operator": "<=", "targetName": "重试计数",
             "output": {"id": "", "dataType": "INTEGER", "type": "OBJECT",
                        "desc": "重试计数", "javaType": "java.lang.Integer",
                        "name": for_out},
             "nodes": []}
    n_for["nodes"].append(make_node(
        "CONVERT_DATA", caption="编号转整数",
        output={"name": "_CONVERT_DATA_" + _rid(), "dataType": "String",
                "type": "Object", "desc": "转换结果", "javaType": ""},
        convertType={"value": "String2Integer", "key": "String2Integer",
                     "dataType": "Integer", "type": "Object", "desc": "文本转整数"},
        selectParam=_ref(n_mapop["nodeId"], "MAP_OPERATION",
                         n_mapop["output"]["name"], "设备编号",
                         data_type="STRING", java_type="java.lang.String"),
        title="转换结果",
    ))
    nodes.append(n_for)

    nodes.append(make_node("CUSTOM_ERROR", caption="超期告警", output=None, input=None,
                           errorType="GLOBAL",
                           error={"type": "Simple", "simple": "设备已超期",
                                  "desc": "设备已超期"}))

    return build_schema({"trigger_type": "MANUAL", "input": None, "output": None,
                         "nodes": nodes}, app_id=APP_ID)


def _find(schema, action):
    out = []

    def walk(ns):
        for n in ns or []:
            if (n.get("actionType") or n.get("type")) == action:
                out.append(n)
            walk(n.get("nodes"))
            for c in n.get("conditions") or []:
                walk(c.get("nodes"))

    walk(schema.get("nodes"))
    return out


# ---------------------------------------------------------------- 正向

def test_generated_schema_passes_structure_validation(schema):
    assert validate_schema(schema) == []


def test_generated_schema_passes_ui_validation(schema):
    assert validate_schema_ui(schema) == []


def test_generated_schema_has_expected_topology(schema):
    actions = [n.get("actionType") or n.get("type") for n in schema["nodes"]]
    assert actions == ["RETRIEVE", "BRANCH", "CREATE_MAP", "MAP_OPERATION",
                       "FOR", "CUSTOM_ERROR"]


def test_branch_children_nested(schema):
    branch = _find(schema, "BRANCH")[0]
    assert len(branch["conditions"]) == 2
    assert len(branch["conditions"][0]["nodes"]) == 1
    assert branch["conditions"][0]["nodes"][0]["actionType"] == "CHANGE_ENTITY"
    assert branch["conditions"][1]["nodes"][0]["actionType"] == "CREATE_ENTITY"


def test_for_body_nested(schema):
    n_for = _find(schema, "FOR")[0]
    assert len(n_for["nodes"]) == 1
    assert n_for["nodes"][0]["actionType"] == "CONVERT_DATA"


# ---------------------------------------------------------------- 反向

def test_convert_type_without_value_caught(schema):
    s = copy.deepcopy(schema)
    n = _find(s, "CONVERT_DATA")[0]
    n["convertType"] = {"key": "String2Integer", "dataType": "Integer"}
    assert validate_schema_ui(s)


def test_map_operation_get_without_key_caught(schema):
    s = copy.deepcopy(schema)
    _find(s, "MAP_OPERATION")[0].pop("theKey", None)
    assert validate_schema_ui(s)


def test_map_operation_put_without_entries_caught(schema):
    s = copy.deepcopy(schema)
    n = _find(s, "MAP_OPERATION")[0]
    n["operationType"] = "PUT"
    n.pop("entries", None)
    assert validate_schema_ui(s)


def test_for_operator_domain_caught(schema):
    s = copy.deepcopy(schema)
    _find(s, "FOR")[0]["operator"] = "!="
    assert validate_schema_ui(s)


def test_for_step_type_caught(schema):
    s = copy.deepcopy(schema)
    _find(s, "FOR")[0]["forStep"] = "1"
    assert validate_schema_ui(s)


def test_custom_error_position_missing_caught(schema):
    s = copy.deepcopy(schema)
    _find(s, "CUSTOM_ERROR")[0]["errorType"] = "POSITION"
    assert validate_schema_ui(s)


def test_activity_type_must_be_activity_caught(schema):
    s = copy.deepcopy(schema)
    _find(s, "CREATE_MAP")[0]["type"] = "CREATE_MAP"
    assert validate_schema_ui(s)


def test_break_at_root_caught(schema):
    s = copy.deepcopy(schema)
    s["nodes"].append({"nodeId": "BREAK_x", "type": "BREAK", "actionType": "BREAK",
                       "caption": "跳出循环(1)", "isCompleted": True})
    assert validate_schema_ui(s)


def test_break_inside_loop_allowed(schema):
    s = copy.deepcopy(schema)
    _find(s, "FOR")[0]["nodes"].append(
        {"nodeId": "BREAK_y", "type": "BREAK", "actionType": "BREAK",
         "caption": "跳出循环(1)", "isCompleted": True})
    assert validate_schema_ui(s) == []


def test_create_map_missing_title_caught_by_structure_layer(schema):
    s = copy.deepcopy(schema)
    n = _find(s, "CREATE_MAP")[0]
    n.pop("title", None)
    assert validate_node_fields("CREATE_MAP", n)
