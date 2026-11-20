# -*- coding: utf-8 -*-
"""平台索引查询（支持分片加载，命中即窄）。

用法：
  python query_platform.py scopes
  python query_platform.py find-class JsonUtils --scope boot
  python query_platform.py find-method send --scope bpm
  python query_platform.py methods com.seeyon.bpm.api.common.BpmAppService
  python query_platform.py search 库存 --scope udc
  python query_platform.py pkg com.seeyon.bpm.dto

scope 可用值：
  域      boot / bpm / cip / udc / ctp / cdp / app / organization / portal / m5 / ai ...
  子域    ctp__affair / cip__connector / ctp__user / udc__microflow ...
  starter file / enums / extmetadata / datasource / mybatis ...
  应用    udc / bpm / ctp-user ...
  全量    不给 --scope

分片越小加载越快，但漏查风险越大；找不到时会提示换全量。
"""
import json, io, sys, os, time, re, argparse
import collections

REPO = "C:/Users/白明涛/xiaozhua-agent"
BASE = os.path.join(REPO, "docs/audit/artifacts/index")
FULL = os.path.join(REPO, "docs/audit/artifacts/extension-surface-full/interfaces-full.json")
PRI_LOCAL = os.path.join(BASE, "priority.json")
PRI_SCRATCH = "D:/software/hermes/cache/scratch/rebuild/priority.json"

_c = {}


def _path(scope):
    if not scope or scope == "all":
        return FULL
    for sub in ("by-domain", "by-sub", "by-starter", "by-app"):
        p = os.path.join(BASE, sub, scope + ".json")
        if os.path.exists(p):
            return p
    return None


def load(scope=None):
    key = scope or "all"
    if key in _c:
        return _c[key]
    p = _path(scope)
    if not p:
        print(f"未知分片: {scope}（用 scopes 子命令查看）")
        sys.exit(2)
    t = time.perf_counter()
    d = json.load(io.open(p, encoding="utf-8"))
    d["_load_s"] = time.perf_counter() - t
    d["_scope"] = key
    _c[key] = d
    return d


def pri():
    if "pri" not in _c:
        p = PRI_LOCAL if os.path.exists(PRI_LOCAL) else PRI_SCRATCH
        _c["pri"] = json.load(io.open(p, encoding="utf-8"))
    return _c["pri"]


def sc(h):
    """权威度排序：分小者优先"""
    if h.startswith("com.seeyon.boot.transport"):
        return 0
    if h.startswith("com.seeyon.boot.core"):
        return 1
    if h.startswith("com.seeyon.boot.util"):
        return 2
    if h.startswith("com.seeyon.boot."):
        return 3
    if re.match(r"^com\.seeyon\.\w+\.api\.", h):
        return 4
    if ".appservice." in h.lower():
        return 5
    if ".domain.service." in h:
        return 7
    if ".util." in h or "Utils" in h:
        return 9
    return 6


def cmd_scopes(a):
    print(f"{'类型':<9} {'名称':<32} {'大小':>7}  文件")
    print("-" * 80)
    for sub, label in (("by-domain", "域"), ("by-sub", "子域"),
                       ("by-starter", "starter"), ("by-app", "应用")):
        d = os.path.join(BASE, sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".json"):
                sz = os.path.getsize(os.path.join(d, f))
                print(f"{label:<9} {f[:-5]:<32} {sz//1024:>6}K  {sub}/{f}")
    return 0


def cmd_find_class(a):
    d = load(a.scope)
    hits = [fq for fq in d["classes"] if fq.endswith("." + a.name) or fq == a.name]
    tag = f"scope={d['_scope']} 加载{d['_load_s']:.2f}s {len(d['classes']):,}类"
    if not hits:
        print(f"未找到 {a.name}  ({tag})")
        if a.scope:
            print("  → 可能不在本分片，试试不给 --scope")
        return 1
    print(f"{a.name}  命中 {len(hits)} 个  ({tag})")
    if len(hits) == 1:
        print(f"    {hits[0]}")
        return 0
    p = pri()
    ranked = p.get(a.name, {}).get("all") or []
    ranked = [x for x in ranked if x in hits] or sorted(hits, key=sc)
    for i, fq in enumerate(ranked):
        print(f"  {'★' if i == 0 else ' '} {fq}")
    print(f"\n  ✅ 推荐: {ranked[0]}")
    return 0


def cmd_find_method(a):
    d = load(a.scope)
    hits = d["method_index"].get(a.name, [])
    if a.domain:
        hits = [h for h in hits if a.domain.lower() in h.lower()]
    print(f"{a.name}()  scope={d['_scope']} 加载{d['_load_s']:.2f}s → {len(hits)} 处")
    for h in sorted(hits, key=sc)[:a.limit]:
        print(f"    {h}")
    if len(hits) > a.limit:
        print(f"    ... 还有 {len(hits)-a.limit} 处")
    if not hits and a.scope:
        print("    → 不在本分片，试试不给 --scope")
    return 0


def cmd_methods(a):
    d = load(a.scope)
    c = d["classes"].get(a.fqcn)
    if not c and d["_scope"] != "all":
        d = load("all")
        c = d["classes"].get(a.fqcn)
    if not c:
        print(f"类不存在: {a.fqcn}")
        short = a.fqcn.split(".")[-1]
        cand = [fq for fq in d["classes"] if fq.endswith("." + short)]
        if cand:
            print("  相近：")
            for x in cand[:5]:
                print(f"    {x}")
        return 1
    ms = [m for m in (c.get("methods") or []) if not m["name"].startswith("lambda$")]
    print(f"{a.fqcn}")
    print(f"  构件 {c.get('pkg')}  {c.get('kind')}  方法 {len(ms)} 个\n")
    for m in ms:
        args = ", ".join(x["type"].split(".")[-1] for x in m.get("args") or [])
        print(f"  {m['name']}({args})")
        print(f"      → {m['returns']}")
    if c.get("fields"):
        print(f"\n  字段 {len(c['fields'])}:")
        for f in c["fields"]:
            t = (f.get("type") or f.get("typename") or "").split(".")[-1]
            print(f"  {t} {f['name']}")
    return 0


def cmd_search(a):
    d = load(a.scope)
    pat = re.compile(a.kw, re.I)
    t = time.perf_counter()
    hits = [fq for fq in d["classes"] if pat.search(fq)]
    ms = (time.perf_counter() - t) * 1000
    print(f"搜「{a.kw}」scope={d['_scope']} → {len(hits)} 个  ({ms:.0f} ms)")
    for fq in hits[:a.limit]:
        print(f"    {fq}")
    if len(hits) > a.limit:
        print(f"    ... 还有 {len(hits)-a.limit} 个")
    return 0


def cmd_pkg(a):
    d = load(a.scope)
    hits = [fq for fq in d["classes"] if fq.startswith(a.prefix + ".")]
    print(f"包 {a.prefix}.* → {len(hits)} 类  (scope={d['_scope']})")
    for fq in sorted(hits)[:a.limit]:
        print(f"    {fq}")
    if len(hits) > a.limit:
        print(f"    ... 还有 {len(hits)-a.limit} 个")
    return 0


def cmd_app(a):
    """看一个关键词在索引里按 4 段包怎么分布"""
    d = load(a.scope)
    pat = a.name.lower()
    c = collections.Counter()
    for fq in d["classes"]:
        if pat in fq.lower():
            parts = fq.split(".")
            c[".".join(parts[:4]) if len(parts) >= 4 else fq] += 1
    print(f"「{a.name}」相关 {sum(c.values()):,} 类，按包分组 {len(c)} 组")
    for pkg, n in c.most_common(15):
        print(f"    {pkg}  ({n})")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("find-class"); p.add_argument("name")
    p.add_argument("--scope", default=None); p.set_defaults(fn=cmd_find_class)

    p = sub.add_parser("find-method"); p.add_argument("name")
    p.add_argument("--scope", default=None)
    p.add_argument("--domain", default=None); p.add_argument("--limit", type=int, default=15)
    p.set_defaults(fn=cmd_find_method)

    p = sub.add_parser("methods"); p.add_argument("fqcn")
    p.add_argument("--scope", default=None); p.set_defaults(fn=cmd_methods)

    p = sub.add_parser("search"); p.add_argument("kw")
    p.add_argument("--scope", default=None); p.add_argument("--limit", type=int, default=20)
    p.set_defaults(fn=cmd_search)

    p = sub.add_parser("pkg"); p.add_argument("prefix")
    p.add_argument("--scope", default=None); p.add_argument("--limit", type=int, default=30)
    p.set_defaults(fn=cmd_pkg)

    p = sub.add_parser("app"); p.add_argument("name")
    p.add_argument("--scope", default=None); p.set_defaults(fn=cmd_app)

    sub.add_parser("scopes").set_defaults(fn=cmd_scopes)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())