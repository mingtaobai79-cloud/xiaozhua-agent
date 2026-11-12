#!/usr/bin/env python3
"""重生成 platform-package-capability-index.md §7.2「包级规模总表」为当前实测数据。"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path("<XIAOZHUA_AGENT_ROOT>")
FACT = ROOT / "core/facts/standard-product/platform-package-capability-index.md"
IP = ROOT / "docs/audit/artifacts/extension-surface-20261029/interfaces.json"


def is_anno(c: dict) -> bool:
    return any("java.lang.annotation.Annotation" in str(x) for x in (c.get("extends") or []))


def main() -> int:
    d = json.loads(IP.read_text(encoding="utf-8"))
    cs = d["classes"]
    sources = d["sources"]

    per: dict[str, dict] = {}
    for pkg in sources:
        per[pkg] = {"cls": 0, "iface": 0, "m": 0, "ver": "?"}
    for fq, c in cs.items():
        pkg = c.get("pkg")
        if pkg not in per:
            continue
        per[pkg]["cls"] += 1
        per[pkg]["m"] += len(c["methods"])
        if c.get("kind") == "interface" and not is_anno(c):
            per[pkg]["iface"] += 1
    for pkg, info in sources.items():
        jar = info.get("jar") or ""
        m = re.search(r"-(\d+\.\d+(?:\.\d+)*)\.jar$", jar)
        per[pkg]["ver"] = m.group(1) if m else "?"

    rows = sorted(per.items(), key=lambda x: (-x[1]["iface"], -x[1]["cls"]))
    lines = [f"### 7.2 包级规模总表（{len(rows)} 个构件，按接口数降序）", "",
             "| # | artifact | 版本 | 类 | 接口 | 方法 |", "|---|---|---|---|---|---|"]
    for i, (pkg, v) in enumerate(rows, 1):
        lines.append(f"| {i} | `{pkg}` | {v['ver']} | {v['cls']} | {v['iface']} | {v['m']} |")
    table = "\n".join(lines)

    t = FACT.read_text(encoding="utf-8")
    i = t.find("### 7.2 包级规模总表")
    j = t.find("### 7.3")
    if i == -1 or j == -1:
        print("ERR: 定位 §7.2 失败")
        return 5
    t = t[:i] + table + "\n\n" + t[j:]

    # 底部与标题的残留 84
    t = t.replace("| 84 个包的类/接口/方法数 | `VERIFIED_STATIC_BYTECODE`（84/84 抽取成功） |",
                  f"| {len(rows)} 个构件的类/接口/方法数 | `VERIFIED_STATIC_BYTECODE`（{len(rows)}/{len(rows)} 抽取成功） |")
    t = t.replace("（`_progress.jsonl` 84/84）", f"（`_progress.jsonl` {len(rows)}/{len(rows)}）")
    t = t.replace("同族构件跨版本混用是常态（udc-* 5.3.517 / boot-* 5.3.358 / 个别 5.3.260~5.3.429），"
                  "引用某个类前先确认它在你解析到的那个包里。",
                  "同族构件跨版本混用是常态（现基线：boot 族 5.3.600 / formula 族 5.3.603 / "
                  "udc 族 5.3.605 / udc-biz 5.3.517），逐构件版本见 `BASELINE.md`；"
                  "引用某个类前先确认它在你解析到的那个包里。")
    FACT.write_text(t, encoding="utf-8")

    tot_c = sum(v["cls"] for v in per.values())
    tot_i = sum(v["iface"] for v in per.values())
    tot_m = sum(v["m"] for v in per.values())
    print(f"重建 {len(rows)} 行：类 {tot_c} / 接口 {tot_i} / 方法 {tot_m}")
    print("前 5 行：")
    for pkg, v in rows[:5]:
        print(f"  {pkg:28s} {v['ver']:9s} 类 {v['cls']:4d} 接口 {v['iface']:3d} 方法 {v['m']:5d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
