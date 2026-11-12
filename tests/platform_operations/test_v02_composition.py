from components.platform_operations import ExecutionContext, PlatformOperationLayer, UdcApplicationAdapter, UdcEntityAdapter, UdcOperationRegistry
from components.platform_operations.models import OperationIntent, OperationStatus


class FakeGateway:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def read(self, operation, path, **kwargs):
        self.calls.append((operation, path, kwargs))
        return self.responses[operation]


def _layer(responses):
    registry = UdcOperationRegistry.default()
    return PlatformOperationLayer(registry, {"application": UdcApplicationAdapter(registry), "entity": UdcEntityAdapter(registry)}, FakeGateway(responses))


def test_application_entity_list_and_attribute_list_normalize_and_verify():
    responses = {
        "udc.application.get": {"verified": True, "response": {"body": {"status": 0, "code": "BOOT_0000", "data": {"content": {"id": "3289082814923688017", "name": "项目管理"}}}}},
        "udc.entity.list": {"verified": True, "response": {"body": {"status": 0, "code": "BOOT_0000", "data": {"content": [{"id": "1", "appId": "3289082814923688017"}]}}}},
        "udc.attribute.list": {"verified": True, "response": {"body": {"status": 0, "code": "BOOT_0000", "data": {"content": [{"id": "a1", "entityId": "4649646467208458935"}]}}}},
    }
    layer = _layer(responses)
    context = ExecutionContext("s", "r", "p", "c", ("3289082814923688017:readonly",))
    app = layer.execute(OperationIntent("udc.application.get", "3289082814923688017", entity_name="application"), context)
    entities = layer.execute(OperationIntent("udc.entity.list", "3289082814923688017", entity_name="entity"), context)
    attrs = layer.execute(OperationIntent("udc.attribute.list", "3289082814923688017", entity_id="4649646467208458935"), context)
    assert app.status == OperationStatus.PASS and app.normalized_data["id"] == "3289082814923688017"
    assert entities.status == OperationStatus.PASS and entities.normalized_data[0]["appId"] == "3289082814923688017"
    assert attrs.status == OperationStatus.PASS and attrs.normalized_data[0]["entityId"] == "4649646467208458935"


def test_auth_scope_denies_other_application_before_gateway():
    responses = {"udc.entity.get": {"verified": True, "response": {"body": {"data": {"content": {"id": "1", "appId": "other"}}}}}}
    layer = _layer(responses)
    context = ExecutionContext("s", "r", "p", "c", ("other:readonly",))
    result = layer.execute(OperationIntent("udc.entity.get", "3289082814923688017", entity_id="1"), context)
    assert result.status == OperationStatus.DENIED
    assert result.error["code"] == "AUTH_SCOPE_DENIED"
    assert layer.gateway_adapter.calls == []
