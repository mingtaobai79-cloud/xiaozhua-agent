"""Offline, evidence-preserving Profile Evidence Graph.

The four allowed profile kinds remain independent nodes. Relations are
allow-listed and retain only direct relation evidence. Static input cannot
claim LIVE verification or make unevidenced profiles/relations become FACT.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

ALLOWED_PROFILE_KINDS = frozenset({
    "udc_platform",
    "standard_product_application",
    "customer_udc_application",
    "extension_service",
})
ALLOWED_RELATION_TYPES = frozenset({
    "udc_builds", "standard_supports", "extension_for",
    "config_binds", "pod_runs", "app_depends_on",
})
ALLOWED_STATIC_STATUSES = frozenset({
    "FACT", "OBSERVATION", "HYPOTHESIS", "UNVERIFIED", "DENIED", "UNAVAILABLE",
})
_SCHEMA_VERSION = "profile-evidence-graph.v1"


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _normalize_status(value: Any) -> tuple[str, str | None]:
    raw = str(value or "UNVERIFIED")
    if raw in {"LIVE", "LIVE_PASS"}:
        return "UNVERIFIED", f"static input status {raw} was downgraded to UNVERIFIED"
    if raw not in ALLOWED_STATIC_STATUSES:
        return "UNVERIFIED", f"invalid input status {raw} was downgraded to UNVERIFIED"
    return raw, None


def build_profile_graph(payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build a deterministic graph without fabricating evidence."""
    raw_profiles = payload.get("profiles") if isinstance(payload, Mapping) else None
    raw_profiles = raw_profiles if isinstance(raw_profiles, list) else []

    entries: list[Mapping[str, Any]] = []
    rejected_profiles: list[dict[str, str]] = []
    for raw in raw_profiles:
        if not isinstance(raw, Mapping):
            rejected_profiles.append({"id": "", "kind": "", "reason": "profile must be an object"})
            continue
        profile_id = str(raw.get("id", "") or "").strip()
        kind = str(raw.get("kind", "") or "").strip()
        if not profile_id:
            rejected_profiles.append({"id": "", "kind": kind, "reason": "profile id is required"})
            continue
        if kind not in ALLOWED_PROFILE_KINDS:
            rejected_profiles.append({"id": profile_id, "kind": kind, "reason": "profile kind is not allowed"})
            continue
        entries.append(raw)

    nodes_by_id: dict[str, dict[str, Any]] = {}
    id_kinds: dict[str, list[str]] = {}
    order: list[str] = []
    status_gaps: list[str] = []
    for entry in entries:
        profile_id = str(entry.get("id")).strip()
        kind = str(entry.get("kind")).strip()
        kinds = id_kinds.setdefault(profile_id, [])
        if kind not in kinds:
            kinds.append(kind)
        if profile_id in nodes_by_id:
            node = nodes_by_id[profile_id]
            for ref in _as_list(entry.get("evidence_refs")):
                if str(ref) not in node["evidence_refs"]:
                    node["evidence_refs"].append(str(ref))
            continue
        order.append(profile_id)
        refs = [str(ref) for ref in _as_list(entry.get("evidence_refs"))]
        if "status" not in entry and refs:
            status, status_reason = "FACT", None
        else:
            status, status_reason = _normalize_status(entry.get("status", "UNVERIFIED"))
        node = {"id": profile_id, "kind": kind, "status": status, "evidence_refs": refs}
        if entry.get("application_id") is not None:
            node["application_id"] = entry.get("application_id")
        nodes_by_id[profile_id] = node
        if status_reason:
            status_gaps.append(f"{profile_id}: {status_reason}")
        elif status != "FACT" or not refs:
            status_gaps.append(f"{profile_id}: profile is not backed by FACT evidence")

    conflicts: list[dict[str, Any]] = []
    for profile_id in order:
        kinds = id_kinds.get(profile_id, [])
        if len(kinds) > 1:
            conflicts.append({"type": "same_id_role_conflict", "id": profile_id, "kinds": list(kinds)})
        if "standard_product_application" in kinds and "udc_platform" in kinds:
            conflicts.append({"type": "standard_product_embedded_in_udc", "standard_id": profile_id, "udc_id": None})

    edges: list[dict[str, Any]] = []
    rejected_relations: list[dict[str, Any]] = []
    relation_gaps: list[str] = []
    for entry in entries:
        profile_id = str(entry.get("id")).strip()
        for relation in _as_list(entry.get("relations")):
            if not isinstance(relation, Mapping):
                continue
            relation_type = str(relation.get("type", "") or "")
            target = str(relation.get("target", "") or "").strip()
            if relation_type in ALLOWED_RELATION_TYPES and target:
                refs = [str(ref) for ref in _as_list(relation.get("evidence_refs"))]
                edges.append({"source": profile_id, "type": relation_type, "target": target, "evidence_refs": refs})
            else:
                rejected_relations.append({
                    "source": profile_id, "type": relation_type, "target": target,
                    "reason": "relation type is not allowed" if relation_type not in ALLOWED_RELATION_TYPES else "missing target",
                })

    for edge in edges:
        if (
            edge["type"] == "udc_builds"
            and nodes_by_id.get(edge["source"], {}).get("kind") == "udc_platform"
            and nodes_by_id.get(edge["target"], {}).get("kind") == "standard_product_application"
        ):
            conflicts.append({
                "type": "standard_product_embedded_in_udc",
                "standard_id": edge["target"], "udc_id": edge["source"],
            })

    gaps = list(status_gaps)
    for profile_id in order:
        node = nodes_by_id[profile_id]
        if node["kind"] == "extension_service" and not node["evidence_refs"]:
            specific = f"{profile_id}: pod responsibility inferred without evidence"
            if specific not in gaps:
                gaps.append(specific)


    if conflicts:
        status = "CONFLICT"
    elif not entries:
        status = "UNVERIFIED"
    elif gaps or rejected_profiles:
        status = "PARTIALLY_VERIFIED"
    else:
        status = "FACT"

    return {
        "schema_version": _SCHEMA_VERSION,
        "status": status,
        "network": "disabled",
        "mode": "offline",
        "nodes": [nodes_by_id[profile_id] for profile_id in order],
        "edges": edges,
        "rejected_profiles": rejected_profiles,
        "rejected_relations": rejected_relations,
        "conflicts": conflicts,
        "gaps": gaps,
        "limitations": [
            "Edges require direct relation evidence; node evidence is never inherited by an edge.",
            "Static input cannot claim LIVE verification and is never upgraded beyond its evidence.",
            "A pod responsibility without evidence refs remains an unsupported inference.",
            "Same ID with different profile kinds is a role conflict; the first role wins in the node list.",
        ],
    }


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("profile input root must be an object")
    return value
