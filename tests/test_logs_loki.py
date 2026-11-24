"""components/logs/loki.py —— 全部离线（不发真实请求）。

要点：
* datasource 可以写名字（先查 /api/datasources）或数字 id（直接用）
* 不传 query 时按 namespace/app/pod/grep 拼 LogQL；给了 query 原样透传
* 凭据只来自环境变量，配置里没有密码
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from components.logs import loki  # noqa: E402


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    p = tmp_path / "logs.yaml"
    p.write_text(
        "environments:\n"
        "  test2:\n"
        "    grafana: https://grafana.example.com\n"
        "    datasource: loki-lowcode-test2\n"
        "  uat:\n"
        "    grafana: https://grafana.example.com\n"
        "    datasource: 29\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("XIAOZHUA_LOKI_CONFIG", str(p))
    monkeypatch.setenv("GRAFANA_USER", "u")
    monkeypatch.setenv("GRAFANA_PASSWORD", "p")
    monkeypatch.delenv("GRAFANA_TOKEN", raising=False)
    return p


def test_envs_listed(cfg):
    assert loki.env_names() == ["test2", "uat"]


def test_unknown_env_raises(cfg):
    with pytest.raises(loki.LokiError, match="未配置环境 nope"):
        loki.search(env="nope")


def test_datasource_by_name_resolves_id(cfg, monkeypatch):
    calls = []

    def fake_get(url, params=None):
        calls.append(url)
        if url.endswith("/api/datasources"):
            return [{"id": 13, "name": "loki-other", "type": "loki"},
                    {"id": 28, "name": "loki-lowcode-test2", "type": "loki"}]
        return {"data": {"result": []}}

    monkeypatch.setattr(loki, "_get", fake_get)
    loki.search(env="test2", minutes=1)
    assert any("proxy/28/" in c for c in calls), calls


def test_numeric_datasource_skips_listing(cfg, monkeypatch):
    calls = []

    def fake_get(url, params=None):
        calls.append(url)
        return {"data": {"result": []}}

    monkeypatch.setattr(loki, "_get", fake_get)
    loki.search(env="uat", minutes=1)
    assert all("/api/datasources/proxy/" in c for c in calls)
    assert "proxy/29/" in calls[0]


def test_selector_built_from_filters(cfg, monkeypatch):
    seen = {}

    def fake_get(url, params=None):
        seen["q"] = (params or {}).get("query")
        return {"data": {"result": []}}

    monkeypatch.setattr(loki, "_get", fake_get)
    loki.search(env="uat", namespace="lowcode-test", app="udc", pod="udc-", grep="Exception")
    assert seen["q"] == '{namespace=~"lowcode-test",app=~"udc",pod=~"udc-"} |= "Exception"'


def test_explicit_query_passthrough(cfg, monkeypatch):
    seen = {}

    def fake_get(url, params=None):
        seen["q"] = (params or {}).get("query")
        return {"data": {"result": []}}

    monkeypatch.setattr(loki, "_get", fake_get)
    loki.search(env="uat", query='{app="x"} |= "y"', app="ignored")
    assert seen["q"] == '{app="x"} |= "y"'


def test_lines_flattened_and_sorted(cfg, monkeypatch):
    def fake_get(url, params=None):
        return {"data": {"result": [
            {"stream": {"pod": "p1", "app": "udc"},
             "values": [["1700000000000000100", "older"], ["1700000000000000300", "newer"]]},
            {"stream": {"pod": "p2", "app": "udc"},
             "values": [["1700000000000000200", "middle"]]},
        ]}}

    monkeypatch.setattr(loki, "_get", fake_get)
    r = loki.search(env="uat", minutes=5, limit=10)
    assert [x["line"] for x in r["lines"]] == ["newer", "middle", "older"]
    assert r["streams"] == 2 and r["returned"] == 3


def test_limit_truncates(cfg, monkeypatch):
    def fake_get(url, params=None):
        return {"data": {"result": [
            {"stream": {"pod": "p"}, "values": [[str(1700000000000000000 + i), f"l{i}"] for i in range(10)]}
        ]}}

    monkeypatch.setattr(loki, "_get", fake_get)
    r = loki.search(env="uat", minutes=5, limit=3)
    assert r["returned"] == 3 and r["truncated"] is True


def test_missing_credentials(cfg, monkeypatch):
    monkeypatch.delenv("GRAFANA_USER")
    with pytest.raises(loki.LokiError, match="缺凭据"):
        loki.search(env="uat")


def test_token_wins_over_basic(cfg, monkeypatch):
    monkeypatch.setenv("GRAFANA_TOKEN", "tok")
    h = loki._auth_headers()
    assert h["Authorization"] == "Bearer tok"