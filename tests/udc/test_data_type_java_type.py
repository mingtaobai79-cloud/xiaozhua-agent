# -*- coding: utf-8 -*-
"""护栏：UDC dataType <-> javaType 权威配对（字节码 + LIVE 双层证据）。

铁律：本文件每条断言都必须能追溯到 CFR 字节码类，或本轮 LIVE 实测口径；
任何只靠"写法直觉"的断言不许进来。含**对抗自证**：被证伪的旧表必须能被咬住。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.data_type_java_type import (
    DATA_TYPE_CODES,
    DATA_TYPE_TO_JAVA_TYPE,
    ENUM_JAVA_TYPE_TEMPLATE,
    HOLDER_MULTI_SELECT_ALWAYS_ABSENT,
    HOLDER_PATH_SUFFIXES,
    JAVA_TYPE_COLLISIONS,
    JAVA_TYPE_TO_DATA_TYPES,
    LIVE_SAMPLE_MISSING,
    MULTI_SELECT_DATA_TYPES,
    MULTI_SELECT_DEPENDENT_DATA_TYPES,
    MULTI_SELECT_JAVA_TYPE,
    NON_HOLDER_CARRIERS,
    SIMPLE_JAVA_TYPES,
    SINGLE_RELATION_JAVA_TYPE,
    is_authoritative_holder,
    java_type_for,
    java_type_mismatches,
    normalize_holder_java_types,
)
from tools.core._fixtures.live_targets import (
    LIVE_APP_ID_DATA_TYPE,
    LIVE_BROAD_CARRIER_COUNT_ALL,
    LIVE_BROAD_CARRIER_COUNT_SAMPLE,
    LIVE_CURRENCY_OCCURRENCES,
    LIVE_HOLDER_COUNT_ALL,
    LIVE_HOLDER_COUNT_RELEASE,
    LIVE_HOLDER_WITH_MULTI_SELECT,
    LIVE_LEFT_PARAM_CTPENUM_FALSE_LONG,
    LIVE_LEFT_PARAM_CTPENUM_TRUE_STRING,
    LIVE_LEFT_PARAM_ENTITY_FALSE_LONG,
    LIVE_LEFT_PARAM_ENTITY_TRUE_STRING,
    LIVE_NEW_TABLE_RESIDUAL_ALL,
    LIVE_OLD_TABLE_FALSE_POSITIVES_ALL,
    LIVE_OLD_TABLE_FALSE_POSITIVES_HOLDER,
    LIVE_OLD_TABLE_FALSE_POSITIVES_SAMPLE,
    LIVE_SAMPLE_SCOPE,
)

MODULE_PATH = ROOT / "components" / "udc" / "data_type_java_type.py"
MODULE_SRC = MODULE_PATH.read_text(encoding="utf-8")

# 锚点已迁出组件：LIVE_* 测试值统一放 tools 固定装置，
# 元测试改为在装置里核对这些锚点仍在（防止"删了没人发现"）。
ANCHOR_PATH = ROOT / "tools" / "core" / "_fixtures" / "live_targets.py"
ANCHOR_SRC = ANCHOR_PATH.read_text(encoding="utf-8")


def _holder(**kw):
    """真实 holder 形状：mappingRows 的 targetField / value.reference（无 multiSelect 键）。"""
    h = {"dataType": "STRING", "javaType": "java.lang.String", "type": "OBJECT",
         "name": "x", "desc": "x", "path": "x", "id": "x"}
    h.update(kw)
    return h


# ---------------------------------------------------------------- 固定映射（字节码直证）
def test_fixed_mapping_is_bytecode_derived_eleven_types():
    """11 条固定映射：与 UdcDataType#getJavaType 的 8 个覆写类 + 2 个基类逐一对应。"""
    assert set(DATA_TYPE_TO_JAVA_TYPE) == {
        "STRING", "MULTILINESTRING", "TIME", "ATTACHMENT", "INTEGER", "BOOLEAN",
        "BIGINTEGER", "DECIMAL", "CURRENCY", "DATE", "DATETIME",
    }
    assert DATA_TYPE_TO_JAVA_TYPE["BIGINTEGER"] == "java.lang.Long"      # ★ 反直觉，勿改
    assert DATA_TYPE_TO_JAVA_TYPE["INTEGER"] == "java.lang.Integer"
    assert DATA_TYPE_TO_JAVA_TYPE["BOOLEAN"] == "java.lang.Boolean"
    assert DATA_TYPE_TO_JAVA_TYPE["DECIMAL"] == "java.math.BigDecimal"
    assert DATA_TYPE_TO_JAVA_TYPE["CURRENCY"] == "java.math.BigDecimal"
    assert DATA_TYPE_TO_JAVA_TYPE["DATE"] == "java.util.Date"
    assert DATA_TYPE_TO_JAVA_TYPE["DATETIME"] == "java.util.Date"


def test_time_is_verified_string_but_live_sample_missing():
    """TIME -> java.lang.String：三源一致（AbstractStringDataType / ExprDataTypeTransferUtil
    / DataType.TIME(10)）；但 LIVE 样本维度 0 例 => 仍登记在 LIVE_SAMPLE_MISSING。"""
    assert DATA_TYPE_TO_JAVA_TYPE["TIME"] == "java.lang.String"
    assert "TIME" in LIVE_SAMPLE_MISSING
    assert DATA_TYPE_CODES["TIME"] == 10


def test_currency_extracted_from_live_sample_missing_this_round():
    """CURRENCY -> java.math.BigDecimal；本轮取到 LIVE 样本（21 例）=> 移出 LIVE_SAMPLE_MISSING。"""
    assert DATA_TYPE_TO_JAVA_TYPE["CURRENCY"] == "java.math.BigDecimal"
    assert "CURRENCY" not in LIVE_SAMPLE_MISSING
    assert LIVE_CURRENCY_OCCURRENCES == 21


def test_attachment_is_string_in_both_modes():
    """ATTACHMENT 恒为 String（旧结论 D 成立），且是 MULTI_SELECT_DATA_TYPES 成员。"""
    assert DATA_TYPE_TO_JAVA_TYPE["ATTACHMENT"] == "java.lang.String"
    assert "ATTACHMENT" in MULTI_SELECT_DATA_TYPES


# ---------------------------------------------------------------- multiSelect 分支（A/B 反转）
def test_ctpenum_entity_are_multi_select_dependent():
    """A/B 反转：CTPENUM/ENTITY 不是单值 —— 靠 multiSelect 分支。
    字节码依据：DtoAttributeUtil.MULTI_SELECT_DATA_TYPES。"""
    assert MULTI_SELECT_DEPENDENT_DATA_TYPES == ("CTPENUM", "ENTITY")
    assert java_type_for("ENTITY", multi_select=True) == "java.lang.String"
    assert java_type_for("ENTITY", multi_select=False) == "java.lang.Long"
    assert java_type_for("CTPENUM", multi_select=True) == "java.lang.String"
    assert java_type_for("CTPENUM", multi_select=False) == "java.lang.Long"


def test_multi_select_constants_are_live_confirmed_on_condition_carriers():
    """LIVE：条件载体（leftParam）单/多选两态实测与常量一致。"""
    assert MULTI_SELECT_JAVA_TYPE == "java.lang.String"
    assert SINGLE_RELATION_JAVA_TYPE == "java.lang.Long"
    assert (LIVE_LEFT_PARAM_ENTITY_FALSE_LONG, LIVE_LEFT_PARAM_ENTITY_TRUE_STRING) == (152, 17)
    assert (LIVE_LEFT_PARAM_CTPENUM_FALSE_LONG, LIVE_LEFT_PARAM_CTPENUM_TRUE_STRING) == (248, 10)
    for dt in MULTI_SELECT_DATA_TYPES:
        for ms in (True, False):
            assert java_type_for(dt, multi_select=ms) in SIMPLE_JAVA_TYPES


# ---------------------------------------------------------------- ENUM 全名
def test_enum_java_type_is_app_own_java_enum_full_name():
    """C 反转：ENUM 的 javaType 是应用自产 Java 枚举全名，不是 java.lang.String。"""
    assert ENUM_JAVA_TYPE_TEMPLATE == "com.seeyon.{app_name}.enums.{code}"
    assert java_type_for("ENUM") is None                       # 无 app/code => 不可判定
    assert java_type_for("ENUM", app_name="x", enum_code="Y") == "com.seeyon.x.enums.Y"
    assert java_type_mismatches(_holder(dataType="ENUM", javaType="java.lang.String"))
    assert java_type_mismatches(_holder(dataType="ENUM", javaType=None))
    assert java_type_mismatches(_holder(dataType="ENUM",
                                        javaType="com.seeyon.x.enums.Y")) == []


# ---------------------------------------------------------------- fail-open（防假阳）
def test_multi_select_missing_is_undecidable_and_must_fail_open():
    """真 holder **从不携带 multiSelect**（LIVE 508/508、全库 514/514）
    => 对 CTPENUM/ENTITY 判据不可判定 => 必须放行（宁可漏报，不可假阳）。"""
    assert HOLDER_MULTI_SELECT_ALWAYS_ABSENT is True
    assert LIVE_HOLDER_WITH_MULTI_SELECT == 0
    assert (LIVE_HOLDER_COUNT_RELEASE, LIVE_HOLDER_COUNT_ALL) == (508, 514)
    for dt in MULTI_SELECT_DEPENDENT_DATA_TYPES:
        for jt in ("java.lang.String", "java.lang.Long", "weird.Type"):
            assert java_type_mismatches(_holder(dataType=dt, javaType=jt)) == []
    assert java_type_for("ENTITY", multi_select=None) is None
    assert java_type_for("CTPENUM", multi_select=None) is None


def test_unlisted_and_missing_datatype_are_passed_through():
    """未收录类型与无 dataType 一律放行（不猜）。"""
    for dt in ("OBJECT", "ARRAY", "MAP", "SORTORDER", "METADATA", "DTO", "ATTACHMENT_x", ""):
        assert java_type_mismatches(_holder(dataType=dt, javaType="whatever")) == []
    assert java_type_mismatches({}) == []
    assert java_type_mismatches("not a dict") == []


def test_reverse_fails_closed_on_real_mismatch():
    """反面：真配对错误必须被咬住（否则就是纯放行的假绿）。"""
    for dt, jt, want in (("INTEGER", "java.lang.String", "java.lang.Integer"),
                         ("BOOLEAN", "java.lang.String", "java.lang.Boolean"),
                         ("BIGINTEGER", "java.lang.Integer", "java.lang.Long"),
                         ("DECIMAL", "java.lang.Double", "java.math.BigDecimal"),
                         ("DATETIME", "java.lang.String", "java.util.Date"),
                         ("STRING", "java.lang.Long", "java.lang.String")):
        errs = java_type_mismatches(_holder(dataType=dt, javaType=jt))
        assert errs, "%s/%s 应判不配对（若放行即为假绿）" % (dt, jt)
        assert want in errs[0]


def test_holder_missing_java_type_is_caught_for_decidable_types():
    assert java_type_mismatches(_holder(dataType="INTEGER", javaType=None))
    assert java_type_mismatches(_holder(dataType="STRING", javaType=""))


# ---------------------------------------------------------------- 权威域（适用边界）
def test_authoritative_domain_is_only_mapping_rows_holders():
    """本判据的权威域只有 DATA_MAPPING holder 两处；其余载体（leftParam/selectParam/
    attrType/output）不得套用 —— 全库 54 条残差即由此产生（54/54 在 holder 之外）。"""
    for p in ("/nodes[1]/mappingRule/mappingRows[3]/targetField",
              "/nodes[1]/mappingRule/mappingRows[3]/value/reference"):
        assert is_authoritative_holder(p), p
    for p in ("/nodes[0]/condition[0]/conditions[0]/leftParam",
              "/nodes[1]/conditions[2]/nodes[1]/value/selectParam",
              "/nodes[0]/conditions[0]/nodes[0]/output",
              "/nodes[4]/attrs[6]/attrType",
              "/nodes[0]/mappingRule/mappingRows[3]/mappingMode"):
        assert not is_authoritative_holder(p), p
    assert HOLDER_PATH_SUFFIXES == ("mappingRule.mappingRows[].targetField",
                                    "mappingRule.mappingRows[].value.reference")
    for c in ("leftParam", "selectParam", "attrs[].attrType", "output"):
        assert c in NON_HOLDER_CARRIERS
    assert LIVE_NEW_TABLE_RESIDUAL_ALL == 54


# ---------------------------------------------------------------- 对抗自证：旧表假阳
def test_adversarial_old_table_would_false_positive_on_hostile_sample():
    """对抗自证：把「CTPENUM/ENTITY 恒 Long、ENUM 恒 String」的旧表装回来，
    本轮的 hostile 样本必须让它假阳、而新表放行。"""
    old = dict(DATA_TYPE_TO_JAVA_TYPE)
    old.update({"CTPENUM": "java.lang.Long", "ENTITY": "java.lang.Long",
                "ENUM": "java.lang.String"})

    def old_bad(h):
        dt = str(h.get("dataType") or "").strip().upper()
        if dt not in old:
            return False
        jt = h.get("javaType")
        return bool(jt) and jt != old[dt]

    hostile = [
        {"dataType": "ENTITY", "javaType": "java.lang.Long"},      # 旧表放行（真单选形态）
        {"dataType": "ENTITY", "javaType": "java.lang.String"},    # 旧表假阳（多选形态）
        {"dataType": "CTPENUM", "javaType": "java.lang.String"},   # 旧表假阳
        {"dataType": "ENUM", "javaType": "com.seeyon.x.enums.Y"},  # 旧表假阳（真名）
    ]
    assert old_bad(hostile[1]) and old_bad(hostile[2]) and old_bad(hostile[3])
    for h in hostile:
        assert java_type_mismatches(h) == [], h           # 新表：全部放行


def test_live_counts_are_pinned_and_two_scopes_are_not_interchangeable():
    """两个口径不可混用（上一轮把样本口径写成「全库」，本轮更正）：
      样本口径 app=3289082814923688017 state=20 LIMIT 500：载体 7666 / 旧表假阳 106 / 新表 0
      全库口径（4734 条 microflow）：载体 28855 / 旧表假阳 296 / 新表残差 54（全在 holder 外）
      真 holder 口径                ：旧表假阳 2 / 新表 0"""
    assert LIVE_APP_ID_DATA_TYPE == "3289082814923688017"
    assert "LIMIT 500" in LIVE_SAMPLE_SCOPE and "state=20" in LIVE_SAMPLE_SCOPE
    assert (LIVE_BROAD_CARRIER_COUNT_SAMPLE, LIVE_OLD_TABLE_FALSE_POSITIVES_SAMPLE) == (7666, 106)
    assert (LIVE_BROAD_CARRIER_COUNT_ALL, LIVE_OLD_TABLE_FALSE_POSITIVES_ALL) == (28855, 296)
    assert LIVE_NEW_TABLE_RESIDUAL_ALL == 54
    assert LIVE_OLD_TABLE_FALSE_POSITIVES_HOLDER == 2
    assert LIVE_NEW_TABLE_RESIDUAL_ALL > 0, "全库残差非 0 => 「0 假阳」只属样本口径，模块须写明"


# ---------------------------------------------------------------- 跨表对账
def test_collision_table_agrees_with_forward_and_reverse_tables():
    """JAVA_TYPE_TO_DATA_TYPES 只由**固定映射**构建（条件类型 CTPENUM/ENTITY/ATTACHMENT
    不出现在其中）；JAVA_TYPE_COLLISIONS 另外把「条件类型在该 javaType 下的必然落点」并入。
    两者关系必须精确可复算，不允许手写漂移。"""
    assert JAVA_TYPE_COLLISIONS["java.math.BigDecimal"] == ("DECIMAL", "CURRENCY")
    assert JAVA_TYPE_COLLISIONS["java.util.Date"] == ("DATE", "DATETIME")
    # java.lang.Long = 固定映射(BIGINTEGER) + 条件类型取单选形态(CONTENT: CTPENUM/ENTITY)
    assert JAVA_TYPE_TO_DATA_TYPES["java.lang.Long"] == ("BIGINTEGER",)
    assert set(JAVA_TYPE_COLLISIONS["java.lang.Long"]) == (
        set(JAVA_TYPE_TO_DATA_TYPES["java.lang.Long"]) | set(MULTI_SELECT_DEPENDENT_DATA_TYPES))
    # java.lang.String = 固定映射(STRING/MULTILINESTRING/TIME/ATTACHMENT)
    #                    + 条件类型取多选形态(CTPENUM/ENTITY) —— ATTACHMENT 已在固定映射里
    assert set(JAVA_TYPE_TO_DATA_TYPES["java.lang.String"]) == {
        "STRING", "MULTILINESTRING", "TIME", "ATTACHMENT"}
    assert set(JAVA_TYPE_COLLISIONS["java.lang.String"]) == (
        set(JAVA_TYPE_TO_DATA_TYPES["java.lang.String"]) | set(MULTI_SELECT_DEPENDENT_DATA_TYPES))
    # 每个可产出的 javaType 都必须在 collision 表里
    assert set(DATA_TYPE_TO_JAVA_TYPE.values()) <= set(JAVA_TYPE_COLLISIONS)
    # 条件类型两态落点都被 collision 覆盖
    for dt in MULTI_SELECT_DATA_TYPES:
        for ms in (True, False):
            jt = java_type_for(dt, multi_select=ms)
            assert jt in JAVA_TYPE_COLLISIONS and dt in JAVA_TYPE_COLLISIONS[jt]


def test_data_type_codes_match_boot_enum_cfr():
    assert DATA_TYPE_CODES["STRING"] == 0 and DATA_TYPE_CODES["INTEGER"] == 1
    assert DATA_TYPE_CODES["ENTITY"] == 11 and DATA_TYPE_CODES["ENUM"] == 13
    assert DATA_TYPE_CODES["CTPENUM"] == 18 and DATA_TYPE_CODES["TIME"] == 10
    assert DATA_TYPE_CODES["CURRENCY"] == 17
    assert len(DATA_TYPE_CODES) == 19


# ---------------------------------------------------------------- normalize
def test_normalize_only_touches_decidable_holders():
    """normalize 走 mappingRows 两处；不可判定（CTPENUM/ENTITY 无 multiSelect）不猜、保持原值。"""
    node = {"mappingRule": {"mappingRows": [
        {"targetField": {"dataType": "INTEGER", "javaType": "java.lang.String", "path": "a"},
         "value": {"reference": {"dataType": "ENTITY", "javaType": "java.lang.String", "path": "b"}}},
    ]}}
    fixed = normalize_holder_java_types(node)
    assert fixed == 1                                     # 只修 INTEGER；ENTITY 放行
    row = node["mappingRule"]["mappingRows"][0]
    assert row["targetField"]["javaType"] == "java.lang.Integer"
    assert row["value"]["reference"]["javaType"] == "java.lang.String"   # 未猜、原样保留
    assert normalize_holder_java_types({}) == 0
    assert normalize_holder_java_types({"nodes": []}) == 0


def test_normalize_never_blanks_enum_java_type():
    node = {"mappingRule": {"mappingRows": [
        {"targetField": {"dataType": "ENUM", "javaType": "com.seeyon.x.enums.Y"}, "value": {}},
    ]}}
    assert normalize_holder_java_types(node) == 0
    assert node["mappingRule"]["mappingRows"][0]["targetField"]["javaType"] == "com.seeyon.x.enums.Y"


# ---------------------------------------------------------------- 模块自洽 / 防陈旧
def test_module_records_both_evidence_layers_and_no_placeholder_markers():
    assert "VERIFIED_STATIC_BYTECODE" in MODULE_SRC
    assert "LIVE" in MODULE_SRC
    assert "udc-common-5.3.517.jar" in MODULE_SRC
    assert "30085724949703b1c2f96a37e72813a6ed9e7b752ebc206c7a47d26afceb30d7" in MODULE_SRC
    assert "DtoAttributeUtil" in MODULE_SRC and "ExprDataTypeTransferUtil" in MODULE_SRC
    for bad in ("TO" + "DO", "FIX" + "ME", "XX" + "X", "T" + "BD"):
        assert bad not in MODULE_SRC, "模块含占位标记 " + bad


def test_module_import_is_side_effect_free():
    ns = {}
    exec(compile(MODULE_SRC, str(MODULE_PATH), "exec"), ns)
    assert ns["DATA_TYPE_TO_JAVA_TYPE"]["BIGINTEGER"] == "java.lang.Long"
    assert ns["is_authoritative_holder"]("/a/mappingRows[0]/targetField") is True


def test_imported_values_agree_with_a_fresh_parse_of_the_source():
    """防「陈旧 .pyc」假绿（同族护栏约定）：等长同秒改写不使 pyc 失效，
    import 可能与当前源码分歧 —— 在此把两者钉死相等。

    ★ 锚点已迁到 tools 固定装置，此处核对 ANCHOR_SRC（装置真源）。"""
    ns = {}
    exec(compile(ANCHOR_SRC, str(ANCHOR_PATH), "exec"), ns)
    for name in ("LIVE_BROAD_CARRIER_COUNT_SAMPLE", "LIVE_OLD_TABLE_FALSE_POSITIVES_SAMPLE",
                 "LIVE_NEW_TABLE_RESIDUAL_ALL", "LIVE_HOLDER_COUNT_ALL",
                 "LIVE_CURRENCY_OCCURRENCES"):
        assert ns[name] == globals()[name], (
            "import 到的 " + name + " = " + repr(globals()[name])
            + " 与源码重新解析结果 " + repr(ns[name]) + " 不一致 => 读到陈旧 .pyc")
