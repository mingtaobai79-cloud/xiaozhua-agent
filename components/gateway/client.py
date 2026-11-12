"""Gateway 只读 HTTP 客户端。"""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from typing import Any

from core.providers import ProviderError, ProviderResult
from .models import GatewayRequest


_SENSITIVE = {"authorization", "cookie", "set-cookie", "token", "password", "secret", "access-key", "private-key"}


def _redact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): ("<REDACTED>" if str(k).lower() in _SENSITIVE or any(x in str(k).lower() for x in ("token", "password", "secret", "credential")) else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    if isinstance(value, tuple):
        return [_redact(v) for v in value]
    return value


def _join_url(base_url: str, path: str, query: Mapping[str, Any] | None = None) -> str:
    url = base_url.rstrip("/") + path
    if query:
        encoded = urllib.parse.urlencode([(str(k), str(v)) for k, v in query.items() if v is not None])
        if encoded:
            url += ("&" if "?" in url else "?") + encoded
    return url


class GatewayReadonlyClient:
    """只允许 GET 的 Gateway 客户端，默认不联网。"""

    def __init__(self, *, base_url: str, allow_network: bool = False, timeout: float = 15.0, opener: Any = None, body_limit: int = 2 * 1024 * 1024):
        self.base_url = base_url.rstrip("/")
        self.allow_network = allow_network
        self.timeout = timeout
        self.opener = opener or urllib.request.build_opener()
        self.body_limit = body_limit

    def request(self, method: str, path: str, *, query: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None, body: Any = None) -> ProviderResult[dict[str, Any]]:
        request_model = GatewayRequest(method=method, path=path, query=query, headers=headers or {})
        url = _join_url(self.base_url, request_model.path, request_model.query)
        method_up = request_model.method.upper()
        payload: bytes | None = None
        if method_up != "GET" and body is not None:
            payload = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            method_headers = {"Content-Type": "application/json", **dict(request_model.headers)}
        else:
            method_headers = dict(request_model.headers)
        request_evidence = {"method": method_up, "url": url, "headers": _redact(method_headers), "query": _redact(dict(request_model.query or {}))}
        result: dict[str, Any] = {"classification": "UNVERIFIED", "request": request_evidence, "response": None}
        if not self.allow_network:
            result["classification"] = "BLOCKED"
            return ProviderResult(result, error=ProviderError("unavailable", "Gateway network access is disabled", {"allow_network": False}))
        request = urllib.request.Request(url, headers=method_headers, method=method_up, data=payload)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                status = int(getattr(response, "status", None) or response.getcode())
                raw = response.read(self.body_limit)
                result["response"] = self._response(status, dict(response.headers.items()), raw)
                result["classification"] = self._classify(status)
                return ProviderResult(result, error=self._status_error(status))
        except urllib.error.HTTPError as exc:
            raw = exc.read(self.body_limit) if hasattr(exc, "read") else b""
            result["response"] = self._response(exc.code, dict(exc.headers.items()) if exc.headers else {}, raw)
            result["classification"] = self._classify(exc.code)
            return ProviderResult(result, error=self._status_error(exc.code) or ProviderError("unavailable", str(exc)))
        except (TimeoutError, socket.timeout) as exc:
            result["classification"] = "TIMEOUT"
            return ProviderResult(result, error=ProviderError("timeout", str(exc)))
        except (urllib.error.URLError, OSError) as exc:
            return ProviderResult(result, error=ProviderError("unavailable", str(exc)))

    def get(self, path: str, *, query: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None) -> ProviderResult[dict[str, Any]]:
        return self.request("GET", path, query=query, headers=headers)

    def post(self, path: str, *, body: Any = None, headers: Mapping[str, str] | None = None) -> ProviderResult[dict[str, Any]]:
        return self.request("POST", path, headers=headers, body=body)

    def graphql_query(self, path: str, query: str, *, variables: Mapping[str, Any] | None = None, headers: Mapping[str, str] | None = None) -> ProviderResult[dict[str, Any]]:
        params = {"query": query}
        if variables:
            params["variables"] = json.dumps(dict(variables), ensure_ascii=False, separators=(",", ":"))
        return self.get(path, query=params, headers=headers)

    @staticmethod
    def _classify(status: int) -> str:
        if 200 <= status < 300:
            return "PASS"
        if status in {401, 403}:
            return "BLOCKED"
        if status == 404:
            return "UNVERIFIED"
        return "FAIL"

    @staticmethod
    def _status_error(status: int) -> ProviderError | None:
        kind = {401: "auth", 403: "permission", 404: "not_found"}.get(status)
        return ProviderError(kind, f"Gateway HTTP status {status}") if kind else None

    @staticmethod
    def _response(status: int, headers: Mapping[str, Any], raw: bytes) -> dict[str, Any]:
        text = raw.decode("utf-8", errors="replace")
        try:
            body: Any = json.loads(text) if text else None
        except (TypeError, ValueError):
            body = text
        return {"status": status, "headers": _redact(dict(headers)), "body": _redact(body)}


__all__ = ["GatewayReadonlyClient"]
