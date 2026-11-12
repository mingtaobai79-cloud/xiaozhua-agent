"""Offline, metadata-only Redis provider."""
from __future__ import annotations
import fnmatch, hashlib, json
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from core.providers import ProviderError, ProviderResult

class RedisFixtureAdapter:
    """Read Redis-like key records from a mapping or local JSON fixture."""
    def __init__(self, source: str | Path | Mapping[str, Any]): self.source = source
    def read(self) -> ProviderResult[dict[str, Any]]:
        if isinstance(self.source, Mapping): return ProviderResult(dict(self.source))
        path = Path(self.source)
        try: payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError as exc: return ProviderResult(error=ProviderError("unavailable", "Redis fixture was not found", {"path": str(path), "exception": type(exc).__name__}))
        except (OSError, UnicodeError) as exc: return ProviderResult(error=ProviderError("unavailable", "Redis fixture is unavailable", {"path": str(path), "exception": type(exc).__name__}))
        except (TypeError, ValueError) as exc: return ProviderResult(error=ProviderError("parse", "Redis fixture is not valid JSON", {"path": str(path), "exception": type(exc).__name__}))
        if not isinstance(payload, dict): return ProviderResult(error=ProviderError("parse", "Redis fixture must be a JSON object", {"path": str(path)}))
        return ProviderResult(payload)

class RedisReadonlyProvider:
    """Expose key pattern/type/TTL and bounded value summaries, never values."""
    network = "disabled"
    allow_network = False
    def __init__(self, adapter: RedisFixtureAdapter, *, allow_network: bool = False):
        if not hasattr(adapter, "read"): raise TypeError("adapter must provide read()")
        self.adapter = adapter
    @staticmethod
    def capabilities() -> list[str]: return ["read"]
    @staticmethod
    def _summary(value: Any) -> dict[str, Any]:
        if isinstance(value, bytes): raw = value
        elif isinstance(value, str): raw = value.encode("utf-8")
        else: raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        summary = {"sha256": hashlib.sha256(raw).hexdigest()[:16], "length": len(raw)}
        if isinstance(value, (list, tuple, set)): summary["items"] = len(value)
        elif isinstance(value, Mapping): summary["fields"] = len(value)
        return summary
    @staticmethod
    def _records(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
        raw = payload.get("keys", [])
        if isinstance(raw, Mapping): raw = [dict(record, key=key) if isinstance(record, Mapping) else {"key": key, "value": record} for key, record in raw.items()]
        if not isinstance(raw, list) or not all(isinstance(item, Mapping) for item in raw): raise ValueError("Redis fixture keys must be a list or object of records")
        return [dict(item) for item in raw]
    def read(self, *, pattern: str = "*", key_type: str | None = None, type: str | None = None) -> ProviderResult[list[dict[str, Any]]]:
        requested_type = key_type if key_type is not None else type
        loaded = self.adapter.read()
        base = {"network": self.network, "pattern": pattern, "type": requested_type, "keys": [], "count": 0, "classification": "UNVERIFIED"}
        if not loaded.ok: return ProviderResult(base, error=loaded.error)
        try: records = self._records(loaded)
        except ValueError as exc: return ProviderResult(base, error=ProviderError("parse", str(exc)))
        keys = [{"key": str(r.get("key", "")), "type": str(r.get("type", "none")), "ttl": r.get("ttl", -1), "value_summary": self._summary(r.get("value"))} for r in records if fnmatch.fnmatchcase(str(r.get("key", "")), pattern) and (requested_type is None or str(r.get("type", "none")) == requested_type)]
        keys.sort(key=lambda item: item["key"])
        base.update(keys=keys, count=len(keys), classification="PASS")
        return ProviderResult(keys, **base)
    def _deny(self, operation: str, *args: Any, **kwargs: Any) -> ProviderResult[None]: return ProviderResult(None, error=ProviderError("permission", f"Redis operation is denied: {operation}", {"operation": operation}), network=self.network, classification="DENIED", operation=operation)
    def delete(self, *args: Any, **kwargs: Any): return self._deny("delete", *args, **kwargs)
    def set(self, *args: Any, **kwargs: Any): return self._deny("set", *args, **kwargs)
    def flush(self, *args: Any, **kwargs: Any): return self._deny("flush", *args, **kwargs)
    def expire(self, *args: Any, **kwargs: Any): return self._deny("expire", *args, **kwargs)
    def execute(self, *args: Any, **kwargs: Any): return self._deny("execute", *args, **kwargs)

__all__ = ["RedisFixtureAdapter", "RedisReadonlyProvider"]
