"""Build a secret-safe evidence manifest from a local Nacos snapshot."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from typing import Any

_SENSITIVE_KEY = re.compile(r"(?:secret|password|passwd|token|api[_-]?key|access[_-]?key|private[_-]?key|credential)", re.I)
_URL = re.compile(r"https?://[^\s\"\'<>]+", re.I)
_MAVEN = re.compile(r"(?:maven:|(?:^|\s))([A-Za-z][A-Za-z0-9_.-]*\.[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+(?:[:@][A-Za-z0-9_.-]+)?)", re.I)
_JDBC = re.compile(r"jdbc:([A-Za-z0-9]+):[^\s\"\']+", re.I)
_EXTS = {".yml", ".yaml", ".properties", ".json", ".conf", ".txt"}

def _safe_text(value: Any) -> str:
    text = str(value)
    text = re.sub(r"(?i)(secret|password|passwd|token|api[_-]?key|access[_-]?key|private[_-]?key|credential)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", text)
    return text

def _walk(value: Any, key: str = ""):
    if isinstance(value, dict):
        for k, v in value.items():
            if _SENSITIVE_KEY.search(str(k)): continue
            yield from _walk(v, str(k))
    elif isinstance(value, list):
        for v in value: yield from _walk(v, key)
    else: yield key, value

def _read_content(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")

def _json_or_lines(text: str):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None

def build_manifest(snapshot_dir: str | Path, *, application_id: str, tenant: str, group: str) -> dict[str, Any]:
    root = Path(snapshot_dir)
    records = []
    urls, datasources, storages, artifacts = set(), set(), set(), set()
    gaps = []
    if not root.exists() or not root.is_dir():
        return {"schema_version":"nacos-evidence-manifest.v1", "network":"disabled", "application_id":application_id, "tenant":tenant, "group":group, "data_ids":[], "datasources":[], "storage":[], "external_urls":[], "artifact_maven_hints":[], "fact_level":"UNVERIFIED", "gaps":["snapshot directory is missing or not a directory"]}
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in _EXTS)
    for path in files:
        text = _read_content(path)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        data_id = path.stem
        rel = path.relative_to(root).as_posix()
        rec = {"dataId": data_id, "sha256": digest, "bytes": len(text.encode("utf-8")), "path": rel, "redaction_applied": True}
        records.append(rec)
        parsed = _json_or_lines(text)
        values = list(_walk(parsed)) if parsed is not None else [("content", text)]
        for key, raw in values:
            value = _safe_text(raw)
            low = (str(key)+" "+value).lower()
            for url in _URL.findall(value):
                clean = re.sub(r"[?&](?:token|password|secret|api[_-]?key)=[^&\s]+", "", url, flags=re.I).rstrip("?&")
                urls.add(clean)
            for m in _JDBC.findall(value): datasources.add(m.lower())
            if any(x in low for x in ("s3://", "oss://", "cos://", "obs://", "minio", "object-storage", "objectstorage")): storages.add("object-storage")
            if "redis" in low: storages.add("redis")
            for m in _MAVEN.findall(value):
                artifacts.add(m)
    if not records: gaps.append("no supported snapshot files found")
    if not datasources: gaps.append("datasource evidence not found")
    if not storages: gaps.append("storage evidence not found")
    if not urls: gaps.append("external URL evidence not found")
    if not artifacts: gaps.append("artifact/maven hints not found")
    level = "FACT" if records and not gaps else ("PARTIAL" if records else "UNVERIFIED")
    return {"schema_version":"nacos-evidence-manifest.v1", "network":"disabled", "application_id":application_id, "tenant":tenant, "group":group, "data_ids":records, "datasources":sorted(datasources), "storage":sorted(storages), "external_urls":sorted(urls), "artifact_maven_hints":sorted(artifacts), "fact_level":level, "gaps":gaps}

__all__ = ["build_manifest"]
