"""Gateway 服务发现结果模型与只读解析。"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .models import GatewayRoute


class GatewayDiscovery:
    """根据 Nacos/服务发现实例生成 Gateway 路由证据。"""

    def __init__(self, *, route_id_prefix: str = "xiaozhua-", url_expression: str = "http://{host}:{port}"):
        self.route_id_prefix = route_id_prefix
        self.url_expression = url_expression

    def routes_from_instances(self, instances: Iterable[Mapping[str, Any]]) -> list[GatewayRoute]:
        routes: list[GatewayRoute] = []
        for instance in instances:
            if instance.get("enabled") is False or instance.get("healthy") is False:
                continue
            service = str(instance.get("serviceName") or instance.get("serviceId") or "").strip()
            if not service:
                continue
            host, port = instance.get("ip") or instance.get("host"), instance.get("port")
            uri = self.url_expression.format(host=host, port=port) if host and port else None
            metadata = instance.get("metadata") if isinstance(instance.get("metadata"), Mapping) else {}
            routes.append(GatewayRoute(service=service, uri=uri, route_id=self.route_id_prefix + service, metadata=dict(metadata), evidence=("Nacos instance", "enabled && healthy")))
        return routes

    def route_from_service(self, service: str, *, host: str | None = None, port: int | str | None = None, metadata: Mapping[str, Any] | None = None) -> GatewayRoute:
        uri = self.url_expression.format(host=host, port=port) if host and port else None
        return GatewayRoute(service=service, uri=uri, route_id=self.route_id_prefix + service, metadata=dict(metadata or {}), evidence=("explicit service discovery result",))


__all__ = ["GatewayDiscovery"]
