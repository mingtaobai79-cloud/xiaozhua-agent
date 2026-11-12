"""v0.2 Layer operation-specific validation and verification tests."""
import pytest

from components.platform_operations import ExecutionContext, PlatformOperationLayer, UdcEntityAdapter, UdcOperationRegistry
from components.platform_operations.models import OperationIntent, OperationStatus


class Gateway:
    def __init__(self, body):
        self.body = body
        self.calls = []

    def read(self, operation, path, **kwargs):
        self.calls.append((operation, path, kwargs))
        return {"verified": True, "response": {"status": 200, "body": self.body}}


def context():
    return ExecutionContext("session", "run", "principal", "credential", ("3289082814923688017:readonly",))


def test_application_get_does_not_require_entity_input():
    intent = OperationIntent("udc.application.get", "3289082814923688017")
    assert intent.entity_id is None


@pytest.mark.parametrize("operation", ["udc.entity.get", "udc.attribute.list"])
def test_entity_scoped_operations_require_entity_id(operation):
    with pytest.raises(ValueError, match="entity_id"):
        OperationIntent(operation, "3289082814923688017")


def test_entity_list_verification_requires_target_app_and_known_entity():
    body = {"status": 0, "code": "BOOT_0000", "data": {"content": [
        {"id": "1", "appId": "3289082814923688017", "name": "other"},
        {"id": "4649646467208458935", "appId": "3289082814923688017", "name": "hetongdangan"},
    ]}}
    gateway = Gateway(body)
    registry = UdcOperationRegistry.default()
    layer = PlatformOperationLayer(registry, UdcEntityAdapter(registry), gateway)
    result = layer.execute(OperationIntent("udc.entity.list", "3289082814923688017", context={"known_entity_id": "4649646467208458935"}), context())
    assert result.status == OperationStatus.PASS
    assert result.verification["identity_matches"] is True
    assert gateway.calls[0][1] == "/service/udc/entity/select-all-by-appid/3289082814923688017"


def test_attribute_list_verification_requires_target_entity_owner():
    body = {"status": 0, "code": "BOOT_0000", "data": {"content": [{"id": "a1", "entityId": "4649646467208458935", "appId": "3289082814923688017"}]}}
    gateway = Gateway(body)
    registry = UdcOperationRegistry.default()
    layer = PlatformOperationLayer(registry, UdcEntityAdapter(registry), gateway)
    result = layer.execute(OperationIntent("udc.attribute.list", "3289082814923688017", entity_id="4649646467208458935"), context())
    assert result.status == OperationStatus.PASS
    assert result.normalized_data[0]["entityId"] == "4649646467208458935"


def test_empty_collection_is_business_not_found_not_transport_success():
    gateway = Gateway({"status": 0, "code": "BOOT_0000", "data": {"content": []}})
    registry = UdcOperationRegistry.default()
    layer = PlatformOperationLayer(registry, UdcEntityAdapter(registry), gateway)
    result = layer.execute(OperationIntent("udc.entity.list", "3289082814923688017"), context())
    assert result.status == OperationStatus.FAIL
    assert result.error["kind"] == "BUSINESS_NOT_FOUND"
