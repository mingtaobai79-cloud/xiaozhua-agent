"""P2-2 表达式中间模型（统一 AST）。

★ 定位：业务逻辑图/构造器只许造 AST，不许各自拼 tokens/context JSON。
序列化统一走 ExpressionCompiler → tokens+context → expression_api 远端链
（/expression/check → /expression/transform → designData+runtimeData）。

节点种类（对应语料与 88 函数目录）：
  Const(v, dtype)                 常量（字符串/数字/布尔/日期）
  NodeField(node, field, dtype)   前序节点出参字段引用（三级 VARIABLE token）
  SysVar(name, dtype)             系统变量（131 项，走全名保类型稳定）
  Compare(op, left, right)        比较（EQ/NE/GT/GE/LT/LE）
  Logic(op, *items)               AND / OR
  Arithmetic(op, *items)          + - * /
  Func(name, *args)               88 函数目录内的函数调用
  Cond(cond, then, else_)         条件取值（IF 函数语义）

每个 AST 节点声明 .dtype（期望结果类型），编译器据此做静态类型检查；
引用节点（NodeField/SysVar）由调用方注入元数据（P2-3 解析器负责提供）。
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any

JAVA = {
    "STRING": "java.lang.String", "INTEGER": "java.lang.Integer",
    "BIGINTEGER": "java.lang.Long", "BOOLEAN": "java.lang.Boolean",
    "DECIMAL": "java.math.BigDecimal", "DOUBLE": "java.lang.Double",
    "DATETIME": "java.util.Date", "DATE": "java.util.Date",
}

# ★ 相等必须是 `==` 不是 `=`：1040 条真实表达式里 OPERATOR '==' 出现 325 次，
#   而 '=' 只作为 desc 出现、从不当 value。写成 '=' 平台回 BOOT_3000（无 message）。
COMPARE_OPS = {"EQ": "==", "NE": "!=", "GT": ">", "GE": ">=", "LT": "<", "LE": "<="}
# OPERATOR token 的 desc（语料 802 个 OPERATOR 全有 desc）
COMPARE_DESC = {"EQ": "=", "NE": "!=", "GT": ">", "GE": ">=", "LT": "<", "LE": "<="}
LOGIC_DESC = {"AND": "and", "OR": "or"}
# ★ 逻辑运算符必须是**单字符** & 和 |：
#   1040 条真实表达式的 OPERATOR 只有 '&' 和 '|'，从无 '&&'/'||'。
#   写成 '&&' 平台 checkSchema 回 BOOT_3000（无 message），极难定位。
LOGIC_OPS = {"AND": "&", "OR": "|"}
ARITH_OPS = {"ADD": "+", "SUB": "-", "MUL": "*", "DIV": "/"}


class ExpressionError(ValueError):
    """表达式模型静态错误（类型不匹配/非法引用等）。"""


# ---------------------------------------------------------------------------
# AST 节点
# ---------------------------------------------------------------------------

class Expr:
    """表达式节点基类。dtype=期望结果类型。"""
    dtype: str = "STRING"

    def children(self) -> list["Expr"]:
        return []


@dataclass
class Const(Expr):
    value: Any
    dtype: str = "STRING"


@dataclass
class NodeField(Expr):
    """前序节点出参字段引用。ref 是引用解析器（P2-3）给的描述：
    {outputName, title, field, field_desc, node_dtype, field_dtype}"""
    ref: dict
    dtype: str = "STRING"

    @property
    def output_name(self) -> str:
        return self.ref["outputName"]


@dataclass
class SysVar(Expr):
    """系统变量（全名，如 currentTime；全名/短名解析通路不等价，强制全名）。"""
    name: str
    dtype: str = "STRING"


@dataclass
class Compare(Expr):
    op: str          # EQ/NE/GT/GE/LT/LE
    left: Expr
    right: Expr
    dtype: str = "BOOLEAN"

    def children(self):
        return [self.left, self.right]


class Logic(Expr):
    """AND / OR。Logic("AND", a, b, ...) 变参写法。"""
    def __init__(self, op: str, *items, dtype: str = "BOOLEAN"):
        if len(items) == 1 and isinstance(items[0], (list, tuple)):
            items = tuple(items[0])
        self.op, self.items, self.dtype = op, list(items), dtype

    def children(self):
        return list(self.items)


class Arithmetic(Expr):
    """+ - * /。Arithmetic("ADD", a, b, ...) 变参写法。"""
    def __init__(self, op: str, *items, dtype: str = "INTEGER"):
        if len(items) == 1 and isinstance(items[0], (list, tuple)):
            items = tuple(items[0])
        self.op, self.items, self.dtype = op, list(items), dtype

    def children(self):
        return list(self.items)


@dataclass
class Func(Expr):
    """88 函数目录内函数。arg_groups 是参数组（每组 list[Expr]，多参组=列表参数）。"""
    name: str
    arg_groups: list
    dtype: str = "STRING"

    def children(self):
        return [x for g in self.arg_groups for x in g]


@dataclass
class Cond(Expr):
    """条件取值 IF(cond, then, else_)。"""
    cond: Expr
    then: Expr
    else_: Expr

    def children(self):
        return [self.cond, self.then, self.else_]


# ---------------------------------------------------------------------------
# 静态类型检查
# ---------------------------------------------------------------------------

NUMERIC = {"INTEGER", "BIGINTEGER", "DECIMAL", "DOUBLE"}


def check_types(e: Expr) -> list[str]:
    """静态类型检查，返回问题清单（空=通过）。只查结构约束，引用类型由 P2-3 保证。"""
    problems: list[str] = []

    def go(x: Expr):
        if isinstance(x, Compare):
            go(x.left); go(x.right)
            if x.op not in COMPARE_OPS:
                problems.append("非法比较 op=%r" % x.op)
            lt, rt = x.left.dtype, x.right.dtype
            if lt and rt and lt != rt and not (lt in NUMERIC and rt in NUMERIC):
                # 日期/时间等异族不匹配直接报
                problems.append("比较两侧类型不一致 %s(%s) vs %s(%s)"
                                % (type(x.left).__name__, lt, type(x.right).__name__, rt))
        elif isinstance(x, Logic):
            if x.op not in LOGIC_OPS:
                problems.append("非法逻辑 op=%r" % x.op)
            if not x.items:
                problems.append("Logic 至少 1 项")
            for i in x.items:
                go(i)
                if i.dtype != "BOOLEAN":
                    problems.append("Logic 子项应为 BOOLEAN，得到 %s(%s)"
                                    % (type(i).__name__, i.dtype))
        elif isinstance(x, Arithmetic):
            if x.op not in ARITH_OPS:
                problems.append("非法算术 op=%r" % x.op)
            if not x.items:
                problems.append("Arithmetic 至少 1 项")
            for i in x.items:
                go(i)
                if i.dtype and i.dtype not in NUMERIC:
                    problems.append("Arithmetic 子项应为数值，得到 %s(%s)"
                                    % (type(i).__name__, i.dtype))
        elif isinstance(x, Cond):
            go(x.cond)
            if x.cond.dtype != "BOOLEAN":
                problems.append("Cond 条件应为 BOOLEAN，得到 %s" % x.cond.dtype)
            go(x.then); go(x.else_)
            if x.then.dtype != x.else_.dtype:
                problems.append("Cond 两支类型不一致 %s vs %s"
                                % (x.then.dtype, x.else_.dtype))
        elif isinstance(x, Func):
            for g in x.arg_groups:
                for i in (g if isinstance(g, list) else [g]):
                    go(i)
        elif isinstance(x, (Const, NodeField, SysVar)):
            pass

    go(e)
    return problems


# ---------------------------------------------------------------------------
# 编译器：AST → tokens + context
# ---------------------------------------------------------------------------

class ExpressionCompiler:
    """AST → designData。context 树由引用解析器提供的 registry 累积：
    每次 NodeField 编译时把宿主节点出参树注册进 context（三级嵌套）。"""

    def __init__(self, result_type: str = "BOOLEAN"):
        self.result_type = result_type
        self.context: list[dict] = []          # 顶层：宿主节点出参树列表
        self._registered: set[str] = set()     # 已注册的 outputName
        self._context_attrs: dict[str, dict] = {}   # outputName → 已合并的字段元数据

    # ---- context 注册（P2-3 解析器调用）----
    def register_node_output(self, ref: dict, entity_model: dict | None = None):
        """注册前序节点出参到 context。

        ★ 复用 expression_build.node_context_entry（真实活体样本照抄的唯一实现），
        本模块不再自己拼 context 层级 —— 早期自拼版本把字段 type 写成 DTO，
        平台直接回 FORMULA_6033 "Context property: xxx Unsupported data type: DTO"。

        ref = {outputName, title, dto_id, is_array?, fields:{fname:{dataType,id,caption|desc}}}
        """
        from .expression_build import node_context_entry
        name = ref["outputName"]
        attrs = {}
        for fname, fm in (ref.get("fields") or {}).items():
            attrs[fname] = {"dataType": fm.get("dataType") or "STRING",
                            "id": fm.get("id") or fname,
                            "caption": fm.get("caption") or fm.get("desc") or fname}

        # ★ 同一节点可能被引用多次、每次只带一个字段（`X.name` 和 `X.driverClassName`
        #   是两次 register_node_output 调用）。早期实现见名即 return，导致 context 里
        #   只留第一个字段，第二个字段在 context 中不存在 →
        #   checkSchema 回 BOOT_3000（无 message），而 token/translation 看起来全对。
        #   正确做法：合并字段后重建该项。
        if name in self._registered:
            for i, item in enumerate(self.context):
                if item.get("name") != name:
                    continue
                # 结构：context[i].properties[0].properties = 字段列表
                holder = (item.get("properties") or [{}])[0]
                have = {p.get("name") for p in (holder.get("properties") or [])}
                if set(attrs) <= have:
                    return                      # 字段已齐，无需重建
                merged_attrs = dict(self._context_attrs.get(name) or {})
                merged_attrs.update(attrs)
                self._context_attrs[name] = merged_attrs
                self.context[i] = self._build_context_entry(name, ref, merged_attrs)
                return

        self._context_attrs[name] = attrs
        self.context.append(self._build_context_entry(name, ref, attrs))
        self._registered.add(name)

    def _build_context_entry(self, name: str, ref: dict, attrs: dict) -> dict:
        from .expression_build import node_context_entry, basic_scalar_context_entry
        node_dtype = ref.get("node_dtype")
        # ★ BASIC 标量变量（SUM/SIZE/MIN/MAX/CREATE_VARIABLE 出参）→ 两级 context。
        #   node_dtype 是标量类型（BIGINTEGER/INTEGER/...），不是 "DTO"。
        #   否则（DTO 对象/数组）→ 三级 DTO 树（node_context_entry）。
        if node_dtype and node_dtype != "DTO":
            return basic_scalar_context_entry(name, ref.get("title") or name,
                                              node_dtype)
        dto = ref.get("dto_id") or name
        fake_node = {
            "nodeId": ref.get("nodeId") or name,
            "title": ref.get("title") or "",
            "caption": ref.get("title") or "",
            "output": {"name": name, "id": dto, "dataType": "DTO",
                       "type": "ARRAY" if ref.get("is_array") else "OBJECT"},
            "structure": {"id": dto},
        }
        merged = {"attributes": dict(attrs)}
        return node_context_entry(fake_node, merged)

    # ---- AST → tokens ----
    def _translation(self, e: Expr) -> str:
        """AST → 中文表达式文本（designData.expressionTranslation）。

        语料样例：`不为空(微流程.查询单条数据(1).X [X].字段) && 不为空(...)`。
        这里只求"人能读懂、平台不校验"，格式与语料同族即可。
        """
        def show(e2):
            if isinstance(e2, NodeField):
                f = e2.ref.get("field") or ""
                t = e2.ref.get("title") or e2.output_name
                return "%s.%s" % (t, f)
            if isinstance(e2, Const):
                return _const_str(e2.value)
            if isinstance(e2, SysVar):
                return e2.name
            if isinstance(e2, Compare):
                # ★ translation 里的等号必须和 token 一致用 `==`：
                #   语料 translation 是 `X == 投标报销核销申请`。
                #   写成单个 `=` 时 token 是 `==` 而 translation 是 `=`，
                #   平台 checkSchema 回 BOOT_3000（无 message）。
                sym = {"EQ": "==", "NE": "!=", "GT": ">", "GE": ">=",
                       "LT": "<", "LE": "<="}[e2.op]
                return "%s %s %s" % (show(e2.left), sym, show(e2.right))
            if isinstance(e2, Logic):
                sym = "&&" if e2.op == "AND" else "||"
                return (" %s " % sym).join("(%s)" % show(x) for x in e2.items)
            if isinstance(e2, Arithmetic):
                sym = {"ADD": "+", "SUB": "-", "MUL": "*", "DIV": "/"}[e2.op]
                return (" %s " % sym).join("(%s)" % show(x) for x in e2.items)
            if isinstance(e2, Func):
                try:
                    from ..udc.microflow.expression_fill import FUNCTION_CATALOG
                    desc = (FUNCTION_CATALOG.get(e2.name) or {}).get("desc") or e2.name
                except Exception:
                    desc = e2.name
                args = ", ".join(", ".join(show(x) for x in g) for g in e2.arg_groups)
                return "%s(%s)" % (desc, args)
            if isinstance(e2, Cond):
                return "IF(%s, %s, %s)" % (show(e2.cond), show(e2.then), show(e2.else_))
            return "?"
        try:
            return show(e)
        except Exception:
            return ""

    def compile(self, e: Expr) -> list[dict]:
        problems = check_types(e)
        if problems:
            raise ExpressionError("; ".join(problems))
        return self._go(e)

    # 结合律成立的运算符：同 op 嵌套不需要括号
    _ASSOCIATIVE = frozenset({"AND", "OR", "ADD", "MUL"})

    def _grouped(self, parent: Expr, child: Expr, index: int = 0) -> list[dict]:
        """复合子项按需加显式括号。

        ★ 平台 transform 只做 token 平铺翻译，不还原 AST 结构：
        `Logic("AND", A, Logic("OR", B, C))` 不带括号被翻译成
        `A && B || C`（= (A&&B)||C），语义静默漂移。
        实测 2026-11-01：OPERATOR "(" / ")" 平台接受且翻译保留括号。

        规则：
          - 子项是复合表达式且 op 不同 → 括号
          - op 相同但**不满足结合律**（SUB/DIV）且不是首项 → 括号
            （`a - (b - c)` ≠ `a - b - c`；左结合陷阱）
        """
        toks = self._go(child)
        if not isinstance(child, (Logic, Arithmetic)):
            return toks
        same = child.op == getattr(parent, "op", None)
        need = (not same) or (same and child.op not in self._ASSOCIATIVE and index > 0)
        if need:
            return ([_op("(", "(")] + toks
                    + [_op(")", ")")])
        return toks

    def _go(self, e: Expr) -> list[dict]:
        if isinstance(e, Const):
            return [{"uid": str(__import__("uuid").uuid4()), "type": "CONSTANT",
                     "value": _const_str(e.value),
                     "desc": _const_str(e.value)}]
        if isinstance(e, NodeField):
            self.register_node_output(e.ref)
            f = e.ref.get("field")
            if not f:
                keys = list((e.ref.get("fields") or {}).keys())
                if len(keys) != 1:
                    raise ExpressionError("NodeField.ref 缺 field（fields=%s）" % (keys,))
                f = keys[0]
            n = e.output_name
            # ★★ BASIC 变量整节点引用是**两级** `X.X`，不是三级 `X.X.X`。
            #   语料裁决（319 个 BASIC 变量引用 token）：292 个两级、27 个三级，
            #   三级那批是真的字段引用（X.X.<字段>）。
            #   BASIC 变量的值槽就是它自己，没有第三层字段，写成三级平台回
            #   FORMULA_6058 「CVariable :xxx does not exist in context」。
            #   判据：field == outputName（_node_ref 对 BASIC 就是这样填的）。
            if f == n:
                return [{"uid": str(__import__("uuid").uuid4()), "type": "VARIABLE",
                         "value": "%s.%s" % (n, n),
                         "desc": "%s.%s" % (e.ref.get("title") or n,
                                            e.ref.get("field_desc") or f)}]
            return [{"uid": str(__import__("uuid").uuid4()), "type": "VARIABLE",
                     "value": "%s.%s.%s" % (n, n, f),        # 三级：真实字段引用
                     "desc": "%s.%s" % (e.ref.get("title") or n, f)}]
        if isinstance(e, SysVar):
            return [{"uid": str(__import__("uuid").uuid4()), "type": "VARIABLE",
                     "value": e.name, "desc": e.name}]
        if isinstance(e, Compare):
            return (self._go(e.left)
                    + [_op(COMPARE_OPS[e.op], COMPARE_DESC[e.op])]
                    + self._go(e.right))
        if isinstance(e, Logic):
            out: list[dict] = []
            for i, item in enumerate(e.items):
                if i:
                    out.append(_op(LOGIC_OPS[e.op], LOGIC_DESC[e.op]))
                out.extend(self._grouped(e, item, i))
            return out
        if isinstance(e, Arithmetic):
            out = []
            for i, item in enumerate(e.items):
                if i:
                    out.append(_op(ARITH_OPS[e.op], ARITH_OPS[e.op]))
                out.extend(self._grouped(e, item, i))
            return out
        if isinstance(e, Func):
            # ★ 真实形态：FUNCTION token 只有自己一个，参数在 subOps 二维数组里
            #   （[[子token序列], ...]）。平铺成顶层流会让平台回 BOOT_3000。
            from .expression_fill import FUNCTION_CATALOG
            if e.name not in FUNCTION_CATALOG:
                raise ExpressionError("未知函数 %r（不在 88 函数目录 "
                                      "core/facts/udc/expression/functions.md）" % e.name)
            meta = FUNCTION_CATALOG.get(e.name) or {}
            groups = []
            for g in e.arg_groups:
                stream: list[dict] = []
                for x in (g if isinstance(g, list) else [g]):
                    stream.extend(self._go(x))
                groups.append(stream)
            return [{"uid": str(__import__("uuid").uuid4()), "type": "FUNCTION",
                     "value": e.name,
                     "desc": meta.get("desc") or e.name, "subOps": groups}]
        if isinstance(e, Cond):
            return (self._go(e.cond)
                    + [{"type": "OPERATOR", "value": "?"}]
                    + self._go(e.then)
                    + [{"type": "OPERATOR", "value": ":"}]
                    + self._go(e.else_))
        raise ExpressionError("未知 AST 节点 %r" % type(e).__name__)

    # ---- 远端链：AST → check → transform → 可直接落库的 expression 对象 ----
    def to_save_dto(self, e: Expr) -> dict:
        """AST → ExpressionSaveDto（schemas 白名单 + skip 标记）。"""
        from .expression_api import context_to_schemas
        toks = self.compile(e)
        return {
            "resultTypeInfo": self.result_type,
            "schemas": context_to_schemas(self.context),
            "tokens": [{k: t[k] for k in t} for t in toks],
            "isMultiSelect": bool(getattr(e, "multi_select", False)),
            "terminalSupportType": "BACKEND",
        }

    def build_remote(self, e: Expr, backend, title: str = "") -> dict:
        """走 /expression/check → /expression/transform，返回落库用 expression 对象
        {title, schema}（schema 是 JSON 字符串，含 designData+runtimeData）。
        backend：CurlBackend（默认，直发）或 PageBackend（页面内 fetch）。
        任一步失败抛 ExpressionError，绝不降级手拼 executableExpr。"""
        import json as _json
        dto = self.to_save_dto(e)
        # ★ 2026-11-01 结论反转（P5 实测推翻了 P4 的判断）：
        #   含 VARIABLE 的表达式，/expression/check 与 /expression/transform
        #   **完全可用**。证据：从设计器抓到的真实请求体（5 字段：
        #   resultTypeInfo/schemas/tokens/isMultiSelect/terminalSupportType）
        #   原样离线重放 → BOOT_0000，且返回的 executableExpr 与设计器生成的
        #   **逐字节一致**（见 core/facts/udc/microflow/expression-engine.md §十五）。
        #   P4 时期之所以报 FORMULA_6058，是当时 DTO 的 schemas/context 结构不对，
        #   不是接口不支持含 VARIABLE 的表达式。
        #   → 因此这里不再走「本地 designData + 占位 executableExpr」的降级路径。
        chk = backend.check(dto)
        if not chk.get("ok"):
            raise ExpressionError("expression/check 失败: code=%s content=%r msg=%s"
                                  % (chk.get("code"), chk.get("content"),
                                     chk.get("message")))
        tr = backend.transform(dto)
        if not tr.get("ok"):
            raise ExpressionError("expression/transform 失败: code=%s msg=%s"
                                  % (tr.get("code"), tr.get("message")))
        content = tr.get("content") or {}
        schema_obj = {"designData": content.get("designData"),
                      "runtimeData": content.get("runtimeData")}
        return {"title": title or _expr_title(self.context, e),
                "schema": _json.dumps(schema_obj, ensure_ascii=False)}


# 含字段引用的表达式：占位 executableExpr（平台不校验内容，但运行期必须有真值，
# 由设计器「确定」时重算）。放在节点上由调用方读取。
PLACEHOLDER_EXEC = "__NEEDS_UI_FINALIZE__"


def _build_local_design_data(comp_self, e: Expr) -> dict:
    """本地构造 designData（不含 executableExpr）。

    与远端 transform 产物的键集一致（语料 1040 条）：
      expressionTranslation / resultTypeInfo / resultTypeFullName /
      terminalType / isMultiSelect / context / tokens / sourceAppName
    """
    tokens = comp_self.compile(e)
    tr = comp_self._translation(e)
    return {
        "expressionTranslation": tr,
        "resultTypeInfo": comp_self.result_type,
        "resultTypeFullName": None,
        "terminalType": "BACKEND",
        "isMultiSelect": False,
        "context": comp_self.context,
        "tokens": tokens,
        "sourceAppName": None,
    }


def _dto_has_variable(dto: dict) -> bool:
    """save dto 的 tokens 里是否有 VARIABLE。"""
    def walk(ts):
        for t in ts or []:
            if not isinstance(t, dict):
                continue
            if t.get("type") == "VARIABLE":
                return True
            for grp in (t.get("subOps") or []):
                if isinstance(grp, list) and walk(grp):
                    return True
        return False
    toks = dto.get("tokens") or []
    for x in toks:
        if isinstance(x, list):
            if walk(x):
                return True
        elif walk([x]):
            return True
    return False


def _op(value: str, desc: str = "") -> dict:
    """OPERATOR token。★ 真实 802 个 OPERATOR 都有 uid + desc，缺了平台不认。"""
    import uuid as _uuid
    return {"uid": str(_uuid.uuid4()), "type": "OPERATOR",
            "value": value, "desc": desc or value}


def _const_str(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def json_ext(d: dict) -> str:
    import json as _json
    return _json.dumps(d, separators=(",", ":"), ensure_ascii=False)


def flatten_func_args(arg_groups: list) -> list[dict]:
    """函数参数组 → token 流（逗号分组）。与 expression_build.func_token 的
    真实样本形态一致：逗号在组间，组内参数直接平铺。"""
    out: list[dict] = []
    for gi, g in enumerate(arg_groups):
        if gi:
            out.append({"type": "OPERATOR", "value": ","})
        for t in g:
            out.extend(t if isinstance(t, list) else [t])
    return out


def _expr_title(context: list, e: Expr) -> str:
    """表达式标题（前端展示用）：微流程.<引用>.±<末尾>"""
    roots = [c.get("name") for c in (context or []) if c.get("name")]
    return "微流程.%s" % (".".join(roots) if roots else "表达式")


def to_save_dto(e: Expr, result_type: str = "BOOLEAN") -> dict:
    """便捷入口：单表达式 → ExpressionSaveDto（无引用时 context 为空）。"""
    return ExpressionCompiler(result_type=result_type).to_save_dto(e)


def to_value_slot(expr_obj: dict, desc: str | None = None) -> dict:
    """表达式对象 {title, schema} → 平台值槽包装（语料 1073 条裁决）。

    真实形态：
        {"type":"Expression","simple":null,"desc":"...",
         "expression":{"title":...,"schema":"<JSON字符串>"}}

    ★ 直接把手拼/编译出的 {title, schema} 塞进 value/forEnd 等槽位，
    平台 checkSchema 报 `value.type PROPERTY_IS_REQUIRED`（缺 type 键）
    再报 `DATA_INVALID` —— 槽位必须带 type 判别键。
    """
    if not isinstance(expr_obj, dict):
        raise ExpressionError("to_value_slot 需要 {title, schema} 对象，得到 %r"
                              % type(expr_obj))
    if expr_obj.get("type") == "Expression":
        return expr_obj                       # 已包装，幂等（先判 type 再判 schema）
    if "schema" not in expr_obj:
        raise ExpressionError("to_value_slot 需要 {title, schema} 对象，得到 %r"
                              % (list(expr_obj)[:5],))
    return {"type": "Expression", "simple": None,
            "desc": desc if desc is not None else (expr_obj.get("title") or ""),
            "expression": {"title": expr_obj.get("title") or "",
                           "schema": expr_obj["schema"]}}
