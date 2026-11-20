# -*- coding: utf-8 -*-
"""由 db-test2.json 生成人类可读的表清单文档（按域分组）。"""
import json, io, os, sys

REPO = r"C:/Users/白明涛/xiaozhua-agent"
T = os.path.join(REPO, "docs/audit/artifacts/tables")
ENV = sys.argv[1] if len(sys.argv) > 1 else "test2"

rows = json.load(io.open(os.path.join(T, f"db-{ENV}.json"), encoding="utf-8"))
by = {}
for r in rows:
    by.setdefault(r["domain"], []).append(r)

L = [f"# 平台真实表清单（{ENV}）", "",
     f"> 来源：`information_schema.tables`，环境 `{ENV}`，{len(rows)} 张表。",
     "> 证据等级：`LIVE`（直连库读取，非推断）。",
     "> 只读清单，不含业务数据。", ""]

tot = 0
for dom in sorted(by, key=lambda d: -len(by[d])):
    rs = sorted(by[dom], key=lambda r: r["table_name"])
    schema = rs[0]["schema"]
    tot += len(rs)
    L.append(f"## {dom}  （schema `{schema}`，{len(rs)} 张）")
    L.append("")
    L.append("| 表名 | 注释 | 行数(估算) |")
    L.append("|---|---|---:|")
    for r in rs:
        cm = (r.get("table_comment") or "").replace("|", "\\|").strip()
        L.append(f"| `{r['table_name']}` | {cm} | {r.get('table_rows') or 0} |")
    L.append("")

L.insert(4, f"合计 **{tot}** 张，分布在 **{len(by)}** 个域。\n")
p = os.path.join(T, f"DB-TABLES-{ENV}.md")
io.open(p, "w", encoding="utf-8").write("\n".join(L))
print(f"→ {p}  ({tot} 张 / {len(by)} 域)")