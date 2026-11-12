"""Offline planning for potentially mutating operations."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def _items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Iterable):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _evidence(evidence: Any) -> tuple[str, list[str]]:
    if not isinstance(evidence, Mapping):
        return "UNVERIFIED", []
    status = str(evidence.get("status", "UNVERIFIED")).strip().upper() or "UNVERIFIED"
    refs = _items(evidence.get("refs", evidence.get("evidence_refs", [])))
    return status, refs


def _known_environment(environment: Any) -> bool:
    value = str(environment or "").strip().lower()
    return bool(value) and value not in {"unknown", "unspecified", "n/a", "na"}


def build_dry_run(
    target: Any,
    environment: Any,
    evidence: Any = None,
    dependencies: Any = (),
    risks: Any = (),
    action: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic, read-only plan; this function performs no writes."""
    target_text = str(target or "").strip()
    environment_text = str(environment or "").strip() or None
    evidence_status, evidence_refs = _evidence(evidence)
    environment_known = _known_environment(environment)
    evidence_sufficient = evidence_status == "FACT" and bool(evidence_refs)
    confirmable = evidence_sufficient and environment_known
    gaps: list[str] = []
    if not evidence_sufficient:
        gaps.append("confirmed evidence is required before execution")
    if not environment_known:
        gaps.append("known environment is required before execution")
    dependencies_list = _items(dependencies)
    risks_list = _items(risks)
    if not risks_list:
        risks_list = ["operation may change shared application state"]
    operation = action or "plan-change"
    steps = [
        {"id": "validate", "action": "validate", "target": target_text, "executable": False},
        {"id": "prepare", "action": "prepare", "target": target_text, "executable": False},
        {"id": "apply", "action": "proposed_write", "target": target_text, "executable": False},
    ]
    return {
        "mode": "dry-run",
        "action": operation,
        "target": target_text,
        "environment": environment_text,
        "requires_confirmation": confirmable,
        "steps": steps,
        "plan": [f"validate {operation} target", f"prepare {operation} change", "execute only after explicit confirmation"],
        "executed": False,
        "dependencies": dependencies_list,
        "risks": risks_list,
        "rollback": [
            "capture current state before any confirmed change",
            "restore the captured state if verification fails",
        ],
        "verification": {
            "status": "CONFIRMABLE" if confirmable else "UNVERIFIED",
            "evidence_status": evidence_status,
            "environment_status": "FACT" if environment_known else "UNVERIFIED",
            "evidence_refs": evidence_refs,
            "gaps": gaps,
            "checks": ["target identified", "environment identified", "evidence references present"],
        },
        "readback_verification": ["read back changed metadata", "verify target version and health"],
        "network": "disabled",
        "writes_performed": False,
    }
