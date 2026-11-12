import json

from components.platform_operations.evidence import OperationEvidenceStore
from components.platform_operations.models import OperationResult, OperationStatus


def test_operation_evidence_store_round_trips_without_credential(tmp_path):
    result = OperationResult(
        "udc.entity.get", OperationStatus.BLOCKED, "readonly", "session-1", "run-1",
        request={"headers": {"Cookie": "<REDACTED>"}},
        error={"kind": "CREDENTIAL_RESOLUTION_FAILED", "code": "CREDENTIAL_RESOLUTION_FAILED", "message": "missing"},
    )
    path = tmp_path / "operation.json"
    OperationEvidenceStore(path).save(result)

    restored = OperationEvidenceStore(path).load()

    assert restored["status"] == "BLOCKED"
    assert restored["session_id"] == "session-1"
    assert restored["run_id"] == "run-1"
    assert "credential_ref" not in json.dumps(restored)
    assert "Cookie" in restored["request"]["headers"]
    assert restored["request"]["headers"]["Cookie"] == "<REDACTED>"
