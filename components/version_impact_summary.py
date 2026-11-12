"""Evidence-preserving association of UDC version audit and impact artifacts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def _load(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _unique(values: list[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = str(value)
        if text and text not in result:
            result.append(text)
    return result


def build_version_impact_summary(version_audit: Mapping[str, Any] | None,
                                  path_matrix: Mapping[str, Any] | None,
                                  impact_graph: Mapping[str, Any] | None) -> dict[str, Any]:
    """Join supplied reports without upgrading static version evidence.

    Artifact/version/SHA facts establish an evidence boundary only. They never
    establish behavioral compatibility; that field remains UNVERIFIED unless a
    separate behavioral test record is explicitly supplied (which this report
    does not infer from matrix or graph data).
    """
    audit, matrix, graph = _load(version_audit), _load(path_matrix), _load(impact_graph)
    facts = audit.get("facts", []) if isinstance(audit.get("facts"), list) else []
    records = audit.get("records", []) if isinstance(audit.get("records"), list) else []
    versions = audit.get("versions", []) if isinstance(audit.get("versions"), list) else []
    if not versions:
        versions = [r.get("version") for r in records if isinstance(r, Mapping) and r.get("version")]
    boundaries = []
    for version in _unique(versions):
        version_facts = [f for f in facts if isinstance(f, Mapping) and str(f.get("version")) == version]
        record_statuses = [str(r.get("status")) for r in records if isinstance(r, Mapping) and str(r.get("version")) == version]
        evidence_status = "FACT" if version_facts else (record_statuses[0] if record_statuses else str(audit.get("status", "UNVERIFIED")))
        boundaries.append({"version": version, "evidence_status": evidence_status, "artifacts": [dict(f) for f in version_facts], "behavior_compatibility": "UNVERIFIED"})

    nodes = graph.get("nodes", []) if isinstance(graph.get("nodes"), list) else []
    affected = []
    gaps: list[Any] = []
    for node in nodes:
        if not isinstance(node, Mapping):
            continue
        status = str(node.get("status", "UNVERIFIED"))
        node_id = node.get("id") or node.get("type")
        if node_id and status not in {"FACT", "HTTP_PASS", "LIVE_PASS"}:
            affected.append(str(node_id))
        if isinstance(node.get("gaps"), list):
            gaps.extend(node["gaps"])
    entries = matrix.get("entries", []) if isinstance(matrix.get("entries"), list) else []
    for entry in entries:
        if isinstance(entry, Mapping) and isinstance(entry.get("gaps"), list):
            gaps.extend(entry["gaps"])
    affected = _unique(affected)
    unverified_gaps = _unique(gaps)
    if not boundaries:
        unverified_gaps.append("version audit contains no declared version boundary")
    if any(b["behavior_compatibility"] == "UNVERIFIED" for b in boundaries):
        unverified_gaps.append("behavioral compatibility is not established by static version evidence")
    status = "FACT" if boundaries and all(b["evidence_status"] == "FACT" for b in boundaries) and not affected and not unverified_gaps else "UNVERIFIED"
    return {"schema_version": "version-impact-summary.v1", "status": status, "network": "disabled", "mode": "offline", "version_boundaries": boundaries, "affected_nodes": affected, "unverified_gaps": _unique(unverified_gaps), "sources": {"version_audit": True, "path_matrix": bool(matrix), "impact_graph": bool(graph)}, "limitations": ["Static artifact/version/SHA evidence does not prove behavioral compatibility.", "Affected nodes and gaps reflect supplied graph/matrix evidence only; dependency edges are not runtime proof."]}


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}
