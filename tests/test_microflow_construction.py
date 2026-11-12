"""MicroFlow 构造骨架（模板填充 + create/checkSchema body，宿主执行）。

证据基线（skill xiaozhua-udc-design-time-build，REST create L71-L73 LIVE 实证）：
- create 走 REST `POST /service/udc/microflow/create`（字符串枚举 triggerType=MANUAL/SERVICE，
  与 GraphQL udcMicroflowUpdatePost 数字枚举是两套契约，别互套）
- create 前必过 `POST /service/udc/microflow/checkSchema`（同 body），check:true errors:0 才建
- dataSchema 是 JSON **字符串**非嵌套对象；body 必带完整键位（缺一报错码不同）
- 节点富结构（RETRIEVE condition / CHANGE_ENTITY attrType 18 键）离线不可证 →
  构造器只出「模板深拷贝 + 占位符替换」，模板来自标品既有微流程 data_schema 或
  udc_microflow_preset_template，宿主填充真实 ID/文案。多一个键/少一个键都可能静默校验不过。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from components.construction.microflow import (
    build_microflow_create_body, fill_schema_template,
    CREATE_BODY_KEYS,
)


def _template():
    """最小 RETRIEVE+CHANGE_ENTITY 模板（占位符形态，模拟标品行 deep-copy 结果）。"""
    return {
        "sourceType": "MFStartNode",
        "trigger": {"type": "MANUAL", "nodes": []},
        "endNode": "END_NODE",
        "nodes": [
            {"nodeType": "RETRIEVE", "id": "n1",
             "entityFullName": "${entityFullName}", "fetchType": "IDS",
             "value": {"type": "SelectParam", "selectParam": {"id": "${dtoField}"}}},
            {"nodeType": "CHANGE_ENTITY", "id": "n2", "entityFullName": "${entityFullName}"},
        ],
        "input": [], "output": [],
    }


def test_fill_replaces_placeholders_recursively():
    filled, unresolved = fill_schema_template(
        _template(),
        replacements={"entityFullName": "com.seeyon.order.Order", "dtoField": "com.seeyon.order.dto.OrderDTO.id"})
    assert filled["nodes"][0]["entityFullName"] == "com.seeyon.order.Order"
    assert filled["nodes"][0]["value"]["selectParam"]["id"] == "com.seeyon.order.dto.OrderDTO.id"
    assert unresolved == [], "全部占位符都提供了替换值，不应有残留"


def test_fill_reports_unresolved_placeholders():
    filled, unresolved = fill_schema_template(
        _template(), replacements={"entityFullName": "com.seeyon.order.Order"})
    assert sorted(unresolved) == ["${dtoField}"], f"未提供替换值的占位符必须暴露：{unresolved}"
    assert "${dtoField}" in filled["nodes"][0]["value"]["selectParam"]["id"], "残留占位符保持原样待宿主补"


def test_fill_keeps_exact_key_set_no_extra_no_missing():
    """skill 铁律：填充前后键位集合一致（多一个键都可能静默校验不过）。"""
    filled, _ = fill_schema_template(_template(), {"entityFullName": "E", "dtoField": "F"})
    import json
    def keyset(o, prefix=""):
        ks = set()
        if isinstance(o, dict):
            for k, v in o.items():
                ks.add(prefix + k); ks |= keyset(v, prefix + k + ".")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                ks |= keyset(v, f"{prefix}{i}.")
        return ks
    assert keyset(filled) == keyset(_template()), "填充必须零缺失零多余键"


def test_create_body_has_all_19_keys_from_skill_evidence():
    body = build_microflow_create_body(
        name="queryOrderMembers", caption="查询订单人员", app_id=5791640252914287064,
        data_schema={"sourceType": "MFStartNode", "nodes": []})
    for key in CREATE_BODY_KEYS:
        assert key in body, f"create body 缺键：{key}（skill L71 键位字典）"
    assert set(body) == CREATE_BODY_KEYS, "create body 键位必须与证据字典完全一致"
    assert body["dataSchema"] == '{"sourceType": "MFStartNode", "nodes": []}'


def test_create_body_data_schema_is_json_string_not_object():
    """dataSchema 必须是字符串化 JSON（嵌套对象会被 create 拒绝）。"""
    body = build_microflow_create_body(
        name="x", caption="x", app_id=1, data_schema={"sourceType": "MFStartNode", "nodes": []})
    assert isinstance(body["dataSchema"], str)
    assert body["triggerType"] == "MANUAL" and body["type"] == "SERVICE", "字符串枚举，非 DB 数字"
    assert body["state"] == "DRAFT"


def test_check_schema_body_equals_create_body():
    """checkSchema 与 create 同 body（skill：同 body POST checkSchema → check:true 才 create）。"""
    body = build_microflow_create_body(
        name="x", caption="x", app_id=1, data_schema={"nodes": []})
    from components.construction.microflow import check_schema_body
    assert check_schema_body(body) == body


def test_create_body_rejects_bad_enum():
    body = build_microflow_create_body(
        name="x", caption="x", app_id=1, data_schema={}, trigger_type="NOT_A_TRIGGER")
    # 值域证据：BUSINESS_EVENT | MANUAL | SCHEDULE（create REST 字符串枚举）
    assert "NOT_A_TRIGGER" in body.get("unknowns", ()) or body.get("unknowns"), \
        "非法 triggerType 必须进 unknowns，不臆造"
