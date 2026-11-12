#!/usr/bin/env python3
"""把 batch3（21 个 *-biz 实现 jar）的抽取结果合并进 interfaces.json。

为什么要合：biz jar 里有 433 个 AppService 接口是 facade 索引里没有的，
它们才是客开真正能调的入口（@AppService 注册成 Bean，泛化调用可直达）。

合并规则：
  · 已存在的全名不覆盖（facade 版本优先，版本更稳定）
  · 新增的补 pkg（构件名）和 implements（batch3 把 implements 混在 extends 里）
  · 只合接口和 DTO 类，不合 Impl / Dao（那些是实现，不是调用面）
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

RE_IMPL = re.compile(r"implements\s+([\w.$<>, ]+)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--batch", required=True)
    ap.add_argument("--emit", required=True)
    a = ap.parse_args()

    d = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    cs = d["classes"]
    before = len(cs)

    added_iface = added_class = skipped_impl = 0
    for f in sorted(Path(a.batch).glob("*.json")):
        b = json.loads(f.read_text(encoding="utf-8"))
        pkg = b.get("jar", "").replace(".jar", "").rsplit("-", 1)[0] or f.stem
        for c in b.get("classes") or []:
            s = c.get("symbols") or {}
            if not s:
                continue
            fq = c["entry"][:-6].replace("/", ".")
            if "$" in fq:
                continue
            short = fq.split(".")[-1]
            # 不合实现层
            if short.endswith(("Impl", "Dao", "Mapper", "Repository", "Controller")):
                skipped_impl += 1
                continue
            if fq in cs:
                continue
            ext = s.get("extends") or ""
            impls = []
            m = RE_IMPL.search(ext)
            if m:
                impls = [x.strip().split("<")[0] for x in m.group(1).split(",") if x.strip()]
            cs[fq] = {
                "kind": s.get("kind", "class"),
                "name": short,
                "pkg": pkg,
                "extends": ext if "implements" not in ext else "",
                "implements": impls,
                "methods": s.get("methods") or [],
                "fields": s.get("fields") or [],
                "source": "biz-jar",
            }
            if s.get("kind") == "interface":
                added_iface += 1
            else:
                added_class += 1

    d["classes"] = cs
    p = Path(a.emit)
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    print(f"类 {before} → {len(cs)}（+{added_iface} 接口 / +{added_class} 类；跳过 {skipped_impl} 个实现层）")
    svc = [k for k, v in cs.items() if v.get("kind") == "interface" and k.split(".")[-1].endswith("AppService")]
    print(f"AppService 接口 {len(svc)}")
    if added_iface < 100:
        print("WARN: 新增接口过少，batch3 可能没抽全")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
