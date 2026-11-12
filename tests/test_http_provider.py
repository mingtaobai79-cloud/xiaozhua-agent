import json

import pytest

from core.providers import JsonHttpProvider, ReadOnlyHttpProvider


def test_json_http_provider_is_read_only_and_returns_normalized_response(tmp_path):
    fixture = tmp_path / "http.json"
    fixture.write_text(json.dumps({"GET https://example.test/health": {
        "status": 200,
        "headers": {"Content-Type": "application/json"},
        "body": {"ok": True, "secret": "must-not-be-redacted-by-network"},
    }}), encoding="utf-8")

    provider = JsonHttpProvider(fixture)
    result = provider.request("GET", "https://example.test/health")

    assert issubclass(JsonHttpProvider, ReadOnlyHttpProvider)
    assert result == {
        "method": "GET", "url": "https://example.test/health", "status": 200,
        "headers": {"Content-Type": "application/json"},
        "body_prefix": json.dumps({"ok": True, "secret": "must-not-be-redacted-by-network"}, separators=(",", ":")),
        "classification": "PASS",
    }


def test_json_http_provider_never_falls_back_to_network_for_missing_fixture(tmp_path):
    result = JsonHttpProvider(tmp_path / "missing.json").request("POST", "https://example.test/write")
    assert result["method"] == "POST"
    assert result["url"] == "https://example.test/write"
    assert result["status"] is None
    assert result["classification"] == "UNVERIFIED"
    assert "body_prefix" in result


@pytest.mark.parametrize("status, expected", [(200, "PASS"), (302, "UNVERIFIED"), (400, "FAIL"), (401, "BLOCKED"), (403, "BLOCKED"), (404, "FAIL"), (500, "FAIL")])
def test_http_status_classification(status, expected):
    assert ReadOnlyHttpProvider.classify_status(status) == expected


def test_json_http_provider_preserves_fixture_error_classification(tmp_path):
    fixture = tmp_path / "http.json"
    fixture.write_text(json.dumps({"GET /timeout": {"error": "timeout"}, "GET /denied": {"status": 403}, "GET /invalid": {"error": "invalid json"}}), encoding="utf-8")
    provider = JsonHttpProvider(fixture)
    assert provider.request("GET", "/timeout")["classification"] == "TIMEOUT"
    assert provider.request("GET", "/denied")["classification"] == "BLOCKED"
    assert provider.request("GET", "/invalid")["classification"] == "UNVERIFIED"


def test_probe_summary_accepts_http_provider_contract(tmp_path):
    fixture = tmp_path / "http.json"
    fixture.write_text(json.dumps({"GET /health": {"status": 200, "headers": {"X-Test": "yes"}, "body": "ok"}}), encoding="utf-8")
    from components.probe_summary import build_probe_summary
    result = build_probe_summary(http_provider=JsonHttpProvider(fixture), http_requests=[("GET", "/health")])
    item = next(x for x in result["facts"] if x["label"] == "GET /health")
    assert item["method"] == "GET"
    assert item["url"] == "/health"
    assert item["status"] == 200
    assert item["body_prefix"] == "ok"


def test_provider_result_exposes_structured_not_found_error_without_losing_http_fields(tmp_path):
    from core.providers import ProviderResult
    fixture = tmp_path / "http.json"
    fixture.write_text(json.dumps({}), encoding="utf-8")
    result = JsonHttpProvider(fixture).request("GET", "/missing")
    assert isinstance(result, ProviderResult)
    assert result.ok is False
    assert result.error.kind == "not_found"
    assert result["method"] == "GET"
    assert result["classification"] == "UNVERIFIED"


def test_json_http_provider_maps_fixture_auth_permission_and_parse_errors(tmp_path):
    fixture = tmp_path / "http.json"
    fixture.write_text(json.dumps({
        "GET /auth": {"status": 401},
        "GET /permission": {"status": 403},
        "GET /parse": {"error": "invalid json"},
    }), encoding="utf-8")
    provider = JsonHttpProvider(fixture)
    assert provider.request("GET", "/auth").error.kind == "auth"
    assert provider.request("GET", "/permission").error.kind == "permission"
    assert provider.request("GET", "/parse").error.kind == "parse"


def test_json_http_provider_returns_unavailable_for_unreadable_fixture(tmp_path):
    result = JsonHttpProvider(tmp_path / "missing.json").request("GET", "/health")
    assert result.ok is False
    assert result.error.kind == "unavailable"
