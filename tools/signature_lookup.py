#!/usr/bin/env python3
"""按类名/方法名查平台接口签名（离线，不连平台、不需要 jar）。

数据源：docs/audit/signatures.txt.gz（21389 个类 / 245709 行签名，2.3 MB）。
一行一个成员，制表符分两类：

    com.seeyon.x.YService<TAB>interface
    com.seeyon.x.YService#doIt(com.seeyon.x.Req):com.seeyon.x.Resp

用法：

    python tools/signature_lookup.py YService              # 类名含 YService
    python tools/signature_lookup.py --method saveAs       # 方法名含 saveAs
    python tools/signature_lookup.py --pkg com.seeyon.udc.api --method create
    python tools/signature_lookup.py XxxService --exact     # 全限定名精确
    python tools/signature_lookup.py XxxService --json      # 机器可读

写自定义微流程扩展时用它查「这个 Service 有哪些方法、参数和返回是什么类型」，
比翻 docs/audit/udc-semantics 下上百份 md 快得多，且覆盖全部 91+ 个构件。
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX = ROOT / "docs" / "audit" / "signatures.txt.gz"

_cache: list[str] | None = None
_kind_of: dict[str, str] = {}


def load_index(path: Path) -> list[str]:
    global _cache
    if _cache is not None:
        return _cache
    if not path.exists():
        print(f"[x] 缺签名索引: {path}\n    先跑 python tools/regen_evidence.py，或见 REGENERATE-EVIDENCE.md",
              file=sys.stderr)
        raise SystemExit(2)
    with gzip.open(path, "rt", encoding="utf-8") as f:
        _cache = f.read().splitlines()
    for line in _cache:
        if "\t" in line:
            fq, kind = line.split("\t", 1)
            _kind_of[fq] = kind
    return _cache


def _parse(line: str) -> dict:
    if "\t" in line:
        fq, kind = line.split("\t", 1)
        return {"class": fq, "kind": kind, "member": None}
    # FQCN#method(args):returns
    head, _, ret = line.partition("):")
    fq, _, sig = head.partition("#")
    name, _, args = sig.partition("(")
    return {"class": fq, "kind": "method", "member": name,
            "args": args, "returns": ret, "signature": line}


def search(lines: list[str], pattern: str, exact: bool, method: str,
           pkg: str, kind: str | None, limit: int) -> list[dict]:
    out: list[dict] = []
    pat = pattern.lower()
    meth = method.lower()
    for line in lines:
        low = line.lower()
        if exact:
            cls = line.split("\t")[0] if "\t" in line else line.split("#")[0]
            if cls.lower() != pat:
                continue
        elif pat and pat not in low:
            continue
        if meth and meth not in low:
            continue
        if pkg and not low.startswith(pkg.lower()):
            continue
        rec = _parse(line)
        if kind and rec["kind"] != kind:
            continue
        out.append(rec)
        if len(out) >= limit:
            break
    return out


def _group(recs: list[dict]) -> dict[str, dict]:
    classes: dict[str, dict] = {}
    for r in recs:
        c = classes.setdefault(r["class"], {"class": r["class"],
                                            "kind": _kind_of.get(r["class"]), "methods": []})
        if r["kind"] != "method":
            c["kind"] = r["kind"]
        elif r["kind"] == "method":
            c["methods"].append({k: r[k] for k in ("member", "args", "returns") if k in r})
    return classes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="离线查平台接口签名")
    ap.add_argument("pattern", nargs="?", default="", help="类名或任意片段（大小写不敏感）")
    ap.add_argument("--method", default="", help="方法名片段")
    ap.add_argument("--pkg", default="", help="限定包前缀")
    ap.add_argument("--kind", default=None, choices=["class", "interface", "enum"])
    ap.add_argument("--exact", action="store_true", help="全限定类名精确匹配")
    ap.add_argument("--limit", type=int, default=40, help="最多返回多少个类（默认 40）")
    ap.add_argument("--raw", action="store_true", help="直接打印命中的行")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--index", default=str(DEFAULT_INDEX))
    a = ap.parse_args(argv)

    if not (a.pattern or a.method or a.pkg):
        ap.print_help()
        return 2

    lines = load_index(Path(a.index))
    # 先按类聚合，再按 limit 截断类数
    hits = search(lines, a.pattern, a.exact, a.method, a.pkg, a.kind, 100_000)
    classes = _group(hits)
    picked = list(classes.values())[: a.limit]

    if a.raw:
        for r in hits:
            if r["kind"] == "method":
                print(r["signature"])
        return 0
    if a.json:
        print(json.dumps(picked, ensure_ascii=False, indent=1))
        return 0

    if not picked:
        print("无命中。换个片段试试，或用 --pkg 收窄。")
        return 1
    for c in picked:
        print(f"{c['class']}  [{c['kind'] or '?'}]")
        for m in c["methods"]:
            print(f"    {m['member']}({m.get('args','')}) : {m.get('returns','')}")
    if len(classes) > len(picked):
        print(f"\n…共 {len(classes)} 个类命中，只显示前 {len(picked)} 个（--limit 调整）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
