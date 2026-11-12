"""实体页面 6 tab 功能字典测试（ENTITY-PAGE-INVENTORY §2.7-§2.8/§3 证据）。"""
from components.udc.entity_page_model import (
    DELETE_TRAP,
    ENTITY_TAB_KEYS,
    EXPRESSION_ENDPOINTS,
    INDEX_DISABLE_MATRIX,
    INDEX_FIELD_MAX,
    INDEX_FIELD_IDS_FORMAT,
    INDEX_NAME_PREFIX,
    PARAMSTYPE_EXCEPTIONS,
    PERMISSION_MODEL,
    RENDERED_TAB_KEYS,
    RESERVED_NOT_RENDERED,
    TAB_VISIBILITY_RULES,
    TAB_WRITE_OPS,
    VERSION_CONSTRAINT,
    EntityTabBinding,
    catalog,
    check_delete_plan,
)


def test_eight_tab_keys_six_rendered():
    assert len(ENTITY_TAB_KEYS) == 8
    assert set(RENDERED_TAB_KEYS) == {"basicInfo", "attributeSet", "rule", "refer", "event", "index"}
    # relation/data 是预留 key（bundle 无消费，§2.8.1 定性）
    assert set(RESERVED_NOT_RENDERED) == {"relation", "data"}


def test_reserved_tab_binding_fails():
    b = EntityTabBinding(tab="relation", planned_ops=["whatever"])
    assert b.validate()["status"] == "FAIL"
    assert any("预留" in e for e in b.validate()["errors"])


def test_tab_visibility_conditions():
    assert "ONE2MANY" in TAB_VISIBILITY_RULES["refer"]
    assert "isThirdEntity" in TAB_VISIBILITY_RULES["rule"]
    assert "CAF" in TAB_VISIBILITY_RULES["basicInfo"]


def test_params_type_exceptions_registry_sizes():
    # §2.7.4：Long/String/Map/数组包装10个/[String] —— 至少 14 个特例
    assert len(PARAMSTYPE_EXCEPTIONS) >= 14
    assert PARAMSTYPE_EXCEPTIONS["udcIndexEntityListPost"].startswith("Long")
    assert PARAMSTYPE_EXCEPTIONS["udcDataTransferObjectCreateDtoWithAttrsPost"].startswith("[")


def test_exception_op_requires_declared_params_shape():
    b = EntityTabBinding(tab="index", planned_ops=["udcIndexEntityListPost"])
    r = b.validate()
    assert r["status"] == "FAIL"
    assert any("paramsType 特例" in e for e in r["errors"])
    b2 = EntityTabBinding(tab="index", planned_ops=["udcIndexEntityListPost"],
                          params_exceptions_used=["udcIndexEntityListPost"])
    assert b2.validate()["status"] != "FAIL"


def test_unproven_op_warns_not_fails():
    b = EntityTabBinding(tab="event", planned_ops=["someNewOp"])
    assert b.validate()["status"] == "UNVERIFIED"


def test_delete_trap_guard():
    rec = check_delete_plan("udcEntityAttributeBatchDeletePost", 1)
    assert rec["decision"] == "RECOMMEND_SINGLE_DELETE"
    assert "content>=1" in rec["verify"]
    ok = check_delete_plan("udcEntityAttributeDeletePost", 1)
    assert ok["decision"] == "ALLOWED"


def test_delete_trap_literal_registered():
    assert "BOOT_0000" in DELETE_TRAP["observed"]
    assert "content=0" in DELETE_TRAP["observed"]


def test_expression_four_endpoints():
    assert len(EXPRESSION_ENDPOINTS) == 4
    assert EXPRESSION_ENDPOINTS["/expression/schema"]["body_required"]
    assert "BOOT_3002" in EXPRESSION_ENDPOINTS["/expression/schema"]["note"]


def test_index_matrix_and_prefix():
    assert INDEX_NAME_PREFIX == {"NORMAL": "idx_", "UNIQUE": "uk_"}
    assert INDEX_FIELD_MAX == 5
    assert INDEX_FIELD_IDS_FORMAT == "comma-joined-string"
    assert any("已发布" in v for v in INDEX_DISABLE_MATRIX.values())


def test_permission_model_two_layers():
    blob = " ".join(PERMISSION_MODEL)
    assert "@HasRole" in blob and "CAF" in blob and "udc_role_resource" in blob


def test_version_constraint_registered():
    assert "已上架版本" in VERSION_CONSTRAINT


def test_catalog_roundtrip():
    import json
    c = catalog()
    back = json.loads(json.dumps(c, ensure_ascii=False))
    assert len(back["write_ops"]) == 6
    assert len(back["params_type_exceptions"]) >= 14


def test_write_ops_cover_all_rendered_tabs():
    assert set(TAB_WRITE_OPS) == set(RENDERED_TAB_KEYS)
