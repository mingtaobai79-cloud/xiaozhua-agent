"""P3 逻辑图 DSL：JSON 表达式 → P2 的 AST。

## 为什么单独一层

逻辑图是 JSON（可序列化、可审阅、可 diff），AST 是 Python 对象。
JSON 装不下 `Compare(...)`，所以中间必须有一层确定性翻译：

```json
{"op": "EQ", "left": {"field": "ds.enabled"}, "right": {"const": true}}
{"fn": "containsText", "args": [[{"field": "ds.jdbcUrl"}, {"const": "mysql"}]]}
{"logic": "AND", "items": [...]}       {"arith": "ADD", "items": [...]}
{"ref": "res"}                          {"sys": "currentTime"}
```

## 顺序裁决在这里做（不放执行器）

`{"field": "ds.jdbcUrl"}` 的 `ds` 必须已执行。若把这条检查放执行器，
执行器就得知道表达式的内部结构；放这里，DSL 解析失败直接抛，位置精确到节点。

★ 平台不会拦这种错：check 只看 context 里有没有这个名字，**有就过**，
运行期才取不到值。这是「check 绿、跑起来空」的经典来源。

## 节点引用 vs 输入引用

- `{"ref": "res"}`   → 引用某节点整体输出（BOOLEAN/数字等基本类型节点）
- `{"field": "ds.jdbcUrl"}` → 引用节点出参的字段（三级 VARIABLE）
- `{"input": "field"}` → 引用流程入参（`$input.<field>`，MANUAL 入参 DTO）
"""
from __future__ import annotations

from typing import Any

from ..udc.microflow.expression_model import (
    Arithmetic, Compare, Cond, Const, ExpressionError, Func, Logic, NodeField, SysVar,
)
from .loop_scope import (
    LoopScopeStack, ScopeError, is_loop_item_ref, parse_loop_item_ref,
)


class DslError(ValueError):
    """表达式 DSL 非法。"""


# 运算符白名单（与 P2 的 Compare/Arithmetic/Logic 对齐，不接受别名猜测）
_CMP = frozenset({"EQ", "NE", "GT", "GE", "LT", "LE"})
_LOGIC = frozenset({"AND", "OR"})
_ARITH = frozenset({"ADD", "SUB", "MUL", "DIV"})

# 判定性函数（返回布尔）：仅这些默认推断为 BOOLEAN，其余默认 STRING。
# ★ 白名单而非黑名单：宁可让用户显式写 dtype，也不要猜错类型导致
#   "Logic 子项应为 BOOLEAN" 这种指向性很差的报错。
_BOOL_FUNCS = {
    "containsText": "BOOLEAN", "notContainsText": "BOOLEAN",
    "contains": "BOOLEAN", "notContains": "BOOLEAN",
    "containsAny": "BOOLEAN", "notContainsAny": "BOOLEAN",
    "isNull": "BOOLEAN", "isNotNull": "BOOLEAN",
    "startsWith": "BOOLEAN", "endsWith": "BOOLEAN",
    "equals": "BOOLEAN", "notEquals": "BOOLEAN",
    "greaterThan": "BOOLEAN", "lessThan": "BOOLEAN",
}

# 常见中文/近义写法 → 规范 op（只做**显式**别名，不做模糊匹配）
_OP_ALIAS = {"==": "EQ", "!=": "NE", ">": "GT", ">=": "GE", "<": "LT", "<=": "LE",
             "=": "EQ", "AND": "AND", "OR": "OR", "+": "ADD", "-": "SUB",
             "*": "MUL", "/": "DIV"}


def _norm_op(raw: str, allowed: frozenset, kind: str) -> str:
    op = _OP_ALIAS.get(str(raw).strip(), str(raw).strip().upper())
    if op not in allowed:
        raise DslError("%s 不支持运算符 %r（可用：%s）" % (kind, raw, sorted(allowed)))
    return op


def parse_expr(spec: Any, *, resolver=None, scope=None, loops=None):
    """表达式 DSL → AST。返回的 AST 带 `_refs`（供编译器注册 context）。

    loops: LoopScopeStack（P3.1 循环作用域；不在循环内传 None）
    """
    refs: list[dict] = []
    ast = _parse(spec, resolver=resolver, scope=scope, refs=refs, loops=loops)
    try:
        ast._refs = refs
    except AttributeError:
        pass
    return ast


def _need(resolver, scope, alias: str, where: str) -> None:
    """顺序裁决：alias 必须已执行（$input 永远可用）。"""
    if resolver is None:
        # 无解析器做不了形式校验，但顺序仍要判
        if scope is not None and not scope.has(alias):
            raise DslError("%s 引用了尚未执行的节点 %r（已执行：%s）"
                           % (where, alias, scope.available()[:8]))
        return
    if scope is not None and not scope.has(alias):
        raise DslError("%s 引用了尚未执行的节点 %r（已执行：%s）"
                       % (where, alias, scope.available()[:8]))


def _parse(spec: Any, *, resolver, scope, refs: list, where: str = "expr", loops=None):
    if not isinstance(spec, dict):
        raise DslError("%s 必须是对象，得到 %r" % (where, type(spec).__name__))

    # ---- 叶子 ----
    if is_loop_item_ref(spec):
        # P3.1 循环项引用：{"item":"eachDs","field":"id"} 或
        # {"field":{"source":"eachDs","path":"id"}}
        return _loop_item_ref(spec, resolver, refs, loops, where)
    if "const" in spec:
        v = spec["const"]
        return Const(v, _guess_type(v, spec.get("dtype")))
    if "sys" in spec:
        name = spec["sys"]
        if not name:
            raise DslError("%s.sys 不能为空" % where)
        return SysVar(name, spec.get("dtype") or "STRING")
    if "ref" in spec:
        alias = spec["ref"]
        if alias == "$input":
            # 流程入参整体（MANUAL paramType=NONE 时不存在）
            _need(resolver, scope, alias, where)
            return NodeField(resolver.input_ref() if resolver else
                             {"outputName": alias, "title": alias, "field": ""},
                             dtype=spec.get("dtype") or "STRING")
        _need(resolver, scope, alias, where)
        return _node_ref(alias, spec, resolver, refs, where)
    if "field" in spec:
        # "ds.jdbcUrl" 或 "ds" （整节点）
        path = str(spec["field"])
        if "." not in path:
            _need(resolver, scope, path, where)
            return _node_ref(path, spec, resolver, refs, where)
        alias, fname = path.split(".", 1)
        _need(resolver, scope, alias, where)
        return _field_ref(alias, fname, spec, resolver, refs, where)
    if "input" in spec:
        _need(resolver, scope, "$input", where)
        return _input_ref(spec, resolver, refs, where)

    # ---- 复合 ----
    if "op" in spec:
        op = _norm_op(spec["op"], _CMP, "compare")
        left = _parse(spec.get("left"), resolver=resolver, scope=scope, refs=refs, loops=loops,
                      where=where + ".left")
        right = _parse(spec.get("right"), resolver=resolver, scope=scope, refs=refs, loops=loops,
                       where=where + ".right")
        return Compare(op, left, right)

    if "logic" in spec:
        op = _norm_op(spec["logic"], _LOGIC, "logic")
        items = spec.get("items")
        if not isinstance(items, list) or not items:
            raise DslError("%s.logic 需要至少一个 item" % where)
        # ★ 单元素 AND/OR 等价于该元素本身（AND 一个条件 = 那个条件）。
        #   需求编译器与逻辑图天然会产出 {logic:AND, items:[单条]}，
        #   这里直接解包，不要报错逼调用方删掉 logic 键。
        if len(items) == 1:
            return _parse(items[0], resolver=resolver, scope=scope, refs=refs,
                          loops=loops, where="%s.items[0]" % where)
        return Logic(op, [_parse(x, resolver=resolver, scope=scope, refs=refs, loops=loops,
                                 where="%s.items[%d]" % (where, i))
                          for i, x in enumerate(items)])

    if "arith" in spec:
        op = _norm_op(spec["arith"], _ARITH, "arith")
        items = spec.get("items")
        if not isinstance(items, list) or len(items) < 2:
            raise DslError("%s.arith 需要至少两个 items" % where)
        return Arithmetic(op, [_parse(x, resolver=resolver, scope=scope, refs=refs, loops=loops,
                                      where="%s.items[%d]" % (where, i))
                               for i, x in enumerate(items)])

    if "fn" in spec:
        name = spec["fn"]
        groups = spec.get("args") or []
        if not isinstance(groups, list):
            raise DslError("%s.args 必须是参数组数组 [[...]]" % where)
        # ★ 平台按 paramCount 校验「参数个数」，不是「组内表达式个数」。
        #   containsText(参数, 被包含文本) → paramCount=2 → 必须两个组：
        #   [[{...a}], [{...b}]]，写成 [[a, b]] 会报 FORMULA_6049
        #   "parameter number does not match, please check parameter Settings!"。
        try:
            from ..udc.microflow.expression_fill import FUNCTION_CATALOG
            meta = FUNCTION_CATALOG.get(name)
        except Exception:
            meta = None
        if meta and meta.get("paramCount") is not None:
            if len(groups) != int(meta["paramCount"]):
                raise DslError("%s 函数 %r 需要 %d 个参数组（args 形如 "
                               "[[a],[b]]），实际 %d 组"
                               % (where, name, int(meta["paramCount"]), len(groups)))
        arg_groups = []
        for gi, g in enumerate(groups):
            if not isinstance(g, list):
                raise DslError("%s.args[%d] 必须是数组（参数组=表达式列表）" % (where, gi))
            arg_groups.append([_parse(x, resolver=resolver, scope=scope, refs=refs, loops=loops,
                                      where="%s.args[%d][%d]" % (where, gi, xi))
                               for xi, x in enumerate(g)])
        # ★ 函数目录没有返回类型字段（function_catalog.json 只有
        #   desc/category/paramCount/argDescs），默认 STRING 是诚实的。
        #   但判定性函数（containsText/isNull…）当条件用时必须推成 BOOLEAN，
        #   否则 Logic 会报「子项应为 BOOLEAN」，错误信息看不出是本处问题。
        dtype = spec.get("dtype") or _BOOL_FUNCS.get(name, "STRING")
        return Func(name, arg_groups, dtype=dtype)

    if "cond" in spec:
        return Cond(_parse(spec["cond"], resolver=resolver, scope=scope, refs=refs, loops=loops,
                           where=where + ".cond"),
                    _parse(spec.get("then"), resolver=resolver, scope=scope, refs=refs, loops=loops,
                           where=where + ".then"),
                    _parse(spec.get("else"), resolver=resolver, scope=scope, refs=refs, loops=loops,
                           where=where + ".else"))

    raise DslError("%s 无法识别：%r（支持的键：const/sys/ref/field/input/"
                   "op/logic/arith/fn/cond）" % (where, list(spec)[:6]))


# ---------------------------------------------------------------- 引用构造
def _loop_item_ref(spec, resolver, refs, loops, where):
    """循环项引用 → NodeField。

    ★ 平台形态（37 条真实样本一致）：循环项就是 FOR_EACH 节点的出参
      `_FOR_EACH_xxx`，`position=parent`，nodeInfo.type=FOR_EACH。
      不存在独立的「循环变量」对象，作用域 = 该节点及其后代。
    """
    alias, field = parse_loop_item_ref(spec)
    if loops is None or len(loops) == 0:
        raise DslError("%s 引用了循环项 %r，但当前不在任何循环体内"
                       "（循环项只能在它自己的 body 里用）" % (where, alias))
    try:
        frame = loops.require(alias)
    except ScopeError as e:
        raise DslError("%s %s" % (where, e)) from e

    if field:
        try:
            fm = frame.field_meta(field)
        except ScopeError as e:
            raise DslError("%s %s" % (where, e)) from e
        ref = {
            "outputName": frame.output_name, "field": field,
            "title": frame.caption or alias, "dto_id": frame.elem_dto,
            "is_array": False, "position": "parent",
            "fields": {field: fm},
        }
        refs.append(ref)
        return NodeField(ref, dtype=fm.get("dataType") or "STRING")

    # 整项引用（元素本身）
    ref = {"outputName": frame.output_name, "field": frame.output_name,
           "title": frame.caption or alias, "dto_id": frame.elem_dto,
           "is_array": False, "position": "parent", "fields": {}}
    refs.append(ref)
    return NodeField(ref, dtype=frame.elem_type)


def _node_ref(alias, spec, resolver, refs, where):
    """整节点输出（基本类型节点，如 CREATE_VARIABLE result）。"""
    if resolver is None:
        return NodeField({"outputName": alias, "title": alias, "field": alias},
                         dtype=spec.get("dtype") or "STRING")
    node = resolver.find_executed(alias)
    if node is None:
        raise DslError("%s 引用的节点 %r 不存在" % (where, alias))
    out = node.get("output") or {}
    dt = out.get("dataType") or spec.get("dtype") or "STRING"
    # 整节点引用：field 用节点自身出参名（BASIC 变量的值槽就是它自己）
    ref = {"outputName": out.get("name") or alias,
           "title": node.get("title") or alias,
           "field": out.get("name") or alias,
           "dto_id": out.get("id") or "",
           # ★ node_action：节点动作类型，供 _scalar_value_slot 区分「LIST_OPERATION
           #   标量出参（走表达式）」vs「CREATE_ENTITY 等写操作的 id 出参（走 SelectParam）」。
           "node_action": node.get("actionType") or "",
           # ★ node_dtype：标量类型（BIGINTEGER/INTEGER/...）或 DTO。
           #   register_node_output 靠它区分「两级标量 context」vs「三级 DTO 树」。
           "node_dtype": dt,
           "fields": {}}
    refs.append(ref)
    return NodeField(ref, dtype=dt)


def _field_ref(alias, fname, spec, resolver, refs, where):
    if resolver is None:
        ref = {"outputName": alias, "title": alias, "field": fname}
        refs.append(ref)
        return NodeField(ref, dtype=spec.get("dtype") or "STRING")
    node = resolver.find_executed(alias)
    if node is None:
        raise DslError("%s 引用的节点 %r 不存在" % (where, alias))
    nf = resolver.field_ref_from_node(node, fname)
    # ★ 必须把引用收集进 _refs：编译器靠它注册 context 三级树。
    #   漏了会生成「tokens 有 VARIABLE、context 没这个出参」的表达式，
    #   平台 check 直接报变量不存在（FORMULA_6058）。
    if getattr(nf, "ref", None):
        refs.append(nf.ref)
    return nf


def _input_ref(spec, resolver, refs, where):
    if resolver is None:
        ref = {"outputName": "$input", "title": "入参",
               "field": spec.get("input") or ""}
        refs.append(ref)
        return NodeField(ref, dtype=spec.get("dtype") or "STRING")
    nf = resolver.input_ref(spec.get("input"), dtype=spec.get("dtype"))
    if getattr(nf, "ref", None):
        refs.append(nf.ref)
    return nf


def _guess_type(v: Any, explicit: str | None) -> str:
    if explicit:
        return explicit.upper()
    if isinstance(v, bool):
        return "BOOLEAN"
    if isinstance(v, int):
        return "INTEGER"
    if isinstance(v, float):
        return "DECIMAL"
    return "STRING"
