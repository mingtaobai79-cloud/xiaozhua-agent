# -*- coding: utf-8 -*-
"""平台索引查询工具（供 Agent 直接调用）。

用法：
  python query_platform.py find-class JsonUtils
  python query_platform.py find-method send --domain bpm
  python query_platform.py methods com.seeyon.bpm.api.common.BpmAppService
  python query_platform.py search 库存扣减
  python query_platform.py app organization

设计要点：
  - 加载 1.0s，之后每次查询 <10ms
  - 裸查自动用 priority.json 挑权威类（解决 787 组重名）
  - 支持 --domain 限定域
"""
import json, io, sys, os, time, re, argparse

REPO = "C:/Users/白明涛/xiaozhua-agent"
IDX = os.path.join(REPO, "docs/audit/artifacts/extension-surface-full/interfaces-full.json")
PRI = "D:/software/hermes/cache/scratch/rebuild/priority.json"

_cache = {}

def load():
    if "idx" not in _cache:
        t = time.perf_counter()
        _cache["idx"] = json.load(io.open(IDX, encoding="utf-8"))
        _cache["pri"] = json.load(io.open(PRI, encoding="utf-8"))
        _cache["load_s"] = time.perf_counter() - t
    return _cache["idx"], _cache["pri"]

def cmd_find_class(a):
    idx, pri = load()
    hits = [fq for fq in idx["classes"] if fq.endswith("." + a.name) or fq == a.name]
    if not hits:
        print(f"未找到 {a.name}"); return 1
    print(f"{a.name}  命中 {len(hits)} 个")
    if a.name in pri and pri[a.name]["conflict"]:
        print(f"  ⚠️ 重名 {len(pri[a.name]['all'])} 个，按权威度排序：")
        for i, fq in enumerate(pri[a.name]["all"]):
            print(f"    {'★' if i == 0 else ' '} {fq}")
        print(f"\n  ✅ 推荐用: {pri[a.name]['primary']}")
    else:
        for fq in hits:
            print(f"    {fq}")
    return 0

def cmd_find_method(a):
    idx, pri = load()
    hits = idx["method_index"].get(a.name, [])
    if a.domain:
        hits = [h for h in hits if h.lower().startswith("com.seeyon." + a.domain.lower())
                or f".{a.domain}." in h.lower()]
        print(f"{a.name}() 限定域 {a.domain} → {len(hits)} 处  ({_cache['load_s']:.2f}s 加载)")
    else:
        print(f"{a.name}() 全部 → {len(hits)} 处")
    # 按权威度排序（boot > api > 其他）
    def sc(h):
        if h.startswith("com.seeyon.boot.transport"): return 0
        if h.startswith("com.seeyon.boot."): return 1
        if re.match(r"^com\.seeyon\.\w+\.api\.", h): return 2
        if ".appservice." in h and h.lower().endswith("appservice#"+a.name): return 3
        if ".domain.service." in h: return 6
        if ".util." in h or "Utils" in h: return 8
        return 4
    for h in sorted(hits, key=sc)[:a.limit]:
        print(f"    {h}")
    if len(hits) > a.limit:
        print(f"    ... 还有 {len(hits)-a.limit} 处（--limit 调整）")
    return 0

def cmd_methods(a):
    idx, pri = load()
    c = idx["classes"].get(a.fqcn)
    if not c:
        print(f"类不存在: {a.fqcn}")
        cand = [fq for fq in idx["classes"] if fq.endswith("." + a.fqcn.split(".")[-1])]
        if cand:
            print("  相近：")
            for x in cand: print(f"    {x}")
        return 1
    ms = [m for m in (c.get("methods") or []) if not m["name"].startswith("lambda$")]
    print(f"{a.fqcn}")
    print(f"  构件 {c.get('pkg')}  方法 {len(ms)} 个\n")
    for m in ms:
        args = ", ".join(x["type"].split(".")[-1] for x in m.get("args") or [])
        print(f"  {m['name']}({args})")
        print(f"      → {m['returns']}")
    return 0

def cmd_search(a):
    idx, pri = load()
    pat = re.compile(a.kw, re.I)
    t = time.perf_counter()
    hits = [fq for fq in idx["classes"] if pat.search(fq)]
    d = (time.perf_counter() - t) * 1000
    print(f"搜「{a.kw}」→ {len(hits)} 个类  ({d:.0f} ms)")
    for fq in hits[:a.limit]:
        print(f"    {fq}")
    if len(hits) > a.limit:
        print(f"    ... 还有 {len(hits)-a.limit} 个")
    return 0

def cmd_app(a):
    idx, pri = load()
    pat = a.name.lower()
    hits = collections_counter(idx, pat)
    print(f"应用 {a.name} 相关类 {len(hits)} 个")
    for pkg, n in hits[:15]:
        print(f"    {pkg}  ({n})")
    return 0

def collections_counter(idx, pat):
    import collections
    c = collections.Counter()
    for fq in idx["classes"]:
        if pat in fq.lower():
            # 取 4 段作为分组
            parts = fq.split(".")
            key = ".".join(parts[:4]) if len(parts) >= 4 else fq
            c[key] += 1
    return c.most_common()

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("find-class"); p.add_argument("name"); p.set_defaults(fn=cmd_find_class)
    p = sub.add_parser("find-method"); p.add_argument("name")
    p.add_argument("--domain", default=None); p.add_argument("--limit", type=int, default=15)
    p.set_defaults(fn=cmd_find_method)
    p = sub.add_parser("methods"); p.add_argument("fqcn"); p.set_defaults(fn=cmd_methods)
    p = sub.add_parser("search"); p.add_argument("kw")
    p.add_argument("--limit", type=int, default=20); p.set_defaults(fn=cmd_search)
    p = sub.add_parser("app"); p.add_argument("name"); p.set_defaults(fn=cmd_app)

    a = ap.parse_args()
    return a.fn(a)

if __name__ == "__main__":
    sys.exit(main())