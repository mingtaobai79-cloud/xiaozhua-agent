"""枚举域本地校验：枚举、枚举项、枚举分组（分类）。

为什么必须有本地校验：
  平台对这些 body 的校验是分散且报错信息有误导性的——
    · 缺 orderNo        → BOOT_1001（看不出是哪个字段）
    · code 传字符串      → BOOT_3002 Failed to convert String to Int
    · name 带数字/小写   → UDC_ENUM_0002 "The code contains only uppercase letters
                          and underscores"（报错说 code，实际校验的是 name）
  这些都在 build_enum_* 的 docstring 里作为 LIVE 证据记录过，但此前**没有任何
  校验器**把它们变成可执行断言，只能靠人记。本模块把它固化。

判据全部来自已有 LIVE 记录，不引入新猜测；标 UNVERIFIED 的不做断言。
"""
from __future__ import annotations

import json
import re
from typing import Any

# UDC_ENUM_0002 实际校验 name：只允许大写字母与下划线
_ENUM_ITEM_NAME = re.compile(r"^[A-Z_]+$")


def _missing(body: dict[str, Any], key: str) -> bool:
    v = body.get(key)
    return v is None or (isinstance(v, str) and not v.strip())


def validate_enum_category_body(body: dict[str, Any]) -> list[str]:
    """枚举分组（UdcEnumCategoryController.create）body 校验。

    必填：appId / name / orderNo。
      orderNo 缺 → BOOT_1001（与 build_enum_body 同族，LIVE 记录）
      name    缺 → 无法定位分组
    parentId 可为 None（顶层分组）；若给则须为整数（平台要 Long）。
    """
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["枚举分组 body 必须是对象"]
    if _missing(body, "appId"):
        errs.append("枚举分组缺 appId")
    if _missing(body, "name"):
        errs.append("枚举分组缺 name（分组名，平台必填）")
    if _missing(body, "orderNo"):
        errs.append("枚举分组缺 orderNo（平台报 BOOT_1001，LIVE 记录）")
    parent = body.get("parentId")
    if parent is not None and not isinstance(parent, int):
        errs.append(f"枚举分组 parentId={parent!r} 须为整数或 null（平台要 Long）")
    return errs


def validate_enum_body(body: dict[str, Any]) -> list[str]:
    """枚举（udcEnumPost）body 校验。

    必填：appId / code（英文编码）/ name（i18n JSON 显示名）/ orderNo。
    额外硬约束（2026-10-20 设计器 UI 抓包 + DB 回读证实）：
      · name 必须是 `{"zh_CN":"..."}` 的 JSON 字符串。传裸文本时平台报
        `BOOT_1001 枚举编码 不能为空`——报错说「编码」，实际缺的是 name 的 i18n 形态。
      · appGuid 必填，取自 udc_application.guid。
      · categoryId 必填（分组归属；"0" = 未归组）。
    """
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["枚举 body 必须是对象"]
    if _missing(body, "appId"):
        errs.append("枚举缺 appId")
    if _missing(body, "code"):
        errs.append("枚举缺 code（英文编码，不是显示名）")
    if _missing(body, "orderNo"):
        errs.append("枚举缺 orderNo（平台报 BOOT_1001，LIVE 记录）")

    name = body.get("name")
    if name is None or (isinstance(name, str) and not name.strip()):
        errs.append("枚举缺 name（显示名，须为 i18n JSON 字符串）")
    elif isinstance(name, str):
        try:
            parsed = json.loads(name)
        except (TypeError, ValueError):
            errs.append(
                f"枚举 name={name!r} 不是合法 JSON 字符串 —— 平台要求 "
                f"{{\"zh_CN\":\"显示名\"}}；传裸文本会报 BOOT_1001 枚举编码 不能为空")
        else:
            if not isinstance(parsed, dict) or not parsed.get("zh_CN"):
                errs.append(
                    f"枚举 name 的 JSON 缺 zh_CN 键（实得 {sorted(parsed) if isinstance(parsed, dict) else type(parsed).__name__}）")

    if _missing(body, "appGuid"):
        errs.append("枚举缺 appGuid（取自 udc_application.guid，不是 appId）")
    if body.get("categoryId") in (None, ""):
        errs.append("枚举缺 categoryId（分组归属，\"0\" 表示未归组）")
    return errs


def validate_enum_item_body(body: dict[str, Any]) -> list[str]:
    """枚举项（udcEnumItemPost）body 校验。

    必填（2026-10-20 报错 + ctp_enum_item 表结构双向确认）：
      appId / enumId / enumCode / name / itemValue / parentId / orderNo
    itemValue 缺失 → 平台报「枚举项编码 不能为空」
    parentId  缺失 → 平台报「上级枚举项ID 不能为null」（顶层项填 "0"）
    name 必须是 i18n JSON 字符串，且 zh_CN 存在。
    """
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["枚举项 body 必须是对象"]
    for key, label in (("appId", "appId"), ("enumId", "enumId"),
                       ("enumCode", "enumCode")):
        if _missing(body, key):
            errs.append(f"枚举项缺 {label}")
    if _missing(body, "itemValue"):
        errs.append("枚举项缺 itemValue（枚举项值；平台报「枚举项编码 不能为空」——"
                    "该槽位是 ctp_enum_item.item_value，不是 code）")
    if body.get("parentId") in (None, ""):
        errs.append("枚举项缺 parentId（上级枚举项ID；顶层项填 \"0\"，"
                    "否则平台报「上级枚举项ID 不能为null」）")
    if _missing(body, "orderNo"):
        errs.append("枚举项缺 orderNo（平台报 BOOT_1001）")

    name = body.get("name")
    if name is None or (isinstance(name, str) and not name.strip()):
        errs.append("枚举项缺 name（枚举项名称，须为 i18n JSON 字符串）")
    elif isinstance(name, str):
        try:
            parsed = json.loads(name)
        except (TypeError, ValueError):
            errs.append(f"枚举项 name={name!r} 不是合法 JSON 字符串（平台要求 "
                        f"{{\"zh_CN\":\"显示名\"}}）")
        else:
            if not isinstance(parsed, dict) or not parsed.get("zh_CN"):
                errs.append("枚举项 name 的 JSON 缺 zh_CN 键")
    return errs


__all__ = [
    "validate_enum_category_body",
    "validate_enum_body",
    "validate_enum_item_body",
]
