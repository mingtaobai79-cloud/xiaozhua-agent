"""菜单域 API 模型测试。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.menu_api_model import (
    MENU_CONTROLLERS, MENU_OPS, menu_api_map, menu_summary)


def test_all_menu_ops_resolve():
    m = menu_api_map()
    assert len(m) == len(MENU_OPS)
    unresolved = [k for k, v in m.items() if not v["resolved"]]
    assert not unresolved, f"未解析: {unresolved}"


def test_function_node_paths():
    m = menu_api_map()
    assert m["菜单_创建功能"]["full_path"] == "/udc/function"
    assert m["菜单_创建功能引用"]["full_path"] == "/udc/function/create/function-refer"
    assert m["菜单_设默认页"]["full_path"] == "/udc/function/default_page"
    assert m["菜单_功能树"]["full_path"] == "/udc/function/select/function-tree"
    assert m["菜单_页面入参"]["full_path"] == "/udc/function/page/in_params/{referId}"


def test_page_route():
    m = menu_api_map()
    assert m["路由_详情"]["controller"] == "PageRouteController"


def test_summary_two_controllers():
    s = menu_summary()
    assert len(s["controllers"]) == 2
    assert s["controllers"]["FunctionNodeController"]["api_count"] == 19
