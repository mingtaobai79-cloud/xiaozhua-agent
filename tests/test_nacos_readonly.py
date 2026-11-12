import json

from providers.nacos_readonly import NacosFixtureAdapter, NacosReadonlyProvider


def test_nacos_fixture_query_matches_data_id_group_and_namespace(tmp_path):
    fixture = tmp_path / "nacos.json"
    fixture.write_text(json.dumps({"configs": [
        {"dataId": "app.yaml", "group": "DEFAULT_GROUP", "namespace": "dev", "content": "a: 1"},
        {"dataId": "app.yaml", "group": "DEFAULT_GROUP", "namespace": "prod", "content": "a: 2"},
    ]}), encoding="utf-8")
    result = NacosReadonlyProvider(NacosFixtureAdapter(fixture)).get_config(
        data_id="app.yaml", group="DEFAULT_GROUP", namespace="dev")
    assert result.ok
    assert result["content"] == "a: 1"
    assert result["dataId"] == "app.yaml"
    assert result["group"] == "DEFAULT_GROUP"
    assert result["namespace"] == "dev"
    assert result["network"] == "disabled"


def test_nacos_fixture_missing_config_is_classified_not_found(tmp_path):
    fixture = tmp_path / "nacos.json"
    fixture.write_text('{"configs": []}', encoding="utf-8")
    result = NacosReadonlyProvider(NacosFixtureAdapter(fixture)).get_config(
        data_id="missing", group="DEFAULT_GROUP", namespace="dev")
    assert not result.ok
    assert result.error.kind == "not_found"
    assert result["classification"] == "UNVERIFIED"


def test_nacos_fixture_malformed_json_is_classified_parse(tmp_path):
    fixture = tmp_path / "nacos.json"
    fixture.write_text("{not-json", encoding="utf-8")
    result = NacosReadonlyProvider(NacosFixtureAdapter(fixture)).get_config(
        data_id="app.yaml", group="DEFAULT_GROUP", namespace="dev")
    assert not result.ok
    assert result.error.kind == "parse"


def test_nacos_fixture_permission_error_is_classified_permission(tmp_path):
    fixture = tmp_path / "nacos.json"
    fixture.write_text(json.dumps({"configs": [{
        "dataId": "secret.yaml", "group": "DEFAULT_GROUP", "namespace": "dev",
        "error": {"kind": "permission", "message": "access denied"},
    }]}), encoding="utf-8")
    result = NacosReadonlyProvider(NacosFixtureAdapter(fixture)).get_config(
        data_id="secret.yaml", group="DEFAULT_GROUP", namespace="dev")
    assert not result.ok
    assert result.error.kind == "permission"
    assert result["classification"] == "BLOCKED"


def test_nacos_provider_is_offline_and_rejects_all_mutations(tmp_path):
    fixture = tmp_path / "nacos.json"
    fixture.write_text('{"configs": []}', encoding="utf-8")
    provider = NacosReadonlyProvider(NacosFixtureAdapter(fixture))
    assert provider.network == "disabled"
    assert provider.capabilities() == ["get"]
    for operation in ("publish", "update", "delete"):
        result = getattr(provider, operation)("app.yaml", "DEFAULT_GROUP", "dev", "x")
        assert not result.ok
        assert result.error.kind == "permission"
        assert result["classification"] == "DENIED"
        assert result["operation"] == operation


def test_nacos_provider_defaults_to_no_network(tmp_path):
    fixture = tmp_path / "nacos.json"
    fixture.write_text('{"configs": []}', encoding="utf-8")
    provider = NacosReadonlyProvider(NacosFixtureAdapter(fixture))
    assert provider.allow_network is False
    assert not hasattr(provider, "client")
