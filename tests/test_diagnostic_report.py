import json
import subprocess
import sys
from pathlib import Path

from components.diagnostic_report import build_diagnostic_report


def test_aggregates_cross_component_conclusions_without_promoting_http_or_fixture():
    result = build_diagnostic_report(
        evidence_context={"status": "FACT", "scope": {"environment": "uat", "application_id": "demo"}, "evidence": [{"status": "FACT", "source": "source"}]},
        dynamic_evidence={"status": "LIVE_PASS", "source_statuses": {"http": "LIVE_PASS", "nacos": "LIVE_PASS"}, "context": {"environment": "uat"}},
        path_matrix={"status": "PARTIALLY_VERIFIED", "entries": [{"kind": "Generate", "status": "UNVERIFIED", "gaps": ["generation evidence missing"]}]},
        impact_graph={"status": "PARTIALLY_VERIFIED", "nodes": [{"id": "generated_artifact", "status": "UNVERIFIED", "gaps": ["generation evidence missing"]}]},
        version_audit={"status": "FACT", "versions": ["5.3.517"], "facts": [{"artifact": "udc-web", "version": "5.3.517", "sha256": "a" * 64}]},
    )
    assert result["status"] == "UNVERIFIED"
    assert result["network"] == "disabled"
    assert "generation evidence missing" in result["unverified_gaps"]
    assert result["blockers"]
    assert result["verified_facts"]
    assert result["recommended_next_steps"]
    assert result["dynamic_evidence"]["source_statuses"]["http"] == "API_PASS"
    assert "LIVE_PASS" not in json.dumps(result["dynamic_evidence"])


def test_diagnostic_cli_reads_only_local_reports(tmp_path):
    def dump(name, value):
        p = tmp_path / name
        p.write_text(json.dumps(value), encoding="utf-8")
        return str(p)
    args = [sys.executable, "-m", "xiaozhua_cli", "diagnostic-report",
            "--evidence-context", dump("context.json", {"status": "FACT", "scope": {}}),
            "--dynamic-evidence", dump("dynamic.json", {"status": "UNVERIFIED"}),
            "--path-matrix", dump("matrix.json", {"status": "UNVERIFIED", "entries": []}),
            "--impact-graph", dump("graph.json", {"status": "UNVERIFIED", "nodes": []}),
            "--version-audit", dump("versions.json", {"status": "UNVERIFIED", "records": []})]
    proc = subprocess.run(args, cwd=Path(__file__).parents[1], capture_output=True, text=True)
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["network"] == "disabled"
    assert payload["status"] == "UNVERIFIED"
    assert payload["blockers"]
