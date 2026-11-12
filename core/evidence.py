from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class Status(str, Enum):
    FACT = "FACT"
    OBSERVATION = "OBSERVATION"
    HYPOTHESIS = "HYPOTHESIS"
    UNVERIFIED = "UNVERIFIED"
    BLOCKED = "BLOCKED"
    DENIED = "DENIED"
    UNAVAILABLE = "UNAVAILABLE"
    CONFLICT = "CONFLICT"

@dataclass(frozen=True)
class Evidence:
    level: str | Status
    source: str
    locator: str
    detail: dict[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        level = self.level.value if isinstance(self.level, Status) else self.level
        if level not in {item.value for item in Status}:
            raise ValueError(f"invalid evidence level: {level}")
        object.__setattr__(self, "level", level)

class Result(dict):
    def __init__(self, component: str, target: str, status: str | Status, evidence: list[Evidence | dict[str, Any]] | None = None, **values: Any):
        status_value = status.value if isinstance(status, Status) else str(status)
        verification_level = str(values.pop("verification_level", "STATIC" if status_value in {"FACT", "OBSERVATION", "HYPOTHESIS"} else "UNKNOWN"))
        conflicts = list(values.pop("conflicts", []))
        if status_value == "LIVE" and verification_level != "LIVE":
            conflicts.append({"reason": "non-live evidence cannot claim LIVE status"})
            status_value = "UNVERIFIED"
        items = []
        for item in evidence or []:
            items.append(item.to_dict() if hasattr(item, "to_dict") else item.__dict__ if hasattr(item, "__dict__") else dict(item))
        defaults = {"facts": {}, "unverified": [], "conflicts": conflicts, "limitations": [], "next_actions": []}
        defaults.update(values)
        super().__init__(component=component, target=target, status=status_value, evidence=items, verification_level=verification_level, **defaults)
    def to_dict(self) -> dict[str, Any]:
        return dict(self)

def report(component: str, target: str, status: str | Status, evidence=None, **values: Any) -> Result:
    return Result(component=component, target=target, status=status, evidence=evidence, **values)
