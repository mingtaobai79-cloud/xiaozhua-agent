# -*- coding: utf-8 -*-
"""补两件事：
  1) by-app 拆分（115 个应用，用 apps.json 的构件清单）
  2) PACKAGES.md：全部包路径 + 类数（一个不省）
"""
import json, io, os, collections

REPO = "C:/Users/白明涛/xiaozhua-agent"
SRC = f"{REPO}/docs/audit/artifacts/extension-surface-full/interfaces-full.json"
OUT = f"{REPO}/docs/audit/artifacts/index"
apps = json.load(io.open("D:/software/hermes/cache/scratch/rebuild/apps.json", encoding="utf-8"))

d = json.load(io.open(SRC, encoding="utf-8"))
cls = d["classes"]
midx = d["method_index"]
# 类 -> 构件（直接读类的 pkg 字段，不从 source 反推）
src_of = {fq: c.get("pkg") for fq, c in cls.items()}
missing = [fq for fq in cls if not src_of.get(fq)]
print(f"类 {len(cls):,}，能定位到构件 {len(cls)-len(missing):,}，无归属 {len(missing)}")

# ── by-app ──
app_dir = os.path.join(OUT, "by-app")
os.makedirs(app_dir, exist_ok=True)

def build(fqset):
    sub = {fq: cls[fq] for fq in fqset}
    own = set(sub)
    subm = {}
    for mn, hits in midx.items():
        keep = [h for h in hits if h.split("#")[0] in own]
        if keep: subm[mn] = keep
    pk = collections.Counter()
    for fq in sub:
        pk[".".join(fq.split(".")[:-1])] += 1
    return {"classes": sub, "method_index": subm, "packages": dict(pk),
            "stats": {"classes": len(sub),
                      "methods": sum(len(c.get("methods") or []) for c in sub.values()),
                      "packages": len(pk)}}

total = 0
rows = []
for app, meta in sorted(apps.items()):
    arts = set(meta.get("artifacts") or [])
    fqset = [fq for fq, p in src_of.items() if p in arts]
    sub = build(fqset)
    io.open(os.path.join(app_dir, f"{app}.json"), "w", encoding="utf-8").write(
        json.dumps(sub, ensure_ascii=False))
    total += sub["stats"]["classes"]
    rows.append((app, sub["stats"]["classes"], sub["stats"]["methods"],
                 meta["n_artifacts"], sub["stats"]["packages"]))

print(f"by-app 合计 {total:,} 类（源 {len(cls):,}）")
print(f"  差额 {len(cls)-total:,} 类无 app 归属（构件不在 115 应用清单内）")

# ── PACKAGES.md：全部包 ──
pk = collections.Counter()
for fq in cls:
    pk[".".join(fq.split(".")[:-1])] += 1
print(f"包总数 {len(pk):,}")

lines = ["# 平台索引 · 全部包路径（一个不省）", "",
         f"源 {len(cls):,} 类 · **{len(pk):,} 个包** · 176 构件", "",
         "## 按包类数降序", "",
         "| # | 包 | 类数 | 构件 |", "|---|---|---:|---|"]
pkg_src = {}
for pkg, meta in d["sources"].items():
    for fq in meta.get("class_list") or []:
        pkg_src[".".join(fq.split(".")[:-1])] = pkg
for i, (p, n) in enumerate(pk.most_common(), 1):
    lines.append(f"| {i} | `{p}` | {n} | {pkg_src.get(p,'')} |")
io.open(os.path.join(OUT, "PACKAGES.md"), "w", encoding="utf-8").write("\n".join(lines))
print(f"→ {OUT}/PACKAGES.md")

# ── INDEX.md 总览 ──
man = json.load(io.open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))
L = ["# 平台索引总目录", "",
     f"源索引：**{len(cls):,} 类 / {len(midx):,} 方法名 / {len(pk):,} 包 / 176 构件 / 115 应用**", "",
     "## 三种拆法", "",
     "| 拆法 | 文件 | 数量 | 合计类数 | 用途 |",
     "|---|---|---:|---:|---|",
     f"| 按顶级域 | `by-domain/*.json` | 16 | {man['checks'].get('domain_sum_equals_source') and len(cls):,} | 跨应用找能力 |",
     f"| 按 starter | `by-starter/*.json` | 79 | {man['checks'].get('boot_starter_total'):,} | 标品组件（文件/枚举/元数据等） |",
     f"| 按应用 | `by-app/*.json` | {len(apps)} | {total:,} | 一个业务系统一个文件 |",
     "",
     "## 其它", "",
     f"- `TREE.md` —— 16 域 + 79 starter 明细表",
     f"- `PACKAGES.md` —— **全部 {len(pk):,} 个包**逐条列出",
     f"- `manifest.json` —— 校验用（各拆分统计 + checks）",
     "",
     "## 按需求选哪个", "",
     "| 你要找什么 | 用哪个 |",
     "|---|---|",
     "| 组织架构、人员、部门 | `by-domain/organization.json` |",
     "| 流程、节点、事件 | `by-domain/bpm.json` |",
     "| 协同事项、待办 | `by-domain/ctp.json` |",
     "| 连接器、集成、第三方对接 | `by-domain/cip.json` |",
     "| 数据展现、报表、BI | `by-domain/cdp.json` |",
     "| 低代码、自定义对象、微流程 | `by-domain/udc.json` |",
     "| 文件、枚举、元数据、数据源、mybatis | `by-starter/{file,enums,extmetadata,datasource,mybatis}.json` |",
     "| 某客户的完整应用 | `by-app/{应用名}.json` |",
     "| 不确定在哪个域 | `interfaces-full.json`（全量） |",
     ""]
io.open(os.path.join(OUT, "INDEX.md"), "w", encoding="utf-8").write("\n".join(L))
print(f"→ {OUT}/INDEX.md")

# ── 追加 by-app 到 TREE ──
T = io.open(os.path.join(OUT, "TREE.md"), encoding="utf-8").read()
add = ["", "## C. 按应用（115 个）", "",
       "| 应用 | 类数 | 方法数 | 构件数 | 包数 |", "|---|---:|---:|---:|---:|"]
for app, n, m, na, np_ in rows:
    add.append(f"| `{app}` | {n:,} | {m:,} | {na} | {np_:,} |")
add.append(f"| **合计** | **{total:,}** | | | |")
io.open(os.path.join(OUT, "TREE.md"), "w", encoding="utf-8").write(T + "\n".join(add))
print("→ TREE.md 追加 by-app 段")