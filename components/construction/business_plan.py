"""业务拆解计划（Business Plan）—— 「需求 → 计划 → 组装」流水线的中间层。

## 为什么需要这一层

平台真实返工的顺序是这样的：

    自然语言需求
        ↓  ← 这里直接跳到 IntentDraft，LLM 只能靠语感猜
    IntentDraft（节点级草稿）

猜错的代价很贵（一轮返工 = 6~10 分钟构建 + 排查）。真实案例：
两个接口都叫「XX查询」，一个写库一个只读，名字里看不出来；
一个出参是数据、一个出参只是状态码。名字相近、都叫分页，
按名字猜必错。

所以中间必须插一层**业务拆解计划**：先把「要做什么、几个能力、
每个能力是什么性质」写清楚并让用户确认，再谈怎么组装。

## 五段流水线

    ① 业务要素（BusinessElement）   —— 这一段是「理解」
    ② 结果计划（BusinessPlan）       —— 这一段是「拆解」，要用户确认
    ③ 工具/技能选型（ToolPlan）      —— 这一段是「挑工具」
    ④ IntentDraft                   —— 这一段才是「组装」
    ⑤ 平台 JSON                     —— 确定性构造器产出，LLM 不参与

本模块只定义 ①②③ 三层的数据契约与校验，不产节点、不联网、不调 LLM。
④ 见 `host_llm_prompt.py`，⑤ 见 `logic_graph.py` / `requirement_compiler.py`。

## 严格程度

`validate_plan()` 的错误分两档：
- **BLOCKING**：缺了就无法往下走（比如一个能力都没有 purpose）
- **ASK**：可以往下走，但必须先在 questions[] 里问用户

`plan_status()` 给出 `DRAFT / NEED_CONFIRM / CONFIRMED / BLOCKED`，
只有 `CONFIRMED` 才允许进入 ④。
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any

from .business_action_index import NO_REINVENT, suggest_for_capability

SCHEMA = "udc.business-plan.v1"

# ───────────────────────────── 枚举（全部闭集，不许自由发挥）─────────────────────────────

# 能力性质：这是最容易搞反的一维，必须显式填
PURPOSE = {
    "WRITE": "写入型：调外部接口后落表/改数据",
    "QUERY": "查询型：只读，把数据返回给调用方",
    "SYNC": "同步型：拉取后落表，出参只回状态（不自带查询语义）",
    "EXPORT": "导出型：拉取后生成文件/附件",
}

# 入参形态
INPUT_SHAPE = {
    "PAGE_CONDITION": "分页条件（pageNum/pageSize/时间范围等）",
    "RECORD_LIST": "一批记录（列表型入参）",
    "SINGLE_RECORD": "单条记录",
    "NONE": "无入参",
}

# 出参形态：★ 「出参不是数据」这个坑就靠这一维显式表达
OUTPUT_SHAPE = {
    "DATA_LIST": "返回数据列表（可能带 total 分页）",
    "STATUS_ONLY": "只回状态码/消息/计数，不回业务数据",
    "SINGLE_OBJECT": "返回单个对象",
    "NONE": "无出参",
}

# 落表目标
PERSIST = {
    "entity": "落到的实体业务名（留 null = 不落表）",
    "mode": "INSERT / UPSERT / REPLACE",
    "key": "UPSERT/REPLACE 时的业务键字段名（列表）",
}

# 触发方式（与平台 triggerType 对应，但这里是业务语言）
TRIGGER = {
    "MANUAL": "人工/被调触发",
    "SCHEDULE": "定时触发",
    "EVENT": "事件触发",
}

# 平台能力缺口：哪些需求平台做不到，必须走扩展代码
GAP = {
    "NO_HTTP_NODE": "平台微流程无 HTTP 节点 → 出网必须走 CUSTOM + Java 扩展",
    "CONNECTOR_NOT_HTTP": "连接器不是通用 HTTP 出口",
    "CUSTOM_REQUIRED": "需要平台节点表达不了的算法/协议",
}

# ───────────────────────────── 数据结构 ─────────────────────────────


@dataclass
class BusinessElement:
    """一个业务能力（通常对应一个接口 / 一个外部系统交互）。

    五项必填是这道闸的全部：任何一项 None 都必须进 questions[]。
    """

    key: str                      # 稳定别名，如 "syncContractPo"
    capability: str | None = None # 一句话业务语言（不出现技术名词）
    purpose: str | None = None    # PURPOSE 之一
    input_shape: str | None = None
    output_shape: str | None = None
    persist_to: str | None = None # 落表目标实体业务名；None = 不落表
    persist_mode: str | None = None
    persist_key: list[str] = dc_field(default_factory=list)
    trigger: str | None = None    # TRIGGER 之一
    schedule_cron: str | None = None
    time_range: str | None = None # 定时拉数时的时间范围口径，如 "LAST_7_DAYS"
    dependency: str | None = None # 依赖的其它能力 key
    gap: list[str] = dc_field(default_factory=list)
    reuse_checked: bool = False    # 是否已确认标品没有现成实现（必须是显式声明）

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "capability": self.capability,
            "purpose": self.purpose,
            "inputShape": self.input_shape,
            "outputShape": self.output_shape,
            "persistTo": self.persist_to,
            "persistMode": self.persist_mode,
            "persistKey": self.persist_key,
            "trigger": self.trigger,
            "scheduleCron": self.schedule_cron,
            "timeRange": self.time_range,
            "dependency": self.dependency,
            "gap": self.gap,
            "reuseChecked": self.reuse_checked,
        }


def element_from_dict(d: dict[str, Any]) -> BusinessElement:
    return BusinessElement(
        key=d.get("key") or "",
        capability=d.get("capability"),
        purpose=d.get("purpose"),
        input_shape=d.get("inputShape"),
        output_shape=d.get("outputShape"),
        persist_to=d.get("persistTo"),
        persist_mode=d.get("persistMode"),
        persist_key=list(d.get("persistKey") or []),
        trigger=d.get("trigger"),
        schedule_cron=d.get("scheduleCron"),
        time_range=d.get("timeRange"),
        dependency=d.get("dependency"),
        gap=list(d.get("gap") or []),
        reuse_checked=bool(d.get("reuseChecked")),
    )


# ───────────────────────────── 校验 ─────────────────────────────


def _is_blank(v: Any) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


def validate_element(e: BusinessElement, *, all_keys: set[str] | None = None) -> tuple[list[str], list[str]]:
    """校验单个能力。返回 (blocking, asks)。

    blocking：填了非法值（枚举外）—— 必须改
    asks：没填 —— 必须问用户，不许替用户猜
    """
    blocking: list[str] = []
    asks: list[str] = []

    if _is_blank(e.key):
        blocking.append("能力缺少 key（稳定别名）")

    # ① capability
    if _is_blank(e.capability):
        asks.append(f"{e.key}：这个能力做什么？（一句话业务语言）")

    # ② purpose —— 最贵的一维
    if _is_blank(e.purpose):
        asks.append(f"{e.key}：这是**写入型**还是**查询型**？（调完接口要不要落库）")
    elif e.purpose not in PURPOSE:
        blocking.append(f"{e.key}：purpose={e.purpose!r} 非法，只能是 {list(PURPOSE)}")

    # ③ 入参形态
    if _is_blank(e.input_shape):
        asks.append(f"{e.key}：入参是什么形态？（分页条件 / 记录列表 / 单条 / 无）")
    elif e.input_shape not in INPUT_SHAPE:
        blocking.append(f"{e.key}：inputShape={e.input_shape!r} 非法")

    # ④ 出参形态 —— 「出参不是数据」的坑
    if _is_blank(e.output_shape):
        asks.append(f"{e.key}：出参返回什么？（数据列表 / 只有状态码消息 / 单个对象 / 无）")
    elif e.output_shape not in OUTPUT_SHAPE:
        blocking.append(f"{e.key}：outputShape={e.output_shape!r} 非法")

    # ⑤ 落表一致性：WRITE/SYNC 必须说清楚落哪
    if e.purpose in ("WRITE", "SYNC"):
        if _is_blank(e.persist_to):
            asks.append(f"{e.key}：写到哪里？（目标实体业务名）")
        if _is_blank(e.persist_mode):
            asks.append(f"{e.key}：写入方式？（新增 / 有则更新 / 覆盖）")
        elif e.persist_mode not in ("INSERT", "UPSERT", "REPLACE"):
            blocking.append(f"{e.key}：persistMode={e.persist_mode!r} 非法")
        if e.persist_mode in ("UPSERT", "REPLACE") and not e.persist_key:
            asks.append(f"{e.key}：按哪些字段判断同一条记录？（业务键）")
    if e.purpose == "QUERY" and not _is_blank(e.persist_to):
        asks.append(
            f"{e.key}：标成 QUERY 却要落表到 {e.persist_to}，"
            f"确认是查询型（不落表）还是要改成写入型？"
        )

    # ⑥ 定时：时间范围从哪来
    if _is_blank(e.trigger):
        asks.append(f"{e.key}：怎么触发？（人工 / 定时 / 事件）")
    elif e.trigger not in TRIGGER:
        blocking.append(f"{e.key}：trigger={e.trigger!r} 非法")
    elif e.trigger == "SCHEDULE":
        if _is_blank(e.schedule_cron):
            asks.append(f"{e.key}：定时多久跑一次？（cron 表达式，如 0 0 1 * * ?）")
        if _is_blank(e.time_range):
            asks.append(
                f"{e.key}：定时拉数的时间范围从哪来？"
                f"（如「近 7 天」，要写成流程入参表达式，不填会空跑）"
            )

    # ⑦ 依赖存在性
    if not _is_blank(e.dependency) and all_keys is not None:
        if e.dependency not in all_keys:
            blocking.append(f"{e.key}：dependency={e.dependency!r} 不在能力清单里")

    # ⑧ gap 枚举
    for g in e.gap:
        if g not in GAP:
            blocking.append(f"{e.key}：gap={g!r} 非法，只能是 {list(GAP)}")

    # ⑨ 标品复用检查：平台已有实现的域，不许默认自己写
    if not _is_blank(e.capability) and not e.reuse_checked:
        hints = suggest_for_capability(e.capability)
        if hints:
            asks.append(
                f"{e.key}：这个能力可能标品已有实现（{('、'.join(h['domain'] for h in hints))}），"
                f"先用 business_action_index 查一下能不能直接调；"
                f"确认要自己写的话把它标成 reuseChecked=true"
            )

    return blocking, asks


def validate_plan(plan: dict[str, Any]) -> tuple[list[str], list[str]]:
    """校验整个计划。返回 (blocking, asks)。"""
    blocking: list[str] = []
    asks: list[str] = []

    raw_elements = plan.get("elements")
    if not isinstance(raw_elements, list) or not raw_elements:
        blocking.append("计划里没有任何业务要素（elements 为空）")
        return blocking, asks

    elements = [element_from_dict(x) for x in raw_elements]
    keys = {e.key for e in elements if e.key}
    if len(keys) != len([e for e in elements if e.key]):
        blocking.append("能力 key 有重复")

    for e in elements:
        b, a = validate_element(e, all_keys=keys)
        blocking.extend(b)
        asks.extend(a)

    return blocking, asks


# ───────────────────────────── 状态 ─────────────────────────────

STATUS_DRAFT = "DRAFT"
STATUS_NEED_CONFIRM = "NEED_CONFIRM"
STATUS_CONFIRMED = "CONFIRMED"
STATUS_BLOCKED = "BLOCKED"


def plan_status(plan: dict[str, Any]) -> str:
    """计划当前处于哪一档。只有 CONFIRMED 允许进入组装。"""
    blocking, asks = validate_plan(plan)
    if blocking:
        return STATUS_BLOCKED
    if asks:
        return STATUS_NEED_CONFIRM
    if not plan.get("confirmedBy"):
        return STATUS_NEED_CONFIRM
    return STATUS_CONFIRMED


def confirm_plan(plan: dict[str, Any], *, by: str = "user") -> dict[str, Any]:
    """登记用户确认。空计划 / 有 blocking 时拒绝确认。"""
    blocking, asks = validate_plan(plan)
    if blocking:
        raise ValueError("计划有硬错误，不能确认：" + "；".join(blocking))
    if asks:
        raise ValueError("计划还有未澄清项，不能确认：" + "；".join(asks))
    plan = dict(plan)
    plan["confirmedBy"] = by
    plan["confirmedAt"] = _now()
    return plan


def _now() -> str:
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


# ───────────────────────────── 工具选型 ─────────────────────────────
# 「挑工具」这一段：每个能力 → 该走哪条路（画布 / 扩展代码 / 两者）

ROUTE = {
    "CANVAS": "纯画布微流程（标准 SERVICE）能完全表达",
    "CUSTOM_EXT": "需要 Java 扩展（CUSTOM 流程 + <Xxx>ServiceService 实现）",
    "CANVAS_PLUS_EXT": "画布编排 + 扩展代码混合（如定时流程调 CUSTOM 子流程）",
}


def plan_routes(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """按能力给出建议路由。规则是确定的，不含猜测。

    判据：
    - 有 gap（出网/连接器/算法）→ CUSTOM_EXT
    - QUERY 且只是查本应用实体 → CANVAS
    - SCHEDULE 且依赖别的能力 → CANVAS_PLUS_EXT
    """
    out: list[dict[str, Any]] = []
    for raw in plan.get("elements") or []:
        e = element_from_dict(raw)
        if e.gap:
            route = "CUSTOM_EXT"
            why = "命中平台缺口：" + "、".join(GAP.get(g, g) for g in e.gap)
        elif e.trigger == "SCHEDULE" and e.dependency:
            route = "CANVAS_PLUS_EXT"
            why = "定时流程调被调能力，定时壳走画布、被调方按自主需求定"
        elif e.purpose == "QUERY" and not e.persist_to:
            route = "CANVAS"
            why = "只读本应用数据，画布节点够用"
        else:
            route = "CANVAS_PLUS_EXT"
            why = "需要落表 + 外部数据源，建议画布编排 + 扩展实现"
        out.append({"key": e.key, "route": route, "meaning": ROUTE[route], "why": why})
    return out


# ───────────────────────────── 提示词片段 ─────────────────────────────

CLARIFY_RULES = """你在做**业务拆解**，不是写代码，也不是产节点。

## 你要产出什么
一份「业务要素表」：把口语需求拆成若干个**业务能力**，每个能力填满 5 项。

## 每个能力必须填满（缺一项就进 questions，该项一律填 null）
1. capability   一句话业务语言说明这个能力干什么（不出现接口/节点等技术名词）
2. purpose      WRITE（写库）/ QUERY（只读返回）/ SYNC（拉取落表只回状态）/ EXPORT
3. inputShape   PAGE_CONDITION / RECORD_LIST / SINGLE_RECORD / NONE
4. outputShape  DATA_LIST（回数据）/ STATUS_ONLY（只回状态码消息）/ SINGLE_OBJECT / NONE
5. trigger      MANUAL / SCHEDULE（定时必须同时给 scheduleCron 和 timeRange）/ EVENT

写库类还要：persistTo（写到哪个实体）+ persistMode（INSERT/UPSERT/REPLACE）
+ persistKey（UPSERT 时按哪些字段判断同一条）。

## 必须主动排查的三个误解（真实踩过的坑）
1. 两个接口都叫「XX查询」，但一个写库一个只读
   → 按 purpose/persistTo 区分，**绝不按名字判断**
2. 「同步」「对接」这两个词，既可能指写库也可能只指调接口
   → 追问落不落表；落表就追问落哪张
3. 出参「不是数据」= STATUS_ONLY
   → 如果用户说「出参不是数据/只要状态」，必须显式填 STATUS_ONLY，
     不要留空也不要默认 DATA_LIST

## 平台已知缺口（命中就标 gap，不要试图在画布上拼）
- 调外部 HTTP 接口：平台微流程**没有 HTTP 节点** → gap: NO_HTTP_NODE
- 连接器不能当通用 HTTP 出口 → gap: CONNECTOR_NOT_HTTP

## ★ 标品复用（默认先查，不许直接自己写）
平台对下面这些域**已有现成实现**，不要重复造轮子：
- 组织/人员/部门/岗位 → OrgCommonAppService / OrgUnitBaseAppService
- 流程发起/提交/退回 → BpmAppService（22 个方法）
- 待办/事项 → AffairUdcAppService / AffairMicroflowAppService
- 文件上传下载 → StorageService（三桶）
- 枚举/字典 → EnumService / EnumAppService
- 系统变量/当前用户/日期 → SystemVariableUtils
- 日期/文本/列表函数 → 88 个表达式函数（别手写 Java）
- 对接外部系统 → 先查 cip-connector 的 *ProviderService 扩展点族

能力描述里出现这些域的关键词时，**必须**先查
`xiaozhua_business_action_index`，确认标品能不能直接调；
确认标品确实覆盖不了，才能把该能力标 `reuseChecked: true` 继续往下走。
不标 reuseChecked 会被校验拦下并反问。

## 输出
{"elements": [...], "questions": [...]}
questions 非空时，**不要输出任何推断值**，对应字段一律 null。宁可问，不要猜。
"""
