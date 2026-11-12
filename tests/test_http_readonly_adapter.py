import pytest
from core.providers import ProviderResult
from providers.http_readonly import HttpReadonlyProvider

class FakeResponse:
    status = 200
    headers = {"Content-Type": "text/plain"}
    def read(self): return b"hello"
    def __enter__(self): return self
    def __exit__(self, *args): return False

class FakeOpener:
    def __init__(self, response=None, error=None): self.response, self.error, self.calls = response, error, []
    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if self.error: raise self.error
        return self.response

def test_default_provider_disables_network_without_calling_opener():
    opener = FakeOpener(FakeResponse())
    result = HttpReadonlyProvider(opener=opener).request("GET", "https://example.test")
    assert isinstance(result, ProviderResult)
    assert result.ok is False
    assert result.error.kind == "unavailable"
    assert result["classification"] == "BLOCKED"
    assert opener.calls == []

def test_write_methods_are_rejected_before_network_access():
    opener = FakeOpener(FakeResponse())
    provider = HttpReadonlyProvider(allow_network=True, opener=opener)
    with pytest.raises(ValueError, match="read-only"):
        provider.request("POST", "https://example.test")
    assert opener.calls == []

def test_allowed_get_response_is_normalized_to_provider_result():
    opener = FakeOpener(FakeResponse())
    result = HttpReadonlyProvider(allow_network=True, opener=opener).request("GET", "https://example.test/health")
    assert isinstance(result, ProviderResult)
    assert result.ok is True
    assert result["method"] == "GET"
    assert result["url"] == "https://example.test/health"
    assert result["status"] == 200
    assert result["headers"] == {"Content-Type": "text/plain"}
    assert result["body_prefix"] == "hello"
    assert result["classification"] == "PASS"
    assert len(opener.calls) == 1

def test_timeout_is_classified_without_real_network():
    opener = FakeOpener(error=TimeoutError("timed out"))
    result = HttpReadonlyProvider(allow_network=True, opener=opener).request("HEAD", "https://example.test/health")
    assert isinstance(result, ProviderResult)
    assert result.ok is False
    assert result.error.kind == "timeout"
    assert result["classification"] == "TIMEOUT"

def test_http_error_preserves_status_and_classification():
    import urllib.error
    error = urllib.error.HTTPError("https://example.test/missing", 404, "not found", {}, None)
    result = HttpReadonlyProvider(allow_network=True, opener=FakeOpener(error=error)).request("GET", "https://example.test/missing")
    assert result.ok is False
    assert result["status"] == 404
    assert result["classification"] == "FAIL"
    assert result.error.kind == "not_found"
