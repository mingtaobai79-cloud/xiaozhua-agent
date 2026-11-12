import json
from pathlib import Path

from components.udc import UdcComponent, UdcRequest
from components.udc.analyzers import UdcAnalyzer
from components.udc.contracts import UdcOperationCatalog
from components.udc.models import ApplicationSpec, EntitySpec, FieldSpec, PageSpec, MicroFlowSpec
from components.udc.planner import UdcPlanner
from components.udc.versioning import UdcVersionRegistry

ROOT = Path(__file__).parents[1]

AUDIT = ROOT / "tests" / "fixtures" / "udc-audit"

def test_udc_models_validate_and_serialize():
    spec = ApplicationSpec(name="demo", caption="Demo", entities=[EntitySpec(name="Order", fields=[FieldSpec(name="code", type="STRING", length=64)])])
    payload = spec.to_dict()
    assert payload["entities"][0]["fields"][0]["length"] == 64

def test_operation_catalog_loads_frontend_and_backend_contracts():
    catalog = UdcOperationCatalog(AUDIT)
    result = catalog.summary()
    assert result["frontend_unique_calls"] == 36
    assert result["backend_endpoints"] == 672
    assert result["status"] == "FACT"

def test_version_registry_selects_exact_version_and_rejects_unknown():
    registry = UdcVersionRegistry(AUDIT)
    assert registry.resolve("5.3.517")["status"] == "FACT"
    assert registry.resolve("9.9.9")["status"] == "UNVERIFIED"

def test_planner_builds_read_only_plan_for_application():
    plan = UdcPlanner().plan_application(ApplicationSpec(name="demo", caption="Demo"))
    assert plan.mode == "dry-run"
    assert plan.write_operations == []
    assert plan.steps[0]["action"] == "inspect_application"

def test_component_dispatches_structured_application_report():
    component = UdcComponent(audit_dir=AUDIT)
    result = component.execute(UdcRequest(action="inspect_application", target="demo"))
    assert result["status"] == "FACT"
    assert result["counts"]["backend_contracts"] == 672

def test_component_rejects_write_actions_by_default():
    component = UdcComponent(audit_dir=AUDIT)
    result = component.execute(UdcRequest(action="publish", target="demo"))
    assert result["status"] == "DENIED"


def test_udc_domain_report_exposes_operation_and_version_details():
    result = UdcComponent(audit_dir=AUDIT).domain_report("demo")
    assert result["status"] == "FACT"
    assert result["domains"]["frontend"]["unique_calls"] == 36
    assert result["domains"]["backend"]["endpoints"] == 672
    assert result["domains"]["versions"]["count"] == 6

def test_udc_domain_report_keeps_unverified_contract_gaps():
    result = UdcComponent(audit_dir=AUDIT).domain_report("demo")
    assert "dynamic_contract_fields" in result["unverified"]

def test_udc_dry_run_has_no_write_operations():
    spec = ApplicationSpec(name="demo", caption="Demo")
    plan = UdcPlanner().plan(spec)
    assert plan["mode"] == "dry-run"
    assert plan["write_operations"] == []


def test_udc_analyzers_return_domain_sections_from_audit_files():
    component = UdcComponent(audit_dir=AUDIT)
    result = component.analyze("demo")
    assert result["status"] == "FACT"
    assert set(result["domains"]) == {"application", "entity", "page", "microflow", "version", "deployment"}
    assert result["domains"]["page"]["frontend_operations"] == 36
    assert result["domains"]["microflow"]["backend_operations"] == 145

def test_udc_analyzer_marks_missing_domain_evidence():
    from components.udc.analyzers import UdcAnalyzer
    result = UdcAnalyzer(AUDIT).analyze("demo")
    assert result["domains"]["application"]["status"] == "FACT"

def test_udc_plan_contains_all_declared_application_parts():
    spec = ApplicationSpec(name="demo", caption="Demo", entities=[EntitySpec("Order")], pages=[PageSpec("OrderPage")], microflows=[MicroFlowSpec("SaveOrder")])
    plan = UdcPlanner().plan(spec)
    assert [step["action"] for step in plan["steps"]] == ["inspect_application", "inspect_entity", "inspect_page", "inspect_microflow"]


def test_udc_report_has_truthful_dynamic_contract_counts():
    result = UdcComponent(audit_dir=AUDIT).report("demo")
    assert result["facts"]["backend_operations"] == 145
    assert result["facts"]["frontend_contracts"] == 16
    assert "dynamic_contract_fields" in result["unverified"]

def test_udc_planner_creates_dry_run_steps_for_all_parts():
    spec = ApplicationSpec(name="demo", caption="Demo", entities=[EntitySpec("Order")], pages=[PageSpec("OrderPage")], microflows=[MicroFlowSpec("SaveOrder")])
    plan = UdcPlanner().plan(spec)
    assert plan["mode"] == "dry-run"
    assert plan["write_operations"] == []
    assert [step["action"] for step in plan["steps"]] == ["inspect_application", "inspect_entity", "inspect_page", "inspect_microflow"]


def test_udc_analyzer_extracts_real_domain_counts_and_evidence_files():
    result = UdcComponent(audit_dir=AUDIT).analyze("demo")
    assert result["domains"]["application"]["count"] == 3
    assert result["domains"]["entity"]["count"] == 16
    assert result["domains"]["page"]["count"] == 8
    assert result["domains"]["microflow"]["count"] == 9
    assert result["domains"]["version"]["count"] == 6
    assert result["domains"]["deployment"]["count"] == 1793
    assert result["domains"]["entity"]["evidence_file"] == "udc_web_controller_contracts.json"
    assert result["domains"]["deployment"]["evidence_file"] == "udc_deployment_artifacts_audit.json"


def test_udc_analyzer_marks_missing_count_as_unverified(tmp_path):
    (tmp_path / "udc_web_controller_contracts.json").write_text(
        '{"domains": {"Application": 1}}', encoding="utf-8"
    )
    result = UdcAnalyzer(tmp_path).analyze("demo")
    assert result["domains"]["application"]["count"] == 1
    assert result["domains"]["entity"]["status"] == "UNVERIFIED"
    assert result["domains"]["entity"]["count"] == "UNVERIFIED"
    assert result["domains"]["entity"]["evidence_file"] == "udc_web_controller_contracts.json"


def test_udc_analyze_preserves_known_unverified_gaps():
    result = UdcComponent(audit_dir=AUDIT).analyze("demo")
    assert "dynamic_contract_fields" in result["unverified"]
    assert "frontend_static_source" in result["unverified"]


def test_udc_report_reads_backend_operation_count_from_dynamic_evidence(tmp_path):
    import shutil
    shutil.copytree(AUDIT, tmp_path / "audit")
    dynamic = tmp_path / "audit" / "udc_dynamic_contract_gap_catalog.json"
    dynamic.write_text(
        '{"backend_operations": [{"id": "one"}, {"id": "two"}], "unverified_dto_gaps": ["EntityDto"]}',
        encoding="utf-8",
    )

    result = UdcComponent(audit_dir=tmp_path / "audit").report("demo")

    assert result["facts"]["backend_operations"] == 2
    assert "dynamic_contract_fields" in result["unverified"]


def test_component_inspect_entity_returns_domain_evidence():
    result = UdcComponent(audit_dir=AUDIT).execute(UdcRequest(action="inspect_entity", target="demo"))
    assert result["status"] == "FACT"
    assert result["domain"] == "entity"
    assert result["count"] == 16
    assert result["evidence_file"] == "udc_web_controller_contracts.json"


def test_component_inspect_page_returns_domain_evidence():
    result = UdcComponent(audit_dir=AUDIT).execute(UdcRequest(action="inspect_page", target="demo"))
    assert result["status"] == "FACT"
    assert result["domain"] == "page"
    assert result["count"] == 8
    assert result["frontend_operations"] == 36


def test_component_inspect_microflow_returns_domain_evidence_and_gap():
    result = UdcComponent(audit_dir=AUDIT).execute(UdcRequest(action="inspect_microflow", target="demo"))
    assert result["status"] == "FACT"
    assert result["domain"] == "microflow"
    assert result["count"] == 9
    assert result["backend_operations"] == 145
    assert "dynamic_contract_fields" in result["unverified"]


def test_component_dry_run_invokes_planner_without_writes():
    result = UdcComponent(audit_dir=AUDIT).execute(UdcRequest(action="dry_run", target="demo"))
    assert result["mode"] == "dry-run"
    assert result["executed"] is False
    assert result["writes_performed"] is False
    assert result["write_operations"] == []


def test_remaining_inspect_actions_return_evidence_bounded_results():
    component = UdcComponent(audit_dir=AUDIT)
    expected = {
        "inspect_field": ("UNVERIFIED", "dynamic_contract_fields"),
        "inspect_page_schema": ("UNVERIFIED", "dynamic_contract_fields"),
        "inspect_dataflow": ("UNVERIFIED", "dynamic_contract_fields"),
        "inspect_version": ("FACT", None),
        "inspect_generated_app": ("FACT", "frontend_static_source"),
        "inspect_runtime_metadata": ("UNVERIFIED", "runtime_metadata_live_state"),
        "inspect_deployment": ("FACT", "frontend_static_source"),
    }
    for action, (status, gap) in expected.items():
        result = component.execute(UdcRequest(action=action, target="demo"))
        assert result["status"] == status, action
        assert result["action"] == action
        assert result["evidence"], action
        if gap:
            assert gap in result["unverified"], action


def test_component_capabilities_list_all_inspect_actions():
    assert set(UdcComponent(audit_dir=AUDIT).capabilities()) == {
        "inspect_application", "inspect_entity", "inspect_field", "inspect_page",
        "inspect_page_schema", "inspect_microflow", "inspect_dataflow",
        "inspect_version", "inspect_generated_app", "inspect_runtime_metadata",
        "inspect_deployment", "dry_run",
    }
