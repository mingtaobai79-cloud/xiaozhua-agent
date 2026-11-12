"""Acceptance boundaries for the offline, read-only CLI surface."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


def _run(*args):
    return subprocess.run([sys.executable, "-m", "xiaozhua_cli", *args], cwd=ROOT, capture_output=True, text=True)


def _all_values(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from _all_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_values(item)


@pytest.mark.offline
@pytest.mark.acceptance
@pytest.mark.parametrize("args", [
    ("capabilities",),
    ("udc-report", "--audit-dir", str(Path.home()), "--target", "demo"),
    ("udc-analyze", "--audit-dir", str(Path.home()), "--target", "demo"),
    ("runtime-report", "--snapshot", str(ROOT / "runtime.json"), "--target", "demo"),
    ("integration-report", "--snapshot", str(ROOT / "integration.json"), "--target", "demo"),
    ("audit-summary", "--audit-dir", str(Path.home()), "--udc-json", str(ROOT / "matrix.actual.json")),
    ("probe-summary",),
    ("udc-path-matrix", "--udc-json", str(ROOT / "matrix.actual.json"), "--runtime", str(ROOT / "runtime.json"), "--http", str(ROOT / "http.json")),
    ("impact-graph", "--path-matrix", str(ROOT / "matrix.actual.json")),
    ("extension-boundary", "--facts-json", str(ROOT / "matrix.actual.json")),
])
def test_every_cli_command_declares_network_disabled_and_never_live_pass(args):
    result = _run(*args)
    assert result.returncode in (0, 2), result.stderr
    payload = json.loads(result.stdout)
    pairs = list(_all_values(payload))
    network_values = [item for key, item in pairs if key == "network"]
    assert network_values, f"CLI output has no network boundary: {payload}"
    assert all(item == "disabled" for item in network_values)
    serialized = json.dumps(payload, ensure_ascii=False).upper()
    assert "LIVE PASS" not in serialized
    assert not any(key.lower() == "status" and str(item).upper() == "LIVE" for key, item in pairs)


@pytest.mark.offline
@pytest.mark.acceptance
def test_evidence_ledger_boundary_is_offline_and_not_live_pass(tmp_path):
    runtime = tmp_path / "runtime.json"
    runtime.write_text(json.dumps({"resources": {}, "conclusion": {}}), encoding="utf-8")
    # http.json 是运行产物（.gitignore 内），不能让测试依赖仓根那份 —— 自建到 tmp_path
    http = tmp_path / "http.json"
    http.write_text(json.dumps({"probes": [{"label": "manifest", "classification": "PASS",
                                            "note": "JSON validity unverified"}]}),
                    encoding="utf-8")
    result = _run("evidence-ledger", "--udc-json", str(ROOT / "matrix.actual.json"), "--runtime", str(runtime), "--http", str(http))
    assert result.returncode in (0, 2), result.stderr
    payload = json.loads(result.stdout)
    assert payload["network"] == "disabled"
    assert "LIVE PASS" not in json.dumps(payload).upper()


@pytest.mark.offline
@pytest.mark.blocked
@pytest.mark.acceptance
def test_write_action_is_denied_and_dry_run_has_no_write_operations():
    result = _run("udc-execute", "publish", "demo", "--audit-dir", str(Path.home()))
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "DENIED"
    assert payload["evidence"][0]["level"] == "DENIED"

    from types import SimpleNamespace
    from components.udc.planner import UdcPlanner
    dry_run = UdcPlanner().plan(SimpleNamespace(name="demo", entities=[], pages=[], microflows=[]))
    assert dry_run["mode"] == "dry-run"
    assert dry_run["write_operations"] == []


@pytest.mark.offline
@pytest.mark.acceptance
def test_policy_gate_cli_does_not_allow_mutating_http_method(tmp_path):
    from core.policy import PolicyGate
    decision = PolicyGate(network_enabled=True).evaluate("http_request", provider="http", method="POST")
    assert decision["status"] == "DENIED"
    assert decision["allowed"] is False
