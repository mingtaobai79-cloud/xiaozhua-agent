"""Unified offline audit bundle assembler."""
from __future__ import annotations
import json
from pathlib import Path

NAMES=("version_audit","runtime","http","path_matrix","impact_graph","evidence_context")
def _load(path):
    p=Path(path)
    try: return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError,ValueError,TypeError): return None

def build_audit_bundle(paths):
    inputs={}; missing=[]
    for name in NAMES:
        value=_load(paths.get(name))
        if value is None: missing.append(name)
        else: inputs[name]=value
    gaps=[]; statuses=[]
    for value in inputs.values():
        if isinstance(value,dict):
            statuses.append(str(value.get("status","UNVERIFIED")).upper())
            for key in ("gaps","unverified_gaps","context_gaps"):
                if isinstance(value.get(key),list): gaps.extend(str(x) for x in value[key])
    status="UNVERIFIED" if missing or gaps or any(s in {"UNVERIFIED","BLOCKED","CONFLICT","FAIL"} for s in statuses) else "PARTIALLY_VERIFIED"
    return {"schema_version":"audit-bundle.v1","network":"disabled","mode":"offline","status":status,"inputs":{k:paths.get(k) for k in NAMES},"missing_inputs":missing,"gaps":list(dict.fromkeys(gaps)),"status_summary":{"fact_count":sum(s=="FACT" for s in statuses),"live_pass_count":sum(s=="LIVE_PASS" for s in statuses),"unverified_count":sum(s=="UNVERIFIED" for s in statuses),"blocked_count":sum(s=="BLOCKED" for s in statuses)},"reports":inputs,"limitations":["offline inputs only","does not prove live reachability or write success"]}
