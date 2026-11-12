#!/usr/bin/env python3
"""审计 standard-product 事实格：结构完整性、数字一致性、过期陈述、交叉引用有效性。

只报告，不改文件。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path("<XIAOZHUA_AGENT_ROOT>")
FD = ROOT / "core/facts/standard-product"
ART = ROOT / "docs/audit/artifacts"

SECTIONS = ["## 1. Capability", "## 2. Version", "## 3. Input", "## 4. Required",
            "## 5. Execution", "## 6. Side Effects", "## 7. Known Constraints",
            "## 8. Evidence", "## 9. Verified"]

# 已作废的数字（重抽/补齐前的旧值）
STALE = ["9652", "98328", "37998", "1017 个接口", "752 个", "1482", "76 个有完整 props",
         "2.2 MB", "55130", "55065251", "2539", "2547", "2551", "2575"]


def main() -> int:
    files = sorted(FD.glob("*.md"))
    print(f"检查 {len(files)} 个格子\n")

    problems: list[tuple[str, str]] = []

    for f in files:
        t = f.read_text(encoding="utf-8", errors="replace")
        # 1. 九段结构
        missing = [s for s in SECTIONS if s not in t]
        if missing:
            problems.append((f.name, f"缺段落 {', '.join(missing)}"))
        # 2. 过期数字
        for s in STALE:
            if s in t:
                # 找出上下文
                for m in re.finditer(re.escape(s), t):
                    ctx = t[max(0, m.start() - 30):m.end() + 20].replace("\n", " ")
                    problems.append((f.name, f"过期数字 {s!r}：…{ctx}…"))
                    break
        # 3. 交叉引用的文件是否存在
        for m in re.finditer(r"`([a-z0-9-]+\.md)`", t):
            ref = m.group(1)
            if not (FD / ref).exists() and not (ROOT / "core/facts" / ref).exists():
                if not (ROOT / "docs").rglob(ref):
                    problems.append((f.name, f"引用不存在的文件 {ref}"))

    # 4. 数字一致性：产物实测 vs 格子声明
    ip = ART / "extension-surface-20261029/interfaces.json"
    if ip.exists():
        d = json.loads(ip.read_text(encoding="utf-8"))
        cs = d["classes"]
        n_cls, n_m = len(cs), sum(len(c["methods"]) for c in cs.values())
        ifaces = {fq: c for fq, c in cs.items() if c.get("kind") == "interface"}
        anno = [fq for fq, c in ifaces.items()
                if any("java.lang.annotation.Annotation" in str(x) for x in (c.get("extends") or []))]
        real = len(ifaces) - len(anno)
        print(f"interfaces.json 实测：{len(d['sources'])} 构件 / {n_cls} 类 / {n_m} 方法 / "
              f"{len(ifaces)} 接口（{len(anno)} 注解，真接口 {real}）")
        for f in files:
            t = f.read_text(encoding="utf-8", errors="replace")
            if "类 /" in t and "方法" in t:
                m = re.search(r"(\d{4,5}) 类 ?/ ?(\d{5,6}) 方法", t)
                if m:
                    a, b = int(m.group(1)), int(m.group(2))
                    if (a, b) != (n_cls, n_m):
                        problems.append((f.name, f"类/方法数声明 {a}/{b}，实测 {n_cls}/{n_m}"))

    sp = ART / "frontend-surface-20261102/signatures.json"
    if sp.exists():
        sd = json.loads(sp.read_text(encoding="utf-8"))
        pk = sd["sources"]["frontend"]["packages"]
        comps = [i for p in pk.values() for i in (p.get("components") or {}).values()]
        withp = [c for c in comps if c.get("props")]
        npt = sum(len(p.get("props_types") or {}) for p in pk.values())
        print(f"signatures.json 实测：{len(pk)} 包 / {len(comps)} 组件 / {len(withp)} 有 props / "
              f"{npt} props 类型")
        for f in files:
            t = f.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r"(\d{2,3}) 个有完整 props", t):
                if int(m.group(1)) != len(withp):
                    problems.append((f.name, f"组件 props 数声明 {m.group(1)}，实测 {len(withp)}"))
            for m in re.finditer(r"(\d{3,4}) 个 props 类型", t):
                if int(m.group(1)) != npt:
                    problems.append((f.name, f"props 类型数声明 {m.group(1)}，实测 {npt}"))

        # 5. 产物里没有的组件被点名（防止写错名字）
        all_names = {c for p in pk.values() for c in (p.get("components") or {})}
        fact = FD / "frontend-component-signatures.md"
        if fact.exists():
            t = fact.read_text(encoding="utf-8", errors="replace")
            named = set(re.findall(r"\|\s*`@seeyon/[a-z0-9-]+`\s*\|\s*`([A-Za-z_][\w]*)`", t))
            for n in named - all_names:
                problems.append((fact.name, f"点名组件 {n} 不在签名产物里"))

    print(f"\n问题 {len(problems)} 条：")
    cur = None
    for name, msg in problems:
        if name != cur:
            print(f"\n[{name}]")
            cur = name
        print(f"  - {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
