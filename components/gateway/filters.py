"""Gateway 过滤器的只读证据模型。"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any


FILTER_CLASSES = {
    "strip_prefix": "com.seeyon.ctp.webapi.gateway.filter.SeeyonStripPrefixGatewayFilterFactory",
    "process_header": "com.seeyon.ctp.webapi.gateway.filter.ProcessHeaderGatewayFilterFactory",
    "signature": "com.seeyon.ctp.webapi.gateway.filter.SignVerificationFilter",
    "request_time": "com.seeyon.ctp.webapi.gateway.filter.RequestTimeFilter",
    "csrf": "com.seeyon.ctp.webapi.gateway.filter.CtpCsrfFilter",
    "response": "com.seeyon.ctp.webapi.gateway.filter.TongWebResponseFilter",
}


def normalize_filter_evidence(filters: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """合并已知类名和运行时采集值，不对未知 Header 做推断。"""
    result = {name: {"class": fqcn, "observed": False, "details": {}} for name, fqcn in FILTER_CLASSES.items()}
    for name, value in (filters or {}).items():
        if name not in result:
            continue
        result[name]["observed"] = True
        result[name]["details"] = dict(value) if isinstance(value, Mapping) else {"value": value}
    return result


__all__ = ["FILTER_CLASSES", "normalize_filter_evidence"]
