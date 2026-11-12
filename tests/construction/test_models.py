from components.construction.models import EvidenceRef, NormalizedAttribute, NormalizedEntityModel, GeneratedArtifact, GeneratedArtifactPlan

def test_normalized_model_preserves_unknown_and_serializes():
    model = NormalizedEntityModel(application_id="demoapp", package_root=None, entity_name="Customer", attributes=[NormalizedAttribute(name="status", type="UNKNOWN")])
    data = model.to_dict()
    assert data["application_id"] == "demoapp"
    assert data["attributes"][0]["type"] == "UNKNOWN"

def test_artifact_plan_is_data_only():
    artifact = GeneratedArtifact("facade", "dto", "com.seeyon.demoapp.dto", "CustomerDto", "facade/dto/CustomerDto.java")
    plan = GeneratedArtifactPlan("udc.construction.artifact-plan.v1", "demoapp", "Customer", [artifact])
    assert plan.to_dict()["artifacts"][0]["class_name"] == "CustomerDto"
