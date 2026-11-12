import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_audit_summary_reads_three_reports_and_udc_json(tmp_path):
    audit = tmp_path / "audit"
    audit.mkdir()
    (audit / "code-reality-audit.md").write_text(
        "# Code\n\n**The repository is a tested offline skeleton.**\n\n## Evidence status\n\n**FOCUSED VERIFIED**\n",
        encoding="utf-8",
    )
    (audit / "udc-evidence-consistency-audit.md").write_text(
        "# Evidence\n\n**PARTIALLY VERIFIED / WITH UNVERIFIED GAPS**\n\n## 5. 结论\n\nPASS / BLOCKED / UNVERIFIED\n",
        encoding="utf-8",
    )
    (audit / "next-direction-input.md").write_text(
        "# Next\n\n## 6. 建议的下一轮取证顺序\n\n1. **先补 D1**\n2. **再补 D3/D4**\n",
        encoding="utf-8",
    )
    udc = tmp_path / "udc.json"
    udc.write_text(json.dumps({"status": "FACT", "artifact_version": "5.3.517", "counts": {"endpoints": 2}}), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "xiaozhua_cli", "audit-summary", "--audit-dir", str(audit), "--udc-json", str(udc)],
        cwd=ROOT, capture_output=True, text=True,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert {"status", "schema_version", "scope", "limitations", "code_reality", "evidence_consistency", "next_direction", "udc"} <= set(payload)
    assert payload["schema_version"] == "1.0"
    assert payload["scope"]["read_only"] is True
    assert payload["limitations"]
    assert payload["code_reality"]["status"] == "FOCUSED VERIFIED"
    assert payload["evidence_consistency"]["status"] == "PARTIALLY VERIFIED"
    assert payload["next_direction"]["items"] == ["先补 D1", "再补 D3/D4"]
    assert payload["udc"]["artifact_version"] == "5.3.517"
    assert payload["udc"]["status"] == "FACT"


def test_audit_summary_reports_missing_inputs_without_traceback(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "xiaozhua_cli", "audit-summary", "--audit-dir", str(tmp_path), "--udc-json", str(tmp_path / "missing.json")],
        cwd=ROOT, capture_output=True, text=True,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "UNVERIFIED"
    assert payload["schema_version"] == "1.0"
    assert payload["scope"]["read_only"] is True
    assert payload["limitations"]
    assert payload["missing"]
    assert "Traceback" not in result.stderr


def test_audit_summary_schema_validation_rejects_missing_required_field():
    from components.report_schema import validate_report_schema

    result = validate_report_schema({"status": "FACT", "scope": {}, "limitations": []})
    assert result["valid"] is False
    assert result["status"] == "UNVERIFIED"
    assert "schema_version" in result["missing"]
