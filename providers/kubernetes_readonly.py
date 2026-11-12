"""Offline, read-only Kubernetes resource provider.

This module deliberately has no Kubernetes client dependency and never opens a
network connection.  The fixture adapter is the only data source in this
phase; live cluster access is an explicit, unsupported boundary.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from core.providers import ProviderError, ProviderResult


_NETWORK = "disabled"
_DENIED_OPERATIONS = ("exec", "apply", "patch", "delete")


class KubernetesFixtureAdapter:
    """Read Kubernetes-like resources from a mapping or local JSON fixture."""

    def __init__(self, source: str | Path | Mapping[str, Any]):
        self.source = source

    def read(self) -> ProviderResult[dict[str, Any]]:
        if isinstance(self.source, Mapping):
            return ProviderResult(dict(self.source))
        path = Path(self.source)
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError as exc:
            return ProviderResult(error=ProviderError("unavailable", "Kubernetes fixture was not found", {"path": str(path), "exception": type(exc).__name__}))
        except (OSError, UnicodeError) as exc:
            return ProviderResult(error=ProviderError("unavailable", "Kubernetes fixture is unavailable", {"path": str(path), "exception": type(exc).__name__}))
        except (TypeError, ValueError) as exc:
            return ProviderResult(error=ProviderError("parse", "Kubernetes fixture is not valid JSON", {"path": str(path), "exception": type(exc).__name__}))
        if not isinstance(payload, dict):
            return ProviderResult(error=ProviderError("parse", "Kubernetes fixture must be a JSON object", {"path": str(path)}))
        return ProviderResult(payload)


class KubernetesReadonlyProvider:
    """Expose only deterministic Kubernetes list/get reads."""

    network = _NETWORK

    def __init__(self, adapter: KubernetesFixtureAdapter):
        if not hasattr(adapter, "read"):
            raise TypeError("adapter must provide read()")
        self.adapter = adapter

    @staticmethod
    def capabilities() -> list[str]:
        return ["list", "get"]

    def _resources(self) -> ProviderResult[list[dict[str, Any]]]:
        payload = self.adapter.read()
        if not payload.ok:
            return ProviderResult([], error=payload.error, network=_NETWORK, resources=[])
        raw = payload.get("resources", [])
        if isinstance(raw, Mapping):
            raw = list(raw.values())
        if not isinstance(raw, list) or not all(isinstance(item, Mapping) for item in raw):
            return ProviderResult([], error=ProviderError("parse", "fixture resources must be a list of objects"), network=_NETWORK, resources=[])
        return ProviderResult([dict(item) for item in raw])

    def list_resources(self, *, namespace: str | None = None, kind: str | None = None) -> ProviderResult[list[dict[str, Any]]]:
        result = self._resources()
        if not result.ok:
            return result
        resources = result.value or []
        if namespace is not None:
            resources = [item for item in resources if item.get("metadata", {}).get("namespace") == namespace]
        if kind is not None:
            resources = [item for item in resources if item.get("kind") == kind]
        return ProviderResult(resources, network=_NETWORK, resources=resources, count=len(resources), classification="PASS")

    def get_resource(self, kind: str, name: str, *, namespace: str | None = None) -> ProviderResult[dict[str, Any]]:
        result = self.list_resources(namespace=namespace, kind=kind)
        if not result.ok:
            return result
        matches = [item for item in (result.value or []) if item.get("metadata", {}).get("name") == name]
        if not matches:
            return ProviderResult({}, error=ProviderError("not_found", "Kubernetes resource was not found", {"kind": kind, "name": name, "namespace": namespace}), network=_NETWORK, resource=None, classification="UNVERIFIED")
        return ProviderResult(matches[0], network=_NETWORK, resource=matches[0], classification="PASS")

    def _deny(self, operation: str, *args: Any, **kwargs: Any) -> ProviderResult[None]:
        return ProviderResult(None, error=ProviderError("permission", f"Kubernetes operation is denied: {operation}", {"operation": operation}), network=_NETWORK, classification="DENIED", operation=operation)

    def exec(self, *args: Any, **kwargs: Any):
        return self._deny("exec", *args, **kwargs)

    def apply(self, *args: Any, **kwargs: Any):
        return self._deny("apply", *args, **kwargs)

    def patch(self, *args: Any, **kwargs: Any):
        return self._deny("patch", *args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any):
        return self._deny("delete", *args, **kwargs)


__all__ = ["KubernetesFixtureAdapter", "KubernetesReadonlyProvider"]
