"""测试：插件契约边界（udc-plugin-api 5.3.517）约束模型。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.plugin_api_constraints import (
    APP_FEATURE_TYPES, APP_TYPE_STEREOTYPES, APP_TYPE_DEFAULT_STEREOTYPE,
    APP_TYPE_DEPENDS, APP_TYPE_DYNAMIC, AUTH_OPERATION_TYPES,
    PLUGIN_API_SERVICES, SERIAL_SCHEME_OPERATIONS,
    validate_entity_stereotype_for_app, validate_app_type,
    app_type_depends_complete, default_stereotype_for,
)


def test_app_feature_types():
    assert APP_FEATURE_TYPES == ("BUSINESS", "STANDARD", "FORM", "INTEGRATION", "LAYOUT", "ONLYPAGE")
    assert APP_TYPE_DYNAMIC["BUSINESS"] is False
    assert APP_TYPE_DYNAMIC["FORM"] is True


def test_app_type_stereotype_matrix():
    # ★约束：标准应用只能建 standard 版型；业务应用 4 种
    assert APP_TYPE_STEREOTYPES["STANDARD"] == ("standard",)
    assert APP_TYPE_STEREOTYPES["BUSINESS"] == ("archive", "archiveTree", "bill", "standard")
    assert APP_TYPE_STEREOTYPES["FORM"] == ("standard", "form")
    assert APP_TYPE_DEFAULT_STEREOTYPE["FORM"] == "form"
    assert default_stereotype_for("BUSINESS") == "standard"


def test_app_type_depends():
    # 业务应用依赖 9 个宿主；集成应用只依赖 2 个
    assert len(APP_TYPE_DEPENDS["BUSINESS"]) == 9
    assert APP_TYPE_DEPENDS["INTEGRATION"] == ("organization", "ctp-user")
    assert "bpm" in APP_TYPE_DEPENDS["FORM"]


def test_auth_operation_types():
    assert AUTH_OPERATION_TYPES == {"CREATE": 1, "DELETE": 2, "UPDATE": 3, "SELECT": 4}


def test_plugin_api_catalog():
    assert len(PLUGIN_API_SERVICES) == 24
    assert PLUGIN_API_SERVICES["ApplicationAppService"] == 52
    assert SERIAL_SCHEME_OPERATIONS == (
        "selectSerialScheme", "selectSerialSchemeById", "selectSerialRange",
        "createEasyScheme", "selectDepAppSerialScheme")


def test_validate_stereotype():
    # 合法
    assert validate_entity_stereotype_for_app("STANDARD", "standard") == []
    assert validate_entity_stereotype_for_app("BUSINESS", "bill") == []
    # 非法：标准应用建 bill 版型
    errs = validate_entity_stereotype_for_app("STANDARD", "bill")
    assert any("不支持实体版型" in e for e in errs)
    # 非法：未知应用类型
    assert validate_entity_stereotype_for_app("BOGUS", "standard")[0].startswith("未知应用类型")
    assert validate_app_type("BOGUS") != []
    assert validate_app_type("FORM") == []


def test_depends_complete():
    ok = app_type_depends_complete("INTEGRATION", ["organization", "ctp-user"])
    assert ok == []
    miss = app_type_depends_complete("FORM", ["organization"])
    assert any("bpm" in e for e in miss)
