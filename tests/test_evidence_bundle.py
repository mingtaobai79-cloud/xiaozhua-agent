from pathlib import Path

from components.evidence_bundle import EvidenceBundle


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "udc-audit"


def test_repository_udc_evidence_bundle_is_self_contained_and_bounded():
    result = EvidenceBundle(FIXTURE).validate()

    assert result["status"] == "FACT"
    assert result["schema_version"] == "udc-evidence-bundle.v1"
    assert result["application_id"] == "app9000000000000000001"
    assert result["artifact_version"] == "5.3.517"
    assert result["files_loaded"] == 11
    assert result["missing"] == []
    assert result["verification_level"] == "FIXTURE"
    assert result["limitations"]


def test_missing_evidence_bundle_is_unverified(tmp_path):
    result = EvidenceBundle(tmp_path / "missing").validate()

    assert result["status"] == "UNVERIFIED"
    assert result["files_loaded"] == 0
    assert result["missing"] == ["manifest.json"]
