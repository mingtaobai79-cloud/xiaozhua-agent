# -*- coding: utf-8 -*-
"""校验 whitemt-pending-issues-repro-plan.md 是否覆盖 非待验收 全部 rid（各一次、无遗漏无多余）"""
import json
import re
import time
from pathlib import Path

OUT = Path(r"<XIAOZHUA_AGENT_ROOT>/docs/audit/evidence/feishu-base")
doc = (OUT / "whitemt-pending-issues-repro-plan.md").read_text(encoding="utf-8")
rec = json.loads((OUT / "records_decoded.json").read_text(encoding="utf-8"))
tbl = json.loads((OUT / "table_decoded.json").read_text(encoding="utf-8"))
fmap = tbl["fieldMap"]
fname = {fid: (f.get("name") or fid) for fid, f in fmap.items()}
opt = {}
for fid, f in fmap.items():
    for o in ((f.get("property") or {}).get("options") or []):
        opt[o.get("id")] = o.get("name")


def text_of(v):
    if v is None:
        return ""
    if isinstance(v, dict):
        if set(v.keys()) <= {"value", "modifiedUser", "modifiedTime"}:
            return text_of(v.get("value"))
        if "users" in v:
            return ", ".join((u.get("name") or "?") for u in v["users"])
        if "text" in v:
            return v["text"]
        return ""
    if isinstance(v, list):
        return "".join(text_of(i) for i in v)
    return opt.get(str(v), str(v))


expect = {}
for rid, r in rec["recordMap"].items():
    fields = r.get("fields") or r
    d = {fname.get(k, k): text_of(v) for k, v in fields.items()}
    if "operator-a" not in d.get("处理人", ""):
        continue
    st = d.get("状态", "?")
    if st == "待验收":
        continue
    expect[rid] = st

found = re.findall(r"^(?:###\s+[\d\-\.]+\.?\s+|\-\s+)(recv[A-Za-z0-9]+)", doc, flags=re.M)
from collections import Counter
cnt = Counter(found)
print(f"非待验收期望 {len(expect)} 条；文档中出现的 rid {len(cnt)} 个（总出现 {len(found)} 次）")
missing = [r for r in expect if r not in cnt]
extra = [r for r in cnt if r not in expect]
dup = [r for r, c in cnt.items() if c > 1]
print("遗漏:", missing or "无")
print("多余(不属非待验收):", extra or "无")
print("重复:", dup or "无")
if missing:
    for r in missing:
        print("   遗漏 rid:", r, expect[r])
print("状态分布(期望):", Counter(expect.values()).most_common())
