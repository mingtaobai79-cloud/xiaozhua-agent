import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_ledger_normalizes_sources_and_detects_conflict_without_overwrite():
    from components.evidence_ledger import EvidenceLedger
    ledger = EvidenceLedger()
    ledger.add(source="udc-static", status="FACT", claim="route /service/demo", result="present")
    ledger.add(source="runtime-probe", status="FACT", claim="route /service/demo", result="missing")
    items = ledger.to_dict()["entries"]
    assert len(items) == 2
    assert all({"source", "status", "claim"} <= set(item) for item in items)
    assert all(item["status"] == "CONFLICT" for item in items)
    assert {item["result"] for item in items} == {"present", "missing"}

def test_ledger_converts_audit_and_probe_records():
    from components.evidence_ledger import build_evidence_ledger
    result = build_evidence_ledger(
        audit_dir=None,
        udc_json={"status": "FACT", "facts": {"route": "present"}},
        runtime={"resources": {"pod": "ready"}},
        http={"probes": [{"label": "GET /x", "classification": "PASS", "http_status": 200}]},
    )
    assert result["entries"]
    assert {item["source"] for item in result["entries"]} == {"udc-static", "runtime-probe", "http-probe"}
    assert all(item["claim"] for item in result["entries"])

def test_evidence_ledger_cli_is_offline_and_json(tmp_path):
    udc = tmp_path / "udc.json"
    runtime = tmp_path / "runtime.json"
    http = tmp_path / "http.json"
    udc.write_text(json.dumps({"status":"FACT", "facts":{"route":"present"}}), encoding="utf-8")
    runtime.write_text(json.dumps({"resources":{"pod":"ready"}}), encoding="utf-8")
    http.write_text(json.dumps({"probes":[{"label":"route","classification":"PASS","http_status":200}]}), encoding="utf-8")
    r = subprocess.run([sys.executable, "-m", "xiaozhua_cli", "evidence-ledger", "--udc-json", str(udc), "--runtime", str(runtime), "--http", str(http)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert payload["network"] == "disabled"
    assert payload["entries"]
    assert {x["source"] for x in payload["entries"]} == {"udc-static", "runtime-probe", "http-probe"}


def test_ledger_status_is_not_fact_when_entries_include_failures():
    from components.evidence_ledger import build_evidence_ledger
    result = build_evidence_ledger(http={"probes": [{"label": "missing", "classification": "FAIL", "http_status": 404}]})
    assert result["status"] == "PARTIALLY_VERIFIED"
