"""表达式公用层 · 写入面（schema 绑定 / DTO / 落位映射）的实证锁定。

这些断言对应 2026-10-23 的 LIVE 实测：
  - 变量只给 paramId 会报 FORMULA_6058 → 必须绑定 schemas
  - schemas 放**实体根节点**没用，必须放**字段节点**
  - resultTypeInfo 必须等于字段 dataType
  - 两条值链互斥（默认值 / 计算值写不同的列）
  - 字段集没有计算值入口（显式登记为 ABSENT）
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.expression import (  # noqa: E402
    bind_schemas,
    build_constant_token,
    build_function_token,
    build_operator_token,
    build_save_dto,
    build_system_token,
    build_variable_token,
    check_binding,
    columns_for,
    get_slot,
    required_param_ids,
    result_type_for,
    slots_for_domain,
    validate_against_data_type,
    validate_save_dto,
    validate_slot_consistency,
    variable_tokens,
)
from components.udc.expression.mapping import ABSENT_SLOTS  # noqa: E402
from components.udc.expression.schema_binding import MINIMAL_SCHEMA_KEYS  # noqa: E402
from components.udc.expression.token import validate_token  # noqa: E402

APP = "8704025620829192834"
ENTITY = "-2537349473285092530"
F03INT_PID = "-6040618203145140416"


# ---------------------------------------------------------------- schema 绑定
def _node(name, pid, dtype, cat="Attr"):
    return {"name": name, "description": name, "type": dtype, "selectable": True,
            "enableDataI18n": False,
            "uniformityParams": {"paramId": str(pid), "paramCategory": cat,
                                 "extensionProperties": None,
                                 "pageNodeExtension": None}}


def _roots():
    """模拟 /expression/schema 返回：实体根 + properties 里的字段。"""
    return [{
        "name": "ysFull6956", "description": "小爪验收实体全量", "type": "OBJECT",
        "selectable": True, "enableDataI18n": False,
        "uniformityParams": {"paramId": ENTITY, "paramCategory": "Entity",
                             "extensionProperties": None, "pageNodeExtension": None},
        "properties": [
            _node("f03int", F03INT_PID, "INTEGER"),
            _node("f04bigint", "4894426588496688945", "BIGINTEGER"),
            _node("f12doc", "5473039530048657965", "STRING"),
        ],
    }]


def test_variable_tokens_found_including_function_args():
    inner = build_variable_token(F03INT_PID, "f03int", "整数字段")
    tokens = [build_function_token("roundOff", "四舍五入", [[inner]])]
    assert len(variable_tokens(tokens)) == 1
    assert required_param_ids(tokens) == (F03INT_PID,)


def test_bind_schemas_returns_entity_tree_with_field_in_properties():
    """★★ 2026-10-23 更正：必须返回**实体 OBJECT 树**，字段挂在 properties 里。

    旧断言「放字段节点、不放实体根」是错的 —— 那种扁平形态能过
    check/transform，但页面回显报 FORMULA_6058「变量:xxx 在上下文中不存在」。
    三维对照见 tests/udc/test_expression_schema_shape.py。
    """
    tokens = [build_variable_token(F03INT_PID, "f03int", "整数字段",
                                   entity_name="ysFull6956", entity_desc="小爪验收实体全量"),
              build_operator_token("+"),
              build_variable_token(F03INT_PID, "f03int", "整数字段",
                                   entity_name="ysFull6956", entity_desc="小爪验收实体全量")]
    schemas = bind_schemas(tokens, _roots())
    assert len(schemas) == 1
    root = schemas[0]
    assert root["name"] == "ysFull6956"
    assert root["type"] == "OBJECT"
    assert [p["name"] for p in root["properties"]] == ["f03int"]
    assert root["properties"][0]["uniformityParams"]["paramId"] == F03INT_PID


def test_minimal_node_keeps_only_required_keys():
    """树形态下：根有 properties，子节点只留最小键。"""
    tokens = [build_variable_token(F03INT_PID, "f03int", "整数字段",
                                   entity_name="ysFull6956", entity_desc="小爪验收实体全量")]
    root = bind_schemas(tokens, _roots())[0]
    assert "properties" in root
    child = root["properties"][0]
    assert set(child) <= set(MINIMAL_SCHEMA_KEYS)
    assert "uniformityParams" in child


def test_bind_schemas_dedupes_same_variable():
    t = build_variable_token(F03INT_PID, "f03int", "整数字段")
    assert len(bind_schemas([t, build_operator_token("+"), t], _roots())) == 1


def test_bind_schemas_raises_when_node_missing():
    tokens = [build_variable_token("999", "ghost", "不存在")]
    try:
        bind_schemas(tokens, _roots())
    except ValueError as exc:
        assert "999" in str(exc)
    else:
        raise AssertionError("缺节点必须抛错，不能静默放过（否则 FORMULA_6058）")


def test_check_binding_reports_unbound_variable():
    tokens = [build_variable_token(F03INT_PID, "f03int", "整数字段",
                                   entity_name="ysFull6956", entity_desc="小爪验收实体全量")]
    assert check_binding(tokens, []) != []          # 没绑定 → 报错
    assert check_binding(tokens, bind_schemas(tokens, _roots())) == []


def test_system_token_needs_no_schema_binding():
    """SYSTEM 走全局变量表，不进 schemas。"""
    tokens = [build_system_token("system.currentDate", "系统日期")]
    assert required_param_ids(tokens) == ()
    assert bind_schemas(tokens, _roots()) == []
    assert validate_token(tokens[0]) == []


# ---------------------------------------------------------------- DTO / 类型
def test_result_type_mapping_matches_data_type():
    assert result_type_for("DOCUMENTNUMBER") == "STRING"
    assert result_type_for("BIGINTEGER") == "BIGINTEGER"
    assert result_type_for("CURRENCY") == "DECIMAL"
    assert result_type_for("CTPENUM") == "LONG"
    assert result_type_for("ENUM") == "LONG"
    assert result_type_for("BOOLEAN") == "BOOLEAN"


def test_unknown_data_type_raises():
    try:
        result_type_for("WHATEVER")
    except ValueError as exc:
        assert "WHATEVER" in str(exc)
    else:
        raise AssertionError("未知类型必须抛错，不能返回原值蒙混")


def test_result_type_mismatch_detected():
    """resultTypeInfo != 字段 dataType 必报 FORMULA_6901。"""
    dto = build_save_dto([build_constant_token("1")], result_type="STRING")
    assert validate_against_data_type(dto, "BIGINTEGER") != []
    assert validate_against_data_type(dto, "DOCUMENTNUMBER") == []


def test_save_dto_requires_terminal_and_nonempty_tokens():
    dto = build_save_dto([build_constant_token("1")], result_type="STRING")
    assert validate_save_dto(dto) == []
    bad = dict(dto)
    bad["tokens"] = []
    assert any("不能为空" in e for e in validate_save_dto(bad))
    bad2 = dict(dto)
    bad2["terminalSupportType"] = "DESIGN"
    assert any("terminalSupportType" in e for e in validate_save_dto(bad2))


def test_save_dto_rejects_variable_without_param_id():
    bad = {"uid": "u", "type": "VARIABLE", "value": "f03int", "desc": "x"}
    dto = build_save_dto([bad], result_type="INTEGER")
    assert any("paramId" in e for e in validate_save_dto(dto))


# ---------------------------------------------------------------- 落位映射
def test_entity_has_two_distinct_slots():
    slots = slots_for_domain("entity")
    purposes = {s.purpose for s in slots}
    assert {"default_value", "calculated_value", "scope"} <= purposes
    d = get_slot("entity", "default_value")
    c = get_slot("entity", "calculated_value")
    assert d.design_column != c.design_column, "两条值链必须写不同的列"
    assert c.calculate_state == "COMPUTE"


def test_setting_has_no_calculated_value_slot():
    """★ 字段集只有默认值，没有计算值 —— 曾经写错导致页面全空。"""
    assert ("setting", "calculated_value") in ABSENT_SLOTS
    try:
        get_slot("setting", "calculated_value")
    except KeyError as exc:
        assert "不存在" in str(exc)
    else:
        raise AssertionError("字段集的计算值槽位必须显式判为不存在")


def test_columns_for_returns_design_runtime_pair():
    assert columns_for("entity", "default_value") == (
        "default_value_expr_design", "default_value_expr_runtime")
    assert columns_for("entity", "calculated_value") == (
        "expression_design_data", "expression_runtime_data")
    # 单列槽位
    assert columns_for("entity", "scope") == ("value_scope_expression",)


def test_slot_param_types_are_registered():
    """每个落位点的 paramType 必须在 @ParamLoadService 注册表里。"""
    assert validate_slot_consistency() == []


# ---------------------------------------------------------------- 两条链互斥
def test_default_and_calc_use_different_column_pairs():
    """公用层的判据：同一字段不该同时有默认值表达式和计算值表达式。"""
    dpair = columns_for("entity", "default_value")
    cpair = columns_for("entity", "calculated_value")
    assert not set(dpair) & set(cpair), "两条值链的列不能有交集"
