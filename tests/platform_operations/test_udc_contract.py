from components.platform_operations.models import OperationStatus, UdcOperationContract
from components.platform_operations.registry import UdcOperationRegistry
from components.platform_operations.udc import UdcEntityAdapter

def test_entity_contract_exposes_verified_read_operations():
    registry=UdcOperationRegistry.default()
    create=registry.get("udc.entity.create")
    assert create.status == OperationStatus.VERIFIED_STATIC_BYTECODE
    assert create.http_method == "POST"
    assert create.path == "/udc/entity"
    assert create.request_type == "com.seeyon.udc.common.dto.EntityDto"
    assert create.write is True

def test_read_operations_build_routes_without_network():
    adapter=UdcEntityAdapter(UdcOperationRegistry.default())
    req=adapter.select_by_id(123)
    assert req.method == "GET"
    assert req.path == "/udc/entity/123"
    assert req.write is False
    assert req.evidence

def test_attribute_read_route_is_separate_from_entity_create():
    adapter=UdcEntityAdapter(UdcOperationRegistry.default())
    req=adapter.select_all_attributes(456)
    assert req.method == "GET"
    assert req.path == "/udc/entity/456/attributes"
    assert req.operation_id == "udc.entity.attributes.list"

def test_write_operations_require_explicit_execution():
    adapter=UdcEntityAdapter(UdcOperationRegistry.default())
    req=adapter.create_payload({"name":"Customer"})
    assert req.method == "POST"
    assert req.write is True
    assert req.payload == {"name":"Customer"}
