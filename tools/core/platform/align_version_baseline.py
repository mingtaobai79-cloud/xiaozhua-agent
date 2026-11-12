#!/usr/bin/env python3
"""版本基线对齐：把事实格里的旧数字换成重抽后的真值，并生成 BASELINE.md。

首轮抽取取了旧版本（boot 5.3.358 / udc 5.3.517），重抽到 pom 对应版本后：
  类 9652→10414 / 方法 98328→106005 / method_index 37998→41152
  接口 1017→1145 / 可 implements 752→845
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path("<SEEYON_AGENT_ROOT>")
ART = ROOT / "docs/audit/artifacts/extension-surface-20261029"

NUM_MAP = [
    ("9652 类", "10414 类"),
    ("98328 方法", "106005 方法"),
    ("37998 个方法名", "41152 个方法名"),
    ("37998 method_index", "41152 method_index"),
    ("1017 个接口", "1145 个接口"),
    ("752 个带 abstract", "845 个带 abstract"),
    ("752 个可 implements", "845 个可 implements"),
    ("（91 构件 / 9652 类）", "（91 构件 / 10414 类）"),
]

TARGETS = [
    ROOT / "core/facts/standard-product/udc-microflow-extend-interfaces.md",
    ROOT / "core/facts/standard-product/extension-point-decision-table.md",
    ROOT / "core/facts/INDEX.md",
]


def fix_domain_tables() -> None:
    """domains 规模表 + packages 表的数字（只有 organization / formconvert / 总量变了）。"""
    p = ROOT / "core/facts/standard-product/standard-product-appservice-surfaces.md"
    t = p.read_text(encoding="utf-8")
    t = t.replace("| 组织架构 | `organization.md` | 51 | 3 | 6108 |",
                  "| 组织架构 | `organization.md` | 55 | 3 | 6409 |")
    t = t.replace("| 单据转文档 | `formconvert.md` | 2 | 14 | 401 |",
                  "| 单据转文档 | `formconvert.md` | 2 | 14 | 402 |")
    t = t.replace("共 **91 份**（扩展工程 pom 里的 86 个标品构件 + 后补的 udc-biz / udc-web / udc-cicd /\n"
                  "udc-extend / udc-plugin-api），合计 3.0 MB。",
                  "共 **91 份**（扩展工程 pom 里的 86 个标品构件 + 后补的 udc-biz / udc-web / udc-cicd /\n"
                  "udc-extend / udc-plugin-api），合计 3.1 MB。")
    t = t.replace("| `boot-core` | 102 KB | 507 | 134 |", "| `boot-core` | 102 KB | 512 | 134 |")
    t = t.replace("| `organization-facade` | 89 KB | 391 | 55 |", "| `organization-facade` | 93 KB | 414 | 59 |")
    t = t.replace("| `udc-starter-runtime` | 124 KB | 306 | 104 |", "| `udc-starter-runtime` | 124 KB | 307 | 104 |")
    p.write_text(t, encoding="utf-8")
    print(f"  {p.name} 域/包表格已对齐")


def write_baseline() -> None:
    data = json.loads((ART / "interfaces.json").read_text(encoding="utf-8"))
    sources = data["sources"]
    rows = []
    for pkg, info in sorted(sources.items()):
        jar = info.get("jar") or ""
        m = re.search(r"-(\d+\.\d+(?:\.\d+)*)\.jar$", jar)
        rows.append((pkg, m.group(1) if m else "?", info.get("classes", 0), info.get("total_methods", 0)))
    vers: dict[str, list[str]] = {}
    for _, v, _, _ in rows:
        vers.setdefault(v, []).append(_)
    lines = [
        "# 签名面版本基线",
        "",
        "> 自动生成，勿手改。`tools/core/platform/rebuild_surfaces.py` 重抽后重跑本脚本即可。",
        "",
        "本目录下 `interfaces.json` / `packages/` / `domains/` / `interface-inventory.md` /",
        "`extension-points.md` / `registration-scan.json` **全部基于下表版本**。",
        "换版本 = 重抽该构件 → 重跑 emit，不要混用两个版本的签名。",
        "",
        f"## 汇总：{len(rows)} 个构件 / {len(vers)} 个版本",
        "",
        "| 版本 | 构件数 |",
        "|---|---|",
    ]
    for v, pkgs in sorted(vers.items(), key=lambda x: -len(x[1])):
        lines.append(f"| `{v}` | {len(pkgs)} |")
    lines += ["", "## 逐构件", "", "| 构件 | 版本 | 类 | 方法 |", "|---|---|---|---|"]
    for pkg, v, n, m in rows:
        lines.append(f"| `{pkg}` | `{v}` | {n} | {m} |")
    lines += [
        "",
        "## 遇到新版本怎么补（增量约定）",
        "",
        "1. 只重抽变了的构件：`rebuild_surfaces.py --interfaces <interfaces.json> --out-dir <batch2> --only-changed`",
        "   （脚本自动取仓库里该构件的最新版本目录）",
        "2. 重跑链条：`index_backend_interfaces.py` → `emit_interface_inventory.py` /",
        "   `emit_extension_points.py` / `emit_domain_surfaces.py` / `emit_package_surfaces.py` /",
        "   `scan_registration.py`",
        "3. 重跑本脚本刷新版本表；事实格里与新版本冲突的数，改成新值并在 §9 Evidence 记新版本。",
        "",
        "## 当前基线不等于客户环境",
        "",
        "基线版是**仓库里该构件的最新版**，客户 pom 里可能写别的版本（如截图中的 udc 族 5.3.605、",
        "boot 族 5.3.600/5.3.603）。签名差一个参数类型就编译不过——",
        "真按某客户环境写代码时，先按该环境 pom 版本重抽对应构件，不要直接照抄本基线。",
    ]
    out = ART / "BASELINE.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"  {out.name}：{len(rows)} 构件 / {len(vers)} 个版本 → {out.stat().st_size} B")


def main() -> int:
    print("对齐事实格数字：")
    for p in TARGETS:
        t = p.read_text(encoding="utf-8")
        orig = t
        for a, b in NUM_MAP:
            t = t.replace(a, b)
        if t != orig:
            p.write_text(t, encoding="utf-8")
            print(f"  {p.name} 已更新")
        else:
            print(f"  {p.name} 无需改动")
    fix_domain_tables()
    write_baseline()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
