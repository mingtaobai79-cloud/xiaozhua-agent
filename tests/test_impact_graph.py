import json
import subprocess
import sys
from pathlib import Path

from components.impact_graph import build_impact_graph


def test_maps_path_entries_to_required_nodes_and_dependency_edges():
    matrix = {
        "schema_version": "phase-c-path-matrix.v1",
        "entries": [
            {"kind": "Version", "status": "FACT", "evidence_refs": ["udc.version"], "gaps": [], "dependencies": []},
            {"kind": "Generate", "status": "UNVERIFIED", "evidence_refs": [], "gaps": ["generation evidence missing"], "dependencies": ["Version"]},
            {"kind": "Runtime Metadata", "status": "FACT", "evidence_refs": ["runtime.resources"], "gaps": [], "dependencies": ["Deploy"]},
        ],
    }
    graph = build_impact_graph(matrix)
    assert {n["type"] for n in graph["nodes"]} >= {
        "metadata", "version", "generated_artifact", "runtime_metadata",
        "physical_table", "redis", "events", "routes_assets",
    }
    assert any(e["source"] == "version" and e["target"] == "generated_artifact" for e in graph["edges"])
    generated = next(n for n in graph["nodes"] if n["type"] == "generated_artifact")
    assert generated["status"] == "UNVERIFIED"
    assert generated["evidence_refs"] == []


def test_inference_is_never_fact_and_missing_nodes_are_unverified():
    graph = build_impact_graph({"entries": [{"kind": "Application", "status": "FACT", "evidence_refs": ["static.app"], "dependencies": []}]})
    for node in graph["nodes"]:
        if node["type"] != "metadata":
            assert node["status"] == "UNVERIFIED"
            assert not node["evidence_refs"]
    assert graph["status"] == "PARTIALLY_VERIFIED"


def test_impact_graph_cli_reads_local_path_matrix_only(tmp_path):
    matrix = tmp_path / "matrix.json"
    matrix.write_text(json.dumps({"entries": []}), encoding="utf-8")
    proc = subprocess.run([sys.executable, "-m", "xiaozhua_cli", "impact-graph", "--path-matrix", str(matrix)], cwd=Path(__file__).parents[1], capture_output=True, text=True)
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["network"] == "disabled"
    assert payload["nodes"]
    assert payload["edges"]


def test_impact_graph_carries_probe_statuses_and_does_not_promote_http_pass():
    graph = build_impact_graph({"entries": [{"kind": "Runtime Metadata", "status": "FACT", "probe_statuses": ["HTTP_PASS"], "evidence_refs": ["http.probes"], "gaps": []}]})
    node = next(n for n in graph["nodes"] if n["type"] == "runtime_metadata")
    assert node["probe_statuses"] == ["HTTP_PASS"]
    assert node["status"] == "HTTP_PASS"
    assert "HTTP PASS does not imply runtime verification" in graph["limitations"]
