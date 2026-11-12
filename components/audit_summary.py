"""Offline audit report aggregation."""

import json
import re
from pathlib import Path

from .report_schema import enforce_report_schema, report_metadata

REPORTS = {
    "code_reality": "code-reality-audit.md",
    "evidence_consistency": "udc-evidence-consistency-audit.md",
    "next_direction": "next-direction-input.md",
}

def _status(text, default="UNVERIFIED"):
    for candidate in ("PARTIALLY VERIFIED", "FOCUSED VERIFIED", "REAL LOCAL SMOKE VERIFIED", "UNVERIFIED", "BLOCKED", "FACT"):
        if candidate in text:
            return candidate
    return default

def _summarize_udc(payload):
    """Keep the machine report bounded while preserving audit evidence."""
    keys = ("status", "artifact_version", "artifact", "counts", "facts", "unverified", "summary", "evidence_limits", "limitations")
    return {key: payload[key] for key in keys if key in payload}


def build_summary(audit_dir, udc_json):
    audit_dir, udc_json = Path(audit_dir), Path(udc_json)
    missing = []
    texts = {}
    for key, filename in REPORTS.items():
        path = audit_dir / filename
        if not path.is_file():
            missing.append(str(path))
        else:
            texts[key] = path.read_text(encoding="utf-8-sig")
    if not udc_json.is_file():
        missing.append(str(udc_json))
        udc = {"status": "UNVERIFIED"}
    else:
        try:
            udc = _summarize_udc(json.loads(udc_json.read_text(encoding="utf-8-sig")))
        except (OSError, json.JSONDecodeError):
            missing.append(str(udc_json))
            udc = {"status": "UNVERIFIED"}
    if missing:
        return enforce_report_schema({"status": "UNVERIFIED", "missing": missing, "code_reality": {}, "evidence_consistency": {}, "next_direction": {}, "udc": udc, **report_metadata(scope={"mode": "offline", "read_only": True, "inputs": "local audit files"}, limitations=["Missing or invalid inputs prevent fact verification."])})
    steps = re.findall(r"^\s*\d+\.\s*\*\*([^*]+)\*\*", texts["next_direction"], re.MULTILINE)
    return enforce_report_schema({
        **report_metadata(scope={"mode": "offline", "read_only": True, "inputs": "local audit files"}, limitations=["Static/local evidence does not prove live environment behavior.", "No test2 connection or external write is performed."]),
        "status": "PARTIALLY VERIFIED" if _status(texts["evidence_consistency"]) == "PARTIALLY VERIFIED" else _status(texts["code_reality"]),
        "code_reality": {"status": _status(texts["code_reality"]), "source": REPORTS["code_reality"]},
        "evidence_consistency": {"status": _status(texts["evidence_consistency"]), "source": REPORTS["evidence_consistency"]},
        "next_direction": {"status": "UNVERIFIED", "items": steps, "source": REPORTS["next_direction"]},
        "udc": udc,
    })
