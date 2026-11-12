import json

import pytest

from providers.kubernetes_readonly import (
    KubernetesReadonlyProvider,
    KubernetesFixtureAdapter,
)


def test_fixture_provider_lists_resources_with_offline_boundary(tmp_path):
    fixture = tmp_path / "kubernetes.json"
    fixture.write_text(json.dumps({
        "resources": [
            {"apiVersion": "v1", "kind": "Pod", "metadata": {"name": "api", "namespace": "test2"}, "status": {"phase": "Running"}},
            {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "api", "namespace": "test2"}},
        ]
    }), encoding="utf-8")

    result = KubernetesReadonlyProvider(KubernetesFixtureAdapter(fixture)).list_resources(namespace="test2")

    assert result.ok
    assert result["network"] == "disabled"
    assert result["resources"] == [
        {"apiVersion": "v1", "kind": "Pod", "metadata": {"name": "api", "namespace": "test2"}, "status": {"phase": "Running"}},
        {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "api", "namespace": "test2"}},
    ]
    assert result["count"] == 2


def test_fixture_provider_classifies_missing_fixture(tmp_path):
    result = KubernetesReadonlyProvider(KubernetesFixtureAdapter(tmp_path / "missing.json")).list_resources()
    assert not result.ok
    assert result.error.kind == "unavailable"
    assert result["network"] == "disabled"
    assert result["resources"] == []


def test_fixture_provider_classifies_invalid_fixture(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("not-json", encoding="utf-8")
    result = KubernetesReadonlyProvider(KubernetesFixtureAdapter(path)).list_resources()
    assert not result.ok
    assert result.error.kind == "parse"


@pytest.mark.parametrize("operation", ["exec", "apply", "patch", "delete"])
def test_write_and_exec_operations_are_denied(operation):
    provider = KubernetesReadonlyProvider(KubernetesFixtureAdapter({"resources": []}))
    result = getattr(provider, operation)("Pod", "api")
    assert not result.ok
    assert result.error.kind == "permission"
    assert result["classification"] == "DENIED"
    assert result["network"] == "disabled"


def test_provider_does_not_accept_network_client():
    provider = KubernetesReadonlyProvider(KubernetesFixtureAdapter({"resources": []}))
    assert provider.network == "disabled"
    assert provider.capabilities() == ["list", "get"]
