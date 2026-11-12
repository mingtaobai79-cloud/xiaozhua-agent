"""测试：菜单/功能节点域约束（后端权威）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.menu_constraints import (
    FUNCTION_NODE_REQUIRED, FUNCTION_NODE_FIELDS, NODE_TYPES, OPEN_STATES,
    PAGE_SCHEMA_STATES, FUNCTION_TAGS, FUNCTION_NODE_TABLE, validate_function_node,
)


def test_function_node_required():
    assert set(FUNCTION_NODE_REQUIRED) == {"appId", "terminalType", "type", "name"}


def test_function_node_name_length():
    assert FUNCTION_NODE_FIELDS["name"][3] == 64
    assert FUNCTION_NODE_FIELDS["url"][3] == 500
    assert FUNCTION_NODE_FIELDS["icon"][3] == 100


def test_node_types():
    assert NODE_TYPES == {"MENU": 0, "PAGE": 1, "REPORT": 2, "EXT_LINK": 3, "PORTAL_SPACE": 4}


def test_open_states_and_schema_states():
    assert OPEN_STATES == {"EDIT": 0, "VIEW": 1, "INPUT": 2}
    assert PAGE_SCHEMA_STATES["DRAFT"] == 1 and PAGE_SCHEMA_STATES["FORMAL"] == 2
    assert PAGE_SCHEMA_STATES["NONE"] == -1


def test_function_tags():
    assert FUNCTION_TAGS["NORMAL"] == 0 and FUNCTION_TAGS["ROOT"] == 1
    assert FUNCTION_TAGS["BIZ_HOME"] == 2
    assert len(FUNCTION_TAGS) >= 17


def test_table_and_validate():
    assert FUNCTION_NODE_TABLE == "udc_function_node"
    errs = validate_function_node({"appId": 1, "type": "MENU"})
    assert any("terminalType" in e for e in errs) and any("name" in e for e in errs)
    ok = {"appId": 1, "terminalType": "PC", "type": "MENU", "name": "首页"}
    assert validate_function_node(ok) == []
    assert any("超限 64" in e for e in validate_function_node(dict(ok, name="x" * 70)))


import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.menu_constraints import (
    AUTO_DEFAULT_PAGE_ON_CHILD_CREATE,
    DEFAULT_PAGE_UNSET,
    FUNCTION_DTO_FIELDS,
    FUNCTION_NODE_08100_TAG_EXEMPT,
    FUNCTION_REFER_DTO_FIELDS,
    FUNCTION_REFER_DTO_REQUIRED,
    FUNCTION_TREE_MISSING_KEY_ERROR,
    FUNCTION_TREE_READ_ENDPOINTS,
    FUNCTION_TREE_REQUIRED_KEYS,
    MENU_CREATE_ENDPOINT_BY_TYPE,
    SET_DEFAULT_PAGE_ERRORS,
    SET_DEFAULT_PAGE_WRITES,
    UDC_CE_FUNCTION_NODE_08100,
    validate_default_page_call,
    validate_function_refer,
)
from tools.core._fixtures.live_targets import (
    LIVE_DETECTION_ERROR_COUNT,
    LIVE_MENU_NAME,
    LIVE_MENU_NODE_ID,
    LIVE_PAGE_ID,
    LIVE_PAGE_NODE_ID,
    LIVE_PAGE_URL,
    LIVE_WARN_COUNT_AFTER,
    LIVE_WARN_COUNT_BEFORE,
)


def test_page_node_must_use_function_refer_endpoint():
    """★ 本轮最有价值的一条：FunctionDto 无 resourceId => POST /function 建 PAGE 必 BOOT_4000。"""
    assert "resourceId" not in FUNCTION_DTO_FIELDS
    assert "resourceId" in FUNCTION_REFER_DTO_FIELDS
    assert MENU_CREATE_ENDPOINT_BY_TYPE["PAGE"] == "POST /udc/function/create/function-refer"
    assert MENU_CREATE_ENDPOINT_BY_TYPE["MENU"] == "POST /udc/function"


def test_dto_field_sets_are_exact():
    assert FUNCTION_DTO_FIELDS == (
        "name", "icon", "permission", "parentId", "appId", "terminalType",
        "defaultPage", "url", "relationId", "tag", "type", "orderNo")
    assert FUNCTION_REFER_DTO_FIELDS == (
        "name", "parentId", "appId", "terminalType", "url", "relationId",
        "resourceId", "relationApp", "openState", "pageParam", "type", "pageType")
    # resourceId 是两者的唯一判别性差集（其余差异是 permission/appBizHome 等可选字段）
    assert set(FUNCTION_REFER_DTO_FIELDS) - set(FUNCTION_DTO_FIELDS) >= {"resourceId"}


def test_function_refer_required_and_page_resource_id():
    assert set(FUNCTION_REFER_DTO_REQUIRED) == {
        "name", "parentId", "appId", "terminalType", "url", "resourceId", "type"}
    errs = validate_function_refer({"type": "PAGE"})
    assert any("name" in e for e in errs)
    assert any("resourceId" in e for e in errs)
    # 齐全即通过
    ok = {"name": "小爪验收页面", "parentId": -1628253460115858501, "appId": 8704025620829192834,
          "terminalType": "PC", "url": "xzhpage951440", "resourceId": "1520098474917276520",
          "type": "PAGE"}
    assert validate_function_refer(ok) == []


def test_08100_true_condition_is_no_child_page_to_point_at():
    """08100 文案是「未设默认页」，真实充分条件是「无子页面可指向」。"""
    assert UDC_CE_FUNCTION_NODE_08100 == "UDC_CE_FUNCTION_NODE_08100"
    assert DEFAULT_PAGE_UNSET == 0
    assert set(FUNCTION_NODE_08100_TAG_EXEMPT) == {"ROOT", "SPACE_MENU", "BIZ_HOME"}


def test_default_page_call_preconditions():
    assert SET_DEFAULT_PAGE_WRITES == ("url", "defaultPage", "relationApp")
    assert "BOOT_1000" in SET_DEFAULT_PAGE_ERRORS
    assert validate_default_page_call(None, None) == ["default_page 缺 functionId",
                                                      "default_page 缺 sourceId"]
    # 前提 A：sourceId 必须是 functionId 的直接子节点
    assert validate_default_page_call("A", "B", parent_of_source="A") == []
    assert len(validate_default_page_call("A", "B", parent_of_source="C")) == 1


def test_auto_default_page_on_child_create():
    assert AUTO_DEFAULT_PAGE_ON_CHILD_CREATE is True


def test_tree_read_endpoints_and_required_keys():
    assert set(FUNCTION_TREE_READ_ENDPOINTS) == {"menu_only", "with_children"}
    assert "onlyMenu" not in FUNCTION_TREE_READ_ENDPOINTS["with_children"]
    assert FUNCTION_TREE_REQUIRED_KEYS == ("appId", "terminalType")
    assert FUNCTION_TREE_MISSING_KEY_ERROR == "UDC_APP_0026"


def test_live_anchors_pin_the_evidence():
    assert LIVE_MENU_NODE_ID == "-1628253460115858501"
    assert LIVE_MENU_NAME == "小爪验收菜单"
    assert LIVE_PAGE_NODE_ID == "4630606675502338872"
    assert LIVE_PAGE_ID == "1520098474917276520"
    assert LIVE_PAGE_URL == "xzhpage951440"
    assert LIVE_WARN_COUNT_AFTER == LIVE_WARN_COUNT_BEFORE - 1 == 8
    assert LIVE_DETECTION_ERROR_COUNT == 0


def test_adversarial_function_dto_must_not_gain_resource_id():
    """对抗自证：若有人给 FunctionDto 补上 resourceId，本护栏必须失败。"""
    assert "resourceId" not in FUNCTION_DTO_FIELDS, \
        "FunctionDto 若出现 resourceId，说明 CFR 结论被改坏或类换版本，须重取字节码证据"
