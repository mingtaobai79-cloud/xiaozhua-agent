"""应用域 8 子菜单 → API 映射测试（侧边栏导航结构落地）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.application_submenu_model import (
    APP_SUBMENUS, submenu_apis, application_submenu_catalog)

_EIGHT_SUBMENUS = ["页面测试", "沙箱测试", "发布版本", "依赖设置", "应用", "组件",
                   "团队设置", "应用主题"]


def test_eight_application_submenus():
    assert list(APP_SUBMENUS) == _EIGHT_SUBMENUS


def test_submenus_resolve_to_real_apis():
    """除应用主题（前端为主）外，7 子菜单声明的 API 全部在 udc-web 契约中命中。"""
    for sm in _EIGHT_SUBMENUS:
        r = submenu_apis(sm)
        if sm == "应用主题":
            assert r["declared"] == 0
            continue
        assert not r["unmatched"], f"{sm} 未匹配: {r['unmatched']}"
        assert r["matched"] >= r["declared"]


def test_sandbox_test_maps_to_deploy_normal():
    r = submenu_apis("沙箱测试")
    names = {a["method"] for a in r["apis"]}
    assert "deployNormal" in names          # TEST 构建入口
    assert "getBuildInfo" in names


def test_publish_version_maps_to_app_online():
    r = submenu_apis("发布版本")
    names = {a["method"] for a in r["apis"]}
    assert "appOnline" in names and "appOnlineNew" in names
    assert "selectAppVersionByAppGuid" in names


def test_team_settings_maps_to_role_resource():
    r = submenu_apis("团队设置")
    names = {a["method"] for a in r["apis"]}
    assert "selectRoleResource" in names and "selectUserRole" in names
    assert "handoverApp" in names


def test_catalog_serializable():
    import json
    c = application_submenu_catalog()
    blob = json.loads(json.dumps(c, ensure_ascii=False))
    assert len(blob["submenus"]) == 8
