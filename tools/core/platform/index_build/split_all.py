# -*- coding: utf-8 -*-
"""全量拆分索引：按顶级域 + 按 starter + 按包。总和必须严格等于 24,618。"""
import json, io, os, collections

REPO = "C:/Users/白明涛/xiaozhua-agent"
SRC = f"{REPO}/docs/audit/artifacts/extension-surface-full/interfaces-full.json"
OUT = f"{REPO}/docs/audit/artifacts/index"
os.makedirs(OUT, exist_ok=True)

d = json.load(io.open(SRC, encoding="utf-8"))
cls = d["classes"]
midx = d["method_index"]
print(f"源: {len(cls):,} 类 / {len(midx):,} 方法名")

def build(fqset):
    """为一组类生成子索引"""
    sub_cls = {fq: cls[fq] for fq in fqset if fq in cls}
    # 方法名索引只保留属于这组类的
    own = set(sub_cls)
    sub_m = {}
    for mn, hits in midx.items():
        keep = [h for h in hits if h.split("#")[0] in own]
        if keep:
            sub_m[mn] = keep
    pkgs = collections.Counter()
    for fq in sub_cls:
        p = fq.split(".")
        pkgs[".".join(p[:-1])] += 1
    return {
        "classes": sub_cls,
        "method_index": sub_m,
        "packages": dict(pkgs),
        "stats": {"classes": len(sub_cls),
                  "methods": sum(len(c.get("methods") or []) for c in sub_cls.values()),
                  "packages": len(pkgs)},
    }

manifest = {"source_classes": len(cls), "splits": {}}

# ── A. 按顶级域（16 个，一个不漏）──
dom_keys = collections.Counter()
for fq in cls:
    p = fq.split(".")
    dom_keys[p[2] if len(p) >= 3 and p[0] == "com" and p[1] == "seeyon" else "_other"] += 1

dom_dir = os.path.join(OUT, "by-domain")
os.makedirs(dom_dir, exist_ok=True)
total_dom = 0

def dom_of(fq):
    """返回顶级域名。com.seeyon.MyMojo 这类三段类名，域就是类名本身。"""
    p = fq.split(".")
    if len(p) >= 3 and p[0] == "com" and p[1] == "seeyon":
        return p[2]
    return "_other"

def in_dom(fq, dom):
    """精确判断 fq 属于 dom，含 com.seeyon.X 本身是类的情况。"""
    return dom_of(fq) == dom

for dom in sorted(dom_keys, key=lambda k: -dom_keys[k]):
    fqset = [fq for fq in cls if in_dom(fq, dom)]
    sub = build(fqset)
    io.open(os.path.join(dom_dir, f"{dom}.json"), "w", encoding="utf-8").write(
        json.dumps(sub, ensure_ascii=False))
    total_dom += sub["stats"]["classes"]
    manifest["splits"][f"domain:{dom}"] = sub["stats"]
    print(f"  by-domain/{dom}.json{'':<{max(0,20-len(dom))}} {sub['stats']['classes']:>7,} 类 "
          f"{sub['stats']['methods']:>8,} 方法")

print(f"  → 顶级域合计 {total_dom:,} / {len(cls):,}")

# ── B. 按 starter（boot.starter 内部 79 个）──
st_keys = collections.Counter()
for fq in cls:
    p = fq.split(".")
    if fq.startswith("com.seeyon.boot.starter.") and len(p) >= 5:
        st_keys[p[4]] += 1
    elif fq.startswith("com.seeyon.boot.starter.") and len(p) == 4:
        st_keys["_root"] += 1

st_dir = os.path.join(OUT, "by-starter")
os.makedirs(st_dir, exist_ok=True)
total_st = 0

def st_of(fq):
    """返回 starter 名。com.seeyon.boot.starter.X 本身是类时，starter 名就是 X。"""
    p = fq.split(".")
    if len(p) >= 5 and fq.startswith("com.seeyon.boot.starter."):
        return p[4]
    return "_root"

for st in sorted(st_keys, key=lambda k: -st_keys[k]):
    fqset = [fq for fq in cls if fq.startswith("com.seeyon.boot.starter.") and st_of(fq) == st]
    sub = build(fqset)
    io.open(os.path.join(st_dir, f"{st}.json"), "w", encoding="utf-8").write(
        json.dumps(sub, ensure_ascii=False))
    total_st += sub["stats"]["classes"]
    manifest["splits"][f"starter:{st}"] = sub["stats"]
print(f"  by-starter/ {len(st_keys)} 个 ~ {total_st:,} 类")

# ── C. manifest ──
# 校验：顶级域总和 == 源；starter 总和 == boot.starter 类数
boot_st_total = sum(1 for fq in cls if fq.startswith("com.seeyon.boot.starter."))
assert total_dom == len(cls), f"顶级域漏了: {total_dom} != {len(cls)}"
assert total_st == boot_st_total, f"starter 漏了: {total_st} != {boot_st_total}"

manifest["checks"] = {
    "domain_sum_equals_source": total_dom == len(cls),
    "starter_sum_equals_boot_starter": total_st == boot_st_total,
    "boot_starter_total": boot_st_total,
}
io.open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8").write(
    json.dumps(manifest, ensure_ascii=False, indent=1))

print()
print(f"✓ 顶级域合计 {total_dom:,} == 源 {len(cls):,}")
print(f"✓ starter 合计 {total_st:,} == boot.starter {boot_st_total:,}")

# ── D. 生成可读目录树 ──
lines = []
lines.append("# 平台索引目录树（全量 · 可核对）")
lines.append("")
lines.append(f"源索引 {len(cls):,} 类 / {len(midx):,} 方法名 / 176 构件")
lines.append("")
lines.append("## A. 按顶级域（16 个，全量，合计 = 源）")
lines.append("")
lines.append("| 域 | 类数 | 方法数 | 包数 | 文件 |")
lines.append("|---|---:|---:|---:|---|")
for dom in sorted(dom_keys, key=lambda k: -dom_keys[k]):
    s = manifest["splits"][f"domain:{dom}"]
    lines.append(f"| `{dom}` | {s['classes']:,} | {s['methods']:,} | {s['packages']:,} | `by-domain/{dom}.json` |")
lines.append(f"| **合计** | **{total_dom:,}** | | | |")
lines.append("")
lines.append("## B. 按 boot.starter（79 个，合计 = boot.starter 全部）")
lines.append("")
lines.append("| starter | 类数 | 方法数 | 文件 |")
lines.append("|---|---:|---:|---|")
for st in sorted(st_keys, key=lambda k: -st_keys[k]):
    s = manifest["splits"][f"starter:{st}"]
    lines.append(f"| `{st}` | {s['classes']:,} | {s['methods']:,} | `by-starter/{st}.json` |")
lines.append(f"| **合计** | **{total_st:,}** | | |")
lines.append("")

io.open(os.path.join(OUT, "TREE.md"), "w", encoding="utf-8").write("\n".join(lines))
print(f"✓ 目录树 → {OUT}/TREE.md")