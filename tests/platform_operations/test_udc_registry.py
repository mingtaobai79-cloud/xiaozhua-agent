from components.platform_operations.registry import UdcOperationRegistry

def test_registry_keeps_unknown_operations_out_of_verified_set():
    r=UdcOperationRegistry.default()
    assert r.has("udc.entity.create")
    assert r.has("udc.entity.select")
    assert not r.has("udc.entity.graphql.create")
    assert r.get("udc.entity.create").evidence[0]["source"] == "test2-container"
