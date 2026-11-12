"""实体域子域 controller API 综合模型测试。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.entity_sub_api_model import (
    ENTITY_SUB_CONTROLLERS, ENTITY_SUB_OPS, entity_sub_api_map, entity_sub_summary)


def test_all_sub_ops_resolve():
    m = entity_sub_api_map()
    assert len(m) == len(ENTITY_SUB_OPS)
    unresolved = [k for k, v in m.items() if not v["resolved"]]
    assert not unresolved, f"未解析: {unresolved}"


def test_index_ops():
    m = entity_sub_api_map()
    assert m["索引_创建"]["full_path"] == "/udc/index"
    assert m["索引_按实体列表"]["full_path"] == "/udc/index/entity/list"
    assert m["索引_可选字段"]["full_path"] == "/udc/index/attribute/{entityId}"


def test_attribute_set_ops():
    m = entity_sub_api_map()
    assert m["字段集_创建"]["full_path"] == "/udc/attributeSet"
    assert m["字段集_按名称含属性"]["full_path"] == "/udc/attributeSet/select-by-name/attributes"


def test_event_ops():
    m = entity_sub_api_map()
    assert m["事件_创建带数据"]["full_path"] == "/udc/event/create-with-data"
    assert m["事件_业务事件"]["full_path"] == "/udc/event/list/business-event"


def test_data_type_and_stereotype():
    m = entity_sub_api_map()
    assert m["数据类型_按应用"]["full_path"] == "/udc/data-type/data-types-by-app-id/{appId}"
    assert m["版型_清单"]["full_path"] == "/udc/stereotype/list"


def test_scalability_ops():
    m = entity_sub_api_map()
    assert m["扩展方案_含明细"]["full_path"] == "/udc/scalability-option/select-by-appid/with-detail/{appId}"


def test_summary_nine_controllers():
    s = entity_sub_summary()
    assert len(s["controllers"]) == 10
    assert s["controllers"]["EventController"]["api_count"] == 13
    assert s["controllers"]["AttributeSetController"]["api_count"] == 10
