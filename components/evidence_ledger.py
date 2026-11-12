"""Evidence ledger for offline, read-only audit inputs."""
from __future__ import annotations
from collections import defaultdict
from typing import Any

class EvidenceLedger:
    def __init__(self): self._entries = []
    def add(self, *, source: str, status: str, claim: str, result: Any, **metadata: Any):
        entry = {"source": str(source), "status": str(status).upper(), "claim": str(claim), "result": result}
        entry.update(metadata); self._entries.append(entry); self._mark_conflicts(); return entry
    def _mark_conflicts(self):
        grouped = defaultdict(list)
        for e in self._entries: grouped[e["claim"]].append(e)
        for entries in grouped.values():
            if len({repr(e.get("result")) for e in entries}) > 1:
                for e in entries: e["status"] = "CONFLICT"
    def to_dict(self):
        entries = [dict(e) for e in self._entries]
        return {"schema_version":"1.0", "network":"disabled", "entries":entries, "conflict_count":sum(e["status"]=="CONFLICT" for e in entries)}

def _add(ledger, source, claim, value, status="FACT"):
    ledger.add(source=source, status=status, claim=claim, result=value)

def build_evidence_ledger(*, audit_dir=None, udc_json=None, runtime=None, http=None):
    import json
    from pathlib import Path
    ledger = EvidenceLedger()
    if isinstance(udc_json, (str, Path)):
        try: udc_json = json.loads(Path(udc_json).read_text(encoding="utf-8-sig"))
        except (OSError, ValueError): udc_json = {"status":"UNVERIFIED"}
    if isinstance(udc_json, dict):
        facts = udc_json.get("facts", {})
        if isinstance(facts, dict):
            for claim, value in facts.items(): _add(ledger, "udc-static", claim, value, udc_json.get("status", "FACT"))
    if isinstance(runtime, dict):
        resources = runtime.get("resources", {})
        if isinstance(resources, dict):
            for claim, value in resources.items(): _add(ledger, "runtime-probe", f"runtime.resources.{claim}", value)
    if isinstance(http, dict):
        for i, probe in enumerate(http.get("probes", [])):
            if not isinstance(probe, dict): continue
            classification = str(probe.get("classification", "UNVERIFIED")).upper()
            status = "FACT" if classification in {"PASS", "FACT"} else classification
            _add(ledger, "http-probe", probe.get("label", f"http.probe.{i}"), probe.get("http_status", classification), status)
    result = ledger.to_dict()
    statuses = {entry["status"] for entry in result["entries"]}
    overall = "CONFLICT" if result["conflict_count"] else ("PARTIALLY_VERIFIED" if any(s not in {"FACT", "OBSERVATION"} for s in statuses) else ("FACT" if result["entries"] else "UNVERIFIED"))
    result.update({"scope":{"read_only":True,"network":"disabled","audit_dir":str(audit_dir) if audit_dir else None},"limitations":["offline inputs only","does not prove live reachability or write success"],"status":overall})
    return result
