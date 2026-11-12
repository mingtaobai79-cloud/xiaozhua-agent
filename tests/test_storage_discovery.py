import json
from providers.nacos_readonly import NacosFixtureAdapter, NacosReadonlyProvider
from providers.storage_discovery import NacosPublicStorageDiscovery, discover_storage

def test_discover_mysql_and_metadata_location():
    result = discover_storage({"content": "spring.datasource.url=jdbc:mysql://db/app\nmetadata.location=s3://bucket/meta"})
    assert result["storage_type"] == "mysql"
    assert result["metadata_location"] == "s3://bucket/meta"
    assert result["classification"] == "PASS"

def test_discover_postgres_oracle_redis_and_object_storage():
    assert discover_storage({"url":"jdbc:postgresql://db/app"})["storage_type"] == "postgres"
    assert discover_storage({"url":"jdbc:oracle:thin:@db:1521/x"})["storage_type"] == "oracle"
    assert discover_storage({"redis.host":"redis.internal"})["storage_type"] == "redis"
    assert discover_storage({"bucket":"s3://bucket/meta"})["storage_type"] == "object-storage"

def test_discovery_does_not_assume_mysql_or_redis_when_absent():
    result = discover_storage({"feature.enabled": "true"})
    assert result["storage_type"] == "unknown"
    assert result["classification"] == "UNVERIFIED"

def test_nacos_unreachable_is_blocked_or_unverified(tmp_path):
    provider = NacosReadonlyProvider(NacosFixtureAdapter(tmp_path / "missing.json"))
    result = NacosPublicStorageDiscovery(provider).discover()
    assert result["status"] in {"BLOCKED", "UNVERIFIED"}
    assert result["storage_type"] == "unknown"
