import json
import subprocess
import sys
from pathlib import Path

from core.providers import FileSnapshotProvider
from components.runtime import RuntimeComponent
from components.integration import IntegrationComponent

ROOT = Path(__file__).parents[1]

def test_file_snapshot_provider_reads_json(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text('{"environment":"test2"}', encoding="utf-8")
    result = FileSnapshotProvider(path).read()
    assert result == {"environment": "test2"}

def test_runtime_component_uses_provider_port(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text('{"pod":"udc"}', encoding="utf-8")
    result = RuntimeComponent(provider=FileSnapshotProvider(path)).inspect("udc")
    assert result["status"] == "FACT"
    assert result["snapshot"]["pod"] == "udc"

def test_integration_component_uses_provider_port(tmp_path):
    path = tmp_path / "integration.json"
    path.write_text('{"http":200}', encoding="utf-8")
    result = IntegrationComponent(provider=FileSnapshotProvider(path)).inspect("sync")
    assert result["status"] == "FACT"
    assert result["snapshot"]["http"] == 200

def test_cli_runtime_report_returns_json(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text('{"environment":"test2"}', encoding="utf-8")
    result = subprocess.run([sys.executable, "-m", "xiaozhua_cli", "runtime-report", "--snapshot", str(path), "--target", "udc"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "FACT"
