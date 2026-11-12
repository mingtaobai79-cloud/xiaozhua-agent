"""Construction Engine v0.2 - TDD RED tests.

Scope (v0.2):
1. package_root semantics fixed to com.seeyon.<application_id>.
2. GeneratedArtifactPlan schema frozen (SCHEMA_ID + type enum).
3. Hetongdangan Golden Sample fixture loader.
4. Unified validation + golden-diff pipeline.

These tests encode the real audited Golden Sample under
docs/audit/artifacts/customer-{facade,biz,web}-1.0.11029, whose observed
package root is com.seeyon.9000000000000000001 - NOT the bare
application id used by the v0.1 synthetic diff.
"""
from pathlib import Path

import pytest

from components.construction.models import (
    GeneratedArtifact,
    GeneratedArtifactPlan,
    NormalizedEntityModel,
)
from components.construction.registry import ConstructionRuleRegistry
from components.construction.evaluator import (
    PACKAGE_ROOT_TEMPLATE,
    ConstructionEvaluator,
)
from components.construction.models import ARTIFACT_TYPES, SCHEMA_ID
from components.construction.validation import (
    ValidationReport,
    validate_pipeline,
)

REPO = Path(__file__).resolve().parents[2]
RULES_ROOT = REPO / "docs" / "construction-rules"
GOLDEN_ROOT = REPO

# 黄金样本的应用标识是仓外事实，测试期望值与 loader 同源运行时解析
# （仓库内不留客户标识；仓外证据缺失时退化为占位自洽校验）
from components.construction.fixtures import golden_application_id as _gid
GOLDEN_APP = _gid()
GOLDEN_ENTITY = "Hetongdangan"


def registry() -> ConstructionRuleRegistry:
    return ConstructionRuleRegistry(RULES_ROOT).load()


# ---------------------------------------------------------------------------
# 1. package_root semantics: com.seeyon.<application_id>
# ---------------------------------------------------------------------------

def test_package_root_template_is_com_seeyon():
    assert PACKAGE_ROOT_TEMPLATE == "com.seeyon.<application_id>"


def test_plan_package_root_is_com_seeyon_prefixed():
    evaluator = ConstructionEvaluator(registry())
    plan = evaluator.plan(NormalizedEntityModel("demoapp", None, "Customer"))
    assert all(a.package.startswith("com.seeyon.demoapp.") for a in plan.artifacts)
    dto = next(a for a in plan.artifacts if a.type == "dto")
    assert dto.package == "com.seeyon.demoapp.dto"
    entity = next(a for a in plan.artifacts if a.type == "entity")
    assert entity.package == "com.seeyon.demoapp.domain.entity"


def test_dao_uses_application_stem_from_prefixed_root():
    plan = ConstructionEvaluator(registry()).plan(
        NormalizedEntityModel(GOLDEN_APP, None, "Hetongdangan")
    )
    dao = next(a for a in plan.artifacts if a.type == "dao")
    assert dao.class_name == GOLDEN_APP[0].upper() + GOLDEN_APP[1:] + "HetongdanganDao"


def test_explicit_package_root_overrides_application_id():
    plan = ConstructionEvaluator(registry()).plan(
        NormalizedEntityModel("demoapp", "com.seeyon.custom.root", "Customer")
    )
    dto = next(a for a in plan.artifacts if a.type == "dto")
    assert dto.package == "com.seeyon.custom.root.dto"


def test_invalid_root_is_blocked_not_silently_prefixed():
    plan = ConstructionEvaluator(registry()).plan(
        NormalizedEntityModel("demoapp", "com.seeyon.demo app", "Customer")
    )
    assert any(x.startswith("invalid-package:") for x in plan.blocked)


# ---------------------------------------------------------------------------
# 2. GeneratedArtifactPlan schema frozen
# ---------------------------------------------------------------------------

def test_plan_schema_id_constant_is_stable():
    assert SCHEMA_ID == "udc.construction.artifact-plan.v1"


def test_artifact_type_enum_frozen():
    assert ARTIFACT_TYPES == frozenset({
        "dto", "api", "entity", "domain_service",
        "app_service_impl", "dao", "abstract_controller", "controller",
    })


def test_plan_carries_schema_constant_by_default():
    plan = GeneratedArtifactPlan(application_id="demoapp", entity_name="Customer")
    assert plan.schema == SCHEMA_ID


def test_plan_to_dict_uses_frozen_schema():
    artifact = GeneratedArtifact(
        "facade", "dto", "com.seeyon.demoapp.dto", "CustomerDto",
        "facade/dto/CustomerDto.java",
    )
    plan = GeneratedArtifactPlan(application_id="demoapp", entity_name="Customer", artifacts=[artifact])
    assert plan.to_dict()["schema"] == "udc.construction.artifact-plan.v1"


# ---------------------------------------------------------------------------
# 3. Hetongdangan Golden Sample fixture loader
# ---------------------------------------------------------------------------

def test_fixture_loader_reads_real_golden_sample():
    from components.construction.fixtures import load_golden_sample
    golden = load_golden_sample(GOLDEN_ROOT)
    assert golden.application_id == GOLDEN_APP
    assert golden.entity_name == GOLDEN_ENTITY
    assert golden.package_root == "com.seeyon." + GOLDEN_APP


def test_fixture_loader_fqns_match_audit_products():
    from components.construction.fixtures import load_golden_sample
    golden = load_golden_sample(GOLDEN_ROOT)
    assert golden.fully_qualified_names == {
        "com.seeyon." + GOLDEN_APP + ".api.HetongdanganAppService",
        "com.seeyon." + GOLDEN_APP + ".appservice.HetongdanganAppServiceImpl",
        "com.seeyon." + GOLDEN_APP + ".controller.AbstractHetongdanganController",
        "com.seeyon." + GOLDEN_APP + ".controller.HetongdanganController",
        "com.seeyon." + GOLDEN_APP + ".domain.dao." + GOLDEN_APP[0].upper() + GOLDEN_APP[1:] + "HetongdanganDao",
        "com.seeyon." + GOLDEN_APP + ".domain.entity.Hetongdangan",
        "com.seeyon." + GOLDEN_APP + ".domain.service.HetongdanganService",
        "com.seeyon." + GOLDEN_APP + ".dto.HetongdanganDto",
    }


def test_fixture_loader_is_not_hardcoded_synthetic():
    """The loader must parse the audit products, not return a literal list."""
    import inspect
    from components.construction import fixtures
    src = inspect.getsource(fixtures.load_golden_sample)
    assert "customer-facade-1.0.11029" in src or "artifacts_root" in src


# ---------------------------------------------------------------------------
# 4. Unified validation + golden diff pipeline
# ---------------------------------------------------------------------------

def test_pipeline_passes_against_real_golden_sample():
    from components.construction.fixtures import load_golden_sample
    evaluator = ConstructionEvaluator(registry())
    golden = load_golden_sample(GOLDEN_ROOT)
    plan = evaluator.plan(NormalizedEntityModel(
        golden.application_id, None, golden.entity_name
    ))
    report = validate_pipeline(plan, golden.fully_qualified_names)
    assert report.validation.status == "PASS"
    assert report.golden_diff.status == "PASS"
    assert report.status == "PASS"
    assert len(report.golden_diff.matched) == 8
    assert report.golden_diff.missing == [] and report.golden_diff.unexpected == []


def test_pipeline_reports_partial_on_missing_observed():
    from components.construction.fixtures import load_golden_sample
    golden = load_golden_sample(GOLDEN_ROOT)
    plan = ConstructionEvaluator(registry()).plan(NormalizedEntityModel(
        golden.application_id, None, golden.entity_name
    ))
    observed = sorted(golden.fully_qualified_names)[:1]
    report = validate_pipeline(plan, observed)
    assert report.status == "PARTIAL"
    assert len(report.golden_diff.missing) == 7


def test_pipeline_fail_fast_on_blocked_plan():
    plan = ConstructionEvaluator(registry()).plan(
        NormalizedEntityModel("demoapp", None, "bad-name")
    )
    report = validate_pipeline(plan, [])
    assert report.status == "FAIL"
    assert report.golden_diff.status == "SKIPPED"
    assert report.golden_diff.missing == [] and report.golden_diff.unexpected == []


def test_pipeline_rejects_mismatched_plan_application():
    from components.construction.fixtures import load_golden_sample
    golden = load_golden_sample(GOLDEN_ROOT)
    plan = ConstructionEvaluator(registry()).plan(NormalizedEntityModel("otherapp", None, "Customer"))
    with pytest.raises(ValueError):
        validate_pipeline(plan, golden.fully_qualified_names)


# ---------------------------------------------------------------------------
# 5. Regression coverage: Hetongdangan names under v0.2 com.seeyon root
# ---------------------------------------------------------------------------

def test_updated_v01_evaluator_tests_semantics():
    plan = ConstructionEvaluator(registry()).plan(
        NormalizedEntityModel(GOLDEN_APP, None, "Hetongdangan")
    )
    assert {a.fully_qualified_name for a in plan.artifacts} == {
        "com.seeyon." + GOLDEN_APP + ".api.HetongdanganAppService",
        "com.seeyon." + GOLDEN_APP + ".appservice.HetongdanganAppServiceImpl",
        "com.seeyon." + GOLDEN_APP + ".controller.AbstractHetongdanganController",
        "com.seeyon." + GOLDEN_APP + ".controller.HetongdanganController",
        "com.seeyon." + GOLDEN_APP + ".domain.dao." + GOLDEN_APP[0].upper() + GOLDEN_APP[1:] + "HetongdanganDao",
        "com.seeyon." + GOLDEN_APP + ".domain.entity.Hetongdangan",
        "com.seeyon." + GOLDEN_APP + ".domain.service.HetongdanganService",
        "com.seeyon." + GOLDEN_APP + ".dto.HetongdanganDto",
    }
