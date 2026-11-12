import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
AUDIT = ROOT / "tests" / "fixtures" / "udc-audit"

def test_cli_udc_report_returns_json():
    result = subprocess.run([sys.executable, "-m", "seeyon_cli", "udc-report", "--audit-dir", str(AUDIT), "--target", "demo"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "FACT"
    assert payload["artifact_version"] == "5.3.517"

def test_cli_udc_analyze_returns_json(tmp_path):
    result = subprocess.run([sys.executable, "-m", "seeyon_cli", "udc-analyze", "--audit-dir", str(tmp_path), "--target", "demo"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["target"] == "demo"
    assert "domains" in payload


def test_cli_integration_report_returns_json(tmp_path):
    snapshot = tmp_path / "integration.json"
    snapshot.write_text('{"http":200}', encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "seeyon_cli", "integration-report", "--snapshot", str(snapshot), "--target", "sync"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "FACT"
    assert payload["snapshot"]["http"] == 200


def test_cli_capabilities_returns_all_read_only_components():
    result = subprocess.run([sys.executable, "-m", "seeyon_cli", "capabilities"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "read-only"
    assert set(payload["components"]) == {"udc", "runtime", "integration"}
    assert all(item["read_only"] is True for item in payload["components"].values())


def test_cli_rejects_write_actions():
    result = subprocess.run([sys.executable, "-m", "seeyon_cli", "udc-execute", "publish", "demo", "--audit-dir", str(AUDIT)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "DENIED"


def test_cli_dry_run_create_entity_emits_plan_without_execution():
    result = subprocess.run(
        [sys.executable, "-m", "seeyon_cli", "dry-run", "--action", "create-entity", "--target", "orders", "--environment", "uat"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["mode"] == "dry-run"
    assert payload["executed"] is False
    assert payload["action"] == "create-entity"
    assert payload["target"] == "orders"
    assert payload["environment"] == "uat"
    assert payload["plan"]
    assert payload["risks"]
    assert payload["confirmations_required"]
    assert payload["rollback"]
    assert payload["readback_verification"]


def test_cli_dry_run_supports_all_write_actions():
    for action in ("create-entity", "add-field", "publish", "deploy"):
        result = subprocess.run(
            [sys.executable, "-m", "seeyon_cli", "dry-run", "--action", action, "--target", "demo", "--environment", "test2"],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["action"] == action
        assert payload["mode"] == "dry-run"
        assert payload["executed"] is False


def test_cli_dry_run_requires_action_target_and_environment():
    result = subprocess.run(
        [sys.executable, "-m", "seeyon_cli", "dry-run", "--action", "publish", "--target", "demo"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "environment" in result.stderr
