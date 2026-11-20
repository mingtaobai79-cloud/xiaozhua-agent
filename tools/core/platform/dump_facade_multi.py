# -*- coding: utf-8 -*-
"""按多个子包合并抽 facade（用于 ctp-other / cip-other 这类聚合模块）。

用法: python dump_facade_multi.py <domain> <slug> pkg1,pkg2,...
"""
import json, io, os, sys

REPO = "C:/Users/白明涛/xiaozhua-agent"
sys.path.insert(0, os.path.join(REPO, "tools/core/platform"))
import dump_facade as df  # noqa

IDX = f"{REPO}/docs/audit/artifacts/extension-surface-full/interfaces-full.json"
OUT = f"{REPO}/docs/audit/artifacts/facade"


def main():
    if len(sys.argv) < 4:
        print("用法: dump_facade_multi.py <domain> <slug> pkg1,pkg2,...")
        return 2
    dom, slug, pkgs = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    d = df.load()
    cls = d["classes"]
    pre = [f"com.seeyon.{dom}.{p}." for p in pkgs]
    sub = {fq: c for fq, c in cls.items() if any(fq.startswith(x) for x in pre)}

    out = {"domain": dom, "pkg": ",".join(pkgs), "slug": slug,
           "total_classes": len(sub), "facades": [], "impls_count": 0}
    for fq in sorted(sub):
        c = sub[fq]
        if c.get("kind") != "interface":
            continue
        if not (".api." in fq or ".appservice." in fq):
            continue
        ms = [m for m in (c.get("methods") or []) if not m["name"].startswith("lambda$")]
        out["facades"].append({
            "fqcn": fq, "name": fq.split(".")[-1],
            "package": ".".join(fq.split(".")[:-1]),
            "pkg_artifact": c.get("pkg"),
            "extends": [df.short(x) for x in (c.get("extends") or [])],
            "implements": [df.short(x) for x in (c.get("implements") or [])],
            "methods": [df.fmt_method(m) for m in ms]})
    out["n_facades"] = len(out["facades"])
    out["n_methods"] = sum(len(f["methods"]) for f in out["facades"])

    os.makedirs(OUT, exist_ok=True)
    io.open(os.path.join(OUT, f"{slug}.json"), "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(f"{slug}: {out['n_facades']} 接口 / {out['n_methods']} 方法 / 类 {len(sub):,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())