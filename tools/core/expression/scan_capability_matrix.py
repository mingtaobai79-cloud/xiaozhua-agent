"""P2-1 表达式能力矩阵：扫 643 条发布语料，按 (actionType, slot-path) 统计
值槽三态（Simple/SelectParam/Expression）分布 + 期望类型 + 引用来源。
产出 core/facts/udc/microflow/expression-capability-matrix.json"""
import os, sys, json, collections
os.chdir("<SEEYON_AGENT_ROOT>"); sys.path.insert(0, ".")

d = json.load(open("scratch/pmp_schemas.json", encoding="utf-8"))
def walk(n, out):
    if isinstance(n, dict):
        out.append(n)
        for v in n.values(): walk(v, out)
    elif isinstance(n, list):
        for v in n: walk(v, out)
nodes = []
for v in d.values(): walk(v, nodes)

SKIP = ("output", "input", "mfService", "structure", "app", "selectMethod")
def slots_of(node):
    """产出 (host_actionType, rel_path, wrapper)。进入子节点(nodes[])后，
    宿主切到最内层节点，路径相对宿主重算。"""
    found = []
    def rec(obj, path, host_at, depth=0):
        if depth > 14:
            return
        if isinstance(obj, dict):
            t = obj.get("type")
            if t in ("Simple", "SelectParam", "Expression") and any(
                    k in obj for k in ("simple", "selectParam", "schema", "title")):
                found.append((host_at, path, obj)); return
            if t in ("CONTEXT_VARIABLE", "CONSTANT", "EXPRESSION") and "value" in obj:
                found.append((host_at, path, obj)); return
            cur_at = host_at
            nxt_path = path
            if obj.get("nodeId") and obj is not node:
                cur_at = obj.get("actionType") or obj.get("type")
                nxt_path = ""          # 宿主切换，路径归零
            for k, v in obj.items():
                if k in SKIP: continue
                rec(v, ("%s.%s" % (nxt_path, k)) if nxt_path else k, cur_at, depth + 1)
        elif isinstance(obj, list):
            for i, x in enumerate(obj):
                rec(x, ("%s[]" % path) if path else "", host_at, depth + 1)
    at0 = node.get("actionType") or node.get("type")
    rec(node, "", at0)
    return found

def norm_path(p):
    """归一：[数字] → []，uuid 段吞掉。"""
    import re
    p = re.sub(r"\[\d+\]", "[]", p)
    p = re.sub(r"\.conditions\[\]\.nodes\[\]", ".conditions[].nodes[]", p)
    return p

def wrap_kind(w):
    t = w.get("type")
    if t in ("CONTEXT_VARIABLE", "CONSTANT", "EXPRESSION"): return t
    if t == "Simple": return "Simple"
    if t == "SelectParam": return "SelectParam"
    if t == "Expression": return "Expression"
    return t

def want_type(node, path):
    """槽位期望类型：从宿主字段元数据推。已知宿主：value←paramType/dataType；右值←leftParam。"""
    at = node.get("actionType")
    if at in ("CREATE_VARIABLE", "CHANGE_VARIABLE", "CREATE_LIST") and path.endswith("value"):
        return node.get("dataType")
    if "rightParams" in path:
        # 同层 leftParam 的 dataType
        return node.get("_right_want")
    return None

mat = collections.defaultdict(lambda: collections.Counter())
types = collections.defaultdict(collections.Counter)
refsrc = collections.defaultdict(collections.Counter)
for n in nodes:
    if not isinstance(n, dict): continue
    at = n.get("actionType") or n.get("type")
    if not at or not n.get("nodeId"):
        continue   # 只扫真实节点（wrapper/元数据对象跳过）
    for host_at, raw_path, w in slots_of(n):
        p = norm_path(raw_path)
        at, k = host_at, (host_at, p)
        mat[k][wrap_kind(w)] += 1
        # 类型
        if wrap_kind(w) == "SelectParam":
            sp = w.get("selectParam") or {}
            types[k][sp.get("dataType")] += 1
        elif wrap_kind(w) == "Simple":
            v = w.get("simple")
            types[k][type(v).__name__] += 1
        elif wrap_kind(w) in ("EXPRESSION", "Expression"):
            types[k]["expression"] += 1
        elif wrap_kind(w) == "CONSTANT":
            types[k]["const"] += 1
        # 引用来源（SelectParam 的 outputName 前缀）
        if wrap_kind(w) == "SelectParam":
            sp = w.get("selectParam") or {}
            on = str(sp.get("outputName") or "")
            src = on.split("_")[1] if on.startswith("_") and len(on.split("_")) > 1 else "other"
            refsrc[k][src] += 1

out = {}
for (at, p), c in sorted(mat.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
    out["%s | %s" % (at, p)] = {
        "counts": dict(c),
        "select_dataType": dict(types[k := (at, p)].most_common(6)) if isinstance(types.get(k), collections.Counter) else {},
        "ref_output_prefix": dict(collections.Counter(refsrc.get(k, {})).most_common(4)),
    }
res = {"_meta": {"source": "pmp_schemas.json 发布语料 643 条", "generated": "2026-11-01",
                 "note": "三态=Simple/SelectParam/Expression；条件右值右三态=CONTEXT_VARIABLE/CONSTANT/EXPRESSION"},
       "slots": out}
json.dump(res, open("scratch/_expr_matrix_draft.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("槽位组合数:", len(out))
for k, v in list(out.items()):
    c = v["counts"]
    tot = sum(c.values())
    if tot >= 20:
        print("%-46s n=%-5d %s" % (k[:46], tot, c))
