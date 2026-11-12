"""Plan validation and golden-diff for the Construction Engine.

v0.2 adds a unified pipeline: validate_plan -> compare_artifact_plan ->
ValidationReport, so a plan is checked structurally and against the audited
Golden Sample through one entry point (validate_pipeline).
"""

from dataclasses import dataclass, field
from collections import Counter

from .models import ARTIFACT_TYPES, GeneratedArtifactPlan, SCHEMA_ID


@dataclass
class ValidationResult:
    status: str
    blocked: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class GoldenDiffResult:
    status: str
    missing: list[str] = field(default_factory=list)
    unexpected: list[str] = field(default_factory=list)
    ambiguous: list[str] = field(default_factory=list)
    matched: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    status: str
    validation: ValidationResult
    golden_diff: GoldenDiffResult
    def to_dict(self):
        return {
            "schema": SCHEMA_ID,
            "status": self.status,
            "validation": {
                "status": self.validation.status,
                "blocked": list(self.validation.blocked),
                "unknown": list(self.validation.unknown),
                "warnings": list(self.validation.warnings),
            },
            "golden_diff": {
                "status": self.golden_diff.status,
                "missing": list(self.golden_diff.missing),
                "unexpected": list(self.golden_diff.unexpected),
                "ambiguous": list(self.golden_diff.ambiguous),
                "matched": list(self.golden_diff.matched),
            },
        }


_REQUIRED = {
    ("facade", "dto"), ("facade", "api"),
    ("biz", "entity"), ("biz", "domain_service"),
    ("biz", "app_service_impl"), ("biz", "dao"),
}

_REQUIRED_TYPES = frozenset(key for _, key in _REQUIRED)


def validate_plan(plan):
    blocked = list(plan.blocked)
    unknown = list(plan.unknown)
    if plan.schema != SCHEMA_ID:
        blocked.append(f"schema-mismatch:{plan.schema} != {SCHEMA_ID}")
    for a in plan.artifacts:
        if a.type not in ARTIFACT_TYPES:
            blocked.append(f"unknown-artifact-type:{a.type}")
    keys = [(a.module, a.relative_path) for a in plan.artifacts]
    for key, count in Counter(keys).items():
        if count > 1:
            blocked.append(f"duplicate-artifact:{key[0]}:{key[1]}")
    present = {(a.module, a.type) for a in plan.artifacts}
    for key in sorted(_REQUIRED - present):
        blocked.append(f"missing-required:{key[0]}:{key[1]}")
    for a in plan.artifacts:
        if not _identifier(a.class_name):
            blocked.append(f"invalid-identifier:{a.class_name}")
        if not all(_identifier(part) for part in a.package.split(".")):
            blocked.append(f"invalid-package:{a.package}")
    return ValidationResult(
        "FAIL" if blocked else ("PARTIAL" if unknown else "PASS"),
        blocked, unknown, list(plan.warnings),
    )


def compare_artifact_plan(predicted_plan, observed_artifacts):
    predicted = [a.fully_qualified_name for a in predicted_plan.artifacts]
    observed = list(observed_artifacts)
    pc, oc = Counter(predicted), Counter(observed)
    ambiguous = sorted([x for x in set(pc) | set(oc) if pc[x] > 1 or oc[x] > 1])
    matched = sorted(set(predicted) & set(observed) - set(ambiguous))
    missing = sorted((set(predicted) - set(observed)))
    unexpected = sorted((set(observed) - set(predicted)))
    if ambiguous:
        status = "FAIL"
    elif not missing and not unexpected:
        status = "PASS"
    elif not matched:
        status = "FAIL"
    else:
        status = "PARTIAL"
    return GoldenDiffResult(status, missing, unexpected, ambiguous, matched)


def validate_pipeline(plan, observed_artifacts):
    """Unified v0.2 pipeline: structural validation, then golden diff.

    Fail-fast: when structural validation fails, the golden diff is reported
    as SKIPPED with empty lists instead of being evaluated against a broken
    plan. A golden comparison against a plan for a different application is
    rejected outright.
    """
    validation = validate_plan(plan)
    if validation.status == "FAIL":
        skipped = GoldenDiffResult("SKIPPED", [], [], [], [])
        return ValidationReport("FAIL", validation, skipped)
    observed = list(observed_artifacts)
    if observed:
        observed_apps = {fqn.split(".")[2] for fqn in observed if fqn.startswith("com.seeyon.") and len(fqn.split(".")) > 3}
        if observed_apps and observed_apps != {plan.application_id}:
            raise ValueError(
                "golden sample belongs to a different application: "
                f"{sorted(observed_apps)} != {plan.application_id}"
            )
    diff = compare_artifact_plan(plan, observed)
    status = "FAIL" if validation.status == "FAIL" or diff.status == "FAIL" else (
        "PARTIAL" if validation.status == "PARTIAL" or diff.status == "PARTIAL" else "PASS"
    )
    return ValidationReport(status, validation, diff)


def _identifier(value):
    return bool(value) and (value[0].isalpha() or value[0] in "_$") and all(
        ch.isascii() and (ch.isalnum() or ch in "_$") for ch in value
    )
