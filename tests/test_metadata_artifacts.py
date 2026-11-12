"""优先级 3：实体配置面生成器（索引/枚举/事件+DTO/过滤方案）— 证据驱动。

证据基线（skill metadata-artifact-apis.md，test2 LIVE 探针推进所得）：
- 索引 /index：{caption, entityId, fieldIds=逗号分隔字符串}（给数组报 BOOT_3002 to type String）
- 枚举 /udc-enum：{appId, caption, name, orderNo}；枚举项 /udc-enum-item：
  {appId, enumId, caption, code(Int), name, orderNo, enable:1}（code 传字符串报 BOOT_3002）
- 事件 /event：{appId, caption, name:拼音, sourceId:0, source:1, actionType:1,
  numberFiredOnce:"1", messageType:0, enabled:1, eventData:<DTO id>, eventDataType:0}
  事件与 DTO 同名配对；eventData 指向 udc_data_transfer_object.id
- DTO create-dto-with-attrs：body=ArrayList（对象形态报反序列化错），元素
  {appId, caption, name, source:5, sourceId:0, isMetaData:1, isRoot:1, isCommandDto:0,
  attributes:[{name, caption, dataType, dataTypeCategory:0, type:0, isNotNull:0}]}
- 过滤方案 /udc-runtime/filter-plan/create-new（udc-bi jar，双 udc 前缀）：
  planType:0=FILTER 列表页隐藏（「页面规则没建立」根因）/ 2=LIST 可见；
  sourceId=`<page_id>_<gridId>`；content 是 JSON 字符串 cond 树
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from components.construction.metadata_artifacts import (
    build_index_body, build_enum_body, build_enum_item_body,
    build_dto_with_attrs_body, build_event_body, build_filter_plan_body,
)


def test_index_body_field_ids_is_comma_string_not_list():
    # 证据：fieldIds 给数组报 BOOT_3002 ... to type String → 必须逗号字符串
    body = build_index_body(caption="订单号索引", entity_id=-6292232560251287724,
                           field_ids=["3729580767880732084"])
    assert body["fieldIds"] == "3729580767880732084"
    assert isinstance(body["fieldIds"], str)
    multi = build_index_body("复合索引", 1, ["111", "222"])
    assert multi["fieldIds"] == "111,222"
    assert body["entityId"] == -6292232560251287724
    assert body["caption"] == "订单号索引"


def test_enum_body_minimal_fields():
    # 证据（2026-10-20 设计器 UI 抓包 + ctp_enum DB 回读）：udcEnumPost 的 body 逐字段
    # name=i18n JSON 显示名、code=英文编码、appGuid/categoryId 必填
    body = build_enum_body(app_id=5791640252914287064, caption="订单状态", name="ddzt",
                            order_no=100, app_guid="2275741415570096882")
    assert json.loads(body["name"]) == {"zh_CN": "订单状态"}
    assert body["code"] == "ddzt"
    assert body["appId"] == "5791640252914287064"
    assert body["orderNo"] == 100
    assert body["appGuid"] == "2275741415570096882"
    assert body["categoryId"] == "0"
    assert body["dataStatus"] is False
    assert body["bizType"] == "UDC_DESIGN"


def test_enum_item_uses_item_value_and_parent_id():
    # 证据（2026-10-20 报错 + ctp_enum_item 表结构）：值槽位是 itemValue，
    # 上级项槽位是 parentId（顶层项填 "0"），name 是 i18n JSON 字符串
    body = build_enum_item_body(app_id=1, enum_id=99, caption="已审核",
                                 item_value="2", enum_code="AUDIT_STATUS", order_no=1)
    assert body["itemValue"] == "2"
    assert body["parentId"] == "0", "顶层枚举项 parentId 必须是 '0'，否则平台报上级枚举项ID 不能为null"
    assert body["enumCode"] == "AUDIT_STATUS"
    assert body["enable"] == 1
    assert body["enumId"] == "99"
    assert json.loads(body["name"]) == {"zh_CN": "已审核"}
    # 老槽位 code / caption 不再出现
    assert "code" not in body or body.get("code") is None
    assert "caption" not in body


def test_dto_body_is_array_single_element():
    # 证据：body=ArrayList，元素 source:5（消息 DTO）+ attributes 不认 javaType
    body = build_dto_with_attrs_body(
        app_id=1, caption="订单审核事件", name="ddshsj",
        attributes=[{"name": "orderStatus", "caption": "订单状态", "dataType": "STRING"}])
    assert isinstance(body, list) and len(body) == 1
    el = body[0]
    for key in ("appId", "caption", "name", "source", "sourceId", "isMetaData",
                "isRoot", "isCommandDto", "attributes"):
        assert key in el, f"DTO 元素缺键：{key}"
    assert el["source"] == 5 and el["sourceId"] == 0 and el["isMetaData"] == 1
    attr = el["attributes"][0]
    # 空值约束字段名叫 notNull（Boolean），不是 isNotNull ——
    # BaseUdcAttributeDto: private Boolean notNull; getNotNull() → Jackson key "notNull"
    for key in ("dataType", "dataTypeCategory", "type", "notNull"):
        assert key in attr, f"DTO attribute 缺键：{key}"
    assert "isNotNull" not in attr, "isNotNull 平台不认，会被静默忽略"
    assert attr["dataTypeCategory"] == 0, "消息类字段 dataTypeCategory=0（全库分布 4089/223/6）"
    assert "javaType" not in attr, "attributes 不认 javaType（报 dataTypeCategory must not be null）"


def test_event_body_minimal_form_and_dto_pairing():
    # 证据：建事件全字段字典（LIVE）；事件与 DTO 同名配对（样本 bxhxlcjssj）
    body = build_event_body(app_id=1, caption="订单审核事件", event_name="ddshsj",
                             dto_id=-5115704479660969239)
    assert body["sourceId"] == 0 and body["source"] == 1
    assert body["actionType"] == 1, "action_type 全库恒 1（41/41）"
    assert body["numberFiredOnce"] == "1", "numberFiredOnce 是字符串 '1'"
    assert body["messageType"] == 0 and body["enabled"] == 1 and body["eventDataType"] == 0
    assert body["eventData"] == -5115704479660969239
    assert body["name"] == "ddshsj"


def test_filter_plan_default_plan_type_2_is_list_visible():
    # 证据：planType:0=FILTER 列表页隐藏（用户「页面规则没建立」根因）/ 2=LIST 可见
    out = build_filter_plan_body(
        app_name="zzprobe", app_id=1, page_id=-4214685795235257124,
        grid_suffix="usOJ", driven_entity="Order", caption="已审核订单",
        conditions=[{"attribute_id": "3729580767880732084", "value": "CHECKED"}])
    body = out["body"]
    assert body["planType"] == 2, "默认必须 2（LIST 可见），0 会静默不可见"
    assert body["sourceId"] == "-4214685795235257124_udcDataGridView_usOJ"
    assert body["sourceType"] == 0 and body["pageUrlType"] == 1
    import json
    content = json.loads(body["content"])
    assert content["entities"] == ["<entity_id>"] or "entities" in content
    cond = content["cond"][0]["conditions"][0]
    assert cond["operator"] == {"value": "EQ", "desc": "="}
    # planType 0 显式传入时进 unknowns 提示不可见
    hidden = build_filter_plan_body("a", 1, 2, "g", "E", "c",
                                     conditions=[{"attribute_id": "1", "value": "X"}],
                                     plan_type=0)
    assert "hidden" in str(hidden["unknowns"]).lower() or "FILTER" in str(hidden["unknowns"]), \
        "planType=0 必须提示列表页不可见"


def test_artifacts_are_readonly_plan_not_executed():
    # 全部生成器只出 body data（宿主执行），无网络/写
    out = build_filter_plan_body("a", 1, 2, "g", "E", "c",
                                  conditions=[{"attribute_id": "1", "value": "X"}])
    assert out["readonly_plan"] is True
