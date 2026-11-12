"""高频节点构造器的结构断言。

这些断言对应本轮实测出来的硬约束：
- CALL_APP_SERVICE 的 parameter.type 是**全限定名**
- 入参是 DTO 才要 mappingType=attrs，标量入参不要（实测 24 vs 15）
- 条件操作符的右参数个数由 22 项权威表决定
- 无出参的节点不能造假 output
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from components.udc.microflow.nodes import (  # noqa: E402
    call_app_service, change_entity, change_variable, condition, condition_group,
    create_entity, create_variable, custom_error, delete_entity, for_each,
    left_param, retrieve, retrieve_array, signature, sub_microflow,
)

ENT = {"name": "demoEntity", "caption": "演示实体", "fullName": "com.x.DemoEntity"}
APP = {"appId": "1", "appName": "demo-app", "caption": "演示应用",
       "inApp": True, "udcApp": True, "dynamicDependency": False}
# 真实场景里 structure 来自实体选择器；测试用最小合法形态
STRUCT = {
    "key": "com.x.domain.entity.Demo", "id": "com.x.dto.DemoDto",
    "label": "演示实体", "dataType": "DTO",
    "entity": "com.x.domain.entity.Demo", "dtoType": "MASTER_ENTITY",
    "udcApp": True, "fullName": "com.x.dto.DemoDto",
    "methodLegal": {"available": True, "complexCondition": True,
                    "seniorMethod": True, "serviceType": "NONE",
                    "interfaceClassFullName": None},
}
COND = condition(left_param("dto", "fInt"), "EQ", 1)
SP = {"type": "SelectParam", "selectParam": {"name": "_v1"}, "desc": "变量1"}


# ---- 条件 ----

def test_condition_fqn_operator_sizes():
    assert condition(left_param("d", "f"), "NULL")["rightParams"] == []
    assert len(condition(left_param("d", "f"), "EQ", 1)["rightParams"]) == 1
    assert len(condition(left_param("d", "f"), "BETWEEN", [1, 2])["rightParams"]) == 2


def test_condition_rejects_unknown_operator():
    with pytest.raises(ValueError):
        condition(left_param("d", "f"), "XXX", 1)


def test_condition_rejects_wrong_arity():
    with pytest.raises(ValueError):
        condition(left_param("d", "f"), "EQ")
    with pytest.raises(ValueError):
        condition(left_param("d", "f"), "NULL", 1)
    with pytest.raises(ValueError):
        condition(left_param("d", "f"), "BETWEEN", 1)


def test_condition_group_fills_logical_operator():
    """GROUP 内第 2 个条件起 logicalOperator 必填（后端 checkConditionLegal）。"""
    g = condition_group([condition(left_param("d", "a"), "EQ", 1),
                         condition(left_param("d", "b"), "EQ", 2)])
    assert g["type"] == "GROUP"
    assert g["logicalOperator"] == "AND"
    assert "logicalOperator" in g["conditions"][1]


def test_condition_group_rejects_empty():
    with pytest.raises(ValueError):
        condition_group([])


# ---- 查询 / 写 ----

def test_retrieve_carries_selector_fields():
    """RETRIEVE 的 app/structure/title/scope/selectType 全来自选择器，必须原样带上。"""
    n = retrieve(APP, STRUCT, title="演示实体_1", condition_=COND)
    assert n["actionType"] == "RETRIEVE"
    assert n["title"] == "演示实体_1"
    assert n["selectType"] == "DTO"
    assert n["scope"] == "OBJECT"
    assert n["methodLegal"] == STRUCT["methodLegal"]
    assert n["output"]["name"].startswith("_RETRIEVE_")
    assert n["output"]["dataType"] == "DTO"
    assert n["condition"]["operator"] == "EQ"


def test_retrieve_rejects_handmade_structure():
    """structure 缺 fullName 必须 fail-closed —— 不能手拼实体标识。"""
    with pytest.raises(ValueError):
        retrieve(APP, {"label": "手拼"}, title="x", condition_=COND)
    with pytest.raises(ValueError):
        retrieve({}, STRUCT, title="x", condition_=COND)


def test_retrieve_requires_condition_or_value():
    with pytest.raises(ValueError):
        retrieve(APP, STRUCT, title="x", fetch_type="CONDITION")


def test_retrieve_array_uses_variable_title():
    """★ RETRIEVE_ARRAY 字段名是 variableTitle，不是 title（523 个真实节点一致）。"""
    n = retrieve_array(APP, STRUCT, variable_title="演示实体_1", condition_=COND)
    assert n["variableTitle"] == "演示实体_1"
    assert "title" not in n
    assert n["output"]["dataType"] == "ARRAY"
    assert n["output"]["name"].startswith("_RETRIEVE_ARRAY_")


def test_change_entity_uses_select_param_not_mapping_type():
    """★ 真实必填是 selectParam + title；按反编译写 mappingType 会 100% 误杀。"""
    n = change_entity(SP, title="演示实体_1", condition_=COND)
    assert n["selectParam"] == SP
    assert n["title"] == "演示实体_1"
    assert "mappingType" not in n


def test_write_nodes_have_no_output():
    """CHANGE/CREATE/DELETE 无出参 —— 不许造假 output。"""
    # ★ 前端权威必填：CREATE_ENTITY 要 app/structure/value/title，
    #   DELETE_ENTITY 要 app/structure/condition/title
    for n in (change_entity(SP, title="t", condition_=COND),
              create_entity(ENT, app=APP, structure=STRUCT, title="t"),
              delete_entity(ENT, app=APP, structure=STRUCT, condition=COND, title="t")):
        assert n["output"] is None


# ---- 自定义服务 ----

def test_signature_builds_fqn_types():
    sig = signature("com.x.Dto", "java.lang.String")
    assert sig["parameter"]["type"] == "com.seeyon.boot.transport.SingleRequest"
    assert sig["parameter"]["item"]["itemType"] == "com.x.Dto"
    assert sig["returnValue"]["item"]["itemType"] == "java.lang.String"


def test_call_app_service_dto_requires_attrs():
    n = call_app_service(APP, dict(signature("com.x.Dto", "java.lang.String"),
                                   fullName="com.x.S.m", implClass="com.x.S"),
                         mapping_type="attrs")
    assert n["mappingType"] == "attrs"
    # type 是全限定名，不是短名
    assert n["selectMethod"]["parameter"]["type"].endswith("SingleRequest")


def test_call_app_service_scalar_needs_no_mapping_type():
    """标量入参不要求 mappingType（实测 15/39 真实节点如此）。"""
    n = call_app_service(APP, dict(signature("java.lang.Long", "java.lang.String"),
                                   fullName="com.x.S.m", implClass="com.x.S"))
    assert n.get("mappingType") is None


def test_call_app_service_rejects_missing_signature():
    """itemType 是作用域键，缺了必须 fail-closed，不能猜。"""
    with pytest.raises(ValueError):
        call_app_service(APP, {"fullName": "com.x.S.m"})


def test_call_app_service_rejects_empty_app():
    with pytest.raises(ValueError):
        call_app_service({}, dict(signature("com.x.D", "java.lang.String"),
                                  fullName="com.x.S.m"))


# ---- 子流程 / 变量 / 循环 ----

def test_sub_microflow_rejects_frontend_type():
    with pytest.raises(ValueError):
        sub_microflow({"id": "1", "type": 1})
    n = sub_microflow({"id": "1", "type": 0})
    assert n["output"]["name"].startswith("_SUB_MICROFLOW_")


def test_create_variable_uses_real_field_names():
    """★ 真实必填 paramType/title/dataType；不是 metaDataType/otherType（100% 误杀）。"""
    n = create_variable("变量_1", "BOOLEAN")
    assert n["title"] == "变量_1"
    assert n["paramType"] == "BASIC"
    assert n["dataType"] == "BOOLEAN"
    assert n["output"]["name"].startswith("_CREATE_VARIABLE_")
    assert n["output"]["javaType"] == "java.lang.Boolean"


def test_create_variable_requires_title():
    with pytest.raises(ValueError):
        create_variable("")


def test_change_variable_needs_select_param():
    assert change_variable(SP, value="x")["output"] is None
    with pytest.raises(ValueError):
        change_variable({})


def test_for_each_nests_children():
    inner = custom_error("boom")
    n = for_each("list", [inner])
    assert n["nodes"][0]["nodeId"] == inner["nodeId"]
    assert n["output"]["name"].startswith("_FOR_")
