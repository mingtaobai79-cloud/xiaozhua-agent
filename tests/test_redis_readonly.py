import hashlib

import pytest

from providers.redis_readonly import RedisFixtureAdapter, RedisReadonlyProvider


def test_fixture_reads_matching_key_metadata_without_raw_values():
    provider = RedisReadonlyProvider(RedisFixtureAdapter({
        "keys": {
            "app:token": {"type": "string", "ttl": 42, "value": "super-secret-token"},
            "app:count": {"type": "string", "ttl": -1, "value": "7"},
            "other": {"type": "list", "ttl": 3, "value": ["a", "b"]},
        }
    }))
    result = provider.read(pattern="app:*")
    assert result.ok
    assert result["network"] == "disabled"
    assert [item["key"] for item in result["keys"]] == ["app:count", "app:token"]
    token = result["keys"][1]
    assert token["type"] == "string"
    assert token["ttl"] == 42
    assert token["value_summary"]["length"] == len("super-secret-token")
    assert token["value_summary"]["sha256"] == hashlib.sha256(b"super-secret-token").hexdigest()[:16]
    assert "super-secret-token" not in str(result)


def test_fixture_supports_json_file_and_missing_key_pattern(tmp_path):
    path = tmp_path / "redis.json"
    path.write_text('{"keys": [{"key": "user:1", "type": "hash", "ttl": 10, "value": {"password": "secret"}}]}', encoding="utf-8")
    result = RedisReadonlyProvider(RedisFixtureAdapter(path)).read(pattern="missing:*")
    assert result.ok
    assert result["keys"] == []
    assert result["count"] == 0


@pytest.mark.parametrize("operation", ["delete", "set", "flush", "expire", "execute"])
def test_all_redis_mutations_are_denied(operation):
    provider = RedisReadonlyProvider(RedisFixtureAdapter({"keys": {}}))
    result = getattr(provider, operation)("app:key")
    assert not result.ok
    assert result.error.kind == "permission"
    assert result["classification"] == "DENIED"
    assert result["network"] == "disabled"


def test_network_is_disabled_even_when_live_access_is_requested():
    provider = RedisReadonlyProvider(RedisFixtureAdapter({"keys": {}}), allow_network=True)
    assert provider.network == "disabled"
    assert provider.allow_network is False
    assert provider.read(pattern="*")["network"] == "disabled"
