import json
import subprocess
import sys
from pathlib import Path

from core.providers import JSONProbeProvider, ReadOnlyProbeProvider

ROOT = Path(__file__).parents[1]


def test_read_only_probe_provider_defines_runtime_and_http_reads():
    assert issubclass(JSONProbeProvider, ReadOnlyProbeProvider)
    assert {"read_runtime", "read_http"} <= set(ReadOnlyProbeProvider.__abstractmethods__)


def test_json_probe_provider_reads_runtime_and_http_snapshots(tmp_path):
    runtime = tmp_path / "runtime.json"
    http = tmp_path / "http.json"
    runtime.write_text('{"resources":{"pod":"observed"}}', encoding="utf-8")
    http.write_text('{"probes":[{"label":"health","classification":"PASS"}]}', encoding="utf-8")

    provider = JSONProbeProvider(runtime, http)

    assert provider.read_runtime() == {"resources": {"pod": "observed"}}
    assert provider.read_http() == {"probes": [{"label": "health", "classification": "PASS"}]}


def test_probe_summary_can_consume_provider_without_cli_file_logic(tmp_path):
    runtime = tmp_path / "runtime.json"
    http = tmp_path / "http.json"
    runtime.write_text('{"resources":{"pod":"observed"}}', encoding="utf-8")
    http.write_text('{"probes":[{"label":"health","classification":"PASS"}]}', encoding="utf-8")

    from components.probe_summary import build_probe_summary

    result = build_probe_summary(provider=JSONProbeProvider(runtime, http))

    assert result["status"] == "FACT"
    assert any(item["label"] == "runtime.resources.pod" for item in result["facts"])
    assert any(item["label"] == "health" for item in result["facts"])


def test_probe_summary_cli_remains_compatible_with_explicit_paths(tmp_path):
    runtime = tmp_path / "runtime.json"
    http = tmp_path / "http.json"
    runtime.write_text('{}', encoding="utf-8")
    http.write_text('{"probes":[]}', encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "xiaozhua_cli", "probe-summary", "--runtime", str(runtime), "--http", str(http)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "UNVERIFIED"


def test_json_probe_provider_returns_structured_errors_without_raising(tmp_path):
    from core.providers import ProviderResult
    provider = JSONProbeProvider(tmp_path / "missing-runtime.json", tmp_path / "missing-http.json")
    result = provider.read_runtime()
    assert isinstance(result, ProviderResult)
    assert result.ok is False
    assert result.error.kind == "unavailable"


def test_json_probe_provider_classifies_parse_errors(tmp_path):
    from core.providers import ProviderResult
    runtime = tmp_path / "runtime.json"
    http = tmp_path / "http.json"
    runtime.write_text("{not-json", encoding="utf-8")
    http.write_text("{}", encoding="utf-8")
    result = JSONProbeProvider(runtime, http).read_runtime()
    assert isinstance(result, ProviderResult)
    assert result.error.kind == "parse"
