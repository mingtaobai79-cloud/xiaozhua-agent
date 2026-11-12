from pathlib import Path


DOC = Path(__file__).parents[1] / "docs" / "audit" / "module-boundary-contract.md"


def test_module_boundary_keeps_udc_standard_spi_integration_runtime_separate():
    text = DOC.read_text(encoding="utf-8")
    assert "UDC、Standard Product Application、SPI、Integration、Runtime 是并列" in text
    assert "客户业务明细（实体、页面、微流程、业务表、ext 文件）默认 `QUERY_ON_DEMAND_NOT_DURABLE`" in text
    assert "禁止表达" in text
    assert "UDC contains SPI" in text


def test_module_boundary_allows_links_without_changing_ownership():
    text = DOC.read_text(encoding="utf-8")
    for marker in ("--generates-->", "--calls-->", "--uses-->", "--hosts/loads/observes-->"):
        assert marker in text
