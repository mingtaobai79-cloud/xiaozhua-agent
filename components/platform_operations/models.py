from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class OperationStatus(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"
    UNVERIFIED = "UNVERIFIED"
    FAIL = "FAIL"
    DENIED = "DENIED"
    VERIFIED_STATIC_BYTECODE = "VERIFIED_STATIC_BYTECODE"
    OBSERVED = "OBSERVED"
    UNKNOWN = "UNKNOWN"


class ErrorKind(str, Enum):
    CONNECTION_ERROR = "CONNECTION_ERROR"
    DISCOVERY_ERROR = "DISCOVERY_ERROR"
    GATEWAY_ROUTE_ERROR = "GATEWAY_ROUTE_ERROR"
    GATEWAY_AUTH_ERROR = "GATEWAY_AUTH_ERROR"
    UDC_TRANSPORT_ERROR = "UDC_TRANSPORT_ERROR"
    UDC_RESPONSE_ERROR = "UDC_RESPONSE_ERROR"
    BUSINESS_NOT_FOUND = "BUSINESS_NOT_FOUND"
    VERIFICATION_ERROR = "VERIFICATION_ERROR"
    POLICY_DENIED = "POLICY_DENIED"


@dataclass(frozen=True)
class UdcOperationContract:
    operation_id: str
    method: str
    path: str
    request_type: str
    response_type: str
    status: OperationStatus
    write: bool
    evidence: list[dict[str, Any]] = field(default_factory=list)
    required_inputs: tuple[str, ...] = ()
    verification_rules: tuple[str, ...] = ()

    @property
    def http_method(self):
        return self.method

    @property
    def effective(self) -> bool:
        return self.status in {OperationStatus.PASS, OperationStatus.VERIFIED_STATIC_BYTECODE, OperationStatus.OBSERVED} and not self.write and self.method.upper() == "GET"


@dataclass(frozen=True)
class OperationRequest:
    operation_id: str
    method: str
    path: str
    payload: Any = None
    write: bool = False
    evidence: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class OperationIntent:
    operation: str
    application_id: str
    entity_id: int | str | None = None
    entity_name: str | None = None
    mode: str = "readonly"
    context: Mapping[str, Any] = field(default_factory=dict)
    readonly: bool | None = None
    session_id: str | None = None
    run_id: str | None = None

    def __post_init__(self) -> None:
        if self.readonly is False or self.mode != "readonly":
            raise ValueError("operation intent must be readonly")
        if not self.application_id:
            raise ValueError("application_id is required")
        if self.entity_id is None and not self.entity_name and self.operation in {"udc.entity.get", "udc.attribute.list"}:
            raise ValueError("entity_id or entity_name is required")

    @property
    def target(self) -> dict[str, Any]:
        target = {"application_id": self.application_id}
        if self.entity_id is not None:
            target["entity_id"] = self.entity_id
        if self.entity_name:
            target["entity_name"] = self.entity_name
        return target


@dataclass(frozen=True)
class ExecutionContext:
    session_id: str
    run_id: str
    principal_id: str
    credential_ref: str
    auth_scope: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("session_id", "run_id", "principal_id", "credential_ref"):
            if not getattr(self, name):
                raise ValueError(f"{name} is required")

    def to_safe_dict(self) -> dict[str, Any]:
        return {"session_id": self.session_id, "run_id": self.run_id, "principal_id": self.principal_id, "credential_ref": "<REDACTED-ID>", "auth_scope": list(self.auth_scope)}


@dataclass(frozen=True)
class AuthContext:
    credential_ref: str
    principal_id: str
    scope: tuple[str, ...] = ()
    source: str = "runtime"


@dataclass(frozen=True)
class OperationResult:
    operation: str
    status: OperationStatus
    mode: str
    session_id: str | None
    run_id: str | None
    request: dict[str, Any] = field(default_factory=dict)
    response: dict[str, Any] | None = None
    normalized_data: Any = None
    verification: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    error: dict[str, Any] | None = None

    @classmethod
    def blocked(cls, operation: str, *, session_id: str | None = None, run_id: str | None = None, reason: str = ""):
        return cls(operation, OperationStatus.BLOCKED, "readonly", session_id, run_id, error={"kind": ErrorKind.CONNECTION_ERROR.value, "code": ErrorKind.CONNECTION_ERROR.value, "message": reason})

    def to_dict(self) -> dict[str, Any]:
        return {"operation": self.operation, "status": self.status.value, "mode": self.mode, "session_id": self.session_id, "run_id": self.run_id, "request": self.request, "response": self.response, "normalized_data": self.normalized_data, "verification": self.verification, "evidence": self.evidence, "unknowns": self.unknowns, "error": self.error}
