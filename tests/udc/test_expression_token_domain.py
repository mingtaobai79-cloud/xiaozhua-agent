"""护栏：表达式 token 类型域 / 系统变量面（LIVE + CFR 双层证据）。

铁律：每条断言必须能追溯到**本轮 LIVE 实测**或 **CFR 字节码行号**。
含**对抗自证**：上一轮交接里被本轮证伪的两处过强表述，必须被钉死。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.attribute_expression_constraints import (
    CHECK_UDC_ENUM_CAST_IS_INDEPENDENT_OF_COMPAT_TABLE,
    COMPAT_DISCRIMINATOR_REFUTED_VARIANT,
    COMPAT_TABLE_ROW_KEY_DISCRIMINATOR,
    ENUM_DATATYPE_CONSTANT_COUNT,
    ENUM_GATE_COMPARES_GENERIC_TYPE_WITH_RESULT_TYPE_FULL_NAME,
    ENUM_GATE_NULL_GENERIC_TYPE_EQUALS_NULL_FULL_NAME,
    ENUM_WITHOUT_RESULT_TYPE_FULL_NAME_ERROR,
    EXPRESSION_TOKEN_ERROR_CODES,
    EXPRESSION_TOKEN_TYPE_DOMAIN,
    EXPRESSION_TOKEN_TYPE_REJECTED_VALUES,
    HIDDEN_SYSTEM_VARIABLE_ITEMS,
    JAR_SYSTEM_VARIABLE_ITEM_COUNT,
    LIVE_SHORT_VS_FULL_ANALYZED_TYPE,
    LIVE_SYSTEM_VARIABLE_GROUP_COUNTS,
    LIVE_SYSTEM_VARIABLE_ITEM_COUNT,
    OUTSIDE_ROW_MEANS_NO_OTHER_GATE_FIRES,
    RESULT_TYPE_COMPATIBILITY_HAS_ENUM_ROW,
    RESULT_TYPE_COMPATIBILITY_HAS_OBJECT_ROW,
    RESULT_TYPE_COMPATIBILITY_HAS_UDCENUM_ROW,
    RESULT_TYPE_COMPATIBILITY_ROW_IS_DERIVED_CAST_TYPE,
    RESULT_TYPE_COMPATIBILITY_TABLE,
    RESULT_TYPE_OUTSIDE_DOMAIN_ERROR,
    SHORT_NAME_ANALYZED_TYPE_MAY_DIFFER_FROM_FULL_NAME,
    SHORT_NAME_WITHOUT_SUBOPS_IS_BOOT_3000,
    SUPPORTED_RESULT_TYPES,
    SUPPORTED_RESULT_TYPE_IS_DATATYPE_CONSTANT_COUNT,
    SYSTEM_SHORT_NAME_PATH_IS_FUNCTION_CALL_EXPR,
    SYSTEM_TOKEN_TWO_RESOLUTION_PATHS,
    SYSTEM_VARIABLE_CHECK_IGNORES_HIDDEN,
    SYSTEM_VARIABLE_ITEMS,
    SYSTEM_VARIABLE_LIST_FILTERS_HIDDEN,
    SYSTEM_VARIABLE_PUT_SITE,
    derive_system_variable_function_name,
    is_system_token_value_legal,
    result_type_compatibility_allows,
    validate_expression_token,
)


# ---------------------------------------------------------------- 1. token.type 值域
def test_token_type_domain_is_exactly_five():
    """CFR TokenTypeEnum / TokenTypeConstant 都是这 5 个字面量。"""
    assert EXPRESSION_TOKEN_TYPE_DOMAIN == (
        "CONSTANT", "VARIABLE", "SYSTEM", "FUNCTION", "OPERATOR")
    assert len(EXPRESSION_TOKEN_TYPE_DOMAIN) == 5


def test_system_variable_is_not_a_token_type():
    """★ 对抗自证：上轮把它当合法 type 做过 2x2；LIVE 证伪（恒 BOOT_3000）。"""
    assert "SYSTEM_VARIABLE" not in EXPRESSION_TOKEN_TYPE_DOMAIN
    assert "SYSTEM_VARIABLE" in EXPRESSION_TOKEN_TYPE_REJECTED_VALUES
    assert "SYSTEM" in EXPRESSION_TOKEN_TYPE_DOMAIN


def test_validate_expression_token_rejects_out_of_domain():
    for bad in ("SYSTEM_VARIABLE", "BOGUS", "", None):
        errs = validate_expression_token({"type": bad, "value": "x"})
        assert errs, bad
    assert validate_expression_token(
        {"type": "SYSTEM", "value": "system.currentDate"}) == []


def test_validate_expression_token_short_name_needs_subops():
    """LIVE：SYSTEM+abs 无 subOps ⇒ BOOT_3000；带参 ⇒ BOOT_0000。"""
    assert SHORT_NAME_WITHOUT_SUBOPS_IS_BOOT_3000 is True
    assert validate_expression_token({"type": "SYSTEM", "value": "abs"})
    assert validate_expression_token(
        {"type": "SYSTEM", "value": "abs",
         "subOps": [[{"type": "CONSTANT", "value": "1"}]]}) == []


# ---------------------------------------------------------------- 2. 两条解析通路
def test_two_resolution_paths_are_declared_and_short_name_is_call_expr():
    assert SYSTEM_TOKEN_TWO_RESOLUTION_PATHS == (
        "SYSTEM_FULL_NAME_TABLE", "SHORT_NAME_FUNCTION_CALL")
    assert SYSTEM_SHORT_NAME_PATH_IS_FUNCTION_CALL_EXPR is True
    assert SHORT_NAME_ANALYZED_TYPE_MAY_DIFFER_FROM_FULL_NAME is True


def test_analyzed_type_split_is_pinned_to_live_values():
    """LIVE 报文逼出的分析类型（short 走 CALL_EXPR，full 走系统变量表）。"""
    t = LIVE_SHORT_VS_FULL_ANALYZED_TYPE
    assert t["currentTime"] == {"short": "STRING", "full": "TIME"}
    assert t["currentDateTime"] == {"short": "DATE", "full": "DATETIME"}
    # 未分裂的两条也必须在案（防"以为全部分裂"）
    assert t["currentDate"]["short"] == t["currentDate"]["full"]
    assert t["currentUserId"]["short"] == t["currentUserId"]["full"]


def test_system_variable_put_site_is_single_and_names_cfr_lines():
    assert "ExpressionPresetRunner.loadSystemVariable:237" in SYSTEM_VARIABLE_PUT_SITE
    assert "getSystemVariableItemsMap().put(" in SYSTEM_VARIABLE_PUT_SITE


# ---------------------------------------------------------------- 3. hidden：list 过滤 / check 不过滤
def test_hidden_filtered_from_list_but_not_from_check():
    assert SYSTEM_VARIABLE_LIST_FILTERS_HIDDEN is True
    assert SYSTEM_VARIABLE_CHECK_IGNORES_HIDDEN is True
    assert HIDDEN_SYSTEM_VARIABLE_ITEMS == ("system.currentTimestamp",)


def test_131_vs_132_difference_is_exactly_the_hidden_item():
    """双向闭合：LIVE 131 + 唯一 hidden 项 = 静态 132。"""
    assert LIVE_SYSTEM_VARIABLE_ITEM_COUNT == 131
    assert JAR_SYSTEM_VARIABLE_ITEM_COUNT == 132
    assert JAR_SYSTEM_VARIABLE_ITEM_COUNT - LIVE_SYSTEM_VARIABLE_ITEM_COUNT == len(
        HIDDEN_SYSTEM_VARIABLE_ITEMS)
    assert len(SYSTEM_VARIABLE_ITEMS) == JAR_SYSTEM_VARIABLE_ITEM_COUNT
    assert sum(LIVE_SYSTEM_VARIABLE_GROUP_COUNTS.values()) == LIVE_SYSTEM_VARIABLE_ITEM_COUNT


def test_hidden_item_is_present_in_static_table():
    names = {n for _, n, _, _ in SYSTEM_VARIABLE_ITEMS}
    for h in HIDDEN_SYSTEM_VARIABLE_ITEMS:
        assert h in names, h


def test_system_variable_table_shape():
    assert len({n for _, n, _, _ in SYSTEM_VARIABLE_ITEMS}) == len(SYSTEM_VARIABLE_ITEMS), "name 重复"
    for g, n, fn, rt in SYSTEM_VARIABLE_ITEMS:
        assert g in LIVE_SYSTEM_VARIABLE_GROUP_COUNTS, g
        assert n.startswith("system."), n
        assert fn and isinstance(rt, str) and rt, (n, fn, rt)
    # ★ 回归：上轮生成器把 resultType 写成裸标识符导致 NameError
    assert all(rt == rt.upper() for _, _, _, rt in SYSTEM_VARIABLE_ITEMS)


# ---------------------------------------------------------------- 4. 返回类型域
def test_supported_result_types_is_15_not_16():
    """★ 对抗自证：上轮交接写 16（把枚举常量数当成值域大小）。"""
    assert len(SUPPORTED_RESULT_TYPES) == 15
    assert ENUM_DATATYPE_CONSTANT_COUNT == 16
    assert SUPPORTED_RESULT_TYPE_IS_DATATYPE_CONSTANT_COUNT is False
    assert "OBJECT" not in SUPPORTED_RESULT_TYPES
    assert len(set(SUPPORTED_RESULT_TYPES)) == 15


def test_result_type_error_codes():
    assert RESULT_TYPE_OUTSIDE_DOMAIN_ERROR == "FORMULA_6003"
    assert ENUM_WITHOUT_RESULT_TYPE_FULL_NAME_ERROR == "FORMULA_6068"


# ---------------------------------------------------------------- 5. 兼容表
def test_compat_table_is_14_rows_and_keys_match_live_derivation():
    assert len(RESULT_TYPE_COMPATIBILITY_TABLE) == 14
    assert set(RESULT_TYPE_COMPATIBILITY_TABLE) == {
        "MULTILINESTRING", "STRING", "INTEGER", "BIGINTEGER", "DECIMAL", "BOOLEAN", "DATE",
        "DATETIME", "TIME", "ENTITY", "ATTACHMENT", "CURRENCY", "CTPENUM", "ARRAY"}


def test_compat_table_has_no_enum_udcenum_object_row():
    assert RESULT_TYPE_COMPATIBILITY_HAS_ENUM_ROW is False
    assert RESULT_TYPE_COMPATIBILITY_HAS_UDCENUM_ROW is False
    assert RESULT_TYPE_COMPATIBILITY_HAS_OBJECT_ROW is False
    for k in ("ENUM", "UDCENUM", "OBJECT"):
        assert k not in RESULT_TYPE_COMPATIBILITY_TABLE
    # ENUM 也不作为任何行的**值**出现
    for row in RESULT_TYPE_COMPATIBILITY_TABLE.values():
        for side in ("BACKEND", "FRONTEND"):
            assert "ENUM" not in row[side], row


def test_row_key_is_derived_cast_type():
    assert RESULT_TYPE_COMPATIBILITY_ROW_IS_DERIVED_CAST_TYPE is True
    # CTPENUM/ENTITY 派生：multi=True -> STRING, multi=False -> BIGINTEGER
    assert result_type_compatibility_allows("CTPENUM", is_multi_select=False)[0] == "BIGINTEGER"
    assert result_type_compatibility_allows("CTPENUM", is_multi_select=True)[0] == "STRING"
    assert result_type_compatibility_allows("ENTITY", is_multi_select=True)[0] == "STRING"
    assert result_type_compatibility_allows("STRING")[0] == "STRING"


def test_outside_row_does_not_mean_no_other_gate():
    """★ 对抗自证：上轮写「表外 ⇒ 恒放行」，本轮 LIVE 证伪。"""
    assert OUTSIDE_ROW_MEANS_NO_OTHER_GATE_FIRES is False
    assert CHECK_UDC_ENUM_CAST_IS_INDEPENDENT_OF_COMPAT_TABLE is True
    # ENUM 查不到行 ⇒ 兼容表这一门确实不生效（in_table=False），但那是**另一回事**
    row_key, compatible, in_table = result_type_compatibility_allows("ENUM", analyzed_type="DATE")
    assert row_key == "ENUM" and in_table is False


def test_enum_gate_semantics_pinned():
    assert ENUM_GATE_COMPARES_GENERIC_TYPE_WITH_RESULT_TYPE_FULL_NAME is True
    assert ENUM_GATE_NULL_GENERIC_TYPE_EQUALS_NULL_FULL_NAME is True


# ---------------------------------------------------------------- 6. 判别器（本轮新证 + 上轮证伪）
def test_discriminator_single_variable_flips_only_multi():
    """唯一自变量 isMultiSelect，同一 token/分析类型下结果翻转。"""
    d = COMPAT_TABLE_ROW_KEY_DISCRIMINATOR
    assert d["token"] == {"type": "CONSTANT", "value": "x"}
    assert d["resultTypeInfo"] == "CTPENUM"
    assert d["multiFalse"] == {"row": "BIGINTEGER", "code": "FORMULA_6901"}
    assert d["multiTrue"] == {"row": "STRING", "code": "BOOT_0000"}
    # 复算一致
    _, ok_f, _ = result_type_compatibility_allows("CTPENUM", is_multi_select=False, analyzed_type="STRING")
    _, ok_t, _ = result_type_compatibility_allows("CTPENUM", is_multi_select=True, analyzed_type="STRING")
    assert ok_f is False and ok_t is True


def test_refuted_variant_does_not_flip():
    """★ 对抗自证：上轮把 SYSTEM currentDate(DATE) 当判别器，本轮实测两臂都 6901。"""
    r = COMPAT_DISCRIMINATOR_REFUTED_VARIANT
    assert r["multiFalse"] == r["multiTrue"] == "FORMULA_6901"
    _, ok_f, _ = result_type_compatibility_allows("CTPENUM", is_multi_select=False, analyzed_type="DATE")
    _, ok_t, _ = result_type_compatibility_allows("CTPENUM", is_multi_select=True, analyzed_type="DATE")
    assert ok_f is False and ok_t is False


# ---------------------------------------------------------------- 7. 辅助函数
def test_derive_system_variable_function_name():
    assert derive_system_variable_function_name("system.currentDateTime") == "currentDateTime"
    assert derive_system_variable_function_name("system.a.b") == "a"
    try:
        derive_system_variable_function_name("currentDate")
    except ValueError:
        pass
    else:
        raise AssertionError("无点输入应报 ValueError")


def test_is_system_token_value_legal():
    assert is_system_token_value_legal("system.currentTimestamp") == []
    assert is_system_token_value_legal("system.currentUserId") == []
    assert is_system_token_value_legal("system.nope")
    assert is_system_token_value_legal("currentTime", known_function_names=["currentTime"]) == []


def test_error_codes_cover_observed_live_codes():
    for c in ("BOOT_3000", "FORMULA_6003", "FORMULA_6049", "FORMULA_6058", "FORMULA_6068",
              "FORMULA_6071", "FORMULA_6169", "FORMULA_6170", "FORMULA_6171", "FORMULA_6172",
              "FORMULA_6901"):
        assert c in EXPRESSION_TOKEN_ERROR_CODES, c
