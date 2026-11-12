"""Offline fixture adapter for read-only Nacos configuration queries."""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from core.providers import ProviderError, ProviderResult


class NacosFixtureAdapter:
    """Load Nacos config records from a mapping or local JSON fixture."""

    def __init__(self, source: str | Path | Mapping[str, Any]):
        self.source = source

    def read(self) -> ProviderResult[dict[str, Any]]:
        if isinstance(self.source, Mapping):
            return ProviderResult(dict(self.source))
        path = Path(self.source)
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError as exc:
            return ProviderResult(error=ProviderError("unavailable", "Nacos fixture was not found", {"path": str(path), "exception": type(exc).__name__}))
        except (OSError, UnicodeError) as exc:
            return ProviderResult(error=ProviderError("unavailable", "Nacos fixture is unavailable", {"path": str(path), "exception": type(exc).__name__}))
        except (TypeError, ValueError) as exc:
            return ProviderResult(error=ProviderError("parse", "Nacos fixture is not valid JSON", {"path": str(path), "exception": type(exc).__name__}))
        if not isinstance(payload, dict):
            return ProviderResult(error=ProviderError("parse", "Nacos fixture must be a JSON object", {"path": str(path)}))
        return ProviderResult(payload)


class NacosReadonlyProvider:
    """Provide offline Nacos reads; publish/update/delete are always denied."""

    network = "disabled"
    allow_network = False

    def __init__(self, adapter: NacosFixtureAdapter):
        if not hasattr(adapter, "read"):
            raise TypeError("adapter must provide read()")
        self.adapter = adapter

    @staticmethod
    def capabilities() -> list[str]:
        return ["get"]

    def get_config(self, *, data_id: str, group: str, namespace: str = "") -> ProviderResult[dict[str, Any]]:
        query = {"dataId": data_id, "group": group, "namespace": namespace}
        result = self.adapter.read()
        if not result.ok:
            return ProviderResult({}, error=result.error, network=self.network, query=query, classification="UNVERIFIED")
        records = result.get("configs", [])
        if isinstance(records, Mapping):
            records = list(records.values())
        if not isinstance(records, list) or not all(isinstance(record, Mapping) for record in records):
            return ProviderResult({}, error=ProviderError("parse", "Nacos fixture configs must be a list of objects"), network=self.network, query=query, classification="UNVERIFIED")
        matches = [dict(record) for record in records if all(record.get(key) == value for key, value in query.items())]
        if not matches:
            return ProviderResult({}, error=ProviderError("not_found", "Nacos config was not found", query), network=self.network, query=query, classification="UNVERIFIED")
        record = matches[0]
        error = record.get("error")
        if error:
            if isinstance(error, Mapping):
                kind = str(error.get("kind", "unavailable"))
                message = str(error.get("message", "Nacos config read failed"))
            else:
                kind, message = "unavailable", str(error)
            try:
                provider_error = ProviderError(kind, message, query)
            except ValueError:
                provider_error = ProviderError("unavailable", message, query)
            return ProviderResult(record, error=provider_error, network=self.network, query=query, classification="BLOCKED" if provider_error.kind == "permission" else "UNVERIFIED")
        return ProviderResult(record, network=self.network, query=query, classification="PASS")

    def _deny(self, operation: str, *args: Any, **kwargs: Any) -> ProviderResult[None]:
        return ProviderResult(None, error=ProviderError("permission", f"Nacos operation is denied: {operation}", {"operation": operation}), network=self.network, classification="DENIED", operation=operation)

    def publish(self, *args: Any, **kwargs: Any):
        return self._deny("publish", *args, **kwargs)

    def update(self, *args: Any, **kwargs: Any):
        return self._deny("update", *args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any):
        return self._deny("delete", *args, **kwargs)


__all__ = ["NacosFixtureAdapter", "NacosReadonlyProvider"]
