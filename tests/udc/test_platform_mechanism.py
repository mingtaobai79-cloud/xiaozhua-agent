"""平台机制模型测试（udc-biz jar 资源固化）—— 版型/特征/权限/openAPI。

证据：docs/audit/artifacts/udc-biz-5.3.517/resources/（jar 原文，STATIC_BYTECODE）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.platform_mechanism_model import (
    features_for_stereotype, load_stereotypes, load_features,
    permission_boundary, openapi_operation_map, load_entity_event_whitelist, catalog,
)

_RES = ROOT / "docs" / "audit" / "artifacts" / "udc-biz-5.3.517" / "resources"
import pytest


def test_six_stereotypes_from_jar():
    st = load_stereotypes()
    assert set(st) == {"standard", "bill", "form", "archive", "archiveTree", "basicData"}


def test_bill_stereotype_features():
    b = features_for_stereotype("bill")
    assert b["found"] is True
    assert b["necessary_features"] == ["basic", "approve", "organization",
                                       "billBasic", "termination", "suspend", "nullify"]
    assert b["features_csv"] == "basic,approve,organization,billBasic,termination,suspend,nullify"
    assert b["attribute_sets"]["billBasic"] == "billBasic"


def test_standard_stereotype_minimal():
    s = features_for_stereotype("standard")
    assert s["features_csv"] == "basic"
    assert s["dataFlowEnabled"] is True


def test_unknown_stereotype_recorded():
    u = features_for_stereotype("bogus")
    assert u["found"] is False and u["unknowns"]


def test_permission_boundary_publish_freezes_update_delete():
    pb = permission_boundary()
    frozen = pb["frozen_on_publish"]
    for r in ("entity.update", "entity.delete", "attribute.update", "attribute.delete"):
        assert any(r in f for f in frozen), r
    # 设计态全允许
    assert pb["draft_auth"]["entity"]["update"] is True
    assert pb["deploy_auth"]["entity"]["update"] is False


def test_openapi_four_operations():
    m = openapi_operation_map()
    assert set(m) == {"创建", "删除", "更新", "查询"}
    assert m["创建"] == ["create", "createBatch", "create4bpm"]
    assert "selectPageByConditions" in m["查询"]


def test_entity_event_whitelist_has_nine():
    ev = load_entity_event_whitelist()
    assert len(ev) == 9
    assert "com.seeyon.udc.common.event.AfterCreateEvent" in ev


def test_catalog_export():
    c = catalog()
    assert len(c["stereotypes"]) == 6 and len(c["features"]) == 18
    assert c["evidence_level"] == "STATIC_BYTECODE"
