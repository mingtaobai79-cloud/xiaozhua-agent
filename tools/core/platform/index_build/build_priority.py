# -*- coding: utf-8 -*-
"""建立「权威类优先级」表：解决 787 组重名类。

规则（按优先级）：
  1. com.seeyon.boot.* 是平台内核 → 权威
  2. com.seeyon.{domain}.api.*  是标品契约 → 权威
  3. com.seeyon.udc.* 是 UDC 自身 → 权威
  4. com.seeyon.ai.core.* / license / 各应用内部同名类 → 次级（应用私有副本）

输出 priority.json：{短类名: [按权威度排序的全名]}
"""
import json, io, collections, re

REPO = "C:/Users/白明涛/xiaozhua-agent"
idx = json.load(io.open(f"{REPO}/docs/audit/artifacts/extension-surface-full/interfaces-full.json", encoding="utf-8"))
cls = idx["classes"]

def score(fq):
    """分数越低越权威"""
    s = 100
    if fq.startswith("com.seeyon.boot.core") or fq.startswith("com.seeyon.boot.util"):
        s = 0                              # 平台内核工具
    elif fq.startswith("com.seeyon.boot.transport"):
        s = 1                              # 传输协议
    elif fq.startswith("com.seeyon.boot."):
        s = 5                              # 其他 boot
    elif re.match(r"^com\.seeyon\.\w+\.api\.", fq):
        s = 10                             # 标品 API 契约
    elif re.match(r"^com\.seeyon\.udc\.", fq):
        s = 15                             # UDC 自身
    elif re.match(r"^com\.seeyon\.(organization|bpm|ctp|portal|m5|cip|cdp|app)\..*\.api\.", fq):
        s = 20
    elif ".core.common." in fq:
        s = 60                             # ai.core 的通用副本 → 低优先
    elif ".license." in fq:
        s = 70
    elif fq.startswith("com.seeyon.ai."):
        s = 50
    # 同分时：包路径短的优先（更像基础类）
    return (s, fq.count("."), len(fq))

by_short = collections.defaultdict(list)
for fq in cls:
    by_short[fq.split(".")[-1]].append(fq)

out = {}
dups = 0
for short, fqs in by_short.items():
    if len(fqs) == 1:
        out[short] = {"primary": fqs[0], "all": fqs, "conflict": False}
    else:
        dups += 1
        ranked = sorted(fqs, key=score)
        out[short] = {"primary": ranked[0], "all": ranked, "conflict": True}

P = "D:/software/hermes/cache/scratch/rebuild/priority.json"
io.open(P, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))

print(f"类名 {len(out):,} 个，其中重名 {dups} 组")
print()
print("=== 关键重名类，权威排序 ===")
for name in ["JsonUtils", "StringUtils", "FileUtils", "GenericService", "BeanUtils", "DateUtils"]:
    if name not in out: continue
    e = out[name]
    if not e["conflict"]:
        print(f"\n  {name}: 唯一")
        print(f"    {e['primary']}")
        continue
    print(f"\n  {name}: {len(e['all'])} 个")
    for i, fq in enumerate(e["all"]):
        mark = "★primary" if i == 0 else "       "
        print(f"    {mark} {fq}")

print()
print(f"→ {P}")