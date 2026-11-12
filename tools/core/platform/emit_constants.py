#!/usr/bin/env python3
"""导出「常量类」清单：错误码表、特性常量、系统变量名这类东西的字面值。

javap 加 -constants 后，`public static final String X = "abc";` 会带出值。
这份产物回答：某个错误码常量到底等于什么字符串、某个特性开关的键名是什么。

只导出常量数 >= --min-consts 的类（默认 10），否则 3000+ 个类太碎。

用法：
  python tools/core/platform/emit_constants.py --interfaces <interfaces.json> --emit <constants.md>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--emit", required=True)
    ap.add_argument("--min-consts", type=int, default=10)
    a = ap.parse_args()

    d = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    cs = d["classes"]

    rows = []
    for fq, c in cs.items():
        fv = [f for f in (c.get("fields") or []) if "value" in f]
        if len(fv) >= a.min_consts:
            rows.append((fq, c["kind"], fv, c.get("pkg")))
    rows.sort(key=lambda x: (-len(x[2]), x[0]))

    total_consts = sum(len(r[2]) for r in rows)
    out = [
        "# 常量类清单（带字面值）",
        "",
        "> 自动生成，勿手改。`tools/core/platform/emit_constants.py` 重跑即可。",
        f"> 来源 `interfaces.json`（javap -p -constants）。只列常量数 >= {a.min_consts} 的类。",
        f"> 共 **{len(rows)} 个类 / {total_consts} 个常量**。全平台共 10257 个字段带字面值，"
        "其余散在小类里，按需查 `packages/<构件>.md`。",
        "",
        "## 用途",
        "",
        "- **错误码**：`ConsistenceErrorCode` 529 个（`UDC_CE_0001` 起）、`CapabilityErrorCode` 141 个",
        "- **特性/字段键名**：`FeatureConstant` 240 个（`enterpriseInfo` 这类 camelCase 键）",
        "- **表名/前缀**：`UdcCommonConstant` 187 个（`app_attachment` 这类物理表名）",
        "- **函数名**：`DateFunction` 230 / `TextFunction` 130 / `ListFunction` 109（表达式引擎函数名）",
        "- **系统变量名**：`SystemVariableUtils` 288",
        "",
        "## 逐类清单",
        "",
    ]
    for fq, kind, fv, pkg in rows:
        out += [f"### `{fq.split('.')[-1]}`（{len(fv)} 常量，{kind}，`{pkg}`）", "",
                f"`{fq}`", "", "| 常量 | 值 |", "|---|---|"]
        for f in fv:
            v = str(f["value"]).replace("|", "\\|")
            if len(v) > 100:
                v = v[:100] + "…"
            out.append(f"| `{f['name']}` | `{v}` |")
        out.append("")

    p = Path(a.emit)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out), encoding="utf-8")
    print(f"constants  {len(rows)} 个类 / {total_consts} 个常量 → {p}（{p.stat().st_size//1024} KB）")
    if len(rows) < 50:
        print("ERR: 常量类过少，-constants 可能没生效")
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
