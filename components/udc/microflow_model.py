"""微流程 dataSchema 解析、节点/动作模型与校验器 —— 证据驱动，只填可证值域。

证据基线（docs/audit/udc-semantics/microflow-source-audit.md，逐字照录，不臆造）：
- 节点类型 MicroFlowNodeTypeEnum：CONDITION / FOR_EACH / BRANCH / CUSTOM_ERROR / END / ACTIVITY / FOR / BREAK
- 活动节点 ActivityNodeTypeEnum：数据活动 / 基础服务 / 变量·集合·转换 / 实体规则 四组
- 前端创建类型 → (type, triggerType) 映射（10 项，src_redux_store_ts bundle）
- ConvertDataActivity.convertType 受控值域（11 值，ConvertDataActivity.java:35-50）
- dataSchema 根 = `nodes` 数组，节点必有 type/caption/nodeId/output；容器节点递归。

边界纪律（与全仓一致）：
- 只枚举有源码/字节码证据的值；无证据值进 UNKNOWN，不静默补全。
- 校验器只做结构 + 值域 + 容器递归 + 作用域一致性检查（离线可证面），
  不证明发布态/模板生成/运行回读（那需要宿主侧 state=20 + 生成物 + 运行数据）。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

SCHEMA_ID = "udc.construction.microflow-node.v1"

# ---------------------------------------------------------------- 值域（全有证据）

# 容器/控制节点（MicroFlowNodeTypeEnum.java:17-50）
NODE_TYPES: tuple[str, ...] = (
    "CONDITION", "FOR_EACH", "BRANCH", "CUSTOM_ERROR", "END", "ACTIVITY", "FOR", "BREAK",
)

# 活动节点受控值域（ActivityNodeTypeEnum.java:17-131，含规则活动；CALL_MICRO_FLOW 存枚举无同名 parser，UNVERIFIED）
DATA_ACTIVITIES: frozenset[str] = frozenset({
    "RETRIEVE", "RETRIEVE_ARRAY", "CREATE_ENTITY", "CREATE_BATCH_ENTITY",
    "CHANGE_ENTITY", "CHANGE_BATCH_ENTITY", "DELETE_ENTITY",
})
BASE_SERVICES: frozenset[str] = frozenset({
    "CALL_APP_SERVICE", "PUBLISH_BUSINESS_EVENT", "CONNECTOR",
    "SUB_MICROFLOW", "CALL_DATA_FLOW",
})
VARIABLE_COLLECTION_TRANSFORM: frozenset[str] = frozenset({
    "CREATE_VARIABLE", "CHANGE_VARIABLE", "CREATE_LIST", "CHANGE_LIST",
    "LIST_OPERATION", "CREATE_MAP", "MAP_OPERATION", "DATA_MAPPING", "CONVERT_DATA",
})
RULE_ACTIVITIES: frozenset[str] = frozenset({
    "ATTRIBUTE_REQUIRED", "ATTRIBUTE_UNIQUE", "ASSIGN_VALUE", "DEFAULT_VALUE", "SHOW_MESSAGE",
})

# 全量已知活动节点值域（四组合）
ACTIVITY_TYPES: frozenset[str] = (
    DATA_ACTIVITIES | BASE_SERVICES | VARIABLE_COLLECTION_TRANSFORM | RULE_ACTIVITIES
)

# 前端创建类型映射（frontend type 名 → (type, triggerType)），bundle 实证 10 项
# 注意：create REST 的 type/triggerType 是字符串枚举（TRIGGER_TYPE_VALUES 见 microflow.py），
# 这里照录前端映射，供 dry-run planner 选型，不混用 GraphQL 数字枚举。
FRONTEND_CREATE_TYPE_MAP: dict[str, tuple[str, str]] = {
    "servicedefinition": ("SERVICE", "MANUAL"),
    "customServicedefinition": ("CUSTOM", "MANUAL"),
    "eventmonitor": ("SERVICE", "BUSINESS_EVENT"),
    "timingtask": ("SERVICE", "SCHEDULE"),
    "frontend": ("FRONTEND", "MANUAL"),
    "frontendparam": ("FRONTEND_PARAM", "MANUAL"),
    "frontendfunction": ("FUNCTION", "MANUAL"),
    "entityrule": ("ENTITYRULE", "MANUAL"),
    "customEventmonitor": ("CUSTOM", "BUSINESS_EVENT"),
    "customTimingtask": ("CUSTOM", "SCHEDULE"),
}

# ConvertDataActivity.convertType 受控值域（ConvertDataActivity.java:35-50）
CONVERT_DATA_TYPES: frozenset[str] = frozenset({
    "MultiAssociation2List", "CtpEnumMultiAssociation2List",
    "String2Integer", "String2Decimal", "String2Long", "BasicData2String",
    "List2multiAssociation", "CtpEnumList2multiAssociation",
    "GetEnumCode", "GetEnumName", "Split",
})

# ---------------------------------------------------------------- 过滤条件约束（前端 xiaozhua-biz-where 实证）
#
# 操作符枚举（★权威：boot-starter-condition 5.3.308 OperatorEnum 反编译；
#   前端 xiaozhua-biz-where 少 ZERO/NOTZERO，且 NEQ 前端显示 "!=" 后端是 "<>"）：
#   EQ="="(1右参) NEQ="<>"(1) GT/LT/GE/LE(1) RLIKE/LLIKE/LIKE/NOTLIKE(1) IN/NOTIN(1)
#   NULL/NOTNULL(0右参) ZERO="= 0"/NOTZERO="<> 0"(0) BETWEEN/NOTBETWEEN(2) INCLUDE*(1)
CONDITION_OPERATORS: frozenset[str] = frozenset({
    "EQ", "NEQ", "GT", "GE", "LT", "LE", "BETWEEN", "NOTBETWEEN",
    "LIKE", "NOTLIKE", "IN", "NOTIN", "RLIKE", "LLIKE", "NULL", "NOTNULL",
    "ZERO", "NOTZERO",
    "INCLUDEALL", "NOTINCLUDEALL", "INCLUDEANY", "NOTINCLUDEANY",
})

# ★dataType → 允许的操作符（映射表 I，写错=非法）
#   LONG→BIGINTEGER；FLOAT/DOUBLE/DECIMAL/CURRENCY→INTEGER；DATE/TIME→DATETIME；
#   CTPENUM→ENUM；OBJECT/DTO→ENTITY；RichText→MULTILINESTRING
# 5.3.318 对账修正：BOOLEAN 支持 ZERO/NOTZERO；BIGINTEGER 支持 NULL/NOTNULL
#   （OperatorEnum size=0 操作符对全部数值/布尔类型可用）
CONDITION_TYPE_OPERATORS: dict[str, frozenset[str]] = {
    "STRING": frozenset({"EQ", "NEQ", "LIKE", "NOTLIKE", "IN", "NOTIN", "RLIKE", "LLIKE", "NULL", "NOTNULL"}),
    "MULTILINESTRING": frozenset({"EQ", "NEQ", "LIKE", "NOTLIKE", "RLIKE", "LLIKE", "NULL", "NOTNULL"}),
    "INTEGER": frozenset({"EQ", "NEQ", "LT", "LE", "GT", "GE", "BETWEEN", "NOTBETWEEN", "ZERO", "NOTZERO", "NULL", "NOTNULL"}),
    "BIGINTEGER": frozenset({"EQ", "NEQ", "IN", "NOTIN", "LT", "LE", "GT", "GE", "BETWEEN", "NOTBETWEEN", "ZERO", "NOTZERO", "NULL", "NOTNULL"}),
    "BOOLEAN": frozenset({"EQ", "NEQ", "ZERO", "NOTZERO"}),
    "ENUM": frozenset({"EQ", "NEQ", "IN", "NOTIN", "NULL", "NOTNULL"}),
    "DATETIME": frozenset({"EQ", "NEQ", "LT", "LE", "GT", "GE", "BETWEEN", "NOTBETWEEN", "ZERO", "NOTZERO", "NULL", "NOTNULL"}),
    "ENTITY": frozenset({"EQ", "NEQ", "IN", "NOTIN", "NULL", "NOTNULL"}),
    "ATTACHMENT": frozenset({"NULL", "NOTNULL"}),
    "MULTIENUM": frozenset({"EQ", "NEQ", "INCLUDEALL", "NOTINCLUDEALL", "INCLUDEANY",
                            "NOTINCLUDEANY", "NULL", "NOTNULL"}),
    "MULTIATTACHMENT": frozenset({"NULL", "NOTNULL"}),
    "MULTIENTITY": frozenset({"EQ", "NEQ", "INCLUDEALL", "NOTINCLUDEALL", "INCLUDEANY",
                              "NOTINCLUDEANY", "NULL", "NOTNULL"}),
    "MULTICTPENUM": frozenset({"EQ", "NEQ", "INCLUDEALL", "NOTINCLUDEALL", "INCLUDEANY",
                               "NOTINCLUDEANY", "NULL", "NOTNULL"}),
}
# 别名归一到上表键
CONDITION_TYPE_ALIAS: dict[str, str] = {
    "LONG": "BIGINTEGER", "FLOAT": "INTEGER", "DOUBLE": "INTEGER",
    "DECIMAL": "INTEGER", "CURRENCY": "INTEGER", "DATE": "DATETIME", "TIME": "DATETIME",
    "CTPENUM": "ENUM", "OBJECT": "ENTITY", "DTO": "ENTITY", "RichText": "MULTILINESTRING",
}
# 无右值操作符（rightParams 必须为空）
# 无右参（size=0）：NULL/NOTNULL/ZERO/NOTZERO（★权威 OperatorEnum.size）
CONDITION_NO_RIGHTPARAM: frozenset[str] = frozenset({"NULL", "NOTNULL", "ZERO", "NOTZERO"})
# 双右值操作符
CONDITION_TWO_RIGHTPARAM: frozenset[str] = frozenset({"BETWEEN", "NOTBETWEEN"})
# rightParam 类型值域
CONDITION_RIGHTPARAM_TYPES: frozenset[str] = frozenset({"CONSTANT", "CONTEXT_VARIABLE", "EXPRESSION"})

# DATA_MAPPING 约束（后端权威，DataMappingActivity.java 反编译）
#   targetType ∈ {ENTITY, DTO}（DataMappingTargetTypeEnum）
#   mappingMode ∈ {REFERENCE, CONSTANT}（DataMappingRow$DataMappingMode，★不是 FieldCopy）
#   mappingRule = {uuid, targetType, mappingRows:[{uuid, targetField, mappingMode, value, subobjects}]}
DATA_MAPPING_TARGET_TYPES: frozenset[str] = frozenset({"ENTITY", "DTO"})
MAPPING_MODES: frozenset[str] = frozenset({"REFERENCE", "CONSTANT"})
# DataMappingConstantValue.constantType 值域
DATA_MAPPING_CONSTANT_TYPES: frozenset[str] = frozenset({"SIMPLE", "JAVA_ENUM", "CTP_ENUM"})

# 节点必有键（buildBaseNode 补 type/caption/nodeId/output，MicroFlowParserUtils.java:468-485）
REQUIRED_NODE_KEYS: tuple[str, ...] = ("type", "nodeId")
# 节点应有键（缺失进警告而非报错——部分前端态可能省略，不臆造为硬错）
RECOMMENDED_NODE_KEYS: tuple[str, ...] = ("caption", "output")


# ---------------------------------------------------------------- 数据模型

@dataclass
class MicroFlowNode:
    """单个 dataSchema 节点（原始 dict 的规范化视图，保留原 dict 供下游用）。"""
    node_type: str                 # 控制节点 type 或活动 actionType
    node_id: str
    caption: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    children: list["MicroFlowNode"] = field(default_factory=list)

    @property
    def is_activity(self) -> bool:
        return self.node_type in ACTIVITY_TYPES

    @property
    def is_container(self) -> bool:
        return self.node_type in {"CONDITION", "BRANCH", "FOR_EACH", "FOR"}

    @property
    def group(self) -> str:
        if self.node_type in DATA_ACTIVITIES:
            return "data_activity"
        if self.node_type in BASE_SERVICES:
            return "base_service"
        if self.node_type in VARIABLE_COLLECTION_TRANSFORM:
            return "variable_transform"
        if self.node_type in RULE_ACTIVITIES:
            return "entity_rule"
        return "control" if self.node_type in NODE_TYPES else "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_type": self.node_type,
            "node_id": self.node_id,
            "caption": self.caption,
            "group": self.group,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class MicroFlowGraph:
    """dataSchema 解析出的节点图 + 校验结果。"""
    schema: str = SCHEMA_ID
    nodes: list[MicroFlowNode] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)      # 结构/值域硬错
    warnings: list[str] = field(default_factory=list)    # 缺键/UNVERIFIED
    activity_count: int = 0

    def status(self) -> str:
        return "FAIL" if self.errors else ("UNVERIFIED" if self.warnings else "PASS")

    def activity_ids(self) -> list[str]:
        out: list[str] = []
        def _walk(n: MicroFlowNode):
            if n.is_activity:
                out.append(n.node_id)
            for c in n.children:
                _walk(c)
        for n in self.nodes:
            _walk(n)
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "status": self.status(),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "activity_count": self.activity_count,
            "activity_ids": self.activity_ids(),
            "nodes": [n.to_dict() for n in self.nodes],
        }


# ---------------------------------------------------------------- 解析器

def _node_type_of(raw: dict[str, Any]) -> str:
    """节点 type：控制节点取 type；活动节点前端 actionType 可能挂在 actionType/type。

    buildBaseNode 补 type（MicroFlowParserUtils.java:468-485）；活动子节点前端用 actionType
    表达具体活动。两者都认，控制节点优先取 type。"""
    t = raw.get("type")
    at = raw.get("actionType")
    if at in ACTIVITY_TYPES:
        return str(at)
    if t:
        return str(t)
    return str(at or "")


def _parse_node(raw: dict[str, Any]) -> MicroFlowNode:
    nt = _node_type_of(raw)
    node = MicroFlowNode(
        node_type=nt,
        node_id=str(raw.get("nodeId", "")),
        caption=str(raw.get("caption", "")),
        raw=raw,
    )
    # 容器递归：CONDITION/FOR_EACH → nodes；BRANCH → conditions[*].nodes；FOR → nodes
    child_roots: list[dict[str, Any]] = []
    if nt in {"CONDITION", "FOR_EACH", "FOR"}:
        sub = raw.get("nodes")
        if isinstance(sub, list):
            child_roots.extend(sub)
    elif nt == "BRANCH":
        for cond in raw.get("conditions", []) or []:
            if isinstance(cond, dict):
                sub = cond.get("nodes")
                if isinstance(sub, list):
                    child_roots.extend(sub)
    for c in child_roots:
        if isinstance(c, dict):
            node.children.append(_parse_node(c))
    return node


def parse_data_schema(data_schema: Any, expected: list[str] | None = None) -> MicroFlowGraph:
    """解析 dataSchema（JSON 字符串或已反序列化对象）为节点图。

    expected: 若提供（宿主已知的活动 nodeId 列表），额外做「作用域一致性」软检查——
    未出现的 expected id 进 warnings（UNVERIFIED），不判硬错（保存成功 ≠ 功能成立）。
    """
    graph = MicroFlowGraph()
    root = data_schema
    if isinstance(root, str):
        try:
            root = json.loads(root)
        except json.JSONDecodeError as exc:
            graph.errors.append(f"dataSchema 非合法 JSON 字符串: {exc}")
            return graph
    if not isinstance(root, dict):
        graph.errors.append(f"dataSchema 根须为对象（含 nodes），实际 {type(root).__name__}")
        return graph

    nodes_raw = root.get("nodes")
    if not isinstance(nodes_raw, list):
        graph.errors.append("dataSchema 缺 root.nodes 数组（MicroFlowParserUtils.parseNodes 读 root 'nodes'）")
        return graph

    # MESSAGE 监听要求根 input 完整：见 _validate_message_trigger_root_input。
    # 必须放在节点循环之前——它校验的是 schema 顶层契约，与活动节点无关。
    _validate_message_trigger_root_input(graph, root)

    for raw in nodes_raw:
        if not isinstance(raw, dict):
            graph.errors.append(f"node 须为对象，实际 {type(raw).__name__}")
            continue
        node = _parse_node(raw)
        graph.nodes.append(node)
        graph._validate_node(node)
    graph.activity_count = len(graph.activity_ids())
    if expected:
        present = set(graph.activity_ids())
        for eid in expected:
            if eid not in present:
                graph.warnings.append(f"expected activity nodeId {eid!r} 未出现在 dataSchema（作用域 UNVERIFIED）")
    return graph


# ---------------------------------------------------------------- 校验器（方法挂到 graph 上）

def _validate_message_trigger_root_input(graph: MicroFlowGraph, root: dict) -> None:
    """MESSAGE 监听分支要求微流程根 input 存在且带 javaType/name。

    证据（2026-10-20 12:24:33 真实发布失败，用户提供 FreeMarker 原文）：
      autocode/JAVA/2.9/templates/microflow/event/BusinessEventListener.java.ftl
      L115 <#elseif messageSource == "MESSAGE">
      L117 <#assign subscribeType = subscribedMessageDto?then("...MessageDto",
                                                            microFlowBo.input.javaType)>
      L119 public void on${microFlowBo.input.name?cap_first}(...)
    报错点 117:109 = 求值 microFlowBo.input.javaType 时 input 为 null。

    ?then 惰性求值决定两种形态都必炸：
      subscribedMessageDto=true  → 不碰 input，L117 通过，但 L119 的 input.name 仍炸
      subscribedMessageDto=false → 直接求值 input.javaType，炸在 117:109
    因此「input 为 null」与「input 存在但缺 javaType」都是硬错，不能只查前者。

    为什么必须本地校验：平台 checkSchema 实测为浅校验
    （core/facts/udc/write-chain/microflow-rest-write-chain.md §4：4 类非法值全部
    返回 check:true, errors:0），不会在保存期拦下这类配置，只会在生成期炸。
    """
    trigger = root.get("trigger")
    if not isinstance(trigger, dict):
        return  # trigger 缺失/形状错由调用方其它规则处理，本规则只负责 MESSAGE 分支
    info = trigger.get("messageInfo")
    if not isinstance(info, dict):
        return
    if info.get("messageSource") != "MESSAGE":
        return  # EVENT / CONNECTOR / MICRO_FLOW_EVENT 走别的模板分支，不套本规则

    root_input = root.get("input")
    if not isinstance(root_input, dict):
        graph.errors.append(
            "trigger.messageInfo.messageSource=MESSAGE 要求根 input 为对象，"
            f"实际 {type(root_input).__name__}；"
            "BusinessEventListener.java.ftl:117 会求值 input.javaType、:119 会读 input.name，"
            "input 缺失必抛 Freemarker InvalidReferenceException"
        )
        return

    missing = [k for k in ("javaType", "name") if not root_input.get(k)]
    if missing:
        graph.errors.append(
            f"trigger.messageInfo.messageSource=MESSAGE 要求根 input 含 {missing}，"
            f"实际 input 键={sorted(root_input)}；"
            "BusinessEventListener.java.ftl:117 取 javaType、:119 取 name?cap_first 会抛空引用"
        )


def _validate_node(self: MicroFlowGraph, node: MicroFlowNode) -> None:
    raw = node.raw
    for key in REQUIRED_NODE_KEYS:
        if not raw.get(key):
            self.errors.append(f"节点 {node.node_id or '<noname>'} 缺必需键 {key!r}（buildBaseNode 必补）")
    # recommended 键（caption/output）只对活动节点约束；控制节点（END 等）本无 output
    if node.is_activity:
        for key in RECOMMENDED_NODE_KEYS:
            if not raw.get(key):
                self.warnings.append(f"节点 {node.node_id or '<noname>'} 缺 {key!r}（前端态可能省略，非硬错）")
    if node.node_type in ACTIVITY_TYPES:
        _ = node.group  # 已证明可归类
    elif node.node_type in NODE_TYPES:
        _ = node.group
    else:
        self.errors.append(
            f"节点 {node.node_id} type={node.node_type!r} 不在已知值域 "
            f"(NODE_TYPES {len(NODE_TYPES)} 项 + ACTIVITY_TYPES {len(ACTIVITY_TYPES)} 项)"
        )
    # 活动节点值域专项
    if node.node_type == "CONVERT_DATA":
        ct = raw.get("convertType")
        # convertType 在真实样本里可能是 dict（{type, dataType, ...}）而非字符串枚举。
        # 直接做 `ct not in frozenset` 会抛 TypeError: unhashable type: 'dict'，
        # 把整条微流程的解析打断（实测 -1014184770817921434 / -3790333238868911627 两条）。
        # 只有可哈希的字符串形态才参与值域判定；dict 形态记 warning 不判硬错。
        if isinstance(ct, dict):
            inner = ct.get("type") or ct.get("convertType")
            if isinstance(inner, str) and inner not in CONVERT_DATA_TYPES:
                self.warnings.append(
                    f"CONVERT_DATA 节点 {node.node_id} convertType.type={inner!r} 不在受控值域"
                    f"（dict 形态，仅警告不判错；ConvertDataActivity.java:35-50）")
        elif ct is not None and isinstance(ct, str) and ct not in CONVERT_DATA_TYPES:
            self.errors.append(
                f"CONVERT_DATA 节点 {node.node_id} convertType={ct!r} 不在 11 值受控值域 "
                f"{sorted(CONVERT_DATA_TYPES)}（ConvertDataActivity.java:35-50）"
            )
    if node.node_type == "CALL_DATA_FLOW":
        if not raw.get("dataFlowMappingId") and "dataFlowMappingId" not in str(raw.get("structure", "")):
            self.warnings.append(f"CALL_DATA_FLOW 节点 {node.node_id} 未见 dataFlowMappingId（生单/扣减边界，需宿主补）")
    # 过滤条件约束（RETRIEVE / RETRIEVE_ARRAY / DELETE_ENTITY 等）
    if raw.get("condition"):
        _validate_condition(self, node)
    # DATA_MAPPING 映射规则约束
    if node.node_type == "DATA_MAPPING":
        _validate_mapping_rule(self, node)
    for c in node.children:
        self._validate_node(c)


def _validate_condition(self: MicroFlowGraph, node: MicroFlowNode) -> None:
    """校验 condition（过滤条件）——操作符值域 + dataType 匹配 + rightParams 形态。"""
    cond = node.raw.get("condition")
    if not isinstance(cond, list):
        self.errors.append(f"节点 {node.node_id} condition 须为数组（前端为 [{{'type':'GROUP','conditions':[]}}]）")
        return
    for gi, grp in enumerate(cond):
        if not isinstance(grp, dict) or grp.get("type") != "GROUP":
            self.errors.append(f"节点 {node.node_id} condition[{gi}] 须为 {{type:'GROUP'}}（前端结构）")
            continue
        if not grp.get("conditions"):
            self.warnings.append(f"节点 {node.node_id} condition[{gi}] 组内无 conditions（空组=未配）")
        for ci, cc in enumerate(grp.get("conditions") or []):
            if cc.get("type") != "CONDITION":
                self.errors.append(f"节点 {node.node_id} condition[{gi}].conditions[{ci}] 须 type='CONDITION'")
                continue
            lp = cc.get("leftParam") or {}
            dt = lp.get("dataType")
            op = (cc.get("operator") or {}).get("value")
            tag = f"{node.node_id} cond[{lp.get('field')}({dt}) {op}]"
            if op not in CONDITION_OPERATORS:
                self.errors.append(f"{tag} 操作符非法（值域 {sorted(CONDITION_OPERATORS)}）")
                continue
            norm = CONDITION_TYPE_ALIAS.get(dt, dt)
            allowed = CONDITION_TYPE_OPERATORS.get(norm)
            if allowed is not None and op not in allowed:
                self.errors.append(f"{tag} 操作符与 dataType 不匹配（{norm} 允许 {sorted(allowed)}）")
            rp = cc.get("rightParams") or []
            if op in CONDITION_NO_RIGHTPARAM and rp:
                self.errors.append(f"{tag} 操作符无需 rightParams（应为空数组）")
            if op in CONDITION_TWO_RIGHTPARAM and len(rp) != 2:
                self.errors.append(f"{tag} BETWEEN/NOTBETWEEN 需 2 个 rightParams，实为 {len(rp)}")
            if op not in CONDITION_NO_RIGHTPARAM and op not in CONDITION_TWO_RIGHTPARAM and len(rp) != 1:
                self.warnings.append(f"{tag} 通常需 1 个 rightParam，实为 {len(rp)}")
            for r in rp:
                if r.get("type") not in CONDITION_RIGHTPARAM_TYPES:
                    self.errors.append(f"{tag} rightParam.type={r.get('type')!r} 非法"
                                       f"（值域 {sorted(CONDITION_RIGHTPARAM_TYPES)}）")
                # ---- 真实样本键集（udc_microflow_info 4405407084014816629 实测）----
                # rightParams[i] 必须是 {type, value, desc}；带 `key` 是错的（前端渲染成空槽位）
                for k in ("value", "desc"):
                    if k not in r:
                        self.errors.append(f"{tag} rightParams[{rp.index(r)}] 缺 {k!r}"
                                           f"（真实样本为 {{type, value, desc}}）")
                if "key" in r:
                    self.errors.append(f"{tag} rightParams[{rp.index(r)}] 含非法键 'key'"
                                       f"（真值用 desc，不是 key；否则前端渲染空槽位）")
            # operator 必须是 {value, desc}；带 `name` 是错的
            opobj = cc.get("operator") or {}
            for k in ("value", "desc"):
                if k not in opobj:
                    self.errors.append(f"{tag} operator 缺 {k!r}（真实样本为 {{value, desc}}）")
            if "name" in opobj:
                self.errors.append(f"{tag} operator 含非法键 'name'（真实样本只有 value+desc）")
            # leftParam 8 键（真实样本逐字）
            for k in ("id", "type", "javaType", "dto", "field", "desc", "dataType", "multiSelect"):
                if k not in lp:
                    self.errors.append(f"{tag} leftParam 缺 {k!r}（真实样本 8 键："
                                       f"id/type/javaType/dto/field/desc/dataType/multiSelect）")
            # 组内第 2 条起 logicalOperator 不可空（ConditionService.checkDetail 契约）
            if ci >= 1 and not cc.get("logicalOperator"):
                self.errors.append(f"{tag} 组内第 {ci + 1} 个条件缺 logicalOperator"
                                   f"（ConditionService.checkDetail：从第 2 个起必填）")


def _validate_mapping_rule(self: MicroFlowGraph, node: MicroFlowNode) -> None:
    """校验 DATA_MAPPING.mappingRule —— 后端权威结构：{uuid, targetType, mappingRows:[...]}。

    mappingMode ∈ {REFERENCE, CONSTANT}；targetType ∈ {ENTITY, DTO}。
    """
    mr = node.raw.get("mappingRule")
    if not isinstance(mr, dict):
        self.errors.append(f"DATA_MAPPING 节点 {node.node_id} 缺 mappingRule"
                           f"（{{uuid,targetType,mappingRows:[]}}，DataMappingActivity 权威）")
        return
    tt = mr.get("targetType")
    if tt is not None and tt not in DATA_MAPPING_TARGET_TYPES:
        self.errors.append(f"DATA_MAPPING 节点 {node.node_id} targetType={tt!r} 非法"
                           f"（值域 {sorted(DATA_MAPPING_TARGET_TYPES)}）")
    rows = mr.get("mappingRows")
    if rows is None:
        self.errors.append(f"DATA_MAPPING 节点 {node.node_id} mappingRule 缺 mappingRows"
                           f"（★不是 mappings，DataMappingActivity.java getArray(\"mappingRows\")）")
        return
    if not isinstance(rows, list):
        self.errors.append(f"DATA_MAPPING 节点 {node.node_id} mappingRows 须为数组")
        return
    if len(rows) == 0:
        self.warnings.append(f"DATA_MAPPING 节点 {node.node_id} mappingRows 为空——不报错但不做任何转换（空转）")
    for i, m in enumerate(rows):
        mm = m.get("mappingMode")
        if mm not in MAPPING_MODES:
            self.errors.append(f"DATA_MAPPING 节点 {node.node_id} mappingRows[{i}].mappingMode={mm!r} 非法"
                               f"（值域 {sorted(MAPPING_MODES)}；★不是 FieldCopy）")
        if not m.get("targetField"):
            self.errors.append(f"DATA_MAPPING 节点 {node.node_id} mappingRows[{i}] 缺 targetField")
        if not m.get("value"):
            self.errors.append(f"DATA_MAPPING 节点 {node.node_id} mappingRows[{i}] 缺 value"
                               f"（{{constant|expression|reference}}）")



MicroFlowGraph._validate_node = _validate_node  # 挂实例方法（保持 dataclass 简洁）


def classify_microflow_type(frontend_type: str) -> tuple[str, str] | None:
    """前端创建类型 → (type, triggerType)；未知返回 None（进 unknowns，不臆造）。"""
    return FRONTEND_CREATE_TYPE_MAP.get(frontend_type)


__all__ = [
    "SCHEMA_ID", "NODE_TYPES", "ACTIVITY_TYPES",
    "DATA_ACTIVITIES", "BASE_SERVICES", "VARIABLE_COLLECTION_TRANSFORM", "RULE_ACTIVITIES",
    "FRONTEND_CREATE_TYPE_MAP", "CONVERT_DATA_TYPES",
    "CONDITION_OPERATORS", "CONDITION_TYPE_OPERATORS", "CONDITION_TYPE_ALIAS",
    "CONDITION_NO_RIGHTPARAM", "CONDITION_TWO_RIGHTPARAM", "CONDITION_RIGHTPARAM_TYPES",
    "MAPPING_MODES",
    "REQUIRED_NODE_KEYS", "RECOMMENDED_NODE_KEYS",
    "MicroFlowNode", "MicroFlowGraph",
    "parse_data_schema", "classify_microflow_type",
]
