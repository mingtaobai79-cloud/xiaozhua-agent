import json
from pathlib import Path

def test_build_evidence_context_binds_target_version_trace_and_sources():
    from components.evidence_context import build_evidence_context
    result = build_evidence_context(
        environment="test2", namespace="lowcode-test", application_id="app-1",
        artifact={"artifact":"udc-web", "version":"5.3.517", "sha256":"a"*64},
        trace_id="trace-1", time_window={"start":"2026-09-03T00:00:00Z", "end":"2026-09-03T01:00:00Z"},
        evidence=[{"source":"http-probe", "status":"API_PASS", "claim":"route", "result":200}],
    )
    assert result["schema_version"] == "evidence-context.v1"
    assert result["scope"] == {"environment":"test2", "namespace":"lowcode-test", "application_id":"app-1"}
    assert result["artifact"]["version"] == "5.3.517"
    assert result["trace_id"] == "trace-1"
    assert result["evidence_count"] == 1
    assert result["network"] == "disabled"

def test_evidence_context_rejects_incomplete_identity_as_unverified():
    from components.evidence_context import build_evidence_context
    result = build_evidence_context(environment="test2", application_id="app-1", evidence=[])
    assert result["status"] == "UNVERIFIED"
    assert result["gaps"]
    assert result["evidence_count"] == 0

def test_evidence_context_never_calls_fixture_evidence_live():
    from components.evidence_context import build_evidence_context
    result = build_evidence_context(environment="test2", namespace="n", application_id="a", evidence=[{"source":"fixture", "status":"PASS"}])
    assert result["status"] == "UNVERIFIED"
    assert result["evidence"][0]["status"] != "LIVE_PASS"
