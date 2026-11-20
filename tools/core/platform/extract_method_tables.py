# -*- coding: utf-8 -*-
"""方法级落表：写方法 -> 实现类字节码 -> 引用到的实体/DAO -> 真实表。

链条（每一步都有字节码证据）：
  facade 方法 createXxx  ->  impl 类（index 的 implements）  ->  javap -c 该方法的常量引用
  -> 引用的 class（实体 / DAO / Manager）
  -> 实体类 -> class-tables 里的表名（@TableName 字面量）
  -> DAO 接口 -> extends BaseMybatisDao<Entity> 的泛型实体 -> 同上
  -> Manager -> 它的 DAO 字段（class-rel.json）-> 同上

只做「写类方法」（create/update/delete/save/…）；读方法不做（不值得）。
输出: docs/audit/artifacts/method-tables/<slug>.json
      { "Interface#method": {"impl":..., "tables":[...], "chain":[...]} }
用法: python extract_method_tables.py [slug ...]
"""
import json, io, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

REPO = r"C:/Users/白明涛/xiaozhua-agent"
T = os.path.join(REPO, "docs/audit/artifacts/tables")
INDEX = os.path.join(REPO, "docs/audit/artifacts/extension-surface-full/interfaces-full.json")
FACADE = os.path.join(REPO, "docs/audit/artifacts/facade")
TARGETS = r"D:/software/hermes/cache/scratch/rebuild/targets_full.json"
OUT = os.path.join(REPO, "docs/audit/artifacts/method-tables")
JAVAP = r"D:/software/java/bin/javap.exe"

WRITE = ("create", "update", "delete", "save", "insert", "remove", "add",
         "submit", "modify", "assign", "publish", "deploy", "enable", "disable",
         "import", "upload", "copy", "execute", "change", "cancel", "merge",
         "transfer", "move", "reset", "sync")

MOD = {
    "organization": ["organization-biz"], "bpm": ["bpm-biz"],
    "ctp-affair": ["ctp-affair-biz"], "ctp-user": ["ctp-user-biz"],
    "ctp-message": ["ctp-message-biz"],
    "ctp-other": ["ctp-media-biz", "ctp-user-biz", "portal-biz"],
    "cip-connector": ["cip-connector-biz"], "cip-capability": ["cip-capability-biz"],
    # 实测：cip-provider 的实现类在 cip-capability-biz，不在 cip-connector-biz
    "cip-provider": ["cip-capability-biz"],
    "cip-other": ["cip-convert-biz", "cip-manager-biz", "cip-connector-biz",
                  "cip-openapi-gateway-biz"],
    "udc": ["udc-biz"], "boot": [], "cdp": ["cdp-data-biz", "cdp-schedule-biz"],
    "app": ["app-common-biz", "app-approval-biz", "app-doc-biz"],
    "portal": ["portal-biz"], "m5": ["m5-biz"], "ocip": [], "ai": ["ai-biz"],
    "devops": [], "gateway": [], "maven": [], "mymojo": [],
}

SIG = re.compile(r"^  [\w<>\[\]\.\$, ]*?(\w+)\(")
REF_CLASS = re.compile(r"//\s*class\s+([\w/$]+)")
# javap 的字段引用是「字段名:类型」——以前写成「类名.字段」，一条都匹配不到
REF_FIELD = re.compile(r"//\s*Field\s+\w+:L?\[*L?([\w/$]+)")
REF_METHOD = re.compile(r"//\s*(?:Interface)?Method\s+([\w/$]+)\.")
GEN = re.compile(r"<([\w\.\$]+)>")


REL = os.path.join(T, "class-rel.json")


def snake(name):
    """OrgMemberRole -> org_member_role"""
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return s


def pick(tabs, cls_simple):
    """实体类优先取与类名同名的表（OrgUnit -> org_unit），其余列为 also。"""
    want = snake(cls_simple)
    if want in tabs:
        return want, sorted(tabs - {want})
    return (sorted(tabs)[0], sorted(tabs)[1:]) if tabs else (None, [])


def resolve(ref, tables, ent, rel, depth=0, seen=None):
    """引用类 -> (主表集合, 附带表集合, 证据链)"""
    seen = seen or set()
    if ref in seen or depth > 2:
        return set(), set(), []
    seen.add(ref)
    main, also, chain = set(), set(), []
    if ref in tables:
        w, rest = pick(tables[ref], ref.rsplit(".", 1)[-1])
        if w:
            main.add(w)
            chain.append(f"{ref.rsplit('.', 1)[-1]}->{w}")
        also |= set(rest)
    for e in ent.get(ref, ()):
        if e in tables:
            w, rest = pick(tables[e], e.rsplit(".", 1)[-1])
            if w:
                main.add(w)
                chain.append(f"{ref.rsplit('.', 1)[-1]}=>{e.rsplit('.', 1)[-1]}->{w}")
            also |= set(rest)
    for f in (rel.get(ref, {}) or {}).get("fields", ()):
        # 只往下跟 DAO/Repository 这类持久化字段；跟 Manager/Service 会把
        # 整个领域对象图拉进来（实测 createBatch 一次挂 19 张表，等于没精度）
        if not f.rsplit(".", 1)[-1].endswith(("Dao", "DAO", "Repository",
                                               "Mapper", "Store", "DaoImpl",
                                               "RepositoryImpl")):
            continue
        m2, a2, c2 = resolve(f, tables, ent, rel, depth + 1, seen)
        main |= m2
        also |= a2
        chain += c2
    return main, also, chain


def load_idx():
    return json.load(io.open(INDEX, encoding="utf-8"))


def entity_map(idx):
    """DAO/Repository -> 泛型实体；只保留 extends 里带 <...> 的。"""
    m = {}
    for fq, c in idx["classes"].items():
        for e in (c.get("extends") or []):
            g = GEN.search(e)
            if g:
                m.setdefault(fq, set()).add(g.group(1))
    return m


def class_tables(arts):
    m = {}
    for a in arts:
        p = os.path.join(T, f"class-tables.{a}.json")
        if os.path.exists(p):
            for k, v in json.load(io.open(p, encoding="utf-8")).items():
                m.setdefault(k, set()).update(v)
    return m


def run_javap(jar, fqcn):
    try:
        r = subprocess.run([JAVAP, "-p", "-c", "-cp", jar, fqcn],
                           capture_output=True, timeout=120)
    except Exception:
        return ""
    b = r.stdout or b""
    for enc in ("gbk", "utf-8"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode("utf-8", "ignore")


def method_refs(txt):
    """{方法名: set(引用的类 fqcn)}"""
    out, cur = {}, None
    for line in txt.splitlines():
        m = SIG.match(line)
        if m and line.rstrip().endswith(";"):
            cur = m.group(1)
            out.setdefault(cur, set())
            continue
        if cur is None:
            continue
        for rx in (REF_CLASS, REF_FIELD, REF_METHOD):
            mm = rx.search(line)
            if mm:
                out[cur].add(mm.group(1).replace("/", "."))
    return out


def main():
    slugs = sys.argv[1:] or list(MOD)
    idx = load_idx()
    ent = entity_map(idx)
    rel = json.load(io.open(REL, encoding="utf-8")) if os.path.exists(REL) else {}
    targets = json.load(io.open(TARGETS, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    implmap = {}
    for fq, c in idx["classes"].items():
        for i in (c.get("implements") or []):
            implmap.setdefault(i, []).append(fq)

    for slug in slugs:
        fp = os.path.join(FACADE, f"{slug}.json")
        if not os.path.exists(fp) or not MOD.get(slug):
            print(f"  - {slug}: 跳过")
            continue
        tables = class_tables(MOD[slug])
        d = json.load(io.open(fp, encoding="utf-8"))
        jar = targets[MOD[slug][0]][1]

        # 1) 收集写方法 + 它的实现类
        jobs = []   # (iface简单名, method, impl列表)
        for f in d["facades"]:
            for m in f["methods"]:
                if not m["name"].lower().startswith(WRITE):
                    continue
                impls = implmap.get(f["fqcn"], [])
                jobs.append((f["name"], m["name"], impls))
        if not jobs:
            print(f"  - {slug}: 无写方法")
            continue

        # 2) 每个实现类只反编译一次
        all_impls = sorted({i for _, _, ims in jobs for i in ims})
        cache = {}
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(run_javap, jar, i): i for i in all_impls}
            for f_, i in futs.items():
                try:
                    cache[i] = method_refs(f_.result())
                except Exception:
                    cache[i] = {}

        # 3) 解析引用 -> 表
        res = {}
        for iname, mname, impls in jobs:
            main, also, chain = set(), set(), []
            for impl in impls:
                m_impl = set()
                for ref in cache.get(impl, {}).get(mname, ()):
                    m1, a1, c1 = resolve(ref, tables, ent, rel)
                    m_impl |= m1
                    also |= a1
                    chain += c1
                if not m_impl:
                    # 泛型基类带实体：Impl extends AbstractService<CipAccessLog>
                    for e in ent.get(impl, ()):
                        if e in tables:
                            w, rest = pick(tables[e], e.rsplit(".", 1)[-1])
                            if w:
                                m_impl.add(w)
                                also |= set(rest)
                                chain.append(f"[{impl.rsplit('.', 1)[-1]}]=>{e.rsplit('.', 1)[-1]}->{w}")
                if not m_impl and impl in tables:
                    # 方法体里没有实体引用（走 super/泛型基类），退到实现类的类级证据
                    m_impl = set(tables[impl])
                    chain.append(f"[{impl.rsplit('.', 1)[-1]}] 类级兜底")
                main |= m_impl
            if main:
                key = f"{iname}#{mname}"
                fallback = any("类级兜底" in c for c in chain)
                res[key] = {"impl": [i.rsplit('.', 1)[-1] for i in impls],
                            "tables": sorted(main),
                            "also": sorted(also - main),
                            "level": "class-fallback" if fallback and not any("->" in c for c in chain) else "method",
                            "chain": sorted(set(chain))[:8]}
        io.open(os.path.join(OUT, f"{slug}.json"), "w", encoding="utf-8").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"  {'✓' if res else '-'} {slug}: 写方法 {len(jobs)}，取到表 {len(res)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())