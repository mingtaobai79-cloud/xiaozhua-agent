import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]

def write_probe(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")

def test_probe_summary_separates_fact_unverified_and_blocked(tmp_path):
    runtime = tmp_path / "runtime.json"
    http = tmp_path / "http.json"
    write_probe(runtime, {"status": "PARTIALLY_VERIFIED", "live_probe": {"status": "BLOCKED", "reason": "kubectl unavailable"}, "resources": {"pod": "observed"}})
    write_probe(http, {"status": "FACTS_COLLECTED_WITH_BLOCKED_OR_UNVERIFIED_ROUTES", "probes": [{"label": "ok", "classification": "PASS", "http_status": 200}, {"label": "post", "classification": "UNVERIFIED"}, {"label": "denied", "classification": "BLOCKED"}]})
    from components.probe_summary import build_probe_summary
    result = build_probe_summary(runtime, http)
    assert result["status"] == "PARTIALLY_VERIFIED"
    assert any(item["label"] == "ok" for item in result["facts"])
    assert any(item["label"] == "post" for item in result["unverified"])
    assert any(item["label"] == "denied" for item in result["blocked"])
    assert not any(item.get("label") == "denied" for item in result["facts"])

def test_probe_summary_missing_input_is_unverified(tmp_path):
    from components.probe_summary import build_probe_summary
    result = build_probe_summary(tmp_path / "missing-runtime.json", tmp_path / "missing-http.json")
    assert result["status"] == "UNVERIFIED"
    assert result["schema_version"] == "1.0"
    assert result["scope"]["read_only"] is True
    assert result["limitations"]
    assert len(result["unverified"]) == 2
    assert result["blocked"] == []

def test_probe_summary_downgrades_pass_with_unverified_note():
    from components.probe_summary import build_probe_summary
    runtime = Path("runtime.json")
    http = Path("http.json")
    write_probe(runtime, {})
    write_probe(http, {"probes": [{"label": "manifest", "classification": "PASS", "note": "JSON validity unverified"}]})
    result = build_probe_summary(runtime, http)
    assert result["facts"] == []
    assert result["unverified"][0]["label"] == "manifest"

def test_probe_summary_cli_reads_default_temp_probe_files():
    result = subprocess.run([sys.executable, "-m", "seeyon_cli", "probe-summary"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert {"status", "schema_version", "scope", "limitations", "facts", "unverified", "blocked", "sources"} <= set(payload)
    assert payload["schema_version"] == "1.0"
    assert payload["scope"]["read_only"] is True
    assert payload["limitations"]
    assert payload["blocked"]
    assert not any(item in payload["facts"] for item in payload["blocked"])


def test_probe_summary_schema_validation_rejects_missing_required_field():
    from components.report_schema import validate_report_schema

    result = validate_report_schema({"status": "FACT", "schema_version": "1.0", "scope": {}})
    assert result["valid"] is False
    assert result["status"] == "UNVERIFIED"
    assert "limitations" in result["missing"]
