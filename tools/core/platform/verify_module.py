# -*- coding: utf-8 -*-
"""校验应用 README：签名齐、类名真、无占位符。

用法:
  python verify_module.py organization --group 03-business-app --name organization
退出码 0 = 通过。
"""
import json, io, os, re, sys, argparse, collections

REPO = "C:/Users/白明涛/xiaozhua-agent"
IDX = f"{REPO}/docs/audit/artifacts/extension-surface-full/interfaces-full.json"
FACADE = f"{REPO}/docs/audit/artifacts/facade"
MODULES = f"{REPO}/core/facts/modules"

fail = []
def chk(c, m):
    print(f"  {'OK  ' if c else 'FAIL'} {m}")
    if not c:
        fail.append(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("domain")
    ap.add_argument("--group", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--slug", default=None)
    ap.add_argument("--pkg", default=None)
    a = ap.parse_args()
    slug = a.slug or a.domain

    p = os.path.join(MODULES, a.group, a.name, "README.md")
    print(f"=== {a.group}/{a.name} ({a.domain}) ===")
    chk(os.path.exists(p), "README.md 存在")
    if not os.path.exists(p):
        return 1
    md = io.open(p, encoding="utf-8").read()
    lines = md.split("\n")

    # 1. 章节
    print("\n[1] 章节完整性")
    for s in ("## 一句话", "## 一、构件清单", "## 二、分层规律",
              "facade 层", "## biz 层：领域服务", "## biz 层：事件与监听",
              "## web 层", "## 落表", "## 证据与自证"):
        chk(s in md, f"含章节 {s}")

    # 2. facade 方法数与索引一致
    print("\n[2] facade 方法数")
    o = json.load(io.open(f"{FACADE}/{slug}.json", encoding="utf-8"))
    exp = o["n_methods"]
    # 只统计 facade 段内的表格行
    fstart = md.index("facade 层")
    fend = md.index("## biz 层：领域服务")
    fseg = md[fstart:fend]
    rows = re.findall(r"^\| `([^`]+)` \| `([^`]*)` \| `([^`]*)` \|", fseg, re.M)
    # 去掉接口清单表（| `包` | 数字 | 数字 |）——它们第3列不是类型
    rows = [r for r in rows if not re.fullmatch(r"\d+", r[1].strip())]
    chk(len(rows) == exp, f"facade 表行数 {len(rows)} == 索引方法数 {exp}")

    # 3. 每个方法都在对应接口里
    print("\n[3] 方法与接口对应")
    cur = None
    bad = []
    nm = 0
    for ln in fseg.split("\n"):
        m = re.match(r"^#### (\w+)$", ln.strip())
        if m:
            cur = m.group(1); continue
        if cur and ln.startswith("| `"):
            mm = re.match(r"^\| `([^`]+)` \|", ln)
            if not mm:
                continue
            method = mm.group(1)
            iface = next((f for f in o["facades"] if f["name"] == cur), None)
            if not iface:
                bad.append(f"{cur} 不在索引"); continue
            names = {x["name"] for x in iface["methods"]}
            if method not in names:
                bad.append(f"{cur}#{method} 不存在")
            nm += 1
    chk(not bad, f"所有方法归属正确（检查 {nm} 行，异常 {len(bad)}: {bad[:3]}）")

    # 4. 文档里出现的 com.seeyon FQCN 必须真存在
    print("\n[4] 类名真实性")
    idx = json.load(io.open(IDX, encoding="utf-8"))["classes"]
    fqcns = set(re.findall(r"`(com\.seeyon\.[A-Za-z0-9_.$]+)`", md))
    # 允许包名：只要索引里有类以它开头
    prefixes = set()
    for fq in idx:
        parts = fq.split(".")
        for i in range(3, len(parts)):
            prefixes.add(".".join(parts[:i]))
    orphan = [x for x in fqcns if x not in idx and x not in prefixes]
    chk(not orphan, f"{len(fqcns)} 个 FQCN/包名全部可解析（孤儿 {len(orphan)}: {orphan[:3]}）")

    # 5. 无占位符
    print("\n[5] 无占位符")
    for w in ("TODO", "待补充", "TBD", "XXX", "???", "占位"):
        chk(w not in md, f"不含 {w}")

    # 6. ⚠️ 数量与生成器一致
    print("\n[6] 待定语义标注")
    warn = len(re.findall(r"⚠️ \|", fseg))
    # 2 = facade 中语义待定；另有 落表/路径 的 ⚠️ 在别处
    chk(warn == 0, f"facade 内 ⚠️ 标注 {warn} 个（要求 0）")

    # 7. biz / web 计数与索引一致
    print("\n[7] biz/web 计数")
    cls = idx
    dom = a.domain
    pres = ([f"com.seeyon.{dom}.{p}." for p in a.pkg.split(",")] if a.pkg
            else [f"com.seeyon.{dom}."])
    def inscope(fq):
        return any(fq.startswith(x) for x in pres)
    svcs = [fq for fq, c in cls.items() if inscope(fq)
            and (".domain." in fq or ".biz." in fq)
            and fq.split(".")[-1].endswith("Service") and c.get("kind") == "class"]
    cons = [fq for fq, c in cls.items() if inscope(fq)
            and ".controller." in fq and fq.split(".")[-1].endswith("Controller")]
    m_svc = re.search(r"共 (\d+) 个领域服务", md)
    m_con = re.search(r"共 (\d+) 个 Controller", md)
    chk(m_svc and int(m_svc.group(1)) == len(svcs),
        f"领域服务数 {m_svc.group(1) if m_svc else '?'} == 索引 {len(svcs)}")
    chk(m_con and int(m_con.group(1)) == len(cons),
        f"Controller 数 {m_con.group(1) if m_con else '?'} == 索引 {len(cons)}")

    print("\n" + "=" * 70)
    print(f"结论: {'通过 ✓' if not fail else str(len(fail)) + ' 项失败'}")
    for f in fail:
        print(f"  ✗ {f}")
    print("=" * 70)
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())