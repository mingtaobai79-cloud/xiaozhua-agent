"""Offline version evidence audit for UDC artifacts.

A FACT is deliberately narrow: the artifact, version and SHA-256 identify a
real local JAR and the digest is recomputed from that JAR.  Catalog/member
diff metadata alone never upgrades a version to FACT.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

MANIFEST = "udc_version_samples_manifest.json"
CATALOG = "udc_version_compatibility_catalog.json"
DIFF_NAMES = ("udc_member_version_diff.json", "udc_member_version_diff_2.json")


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None

def _path_candidates(root: Path, item: dict[str, Any]) -> Iterable[Path]:
    for key in ("jar", "path", "file", "filename"):
        raw = item.get(key)
        if not raw:
            continue
        path = Path(str(raw))
        yield path
        if not path.is_absolute():
            yield root / path

def _record(item: dict[str, Any], root: Path, source: str) -> dict[str, Any] | None:
    artifact, version, expected = item.get("artifact"), item.get("version"), item.get("sha256")
    if not (artifact and version and isinstance(expected, str) and len(expected) == 64):
        return None
    result = {"artifact": str(artifact), "version": str(version), "sha256": expected.lower()}
    for candidate in _path_candidates(root, item):
        if candidate.is_file():
            actual = _sha256(candidate)
            result["path"] = str(candidate)
            result["sha256_actual"] = actual
            result["source"] = source
            result["status"] = "FACT" if actual == expected.lower() else "UNVERIFIED"
            return result
    result["source"] = source
    result["status"] = "UNVERIFIED"
    result["reason"] = "no local JAR sample"
    return result

def _catalog_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    evidence = data.get("artifact_evidence", {})
    if isinstance(evidence, dict):
        for values in evidence.values():
            if isinstance(values, list): items.extend(x for x in values if isinstance(x, dict))
    return items

def audit_versions(audit_dir: str | Path, versions: Iterable[str] | None = None) -> dict[str, Any]:
    root = Path(audit_dir)
    manifest = _load(root / MANIFEST)
    catalog = _load(root / CATALOG)
    diff = {}
    for name in DIFF_NAMES:
        if (root / name).exists():
            diff = _load(root / name); break
    manifest_items = [x for x in manifest.get("samples", []) if isinstance(x, dict)]
    catalog_items = _catalog_items(catalog)
    declared = {str(v) for v in manifest.get("versions", []) if v is not None}
    declared.update(str(v) for v in catalog.get("source", {}).get("versions", []) if v is not None)
    declared.update(str(v) for v in diff.get("versions", []) if v is not None)
    requested = [str(v) for v in versions] if versions is not None else sorted(declared)
    records: list[dict[str, Any]] = []
    facts: list[dict[str, str]] = []
    for version in requested:
        candidates = [x for x in manifest_items + catalog_items if str(x.get("version")) == version]
        by_key: dict[tuple[str, str], dict[str, Any]] = {}
        for item in candidates:
            rec = _record(item, root, MANIFEST if item in manifest_items else CATALOG)
            if rec is None:
                continue
            key = (rec["artifact"], rec["sha256"])
            previous = by_key.get(key)
            # Prefer a verified local readback when the same evidence unit is
            # described by both manifest and compatibility catalog.
            if previous is None or (rec["status"] == "FACT" and previous["status"] != "FACT"):
                by_key[key] = rec
        version_records = list(by_key.values())
        records.extend(version_records)
        for rec in version_records:
            if rec["status"] == "FACT": facts.append({k: rec[k] for k in ("artifact", "version", "sha256")})
        if not version_records:
            records.append({"version": version, "status": "OBSERVATION" if version in declared else "UNVERIFIED", "reason": "declared version without artifact/version/sha256 evidence"})
    statuses = [r["status"] for r in records]
    status = "FACT" if facts and all(s == "FACT" for s in statuses) else ("PARTIALLY_VERIFIED" if facts else ("OBSERVATION" if any(s == "OBSERVATION" for s in statuses) else "UNVERIFIED"))
    return {"status": status, "versions": requested, "facts": facts, "records": records, "sources": {"manifest": (root / MANIFEST).exists(), "compatibility_catalog": (root / CATALOG).exists(), "member_diff": bool(diff)}}
