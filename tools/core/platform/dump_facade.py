# -*- coding: utf-8 -*-
"""抽取应用 facade 面，输出规范签名。

用法：
  python dump_facade.py organization            # 打印
  python dump_facade.py organization --json     # 落 json（给文档生成器用）
"""
import json, io, os, sys, re, collections

REPO = "C:/Users/白明涛/xiaozhua-agent"
IDX = f"{REPO}/docs/audit/artifacts/extension-surface-full/interfaces-full.json"
OUTDIR = f"{REPO}/docs/audit/artifacts/facade"

_FQN = re.compile(r"\b(?:[a-z][a-zA-Z0-9_]*\.)+([A-Z][A-Za-z0-9_$]*)")


def short(t):
    """去掉包前缀，保留泛型结构。"""
    if not t:
        return "void"
    t = _FQN.sub(r"\1", t)
    return t.replace("java.lang.", "")


def load():
    return json.load(io.open(IDX, encoding="utf-8"))


def collect(dom, pkg=None):
    d = load()
    cls = d["classes"]
    pre = f"com.seeyon.{dom}." + (pkg + "." if pkg else "")
    sub = {fq: c for fq, c in cls.items() if fq.startswith(pre)}
    faces, impls = {}, {}
    for fq, c in sub.items():
        is_if = c.get("kind") == "interface"
        in_api = (".api." in fq or ".appservice." in fq)
        if is_if and in_api:
            faces[fq] = c
        elif not is_if:
            impls[fq] = c
    return sub, faces, impls


def methods_of(c):
    return [m for m in (c.get("methods") or []) if not m["name"].startswith("lambda$")]


def fmt_method(m):
    args = []
    for a in (m.get("args") or []):
        t = short(a.get("type"))
        n = a.get("name") or ""
        args.append(f"{t} {n}".strip())
    flags = ",".join(x for x in (m.get("modifiers") or [])
                     if x in ("static", "abstract", "default"))
    return {"name": m["name"], "args": args,
            "raw_args": [a.get("type") for a in (m.get("args") or [])],
            "returns": short(m.get("returns")),
            "raw_returns": m.get("returns"),
            "sig": f"{m['name']}({', '.join(args)}) -> {short(m.get('returns'))}",
            "flags": flags}


def build(dom, pkg=None, slug=None):
    sub, faces, impls = collect(dom, pkg)
    out = {"domain": dom, "pkg": pkg, "slug": slug or dom, "total_classes": len(sub),
           "facades": [], "impls_count": len(impls)}
    for fq in sorted(faces):
        c = faces[fq]
        ms = methods_of(c)
        out["facades"].append({
            "fqcn": fq,
            "name": fq.split(".")[-1],
            "package": ".".join(fq.split(".")[:-1]),
            "pkg_artifact": c.get("pkg"),
            "extends": [short(x) for x in (c.get("extends") or [])],
            "implements": [short(x) for x in (c.get("implements") or [])],
            "methods": [fmt_method(m) for m in ms],
        })
    out["n_facades"] = len(out["facades"])
    out["n_methods"] = sum(len(f["methods"]) for f in out["facades"])
    return out


def print_human(o):
    print(f"=== {o['domain']} ===")
    print(f"类 {o['total_classes']:,}  facade 接口 {o['n_facades']}  方法 {o['n_methods']}  "
          f"实现类 {o['impls_count']}\n")
    byp = collections.defaultdict(list)
    for f in o["facades"]:
        byp[f["package"]].append(f)
    for p in sorted(byp):
        print(f"--- {p}  ({len(byp[p])} 接口)")
        for f in byp[p]:
            print(f"  {f['name']}  [{len(f['methods'])}]  {f['pkg_artifact']}")
            for m in f["methods"]:
                print(f"      {m['sig']}")
        print()


def main():
    if len(sys.argv) < 2:
        print("用法: dump_facade.py <domain> [--json]")
        return 2
    dom = sys.argv[1]
    pkg = None
    if "--pkg" in sys.argv:
        pkg = sys.argv[sys.argv.index("--pkg") + 1]
    slug = None
    if "--slug" in sys.argv:
        slug = sys.argv[sys.argv.index("--slug") + 1]
    o = build(dom, pkg, slug)
    if "--json" in sys.argv:
        os.makedirs(OUTDIR, exist_ok=True)
        p = os.path.join(OUTDIR, f"{o['slug']}.json")
        io.open(p, "w", encoding="utf-8").write(json.dumps(o, ensure_ascii=False, indent=1))
        print(f"{o['n_facades']} 接口 / {o['n_methods']} 方法 -> {p}")
    else:
        print_human(o)
    return 0


if __name__ == "__main__":
    sys.exit(main())