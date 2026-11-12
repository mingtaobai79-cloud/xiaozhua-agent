"""Explicitly opt-in, read-only HTTP live adapter."""
from __future__ import annotations

import socket
import urllib.error
import urllib.request
from typing import Any

from core.providers import ProviderError, ProviderResult, ReadOnlyHttpProvider


class HttpReadonlyProvider(ReadOnlyHttpProvider):
    """Perform only GET/HEAD requests, with network access disabled by default."""

    def __init__(self, *, allow_network: bool = False, timeout: float = 10.0, opener: Any = None, body_prefix_limit: int = 4096):
        self.allow_network = allow_network
        self.timeout = timeout
        self.opener = opener or urllib.request.build_opener()
        self.body_prefix_limit = body_prefix_limit

    def request(self, method: str, url: str) -> ProviderResult:
        method = method.upper()
        result = {"method": method, "url": url, "status": None, "headers": {}, "body_prefix": "", "classification": "UNVERIFIED"}
        if method not in {"GET", "HEAD"}:
            raise ValueError(f"HTTP method {method} is not allowed by read-only provider")
        if not self.allow_network:
            result["classification"] = "BLOCKED"
            return ProviderResult(result, error=ProviderError("unavailable", "network access is disabled", {"allow_network": False}))
        request = urllib.request.Request(url, method=method)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                status = getattr(response, "status", None) or response.getcode()
                headers = dict(response.headers.items())
                body = b"" if method == "HEAD" else response.read()[:self.body_prefix_limit]
                result.update(status=status, headers=headers, body_prefix=body.decode("utf-8", errors="replace"), classification=self.classify_status(status))
                return ProviderResult(result, error=_status_error(status, url))
        except urllib.error.HTTPError as exc:
            result.update(status=exc.code, headers=dict(exc.headers.items()) if exc.headers else {}, classification=self.classify_status(exc.code))
            return ProviderResult(result, error=_status_error(exc.code, url) or ProviderError("unavailable", str(exc)))
        except (TimeoutError, socket.timeout) as exc:
            result["classification"] = "TIMEOUT"
            return ProviderResult(result, error=ProviderError("timeout", str(exc)))
        except (urllib.error.URLError, OSError) as exc:
            return ProviderResult(result, error=ProviderError("unavailable", str(exc)))


def _status_error(status: int, url: str) -> ProviderError | None:
    kind = {401: "auth", 403: "permission", 404: "not_found"}.get(status)
    return ProviderError(kind, f"HTTP status {status}", {"url": url}) if kind else None
