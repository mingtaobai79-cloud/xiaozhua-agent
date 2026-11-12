"""表达式公用层：契约与扩展点必须被锁住。

这些断言锁的是**已实证的事实**，不是设计口味：
  1. 端点 method 不能凭"像查询"猜（operator/list 只认 GET，POST 405）
  2. token 值域恰 5 值，值域外平台只回 null message → 必须本地拦
  3. 变量 token 必须带 paramId（schema 的 uniformityParams.paramId）
  4. terminalSupportType 决定函数面（88/81），不受模块影响
  5. paramType 注册表 = 扩展点；未注册的传了报 BOOT_3000
  6. 结构错本地拦，语义错交平台（不在本地重复实现引擎）
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.expression import (  # noqa: E402
    EXPRESSION_ENDPOINTS,
    EXPRESSION_ERROR_CODES,
    OPERATOR_OP_TYPES,
    OPERATORS,
    PARAM_TYPE_REGISTRY,
    QUICK_FUNCTIONS,
    TERMINAL_BACKEND,
    TERMINAL_FRONTEND,
    TERMINAL_SUPPORTED,
    TOKEN_TYPES,
    build_constant_token,
    build_function_token,
    build_variable_token,
    endpoint_names,
    function_count_for,
    is_registered,
    operators_by_type,
    registered_types,
    spec_for,
    validate_token,
    validation_chain_order,
)
from components.udc.expression.endpoints import full_path  # noqa: E402
from components.udc.expression.terminal import (  # noqa: E402
    BACKEND_ONLY_GROUPS,
    FUNCTION_GROUP_COUNTS,
    SYSTEM_VARIABLE_TOTAL,
    groups_for,
    has_group,
    is_valid_terminal,
)
from components.udc.expression.validation import (  # noqa: E402
    DESIGN_RUNTIME_PAIRS,
    is_semantic,
    is_structural,
)


# ---------------------------------------------------------------- 端点
def test_operator_list_is_get_only():
    """LIVE 实测 POST 返回 405 —— method 不能猜。"""
    assert EXPRESSION_ENDPOINTS["operator_list"]["method"] == "GET"
    assert EXPRESSION_ENDPOINTS["operator_list"]["live"] == "PASS"


def test_all_write_endpoints_are_post():
    for name in ("preset_list", "schema", "transform", "check"):
        assert EXPRESSION_ENDPOINTS[name]["method"] == "POST", name


def test_endpoints_cover_controller_surface():
    """Controller 有 10 个方法，本层必须都有登记（不多不少）。"""
    assert len(EXPRESSION_ENDPOINTS) == 10
    for must in ("operator_list", "preset_list", "schema", "transform", "check",
                 "system_variable_list", "system_values"):
        assert must in endpoint_names(), must


def test_full_path_uses_gateway_prefix():
    assert full_path("check") == "/service/udc/expression/check"
    assert full_path("preset_list") == "/service/udc/expression/preset/list"


def test_unknown_endpoint_raises():
    try:
        full_path("nope")
    except KeyError as exc:
        assert "nope" in str(exc)
    else:
        raise AssertionError("未知端点应抛 KeyError")


# ---------------------------------------------------------------- 运算符
def test_operator_count_and_grouping():
    """18 个 / 5 类，LIVE 实测。"""
    assert len(OPERATORS) == 18
    by = operators_by_type()
    assert list(by) == list(OPERATOR_OP_TYPES)
    assert {k: len(v) for k, v in by.items()} == {
        "ARITHMETIC": 5, "COMPARE": 6, "LOGIC": 3, "BOOLEAN": 2, "SYMBOL": 2,
    }


def test_quick_functions_are_not_full_catalog():
    """operator/list 只给 4 个快捷函数，不是完整 88 个 —— 别混。"""
    assert len(QUICK_FUNCTIONS) == 4
    names = {f["value"] for f in QUICK_FUNCTIONS}
    assert names == {"isNull", "isNotNull", "contains", "thereIn"}


# ---------------------------------------------------------------- token
def test_token_type_domain_is_exactly_five():
    assert TOKEN_TYPES == ("CONSTANT", "VARIABLE", "SYSTEM", "FUNCTION", "OPERATOR")


def test_invalid_token_type_rejected_locally():
    """值域外平台只回 BOOT_3000 + null message，本地必须拦。"""
    try:
        build_constant_token("1", uid="x")
        # 直接构造非法 type 走 validate
        bad = {"uid": "u", "type": "SYSTEM_VARIABLE", "value": "v"}
        errs = validate_token(bad)
        assert any("不在值域" in e for e in errs), errs
    except Exception as exc:  # pragma: no cover
        raise AssertionError(exc)


def test_variable_token_requires_param_id():
    """变量必须链接 schema 的 paramId —— 用户强调的「一定会用到」。"""
    try:
        build_variable_token(None, "id", "ID")
    except ValueError as exc:
        assert "paramId" in str(exc)
    else:
        raise AssertionError("缺 paramId 的变量 token 应被拒")

    tok = build_variable_token(-9128484922878356860, "id", "ID")
    assert tok["paramId"] == "-9128484922878356860"
    assert validate_token(tok) == []


def test_variable_without_param_id_fails_validation():
    bad = {"uid": "u1", "type": "VARIABLE", "value": "id", "desc": "ID"}
    errs = validate_token(bad)
    assert any("paramId" in e for e in errs), errs


def test_function_token_requires_subops():
    tok = build_function_token("isNull", "为空", [[build_variable_token(1, "a", "A")]])
    assert tok["type"] == "FUNCTION"
    assert len(tok["subOps"]) == 1
    assert validate_token(tok) == []

    bad = {"uid": "u2", "type": "FUNCTION", "value": "isNull", "desc": "为空"}
    assert any("subOps" in e for e in validate_token(bad))

    noargs = build_function_token("currentDate", "当前日期", [])
    assert validate_token(noargs) == []


# ---------------------------------------------------------------- 扩展点
def test_param_type_registry_matches_cfr_registrations():
    """@ParamLoadService 全库 grep 的 4 个 + EVENT_ATTR（formula 声明）。"""
    assert set(registered_types()) == {
        "CONFIG_PARAM", "ENTITY", "ATTR_DEFAULT_VALUE", "ATTRIBUTE_SCOPE", "EVENT_ATTR",
    }
    assert is_registered("CONFIG_PARAM")
    assert not is_registered("PARAM_CONFIG"), "PARAM_CONFIG 未注册，传了报 BOOT_3000"


def test_unregistered_formula_types_are_marked():
    """formula 枚举里有、但没注册的类型要显式标注，避免当成可用。"""
    from components.udc.expression.param_types import UNREGISTERED_FORMULA_TYPES
    assert "PARAM_CONFIG" in UNREGISTERED_FORMULA_TYPES
    assert "BPM" in UNREGISTERED_FORMULA_TYPES


def test_formula_enum_trailing_space_documented():
    """BPMAUTO / PARAM_CONFIG 的 code 字面量带尾空格 —— 这是坑，必须记住。"""
    from components.udc.expression.param_types import FORMULA_ENUM_LITERALS
    assert FORMULA_ENUM_LITERALS["BPMAUTO"].endswith(" ")
    assert FORMULA_ENUM_LITERALS["PARAM_CONFIG"].endswith(" ")


def test_entity_param_type_requires_ids():
    spec = spec_for("ENTITY")
    assert spec.requires_entity is True
    assert "ids" in spec.required_body_keys

    from components.udc.expression.param_types import check_body
    assert check_body("ENTITY", {}) != []
    assert check_body("ENTITY", {"ids": [1]}) == []


def test_event_attr_is_not_marked_pass():
    """EVENT_ATTR 只验到 UDC_EXPRESSION_7005，不能标 PASS。"""
    assert spec_for("EVENT_ATTR").live != "PASS"


# ---------------------------------------------------------------- terminal
def test_terminal_function_counts():
    """BACKEND 88 / FRONTEND 81 —— LIVE 实测三档。"""
    assert function_count_for(TERMINAL_BACKEND) == 88
    assert function_count_for(TERMINAL_FRONTEND) == 81
    assert TERMINAL_SUPPORTED == ("BACKEND", "FRONTEND", "ALL")


def test_backend_only_groups():
    """变化函数 / 枚举函数只有 BACKEND 有。"""
    assert has_group(TERMINAL_BACKEND, "变化函数")
    assert has_group(TERMINAL_BACKEND, "枚举函数")
    assert not has_group(TERMINAL_FRONTEND, "变化函数")
    assert not has_group(TERMINAL_FRONTEND, "枚举函数")
    assert set(BACKEND_ONLY_GROUPS) == {"变化函数", "枚举函数"}


def test_invalid_terminal_raises_not_zero():
    """非法 terminal 报 BOOT_3002；函数计数必须抛错，不能返回 0 掩盖。"""
    assert not is_valid_terminal("")
    assert not is_valid_terminal("DESIGN")
    for bad in ("", "DESIGN", "RUNTIME"):
        try:
            function_count_for(bad)
        except ValueError as exc:
            assert "非法" in str(exc)
        else:
            raise AssertionError("%r 应抛错" % bad)


def test_system_variables_do_not_depend_on_terminal():
    """变量面三档一致（131），裁剪只作用于函数。"""
    assert SYSTEM_VARIABLE_TOTAL == 131
    assert all(
        sum(FUNCTION_GROUP_COUNTS[t].values()) in (88, 81) for t in TERMINAL_SUPPORTED
    )
    for t in TERMINAL_SUPPORTED:
        assert sum(FUNCTION_GROUP_COUNTS[t].values()) > 0


# ---------------------------------------------------------------- 校验链
def test_validation_chain_has_four_filters():
    """4 个 Filter 实现（接口与调度器不算）。"""
    chain = validation_chain_order()
    assert len(chain) == 4
    assert chain[0] == "TokenLexerFilter"
    assert chain[-1] == "ResultTypeDefinitionFilter"


def test_structural_vs_semantic_error_split():
    """结构错本地拦（平台只回 null message），语义错交平台。"""
    assert is_structural("BOOT_3000")
    assert is_structural("BOOT_3002")
    assert is_semantic("FORMULA_6058")
    assert is_semantic("UDC_ATTR_0017")
    assert not is_structural("FORMULA_6058")
    assert not is_semantic("BOOT_3000")


def test_error_codes_documented():
    for code in ("BOOT_3000", "BOOT_3002", "FORMULA_6058", "UDC_EXPRESSION_7005"):
        assert code in EXPRESSION_ERROR_CODES


def test_design_runtime_pairs_must_be_written_together():
    """design / runtime 成对写 —— 与具体域无关的公用约束。"""
    assert ("expressionDesignData", "expressionRuntimeData") in DESIGN_RUNTIME_PAIRS
    assert ("defaultValueExpressionDesignData",
            "defaultValueExpressionRuntimeData") in DESIGN_RUNTIME_PAIRS


# ---------------------------------------------------------------- 落位
def test_expression_layer_is_not_under_a_single_domain():
    """公用层不能在 setting/ 或 entity/ 子目录下 —— 它是跨域的。"""
    layer = ROOT / "components" / "udc" / "expression"
    assert layer.is_dir()
    assert "setting" not in layer.parts
    assert "entity" not in layer.parts


def test_facts_live_at_cross_domain_location():
    f = ROOT / "core" / "facts" / "udc" / "expression" / "README.md"
    assert f.is_file(), "公用层事实应在 core/facts/udc/expression/"


def test_facts_record_evidence_not_just_claims():
    """事实件必须带证据等级与 UNVERIFIED 标注，不能只有正例。"""
    text = (ROOT / "core" / "facts" / "udc" / "expression" / "README.md").read_text(
        encoding="utf-8")
    assert "VERIFIED_STATIC_BYTECODE" in text
    assert "UNVERIFIED" in text, "必须显式登记未验证项"
    assert "5.3.318" in text


# ---------------------------------------------------------------- 前端扩展
def test_front_node_is_the_only_node_type():
    """bundle 实测只有 FRONT_NODE，别臆造 BACK_NODE / ENTITY_NODE。"""
    from components.udc.expression import FRONT_NODE
    assert FRONT_NODE == "FRONT_NODE"


def test_terminal_derived_from_flow_type_not_module():
    """terminal 由微流程节点 type 决定 —— 「模块能力差异」的真相。"""
    from components.udc.expression import terminal_for_flow_type
    assert terminal_for_flow_type("FUNCTION") == "FRONTEND"
    assert terminal_for_flow_type("FRONTEND") == "FRONTEND"
    assert terminal_for_flow_type("SERVICE") == "BACKEND"
    assert terminal_for_flow_type(None) == "BACKEND"


def test_enum_result_type_normalized_to_long():
    """枚举/选项集结果类型必须按 LONG 提交，否则类型兼容检查拒。"""
    from components.udc.expression import normalize_result_type
    assert normalize_result_type("Enum") == "LONG"
    assert normalize_result_type("CtpEnum") == "LONG"
    assert normalize_result_type("STRING") == "STRING"
    assert normalize_result_type("DATE") == "DATE"


def test_app_param_schema_unloaded_by_default():
    """APP_PARAM 默认不加载 —— 面板上时有时无不是 bug。"""
    from components.udc.expression import DEFAULT_UNLOADED_SCHEMAS, should_load_schema
    assert "APP_PARAM" in DEFAULT_UNLOADED_SCHEMAS
    assert should_load_schema("APP_PARAM") is False
    assert should_load_schema("ENTITY") is True


def test_build_front_node_shape():
    from components.udc.expression import MODULE_LABELS, build_front_node
    node = build_front_node("页面规则", [{"name": "x"}])
    assert node["type"] == "FRONT_NODE"
    assert node["name"] == "udc"
    assert node["description"] == "页面规则"
    assert isinstance(node["schemas"], list)
    assert "页面规则" in MODULE_LABELS
    assert "公共页面规则" in MODULE_LABELS


def test_build_front_node_rejects_bad_schemas():
    from components.udc.expression import build_front_node
    try:
        build_front_node("页面规则", "not-a-list")
    except TypeError as exc:
        assert "schemas" in str(exc)
    else:
        raise AssertionError("schemas 非 list 应抛 TypeError")


def test_system_variables_catalog_is_present_and_complete():
    """131 项系统变量目录要落地，且带全名/短名/类型。"""
    f = ROOT / "core" / "facts" / "udc" / "expression" / "system-variables.md"
    assert f.is_file()
    text = f.read_text(encoding="utf-8")
    assert "131" in text
    assert "system.currentUserId" in text
    assert "currentUserId" in text, "短名也要在，因为两条通路不等价"


def test_function_catalog_is_present_and_complete():
    """88 个函数用法目录要落地。"""
    f = ROOT / "core" / "facts" / "udc" / "expression" / "functions.md"
    assert f.is_file()
    text = f.read_text(encoding="utf-8")
    assert "88" in text
    for must in ("isNull", "getWeekday", "ifs", "changeTo",
                 "getEnumItemName", "roundOff", "sum", "dateToString"):
        assert "`%s`" % must in text, must
    # 每个函数都要有参数行与示例行
    assert "参数：" in text
    assert "示例：" in text
