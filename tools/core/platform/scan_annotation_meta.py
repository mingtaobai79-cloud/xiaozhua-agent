#!/usr/bin/env python3
"""抓 109 个注解的元信息：@Target / @Retention / 其他元注解（@Service/@Component…）。

为什么必须抓：注解不能 implements，但「能贴在类上还是方法上」「运行期能不能反射读到」
决定了它怎么用。`@Retention(SOURCE)` 的注解编译完就没了，靠它做运行时判断必失败。

做法：对每个注解类跑 `javap -v`，解常量池 + RuntimeVisibleAnnotations 块。
只做这一件事，不重抽全量（-v 输出巨大，91 jar 全量重抽不划算）。

用法：
  python tools/core/platform/scan_annotation_meta.py \
      --interfaces <interfaces.json> --repo <MAVEN_REPO>/com/seeyon --emit <annotations.md>
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

JAVAP = "<LOCAL_ROOT>/java/bin/javap.exe"
CP_UTF8 = re.compile(r"^#(\d+) = Utf8\s+(.*)$")
ANN_LINE = re.compile(r"^\s+\d+:\s+#(\d+)\((.*)\)\s*$")


def resolve_jar(repo: Path, pkg: str) -> Path | None:
    d = repo / pkg
    if not d.is_dir():
        return None
    jars = sorted(d.rglob("*.jar"), key=lambda p: p.name)
    return jars[-1] if jars else None


def parse_cp(text: str) -> dict[int, str]:
    cp = {}
    for line in text.splitlines():
        m = CP_UTF8.match(line.strip())
        if m:
            cp[int(m.group(1))] = m.group(2).strip()
    return cp


def deref(token: str, cp: dict[int, str]) -> str:
    """把 `#22` / `e#21.#22` / `Ljava/lang/annotation/Target;` 解成 `TYPE` / `Target`。"""
    token = str(token).strip().lstrip("#")
    if "." in token:
        token = token.split(".")[-1].lstrip("#")
    v = cp.get(int(token), "") if token.isdigit() else token
    # 只剥真正的类型描述符 `Lcom/x/Y;`，别把 LOCAL_VARIABLE 的首字母 L 也剥了
    if v.startswith("L") and v.endswith(";"):
        v = v[1:-1]
    v = re.sub(r"/", ".", v)
    return v.split(".")[-1]


def parse_annotations(text: str) -> list[dict]:
    cp = parse_cp(text)
    out, inside = [], False
    for line in text.splitlines():
        if line.startswith("RuntimeVisibleAnnotations:"):
            inside = True
            continue
        if inside:
            if not line.strip() or not line.startswith(" "):
                break
            m = ANN_LINE.match(line)
            if not m:
                continue
            ann_type = deref(m.group(1), cp)
            body = m.group(2)
            params: dict[str, list[str]] = {}
            # `#7=[e#21.#22]` 或 `#7=[e#21.#22,e#21.#23]`
            for pm in re.finditer(r"#(\d+)=\[([^\]]+)\]", body):
                pname = deref(pm.group(1), cp)
                vals = [deref(x.split(".")[-1], cp) for x in pm.group(2).split(",") if "#" in x]
                params[pname] = vals
            # `#7=e#21.#22`（单值）
            for pm in re.finditer(r"#(\d+)=e#\d+\.(?:#(\d+)|(\w+))", body):
                pname = deref(pm.group(1), cp)
                params.setdefault(pname, []).append(deref(pm.group(2) or pm.group(3), cp))
            out.append({"type": ann_type, "params": params})
            if not body:  # 无参注解，下一个 `N:` 行是同级
                continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interfaces", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--emit", required=True)
    a = ap.parse_args()

    d = json.loads(Path(a.interfaces).read_text(encoding="utf-8"))
    cs = d["classes"]
    annos = {fq: c for fq, c in cs.items()
             if c["kind"] == "interface"
             and any("java.lang.annotation.Annotation" in str(x) for x in (c.get("extends") or []))}

    repo = Path(a.repo)
    jar_cache: dict[str, Path | None] = {}
    rows, failed = [], []

    for i, (fq, c) in enumerate(sorted(annos.items()), 1):
        pkg = c.get("pkg") or ""
        if pkg not in jar_cache:
            jar_cache[pkg] = resolve_jar(repo, pkg)
        jar = jar_cache[pkg]
        if not jar:
            failed.append((fq, "jar 未找到"))
            continue
        try:
            r = subprocess.run([JAVAP, "-v", "-cp", str(jar), fq],
                               capture_output=True, text=True, timeout=60,
                               encoding="utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            failed.append((fq, "javap 超时"))
            continue
        if r.returncode != 0:
            failed.append((fq, f"javap rc={r.returncode}"))
            continue
        metas = parse_annotations(r.stdout)
        target, retention, others = [], "", []
        for m in metas:
            t = m["type"]
            if t == "Target":
                target = m["params"].get("value", [])
            elif t == "Retention":
                retention = (m["params"].get("value") or ["?"])[0]
            elif t in ("Documented", "Inherited", "Repeatable", "Native"):
                others.append(t)
            else:
                others.append(t)
        rows.append({"fq": fq, "name": fq.split(".")[-1], "pkg": pkg,
                     "target": target, "retention": retention, "others": others,
                     "elements": [m["name"] for m in c["methods"]],
                     "jar": jar.name})
        if i % 20 == 0:
            print(f"  ... {i}/{len(annos)}", flush=True)

    rows.sort(key=lambda x: (x["retention"] != "RUNTIME", -len(x["elements"]), x["fq"]))

    out = ["# 平台注解速查（109 个 @interface）", "",
           "> 自动生成，勿手改。`tools/core/platform/scan_annotation_meta.py` 重跑即可。",
           "> 来源：`javap -v` 的 RuntimeVisibleAnnotations 块（解常量池）。",
           f"> 共 **{len(rows)} 个**注解（另有 {len(failed)} 个未能解析）。", "",
           "## 怎么用", "",
           "- **@Target** 决定能贴哪：`TYPE`=类/接口、`METHOD`=方法、`FIELD`=字段、",
           "  `PARAMETER`=参数、`ANNOTATION_TYPE`=元注解、`CONSTRUCTOR`=构造器",
           "- **@Retention** 决定何时有效：`RUNTIME`=运行期可反射读到（扩展点都是这个）、",
           "  `CLASS`=编译进字节码但反射读不到、`SOURCE`=编译完就丢（只给编译器/APT 用）",
           "- **元注解里的 @Service / @Component** = 贴了这个注解就等于贴了 Spring 组件注解，",
           "  会自动被扫描注册——这是「写了代码怎么被平台发现」的一条暗线。", ""]

    # 按 Retention 分组
    for ret in ("RUNTIME", "CLASS", "SOURCE", "?"):
        grp = [r for r in rows if (r["retention"] or "?") == ret]
        if not grp:
            continue
        out += [f"## @Retention({ret}) —— {len(grp)} 个", ""]
        out += ["| 注解 | 元素数 | @Target | 元注解（Spring 等） | 构件 |",
                "|---|---|---|---|---|"]
        for r in grp:
            tgt = ", ".join(r["target"]) if r["target"] else "—"
            oth = ", ".join(x for x in r["others"] if x not in ("Documented", "Inherited")) or "—"
            out.append(f"| `{r['name']}` | {len(r['elements'])} | {tgt} | {oth} | `{r['pkg']}` |")
        out.append("")

    # 元素最多的注解（贴代码时要知道填什么）
    out += ["## 元素最多的 15 个（贴之前先看要填什么）", ""]
    for r in sorted(rows, key=lambda x: -len(x["elements"]))[:15]:
        els = ", ".join(r["elements"][:14]) + (" …" if len(r["elements"]) > 14 else "")
        out.append(f"- **`{r['name']}`**（{len(r['elements'])} 元素，@Target({', '.join(r['target']) or '—'})）：{els or '无元素'}")
    out.append("")

    out += ["## 全部逐个（含全名与 jar）", "",
            "| 注解 | 全名 | Retention | Target | 构件 / jar |", "|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| `{r['name']}` | `{r['fq']}` | {r['retention'] or '?'} | "
                   f"{', '.join(r['target']) or '—'} | `{r['pkg']}` / {r['jar']} |")
    out.append("")

    if failed:
        out += ["## 未能解析的", ""]
        for fq, why in failed:
            out.append(f"- `{fq}`：{why}")
        out.append("")

    p = Path(a.emit)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out), encoding="utf-8")
    rt = sum(1 for r in rows if r["retention"] == "RUNTIME")
    print(f"annotations  {len(rows)} 个（RUNTIME {rt}）失败 {len(failed)} → {p}（{p.stat().st_size//1024} KB）")
    if len(rows) < 90:
        print("ERR: 解析出的注解过少")
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
