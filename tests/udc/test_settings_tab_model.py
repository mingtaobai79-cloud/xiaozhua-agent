"""设置面板 13 tab op 目录测试（SETTINGS-TABS-CALLCHAIN §1/§2.5/§3 证据）。"""
from components.udc.setting.settings_tab_model import (
    CALLBACK_FORMS, NAMING_RULES, SETTING_TABS,
    all_op_names, tab_catalog, tabs_by_status,
)


def test_thirteen_tabs_present():
    assert len(SETTING_TABS) == 13
    labels = {t.tab for t in SETTING_TABS}
    assert "枚举" in labels and "选项集" in labels and "导入导出模板" in labels
    assert "页面模板" in labels and "外框模板" in labels and "角色权限" in labels


def test_cross_naming_trap_registered():
    """JS key 与中文标签交叉是已证陷阱，目录以标签为准。"""
    by_label = {t.tab: t for t in SETTING_TABS}
    assert by_label["枚举"].js_key == "collections"
    assert by_label["选项集"].js_key == "enumeration"
    assert by_label["选项集"].uniformity_key == "enum"


def test_definiton_typo_preserved():
    """平台原样拼写禁止修正——防'好心'破坏。"""
    names = " ".join(all_op_names())
    assert "CtpParameterDefinitonPost" in names
    assert "CtpParameterDefinition" not in names   # 未被"修正"


def test_call_forms_four_plus_rest():
    assert set(CALLBACK_FORMS) == {"A", "A2", "B", "C", "D"}


def test_naming_rules_present():
    blob = " ".join(NAMING_RULES)
    assert "InputBody" in blob and "paramsKey" in blob and "introspection" in blob


def test_layout_vs_page_template_shared_component():
    """外框/页面模板同组件靠 category/pageType 分流，backend 必须体现两层。"""
    by_label = {t.tab: t for t in SETTING_TABS}
    assert "LAYOUT" in by_label["外框模板"].backend or "PageLayoutController" in by_label["外框模板"].backend
    assert "category" in by_label["页面模板"].note + by_label["外框模板"].note


def test_role_permission_not_udc_owned():
    by_label = {t.tab: t for t in SETTING_TABS}
    assert "ctp-user" in by_label["角色权限"].backend


def test_qrcode_backend_unlocated_marked():
    unloc = tabs_by_status("UNLOCATED")
    assert unloc and any("Ctp" in (t.note + t.backend) for t in unloc)


def test_catalog_json_roundtrip():
    import json
    cat = tab_catalog()
    back = json.loads(json.dumps(cat, ensure_ascii=False))
    assert len(back["tabs"]) == 13
    assert back["status_legend"]["OK"] == "调用链闭环"


def test_basicdata_init_chain_registered():
    """建完即初始化页面 op 必须在目录里（§3.13 链证据）。"""
    assert any("InitBasicdataPage" in o for o in all_op_names())
