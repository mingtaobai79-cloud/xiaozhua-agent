"""菜单域 —— FunctionNodeController + PageRouteController API 全集模型。

controller（udc-web-5.3.517 javap，STATIC_BYTECODE）：
- FunctionNodeController（udc/function，19）：菜单/功能节点 CRUD + 页面引用 + 默认页 + 排序 + 移动分组
- PageRouteController（udc/page-route，1）：页面路由详情

与 function_node_model（校验器视角 7 endpoint）互补：本模型给 controller 全量 20 方法级契约。
订单应用映射：菜单挂订单列表/详情页 = createFunction + create/function-refer + default_page。

证据边界：STATIC_BYTECODE。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.nav.menu-api.v1"

_API = (Path(__file__).resolve().parents[2] / "docs" / "audit" / "artifacts"
        / "udc-web-5.3.517-contracts" / "_api_full.json")

MENU_CONTROLLERS = ["FunctionNodeController", "PageRouteController"]

MENU_OPS: dict[str, tuple[str, str]] = {
    "菜单_创建功能": ("FunctionNodeController", "createFunction"),
    "菜单_修改功能": ("FunctionNodeController", "updateFunction"),
    "菜单_创建功能引用": ("FunctionNodeController", "createFunctionRefer"),
    "菜单_修改功能引用": ("FunctionNodeController", "updateFunctionRefer"),
    "菜单_修改引用名称": ("FunctionNodeController", "updateFunctionReferName"),
    "菜单_查询功能引用": ("FunctionNodeController", "selectFunction"),
    "菜单_删除功能": ("FunctionNodeController", "deleteFunction"),
    "菜单_批量删除": ("FunctionNodeController", "batchDeleteFunction"),
    "菜单_复制": ("FunctionNodeController", "copyFunction"),
    "菜单_设移动业务首页": ("FunctionNodeController", "setMobileBizHome"),
    "菜单_取消业务首页": ("FunctionNodeController", "cancelBizHome"),
    "菜单_设默认页": ("FunctionNodeController", "setFunctionDefaultPage"),
    "菜单_功能树": ("FunctionNodeController", "selectFunctionTree"),
    "菜单_删除引用页面": ("FunctionNodeController", "deleteFunctionReferPage"),
    "菜单_排序": ("FunctionNodeController", "functionSort"),
    "菜单_树和分组": ("FunctionNodeController", "findMenuTree"),
    "菜单_更新到用户中心": ("FunctionNodeController", "updateRootFunctionToUserCenter"),
    "菜单_处理菜单数据": ("FunctionNodeController", "handleFunction"),
    "菜单_页面入参": ("FunctionNodeController", "findPageInParams"),
    "路由_详情": ("PageRouteController", "selectById"),
}


def _load() -> dict[str, Any]:
    if not _API.exists():
        return {}
    return json.loads(_API.read_text(encoding="utf-8"))


def menu_api_map() -> dict[str, dict[str, Any]]:
    data = _load()
    out: dict[str, dict[str, Any]] = {}
    for op, (ctrl, name) in MENU_OPS.items():
        v = data.get(ctrl, {})
        m = next((x for x in v.get("methods", []) if x["method"] == name), None)
        out[op] = ({"controller": ctrl, "class_mapping": v.get("class_mapping"),
                    "http": m["http"], "full_path": m["full_path"],
                    "desc": m.get("desc", ""), "resolved": True}
                   if m else {"controller": ctrl, "method_name": name, "resolved": False})
    return out


def menu_summary() -> dict[str, Any]:
    data = _load()
    return {"schema": SCHEMA_ID,
            "controllers": {c: {"class_mapping": data.get(c, {}).get("class_mapping"),
                                "api_count": data.get(c, {}).get("api_count", 0)}
                            for c in MENU_CONTROLLERS},
            "op_count": len(MENU_OPS)}


__all__ = ["SCHEMA_ID", "MENU_CONTROLLERS", "MENU_OPS", "menu_api_map", "menu_summary"]
