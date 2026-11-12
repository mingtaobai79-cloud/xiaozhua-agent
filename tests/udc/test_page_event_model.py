"""页面事件/动作值域模型测试（证据驱动，全离线）。

证据来源：docs/audit/udc-semantics/UDC-MAINLINE-AUDIT.md §3、
           docs/audit/udc-semantics/page-menu-source-audit.md
"""
from components.udc.page_event_model import (
    ACTION_TYPES, BUILTIN_ACTIONS, DETAIL_OPEN_MODES, PAGE_INFO_TYPES,
    WIDGET_ACTIONS, PageEventValidator,
)


def test_action_type_values():
    assert ACTION_TYPES == {"buildin", "widget", "microflow", "enevtThrow"}


def test_bad_action_type_fails():
    v = PageEventValidator([{"id": "e1", "eventType": "btn", "actionType": "invalid_xyz"}])
    assert v.status() == "FAIL"
    assert any("invalid_xyz" in e for e in v.errors())


def test_row_edit_pdrilldown_valid():
    ev = [
        {"id": "ev_edit", "eventType": "btn_edit", "actionType": "buildin",
         "actionName": "openPage",
         "paramsMapping": {
             "PRESET_ID": {"type": "CONTEXT_VARIABLE", "value": "CURRENT_ROW id grid"},
             "PRESET_DETAIL_PAGE_OPEN_MODE": "edit",
             "pageInfoType": "DETAIL",
         }},
    ]
    v = PageEventValidator(ev)
    assert v.status() == "PASS", v.to_dict()


def test_row_edit_missing_preset_id_fails():
    ev = [
        {"id": "ev_edit", "eventType": "btn_edit", "actionType": "buildin",
         "actionName": "openPage",
         "paramsMapping": {"pageInfoType": "DETAIL", "PRESET_DETAIL_PAGE_OPEN_MODE": "edit"}},
    ]
    v = PageEventValidator(ev)
    assert v.status() == "FAIL"
    assert any("PRESET_ID" in e for e in v.errors())


def test_row_delete_requires_row_data():
    ok = PageEventValidator([
        {"id": "ev_del", "eventType": "btn_del", "actionType": "widget",
         "actionName": "ENTITY_DELETE", "callbackDataType": "ROW_DATA",
         "noticeEntitys": ["full.name"]},
    ])
    assert ok.status() == "PASS", ok.to_dict()
    bad = PageEventValidator([
        {"id": "ev_del", "eventType": "btn_del", "actionType": "widget",
         "actionName": "ENTITY_DELETE"},
    ])
    assert bad.status() == "FAIL"
    assert any("ROW_DATA" in e for e in bad.errors())


def test_panel_action_requires_target():
    v = PageEventValidator([
        {"id": "ev_p", "eventType": "btn", "actionType": "widget",
         "actionName": "panel_openPanel"},
    ])
    assert v.status() in {"FAIL", "UNVERIFIED"}
    assert any("target" in m for m in v.errors() + v.warnings())


def test_microflow_button_fails_when_unbound():
    v = PageEventValidator([
        {"id": "ev_mf", "eventType": "btn", "actionType": "microflow"},
    ])
    # 未绑 microflow id = 无效事件（「必须带真实微流程 id」）→ 硬错
    assert v.status() == "FAIL"
    assert any("microflow" in e for e in v.errors())


def test_microflow_button_with_id_passes():
    v = PageEventValidator([
        {"id": "ev_mf", "eventType": "btn", "actionType": "microflow",
         "microFlowId": "732255149534301888"},
    ])
    assert v.status() == "PASS", v.to_dict()


def test_entity_rule_validate_group_not_confused_with_widget():
    # 对象边界：实体规则 VALIDATE 组 ≠ 页面动作 VALIDATE_ENTITY；
    # 这里验证 widget 值域不含 VALIDATE_ENTITY（它是实体规则组，不在页面动作值域）
    assert "VALIDATE_ENTITY" not in WIDGET_ACTIONS
