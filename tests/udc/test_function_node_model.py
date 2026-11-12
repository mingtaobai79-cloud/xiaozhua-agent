"""菜单功能节点模型测试（page-menu-source-audit.md §2.2/§3.4/§6 证据）。"""
from components.udc.function_node_model import (
    FUNCTION_ENDPOINTS,
    FunctionNode,
    FunctionTree,
    menu_duplication_key,
)


def test_controller_paths_literal_not_gateway_prefixed():
    for p in FUNCTION_ENDPOINTS.values():
        assert p.split(" ")[1].startswith("/udc/function")
        assert "/service/" not in p


def test_page_node_requires_relation_and_resource():
    n = FunctionNode(node_id="p1", node_type="PAGE", app_id="8704")
    r = n.validate()
    assert r["status"] == "FAIL"
    assert any("relationId" in e for e in r["errors"])
    assert any("resourceId" in e for e in r["errors"])
    assert any("url" in e for e in r["errors"])


def test_complete_page_node_passes():
    n = FunctionNode(node_id="p1", parent_id="m1", node_type="PAGE", app_id="8704",
                     url="orderlist", resource_id="pg1", relation_id="g1")
    r = n.validate()
    assert r["status"] == "PASS"


def test_menu_node_without_relation_ok():
    n = FunctionNode(node_id="m1", node_type="MENU", app_id="8704", name="订单管理")
    r = n.validate()
    # MENU 节点不要求 relationId/resourceId（那是 PAGE 引用）
    assert r["status"] == "UNVERIFIED"   # 无 parentId 警告挂根
    assert not any("relationId" in e for e in r["errors"])


def test_bad_node_type_fails():
    n = FunctionNode(node_id="x", node_type="PORTLET", app_id="8704",
                     resource_id="r", relation_id="g", url="u")
    assert any("PORTLET" in e for e in n.validate()["errors"])


def test_tree_default_page_must_be_direct_child_of_menu():
    menu = FunctionNode(node_id="m1", node_type="MENU", app_id="8704", name="组")
    other_page = FunctionNode(node_id="p2", parent_id="p9", node_type="PAGE", app_id="8704",
                              url="x", resource_id="pg2", relation_id="g2")
    t = FunctionTree(nodes=[menu, other_page])
    # p9 不在树内 → 警告；无默认页 → 不报错
    assert t.validate()["status"] in {"UNVERIFIED", "PASS"}


def test_subpage_cannot_be_default_page():
    menu = FunctionNode(node_id="m1", node_type="MENU", app_id="8704", name="组")
    sub = FunctionNode(node_id="sp1", parent_id="m1", node_type="PAGE", app_id="8704",
                       url="sub", resource_id="pg", relation_id="g",
                       page_type="SUBPAGE", is_default_page=True)
    r = FunctionTree(nodes=[menu, sub]).validate()
    assert r["status"] == "FAIL"
    assert any("SUBPAGE" in e for e in r["errors"])


def test_default_page_parent_must_be_menu():
    parent_page = FunctionNode(node_id="p1", node_type="PAGE", app_id="8704",
                               url="host", resource_id="pg1", relation_id="g1")
    child = FunctionNode(node_id="p2", parent_id="p1", node_type="PAGE", app_id="8704",
                         url="c", resource_id="pg2", relation_id="g2", is_default_page=True)
    r = FunctionTree(nodes=[parent_page, child]).validate()
    assert any("≠MENU" in e or "直接子" in e for e in r["errors"])


def test_duplicate_node_ids_fails():
    t = FunctionTree(nodes=[
        FunctionNode(node_id="dup", node_type="MENU", app_id="8704", name="a"),
        FunctionNode(node_id="dup", node_type="MENU", app_id="8704", name="b"),
    ])
    assert any("重复" in e for e in t.validate()["errors"])


def test_menu_duplication_key_shape():
    n = FunctionNode(node_id="m", node_type="MENU", app_id="8704", name="订单",
                     parent_id="root", terminal_type="PC")
    assert menu_duplication_key(n) == ("订单", "PC", "MENU", "root", "8704")
