"""测试：元数据域（boot-starter-metadata 5.3.358）约束模型。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.metadata_constraints import (
    METADATA_ENDPOINTS, METADATA_ENDPOINT_PATHS, METADATA_TYPES, SERVICE_STATES,
    SERVICE_METADATA_FIELDS, STARTER_METADATA_FIELDS, METADATA_ENDPOINT_COUNT,
    METADATA_OP_SURFACE_COUNT, METADATA_NO_OP_SUBS,
    find_metadata_endpoint, metadata_external_path, is_metadata_op_exposed,
    is_udc_app, is_service_published, is_graphql_enabled,
)


def test_endpoint_catalog():
    """105 个 mapping 端点（字节码直读），不再是旧的 12。"""
    assert METADATA_ENDPOINT_COUNT == 105
    assert len(METADATA_ENDPOINTS) == 105
    assert METADATA_OP_SURFACE_COUNT == 99
    assert len(METADATA_ENDPOINT_PATHS) == 105
    assert find_metadata_endpoint("metadata/service")[0] == "GET"
    assert find_metadata_endpoint("metadata/starters")[0] == "POST"
    assert find_metadata_endpoint("metadata/nope") is None


def test_endpoint_shape_and_uniqueness():
    for http, sub, handler, op in METADATA_ENDPOINTS:
        assert http in ("GET", "POST"), (sub, http)
        assert sub and sub == sub.strip("/"), sub
        assert handler, sub
    subs = [s for _h, s, _hd, _o in METADATA_ENDPOINTS]
    assert len(subs) == len(set(subs))          # 子路径唯一，无重复登记


def test_op_surface_partition():
    """99 进 op 面 + 6 不进 = 105，且两个集合恰好互补（无重叠、无遗漏）。"""
    no_op = sorted(s for _h, s, _hd, o in METADATA_ENDPOINTS if not o)
    assert no_op == sorted(METADATA_NO_OP_SUBS)
    assert sum(1 for _h, _s, _hd, o in METADATA_ENDPOINTS if o) == METADATA_OP_SURFACE_COUNT
    assert METADATA_OP_SURFACE_COUNT + len(METADATA_NO_OP_SUBS) == METADATA_ENDPOINT_COUNT
    for s in METADATA_NO_OP_SUBS:
        assert not is_metadata_op_exposed(s)
    assert is_metadata_op_exposed("entity-by-name")


def test_live_observed_route_is_registered():
    """LIVE 观测到的 /udc/metadata/app-service-by-name 必须在登记表内（发现 A 的收口）。"""
    hit = find_metadata_endpoint("/udc/metadata/app-service-by-name")
    assert hit == ("POST", "AppService.1006.查询AppService信息")
    assert metadata_external_path("app-service-by-name") == "/udc/metadata/app-service-by-name"


def test_metadata_types():
    assert len(METADATA_TYPES) == 14
    assert METADATA_TYPES["Service"] == 0
    assert METADATA_TYPES["Entity"] == 1
    assert METADATA_TYPES["Page"] == 10
    assert METADATA_TYPES["Starter"] == 11
    assert METADATA_TYPES["CtpEnumItem"] == 13


def test_service_states():
    assert SERVICE_STATES == ("PUBLISHED", "UNPUBLISHED")


def test_service_metadata_fields():
    # 语义键齐全（UDC 应用判定就靠这几个字段）
    for f in ("appName", "hostAppName", "udcApp", "enableGraphql", "status", "appVersion"):
        assert f in SERVICE_METADATA_FIELDS
    for f in ("name", "basePackage"):
        assert f in STARTER_METADATA_FIELDS


def test_semantic_predicates():
    svc = {"udcApp": True, "status": "PUBLISHED", "enableGraphql": True}
    assert is_udc_app(svc) and is_service_published(svc) and is_graphql_enabled(svc)
    # enableGraphql 默认 true（字段缺省时）
    assert is_graphql_enabled({"enableGraphql": None}) is True
    assert is_graphql_enabled({"enableGraphql": False}) is False
    assert not is_service_published({"status": "UNPUBLISHED"})
    assert not is_udc_app({"udcApp": False})
