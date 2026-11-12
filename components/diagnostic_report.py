"""Cross-component, offline read-only diagnostic conclusion report."""
from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Mapping
from typing import Any

_COMPONENTS = ("evidence_context", "dynamic_evidence", "path_matrix", "impact_graph", "version_audit")
_BAD = {"UNVERIFIED", "BLOCKED", "CONFLICT", "FAIL", "ERROR", "OBSERVATION"}

def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}

def _unique(values: list[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in out:
            out.append(text)
    return out

def _safe_dynamic(report: Mapping[str, Any]) -> dict[str, Any]:
    """Copy dynamic evidence while enforcing the no-live-promotion boundary."""
    result = dict(report)
    statuses = dict(result.get("source_statuses", {})) if isinstance(result.get("source_statuses"), Mapping) else {}
    origin = str(result.get("source", result.get("origin", ""))).lower()
    for source, status in list(statuses.items()):
        value = str(status).upper()
        # HTTP/API/fixture/snapshot/local evidence is never LIVE_PASS.
        if source in {"http", "nacos", "k8s", "mysql", "redis"} or origin in {"http", "api", "fixture", "snapshot", "file", "local"}:
            if value == "LIVE_PASS":
                value = "API_PASS"
        statuses[source] = value
    result["source_statuses"] = statuses
    if str(result.get("status", "")).upper() == "LIVE_PASS" and statuses and all(v != "LIVE_PASS" for v in statuses.values()):
        result["status"] = "API_PASS"
    result.setdefault("network", "disabled")
    result["read_only"] = True
    return result

def _collect_gaps(report: Mapping[str, Any], component: str) -> list[str]:
    gaps: list[Any] = []
    for key in ("gaps", "unverified_gaps", "context_gaps", "missing_inputs"):
        if isinstance(report.get(key), list):
            gaps.extend(report[key])
    if component == "path_matrix":
        entries = report.get("entries", [])
        for entry in entries if isinstance(entries, list) else []:
            if isinstance(entry, Mapping) and isinstance(entry.get("gaps"), list): gaps.extend(entry["gaps"])
    if component == "impact_graph":
        for node in report.get("nodes", []) if isinstance(report.get("nodes"), list) else []:
            if isinstance(node, Mapping) and isinstance(node.get("gaps"), list): gaps.extend(node["gaps"])
    return _unique(gaps)

def build_diagnostic_report(*, evidence_context=None, dynamic_evidence=None, path_matrix=None, impact_graph=None, version_audit=None) -> dict[str, Any]:
    reports = {
        "evidence_context": _as_dict(evidence_context),
        "dynamic_evidence": _safe_dynamic(_as_dict(dynamic_evidence)),
        "path_matrix": _as_dict(path_matrix),
        "impact_graph": _as_dict(impact_graph),
        "version_audit": _as_dict(version_audit),
    }
    gaps: list[str] = []
    blockers: list[str] = []
    for name, report in reports.items():
        gaps.extend(_collect_gaps(report, name))
        status = str(report.get("status", "UNVERIFIED")).upper()
        if status in {"BLOCKED", "CONFLICT", "FAIL", "ERROR"}: blockers.append(f"{name}: {status}")
        elif status == "UNVERIFIED" or (name in {"path_matrix", "impact_graph"} and status != "FACT"):
            blockers.append(f"{name}: evidence is {status}")
    if not reports["evidence_context"].get("scope"): blockers.append("evidence_context: target scope is missing")
    dynamic_statuses = reports["dynamic_evidence"].get("source_statuses", {})
    for source, status in dynamic_statuses.items():
        if str(status).upper() in _BAD: gaps.append(f"dynamic evidence source {source} is {str(status).upper()}")
    facts: list[str] = []
    for fact in reports["version_audit"].get("facts", []) if isinstance(reports["version_audit"].get("facts"), list) else []:
        if isinstance(fact, Mapping) and all(fact.get(k) for k in ("artifact", "version", "sha256")):
            facts.append(f"artifact {fact['artifact']} version {fact['version']} SHA-256 {fact['sha256']}")
    for name in ("evidence_context", "path_matrix", "impact_graph"):
        if str(reports[name].get("status", "")).upper() == "FACT": facts.append(f"{name} report is FACT")
    facts = _unique(facts)
    gaps = _unique(gaps)
    blockers = _unique(blockers)
    if gaps and "behavioral compatibility is not established by static version evidence" not in gaps and reports["version_audit"].get("facts"):
        gaps.append("behavioral compatibility is not established by static version evidence")
    next_steps = []
    if blockers or gaps:
        next_steps.append("provide missing target-bound evidence and rerun this offline report")
    if any("generation" in gap.lower() for gap in gaps): next_steps.append("verify the Generate path with direct artifact evidence")
    if any("runtime" in gap.lower() or "deploy" in gap.lower() for gap in gaps): next_steps.append("verify deployment and runtime metadata separately; do not infer from HTTP/API results")
    if reports["version_audit"].get("facts") and any(b.get("behavior_compatibility") == "UNVERIFIED" for b in reports["version_audit"].get("version_boundaries", []) if isinstance(b, Mapping)):
        next_steps.append("run an explicit behavioral compatibility check for each version boundary")
    if not next_steps: next_steps.append("retain the verified evidence ledger and perform no writes")
    status = "FACT" if facts and not blockers and not gaps else ("BLOCKED" if blockers and not facts else "UNVERIFIED")
    return {"schema_version": "diagnostic-report.v1", "status": status, "network": "disabled", "mode": "offline", "read_only": True, "blockers": blockers, "unverified_gaps": gaps, "verified_facts": facts, "recommended_next_steps": _unique(next_steps), "evidence_context": reports["evidence_context"], "dynamic_evidence": reports["dynamic_evidence"], "path_matrix": reports["path_matrix"], "impact_graph": reports["impact_graph"], "version_audit": reports["version_audit"], "limitations": ["read-only local reports only", "HTTP/API/fixture/snapshot evidence is never LIVE_PASS", "static version evidence does not prove behavior or compatibility"]}

def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}
