"""设置域 —— 枚举（字典）管理 API 模型。

枚举是订单应用「枚举选项集」需求的后端契约来源。四 controller：
- UdcEnumController        枚举定义（创建/修改/删/查）
- UdcEnumItemController    枚举项（含 operate-batch 批量、import/export）
- UdcEnumCategoryController 枚举分类（按应用查询分类+枚举）
- UdcCtpEnumController     运行时按 code 查枚举项/级联树（Ctp=运行时组件）

数据源：udc-web-5.3.517 javap（_api_full.json，STATIC_BYTECODE）。
证据边界：STATIC_BYTECODE。写操作是否真生效需宿主执行回读。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.settings.enum.v1"

_API = (Path(__file__).resolve().parents[3] / "docs" / "audit" / "artifacts"
        / "udc-web-5.3.517-contracts" / "_api_full.json")

ENUM_CONTROLLERS = ["UdcEnumController", "UdcEnumItemController",
                    "UdcEnumCategoryController", "UdcCtpEnumController"]

# 枚举管理操作语义 → 完整路径
ENUM_OPS: dict[str, dict[str, str]] = {
    # 枚举定义
    "枚举_创建": {"ctrl": "UdcEnumController", "method": "create"},
    "枚举_修改": {"ctrl": "UdcEnumController", "method": "update"},
    "枚举_删除": {"ctrl": "UdcEnumController", "method": "deleteById"},
    "枚举_批量删除": {"ctrl": "UdcEnumController", "method": "deleteByIds"},
    "枚举_详情": {"ctrl": "UdcEnumController", "method": "selectById"},
    "枚举_分页": {"ctrl": "UdcEnumController", "method": "search"},
    "枚举_列表": {"ctrl": "UdcEnumController", "method": "selectListByConditions"},
    "枚举_模糊": {"ctrl": "UdcEnumController", "method": "selectListByTerm"},
    # 枚举项
    "项_创建": {"ctrl": "UdcEnumItemController", "method": "create"},
    "项_修改": {"ctrl": "UdcEnumItemController", "method": "update"},
    "项_批量操作": {"ctrl": "UdcEnumItemController", "method": "operateBatch"},   # 新增/修改/删除合一
    "项_删除": {"ctrl": "UdcEnumItemController", "method": "deleteById"},
    "项_批量删除": {"ctrl": "UdcEnumItemController", "method": "deleteByIds"},
    "项_详情": {"ctrl": "UdcEnumItemController", "method": "selectById"},
    "项_分页": {"ctrl": "UdcEnumItemController", "method": "selectPageByConditions"},
    "项_列表": {"ctrl": "UdcEnumItemController", "method": "selectListByConditions"},
    "项_按枚举层级": {"ctrl": "UdcEnumItemController", "method": "selectByEnumIdAndLevel"},
    "项_导出": {"ctrl": "UdcEnumItemController", "method": "exportExcel"},
    "项_导入": {"ctrl": "UdcEnumItemController", "method": "importExcel"},
    # 分类
    "分类_创建": {"ctrl": "UdcEnumCategoryController", "method": "create"},
    "分类_按应用查分类+枚举": {"ctrl": "UdcEnumCategoryController", "method": "selectCategoryAndEnum"},
    # 运行时（Ctp）
    "运行时_按code查项": {"ctrl": "UdcCtpEnumController", "method": "selectByEnumCode"},
    "运行时_按codes查项": {"ctrl": "UdcCtpEnumController", "method": "selectByEnumCodes"},
    "运行时_级联树": {"ctrl": "UdcCtpEnumController", "method": "selectCascadeTreeByEnumCode"},
}


def _load() -> dict[str, Any]:
    if not _API.exists():
        return {}
    return json.loads(_API.read_text(encoding="utf-8"))


def enum_api_map() -> dict[str, dict[str, Any]]:
    """枚举管理操作 → 真实 API（方法名/http/完整路径）。"""
    data = _load()
    out: dict[str, dict[str, Any]] = {}
    for op, spec in ENUM_OPS.items():
        ctrl = data.get(spec["ctrl"], {})
        match = next((m for m in ctrl.get("methods", []) if m["method"] == spec["method"]), None)
        if match:
            out[op] = {"controller": spec["ctrl"], "http": match["http"],
                       "full_path": match["full_path"], "desc": match.get("desc", ""),
                       "resolved": True}
        else:
            out[op] = {"controller": spec["ctrl"], "method_name": spec["method"],
                       "resolved": False}
    return out


def enum_controller_summary() -> dict[str, Any]:
    data = _load()
    return {"schema": SCHEMA_ID,
            "evidence": "udc-web-5.3.517 javap（STATIC_BYTECODE）",
            "controllers": {c: {"class_mapping": data.get(c, {}).get("class_mapping"),
                                "api_count": data.get(c, {}).get("api_count", 0)}
                            for c in ENUM_CONTROLLERS},
            "op_count": len(ENUM_OPS)}


__all__ = ["SCHEMA_ID", "ENUM_CONTROLLERS", "ENUM_OPS", "enum_api_map",
           "enum_controller_summary"]
