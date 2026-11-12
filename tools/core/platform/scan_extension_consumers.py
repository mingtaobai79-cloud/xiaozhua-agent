#!/usr/bin/env python3
"""扫 jar 内 class 字节，找「谁引用了这个接口」——即在常量池里出现该类型的类。

回答的问题：128 个扩展点里，哪些平台代码**真的在用它**（会被调），
哪些零引用（纯扩展位 / 死代码 / 只能靠元数据驱动）。

为什么扫字节而不是 javap：javap -p 只给签名，看不到方法体里
`List<ApplicationInnerReference>` 注入、`getBeansOfType(Xxx.class)` 这类调用。

判据：class 文件常量池里出现 `com/seeyon/xxx/Iface` 这个 UTF-8 串。
  - 排除接口自身的 class
  - 排除接口所在包内的类（同包引用不代表平台在调）

用法：
  python tools/core/platform/scan_extension_consumers.py \
      --interfaces docs/audit/artifacts/extension-surface-20261029/interfaces.json \
      --repo <MAVEN_REPO>/com/seeyon \
      --emit docs/audit/artifacts/extension-surface-20261029/consumers.json
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path


def resolve_jar(repo: Path, pkg: str, jar_name: str) -> Path | None:
    p = Path(jar_name)
    if p.is_absolute() and p.exists():
        return p
    d = repo / pkg
    if d.is_dir():
        hits = sorted(d.rglob(Path(jar_name).name))
        if hits:
            return hits[-1]
        allj = sorted(d.rglob("*.jar"))
        if allj:
            return allj[-1]
    hits = sorted(repo.rglob(Path(jar_name).name))
    return hits[-1] if hits else None


def is_annotation(c: dict) -> bool:
    return any("java.lang.annotation.Annotation" in str(x) for x in (c.get("extends") or []))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--repo", default="<MAVEN_REPO>/com/seeyon")
    ap.add_argument("--emit", required=True)
    ap.add_argument("--scope", default="com.seeyon.udc",
                    help="只查这些前缀下的接口（默认 UDC 扩展点域）")
    a = ap.parse_args()

    data = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    cs = data["classes"]
    sources = data["sources"]

    # 待查扩展点：scope 下、真接口、非注解、带 abstract（= 有实现价值）
    targets = {}
    for fq, c in cs.items():
        if not fq.startswith(a.scope) or c.get("kind") != "interface" or is_annotation(c):
            continue
        if not any("abstract" in m.get("modifiers", "") for m in c["methods"]):
            continue
        targets[fq] = c
    print(f"待查扩展点 {len(targets)} 个（{a.scope} 下带 abstract 的真接口）", flush=True)

    needles = {fq: fq.replace(".", "/").encode() for fq in targets}
    pkg_of = {fq: fq.rsplit(".", 1)[0] for fq in targets}

    repo = Path(a.repo)
    consumers: dict[str, list] = defaultdict(list)
    scanned = 0
    for pkg, info in sorted(sources.items()):
        jar = resolve_jar(repo, pkg, info.get("jar") or "")
        if not jar:
            continue
        try:
            zf = zipfile.ZipFile(jar)
        except Exception:  # noqa: BLE001
            continue
        with zf:
            for name in zf.namelist():
                if not name.endswith(".class") or name.startswith("META-INF/"):
                    continue
                cls = name[:-6].replace("/", ".")
                try:
                    b = zf.read(name)
                except Exception:  # noqa: BLE001
                    continue
                scanned += 1
                for fq, needle in needles.items():
                    if fq == cls:
                        continue                      # 接口自身
                    if needle in b:
                        same = cls.rsplit(".", 1)[0] == pkg_of[fq]
                        consumers[fq].append({"cls": cls, "src_pkg": pkg, "same_pkg": same})
        print(f"  {pkg:28s} 累计扫描 {scanned} 个 class，命中接口 {len(consumers)} 个", flush=True)

    # 只保留 target 里的接口（needles 已限定），跨包引用才是「平台在用」的强证据
    rows = []
    for fq, c in targets.items():
        refs = consumers.get(fq) or []
        cross = [r for r in refs if not r["same_pkg"]]
        intra = [r for r in refs if r["same_pkg"]]
        rows.append({
            "iface": fq,
            "simple": fq.split(".")[-1],
            "methods": len(c["methods"]),
            "pkg": c.get("pkg"),
            "ref_count": len(refs),
            "cross_count": len(cross),
            "intra_count": len(intra),
            "cross_pkgs": sorted({r["src_pkg"] for r in cross}),
            "refs": [f"{r['src_pkg']}:{r['cls']}" for r in refs[:40]],
        })

    out = {"scope": a.scope, "scanned_classes": scanned, "targets": len(rows), "rows": rows}
    Path(a.emit).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    used = [r for r in rows if r["ref_count"]]
    cross = [r for r in rows if r["cross_count"]]
    intra_only = [r for r in rows if r["ref_count"] and not r["cross_count"]]
    zero = [r for r in rows if not r["ref_count"]]
    print(f"\n扫描 {scanned} 个 class / 扩展点 {len(rows)} 个")
    print(f"  跨包被引用（平台真在用）    {len(cross)}")
    print(f"  只有同包引用（包内自用）    {len(intra_only)}")
    print(f"  零引用（连实现都没有）      {len(zero)}")
    print("\n跨包引用最多的 15 个：")
    for r in sorted(cross, key=lambda x: -x["cross_count"])[:15]:
        print(f"  {r['cross_count']:4d} 跨包  {r['simple']:40s} {len(r['cross_pkgs'])} 个来源包")
    print("\n零引用：")
    for r in sorted(zero, key=lambda x: x["simple"]):
        print(f"        {r['simple']:44s} {r['methods']:2d} 方法  [{r['pkg']}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
