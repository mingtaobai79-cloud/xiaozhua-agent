"""Offline UDC critical-path matrix and evidence projection."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

PATH_KINDS = [
    "Application", "Entity", "Field", "Page Schema", "MicroFlow", "DataFlow",
    "Generate", "Publish", "Deploy", "Runtime Metadata",
]

@dataclass
class PathEntry:
    kind: str
    application_id: str | None = None
    environment: str | None = None
    artifact_version: str | None = None
    status: str = "UNVERIFIED"
    evidence_refs: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _has(value: Any) -> bool:
    return value not in (None, "", [], {}, "UNVERIFIED")


def _status(*values: Any) -> str:
    return "FACT" if any(_has(v) for v in values) else "UNVERIFIED"


def _refs(*names: str) -> list[str]:
    return [name for name in names if name]


def map_probe_status(classification: Any, *, source: str) -> str:
    value = str(classification or "UNVERIFIED").upper()
    if value in {"BLOCKED", "UNVERIFIED"}:
        return value
    if value in {"PASS", "FACT"}:
        return "LIVE_PASS" if source == "runtime" else "HTTP_PASS"
    return "UNVERIFIED"


def _entry(kind: str, evidence: list[str], dependencies: list[str], gap: str, probe_statuses: list[str] | None = None, *, binding: Mapping[str, Any] | None = None) -> PathEntry:
    gaps = [] if evidence else [gap]
    if probe_statuses and "HTTP_PASS" in probe_statuses:
        gaps.append("HTTP PASS does not imply runtime verification")
    binding = binding or {}
    bound = all(_has(binding.get(key)) for key in ("application_id", "environment", "artifact_version"))
    if not bound:
        gaps.append("application/environment/artifact_version binding identity missing")
    item = PathEntry(
        kind=kind, application_id=binding.get("application_id"),
        environment=binding.get("environment"), artifact_version=binding.get("artifact_version"),
        status="FACT" if evidence and bound else "UNVERIFIED",
        evidence_refs=evidence, gaps=gaps, dependencies=dependencies)
    result = item.to_dict()
    if probe_statuses:
        result["probe_statuses"] = probe_statuses
    return result


def import_evidence(udc: Mapping[str, Any] | None = None,
                    runtime: Mapping[str, Any] | None = None,
                    http: Mapping[str, Any] | None = None,
                    *, scope: Mapping[str, Any] | None = None,
                    context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Project supplied audit/runtime/http JSON into the smallest useful matrix.

    This function is deliberately evidence-first: a plausible domain name is not
    treated as proof. Only non-empty source records create evidence references;
    all other paths remain explicitly ``UNVERIFIED``.
    """
    udc, runtime, http = udc or {}, runtime or {}, http or {}
    scope, context = scope or {}, context or {}
    binding = {
        "application_id": scope.get("application_id") or context.get("application_id"),
        "environment": scope.get("environment") or context.get("environment"),
        "artifact_version": context.get("artifact_version") or scope.get("artifact_version"),
    }
    domains = udc.get("domains", {}) if isinstance(udc.get("domains", {}), Mapping) else {}
    dynamic = udc.get("dto_field_signatures") or udc.get("backend_operations")
    resources = runtime.get("resources", {})
    if not isinstance(resources, Mapping): resources = {}
    probes = http.get("probes", [])
    if not isinstance(probes, list): probes = []
    runtime_probes = runtime.get("probes", [])
    if not isinstance(runtime_probes, list): runtime_probes = []
    probe_statuses = [map_probe_status(p.get("classification"), source="runtime") for p in runtime_probes if isinstance(p, Mapping)]
    probe_statuses += [map_probe_status(p.get("classification"), source="http") for p in probes if isinstance(p, Mapping)]
    deployment = udc.get("deployment") or runtime.get("deployment") or {}
    if not isinstance(deployment, Mapping): deployment = {}

    evidence = {
        "Application": _refs("udc.domains.Application" if _has(domains.get("Application")) else ""),
        "Entity": _refs("udc.domains.Entity" if _has(domains.get("Entity")) else ""),
        "Field": _refs("udc.dto_field_signatures" if _has(dynamic) else ""),
        "Page Schema": _refs("runtime.resources.PageSchema" if any("page" in str(k).lower() for k in resources) else ""),
        "MicroFlow": _refs("udc.domains.MicroFlow" if _has(domains.get("MicroFlow") or domains.get("microflow")) else ""),
        "DataFlow": _refs("udc.persistence" if _has(udc.get("persistence") or udc.get("records")) else ""),
        "Generate": _refs("udc.generate" if _has(udc.get("generate") or udc.get("generated")) else ""),
        "Publish": _refs("udc.publish" if _has(udc.get("publish") or udc.get("published")) else ""),
        "Deploy": _refs("runtime.deployment" if _has(deployment) else ""),
        "Runtime Metadata": _refs("runtime.resources" if _has(resources) else "", "http.probes" if _has(probes) else ""),
    }
    dependencies = {
        "Application": [], "Entity": ["Application"], "Field": ["Entity"],
        "Page Schema": ["Application", "Entity"], "MicroFlow": ["Application", "Entity"],
        "DataFlow": ["Entity", "Field"], "Generate": ["Application", "Entity", "Page Schema"],
        "Publish": ["Generate"], "Deploy": ["Publish"], "Runtime Metadata": ["Deploy"],
    }
    gaps = {
        "Application": "application definition evidence missing", "Entity": "entity definition evidence missing",
        "Field": "field schema evidence missing", "Page Schema": "page schema evidence missing",
        "MicroFlow": "microflow evidence missing", "DataFlow": "dataflow/persistence evidence missing",
        "Generate": "generation evidence missing", "Publish": "publish evidence missing",
        "Deploy": "deployment evidence missing", "Runtime Metadata": "runtime metadata evidence missing",
    }
    entries = [_entry(k, evidence[k], dependencies[k], gaps[k], probe_statuses if k == "Runtime Metadata" else None, binding=binding) for k in PATH_KINDS]
    statuses = {e["status"] for e in entries}
    has_evidence = any(e["evidence_refs"] for e in entries)
    overall = "FACT" if statuses == {"FACT"} else ("PARTIALLY_VERIFIED" if has_evidence else "UNVERIFIED")
    return {"schema_version": "phase-c-path-matrix.v1", "status": overall, "scope": dict(scope), "context": dict(context), "entries": entries}


def build_path_matrix(udc: Mapping[str, Any] | None = None,
                      runtime: Mapping[str, Any] | None = None,
                      http: Mapping[str, Any] | None = None,
                      *, scope: Mapping[str, Any] | None = None,
                      context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return import_evidence(udc, runtime, http, scope=scope, context=context)


def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {"value": value}
