# Apply the "document name vs. field name" correction to the frontend op reconciliation.
#
# Defect (found 2026-10-15, sixth round): the frontend op inventory is harvested from bundle
# literals by name, which conflates a GraphQL DOCUMENT/OPERATION name with the FIELD name it
# selects. Two recorded entries are document names only:
#
#   literal "mutation udcMicroflowCopy ($body: udcMicroflowCopyPostInputBody) {
#                udcMicroflowCopyPost(body: $body) {...} }"
#     -> the string "udcMicroflowCopy" is a document name; the op is udcMicroflowCopyPost
#        (which IS a udc-web endpoint: MicroFlowController.copy -> POST /udc/microflow/copy)
#
#   literal "query udcPinyinGet ($query: udcI18nResourceStrToPinyinGetInputQuery) {
#                udcI18nResourceStrToPinyinGet(query: $query) {...} }"
#     -> the string "udcPinyinGet" is a document name; the op is udcI18nResourceStrToPinyinGet
#        (I18nResourceController.toPinYin -> GET /udc/i18n-resource/str-to-pinyin)
#
# Neither name can ever equal an op produced by the path->op rule, because the rule always
# appends the lowercase HTTP method. That is why the exhaustive 437-jar scan found 0 -- the two
# entries are unreachable by construction, not hiding in an unscanned artifact.
#
# Corrections (measured, not assumed):
#   1. drop the 2 document-name-only entries from the inventory;
#   2. add the 2 real field ops;
#   3. udcMicroflowCopyPost is covered by the udc-web contract -> matched 230 -> 231;
#   4. udcI18nResourceStrToPinyinGet is NOT -> a verified relocation, 31 -> 32.
#
# Raw evidence (frontend-extraction.json) is deliberately left untouched; the correction is
# declared in the spec instead, so raw and corrected views stay separable.
#
# Evidence level: STATIC bundle literal + VERIFIED_STATIC_BYTECODE (i18n controller javap).
# Usage: python tools/correct_frontend_op_reference.py [--check]
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEM = ROOT / "docs/audit/udc-semantics"
SPEC = SEM / "frontend-udc-unlocated.json"
EXTRACTION = SEM / "frontend-extraction.json"
LOADER = SEM / "frontend-op-loader-contract.json"
API = ROOT / "docs/audit/artifacts/udc-web-5.3.517-contracts/_api_full.json"

# op string that is really a GraphQL document name -> the real field op inside that document
PHANTOM_TO_OP = {
    "udcMicroflowCopy": ("udcMicroflowCopyPost",
                         "MicroFlowController.copy -> POST /udc/microflow/copy (udc-web)"),
    "udcPinyinGet": ("udcI18nResourceStrToPinyinGet",
                     "I18nResourceController.toPinYin -> GET /udc/i18n-resource/str-to-pinyin "
                     "(boot-starter-i18n-5.3.358, extends BaseComponentController)"),
}

FAMILY_TOKENS = ("FormUpgradeDeploy", "CustomDataType", "PageComponent", "RuntimeUpgrade",
                 "CtpManager", "Message", "Sandbox", "PageInfo", "PageAdmin", "Portal",
                 "MetaData", "Microflow", "Pinyin", "Application", "Affair", "Entity", "Env")


def family(op):
    hits = sorted((t for t in FAMILY_TOKENS if op.startswith("udc" + t)), key=len, reverse=True)
    return hits[0] if hits else "OTHER"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify the committed spec already carries the correction")
    ns = ap.parse_args()

    import sys
    sys.path.insert(0, str(ROOT))
    from components.udc.graphql_op_naming import derive_ops

    spec = json.load(io.open(SPEC, encoding="utf-8-sig"))
    extract = json.load(io.open(EXTRACTION, encoding="utf-8-sig"))
    api = json.load(io.open(API, encoding="utf-8-sig"))
    derived = set(derive_ops(api))

    inventory = set(extract["frontend_ops"]["ops"])
    phantoms = {k: v[0] for k, v in PHANTOM_TO_OP.items()}
    missing = [k for k in phantoms if k not in inventory]
    if missing:
        raise SystemExit("inventory does not contain phantom(s): %s" % missing)

    corrected_inv = (inventory - set(phantoms)) | set(phantoms.values())
    matched = corrected_inv & derived
    unlocated = {o for o in corrected_inv if o.startswith("udc")} - matched
    relocated = (set(spec["relocated_ops"]) | {phantoms["udcPinyinGet"]}) & unlocated
    remaining = unlocated - relocated

    new = dict(spec)
    new["frontend_total"] = len(corrected_inv)
    new["matched_udc_web"] = len(matched)
    new["udc_unlocated"] = len(unlocated)
    new["relocated_cross_artifact"] = len(relocated)
    new["remaining"] = len(remaining)
    new["remaining_ops"] = sorted(remaining)
    new["relocated_ops"] = sorted(relocated)
    new["remaining_registry_ops"] = sorted(
        set(spec["remaining_registry_ops"]) & remaining)
    new["remaining_with_registry_contract"] = len(new["remaining_registry_ops"])
    new["remaining_families"] = {f: sum(1 for o in remaining if family(o) == f)
                                 for f in sorted({family(o) for o in remaining})}
    new["reference_kind_correction"] = {
        "why": "bundle harvest conflated GraphQL document names with field names",
        "phantom_entries": sorted(phantoms),
        "real_ops": {k: v for k, v in sorted(phantoms.items())},
        "evidence": {
            k: {"real_op": v[0], "locus": v[1]} for k, v in sorted(PHANTOM_TO_OP.items())
        },
        "effect": {
            "matched_udc_web": "%d -> %d" % (spec["matched_udc_web"], len(matched)),
            "udc_unlocated": "%d -> %d" % (spec["udc_unlocated"], len(unlocated)),
            "relocated_cross_artifact": "%d -> %d"
            % (spec["relocated_cross_artifact"], len(relocated)),
            "remaining": "%d -> %d" % (spec["remaining"], len(remaining)),
        },
    }

    if ns.check:
        diffs = [k for k in new
                 if k not in ("reference_kind_correction",) and new[k] != spec.get(k)]
        if diffs:
            print("spec is NOT corrected; fields differing: %s" % diffs)
            return 1
        print("spec carries the correction")
        return 0

    SPEC.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % SPEC)
    for k in ("frontend_total", "matched_udc_web", "udc_unlocated",
              "relocated_cross_artifact", "remaining"):
        print("  %-24s %s" % (k, new[k]))

    # loader contract: keep only records for ops still in the remaining list
    lc = json.load(io.open(LOADER, encoding="utf-8-sig"))
    lc["remaining_total"] = len(remaining)
    lc["records"] = [r for r in lc["records"] if r["op"] in remaining]
    lc["records"].sort(key=lambda r: r["op"])
    lc["with_loader_contract"] = sum(1 for r in lc["records"] if r["has_loader_contract"])
    lc["without_loader_contract"] = len(lc["records"]) - lc["with_loader_contract"]
    lc["naming_deviations"] = sum(1 for r in lc["records"]
                                  if r["has_loader_contract"] and not r.get("standard_naming"))
    LOADER.write_text(json.dumps(lc, ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s (records %d, with_loader %d)"
          % (LOADER, len(lc["records"]), lc["with_loader_contract"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
