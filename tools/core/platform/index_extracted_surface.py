#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把批量抽取产物汇总成「按包 / 按角色」两张索引表（只读输入，产出 JSON+MD）。

为什么需要：84 个包 / 7255 类 / 7 万方法，逐个人读不现实。
本脚本把签名件压成可检索的索引：
  ① 包级概览：每个包的类数/接口数/方法数 + 其主要接口（方法数 top）
  ② 角色分组：按包名后缀把包归到 appservice / facade / starter 等角色
  ③ 方法级检索表：<包>/<类>#<方法>(<参数>) → 返回类型，供查「某能力在哪个类」

产物里**不含**任何工程/环境信息（只有 artifact 名与版本号）。

用法：
  uv run --no-project python tools/core/platform/index_extracted_surface.py \
      --batch-dir docs/audit/artifacts/extension-surface-20261029/batch2 \
      --emit-json docs/audit/artifacts/extension-surface-20261029/batch2/_index.json \
      --emit-md docs/audit/artifacts/extension-surface-20261029/batch2/_INDEX.md
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROLE_RULES = [
    ("facade", lambda a: a.endswith("-facade")),
    ("api", lambda a: a.endswith("-api")),
    ("common", lambda a: a.endswith("-common")),
    ("starter", lambda a: a.startswith("boot-starter-") or a.startswith("udc-starter-")
                         or a.startswith("devops-starter-")),
    ("engine", lambda a: "engine" in a or a.endswith("-spi") or a == "boot-core"),
    ("extension", lambda a: a in ("boot-extend", "boot-spi")),
]


def role_of(artifact: str) -> str:
    for name, pred in ROLE_RULES:
        if pred(artifact):
            return name
    return "other"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-dir", required=True)
    ap.add_argument("--emit-json", required=True)
    ap.add_argument("--emit-md", required=True)
    ap.add_argument("--top-interfaces", type=int, default=8)
    a = ap.parse_args()

    bd = Path(a.batch_dir)
    contracts = defaultdict(list)
    packs = []
    method_index = {}

    for f in sorted(bd.glob("*.json")):
        if f.name.startswith("_"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        ifaces = []
        total_fields = 0
        for c in d.get("classes", []):
            s = c.get("symbols") or {}
            name = s.get("name")
            if not name:
                continue
            total_fields += len(s.get("fields") or [])
            if s.get("kind") == "interface":
                ifaces.append(s)
            for m in s.get("methods") or []:
                key = f"{d['jar'].rsplit('-', 1)[0]}/{name}#{m['name']}"
                method_index.setdefault(key, []).append(
                    {"returns": m["returns"], "args": m["args"]})
        ifaces.sort(key=lambda s: -(s.get("method_count") or 0))
        art = f.stem
        packs.append({
            "artifact": art,
            "version": d.get("jar_path_hint", "").split("/")[0],
            "role": role_of(art),
            "classes": d.get("class_count_scanned"),
            "interfaces": d.get("interfaces"),
            "methods": d.get("total_methods"),
            "fields": total_fields,
            "top_interfaces": [
                {"name": s["name"], "methods": s["method_count"]}
                for s in ifaces[: a.top_interfaces]
            ],
        })
        for s in ifaces:
            contracts[s["name"]].append({
                "artifact": art,
                "methods": s.get("method_count"),
                "extends": s.get("extends"),
            })

    by_role = defaultdict(list)
    for p in packs:
        by_role[p["role"]].append(p["artifact"])

    dup = {k: v for k, v in contracts.items() if len(v) > 1}

    out = {
        "packages": sorted(packs, key=lambda p: p["artifact"]),
        "by_role": {k: sorted(v) for k, v in sorted(by_role.items())},
        "totals": {
            "packages": len(packs),
            "classes": sum(p["classes"] or 0 for p in packs),
            "interfaces": sum(p["interfaces"] or 0 for p in packs),
            "methods": sum(p["methods"] or 0 for p in packs),
            "fields": sum(p["fields"] or 0 for p in packs),
        },
        "method_index": method_index,
        "same_name_interfaces": dup,
    }
    Path(a.emit_json).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = ["# 84 个平台包 · 抽取索引", "",
             f"合计 **{out['totals']['packages']}** 个包 / "
             f"**{out['totals']['classes']}** 个类 / **{out['totals']['interfaces']}** 个接口 / "
             f"**{out['totals']['methods']}** 个方法 / **{out['totals']['fields']}** 个字段", "",
             "> 本索引只含 artifact 名与版本号，无工程/环境信息。", "",
             "## 按角色", ""]
    for role in sorted(out["by_role"]):
        lines.append(f"- **{role}**（{len(out['by_role'][role])}）："
                     + "、".join(f"`{x}`" for x in out["by_role"][role]))
    lines += ["", "## 包级概览（按接口数降序）", "",
              "| artifact | 版本 | 角色 | 类 | 接口 | 方法 | 字段 | 主要接口（方法数）|",
              "|---|---|---|---|---|---|---|---|"]
    for p in sorted(packs, key=lambda p: -(p["interfaces"] or 0)):
        top = "、".join(f"{t['name']}({t['methods']})" for t in p["top_interfaces"][:4])
        lines.append(f"| `{p['artifact']}` | {p['version']} | {p['role']} | {p['classes']} | "
                     f"{p['interfaces']} | {p['methods']} | {p['fields']} | {top} |")
    if dup:
        lines += ["", "## 跨包同名接口（引用前先确认是哪一个）", ""]
        for name, where in sorted(dup.items()):
            lines.append(f"- `{name}`：" + "；".join(
                f"{w['artifact']}({w['methods']})" for w in where))
    Path(a.emit_md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"包 {out['totals']['packages']} / 类 {out['totals']['classes']} / "
          f"接口 {out['totals']['interfaces']} / 方法 {out['totals']['methods']}")
    print(f"同名接口 {len(dup)} 组；方法索引 {len(method_index)} 条")
    print(f"emit -> {a.emit_md}")


if __name__ == "__main__":
    main()
