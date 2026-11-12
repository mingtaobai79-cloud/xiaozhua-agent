"""设置域设计态元数据查询模型测试（订单应用元数据面）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.design_metadata_model import (
    METADATA_CONTROLLERS, METADATA_QUERIES, metadata_api_map, design_metadata_summary)


def test_all_metadata_queries_resolve():
    m = metadata_api_map()
    assert len(m) == len(METADATA_QUERIES)
    unresolved = [k for k, v in m.items() if not v["resolved"]]
    assert not unresolved, f"未解析: {unresolved}"


def test_entity_and_refer_paths():
    m = metadata_api_map()
    assert m["实体_按id或fullName"]["full_path"] == "/udc/meta-data/select-entity"
    assert m["参照_按实体"]["full_path"] == "/udc/meta-data/select-refer-by-entity"
    assert m["参照_按实体含微服务"]["full_path"] == "/udc/meta-data/refer-and-app"


def test_enum_paths():
    m = metadata_api_map()
    assert m["库枚举_按应用"]["full_path"] == "/udc/meta-data/select-ctp-enum-by-app"
    assert m["java枚举_按应用"]["full_path"] == "/udc/meta-data/select-java-enum-by-app"
    assert m["库枚举项"]["full_path"] == "/udc/meta-data/select-ctp-enum-item"


def test_page_and_layout_paths():
    m = metadata_api_map()
    assert m["页面_按应用全量"]["full_path"] == "/udc/meta-data/select-all-page-by-app"
    assert m["页面_菜单树含页面"]["full_path"] == "/udc/meta-data/select-function-node-with-page-tree"
    assert m["外框_按应用"]["full_path"] == "/udc/meta-data/select-all-layout-by-app"


def test_design_metadata_kinds():
    s = design_metadata_summary()
    assert s["api_count"] == 47
    kinds = s["kinds"]
    assert kinds["Agg"] == 9
    assert kinds["DTO"] == 8
    assert kinds["AppService"] == 5
    assert kinds["Rest"] == 4
    assert kinds["Entity"] == 4
