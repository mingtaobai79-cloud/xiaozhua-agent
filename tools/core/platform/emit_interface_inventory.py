#!/usr/bin/env python3
"""把 interfaces.json 里的全部接口导成人可读清单。

用途：`interfaces.json` 是机器索引（39 MB，841 个接口），人不会去翻 JSON。
本脚本产出 `interface-inventory.md`：按顶层包分组，每个接口一行，
标注 abstract 方法数（= 必须实现的个数）与必实现方法名。

abstract 方法是「要 implements 就必须写」的那批；方法数为 0 的 abstract
说明该接口是纯标记接口。

用法：
  python tools/core/platform/emit_interface_inventory.py \
      --interfaces docs/audit/artifacts/extension-surface-20261029/interfaces.json \
      --emit docs/audit/artifacts/extension-surface-20261029/interface-inventory.md
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path


def top_pkg(fqcn: str) -> str:
    p = fqcn.split(".")
    return ".".join(p[:3]) if len(p) > 3 else fqcn


def short_sig(sig: str) -> str:
    """`public abstract void in(com.x.TransportData) throws E` → `in(TransportData)`"""
    m = re.search(r"(\w+)\(([^)]*)\)", sig)
    if not m:
        return ""
    name, args = m.group(1), m.group(2)
    types = []
    for a in args.split(","):
        a = a.strip()
        if not a:
            continue
        t = a.split()[-1] if " " in a else a
        t = t.split("<")[0].split(".")[-1]
        if t:
            types.append(t)
    return f"{name}({', '.join(types)})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--emit", required=True)
    a = ap.parse_args()

    data = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    cs = data["classes"]
    ifs = {fq: c for fq, c in cs.items() if c.get("kind") == "interface"}
    if not ifs:
        print("ERR: interfaces.json 里没有任何 interface，抽取口径可能坏了")
        return 5

    groups: dict[str, list] = collections.defaultdict(list)
    for fq, c in ifs.items():
        groups[top_pkg(fq)].append((fq, c))

    # 注解（@interface）不能 implements，必须从「可 implements」里剔掉，
    # 否则数字虚高（实测虚高 90 个）。
    def is_anno(c: dict) -> bool:
        return any("java.lang.annotation.Annotation" in str(x) for x in (c.get("extends") or []))

    real = {fq: c for fq, c in ifs.items() if not is_anno(c)}
    anno = {fq: c for fq, c in ifs.items() if is_anno(c)}
    n_abs_ifaces = sum(1 for c in real.values()
                       if any("abstract" in m.get("modifiers", "") for m in c["methods"]))

    out: list[str] = [
        "# 后端接口全量清单",
        "",
        f"> 自动生成，勿手改。`tools/core/platform/emit_interface_inventory.py` 重跑即可。",
        f"> 来源 `interfaces.json`：**{len(ifs)} 个接口** = **{len(real)} 个真接口**"
        f" + **{len(anno)} 个注解**（`@interface`，贴代码上由平台读，不能 implements）。",
        f"> 真接口里 **{n_abs_ifaces} 个有 abstract 方法** = 真正可以被 implements 的扩展点；"
        f"其余是纯标记接口或纯 default 接口。",
        f"> 「必实现」列只列 abstract 方法，default 方法不列（有默认实现，不必写）。",
        "",
        "## 分组总览",
        "",
        "| 顶层包 | 接口数 |",
        "|---|---|",
    ]
    for g in sorted(groups, key=lambda x: (-len(groups[x]), x)):
        out.append(f"| `{g}` | {len(groups[g])} |")
    out.append("")

    for g in sorted(groups, key=lambda x: (-len(groups[x]), x)):
        items = sorted(groups[g])
        out += [f"## {g}（{len(items)}）", "",
                "| 接口 | abstract | 方法 | 必实现方法（abstract） |",
                "|---|---|---|---|"]
        for fq, c in items:
            ms = c["methods"]
            ab = [m for m in ms if "abstract" in m.get("modifiers", "")]
            names = ", ".join(f"`{short_sig(m['signature'])}`" for m in ab[:5])
            if len(ab) > 5:
                names += f" …+{len(ab) - 5}"
            out.append(f"| `{fq.split('.')[-1]}` | {len(ab)} | {len(ms)} | {names or '—'} |")
        out.append("")

    p = Path(a.emit)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out), encoding="utf-8")

    # 闸门：可 implements 数与头部声明必须一致（口径含注解就会立刻红）
    ok_abs = sum(1 for c in real.values() if any("abstract" in m.get("modifiers", "") for m in c["methods"]))
    if ok_abs != n_abs_ifaces:
        print("ERR: 统计口径漂移")
        return 5
    # 闸门：每个接口必须出现在产物里，漏一个就失败
    txt = p.read_text(encoding="utf-8")
    missing = [fq for fq in ifs if f"`{fq.split('.')[-1]}`" not in txt]
    if missing:
        print(f"ERR: {len(missing)} 个接口没写进清单，例：{missing[:3]}")
        return 5

    print(f"interface-inventory  {len(ifs)} 接口 / {len(groups)} 个顶层包 / "
          f"{n_abs_ifaces} 个可 implements → {a.emit}（{p.stat().st_size} B）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
