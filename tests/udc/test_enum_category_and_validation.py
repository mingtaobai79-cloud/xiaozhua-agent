"""枚举域：构造器 + 本地校验（契约全部来自 LIVE 证据）

契约来源：
  · 2026-10-20 设计器 UI 抓包（rea capture_browser_scenario）+ ctp_enum DB 回读：
      udcEnumPost 的真实 body 逐字段（name=i18n JSON、code=英文编码、
      appGuid/categoryId/dataStatus/bizType/expansible/enable/enumType/children）
  · 已有 LIVE 报错记录：
      缺 orderNo        → BOOT_1001
      code 传字符串      → BOOT_3002 Failed to convert String to Int
      name 非大写+下划线   → UDC_ENUM_0002（报错说 code，实际校验 name）
  · 分组表结构（本轮 DB 实读 ctp_enum_category）：
      id/tenant_id/create_time/update_time/version/guid/name/description/
      parent_id/order_no/is_delete/app_id/app_guid/host_app_name/is_preset/data_status

缺口背景（补这个能力的理由）：
  components/udc/setting/enum_model.py 记了「分类_创建 -> UdcEnumCategoryController.create」，
  但仓库里原本**没有任何构造器、校验器或提交端点**——知道接口却没能力调用。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

import pytest

APP = 8704025620829192834
APP_GUID = "2275741415570096882"
CATEGORY = "-2165189518708277331"


# ---------------------------------------------------------------- 枚举构造器

def test_build_enum_body_matches_platform_shape():
    """产出必须与设计器真实提交同构（2026-10-20 抓包原文）。"""
    from components.construction.metadata_artifacts import build_enum_body
    b = build_enum_body(APP, "验收枚举2026", "zxjAcceptEnum", order_no=10,
                        category_id=CATEGORY, app_guid=APP_GUID)
    # name 是 i18n JSON 字符串，code 才是英文编码
    assert json.loads(b["name"]) == {"zh_CN": "验收枚举2026"}
    assert b["code"] == "zxjAcceptEnum"
    assert b["orderNo"] == 10
    assert b["categoryId"] == CATEGORY
    assert b["appId"] == str(APP)
    assert b["appGuid"] == APP_GUID
    assert b["dataStatus"] is False
    assert b["bizType"] == "UDC_DESIGN"
    assert b["enumType"] == "SAME_LEVEL"
    assert b["expansible"] is True
    assert b["enable"] is True
    assert b["children"] == []
    assert b["hostAppName"] is None


def test_build_enum_body_defaults_category_to_zero():
    """未指定分组时 categoryId="0"（未归组），不能是 None。"""
    from components.construction.metadata_artifacts import build_enum_body
    b = build_enum_body(APP, "x", "xCode", app_guid=APP_GUID)
    assert b["categoryId"] == "0"


# ---------------------------------------------------------------- 分组构造器

def test_build_category_body_minimal():
    from components.construction.metadata_artifacts import build_enum_category_body
    body = build_enum_category_body(APP, name="测试分组")
    assert body["appId"] == APP
    assert body["name"] == "测试分组"
    assert body["orderNo"] == 100, "缺 orderNo 平台报 BOOT_1001，构造器必须补默认值"


def test_build_category_body_with_parent():
    from components.construction.metadata_artifacts import build_enum_category_body
    body = build_enum_category_body(APP, name="子分组", parent_id=123, order_no=10,
                                    description="说明")
    assert body["parentId"] == 123
    assert body["orderNo"] == 10
    assert body["description"] == "说明"


def test_build_category_body_rejects_empty_name():
    from components.construction.metadata_artifacts import build_enum_category_body
    with pytest.raises(ValueError, match="name"):
        build_enum_category_body(APP, name="")
    with pytest.raises(ValueError, match="name"):
        build_enum_category_body(APP, name="   ")


def test_build_category_body_rejects_bad_parent():
    """parentId 必须是整数或 None；字符串 '123' 要拒（平台要 Long）。"""
    from components.construction.metadata_artifacts import build_enum_category_body
    with pytest.raises(ValueError, match="parent"):
        build_enum_category_body(APP, name="x", parent_id="123")


# ---------------------------------------------------------------- 本地校验

def test_validate_category_catches_missing_orderno():
    from components.udc.setting.enum_constraints import validate_enum_category_body
    errs = validate_enum_category_body({"appId": APP, "name": "x"})
    assert any("orderNo" in e for e in errs), errs


def test_validate_category_passes_complete():
    from components.udc.setting.enum_constraints import validate_enum_category_body
    assert validate_enum_category_body(
        {"appId": APP, "name": "分组A", "orderNo": 100}) == []


def test_validate_enum_passes_platform_real_body():
    """平台真实 body 必须通过本地校验（不能误杀）。"""
    from components.construction.metadata_artifacts import build_enum_body
    from components.udc.setting.enum_constraints import validate_enum_body
    b = build_enum_body(APP, "验收枚举2026", "zxjAcceptEnum", order_no=10,
                        category_id=CATEGORY, app_guid=APP_GUID)
    assert validate_enum_body(b) == []


def test_validate_enum_rejects_plain_text_name():
    """裸文本 name → 平台报 BOOT_1001 枚举编码 不能为空，本地必须提前拦。"""
    from components.udc.setting.enum_constraints import validate_enum_body
    errs = validate_enum_body({
        "appId": str(APP), "code": "xCode", "name": "显示名",
        "orderNo": 10, "appGuid": APP_GUID, "categoryId": "0"})
    assert any("name" in e for e in errs), errs


def test_validate_enum_rejects_name_json_without_zh_cn():
    from components.udc.setting.enum_constraints import validate_enum_body
    errs = validate_enum_body({
        "appId": str(APP), "code": "xCode", "name": json.dumps({"en": "x"}),
        "orderNo": 10, "appGuid": APP_GUID, "categoryId": "0"})
    assert any("zh_CN" in e for e in errs), errs


def test_validate_enum_requires_app_guid():
    """appGuid 必须是 udc_application.guid，不是 appId。"""
    from components.udc.setting.enum_constraints import validate_enum_body
    errs = validate_enum_body({
        "appId": str(APP), "code": "xCode",
        "name": json.dumps({"zh_CN": "x"}),
        "orderNo": 10, "categoryId": "0"})
    assert any("appGuid" in e for e in errs), errs


def test_validate_enum_requires_category_id():
    from components.udc.setting.enum_constraints import validate_enum_body
    errs = validate_enum_body({
        "appId": str(APP), "code": "xCode",
        "name": json.dumps({"zh_CN": "x"}),
        "orderNo": 10, "appGuid": APP_GUID})
    assert any("categoryId" in e for e in errs), errs


def test_validate_enum_requires_code():
    from components.udc.setting.enum_constraints import validate_enum_body
    errs = validate_enum_body({
        "appId": str(APP), "name": json.dumps({"zh_CN": "x"}),
        "orderNo": 10, "appGuid": APP_GUID, "categoryId": "0"})
    assert any("code" in e for e in errs), errs


def test_validate_enum_rejects_missing_orderno():
    from components.udc.setting.enum_constraints import validate_enum_body
    errs = validate_enum_body({
        "appId": str(APP), "code": "xCode",
        "name": json.dumps({"zh_CN": "x"}),
        "appGuid": APP_GUID, "categoryId": "0"})
    assert any("orderNo" in e for e in errs), errs


def _valid_item(**over):
    """平台真实形态的枚举项 body（2026-10-20 报错 + ctp_enum_item 表结构确认）。"""
    b = {"appId": str(APP), "enumId": "1", "enumCode": "SOME_ENUM",
         "name": json.dumps({"zh_CN": "启用"}), "itemValue": "1",
         "parentId": "0", "itemLevel": 1, "leaf": 1, "enable": 1, "orderNo": 10}
    b.update(over)
    return b


def test_validate_enum_item_rejects_missing_item_value():
    """缺 itemValue → 平台报「枚举项编码 不能为空」，本地必须提前拦。"""
    from components.udc.setting.enum_constraints import validate_enum_item_body
    body = _valid_item()
    del body["itemValue"]
    errs = validate_enum_item_body(body)
    assert any("itemValue" in e for e in errs), errs


def test_validate_enum_item_rejects_missing_parent_id():
    """缺 parentId → 平台报「上级枚举项ID 不能为null」。"""
    from components.udc.setting.enum_constraints import validate_enum_item_body
    body = _valid_item()
    del body["parentId"]
    errs = validate_enum_item_body(body)
    assert any("parentId" in e for e in errs), errs


def test_validate_enum_item_requires_enum_code():
    """所属枚举要同时给 enumId 与 enumCode。"""
    from components.udc.setting.enum_constraints import validate_enum_item_body
    body = _valid_item()
    del body["enumCode"]
    errs = validate_enum_item_body(body)
    assert any("enumCode" in e for e in errs), errs


def test_validate_enum_item_rejects_plain_text_name():
    """name 必须是 i18n JSON 字符串。"""
    from components.udc.setting.enum_constraints import validate_enum_item_body
    errs = validate_enum_item_body(_valid_item(name="启用"))
    assert any("name" in e for e in errs), errs


def test_validate_enum_item_passes_valid():
    from components.udc.setting.enum_constraints import validate_enum_item_body
    assert validate_enum_item_body(_valid_item()) == []
