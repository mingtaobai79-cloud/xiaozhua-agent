"""栏目域 API 模型测试。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.column_api_model import (
    COLUMN_CONTROLLERS, COLUMN_OPS, column_api_map, column_summary)


def test_all_column_ops_resolve():
    m = column_api_map()
    assert len(m) == len(COLUMN_OPS)
    unresolved = [k for k, v in m.items() if not v["resolved"]]
    assert not unresolved, f"未解析: {unresolved}"


def test_page_info_paths():
    m = column_api_map()
    assert m["页面_创建基础信息"]["full_path"] == "/udc/page-info/base-info/create"
    assert m["页面_批量创建含schema"]["full_path"] == "/udc/page-info/batch-create"
    assert m["页面_详情"]["full_path"] == "/udc/page-info/detail/{id}"
    assert m["页面_按应用树"]["full_path"] == "/udc/page-info/select-by-appId/{appId}"


def test_page_layout_paths():
    m = column_api_map()
    assert m["外框_可用列表"]["full_path"] == "/udc/page-layout/search-no-page-available"
    assert m["外框_套用"]["controller"] == "PageLayoutController" if "外框_套用" in m else True
    assert m["外框_更新标题"]["full_path"] == "/udc/page-layout/base-info/update/caption"


def test_portlet_paths():
    m = column_api_map()
    assert m["栏目_创建"]["full_path"] == "/udc/portlet/create-portlet"
    assert m["栏目_排序"]["full_path"] == "/udc/portlet/sort"
    assert m["栏目分组_按应用"]["full_path"] == "/udc/portlet-group/select-by-appId/{appId}"


def test_template_paths():
    m = column_api_map()
    assert m["模板_发布"]["full_path"] == "/udc/page-template/publish"
    assert m["模板_查重"]["full_path"] == "/udc/page-template/check-name"
    assert m["模板分类_树"]["full_path"] == "/udc/page-template-class/select-tree"


def test_summary_seven_controllers():
    s = column_summary()
    assert len(s["controllers"]) == 7
    assert s["controllers"]["PageInfoController"]["api_count"] == 25
    assert s["controllers"]["PageLayoutController"]["api_count"] == 18
