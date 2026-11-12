"""运算符与快捷函数 —— `GET /expression/operator/list` 的权威内容。

证据：LIVE（test2，2026-10-23 实测 18 运算符 / 4 快捷函数），
      结构类型 `QuickSymbolDto`（CFR: dto/operator）。

⚠ 与界面「运算符行」不完全一致（既有事实已记录）：
   接口只给 18 个真运算符 + 4 个快捷函数；
   界面还显示「可选范围」等按钮，那是前端按场景补的，不来自本接口。
   写表达式时以本模块为准，不要按界面按钮列表臆造 opType。
"""
from __future__ import annotations

# opType 值域（实测恰 5 类）
OPERATOR_OP_TYPES: tuple[str, ...] = (
    "ARITHMETIC",
    "COMPARE",
    "LOGIC",
    "BOOLEAN",
    "SYMBOL",
)

# 18 个运算符：value 是写进 token 的值，desc 是界面展示
OPERATORS: tuple[dict, ...] = (
    # ARITHMETIC 5
    {"opType": "ARITHMETIC", "value": "+", "desc": "+", "usage": ""},
    {"opType": "ARITHMETIC", "value": "-", "desc": "-", "usage": ""},
    {"opType": "ARITHMETIC", "value": "*", "desc": "×", "usage": ""},
    {"opType": "ARITHMETIC", "value": "/", "desc": "÷", "usage": ""},
    {"opType": "ARITHMETIC", "value": "%", "desc": "mod", "usage": "取余，数值1 mod 数值2"},
    # COMPARE 6
    {"opType": "COMPARE", "value": "==", "desc": "=", "usage": ""},
    {"opType": "COMPARE", "value": "!=", "desc": "!=", "usage": ""},
    {"opType": "COMPARE", "value": ">", "desc": ">", "usage": ""},
    {"opType": "COMPARE", "value": "<", "desc": "<", "usage": ""},
    {"opType": "COMPARE", "value": ">=", "desc": ">=", "usage": ""},
    {"opType": "COMPARE", "value": "<=", "desc": "<=", "usage": ""},
    # LOGIC 3
    {"opType": "LOGIC", "value": "&", "desc": "and", "usage": "逻辑与, 条件表达式1 and 条件表达式2"},
    {"opType": "LOGIC", "value": "|", "desc": "or", "usage": "逻辑或, 条件表达式1 or 条件表达式2"},
    {"opType": "LOGIC", "value": "!", "desc": "not", "usage": "逻辑非, not(条件表达式)"},
    # BOOLEAN 2
    {"opType": "BOOLEAN", "value": "true", "desc": "true", "usage": "常量，真"},
    {"opType": "BOOLEAN", "value": "false", "desc": "false", "usage": "常量，假"},
    # SYMBOL 2
    {"opType": "SYMBOL", "value": "(", "desc": "(", "usage": ""},
    {"opType": "SYMBOL", "value": ")", "desc": ")", "usage": ""},
)

# 随 operator/list 一起下发的 4 个快捷函数（不是完整函数目录）
QUICK_FUNCTIONS: tuple[dict, ...] = (
    {"value": "isNull", "desc": "为空", "args": ["对象"],
     "usage": "判断文本或属性是否为空"},
    {"value": "isNotNull", "desc": "不为空", "args": ["对象"],
     "usage": "判断文本或属性是否不为空"},
    {"value": "contains", "desc": "包含(全部)", "args": ["对象", "对象"],
     "usage": "判断一个字段是否包含全部指定值，与值顺序无关"},
    {"value": "thereIn", "desc": "属于", "args": ["对象", "对象"],
     "usage": "参数1集合是否完全属于参数2集合，或文本1是否属于文本2"},
)

# 完整函数目录（88/81）来自 preset/list，不在本模块 —— 见 facts
FULL_CATALOG_SOURCE = "preset_list"

# 运算符对应的 token.type 一律是 OPERATOR（BOOLEAN 常量也是）
OPERATOR_TOKEN_TYPE = "OPERATOR"


def operators_by_type() -> dict[str, list[dict]]:
    """按 opType 分组；分组顺序固定为 OPERATOR_OP_TYPES。"""
    out = {t: [] for t in OPERATOR_OP_TYPES}
    for op in OPERATORS:
        out[op["opType"]].append(dict(op))
    return out


def operator_values() -> tuple[str, ...]:
    return tuple(op["value"] for op in OPERATORS)


def is_operator(value: str) -> bool:
    return value in operator_values()


def quick_function_names() -> tuple[str, ...]:
    return tuple(f["value"] for f in QUICK_FUNCTIONS)
