import json
import subprocess
import sys
from pathlib import Path

from providers.nacos_evidence_manifest import build_manifest

def test_manifest_groups_application_and_redacts_sensitive_values(tmp_path):
    (tmp_path / "app.yml").write_text("spring:\n  datasource: jdbc:mysql://db/app\n  password: should-not-leak\nserver:\n  url: https://example.test/api\ndependencies: maven:com.acme:demo:1.2.3\n", encoding="utf-8")
    (tmp_path / "public.yml").write_text("storage: s3://bucket/path\n", encoding="utf-8")
    result = build_manifest(tmp_path, application_id="app", tenant="t1", group="g1")
    assert result["application_id"] == "app"
    assert result["tenant"] == "t1" and result["group"] == "g1"
    assert len(result["data_ids"]) == 2
    assert result["data_ids"][0]["sha256"]
    text = json.dumps(result).lower()
    assert "should-not-leak" not in text
    assert "should-not-leak" not in text
    assert any("https://example.test/api" == x for x in result["external_urls"])
    assert any("com.acme" in x for x in result["artifact_maven_hints"])
    assert result["fact_level"] in {"FACT", "PARTIAL", "UNVERIFIED"}

def test_manifest_cli_reads_snapshot_and_reports_gaps(tmp_path):
    (tmp_path / "app.yaml").write_text("spring.application.name: app\n", encoding="utf-8")
    proc = subprocess.run([sys.executable, "-m", "xiaozhua_cli", "nacos-evidence-manifest", "--snapshot-dir", str(tmp_path), "--application-id", "app", "--tenant", "t1", "--group", "g1"], capture_output=True, text=True)
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["network"] == "disabled"
    assert payload["gaps"]
