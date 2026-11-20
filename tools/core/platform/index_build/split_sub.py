# -*- coding: utf-8 -*-
"""二级拆分：大域内部的子域各成一文件（事项/用户中心/连接器等）。

com.seeyon.ctp.affair     → by-sub/ctp-affair.json
com.seeyon.cip.connector  → by-sub/cip-connector.json
com.seeyon.boot.starter.X → by-sub/boot-starter-X.json（与 by-starter 重复，跳过）
"""
import json, io, os, collections

REPO = "C:/Users/白明涛/xiaozhua-agent"
SRC = f"{REPO}/docs/audit/artifacts/extension-surface-full/interfaces-full.json"
OUT = f"{REPO}/docs/audit/artifacts/index/by-sub"
os.makedirs(OUT, exist_ok=True)

d = json.load(io.open(SRC, encoding="utf-8"))
cls = d["classes"]
midx = d["method_index"]

# 只对大域做二级拆分（类数 >= 400 的顶级域，boot 走 by-starter 不重复）
BIG = {"cip", "bpm", "udc", "cdp", "ctp", "app", "organization", "portal", "m5"}

def build(fqset):
    sub = {fq: cls[fq] for fq in fqset}
    own = set(sub)
    subm = {}
    for mn, hits in midx.items():
        keep = [h for h in hits if h.split("#")[0] in own]
        if keep: subm[mn] = keep
    pk = collections.Counter(".".join(fq.split(".")[:-1]) for fq in sub)
    return {"classes": sub, "method_index": subm, "packages": dict(pk),
            "stats": {"classes": len(sub),
                      "methods": sum(len(c.get("methods") or []) for c in sub.values()),
                      "packages": len(pk)}}

# 收集 (域, 子域) 组合
combos = collections.Counter()
for fq in cls:
    p = fq.split(".")
    if len(p) >= 4 and p[0] == "com" and p[1] == "seeyon" and p[2] in BIG:
        combos[(p[2], p[3])] += 1

total = 0
rows = []
for (dom, sub), n in sorted(combos.items(), key=lambda kv: -kv[1]):
    fqset = [fq for fq in cls
             if fq.startswith(f"com.seeyon.{dom}.{sub}.") or fq == f"com.seeyon.{dom}.{sub}"]
    s = build(fqset)
    name = f"{dom}__{sub}"
    io.open(os.path.join(OUT, f"{name}.json"), "w", encoding="utf-8").write(
        json.dumps(s, ensure_ascii=False))
    total += s["stats"]["classes"]
    rows.append((dom, sub, s["stats"]["classes"], s["stats"]["methods"]))

print(f"二级拆分 {len(rows)} 个文件，覆盖 {total:,} 类（大域共 "
      f"{sum(1 for fq in cls if fq.split('.')[2] in BIG and len(fq.split('.'))>=3):,} 类）")

# ── SUB.md ──
L = ["# 二级拆分（大域内部）", "",
     f"{len(rows)} 个子域 · 覆盖 {total:,} 类", "",
     "| 域 | 子域 | 类数 | 方法数 | 文件 |", "|---|---|---:|---:|---|"]
for dom, sub, n, m in rows:
    L.append(f"| `{dom}` | `{sub}` | {n:,} | {m:,} | `by-sub/{dom}__{sub}.json` |")
io.open(f"{REPO}/docs/audit/artifacts/index/SUB.md", "w", encoding="utf-8").write("\n".join(L))
print(f"→ {OUT}/../SUB.md")

# ── 打印用户点名的几个 ──
print()
print("你点名的，逐一对应到文件：")
NAMED = [("ctp", "affair", "事项"), ("cip", "connector", "连接器"),
         ("ctp", "user", "用户中心"), ("ctp", "message", "消息"),
         ("udc", "microflow", "微流程"), ("udc", "dataflow", "数据流"),
         ("cip", "capability", "集成能力"), ("cdp", "bi", "BI 报表"),
         ("bpm", "detection", "流程检测")]
for dom, sub, label in NAMED:
    hit = [r for r in rows if r[0] == dom and r[1] == sub]
    if hit:
        print(f"  {label:<10} {dom}.{sub:<14} {hit[0][2]:>6,} 类 → by-sub/{dom}__{sub}.json")