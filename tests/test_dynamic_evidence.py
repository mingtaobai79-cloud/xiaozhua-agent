import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).parents[1]

def test_dynamic_report_projects_sources_and_matrices():
 from components.dynamic_evidence import build_dynamic_evidence_report
 r=build_dynamic_evidence_report({"http":{"classification":"PASS","source":"live"},"k8s":{"classification":"PASS","source":"fixture"},"nacos":{"classification":"PASS","source":"fixture"},"mysql":{"classification":"PASS","source":"live"},"redis":{"classification":"PASS","source":"live"}})
 assert set(r["sources"])=={"http","k8s","nacos","mysql","redis"}
 assert len(r["evidence_ledger"]["entries"])==5
 assert len(r["path_matrix"]["entries"])==10
 assert r["source_statuses"]["http"]=="API_PASS" and r["source_statuses"]["mysql"]=="LIVE_PASS"

def test_fixture_can_never_be_live_pass():
 from components.dynamic_evidence import classify_dynamic_result
 assert classify_dynamic_result({"classification":"PASS","source":"fixture"},source="redis")=="API_PASS"
 assert classify_dynamic_result({"classification":"LIVE_PASS","source":"fixture"},source="redis")=="API_PASS"

def test_blocked_and_unverified_are_preserved():
 from components.dynamic_evidence import build_dynamic_evidence_report
 r=build_dynamic_evidence_report({"http":{"classification":"BLOCKED"},"k8s":{"classification":"UNVERIFIED"}})
 assert r["source_statuses"]["http"]=="BLOCKED" and r["source_statuses"]["k8s"]=="UNVERIFIED"
 assert r["status"]=="UNVERIFIED"

def test_dynamic_cli_fixture_boundary(tmp_path):
 paths=[]
 for n in ("http","k8s","nacos","mysql","redis"):
  p=tmp_path/(n+".json"); p.write_text(json.dumps({"classification":"PASS"})); paths += ["--"+n,str(p)]
 x=subprocess.run([sys.executable,"-m","xiaozhua_cli","dynamic-evidence"]+paths,cwd=ROOT,capture_output=True,text=True)
 assert x.returncode==0
 r=json.loads(x.stdout); assert r["network"]=="disabled" and all(v=="API_PASS" for v in r["source_statuses"].values())


def test_fixture_api_pass_does_not_promote_path_matrix_to_fact():
    from components.dynamic_evidence import build_dynamic_evidence_report
    payload = {name: {"classification": "PASS", "source": "fixture"} for name in ("http", "k8s", "nacos", "mysql", "redis")}
    result = build_dynamic_evidence_report(payload)
    assert result["status"] == "API_PASS"
    assert result["path_matrix"]["status"] == "UNVERIFIED"
    assert all(entry["status"] == "UNVERIFIED" for entry in result["path_matrix"]["entries"])


def test_dynamic_report_projects_bound_evidence_context_fields():
    from components.dynamic_evidence import build_dynamic_evidence_report
    context = {
        "environment": "test2",
        "namespace": "lowcode-test",
        "application_id": "app-1",
        "trace_id": "trace-42",
        "time_window": {"start": "2026-09-03T00:00:00Z", "end": "2026-09-03T01:00:00Z"},
    }
    result = build_dynamic_evidence_report(
        {"http": {"classification": "PASS", "source": "live"}},
        evidence_context=context,
    )
    assert result["context"] == {
        "environment": "test2", "namespace": "lowcode-test", "application_id": "app-1"
    }
    assert result["trace_id"] == "trace-42"
    assert result["time_window"] == context["time_window"]
    assert result["status"] == "UNVERIFIED"


def test_dynamic_report_without_identity_stays_unverified():
    from components.dynamic_evidence import build_dynamic_evidence_report
    result = build_dynamic_evidence_report(
        {name: {"classification": "PASS", "source": "live"} for name in ("http", "k8s", "nacos", "mysql", "redis")},
        evidence_context={"environment": "test2", "trace_id": "trace-1"},
    )
    assert result["status"] == "UNVERIFIED"
    assert result["context"]["namespace"] is None
    assert result["trace_id"] == "trace-1"
    assert result["time_window"] is None
    assert "namespace is required" in result["context_gaps"]
