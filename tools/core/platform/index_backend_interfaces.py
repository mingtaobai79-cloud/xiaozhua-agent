# -*- coding: utf-8 -*-
"""从 batch2 的 javap 文本归纳「后端接口面」：类 → 方法签名（参数 / 返回 / 修饰符）。

回答的问题：写 UDC 自定义微流程（后端 extend 工程）时，
  我该继承哪个类？方法叫什么？参数是什么类型？返回什么？
数据源：docs/audit/artifacts/extension-surface-*/{batch2/*.json, symbols-*.json}
        （每件含 classes[].javap 原文，本脚本只做结构化，不重新反编译）

用法：
    python tools/core/platform/index_backend_interfaces.py \
        --artifacts docs/audit/artifacts/extension-surface-20261029 \
        --packages udc-extend udc-facade udc-starter-runtime udc-starter-lowcode udc-common \
        --emit docs/audit/artifacts/extension-surface-20261029/interfaces.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

RE_TYPE_DECL = re.compile(
    r"^\s*(?:public\s+|final\s+|abstract\s+|static\s+)*(class|interface|enum|@interface)\s+([\w.$]+)")
# javap 成员行：修饰符… 返回类型 名字(参数);
RE_METHOD = re.compile(
    r"^\s+(?P<mods>(?:(?:public|protected|private|static|final|abstract|default|native|synchronized)\s+)*)"
    r"(?P<ret>[\w.$<>\[\], ?]+?)\s+(?P<name>[\w$]+)\((?P<args>[^)]*)\)"
    r"(?:\s+throws\s+[\w., ]+)?;")
RE_FIELD = re.compile(
    r"^\s+(?P<mods>(?:(?:public|protected|private|static|final|volatile|transient)\s+)*)"
    r"(?P<type>[\w.$<>\[\], ?]+?)\s+(?P<name>[\w$]+)"
    r"(?:\s*=\s*(?P<value>.+?))?;")
RE_EXTENDS = re.compile(r"\bextends\s+([\w.$<>,\[\]]+?)(?=\s+implements\s+|\s*\{?\s*$)", re.M)
RE_IMPLEMENTS = re.compile(r"\bimplements\s+([\w.$<>,\[\]\s]+?)\s*\{?\s*$", re.M)


def split_args(s: str) -> list[dict]:
    """按顶层逗号切参数；javap 无 -l 时参数名是 argN，类型才是重点。"""
    if not s.strip():
        return []
    out, buf, depth = [], [], 0
    for ch in s:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        out.append("".join(buf).strip())
    args = []
    for i, a in enumerate(out):
        parts = a.rsplit(" ", 1)
        if len(parts) == 2 and re.fullmatch(r"arg\d+|\w+", parts[1]):
            args.append({"type": parts[0].strip(), "name": parts[1]})
        else:
            args.append({"type": a, "name": f"arg{i}"})
    return args


def parse_javap(text: str) -> dict | None:
    head = None
    for line in text.splitlines():
        m = RE_TYPE_DECL.match(line)
        if m:
            head = {"kind": m.group(1), "fqcn": m.group(2), "decl": line.strip()}
            break
    if not head:
        return None
    ext = RE_EXTENDS.search(text)
    imp = RE_IMPLEMENTS.search(text)
    head["extends"] = [x.strip() for x in (ext.group(1).split(",") if ext else []) if x.strip()]
    head["implements"] = [x.strip() for x in (imp.group(1).split(",") if imp else []) if x.strip()]
    head["methods"], head["fields"] = [], []
    for line in text.splitlines():
        m = RE_METHOD.match(line)
        if m:
            mods = m.group("mods").split()
            head["methods"].append({
                "name": m.group("name"),
                "returns": " ".join(m.group("ret").split()),
                "args": split_args(m.group("args")),
                "modifiers": mods,
                "signature": " ".join(line.split()),
            })
            continue
        f = RE_FIELD.match(line)
        if f and "(" not in line:
            rec = {"name": f.group("name"),
                   "type": " ".join(f.group("type").split()),
                   "modifiers": f.group("mods").split()}
            val = (f.groupdict().get("value") or "").strip()
            if val:
                rec["value"] = val[:120]
            head["fields"].append(rec)

    # javap 把 enum 输出成 `final class X extends java.lang.Enum<X>`，
    # 不还原就会被当成普通 class（实测 758 个枚举全混在 class 里）。
    if head["kind"] == "class" and any("java.lang.Enum" in x for x in head["extends"]):
        head["kind"] = "enum"
        # 枚举常量 = 类型等于自身的 static final 字段，声明顺序即 ordinal
        head["constants"] = [f["name"] for f in head["fields"]
                             if f["name"] != "$VALUES" and f["type"].endswith(head["fqcn"].split(".")[-1])
                             and "static" in f["modifiers"]]
    return head


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="从 batch2 javap 归约后端接口面（只读）")
    ap.add_argument("--artifacts", required=True, help="extension-surface-<日期> 目录")
    ap.add_argument("--packages", required=True, nargs="+",
                    help="构件名（不含版本），如 udc-extend udc-facade")
    ap.add_argument("--emit", required=True)
    ap.add_argument("--require-methods", action="store_true", default=True,
                    help="类必须解析出方法，否则计入 empty 并 exit 6")
    a = ap.parse_args(argv)

    root = Path(a.artifacts)
    out: dict = {"sources": {}, "classes": {}, "method_index": {}}
    empty = []
    for pkg in a.packages:
        cands = list((root / "batch2").glob(f"{pkg}.json")) + list(root.glob(f"symbols-{pkg}.json"))
        if not cands:
            print(f"WARN: 找不到 {pkg} 的签名件", flush=True)
            continue
        src = cands[0]
        d = json.loads(src.read_text(encoding="utf-8"))
        out["sources"][pkg] = {"jar": d.get("jar"), "file": str(src.relative_to(root)),
                               "classes": len(d.get("classes") or []),
                               "total_methods": d.get("total_methods")}
        for c in d.get("classes") or []:
            info = parse_javap(c.get("javap") or "")
            if not info:
                empty.append(f"{pkg}:{c.get('entry')}")
                continue
            out["classes"][info["fqcn"]] = info
            info["pkg"] = pkg
            for m in info["methods"]:
                out["method_index"].setdefault(m["name"], []).append(f"{info['fqcn']}#{m['name']}")

    p = Path(a.emit)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    n_cls = len(out["classes"])
    n_m = sum(len(c["methods"]) for c in out["classes"].values())
    print(f"classes {n_cls} / methods {n_m} / method_index {len(out['method_index'])} → {p}"
          f"（{p.stat().st_size} B）")
    if empty:
        print(f"ERR: {len(empty)} 个类未解析出类型声明：{empty[:5]}", flush=True)
        return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
