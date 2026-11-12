"""外框/子页面/复制上下文模型测试（page-menu-source-audit §7 + SETTINGS §2/§3.11 证据）。"""
from components.udc.layout_model import (
    LAYOUT_ENDPOINTS,
    LAYOUT_INSTANCE_TABLE,
    LAYOUT_TEMPLATE_TABLE,
    PAGE_INFO_NO_LAYOUT,
    PAGE_TYPES,
    PUBLISH_STATES,
    PageCopyContext,
    PageLayout,
    PageLayoutItem,
    SubPageConstraint,
)


def test_page_types_include_layout_and_subpage():
    assert "LAYOUT" in PAGE_TYPES and "SUBPAGE" in PAGE_TYPES
    assert PUBLISH_STATES == {"PUBLISHED", "UNPUBLISH", "ON_SHELF", "RELEASE"}


def test_controller_paths_literal():
    for p in LAYOUT_ENDPOINTS.values():
        assert p.split(" ")[1].startswith("/udc/page-layout")
        assert "/service/" not in p


def test_layout_template_vs_instance_tables():
    # 写错表=0 行（本仓踩过的坑，固化防回归）
    assert LAYOUT_TEMPLATE_TABLE == "udc_page_template_published"
    assert LAYOUT_INSTANCE_TABLE == "udc_page_layout"
    assert PAGE_INFO_NO_LAYOUT is True


def test_empty_items_rejected():
    r = PageLayout(layout_id="L1", app_id="8704").validate()
    assert r["status"] == "FAIL"
    assert any("item" in e for e in r["errors"])


def test_duplicate_page_url_rejected():
    layout = PageLayout(layout_id="L1", app_id="8704", items=[
        PageLayoutItem(terminal_type="PC", page_url="dup"),
        PageLayoutItem(terminal_type="MOBILE", page_url="dup"),
    ])
    r = layout.validate()
    assert any("重复" in e for e in r["errors"])


def test_valid_layout_passes():
    layout = PageLayout(layout_id="L1", app_id="8704", items=[
        PageLayoutItem(terminal_type="PC", page_url="mylayout")])
    r = layout.validate()
    assert r["status"] == "PASS"


def test_bad_terminal_and_action_rejected():
    layout = PageLayout(layout_id="L1", app_id="8704", items=[
        PageLayoutItem(terminal_type="WATCH", page_url="x", action_type="FROB")])
    errs = layout.validate()["errors"]
    assert any("WATCH" in e for e in errs)
    assert any("FROB" in e for e in errs)


def test_subpage_three_hard_constraints():
    c = SubPageConstraint(layout_id="validLayoutId123", layout_info="otherAppFrame",
                          out_parameters='[{"name":"p"}]')
    v = c.violations(page_type="SUBPAGE")
    assert len(v) == 3
    assert any("外框" in x for x in v) and any("outParameters" in x for x in v)


def test_subpage_constraints_not_applied_to_normal_page():
    c = SubPageConstraint(layout_id="validLayoutId123")
    assert c.violations(page_type="DETAIL") == []


def test_subpage_null_layout_id_ok():
    c = SubPageConstraint(layout_id="0", layout_info="", out_parameters="[]")
    assert c.violations(page_type="SUBPAGE") == []


def test_copy_context_requires_app_refs():
    ctx = PageCopyContext()
    assert ctx.validate()["status"] == "FAIL"


def test_copy_context_warns_on_missing_microflow_mapping():
    ctx = PageCopyContext(source_app_name="a8704", new_app_id="9999",
                          copied_schema='{"nodes":["mf_old_id"]}')
    r = ctx.validate()
    assert r["status"] == "UNVERIFIED"
    assert any("idReplace" in w for w in r["warnings"])


def test_copy_context_with_mapping_passes():
    ctx = PageCopyContext(source_app_name="a", new_app_id="b",
                          function_microflow_mapping={"old1": "new1"},
                          copied_schema="{}")
    assert ctx.validate()["status"] == "PASS"
