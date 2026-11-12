# Independent (second-parser) enumerator of HTTP-annotated methods in udc-web javap dumps.
#
# Why this exists: tools/extract_udc_web_methods.py derives endpoints from "annotation.<Name>"
# text search plus descriptor segmentation. This tool parses a DIFFERENT axis -- javap own
# RuntimeVisibleAnnotations blocks by indentation level -- so a defect in either parser shows
# up as a disagreement between the two. Neither is treated as ground truth on its own.
#
# Indentation contract in javap -v output (verified on udc-web-5.3.517):
#   indent 0   -> class / field / method declaration line
#   indent 2   -> member-level sub-record, class-level annotation block entry
#   indent 4   -> member annotation block header, class-level annotation type line
#   indent 6   -> entry line / class-level annotation arg
#   indent 8   -> annotation type line of a member-level entry
# Class-level annotations appear AFTER the closing brace of the class body.
#
# Evidence level: STATIC_BYTECODE. Read-only.
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HTTP_ANNS = {
    "PostMapping": "POST", "GetMapping": "GET", "PutMapping": "PUT",
    "DeleteMapping": "DELETE", "PatchMapping": "PATCH", "RequestMapping": "ANY",
}
ENTRY_RE = re.compile(r"^\s*\d+: #\d+\(.*\)$")
VALUE_LIST_RE = re.compile(r"value=\[(.*)\]")
VALUE_ONE_RE = re.compile(r'value="([^"]*)"')
STR_RE = re.compile(r'"([^"]*)"')
NAME_RE = re.compile(r"^\s*[A-Za-z_][\w.]*$")
METHOD_RE = re.compile(r"^  [^()]*?([\w$<>]+)\(")


def _indent(line):
    return len(line) - len(line.lstrip())


def _block_end(lines, entry_idx):
    d = _indent(lines[entry_idx])
    k = entry_idx + 1
    while k < len(lines):
        if not lines[k].strip() or _indent(lines[k]) <= d:
            break
        k += 1
    return k


def _block(lines, entry_idx):
    return lines[entry_idx:_block_end(lines, entry_idx)]


def _ann_type(block):
    for ln in block[1:]:
        s = ln.strip()
        if not s:
            continue
        s = s.rstrip("(")
        if NAME_RE.match(s):
            return s
    return None


def _path_values(block):
    txt = " ".join(x.strip() for x in block)
    m = VALUE_LIST_RE.search(txt)
    if m:
        return STR_RE.findall(m.group(1))
    m = VALUE_ONE_RE.search(txt)
    if m:
        return [m.group(1)]
    return []


def _http_entries(region):
    out = []
    for i, l in enumerate(region):
        if not ENTRY_RE.match(l):
            continue
        blk = _block(region, i)
        simple = (_ann_type(blk) or "").rsplit(".", 1)[-1]
        if simple in HTTP_ANNS:
            out.append((HTTP_ANNS[simple], _path_values(blk), simple))
    return out


def join_path(base, frag):
    base = (base or "").strip("/")
    frag = (frag or "").lstrip("/")
    if base and frag:
        return "/" + base + "/" + frag
    if base:
        return "/" + base
    return "/" + frag


def parse_class(text):
    lines = text.split("\n")
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "{")
        end = max(i for i, l in enumerate(lines) if l.strip() == "}")
    except StopIteration:
        return {"error": "no-member-region", "class_mapping": None,
                "endpoints": [], "non_endpoint": [], "bare_mapping": []}
    member = lines[start + 1:end]
    tail = lines[end + 1:]

    class_mapping = None
    hits = _http_entries(tail)
    if hits:
        class_mapping = hits[0][1][0] if hits[0][1] else ""

    decl_idxs = [i for i, l in enumerate(member)
                 if _indent(l) == 2 and not l.rstrip().endswith(":")]
    endpoints, non_endpoint, bare = [], [], []
    for n, di in enumerate(decl_idxs):
        stop = decl_idxs[n + 1] if n + 1 < len(decl_idxs) else len(member)
        head = member[di:stop]
        decl = head[0]
        body = "\n".join(head)
        if "descriptor:" not in body:
            continue
        m = METHOD_RE.match(decl)
        method_name = m.group(1) if m else decl.strip()
        if method_name in ("static", "") or "<init>" in decl:
            non_endpoint.append({"method": method_name, "reason": "ctor-or-init"})
            continue
        if method_name.startswith("lambda$") or "ACC_SYNTHETIC" in body:
            non_endpoint.append({"method": method_name, "reason": "synthetic"})
            continue
        entries = _http_entries(head)
        if not entries:
            non_endpoint.append({"method": method_name, "reason": "no-http-annotation"})
            continue
        for verb, vals, simple in entries:
            if not vals:
                bare.append({"method": method_name, "verb": verb, "annotation": simple})
                continue
            for v in vals:
                endpoints.append({"http": verb, "path_value": v, "method": method_name,
                                  "full_path": join_path(class_mapping, v)})
    return {"class_mapping": class_mapping, "endpoints": endpoints,
            "non_endpoint": non_endpoint, "bare_mapping": bare}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("javap_dir")
    ap.add_argument("--out")
    ns = ap.parse_args()
    d = Path(ns.javap_dir)
    out = {}
    for f in sorted(d.glob("*.javap.txt")):
        out[f.name.replace(".javap.txt", "")] = parse_class(
            f.read_text(encoding="utf-8", errors="replace"))
    tot = sum(len(v.get("endpoints", [])) for v in out.values())
    bn = sum(len(v.get("bare_mapping", [])) for v in out.values())
    print("classes=%d endpoints=%d bare_annotation_mappings=%d" % (len(out), tot, bn))
    if ns.out:
        Path(ns.out).write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                encoding="utf-8")
        print("wrote " + ns.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
