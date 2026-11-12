import json
import subprocess
import sys
from pathlib import Path

from components.udc.path_matrix import PATH_KINDS, build_path_matrix, import_evidence


def test_matrix_contains_all_required_path_kinds_with_contract_fields():
    matrix = build_path_matrix({}, {}, {})
    assert [entry["kind"] for entry in matrix["entries"]] == PATH_KINDS
    for entry in matrix["entries"]:
        assert set(("status", "evidence_refs", "gaps", "dependencies")) <= set(entry)
        assert entry["status"] == "UNVERIFIED"


def test_import_evidence_projects_minimal_entries_and_marks_missing_proof_unverified(tmp_path):
    udc = {"controller_count": 2, "endpoint_count": 7}
    runtime = {"status": "FACT", "resources": {"page": 1}}
    http = {"status": "FACT", "probes": [{"label": "manifest", "classification": "PASS"}]}
    result = import_evidence(udc, runtime, http)
    by_kind = {entry["kind"]: entry for entry in result["entries"]}
    assert by_kind["Application"]["status"] == "UNVERIFIED"
    assert by_kind["Application"]["evidence_refs"] == []
    assert by_kind["Runtime Metadata"]["status"] == "UNVERIFIED"
    assert by_kind["Runtime Metadata"]["evidence_refs"]
    assert by_kind["Publish"]["status"] == "UNVERIFIED"
    assert "publish" in " ".join(by_kind["Publish"]["gaps"]).lower()


def test_cli_udc_path_matrix_emits_json(tmp_path):
    udc_path = tmp_path / "udc.json"
    runtime_path = tmp_path / "runtime.json"
    http_path = tmp_path / "http.json"
    for path, payload in ((udc_path, {"status": "FACT"}), (runtime_path, {}), (http_path, {})):
        path.write_text(json.dumps(payload), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "xiaozhua_cli.py", "udc-path-matrix", "--udc-json", str(udc_path), "--runtime", str(runtime_path), "--http", str(http_path)],
        cwd=Path(__file__).parents[1], capture_output=True, text=True,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["entries"]
    assert payload["entries"][0]["kind"] == "Application"


def test_path_matrix_is_not_fact_when_critical_paths_are_unverified():
    from components.udc.path_matrix import build_path_matrix
    result = build_path_matrix(runtime={"resources": {"pod": "ready"}}, http={"probes": []})
    assert result["status"] == "PARTIALLY_VERIFIED"


def test_probe_status_mapping_keeps_http_pass_distinct_from_live_pass_and_preserves_blocked_unverified():
    from components.udc.path_matrix import map_probe_status
    assert map_probe_status("PASS", source="http") == "HTTP_PASS"
    assert map_probe_status("PASS", source="runtime") == "LIVE_PASS"
    assert map_probe_status("BLOCKED", source="http") == "BLOCKED"
    assert map_probe_status("UNVERIFIED", source="runtime") == "UNVERIFIED"


def test_path_matrix_projects_probe_status_without_upgrading_http_to_live():
    result = build_path_matrix(
        runtime={"probes": [{"label": "runtime", "classification": "PASS"}]},
        http={"probes": [{"label": "http", "classification": "PASS"}, {"label": "blocked", "classification": "BLOCKED"}]},
    )
    entry = next(e for e in result["entries"] if e["kind"] == "Runtime Metadata")
    assert entry["probe_statuses"] == ["LIVE_PASS", "HTTP_PASS", "BLOCKED"]
    assert "HTTP PASS does not imply runtime verification" in entry["gaps"]


def test_path_matrix_accepts_scope_and_context_and_projects_binding_identity():
    result = build_path_matrix(
        scope={"application_id": "app-42", "environment": "uat"},
        context={"artifact_version": "2026.09.03"},
    )
    assert result["scope"] == {"application_id": "app-42", "environment": "uat"}
    assert result["context"] == {"artifact_version": "2026.09.03"}
    for entry in result["entries"]:
        assert entry["application_id"] == "app-42"
        assert entry["environment"] == "uat"
        assert entry["artifact_version"] == "2026.09.03"
        assert entry["status"] == "UNVERIFIED"


def test_path_matrix_does_not_upgrade_evidence_to_fact_without_complete_binding_identity():
    for scope, context in (
        ({"application_id": "app-42", "environment": "uat"}, {}),
        ({"application_id": "app-42"}, {"artifact_version": "2026.09.03"}),
        ({}, {"environment": "uat", "artifact_version": "2026.09.03"}),
    ):
        result = build_path_matrix(
            {"domains": {"Application": ["app"]}},
            scope=scope,
            context=context,
        )
        application = next(e for e in result["entries"] if e["kind"] == "Application")
        assert application["status"] != "FACT"
        assert result["status"] != "FACT"


def test_path_matrix_binding_fields_are_present_even_when_identity_is_missing():
    result = build_path_matrix({}, scope={"application_id": ""}, context={})
    for entry in result["entries"]:
        assert set(("application_id", "environment", "artifact_version", "status")) <= set(entry)
        assert entry["application_id"] is None
        assert entry["environment"] is None
        assert entry["artifact_version"] is None
