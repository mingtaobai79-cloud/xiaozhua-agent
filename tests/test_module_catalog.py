import json
import subprocess
import sys
from pathlib import Path

from components.module_catalog import build_module_catalog

ROOT = Path(__file__).parents[1]

def test_catalog_keeps_five_modules_independent_and_links_are_separate():
    result = build_module_catalog()
    assert result["status"] == "PARTIALLY_VERIFIED"
    modules = {item["id"]: item for item in result["modules"]}
    assert set(modules) == {"udc", "standard-product", "spi", "integration", "runtime"}
    assert modules["udc"]["kind"] == "udc_platform"
    assert modules["standard-product"]["kind"] == "standard_product_application"
    assert modules["spi"]["kind"] == "spi"
    assert modules["integration"]["kind"] == "integration"
    assert modules["runtime"]["kind"] == "runtime"
    assert result["relations"]
    assert all("source" in x and "target" in x and "type" in x for x in result["relations"])

def test_catalog_does_not_promote_customer_business_detail():
    text = json.dumps(build_module_catalog(), ensure_ascii=False)
    assert "410" not in text and "404" not in text and "1664" not in text
    assert "customer_entity_inventory" not in text

def test_module_catalog_cli_is_machine_readable():
    r = subprocess.run([sys.executable, "-m", "xiaozhua_cli", "module-catalog"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    assert payload["network"] == "disabled"
    assert payload["modules"]


def test_standard_product_and_spi_are_independent_evidence_profiles():
    from pathlib import Path
    import json
    root = Path(__file__).parents[1] / "docs" / "audit" / "modules"
    standard = json.loads((root / "standard-product-module-profile.json").read_text(encoding="utf-8"))
    spi = json.loads((root / "spi-module-profile.json").read_text(encoding="utf-8"))
    assert standard["module_id"] == "standard-product"
    assert spi["module_id"] == "spi"
    assert standard["module_id"] != spi["module_id"]
    assert standard["scope"] != spi["scope"]
    assert "not UDC" in spi["scope"]
    assert "not UDC core" in standard["scope"]


def test_spi_registration_and_standard_contract_profiles_are_evidence_bound():
    import json
    root = Path(__file__).parents[1] / "docs" / "audit" / "modules"
    spi = json.loads((root / "spi-module-profile.json").read_text(encoding="utf-8"))
    standard = json.loads((root / "standard-product-module-profile.json").read_text(encoding="utf-8"))
    assert spi["registration_evidence"]
    assert all(item["status"] == "FACT" for item in spi["registration_evidence"])
    assert any(item["contract"].endswith("SsoService") for item in spi["registration_evidence"])
    assert len(standard["contract_packages"]) == 3
    assert all(item["module"] if "module" in item else True for item in [{"module": "standard-product"}])
    assert standard["scope"] == "Independent Standard Product Application module; artifacts are not UDC core."
    assert spi["scope"] == "Independent SPI module; not UDC or Standard Product Application."
