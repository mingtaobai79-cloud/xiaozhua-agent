"""设置域 · 选项集（Option Set）实现与校验。

选项集 ≠ 枚举 —— 两套完全独立的表和接口：

  枚举    ctp_enum / ctp_enum_category / ctp_enum_item
          operation: udcEnumCategoryPost / udcEnumPost / udcEnumItemPost
  选项集  udc_enum / udc_enum_category / udc_enum_item
          operation: udcUdcEnumCategoryPost / udcUdcEnumPost / udcUdcEnumItemPost
                      udcUdcEnumBatchDeletePost / udcUdcEnumCategorySelectCategoryAndEnumPost

证据：2026-10-21 LIVE PASS（BOOT_0000 + DB 回读），见
`core/facts/udc/setting/option-set/create.md`。

字段级关键差异（踩过才知道）：
  - 选项集编码必须**首字母大写**（UDC_ENUM_0001「编码只能由首字母大写的数字和字母的组合」）
  - 选项项有 name（编码，如 ONE）+ caption（显示名，如 选项甲）**两个都要**
  - 选项项 code 是整数（不是字符串）
  - 字段组装时 dataTypeCategory = "ENUM"（第三个枚举值，不是 PRIMITIVE）
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------- 枚举值域
# dataTypeCategory 真实值域（第三个值 ENUM 只有选项集用）
CATEGORY_PRIMITIVE = "PRIMITIVE"
CATEGORY_COMPOSITE = "COMPOSITE"
CATEGORY_ENUM = "ENUM"
VALID_CATEGORIES = (CATEGORY_PRIMITIVE, CATEGORY_COMPOSITE, CATEGORY_ENUM)

# type 真实值域
TYPE_OBJECT = "OBJECT"
TYPE_LIST = "LIST"
VALID_TYPES = (TYPE_OBJECT, TYPE_LIST)

# section type（流水号段用，此处仅登记以免混淆）
SECTION_FIXED = 0
SECTION_DATE = 1
SECTION_INCREASE = 3


# ---------------------------------------------------------------- 构造器
def build_option_set_category_body(app_id: str | int, app_guid: str | int, *,
                                   name: str, caption: str,
                                   order_no: int = 1,
                                   parent_id: str | int = "0",
                                   description: str = "") -> dict[str, Any]:
    """选项集分组（udcUdcEnumCategoryPost）。

    实测必填：appId / appGuid / name / caption / orderNo
    报错：BOOT_1001「应用ID 不能为null;  分类名称 不能为空」
    """
    return {
        "appId": str(app_id),
        "appGuid": str(app_guid),
        "name": name,
        "caption": caption,
        "orderNo": int(order_no),
        "parentId": str(parent_id),
        "description": description,
    }


def build_option_set_body(app_id: str | int, app_guid: str | int, *,
                          name: str, caption: str,
                          category_id: str | int,
                          order_no: int = 1,
                          description: str = "") -> dict[str, Any]:
    """选项集本体（udcUdcEnumPost）。

    ⚠ name 必须**首字母大写**，否则 UDC_ENUM_0001
      「编码只能由首字母大写的数字和字母的组合」
    """
    return {
        "appId": str(app_id),
        "appGuid": str(app_guid),
        "name": name,
        "caption": caption,
        "categoryId": str(category_id),
        "orderNo": int(order_no),
        "description": description,
    }


def build_option_set_item_body(app_id: str | int, app_guid: str | int, *,
                               enum_id: str | int,
                               name: str, caption: str, code: int,
                               order_no: int | None = None,
                               enable: bool = True,
                               description: str = "") -> dict[str, Any]:
    """选项项（udcUdcEnumItemPost）。

    ⚠ 三个槽位都不能少：
      name    = 编码（英文，如 ONE）
      caption = 显示名（如 选项甲）
      code    = 整数
    缺 caption 报 BOOT_1001「选项名称 不能为空」（报错说"名称"，实际是 caption）
    """
    return {
        "appId": str(app_id),
        "appGuid": str(app_guid),
        "enumId": str(enum_id),
        "name": name,
        "caption": caption,
        "code": int(code),
        "orderNo": int(order_no if order_no is not None else code),
        "enable": bool(enable),
        "description": description,
    }


# ---------------------------------------------------------------- 校验器
def validate_option_set_category_body(body: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["选项集分组 body 必须是对象"]
    for k in ("appId", "appGuid", "name", "caption"):
        if not body.get(k):
            errs.append(f"选项集分组缺 {k}")
    if body.get("orderNo") is None:
        errs.append("选项集分组缺 orderNo（实测 BOOT_1001「排序号 不能为null」）")
    return errs


def validate_option_set_body(body: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["选项集 body 必须是对象"]
    for k in ("appId", "appGuid", "name", "caption", "categoryId"):
        if not body.get(k):
            errs.append(f"选项集缺 {k}")
    name = str(body.get("name") or "")
    if name and not name[0].isupper():
        errs.append("选项集编码首字母必须大写（实测 UDC_ENUM_0001"
                    "「编码只能由首字母大写的数字和字母的组合」）")
    return errs


def validate_option_set_item_body(body: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["选项项 body 必须是对象"]
    for k in ("appId", "enumId", "name", "caption"):
        if not body.get(k):
            errs.append(f"选项项缺 {k}")
    code = body.get("code")
    if code is None:
        errs.append("选项项缺 code（整数）")
    elif not isinstance(code, int):
        errs.append("选项项 code 必须是整数，不能是字符串")
    return errs


def validate_custom_object_enum_field(data_type: str, data_type_category: str,
                                      type_: str, relation_app: str,
                                      relation_entity: str) -> list[str]:
    """自定义对象里「选项集」字段的形态校验。

    两条分支（实证）：
      本应用  dataType = "<选项集 id>"         relationApp = "<appId>"   cat = ENUM
      BPM引擎 dataType = "<Java 全类名>"        relationApp = "bpm"       cat = ENUM
    共同点：dataTypeCategory 必须是 ENUM（不是 PRIMITIVE）
    """
    errs: list[str] = []
    if data_type_category != CATEGORY_ENUM:
        errs.append(f"选项集字段 dataTypeCategory 必须是 {CATEGORY_ENUM}，"
                    f"实际 {data_type_category!r}（写成 PRIMITIVE 页面会显示异常串）")
    if type_ not in VALID_TYPES:
        errs.append(f"type 必须是 {VALID_TYPES} 之一，实际 {type_!r}")
    if not data_type:
        errs.append("选项集字段缺 dataType")
    if not relation_app:
        errs.append("选项集字段缺 relationApp（本应用填 appId，BPM 分支填 'bpm'）")
    if not relation_entity:
        errs.append("选项集字段缺 relationEntity（选项集 id）")
    return errs


__all__ = [
    "CATEGORY_PRIMITIVE", "CATEGORY_COMPOSITE", "CATEGORY_ENUM", "VALID_CATEGORIES",
    "TYPE_OBJECT", "TYPE_LIST", "VALID_TYPES",
    "build_option_set_category_body", "build_option_set_body", "build_option_set_item_body",
    "validate_option_set_category_body", "validate_option_set_body",
    "validate_option_set_item_body", "validate_custom_object_enum_field",
]
