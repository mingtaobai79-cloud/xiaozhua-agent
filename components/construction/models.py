"""Frozen constants and dataclasses for Construction Engine v0.2."""

from dataclasses import dataclass, field, asdict
from typing import Any
from enum import Enum

UNKNOWN = "UNKNOWN"

# v0.2: the GeneratedArtifactPlan schema id is frozen. All plans carry this
# exact identifier; consumers may pin on it.
SCHEMA_ID = "udc.construction.artifact-plan.v1"

# v0.2: closed enum of planned artifact types. The Hetongdangan Golden Sample
# covers exactly these eight core types.
class ArtifactType(str, Enum):
    DTO = "dto"
    API = "api"
    ENTITY = "entity"
    DOMAIN_SERVICE = "domain_service"
    APP_SERVICE_IMPL = "app_service_impl"
    DAO = "dao"
    ABSTRACT_CONTROLLER = "abstract_controller"
    CONTROLLER = "controller"


ARTIFACT_TYPES = frozenset({
    "dto", "api", "entity", "domain_service",
    "app_service_impl", "dao", "abstract_controller", "controller",
})

_MODULES = frozenset({"facade", "biz", "web"})


@dataclass
class EvidenceRef:
    source: str = UNKNOWN
    ref: str = UNKNOWN
    confidence: str = UNKNOWN
    note: str = UNKNOWN
    def to_dict(self): return asdict(self)

@dataclass
class NormalizedAttribute:
    name: str
    type: Any = UNKNOWN
    caption: Any = UNKNOWN
    required: Any = UNKNOWN
    default_value: Any = UNKNOWN
    relation: Any = UNKNOWN
    evidence: list[EvidenceRef] = field(default_factory=list)
    def __post_init__(self):
        self.evidence = [x if isinstance(x, EvidenceRef) else EvidenceRef(**x) if isinstance(x, dict) else x for x in self.evidence]
    def to_dict(self):
        data = asdict(self); data["evidence"] = [x.to_dict() if hasattr(x, "to_dict") else x for x in self.evidence]; return data

@dataclass
class NormalizedEntityModel:
    application_id: str
    package_root: Any
    entity_name: str
    attributes: list[Any] = field(default_factory=list)
    caption: Any = UNKNOWN
    description: Any = UNKNOWN
    children: list[Any] = field(default_factory=list)
    indexes: list[Any] = field(default_factory=list)
    events: list[Any] = field(default_factory=list)
    rule_flags: dict[str, Any] = field(default_factory=dict)
    evidence: list[EvidenceRef] = field(default_factory=list)
    def __post_init__(self):
        self.attributes = [x if isinstance(x, NormalizedAttribute) else NormalizedAttribute(**x) if isinstance(x, dict) else x for x in self.attributes]
        self.evidence = [x if isinstance(x, EvidenceRef) else EvidenceRef(**x) if isinstance(x, dict) else x for x in self.evidence]
    def to_dict(self):
        data = asdict(self); data["attributes"] = [x.to_dict() if hasattr(x, "to_dict") else x for x in self.attributes]; data["evidence"] = [x.to_dict() if hasattr(x, "to_dict") else x for x in self.evidence]; return data

@dataclass
class GeneratedArtifact:
    module: str
    type: str
    package: str
    class_name: str
    relative_path: str
    required: bool = True
    rule_id: str = UNKNOWN
    confidence: str = UNKNOWN

    def __post_init__(self):
        try:
            self.type = ArtifactType(self.type).value
        except (TypeError, ValueError) as exc:
            raise ValueError(f"unknown artifact type: {self.type}") from exc
        if not self.module or not self.package or not self.class_name or not self.relative_path:
            raise ValueError("module, package, class_name and relative_path are required")

    @property
    def fully_qualified_name(self): return f"{self.package}.{self.class_name}"
    def to_dict(self): return asdict(self)

@dataclass
class GeneratedArtifactPlan:
    schema: str = SCHEMA_ID
    application_id: str = ""
    entity_name: str = ""
    artifacts: list[GeneratedArtifact] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence: list[Any] = field(default_factory=list)
    def to_dict(self):
        return {"schema": self.schema, "application_id": self.application_id, "entity_name": self.entity_name, "artifacts": [x.to_dict() for x in self.artifacts], "unknown": self.unknown, "blocked": self.blocked, "warnings": self.warnings, "evidence": [x.to_dict() if hasattr(x, "to_dict") else x for x in self.evidence]}
