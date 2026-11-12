# -*- coding: utf-8 -*-
"""部署态 544 jar marker 普查复算器（离线只读，LIVE-DEPLOYED + VERIFIED_STATIC_BYTECODE）。

要回答的问题（PROGRESS 第二十轮遗留 / 域边界是否闭合）：
「余 60 条 op 在部署域内 0 命中」当前只在 94 个 jar 的扫描域内成立，而部署态
BOOT-INF/lib 实为 544 jar。若某些构件被漏掉、而它恰好提供这些 op，结论就塌。

判据（本器把它做成可复算的普查，而不是抽样）：
  对每个部署 jar，扫描其 .class 常量池是否含 marker bind/annotation。
  ① 任何带 @RequestMapping/@GetMapping/... 的类必然引用
     org/springframework/web/bind/annotation/*  ⇒ 含 marker 是能暴露注解路由的必要条件；
  ② 故 0 marker 的 jar 结构上不可能暴露注解路由 —— 漏掉它们不可能隐藏端点；
  ③ 于是「域是否漏构件」可收窄为一条可检验命题：
     全部含 marker 的部署构件 ⊆ 扫描域（缺失清单须为空）。

诚实边界：NOT_OBTAINABLE 的构件 marker 状态未知（本地与 Artifactory 均取不到 jar），
故本器不把它们算作 0 marker；闭包命题只在已扫子集上成立，且另报不可取清单。

用法：
    uv run --no-project python tools/enumerate_deployed_marker_census.py \
        --inventory <lib_inventory.json> --class-dir <域根> --emit <out.json>
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

MARKER = b"bind/annotation"
CACHE_DIRS = ("djars", "missingjars", "artif", "art517", "cand", "udcchk",
              "deployed-extra", "bulk/jars", "bulk/allvers")


def local_index(extra_roots):
    idx = {}
    for f in glob.glob("<MAVEN_REPO>/**/*.jar", recursive=True):
        idx.setdefault(os.path.basename(f), f)
    for root in extra_roots:
        for d in CACHE_DIRS:
            for f in glob.glob(str(Path(root) / d / "*.jar")):
                idx.setdefault(os.path.basename(f), f)
    return idx


def scan_jar(path):
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.endswith(".class")]
        n = sum(1 for x in names if MARKER in z.read(x))
    return len(names), n


def build(inventory, class_dir=None):
    inv = Path(inventory)
    raw = inv.read_bytes()
    meta = {"name": inv.name, "sha256": hashlib.sha256(raw).hexdigest()}
    jars = json.loads(raw.decode("utf-8"))["jars"]
    idx = local_index([inv.parent])
    rows = []
    for j in sorted(jars):
        p = idx.get(j)
        rec = {"jar": j}
        if not p:
            rec["status"] = "NOT_OBTAINABLE"
        else:
            try:
                c, n = scan_jar(p)
                rec.update({"status": "SCANNED", "classes": c,
                            "annotated_classes": n})
            except Exception as e:
                rec.update({"status": "BADJAR", "err": str(e)[:120]})
        rows.append(rec)
    sc = [r for r in rows if r["status"] == "SCANNED"]
    mk = [r["jar"] for r in sc if r["annotated_classes"] > 0]
    zero = [r["jar"] for r in sc if r["annotated_classes"] == 0]
    na = [r["jar"] for r in rows if r["status"] == "NOT_OBTAINABLE"]
    closure = None
    if class_dir:
        dom = set(os.listdir(class_dir))
        missing = [j for j in mk if j[:-4] not in dom]
        closure = {
            "class_dir_dir_count": len(dom),
            "marker_jars_missing_from_domain": missing,
            "verdict": "PASS" if not missing else "FAIL",
            "reading": ("marker 构件是能暴露注解路由的超集；其全部落在扫描域内 ⇒"
                         " 域外只可能剩 0-marker 构件（无注解路由）或未取到的第三方构件"),
        }
    return {
        "schema": "deployed-marker-census.v1",
        "evidence": "LIVE-DEPLOYED (BOOT-INF/lib 清单) + VERIFIED_STATIC_BYTECODE (直读 .class 常量池)",
        "criterion": ("marker = .class 常量池含 bind/annotation；任何带 HTTP 注解的类必含之，"
                      "故含 marker 是可暴露注解路由的必要条件，0-marker 构件不可能暴露端点"),
        "inventory": meta,
        "total": len(rows),
        "scanned": len(sc),
        "marker_bearing": len(mk),
        "zero_marker": len(zero),
        "not_obtainable": len(na),
        "classes_scanned": sum(r["classes"] for r in sc),
        "marker_jars": mk,
        "not_obtainable_jars": na,
        "closure_over_marker_bearing": closure,
        "limitations": [
            "NOT_OBTAINABLE 的第三方构件 marker 状态未知（本地 maven 与本机缓存均无，Artifactory GAVC 只返回 .pom 兄弟）⇒ 闭包命题只在已扫子集上成立",
            "本器只判「能否暴露注解路由」这一必要条件，不判路由字面量；后者由 tools/enumerate_full_domain_op_surface.py 裁定",
            "jar / class 本体不入 git；本件为复算产物",
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="部署态 544 jar marker 普查（离线只读）")
    ap.add_argument("--inventory", required=True, help="lib_inventory.json（544 jar 清单）")
    ap.add_argument("--class-dir", default=None, help="扫描域 class 根（做闭包检验）")
    ap.add_argument("--emit", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not Path(a.inventory).is_file():
        print(json.dumps({"error": "inventory 不存在", "path": a.inventory},
                         ensure_ascii=False))
        return 2
    payload = build(a.inventory, a.class_dir)
    txt = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if a.emit:
        Path(a.emit).write_text(txt, encoding="utf-8", newline="\n")
        print("WROTE", a.emit)
    if a.json or not a.emit:
        print(txt)
    else:
        print("total=%d scanned=%d marker=%d zero=%d not_obtainable=%d classes=%d" % (
            payload["total"], payload["scanned"], payload["marker_bearing"],
            payload["zero_marker"], payload["not_obtainable"],
            payload["classes_scanned"]))
        c = payload["closure_over_marker_bearing"]
        if c:
            print("closure marker⊆domain: %s (missing %d)" % (
                c["verdict"], len(c["marker_jars_missing_from_domain"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
