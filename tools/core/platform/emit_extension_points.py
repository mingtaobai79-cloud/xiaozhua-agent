#!/usr/bin/env python3
"""把「UDC 可 implements 接口」和「平台自带实现类」拼成落地表。

回答的问题：我要扩展 X 能力时，平台有没有现成实现可以参考/继承？还是纯扩展位得自己全写？

数据源：interfaces.json（classes[].implements 给出接口→实现的边）。
分类：
  有实现类   → 平台至少有一个实现，可继承或参照；重点看 impl 数多的（族主）
  纯扩展位   → 平台零实现，必须自己从零实现；写之前先想清楚注册方式

用法：
  python tools/core/platform/emit_extension_points.py \
      --interfaces docs/audit/artifacts/extension-surface-20261029/interfaces.json \
      --emit docs/audit/artifacts/extension-surface-20261029/extension-points.md
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--emit", required=True)
    a = ap.parse_args()

    data = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    cs = data["classes"]
    ifaces = {fq: c for fq, c in cs.items() if c.get("kind") == "interface"}

    # UDC 里可 implements 的接口：带 abstract、且不是 AppService 调用面
    points = [fq for fq, c in ifaces.items()
              if fq.startswith("com.seeyon.udc")
              and not fq.split(".")[-1].endswith("AppService")
              and any("abstract" in m.get("modifiers", "") for m in c["methods"])]
    if not points:
        print("ERR: 没找到 UDC 扩展点接口，抽取口径可能坏了")
        return 5

    impl: dict[str, list[str]] = collections.defaultdict(list)
    for fq, c in cs.items():
        if c.get("kind") == "interface":
            continue
        for i in (c.get("implements") or []):
            base = i.split("<")[0]
            if base in ifaces and base in points:
                impl[base].append(fq)

    def is_annotation(fq: str) -> bool:
        return any("java.lang.annotation.Annotation" in str(x) for x in (ifaces[fq].get("extends") or []))

    # 注解（@interface）不是能 implements 的接口，单独分组，别混在扩展点里
    annos = [p for p in points if is_annotation(p)]
    real = [p for p in points if not is_annotation(p)]
    with_impl = sorted([p for p in real if impl[p]], key=lambda p: (-len(impl[p]), p))
    pure = sorted([p for p in real if not impl[p]], key=lambda p: p)

    def abs_count(fq: str) -> int:
        return len([m for m in ifaces[fq]["methods"] if "abstract" in m.get("modifiers", "")])

    def pkg_of(fq: str) -> str:
        return fq.rsplit(".", 1)[0]

    out = [
        "# UDC 扩展点落地表：接口 × 平台实现",
        "",
        "> 自动生成，勿手改。`tools/core/platform/emit_extension_points.py` 重跑即可。",
        f"> 共 {len(points)} 个带 abstract 的 UDC 接口，其中 **{len(real)} 个是真接口**："
        f"**{len(with_impl)} 个平台已有实现**（可继承或参照），**{len(pure)} 个是纯扩展位**（零实现，自己全写）。",
        f"> 另 **{len(annos)} 个是注解（@interface）**，不是 implements 的对象，见文末。",
        "> 「abstract」= 必须实现的方法个数；「impl」= 平台自带实现类个数。",
        "> 重名接口（如 `BaseNode` / `BaseTrigger` / `Functor`）出现在不同包，implements 时认全名。",
        "",
        f"## 一、平台已有实现（{len(with_impl)} 个）—— 优先看 impl 多的，那是族主",
        "",
        "| 接口 | abstract | impl | 代表实现类 | 接口所在包 |",
        "|---|---|---|---|---|",
    ]
    for fq in with_impl:
        reps = ", ".join(f"`{x.split('.')[-1]}`" for x in impl[fq][:3])
        if len(impl[fq]) > 3:
            reps += f" …+{len(impl[fq]) - 3}"
        out.append(f"| `{fq.split('.')[-1]}` | {abs_count(fq)} | {len(impl[fq])} | {reps} | `{pkg_of(fq)}` |")

    out += [
        "",
        f"## 二、纯扩展位（{len(pure)} 个）—— 零实现，自己从零写",
        "",
        "| 接口 | abstract | 接口所在包 |",
        "|---|---|---|",
    ]
    for fq in pure:
        out.append(f"| `{fq.split('.')[-1]}` | {abs_count(fq)} | `{pkg_of(fq)}` |")
    out += ["", f"## 三、注解（{len(annos)} 个）—— 贴在代码上，不是 implements", "",
            "| 注解 | 参数 | 所在包 |", "|---|---|---|"]
    for fq in sorted(annos):
        args = ", ".join(m["name"] for m in ifaces[fq]["methods"][:4])
        out.append("| `%s` | %s | `%s` |" % (fq.split(".")[-1], args, pkg_of(fq)))
    out.append("")

    p = Path(a.emit)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out), encoding="utf-8")

    # 闸门：每个扩展点必须出现在产物里
    txt = p.read_text(encoding="utf-8")
    missing = [fq for fq in points if f"`{fq.split('.')[-1]}`" not in txt]
    if missing:
        print(f"ERR: {len(missing)} 个扩展点没写进表，例：{missing[:3]}")
        return 5

    print(f"extension-points  {len(points)} 扩展点（有实现 {len(with_impl)} / 纯扩展位 {len(pure)}）"
          f" → {a.emit}（{p.stat().st_size} B）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
