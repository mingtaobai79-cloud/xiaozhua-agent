from pathlib import Path
from components.construction.registry import ConstructionRuleRegistry

def test_registry_loads_only_executable_rules():
    root = Path(__file__).resolve().parents[2] / "docs" / "construction-rules"
    registry = ConstructionRuleRegistry(root).load()
    assert registry.has("udc.construction.entity.naming.v1")
    assert registry.has("udc.construction.entity.package.v1")
    assert registry.has("udc.construction.entity.generation-contract.v1")
    assert not registry.has("udc.entity.attribute-propagation.v1")
    assert registry.get("udc.construction.entity.naming.v1").status == "STATIC_RULE_CROSS_SAMPLE_OBSERVED"
