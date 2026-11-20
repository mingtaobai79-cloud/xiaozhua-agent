# -*- coding: utf-8 -*-
"""索引拆分自证（四种拆法）。退出码非 0 = 有失败。"""
import json, io, os, sys, collections, re

REPO = "C:/Users/白明涛/xiaozhua-agent"
IDX = f"{REPO}/docs/audit/artifacts/extension-surface-full/interfaces-full.json"
OUT = f"{REPO}/docs/audit/artifacts/index"

fail = []
def chk(c, m):
    print(f"  {'OK  ' if c else 'FAIL'} {m}")
    if not c:
        fail.append(m)

src = json.load(io.open(IDX, encoding="utf-8"))
S = set(src["classes"])
print(f"源: {len(S):,} 类\n")

def scan(sub):
    d = os.path.join(OUT, sub)
    if not os.path.isdir(d):
        return []
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))

def load(sub, name):
    return json.load(io.open(os.path.join(OUT, sub, name + ".json"), encoding="utf-8"))

print("=" * 80); print("A. by-domain"); print("=" * 80)
doms = scan("by-domain")
seen = set(); tot = 0; overlap = 0
for d in doms:
    cs = set(load("by-domain", d)["classes"])
    overlap += len(seen & cs); seen |= cs; tot += len(cs)
chk(len(doms) == 16, f"文件 16（实测 {len(doms)}）")
chk(overlap == 0, f"域间无重复（重复 {overlap}）")
chk(tot == len(S), f"类数合计 {tot:,} == 源 {len(S):,}")
chk(seen == S, "并集 == 源")
print()

print("=" * 80); print("B. by-sub"); print("=" * 80)
BIG = {"cip", "bpm", "udc", "cdp", "ctp", "app", "organization", "portal", "m5"}
big_cls = {fq for fq in S if fq.split(".")[2] in BIG and len(fq.split(".")) >= 3}
subs = scan("by-sub")
sseen = set(); stot = 0; sover = 0
for s in subs:
    cs = set(load("by-sub", s)["classes"])
    sover += len(sseen & cs); sseen |= cs; stot += len(cs)
chk(sover == 0, f"子域间无重复（重复 {sover}）")
chk(stot == len(big_cls), f"子域合计 {stot:,} == 9 大域 {len(big_cls):,}")
chk(sseen == big_cls, "子域并集 == 9 大域全部")
print(f"  {len(subs)} 个子域")
print()

print("=" * 80); print("C. by-starter"); print("=" * 80)
boot_st = {fq for fq in S if fq.startswith("com.seeyon.boot.starter.")}
sts = scan("by-starter")
tseen = set(); ttot = 0
for s in sts:
    cs = set(load("by-starter", s)["classes"])
    tseen |= cs; ttot += len(cs)
chk(len(sts) == 79, f"文件 79（实测 {len(sts)}）")
chk(ttot == len(boot_st), f"合计 {ttot:,} == boot.starter {len(boot_st):,}")
chk(tseen == boot_st, "并集 == boot.starter 全部")
print()

print("=" * 80); print("D. by-app"); print("=" * 80)
aps = scan("by-app")
aseen = set(); atot = 0
for a in aps:
    cs = set(load("by-app", a)["classes"])
    aseen |= cs; atot += len(cs)
chk(len(aps) == 115, f"文件 115（实测 {len(aps)}）")
chk(atot == len(S), f"合计 {atot:,} == 源 {len(S):,}")
chk(aseen == S, "并集 == 源")
print()

print("=" * 80); print("E. 文档完整性"); print("=" * 80)
pk = collections.Counter()
for fq in S:
    pk[".".join(fq.split(".")[:-1])] += 1
txt = io.open(f"{OUT}/PACKAGES.md", encoding="utf-8").read()
rows = re.findall(r"^\| \d+ \| `([^`]+)` \| (\d+) \|", txt, re.M)
chk(len(rows) == len(pk), f"PACKAGES 行 {len(rows):,} == 包数 {len(pk):,}")
chk(sum(int(n) for _, n in rows) == len(S), "PACKAGES 类数合计 == 源")

tree = io.open(f"{OUT}/TREE.md", encoding="utf-8").read()
chk(tree.count("## A. 按顶级域") == 1, "TREE 只有一段 A")
chk(tree.count("## D. 按应用") == 1, "TREE 只有一段 D（无残留旧段）")
# 0 类分片必须只有「jar 内无 com.seeyon 类」的那几个，且已标注
zero_rows = re.findall(r"^\| `([^`]+)`  ⚠️空 \| 0 \|", tree, re.M)
KNOWN_EMPTY = {"bpm-ext-models", "jakarta.persistence", "mobile-message-client"}
chk(set(zero_rows) == KNOWN_EMPTY,
    f"0 类分片仅限已知空 jar（实测 {len(zero_rows)} 个: {sorted(zero_rows)}）")
chk("⚠️ 空分片" in tree, "TREE 已标注空分片原因")
for expect in ("1,103", "3,415", "481", "439", "1,069"):
    chk(expect in tree, f"TREE 含关键类数 {expect}")
print()

print("=" * 80)
print(f"结论: {'全部通过 ✓' if not fail else str(len(fail)) + ' 项失败'}")
for f in fail:
    print(f"  ✗ {f}")
print("=" * 80)
sys.exit(1 if fail else 0)