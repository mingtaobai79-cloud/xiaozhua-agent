"""测试：低代码运行时框架（udc-starter-lowcode 5.3.517）约束模型。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.lowcode_constraints import (
    FLOW_ACTION_TYPES, RECURSIVE_TYPES, ATTR_SNAPSHOT_REF_TYPES,
    ENTITY_META_FIELDS, ATTRIBUTE_META_FIELDS, CURD_SERVICE_METHODS,
    CALLBACK_TYPES, LOWCODE_BASE_SERVICES, LOWCODE_CACHE_CLASSES,
    CACHE_ANNOTATIONS, validate_entity_meta, validate_flow_action_type,
)


def test_enum_domains():
    assert FLOW_ACTION_TYPES == {
        "NONE": 0, "SAVE": 1, "SEND": 2, "REPEAL": 3, "TASK_TO_SENDER": 4, "RE_SEND": 5}
    assert RECURSIVE_TYPES == {"TEMPLATE": 0, "FORWARD": 1}
    assert ATTR_SNAPSHOT_REF_TYPES == {"ENTITY": 0, "CTP_ENUM": 1}


def test_meta_fields():
    # EntityMeta 关键字段
    for f in ("name", "fullName", "entityTable", "stereotype", "entityCategory",
              "entityClass", "dtoClass", "children"):
        assert f in ENTITY_META_FIELDS
    # AttributeMeta 关键字段
    for f in ("dataType", "realDataType", "relationEntity", "multiSelect", "maskType"):
        assert f in ATTRIBUTE_META_FIELDS


def test_curd_contract():
    names = {m for m, _ in CURD_SERVICE_METHODS}
    # CRUD 四件套 + 级联查 + 批量
    for m in ("create", "update", "deleteById", "selectCascadeById",
              "createBatch", "updateBatch", "deleteByIds"):
        assert m in names
    assert len(CURD_SERVICE_METHODS) == 22


def test_callbacks():
    # 13 个生命周期回调
    assert len(CALLBACK_TYPES) == 13
    for c in ("PreCreateCallBack", "PreUpdateCallBack", "ValidateCallBack",
              "PermissionCallBack", "SecretCallBack", "ApprovalCallBack", "BillStateCallBack"):
        assert c in CALLBACK_TYPES


def test_base_services_and_cache():
    assert LOWCODE_BASE_SERVICES == (
        "BaseEntityCurdService", "BaseMicroFlowService",
        "BaseDataFlowService", "BaseDeductionService")
    assert "EntityCacheManager" in LOWCODE_CACHE_CLASSES
    assert "RCacheable" in CACHE_ANNOTATIONS


def test_validate_entity_meta():
    ok = {"name": "Order", "fullName": "com.seeyon.Order",
          "entityTable": "order", "stereotype": "standard", "entityCategory": "ENTITY"}
    assert validate_entity_meta(ok) == []
    errs = validate_entity_meta({"name": "Order"})
    assert any("fullName" in e for e in errs)
    assert any("entityTable" in e for e in errs)


def test_flow_action():
    assert validate_flow_action_type("SEND") is True
    assert validate_flow_action_type("BOGUS") is False
