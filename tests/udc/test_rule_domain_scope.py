"""规则域作用域约束的回归测试。

这些用例全部来自真实踩坑：
- 默认值域塞「设置值」(ASSIGN_VALUE) → 用户看到面板里是「默认值」，节点却是「设置值」
- 默认值域引用实体字段 → 表达式红字「变量在上下文中不存在」
- 条件用 `==` → 前端判非法
- 子微流程引用 type=1 前端微流程 → 「所选择xxx已失效」
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.udc.rule_domain_scope import (  # noqa: E402
    DOMAIN_HAS_ENTITY_START, DOMAIN_NODES, domain_of,
    validate_rule_scope, validate_sub_microflow_service,
)


def _schema(nodes, end=True):
    s = {"nodes": nodes}
    if end:
        s["endNode"] = {"nodeId": "MFEndNode", "type": "END",
                        "actionType": "END_NODE", "caption": "结束"}
    return s


def _act(action_type):
    return {"nodeId": "%s_x" % action_type, "type": "ACTIVITY",
            "actionType": action_type, "caption": action_type}


def _branch(if_nodes, cond_title="整数字段 == 1"):
    return {"nodeId": "BRANCH_x", "type": "BRANCH", "caption": "分支(1)",
            "conditions": [
                {"name": "CONDITION_if", "expression": {"title": cond_title},
                 "nodes": if_nodes},
                {"name": "CONDITION_el", "expression": None, "nodes": []},
            ]}


# ---------------------------------------------------------------- 域映射
def test_group_type_maps_to_domain():
    assert domain_of(1) == "VALIDATE"
    assert domain_of(3) == "DEFAULT_VALUE"
    assert domain_of(2) == "ASSIGN_VALUE"
    assert domain_of("VALIDATE") == "VALIDATE"
    assert domain_of(99) == "OTHER"


def test_default_value_domain_has_no_assign_value_node():
    """默认值域只有 分支/默认值/子微流程。"""
    assert DOMAIN_NODES["DEFAULT_VALUE"] == frozenset(
        {"BRANCH", "DEFAULT_VALUE", "SUB_MICROFLOW"})
    assert "ASSIGN_VALUE" not in DOMAIN_NODES["DEFAULT_VALUE"]


def test_assign_value_domain_has_no_default_value_node():
    assert DOMAIN_NODES["ASSIGN_VALUE"] == frozenset(
        {"BRANCH", "ASSIGN_VALUE", "SUB_MICROFLOW"})
    assert "DEFAULT_VALUE" not in DOMAIN_NODES["ASSIGN_VALUE"]


def test_validate_domain_nodes():
    assert DOMAIN_NODES["VALIDATE"] == frozenset(
        {"BRANCH", "ATTRIBUTE_UNIQUE", "ATTRIBUTE_REQUIRED",
         "SHOW_MESSAGE", "SUB_MICROFLOW"})


def test_default_value_domain_cannot_see_entity():
    assert DOMAIN_HAS_ENTITY_START["DEFAULT_VALUE"] is False
    assert DOMAIN_HAS_ENTITY_START["VALIDATE"] is True


# ---------------------------------------------------------------- 节点越域
def test_assign_value_node_rejected_in_default_value_domain():
    """★ 真实踩坑：我在默认值规则里放了「设置值」。"""
    errors = validate_rule_scope(_schema([_act("ASSIGN_VALUE")]), "DEFAULT_VALUE")
    assert errors, "默认值域放 ASSIGN_VALUE 必须被拦"
    assert "ASSIGN_VALUE" in errors[0]


def test_default_value_node_rejected_in_assign_value_domain():
    errors = validate_rule_scope(_schema([_act("DEFAULT_VALUE")]), "ASSIGN_VALUE")
    assert errors
    assert "DEFAULT_VALUE" in errors[0]


def test_default_value_node_rejected_in_validate_domain():
    errors = validate_rule_scope(_schema([_act("DEFAULT_VALUE")]), "VALIDATE")
    assert errors


def test_show_message_only_in_validate():
    assert not validate_rule_scope(_schema([_act("SHOW_MESSAGE")]), "VALIDATE")
    assert validate_rule_scope(_schema([_act("SHOW_MESSAGE")]), "DEFAULT_VALUE")


def test_legal_default_value_rule_passes():
    schema = _schema([_act("SUB_MICROFLOW"), _branch([_act("DEFAULT_VALUE")], "1 = 1")])
    assert validate_rule_scope(schema, "DEFAULT_VALUE") == []


def test_legal_validate_rule_passes():
    schema = _schema([_branch([_act("SHOW_MESSAGE")], "为空(文本字段)")])
    assert validate_rule_scope(schema, 1) == []


# ---------------------------------------------------------------- 实体字段可见性
def test_entity_field_token_rejected_in_default_value_domain():
    """★ 真实踩坑：默认值域表达式引用了 dto.dto.fInt。"""
    node = _act("DEFAULT_VALUE")
    node["attrs"] = [{"value": {"type": "Expression", "expression": {
        "title": "x", "schema": "{}", "tokens": [
            {"uid": "u1", "type": "VARIABLE", "value": "dto.dto.fInt", "desc": "整数字段"},
        ]}}}]
    errors = validate_rule_scope(_schema([node]), "DEFAULT_VALUE")
    assert any("dto.dto.fInt" in e for e in errors)


def test_entity_field_token_allowed_in_validate_domain():
    node = _act("ATTRIBUTE_REQUIRED")
    node["params"] = [{"uid": "u1", "type": "VARIABLE",
                       "value": "dto.dto.fText", "desc": "文本字段"}]
    assert validate_rule_scope(_schema([node]), "VALIDATE") == []


# ---------------------------------------------------------------- 运算符
def test_double_equals_rejected():
    """★ 真实踩坑：条件写成 `fInt == 1`，平台只认 `=`。"""
    schema = _schema([_branch([_act("DEFAULT_VALUE")], "整数字段 == 1")])
    errors = validate_rule_scope(schema, "DEFAULT_VALUE")
    assert any("==" in e for e in errors)


def test_single_equals_accepted():
    schema = _schema([_branch([_act("DEFAULT_VALUE")], "整数字段 = 1")])
    assert validate_rule_scope(schema, "DEFAULT_VALUE") == []


# ---------------------------------------------------------------- 子微流程
def test_frontend_microflow_rejected():
    """★ 真实踩坑：引用了 type=1 前端微流程「全量同步」，前端报「已失效」。"""
    errs = validate_sub_microflow_service({
        "id": "852569737663629194", "name": "MFFRONTENDPZCldG",
        "type": "CUSTOM",
    })
    assert any("MFFRONTEND" in e for e in errs)


def test_service_type_required():
    assert validate_sub_microflow_service({"id": "1", "name": "x", "type": "FRONTEND"})
    assert validate_sub_microflow_service({"id": "1", "name": "MFSERVICEabc", "type": "SERVICE"}) == []
    assert validate_sub_microflow_service({"id": "1", "name": "getProgressByPlan", "type": "CUSTOM"}) == []


def test_missing_mfservice_rejected():
    assert validate_sub_microflow_service(None)
