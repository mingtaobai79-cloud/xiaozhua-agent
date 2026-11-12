"""LIVE 写链模板测试（datamigration 实验实证）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.live_write_templates import (
    WRITE_TEMPLATES, ATTR_TYPE_MATRIX, READ_TEMPLATES, VALIDATION_RULES, template, build_order,
    SCHEMA_ID, EVIDENCE)


def test_ten_templates():
    assert len(WRITE_TEMPLATES) == 20
    for name, t in WRITE_TEMPLATES.items():
        assert t["channel"] in ("rest", "graphql"), name
        assert t.get("verified"), name


def test_channels_split():
    rest = [k for k, v in WRITE_TEMPLATES.items() if v["channel"] == "rest"]
    gql = [k for k, v in WRITE_TEMPLATES.items() if v["channel"] == "graphql"]
    assert set(rest) == {"entity_create", "entity_update", "attribute_update", "attribute_create_text",
                         "attribute_create_ctpenum", "enum_create",
                         "enum_item_create", "index_create", "page_create", "attribute_create_members",
                         "page_schema_draft", "page_schema_formal"}
    assert set(gql) == {"menu_create", "microflow_create", "microflow_update", "microflow_update_dataSchema",
                        "microflow_business_event_trigger", "microflow_schedule_trigger",
                        "microflow_service_create", "microflow_activity_node"}


def test_rest_paths_verified_live():
    assert WRITE_TEMPLATES["entity_create"]["path"] == "/service/udc/entity"
    # 页面路径带 page-info 前缀（拼接 bug 实证）
    assert WRITE_TEMPLATES["page_create"]["path"] == "/service/udc/page-info/base-info/create"


def test_graphql_ops():
    assert WRITE_TEMPLATES["menu_create"]["op"] == "udcFunctionPost"
    assert WRITE_TEMPLATES["microflow_create"]["op"] == "udcMicroflowCreatePost"
    assert "mutation" in WRITE_TEMPLATES["menu_create"]["gql"]


def test_page_constraints_menu_first():
    pc = WRITE_TEMPLATES["page_create"]
    assert any("menuId" in c for c in pc["constraints"])
    assert any("page-info" in c for c in pc["constraints"])


def test_build_order_dependency_valid():
    order = build_order()
    assert order.index("menu_create") < order.index("page_create")
    assert order.index("enum_create") < order.index("enum_item_create")
    assert order.index("enum_item_create") < order.index("attribute_create_ctpenum")
    assert order.index("entity_create") < order.index("attribute_create_text")


def test_read_templates_and_rules():
    assert len(READ_TEMPLATES) >= 9
    assert len(VALIDATION_RULES) >= 6
