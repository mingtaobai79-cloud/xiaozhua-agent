"""UDC 规则域作用域约束（可执行）。

权威来源：设计器前端 `ty()` —— `docs/audit/udc-semantics/RULE-DOMAIN-SCOPE-CONSTRAINTS.md`

★ 三个域的可用节点集合彼此不相交（除 BRANCH / SUB_MICROFLOW），
  生成前必须校验，否则会「把页面域的节点拖进默认值域」，
  前端不报错但节点行为不正确（用户实测踩过）。

用法：
    from components.udc.rule_domain_scope import validate_rule_scope
    errors = validate_rule_scope(schema, "DEFAULT_VALUE")
    if errors: raise SystemExit(...)
"""
from __future__ import annotations

import json
import re

# --- 域 → 允许的 actionType（前端 ty() 三套定义，逐字对照模块 6036/2372/82800） ---
DOMAIN_NODES: dict[str, frozenset[str]] = {
    "VALIDATE": frozenset({
        "BRANCH", "ATTRIBUTE_UNIQUE", "ATTRIBUTE_REQUIRED",
        "SHOW_MESSAGE", "SUB_MICROFLOW",
    }),
    "DEFAULT_VALUE": frozenset({
        "BRANCH", "DEFAULT_VALUE", "SUB_MICROFLOW",
    }),
    "ASSIGN_VALUE": frozenset({
        "BRANCH", "ASSIGN_VALUE", "SUB_MICROFLOW",
    }),
    # 兜底域（ty() 落到 n(47118) 时）
    "OTHER": frozenset({
        "BRANCH", "ATTRIBUTE_UNIQUE", "ASSIGN_VALUE",
        "ATTRIBUTE_REQUIRED", "SHOW_MESSAGE",
    }),
}

# --- group_type（DB 数字）→ 域 ---
GROUP_TYPE_TO_DOMAIN: dict[int, str] = {
    1: "VALIDATE",
    2: "ASSIGN_VALUE",   # 推断：本环境无样本，见文档 UNVERIFIED
    3: "DEFAULT_VALUE",
}

# --- 域 → 「开始节点（实体本体）」是否出现在可选范围 ---
# DEFAULT_VALUE 被两处 shift() 移除，因此无法引用实体字段
DOMAIN_HAS_ENTITY_START: dict[str, bool] = {
    "VALIDATE": True,
    "DEFAULT_VALUE": False,
    "ASSIGN_VALUE": False,   # 未验证
    "OTHER": True,
}

# --- 域中文名（token.desc 前缀） ---
DOMAIN_TOKEN_PREFIX: dict[str, str] = {
    "VALIDATE": "实体规则",
    "DEFAULT_VALUE": "实体规则",
    "ASSIGN_VALUE": "实体规则",
}


def domain_of(group_type) -> str:
    """group_type（数字或域名）→ 域名。"""
    if isinstance(group_type, str):
        up = group_type.upper()
        if up in DOMAIN_NODES:
            return up
        if up.isdigit():
            group_type = int(up)
        else:
            return "OTHER"
    return GROUP_TYPE_TO_DOMAIN.get(int(group_type), "OTHER")


def iter_action_nodes(schema: dict):
    """深度遍历规则节点，产出 (actionType, node)。"""
    def walk(nodes):
        for n in nodes or []:
            at = n.get("actionType") or n.get("type")
            if at:
                yield at, n
            yield from walk(n.get("nodes"))
            for c in n.get("conditions") or []:
                yield from walk(c.get("nodes"))
    yield from walk(schema.get("nodes"))


def _iter_tokens(node: dict):
    """产出节点内所有 token dict（含 subOps 递归）。"""
    def walk(obj):
        if isinstance(obj, dict):
            if "type" in obj and "value" in obj and "uid" in obj:
                yield obj
            for v in obj.values():
                yield from walk(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from walk(v)
    yield from walk(node)


def validate_rule_scope(schema: dict, group_type) -> list[str]:
    """校验一条规则的节点/表达式是否越域。返回错误列表（空 = 合规）。"""
    domain = domain_of(group_type)
    allowed = DOMAIN_NODES[domain]
    errs: list[str] = []

    if not schema.get("endNode"):
        errs.append("缺 endNode（前端会补，但保存后可能被判历史版本）")

    for at, node in iter_action_nodes(schema):
        if at in ("CONDITION", "END", "END_NODE"):
            continue
        if at not in allowed:
            errs.append(
                "节点 %r 不属于 %s 域（该域只允许 %s）"
                % (at, domain, "/".join(sorted(allowed)))
            )

    # 默认值域不得引用实体字段
    if not DOMAIN_HAS_ENTITY_START[domain]:
        for at, node in iter_action_nodes(schema):
            for tok in _iter_tokens(node):
                if tok.get("type") == "VARIABLE" and str(tok.get("value", "")).startswith("dto."):
                    errs.append(
                        "节点 %r 引用了实体字段 %r，但 %s 域可选范围里没有实体（被 shift 移除）"
                        % (at, tok.get("value"), domain)
                    )

    # 表达式运算符必须是单等号
    for at, node in iter_action_nodes(schema):
        for c in node.get("conditions") or []:
            expr = c.get("expression") or {}
            title = str(expr.get("title") or "")
            if "==" in title:
                errs.append("条件表达式用了 `==`：%r —— 平台只认单等号 `=`" % title)

    return errs


def validate_sub_microflow_service(mf_service: dict | None) -> list[str]:
    """校验子微流程节点引用的服务能否被规则调用。"""
    if not mf_service:
        return ["子微流程节点缺 mfService"]
    errs = []
    t = str(mf_service.get("type") or "")
    if t not in ("SERVICE", "CUSTOM"):
        errs.append(
            "mfService.type=%r 非法（只允许 SERVICE=type0 / CUSTOM=type3；"
            "type=1 前端微流程不可被规则引用）" % t
        )
    if not mf_service.get("id"):
        errs.append("mfService.id 为空")
    name = str(mf_service.get("name") or "")
    if name.startswith("MFFRONTEND"):
        errs.append("mfService.name=%r 是前端微流程（type=1），不可被规则引用" % name)
    return errs


def load_domain_node_sets(path: str | None = None) -> dict:
    """从抽取产物读三套域节点集（供审计/刷新用）。"""
    import os
    p = path or os.path.join(
        os.path.dirname(__file__), "..", "..",
        "core", "facts", "udc", "microflow", "domain-node-sets.json",
    )
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


__all__ = [
    "DOMAIN_NODES", "GROUP_TYPE_TO_DOMAIN", "DOMAIN_HAS_ENTITY_START",
    "domain_of", "iter_action_nodes", "validate_rule_scope",
    "validate_sub_microflow_service", "load_domain_node_sets",
]
