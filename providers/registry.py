"""Read-only registry for infrastructure provider capabilities."""
from __future__ import annotations

from copy import deepcopy
from typing import Any


_DEFAULT_WRITES = ["all write operations denied"]


class ProviderRegistry:
    """Register and discover declarative provider metadata without instantiation or I/O."""

    def __init__(self):
        self._providers: dict[str, dict[str, Any]] = {}
        self._conflicts: list[dict[str, Any]] = []

    def register(self, name: str, *, capabilities: list[str], network_boundary: str = "disabled",
                 write_restrictions: list[str] | None = None, mode: str = "offline",
                 provider: Any = None) -> dict[str, Any]:
        if name in self._providers:
            self._conflicts.append({"name": name, "reason": "duplicate registration"})
            return deepcopy(self._providers[name])
        item = {
            "name": name,
            "capabilities": list(capabilities),
            "network_boundary": network_boundary,
            "write_restrictions": list(write_restrictions or _DEFAULT_WRITES),
            "mode": mode,
            "read_only": True,
        }
        if provider is not None:
            item["provider"] = provider
        self._providers[name] = item
        return deepcopy(item)

    def get(self, name: str) -> dict[str, Any]:
        return deepcopy(self._providers[name])

    def names(self) -> list[str]:
        return list(self._providers)

    def discover(self) -> list[dict[str, Any]]:
        return [self.get(name) for name in self.names()]

    def conflicts(self) -> list[dict[str, Any]]:
        return deepcopy(self._conflicts)

    def capabilities(self) -> dict[str, Any]:
        return {"mode": "read-only", "network": "disabled", "providers": {
            item["name"]: {key: value for key, value in item.items() if key != "name" and key != "provider"}
            for item in self.discover()
        }}


def default_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    common = {
        "http": (["get", "head"], "fixture"),
        "kubernetes": (["list", "get"], "fixture"),
        "nacos": (["get"], "fixture"),
        "mysql": (["read_tables", "read_columns", "read_indexes"], "fixture"),
        "redis": (["read"], "fixture"),
    }
    for name, (caps, mode) in common.items():
        registry.register(name, capabilities=caps, mode=mode)
    return registry


__all__ = ["ProviderRegistry", "default_provider_registry"]
