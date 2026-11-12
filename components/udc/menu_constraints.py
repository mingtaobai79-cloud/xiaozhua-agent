"""UDC 菜单/导航（功能节点）域 约束模型（后端权威，反编译 5.3.517）。

证据：
- com.seeyon.udc.page.dto.FunctionNodeDto（udc-plugin-api）@NotEmpty/@NotNull/@Size
- com.seeyon.udc.page.domain.entity.FunctionNodeEntity（交互表 @Table udc_function_node）
- com.seeyon.udc.common.enums.UdcNodeTypeEnum / OpenStateEnum / PageSchemaStateEnum / TerminalTypeEnum
- com.seeyon.udc.page.enums.FunctionTagEnum
"""
from __future__ import annotations

# ---- 功能节点创建/更新（FunctionNodeDto）----
#   value = (类型, 必填, 说明, 最大长度)
FUNCTION_NODE_FIELDS: dict[str, tuple[str, bool, str, int | None]] = {
    "appId": ("Long", True, "appId"),
    "terminalType": ("TerminalTypeEnum", True, "端类型 PC/MOBILE"),
    "type": ("UdcNodeTypeEnum", True, "节点类型 MENU/PAGE/REPORT/EXT_LINK/PORTAL_SPACE"),
    "name": ("String", True, "功能显示名称（1..64）", 64),
    "icon": ("String", False, "功能图标", 100),
    "permission": ("Boolean", False, "权限配置（默认 true）"),
    "appBizHome": ("Boolean", False, "应用业务首页（默认 false）"),
    "parentId": ("Long", False, "父功能id"),
    "defaultPage": ("Long", False, "默认页面"),
    "url": ("String", False, "url", 500),
    "relationId": ("Long", False, "关联id"),
    "tag": ("FunctionTagEnum", False, "功能标记（默认 NORMAL）"),
    "resourceId": ("String", False, "引用资源的id 或 fullName", 255),
    "relationApp": ("String", False, "关联应用", 100),
    "openState": ("OpenStateEnum", False, "页面打开状态 EDIT/VIEW/INPUT"),
    "pageParam": ("String", False, "页面入参"),
    "pageType": ("String", False, "页面类型", 50),
    "orderNo": ("Integer", False, "排序号（默认 0）"),
    "childNodes": ("List<FunctionNodeDto>", False, "子节点"),
}
FUNCTION_NODE_REQUIRED: tuple[str, ...] = tuple(k for k, v in FUNCTION_NODE_FIELDS.items() if v[1])

# ---- 节点类型（UdcNodeTypeEnum）----
NODE_TYPES: dict[str, int] = {"MENU": 0, "PAGE": 1, "REPORT": 2, "EXT_LINK": 3, "PORTAL_SPACE": 4}
# ---- 打开状态（OpenStateEnum）----
OPEN_STATES: dict[str, int] = {"EDIT": 0, "VIEW": 1, "INPUT": 2}
# ---- 页面 schema 状态（PageSchemaStateEnum）----
PAGE_SCHEMA_STATES: dict[str, int] = {"NONE": -1, "EMPTY": 0, "DRAFT": 1, "FORMAL": 2,
                                      "CUSTOMIZE": 3, "REFERENCE": 4}
# ---- 功能标记（FunctionTagEnum）----
FUNCTION_TAGS: dict[str, int] = {
    "NORMAL": 0, "ROOT": 1, "BIZ_HOME": 2, "ENUM_MANAGE": 3, "PARAM_MANAGE": 4, "DEDUCT": 5,
    "EXTENSION_PLAN": 6, "SERIAL_NUMBER": 7, "BILL_CATEGORY": 8, "ARCHIVE_CATEGORY": 9,
    "DATA_FLOW": 10, "BIZ_RULE": 11, "BASE_SET": 12, "SPACE_MENU": 13, "DEFAULT_GROUP": 14,
    "EXTENSION_REFER_CONTROL": 15, "EXCEL_SETTING": 16, "CUSTOM_PAGE": 17,
}
# ---- 端类型（TerminalTypeEnum，udc-common）----
TERMINAL_TYPES: tuple[str, ...] = ("PC", "MOBILE", "ALL")

# 交互表（FunctionNodeEntity @Table）
FUNCTION_NODE_TABLE: str = "udc_function_node"


def validate_function_node(body: dict) -> list[str]:
    """校验功能节点创建/更新入参必填与长度（空=通过）。"""
    errs = []
    for f in FUNCTION_NODE_REQUIRED:
        v = body.get(f)
        if v is None or v == "":
            errs.append(f"FunctionNode 缺必填字段 {f}（{FUNCTION_NODE_FIELDS[f][2]}）")
    for f, meta in FUNCTION_NODE_FIELDS.items():
        maxlen = meta[3] if len(meta) > 3 else None
        if maxlen and isinstance(body.get(f), str) and len(body[f]) > maxlen:
            errs.append(f"FunctionNode.{f} 长度 {len(body[f])} 超限 {maxlen}")
    return errs

# FunctionDto（FunctionNodeController.createFunction 入参）必填与 FunctionNodeDto 一致：
#   @NotNull appId / @NotNull terminalType / @NotNull type / @NotEmpty @Size(max=64) name
# LIVE 验收：POST /service/udc/function → 返回 data.content=<新功能id>（appId/terminalType/type/name 必填）

# ============================================================================
# 菜单写链（PAGE 子节点 / default_page / 树回读）—— 第二十六轮 LIVE + CFR 双层证据
# ============================================================================
# 证据分层（禁止跨层互套）：
#   LIVE（test2, app=8704025620829192834, 菜单 -1628253460115858501）：
#     POST /udc/function/create/function-refer -> BOOT_0000, content=<新PAGE节点id>
#     POST /udc/function/default_page {functionId,sourceId} -> BOOT_0000, content=1
#     POST /udc/function/update/name/function-refer {appId,relationId,name}
#     POST /udc/function/delete {id}
#     GET  /udc/function/{id} / POST /udc/function/find/tree-and-group {appId}
#     POST /udc/function/select/function-tree {params:{appId,terminalType}, sort:{...}}
#   CFR（udc-web-5.3.517 / udc-biz-5.3.517 / udc-plugin-api-5.3.517）：
#     controller/FunctionNodeController（类级 mapping `udc/function`，全 17 REST 入参形状）
#     page/dto/{FunctionDto,FunctionReferDto,FunctionNodeDto}
#     page/domain/service/FunctionNodeService：
#       :189 createFunctionNode -> setSchemaState -> selectOnePageByPageId(dto.getResourceId())
#       :510 setFunctionDefaultPage（三前提 + 三写入）
#       :543 excludeSubPage（resourceId 必须数字且非 NULL_ID，且非 SUBPAGE）
#       :1181 handleFunctionDefaultPage（子节点为空 -> default_page=0 且清空 url）
#       :1662 findMenuTree（ONLY_MENU=true -> 只回 MENU，子 PAGE 全被过滤）
#       :1427 selectFunctionTree（param 里 null/空白值被剔除；缺 terminalType/appId -> UDC_APP_0026）
#     detection/task/util/FunctionNodeDetectionUtils#doDetection + ConsistenceDetectionCodeEnum
#       UDC_CE_FUNCTION_NODE_MIS_DEFAULT_PAGE(500, "UDC_CE_FUNCTION_NODE_08100")

# ---- 不变量 1：PAGE 子节点必须走 create/function-refer，不能走 POST /function ----
# FunctionDto（POST /udc/function 的入参）没有 resourceId 字段（CFR 逐字段确认）。
# createFunctionNode 在 type 未命中 type2SchemaState(MENU/PORTAL_SPACE/EXT_LINK/REPORT) 时
# 走 selectOnePageByPageId(appId, dto.getResourceId())，而 FunctionDto 无该字段 -> null；
# SearchFilter 对 [resourceId] 的空条件直接拒绝（[resourceId]字段的条件数据不能为null）
# -> MyBatisSystemException -> BOOT_4000 DB Error（LIVE 实测 3/3 复现，且零落库）。
# => 建 PAGE 节点用 create/function-refer（FunctionReferDto 带 resourceId 且 @NotBlank）。
MENU_CREATE_ENDPOINT_BY_TYPE: dict[str, str] = {
    "MENU": "POST /udc/function",
    "PAGE": "POST /udc/function/create/function-refer",
    "REPORT": "POST /udc/function/create/function-refer",
    "EXT_LINK": "POST /udc/function/create/function-refer",
    "PORTAL_SPACE": "POST /udc/function",
}
# FunctionDto 全字段（CFR udc-plugin-api 5.3.517 com.seeyon.udc.page.dto.FunctionDto）
FUNCTION_DTO_FIELDS: tuple[str, ...] = (
    "name", "icon", "permission", "parentId", "appId", "terminalType",
    "defaultPage", "url", "relationId", "tag", "type", "orderNo",
)
# FunctionReferDto 全字段（CFR 同包）
FUNCTION_REFER_DTO_FIELDS: tuple[str, ...] = (
    "name", "parentId", "appId", "terminalType", "url", "relationId",
    "resourceId", "relationApp", "openState", "pageParam", "type", "pageType",
)
FUNCTION_REFER_DTO_REQUIRED: tuple[str, ...] = ("name", "parentId", "appId", "terminalType",
                                                "url", "resourceId", "type")

# ---- 不变量 2：空目录 WARN 08100 的真实语义与真实触发条件 ----
# FunctionNodeDetectionUtils#doDetection 的叶子菜单筛选（CFR 逐条）：
#   1) terminalType == PC
#   2) type == MENU
#   3) tag 不属于 {ROOT, SPACE_MENU, BIZ_HOME}
#   4) childNodes 为空 或 无任何 type==MENU 的子节点
#   5) 命中后，defaultPage == null 或 == NULL_ID(0) 才报 08100
# => WARN 文案是「未设默认页」，但真实充分条件是「无子页面可指向」：
#   即使子节点全为 PAGE（type=1，第 4 条仍判空），只要 default_page 已指向其中之一即不报。
# LIVE 实测：建 PAGE 子节点后父菜单 default_page 由 0 自动落为子节点 id，WARN 9 -> 8，
#   08100 条目消失（04003x7 + 04009x1 仍在）。
UDC_CE_FUNCTION_NODE_08100 = "UDC_CE_FUNCTION_NODE_08100"
FUNCTION_NODE_08100_WARN = "WARN"
FUNCTION_NODE_08100_MESSAGE = "菜单未设置默认页面（真实充分条件 = 该 PC 叶菜单无子页面可指向）"
FUNCTION_NODE_08100_TAG_EXEMPT: tuple[str, ...] = ("ROOT", "SPACE_MENU", "BIZ_HOME")
DEFAULT_PAGE_UNSET: int = 0

# ---- 不变量 3：setFunctionDefaultPage 的三前提 / 三写入 ----
# CFR FunctionNodeService#setFunctionDefaultPage(:510)：
#   前提 A：refer.getParentId() == function.getId()，否则 BOOT_1000「菜单绑定的默认页面信息异常」
#   前提 B：excludeSubPage(refer) —— 若 refer.type==PAGE：
#             resourceId 非空 且（有 relationApp 直接放行 或 resourceId 是数字且 != NULL_ID），
#             且该页面 pageType != SUBPAGE（SUBPAGE 报「菜单只能绑定主页面」）
#   写入：function.url = refer.url; function.defaultPage = refer.id; function.relationApp = refer.relationApp
# LIVE 实测：切到 C2 -> defaultPage/url 同步变；切回 C1 -> 同步回；负控（非直接子节点）-> BOOT_1000。
SET_DEFAULT_PAGE_ERRORS: dict[str, str] = {
    "BOOT_1000": "菜单绑定的默认页面信息异常（sourceId 不是 functionId 的直接子节点）",
    "UDC_PAGE_0004": "页面不存在（excludeSubPage 的 pageInfoService.selectById 返回空）",
}
SET_DEFAULT_PAGE_WRITES: tuple[str, ...] = ("url", "defaultPage", "relationApp")

# ---- 不变量 4：建 PAGE 子节点后父菜单自动落 default_page ----
# createFunctionNode(:252) 对 type != MENU 的节点调用 handleFunctionDefaultPage(parentId)；
# handleFunctionDefaultPage(:1181) 仅处理 terminalType==PC 的父节点：
#   子节点（type!=MENU 且 pageType 不是 SUBPAGE，按 create_time 升序）非空、且现有
#   defaultPage 不在子节点集合内时，取最早创建的一个写入 defaultPage/url/relationApp。
# LIVE 实测：新建 C2 后 defaultPage 仍指向先建的 C1（map.containsKey 判据正确）；
#          显式切到 C2 生效；删除 C2 后父节点保留 C1。
AUTO_DEFAULT_PAGE_ON_CHILD_CREATE: bool = True
AUTO_DEFAULT_PAGE_PICK = "最早创建的（create_time 升序）非 MENU 子节点"
# 子节点全空时 handleFunctionDefaultPage 写回 default_page=0 并清空 url / relation_app

# ---- 不变量 5：树回读双端点差异（判「读面 0 子节点」前必须先确认口径）----
# findMenuTree(ONLY_MENU=true) -> selectFunctionTree 先按 type==MENU 过滤，子 PAGE 全被丢掉，
#   故 find/tree-and-group 的 pcTree 里菜单 childNodes 恒为空，这不是「没建成」。
# 要连子 PAGE 一起读：POST /udc/function/select/function-tree
#   body = {params:{appId,terminalType}, sort:{...}}（两层包装；裸 {appId,terminalType} 报 BOOT_3000）
#   注意 selectFunctionTree 会剔除 null/空白值：terminalType=null 即被丢 -> UDC_APP_0026。
FUNCTION_TREE_READ_ENDPOINTS: dict[str, str] = {
    "menu_only": "POST /udc/function/find/tree-and-group {appId} -> pcTree/mobileTree，仅 MENU",
    "with_children": "POST /udc/function/select/function-tree {params:{appId,terminalType}, sort:{...}} -> 含 PAGE",
}
FUNCTION_TREE_REQUIRED_KEYS: tuple[str, ...] = ("appId", "terminalType")
FUNCTION_TREE_MISSING_KEY_ERROR = "UDC_APP_0026"

# ---- LIVE 锚点（供护栏钉桩，防证据漂移）----


def validate_function_refer(body: dict) -> list[str]:
    """校验 PAGE 子节点创建入参（FunctionReferDto 口径；空=通过）。"""
    errs = []
    for f in FUNCTION_REFER_DTO_REQUIRED:
        v = body.get(f)
        if v is None or v == "":
            errs.append("FunctionReferDto 缺必填字段 " + f)
    if body.get("type") == "PAGE" and not str(body.get("resourceId") or "").strip():
        errs.append("FunctionReferDto.resourceId 在 type=PAGE 时不可空"
                    "（excludeSubPage 会报 UDC_PAGE_0004/页面信息异常）")
    return errs


def validate_default_page_call(function_id, source_id, parent_of_source=None) -> list[str]:
    """校验 setFunctionDefaultPage 调用（前提 A 可在本地先判）。"""
    errs = []
    if function_id is None:
        errs.append("default_page 缺 functionId")
    if source_id is None:
        errs.append("default_page 缺 sourceId")
    if parent_of_source is not None and function_id is not None:
        if str(parent_of_source) != str(function_id):
            errs.append("sourceId 不是 functionId 的直接子节点（服务端将返 BOOT_1000）")
    return errs
