# udc-web javap -v method-level contract extraction - one record per REST endpoint instance.
#
# Source: docs/audit/artifacts/udc-web-5.3.517-javap/*.javap.txt (javap -v, GBK CJK).
#
# 2026-10-15 rewrite: fixes three real defects (evidence: COMPONENT-RELOCATION.md section 2)
#   A old version keyed methods by method NAME so same-name overloads overwrote each other,
#     silently dropping endpoints (14 groups / 15 instances). Now one per declaration.
#   B old version took the first quoted string within 400 chars after an annotation name, so
#     for a bare mapping followed by RestApiOperation the CJK description became the path.
#     Now args are read by paren matching inside the annotation section; a bare mapping
#     records an empty method-level value.
#   C old version setdefault-ed non-mapping methods to a method-name path -> 1 phantom.
#     Now no fallback: no mapping means not an endpoint, kept in non_endpoint_methods.
#
# Gate: endpoint = a method declaration instance carrying an HTTP mapping annotation, at ANY
# access level (Spring maps package-private handlers too -- defect D, 3 endpoints:
# DataTransferObjectController.searchSelectableDtoList, EventController.selectWithEventData,
# MicroFlowUpgradeController.upgradeEntityEventFullName). Constructors, ACC_SYNTHETIC
# (lambda-...) and the class-level annotation block are excluded.
# Class-level mapping is concatenated by tools/merge_udc_web_api.py.
#
# Usage: python tools/extract_udc_web_methods.py <javap_dir> [--out <file>]
#
# Evidence level: STATIC_BYTECODE.

from __future__ import annotations

import argparse
import json
from pathlib import Path

_HTTP = (("PostMapping", "POST"), ("GetMapping", "GET"),
         ("PutMapping", "PUT"), ("DeleteMapping", "DELETE"),
         ("PatchMapping", "PATCH"), ("RequestMapping", "ANY"))
_WRITE_HINT = ("create", "update", "delete", "save", "import",
               "copy", "move", "transfer", "publish", "deploy",
               "stop", "restart", "disable", "batch", "clear",
               "handover", "upload", "remove", "add", "modify")
_Q = chr(34)
_ANN_STOP = ("RuntimeVisibleParameterAnnotations:", "RuntimeInvisibleParameterAnnotations:",
             "RuntimeVisibleTypeAnnotations:", "RuntimeInvisibleAnnotations:")


def _ann_args(text, name):
    # Args of annotation name: absent -> None; bare annotation (no parens) -> empty string.
    key = "annotation." + name
    i = text.find(key)
    if i < 0:
        return None
    j = i + len(key)
    if text[j:j + 1] != "(":
        return ""
    depth = 1
    k = j + 1
    while k < len(text) and depth:
        c = text[k]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        k += 1
    return text[j + 1:k - 1]


def _strings(args):
    # The value string list inside annotation args; no value -> empty list.
    if not args:
        return []
    i = args.find("value=")
    if i < 0:
        return []
    k = i + len("value=")
    if args[k:k + 1] == "[":
        e = args.find("]", k)
        return [x for x in args[k + 1:e].split(_Q) if x and x != ","]
    if args[k:k + 1] == _Q:
        e = args.find(_Q, k + 1)
        return [args[k + 1:e]]
    return []


def _decl_starts(lines):
    # Start line index of each method declaration (top-level member, next line is descriptor).
    out = []
    for i in range(len(lines) - 1):
        line = lines[i]
        if not line.startswith("  ") or line.startswith("   "):
            continue
        s = line.strip()
        # Any access level counts: Spring maps package-private handlers too.
        if s.startswith(("class ", "interface ", "enum ", "static ")):
            continue
        if not s.endswith(";") or "(" not in s:
            continue
        if not lines[i + 1].strip().startswith("descriptor:"):
            continue
        out.append(i)
    return out


def _member_end(lines, start, next_start):
    # End of a member region: class-level annotation block / top-level brace / SourceFile.
    end = next_start if next_start is not None else len(lines)
    for j in range(start + 1, end):
        t = lines[j].rstrip()
        if t == "}" or t.startswith("SourceFile"):
            return j
    return end


def _ann_section(block):
    # The member own RuntimeVisibleAnnotations section (excluding parameter annotations).
    a = block.find("RuntimeVisibleAnnotations:")
    if a < 0:
        return ""
    stop = len(block)
    for m in _ANN_STOP:
        k = block.find(m, a + 1)
        if k >= 0:
            stop = min(stop, k)
    return block[a:stop]


def parse_javap(src):
    # Rebuild each method declaration instance -> endpoints / non_endpoint_methods.
    lines = src.replace(chr(13), "").split(chr(10))
    starts = _decl_starts(lines)
    endpoints = []
    non_endpoint = []
    for idx, i in enumerate(starts):
        head = lines[i].strip().split("(")[0]
        name = head.split()[-1]
        if "." in name:
            continue
        nxt = starts[idx + 1] if idx + 1 < len(starts) else None
        end = _member_end(lines, i, nxt)
        block_lines = lines[i:end]
        block = chr(10).join(block_lines)
        flags = [b.strip() for b in block_lines if b.strip().startswith("flags:")]
        if "ACC_SYNTHETIC" in (flags[0] if flags else ""):
            continue
        ann = _ann_section(block)
        http = None
        path_value = None
        for ann_name, verb in _HTTP:
            args = _ann_args(ann, ann_name)
            if args is None:
                continue
            http = verb
            vals = _strings(args)
            path_value = vals[0] if vals else ""
            break
        if http is None:
            non_endpoint.append(name)
            continue
        desc_args = _ann_args(ann, "RestApiOperation")
        desc = (_strings(desc_args) or [""])[0] if desc_args else ""
        role_args = _ann_args(ann, "HasRole")
        endpoints.append({
            "method": name,
            "path_value": path_value,
            "http": http,
            "desc": desc,
            "roles": _strings(role_args) if role_args else [],
            "is_write": any(w in name.lower() for w in _WRITE_HINT),
        })
    return {"endpoints": endpoints, "non_endpoint_methods": non_endpoint}


def main():
    ap = argparse.ArgumentParser(description="udc-web method-level contract extraction (javap -v)")
    ap.add_argument("javap_dir")
    ap.add_argument("--out", default="docs/audit/artifacts/udc-web-5.3.517-methods/_methods.json")
    ns = ap.parse_args()
    d = Path(ns.javap_dir)
    out = {}
    for f in sorted(d.glob("*.javap.txt")):
        raw = f.read_bytes()
        try:
            s = raw.decode("gbk", errors="replace")
        except Exception:
            s = raw.decode("utf-8", errors="replace")
        cls = f.name.replace(".javap.txt", "")
        parsed = parse_javap(s)
        eps = parsed["endpoints"]
        out[cls] = {
            "class": cls,
            "endpoint_count": len(eps),
            "write_count": sum(1 for m in eps if m["is_write"]),
            "methods": eps,
            "non_endpoint_methods": parsed["non_endpoint_methods"],
        }
    outp = Path(ns.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, ensure_ascii=False, indent=1) + chr(10), encoding="utf-8")
    tot = sum(v["endpoint_count"] for v in out.values())
    wc = sum(v["write_count"] for v in out.values())
    wd = sum(1 for v in out.values() for m in v["methods"] if m["desc"])
    ne = sum(len(v["non_endpoint_methods"]) for v in out.values())
    print("controller: " + str(len(out)) + " | endpoints: " + str(tot)
          + " | write: " + str(wc) + " | with-desc: " + str(wd)
          + " | non-endpoint: " + str(ne) + " -> " + str(outp))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
