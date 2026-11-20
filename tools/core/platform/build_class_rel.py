# -*- coding: utf-8 -*-
"""从字节码索引抽类关系索引：implements + 字段类型（用于接口 -> 表 溯源）。

输出 docs/audit/artifacts/tables/class-rel.json
  { "com.x.Foo": {"implements": ["com.y.IFoo"], "fields": ["com.z.FooManager", ...]} }
只保留与「持久化可能的承载类」相关的字段类型，控制体积。
"""
import json, io, os, sys

REPO = r"C:/Users/白明涛/xiaozhua-agent"
SRC = os.path.join(REPO, "docs/audit/artifacts/extension-surface-full/interfaces-full.json")
OUT = os.path.join(REPO, "docs/audit/artifacts/tables/class-rel.json")

KEEP = ("Manager", "Dao", "DAO", "Repository", "Mapper", "ServiceImpl",
        "Service", "RepositoryImpl", "Store", "Storage", "Helper", "Support")


def main():
    d = json.load(io.open(SRC, encoding="utf-8"))
    res = {}
    for fq, c in d["classes"].items():
        impls = c.get("implements") or []
        ftypes = []
        for f in (c.get("fields") or []):
            t = f.get("type") or ""
            t = t.replace("java.util.List<", "").replace("java.util.Set<", "").rstrip(">")
            if not t.startswith("com.seeyon"):
                continue
            if t.rsplit(".", 1)[-1].endswith(KEEP):
                ftypes.append(t)
        if impls or ftypes:
            res[fq] = {"implements": impls, "fields": sorted(set(ftypes))}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False))
    print(f"class-rel: {len(res)} 类, {os.path.getsize(OUT)//1024} KB")


if __name__ == "__main__":
    sys.exit(main())