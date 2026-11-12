#!/usr/bin/env python3
"""从本地 node_modules 里抽出前端自定义页面可用组件清单。

背景：UDC 自定义页面的组件来自 npm 包（`@seeyon/ui`、`@seeyon/udc-runtime-core`、
`@seeyon/biz-*` …），没有公开文档站。写页面时「这个组件叫什么、能传哪些属性」
只能翻 node_modules 里的 .d.ts。本脚本把 .d.ts 摊平成可 grep 的索引。

.d.ts 里组件的三种写法都要认：

    export declare const TagDisplay: ({ value, options, size }: any) => JSX.Element;
    declare const Button: React.FC<ButtonProps>;
    export type ButtonProps = Omit<AdButtonProps,'onClick'> & { isDebounce?: boolean };

用法：

    python tools/build_component_index.py --modules <pc/node_modules>
    python tools/build_component_index.py --modules <...> --pkg ui --pkg biz-org-tree

输出（TSV，一行一个属性；组件本身那行 prop 为 `-`）：

    pkg<TAB>version<TAB>component<TAB>prop<TAB>type

诚实边界：很多组件是 `: any` 透传，属性名可列、类型拿不到（记为 `any`），
脚本会在末尾打印这个比例，别把 `any` 当成真实类型。
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "audit" / "reference" / "ui-components.txt.gz"

DECL_RE = re.compile(r"(?:export\s+)?declare\s+const\s+([A-Z]\w*)\s*[:=]", re.M)
DESTRUCT_RE = re.compile(
    r"(?:const|let|var)\s+([A-Z]\w*)\s*[:=]\s*\(\s*\{([^}]*)\}\s*(?::\s*([\w.<>\[\]| ]+))?\s*\)")
FC_RE = re.compile(r"([A-Z]\w*)\s*[:=][^;\n]*React\.(?:FC|FunctionComponent)<\s*(\w+)\s*>")
PROPS_RE = re.compile(r"(?:export\s+)?(?:declare\s+)?(?:type|interface)\s+(\w*Props)\b")


def _members_in_brace(text: str, start: int) -> list[tuple[str, str]]:
    """从 start 起，取该声明下所有顶层 {...} 里的成员。"""
    mem: list[tuple[str, str]] = []
    i, depth, buf = start, 0, ""
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
            buf = ""
            i += 1
            continue
        if ch == "}":
            depth -= 1
            if depth == 0:
                for line in buf.splitlines():
                    line = line.strip()
                    if not line or line.startswith(("/", "*")):
                        continue
                    m = re.match(r"([A-Za-z_$][\w$]*)\??\s*:\s*(.+?);?$", line)
                    if m:
                        mem.append((m.group(1), m.group(2).rstrip(";").strip()[:70]))
                buf = ""
            i += 1
            continue
        if depth == 0 and ch == ";":
            break
        if depth:
            buf += ch
        i += 1
    return mem


def parse_package(pkg_dir: Path) -> tuple[str, str, dict[str, list[tuple[str, str]]]]:
    pj = pkg_dir / "package.json"
    meta = json.loads(pj.read_text(encoding="utf-8"))
    name, ver = meta.get("name", pkg_dir.name), meta.get("version", "?")
    files = [f for f in pkg_dir.rglob("*.d.ts")
             if "node_modules" not in f.relative_to(pkg_dir).parts]

    props: dict[str, list[tuple[str, str]]] = {}
    destructured: dict[str, list[tuple[str, str]]] = {}
    fc_map: dict[str, str] = {}

    for f in files:
        try:
            t = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in PROPS_RE.finditer(t):
            mem = _members_in_brace(t, m.end())
            if mem:
                cur = props.setdefault(m.group(1), [])
                have = {k for k, _ in cur}
                cur += [(k, v) for k, v in mem if k not in have]
        for m in DESTRUCT_RE.finditer(t):
            names = [x.strip().split(":")[0].strip() for x in m.group(2).split(",")]
            names = [n for n in names if re.fullmatch(r"[A-Za-z_$][\w$]*", n or "")]
            if names:
                destructured[m.group(1)] = [(n, "any") for n in names]
        for m in FC_RE.finditer(t):
            fc_map[m.group(1)] = m.group(2)

    # 只认 package 入口（index.d.ts）真正导出的名字 —— 页面里 import 的就是它们；
    # 顺带排除 ATOMIC_DELETE_TAG 这类常量（全大写）与内部实现名。
    exported: set[str] = set()
    for f in files:
        if f.name != "index.d.ts":
            continue
        t = f.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"export\s*(?:type\s*)?\{([^}]+)\}\s*(?:from\s*'[^']*')?", t):
            for raw in m.group(1).split(","):
                n = raw.strip().split(" as ")[-1].strip()
                if re.fullmatch(r"[A-Z]\w*", n) and not n.isupper():
                    exported.add(n)

    comps: dict[str, list[tuple[str, str]]] = {}
    for name_ in sorted(exported or set(destructured)):
        members = (props.get(f"{name_}Props")
                   or props.get(fc_map.get(name_, ""))
                   or destructured.get(name_))
        comps[name_] = members or [("-", "-")]
    return name, ver, comps


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="抽出前端组件清单")
    ap.add_argument("--modules", required=True, help="pc/node_modules 目录")
    ap.add_argument("--scope", default="@seeyon", help="npm scope，默认 @seeyon")
    ap.add_argument("--pkg", action="append", default=[], help="只处理这些包（可重复）")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)

    base = Path(a.modules) / a.scope
    if not base.is_dir():
        print(f"[x] 找不到 {base}")
        return 2

    rows: list[str] = []
    n_comp = n_prop = n_any = 0
    pkgs = a.pkg or sorted(p.name for p in base.iterdir() if (p / "package.json").exists())
    for pname in pkgs:
        d = base / pname
        if not (d / "package.json").exists():
            continue
        name, ver, comps = parse_package(d)
        for comp, members in sorted(comps.items()):
            rows.append(f"{name}\t{ver}\t{comp}\t-\t-")
            n_comp += 1
            for pn, pt in members:
                if pn == "-":
                    continue
                rows.append(f"{name}\t{ver}\t{comp}\t{pn}\t{pt}")
                n_prop += 1
                if pt == "any":
                    n_any += 1

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = "\n".join(rows).encode("utf-8")
    with gzip.open(out, "wb", 6) as f:
        f.write(data)
    print(f"[ok] {out}  {n_comp} 组件 / {n_prop} 属性 / {len(pkgs)} 包 / "
          f"{out.stat().st_size/1024:.0f} KB")
    if n_prop:
        print(f"[!] 其中 {100*n_any/n_prop:.0f}% 属性类型是 any（组件用 any 透传，"
              f"属性名可信、类型不可信）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
