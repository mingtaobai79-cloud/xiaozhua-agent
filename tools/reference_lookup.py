#!/usr/bin/env python3
"""离线查「自定义微流程能调什么 / 自定义页面能用什么组件」。

两个索引：

    docs/audit/reference/svc-app-service.txt.gz   833 个 AppService / 10176 行 / 带依赖 jar
    docs/audit/reference/ui-components.txt.gz     515 个前端组件 / 属性 / 包版本

用法：

    python tools/reference_lookup.py svc MigrationPlanAppService
    python tools/reference_lookup.py svc --dep app-udc-facade
    python tools/reference_lookup.py ui Button
    python tools/reference_lookup.py ui --pkg biz-org-tree
    python tools/reference_lookup.py ui Table --json

判据说明（别把索引当权威类型）：
  · svc 的参数类型来自 javap，可信；泛型内层若被擦除，只显示外层。
  · ui 的属性名来自 .d.ts，可信；标 any 的是组件 `: any` 透传，类型不可信。
  · ui 组件若继承 antd，属性多在 antd 侧，本索引只列包内显式声明的那批。
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "docs" / "audit" / "reference"
SVC = REF / "svc-app-service.txt.gz"
UI = REF / "ui-components.txt.gz"


def _load(path: Path) -> list[list[str]]:
    if not path.exists():
        print(f"[x] 缺索引 {path}\n    见 docs/audit/REGENERATE-EVIDENCE.md", file=sys.stderr)
        raise SystemExit(2)
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [line.split("\t") for line in f.read().splitlines() if line]


def cmd_svc(a) -> int:
    rows = _load(SVC)
    q = (a.pattern or "").lower()
    dep = (a.dep or "").lower()
    classes: dict[str, dict] = {}
    for row in rows:
        head = row[0]
        jar = row[1] if len(row) > 1 else ""
        if dep and dep not in jar.lower():
            continue
        if q and q not in head.lower():
            continue
        if "#" in head:
            fq, rest = head.split("#", 1)
            name = rest.split("(", 1)[0]
            args = rest.split("(", 1)[1].rsplit("):", 1)[0] if "(" in rest else ""
            ret = rest.rsplit("):", 1)[1] if "):" in rest else ""
            classes.setdefault(fq, {"class": fq, "dep": jar, "methods": []})
            classes[fq]["methods"].append({"method": name, "args": args, "returns": ret})
        else:
            classes.setdefault(head, {"class": head, "dep": jar, "methods": []})
    picked = sorted(classes.values(), key=lambda c: c["class"])[: a.limit]
    if a.json:
        print(json.dumps(picked, ensure_ascii=False, indent=1))
        return 0 if picked else 1
    if not picked:
        print("无命中。换个片段，或用 --dep 只按构件看（如 --dep udc-facade）。")
        return 1
    for c in picked:
        print(f"{c['class']}   [{c['dep']}]")
        for m in c["methods"]:
            print(f"    {m['method']}({m['args']}) : {m['returns']}")
    if len(classes) > len(picked):
        print(f"\n…共 {len(classes)} 个服务命中，只显示 {len(picked)} 个（--limit）")
    return 0


def cmd_ui(a) -> int:
    rows = _load(UI)
    q = (a.pattern or "").lower()
    pkg = (a.pkg or "").lower()
    comps: dict[tuple[str, str], dict] = defaultdict(lambda: {"props": []})
    order: list[tuple[str, str]] = []
    for row in rows:
        p, ver, comp, prop, typ = (row + ["", "", "", "", ""])[:5]
        if pkg and pkg not in p.lower():
            continue
        if q and q not in comp.lower() and q not in p.lower():
            continue
        key = (comp, p)
        if key not in comps:
            order.append(key)
            comps[key] = {"component": comp, "pkg": p, "version": ver, "props": []}
        if prop and prop != "-":
            comps[key]["props"].append({"name": prop, "type": typ})
    def _rank(key):
        name = key[0].lower()
        return (0 if name == q else 1 if name.startswith(q) else 2, name)
    picked = [comps[k] for k in sorted(order, key=_rank)[: a.limit]]
    if a.json:
        print(json.dumps(picked, ensure_ascii=False, indent=1))
        return 0 if picked else 1
    if not picked:
        print("无命中。")
        return 1
    for c in picked:
        print(f"{c['component']}   {c['pkg']}@{c['version']}")
        if not c["props"]:
            print("    （无显式属性声明；antd 派生或 any 透传）")
        for p in c["props"]:
            print(f"    {p['name']}?: {p['type']}")
    if len(order) > len(picked):
        print(f"\n…共 {len(order)} 个组件命中，只显示 {len(picked)} 个（--limit）")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="查自定义微流程可用服务 / 自定义页面可用组件")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("svc", help="自定义微流程可调用的 AppService")
    s.add_argument("pattern", nargs="?", default="")
    s.add_argument("--dep", default="", help="按依赖构件过滤，如 app-udc-facade")
    s.add_argument("--limit", type=int, default=8)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_svc)

    u = sub.add_parser("ui", help="自定义页面可用前端组件")
    u.add_argument("pattern", nargs="?", default="")
    u.add_argument("--pkg", default="", help="按包过滤，如 biz-org-tree")
    u.add_argument("--limit", type=int, default=10)
    u.add_argument("--json", action="store_true")
    u.set_defaults(fn=cmd_ui)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
