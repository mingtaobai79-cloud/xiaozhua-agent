"""Gateway 只读访问的数据模型。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


_ALLOWED_METHODS = frozenset({"GET", "POST"})
# GET=标准只读；POST=xiaozhua UDC 只读端点的 HTTP 方法（如 /udc-runtime/meta-data/*），
# 业务只读语义由 PlatformOperationLayer 契约(write=False)+调用方保证，非写方法。
# 写方法 PUT/PATCH/DELETE 仍拒。


@dataclass(frozen=True)
class GatewayRequest:
    """表示一个只能读取的 Gateway 请求。"""

    method: str
    path: str
    query: Mapping[str, Any] | None = None
    headers: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        method = self.method.upper()
        if method not in _ALLOWED_METHODS:
            raise ValueError(f"read-only gateway does not allow method {method}")
        if not self.path.startswith("/"):
            raise ValueError("gateway path must start with '/'")
        object.__setattr__(self, "method", method)


@dataclass(frozen=True)
class GatewayRoute:
    """Gateway 路由及其服务发现证据。"""

    service: str
    uri: str | None = None
    route_id: str | None = None
    path: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    evidence: tuple[str, ...] = ()


__all__ = ["GatewayRequest", "GatewayRoute"]
