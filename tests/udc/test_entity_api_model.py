"""实体域 EntityController 全 API 模型测试。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.entity_api_model import (
    ENTITY_CONTROLLER, ENTITY_OPS, entity_api_map, entity_coverage)


def test_all_entity_ops_resolve():
    m = entity_api_map()
    assert len(m) == len(ENTITY_OPS)
    unresolved = [k for k, v in m.items() if not v["resolved"]]
    assert not unresolved, f"未解析: {unresolved}"


def test_entity_crud_paths():
    m = entity_api_map()
    assert m["实体_创建"]["full_path"] == "/udc/entity"
    assert m["实体_修改"]["full_path"] == "/udc/entity/update"
    assert m["实体_删除"]["full_path"] == "/udc/entity/delete"
    assert m["实体_详情"]["full_path"] == "/udc/entity/{id}"
    assert m["实体_父实体"]["full_path"] == "/udc/entity/{id}/parent"


def test_attribute_paths():
    m = entity_api_map()
    assert m["属性_创建"]["full_path"] == "/udc/entity/attribute"
    assert m["属性_批量创建"]["full_path"] == "/udc/entity/attribute-batch"
    assert m["属性_修改"]["full_path"] == "/udc/entity/attribute/update"
    assert m["属性_全量按实体"]["full_path"] == "/udc/entity/attribute/select-all-by-entity-id/{entityId}"


def test_preset_and_association_paths():
    m = entity_api_map()
    assert m["预置_默认Excel模板"]["full_path"] == "/udc/entity/preset/create-default-excel-template"
    assert m["关联_实体分组"]["full_path"] == "/udc/entity/association/entity/{appId}"
    assert m["序列_列表"]["full_path"] == "/udc/entity/association/serial"


def test_full_coverage():
    c = entity_coverage()
    assert c["api_count"] == 55
    assert c["unmapped"] == []
