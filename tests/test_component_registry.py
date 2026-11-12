from core.registry import ComponentRegistry
from core.ports import ComponentPort
from core.agent import AgentRequest, XiaozhuaAgent
from components.udc.component import UdcComponent

def test_registry_registers_components_and_discovers_capabilities():
    registry = ComponentRegistry()
    udc = UdcComponent()
    assert registry.register(udc) is udc
    assert registry.get("udc") is udc
    assert registry.names() == ["udc"]
    assert registry.capabilities("udc") == udc.capabilities()
    assert registry.discover() == {"udc": udc.capabilities()}

def test_registry_rejects_duplicate_component_names():
    registry = ComponentRegistry()
    registry.register(UdcComponent())
    import pytest
    with pytest.raises(ValueError, match="udc"):
        registry.register(UdcComponent())

def test_registry_dispatches_by_component_name():
    registry = ComponentRegistry([UdcComponent()])
    result = registry.dispatch("udc", "demo", "inspect_application")
    assert result["component"] == "udc"
    assert result["target"] == "demo"
    assert result["status"] == "UNVERIFIED"

def test_agent_accepts_registry_and_preserves_legacy_dispatch():
    registry = ComponentRegistry([UdcComponent()])
    agent = XiaozhuaAgent(registry)
    result = agent.dispatch(AgentRequest("分析 UDC 实体", {"target": "demo"}))
    assert result["component"] == "udc"
    assert result["target"] == "demo"

def test_component_port_is_runtime_checkable_contract():
    assert isinstance(UdcComponent(), ComponentPort)
