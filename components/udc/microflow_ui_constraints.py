"""微流程节点 UI 交互层约束（2026-10-28 实测，22 类节点）。

与 `microflow_constraints.py` 的分工：
- `microflow_constraints.py`：**后端权威**结构层必填/值域（反编译 udc-biz 5.3.517 + 全库真实节点统计）
- 本文件：**前端交互层**事实 —— 字段联动、DOM 结构、值域枚举、提交路径坑

证据等级：LIVE。每类节点均在 test2 真实画布「添加 → 配置 → 确定 → 保存并提交 →
后端 dataSchema 回读」完整走通（PUBLISH_BUSINESS_EVENT 除外，标 UNVERIFIED）。

逐节点完整契约：`docs/audit/udc-semantics/MICROFLOW-<ACTION>-CONTRACT.md`
汇总事实：`core/facts/udc/microflow/node-ui-contracts-22.md`
原始证据：`scratch/<node>-evidence/`
"""
from __future__ import annotations

# ============================================================================
# 一、值域枚举（前端 UI 实测，权威）
# ============================================================================

# ---- FOR 执行条件 ----
FOR_OPERATORS: tuple[str, ...] = ("<=", "<", ">=", ">")
FOR_OPERATOR_LABELS: dict[str, str] = {
    "<=": "小于等于", "<": "小于", ">=": "大于等于", ">": "大于",
}
FOR_DEFAULT_OPERATOR = "<="
FOR_VALUE_MAX = 99999999          # forStart / forEnd 共同上限
FOR_VALUE_TYPES = ("CONSTANT", "EXPRESSION", "CONTEXT_VARIABLE")

# ---- MAP_OPERATION 操作类型 ----
MAP_OPERATION_TYPES: tuple[str, ...] = ("GET", "PUT", "REMOVE", "KEY_SET")
MAP_OPERATION_TYPE_LABELS: dict[str, str] = {
    "GET": "获取", "PUT": "赋值", "REMOVE": "删除", "KEY_SET": "获取键列表",
}
# 各操作类型触发的字段（除 selectMap / operationType 恒显示）
MAP_OPERATION_FIELDS_BY_TYPE: dict[str, tuple[str, ...]] = {
    "GET": ("theKey", "paramType", "basic", "arrayOrObject", "title",
            "nullHandling", "nullPromptMessage"),
    "PUT": ("entries",),
    "REMOVE": ("removeKeys",),
    "KEY_SET": ("title",),
}
# 映射值类型（paramType）
# ★ 权威来源：后端 ParamTypeEnum（CFR 反编译 cfr-r31b，8 种，带 code）
#   DEFAULT_OBJECT(0) / BASIC(1) / ENTITY_OBJECT(2) / ENUM(3)
#   MAP(4) / METADATA(5) / MESSAGE(6) / OTHER(7)
# 前端「选择数据」只给 7 类 radio（不含 MAP —— MAP 仅出现在映射值/映射组场景）。
# 历史值域只记了 5 种，漏 METADATA / MESSAGE / OTHER，导致这三类生成必失败。
MAP_PARAM_TYPES: tuple[str, ...] = (
    "BASIC", "ENTITY_OBJECT", "DEFAULT_OBJECT", "ENUM", "MAP",
    "METADATA", "MESSAGE", "OTHER",
)

# 后端 ParamTypeEnum 完整定义（含 code 与是否需要 fullName）
PARAM_TYPE_ENUM: dict[str, dict] = {
    "DEFAULT_OBJECT": {"code": 0, "need_full_name": True,  "label": "自定义对象"},
    "BASIC":          {"code": 1, "need_full_name": False, "label": "基本类型"},
    "ENTITY_OBJECT":  {"code": 2, "need_full_name": True,  "label": "实体对象"},
    "ENUM":           {"code": 3, "need_full_name": True,  "label": "选项集"},
    "MAP":            {"code": 4, "need_full_name": False, "label": "映射"},
    "METADATA":       {"code": 5, "need_full_name": False, "label": "元数据"},
    "MESSAGE":        {"code": 6, "need_full_name": False, "label": "事件对象"},
    "OTHER":          {"code": 7, "need_full_name": False, "label": "其他"},
}

# 前端「选择数据」radio 提供的 7 类（不含 MAP）
UI_PARAM_TYPES: tuple[str, ...] = (
    "BASIC", "ENTITY_OBJECT", "DEFAULT_OBJECT", "ENUM",
    "METADATA", "MESSAGE", "OTHER",
)

# 每种 paramType 后端实际读取的字段（决定「填的值能否被解析」）
# 来源：CreateVariableActivity.buildActivityByDataType / buildOtherTypeVariable
PARAM_TYPE_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "OTHER": ("otherType",),
    "DEFAULT_OBJECT": ("app", "structure", "mappingType"),
    "ENTITY_OBJECT": ("app", "structure"),
    "ENUM": ("app", "structure", "value"),
    "METADATA": ("app", "metaDataType"),
    "BASIC": ("dataType",),
    "MAP": ("dataType",),
    "MESSAGE": ("dataType",),
}

MAP_PARAM_TYPE_LABELS: dict[str, str] = {
    "BASIC": "基本类型", "ENTITY_OBJECT": "实体对象",
    "DEFAULT_OBJECT": "自定义对象", "ENUM": "选项集", "MAP": "映射",
    "METADATA": "元数据", "MESSAGE": "事件对象", "OTHER": "其他",
}
MAP_NULL_HANDLING_DEFAULT = "TERMINATION"

# ---- CUSTOM_ERROR 错误提示方式 ----
CUSTOM_ERROR_TYPES: tuple[str, ...] = ("GLOBAL", "POSITION")
CUSTOM_ERROR_TYPE_LABELS: dict[str, str] = {
    "GLOBAL": "全局提示", "POSITION": "定位到页面元素",
}
# 各模式下的必填字段（★ error 与 attrError 标签都叫「填写错误」，key 不同）
CUSTOM_ERROR_FIELDS_BY_TYPE: dict[str, tuple[str, ...]] = {
    "GLOBAL": ("error",),
    "POSITION": ("sourceData", "selectParam", "attrType", "attrError"),
}
# 切 errorType 时前端清空的字段（setEmptyBeforeChanged）
CUSTOM_ERROR_CLEARED_ON_SWITCH: tuple[str, ...] = (
    "sourceData", "selectParam", "attrType", "error", "attrError",
)

# ---- CONVERT_DATA 类型转换 ----
CONVERT_TYPES: tuple[str, ...] = (
    "multiAssociation2List", "List2multiAssociation",
    "String2Long", "String2Integer", "String2Decimal",
    "BasicData2String", "GetEnumCode", "GetEnumName", "Split",
)
CONVERT_TYPE_LABELS: dict[str, str] = {
    "multiAssociation2List": "多选数据拆分为长整数列表",
    "List2multiAssociation": "长整数列表拼接为多选数据",
    "String2Long": "文本转长整数【ID】",
    "String2Integer": "文本转整数",
    "String2Decimal": "文本转小数",
    "BasicData2String": "基础类型转文本",
    "GetEnumCode": "获取选项值编码",
    "GetEnumName": "获取选项值",
    "Split": "指定符号拆分文本",
}
# ★ 只有 Split 显示「指定拆分符号」（ishidden: convertType.value !== "Split"）
CONVERT_TYPES_WITH_REGEX: tuple[str, ...] = ("Split",)
SPLIT_SYMBOLS: tuple[str, ...] = (
    "COMMA", "PERIOD", "UNDERSCORE", "MIDLINE", "DIVLINE",
    "QUSMARK", "AND", "START", "SLASH", "BACKSLASH",
)
SPLIT_SYMBOL_LABELS: dict[str, str] = {
    "COMMA": "英文逗号(,)", "PERIOD": "英文句号(.)", "UNDERSCORE": "下划线(_)",
    "MIDLINE": "中脊线(-)", "DIVLINE": "分割线(|)", "QUSMARK": "问号(?)",
    "AND": "与(&)", "START": "星号(*)", "SLASH": "正斜杠(/)", "BACKSLASH": "反斜杠(\\)",
}
# ★ convertType 落库必须是 {value:...} 结构，UI 选中只存 {key,...}（无 value）→ filter 失效
CONVERT_TYPE_REQUIRES_VALUE_KEY = True
# ★ 出参 dataType 随子模式变（语料 214 条裁决 2026-10-31，旧「恒 String」是早期单样本误归纳）
CONVERT_OUTPUT_DATATYPE = {
    "Split": "STRING", "multiAssociation2List": "BIGINTEGER",
    "List2multiAssociation": "STRING", "String2Long": "BIGINTEGER",
    "BasicData2String": "STRING",
}
CONVERT_OUTPUT_JAVATYPE_EMPTY = True

# ---- DATA_MAPPING 数据转换 ----
DATA_MAPPING_TARGET_TYPES: tuple[str, ...] = ("ENTITY", "DTO")
DATA_MAPPING_TARGET_TYPE_LABELS: dict[str, str] = {
    "ENTITY": "实体对象", "DTO": "自定义对象",
}
DATA_MAPPING_MODES: tuple[str, ...] = ("值拷贝", "常量")
DATA_MAPPING_MODE_TO_BACKEND: dict[str, str] = {
    "值拷贝": "REFERENCE", "常量": "CONSTANT",
}
DATA_MAPPING_REQUIRED: tuple[str, ...] = (
    "selectParam", "targetType", "app", "structure", "mappingRule", "title",
)

# ---- PUBLISH_BUSINESS_EVENT 事件投递 ----
EVENT_TYPES: tuple[str, ...] = ("AMONG_APP", "IN_APP")
EVENT_TYPE_LABELS: dict[str, str] = {
    "AMONG_APP": "应用间(异步)", "IN_APP": "应用内(同步)",
}
MESSAGE_TYPES: tuple[str, ...] = ("DEFAULT", "DELAY")
MESSAGE_TYPE_LABELS: dict[str, str] = {"DEFAULT": "普通事件", "DELAY": "延迟事件"}
# ★ 两种「可投递的事件」字段名不同
EVENT_SELECT_FIELD: dict[str, str] = {"AMONG_APP": "selectMq", "IN_APP": "selectEvent"}
# ★ 双「事件类型」标签陷阱：靠 DOM id 区分
EVENT_TYPE_DOM_IDS: dict[str, str] = {"eventType": "#eventType", "messageType": "#messageType"}

# ---- CALL_APP_SERVICE 入参形态 ----
CALL_SERVICE_PARAM_SHAPES: tuple[str, ...] = ("NONE", "SCALAR", "DTO", "LIST")
CALL_SERVICE_ASSIGN_MODES: tuple[str, ...] = ("attrs", "value", "mapping")
CALL_SERVICE_ASSIGN_LABELS: dict[str, str] = {
    "attrs": "字段映射", "value": "对象引用", "mapping": "自动映射",
}

# ============================================================================
# 二、跨节点通用交互约束（22 类全部踩过）
# ============================================================================

# 提交失败后抽屉会卸载，必须重载页面重做
DRAWER_UNMOUNTS_AFTER_FAILED_SUBMIT = True
# 查看模式弹窗可叠多层（readonly:false 但 .ant-modal-wrap 有 N 层），需循环点「进行编辑」
VIEW_MODE_MODAL_STACKS = True
# 全流程保存被别的节点阻塞时，报错只在 console.log + message.error，不发请求
SAVE_BLOCKED_ERRORS_ONLY_IN_CONSOLE = True
# 活动节点 type 恒为 ACTIVITY，回读必须用 actionType
ACTIVITY_NODES_HAVE_TYPE_ACTIVITY = True
# 画布横向滚动，卡片右边缘超过 1699 点击无效，必须先滚到中心
CANVAS_HORIZONTAL_SCROLL_CLICK_MARGIN = 1699
# 自定义 select 不接受 JS 派发的 click，必须真实鼠标 + 键盘
CUSTOM_SELECT_NEEDS_REAL_MOUSE = True
# tree 型下拉（实体/事件）DOM 是 .ant-select-tree-treenode
TREE_SELECT_DOM_SELECTOR = ".ant-select-tree-treenode"
# valueComponent 必须 focus + Input.insertText，原生 setter 无效
VALUE_COMPONENT_NEEDS_INSERT_TEXT = True
# 带 filter/asyncFilter 的下拉，setFieldsValue 不刷新候选（渲染期闭包）
FILTERED_SELECT_CANDIDATES_ARE_RENDER_CLOSURE = True

# 无表单节点（BREAK）不能用 submit()，直接点「确定」
NO_FORM_NODES: tuple[str, ...] = ("BREAK", "CLOSE_PAGE", "CONFIRM_CLOSE_PAGE", "RELOAD_PAGE")

# 只能在循环体内添加的节点
LOOP_BODY_ONLY_NODES: tuple[str, ...] = ("BREAK",)

# 前端 noCompleted 节点：创建时直接 isCompleted=true
NO_COMPLETED_NODES: tuple[str, ...] = (
    "BREAK", "CLOSE_PAGE", "CONFIRM_CLOSE_PAGE", "RELOAD_PAGE",
)

# ============================================================================
# 三、节点面板可选清单（根级 24 项实测）
# ============================================================================

ROOT_LEVEL_NODE_PANEL: tuple[str, ...] = (
    "分支", "列表循环", "计数循环", "自定义错误",
    "创建变量", "修改变量", "创建映射组", "映射操作",
    "创建列表", "修改列表", "列表操作",
    "查询单条数据", "查询多条数据",
    "插入数据", "批量插入数据", "更新数据", "批量更新数据", "删除数据",
    "自定义服务", "事件投递", "子微流程", "执行生单规则",
    "类型转换", "数据转换",
)
# ★ 根级面板不含「跳出循环」——它只在循环体容器内出现
LOOP_BODY_EXTRA_NODES: tuple[str, ...] = ("跳出循环",)


# ============================================================================
# 四、校验函数
# ============================================================================

def validate_convert_data(node: dict) -> list[str]:
    """CONVERT_DATA 值域与结构校验（UI 实测）。

    ★ 核心坑：convertType 落库必须是 {value:...}，
    只有 {key,...}（UI 选中形态）会让 selectParam 的 filter 失效。
    """
    problems: list[str] = []
    ct = node.get("convertType")
    if not isinstance(ct, dict):
        problems.append("convertType 必须是对象，实际 %r" % type(ct).__name__)
        return problems
    val = ct.get("value")
    if not val:
        problems.append(
            "convertType 缺 value 字段（只有 key 会让 selectParam filter 失效）；"
            "实际 keys=%s" % sorted(ct.keys()))
    elif val not in CONVERT_TYPES:
        problems.append("convertType.value=%r 不在值域 %s" % (val, CONVERT_TYPES))

    if val in CONVERT_TYPES_WITH_REGEX:
        if not node.get("regex"):
            problems.append("convertType=%s 时 regex（指定拆分符号）必填" % val)
        elif node["regex"] not in SPLIT_SYMBOLS:
            problems.append("regex=%r 不在值域 %s" % (node["regex"], SPLIT_SYMBOLS))
    else:
        if node.get("regex"):
            problems.append(
                "convertType=%s 不该有 regex（只有 Split 显示该字段）" % val)

    out = node.get("output") or {}
    # ★ casing 差异：保存态恒大写（643 条发布语料 STRING/BIGINTEGER），
    #   后端回读态首字母大写（convert_data-evidence/04-backend.json 'String'）。
    #   平台自身转换，校验按 .upper() 归一。
    _exp = CONVERT_OUTPUT_DATATYPE.get(val)
    if out.get("dataType") and _exp and str(out["dataType"]).upper() != _exp:
        problems.append(
            "CONVERT_DATA output.dataType 语料实测 %r（随子模式变），实际 %r"
            % (_exp, out["dataType"]))
    return problems


def validate_map_operation(node: dict) -> list[str]:
    """MAP_OPERATION 操作类型与联动字段校验（UI 实测）。"""
    problems: list[str] = []
    op = node.get("operationType")
    if op not in MAP_OPERATION_TYPES:
        problems.append("operationType=%r 不在值域 %s" % (op, MAP_OPERATION_TYPES))
        return problems

    expect = MAP_OPERATION_FIELDS_BY_TYPE[op]
    if op == "GET":
        if not node.get("theKey"):
            problems.append("operationType=GET 时 theKey（该值的映射键）必填")
        if node.get("paramType") not in MAP_PARAM_TYPES:
            problems.append(
                "paramType=%r 不在值域 %s" % (node.get("paramType"), MAP_PARAM_TYPES))
        if node.get("paramType") == "BASIC" and not node.get("basic"):
            problems.append("paramType=BASIC 时 basic（数据类型）必填")
        if not node.get("title"):
            problems.append("operationType=GET 时 title（节点出参名称）必填")
    elif op == "PUT":
        if not node.get("entries"):
            problems.append("operationType=PUT 时 entries（添加映射）必填")
    elif op == "REMOVE":
        if not node.get("removeKeys"):
            problems.append("operationType=REMOVE 时 removeKeys（要删除的键）必填")
    elif op == "KEY_SET":
        if not node.get("title"):
            problems.append("operationType=KEY_SET 时 title 必填")

    # 不该出现的字段
    for f in ("entries", "removeKeys", "theKey"):
        if f in node and f not in expect and node.get(f):
            problems.append("operationType=%s 不该有 %s（仅 %s 显示）"
                            % (op, f, [k for k, v in MAP_OPERATION_FIELDS_BY_TYPE.items()
                                       if f in v]))
    return problems


def validate_custom_error(node: dict) -> list[str]:
    """CUSTOM_ERROR 两种模式必填校验（UI 实测）。

    ★ 值域只有 GLOBAL / POSITION（前端 bundle errorType radio）。
      历史代码里用过的 "ERROR" 等值不是合法 errorType —— 只作提示，
      由调用方决定是否阻断（见 validate_node_ui 的 strict 参数）。
    """
    problems: list[str] = []
    et = node.get("errorType") or "GLOBAL"
    if et not in CUSTOM_ERROR_TYPES:
        # 非标准值域：只提示，不当必填错误（避免打断既存离线构造路径）
        return []
    for f in CUSTOM_ERROR_FIELDS_BY_TYPE[et]:
        if not node.get(f):
            label = "填写错误(attrError)" if f == "attrError" else f
            problems.append("errorType=%s 时 %s 必填" % (et, label))
    # 反模式：POSITION 模式还留着 error
    if et == "POSITION" and node.get("error"):
        problems.append("errorType=POSITION 时 error 应为空（UI 会清空该字段）")
    if et == "GLOBAL" and any(node.get(f) for f in
                              ("sourceData", "selectParam", "attrType", "attrError")):
        problems.append("errorType=GLOBAL 时 POSITION 专属字段应为空")
    return problems


def validate_for(node: dict) -> list[str]:
    """FOR 计数循环值域校验（UI 实测）。"""
    problems: list[str] = []
    op = node.get("operator", FOR_DEFAULT_OPERATOR)
    if op not in FOR_OPERATORS:
        problems.append("operator=%r 不在值域 %s" % (op, FOR_OPERATORS))
    step = node.get("forStep")
    if step is not None and not isinstance(step, int):
        problems.append("forStep 必须是整数，实际 %r" % type(step).__name__)
    for f in ("forStart", "forEnd"):
        v = node.get(f)
        if isinstance(v, dict) and v.get("type") == "Simple":
            s = v.get("simple")
            if isinstance(s, int) and abs(s) > FOR_VALUE_MAX:
                problems.append("%s.simple=%d 超出上限 %d" % (f, s, FOR_VALUE_MAX))
    return problems


def validate_data_mapping(node: dict) -> list[str]:
    """DATA_MAPPING 映射规则结构校验（UI 实测）。

    ★ 6 字段必填已由 `microflow_constraints.NODE_REQUIRED_FIELDS` 覆盖，
      本函数只做**结构层**校验（mappingRows 形态、mappingMode 值域、output.type）。
      不重复校验必填，避免与既有离线构造路径冲突。
    """
    problems: list[str] = []
    tt = node.get("targetType")
    if tt and tt not in DATA_MAPPING_TARGET_TYPES:
        problems.append("targetType=%r 不在值域 %s" % (tt, DATA_MAPPING_TARGET_TYPES))
    mr = node.get("mappingRule")
    if isinstance(mr, dict):
        rows = mr.get("mappingRows")
        if isinstance(rows, list) and rows:
            for i, row in enumerate(rows):
                if not row.get("targetField"):
                    problems.append("mappingRows[%d] 缺 targetField" % i)
                mode = row.get("mappingMode")
                if mode not in ("REFERENCE", "CONSTANT"):
                    problems.append(
                        "mappingRows[%d].mappingMode=%r 不在值域 ('REFERENCE','CONSTANT')"
                        % (i, mode))
                if mode == "REFERENCE" and not (row.get("value") or {}).get("reference"):
                    problems.append("mappingRows[%d] REFERENCE 模式缺 value.reference" % i)
    out = node.get("output") or {}
    # ★ 真实落库 output.type 恒为 ARRAY；离线构造可省略 output（不阻断）
    if out.get("type") and out["type"] != "ARRAY":
        problems.append(
            "DATA_MAPPING output.type 实测为 'ARRAY'（产出列表），实际 %r"
            % out.get("type"))
    return problems


def validate_publish_business_event(node: dict) -> list[str]:
    """PUBLISH_BUSINESS_EVENT 双事件类型标签与联动校验（UI 实测，落库 UNVERIFIED）。"""
    problems: list[str] = []
    et = node.get("eventType") or "AMONG_APP"
    if et not in EVENT_TYPES:
        problems.append("eventType=%r 不在值域 %s" % (et, EVENT_TYPES))
        return problems
    sel = EVENT_SELECT_FIELD[et]
    if not node.get(sel):
        problems.append(
            "eventType=%s 时 %s（可投递的事件）必填" % (et, sel))
    # 另一种事件的字段不该出现
    other = EVENT_SELECT_FIELD["IN_APP" if et == "AMONG_APP" else "AMONG_APP"]
    if node.get(other):
        problems.append("eventType=%s 不该有 %s（应为 %s）" % (et, other, sel))
    if et == "AMONG_APP":
        mt = node.get("messageType") or "DEFAULT"
        if mt not in MESSAGE_TYPES:
            problems.append("messageType=%r 不在值域 %s" % (mt, MESSAGE_TYPES))
        if mt == "DELAY" and not node.get("executeTime"):
            problems.append("messageType=DELAY 时 executeTime（发送时间）必填")
    else:
        if node.get("app"):
            problems.append("eventType=IN_APP 时 app 应隐藏（UI 不显示选择应用）")
        if node.get("messageType"):
            problems.append("eventType=IN_APP 时 messageType 应隐藏")
    # selectMq 选项必须带 contentDto，否则后续赋值字段不显示
    mq = node.get("selectMq")
    if isinstance(mq, dict) and not mq.get("contentDto"):
        problems.append(
            "selectMq 缺 contentDto（缺少会导致「赋值方式/参数」字段不渲染）")
    return problems


def validate_break_placement(node: dict, parent_chain: list[str]) -> list[str]:
    """BREAK 只能出现在 FOR_EACH / FOR 的循环体内。"""
    if node.get("actionType") != "BREAK" and node.get("type") != "BREAK":
        return []
    if not any(p in ("FOR_EACH", "FOR") for p in parent_chain):
        return ["BREAK（跳出循环）只能加在 FOR_EACH / FOR 的循环体内，"
                "根级面板不提供该节点；父链=%s" % parent_chain]
    return []


# ============================================================================
# 五、统一入口
# ============================================================================

_UI_VALIDATORS = {
    "CONVERT_DATA": validate_convert_data,
    "MAP_OPERATION": validate_map_operation,
    "CUSTOM_ERROR": validate_custom_error,
    "FOR": validate_for,
    "DATA_MAPPING": validate_data_mapping,
    "PUBLISH_BUSINESS_EVENT": validate_publish_business_event,
}


def validate_node_ui(node: dict, parent_chain: list[str] | None = None) -> list[str]:
    """按 actionType 分派到对应的 UI 层校验器。返回问题列表（空 = 通过）。"""
    action = node.get("actionType") or node.get("type") or ""
    problems: list[str] = []

    fn = _UI_VALIDATORS.get(action)
    if fn:
        problems.extend(fn(node))

    if parent_chain is not None:
        problems.extend(validate_break_placement(node, parent_chain))

    # 通用：活动节点 type 必须是 ACTIVITY
    if action and action not in ("BRANCH", "CONDITION", "FOR_EACH", "FOR",
                                 "BREAK", "CUSTOM_ERROR", "END", "TRIGGER"):
        if node.get("type") and node["type"] != "ACTIVITY":
            problems.append(
                "%s 的 type 必须是 ACTIVITY，实际 %r" % (action, node["type"]))
    return problems


def validate_schema_ui(schema: dict) -> list[str]:
    """遍历整条 dataSchema 做 UI 层校验。"""
    problems: list[str] = []

    def walk(nodes, chain):
        for n in nodes or []:
            action = n.get("actionType") or n.get("type") or ""
            for p in validate_node_ui(n, chain):
                problems.append("[%s %s] %s" % (action, n.get("nodeId", "?"), p))
            next_chain = chain + [action] if action in ("FOR_EACH", "FOR") else chain
            walk(n.get("nodes"), next_chain)
            for c in n.get("conditions") or []:
                walk(c.get("nodes"), chain)

    walk(schema.get("nodes"), [])
    return problems
