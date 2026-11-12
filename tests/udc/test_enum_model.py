"""设置域枚举管理模型测试 —— 枚举/项/分类/运行时 API 映射。

数据源：enum_model（udc-web-5.3.517 javap，STATIC_BYTECODE）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.setting.enum_model import (
    ENUM_CONTROLLERS, ENUM_OPS, enum_api_map, enum_controller_summary)


def test_all_enum_ops_resolve():
    m = enum_api_map()
    assert len(m) == len(ENUM_OPS)
    unresolved = [k for k, v in m.items() if not v["resolved"]]
    assert not unresolved, f"未解析: {unresolved}"


def test_enum_crud_paths():
    m = enum_api_map()
    assert m["枚举_创建"]["full_path"] == "/udc/udc-enum"
    assert m["枚举_修改"]["full_path"] == "/udc/udc-enum/update"
    assert m["枚举_删除"]["full_path"] == "/udc/udc-enum/delete"
    assert m["枚举_详情"]["full_path"] == "/udc/udc-enum/{id}"


def test_enum_item_import_export():
    m = enum_api_map()
    assert m["项_导入"]["full_path"] == "/udc/udc-enum-item/import"
    assert m["项_导出"]["full_path"] == "/udc/udc-enum-item/export"
    assert m["项_批量操作"]["full_path"] == "/udc/udc-enum-item/operate-batch"


def test_runtime_enum_queries():
    m = enum_api_map()
    assert m["运行时_按code查项"]["full_path"] == "/udc/udc-enum-item/search-by-enum-code"
    assert m["运行时_级联树"]["full_path"] == "/udc/udc-enum-item/search-cascade-tree-by-enum-code"


def test_enum_category_by_app():
    m = enum_api_map()
    assert m["分类_按应用查分类+枚举"]["full_path"] == "/udc/udc-enum-category/select-category-and-enum"


def test_summary_shape():
    s = enum_controller_summary()
    assert set(s["controllers"]) == set(ENUM_CONTROLLERS)
    assert s["op_count"] == len(ENUM_OPS)
