import json
import subprocess
import sys
from pathlib import Path

from components.profiles.builder import ProfileBuilder

ROOT = Path(__file__).parents[1]
NACOS = ROOT / "docs" / "audit" / "evidence" / "nacos-test2-manifest.json"
UDC = ROOT / "tests" / "fixtures" / "udc-audit" / "manifest.json"


def test_profile_builder_creates_separate_udc_and_customer_profiles():
    result = ProfileBuilder(nacos_manifest=NACOS, udc_manifest=UDC).build()
    profiles = {item["kind"]: item for item in result["profiles"]}

    assert result["status"] == "FACT"
    assert set(profiles) == {"udc_platform", "customer_udc_application"}
    assert profiles["udc_platform"]["id"] == "udc-platform"
    assert profiles["customer_udc_application"]["application_id"] == "app9000000000000000001"
    assert "udc" in profiles["udc_platform"]["data_ids"]
    assert "app9000000000000000001" in profiles["customer_udc_application"]["data_ids"]
    assert profiles["udc_platform"]["evidence_refs"]
    assert profiles["customer_udc_application"]["evidence_refs"]


def test_profile_builder_does_not_create_standard_or_extension_without_evidence():
    result = ProfileBuilder(nacos_manifest=NACOS, udc_manifest=UDC).build()
    kinds = {item["kind"] for item in result["profiles"]}
    assert "standard_product_application" not in kinds
    assert "extension_service" not in kinds
    assert "standard_product_application" in result["unverified"]
    assert "extension_service" in result["unverified"]


def test_profile_builder_missing_inputs_is_unverified(tmp_path):
    result = ProfileBuilder(nacos_manifest=tmp_path / "nacos.json", udc_manifest=tmp_path / "udc.json").build()
    assert result["status"] == "UNVERIFIED"
    assert result["profiles"] == []
    assert result["missing_inputs"]


def test_profile_build_cli_returns_single_line_json():
    result = subprocess.run([
        sys.executable, "-m", "seeyon_cli", "profile-build",
        "--nacos-manifest", str(NACOS), "--udc-manifest", str(UDC),
    ], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().count("\n") == 0
    payload = json.loads(result.stdout)
    assert payload["network"] == "disabled"
    assert payload["status"] == "FACT"
    assert len(payload["profiles"]) == 2


def test_profile_build_cli_missing_input_returns_two(tmp_path):
    result = subprocess.run([
        sys.executable, "-m", "seeyon_cli", "profile-build",
        "--nacos-manifest", str(tmp_path / "missing.json"),
        "--udc-manifest", str(UDC),
    ], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "UNVERIFIED"
    assert "Traceback" not in result.stderr
