"""测试：页面域约束（后端权威）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.page_constraints import (
    PAGE_DEFINITION_REQUIRED, PAGE_LAYOUT_REQUIRED, PAGE_TYPES, OPEN_TYPES,
    FUNCTION_TYPES, PORTLET_TYPES, validate_page_definition, validate_page_layout,
)


def test_page_definition_required():
    assert set(PAGE_DEFINITION_REQUIRED) == {"appId", "relationGroupId", "pageType"}


def test_page_layout_required():
    assert PAGE_LAYOUT_REQUIRED == ("appId",)


def test_page_type_enum():
    assert PAGE_TYPES["LIST"] == 5
    assert PAGE_TYPES["DETAIL"] == 4
    assert PAGE_TYPES["LAYOUT"] == 14
    assert PAGE_TYPES["SUBPAGE"] == 15
    assert len(PAGE_TYPES) == 14  # 13 = 缺（枚举从1跳到14）


def test_other_enums():
    assert OPEN_TYPES == {"WORK_SPACE": 1, "DIALOG": 2}
    assert FUNCTION_TYPES == {"FRONTEND": 0, "BACKEND": 1}
    assert PORTLET_TYPES == {"GROUP": 0, "PORTLET": 1}


def test_validate_page_definition():
    errs = validate_page_definition({"appId": 1})
    assert any("relationGroupId" in e for e in errs) and any("pageType" in e for e in errs)
    ok = {"appId": 1, "relationGroupId": 2, "pageType": "LIST"}
    assert validate_page_definition(ok) == []


def test_validate_page_layout():
    assert validate_page_layout({}) == ["PageLayout 缺必填字段 appId（应用ID）"]
    assert validate_page_layout({"appId": 1}) == []


def test_page_item_required():
    from components.udc.page_constraints import PAGE_ITEM_REQUIRED, PAGE_ITEM_FIELDS, PAGE_CREATE_SERVICE_REQUIREMENTS
    assert PAGE_ITEM_REQUIRED == ("urlType",)
    assert PAGE_ITEM_FIELDS["pageUrl"][0] == "String"
    assert any("urlType" in s for s in PAGE_CREATE_SERVICE_REQUIREMENTS)
