"""UDC 页面/布局/菜单域 约束模型（后端权威，反编译 udc-biz 5.3.517）。

证据：
- com.seeyon.udc.page.dto.PageDefinitionDto / PageLayoutDefinitionDto / PageInfoGroupDto / PageDesignerDto
- com.seeyon.udc.page.enums.PageTypeEnum / OpenTypeEnum / FunctionTypeEnum / PortletTypeEnum
- 约束来自 @NotNull / @NotBlank；字段说明来自 @DtoAttribute(value=...)
"""
from __future__ import annotations

# ---- 页面创建（PageDefinitionDto）----
#   value = (类型, 必填, 说明)
PAGE_DEFINITION_FIELDS: dict[str, tuple[str, bool, str]] = {
    "appId": ("Long", True, "应用ID"),
    "relationGroupId": ("Long", True, "关联分组"),
    "pageType": ("String", True, "页面类型（见 PAGE_TYPES）"),
    "groupId": ("Long", False, "分组ID"),
    "designState": ("DesignStateEnum", False, "设计态|运行态"),
    "sourceAppName": ("String", False, "源应用名称"),
    "masterEntityIds": ("String", False, "页面对应的主实体Id"),
    "relationAppName": ("String", False, "页面对应主实体的 appName"),
    "handWritten": ("Boolean", False, "手写页面（自定义页面）"),
    "defaultOpenType": ("String", False, "默认打开方式"),
    "sourceType": ("PageSourceTypeEnum", False, "页面来源类型"),
    "pageItems": ("List<PageItemDefinitionDto>", False, "页面信息"),
    "curTerminalType": ("TerminalTypeEnum", False, "当前端类型"),
    "category": ("PortletCategoryEnum", False, "栏目模板分类"),
    "isCustomCreate": ("Boolean", False, "是否来自于个性化创建"),
}
PAGE_DEFINITION_REQUIRED: tuple[str, ...] = tuple(k for k, v in PAGE_DEFINITION_FIELDS.items() if v[1])

# ---- 页面布局创建（PageLayoutDefinitionDto）----
PAGE_LAYOUT_FIELDS: dict[str, tuple[str, bool, str]] = {
    "appId": ("Long", True, "应用ID"),
    "relationGroupId": ("Long", False, "关联分组"),
    "designState": ("DesignStateEnum", False, "设计态|运行态"),
    "sourceAppName": ("String", False, "源应用名称"),
    "sourceType": ("PageSourceTypeEnum", False, "页面来源类型"),
    "pageLayoutItems": ("List<PageLayoutItemDefinitionDto>", False, "页面外框信息"),
    "curTerminalType": ("TerminalTypeEnum", False, "当前端类型"),
}
PAGE_LAYOUT_REQUIRED: tuple[str, ...] = tuple(k for k, v in PAGE_LAYOUT_FIELDS.items() if v[1])

# ---- pageItems[] 元素（PageItemDefinitionDto）----
#   ★urlType 有 @NotNull(groups=AppService.ValidationGroup.Create.class)
PAGE_ITEM_FIELDS: dict[str, tuple[str, bool, str]] = {
    "urlType": ("PageUrlTypeEnum", True, "url 应用类型（终端）——创建组必填"),
    "pageUrl": ("String", False, "页面 url（≤100）"),
    "sourceId": ("Long", False, "来源资源id（归属资源）"),
    "designState": ("DesignStateEnum", False, "设计态（默认 DESIGN）"),
    "layoutId": ("Long", False, "外框id（默认 NULL_ID）"),
    "menuId": ("Long", False, "菜单id"),
    "menuName": ("String", False, "菜单名（≤100）"),
    "inParams": ("String", False, "入参"),
    "outParameters": ("String", False, "出参"),
    "pageSchema": ("String", False, "页面 schema"),
    "schemaState": ("PageSchemaStateEnum", False, "页面 schema 状态"),
    "orderNo": ("Integer", False, "排序号"),
}
PAGE_ITEM_REQUIRED: tuple[str, ...] = tuple(k for k, v in PAGE_ITEM_FIELDS.items() if v[1])

# ---- 服务端（biz）强制但 DTO 未标注的项（LIVE 全部发现，PageInfoService.checkDefinitionPageDto）----
#   顺序：pageItems 非空 → checkPageUrl → validationPageUrl → validationPageType → validationOnCreate →
#         归属资源绑定 → validationGroup → validationSubpage4Layout
PAGE_CREATE_SERVICE_REQUIREMENTS: tuple[str, ...] = (
    "pageItems 非空（否则『页面终端信息为空，请选择』）",
    "pageUrl（BOOT_1001 pageUrl must not be null）",
    "pageItems[].urlType（@NotNull Create）",
    "pageItems[].menuName 或 menuId（否则『页面必需绑定归属资源』）★仅当 app.sourceType!=FORM 且 pageType 非 unRelationFunction",
    "curTerminalType（否则『curTerminalType 字段不能为空！』）★仅当 pageItems[].menuName 非空走 setFunctionRefer",
    "页面名称非空（『页面名称不能为空！』）",
)
# LIVE 验收：POST /service/udc/page-info/base-info/create
#   body={appId,relationGroupId,pageType,pageUrl,curTerminalType:"ALL",
#         pageItems:[{pageUrl,urlType:"PC",menuName}]} → 成功（返回 PageInfoGroupDto，含新 pageId + relationGroupId）

# ---- 页面类型（PageTypeEnum，15 值）----
PAGE_TYPES: dict[str, int] = {
    "PORTAL": 1, "WELCOME": 2, "REPORT_FORM": 3, "DETAIL": 4, "LIST": 5, "APPROVAL": 6,
    "PORTLET": 7, "SEARCH_LIST": 8, "EDIT_LIST": 9, "LIST_DETAIL": 10, "ASSIST_INFO": 11,
    "OTHER": 12, "LAYOUT": 14, "SUBPAGE": 15,
}
# ---- 打开方式（OpenTypeEnum）----
OPEN_TYPES: dict[str, int] = {"WORK_SPACE": 1, "DIALOG": 2}
# ---- 功能类型（FunctionTypeEnum）----
FUNCTION_TYPES: dict[str, int] = {"FRONTEND": 0, "BACKEND": 1}
# ---- 栏目类型（PortletTypeEnum）----
PORTLET_TYPES: dict[str, int] = {"GROUP": 0, "PORTLET": 1}


def validate_page_definition(body: dict) -> list[str]:
    """校验页面创建入参必填（空=通过）。"""
    return [f"PageDefinition 缺必填字段 {f}（{PAGE_DEFINITION_FIELDS[f][2]}）"
            for f in PAGE_DEFINITION_REQUIRED if not body.get(f)]


def validate_page_layout(body: dict) -> list[str]:
    """校验页面布局创建入参必填（空=通过）。"""
    return [f"PageLayout 缺必填字段 {f}（{PAGE_LAYOUT_FIELDS[f][2]}）"
            for f in PAGE_LAYOUT_REQUIRED if not body.get(f)]
