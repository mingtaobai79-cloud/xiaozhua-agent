import pytest

from components.platform_operations.layer import PlatformOperationLayer
from components.platform_operations.models import ExecutionContext, OperationIntent, OperationResult, OperationStatus
from components.platform_operations.registry import UdcOperationRegistry
from components.platform_operations.udc import UdcEntityAdapter


class FakeGatewayAdapter:
    def __init__(self, result=None):
        self.result = result or {"response": {"status": 200, "body": {"content": {"id": 123, "appId": "app-1"}}}, "verified": True}
        self.calls = []

    def read(self, operation, path, **kwargs):
        self.calls.append((operation, path, kwargs))
        return self.result


def context():
    return ExecutionContext("s1", "r1", "principal-1", "cred-1")


def test_operation_intent_requires_readonly_and_target():
    intent = OperationIntent(operation="udc.entity.get", application_id="app-1", entity_id=123, readonly=True)
    assert intent.operation == "udc.entity.get"
    assert intent.target == {"application_id": "app-1", "entity_id": 123}
    with pytest.raises(ValueError, match="readonly"):
        OperationIntent(operation="udc.entity.get", application_id="app-1", entity_id=123, readonly=False)


def test_operation_result_preserves_status_error_and_identity():
    result = OperationResult.blocked("udc.entity.get", session_id="s1", run_id="r1", reason="VPN unavailable")
    assert result.status == OperationStatus.BLOCKED
    assert result.session_id == "s1"
    assert result.run_id == "r1"
    assert result.error["code"] == "CONNECTION_ERROR"


def test_platform_layer_composes_intent_contract_adapter_result_and_session():
    gateway = FakeGatewayAdapter()
    layer = PlatformOperationLayer(UdcOperationRegistry.default(), UdcEntityAdapter(UdcOperationRegistry.default()), gateway)
    session = []
    intent = OperationIntent(operation="udc.entity.get", application_id="app-1", entity_id=123, session_id="s1", run_id="r1")

    result = layer.execute(intent, context(), session=session)

    assert result.status == OperationStatus.PASS
    assert result.normalized_data["id"] == 123
    assert result.session_id == "s1"
    assert result.run_id == "r1"
    assert gateway.calls[0][0] == "udc.entity.get"
    assert gateway.calls[0][1] == "/service/udc/entity/123"
    assert session[0]["run_id"] == "r1"


def test_platform_layer_blocks_declared_write_operation_before_adapter():
    gateway = FakeGatewayAdapter()
    layer = PlatformOperationLayer(UdcOperationRegistry.default(), UdcEntityAdapter(UdcOperationRegistry.default()), gateway)
    intent = OperationIntent(operation="udc.entity.create", application_id="app-1", entity_name="Customer", session_id="s1", run_id="r1")

    result = layer.execute(intent, context())

    assert result.status == OperationStatus.DENIED
    assert result.error["code"] == "POLICY_DENIED"
    assert gateway.calls == []
