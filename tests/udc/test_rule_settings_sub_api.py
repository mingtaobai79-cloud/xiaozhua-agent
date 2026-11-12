"""规则域/设置域剩余子域 controller API 模型测试。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.rule_sub_api_model import (
    RULE_SUB_CONTROLLERS, RULE_SUB_OPS, rule_sub_api_map, rule_sub_summary)
from components.udc.setting.settings_sub_api_model import (
    SETTINGS_SUB_CONTROLLERS, SETTINGS_SUB_OPS, settings_sub_api_map, settings_sub_summary)


def test_all_rule_sub_ops_resolve():
    m = rule_sub_api_map()
    assert len(m) == len(RULE_SUB_OPS)
    assert not [k for k, v in m.items() if not v["resolved"]]


def test_all_settings_sub_ops_resolve():
    m = settings_sub_api_map()
    assert len(m) == len(SETTINGS_SUB_OPS)
    assert not [k for k, v in m.items() if not v["resolved"]]


def test_deduction_rule_paths():
    m = rule_sub_api_map()
    assert m["扣减_创建图"]["full_path"] == "/udc/deduction/map"
    assert m["扣减_创建规则"]["full_path"] == "/udc/deduction/rule"
    assert m["扣减_规则详情"]["full_path"] == "/udc/deduction/rule/{id}"


def test_data_flow_paths():
    m = settings_sub_api_map()
    assert m["生单图_创建"]["full_path"] == "/udc/data-flow"
    assert m["生单图_创建映射"]["full_path"] == "/udc/data-flow/mapping"
    assert m["生单图_事件实体"]["full_path"] == "/udc/data-flow/list/event/entity"


def test_dto_paths():
    m = settings_sub_api_map()
    assert m["DTO_创建含属性和引用"]["full_path"] == "/udc/data-transfer-object/create-dto-with-attrs"
    assert m["DTO属性_修改"]["full_path"] == "/udc/data-transfer-object/attribute/update"


def test_summaries():
    rs = rule_sub_summary()
    assert len(rs["controllers"]) == 7
    assert rs["controllers"]["DeductionRuleController"]["api_count"] == 16
    ss = settings_sub_summary()
    assert len(ss["controllers"]) == 10
    assert ss["controllers"]["DataFlowDesignController"]["api_count"] == 24
    assert ss["controllers"]["DataTransferObjectController"]["api_count"] == 21
