"""宿主意图 → 组件内只读 action 的最小路由表与发现面。

为什么需要这一层：`XiaozhuaAgent.route` 只回答「哪个组件」，`dispatch` 随后对 udc 域
固定用 `inspect_application`。于是宿主问「微流程节点怎么配」时永远拿不到
`inspect_microflow`（该 action 早在 `UdcComponent.capabilities()` 里，却没有任何
入口能选中它）。本模块把「意图关键词 → action」显式登记，并只对组件**已登记**的
能力生效，避免凭空造 action。

纪律：
  1. 表是白名单，不是猜测器；未命中就走调用方给的 default。
  2. 规则顺序即优先级，更具体的 action 在前。
  3. `intent_index()` 只回显组件真实 capabilities，供宿主发现「能问什么」。
  4. 关键词命中要过否定判定（`keyword_matches`）：同一分句内、关键词之前的显式
     否定词（不要/不用/跳过/ignore…）会取消该次命中。否定不外溢到其他分句，
     「不只看」「区别」这类递进或构词不当作否定；判不准时按未命中处理（保守回默认 action）。
"""
from __future__ import annotations

import re
from typing import Iterable

# domain → [(action, keywords)]，顺序即优先级
INTENT_RULES: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "udc": (
        ("inspect_microflow", ("微流程", "microflow", "micro-flow")),
    ),
}

# 组件域的默认只读 action（无更具体命中时）
DEFAULT_ACTIONS: dict[str, str] = {
    "udc": "inspect_application",
}
FALLBACK_ACTION = "inspect"


_CLAUSE_PATTERN = re.compile(r"[，,；;。！!？?\n]|而是|但是|不过|然而|但")


# 显式否定词，不用裸「不」：避免「不支持/不同/不足」这类陈述被当成否定。
# 单字「别/勿」不入表（「区别/类别/分别」会被误伤），宁可漏判也不误判。
_NEGATION_CUES: tuple[str, ...] = (
    "不要", "不用", "不需要", "不必", "无需", "无须", "不看", "不分析", "不做",
    "不查", "不涉及", "不包括", "不考虑", "不关注", "跳过", "忽略", "排除",
)
# 刻意不收「不是/并非/no/not」：既可能是排除，也可能是「是不是…」「not only」类
# 疑问或限定，语义不确定时按未命中处理会误伤真实意图，故保守地不判否定。
_EN_NEGATION_CUES: tuple[str, ...] = (
    "skip", "ignore", "without", "exclude", "don't", "do not", "no need", "not need",
)

# 「不要只看微流程」「不只看微流程」是递进/限定，不是排除。
_NEGATION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(re.escape(cue) + r"(?!只|仅|单)") for cue in _NEGATION_CUES
) + tuple(
    re.compile(r"(?<![a-z])" + re.escape(cue) + r"(?![a-z])(?!\s*only)")
    for cue in _EN_NEGATION_CUES
)

# 后置否定：只认「看/分析/查」这类观察动词，避免把「微流程不需要重新部署」
# 这种仍在问微流程的句子误判成排除。
_POST_NEGATION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(r"^(这块|这块先|先|就)?\s*" + re.escape(cue))
    for cue in ("不用看", "不用分析", "不用查", "不必看", "不必分析", "不必查", "不看", "不分析", "不查")
)


def _is_negated(prefix: str, suffix: str = "") -> bool:
    """分句内、关键词之前是否出现过否定词；也接受紧跟其后的后置否定（「微流程不用看」）。"""
    if any(pattern.search(prefix) for pattern in _NEGATION_PATTERNS):
        return True
    return any(pattern.match(suffix) for pattern in _POST_NEGATION_PATTERNS)


def _keyword_positions(term: str, clause: str) -> list[int]:
    if term.isascii() and term.isalpha():
        pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
        return [m.start() for m in re.finditer(pattern, clause)]
    positions: list[int] = []
    start = clause.find(term)
    while start >= 0:
        positions.append(start)
        start = clause.find(term, start + 1)
    return positions


def keyword_matches(term: str, text: str) -> bool:
    """存在**未被否定**的关键词命中即算命中。

    中文按子串；ASCII 字母关键词要求字母数字边界（避免 microflows 命中 microflow）。
    否定只在同一分句内、且必须出现在关键词之前（或紧跟其后的观察动词否定），
    避免跨句误伤；整句只有被否定的命中时返回 False，调用方据此回默认 action。
    """
    for clause in _CLAUSE_PATTERN.split(text):
        for position in _keyword_positions(term, clause):
            suffix = clause[position + len(term):]
            if not _is_negated(clause[:position], suffix):
                return True
    return False


def rules_for(domain: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return INTENT_RULES.get(domain, ())


def default_action(domain: str) -> str:
    return DEFAULT_ACTIONS.get(domain, FALLBACK_ACTION)


def resolve_action(domain: str, intent: str, capabilities: Iterable[str]) -> str:
    """按优先级挑第一个「已登记能力 + 关键词命中」的 action；否则回默认。

    默认 action 同样要落在组件已登记能力里：域默认（如 udc 的
    inspect_application）不在 capabilities 时退到通用 `inspect`，避免派发一个
    组件没有的 action。两者都不在时保留域默认值（交由 registry 报 UNAVAILABLE）。
    """
    caps = set(capabilities or ())
    text = (intent or "").lower()
    for action, keywords in rules_for(domain):
        if action not in caps:
            continue
        if any(keyword_matches(k, text) for k in keywords):
            return action
    for action in (default_action(domain), FALLBACK_ACTION):
        if action in caps:
            return action
    return default_action(domain)


def intent_index(domain: str, capabilities: Iterable[str]) -> dict[str, list[str]]:
    """组件实际可命中的意图表：{action: [keywords]}；未登记的 action 不出现。"""
    caps = set(capabilities or ())
    return {action: list(keywords) for action, keywords in rules_for(domain) if action in caps}
