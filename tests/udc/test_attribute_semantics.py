"""字段语义模型测试 —— 默认值六件套/参照/多选/唯一性 + 跨文件一致性（防漂移）。"""
from components.udc.attribute_semantics import (
    CREATE_ACCEPTED_SEMANTIC_KEYS,
    DEFAULT_VALUE_KEYS,
    ENTITY_RULE_FLAGS,
    MULTI_SELECT_PEOPLE_COMBO,
    PEOPLE_COMPONENT,
    RELATION_TYPE_NUMERIC_LIVE,
    RELATION_TYPE_STRING,
    AttributeSemantics,
    build_attribute_plan,
    field_default_value_is_not_entity_rule_flag,
)


def test_default_value_six_keys_from_source():
    # AttributeService.java:298-332 逐字六件套
    assert set(DEFAULT_VALUE_KEYS) == {
        "defaultValue", "defaultValueCaption",
        "defaultValueExpressionDesignData", "defaultValueExpressionRuntimeData",
        "defaultValueSystemVariable", "defaultValueIsChange",
    }


def test_multi_select_people_combo():
    assert MULTI_SELECT_PEOPLE_COMBO["dataType"] == "ENTITY"
    assert MULTI_SELECT_PEOPLE_COMBO["relationApp"] == "organization"
    assert "OrgMember" in MULTI_SELECT_PEOPLE_COMBO["relationEntity"]
    assert MULTI_SELECT_PEOPLE_COMBO["multiSelect"] is True


def test_valid_people_multi_field_passes_or_unverified():
    sem = AttributeSemantics(
        name="handler", caption="办理人", data_type="ENTITY",
        relation={"relationType": RELATION_TYPE_STRING,
                  "relationApp": "organization",
                  "relationEntity": "com.seeyon.organization.domain.core.entity.OrgMember"},
        multi_select=True,
    )
    r = sem.validate()
    assert r["status"] in {"PASS", "UNVERIFIED"}
    assert r["component"] == PEOPLE_COMPONENT


def test_multi_select_wrong_datatype_fails():
    sem = AttributeSemantics(name="tags", data_type="STRING",
                             relation={"relationType": RELATION_TYPE_STRING,
                                       "relationEntity": "x"},
                             multi_select=True)
    r = sem.validate()
    assert r["status"] == "FAIL"
    assert any("ENTITY" in e for e in r["errors"])


def test_multi_select_missing_relation_fails():
    sem = AttributeSemantics(name="p", data_type="ENTITY", multi_select=True)
    r = sem.validate()
    assert any("relationType" in e for e in r["errors"])
    assert any("relationEntity" in e for e in r["errors"])


def test_uniqueness_must_be_boolean():
    sem = AttributeSemantics(name="order_no", data_type="STRING", uniqueness="1")  # 字符串 BOOT_3002 教训
    r = sem.validate()
    assert any("Boolean" in e for e in r["errors"])


def test_unknown_default_value_key_fails_six_pack_beyond():
    sem = AttributeSemantics(name="x", default_value={"defaultExpression": "now()"})
    r = sem.validate()
    assert any("六件套" in e for e in r["errors"])


def test_six_pack_keys_are_unverified_for_create_channel():
    # 六件套有装配面证据，但 create 面受键 UNVERIFIED → status 不得为 PASS
    sem = AttributeSemantics(name="created", data_type="DATETIME",
                             default_value={"defaultValueSystemVariable": "创建时间"})
    r = sem.validate()
    assert r["status"] == "UNVERIFIED"
    assert any("UNVERIFIED" in u for u in r["unknowns"])


def test_build_plan_keeps_unverified_keys_out_of_create_body():
    sem = AttributeSemantics(name="no", data_type="STRING", uniqueness=True,
                             default_value={"defaultValue": "AUTO-001"})
    plan = build_attribute_plan(sem)
    assert plan["create_body_proven"]["uniqueness"] is True
    assert "defaultValue" not in plan["create_body_proven"]
    assert plan["plan_only_unverified_keys"] == {"defaultValue": "AUTO-001"}


def test_semantic_whitelist_consistent_with_deployment_plan():
    """跨文件防漂移：attribute_semantics 与 deployment.py 白名单必须同源。"""
    from components.platform_operations.deployment import _ATTR_SEMANTIC_KEYS
    assert set(CREATE_ACCEPTED_SEMANTIC_KEYS) == set(_ATTR_SEMANTIC_KEYS)


def test_datatypes_snapshot_consistent_with_deployment_plan():
    from components.platform_operations.deployment import DATATYPES as DEP_DATATYPES
    from components.udc.attribute_semantics import DATATYPES
    assert set(DATATYPES) == set(DEP_DATATYPES)


def test_entity_rule_flags_boundary():
    assert set(ENTITY_RULE_FLAGS) == {"VALIDATE", "DEFAULT_VALUE", "ASSIGN_VALUE"}
    # 字段 defaultValue ≠ 实体规则 DEFAULT_VALUE 组（边界声明在场）
    assert "DEFAULT_VALUE" in field_default_value_is_not_entity_rule_flag()


def test_relation_forms_both_registered():
    # 两套形态共存不合并（数字 LIVE 形态 / 字符串装配形态）
    assert RELATION_TYPE_STRING != RELATION_TYPE_NUMERIC_LIVE
    sem = AttributeSemantics(name="p", data_type="ENTITY", multi_select=True,
                             relation={"relationType": RELATION_TYPE_NUMERIC_LIVE,
                                       "relationEntity": "com.x.Y"})
    assert sem.validate()["status"] in {"PASS", "UNVERIFIED"}
