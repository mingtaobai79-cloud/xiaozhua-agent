"""认证上下文的边界测试。"""
from __future__ import annotations

from components.gateway.adapter import GatewayAdapter
from components.gateway.client import GatewayReadonlyClient
from components.gateway.credentials import MappingCredentialProvider
from components.platform_operations import PlatformOperationLayer, UdcEntityAdapter, UdcOperationRegistry
from components.platform_operations.models import ExecutionContext, OperationIntent, OperationStatus


class FakeResponse:
    status = 200
    headers = {"Content-Type": "application/json"}

    def read(self, n=-1):
        return b'{"status":0,"code":"BOOT_0000","message":"SUCCESS","data":{"content":{"id":"123","appId":"app-1"}}}'

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    def open(self, request, timeout):
        assert request.method == "GET"
        assert request.headers.get("Cookie") == "session=secret"
        return FakeResponse()


def test_execution_context_is_runtime_only_and_intent_has_no_auth_fields():
    intent = OperationIntent("udc.entity.get", "app-1", entity_id=123)
    context = ExecutionContext("s1", "r1", "principal-1", "cred-1", ("app-1:readonly",))
    assert not hasattr(intent, "credential_ref")
    assert context.to_safe_dict()["credential_ref"] == "<REDACTED-ID>"
    assert "secret" not in repr(context.to_safe_dict())


def test_missing_context_fails_closed_without_gateway_call():
    registry = UdcOperationRegistry.default()
    gateway = GatewayAdapter(GatewayReadonlyClient(base_url="https://gateway.test"), gateway_name="gateway.test")
    layer = PlatformOperationLayer(registry, UdcEntityAdapter(registry), gateway)
    result = layer.execute(OperationIntent("udc.entity.get", "app-1", entity_id=123))
    assert result.status == OperationStatus.BLOCKED
    assert result.error["code"] == "MISSING_EXECUTION_CONTEXT"


def test_authenticated_platform_layer_composition_keeps_credential_out_of_result():
    registry = UdcOperationRegistry.default()
    provider = MappingCredentialProvider({"cred-1": {"Cookie": "session=secret"}})
    client = GatewayReadonlyClient(base_url="https://gateway.test", allow_network=True, opener=FakeOpener())
    gateway = GatewayAdapter(client, gateway_name="gateway.test", credential_provider=provider)
    layer = PlatformOperationLayer(registry, UdcEntityAdapter(registry), gateway)
    context = ExecutionContext("s1", "r1", "principal-1", "cred-1")

    result = layer.execute(OperationIntent("udc.entity.get", "app-1", entity_id=123), context)

    assert result.status == OperationStatus.PASS
    assert result.normalized_data["id"] == "123"
    serialized = repr(result.to_dict())
    assert "session=secret" not in serialized
    assert "cred-1" not in serialized
    assert result.session_id == "s1"
    assert result.run_id == "r1"


def test_unresolvable_credential_does_not_send_request():
    registry = UdcOperationRegistry.default()
    provider = MappingCredentialProvider({})
    client = GatewayReadonlyClient(base_url="https://gateway.test", allow_network=True, opener=FakeOpener())
    gateway = GatewayAdapter(client, gateway_name="gateway.test", credential_provider=provider)
    layer = PlatformOperationLayer(registry, UdcEntityAdapter(registry), gateway)
    context = ExecutionContext("s1", "r1", "principal-1", "missing")

    result = layer.execute(OperationIntent("udc.entity.get", "app-1", entity_id=123), context)

    assert result.status == OperationStatus.BLOCKED
    assert result.error["code"] == "CREDENTIAL_RESOLUTION_FAILED"
    assert result.response is None
