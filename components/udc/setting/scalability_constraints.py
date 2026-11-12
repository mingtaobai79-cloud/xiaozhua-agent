"""设置域 · 扩展实体（Scalability Option）实现与校验。

## 协议：混合 —— 方案 REST，预留组 GraphQL（★ 与字段集同一模式）

```
方案    REST     /service/udc/scalability-option              ← 连字符
预留组  GraphQL  udcScalabilityPost                           ← ★ 不是 REST
读方案  REST     GET /service/udc/scalability-option/...</appId>
```

**我最初以为预留组也走 REST update 带 `scalabilityDtoList`，2 种变体全部静默失败。**
真实入口是 GraphQL `udcScalabilityPost` —— 2026-10-21 从页面真实操作抓包确认。

## 完整可用链路（LIVE PASS）

```python
# 1) 建方案（REST）
POST /service/udc/scalability-option
{appId, name, caption}                            → data.content = 方案 id

# 2) 加预留组（GraphQL）
mutation udcScalabilityPost
body = build_scalability_group_body(option_id, app_id=..., prefix=..., caption=..., count=5)
→ BOOT_0000, data.content = 预留组 id

# 3) 读方案（REST）
GET /service/udc/scalability-option/select-by-appid/with-detail/{appId}
```

## 页面操作要点（UI 走通记录）

扩展实体界面是「左方案列表 + 右预留组表格 + 右常驻表单」：

1. 左列表点行内 `lined-edit` 选中方案
2. 右侧表单填「字段名称前缀」+「预留字段数量」
3. **预览区会实时显示**派生出的字段名（如 `probeExt01，probeExt02，…，probeExt05`）
4. 点「确定」（在 `.extension-form-footer`）→ 发 `udcScalabilityPost`
5. ⚠ 表格里点「新建」只是加内存行，**不会提交**；必须点表单底部的「确定」

⚠ `count` 页面限 20（DTO 上 `@Max(50)`），`prefix` ≤ 20 字。
"""
from __future__ import annotations

from typing import Any

PREFIX_MAX = 20
COUNT_MAX = 50        # DTO @Max(50)
COUNT_MAX_UI = 20     # 页面 UI 限制

GLOBAL_APP_ID = "-1"  # appId=-1 表示全局扩展

# 预留组的字段类型（基础类型；关联型/自定义型语义上不适用）
GROUP_DATA_TYPES = ("STRING", "MULTILINESTRING", "INTEGER", "BIGINTEGER",
                    "DECIMAL", "CURRENCY", "DATE", "TIME", "DATETIME", "BOOLEAN")


def build_scalability_option_body(app_id: str | int, *,
                                  name: str, caption: str,
                                  option_id: str | int | None = None) -> dict[str, Any]:
    """构造方案 body（ScalabilityOptionDto）—— REST create/update 用。

    ⚠ `scalabilityDtoList` 在这里**不生效**（父级不处理子集合）；
      加预留组用 `build_scalability_group_body` + GraphQL `udcScalabilityPost`。
    """
    body: dict[str, Any] = {
        "appId": str(app_id),
        "name": name,
        "caption": caption,
        "scalabilityDtoList": [],
        "attributeDtoList": [],
    }
    if option_id is not None:
        body["id"] = str(option_id)
    return body


def build_scalability_group_body(option_id: str | int, *,
                                 app_id: str | int,
                                 prefix: str, caption: str | None = None,
                                 count: int = 5,
                                 data_type: str = "STRING",
                                 data_type_properties: str | None = None,
                                 min_length: int = 0,
                                 max_length: int = 50) -> dict[str, Any]:
    """构造预留组 body —— 用于 **GraphQL `udcScalabilityPost`**。

    字段名与页面实际发出的 body 逐字对齐：
    `dataTypeProperties` 是**字符串化的 JSON**（页面发的是
    `"{\\"minLength\\":\\"0\\",\\"maxLength\\":50}"`，注意 minLength 是字符串）。
    """
    if data_type_properties is None:
        data_type_properties = ('{"minLength":"%d","maxLength":%d}'
                                % (int(min_length), int(max_length)))
    return {
        "dataType": data_type,
        "prefix": prefix,
        "count": int(count),
        "dataTypeProperties": data_type_properties,
        "optionId": str(option_id),
        "caption": caption if caption is not None else prefix,
    }


def validate_scalability_option_body(body: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["扩展实体方案 body 必须是对象"]

    if not body.get("appId"):
        errs.append("缺 appId（DTO @NotNull；-1 表示全局扩展）")
    if not body.get("name"):
        errs.append("缺 name（DTO @NotBlank 方案编码）")
    if not body.get("caption"):
        errs.append("缺 caption（DTO @NotBlank 方案名称）")

    if body.get("scalabilityDtoList"):
        errs.append("⚠ scalabilityDtoList 在本接口不生效 —— 加预留组请用 "
                    "build_scalability_group_body + GraphQL udcScalabilityPost")
    return errs


def validate_scalability_group_body(body: dict[str, Any],
                                    option_id: str | int | None = None) -> list[str]:
    errs: list[str] = []
    if not isinstance(body, dict):
        return ["预留组 body 必须是对象"]

    if not body.get("optionId"):
        errs.append("预留组缺 optionId（DTO @NotNull；实测「方案id 不能为null」）")
    elif option_id is not None and str(body["optionId"]) != str(option_id):
        errs.append(f"预留组 optionId={body['optionId']!r} 必须等于方案 id {option_id!r}")

    prefix = str(body.get("prefix") or "")
    if not prefix:
        errs.append("预留组缺 prefix（DTO @NotBlank）")
    elif len(prefix) > PREFIX_MAX:
        errs.append(f"prefix 超长 {len(prefix)} > {PREFIX_MAX}（DTO @Size(max=20)）")

    if not body.get("caption"):
        errs.append("预留组缺 caption（DTO @NotBlank）")

    cnt = body.get("count")
    if cnt is None:
        errs.append("预留组缺 count（DTO @NotNull）")
    elif not isinstance(cnt, int):
        errs.append("count 必须是整数")
    elif cnt > COUNT_MAX:
        errs.append(f"count={cnt} 超出 DTO @Max({COUNT_MAX})")
    elif cnt > COUNT_MAX_UI:
        errs.append(f"count={cnt} 超出页面 UI 上限 {COUNT_MAX_UI}（能提交但页面显示不了）")

    dt = body.get("dataType")
    if not dt:
        errs.append("预留组缺 dataType（DTO @NotBlank，如 STRING）")
    elif dt not in GROUP_DATA_TYPES:
        errs.append(f"dataType 应为 {GROUP_DATA_TYPES} 之一，实际 {dt!r}")

    dp = body.get("dataTypeProperties")
    if dp is not None and not isinstance(dp, str):
        errs.append("dataTypeProperties 必须是 JSON **字符串**（页面发的就是这个形态）")
    return errs


__all__ = [
    "PREFIX_MAX", "COUNT_MAX", "COUNT_MAX_UI", "GLOBAL_APP_ID", "GROUP_DATA_TYPES",
    "build_scalability_option_body", "build_scalability_group_body",
    "validate_scalability_option_body", "validate_scalability_group_body",
]
