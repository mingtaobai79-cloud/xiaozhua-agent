import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def _dump(tmp_path, name, payload):
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_audit_bundle_subprocess_unifies_all_inputs_and_preserves_gaps(tmp_path):
    paths = {
        "version": _dump(tmp_path, "version.json", {"status": "FACT", "versions": ["5.3.517"], "facts": [{"artifact": "udc-web", "version": "5.3.517", "sha256": "a" * 64}]}),
        "runtime": _dump(tmp_path, "runtime.json", {"probes": [{"label": "runtime", "classification": "PASS"}]}),
        "http": _dump(tmp_path, "http.json", {"probes": [{"label": "health", "classification": "PASS"}]}),
        "matrix": _dump(tmp_path, "matrix.json", {"status": "UNVERIFIED", "entries": [{"kind": "Runtime Metadata", "status": "UNVERIFIED", "gaps": ["trace missing"]}]}),
        "graph": _dump(tmp_path, "graph.json", {"status": "UNVERIFIED", "nodes": [{"id": "runtime_metadata", "status": "UNVERIFIED", "gaps": ["trace missing"]}]}),
        "context": _dump(tmp_path, "context.json", {"status": "UNVERIFIED", "scope": {"environment": "uat"}, "gaps": ["trace_id is unavailable"]}),
    }
    proc = subprocess.run([sys.executable, "-m", "seeyon_cli", "audit-bundle", "--version-audit", paths["version"], "--runtime", paths["runtime"], "--http", paths["http"], "--path-matrix", paths["matrix"], "--impact-graph", paths["graph"], "--evidence-context", paths["context"]], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["schema_version"] == "audit-bundle.v1"
    assert payload["network"] == "disabled"
    assert payload["status"] == "UNVERIFIED"
    assert set(payload["inputs"]) == {"version_audit", "runtime", "http", "path_matrix", "impact_graph", "evidence_context"}
    assert "trace_id is unavailable" in payload["gaps"]
    assert payload["status_summary"]["live_pass_count"] == 0


def test_audit_bundle_missing_input_fails_closed_in_subprocess(tmp_path):
    missing = str(tmp_path / "missing.json")
    proc = subprocess.run([sys.executable, "-m", "seeyon_cli", "audit-bundle", "--version-audit", missing, "--runtime", missing, "--http", missing, "--path-matrix", missing, "--impact-graph", missing, "--evidence-context", missing], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["status"] == "UNVERIFIED"
    assert len(payload["missing_inputs"]) == 6
    assert payload["status_summary"]["live_pass_count"] == 0
