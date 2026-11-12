"""护栏：属性「计算值 / 默认值表达式」表达式引擎约束（LIVE + CFR 双层证据）。

铁律：本文件每条断言都必须能追溯到**本轮 LIVE 实测**或 **CFR 字节码行号**；
任何只靠"写法直觉"的断言不许进来。含**对抗自证**：故意构造崩检测器的形状必须被咬住。
"""
import json as _json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.attribute_expression_constraints import (
    ATTRIBUTE_EXPRESSION_COLUMNS,
    ATTRIBUTE_EXPRESSION_PAIRS,
    AGGREGATION_0006_IS_NULL_SHAPE_GATE_ONLY,
    AGGREGATION_0006_VALIDATES_FIELD_CONSISTENCY,
    AGGREGATION_CONDITION_KEYS,
    AGGREGATION_DTO_KEYS,
    AGGREGATION_ENTITY_TYPES,
    AGGREGATION_ENTITY_TYPE_CODES,
    AGGREGATION_ERROR_CODES,
    AGGREGATION_FUNCTIONS,
    AGGREGATION_FUNCTION_CODES,
    AGGREGATION_OPTIONAL_KEYS,
    AGGREGATION_RELATIONS,
    AGGREGATION_RELATION_CODES,
    AGGREGATION_REQUIRED_KEYS,
    AGGREGATION_RUNTIME_SHAPE_MATCHES_CALCULATE,
    CALCULATE_AGGREGATION,
    CALCULATE_COMPUTE,
    CALCULATE_NORMAL,
    CONTEXT_KEY_IS_MANDATORY,
    EMPTY_STRING_CLEARS_EXPRESSION,
    EXPRESSION_DESIGN_KEYS,
    EXPRESSION_ENDPOINTS,
    EXPRESSION_ERROR_CODES,
    EXPRESSION_REQUIRED_DESIGN_KEYS,
    EXPRESSION_RUNTIME_KEYS,
    EXPRESSION_SAVE_KEYS,
    NULL_CLEARS_EXPRESSION,
    RESULT_TYPE_DECOUPLED_FROM_DATATYPE,
    UPDATE_USES_IGNORE_NULL,
    clear_expression_payload,
    validate_aggregation_runtime_data,
    derived_default_value_caption,
    validate_attribute_expression,
    validate_expression_design_data,
)

MODULE_PATH = ROOT / "components" / "udc" / "attribute_expression_constraints.py"
MODULE_SRC = MODULE_PATH.read_text(encoding="utf-8")


def _live_design():
    """真实 transform 产出形状（裁剪自本轮 LIVE 回读）。"""
    return {
        "expressionTranslation": "实验数量 * 2 ",
        "resultTypeInfo": "INTEGER",
        "resultTypeFullName": None,
        "terminalType": "BACKEND",
        "isMultiSelect": False,
        "context": [{"name": "xzhExp950795", "type": "OBJECT",
                     "uniformityParams": {"paramId": "474806313816300867", "paramCategory": "Entity"}}],
        "tokens": [{"uid": "u1", "type": "VARIABLE", "value": "xzhExp950795.expNum", "desc": "实验数量"}],
        "sourceAppName": None,
        "version": "1",
    }


def _live_runtime():
    return {"executableExpr":
            "93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=+%28+xzhExp950795.expNum+*+2+%29+"}


# ---------------------------------------------------------------- 端点面（LIVE）
def test_expression_endpoints_are_the_four_live_verified_paths():
    assert set(EXPRESSION_ENDPOINTS) == {"schema", "transform", "check", "preset_list"}
    paths = {k: v["path"] for k, v in EXPRESSION_ENDPOINTS.items()}
    assert paths == {
        "schema": "/udc/expression/schema",
        "transform": "/udc/expression/transform",
        "check": "/udc/expression/check",
        "preset_list": "/udc/expression/preset/list",
    }
    assert all(v["method"] == "POST" for v in EXPRESSION_ENDPOINTS.values())


def test_expression_save_keys_are_the_live_verified_request_keys():
    assert set(EXPRESSION_SAVE_KEYS) == {
        "resultTypeInfo", "schemas", "tokens", "isMultiSelect",
        "terminalSupportType", "sourceAppName", "version",
    }


def test_design_keys_contain_the_three_required_ones():
    assert set(EXPRESSION_REQUIRED_DESIGN_KEYS) <= set(EXPRESSION_DESIGN_KEYS)
    assert set(EXPRESSION_REQUIRED_DESIGN_KEYS) == {"context", "resultTypeInfo", "tokens"}


def test_runtime_data_key_is_executable_expr():
    assert EXPRESSION_RUNTIME_KEYS == ("executableExpr",)


# ---------------------------------------------------------------- 承载列（information_schema LIVE）
def test_attribute_expression_columns_match_information_schema():
    assert set(ATTRIBUTE_EXPRESSION_COLUMNS) == {
        "expression_design_data", "expression_runtime_data", "value_scope_expression",
        "default_value_expr_design", "default_value_expr_runtime",
    }


def test_expression_pairs_cover_design_and_runtime_sides():
    assert set(ATTRIBUTE_EXPRESSION_PAIRS) == {
        ("expressionDesignData", "expressionRuntimeData"),
        ("defaultValueExpressionDesignData", "defaultValueExpressionRuntimeData"),
    }
    for d, r in ATTRIBUTE_EXPRESSION_PAIRS:
        assert d.endswith("DesignData")
        assert r == d[:-len("DesignData")] + "RuntimeData"


# ---------------------------------------------------------------- 不变量 1：context 必填
def test_context_key_is_mandatory_flag_is_on():
    assert CONTEXT_KEY_IS_MANDATORY is True


def test_validate_design_data_accepts_live_sample():
    assert validate_expression_design_data(_live_design()) == []


def test_validate_design_data_rejects_missing_context():
    """本轮血证：缺 context 会让 buildSchemaMap:148 抛 NPE，整轮检测 FAIL。"""
    d = _live_design()
    d.pop("context")
    errs = validate_expression_design_data(d)
    assert len(errs) == 1 and "context" in errs[0] and "NPE" in errs[0]


def test_adversarial_shape_that_crashed_the_detector_is_rejected():
    """对抗自证：本轮我实际写坏的那一条（resultTypeInfo+tokens、无 context）必须被咬住。"""
    crashed = {"resultTypeInfo": "INTEGER", "tokens": []}
    errs = validate_expression_design_data(crashed)
    assert any("context" in e for e in errs)
    assert any("tokens" in e for e in errs)
    assert errs != []


def test_validate_design_data_rejects_empty_tokens_and_missing_result_type():
    d = _live_design()
    d["tokens"] = []
    assert any("tokens" in e for e in validate_expression_design_data(d))
    d = _live_design()
    d["resultTypeInfo"] = ""
    assert any("resultTypeInfo" in e for e in validate_expression_design_data(d))


def test_validate_design_data_rejects_non_list_context_and_non_dict():
    d = _live_design()
    d["context"] = {"name": "x"}
    assert any("context" in e for e in validate_expression_design_data(d))
    assert validate_expression_design_data([1, 2]) != []


def test_validate_design_data_treats_blank_as_absent():
    for blank in (None, "", {}):
        assert validate_expression_design_data(blank) == []


# ---------------------------------------------------------------- 不变量 2：清空须用空字符串
def test_update_semantics_flags_are_consistent():
    assert UPDATE_USES_IGNORE_NULL is True
    assert NULL_CLEARS_EXPRESSION is False
    assert EMPTY_STRING_CLEARS_EXPRESSION is True


def test_clear_payload_uses_empty_string_never_null():
    p = clear_expression_payload()
    assert p["calculate"] == "NORMAL"
    for k in ("expressionDesignData", "expressionRuntimeData",
              "defaultValueExpressionDesignData", "defaultValueExpressionRuntimeData"):
        assert p[k] == "", k + " 必须为空字符串（传 null 因 IGNORE_NULL 清不掉）"
    assert all(v is not None for v in p.values())


def test_clear_payload_passes_its_own_validator():
    assert validate_attribute_expression(clear_expression_payload()) == []


# ---------------------------------------------------------------- COMPUTE 耦合（CFR）
def test_compute_requires_runtime_expression():
    body = {"calculate": CALCULATE_COMPUTE,
            "expressionDesignData": '{"context":[],"resultTypeInfo":"INTEGER","tokens":[1]}'}
    errs = validate_attribute_expression(body)
    assert any("expressionRuntimeData" in e for e in errs)
    body["expressionRuntimeData"] = '{"executableExpr":"x"}'
    assert validate_attribute_expression(body) == []


def test_pairs_require_both_sides():
    errs = validate_attribute_expression(
        {"expressionDesignData": '{"context":[],"resultTypeInfo":"I","tokens":[1]}'})
    assert any("expressionRuntimeData" in e for e in errs)
    errs = validate_attribute_expression({"expressionRuntimeData": '{"executableExpr":"x"}'})
    assert any("expressionDesignData" in e for e in errs)


def test_result_type_is_decoupled_from_attribute_datatype():
    """实测：DATETIME 字段承载 INTEGER 表达式，检测 SUCCESS ⇒ 两者不耦合。"""
    assert RESULT_TYPE_DECOUPLED_FROM_DATATYPE is True


# ---------------------------------------------------------------- defaultValueCaption（CFR 优先链）
def test_derived_caption_priority_chain():
    expr = '{"expressionTranslation": "系统日期时间 "}'
    sysvar = '{"type":"SYSTEM_VARIABLE","value":"currentUserId","desc":"登录人员ID"}'
    assert derived_default_value_caption(expression_design=expr) == "系统日期时间 "
    assert derived_default_value_caption(
        system_variable_json=sysvar, expression_design=expr) == "登录人员ID"
    assert derived_default_value_caption(default_value='"默认文本"') == '"默认文本"'
    assert derived_default_value_caption() is None


def test_derived_caption_is_not_trimmed():
    """实测回填 '"系统日期时间 "' 带尾空格 ⇒ 不得 trim。"""
    got = derived_default_value_caption(expression_design='{"expressionTranslation":"系统日期时间 "}')
    assert got != "系统日期时间"
    assert got.endswith(" ")


def test_derived_caption_malformed_input_degrades_without_raising():
    assert derived_default_value_caption(expression_design="{not json") is None
    assert derived_default_value_caption(system_variable_json="{not json", default_value="d") == "d"


def test_module_does_not_claim_to_handle_ctpenum_caption_branch():
    """边界诚实：CTPENUM 默认值 caption 走另一支（setCtpEnumDefaultValueCaption）。"""
    assert "setCtpEnumDefaultValueCaption" in MODULE_SRC
    assert "CTPENUM" in MODULE_SRC


# ---------------------------------------------------------------- 错误码与清洗门
def test_error_codes_cover_cfr_and_live_observed_codes():
    for c in ("UDC_ATTR_0017", "UDC_ATTR_0018", "FORMULA_6058", "BOOT_3000"):
        assert c in EXPRESSION_ERROR_CODES
    assert "checkExpressionPattern:1601-1603" in EXPRESSION_ERROR_CODES["UDC_ATTR_0017"]
    assert "checkExpressionPattern:1604-1607" in EXPRESSION_ERROR_CODES["UDC_ATTR_0018"]


def test_module_records_both_evidence_layers():
    assert "LIVE" in MODULE_SRC and "CFR" in MODULE_SRC
    assert "buildSchemaMap:148" in MODULE_SRC
    assert "IGNORE_NULL" in MODULE_SRC


def test_module_has_no_placeholder_markers():
    for bad in ("TODO", "FIXME", "XXX", "TBD"):
        assert bad not in MODULE_SRC, "模块含占位标记 " + bad


def test_module_records_the_live_app_id_and_entity():
    """本轮 LIVE 证据锚点必须写进模块（可复核）。"""
    assert "8704025620829192834" in MODULE_SRC
    assert "474806313816300867" in MODULE_SRC


def test_live_runtime_helper_shape_matches_contract():
    assert set(_live_runtime()) == set(EXPRESSION_RUNTIME_KEYS)

# ================================================================ calculate 第三态 AGGREGATION（本轮 LIVE + CFR）
def _live_aggregation():
    """本轮 LIVE 正例的**形状**逐字（id 与业务名按事实治理规则替换为合成占位符）。

    ★ 事实治理：客户侧实体/字段/业务名**不回流仓库**，故此处只保留形状。
    落库回读原文（app 8704025620829192834 / 字段 8016904624316689195）见
    `core/facts/udc/write-chain/attribute-aggregation-write-chain.md` §4 的口径描述。
    """
    return {
        "sourceEntityId": "app9000000000000000001", "targetEntityId": "app9000000000000000002",
        "sourceFieldId": "9000000000000000011", "targetFieldId": "9000000000000000021",
        "entityType": "CHILD", "functionType": "SUM", "entityName": "AggSourceEntity",
        "relation": "ONE2MANY", "targetDataType": "INTEGER", "targetFieldName": "targetNum",
        "sourceDataType": "INTEGER", "sourceFieldName": "sourceNum",
        "condition": {"expressionDesignData": None, "expressionRuntimeData": None},
    }


def test_calculate_has_three_states_and_aggregation_is_the_third():
    assert CALCULATE_NORMAL == "NORMAL"
    assert CALCULATE_COMPUTE == "COMPUTE"
    assert CALCULATE_AGGREGATION == "AGGREGATION"


def test_aggregation_dto_keys_match_cfr_class_fields_exactly():
    """CFR AggregationDto.java 12 字段 + 嵌套 condition，逐字。"""
    assert set(AGGREGATION_DTO_KEYS) == {
        "sourceEntityId", "targetEntityId", "sourceFieldId", "targetFieldId",
        "entityType", "functionType", "entityName", "relation",
        "targetDataType", "targetFieldName", "sourceDataType", "sourceFieldName",
        "condition"}
    assert len(AGGREGATION_DTO_KEYS) == 13
    assert set(AGGREGATION_CONDITION_KEYS) == {"expressionDesignData", "expressionRuntimeData"}


def test_aggregation_required_is_exactly_the_twelve_non_condition_keys():
    """关键不变量：判据集不含 condition（CFR 补默认值 => 永不 null）。"""
    assert set(AGGREGATION_REQUIRED_KEYS) == set(AGGREGATION_DTO_KEYS) - {"condition"}
    assert len(AGGREGATION_REQUIRED_KEYS) == 12
    assert AGGREGATION_OPTIONAL_KEYS == ("condition",)


def test_aggregation_live_positive_passes_validator():
    assert validate_aggregation_runtime_data(_live_aggregation()) == []


def test_aggregation_accepts_live_positive_even_as_json_string():
    assert validate_aggregation_runtime_data(_json.dumps(_live_aggregation())) == []


def test_each_of_the_twelve_keys_dropped_is_caught():
    """对抗自证：LIVE 12/12 逐键删一均报 UDC_ATTR_0006 —— 校验器须逐条咬住。"""
    for k in AGGREGATION_REQUIRED_KEYS:
        d = _live_aggregation()
        d.pop(k)
        errs = validate_aggregation_runtime_data(d)
        assert any(k in e and "UDC_ATTR_0006" in e for e in errs), k
    caught = sum(1 for k in AGGREGATION_REQUIRED_KEYS
                 if validate_aggregation_runtime_data(dict.fromkeys(AGGREGATION_DTO_KEYS, 1) | {k: None}) != [])
    assert caught == 12


def test_dropping_condition_is_allowed_and_matches_cfr_default_fill():
    """LIVE：condition 整键缺失 => BOOT_0000；CFR 亦有先补 new Condition()。"""
    d = _live_aggregation()
    d.pop("condition")
    assert validate_aggregation_runtime_data(d) == []


def test_condition_subkeys_null_are_not_flagged():
    """LIVE：condition 内两子键全 null 仍 PASS（两层嵌套，子键不进顶层判据）。"""
    d = _live_aggregation()
    d["condition"] = {"expressionDesignData": None, "expressionRuntimeData": None}
    assert validate_aggregation_runtime_data(d) == []


def test_aggregation_function_domain_is_enum_backed_and_rejects_avg():
    assert AGGREGATION_FUNCTIONS == ("SUM", "COUNT", "MAX", "MIN")
    assert AGGREGATION_FUNCTION_CODES == {"SUM": 0, "COUNT": 1, "MAX": 2, "MIN": 3}
    for f in AGGREGATION_FUNCTIONS:
        assert validate_aggregation_runtime_data(dict(_live_aggregation(), functionType=f)) == []
    for f in ("AVG", "BOGUS"):
        errs = validate_aggregation_runtime_data(dict(_live_aggregation(), functionType=f))
        assert any("functionType" in e and "BOOT_3000" in e for e in errs), f


def test_aggregation_entity_type_domain_matches_entity_type_enum():
    assert AGGREGATION_ENTITY_TYPES == ("PRIMARYWITHCHILD", "PRIMARYONLY", "CHILD")
    assert AGGREGATION_ENTITY_TYPE_CODES == {"PRIMARYWITHCHILD": 0, "PRIMARYONLY": 1, "CHILD": 2}
    for v in AGGREGATION_ENTITY_TYPES:
        assert validate_aggregation_runtime_data(dict(_live_aggregation(), entityType=v)) == []
    errs = validate_aggregation_runtime_data(dict(_live_aggregation(), entityType="BOGUS"))
    assert any("entityType" in e for e in errs)


def test_aggregation_relation_domain_excludes_many2many():
    """LIVE：MANY2MANY => BOOT_3000 —— 权威枚举只有 ONE2ONE/ONE2MANY。"""
    assert AGGREGATION_RELATIONS == ("ONE2ONE", "ONE2MANY")
    assert AGGREGATION_RELATION_CODES == {"ONE2ONE": 0, "ONE2MANY": 1}
    for v in AGGREGATION_RELATIONS:
        assert validate_aggregation_runtime_data(dict(_live_aggregation(), relation=v)) == []
    for v in ("MANY2MANY", "BOGUS"):
        assert validate_aggregation_runtime_data(dict(_live_aggregation(), relation=v)) != []


def test_aggregation_blank_runtime_is_rejected():
    for blank in (None, "", {}):
        assert validate_aggregation_runtime_data(blank) != []
    assert validate_aggregation_runtime_data("{not json") != []
    assert validate_aggregation_runtime_data([1, 2]) != []


def test_attribute_expression_wires_aggregation_validation():
    """validate_attribute_expression 必须把 AGGREGATION 的 runtimeData 纳入校验。"""
    errs = validate_attribute_expression(
        {"calculate": CALCULATE_AGGREGATION, "expressionRuntimeData": "{}"})
    assert any("UDC_ATTR_0006" in e for e in errs)
    ok = {"calculate": CALCULATE_AGGREGATION,
          "expressionDesignData": _json.dumps(_live_design()),
          "expressionRuntimeData": _json.dumps(_live_aggregation())}
    assert validate_attribute_expression(ok) == []


def test_aggregation_error_code_0006_is_the_cfr_throw_site():
    assert "UDC_ATTR_0006" in AGGREGATION_ERROR_CODES
    assert "checkAggregation:458-459" in AGGREGATION_ERROR_CODES["UDC_ATTR_0006"]


def test_0006_is_a_null_shape_gate_not_a_semantic_validator():
    """诚实边界：LIVE 三组语义负控（类型不符/字段名不符/源=目标）全部 BOOT_0000 通过。"""
    assert AGGREGATION_0006_IS_NULL_SHAPE_GATE_ONLY is True
    assert AGGREGATION_0006_VALIDATES_FIELD_CONSISTENCY is False
    d = dict(_live_aggregation(), targetDataType="STRING",
             targetFieldName="notExist", targetEntityId="app9000000000000000001")
    assert validate_aggregation_runtime_data(d) == []


def test_runtime_shape_is_not_checked_against_calculate_by_the_server():
    """LIVE：COMPUTE + AggregationDto 形态亦 PASS => 服务端不做形态耦合校验。"""
    assert AGGREGATION_RUNTIME_SHAPE_MATCHES_CALCULATE is False


def test_module_records_aggregation_cfr_sites_and_frontend_anchor():
    for s in ("AttributeEventListener", "existFieldIsNull", "AggregationTypeEnum",
              "module-62746.js", "setCalculate"):
        assert s in MODULE_SRC, s
