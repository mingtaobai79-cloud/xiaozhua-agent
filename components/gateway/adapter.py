"""Gateway 只读适配器，认证只在单次请求生命周期内存在。"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.providers import ProviderError, ProviderResult
from .client import GatewayReadonlyClient
from .credentials import CredentialProvider
from .discovery import GatewayDiscovery
from components.platform_operations.models import AuthContext


class GatewayAdapter:
    """把 Gateway 客户端结果包装为 Agent operation evidence。"""

    def __init__(self, client: GatewayReadonlyClient, *, gateway_name: str, credential_provider: CredentialProvider | None = None, discovery: GatewayDiscovery | None = None):
        self.client = client
        self.gateway_name = gateway_name
        self.credential_provider = credential_provider
        self.discovery = discovery or GatewayDiscovery()

    def read(self, operation: str, path: str, *, auth_context: AuthContext | None = None, query: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None, service: str | None = None, route: str | None = None) -> ProviderResult[dict[str, Any]]:
        if auth_context is None:
            return self._blocked(operation, path, service, route, "missing execution authentication context", "MISSING_EXECUTION_CONTEXT")
        if self.credential_provider is None:
            return self._blocked(operation, path, service, route, "credential provider is unavailable", "CREDENTIAL_RESOLUTION_FAILED")
        try:
            resolved = dict(self.credential_provider.resolve(auth_context))
        except (LookupError, RuntimeError, ValueError) as exc:
            return self._blocked(operation, path, service, route, str(exc), "CREDENTIAL_RESOLUTION_FAILED")
        merged_headers = {**resolved, **dict(headers or {})}
        result = self.client.get(path, query=query, headers=merged_headers)
        return self._evidence(operation, path, auth_context, result, service, route)

    def _evidence(self, operation, path, auth_context, result, service, route):
        evidence = {"operation": operation, "mode": "readonly", "gateway": self.gateway_name, "service": service, "path": path, "route": route, "auth_present": True, "auth_scheme": self._auth_scheme(result), "credential_ref": "<REDACTED-ID>", "request": result.get("request"), "response": result.get("response"), "verified": bool(result.ok and result.get("classification") == "PASS")}
        if result.error:
            evidence["error"] = {"kind": result.error.kind, "message": result.error.message}
        return ProviderResult(evidence, error=result.error)

    @staticmethod
    def _auth_scheme(result):
        headers = result.get("request", {}).get("headers", {}) if isinstance(result.get("request"), dict) else {}
        if "Cookie" in headers:
            return "cookie"
        if "Authorization" in headers:
            return "header"
        return "unknown"

    @staticmethod
    def _blocked(operation, path, service, route, message, kind):
        evidence = {"operation": operation, "mode": "readonly", "gateway": None, "service": service, "path": path, "route": route, "auth_present": False, "auth_scheme": "unknown", "credential_ref": "<REDACTED-ID>", "request": None, "response": None, "verified": False, "error": {"kind": kind, "message": message}}
        return ProviderResult(evidence, error=ProviderError("unavailable", message, {"error_kind": kind}))


__all__ = ["GatewayAdapter"]
