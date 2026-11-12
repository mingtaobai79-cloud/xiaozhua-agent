"""把微流程节点的值字段批量升级为表达式（API 路径，不依赖 UI）。

## 为什么需要这个模块

微流程里每个「值」字段（节点参数、映射行值、循环边界、错误定位文本……）
在 schema 里都是一个值包装对象：

    {"type": "Simple", "simple": 0, "desc": 0}                常量
    {"type": "SelectParam", "selectParam": {...}}             选变量
    {"type": "Expression", "expression": {"title", "schema"}}  表达式

把 Simple/SelectParam 升级成 Expression 需要：
  1. 选一个类型匹配、且【执行顺序在前】的变量
  2. 装配 ExpressionSaveDto 并过 /check + /transform
  3. 写回 dataSchema 再整体 udcMicroflowUpdatePost

## 关键约束（都是实测踩出来的）

- **执行顺序**：表达式只能引用本节点之前已执行节点的输出
- **系统变量**：`system.*` 不依赖前置节点，任何位置都能用，
  且 token 类型是 `SYSTEM` 不是 `VARIABLE`，schemas 可为空
- **resultTypeInfo 值域 15 个**：`OBJECT` 非法（FORMULA_6003），
  DTO 要用 `ENTITY` 且必须带 `resultTypeFullName`（否则 FORMULA_6901）
- **类型名归一化**：后端存在 `String`（小写 s）与 `STRING` 两种写法，
  `Long` ≡ `BIGINTEGER`，比较前必须归一化
- **DTO 字段**：若字段自带 `selectParam.id`，用它构造 schemas 最准
- **不能无脑全改**：DTO 选择器类字段（如 RETRIEVE_ARRAY.pageInfo 指向
  PageInfo 实例）保持 SelectParam，强行表达式化会 FORMULA_6901

## 用法

    from components.udc.microflow.expression_fill import (
        iter_value_slots, norm_type, build_expression_dto, apply_plan,
    )
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

# 值包装类型
VALUE_TYPES: tuple[str, ...] = ("Simple", "SelectParam", "Expression")

# resultTypeInfo 合法值域（15 个；OBJECT 不在其中）
SUPPORTED_RESULT_TYPES: tuple[str, ...] = (
    "INTEGER", "BIGINTEGER", "DECIMAL", "STRING", "MULTILINESTRING",
    "DATETIME", "DATE", "TIME", "BOOLEAN", "CURRENCY", "ATTACHMENT",
    "ARRAY", "ENTITY", "CTPENUM", "ENUM",
)

# 数值族
NUMERIC_TYPES: frozenset[str] = frozenset(
    {"INTEGER", "BIGINTEGER", "LONG", "DECIMAL", "DOUBLE"})
# 文本族
STRING_TYPES: frozenset[str] = frozenset(
    {"STRING", "MULTILINESTRING", "TEXT"})


def norm_type(dt) -> str:
    """归一化后端类型名。

    后端同一概念有多种写法，不归一会导致「明明有变量却匹配不到」：
        String  → STRING
        Long    → BIGINTEGER（平台口径）
        Object / Dto → DTO
    """
    t = (dt or "").strip().upper()
    if t == "LONG":
        return "BIGINTEGER"
    if t in ("OBJECT", "DTO"):
        return "DTO"
    return t or "STRING"


def iter_value_slots(node: dict):
    """递归产出 (path, slot)，只含值包装，不进入 output/input/mfService。"""
    found: list[tuple[str, dict]] = []

    def rec(obj, path, depth=0):
        if depth > 12:
            return
        if isinstance(obj, dict):
            if obj.get("type") in ("Simple", "SelectParam") and any(
                    k in obj for k in ("simple", "selectParam")):
                found.append((path, obj))
                return
            for k, v in obj.items():
                if k in ("output", "input", "mfService"):
                    continue
                rec(v, "%s.%s" % (path, k) if path else k, depth + 1)
        elif isinstance(obj, list):
            for i, x in enumerate(obj):
                rec(x, "%s[%d]" % (path, i), depth + 1)

    rec(node, "")
    yield from found


def slot_want_type(slot: dict) -> str:
    """该槽位期望的表达式结果类型。"""
    if slot.get("type") == "SelectParam":
        sp = slot.get("selectParam") or {}
        return norm_type(sp.get("dataType"))
    v = slot.get("simple")
    if isinstance(v, bool):
        return "BOOLEAN"
    if isinstance(v, int):
        return "INTEGER"
    if isinstance(v, float):
        return "DECIMAL"
    return "STRING"


def _scalar_schemas(name: str, dtype: str, desc: str = "") -> list:
    """标量变量 → schemas 树（根 OBJECT + 自身 OBJECT + value 叶子）。"""
    return [{
        "name": name, "description": desc[:20], "type": "OBJECT",
        "selectable": False, "enableDataI18n": False, "skip": True,
        "uniformityParams": {"paramId": name, "paramCategory": "DTO"},
        "properties": [{
            "name": name, "description": desc[:20], "type": "OBJECT",
            "selectable": True, "enableDataI18n": False, "skip": True,
            "uniformityParams": {"paramId": name, "paramCategory": "OBJECT"},
            "properties": [{
                "name": "value", "description": "取值", "type": dtype,
                "selectable": True, "enableDataI18n": False, "skip": True,
                "uniformityParams": {"paramId": "%s.value" % name,
                                     "paramCategory": dtype},
            }],
        }],
    }]


def _dto_schemas(name: str, param_id: str, desc: str = "") -> list:
    return [{
        "name": name, "description": desc[:20], "type": "OBJECT",
        "selectable": False, "enableDataI18n": False, "skip": True,
        "uniformityParams": {"paramId": param_id, "paramCategory": "DTO"},
        "properties": [{
            "name": name, "description": desc[:20], "type": "OBJECT",
            "selectable": True, "enableDataI18n": False, "skip": True,
            "uniformityParams": {"paramId": param_id, "paramCategory": "OBJECT"},
            "properties": [],
        }],
    }]


def build_expression_dto(var: dict, want: str) -> dict:
    """构造 ExpressionSaveDto。

    var:  {name, dataType, desc, paramId?, system?}
    want: 目标结果类型（已在 SUPPORTED_RESULT_TYPES 内）
    """
    name = var["name"]
    u = lambda: str(uuid.uuid4())
    is_sys = bool(var.get("system"))

    if is_sys:
        sym = {"uid": u(), "type": "SYSTEM", "value": name,
               "desc": var.get("desc") or ""}
        if want in NUMERIC_TYPES:
            tokens = [sym,
                      {"uid": u(), "type": "OPERATOR", "value": "+", "desc": "+"},
                      {"uid": u(), "type": "CONSTANT", "value": "0", "desc": "0"}]
            rt = "INTEGER" if want == "INTEGER" else want
        elif want == "BOOLEAN":
            tokens = [sym,
                      {"uid": u(), "type": "OPERATOR", "value": "=", "desc": "="},
                      {"uid": u(), "type": "CONSTANT", "value": "true", "desc": "true"}]
            rt = "BOOLEAN"
        else:
            tokens = [sym]
            rt = want if want in ("DATETIME", "DATE", "TIME") else "STRING"
        return {"resultTypeInfo": rt, "schemas": [], "tokens": tokens,
                "isMultiSelect": False, "terminalSupportType": "BACKEND"}

    desc = var.get("desc") or ""
    if want in NUMERIC_TYPES:
        return {"resultTypeInfo": "INTEGER" if want == "INTEGER" else want,
                "schemas": _scalar_schemas(name, want, desc),
                "tokens": [{"uid": u(), "type": "VARIABLE",
                            "value": "%s.%s.value" % (name, name), "desc": desc},
                           {"uid": u(), "type": "OPERATOR", "value": "+", "desc": "+"},
                           {"uid": u(), "type": "CONSTANT", "value": "0", "desc": "0"}],
                "isMultiSelect": False, "terminalSupportType": "BACKEND"}
    if want == "BOOLEAN":
        return {"resultTypeInfo": "BOOLEAN",
                "schemas": _scalar_schemas(name, "BOOLEAN", desc),
                "tokens": [{"uid": u(), "type": "VARIABLE",
                            "value": "%s.%s.value" % (name, name), "desc": desc},
                           {"uid": u(), "type": "OPERATOR", "value": "=", "desc": "="},
                           {"uid": u(), "type": "CONSTANT", "value": "true", "desc": "true"}],
                "isMultiSelect": False, "terminalSupportType": "BACKEND"}
    if want == "DTO":
        pid = var.get("paramId") or name
        return {"resultTypeInfo": "ENTITY", "resultTypeFullName": pid,
                "schemas": _dto_schemas(name, pid, desc),
                "tokens": [{"uid": u(), "type": "VARIABLE",
                            "value": "%s.%s" % (name, name), "desc": desc}],
                "isMultiSelect": False, "terminalSupportType": "BACKEND"}
    # STRING 及其它
    return {"resultTypeInfo": "STRING",
            "schemas": _scalar_schemas(name, "STRING", desc),
            "tokens": [{"uid": u(), "type": "VARIABLE",
                        "value": "%s.%s.value" % (name, name), "desc": desc}],
            "isMultiSelect": False, "terminalSupportType": "BACKEND"}


def _load_function_catalog() -> dict:
    """加载函数签名清单（88 个，LIVE preset/list）。"""
    p = Path(__file__).parent / "function_catalog.json"
    if not p.exists():
        return {}
    try:
        return (json.loads(p.read_text(encoding="utf-8")).get("functions") or {})
    except Exception:
        return {}


#: 函数签名清单：name -> {desc, category, paramCount, argDescs}
FUNCTION_CATALOG: dict = _load_function_catalog()


def build_function_token(func_name: str, arg_token_groups: list) -> dict:
    """构造 FUNCTION token。

    arg_token_groups 是 [[子token...], ...]（外层参数组，内层 token 序列）。
    例：roundOffFloor(变量/999) → [[VARIABLE, OPERATOR, CONSTANT]]
    """
    meta = FUNCTION_CATALOG.get(func_name) or {}
    return {
        "uid": str(uuid.uuid4()),
        "type": "FUNCTION",
        "value": func_name,
        "desc": meta.get("desc") or func_name,
        "subOps": arg_token_groups,
    }


def build_function_expression_dto(func_name: str, arg_token_groups: list,
                                  want: str,
                                  result_type_full_name: str | None = None,
                                  schemas: list | None = None) -> dict:
    """构造 FUNCTION 表达式 ExpressionSaveDto（/check /transform 输入形态）。

    与 build_expression_dto 的关键差异（实测 skeleton_110 roundOffFloor）：
    - tokens 只有一个 FUNCTION token，subOps 二维数组装参数
    - resultTypeInfo = 函数返回类型（want 由槽位期望类型决定）

    schemas 是参数变量的上下文树（/transform 解析参数 VARIABLE 用）：
    闸门层（validate/gates）不查 schemas，可传 None；提交层（/transform）
    必须传参数变量的 context → context_to_schemas() 裁剪结果，否则参数
    变量无法解析。skeleton_110 里该值来自 designData.context 的裁剪。
    """
    if func_name not in FUNCTION_CATALOG:
        raise KeyError(
            f"未知函数 {func_name!r}，不在 88 个函数目录里 "
            f"(core/facts/udc/expression/functions.md)")
    dto = {
        "resultTypeInfo": want,
        "schemas": schemas,  # 参数变量上下文（/transform 用；闸门层可 None）
        "tokens": [build_function_token(func_name, arg_token_groups)],
        "isMultiSelect": False,
        "terminalSupportType": "BACKEND",
    }
    if result_type_full_name:
        dto["resultTypeFullName"] = result_type_full_name
    return dto


def pick_variable(pool: list[dict], want: str):
    """从候选变量里挑第一个类型匹配的。pool 已按「前置 + 系统变量」准备。"""
    for v in pool:
        dt = v.get("dataType")
        if want in NUMERIC_TYPES and dt in NUMERIC_TYPES:
            return v
        if want == "BOOLEAN" and dt == "BOOLEAN":
            return v
        if want == "DATETIME" and dt == "DATETIME":
            return v
        if want == "DTO" and dt == "DTO":
            return v
        if want == "STRING" and dt in STRING_TYPES:
            return v
        if want == "ENTITY" and dt in ("DTO", "ENTITY"):
            return v
    return None


def walk_ordered(nodes, out=None) -> list:
    """按执行顺序遍历（条件分支的 nodes 先于后续兄弟）。"""
    if out is None:
        out = []
    for n in nodes or []:
        out.append(n)
        for c in n.get("conditions") or []:
            walk_ordered(c.get("nodes"), out)
        walk_ordered(n.get("nodes"), out)
    return out


def available_vars(ordered: list, idx: int, sysvars: list | None = None) -> list:
    """第 idx 个节点可用的变量：前置输出 + 系统变量。"""
    pool = []
    for j in range(idx):
        o = ordered[j].get("output")
        if isinstance(o, dict) and o.get("name"):
            pool.append({"name": o["name"],
                         "dataType": norm_type(o.get("dataType")),
                         "desc": o.get("desc") or "",
                         "paramId": o.get("id") or o.get("javaType") or o["name"]})
    return pool + list(sysvars or [])
