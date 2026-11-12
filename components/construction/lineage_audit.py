"""字段级血缘审计（Data Lineage Audit）—— 批量验证器的固定环节。

任务书（2026-11-04 用户纠偏）要求：每个写实体字段都要能追溯来源，输出
lineage-report.json + 统计，评估「节点串得少、关联性不强」的问题。

分析对象：draft（逻辑图，construct 之前的意图层），写节点 fields 的值槽
是明确的 const/field/input/op/arith/fn/item 表达，比 dataSchema 的
SelectParam/Expression/Simple 更容易判来源。

7 种来源（CONSTANT/TRIGGER_INPUT/PREVIOUS_NODE/PREVIOUS_NODE_FIELD/
LOOP_ITEM/EXPRESSION/SYSTEM_VALUE）——见 core/facts/udc/microflow/
business-data-flow.md 结论五 + intent_draft_schema.py VALUE_SLOTS。
"""
from __future__ import annotations

from collections import Counter
from typing import Any

SOURCE_CONSTANT = "CONSTANT"
SOURCE_TRIGGER_INPUT = "TRIGGER_INPUT"
SOURCE_PREVIOUS_NODE = "PREVIOUS_NODE"
SOURCE_PREVIOUS_NODE_FIELD = "PREVIOUS_NODE_FIELD"
SOURCE_LOOP_ITEM = "LOOP_ITEM"
SOURCE_EXPRESSION = "EXPRESSION"
SOURCE_SYSTEM_VALUE = "SYSTEM_VALUE"

ALL_SOURCES = (
    SOURCE_CONSTANT, SOURCE_TRIGGER_INPUT, SOURCE_PREVIOUS_NODE,
    SOURCE_PREVIOUS_NODE_FIELD, SOURCE_LOOP_ITEM, SOURCE_EXPRESSION,
    SOURCE_SYSTEM_VALUE,
)

# 有 fields 的写节点（值槽直接落实体字段）。
WRITE_WITH_FIELDS = ("create_entity", "change_entity")
# 循环节点：body 是嵌套 nodes，循环项字段引用它的 id 作别名。
LOOP_KIND = "for_each"
# 有数据出参、业务上应被下游引用的节点（孤立检测只看这些）。
# 写节点（create/change_entity 标量 id）、控制节点（branch）、调用节点
# （sub_microflow）出参本可不被引用，不算孤立。
DATA_NODE_KINDS = ("retrieve", "retrieve_array", "create_variable", "list_operation")


def _child_lists(n: dict) -> list[list[dict]]:
    """节点的嵌套 nodes 列表（for_each.body / branch.then/else）。"""
    kind = n.get("kind")
    if kind == LOOP_KIND:
        return [n.get("body") or []]
    if kind == "branch":
        return [n.get("then") or [], n.get("else") or []]
    return []


def classify_value(value: Any, loop_aliases: set[str]) -> str:
    """判断单个值槽的来源类型。

    规则顺序敏感：const/input 优先，其次表达式（op/arith/fn）、item（循环项），
    最后 field 按别名/字段级/整节点三级判定。
    """
    if not isinstance(value, dict):
        return SOURCE_CONSTANT  # 裸字面量（bool/int/float/str）
    if "const" in value:
        return SOURCE_CONSTANT
    if "input" in value:
        return SOURCE_TRIGGER_INPUT
    if any(k in value for k in ("op", "arith", "fn")):
        return SOURCE_EXPRESSION
    if "item" in value:
        return SOURCE_LOOP_ITEM
    if "field" in value:
        f = value["field"]
        if f == "$input" or f.startswith("$input."):
            return SOURCE_TRIGGER_INPUT
        alias = f.split(".")[0]
        if alias in loop_aliases:
            return SOURCE_LOOP_ITEM
        if "." in f:
            return SOURCE_PREVIOUS_NODE_FIELD
        return SOURCE_PREVIOUS_NODE
    if "system" in value:
        return SOURCE_SYSTEM_VALUE
    return SOURCE_CONSTANT  # 兜底：未知形态当固定值，别误判成引用


def _ref_target(value: Any) -> str | None:
    """提取值槽引用的节点别名（field/input/item 的第一段），无引用返回 None。"""
    if not isinstance(value, dict):
        return None
    if "field" in value:
        f = value["field"]
        if f == "$input" or f.startswith("$input."):
            return None  # 入参不是节点
        return f.split(".")[0]
    if "item" in value:
        return value.get("item") or value.get("alias")
    return None


def _extract_refs(obj: Any, out: set[str]) -> None:
    """递归提取 obj 里所有节点引用目标（field/item 第一段 + 裸字符串引用键）。

    覆盖：写节点 fields、create_variable.value、retrieve.by_id_from、
    retrieve_array.right/conditions、branch.condition、sub_microflow.value、
    change_entity.from_node、for_each.list、list_operation.list_node 等。
    field/item 是值槽引用（第一段=别名）；list_node/by_id_from/from_node/list/
    ids_from/page_info_from 是裸字符串引用键。不碰实体字段名（sort_by/cond_field）。
    """
    if isinstance(obj, dict):
        f = obj.get("field")
        if isinstance(f, str) and f and f != "$input" and not f.startswith("$input."):
            out.add(f.split(".")[0])
        it = obj.get("item")
        if it:
            out.add(obj.get("item") or obj.get("alias"))
        for k in _NODE_REF_KEYS:
            v = obj.get(k)
            if isinstance(v, str) and v and v != "$input":
                out.add(v)
        for v in obj.values():
            _extract_refs(v, out)
    elif isinstance(obj, list):
        for x in obj:
            _extract_refs(x, out)


_NODE_REF_KEYS = ("list_node", "by_id_from", "from_node", "list",
                  "ids_from", "page_info_from")


def audit_lineage(draft: dict[str, Any]) -> dict[str, Any]:
    """分析 draft 的字段血缘。

    返回：
    {
      "fields": [{node, kind, entity, field, source, ref?, value}, ...],
      "metrics": {
        "sources": {SOURCE: 计数, ...},          # 7 种来源各自字段数
        "const_fields": 固定值字段数,
        "prev_node_refs": 前序节点（整节点）引用数,
        "field_refs": 前序节点字段级引用数,
        "loop_item_refs": 循环项引用数,
        "expr_refs": 表达式引用数,
        "trigger_input_refs": 入参引用数,
        "isolated_nodes": [出参没被下游引用的节点 id],
        "hardcoded_links": [疑似硬编码的跨表关联（见 _flag_hardcoded）],
      }
    }
    """
    nodes = draft.get("nodes") or []

    # 第一遍：收集循环别名 + 所有节点 id（含循环体内部）+ 所有引用目标。
    loop_aliases: set[str] = set()
    all_node_ids: list[str] = []
    refs: set[str] = set()  # 被引用的节点 id（孤立节点检测）
    node_kinds: dict[str, str] = {}  # id -> kind（孤立检测按类型过滤）

    def _collect(ns):
        for n in ns:
            nid = n.get("id")
            if nid:
                all_node_ids.append(nid)
                node_kinds[nid] = n.get("kind")
            if n.get("kind") == LOOP_KIND:
                loop_aliases.add(nid)
            _extract_refs(n, refs)  # 提取所有引用目标（含嵌套子节点）
            for child in _child_lists(n):
                _collect(child)

    _collect(nodes)

    fields: list[dict[str, Any]] = []
    counters: Counter = Counter()

    def _analyze(ns):
        for n in ns:
            kind = n.get("kind")
            if kind in WRITE_WITH_FIELDS:
                entity = n.get("entity")
                for fname, v in (n.get("fields") or {}).items():
                    src = classify_value(v, loop_aliases)
                    rec = {
                        "node": n.get("id"), "kind": kind, "entity": entity,
                        "field": fname, "source": src,
                    }
                    tgt = _ref_target(v)
                    if tgt:
                        rec["ref"] = tgt
                    rec["value"] = v
                    fields.append(rec)
                    counters[src] += 1
            elif _child_lists(n):
                for child in _child_lists(n):
                    _analyze(child)

    _analyze(nodes)

    # 孤立节点：有数据出参（DATA_NODE_KINDS）却没被任何下游引用的节点。
    #   写节点标量 id、branch、sub_microflow 出参本可不被引用，不算孤立。
    isolated = [nid for nid in all_node_ids
                if nid not in refs and node_kinds.get(nid) in DATA_NODE_KINDS]

    metrics = {
        "sources": {s: counters.get(s, 0) for s in ALL_SOURCES},
        "const_fields": counters.get(SOURCE_CONSTANT, 0),
        "prev_node_refs": counters.get(SOURCE_PREVIOUS_NODE, 0),
        "field_refs": counters.get(SOURCE_PREVIOUS_NODE_FIELD, 0),
        "loop_item_refs": counters.get(SOURCE_LOOP_ITEM, 0),
        "expr_refs": counters.get(SOURCE_EXPRESSION, 0),
        "trigger_input_refs": counters.get(SOURCE_TRIGGER_INPUT, 0),
        "isolated_nodes": isolated,
        "hardcoded_links": _flag_hardcoded(fields),
    }
    return {"fields": fields, "metrics": metrics}


def _flag_hardcoded(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """疑似硬编码关联：同一写节点里，一个字段引用前序节点 X，另一个字段是
    本应继承 X 上下文的固定值（同实体已用 X 关联，却再 hardcode 同类 key）。
    当前只做启发式：CONSTANT 字段值形如「<别名>-<编号>」或纯数字 id，且同节点
    存在 PREVIOUS_NODE(_FIELD) 引用——提示「可能是硬编码关联，核查是否该引用」。

    这是提示（HINT），不是硬拦截——业务上固定枚举/状态允许 const。
    """
    hints = []
    for f in fields:
        if f["source"] != SOURCE_CONSTANT:
            continue
        # 同节点是否有引用来源（说明这个写节点在继承前序上下文）
        node_id = f["node"]
        siblings = [x for x in fields if x["node"] == node_id]
        has_ref = any(x["source"] in (SOURCE_PREVIOUS_NODE,
                                      SOURCE_PREVIOUS_NODE_FIELD,
                                      SOURCE_LOOP_ITEM) for x in siblings)
        if has_ref:
            hints.append({"node": node_id, "field": f["field"],
                          "value": f["value"].get("const"),
                          "hint": "同节点有引用来源，此字段却用固定值，核查是否该继承前序结果"})
    return hints


def score_case(draft: dict[str, Any]) -> dict[str, Any]:
    """基于血缘指标给案例质量打分（任务书第三项：案例质量评分）。

    评分维度（衡量「节点串得少、关联性不强」的反面）：
    - 数据流密度：非 const 字段占比（引用/表达式/入参 = 节点间数据流转）
    - 孤立节点：读而不用 = 链断（每个扣 20）
    - 硬编码关联：该引用却硬编码（每个扣 10）

    100 分起。纯读流程（无写字段）给 100（无可评字段，不误扣）。
    分级：S≥90 / A≥75 / B≥60 / C<60。
    """
    rep = audit_lineage(draft)
    m = rep["metrics"]
    total = len(rep["fields"])
    if total == 0:
        return {"score": 100, "grade": "S", "reason": "无写节点字段（纯读流程，无可评）",
                "total_fields": 0, "const_fields": 0, "dynamic_fields": 0,
                "ref_rate": 1.0, "isolated_nodes": [], "hardcoded_links": [],
                "sources": m["sources"]}

    srcs = m["sources"]
    const = srcs[SOURCE_CONSTANT]
    dynamic = total - const  # 所有非 const 字段（引用/表达式/入参/系统值）
    ref_rate = dynamic / total

    isolated = m["isolated_nodes"]
    hardcoded = m["hardcoded_links"]

    score = 100.0
    score -= len(isolated) * 20                    # 读而不用是硬伤
    score -= len(hardcoded) * 10                   # 该引用却硬编码
    if ref_rate < 0.5:                             # 引用率低于一半 = 偏 CRUD 堆
        score -= (0.5 - ref_rate) * 60             # 最多扣 30

    score = max(0, round(score))
    grade = "S" if score >= 90 else "A" if score >= 75 else "B" if score >= 60 else "C"

    return {"score": score, "grade": grade,
            "total_fields": total, "const_fields": const, "dynamic_fields": dynamic,
            "ref_rate": round(ref_rate, 2),
            "isolated_nodes": isolated, "hardcoded_links": hardcoded,
            "sources": srcs}


if __name__ == "__main__":
    import json
    import sys
    # 一次性自检：从 stdin 或 --file 读 draft JSON，输出 lineage-report。
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if path:
        draft = json.load(open(path, encoding="utf-8"))
    else:
        draft = json.load(sys.stdin)
    print(json.dumps(audit_lineage(draft), ensure_ascii=False, indent=2))
