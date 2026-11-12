from __future__ import annotations

from typing import Any


class PolicyGate:
    """Fail-closed policy for the current read-only phase."""

    MUTATING_ACTIONS = frozenset({"create", "save", "publish", "deploy", "restart", "delete", "exec", "apply", "patch"})
    MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
    READ_METHODS = frozenset({"GET", "HEAD"})

    def __init__(self, *, network_enabled: bool = False):
        self.network_enabled = network_enabled

    def evaluate(self, action: str, *, provider: str | None = None, method: str | None = None, **_: Any) -> dict[str, Any]:
        action = str(action).strip().lower()
        method = str(method).strip().upper() if method else None
        if action in self.MUTATING_ACTIONS or method in self.MUTATING_METHODS:
            return {"allowed": False, "status": "DENIED", "action": action, "reason": "mutating operation is disabled"}
        if provider == "kubernetes" and action in {"exec", "apply", "patch", "delete"}:
            return {"allowed": False, "status": "DENIED", "action": action, "reason": "kubernetes mutation is disabled"}
        if action == "http_request" and method not in self.READ_METHODS:
            return {"allowed": False, "status": "DENIED", "action": action, "reason": "only GET/HEAD are read-only"}
        if action == "http_request" and not self.network_enabled:
            return {"allowed": False, "status": "BLOCKED", "action": action, "reason": "network access is disabled"}
        return {"allowed": True, "status": "ALLOWED", "action": action}
