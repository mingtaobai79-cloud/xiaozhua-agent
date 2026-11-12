import json
import subprocess
import sys
from pathlib import Path

from components.udc.extension_boundary import build_extension_boundary


def test_without_source_dir_is_unverified_and_does_not_guess(tmp_path):
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"facts": {"custom": "looks plausible"}}), encoding="utf-8")
    result = build_extension_boundary(None, facts)
    assert result["status"] == "UNVERIFIED"
    assert result["items"] == []
    assert "source directory" in " ".join(result["gaps"]).lower()


def test_source_files_are_classified_with_refs_and_gaps(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "CoreController.java").write_text("package com.seeyon.udc.core; class CoreController {}", encoding="utf-8")
    (src / "CustomerForm.java").write_text("package com.customer.ext; class CustomerForm {}", encoding="utf-8")
    (src / "SpiAdapter.java").write_text("import com.seeyon.spi.Extension; class SpiAdapter implements Extension {}", encoding="utf-8")
    (src / "IntegrationClient.py").write_text("import requests\nclass Client: pass", encoding="utf-8")
    (src / "Mystery.txt").write_text("nothing recognizable", encoding="utf-8")
    result = build_extension_boundary(src, {"facts": {"known": True}})
    by_name = {item["path"]: item for item in result["items"]}
    assert by_name["CoreController.java"]["classification"] == "UDC_CORE"
    assert by_name["CustomerForm.java"]["classification"] == "CUSTOMER_EXTENSION"
    assert by_name["SpiAdapter.java"]["classification"] == "SPI_DEPENDENCY"
    assert by_name["IntegrationClient.py"]["classification"] == "INTEGRATION_DEPENDENCY"
    assert by_name["Mystery.txt"]["classification"] == "UNKNOWN"
    assert by_name["CoreController.java"]["evidence_refs"]
    assert result["status"] == "PARTIALLY_VERIFIED"


def test_cli_extension_boundary_emits_json_and_returns_unverified_without_source(tmp_path):
    facts = tmp_path / "facts.json"
    facts.write_text("{}", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "xiaozhua_cli.py", "extension-boundary", "--facts-json", str(facts)],
        cwd=Path(__file__).parents[1], capture_output=True, text=True,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["status"] == "UNVERIFIED"
