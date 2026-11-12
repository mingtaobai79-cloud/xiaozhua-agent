"""Public Construction Engine v0.2 API."""
from dataclasses import dataclass, field
from typing import Any

from .models import NormalizedEntityModel, GeneratedArtifactPlan
from .evaluator import ConstructionEvaluator
from .validation import ValidationReport, validate_pipeline


@dataclass
class ConstructionTask:
    model: NormalizedEntityModel
    observed_artifacts: list[str] | None = None


@dataclass
class ConstructionResult:
    plan: GeneratedArtifactPlan
    validation: Any
    golden_diff: Any
    warnings: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    status: str = "UNVERIFIED"

    def to_dict(self):
        return {
            "status": self.status,
            "plan": self.plan.to_dict(),
            "validation": self.validation.status,
            "golden_diff": self.golden_diff.status,
            "warnings": list(self.warnings),
            "unknowns": list(self.unknowns),
        }


class ConstructionEngine:
    def __init__(self, evaluator: ConstructionEvaluator):
        self.evaluator = evaluator

    def evaluate(self, task: ConstructionTask, observed_artifacts=None) -> ConstructionResult:
        model = task.model
        observed = task.observed_artifacts if observed_artifacts is None else observed_artifacts
        observed = list(observed or [])
        plan = self.evaluator.plan(model)
        report = validate_pipeline(plan, observed)
        return ConstructionResult(
            plan=plan, validation=report.validation, golden_diff=report.golden_diff,
            warnings=list(plan.warnings), unknowns=list(plan.unknown), status=report.status,
        )
