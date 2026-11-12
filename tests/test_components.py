from components.runtime import RuntimeComponent
from components.integration import IntegrationComponent

def test_runtime_component_contract_is_read_only():
    component = RuntimeComponent()
    assert component.read_only is True
    assert "inspect_pod" in component.capabilities()
    assert component.inspect("pod")["status"] == "UNVERIFIED"

def test_integration_component_contract_is_read_only():
    component = IntegrationComponent()
    assert component.read_only is True
    assert "trace_http" in component.capabilities()
    assert component.inspect("sync")["status"] == "UNVERIFIED"


def test_runtime_component_can_read_local_snapshot():
    from pathlib import Path
    snapshot = Path("runtime.json")
    snapshot.write_text('{"environment":"test2","pod":"udc"}', encoding="utf-8")
    result = RuntimeComponent(snapshot_path=snapshot).inspect("udc")
    assert result["status"] == "FACT"
    assert result["snapshot"]["environment"] == "test2"

def test_integration_component_can_read_local_snapshot():
    from pathlib import Path
    snapshot = Path("integration.json")
    snapshot.write_text('{"http":200,"business_code":"SUCCESS"}', encoding="utf-8")
    result = IntegrationComponent(snapshot_path=snapshot).inspect("invoice")
    assert result["status"] == "FACT"
    assert result["snapshot"]["http"] == 200
