import re

from .models import UNKNOWN, GeneratedArtifact, GeneratedArtifactPlan

_IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")

# v0.2: package_root semantics are frozen. The audited Golden Sample
# (docs/audit/artifacts/customer-{facade,biz,web}-1.0.11029) observes
# com.seeyon.<application_id> as the real package root of every core artifact.
PACKAGE_ROOT_TEMPLATE = "com.seeyon.<application_id>"
_PACKAGE_ROOT_PREFIX = "com.seeyon."


def package_root_for(application_id: str, package_root=None) -> str:
    """Resolve the concrete package root for an application.

    v0.2 semantics: the root is always com.seeyon.<application_id>.
    An explicit NormalizedEntityModel.package_root overrides the template,
    which keeps inputs whose root cannot be derived from the application id
    expressible, but the default derivation is no longer the bare id.
    """
    expected = _PACKAGE_ROOT_PREFIX + application_id
    if package_root is not None and str(package_root) != expected:
        return str(package_root)
    return expected


class ConstructionEvaluator:
    def __init__(self, registry):
        self.registry = registry

    def plan(self, model):
        naming = self.registry.get("udc.construction.entity.naming.v1")
        package = self.registry.get("udc.construction.entity.package.v1")
        contracts = [self.registry.get(x) for x in ("udc.construction.entity.generation-contract.v1",)]
        root = package_root_for(model.application_id, model.package_root)
        template_root = PACKAGE_ROOT_TEMPLATE.replace(
            "<application_id>", model.application_id
        )
        plan_warning = None
        if root != template_root:
            plan_warning = (
                "package-root-override:"
                f"{root} != {template_root}"
            )
        plan = GeneratedArtifactPlan(
            SCHEMA_ID,
            model.application_id,
            model.entity_name,
            evidence=[*naming.evidence, *package.evidence],
        )
        if plan_warning:
            plan.warnings.append(plan_warning)
        if not _IDENTIFIER.match(model.entity_name):
            plan.blocked.append(f"invalid-entity-identifier:{model.entity_name}")
            return plan
        if not self._valid_package(root):
            plan.blocked.append(f"invalid-package:{root}")
            return plan
        # naming.json: DAO class = <ApplicationStem>XDao, where the stem is
        # the application id with its first character capitalized.
        stem = model.application_id[:1].upper() + model.application_id[1:]
        specs = [
            ("facade", "dto", "dto", f"{model.entity_name}Dto", True),
            ("facade", "api", "api", f"{model.entity_name}AppService", True),
            ("biz", "entity", "domain.entity", model.entity_name, True),
            ("biz", "domain_service", "domain.service", f"{model.entity_name}Service", True),
            ("biz", "app_service_impl", "appservice", f"{model.entity_name}AppServiceImpl", True),
            ("biz", "dao", "domain.dao", f"{stem}{model.entity_name}Dao", True),
            ("web", "abstract_controller", "controller", f"Abstract{model.entity_name}Controller", False),
            ("web", "controller", "controller", f"{model.entity_name}Controller", False),
        ]
        for module, kind, suffix, cls, required in specs:
            pkg = f"{root}.{suffix}"
            directory = {"facade": "facade", "biz": "biz", "web": "web"}[module]
            subdir = {
                "dto": "dto", "api": "api", "entity": "domain/entity",
                "domain_service": "domain/service", "app_service_impl": "appservice",
                "dao": "domain/dao", "abstract_controller": "controller",
                "controller": "controller",
            }[kind]
            plan.artifacts.append(
                GeneratedArtifact(
                    module, kind, pkg, cls,
                    f"{directory}/{subdir}/{cls}.java", required,
                    contracts[0].rule_id, contracts[0].confidence,
                )
            )
        for attr in model.attributes:
            name = getattr(attr, "name", None) if not isinstance(attr, dict) else attr.get("name")
            typ = getattr(attr, "type", UNKNOWN) if not isinstance(attr, dict) else attr.get("type", UNKNOWN)
            if typ in (None, UNKNOWN, ""):
                plan.unknown.append(f"attribute:{name}:type")
        return plan

    @staticmethod
    def _valid_package(value):
        return bool(value) and all(_IDENTIFIER.match(part) for part in value.split("."))


# Imported late to avoid a circular import at module load time:
# validation.py imports the frozen schema id from models, and the evaluator
# shares the same constant.
from .validation import SCHEMA_ID  # noqa: E402
