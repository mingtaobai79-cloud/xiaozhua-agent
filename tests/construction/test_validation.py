from components.construction.models import GeneratedArtifact, GeneratedArtifactPlan, NormalizedEntityModel
from components.construction.registry import ConstructionRuleRegistry
from components.construction.evaluator import ConstructionEvaluator
from components.construction.validation import validate_plan, compare_artifact_plan
from pathlib import Path

def registry(): return ConstructionRuleRegistry(Path(__file__).resolve().parents[2] / "docs" / "construction-rules").load()

def test_validation_detects_duplicate_and_required_artifacts():
    plan = GeneratedArtifactPlan("v1", "demoapp", "Customer", [GeneratedArtifact("facade", "dto", "com.seeyon.demoapp.dto", "CustomerDto", "facade/dto/CustomerDto.java"), GeneratedArtifact("facade", "dto", "com.seeyon.demoapp.dto", "CustomerDto", "facade/dto/CustomerDto.java")])
    result = validate_plan(plan)
    assert result.status == "FAIL"
    assert any("duplicate" in x for x in result.blocked)
    assert any("required" in x for x in result.blocked)

def test_golden_diff_passes_for_hetongdangan():
    plan = ConstructionEvaluator(registry()).plan(NormalizedEntityModel("app9000000000000000001", None, "Hetongdangan"))
    observed = [a.fully_qualified_name for a in plan.artifacts]
    diff = compare_artifact_plan(plan, observed)
    assert diff.status == "PASS"
    assert len(diff.matched) == 8
    assert diff.missing == [] and diff.unexpected == []

def test_golden_diff_reports_partial():
    plan = ConstructionEvaluator(registry()).plan(NormalizedEntityModel("demoapp", None, "Customer"))
    diff = compare_artifact_plan(plan, [plan.artifacts[0].fully_qualified_name])
    assert diff.status == "PARTIAL"
    assert len(diff.missing) == 7
