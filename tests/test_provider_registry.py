import json
import subprocess
import sys
from pathlib import Path

from providers.registry import ProviderRegistry, default_provider_registry

ROOT = Path(__file__).parents[1]


def test_default_registry_discovers_all_readonly_providers():
    registry = default_provider_registry()
    assert registry.names() == ["http", "kubernetes", "nacos", "mysql", "redis"]
    discovered = registry.discover()
    assert {item["name"] for item in discovered} == set(registry.names())
    for item in discovered:
        assert item["mode"] in {"offline", "fixture"}
        assert item["network_boundary"] == "disabled"
        assert item["write_restrictions"]
        assert item["read_only"] is True


def test_registry_rejects_duplicate_provider_names_without_replacement():
    registry = ProviderRegistry()
    registry.register("demo", capabilities=["read"], network_boundary="disabled", write_restrictions=["all writes denied"])
    registry.register("demo", capabilities=["other"], network_boundary="enabled", write_restrictions=[])
    assert registry.get("demo")["capabilities"] == ["read"]
    assert registry.conflicts()[0]["name"] == "demo"


def test_registry_capabilities_is_json_serializable_and_read_only():
    payload = default_provider_registry().capabilities()
    assert payload["mode"] == "read-only"
    assert payload["network"] == "disabled"
    assert set(payload["providers"]) == {"http", "kubernetes", "nacos", "mysql", "redis"}
    assert all(item["read_only"] for item in payload["providers"].values())
    json.dumps(payload)


def test_provider_capabilities_cli_returns_registry_projection():
    result = subprocess.run(
        [sys.executable, "-m", "seeyon_cli", "provider-capabilities"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["mode"] == "read-only"
    assert set(payload["providers"]) == {"http", "kubernetes", "nacos", "mysql", "redis"}
    assert all(item["network_boundary"] == "disabled" for item in payload["providers"].values())
    assert all(item["write_restrictions"] for item in payload["providers"].values())
