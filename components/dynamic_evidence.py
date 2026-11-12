from __future__ import annotations
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SOURCES = ("http", "k8s", "nacos", "mysql", "redis")

def classify_dynamic_result(result: Mapping[str, Any] | None, *, source: str) -> str:
    value = result or {}
    classification = str(value.get("classification", "UNVERIFIED")).upper()
    origin = str(value.get("source", value.get("origin", "fixture"))).lower()
    if origin in {"fixture", "file", "snapshot", "mapping", "local"}:
        return "API_PASS" if classification in {"PASS", "FACT", "LIVE_PASS", "API_PASS"} else (classification if classification in {"BLOCKED", "UNVERIFIED"} else "UNVERIFIED")
    if source in {"http", "nacos"} and classification in {"PASS", "FACT", "LIVE_PASS"}:
        return "API_PASS"
    if classification in {"PASS", "FACT", "LIVE_PASS"}:
        return "LIVE_PASS"
    return classification if classification in {"API_PASS", "BLOCKED", "UNVERIFIED"} else "UNVERIFIED"

def _load(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping): return dict(value)
    if value is None: return {}
    try: loaded = json.loads(Path(value).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, TypeError): return {"classification": "UNVERIFIED", "source": "fixture"}
    return dict(loaded) if isinstance(loaded, Mapping) else {"classification": "UNVERIFIED", "source": "fixture"}

def _overall(statuses: list[str]) -> str:
    if not statuses or all(s == "UNVERIFIED" for s in statuses): return "UNVERIFIED"
    if any(s == "BLOCKED" for s in statuses): return "BLOCKED" if any(s in {"API_PASS", "LIVE_PASS"} for s in statuses) else "UNVERIFIED"
    return "LIVE_PASS" if all(s == "LIVE_PASS" for s in statuses) else ("API_PASS" if all(s in {"API_PASS", "LIVE_PASS"} for s in statuses) else "UNVERIFIED")

def build_dynamic_evidence_report(results=None, **kwargs):
    results = dict(results or {})
    context = kwargs.pop("evidence_context", None) or {}
    results.update(kwargs)
    values = {name: _load(results.get(name)) for name in SOURCES}
    statuses = {name: classify_dynamic_result(value, source=name) for name, value in values.items()}
    context_output = {key: context.get(key) for key in ("environment", "namespace", "application_id")}
    context_gaps = [f"{key} is required" for key, value in context_output.items() if not value] if context else []
    if context_gaps: statuses = {name: ("UNVERIFIED" if status in {"API_PASS", "LIVE_PASS"} else status) for name, status in statuses.items()}
    bound = not context_gaps
    from components.evidence_ledger import EvidenceLedger
    ledger = EvidenceLedger()
    for name in SOURCES: ledger.add(source=name, status=statuses[name], claim=f"dynamic.{name}", result=values[name])
    from components.udc.path_matrix import PATH_KINDS
    refs = [f"dynamic.{name}" for name, status in statuses.items() if status in {"API_PASS", "LIVE_PASS"}]
    matrix_status = "FACT" if bound and len(refs) == len(SOURCES) and any(s == "LIVE_PASS" for s in statuses.values()) else "UNVERIFIED"
    entries = [{"kind": kind, "status": matrix_status, "evidence_refs": refs, "gaps": [] if matrix_status == "FACT" else ["dynamic evidence closure incomplete"], "dependencies": []} for kind in PATH_KINDS]
    return {"schema_version": "dynamic-evidence.v1", "network": "disabled", "read_only": True, "status": _overall(list(statuses.values())) if bound else "UNVERIFIED", "context": context_output, "context_gaps": context_gaps, "trace_id": context.get("trace_id"), "time_window": context.get("time_window"), "sources": list(SOURCES), "source_statuses": statuses, "evidence_ledger": ledger.to_dict(), "path_matrix": {"schema_version": "dynamic-evidence-path-matrix.v1", "status": matrix_status, "entries": entries}, "limitations": ["read-only inputs", "fixture and snapshot reads are API_PASS, never LIVE_PASS"]}
