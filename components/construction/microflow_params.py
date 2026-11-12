"""出入参定义（trigger/endNode 的 paramType + 引用）。已 LIVE 验证。"""
from __future__ import annotations

import uuid
from typing import Any

from .microflow_fields import entity_ref


def _app_ref(app_id: str, app_name: str, caption: str = "数据迁移") -> dict[str, Any]:
    return {"appId": app_id, "appName": app_name, "caption": caption,
            "inApp": True, "udcApp": True, "dynamicDependency": False}


def make_trigger_entity(app_id: str, app_name: str, entity: dict[str, Any],
                        desc: str | None = None, is_array: bool = False) -> tuple[dict, dict]:
    """实体对象入参：返回 (trigger, input_dto)。"""
    dto = entity["fullName"]
    cap = entity["caption"]
    input_name = "_FLOW_INPUT_" + uuid.uuid4().hex[:6]
    inp_dto = {"id": dto, "javaType": dto, "inApp": True, "appName": app_name,
               "dataType": "DTO", "type": "ARRAY" if is_array else "OBJECT",
               "desc": desc or cap, "dtoType": "MASTER_ENTITY", "udcApp": True,
               "hasPagination": False, "name": input_name}
    trigger = {
        "id": "", "nodeId": "MFStartNode", "caption": None, "description": None,
        "type": "MANUAL", "input": None, "output": inp_dto,
        "paramType": "ENTITY_OBJECT", "basic": None, "isArray": is_array,
        "desc": desc or cap, "app": _app_ref(app_id, app_name),
        "hasPagination": False, "entityObject": entity_ref(entity),
    }
    return trigger, inp_dto


def make_end_entity(app_id: str, app_name: str, entity: dict[str, Any],
                    src_node_id: str, src_action: str, desc: str = "出参实体",
                    is_array: bool = False) -> tuple[dict, dict]:
    """实体对象出参：返回 (endNode, output_dto)。src_node_id 是出参来源节点。"""
    dto = entity["fullName"]
    cap = entity["caption"]
    output_name = "_FLOW_OUTPUT_" + uuid.uuid4().hex[:6]
    out_dto = {"id": dto, "javaType": dto, "dataType": "DTO",
               "type": "ARRAY" if is_array else "OBJECT", "desc": desc,
               "dtoType": "MASTER_ENTITY", "udcApp": True, "name": output_name}
    end_node = {
        "id": "", "name": "", "type": "END", "actionType": "END_NODE", "nodeId": "MFEndNode",
        "caption": "结束", "description": "", "input": None, "output": out_dto,
        "value": {"type": "SelectParam", "selectParam": {
            "id": dto, "javaType": dto, "dataType": "DTO",
            "type": "ARRAY" if is_array else "OBJECT", "desc": cap,
            "dtoType": "MASTER_ENTITY", "udcApp": True,
            "name": "_" + src_node_id, "outputName": "_" + src_node_id,
            "position": "parent", "appName": app_name,
            "relationEntity": entity["relationEntityId"],
            "nodeInfo": {"nodeId": src_node_id, "type": "ACTIVITY", "actionType": src_action},
            "description": cap},
            "desc": cap},
        "paramType": "ENTITY_OBJECT", "basic": None, "isArray": is_array,
        "desc": desc, "app": _app_ref(app_id, app_name),
        "entityObject": entity_ref(entity), "outPutDesc": None, "isCompleted": True,
    }
    return end_node, out_dto
