#!/usr/bin/env python3
"""按「构件（Maven artifact）」逐个导出接口与方法签名。

与 emit_domain_surfaces.py 的区别：
  那个按业务域（bpm/组织/连接器…）合并导出，方便按场景找；
  这个按构件一包一份，覆盖扩展工程 pom 里声明的**每一个**标品依赖——
  你截图的 86 个包，加上后补的 udc-biz 等，一包不缺。

数据源：interfaces.json（classes[].pkg 记录来源构件）。

用法：
  python tools/core/platform/emit_package_surfaces.py \
      --interfaces docs/audit/artifacts/extension-surface-20261029/interfaces.json \
      --emit-dir docs/audit/artifacts/extension-surface-20261029/packages
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

KEY_CLASS_HINTS = ("AppService", "Service", "Utils", "Util", "Helper", "Dao", "Factory",
                   "Manager", "Provider", "Executor", "Template", "Handler", "Builder",
                   "Converter", "Convertor", "Config", "Client")


def sig_of(m: dict) -> str:
    s = m.get("signature", "")
    for p in ("public abstract ", "public static ", "public ", "static "):
        if s.startswith(p):
            s = s[len(p):]
            break
    return s.split(" throws")[0].strip()


def is_annotation(c: dict) -> bool:
    return any("java.lang.annotation.Annotation" in str(x) for x in (c.get("extends") or []))


def render(pkg: str, jar: str | None, classes: dict[str, dict]) -> str:
    ifaces = {fq: c for fq, c in classes.items() if c.get("kind") == "interface" and not is_annotation(c)}
    annos = {fq: c for fq, c in classes.items() if c.get("kind") == "interface" and is_annotation(c)}
    enums = {fq: c for fq, c in classes.items() if c.get("kind") == "enum"}
    key_cls = {fq: c for fq, c in classes.items()
               if c.get("kind") == "class"
               and len(c["methods"]) >= 3
               and any(h in fq.split(".")[-1] for h in KEY_CLASS_HINTS)}
    # 兜底：本构件没有接口、也没有命中关键类（纯自动装配/配置包）→ 列全部类，
    # 否则签名表只剩个头部，等于没内容。
    if not ifaces and not key_cls:
        key_cls = {fq: c for fq, c in classes.items()
                   if c.get("kind") == "class" and c["methods"]}
    total_m = sum(len(c["methods"]) for c in classes.values())

    out = [
        f"# {pkg}：接口与方法签名",
        "",
        "> 自动生成，勿手改。`tools/core/platform/emit_package_surfaces.py` 重跑即可。",
        f"> 构件 `com.seeyon:{pkg}`" + (f"（jar `{Path(jar).name}`）" if jar else ""),
        f"> 规模：{len(classes)} 类 / {len(ifaces)} 接口 / {len(annos)} 注解 / {len(enums)} 枚举"
        f" / {len(key_cls)} 个关键类 / {total_m} 方法。",
        "> 签名逐字来自 javap 原文；已去掉 `public` 前缀与 `throws` 子句。",
        "",
        f"## 一、接口（{len(ifaces)}）",
        "",
    ]
    if not ifaces:
        out += ["（本构件没有接口）", ""]
    for fq, c in sorted(ifaces.items(), key=lambda x: (-len(x[1]["methods"]), x[0])):
        ext = c.get("extends") or []
        ext_s = f" extends {', '.join(x.split('.')[-1] for x in ext)}" if ext else ""
        out += [f"### `{fq.split('.')[-1]}`（{len(c['methods'])} 方法）{ext_s}", "",
                f"`{fq}`", "", "```java"]
        for m in c["methods"]:
            if m["name"].startswith(("lambda$", "access$")):
                continue
            out.append("    " + sig_of(m))
        out += ["```", ""]

    if key_cls:
        out += [f"## 二、关键类（{len(key_cls)}）", ""]
        for fq, c in sorted(key_cls.items(), key=lambda x: (-len(x[1]["methods"]), x[0])):
            out += [f"### `{fq.split('.')[-1]}`（{len(c['methods'])} 方法）", "",
                    f"`{fq}`", "", "```java"]
            for m in c["methods"]:
                if m["name"].startswith(("lambda$", "access$")):
                    continue
                static_s = "static " if "static" in m.get("modifiers", "") else ""
                out.append("    " + static_s + sig_of(m))
            out += ["```", ""]

    if annos:
        out += [f"## 三、注解（{len(annos)}）", "", "| 注解 | 元素 |", "|---|---|"]
        for fq, c in sorted(annos.items()):
            elems = ", ".join(m["name"] for m in c["methods"][:6])
            out.append(f"| `{fq.split('.')[-1]}` | {elems} |")
        out.append("")

    if enums:
        out += [f"## 四、枚举（{len(enums)}）", ""]
        for fq, c in sorted(enums.items()):
            consts = c.get("constants") or []
            tail = "：" + ", ".join(consts[:12]) + (" …" if len(consts) > 12 else "") if consts else ""
            out.append(f"- `{fq.split('.')[-1]}`（{len(consts)} 常量）{tail}")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--emit-dir", required=True)
    a = ap.parse_args()

    data = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    classes = data["classes"]
    sources = data.get("sources") or {}

    by_pkg: dict[str, dict[str, dict]] = collections.defaultdict(dict)
    no_pkg = 0
    for fq, c in classes.items():
        pkg = c.get("pkg")
        if not pkg:
            no_pkg += 1
            pkg = "unknown"
        by_pkg[pkg][fq] = c

    outdir = Path(a.emit_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = []
    for pkg in sorted(by_pkg):
        jar = (sources.get(pkg) or {}).get("jar")
        md = render(pkg, jar, by_pkg[pkg])
        p = outdir / f"{pkg}.md"
        p.write_text(md, encoding="utf-8")
        n_if = md.count("### `")
        rows.append((pkg, len(by_pkg[pkg]), n_if, p.stat().st_size))

    total = sum(r[3] for r in rows)
    print(f"emit-dir {outdir}：{len(rows)} 个构件，合计 {total/1024:.0f} KB")
    for pkg, n_cls, n_sec, size in sorted(rows, key=lambda r: -r[3])[:12]:
        print(f"  {pkg:28s} {size/1024:7.1f} KB  {n_cls:4d} 类  {n_sec:3d} 段")
    if len(rows) < 80:
        print(f"ERR: 只出了 {len(rows)} 个构件，远少于预期 86+；pkg 字段可能没写进索引")
        return 5
    if no_pkg:
        print(f"WARN: {no_pkg} 个类没有 pkg 标记，归到 unknown.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
