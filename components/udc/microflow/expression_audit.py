"""微流程表达式层审计 —— 补齐 find_refs 漏掉 expression 的缺口。

## 为什么要单独成模块

`expression` 是 `{title, schema}` 对象，不是字符串。
早期审计脚本只匹配 `outputName` / `name` 这类字符串字段，
**整个表达式层被静默跳过**，于是给出「全部健康」的假绿结论。

## 三层一致性

    微流程编辑器里同一个表达式存在于三层：
      L1  store.flowNodes[id].expression      前端编辑态（点确定即更新）
      L2  store.oldFlowSchema.flowNodes[id]   加载基线
      L3  后端 dataSchema                     只在「暂存草稿」时更新

    ★ 点「确定」只写 L1。少了「暂存草稿」，L3 永远是旧值。

## 检测能力

    iter_expressions(node)        找出节点内所有 expression 对象
    check_expression(expr, vars)  单条表达式体检
    audit_node_expressions(node, vars)

    check_three_layers(l1, l3)    三层一致性判定

## 已知不可用路径

    POST /expression/schema  paramType=MICROFLOW → BOOT_3000（未注册）
    微流程表达式无法通过 API 生成，只能走 UI 或复制已有正确结构。
"""
from __future__ import annotations

import json
from typing import Any, Iterable

# token 五型（TokenTypeEnum 权威）
TOKEN_TYPES: tuple[str, ...] = (
    "CONSTANT", "VARIABLE", "SYSTEM", "FUNCTION", "OPERATOR",
)

# 布尔常量 true/false 是 OPERATOR 类型（value/desc 都是 "true"/"false"），
# 不是 CONSTANT。这是活体样本归纳的约定，生成/审计都按它判。
BOOLEAN_LITERALS_ARE_OPERATOR = True


def _iter_tokens_recursive(tokens) -> Iterable[dict]:
    """递归遍历 token 树（含 FUNCTION.subOps），产出所有 token。

    ★ 早期只遍历顶层 tokens，导致 FUNCTION 的参数表达式（subOps）里的
    VARIABLE 悬空引用 / token 类型值域全部漏检 —— 这是悬空引用假绿的一个来源。
    subOps 是二维数组：[[子token序列]]（外层参数组，内层 token 序列）。
    """
    for t in tokens or []:
        if not isinstance(t, dict):
            continue
        yield t
        sub = t.get("subOps")
        if isinstance(sub, list):
            for grp in sub:
                if isinstance(grp, list):
                    yield from _iter_tokens_recursive(grp)

# 判定 expression 对象的特征键
EXPR_SIGNATURE_KEYS: tuple[str, ...] = ("title", "schema")


def is_expression(obj: Any) -> bool:
    """expression 是 {title, schema}，schema 内含 designData 或 expressionTranslation。"""
    if not isinstance(obj, dict):
        return False
    if "schema" not in obj:
        return False
    s = obj.get("schema")
    if isinstance(s, str):
        return "designData" in s or "expressionTranslation" in s
    if isinstance(s, dict):
        return "designData" in s or "expressionTranslation" in s
    return False


def parse_expression(expr: dict) -> dict:
    """拆解 expression 对象为可判定的字段。"""
    s = expr.get("schema")
    if isinstance(s, str):
        try:
            s = json.loads(s)
        except Exception:
            s = {}
    s = s or {}
    des = s.get("designData") or {}
    rt = s.get("runtimeData") or {}
    return {
        "title": expr.get("title") or "",
        "translation": des.get("expressionTranslation") or "",
        "resultType": des.get("resultTypeInfo"),
        "terminalType": des.get("terminalType"),
        "tokens": des.get("tokens") or [],
        "context": des.get("context") or [],
        "executableExpr": rt.get("executableExpr") or "",
    }


def iter_expressions(obj: Any, path: str = "", _depth: int = 0) -> Iterable[tuple[str, dict]]:
    """递归找出对象内所有 expression（按特征识别，不靠字段名猜）。"""
    if _depth > 16:
        return
    if isinstance(obj, dict):
        if is_expression(obj):
            yield path, obj
            return
        for k, v in obj.items():
            sub = "%s.%s" % (path, k) if path else k
            yield from iter_expressions(v, sub, _depth + 1)
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            yield from iter_expressions(x, "%s[%d]" % (path, i), _depth + 1)


def variable_roots(expr: dict) -> list[str]:
    """表达式里引用的变量根（token.value 第一段）。"""
    info = parse_expression(expr)
    roots = []
    for t in info["tokens"]:
        if t.get("type") != "VARIABLE":
            continue
        v = t.get("value") or ""
        if v:
            roots.append(v.split(".")[0])
    return roots


def check_expression(expr: dict, known_vars: Iterable[str]) -> list[dict]:
    """单条表达式体检。返回问题列表，空 = 通过。

    known_vars: 本流程所有节点的 output.name 集合。
    """
    known = set(known_vars)
    info = parse_expression(expr)
    problems: list[dict] = []

    if not info["tokens"]:
        problems.append({"level": "EXPR", "issue": "tokens 为空"})
        return problems

    var_tokens = [t for t in _iter_tokens_recursive(info["tokens"])
                  if t.get("type") == "VARIABLE"]
    for t in var_tokens:
        v = t.get("value") or ""
        root = v.split(".")[0]
        if root and root not in known:
            problems.append({
                "level": "EXPR",
                "issue": "变量根 %r 不在流程输出中（悬空引用）" % root,
                "token": v,
                "desc": t.get("desc"),
            })

    # 恒等式：左右同一变量（只查顶层 tokens，简单二元表达式；subOps 里的不参与）
    top_var_tokens = [t for t in info["tokens"] if t.get("type") == "VARIABLE"]
    if len(top_var_tokens) == 2:
        v0 = top_var_tokens[0].get("value")
        v1 = top_var_tokens[1].get("value")
        if v0 and v0 == v1:
            ops = [t.get("value") for t in info["tokens"] if t.get("type") == "OPERATOR"]
            problems.append({
                "level": "EXPR",
                "issue": "左右引用同一变量，恒等式（x %s x）" % (ops[0] if ops else "?"),
                "token": v0,
            })

    # token 类型值域（递归进 FUNCTION.subOps）
    for t in _iter_tokens_recursive(info["tokens"]):
        tp = t.get("type")
        if tp and tp not in TOKEN_TYPES:
            problems.append({
                "level": "EXPR",
                "issue": "token.type=%r 不在五型值域" % tp,
                "token": t.get("value"),
            })

    # 结果类型必须存在
    if not info["resultType"]:
        problems.append({"level": "EXPR", "issue": "缺 resultTypeInfo"})

    return problems


def audit_node_expressions(node: dict, known_vars: Iterable[str]) -> list[dict]:
    """审计单个节点内所有表达式，返回带路径的问题列表。"""
    out = []
    for path, expr in iter_expressions(node):
        for p in check_expression(expr, known_vars):
            p = dict(p)
            p["where"] = path
            p["nodeId"] = node.get("nodeId")
            p["action"] = node.get("actionType") or node.get("type")
            out.append(p)
    return out


def collect_known_vars(schema: dict) -> set[str]:
    """本流程所有可引用变量名（节点 output.name + 流程入参名）。"""
    names: set[str] = set()

    def walk(nodes):
        for n in nodes or []:
            o = n.get("output")
            if isinstance(o, dict) and o.get("name"):
                names.add(o["name"])
            walk(n.get("nodes"))
            for c in n.get("conditions") or []:
                o = c.get("output")
                if isinstance(o, dict) and o.get("name"):
                    names.add(o["name"])
                walk(c.get("nodes"))

    walk(schema.get("nodes"))
    inp = schema.get("input")
    if isinstance(inp, dict) and inp.get("name"):
        names.add(inp["name"])
    return names


def check_three_layers(l1_expr: Any, l3_expr: Any) -> dict:
    """三层一致性判定（L1 = store，L3 = 后端 dataSchema）。

    返回 {same, l1, l3, verdict}
    """
    def title_of(e):
        if isinstance(e, dict):
            return (e.get("title") or "").strip()
        return (e or "").strip() if isinstance(e, str) else ""

    t1, t3 = title_of(l1_expr), title_of(l3_expr)
    same = t1 == t3
    if same:
        verdict = "一致"
    elif not t3:
        verdict = "L3 为空 —— 从未保存过"
    elif not t1:
        verdict = "L1 为空 —— 前端未加载"
    else:
        verdict = "★ 不一致 —— 改动只在 store，未「暂存草稿」"
    return {"same": same, "l1": t1[:120], "l3": t3[:120], "verdict": verdict}
