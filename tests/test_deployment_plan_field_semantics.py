"""build_deployment_plan 字段语义键白名单（证据驱动，收窄版）。

白名单 _ATTR_SEMANTIC_KEYS = 平台 AttributeDto 实际接受、且 skill 有 LIVE/静态
证据的键：multiSelect / relationType / relationApp / relationEntity / uniqueness。
白名单外的键（required / length / defaultValue / indexSource ...）无「建属性 create
接口接受这些键」的证据 → 一律不塞 body（塞了平台不认的键 → BOOT_3002 或静默忽略）。
indexSource 更是跨对象错置（它属于 udc_index 索引对象，不是属性键）。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from components.platform_operations.deployment import (
    build_deployment_plan, infer_datatype, _ATTR_SEMANTIC_KEYS,
)


def _first_attr_body(plan):
    body = plan["steps"][1]["body"]
    if isinstance(body, list):
        body = body[0]
    return body


def test_attribute_body_preserves_whitelisted_entity_relation_keys():
    attr = {"name": "participants", "caption": "Participants", "dataType": "ENTITY",
            "multiSelect": True, "relationType": 1,
            "relationApp": "organization",
            "relationEntity": "com.seeyon.organization.domain.core.entity.OrgMember",
            "uniqueness": False}
    body = _first_attr_body(build_deployment_plan("1", "Order", "订单", [attr]))
    for key in _ATTR_SEMANTIC_KEYS:
        assert key in body, f"白名单键丢失：{key}"
        assert body[key] == attr[key]
    assert body["dataType"] == "ENTITY"


def test_attribute_body_omits_unverified_semantic_keys():
    # 白名单外、无建属性 create 受键证据的键 → 不臆造塞入 body
    attr = {"name": "orderNo", "dataType": "STRING",
            "required": True, "length": 32, "defaultValue": "DN0", "indexSource": 1}
    body = _first_attr_body(build_deployment_plan("1", "Order", "订单", [attr]))
    for key in ("required", "length", "defaultValue", "indexSource"):
        assert key not in body, f"白名单外键被臆造塞入：{key}"
    # 基础三键仍在
    assert body["name"] == "orderNo"
    assert body["caption"] == "orderNo"
    assert body["dataType"] == "STRING"


def test_attribute_body_omits_unsupplied_whitelisted_keys():
    """白名单键输入没给 → 不臆造（缺省不塞进 body）。"""
    body = _first_attr_body(build_deployment_plan("1", "Order", "订单", [{"name": "memo", "dataType": "STRING"}]))
    for key in _ATTR_SEMANTIC_KEYS:
        assert key not in body, f"输入未提供却塞入：{key}"


def test_attribute_body_carries_appid_and_entityid_placeholder():
    # 审计修正：build 必须带 appId(数字) + entityId(<entity_id> 占位，宿主建实体后替换)
    body = _first_attr_body(build_deployment_plan("3289082814923688017", "Order", "订单",
                                                  [{"name": "memo", "dataType": "STRING"}]))
    assert body["appId"] == 3289082814923688017, "appId 必须是数字 Long（非 app name）"
    assert body["entityId"] == "<entity_id>", "entityId plan 阶段用占位符，宿主建实体后替换"


def test_infer_localdatetime_maps_to_datetime_not_date():
    # java.time.LocalDateTime 含子串 "Date"，旧逻辑会误判成 DATE；必须先判 LocalDateTime
    assert infer_datatype("x", "java.time.LocalDateTime") == ("DATETIME", False)
    assert infer_datatype("x", "java.time.LocalDate") == ("DATE", False)
    assert infer_datatype("x", "java.util.Date") == ("DATE", False)


def test_to_app_id_no_trailing_digits_raises_clear_valueerror():
    """审计点：app name 无尾数段（如 appx/zzprob）→ 必须抛可行动的 ValueError，
    不能抛 AttributeError（None.group），宿主看不出根因。"""
    import pytest
    from components.platform_operations.deployment import _to_app_id
    with pytest.raises(ValueError) as e:
        _to_app_id("appx")
    assert "appId" in str(e.value) or "数字" in str(e.value), \
        f"错误信息须含可行动提示，而非 None.group：{e.value}"


def test_build_deployment_plan_no_trailing_digits_raises_clear_valueerror():
    """build_deployment_plan 同边界——传无尾数段 app 名，出可行动错误不崩 AttributeError。"""
    import pytest
    with pytest.raises(ValueError):
        build_deployment_plan("zzprob", "Order", "订单", [])


def test_enum_item_empty_item_value_raises_clear_valueerror():
    """2026-10-20 契约修正：枚举项的值槽位是 itemValue（不是 code 整数）。

    平台报「枚举项编码 不能为空」指的正是 itemValue 槽位
    （ctp_enum_item.item_value），不是整数 code。
    """
    import pytest
    from components.construction.metadata_artifacts import build_enum_item_body
    with pytest.raises(ValueError) as e1:
        build_enum_item_body(1, 9, "c", None, "ENUM_CODE", 1)
    assert "item_value" in str(e1.value), f"须点名 item_value 槽位：{e1.value}"
    with pytest.raises(ValueError) as e2:
        build_enum_item_body(1, 9, "c", "", "ENUM_CODE", 1)
    assert "item_value" in str(e2.value), f"空串须报 item_value 不能为空：{e2.value}"
