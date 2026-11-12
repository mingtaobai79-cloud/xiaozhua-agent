"""GROUP_AND_SUM：分组字段 + 汇总字段 → groupByAttrs / countAttrs。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.construction.node_builder import NodeBuilder
from components.construction.microflow_nodes_extra import list_operation

APP = "1000000000000000001"
AN = "demotenant"


def _src():
    return {"nodeId": "RA1", "actionType": "RETRIEVE_ARRAY", "title": "列表",
            "output": {"id": "x.Dto", "javaType": "x.Dto", "dataType": "DTO",
                       "type": "ARRAY", "dtoType": "MASTER_ENTITY",
                       "appName": AN, "name": "_RETRIEVE_1"}}


def _attr(name):
    return {"name": name, "id": "x.Dto." + name, "dataType": "STRING"}


def test_group_and_sum_sets_both_attr_arrays():
    n = list_operation(NodeBuilder(app_id=APP, app_name=AN), _src(),
                       op_type="GROUP_AND_SUM", group_by=[_attr("sourceTable")],
                       count_attrs=[_attr("processedRows")])
    assert n["operationType"]["type"] == "GROUP_AND_SUM"
    assert [a["name"] for a in n["groupByAttrs"]] == ["sourceTable"]
    assert [a["name"] for a in n["countAttrs"]] == ["processedRows"]


def test_group_and_sum_output_stays_array():
    """分组结果仍是列表，元素 DTO 不变（不是新 DTO）。"""
    n = list_operation(NodeBuilder(app_id=APP, app_name=AN), _src(),
                       op_type="GROUP_AND_SUM", group_by=[_attr("sourceTable")],
                       count_attrs=[_attr("processedRows")])
    assert n["output"]["type"] == "ARRAY"
    assert n["output"]["id"] == "x.Dto"


def test_group_and_sum_requires_group_by():
    try:
        list_operation(NodeBuilder(app_id=APP, app_name=AN), _src(),
                       op_type="GROUP_AND_SUM", count_attrs=[_attr("processedRows")])
    except ValueError:
        return
    raise AssertionError("GROUP_AND_SUM 缺 group_by 必须拒绝")
