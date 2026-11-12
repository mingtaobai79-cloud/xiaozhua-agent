"""Storage discovery from public Nacos configuration."""
from __future__ import annotations
import json, re
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any
from core.providers import ProviderResult

STORAGE_TYPES = frozenset({"mysql", "postgres", "oracle", "redis", "object-storage", "unknown"})
_JDBC_RE = re.compile(r"jdbc:(mysql|postgresql|postgres|oracle):", re.I)
_OBJECT_RE = re.compile(r"(?:s3|s3a|oss|cos|obs|minio|az|azure|gs)://", re.I)

def _walk(value: Any, path: str = ""):
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for i, child in enumerate(value): yield from _walk(child, f"{path}[{i}]")
    else: yield path, value

def _parse_content(content: Any):
    if isinstance(content, Mapping): return content, None
    if not isinstance(content, str): return None, "config content must be an object or string"
    try:
        parsed = json.loads(content)
        if isinstance(parsed, Mapping): return parsed, None
    except (TypeError, ValueError): pass
    result = {}
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("---"): continue
        match = re.match(r"([^:=\s]+(?:\.[^:=\s]+)*)\s*[:=]\s*(.*?)\s*$", line)
        if match:
            key, value = match.groups(); result[key] = value.strip("'\"")
    return (result, None) if result else (None, "config content is not parseable JSON/YAML/properties")

def _normalise_type(value: str) -> str:
    return {"postgresql": "postgres", "object_storage": "object-storage"}.get(value.lower(), value.lower())

def discover_storage(config: Mapping[str, Any]) -> dict[str, Any]:
    root = config
    if "content" in config:
        root, error = _parse_content(config["content"])
        if error: return {"storage_type":"unknown", "metadata_location":None, "classification":"UNVERIFIED", "status":"UNVERIFIED", "error":error, "evidence":[]}
    candidates, location = [], None
    for path, raw in _walk(root):
        value = str(raw); lp, lv = path.lower(), value.lower()
        if any(x in lp for x in ("metadata.location", "metadata_location", "metadata-uri", "metadata_uri")) or lp in {"metadata", "location"}:
            if value:
                location = value
                continue
        match = _JDBC_RE.search(value)
        if match: candidates.append((_normalise_type(match.group(1)), path))
        elif "redis" in lp or re.search(r"(?:^|[/:])redis(?:$|[/:?])", lv): candidates.append(("redis", path))
        elif _OBJECT_RE.search(value) or any(x in lp for x in ("bucket", "objectstorage", "object-storage", "s3.endpoint", "oss.endpoint")): candidates.append(("object-storage", path))
        elif lp.endswith(("storage.type", "database.type", "datasource.type")) or lp in {"storage.type", "database.type", "db.type"}:
            kind = _normalise_type(lv); candidates.append((kind if kind in STORAGE_TYPES else "unknown", path))
    types = {k for k, _ in candidates if k in STORAGE_TYPES and k != "unknown"}
    selected = next(iter(types), "unknown") if len(types) == 1 else "unknown"
    classification = "PASS" if selected != "unknown" else "UNVERIFIED"
    evidence = [{"level":"FACT" if selected != "unknown" else "UNVERIFIED", "source":"nacos-public-config", "locator":p, "detail":{"storage_type":k}} for k,p in candidates]
    if location: evidence.append({"level":"FACT", "source":"nacos-public-config", "locator":"metadata.location", "detail":{"metadata_location":location}})
    return {"storage_type":selected, "metadata_location":location, "classification":classification, "status":classification, "candidates":sorted(types), "evidence":evidence}

class StorageDiscovery(ABC):
    @abstractmethod
    def discover(self) -> ProviderResult[dict[str, Any]]: raise NotImplementedError

class NacosPublicStorageDiscovery(StorageDiscovery):
    def __init__(self, provider: Any, *, data_id="application.yml", group="DEFAULT_GROUP", namespace="public"):
        self.provider, self.data_id, self.group, self.namespace = provider, data_id, group, namespace
    def discover(self):
        query={"dataId":self.data_id,"group":self.group,"namespace":self.namespace}
        read=self.provider.get_config(data_id=self.data_id, group=self.group, namespace=self.namespace)
        if not read.ok:
            classification=read.get("classification", "UNVERIFIED")
            if classification not in {"BLOCKED", "UNVERIFIED"}: classification="UNVERIFIED"
            return ProviderResult({"storage_type":"unknown","metadata_location":None,"classification":classification,"status":classification,"evidence":[]}, error=read.error, query=query)
        return ProviderResult(discover_storage(read), query=query, network=read.get("network", "disabled"))

__all__=["STORAGE_TYPES","StorageDiscovery","NacosPublicStorageDiscovery","discover_storage"]
