#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
std_census.py —— 标品包系统性清点

输出：
  1. 每个包的类/接口/枚举/注解/方法总数
  2. 按包前缀归域的统计
  3. 每个域的核心接口（含方法数）
  4. 去重后的全量签名清单 -> signatures.json

用法：
  python std_census.py                      # 全量统计打印
  python std_census.py --json out.json      # 导出结构化
  python std_census.py --domain organization # 单域详情
"""
import os, re, json, sys, argparse
from collections import defaultdict

BASE = r"D:/software/hermes/cache/scratch/std-src"

# 类型统计
TYPE_PATTERNS = [
    ("interface", re.compile(r"^\s*public\s+interface\s+(\w+)", re.M)),
    ("enum",      re.compile(r"^\s*public\s+enum\s+(\w+)", re.M)),
    ("annotation",re.compile(r"^\s*public\s+@interface\s+(\w+)", re.M)),
    ("class",     re.compile(r"^\s*public\s+(?:abstract\s+|final\s+)?class\s+(\w+)", re.M)),
]

METHOD_RE = re.compile(
    r"^\s+(?:default\s+|public\s+|protected\s+|private\s+|static\s+|final\s+|abstract\s+)*"
    r"(?:(?:Single|List|Page)Response<[^>]*>|[\w<>\[\],\.\s\?]+?)\s+(\w+)\s*\(([^)]*)\)\s*[;{]",
    re.M)

NOT_METHODS = {"if","for","while","switch","catch","try","synchronized","return","new","else"}


def scan_file(path):
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return None
    pkg_m = re.search(r"^\s*package\s+([\w\.]+);", src, re.M)
    pkg = pkg_m.group(1) if pkg_m else ""

    kind, name = "unknown", os.path.basename(path)[:-5]
    for k, pat in TYPE_PATTERNS:
        m = pat.search(src)
        if m:
            kind, name = k, m.group(1)
            break

    methods = []
    for m in METHOD_RE.finditer(src):
        n = m.group(1)
        if n in NOT_METHODS:
            continue
        args = re.sub(r"\s+", " ", m.group(2)).strip()
        methods.append({"name": n, "args": args})

    # 去重（同名保留最长参数版本）
    seen, dedup = {}, []
    for me in methods:
        prev = seen.get(me["name"])
        if prev is None:
            seen[me["name"]] = me
            dedup.append(me)
        elif len(me["args"]) > len(prev["args"]):
            dedup[dedup.index(prev)] = me
            seen[me["name"]] = me

    return {"pkg": pkg, "kind": kind, "name": name, "methods": dedup, "path": path}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--domain")
    args = ap.parse_args()

    pkgs = sorted(d for d in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, d)))

    all_types = []
    pkg_stats = {}

    for p in pkgs:
        pdir = os.path.join(BASE, p)
        cnt = defaultdict(int)
        mcnt = 0
        for dp, _, fns in os.walk(pdir):
            for f in fns:
                if not f.endswith(".java"):
                    continue
                info = scan_file(os.path.join(dp, f))
                if not info:
                    continue
                cnt[info["kind"]] += 1
                mcnt += len(info["methods"])
                info["jar"] = p
                all_types.append(info)
        pkg_stats[p] = {
            "class": cnt["class"], "interface": cnt["interface"],
            "enum": cnt["enum"], "annotation": cnt["annotation"],
            "unknown": cnt["unknown"], "methods": mcnt,
            "total": sum(cnt.values()),
        }

    grand = {k: sum(v[k] for v in pkg_stats.values()) for k in ("class","interface","enum","annotation","unknown","methods","total")}

    if args.domain:
        rows = [t for t in all_types if t["jar"] == args.domain]
        rows.sort(key=lambda x: -len(x["methods"]))
        print(f"=== {args.domain}  {len(rows)} 类型 ===")
        for r in rows:
            if r["kind"] in ("interface", "class") and len(r["methods"]) >= 5:
                print(f"\n[{r['kind']}] {r['name']}  ({len(r['methods'])} 方法)")
                print(f"    {r['pkg']}")
                for m in r["methods"][:15]:
                    print(f"      {m['name']}({m['args'][:70]})")
        return

    print("=" * 86)
    print("标品包系统清点")
    print("=" * 86)
    print(f"{'包':<30}{'类':>6}{'接口':>6}{'枚举':>6}{'注解':>6}{'方法':>8}{'合计':>7}")
    print("-" * 86)
    for p, s in sorted(pkg_stats.items(), key=lambda x: -x[1]["total"]):
        print(f"{p:<30}{s['class']:>6}{s['interface']:>6}{s['enum']:>6}"
              f"{s['annotation']:>6}{s['methods']:>8}{s['total']:>7}")
    print("-" * 86)
    print(f"{'合计':<30}{grand['class']:>6}{grand['interface']:>6}{grand['enum']:>6}"
          f"{grand['annotation']:>6}{grand['methods']:>8}{grand['total']:>7}")

    # 接口 top
    ifaces = sorted([t for t in all_types if t["kind"] == "interface"], key=lambda x: -len(x["methods"]))
    print("\n" + "=" * 86)
    print("方法数 Top 30 接口")
    print("=" * 86)
    for r in ifaces[:30]:
        print(f"  {len(r['methods']):>4}  {r['name']:<42} {r['jar']}")

    # 去重同名类
    name_dup = defaultdict(list)
    for t in all_types:
        if t["kind"] in ("class", "interface"):
            name_dup[t["name"]].append(t["jar"])
    dups = {k: v for k, v in name_dup.items() if len(v) > 1}
    print(f"\n跨包同名类型: {len(dups)} 个")
    for k, v in list(sorted(dups.items()))[:15]:
        print(f"  {k:<40} {' / '.join(sorted(set(v)))}")

    print(f"\n去重后唯一类型名: {len(name_dup)}")

    if args.json:
        out = {
            "generated_at": "2026-11-17",
            "source": BASE,
            "pkg_stats": pkg_stats,
            "grand_total": grand,
            "types": [{k: t[k] for k in ("jar","pkg","kind","name","methods")} for t in all_types],
        }
        json.dump(out, open(args.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n导出: {args.json}")


if __name__ == "__main__":
    main()