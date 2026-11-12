"""UDC v0.2 readonly capability contracts and adapter mapping tests."""
from components.platform_operations import UdcApplicationAdapter, UdcEntityAdapter, UdcOperationRegistry


def test_v02_readonly_registry_contains_only_the_four_expansion_operations():
    registry = UdcOperationRegistry.default()
    expected = {"udc.application.get", "udc.entity.get", "udc.entity.list", "udc.attribute.list"}
    assert expected.issubset(registry.all())
    for operation in expected:
        contract = registry.get(operation)
        assert contract.method == "GET"
        assert contract.write is False
        assert contract.effective is True
        assert contract.required_inputs
        assert contract.verification_rules


def test_application_get_maps_application_id_to_gateway_path():
    registry = UdcOperationRegistry.default()
    request = UdcApplicationAdapter(registry).get(3289082814923688017)
    assert request.operation_id == "udc.application.get"
    assert request.method == "GET"
    assert request.path == "/udc/application/3289082814923688017"
    assert request.write is False


def test_entity_list_maps_application_id_without_pagination_guess():
    registry = UdcOperationRegistry.default()
    request = UdcEntityAdapter(registry).list_by_application(3289082814923688017)
    assert request.operation_id == "udc.entity.list"
    assert request.path == "/udc/entity/select-all-by-appid/3289082814923688017"
    assert request.payload is None


def test_attribute_list_maps_entity_id_and_keeps_owner_verification_rule():
    registry = UdcOperationRegistry.default()
    request = UdcEntityAdapter(registry).list_attributes(4649646467208458935)
    assert request.operation_id == "udc.attribute.list"
    assert request.path == "/udc/entity/attribute/select-all-by-entity-id/4649646467208458935"
    assert request.evidence
