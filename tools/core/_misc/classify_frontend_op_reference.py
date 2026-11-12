# Classify how each unlocated frontend op is actually REFERENCED inside the design-time bundle.
#
# Why: docs/audit/udc-semantics/frontend-udc-unlocated.json calls its 62 entries "frontend ops",
# but the bundle references them through THREE structurally different channels:
#   1. LOADER      udcMutationLoader|udcQueryLoader.load({fieldType:"<op>", ...})  -> op is a field name
#   2. GQL_FIELD   <op> appears as the selection field of a GraphQL document literal
#   3. DOC_NAME    <op> appears only as the GraphQL document/operation name, while the field
#                  inside that document is a DIFFERENT name  -> the string is not an op at all
# Only 1 and 2 are op references; a DOC_NAME-only string is a phantom entry.
#
# GraphQL document literals are JS string literals beginning with "query " / "mutation "
# (optionally after escaped whitespace). The field is the first selection identifier.
#
# Evidence level: STATIC (bundle literal). Read-only, deterministic.
#
# Usage: python tools/classify_frontend_op_reference.py [--bundle <dir-or-file>] [--out <json>]
from __future__ import annotations

import argparse
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UNLOCATED = ROOT / "docs/audit/udc-semantics/frontend-udc-unlocated.json"
DEFAULT_BUNDLE = ROOT / "docs/audit/artifacts/udc-frontend-5.3.496/chunks"

DOC_LIT = re.compile(r'"((?:\[ntr]|\s)*(?:mutation|query)\s[^"]{0,2500}?)"', re.S)
DOC_HEAD = re.compile(r"\s*(mutation|query)\s+([A-Za-z0-9_]+)")
SEL_FIELD = re.compile(r"\{\s*([A-Za-z0-9_]+)\s*[\({]")


def _unescape(raw):
    try:
        return raw.encode("utf-8").decode("unicode_escape")
    except Exception:
        return raw.replace("\n", " ").replace("\t", " ")


def load_text(target):
    p = Path(target)
    files = sorted(p.rglob("*.js")) if p.is_dir() else [p]
    return {str(f.relative_to(p if p.is_dir() else p.parent)):
            io.open(f, encoding="utf-8", errors="replace").read() for f in files}


def scan(text):
    """-> (doc_name -> set(field), doc_name -> set(kind))."""
    doc_field, doc_kind = {}, {}
    for m in DOC_LIT.finditer(text):
        txt = _unescape(m.group(1))
        head = DOC_HEAD.match(txt)
        if not head:
            continue
        kind, doc = head.group(1), head.group(2)
        doc_kind.setdefault(doc, set()).add(kind)
        fm = SEL_FIELD.search(txt)
        if fm:
            doc_field.setdefault(doc, set()).add(fm.group(1))
    return doc_field, doc_kind


def classify(op, text, doc_field, all_fields):
    loader = len(re.findall(r'fieldType:\s*"' + re.escape(op) + r'"', text))
    loader += len(re.findall(r"fieldType:\s*" + re.escape(op) + r"(?![\w$])", text))
    as_field = op in all_fields
    as_doc = op in doc_field
    if loader:
        kind = "LOADER"
    elif as_field:
        kind = "GQL_FIELD"
    elif as_doc:
        kind = "DOC_NAME_ONLY"
    else:
        kind = "ABSENT"
    return {
        "op": op,
        "kind": kind,
        "loader_sites": loader,
        "referenced_as_graphql_field": as_field,
        "used_as_document_name": as_doc,
        "document_kinds": sorted(doc_kind_of(op, doc_field)) if as_doc else [],
        "alias_field_candidates": sorted(doc_field.get(op, set()) - {op}) if as_doc else [],
    }


def doc_kind_of(op, doc_field):
    return set()


def build(bundle=DEFAULT_BUNDLE):
    unlocated = json.load(io.open(UNLOCATED, encoding="utf-8-sig"))
    ops = unlocated["remaining_ops"]
    blobs = load_text(bundle)
    text = "\n".join(blobs.values())
    doc_field, doc_kind = scan(text)
    all_fields = set()
    for v in doc_field.values():
        all_fields |= v
    records = []
    for op in ops:
        r = classify(op, text, doc_field, all_fields)
        r["document_kinds"] = sorted(doc_kind.get(op, []))
        records.append(r)
    return {
        "schema": "frontend-op-reference-kind.v1",
        "evidence": "STATIC bundle literal (design-time chunk set)",
        "source_bundle": str(bundle),
        "bundle_files": len(blobs),
        "source_unlocated": "docs/audit/udc-semantics/frontend-udc-unlocated.json",
        "remaining_total": len(ops),
        "kinds": {k: sum(1 for r in records if r["kind"] == k)
                  for k in ("LOADER", "GQL_FIELD", "DOC_NAME_ONLY", "ABSENT")},
        "doc_name_only": [r["op"] for r in records if r["kind"] == "DOC_NAME_ONLY"],
        "records": records,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
    ap.add_argument("--out")
    ns = ap.parse_args()
    d = build(ns.bundle)
    print("remaining_total=%d kinds=%s" % (d["remaining_total"], d["kinds"]))
    print("DOC_NAME_ONLY:", d["doc_name_only"])
    for r in d["records"]:
        if r["kind"] == "DOC_NAME_ONLY":
            print("   %s used as %s doc-name; field(s)=%s"
                  % (r["op"], r["document_kinds"], r["alias_field_candidates"]))
    if ns.out:
        Path(ns.out).write_text(json.dumps(d, ensure_ascii=False, indent=1),
                                encoding="utf-8")
        print("wrote " + ns.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
