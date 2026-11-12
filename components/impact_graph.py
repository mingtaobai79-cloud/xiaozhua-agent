"""Offline, evidence-preserving Phase E impact graph."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

NODE_TYPES = (
    "metadata", "version", "generated_artifact", "runtime_metadata",
    "physical_table", "redis", "events", "routes_assets",
)

# These are explicit projections, not guesses about an absent relationship.
_KIND_ALIASES = {
    "metadata": {"metadata", "application", "page schema", "pageschema"},
    "version": {"version"},
    "generated_artifact": {"generate", "generated artifact", "generated_artifacts", "artifact"},
    "runtime_metadata": {"runtime metadata", "runtimemetadata"},
    "physical_table": {"physical table", "physical_table", "table", "dataflow", "data flow"},
    "redis": {"redis", "redis key", "cache"},
    "events": {"events", "event", "message", "消息"},
    "routes_assets": {"routes/assets", "routes assets", "route", "routes", "asset", "assets", "frontend asset"},
}

# The default graph is deliberately a possible propagation order only.  Its
# edges do not assert that any node exists or that the dependency was verified.
_DEPENDENCIES = (
    ("metadata", "version"),
    ("version", "generated_artifact"),
    ("generated_artifact", "runtime_metadata"),
    ("runtime_metadata", "physical_table"),
    ("physical_table", "redis"),
    ("redis", "events"),
    ("events", "routes_assets"),
)


def _norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def _node_type(kind: Any) -> str | None:
    value = _norm(kind)
    for node_type, aliases in _KIND_ALIASES.items():
        if value in {_norm(alias) for alias in aliases}:
            return node_type
    return None


def _source_entries(matrix: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    entries = matrix.get("entries", [])
    return [entry for entry in entries if isinstance(entry, Mapping)] if isinstance(entries, list) else []


def _project_node(node_type: str, entries: list[Mapping[str, Any]]) -> dict[str, Any]:
    matched = [entry for entry in entries if _node_type(entry.get("kind")) == node_type]
    refs: list[str] = []
    gaps: list[str] = []
    source_kinds: list[str] = []
    probe_statuses: list[str] = []
    for entry in matched:
        kind = str(entry.get("kind", ""))
        if kind and kind not in source_kinds:
            source_kinds.append(kind)
        for ref in entry.get("evidence_refs", []) if isinstance(entry.get("evidence_refs", []), list) else []:
            if ref not in refs:
                refs.append(str(ref))
        for probe_status in entry.get("probe_statuses", []) if isinstance(entry.get("probe_statuses", []), list) else []:
            if probe_status not in probe_statuses:
                probe_statuses.append(str(probe_status))
        for gap in entry.get("gaps", []) if isinstance(entry.get("gaps", []), list) else []:
            if gap not in gaps:
                gaps.append(str(gap))
    # Only an explicit FACT entry can produce FACT.  An inferred/default node
    # is never upgraded from a neighboring node or a dependency edge.
    is_fact = any(str(entry.get("status", "")) == "FACT" for entry in matched)
    return {
        "id": node_type, "type": node_type,
        "status": (probe_statuses[0] if probe_statuses and probe_statuses == ["HTTP_PASS"] else ("FACT" if is_fact else "UNVERIFIED")),
        "evidence_refs": refs if is_fact else (refs if matched and any(str(e.get("status", "")) != "UNVERIFIED" for e in matched) else []),
        "gaps": gaps if gaps else ([] if is_fact else [f"{node_type} evidence missing"]),
        "source_kinds": source_kinds,
        "probe_statuses": probe_statuses,
    }


def build_impact_graph(path_matrix: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build a deterministic graph from a path matrix without fabricating facts."""
    matrix = path_matrix if isinstance(path_matrix, Mapping) else {}
    entries = _source_entries(matrix)
    nodes = [_project_node(node_type, entries) for node_type in NODE_TYPES]
    edges = [{"source": source, "target": target, "type": "depends_on", "status": "UNVERIFIED"} for source, target in _DEPENDENCIES]
    status = "FACT" if all(node["status"] == "FACT" for node in nodes) else ("PARTIALLY_VERIFIED" if any(node["status"] == "FACT" for node in nodes) else "UNVERIFIED")
    return {
        "schema_version": "phase-e-impact-graph.v1", "status": status,
        "network": "disabled", "mode": "offline",
        "nodes": nodes, "edges": edges,
        "limitations": ["Dependency edges describe the model order; they are not proof of runtime coupling.", "Missing evidence remains UNVERIFIED; inference is never FACT.", "HTTP PASS does not imply runtime verification"],
    }


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {}
