# -*- coding: utf-8 -*-
"""FILTER 的过滤条件表达式：离线构造 + 平台编译。

为什么能离线做（2026-11-03 实测）：
  把语料里一条带「过滤条件」字段引用的 FILTER 表达式原样重放给
  /expression/check + /transform → BOOT_0000，返回的 executableExpr 与
  设计器产出的**逐字节一致**。
  → FILTER 不需要进设计器点「确定」，只要 context 里带上「过滤条件」根。

context 结构（真实样本校准）：

    根  name=<DTO 去点>  description=过滤条件  type=OBJECT  selectable=false
      └ 子  name=<DTO 去点>  description=<列表名>  type=OBJECT  selectable=true
           └ 字段  name=<字段名>  description=<中文名>  type=<STRING|INTEGER...>

token 里的变量路径是 `<DTO去点>.<DTO去点>.<字段名>`（DTO 名重复两次）。
"""

import json
import uuid

from components.udc.microflow.expression_api import context_to_schemas

OP_TOKEN = {
    # 业务操作 → (token type, platform value, 标题里的中文)
    "EQ": ("OPERATOR", "==", "="),
    "NE": ("OPERATOR", "!=", "<>"),
    "GT": ("OPERATOR", ">", ">"),
    "GE": ("OPERATOR", ">=", ">="),
    "LT": ("OPERATOR", "<", "<"),
    "LE": ("OPERATOR", "<=", "<="),
    "CONTAINS": ("FUNCTION", "containsText", "文本包含"),
    "NOT_EMPTY": ("FUNCTION", "isNotNull", "不为空"),
}


def _uniform(param_id, category, extra=None):
    ext = {"id": param_id}
    if extra:
        ext.update(extra)
    return {"paramId": param_id, "paramCategory": category,
            "extensionProperties": json.dumps(ext, ensure_ascii=False),
            "pageNodeExtension": None}


def _field_node(attr: dict, dto_full: str) -> dict:
    name = attr.get("name")
    return {"name": name,
            "description": attr.get("label") or attr.get("description") or name,
            "type": attr.get("dataType") or "STRING",
            "selectable": True, "enableDataI18n": False,
            "uniformityParams": _uniform(dto_full + "." + name,
                                         attr.get("dataType") or "STRING",
                                         {"relationType": "NONE", "relationEntity": ""})}


def build_context(dto_full: str, list_desc: str, entity_model: dict,
                  only_fields=None) -> list:
    """构造含「过滤条件」根的 context。"""
    nodots = dto_full.replace(".", "")
    attrs = entity_model.get("attributes") or {}
    props = []
    for name, a in attrs.items():
        if only_fields and name not in only_fields:
            continue
        props.append(_field_node(a, dto_full))
    root = {"name": nodots, "description": "过滤条件", "type": "OBJECT",
            "selectable": False, "enableDataI18n": False,
            "uniformityParams": _uniform(dto_full, "DTO", {"javaType": dto_full}),
            "properties": [{
                "name": nodots, "description": list_desc, "type": "OBJECT",
                "selectable": True, "enableDataI18n": False,
                "uniformityParams": _uniform(dto_full, "OBJECT"),
                "properties": props}]}
    return [root]


def build_tokens(dto_full: str, list_desc: str, field: str, field_desc: str,
                 op: str, const=None, const_desc=None) -> list:
    """★ 真实形态（语料实测）：
      OPERATOR 是**平铺**的三个 token [VARIABLE, OPERATOR, CONSTANT]，不带 subOps；
      只有 FUNCTION（文本包含/不为空）才用 subOps 包参数。
      早先按「所有 token 都带 subOps」构造 → FORMULA_6070 Operator: =, input error!
    """
    kind, value, cn = OP_TOKEN.get((op or "").upper(), ("OPERATOR", op, op))
    nodots = dto_full.replace(".", "")
    var = {"uid": str(uuid.uuid4()), "type": "VARIABLE",
           "value": "%s.%s.%s" % (nodots, nodots, field),
           "desc": "微流程.过滤条件.%s.%s" % (list_desc, field_desc)}
    op_tok = {"uid": str(uuid.uuid4()), "type": kind, "value": value, "desc": cn}
    if kind == "OPERATOR":
        toks = [var, op_tok]
        if const is not None:
            toks.append({"uid": str(uuid.uuid4()), "type": "CONSTANT",
                         "value": str(const),
                         "desc": const_desc if const_desc is not None else str(const)})
        return toks
    # FUNCTION：参数放 subOps
    sub = [[var]]
    if const is not None:
        sub.append([{"uid": str(uuid.uuid4()), "type": "CONSTANT",
                     "value": str(const),
                     "desc": const_desc if const_desc is not None else str(const)}])
    op_tok["subOps"] = sub
    return [op_tok]


def title_of(list_desc: str, field_desc: str, op: str, const) -> str:
    """与平台表达式标题同构：等于(微流程.过滤条件.列表.字段,值)。"""
    kind, _v, cn = OP_TOKEN.get((op or "").upper(), ("OPERATOR", op, op))
    if kind == "FUNCTION" and const is None:
        return "%s(微流程.过滤条件.%s.%s)" % (cn, list_desc, field_desc)
    return "%s(微流程.过滤条件.%s.%s,%s)" % (cn, list_desc, field_desc, const)


def build_filter_expression(*, dto_full: str, list_desc: str, entity_model: dict,
                            field: str, op: str, const=None,
                            backend=None) -> dict:
    """返回平台落库形态 {"title", "schema"}（schema 是含 designData/runtimeData 的 JSON 串）。"""
    if backend is None:
        raise ValueError("build_filter_expression 需要 backend（expression/check+transform）")
    attrs = entity_model.get("attributes") or {}
    if field not in attrs:
        raise KeyError("实体没有字段 %r（可用：%s）" % (field, sorted(attrs)))
    fdesc = attrs[field].get("label") or attrs[field].get("description") or field
    dto = {"resultTypeInfo": "BOOLEAN",
           "schemas": context_to_schemas(build_context(dto_full, list_desc, entity_model)),
           "tokens": build_tokens(dto_full, list_desc, field, fdesc, op, const),
           "isMultiSelect": False,
           "terminalSupportType": "BACKEND"}
    chk = backend.check(dto)
    if not chk.get("ok"):
        raise RuntimeError("过滤条件 expression/check 失败: code=%s msg=%s"
                           % (chk.get("code"), (chk.get("message") or "")[:200]))
    tr = backend.transform(dto)
    if not tr.get("ok"):
        raise RuntimeError("过滤条件 expression/transform 失败: code=%s msg=%s"
                           % (tr.get("code"), (tr.get("message") or "")[:200]))
    content = tr.get("content") or {}
    return {"title": title_of(list_desc, fdesc, op, const),
            "schema": json.dumps({"designData": content.get("designData"),
                                  "runtimeData": content.get("runtimeData")},
                                 ensure_ascii=False)}


# --------------------------------------------------------------------------
# 任意布尔表达式（AST）→ FILTER 表达式
# --------------------------------------------------------------------------

def field_ref(dto_full: str, field: str, list_desc: str = "列表",
              field_desc: str | None = None) -> dict:
    """构造 FILTER 里引用「过滤条件」字段的 NodeField ref。

    token 路径是 `<DTO去点>.<DTO去点>.<字段>` —— 把 outputName 直接设成
    DTO 去点，ExpressionCompiler 生成的两级重复正好等于平台要求。
    """
    return {"outputName": dto_full.replace(".", ""), "title": list_desc,
            "field": field, "field_desc": field_desc or field,
            "dto_id": dto_full}


def build_ast_expression(*, dto_full: str, list_desc: str, entity_model: dict,
                         ast, backend=None, title: str | None = None) -> dict:
    """把任意布尔 AST（含算术/函数/逻辑组合）编译成 FILTER 的 expression。

    与 build_filter_expression 的区别：那个只支持 `字段 op 常量`，这个支持
    完整 AST，例如 `substring(taskId,1,3) == 'P6E' && processedRows + 3 > 5`。
    """
    if backend is None:
        raise ValueError("build_ast_expression 需要 backend")
    from components.udc.microflow.expression_model import ExpressionCompiler
    attrs = entity_model.get("attributes") or {}
    nodots = dto_full.replace(".", "")
    fields = {}
    for name, a in attrs.items():
        fields[name] = {"dataType": a.get("dataType") or "STRING",
                        "id": dto_full + "." + name,
                        "caption": a.get("label") or a.get("description") or name}
    comp = ExpressionCompiler(result_type="BOOLEAN")
    comp.register_node_output({"outputName": nodots, "title": list_desc,
                               "dto_id": dto_full, "is_array": True,
                               "fields": fields})
    toks = comp.compile(ast)
    # ★ context 必须用 FILTER 专属两级树（过滤条件根），不能用节点出参树，
    #   否则平台回 BOOT_3000（无 message）。token 路径两者恰好同形。
    dto = {"resultTypeInfo": "BOOLEAN",
           "schemas": context_to_schemas(build_context(dto_full, list_desc, entity_model)),
           "tokens": toks, "isMultiSelect": False,
           "terminalSupportType": "BACKEND"}
    chk = backend.check(dto)
    if not chk.get("ok"):
        raise RuntimeError("表达式 expression/check 失败: code=%s msg=%s"
                           % (chk.get("code"), (chk.get("message") or "")[:200]))
    tr = backend.transform(dto)
    if not tr.get("ok"):
        raise RuntimeError("表达式 expression/transform 失败: code=%s msg=%s"
                           % (tr.get("code"), (tr.get("message") or "")[:200]))
    content = tr.get("content") or {}
    return {"title": title or (comp._translation(ast) or "过滤条件"),
            "schema": json.dumps({"designData": content.get("designData"),
                                  "runtimeData": content.get("runtimeData")},
                                 ensure_ascii=False)}


def field_expr(dto_full: str, field: str, dtype: str = "STRING",
               list_desc: str = "列表", field_desc: str | None = None):
    """field_ref 的 AST 版本：直接返回可参与运算的 NodeField。"""
    from components.udc.microflow.expression_model import NodeField
    return NodeField(field_ref(dto_full, field, list_desc, field_desc), dtype=dtype)


def parse_filter_spec(spec, *, dto_full: str, list_desc: str, entity_model: dict,
                      where: str = "expr"):
    """JSON 规格 → AST，字段按**实体字段**解析（FILTER 上下文专用）。

    与 expression_dsl.parse_expr 的区别：那里的 {"field": "x.y"} 指向节点别名，
    这里指向过滤条件列表的字段（同一 DTO），所以不能复用节点引用解析。
    """
    from components.udc.microflow.expression_model import (
        Arithmetic, Compare, Cond, Const, Func, Logic)

    if not isinstance(spec, dict):
        raise ValueError("%s 必须是对象" % where)
    attrs = entity_model.get("attributes") or {}

    if "const" in spec:
        v = spec["const"]
        dt = spec.get("dtype") or ("BOOLEAN" if isinstance(v, bool) else
                                   "INTEGER" if isinstance(v, int) else
                                   "DECIMAL" if isinstance(v, float) else "STRING")
        return Const(v, dt)

    if "field" in spec:
        name = str(spec["field"]).split(".")[-1]
        if name not in attrs:
            raise ValueError("%s 字段 %r 不存在（可用：%s）"
                             % (where, name, sorted(attrs)[:8]))
        return field_expr(dto_full, name,
                          spec.get("dtype") or attrs[name].get("dataType") or "STRING",
                          list_desc, attrs[name].get("label") or name)

    if "op" in spec:
        op = str(spec["op"]).upper()
        if op not in ("EQ", "NE", "GT", "GE", "LT", "LE"):
            raise ValueError("%s 未知比较符 %r" % (where, op))
        left = parse_filter_spec(spec["left"], dto_full=dto_full, list_desc=list_desc,
                                 entity_model=entity_model, where=where + ".left")
        right = parse_filter_spec(spec["right"], dto_full=dto_full, list_desc=list_desc,
                                  entity_model=entity_model, where=where + ".right")
        # ★ 布尔函数不要包 `== true`：实测 containsText(...) == true 恒为 false
        #   （P6EX01 TEXT=0），裸函数条件才对（P6EX03 T3=1）。这里自动解包。
        if (op == "EQ" and getattr(right, "value", None) is True
                and getattr(left, "dtype", "") == "BOOLEAN"):
            return left
        return Compare(op, left, right)

    if "logic" in spec:
        op = str(spec["logic"]).upper()
        if op not in ("AND", "OR"):
            raise ValueError("%s 未知逻辑符 %r" % (where, op))
        items = spec.get("items") or []
        if not items:
            raise ValueError("%s.logic 需要 items" % where)
        return Logic(op, [parse_filter_spec(x, dto_full=dto_full, list_desc=list_desc,
                                           entity_model=entity_model,
                                           where="%s.items[%d]" % (where, i))
                          for i, x in enumerate(items)])

    if "arith" in spec:
        op = str(spec["arith"]).upper()
        if op not in ("ADD", "SUB", "MUL", "DIV"):
            raise ValueError("%s 未知算术符 %r" % (where, op))
        items = spec.get("items") or []
        if len(items) < 2:
            raise ValueError("%s.arith 至少 2 项" % where)
        return Arithmetic(op, [parse_filter_spec(x, dto_full=dto_full, list_desc=list_desc,
                                                 entity_model=entity_model,
                                                 where="%s.items[%d]" % (where, i))
                               for i, x in enumerate(items)],
                          dtype=spec.get("dtype") or "INTEGER")

    if "fn" in spec:
        groups = spec.get("args") or []
        norm = []
        for gi, g in enumerate(groups):
            seq = g if isinstance(g, list) else [g]
            norm.append([parse_filter_spec(x, dto_full=dto_full, list_desc=list_desc,
                                           entity_model=entity_model,
                                           where="%s.args[%d]" % (where, gi))
                         for x in seq])
        return Func(spec["fn"], norm, dtype=spec.get("dtype") or "STRING")

    if "cond" in spec:
        then_e = parse_filter_spec(spec["then"], dto_full=dto_full, list_desc=list_desc,
                                   entity_model=entity_model, where=where + ".then")
        node = Cond(parse_filter_spec(spec["cond"], dto_full=dto_full, list_desc=list_desc,
                                      entity_model=entity_model, where=where + ".cond"),
                    then_e,
                    parse_filter_spec(spec["else"], dto_full=dto_full, list_desc=list_desc,
                                      entity_model=entity_model, where=where + ".else"))
        # ★ Cond 没有 dtype 字段（继承默认 STRING），必须显式补，
        #   否则 IF(...) 被当 STRING，与数字比较时报「类型不一致」。
        node.dtype = spec.get("dtype") or getattr(then_e, "dtype", "STRING")
        return node

    raise ValueError("%s 无法识别：%r（支持 const/field/op/logic/arith/fn/cond）"
                     % (where, list(spec)[:5]))
