# -*- coding: utf-8 -*-
"""全量自证：19 个模块逐个校验 + 跨模块汇总与索引对齐。

退出码 0 = 全部通过。
"""
import os, sys, json, io, re, glob, subprocess, collections

REPO = "C:/Users/白明涛/xiaozhua-agent"
T = f"{REPO}/tools/core/platform"
IDX = f"{REPO}/docs/audit/artifacts/extension-surface-full/interfaces-full.json"
FACADE = f"{REPO}/docs/audit/artifacts/facade"
MODULES = f"{REPO}/core/facts/modules"

from gen_all_modules import MODULES as MODDEF  # noqa

fail = []
def chk(c, m):
    print(f"  {'OK  ' if c else 'FAIL'} {m}")
    if not c:
        fail.append(m)


def main():
    print("=" * 78)
    print("A. 逐模块自证")
    print("=" * 78)
    for dom, pkg, slug, group, name, title in MODDEF:
        argv = [sys.executable, f"{T}/verify_module.py", dom,
                "--slug", slug, "--group", group, "--name", name]
        if pkg:
            argv += ["--pkg", pkg]
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8")
        ok = r.returncode == 0
        print(f"  {'OK  ' if ok else 'FAIL'} {slug:<16} "
              f"{'通过' if ok else '失败'}")
        if not ok:
            fail.append(f"{slug} 自证失败")
            for ln in (r.stdout or "").split("\n"):
                if "FAIL" in ln:
                    print(f"        {ln.strip()}")

    print()
    print("=" * 78)
    print("B. 全量覆盖：19 模块 facade 合计 vs 索引")
    print("=" * 78)
    idx = json.load(io.open(IDX, encoding="utf-8"))["classes"]
    # 索引里全部 api/appservice 接口
    all_ifaces = {}
    for fq, c in idx.items():
        if c.get("kind") == "interface" and (".api." in fq or ".appservice." in fq):
            ms = [m for m in (c.get("methods") or []) if not m["name"].startswith("lambda$")]
            all_ifaces[fq] = ms
    exp_i, exp_m = len(all_ifaces), sum(len(v) for v in all_ifaces.values())
    got_i = got_m = 0
    seen = set()
    for dom, pkg, slug, group, name, title in MODDEF:
        p = f"{FACADE}/{slug}.json"
        if not os.path.exists(p):
            continue
        o = json.load(io.open(p, encoding="utf-8"))
        got_i += o["n_facades"]
        got_m += o["n_methods"]
        for f in o["facades"]:
            if f["fqcn"] in seen:
                fail.append(f"{f['fqcn']} 在多个模块重复")
            seen.add(f["fqcn"])
    print(f"  索引 api/appservice 接口 {exp_i} / 方法 {exp_m}")
    print(f"  19 模块合计          接口 {got_i} / 方法 {got_m}")
    chk(got_i == exp_i, f"接口数对齐 {got_i} == {exp_i}")
    chk(got_m == exp_m, f"方法数对齐 {got_m} == {exp_m}")
    chk(seen == set(all_ifaces), f"接口集合完全一致（缺 {len(set(all_ifaces)-seen)}，多 {len(seen-set(all_ifaces))}）")
    miss = sorted(set(all_ifaces) - seen)[:5]
    if miss:
        print(f"    缺: {miss}")

    print()
    print("=" * 78)
    print("C. README 存在性 + 无占位符 + 无 ⚠️")
    print("=" * 78)
    n = 0
    for dom, pkg, slug, group, name, title in MODDEF:
        p = f"{MODULES}/{group}/{name}/README.md"
        ok = os.path.exists(p)
        chk(ok, f"{group}/{name}/README.md 存在")
        if not ok:
            continue
        n += 1
        t = io.open(p, encoding="utf-8").read()
        for w in ("TODO", "待补充", "TBD"):
            if w in t:
                fail.append(f"{name} 含 {w}")
        if "⚠️ |" in t:
            fail.append(f"{name} facade 仍有 ⚠️")
    print(f"  有效 README {n} / {len(MODDEF)}")

    print()
    print("=" * 78)
    print("D. 索引域覆盖：16 个域是否都进了模块")
    print("=" * 78)
    covered = set()
    for dom, pkg, slug, group, name, title in MODDEF:
        covered.add(dom)
    all_dom = collections.Counter()
    for fq in idx:
        p = fq.split(".")
        if len(p) >= 3 and p[0] == "com" and p[1] == "seeyon":
            all_dom[p[2]] += 1
    miss = [d for d in all_dom if d not in covered]
    chk(not miss, f"16 域全覆盖（未覆盖 {miss}）")
    print(f"  域 {len(all_dom)} 个，模块覆盖 {len(set(all_dom) & covered)} 个")

    print()
    print("=" * 78)
    print(f"结论: {'全部通过 ✓' if not fail else str(len(fail)) + ' 项失败'}")
    for f in fail[:20]:
        print(f"  ✗ {f}")
    print("=" * 78)
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())