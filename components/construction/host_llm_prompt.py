"""宿主 LLM Prompt（P7-E2E-2 产品化）。

把「自然语言业务需求 → IntentDraft」这一步固化成 prompt，让任何 LLM 都能
稳定产出 `BusinessRequirementCompiler.compile()` 能吃、能归一化、能执行的草稿。

职责边界（和 requirement-to-graph.md 一致）：
- LLM 只产 IntentDraft（业务意图草稿），不产平台 JSON、不调构造器。
- 真名归一化 / 结构校验 / 歧义扫描由 Python 编译器做，LLM 不越位。

用法：
    from components.construction.host_llm_prompt import render
    system, user = render(requirement="统计失败行数...", entities=[...])
"""
from __future__ import annotations

from .intent_draft_schema import NODE_SPECS, VALUE_SLOTS

# 最常用的 kind 速查（不全列 28 个，避免 prompt 过长；冷门 kind 靠 schema 文档兜底）
_CHEATSHEET_KINDS = [
    "retrieve", "retrieve_array", "create_entity", "change_entity", "delete_entity",
    "create_batch_entity", "create_variable", "change_variable",
    "list_operation", "branch", "for_each", "for_count", "custom_error",
    "sub_microflow", "data_mapping", "break",
]

SYSTEM_PROMPT = """你是「低代码微流程生成」的宿主 LLM。

你的唯一职责：把用户的自然语言业务需求，理解并结构化成一份 IntentDraft（JSON），
交给下游确定性编译器去归一化真名、构造微流程、执行。你只做「理解业务 → 产出草稿」这一步。

## 硬约束（违反即编译失败，必须逐条遵守）

1. 只产出 IntentDraft JSON，绝不产平台节点 JSON，绝不写任何代码。
2. 实体名、字段名只能从「可用实体/字段清单」里选。清单里没有的，停下问用户，绝不猜。
   （可以用中文名或真名，编译器会归一化；但名字必须真实存在。）
3. 跨环境 id（子流程 id、事件对象、生单规则）只写业务名，绝不写数字 id。
4. 每个节点必须有稳定、有业务语义的 id（别名），例如 "查批次"、"统计失败数"、
   "写汇总"——不要用 node1/node2 这种无意义名。
5. 引用别的节点出参，只能用那个节点已经在草稿里声明过的 id（别名），
   且只能引用**前面**已声明的节点（按 nodes 数组顺序）。

## 值槽三态（写字段值、变量值、条件右值，都只能是这三种之一）

- 字面量：`{"const": <bool|int|float|str>}`
- 节点出参引用：`{"field": "<节点id>"}` 取整节点；`{"field": "<节点id>.<字段名>"}` 取 DTO 字段
- 流程入参：`{"input": "<入参名>"}`

## 表达式（filter 的过滤条件、branch 的判断条件）

递归 JSON，常用：
- 比较：`{"op": "GT|GE|LT|LE|EQ|NE", "left": {...}, "right": {...}}`
- 逻辑：`{"logic": "AND|OR", "items": [{...}, {...}]}`
- 函数：`{"fn": "containsText", "args": [[被查文本], [子串]], "dtype": "BOOLEAN"}`
- 引用节点出参，两种形态（务必分清）：
  - 标量出参（SUM/SIZE/变量等基本类型）→ `{"ref": "<节点id>"}`（如 `{"ref": "sum"}`）
  - DTO 字段 → `{"field": "<节点id>.<字段名>"}`（如 `{"field": "ra.taskId"}`）
- 实体字段（filter 里过滤当前列表的字段）→ `{"field": "<字段名>"}`

⚠ 注意：`field` 在「表达式」里是字段引用，在「值槽」里是节点引用，两者语义不同。

## 输出格式

只输出一个 JSON 对象（IntentDraft），形如：
{"nodes": [ ...按执行顺序... ], "end": {...可选...}}

不要输出任何解释、前后缀、markdown 代码块围栏以外的文字。JSON 必须合法。"""


def _render_entities(entities: list[dict]) -> str:
    """实体清单 → 可读文本。entities: [{caption, fields:[{name, caption, dataType}]}]"""
    if not entities:
        return "（未提供实体清单，调用方应注入应用内真实实体）"
    lines = []
    for e in entities:
        cap = e.get("caption") or e.get("name") or "?"
        lines.append("### 实体：%s" % cap)
        for f in e.get("fields") or []:
            fc = f.get("caption") or f.get("name") or "?"
            dt = f.get("dataType") or ""
            lines.append("  - %s（%s，%s）" % (fc, f.get("name") or "", dt))
    return "\n".join(lines)


def _render_cheatsheet() -> str:
    lines = []
    for kind in _CHEATSHEET_KINDS:
        spec = NODE_SPECS[kind]
        req = ", ".join(spec["required"]) or "无"
        lines.append("- **%s**：必填=%s；%s" % (kind, req, spec["doc"]))
        if kind == "list_operation":
            lines.append("  例：{\"kind\":\"list_operation\",\"list_node\":\"<列表节点id>\","
                         "\"op_type\":\"SUM\",\"count_fields\":[\"<字段>\"]}")
    return "\n".join(lines)


def render(requirement: str, entities: list[dict] | None = None) -> tuple[str, str]:
    """渲染 system + user 两个 prompt。

    requirement: 自然语言业务需求
    entities:    应用内实体清单（caption + fields），LLM 只能从这里选实体/字段。
    """
    user = [
        "## 可用实体/字段清单（只能从这里选，查不到就问）",
        "",
        _render_entities(entities or []),
        "",
        "## 常用节点 kind 速查",
        "",
        _render_cheatsheet(),
        "",
        "## 业务需求",
        "",
        requirement,
        "",
        "请把上面的需求结构化成 IntentDraft JSON。",
    ]
    return SYSTEM_PROMPT, "\n".join(user)


# ─────────────────── 三段式：拆解 → 确认 → 组装 ───────────────────
# 为什么分三段：直接「口语需求 → IntentDraft」是 LLM 靠语感猜业务，
# 猜错的代价是一轮 6~10 分钟的构建返工。中间插「业务拆解计划」并强制
# 用户确认后，才允许进组装。见 components/construction/business_plan.py。

def render_clarify(requirement: str) -> tuple[str, str]:
    """第一段：业务拆解。产出 BusinessPlan（elements + questions）。

    这一段的产物**不含任何节点**，只有业务能力表。用户先看这表对不对。
    """
    from .business_plan import CLARIFY_RULES

    system = CLARIFY_RULES
    user = "\n".join([
        "## 业务需求原文（用户的真实口语，可能不精确）",
        "",
        requirement,
        "",
        "请拆成业务要素表 JSON：{\"elements\": [...], \"questions\": [...]}",
        "任何拿不准的，放进 questions，不要猜。",
    ])
    return system, user


def render_assemble(plan: dict, entities: list[dict] | None = None) -> tuple[str, str]:
    """第三段：组装。输入是**用户已确认的业务计划**，不是原始口语。

    这样 LLM 不需要再理解业务，只需要按已确认的要素表挑节点 —— 
    purpose/outputShape/persistTo 都已经定死，不会跑偏。
    """
    from .business_plan import plan_routes, plan_status

    st = plan_status(plan)
    if st != "CONFIRMED":
        raise ValueError(
            "计划未确认（当前 %s），不能进入组装。先跑 render_clarify → 用户确认 → confirm_plan" % st
        )

    routes = plan_routes(plan)
    lines = [
        "## 已确认的业务计划（不要再改它，只按它挑节点）",
        "",
    ]
    for e in plan.get("elements") or []:
        lines.append("- **%s**：%s" % (e.get("key"), e.get("capability")))
        lines.append("    - 性质：%s / 入参：%s / 出参：%s"
                     % (e.get("purpose"), e.get("inputShape"), e.get("outputShape")))
        if e.get("persistTo"):
            lines.append("    - 落表：%s（%s，键=%s）"
                         % (e.get("persistTo"), e.get("persistMode"),
                            e.get("persistKey")))
        if e.get("trigger"):
            extra = ""
            if e.get("trigger") == "SCHEDULE":
                extra = "（%s，时间范围=%s）" % (e.get("scheduleCron"), e.get("timeRange"))
            lines.append("    - 触发：%s%s" % (e.get("trigger"), extra))
        if e.get("dependency"):
            lines.append("    - 依赖：%s" % e.get("dependency"))
        if e.get("gap"):
            lines.append("    - 平台缺口：%s" % "、".join(e.get("gap")))

    lines += ["", "## 建议路由（按已确认计划推导，不是猜的）", ""]
    for r in routes:
        lines.append("- %s → **%s**：%s" % (r["key"], r["route"], r["why"]))

    lines += [
        "",
        "## 可用实体/字段清单（只能从这里选，查不到就问）",
        "",
        _render_entities(entities or []),
        "",
        "## 常用节点 kind 速查",
        "",
        _render_cheatsheet(),
        "",
        "按上面的计划产出 IntentDraft JSON。计划里的字段是定死的，不要自行改动；"
        "如果计划里有 gap 标记（平台节点表达不了），对应能力不要试图用画布节点拼，"
        "在 IntentDraft 里用 sub_microflow 引用对应的 CUSTOM 微流程。",
    ]
    return SYSTEM_PROMPT, "\n".join(lines)
