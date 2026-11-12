from pathlib import Path

import pytest

from components.construction import (
    ConstructionEvaluator, ConstructionRuleRegistry, NormalizedEntityModel,
)
from components.construction.generator import DtoSourceGenerator


ROOT = Path(__file__).resolve().parents[5]


def _plan(model):
    registry = ConstructionRuleRegistry(ROOT / "docs" / "construction-rules").load()
    return ConstructionEvaluator(registry).plan(model)


def test_dto_generator_renders_only_dto_artifact():
    model = NormalizedEntityModel("demoapp", None, "Customer")
    plan = _plan(model)
    generated = DtoSourceGenerator().generate(plan, model)
    assert generated.relative_path == "facade/dto/CustomerDto.java"
    assert "package com.seeyon.demoapp.dto;" in generated.source
    assert "public class CustomerDto extends BaseRootDto" in generated.source
    assert generated.artifact_type == "dto"


def test_dto_generator_uses_explicit_attributes_without_inventing_fields():
    model = NormalizedEntityModel(
        "demoapp", None, "Customer",
        [{"name": "customerNo", "type": "String", "required": True}],
    )
    generated = DtoSourceGenerator().generate(_plan(model), model)
    assert "private String customerNo;" in generated.source
    assert "private String missing;" not in generated.source


def test_dto_generator_rejects_plan_without_dto():
    model = NormalizedEntityModel("demoapp", None, "Customer")
    plan = _plan(model)
    plan.artifacts = [a for a in plan.artifacts if a.type != "dto"]
    with pytest.raises(ValueError, match="dto artifact"):
        DtoSourceGenerator().generate(plan, model)


def test_dto_generator_does_not_generate_other_artifacts():
    model = NormalizedEntityModel("demoapp", None, "Customer")
    generated = DtoSourceGenerator().generate(_plan(model), model)
    assert generated.artifact_type == "dto"
    assert "CustomerService" not in generated.source
    assert "CustomerController" not in generated.source
