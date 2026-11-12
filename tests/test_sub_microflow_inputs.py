"""子微流程 DTO 入参的字段级映射形态。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.construction.node_builder import NodeBuilder
from components.construction.microflow_nodes_extra import sub_microflow

APP = "1000000000000000001"
AN = "demotenant"


def _svc(inp=None):
    return {"id": "123", "name": "sub1", "caption": "子流程", "appId": APP,
            "hasInput": bool(inp), "hasOutput": True, "input": inp,
            "output": {"dataType": "INTEGER"}, "path": "/microflow/sub1",
            "triggerType": "MANUAL", "type": "SERVICE", "method": "POST",
            "restType": "POST"}


def test_attrs_shape_is_field_level():
    """attrs[].attrType 必须是子流程入参 DTO 的字段；value 是 Simple 或 SelectParam。"""
    inp = {"id": "x.Dto", "dataType": "DTO", "type": "OBJECT"}
    attrs = [{"attrType": {"name": "taskId", "id": "x.Dto.taskId"},
              "value": {"type": "Simple", "simple": "V", "desc": "V"}}]
    n = sub_microflow(NodeBuilder(app_id=APP, app_name=AN), _svc(inp), attrs)
    assert n["mappingType"] == "attrs"
    assert n["attrs"][0]["attrType"]["name"] == "taskId"
    assert n["attrs"][0]["value"]["type"] == "Simple"


def test_no_attrs_means_no_input_mapping():
    n = sub_microflow(NodeBuilder(app_id=APP, app_name=AN), _svc(None), None)
    assert n["attrs"] == []
    assert n["mappingType"] == "attrs"
