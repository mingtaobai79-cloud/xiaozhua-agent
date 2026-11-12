# -*- coding: utf-8 -*-
"""B4 取证/闸门脚本（纯只读，零网络）：36 键精简 DTO 的来源与触发条件判别

数据源（全部已落盘，无新抓取）：
  E1 = 04:08:54 CREATE 批次（14x76 UPDATE + 1x26 ADD）
  E2 = 04:52:05 UPDATE 批次（14x76 UPDATE + 1x36 UPDATE）
  bundle = src_redux_store_ts.14dc061e.js（STATIC，含 f[type] 表单默认表 / E[type] 提交默认表）

核心命题（逐条断言）：
  P1  键数不是 dataType 的函数（同 dataType 下存在多档键数）
  P2  76 键 = 读接口 77 键 - 5 个纯服务端键 + 4 个前端索引键（回显直传，等式精确）
  P3  36 键 = core(19) | E[INTEGER](17) | IDENT_REL(8)（编辑重建，等式 0 残差）
  P4  26 键(ADD) 无任何身份键（记录尚不存在），且不走 E[type] 提交默认表
  P5  76-36 的 40 键可完整归类，其中 13 键是 E[String]-E[Integer] 专属
  P6  类型模板值精确命中：ADD 的 minLength/maxLength = f[String]；36 键的 min/max/defaultValue = E[Integer]

退出码：0 = 全部断言通过；1 = 有断言失败。
"""
import collections
import json
import pathlib
import re
import sys

REPO = pathlib.Path(r"<SEEYON_AGENT_ROOT>")
E1 = REPO / "docs/audit/entity-field-matrix/EVIDENCE-batch-contract-live.json"
E2 = REPO / "docs/audit/entity-field-matrix/EVIDENCE-batch-update-live.json"
# 优先读仓库内落地的资产段（可复现、不受 cache 24h 清理影响）；
# 缺失时回退到 cache 原 bundle，两者都不可用则显式失败，绝不静默给假结论。
ASSET = REPO / "docs/audit/entity-field-matrix/assets/bundle-type-default-tables.js.txt"
BUNDLE = pathlib.Path(r"<HERMES_HOME>/cache/scratch/src_redux_store_ts.14dc061e.js")

fails = []


def need(label, cond, extra=""):
    if not cond:
        fails.append(label)
    print(("PASS " if cond else "FAIL ") + label + ((" | " + str(extra)) if (not cond and extra) else ""))


def rows(ev):
    return [d for g in ev["request_full"]["variables"]["params0"] for d in g["attributeDtoList"]]


e1 = json.load(open(E1, encoding="utf-8"))
e2 = json.load(open(E2, encoding="utf-8"))
cr, ur = rows(e1), rows(e2)
allrows = cr + ur

# ---------- 0. 样本轮廓 ----------
need("0.1 两批共 30 条 DTO", len(allrows) == 30, len(allrows))
non76 = [(len(d), d.get("actionType"), d.get("name")) for d in allrows if len(d) != 76]
need("0.2 非 76 键只有 2 条", len(non76) == 2, non76)
need("0.3 26 键=ADD / 36 键=UPDATE，同为 b2IntField",
     sorted(n[0] for n in non76) == [26, 36]
     and {n[1] for n in non76} == {"ADD", "UPDATE"}
     and all(n[2] == "b2IntField" for n in non76), non76)

k76 = set([d for d in ur if len(d) == 76][0])
k36 = set([d for d in ur if len(d) == 36][0])
k26 = set([d for d in cr if d.get("actionType") == "ADD"][0])
core = set(allrows[0])
for d in allrows:
    core &= set(d)

need("0.4 28 条 76 键的键集完全一致",
     len({frozenset(d) for d in allrows if len(d) == 76}) == 1)
need("0.5 36 < 76 且 26 < 76", k36 < k76 and k26 < k76)
need("0.6 26 不是 36 的子集（ADD 与 UPDATE 精简档不同源）",
     not k26.issubset(k36), sorted(k26 - k36))

# ---------- P1 键数不是 dataType 的函数 ----------
cnt = collections.Counter((len(d), d.get("dataType")) for d in allrows)
per_type = collections.defaultdict(set)
for (n, dt) in cnt:
    per_type[dt].add(n)
multi = {dt: sorted(v) for dt, v in per_type.items() if len(v) > 1}
need("P1 * 同 dataType 下存在多档键数（键数不随 dataType 变）",
     set(multi) == {"INTEGER", "STRING"}, multi)
need("P1b INTEGER 同时出现 76 与 36", per_type["INTEGER"] == {36, 76}, sorted(per_type["INTEGER"]))
need("P1c STRING 同时出现 76 与 26", per_type["STRING"] == {26, 76}, sorted(per_type["STRING"]))

# ---------- P2 76 = 读对象 77 - 5 + 4（回显直传） ----------
resp = e2["b2IntField_dto_response"]["dto"]
resp_keys = set(resp)
need("P2a 响应端 77 键", len(resp_keys) == 77, len(resp_keys))
srv_only = resp_keys - k76      # 纯服务端键
fe_only = k76 - resp_keys       # 前端索引键
need("P2b 响应独有 = 5 个纯服务端键", srv_only == {
    "attribute4DtoFullName", "backupCode", "originalId", "ownerCode", "validate"}, sorted(srv_only))
need("P2c 请求独有 = 4 个前端索引键",
     fe_only == {"g_l_index", "index", "key", "parentKey"}, sorted(fe_only))
need("P2d * 76 == 77 - 5 + 4（等式精确）", 77 - len(srv_only) + len(fe_only) == len(k76),
     (77, len(srv_only), len(fe_only), len(k76)))

names1 = {d["name"]: d for d in cr}
names2 = {d["name"]: d for d in ur}
untouched_diff = {}
for n in set(names1) & set(names2):
    if n == "b2IntField":
        continue
    a, b = names1[n], names2[n]
    untouched_diff[n] = sorted({k for k in set(a) | set(b) if a.get(k) != b.get(k)})
need("P2e 14 个未编辑字段 E1->E2 仅 updateTime 变化（=回显，非重建）",
     all(v == ["updateTime"] for v in untouched_diff.values()),
     {k: v for k, v in untouched_diff.items() if v != ["updateTime"]})

# ---------- STATIC：从 bundle 反解默认表（优先仓库资产，保证可复现） ----------
if ASSET.exists():
    src = ASSET.read_text(encoding="utf-8", errors="replace")
    src_origin = "asset(repo)"
elif BUNDLE.exists():
    src = BUNDLE.read_text(encoding="utf-8", errors="replace")
    src_origin = "bundle(cache, fallback)"
else:
    raise SystemExit("bundle 源不可用：asset 与 cache 均缺失，拒绝在无源情况下出结论")
print(f"[src] {src_origin}")


def _block_after(anchor, span=40000):
    i = src.find(anchor)
    if i < 0:
        raise SystemExit("anchor not found: " + anchor)
    k = src.find("{", i)
    depth = 0
    for j in range(k, k + span):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[k:j + 1]
    raise SystemExit("block not closed: " + anchor)


def _type_entry(block, typekey):
    m = re.search(r"\[a\.%s\]:\{" % typekey, block)
    if not m:
        return None
    k = m.end() - 1
    depth = 0
    for j in range(k, len(block)):
        if block[j] == "{":
            depth += 1
        elif block[j] == "}":
            depth -= 1
            if depth == 0:
                return set(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*:", block[k:j + 1]))
    return None


E_BLK = _block_after('E={[a.String]:{dataType:"STRING"')
E_INT = _type_entry(E_BLK, "Integer")
E_STR = _type_entry(E_BLK, "String")
need("S1 E[Integer] 反解 17 键", E_INT is not None and len(E_INT) == 17, len(E_INT or []))
need("S2 E[String] 反解 23 键", E_STR is not None and len(E_STR) == 23, len(E_STR or []))

IDENT_REL = {"guid", "id", "relationApp", "relationCode", "relationEntity",
             "relationEntityCategory", "relationEntityName", "system"}

# ---------- P3 36 = core | E[Integer] | IDENT_REL ----------
need("P3a core = 19 键", len(core) == 19, len(core))
pred36 = core | E_INT | IDENT_REL
need("P3b * 36 == core | E[Integer] | IDENT_REL（0 残差）",
     k36 == pred36, {"missing": sorted(pred36 - k36), "extra": sorted(k36 - pred36)})

# ---------- P4 26(ADD) ----------
need("P4a 26(ADD) 不含任何身份/关系键", not (k26 & IDENT_REL), sorted(k26 & IDENT_REL))
need("P4b 36(UPDATE) 含全部 8 个身份/关系键", IDENT_REL <= k36, sorted(IDENT_REL - k36))
need("P4c 26 != core | E[String] | IDENT_REL（ADD 不走 E[type] 提交默认表）",
     k26 != (core | E_STR | IDENT_REL))

# ---------- P5 76-36 的 40 键完整归类 ----------
diff40 = k76 - k36
need("P5a 76-36 = 40 键", len(diff40) == 40, len(diff40))
only_str = E_STR - E_INT
need("P5b 36 与 (E[String]-E[Integer]) 交集为空（精简档不含字符串专属键）",
     not (k36 & only_str), sorted(k36 & only_str))
need("P5c 76 含全部 8 个字符串专属键",
     sorted(k76 & only_str) == sorted(only_str), {"missing": sorted(only_str - k76)})
need("P5d 40 键里 8 个是字符串/加密专属（=only_str 全量）",
     len(diff40 & only_str) == 8, len(diff40 & only_str))

# ---------- P6 类型默认值精确命中 ----------
F_BLK = _block_after('f={[a.String]:{defaultValue:p')
F_STR = _type_entry(F_BLK, "String")
need("S3 f[String] 表单默认表反解成功", F_STR is not None and len(F_STR) > 0, F_STR)
add = [d for d in cr if d.get("actionType") == "ADD"][0]
up36 = [d for d in ur if len(d) == 36][0]
need("P6a * ADD 的 minLength/maxLength == f[String] 默认 (0/50)",
     add.get("minLength") == 0 and add.get("maxLength") == 50,
     (add.get("minLength"), add.get("maxLength")))
need("P6b * 36 键的 min/max/defaultValue == E[Integer] 默认 (''/''/0)",
     up36.get("min") == "" and up36.get("max") == "" and up36.get("defaultValue") == 0,
     (up36.get("min"), up36.get("max"), up36.get("defaultValue")))

# ---------- P7 全 14 张类型表：3.4 的类型判别力边界（auditor 12:06 口径 ②a/②b/③） ----------
TYPES = ["String", "MultilineString", "Integer", "BigInteger", "Decimal", "Currency",
         "Date", "Time", "DateTime", "Boolean", "Enum", "CtpEnum", "Entity", "Attachment"]
E_TABS = {t: _type_entry(E_BLK, t) for t in TYPES}
missing_tabs = [t for t in TYPES if E_TABS[t] is None]
need("P7a 14 张类型默认表全部反解成功", not missing_tabs, missing_tabs)

base = core | IDENT_REL
need("P7b base = core ∪ IDENT_REL = 27 且 base ⊆ k36", len(base) == 27 and base <= k36,
     {"n": len(base), "漏": sorted(base - k36)})

# 口径 ②a：接受集 = 键集相等（不是键数相等）的类型
accept = [t for t in TYPES if E_TABS[t] is not None and (base | E_TABS[t]) == k36]
need("P7c ★ 3.4 无类型判别力：base∪E[t]==k36 对 5 个类型同时成立 5/14",
     accept == ["Integer", "BigInteger", "Date", "Time", "DateTime"], accept)

# 口径 ②b：MultilineString 是陷阱——键数 36 但键集不等，必须比键集
ms = E_TABS["MultilineString"]
need("P7d ★ MultilineString 键数=36 但键集≠k36（陷阱：只看键数会误判）",
     len(base | ms) == 36 and (base | ms) != k36,
     {"union_n": len(base | ms), "equal": (base | ms) == k36, "E-k36": sorted(ms - k36)})

# 口径 ③：max/min 覆盖 7/14（STATIC 层），与「有值 / 可配」三层分开
has_mm = [t for t in TYPES if E_TABS[t] is not None and {"max", "min"} <= E_TABS[t]]
need("P7e ★ max/min 键覆盖 7/14 类型（非 INTEGER 专属）", len(has_mm) == 7, has_mm)

# 值域三层：STATIC 键存在 vs LIVE 有值 vs 可配置（当前 BLOCKED，本脚本不下结论）
up36_min = up36.get("min")
need("P7f 36 键 DTO 的 min/max 是空串（键存在 ≠ 有值）",
     up36_min == "" and up36.get("max") == "")

# ---------- 触发条件判别力 ----------
print("\n--- 触发条件判别力 ---")
print("同批其余 14 字段：键集 76 不变、仅 updateTime 变 => 回显直传")
print("b2IntField 自身键数 26(ADD) -> 36(UPDATE)")
print("判别力结论：")
print("  - 键数=dataType 的函数      已反证（P1：同类型多档键数）")
print("  - 76=读对象回显直传         已证（P2：等式精确 + 未编辑字段仅 updateTime 变）")
print("  - 36=按类型模板重建         已证（P3：代数 0 残差；P6b：默认值精确命中）")
print("  - n=1：无法把「dataType 变更」与「用户实际编辑了本字段」两个因素分离")
print("    => 触发条件的充分条件 UNVERIFIED；必要机制（模板重建）已证")

print()
if fails:
    print("GATE FAILED:", len(fails))
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("GATE PASS  (B4：键数来源代数 + 双默认表反解 + 判别力评估)")
