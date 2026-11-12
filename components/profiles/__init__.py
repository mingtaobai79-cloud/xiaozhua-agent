from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

@dataclass
class BaseProfile:
    id: str
    status: str = "UNVERIFIED"
    evidence_refs: list[str] = field(default_factory=list)
    relations: list[dict[str, Any]] = field(default_factory=list)
    data_ids: list[str] = field(default_factory=list)
    application_id: str | None = None
    kind: str = "profile"
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class UdcPlatformProfile(BaseProfile):
    kind: str = "udc_platform"

@dataclass
class StandardProductApplicationProfile(BaseProfile):
    kind: str = "standard_product_application"

@dataclass
class CustomerUdcApplicationProfile(BaseProfile):
    kind: str = "customer_udc_application"

@dataclass
class ExtensionServiceProfile(BaseProfile):
    kind: str = "extension_service"

__all__ = ["BaseProfile", "UdcPlatformProfile", "StandardProductApplicationProfile", "CustomerUdcApplicationProfile", "ExtensionServiceProfile"]
