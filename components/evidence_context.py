"""Target-bound evidence context for offline audit reports."""
from __future__ import annotations
from collections.abc import Mapping
from typing import Any

def _normalize_evidence(items):
    result=[]
    for item in items or []:
        if not isinstance(item, Mapping): continue
        value=dict(item)
        status=str(value.get("status", "UNVERIFIED")).upper()
        if str(value.get("source", "")).lower() in {"fixture", "snapshot", "file", "local"} and status in {"PASS", "FACT", "LIVE_PASS"}: status="API_PASS"
        value["status"]=status; result.append(value)
    return result

def build_evidence_context(*, environment=None, namespace=None, application_id=None, artifact=None, trace_id=None, time_window=None, evidence=None):
    scope={"environment":environment, "namespace":namespace, "application_id":application_id}
    normalized=_normalize_evidence(evidence)
    gaps=[]
    if not environment: gaps.append("environment is required")
    if not namespace: gaps.append("namespace is required")
    if not application_id: gaps.append("application_id is required")
    if not normalized: gaps.append("at least one evidence item is required")
    if artifact is not None:
        if not all(artifact.get(k) for k in ("artifact","version","sha256")): gaps.append("artifact requires artifact/version/sha256")
    if trace_id is None: gaps.append("trace_id is unavailable")
    status="FACT" if not gaps and all(x.get("status") in {"FACT","API_PASS","LIVE_PASS"} for x in normalized) else "UNVERIFIED"
    return {"schema_version":"evidence-context.v1","status":status,"network":"disabled","scope":scope,"artifact":artifact,"trace_id":trace_id,"time_window":time_window,"evidence":normalized,"evidence_count":len(normalized),"gaps":gaps,"limitations":["offline evidence context","fixture/snapshot evidence cannot establish LIVE_PASS"]}
