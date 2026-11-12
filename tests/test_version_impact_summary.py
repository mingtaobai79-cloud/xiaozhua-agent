import json
import subprocess
import sys
from pathlib import Path

from components.version_impact_summary import build_version_impact_summary


def test_summary_keeps_static_version_fact_out_of_behavior_compatibility():
    version_audit = {"status": "FACT", "versions": ["5.3.517"], "facts": [{"artifact": "udc-web", "version": "5.3.517", "sha256": "a" * 64}], "records": []}
    matrix = {"entries": [{"kind": "Generate", "status": "UNVERIFIED", "gaps": ["generation evidence missing"]}]}
    graph = {"nodes": [{"id": "generated_artifact", "type": "generated_artifact", "status": "UNVERIFIED", "gaps": ["generation evidence missing"]}], "edges": []}
    result = build_version_impact_summary(version_audit, matrix, graph)
    assert result["version_boundaries"][0]["evidence_status"] == "FACT"
    assert result["version_boundaries"][0]["behavior_compatibility"] == "UNVERIFIED"
    assert "generated_artifact" in result["affected_nodes"]
    assert "generation evidence missing" in result["unverified_gaps"]


def test_summary_reports_missing_version_evidence_and_deduplicates_gaps():
    result = build_version_impact_summary(
        {"status": "OBSERVATION", "versions": ["5.3.496"], "facts": [], "records": [{"version": "5.3.496", "status": "OBSERVATION"}]},
        {"entries": [{"kind": "Runtime Metadata", "status": "UNVERIFIED", "gaps": ["runtime metadata evidence missing"]}]},
        {"nodes": [{"id": "runtime_metadata", "type": "runtime_metadata", "status": "UNVERIFIED", "gaps": ["runtime metadata evidence missing"]}], "edges": []},
    )
    assert result["version_boundaries"][0]["version"] == "5.3.496"
    assert result["version_boundaries"][0]["evidence_status"] == "OBSERVATION"
    assert result["version_boundaries"][0]["behavior_compatibility"] == "UNVERIFIED"
    assert result["unverified_gaps"].count("runtime metadata evidence missing") == 1
    assert result["status"] == "UNVERIFIED"


def test_version_impact_summary_cli_accepts_audit_matrix_and_graph(tmp_path):
    def dump(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return str(path)
    audit = dump("audit.json", {"status": "FACT", "versions": ["5.3.517"], "facts": [{"artifact": "udc-web", "version": "5.3.517", "sha256": "b" * 64}]})
    matrix = dump("matrix.json", {"entries": [{"kind": "Version", "status": "FACT", "evidence_refs": ["audit"]}]})
    graph = dump("graph.json", {"nodes": [{"id": "version", "type": "version", "status": "FACT", "evidence_refs": ["audit"], "gaps": []}], "edges": []})
    proc = subprocess.run([sys.executable, "-m", "xiaozhua_cli", "version-impact-summary", "--version-audit", audit, "--path-matrix", matrix, "--impact-graph", graph], capture_output=True, text=True, cwd=Path(__file__).parents[1])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["network"] == "disabled"
    assert payload["version_boundaries"][0]["behavior_compatibility"] == "UNVERIFIED"
