"""栏目域 —— 页面（PageInfo）/外框（PageLayout）/栏目（Portlet）/模板（PageTemplate）API 模型。

controller（udc-web-5.3.517 javap，STATIC_BYTECODE）：
- PageInfoController（udc/page-info，25）：页面基础信息 CRUD + 批量 + 关联 + 入参 + PC筛选方案转移动
- PageLayoutController（udc/page-layout，18）：外框 CRUD + 可用列表 + 关联
- PortletController（udc/portlet，7）+ PortletGroupController（udc/portlet-group，4）：栏目及分组
- PageTemplateController（udc/page-template，13）+ ClassController（7）+ PublishedController（8）：模板 CRUD/分类/发布

订单应用映射：列表/详情排版=PageInfo、外框=PageLayout、栏目=Portlet、
工具栏/页面规则弹窗绑定在页面 schema（update/update-draf + batch-create）。

证据边界：STATIC_BYTECODE。页面 schema 内容不在本模型（在 construction 面）。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.nav.column-api.v1"

_API = (Path(__file__).resolve().parents[2] / "docs" / "audit" / "artifacts"
        / "udc-web-5.3.517-contracts" / "_api_full.json")

COLUMN_CONTROLLERS = [
    "PageInfoController", "PageLayoutController", "PortletController",
    "PortletGroupController", "PageTemplateController", "PageTemplateClassController",
    "PageTemplatePublishedController",
]

COLUMN_OPS: dict[str, tuple[str, str]] = {
    # 页面（PageInfo）—— 注意：/udc/page-info/base-info/* 与 /udc/page-info/{id} 等是页面类级；
    # 外框同构但类级为 /udc/page-layout/...（方法级 value 以 "/" 开头仍须拼接类级 mapping）
    "页面_按关联组id": ("PageInfoController", "findPageByRelationId"),
    "页面_创建基础信息": ("PageInfoController", "createBaseInfo"),
    "页面_批量创建基础信息": ("PageInfoController", "batchCreateBaseInfo"),
    "页面_更新基础信息": ("PageInfoController", "updateBaseInfo"),
    "页面_更新名称": ("PageInfoController", "updatePageName"),
    "页面_更新设计器版本": ("PageInfoController", "updateDesignerVersion"),
    "页面_批量创建含schema": ("PageInfoController", "batchCreate"),
    "页面_详情": ("PageInfoController", "selectDetailsById"),
    "页面_预置列表": ("PageInfoController", "selectAndCreatePresetListByAppId"),
    "页面_关联列表": ("PageInfoController", "selectMergeListByAppId"),
    "页面_按应用全部详情": ("PageInfoController", "selectDetailByAppId"),
    "页面_入参": ("PageInfoController", "selectPageInParams"),
    "页面_更新": ("PageInfoController", "update"),
    "页面_更新草稿": ("PageInfoController", "updateDraf"),
    "页面_列表按条件": ("PageInfoController", "selectListByConditions"),
    "页面_详情列表": ("PageInfoController", "selectDetailListByConditions"),
    "页面_详情列表含草稿": ("PageInfoController", "selectDetailListWithDraftSchemaByConditions"),
    "页面_设计器详情列表": ("PageInfoController", "selectDetailListByConditions4Page"),
    "页面_按条件删除": ("PageInfoController", "deleteByConditions"),
    "页面_按应用树": ("PageInfoController", "selectByAppIdV2"),
    "页面_复制PC筛选方案": ("PageInfoController", "copyPcFilterPlan2Mobile"),
    "页面_按条件复制PC筛选方案": ("PageInfoController", "copyPcFilterPlan2MobileByCondition"),
    # 外框（PageLayout）
    "外框_创建基础信息": ("PageLayoutController", "createBaseInfo"),
    "外框_更新基础信息": ("PageLayoutController", "updateBaseInfo"),
    "外框_按关联id": ("PageLayoutController", "findPageByRelationId"),
    "外框_详情": ("PageLayoutController", "selectDetailsById"),
    "外框_关联列表": ("PageLayoutController", "selectMergeListByAppId"),
    "外框_按应用全部详情": ("PageLayoutController", "selectDetailByAppId"),
    "外框_入参": ("PageLayoutController", "selectPageInParams"),
    "外框_更新标题": ("PageLayoutController", "updateCaption"),
    "外框_更新": ("PageLayoutController", "update"),
    "外框_更新草稿": ("PageLayoutController", "updateDraf"),
    "外框_可用列表": ("PageLayoutController", "selectAvailableListByConditions"),
    "外框_详情列表": ("PageLayoutController", "selectDetailListByConditions"),
    "外框_设计器详情列表": ("PageLayoutController", "selectDetailListByConditions4Page"),
    "外框_按条件删除": ("PageLayoutController", "deleteByConditions"),
    # 栏目（Portlet）
    "栏目_创建": ("PortletController", "createPortlet"),
    "栏目_修改": ("PortletController", "updatePortlet"),
    "栏目_按应用": ("PortletController", "selectAllByAppId"),
    "栏目_排序": ("PortletController", "portletSort"),
    "栏目分组_创建": ("PortletGroupController", "create"),
    "栏目分组_修改": ("PortletGroupController", "update"),
    "栏目分组_按应用": ("PortletGroupController", "selectAllByAppId"),
    # 模板（PageTemplate）
    "模板_批量创建": ("PageTemplateController", "batchCreate"),
    "模板_创建或更新": ("PageTemplateController", "createOrUpdate"),
    "模板_另存为": ("PageTemplateController", "saveAs"),
    "模板_详情": ("PageTemplateController", "selectDetailById"),
    "模板_列表": ("PageTemplateController", "selectListByConditions"),
    "模板_按权限列表": ("PageTemplateController", "selectListByConditionsWithRights"),
    "模板_可用列表": ("PageTemplateController", "selectAvailableListByConditions"),
    "模板_导出预置": ("PageTemplateController", "exportPreset"),
    "模板_发布": ("PageTemplateController", "publish"),
    "模板_查重": ("PageTemplateController", "checkName"),
    "模板分类_树": ("PageTemplateClassController", "selectClassTree"),
    "模板分类_按类别树": ("PageTemplateClassController", "selectClassTreeByCategory"),
    "模板发布_可用列表": ("PageTemplatePublishedController", "selectAvailableListByConditions"),
    "模板发布_转预置json": ("PageTemplatePublishedController", "selectPageTemplatePublishedToPresetJson"),
}


def _load() -> dict[str, Any]:
    if not _API.exists():
        return {}
    return json.loads(_API.read_text(encoding="utf-8"))


def column_api_map() -> dict[str, dict[str, Any]]:
    data = _load()
    out: dict[str, dict[str, Any]] = {}
    for op, (ctrl, name) in COLUMN_OPS.items():
        v = data.get(ctrl, {})
        m = next((x for x in v.get("methods", []) if x["method"] == name), None)
        out[op] = ({"controller": ctrl, "class_mapping": v.get("class_mapping"),
                    "http": m["http"], "full_path": m["full_path"],
                    "desc": m.get("desc", ""), "resolved": True}
                   if m else {"controller": ctrl, "method_name": name, "resolved": False})
    return out


def column_summary() -> dict[str, Any]:
    data = _load()
    return {"schema": SCHEMA_ID,
            "controllers": {c: {"class_mapping": data.get(c, {}).get("class_mapping"),
                                "api_count": data.get(c, {}).get("api_count", 0)}
                            for c in COLUMN_CONTROLLERS},
            "op_count": len(COLUMN_OPS)}


__all__ = ["SCHEMA_ID", "COLUMN_CONTROLLERS", "COLUMN_OPS", "column_api_map",
           "column_summary"]
