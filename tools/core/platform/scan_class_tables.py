# -*- coding: utf-8 -*-
"""静态取证：biz jar 内 class 常量池出现过的真实表名 -> class 映射。

原理：class 在 jar 内是 deflate 压缩的，grep 二进制命中 0；
     用 zipfile 解压后取字节，ASCII 片段里就能读到 SQL/表名字面量。
只认 information_schema 里真实存在的表名（白名单），避免把巧合字符串当表。

输出：docs/audit/artifacts/tables/class-tables.json
      { artifact: { "com.x.Y": ["t1","t2"] } }
"""
import json, io, os, re, sys, zipfile

REPO = r"C:/Users/白明涛/xiaozhua-agent"
TARGETS = r"D:/software/hermes/cache/scratch/rebuild/targets_full.json"
OUT = os.path.join(REPO, "docs/audit/artifacts/tables")

BIZ = ['organization-biz', 'bpm-biz', 'udc-biz', 'ctp-user-biz', 'ctp-affair-biz',
       'ctp-message-biz', 'cip-connector-biz', 'cip-capability-biz', 'cip-manager-biz',
       'cip-convert-biz', 'cdp-data-biz', 'cdp-schedule-biz', 'portal-biz', 'm5-biz',
       'ctp-media-biz', 'app-common-biz', 'app-approval-biz', 'app-doc-biz',
       'ai-biz', 'cip-openapi-gateway-biz', 'ctp-webapi-gateway-biz']

STR = re.compile(rb"[ -~]{4,400}")
PREFIX = re.compile(r"^(tb_|org_|ctp_|udc_|bpm_|cip_|cdp_|m5_|portal_|app_|ai_)[a-z0-9_]{2,}$")
SQL_FROM = re.compile(r"from\s+([a-z0-9_]+)")
SQL_INTO = re.compile(r"into\s+([a-z0-9_]+)")
SQL_UPDATE = re.compile(r"update\s+([a-z0-9_]+)")
SQL_JOIN = re.compile(r"join\s+([a-z0-9_]+)")
SQL_DELETE = re.compile(r"delete\s+from\s+([a-z0-9_]+)")


def load_tables(env="test2"):
    rows = json.load(io.open(os.path.join(OUT, f"db-{env}.json"), encoding="utf-8"))
    by_schema = {}
    for r in rows:
        by_schema.setdefault(r["domain"], set()).add(r["table_name"].lower())
    allset = set()
    for s in by_schema.values():
        allset |= s
    return by_schema, allset


def scan(artifact, jarpath, allset):
    res = {}
    zf = zipfile.ZipFile(jarpath)
    for name in zf.namelist():
        if not name.endswith(".class"):
            continue
        try:
            b = zf.read(name)
        except Exception:
            continue
        hits = set()
        for m in STR.finditer(b):
            t = m.group(0).decode("latin-1").lower()
            # ① 整个字面量就是表名（最硬）：带前缀，或含下划线且足够长
            #    （排除 category / application / affair 这类同时是普通单词的表名）
            if t in allset and (PREFIX.match(t) or ("_" in t and len(t) >= 6)):
                hits.add(t)
                continue
            # ② SQL 上下文：必须成对出现 SQL 动词，避免
            #    "find enums from application:" / "{} update category:{}" 这类日志文案误报
            if "select" in t:
                for mm in SQL_FROM.finditer(t):
                    if mm.group(1) in allset:
                        hits.add(mm.group(1))
                for mm in SQL_JOIN.finditer(t):
                    if mm.group(1) in allset:
                        hits.add(mm.group(1))
            if "insert" in t:
                for mm in SQL_INTO.finditer(t):
                    if mm.group(1) in allset:
                        hits.add(mm.group(1))
            if "update" in t and " set " in t:
                for mm in SQL_UPDATE.finditer(t):
                    if mm.group(1) in allset:
                        hits.add(mm.group(1))
            if "delete" in t:
                for mm in SQL_DELETE.finditer(t):
                    if mm.group(1) in allset:
                        hits.add(mm.group(1))
        if hits:
            cls = name[:-6].replace("/", ".")
            res[cls] = sorted(hits)
    zf.close()
    return res


def main():
    targets = json.load(io.open(TARGETS, encoding="utf-8"))
    _, allset = load_tables()
    print(f"白名单表名: {len(allset)}")
    os.makedirs(OUT, exist_ok=True)
    for a in BIZ:
        if a not in targets:
            print(f"  ? {a}")
            continue
        path = targets[a][1]
        if not os.path.exists(path):
            print(f"  ✗ {a}: 缺 jar")
            continue
        r = scan(a, path, allset)
        tabs = sorted({t for v in r.values() for t in v})
        out = os.path.join(OUT, f"class-tables.{a}.json")
        io.open(out, "w", encoding="utf-8").write(json.dumps(r, ensure_ascii=False, indent=1))
        print(f"  ✓ {a}: {len(r)} 个 class 命中, {len(tabs)} 张表")
    return 0


if __name__ == "__main__":
    sys.exit(main())