import json

import pytest

from components.gateway.client import GatewayReadonlyClient
from components.gateway.models import GatewayRequest


def test_gateway_request_rejects_write_methods():
    # 只读白名单 = GET + 只读 POST；写方法 PUT/PATCH/DELETE 仍拒。
    for write_method in ("PUT", "PATCH", "DELETE"):
        with pytest.raises(ValueError, match="read-only"):
            GatewayRequest(method=write_method, path="/udc/graphql")


def test_gateway_request_allows_readonly_post():
    # xiaozhua UDC 只读端点（/udc-runtime/meta-data/*）业务上写=False 但 HTTP 方法为 POST。
    req = GatewayRequest(method="POST", path="/udc/graphql", query="query { health }")
    assert req.method == "POST"


def test_gateway_client_builds_sanitized_get_evidence_without_network():
    client = GatewayReadonlyClient(base_url="https://gateway.test", allow_network=False)
    result = client.get("/udc/entity/1", headers={"Authorization": "Bearer secret"})

    assert result["classification"] == "BLOCKED"
    assert result["request"]["method"] == "GET"
    assert result["request"]["url"] == "https://gateway.test/udc/entity/1"
    assert result["request"]["headers"]["Authorization"] == "<REDACTED>"
    assert result.error.kind == "unavailable"


def test_gateway_client_normalizes_readonly_http_response():
    class FakeResponse:
        status = 200
        headers = {"Content-Type": "application/json", "Set-Cookie": "token=secret"}

        def read(self, n=-1):
            return json.dumps({"data": {"id": 1}, "token": "secret"}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class FakeOpener:
        def open(self, request, timeout):
            assert request.method == "GET"
            assert request.full_url == "https://gateway.test/udc/entity/1"
            return FakeResponse()

    client = GatewayReadonlyClient(base_url="https://gateway.test", allow_network=True, opener=FakeOpener())
    result = client.get("/udc/entity/1")

    assert result.ok
    assert result["classification"] == "PASS"
    assert result["response"]["status"] == 200
    assert result["response"]["body"]["data"]["id"] == 1
    assert result["response"]["body"]["token"] == "<REDACTED>"


def test_gateway_client_allows_readonly_post_when_network_enabled():
    # 只读 POST（xiaozhua UDC 端点）已放行：网络开时不再 ValueError；
    # 请求带 body 且不触发写方法拒绝。写方法仍由 GatewayRequest 白名单拦。
    class FakeOpener:
        def __init__(self):
            self.captured = None
        def open(self, request, timeout):
            self.captured = request
            class _Resp:
                status = 200
                headers = {}
                def read(self, n=-1):
                    return json.dumps({"status": 0, "code": "BOOT_0000", "data": {"content": [1]}}).encode()
                def __enter__(self): return self
                def __exit__(self, *a): return False
            return _Resp()
    opener = FakeOpener()
    client = GatewayReadonlyClient(base_url="https://gateway.test", allow_network=True, opener=opener)
    result = client.post("/service/x/udc-runtime/meta-data/check-page-exists",
                         body={"pageExistsDtoList": [{"id": 1}]}, headers={"Cookie": "c=1"})
    assert result.ok
    assert result["classification"] == "PASS"
    assert opener.captured.method == "POST"
    assert opener.captured.data is not None  # body 已序列化
