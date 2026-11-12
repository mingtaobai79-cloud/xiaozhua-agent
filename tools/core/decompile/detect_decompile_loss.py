# Detect ops the harvested frontend inventory CLAIMS but the decompiled bundle cannot show.
#
# Why: this repo treats `docs/audit/artifacts/udc-frontend-5.3.496/chunks/` (raw chunk) and the
# wakaru-decompiled bundle as interchangeable evidence sources. They are NOT: a raw chunk that the
# decompiler drops a module from loses string literals that the raw chunk demonstrably contains.
#
# Consequence for method: any *negative* finding of the form "op X has 0 hits in the bundle"
# MUST be re-checked against the raw chunks, or a decompiler loss is silently read as
# "the frontend never references X". Found 2026-10-15 (sixth round): 6 of the 346 harvested ops
# are present in the raw chunks but absent from the decompiled bundle, including 2 udc-* ops that
# the udc-web contract independently derives (`udcDesignMetadataAggEntityExcludeBootGet`,
# `udcPageInfoDeletePost`).
#
# Evidence level: STATIC (raw chunk literal vs decompiled module literal). Read-only, deterministic.
#
# Usage:
#   python tools/detect_decompile_loss.py #       --chunks  <dir of raw *.js chunks> #       --decoded <dir of decompiled *.js modules>
# Defaults point at the scratch locations used when the finding was made; both are volatile.
from __future__ import annotations

import argparse
import io
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXTRACTION = ROOT / "docs/audit/udc-semantics/frontend-extraction.json"
DEFAULT_CHUNKS = Path("<HERMES_HOME>/cache/scratch/udc-frontend/chunks")
DEFAULT_DECODED = Path("<HERMES_HOME>/cache/scratch/udc-frontend/unpacked")

# Pinned finding: harvested ops visible in the raw chunks but lost by the decompile.
# If this changes, the doc statement in COMPONENT-RELOCATION.md section 6.3 must change too.
KNOWN_LOST = (
    "appCommonImageSearch",
    "appCommonImageStoreCategoryGet",
    "cipManagerManageSelectActivexCapabilityEnumGet",
    "organizationOrgMemberAvatarIdsPost",
    "udcDesignMetadataAggEntityExcludeBootGet",
    "udcPageInfoDeletePost",
)


def load(directory: Path):
    files = sorted(directory.rglob("*.js"))
    return {str(f.relative_to(directory)):
            io.open(f, encoding="utf-8", errors="replace").read() for f in files}


def scan(ops, blobs):
    """-> {op: [files that literally contain it]}."""
    out = {}
    for op in ops:
        pat = re.compile(re.escape(op))
        out[op] = sorted(name for name, text in blobs.items() if pat.search(text))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunks", default=str(DEFAULT_CHUNKS))
    ap.add_argument("--decoded", default=str(DEFAULT_DECODED))
    ap.add_argument("--json", action="store_true", help="machine-readable summary")
    ns = ap.parse_args()

    ops = list(json.load(io.open(EXTRACTION, encoding="utf-8"))["frontend_ops"]["ops"])
    chunks_dir, decoded_dir = Path(ns.chunks), Path(ns.decoded)
    for d in (chunks_dir, decoded_dir):
        if not d.is_dir():
            raise SystemExit("missing directory: %s" % d)

    in_raw = scan(ops, load(chunks_dir))
    in_dec = scan(ops, load(decoded_dir))

    lost = [o for o in ops if in_raw[o] and not in_dec[o]]
    absent_both = [o for o in ops if not in_raw[o] and not in_dec[o]]
    only_decoded = [o for o in ops if in_dec[o] and not in_raw[o]]

    summary = {
        "harvested": len(ops),
        "chunks_dir": str(chunks_dir), "chunk_files": len(load(chunks_dir)),
        "decoded_dir": str(decoded_dir), "decoded_files": len(load(decoded_dir)),
        "lost_by_decompile": lost,
        "absent_from_both": absent_both,
        "decoded_only": only_decoded,
        "known_lost_pinned": list(KNOWN_LOST),
        "matches_pinned_finding": sorted(lost) == sorted(KNOWN_LOST),
    }
    if ns.json:
        print(json.dumps(summary, ensure_ascii=False, indent=1))
        return 0 if summary["matches_pinned_finding"] else 1

    print("harvested %d ops; raw chunks=%d files; decompiled=%d files"
          % (len(ops), summary["chunk_files"], summary["decoded_files"]))
    print("LOST by decompile (%d): %s" % (len(lost), lost))
    print("absent from both (%d): %s" % (len(absent_both), absent_both))
    print("decoded-only (%d): %s" % (len(only_decoded), only_decoded))
    print("matches pinned finding: %s" % summary["matches_pinned_finding"])
    if not summary["matches_pinned_finding"]:
        print("!! the pinned list changed -- update COMPONENT-RELOCATION.md section 6.3")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
