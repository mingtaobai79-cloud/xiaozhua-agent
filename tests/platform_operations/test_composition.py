"""平台操作层组合验证：不依赖真实网络，验证跨模块边界。"""
from components.gateway.adapter import GatewayAdapter
from components.gateway.client import GatewayReadonlyClient
from components.platform_operations import ExecutionContext, PlatformOperationLayer, UdcEntityAdapter, UdcOperationRegistry
from components.platform_operations.models import OperationIntent, OperationStatus


def test_platform_operation_layer_composes_real_gateway_adapter_with_blocked_network():
    registry = UdcOperationRegistry.default()
    client = GatewayReadonlyClient(base_url="https://gateway.test", allow_network=False)
    gateway = GatewayAdapter(client, gateway_name="gateway.test", credential_provider=None)
    layer = PlatformOperationLayer(registry, UdcEntityAdapter(registry), gateway)
    session = []

    result = layer.execute(OperationIntent("udc.entity.get", "app-1", entity_id=123, session_id="s1", run_id="r1"), ExecutionContext("s1", "r1", "principal-1", "cred-1"), session=session)

    assert result.status == OperationStatus.BLOCKED
    assert result.error["code"] == "CREDENTIAL_RESOLUTION_FAILED"
    assert result.request == {}
    assert result.session_id == "s1"
    assert result.run_id == "r1"
    assert session[0]["status"] == "BLOCKED"
