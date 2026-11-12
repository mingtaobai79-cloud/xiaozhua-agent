#!/usr/bin/env python3
"""开工前全面盘点：拿业务需求对四个权威源做差集，输出开工风险清单。

用法：
    python scripts/business_readiness_audit.py --kinds create_entity,for_each,branch \\
        --entities 采购订单,采购明细 --fields poCode:STRING,poId:ENTITY,totalAmount:DECIMAL

    # 或从 draft 脚本直接盘（推荐）
    python scripts/business_readiness_audit.py --draft _attic_pending/biz/mfg/05_mf02_purchase.py

输出：
    - 本次用到的节点/子模式，各自能力等级 + 未验范围
    - 字段类型风险（DECIMAL 无精度 / ENTITY 无关联 / 未走流水号的编码字段）
    - 流转模式对照（是否属于语料主流组合）
    - 退出码：0=无阻碍风险，2=有阻碍风险（不许直接开工）

★ 设计原则：不靠记忆列风险，从四个权威源实时读：
    ① scratch/pmp_schemas.json                         真实语料
    ② core/facts/.../node-settings-capability.json    配置矩阵
    ③ components/udc/microflow/capability_registry   能力等级
    ④ core/facts/udc/setting/*                       设置域构件
"""
import argparse
import importlib.util
import json
import os
import re
import sys
from collections import Counter

REPO = os.environ.get("XIAOZHUA_AGENT_REPO", "<XIAOZHUA_AGENT_ROOT>")


def _load_json(rel):
    p = os.path.join(REPO, rel)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_corpus_stats():
    """从 643 条真实语料统计节点分布 + 流转序列 + 循环体构成。"""
    d = _load_json("scratch/pmp_schemas.json")
    if not d:
        return {"error": "语料快照不存在（scratch/pmp_schemas.json）"}
    actions, seq, loop_body, triggers = Counter(), Counter(), Counter(), Counter()
    total = 0

    for _mid, item in d.items():
        ds = (item or {}).get("ds") or {}
        trig = (ds.get("trigger") or {}).get("type")
        if trig:
            triggers[trig] += 1

        def walk(ns, in_loop=False):
            nonlocal total
            prev = None
            for n in ns or []:
                at = n.get("actionType") or n.get("type")
                if at:
                    actions[at] += 1
                    total += 1
                    if in_loop:
                        loop_body[at] += 1
                    if prev:
                        seq[(prev, at)] += 1
                    prev = at
                for key in ("ifBranch", "elseBranch"):
                    b = n.get(key)
                    if isinstance(b, dict) and isinstance(b.get("nodes"), list):
                        walk(b["nodes"], in_loop)
                if isinstance(n.get("nodes"), list):
                    walk(n["nodes"], in_loop or at in ("FOR_EACH", "FOR"))

        walk(ds.get("nodes") or [])

    return {"flows": len(d), "nodes": total, "actions": actions,
            "seq": seq, "loop_body": loop_body, "triggers": triggers}


def load_caps():
    sys.path.insert(0, REPO)
    try:
        from components.udc.microflow import capability_registry as cr
        return cr.load()
    except Exception as e:
        return {"_error": str(e)}


def load_settings_matrix():
    return _load_json("core/facts/udc/microflow/node-settings-capability.json")


# draft kind → 平台 actionType（DSL 层小写，平台大写）
KIND_TO_ACTION = {
    "create_entity": "CREATE_ENTITY", "change_entity": "CHANGE_ENTITY",
    "delete_entity": "DELETE_ENTITY", "retrieve": "RETRIEVE",
    "retrieve_array": "RETRIEVE_ARRAY", "create_batch_entity": "CREATE_BATCH_ENTITY",
    "change_batch_entity": "CHANGE_BATCH_ENTITY", "create_list": "CREATE_LIST",
    "create_list_entity": "CREATE_LIST", "change_list": "CHANGE_LIST",
    "change_list_add": "CHANGE_LIST", "list_operation": "LIST_OPERATION",
    "create_variable": "CREATE_VARIABLE", "change_variable": "CHANGE_VARIABLE",
    "create_map": "CREATE_MAP", "map_operation": "MAP_OPERATION",
    "branch": "BRANCH", "for_each": "FOR_EACH", "for_count": "FOR",
    "break": "BREAK", "custom_error": "CUSTOM_ERROR",
    "sub_microflow": "SUB_MICROFLOW", "call_app_service": "CALL_APP_SERVICE",
    "call_data_flow": "CALL_DATA_FLOW", "publish_business_event": "PUBLISH_BUSINESS_EVENT",
    "convert_data": "CONVERT_DATA", "data_mapping": "DATA_MAPPING",
    "page_info": "CREATE_VARIABLE",
}

# 能力矩阵口径外的结构节点（矩阵只统计 22 个数据节点，控制流/触发器不在其中）
STRUCTURAL_ACTIONS = {"BRANCH", "FOR_EACH", "FOR", "BREAK", "CUSTOM_ERROR", "END"}

# ── 子模式级必填校验：DSL kind + DSL 字段 → 配置矩阵的 UI 子模式 ──
# 平台配置矩阵用中文 UI 标签表述子模式与必填项；DSL 用英文 kind/字段。
# 这张表是两者之间的桥，新增子模式时必须同步这里（否则校验退化为跳过）。
DSL_SUBMODE = {
    # kind: (mode_field_ui, dsl_field, {dsl_value: ui_mode})
    "create_variable": ("变量类型", "entity", {
        "_entity": "实体对象",   # 有 entity 字段 = 实体对象
        "_scalar": "基本类型",   # 无 entity 且有 data_type = 基本类型
    }),
    "change_list": ("操作类型", "action", {
        "ADD": "增加", "REPLACE": "全量替换", "REMOVE": "删除", "CLEAR": "清空",
    }),
    # DSL 的 change_list_add 等价于 CHANGE_LIST 的 ADD 形态（构造器会生成 action=ADD）
    "change_list_add": ("操作类型", "_implicit_add", {"_implicit_add": "增加"}),
    "list_operation": ("操作类型", "op_type", {
        "SIZE": "计数", "FILTER": "过滤", "DISTINCT": "去重",
        "FIRST_ONE": "第一条", "LAST_ONE": "最后一条", "PICK_ONE": "第N条",
    }),
    "retrieve": ("查询方式", "by_id_from", {
        "_id": "ID查询", "_cond": "条件查询",
    }),
    "retrieve_array": ("查询方式", "fetch_type", {
        "CONDITION": "条件查询", "IDS": "ID集合查询", "COUNT": "计数",
    }),
    "create_entity": ("赋值方式", "mapping_type", {
        "_default": "字段映射", "attrs": "对象引用",
    }),
    "delete_entity": ("删除规则", "delete_type", {
        "SELECT_PARAM": "指定删除", "CONDITION": "过滤条件删除",
    }),
    "publish_business_event": ("事件类型", None, {
        "IN_APP": "应用内(同步)", "CROSS_APP": "应用间(异步)",
    }),
    "data_mapping": ("目标数据对象类型", None, {
        "ENTITY": "实体对象",
    }),
    "call_data_flow": ("数据来源方式", None, {
        "CONDITION": "查询数据", "SELECT_PARAM": "选择数据",
    }),
    "custom_error": ("错误提示方式", None, {
        "GLOBAL": "全局提示", "ELEMENT": "定位到页面元素",
    }),
}


def _resolve_submode(kind, node):
    """从 DSL 节点推断它落在配置矩阵的哪个 UI 子模式；推不出返回 None。"""
    spec = DSL_SUBMODE.get(kind)
    if not spec:
        return None, None
    mode_field, dsl_field, mapping = spec
    if kind == "create_variable":
        key = "_entity" if node.get("entity") else "_scalar"
        return mode_field, mapping.get(key)
    if kind == "retrieve":
        key = "_id" if node.get("by_id_from") else "_cond"
        return mode_field, mapping.get(key)
    if kind == "create_entity":
        key = "attrs" if node.get("mapping_type") == "attrs" else "_default"
        return mode_field, mapping.get(key)
    if dsl_field is None:
        # 没有明确 DSL 字段，尝试从 node 里找已知键
        for k in ("event_type", "data_source_type", "error_mode"):
            if node.get(k) and node[k] in mapping:
                return mode_field, mapping[node[k]]
        return None, None
    # 有默认值的子模式：DSL 不写时按平台默认形态
    DEFAULTS = {
        "retrieve_array": "条件查询",   # 不写 fetch_type = CONDITION
        "retrieve": "条件查询",          # 不写 by_id_from = CONDITION
        "delete_entity": "指定删除",
        "publish_business_event": "应用内(同步)",   # 默认 in-app
    }
    if kind == "change_list_add":
        return mode_field, mapping.get("_implicit_add")

    val = node.get(dsl_field)
    if not val:
        return mode_field, DEFAULTS.get(kind)
    return mode_field, mapping.get(val)


# DSL 字段 → 配置矩阵 UI 标签（一个字段可能满足多个 UI 标签）
DSL_FIELD_TO_UI = {
    # 通用
    "entity": {"选择实体", "实体对象", "选择应用"},
    "title": {"节点出参名称"},
    "caption": {"节点出参名称"},
    "list_node": {"选择列表"},
    "from_node": {"列表/对象", "选择该记录的ID"},
    "by_id_from": {"选择该记录的ID"},
    "cond_field": {"过滤条件"},
    "right": {"过滤条件"},
    "conditions": {"过滤条件"},
    "count_fields": {"操作数据"},
    "filter": {"过滤条件"},
    "index_value": {"第几条"},
    "fields": {"字段映射"},
    "value": {"默认值"},
    "data_type": {"数据类型"},
    "param_type": {"变量类型"},
    "sub_id": {"选择微流程", "子微流程"},
    "method_full": {"选择服务", "服务方法"},
    "event": {"可投递的事件", "选择应用"},
    "attrs": {"事件属性", "字段映射"},
    "item": {"列表/对象", "列表/对象元素"},
    "action": {"操作类型"},
    "op_type": {"操作类型"},
    "fetch_type": {"查询方式"},
    "delete_type": {"删除规则"},
    "message": {"填写错误"},
    "list_id": {"选择列表"},
}

# 由构造器/平台自动提供、不需要 DSL 显式写的 UI 必填项（否则全是假警报）
AUTO_PROVIDED_UI = {
    "选择应用", "变量类型", "操作类型", "查询方式", "赋值方式", "删除规则",
    "提示内容", "节点出参名称", "分页数据",   # 分页数据由 composer 自动注入默认 page_info
}

# 编码类字段名（必须走流水号，禁 const）
CODE_FIELD_RE = re.compile(r"(^|_)(code|no|number)$|Code$|No$|Number$", re.I)

# 汇总/余额类字段（写明细时必须同步更新）
SUMMARY_FIELD_RE = re.compile(r"(qty|quantity|amount|cost|count|total|balance|sum)", re.I)


def collect_draft_nodes(draft):
    """递归收集 draft 的节点（含循环体/分支体）。"""
    out = []

    def walk(ns):
        for n in ns or []:
            out.append(n)
            for key in ("body", "then", "else"):
                v = n.get(key)
                if isinstance(v, list):
                    walk(v)
            for key in ("nodes",):
                if isinstance(n.get(key), list):
                    walk(n[key])

    walk(draft.get("nodes") or [])
    return out


def load_draft(path):
    d = os.path.dirname(path)
    sys.path.insert(0, os.path.abspath(d))
    sys.path.insert(0, REPO)
    cwd = os.getcwd()
    os.chdir(REPO)
    try:
        spec = importlib.util.spec_from_file_location("audit_target", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for fn in ("build_draft", "draft"):
            if hasattr(mod, fn):
                v = getattr(mod, fn)
                return v() if callable(v) else v
        raise RuntimeError("draft 脚本没有 build_draft()/draft")
    finally:
        os.chdir(cwd)


def audit_nodes(nodes, matrix):
    """子模式级必填校验：对每个节点，定位它的 UI 子模式，比对必填项是否齐全。

    返回 (blockers, warns, checked)：
      blockers = 必填项缺失（前端会零请求拦下，后端 checkSchema 却可能放行）
      warns    = 子模式识别失败 / 矩阵缺该子模式（校验退化，需人工确认）
      checked  = 实际校验过的 (节点id, 子模式, 必填数) 列表
    """
    blockers, warns, checked = [], [], []
    nodes_cfg = (matrix or {}).get("nodes") or {}
    if not nodes_cfg:
        return blockers, ["配置矩阵不可用，子模式校验已跳过"], checked

    for n in nodes:
        kind = n.get("kind")
        if not kind:
            continue
        action = KIND_TO_ACTION.get(kind)
        cfg = nodes_cfg.get(action)
        if not cfg:
            continue  # 结构节点/无矩阵项，前面已归类为矩阵口径

        submodes = cfg.get("submodes") or []
        if not submodes:
            continue  # 单一形态节点，无子模式概念

        mode_field, ui_mode = _resolve_submode(kind, n)
        nid = n.get("id") or kind

        if not ui_mode:
            warns.append(f"{nid}({kind}): 无法从 DSL 推断子模式（{mode_field or '?'}），"
                         f"可选: {[s.get('mode') for s in submodes]}")
            continue

        target = next((s for s in submodes if s.get("mode") == ui_mode), None)
        if not target:
            warns.append(f"{nid}({kind}): 矩阵中无子模式「{ui_mode}」"
                         f"（现有: {[s.get('mode') for s in submodes]}）")
            continue

        required = target.get("required") or []
        # 把 DSL 节点里出现的键翻译成 UI 标签，看必填项覆盖到没有
        present_ui = set()
        for k in n.keys():
            uis = DSL_FIELD_TO_UI.get(k)
            if uis:
                present_ui |= uis
        # 子模式切换会移除的字段不算缺
        removed = set(target.get("fields_removed") or [])
        missing = [r for r in required if r not in present_ui and r not in removed]

        missing = [m for m in missing if m not in AUTO_PROVIDED_UI]
        # 「选择实体」由 entity 字段满足
        if "entity" in n and "选择实体" in missing:
            missing.remove("选择实体")

        checked.append((nid, ui_mode, len(required)))
        if missing:
            blockers.append(f"{nid}({kind}) 子模式「{ui_mode}」缺必填项: {missing}")

    return blockers, warns, checked


def audit_patterns(nodes, corpus):
    """业务模式校验：用户明确禁止的写法 + 流转组合是否符合语料主流。

    ① 循环内逐条 create_entity —— 用户偏好批量写（每轮一次 INSERT，N 次 vs 1 次）
    ② 相邻节点组合在 643 条语料中从未出现 —— 罕见串法，需额外验证
    """
    blockers, warns = [], []
    corpus_ok = corpus and "error" not in corpus
    seq_counts = corpus["seq"] if corpus_ok else {}

    def walk(ns, in_loop=False, prev=None):
        for n in ns or []:
            kind = n.get("kind")
            action = KIND_TO_ACTION.get(kind) if kind else None

            # ① 循环内逐条写实体
            if in_loop and kind == "create_entity":
                warns.append(f"{n.get('id')}: 循环内逐条 create_entity（用户偏好批量写："
                             f"create_list_entity→create_variable→change_list_add→create_batch_entity）")

            # ② 流转组合对照语料
            if prev and action and corpus_ok:
                pair = (prev, action)
                if pair not in seq_counts:
                    warns.append(f"{prev} → {action} 在 643 条语料中未出现"
                                 f"（{n.get('id')}），罕见串法需额外验证")

            body = n.get("body") if isinstance(n.get("body"), list) else []
            walk(body, in_loop or kind in ("for_each", "for_count"), action)

            for key in ("then", "else"):
                v = n.get(key)
                if isinstance(v, list):
                    walk(v, in_loop, action)
            if isinstance(n.get("nodes"), list):
                walk(n["nodes"], in_loop, action)

    walk(nodes or [])
    return blockers, warns


def audit(actions_used, fields, corpus, caps, matrix):
    blockers, warns = [], []

    # ① 能力等级
    matrix_gap = []
    for act in sorted(actions_used):
        c = caps.get(act)
        if not c:
            # 能力矩阵只收 22 个数据节点；控制流/触发器不在其中是矩阵口径，不是风险
            if act in STRUCTURAL_ACTIONS:
                matrix_gap.append(act)
            else:
                blockers.append(f"{act}: 节点未出现在能力矩阵，也未列入结构节点白名单")
            continue
        note = c.note or ""
        if "RUNTIME_VERIFIED" not in note:
            blockers.append(f"{act}: 未达 RUNTIME_VERIFIED → {note[:80]}")
        elif "未验" in note:
            warns.append(f"{act}: 部分形态未验 → {note[:100]}")

    # ② 配置矩阵：子模式存在性
    nodes_cfg = (matrix or {}).get("nodes") or {}
    for act in sorted(actions_used):
        if act not in nodes_cfg:
            warns.append(f"{act}: 配置项矩阵中无此节点（共 {len(nodes_cfg)} 项）")

    # ③ 字段风险
    for fname, ftype in (fields or {}).items():
        ft = (ftype or "").upper()
        if CODE_FIELD_RE.search(fname):
            blockers.append(f"字段 {fname}: 编码类字段必须走流水号（CALL_APP_SERVICE），禁 const")
        if ft in ("DECIMAL", "CURRENCY"):
            warns.append(f"字段 {fname}: DECIMAL/CURRENCY 必须传 decimalDigits+maxLength（否则 scale=0）")
        if ft == "ENTITY":
            warns.append(f"字段 {fname}: 关联字段需 relationEntity+relationApp+relationType")
        if ft in ("ENUM", "CTPENUM"):
            warns.append(f"字段 {fname}: 枚举字段需 relationEntity 指向枚举实体验证")

    # ④ 流转模式对照
    if corpus and "error" not in corpus:
        known = {a for a in corpus["actions"]}
        for act in sorted(actions_used):
            if act not in known:
                warns.append(f"{act}: 语料 643 条流程中从未出现（罕见形态，需额外验证）")

    return blockers, warns, matrix_gap


def main():
    ap = argparse.ArgumentParser(description="开工前全面盘点")
    ap.add_argument("--draft", help="draft 脚本路径（含 build_draft()）")
    ap.add_argument("--kinds", help="逗号分隔的 DSL kind（无 draft 时手动指定）")
    ap.add_argument("--fields", help="字段清单 name:TYPE,...")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    corpus = load_corpus_stats()
    caps = load_caps()
    matrix = load_settings_matrix()

    actions_used = Counter()
    fields = {}
    draft_nodes = []
    if args.draft:
        draft = load_draft(args.draft)
        draft_nodes = collect_draft_nodes(draft)
        for n in draft_nodes:
            k = n.get("kind")
            if k:
                actions_used[KIND_TO_ACTION.get(k, k.upper())] += 1
            for fname in (n.get("fields") or {}):
                fields.setdefault(fname, "")
    if args.kinds:
        for k in args.kinds.split(","):
            k = k.strip()
            if k:
                actions_used[KIND_TO_ACTION.get(k, k.upper())] += 1
    if args.fields:
        for pair in args.fields.split(","):
            if ":" in pair:
                n, t = pair.split(":", 1)
                fields[n.strip()] = t.strip()

    blockers, warns, matrix_gap = audit(actions_used, fields, corpus, caps, matrix)

    # 子模式级必填校验（只对 draft 模式生效）
    submode_checked = []
    if draft_nodes:
        sb, sw, submode_checked = audit_nodes(draft_nodes, matrix)
        blockers = sb + blockers
        warns = warns + sw

        pb, pw = audit_patterns(draft_nodes, corpus)
        blockers = pb + blockers
        warns = warns + pw

    if args.json:
        print(json.dumps({"actions": dict(actions_used), "fields": fields,
                          "blockers": blockers, "warnings": warns},
                         ensure_ascii=False, indent=1))
    else:
        print("=" * 62)
        print("开工前盘点")
        print("=" * 62)
        if corpus and "error" not in corpus:
            print(f"语料基准: {corpus['flows']} 流程 / {corpus['nodes']} 节点")
            print(f"触发分布: {dict(corpus['triggers'])}")
        else:
            print(f"语料基准: 不可用（{(corpus or {}).get('error')}）")
        print(f"\n本次用到节点 {len(actions_used)} 种: {dict(actions_used)}")
        print(f"本次涉及字段 {len(fields)} 个")

        print("\n—— 阻碍项（必须解决才能开工）——")
        if blockers:
            for b in blockers:
                print(f"  ❌ {b}")
        else:
            print("  （无）")

        if submode_checked:
            print(f"\n—— 子模式级校验：{len(submode_checked)} 个节点已定位子模式 ——")
            for nid, mode, reqn in submode_checked[:20]:
                print(f"  ✓ {nid:20s} {mode}（必填 {reqn} 项）")

        if matrix_gap:
            print("\n—— 矩阵口径说明（结构节点，能力矩阵不统计）——")
            print(f"  ℹ️  {', '.join(matrix_gap)}")

        print("\n—— 警告项（已知风险，需注意）——")
        if warns:
            for w in warns:
                print(f"  ⚠️  {w}")
        else:
            print("  （无）")

        print("\n—— 语料高频流转（校验自己的串法是否主流）——")
        if corpus and "error" not in corpus:
            for (a, b), c in corpus["seq"].most_common(10):
                print(f"  {a:22s} → {b:22s} {c}")

    sys.exit(2 if blockers else 0)


if __name__ == "__main__":
    main()
