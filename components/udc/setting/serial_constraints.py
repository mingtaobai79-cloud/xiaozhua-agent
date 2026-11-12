"""设置域 · 流水号（Serial Scheme）实现与校验。

落库表：`ctp_serial_scheme` / `ctp_serial_section` / `ctp_serial_condition`
接口：`udcSerialSchemeCreatePost` / `udcSerialSchemeUpdatePost`

## 证据来源（重要）

字段名不是猜的，是**反编译 `boot-starter-serialnumber-5.3.318.jar`** 读出来的：

```
com/seeyon/boot/starter/serialnumber/domain/dto/SerialSchemeDto.java
com/seeyon/boot/starter/serialnumber/domain/dto/SerialSectionDto.java
枚举 SerialTypeEnum / FillTypeEnum / CutTypeEnum / SerialResetRuleEnum / SerialRuleTypeEnum
```

证伪过程（别再重复）：GraphQL 层**不校验未知字段**，传不存在的字段和传错字段名
返回完全一样的业务错 `BOOT_1001 流水号段 个数必须在1和12之间`，
所以"猜字段名"这条路无法收敛。必须读 DTO。

## 段列表的真实字段名

```
serialSectionDtoList     ← 不是 sections / serialSections / serialSectionDtos
serialConditionDtoList   ← 绑定实体条件
```

## 枚举是**字符串**，不是数字

```
SerialTypeEnum      CONSTANT(0) / CONTEXT(1) / ENTITY(2) / SERIAL(3)
FillTypeEnum        LEFT(0) / RIGHT(1) / NONE(2)
CutTypeEnum         LEFT(0) / RIGHT(1) / NONE(2)
SerialResetRuleEnum NONE(0) / YEAR(1) / MONTH(2) / DAY(3)
SerialRuleTypeEnum  APP(0) / BIG(1) / SMALL(2)
```

⚠ **平台会把枚举语义反转后落库**：传 `"NONE"` 落库成 `2`，而真实样本里固定值段是
`fill_type=0`（对应 `LEFT`）。写库值是枚举 ordinal，别拿 DB 数字反推语义。

证据：2026-10-21 **LIVE PASS**（BOOT_0000 + 主表 + 3 段全部落库 + 页面正确渲染
「规则组成: 常量:ZXJ 上下文字段:系统日期 流水号 / 效果预览: ZXJ202610211」）
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------- 枚举（照抄反编译）
SERIAL_TYPE = {"CONSTANT": 0, "CONTEXT": 1, "ENTITY": 2, "SERIAL": 3}
FILL_TYPE = {"LEFT": 0, "RIGHT": 1, "NONE": 2}
CUT_TYPE = {"LEFT": 0, "RIGHT": 1, "NONE": 2}
RESET_RULE = {"NONE": 0, "YEAR": 1, "MONTH": 2, "DAY": 3}
RULE_TYPE = {"APP": 0, "BIG": 1, "SMALL": 2}

MAX_SECTIONS = 12   # DTO @Size(min=1, max=12)


def build_serial_section(*, type_: str = "SERIAL", size: int = 4,
                         value: str = "", caption: str = "",
                         fill_type: str = "NONE", cut_type: str = "NONE",
                         fill_char: str = "0",
                         date_type: bool = False, date_pattern: str = "",
                         show: bool = True, flow: bool = False,
                         increase: bool = True, section_rank: int = 1,
                         serial_current: int = 1,
                         start_value: int = 1, end_value: int = -1,
                         source_app_name: str = "udc") -> dict[str, Any]:
    """构造一个流水号段 —— 字段名严格照 `SerialSectionDto`。

    注意 DTO 字段名与 DB 列名的差异：
      DTO `size`     ↔ DB `section_size`
      DTO `dateType` ↔ DB `is_date_type`
      DTO `show`     ↔ DB `is_show`
      DTO `flow`     ↔ DB `is_flow`
      DTO `increase` ↔ DB `is_increase`
    """
    return {
        "size": int(size),
        "type": type_,
        "value": value,
        "caption": caption,
        "fillType": fill_type,
        "cutType": cut_type,
        "fillChar": fill_char,
        "dateType": bool(date_type),
        "datePattern": date_pattern,
        "show": bool(show),
        "flow": bool(flow),
        "increase": bool(increase),
        "sectionRank": int(section_rank),
        "serialCurrent": int(serial_current),
        "startValue": int(start_value),
        "endValue": int(end_value),
        "sourceAppName": source_app_name,
    }


def build_serial_scheme_body(app_id: str | int, app_guid: str | int, *,
                             code: str, name: str,
                             sections: list[dict[str, Any]],
                             conditions: list[dict[str, Any]] | None = None,
                             serial_type: str = "APP",
                             serial_reset_rule: str = "NONE",
                             contain_flow: bool = False,
                             active: bool = True,
                             edit_entity: bool = True,
                             sort_num: int = 1,
                             org_id: str = "-1",
                             entity_full_name: str = "",
                             source_app_name: str = "udc") -> dict[str, Any]:
    """流水号方案 body —— 字段名严格照 `SerialSchemeDto`。

    totalSize 按各段 size 之和自动算（平台会校验一致性）。
    """
    total = sum(int(s.get("size") or 0) for s in sections)
    body = {
        "appId": str(app_id),
        "appGuid": str(app_guid),
        "code": code,
        "name": name,
        "totalSize": total,
        "containFlow": bool(contain_flow),
        "active": bool(active),
        "serialResetRule": serial_reset_rule,
        "editEntity": bool(edit_entity),
        "serialType": serial_type,
        "sortNum": int(sort_num),
        "orgId": org_id,
        "entityFullName": entity_full_name,
        "sourceAppName": source_app_name,
        "serialSectionDtoList": sections,
    }
    if conditions:
        body["serialConditionDtoList"] = conditions
    return body


def validate_serial_scheme_body(body: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["流水号 body 必须是对象"]

    for k in ("appId", "appGuid", "code", "name"):
        if not body.get(k):
            errs.append(f"流水号缺 {k}")

    code = str(body.get("code") or "")
    if code and any("\u4e00" <= ch <= "\u9fa5" for ch in code):
        errs.append("code 只支持字母数字，不支持中文（DTO @Pattern ^[^\\u4e00-\\u9fa5]*$）")

    st = body.get("serialType")
    if st not in RULE_TYPE:
        errs.append(f"serialType 必须是 {tuple(RULE_TYPE)} 之一，实际 {st!r}"
                    "（对应 SerialRuleTypeEnum，字符串枚举不是数字）")
    rr = body.get("serialResetRule")
    if rr not in RESET_RULE:
        errs.append(f"serialResetRule 必须是 {tuple(RESET_RULE)} 之一，实际 {rr!r}")

    secs = body.get("serialSectionDtoList")
    if not isinstance(secs, list) or not secs:
        errs.append("缺 serialSectionDtoList（不是 sections / serialSections / serialSectionDtos）"
                    "—— 缺它报 BOOT_1001「流水号段 个数必须在1和12之间」")
        return errs

    if not (1 <= len(secs) <= MAX_SECTIONS):
        errs.append(f"流水号段个数 {len(secs)} 超出 DTO @Size(1..{MAX_SECTIONS})")
        return errs

    calc = sum(int(s.get("size") or 0) for s in secs)
    if body.get("totalSize") is not None and int(body["totalSize"]) != calc:
        errs.append(f"totalSize={body['totalSize']} 与各段 size 之和 {calc} 不一致")

    for i, s in enumerate(secs, 1):
        if s.get("type") not in SERIAL_TYPE:
            errs.append(f"第 {i} 段 type={s.get('type')!r} 不在 {tuple(SERIAL_TYPE)} 内")
        if s.get("fillType") not in FILL_TYPE:
            errs.append(f"第 {i} 段 fillType={s.get('fillType')!r} 不在 {tuple(FILL_TYPE)} 内")
        if s.get("cutType") not in CUT_TYPE:
            errs.append(f"第 {i} 段 cutType={s.get('cutType')!r} 不在 {tuple(CUT_TYPE)} 内")
        if not s.get("size"):
            errs.append(f"第 {i} 段缺 size（DTO 字段名是 size，不是 sectionSize）")
        if "sectionSize" in s:
            errs.append(f"第 {i} 段用了 sectionSize —— DTO 字段名是 size")
    return errs


__all__ = [
    "SERIAL_TYPE", "FILL_TYPE", "CUT_TYPE", "RESET_RULE", "RULE_TYPE", "MAX_SECTIONS",
    "build_serial_section", "build_serial_scheme_body", "validate_serial_scheme_body",
]
