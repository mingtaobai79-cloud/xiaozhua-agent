"""UDC 流水号机制（boot-starter-serialnumber 5.3.318）约束模型。

证据（CFR 反编译 boot-starter-serialnumber-5.3.318.jar）：
- controller/serial-scheme|serial-number|serial-range|serial-condition（4 Controller，44 端点）
- domain/entity/SerialScheme|SerialSection|SerialRange|SerialCondition|SerialCurrent|SerialHistory（6 表）
- enums: SerialTypeEnum / SerialRuleTypeEnum / SerialResetRuleEnum /
  SerialRangeTypeEnum / FillTypeEnum / CutTypeEnum

用途：订单类应用的流水号方案设计（scheme→section 多段拼接）与运行时取号。
"""
from __future__ import annotations

# ---- Controller 基址（4 个）----
SERIAL_CONTROLLERS: dict[str, str] = {
    "SerialSchemeController": "serial-scheme",
    "SerialNumberController": "serial-number",
    "SerialRangeController": "serial-range",
    "SerialConditionController": "serial-condition",
}

# ---- 端点目录：(controller, method, sub, 描述, readonly) ----
SERIAL_ENDPOINTS: tuple[tuple[str, str, str, str, bool], ...] = (
    # SerialScheme（流水号方案）
    ("SerialSchemeController", "POST", "create", "创建流水号方案", False),
    ("SerialSchemeController", "POST", "createEasyScheme", "创建简易方案", False),
    ("SerialSchemeController", "POST", "update", "更新方案", False),
    ("SerialSchemeController", "POST", "update-active", "启停方案", False),
    ("SerialSchemeController", "POST", "delete", "删除方案", False),
    ("SerialSchemeController", "POST", "runtime-delete", "运行态删除", False),
    ("SerialSchemeController", "POST", "batch-delete", "批量删除", False),
    ("SerialSchemeController", "GET", "{id}", "方案详情", True),
    ("SerialSchemeController", "GET", "ids", "按ids批量查", True),
    ("SerialSchemeController", "GET", "selectByCode/{code}", "按编码查方案", True),
    ("SerialSchemeController", "POST", "search-page", "分页查询", True),
    ("SerialSchemeController", "POST", "search-page-4-entity-fullname", "按实体分页查", True),
    ("SerialSchemeController", "POST", "search-no-page", "不分页查询", True),
    ("SerialSchemeController", "GET", "context-value/{contextKey}", "上下文值", True),
    ("SerialSchemeController", "GET", "context-value-list", "上下文值列表", True),
    ("SerialSchemeController", "GET", "context-key-list", "上下文键列表", True),
    ("SerialSchemeController", "GET", "max-sort-number/{appId}", "应用内最大排序号", True),
    # SerialNumber（取号——核心运行时）
    ("SerialNumberController", "POST", "get-serial-number", "取流水号", False),
    ("SerialNumberController", "POST", "batch-serial-number", "批量取号", False),
    ("SerialNumberController", "POST", "preview-serial-value", "预览流水号值", True),
    ("SerialNumberController", "POST", "search-page", "分页查询", True),
    ("SerialNumberController", "POST", "update-serial-number", "更新流水号", False),
    ("SerialNumberController", "POST", "reset-serial-number/{serialSchemeId}", "重置方案流水号", False),
    ("SerialNumberController", "POST", "reset-app-serial-number/{appId}", "重置应用流水号", False),
    ("SerialNumberController", "POST", "upgrade", "升级", False),
    ("SerialNumberController", "POST", "upgrade-v1", "升级V1", False),
    ("SerialNumberController", "POST", "upgrade-v2", "升级V2", False),
    ("SerialNumberController", "POST", "create-or-update-current", "新建/更新当前值", False),
    ("SerialNumberController", "POST", "recover-number", "恢复号码", False),
    # SerialRange（号段）
    ("SerialRangeController", "POST", "create", "创建号段", False),
    ("SerialRangeController", "POST", "createUnused", "创建空闲号段", False),
    ("SerialRangeController", "POST", "createUnusedBySerialNumber", "按流水号创建空闲号段", False),
    ("SerialRangeController", "POST", "createBatchUnused", "批量创建空闲号段", False),
    ("SerialRangeController", "POST", "update", "更新号段", False),
    ("SerialRangeController", "POST", "batch-updateForbiddenFlag", "批量更新禁用标记", False),
    ("SerialRangeController", "POST", "delete", "删除号段", False),
    ("SerialRangeController", "POST", "deleteById/{id}", "按id删除号段", False),
    ("SerialRangeController", "POST", "batch-delete", "批量删除号段", False),
    ("SerialRangeController", "GET", "{id}", "号段详情", True),
    ("SerialRangeController", "POST", "search-page", "分页查询号段", True),
    ("SerialRangeController", "POST", "search-no-page", "不分页查询号段", True),
    ("SerialRangeController", "POST", "recover-number", "号段回收号码", False),
    # SerialCondition（条件）
    ("SerialConditionController", "POST", "batch-create", "批量创建条件", False),
    ("SerialConditionController", "POST", "list", "条件列表", True),
    ("SerialConditionController", "POST", "eval", "条件求值", True),
)

# ---- 枚举值域（反编译权威）----
# 段类型：流水号由多段拼接，每段类型 ∈ 4 种
SERIAL_SECTION_TYPES: dict[str, int] = {
    "CONSTANT": 0, "CONTEXT": 1, "ENTITY": 2, "SERIAL": 3,
}
# 流水号方案类型（方案级）：应用内/大流水号/小流水号
SERIAL_RULE_TYPES: dict[str, int] = {"APP": 0, "BIG": 1, "SMALL": 2}
# 重置规则
SERIAL_RESET_RULES: dict[str, int] = {"NONE": 0, "YEAR": 1, "MONTH": 2, "DAY": 3}
# 号段类型
SERIAL_RANGE_TYPES: dict[str, int] = {"RESERVE": 0, "UNUSED": 1}
# 补位方式 / 截取方式
SERIAL_FILL_TYPES: dict[str, int] = {"LEFT": 0, "RIGHT": 1, "NONE": 2}
SERIAL_CUT_TYPES: dict[str, int] = {"LEFT": 0, "RIGHT": 1, "NONE": 2}

# ---- 表结构（@Table/@Column 权威，nullable + 默认值）----
SERIAL_DB_TABLES: dict[str, dict] = {
    "ctp_serial_scheme": {
        "comment": "流水号方案",
        "columns": {
            "code": ("VARCHAR(50)", False, None, "规则编码"),
            "name": ("VARCHAR(255)", False, None, "规则名称"),
            "serial_type": ("SMALLINT", False, "APP", "APP(应用内流水号)/BIG(大流水号)/SMALL(小流水号)"),
            "app_guid": ("VARCHAR(50)", False, "-1", "UDC应用GUID"),
            "app_id": ("VARCHAR(50)", False, "-1", "UDC应用ID"),
            "entity_full_name": ("VARCHAR(255)", False, "", "绑定实体全名"),
            "org_id": ("VARCHAR(255)", False, "", "组织ID"),
            "total_size": ("INT", False, 0, "编码长度"),
            "is_unused_priority": ("TINYINT", False, False, "空号优先标识"),
            "sort_num": ("INT", False, 1, "排序号"),
            "is_contain_flow": ("TINYINT", False, False, "是否有流水依据的标识"),
            "is_active": ("TINYINT", False, True, "启停用标识"),
            "serial_reset_rule": ("SMALLINT", False, "NONE", "NONE(不重置)/YEAR(跨年时)/MONTH(跨月时)/DAY(跨日时)"),
            "edit_entity": ("tinyint(4)", False, True, "是否可以编辑实体"),
            "is_delete": ("tinyint(4)", False, False, "是否删除"),
            "is_preset": ("TINYINT", False, False, "是否预制"),
            "source_app_name": ("VARCHAR(50)", False, None, "数据所属AppName"),
        },
    },
    "ctp_serial_section": {
        "comment": "流水号段（方案 → 多段拼接）",
        "columns": {
            "serial_scheme_id": ("BIGINT", False, None, "规则id"),
            "section_size": ("INT", False, 4, "编码长度"),
            "type": ("SMALLINT", False, "CONSTANT", "CONTEXT(上下文段)/CONSTANT(常量段)/SERIAL(流水号段)"),
            "value": ("VARCHAR(255)", False, "", "段值"),
            "caption": ("VARCHAR(255)", False, "", "显示名"),
            "fill_type": ("SMALLINT", False, "NONE", "LEFT(左补位)/RIGHT(右补位)/none(不补位)"),
            "cut_type": ("SMALLINT", False, "NONE", "LEFT(从左截取)/RIGHT(从右截取)/none(不截取)"),
            "fill_char": ("VARCHAR(20)", False, "0", "补位字符"),
            "is_date_type": ("TINYINT", False, False, "是否日期类型"),
            "date_pattern": ("VARCHAR(20)", False, "", "日期格式"),
            "is_show": ("TINYINT", False, True, "是否显示"),
            "is_flow": ("TINYINT", False, False, "是否流水依据"),
            "is_increase": ("TINYINT", False, True, "是否超出最大值递增"),
            "section_rank": ("INT", False, 1, "段序号"),
            "serial_current": ("BIGINT", False, 1, "当前流水号"),
            "is_delete": ("tinyint(4)", False, False, "是否删除"),
            "source_app_name": ("VARCHAR(50)", False, None, "数据所属AppName"),
            "start_value": ("BIGINT", False, 1, "起始值"),
            "end_value": ("BIGINT", False, -1, "结束值"),
        },
    },
    "ctp_serial_range": {"comment": "号段（预留/空闲）", "columns": {}},
    "ctp_serial_condition": {"comment": "流水号条件", "columns": {}},
    "ctp_serial_current": {"comment": "流水号当前值", "columns": {}},
    "ctp_serial_history": {"comment": "流水号历史", "columns": {}},
}

# DTO 必填（SerialSchemeController.create 的 DTO）
SERIAL_SCHEME_REQUIRED: tuple[str, ...] = ("code", "name", "serialType", "entityFullName")


def validate_serial_scheme(body: dict) -> list[str]:
    """校验流水号方案入参（空=通过）。"""
    errs: list[str] = []
    for f in SERIAL_SCHEME_REQUIRED:
        v = body.get(f)
        if v is None or v == "":
            errs.append(f"SerialScheme 缺必填字段 {f}")
    st = body.get("serialType")
    if st is not None and st not in SERIAL_RULE_TYPES:
        errs.append(f"SerialScheme.serialType '{st}' 不在值域 {list(SERIAL_RULE_TYPES)}")
    rr = body.get("serialResetRule")
    if rr is not None and rr not in SERIAL_RESET_RULES:
        errs.append(f"SerialScheme.serialResetRule '{rr}' 不在值域 {list(SERIAL_RESET_RULES)}")
    return errs


def validate_serial_section(body: dict) -> list[str]:
    """校验流水号段入参（空=通过）。"""
    errs: list[str] = []
    t = body.get("type")
    if t is not None and t not in SERIAL_SECTION_TYPES:
        errs.append(f"SerialSection.type '{t}' 不在值域 {list(SERIAL_SECTION_TYPES)}")
    ft = body.get("fillType")
    if ft is not None and ft not in SERIAL_FILL_TYPES:
        errs.append(f"SerialSection.fillType '{ft}' 不在值域 {list(SERIAL_FILL_TYPES)}")
    ct = body.get("cutType")
    if ct is not None and ct not in SERIAL_CUT_TYPES:
        errs.append(f"SerialSection.cutType '{ct}' 不在值域 {list(SERIAL_CUT_TYPES)}")
    # SERIAL 段必须有起止值语义
    if t == "SERIAL":
        sv, ev = body.get("startValue"), body.get("endValue")
        if sv is not None and ev is not None and ev != -1 and sv > ev:
            errs.append(f"SerialSection startValue {sv} > endValue {ev}")
    # 补位长度与段长一致语义
    sz = body.get("size")
    if isinstance(sz, int) and sz < 1:
        errs.append(f"SerialSection.size {sz} 须 ≥1")
    return errs
