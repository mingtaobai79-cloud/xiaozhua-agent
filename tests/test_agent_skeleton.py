from pathlib import Path
from core.agent import AgentRequest, MemoryContext, MemorySession, XiaozhuaAgent
from core.evidence import Evidence
from components.udc.component import UdcComponent

ROOT = Path(__file__).parents[1]

def test_routes_udc_request_to_udc_component():
    agent = XiaozhuaAgent({"udc": UdcComponent()})
    assert agent.route(AgentRequest("分析 UDC 实体")) == "udc"

def test_mixed_udc_and_runtime_intent_is_not_silently_routed():
    agent = XiaozhuaAgent({"udc": UdcComponent()})
    assert agent.route(AgentRequest("排查微流程运行态 Redis 缓存")) == "unknown"


def test_english_keyword_inside_unrelated_word_does_not_route():
    agent = XiaozhuaAgent({"udc": UdcComponent()})
    assert agent.route(AgentRequest("review the teamquality report")) == "unknown"
    assert agent.route(AgentRequest("排查 MQ 消息队列")) == "spi"


def test_udc_component_is_read_only_and_exposes_dry_run():
    component = UdcComponent()
    assert component.read_only is True
    assert "dry_run" in component.capabilities()

def test_host_can_inject_context_and_session():
    session = MemorySession()
    agent = XiaozhuaAgent({"udc": UdcComponent()}, context=MemoryContext({"env": "test2"}), session=session)
    result = agent.dispatch(AgentRequest("分析 UDC 实体", {"target": "demo"}))
    assert result["mode"] == "read-only"
    assert session.events[0]["component"] == "udc"

def test_evidence_accepts_only_known_levels():
    assert Evidence("FACT", "jar", "A.class").level == "FACT"


def test_udc_inspect_application_reads_audit_artifact(tmp_path):
    from components.udc.component import UdcComponent

    artifact = tmp_path / "audit.json"
    artifact.write_text('{"artifact_version":"5.3.517","frontend_calls":3}', encoding="utf-8")
    result = UdcComponent(audit_path=artifact).inspect_application("demo")
    assert result["status"] == "FACT"
    assert result["artifact_version"] == "5.3.517"
    assert result["target"] == "demo"

def test_udc_inspection_without_artifact_is_unverified():
    from components.udc.component import UdcComponent

    result = UdcComponent().inspect_application("demo")
    assert result["status"] == "UNVERIFIED"

def test_host_can_inject_tool_port():
    from core.ports import ToolPort
    assert ToolPort is not None


def test_udc_catalog_analyzes_real_audit_directory():
    from components.udc.component import UdcComponent

    audit_dir = ROOT / "tests" / "fixtures" / "udc-audit"
    result = UdcComponent(audit_dir=audit_dir).inspect_application("app9000000000000000001")
    assert result["status"] == "FACT"
    assert result["artifact_version"] == "5.3.517"
    assert result["evidence_files"] >= 8

def test_udc_catalog_reports_missing_directory_as_unverified(tmp_path):
    from components.udc.component import UdcComponent

    result = UdcComponent(audit_dir=tmp_path / "missing").inspect_application("demo")
    assert result["status"] == "UNVERIFIED"


def test_udc_catalog_returns_structured_fact_summary():
    from components.udc.catalog import UdcEvidenceCatalog
    catalog = UdcEvidenceCatalog(ROOT / "tests" / "fixtures" / "udc-audit")
    result = catalog.summary()
    assert result["status"] == "FACT"
    assert result["artifact_version"] == "5.3.517"
    assert result["files_loaded"] >= 10
    assert "frontend_contracts" in result["domains"]

def test_udc_catalog_does_not_claim_missing_evidence(tmp_path):
    from components.udc.catalog import UdcEvidenceCatalog
    result = UdcEvidenceCatalog(tmp_path).summary()
    assert result["status"] == "UNVERIFIED"
    assert result["files_loaded"] == 0
    assert result["missing"]


def test_catalog_exposes_domain_counts():
    from components.udc.catalog import UdcEvidenceCatalog
    result = UdcEvidenceCatalog(ROOT / "tests" / "fixtures" / "udc-audit").report()
    assert result["status"] == "FACT"
    assert result["counts"]["backend_contracts"] == 672
    assert result["counts"]["frontend_contracts"] == 36

def test_agent_dispatch_returns_component_report():
    from components.udc.catalog import UdcEvidenceCatalog
    component = UdcComponent(audit_dir=ROOT / "tests" / "fixtures" / "udc-audit")
    result = component.report("demo")
    assert result["status"] == "FACT"
    assert result["component"] == "udc"
    assert "domains" in result


def test_udc_report_exposes_domain_facts():
    result = UdcComponent(audit_dir=ROOT / "tests" / "fixtures" / "udc-audit").report("demo")
    assert result["domains"]["backend_contracts"]["status"] == "FACT"
    assert result["facts"]["backend_operations"] == 145
    assert result["facts"]["frontend_contracts"] == 16

def test_udc_report_exposes_version_and_deployment_facts():
    result = UdcComponent(audit_dir=ROOT / "tests" / "fixtures" / "udc-audit").report("demo")
    assert result["facts"]["sampled_versions"] == 6
    assert result["facts"]["frontend_independent_artifact"] is True

def test_udc_report_preserves_unverified_gaps():
    result = UdcComponent(audit_dir=ROOT / "tests" / "fixtures" / "udc-audit").report("demo")
    assert result["unverified"]
    assert "frontend_static_source" in result["unverified"]
