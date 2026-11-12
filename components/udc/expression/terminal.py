"""函数面裁剪 —— 各模块"能力多少不同"的真正开关。

证据：LIVE（test2，2026-10-23）实测 `POST /expression/preset/list`

    terminalSupportType=BACKEND   88 函数 / 8 组
        基础函数15 日期函数24 数学函数10 文本函数17
        条件函数1  聚合函数18 变化函数1  枚举函数2
    terminalSupportType=FRONTEND  81 函数 / 6 组
        基础函数11 日期函数24 数学函数10 文本函数17 条件函数1 聚合函数18
        （缺 变化函数1 + 枚举函数2，基础函数少 4 个）
    terminalSupportType=ALL       81（同 FRONTEND）
    terminalSupportType=""        BOOT_3002
    terminalSupportType=DESIGN    BOOT_3002
    terminalSupportType=RUNTIME   BOOT_3002

变量面（131 项 / 4 组：organization 95 / date 33 / env 2 / plugin 1）
**三种 terminal 完全一致** —— 说明裁剪只作用于函数，不作用于系统变量。

这条纠正了一个常见误判：
    「页面规则能力弱、微流程能力强」
→ 真实差异来自 terminalSupportType（前端跑 vs 后端跑）与 paramType（变量从哪来），
  不是来自"模块等级"。同一个模块配不同 terminal 也会拿到不同函数集。
"""
from __future__ import annotations

TERMINAL_BACKEND = "BACKEND"
TERMINAL_FRONTEND = "FRONTEND"
TERMINAL_ALL = "ALL"

# 合法值（其余报 BOOT_3002）
TERMINAL_SUPPORTED: tuple[str, ...] = (
    TERMINAL_BACKEND,
    TERMINAL_FRONTEND,
    TERMINAL_ALL,
)

# 函数分组实测计数
FUNCTION_GROUP_COUNTS: dict[str, dict[str, int]] = {
    TERMINAL_BACKEND: {
        "基础函数": 15, "日期函数": 24, "数学函数": 10, "文本函数": 17,
        "条件函数": 1, "聚合函数": 18, "变化函数": 1, "枚举函数": 2,
    },
    TERMINAL_FRONTEND: {
        "基础函数": 11, "日期函数": 24, "数学函数": 10, "文本函数": 17,
        "条件函数": 1, "聚合函数": 18,
    },
}
FUNCTION_GROUP_COUNTS[TERMINAL_ALL] = FUNCTION_GROUP_COUNTS[TERMINAL_FRONTEND]

# 系统变量分组计数（与 terminal 无关）
SYSTEM_VARIABLE_GROUP_COUNTS: dict[str, int] = {
    "organization": 95,
    "date": 33,
    "env": 2,
    "plugin": 1,
}
SYSTEM_VARIABLE_TOTAL = sum(SYSTEM_VARIABLE_GROUP_COUNTS.values())

# 只有 BACKEND 才有的组 —— 涉及"变化"(前后值对比) 与"枚举"解析
BACKEND_ONLY_GROUPS: tuple[str, ...] = ("变化函数", "枚举函数")


def is_valid_terminal(terminal: str) -> bool:
    return terminal in TERMINAL_SUPPORTED


def function_count_for(terminal: str) -> int:
    """该 terminal 下的函数总数；非法 terminal 直接抛，不返回 0 掩盖错误。"""
    if not is_valid_terminal(terminal):
        raise ValueError(
            "terminalSupportType=%r 非法；合法值: %s（空串/DESIGN/RUNTIME 均报 BOOT_3002）"
            % (terminal, ", ".join(TERMINAL_SUPPORTED))
        )
    return sum(FUNCTION_GROUP_COUNTS[terminal].values())


def groups_for(terminal: str) -> tuple[str, ...]:
    if not is_valid_terminal(terminal):
        raise ValueError("terminalSupportType=%r 非法" % (terminal,))
    return tuple(FUNCTION_GROUP_COUNTS[terminal])


def has_group(terminal: str, group: str) -> bool:
    return group in groups_for(terminal)
