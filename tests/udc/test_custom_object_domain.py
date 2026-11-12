"""自定义对象域：构造器 + 校验器 + 引用分析的落位契约。

锁住三件事（防止又被摊平到仓库各处）：
  1. 实现在 components/udc/setting/（设置域，不越界到其它域）
  2. 事实落在 core/facts/udc/setting/custom-object/
  3. 契约登记在 registry（可调用，不只是文档）
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.setting.custom_object_constraints import (
    build_custom_object_body,
    build_custom_object_delete_body,
    validate_custom_object_body,
    validate_custom_object_delete_body,
)

APP = "app9000000000000000001"
GUID = "2275741415570096882"


# ---------------------------------------------------------------- 构造器

def test_build_body_has_all_required_slots():
    """平台 BOOT_1001 点名的必填槽位必须齐全。"""
    b = build_custom_object_body(APP, GUID, "显示名", "objCode")
    assert b["appId"] == APP
    assert b["appGuid"] == GUID
    assert b["caption"] == "显示名"
    assert b["name"] == "objCode"
    assert b["source"] == 1
    assert b["dataStatus"] is False
    assert b["hostAppName"] is None


def test_build_body_rejects_empty_name():
    import pytest
    with pytest.raises(ValueError, match="name"):
        build_custom_object_body(APP, GUID, "显示名", "  ")


def test_build_body_rejects_empty_caption():
    import pytest
    with pytest.raises(ValueError, match="caption"):
        build_custom_object_body(APP, GUID, "", "objCode")


def test_build_body_rejects_empty_app_guid():
    import pytest
    with pytest.raises(ValueError, match="appGuid"):
        build_custom_object_body(APP, "", "显示名", "objCode")


# ---------------------------------------------------------------- 校验器

def test_validate_accepts_complete_body():
    b = build_custom_object_body(APP, GUID, "显示名", "objCode")
    assert validate_custom_object_body(b) == []


def test_validate_catches_each_missing_slot():
    """每个必填槽位缺失都要被本地拦下（平台侧是 BOOT_1001 逐字段点名）。"""
    for key, hint in (("appId", "appId"),
                      ("appGuid", "appGuid"),
                      ("caption", "caption"),
                      ("name", "name"),
                      ("source", "source")):
        b = build_custom_object_body(APP, GUID, "显示名", "objCode")
        del b[key]
        errs = validate_custom_object_body(b)
        assert any(hint in e for e in errs), f"缺 {key} 未被拦: {errs}"


def test_delete_body_requires_id():
    """缺 id 时平台仍返回 BOOT_0000 但 content=0 —— 本地必须拦。"""
    errs = validate_custom_object_delete_body({"appId": APP})
    assert any("id" in e for e in errs), errs


def test_delete_body_ok():
    b = build_custom_object_delete_body(APP, "12345")
    assert validate_custom_object_delete_body(b) == []
    assert b["id"] == "12345"


# ---------------------------------------------------------------- 落位

def test_impl_is_in_setting_domain():
    p = ROOT / "components" / "udc" / "setting" / "custom_object_constraints.py"
    assert p.exists(), f"自定义对象实现未归位到设置域: {p}"
    assert not (ROOT / "components" / "udc" / "custom_object_constraints.py").exists()


def test_fact_grid_exists():
    d = ROOT / "core" / "facts" / "udc" / "setting" / "custom-object"
    assert d.is_dir(), f"缺自定义对象事实目录: {d}"
    assert (d / "create.md").exists(), "缺自定义对象事实格 create.md"


def test_contracts_registered():
    """4 条自定义对象契约必须登记（可调用，不只是文档）。"""
    from components.platform_operations.registry import UdcOperationRegistry
    reg = UdcOperationRegistry.default()
    for op in ("udc.custom_object.create", "udc.custom_object.update",
               "udc.custom_object.delete", "udc.custom_object.list"):
        assert reg.has(op), f"契约未登记: {op}"


def test_write_contracts_flagged_and_need_scope():
    from components.platform_operations.registry import UdcOperationRegistry
    reg = UdcOperationRegistry.default()
    for op in ("udc.custom_object.create", "udc.custom_object.update",
               "udc.custom_object.delete"):
        c = reg.get(op)
        assert c.write is True, f"{op} 应为写契约"
        assert "WriteScope" in " ".join(c.verification_rules), \
            f"{op} 须提示需显式 WriteScope"


def test_list_contract_documents_no_query_operation():
    """平台**无**自定义对象查询 operation —— 这是事实，必须写在契约里，不能装作有。"""
    from components.platform_operations.registry import UdcOperationRegistry
    reg = UdcOperationRegistry.default()
    c = reg.get("udc.custom_object.list")
    # 「平台无查询 operation」这条事实要出现在契约的任一处（rules 或 evidence）
    blob = " ".join(c.verification_rules) + " " + str(c.evidence)
    assert "无" in blob and "查询 operation" in blob, blob
    # 并且必须明说列表走 DB
    assert "DB" in " ".join(c.verification_rules), c.verification_rules


def test_delete_contract_warns_success_code_is_not_enough():
    """删 id 缺失时平台仍回 BOOT_0000 但 content=0 —— 契约必须警告回读。"""
    from components.platform_operations.registry import UdcOperationRegistry
    reg = UdcOperationRegistry.default()
    c = reg.get("udc.custom_object.delete")
    rules = " ".join(c.verification_rules)
    assert "content=0" in rules and "回读" in rules, rules
