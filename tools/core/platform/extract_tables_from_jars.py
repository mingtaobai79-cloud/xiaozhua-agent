# -*- coding: utf-8 -*-
"""从 jar 内 mapper XML 提取真实表名（静态证据，不连库）。

输出：
  docs/audit/artifacts/tables/{artifact}.json   {xml文件: {namespace, tables[], operations[]}}
  docs/audit/artifacts/tables/SUMMARY.md        汇总

用法: python extract_tables_from_jars.py [artifact ...]
"""
import json, io, os, re, sys, zipfile

REPO = "C:/Users/白明涛/xiaozhua-agent"
TARGETS = "D:/software/hermes/cache/scratch/rebuild/targets_full.json"
OUT = f"{REPO}/docs/audit/artifacts/tables"

# 只扫 biz 层（mapper 都在 biz）
DEFAULT = [
    "organization-biz", "bpm-biz", "udc-biz", "ctp-user-biz", "ctp-affair-biz",
    "ctp-message-biz", "cip-connector-biz", "cip-capability-biz", "cdp-data-biz",
    "app-common-biz", "portal-biz", "m5-biz",
]

TABLE_RE = re.compile(
    r"\b(?:from|into|update|join|table)\s+([a-zA-Z_][a-zA-Z0-9_]{3,})", re.I)
TABLE_ATTR = re.compile(r'table\s*=\s*"([^"]+)"')
# 排除 SQL 结构关键字
SKIP = {
    "select", "where", "set", "values", "and", "or", "on", "as", "left", "right",
    "inner", "outer", "group", "order", "by", "having", "limit", "union", "all",
    "case", "when", "then", "else", "end", "distinct", "count", "sum", "max",
    "min", "avg", "concat", "ifnull", "now", "dual", "results", "parameter",
    "result", "insert", "delete", "update", "this", "the", "user", "table",
}


def tables_in(text):
    got = set()
    for m in TABLE_RE.finditer(text):
        t = m.group(1)
        if t.lower() in SKIP:
            continue
        got.add(t)
    for m in TABLE_ATTR.finditer(text):
        got.add(m.group(1))
    return got


def scan(artifact, jarpath):
    res = {}
    try:
        zf = zipfile.ZipFile(jarpath)
    except Exception as e:
        print(f"  ✗ {artifact}: {e}")
        return res
    for name in zf.namelist():
        if not name.endswith(".xml"):
            continue
        try:
            raw = zf.read(name)
        except Exception:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("gbk", errors="ignore")
        if "<mapper" not in text and "<sql" not in text.lower():
            continue
        tabs = tables_in(text)
        if not tabs:
            continue
        ns = ""
        m = re.search(r'namespace\s*=\s*"([^"]+)"', text)
        if m:
            ns = m.group(1)
        ops = re.findall(r'<(select|insert|update|delete)\s+id\s*=\s*"([^"]+)"', text)
        res[name] = {
            "namespace": ns,
            "tables": sorted(tabs),
            "operations": [f"{a}:{b}" for a, b in ops],
        }
    zf.close()
    return res


def main():
    targets = json.load(io.open(TARGETS, encoding="utf-8"))
    arts = sys.argv[1:] or DEFAULT
    os.makedirs(OUT, exist_ok=True)
    all_tables = set()
    summary = []
    for a in arts:
        if a not in targets:
            print(f"  ? {a}: 不在 targets")
            continue
        ver, path = targets[a]
        if not os.path.exists(path):
            print(f"  ✗ {a}: jar 不存在 {path}")
            continue
        r = scan(a, path)
        if not r:
            print(f"  - {a}: 无 mapper XML")
            continue
        io.open(os.path.join(OUT, f"{a}.json"), "w", encoding="utf-8").write(
            json.dumps(r, ensure_ascii=False, indent=1))
        tabs = set()
        for v in r.values():
            tabs.update(v["tables"])
        all_tables |= tabs
        summary.append((a, len(r), len(tabs)))
        print(f"  ✓ {a}: {len(r)} 个 mapper XML, {len(tabs)} 张表")

    print()
    print(f"合计 {len(summary)} 个构件，{len(all_tables)} 张不同的表")
    L = ["# mapper XML 里的表名（MyBatis 存量）", "",
         f"> 来源：{len(summary)} 个 biz 构件的 `*.xml`（MyBatis mapper）",
         "> 证据等级：`VERIFIED_STATIC_BYTECODE`（XML 在 jar 里，非推测）", "",
         "| 构件 | mapper XML | 表数 |", "|---|---:|---:|"]
    for a, nx, nt in summary:
        L.append(f"| `{a}` | {nx} | {nt} |")
    L.append(f"| **合计** | | **{len(all_tables)}** |")
    L.append("")
    io.open(os.path.join(OUT, "MAPPERS.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"→ {OUT}/MAPPERS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())