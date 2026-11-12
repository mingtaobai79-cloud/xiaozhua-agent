"""外框（PageLayout）与页面类型常量模型 —— 页面域最后一块硬边界。

证据基线（page-menu-source-audit.md §2.3/§7 + SETTINGS-TABS-CALLCHAIN.md §2/§3.11）：
- 外框 Controller 字面路径（§2.3）：POST /udc/page-layout/base-info/create、
  /base-info/update、/update、/update-draf；GET /{id}、/detail/{id}、
  /detail-app-id/{appId}、/params/{layoutId}。
- 外框创建校验（PageLayoutService.checkDefinitionPageDto，§7.3）：
  item 不能为空；终端类型集合；pageUrl 唯一性与合法性；appId 应用存在。
- createPages（§7.3）：外框组生成 relationGroupId；每终端 PageLayoutEntity + 独立 layout id；
  生成 PageSchemaEntity(layout_id=layoutId)；来源存在时复制自定义参照 + 过滤方案。
- 正式 update / updateDraft（§7.4）：分别写正式 schema+数据源+默认过滤+参照 /
  写 draftPageSchema+operationSteps+草稿数据源+过滤方案；草稿不升正式。
- 子页面硬约束（§7.1）：pageType=SUBPAGE 时 layoutId 不能是有效外框 id、
  layoutInfo 不能引用外部外框、outParameters 不能是非空 JSON 数组。
- 双层（SETTINGS §3.11 三层互证）：
  模板层 = PageTemplateController(pageType=LAYOUT) + PageTemplatePublishedController；
  实例层 = PageLayoutController + 表 udc_page_layout；
  **外框模板在 udc_page_template_published（LAYOUT 行），不在 udc_page_template**；
  udc_page_info 1494 行**无 LAYOUT**（page_type 分布 LIVE 实查）。
- 复制（§7.5）：PageCreation4MicroFlowContext 携带
  sourceAppName/newAppId/functionMiroFlowMapping/microFlowGroupMapping；
  先复制规则分组与微流程 → old→new id 映射 → SchemaParser.idReplace 替换 schema 引用。

页面类型常量（SETTINGS §2，page-type chunk 中文对照）：
  LAYOUT=外框；SUBPAGE=子页面；发布态 PUBLISHED/UNPUBLISH/ON_SHELF/RELEASE。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_ID = "udc.construction.page-layout.v1"

# pageType 受控值域（page-type chunk，SETTINGS-TABS-CALLCHAIN §2）
PAGE_TYPES: frozenset[str] = frozenset({
    "PORTAL", "WELCOME", "REPORT_FORM", "DETAIL", "LIST", "APPROVAL",
    "CHANGE_TERMINAL", "PORTLET", "SEARCH_LIST", "EDIT_LIST", "LIST_DETAIL",
    "ASSIST_INFO", "OTHER", "SUBPAGE", "LAYOUT", "NORMAL", "FORM", "MOBILE",
})
PUBLISH_STATES: frozenset[str] = frozenset({"PUBLISHED", "UNPUBLISH", "ON_SHELF", "RELEASE"})
TERMINAL_TYPES: frozenset[str] = frozenset({"PC", "MOBILE"})

# Controller 字面路径（不拼 Gateway 前缀，证据纪律）
LAYOUT_ENDPOINTS: dict[str, str] = {
    "create_base": "POST /udc/page-layout/base-info/create",
    "update_base": "POST /udc/page-layout/base-info/update",
    "update": "POST /udc/page-layout/update",
    "update_draft": "POST /udc/page-layout/update-draf",
    "get": "GET /udc/page-layout/{id}",
    "detail": "GET /udc/page-layout/detail/{id}",
    "detail_by_app": "GET /udc/page-layout/detail-app-id/{appId}",
    "params": "GET /udc/page-layout/params/{layoutId}",
}

# 双层归属（SETTINGS §3.11；写错表=查不到，本仓第一次就查错 udc_page_template 得 0 行）
LAYOUT_TEMPLATE_TABLE = "udc_page_template_published"   # LAYOUT 模板在这里
LAYOUT_INSTANCE_TABLE = "udc_page_layout"               # 外框实例（独立对象表）
PAGE_INFO_NO_LAYOUT = True                              # udc_page_info 的 page_type 无 LAYOUT（LIVE 分布）


@dataclass
class PageLayoutItem:
    terminal_type: str = "PC"
    page_url: str = ""
    layout_id: str = ""
    action_type: str = "NORMAL"     # {NORMAL, INSERT, UPDATE, DELETE}（§3.2 pageItems）
    source_id: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class PageLayout:
    """外框（实例层）。校验面=创建约束（§7.3）+ 草稿/正式边界（§7.4）。"""
    layout_id: str = ""
    app_id: str = ""
    caption: str = ""
    relation_group_id: str = ""
    items: list[PageLayoutItem] = field(default_factory=list)
    schema: str = ""
    draft_schema: str = ""
    is_draft: bool = False

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        if not self.items:
            errors.append("外框 item 为空（checkDefinitionPageDto 拒绝，§7.3）")
        urls: list[str] = []
        for it in self.items:
            if it.terminal_type not in TERMINAL_TYPES:
                errors.append(f"item terminalType={it.terminal_type!r} 不在终端集合")
            if not it.page_url:
                errors.append("item 缺 pageUrl（唯一性/合法性校验前提）")
            else:
                urls.append(it.page_url)
            if it.action_type not in ("NORMAL", "INSERT", "UPDATE", "DELETE"):
                errors.append(f"item actionType={it.action_type!r} 越界")
        if len(urls) != len(set(urls)):
            errors.append("外框 item pageUrl 重复（唯一性校验，§7.3）")
        if not self.app_id:
            errors.append("缺 appId（应用必须存在，§7.3）")
        if self.is_draft and self.draft_schema and not self.schema:
            warnings.append("草稿态：draft_page_schema 有而正式 schema 空 → updateDraft 不会升正式（§5.2/§7.4）")
        return {"schema": SCHEMA_ID, "kind": "page_layout",
                "status": "FAIL" if errors else ("UNVERIFIED" if warnings else "PASS"),
                "errors": errors, "warnings": warnings, "can_execute": False,
                "tables": {"template": LAYOUT_TEMPLATE_TABLE, "instance": LAYOUT_INSTANCE_TABLE}}


@dataclass
class SubPageConstraint:
    """子页面三硬约束（§7.1）；validate_subpage 是页面/外框全路径共用门。"""
    layout_id: str = "0"            # 有效外框 id 即违规（默认 NULL_ID=0）
    layout_info: str = ""           # 引用外部外框即违规
    out_parameters: str = ""        # 非空 JSON 数组即违规

    def violations(self, page_type: str) -> list[str]:
        if page_type != "SUBPAGE":
            return []
        out: list[str] = []
        if self.layout_id and self.layout_id != "0":
            out.append(f"SUBPAGE layoutId={self.layout_id} 绑定了外框（硬拒，§7.1）")
        if self.layout_info:
            out.append("SUBPAGE layoutInfo 引用外部外框（硬拒，§7.1）")
        if self.out_parameters and self.out_parameters.strip() not in ("[]", "{}", ""):
            out.append("SUBPAGE outParameters 非空（硬拒，§7.1）")
        return out


@dataclass
class PageCopyContext:
    """复制上下文（PageCreation4MicroFlowContext，§7.5）。

    复制页面/外框不能只复制 JSON：必须先复制规则分组与微流程、建 old→new id 映射，
    再 SchemaParser.idReplace 替换 schema 引用。
    """
    source_app_name: str = ""
    new_app_id: str = ""
    function_microflow_mapping: dict[str, str] = field(default_factory=dict)   # old mf id → new mf id
    microflow_group_mapping: dict[str, str] = field(default_factory=dict)
    copied_schema: str = ""

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        if not (self.source_app_name and self.new_app_id):
            errors.append("复制上下文缺 sourceAppName/newAppId")
        if not self.function_microflow_mapping and self.copied_schema:
            warnings.append("有 schema 无微流程 id 映射 → idReplace 未发生（复制的页面规则引用悬空，§7.5）")
        return {"schema": SCHEMA_ID, "kind": "page_copy_context",
                "status": "FAIL" if errors else ("UNVERIFIED" if warnings else "PASS"),
                "errors": errors, "warnings": warnings, "can_execute": False}


__all__ = [
    "SCHEMA_ID", "PAGE_TYPES", "PUBLISH_STATES", "TERMINAL_TYPES", "LAYOUT_ENDPOINTS",
    "LAYOUT_TEMPLATE_TABLE", "LAYOUT_INSTANCE_TABLE", "PAGE_INFO_NO_LAYOUT",
    "PageLayoutItem", "PageLayout", "SubPageConstraint", "PageCopyContext",
]
