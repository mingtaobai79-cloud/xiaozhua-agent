import json
import subprocess
import sys
from pathlib import Path

from components.udc.version_audit import audit_versions

def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")

def test_audit_uses_artifact_version_sha256_as_fact_unit(tmp_path):
    jar = tmp_path / "udc-web-5.3.517.jar"
    jar.write_bytes(b"jar-bytes")
    import hashlib
    digest = hashlib.sha256(b"jar-bytes").hexdigest()
    write_json(tmp_path / "udc_version_samples_manifest.json", {"versions": ["5.3.517"], "samples": [{"artifact": "udc-web", "version": "5.3.517", "filename": jar.name, "sha256": digest}]})
    write_json(tmp_path / "udc_version_compatibility_catalog.json", {"artifact_evidence": {"udc-web": [{"artifact": "udc-web", "version": "5.3.517", "sha256": digest, "jar": str(jar)}]}})
    write_json(tmp_path / "udc_member_version_diff.json", {"versions": ["5.3.517"], "artifacts": ["udc-web"]})
    result = audit_versions(tmp_path, versions=["5.3.517"])
    assert result["status"] == "FACT"
    assert result["facts"] == [{"artifact": "udc-web", "version": "5.3.517", "sha256": digest}]

def test_audit_does_not_promote_inventory_only_496_to_fact(tmp_path):
    write_json(tmp_path / "udc_version_samples_manifest.json", {"versions": ["5.3.517"], "samples": []})
    write_json(tmp_path / "udc_version_compatibility_catalog.json", {"source": {"versions": ["5.3.517"]}})
    write_json(tmp_path / "inventory.json", {"versions": ["5.3.496"]})
    result = audit_versions(tmp_path, versions=["5.3.496"])
    assert result["status"] in {"OBSERVATION", "UNVERIFIED"}
    assert not result.get("facts")
    assert result["records"][0]["status"] in {"OBSERVATION", "UNVERIFIED"}

def test_cli_version_audit_emits_json_and_preserves_496_boundary(tmp_path):
    write_json(tmp_path / "udc_version_samples_manifest.json", {"versions": ["5.3.496"], "samples": []})
    result = subprocess.run([sys.executable, "-m", "seeyon_cli", "version-audit", "--audit-dir", str(tmp_path), "--version", "5.3.496"], capture_output=True, text=True)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] in {"OBSERVATION", "UNVERIFIED"}
    assert not payload.get("facts")


def test_mixed_verified_and_missing_artifacts_is_partially_verified(tmp_path):
    jar = tmp_path / "udc-web-5.3.517.jar"
    jar.write_bytes(b"jar")
    import hashlib
    digest = hashlib.sha256(b"jar").hexdigest()
    write_json(tmp_path / "udc_version_samples_manifest.json", {"versions": ["5.3.517"], "samples": [
        {"artifact": "udc-web", "version": "5.3.517", "filename": jar.name, "sha256": digest},
        {"artifact": "udc-common", "version": "5.3.517", "filename": "missing.jar", "sha256": "0" * 64},
    ]})
    result = audit_versions(tmp_path, versions=["5.3.517"])
    assert result["status"] == "OBSERVATION" or result["status"] == "PARTIALLY_VERIFIED"
    assert result["facts"]
