"""依赖设置（应用依赖 / 组件依赖）本地校验。

只固化**实测坐实**的规则，不臆造平台报错文案。每条规则都标注证据来源。

证据：
  core/facts/udc/application/evidence/app-inner-build-2026-10-22/
      cmp-dep-create-full.json      添加依赖的真实请求体
      cmp-dep-page-hook.json        批量删除的真实请求体
  docs/operation-contracts/udc/application/app-inner-contracts.md §6
"""

from __future__ import annotations

from typing import Any, Dict, List

SCHEMA_ID = "udc.application.dependency.v1"

DEPENDENT_TYPES = ("SERVICE", "FRONTEND")

# 应用依赖（SERVICE）六字段，实测抓包就是这个顺序与集合
SERVICE_FIELDS = (
    "appId",
    "depAppName",
    "depAppCaption",
    "depAppVersion",
    "depAppBasePackage",
    "dependentAppType",
)

# 组件依赖（FRONTEND）在六字段之外额外携带的十个字段
FRONTEND_EXTRA_FIELDS = (
    "description",
    "dynamicModuleGroup",
    "dynamicService",
    "enableDelete",
    "needGenerate",
    "sort",
    "supportUpgrade",
    "terminalType",
    "sourceType",
    "packageType",
)

# 实测一条组件依赖的取值形态（不写具体组件名，避免客户资产入库）
FRONTEND_SAMPLE_SHAPE = {
    "packageType": "CONTROL",
    "sourceType": "CUSTOMIZE",
    "terminalType": "PC",
    "dynamicService": True,
}


def validate_create_row(row: Dict[str, Any]) -> List[str]:
    """校验一条「添加依赖」写行；返回错误列表，空表示通过。"""
    errs: List[str] = []
    missing = [k for k in SERVICE_FIELDS if not row.get(k)]
    if missing:
        errs.append("缺必填字段: " + ", ".join(missing))
    dtype = row.get("dependentAppType")
    if dtype not in DEPENDENT_TYPES:
        errs.append(f"dependentAppType={dtype!r} 非法，只能是 SERVICE / FRONTEND")
    if dtype == "FRONTEND":
        missing_extra = [k for k in FRONTEND_EXTRA_FIELDS if k not in row]
        if missing_extra:
            errs.append("组件依赖缺字段: " + ", ".join(missing_extra))
    if "packageType" in row and dtype != "FRONTEND":
        errs.append("packageType 只出现在组件依赖行，SERVICE 行不应携带")
    return errs


def validate_delete_arg(row_id: Any) -> List[str]:
    """移除应用依赖只吃依赖行 id。

    实测：传 appId / depAppName 不报错但删不掉（依赖行 id 与 appId 不同源）。
    """
    errs: List[str] = []
    if row_id is None or str(row_id) == "":
        errs.append("id 不能为空")
        return errs
    s = str(row_id)
    if not s.lstrip("-").isdigit():
        errs.append("id 必须是依赖行 id（纯数字），不是 appId / depAppName")
    return errs


def validate_component_delete(ids: Any) -> List[str]:
    """组件依赖批量删除：REST ``{"ids": [...]}``，非空数组。"""
    errs: List[str] = []
    if not isinstance(ids, (list, tuple)) or not list(ids):
        errs.append("ids 必须是非空数组")
        return errs
    for i in list(ids):
        if not str(i).lstrip("-").isdigit():
            errs.append(f"非法依赖行 id: {i!r}")
    return errs


def is_deletable(row: Dict[str, Any]) -> bool:
    """行内是否可移除。

    平台/集成平台这类内置依赖 ``enableDelete=false`` —— 页面上「移除」是禁用态；
    应用能否被加进来则看 ``enableDependent``（候选列表里的许可位）。
    """
    return bool(row.get("enableDelete", False))


def partition_rows(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """把依赖列表按类型拆开（同一个列表口返回两类）。"""
    out: Dict[str, List[Dict[str, Any]]] = {"SERVICE": [], "FRONTEND": [], "other": []}
    for r in rows:
        key = r.get("dependentAppType")
        out[key if key in DEPENDENT_TYPES else "other"].append(r)
    return out
