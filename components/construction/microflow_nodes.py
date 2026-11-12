"""微流程节点构造器（以真实落库节点为模板，禁止凭空拼字段）。

证据来源
--------
`fixtures/microflow/create_entity_node.sample.json` 取自 test2 活体微流程
`小爪全节点24-V16`(id=-5472409826136842382) 的真实节点 `CREATE_ENTITY_UuKpNp`
（"插入数据"）。模板里的每个键都是平台真实产出的键，构造器只做替换，不新增键。

节点域分类（用户口径，勿混用）
----------------------------
* 数据活动（CREATE_ENTITY / CHANGE_ENTITY / DELETE_ENTITY / RETRIEVE ...）
  应用内实体 CRUD，**建档写库用这里**，不要用「自定义服务」。
* 数据加工（CONVERT_DATA / DATA_MAPPING）
* 基础服务（CALL_APP_SERVICE / SUB_MICROFLOW / CALL_DATA_FLOW / EVENT_DISPATCH）
  自定义服务 = 对外开放的 dubbo 接口 / 基础组件接口。

表达式铁律
----------
手写 Expression 的 `designData.context[]` 每条必须带 `uniformityParams`
（paramId/paramCategory/extensionProperties），缺了会触发
`ExpressionReferenceDataResolver` NPE → 整个应用检测 FAIL。
"""

from __future__ import annotations

import copy
import json
import uuid
from typing import Any, Iterable

SAMPLE_PATH = "fixtures/microflow/create_entity_node.sample.json"

_JAVA_BY_TYPE = {
    "STRING": "java.lang.String",
    "MULTILINESTRING": "java.lang.String",
    "INTEGER": "java.lang.Integer",
    "BIGINTEGER": "java.lang.Long",
    "DECIMAL": "java.math.BigDecimal",
    "BOOLEAN": "java.lang.Boolean",
    "DATE": "java.util.Date",
    "DATETIME": "java.util.Date",
}


def _cap(name: str) -> str:
    return name[0].upper() + name[1:]


def load_template(path: str = SAMPLE_PATH) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
# 值构造：SelectParam（引用前序节点出参） / Expression（表达式）
# --------------------------------------------------------------------------
def value_select_param(*, output_name: str, field_name: str, dto_full: str,
                       caption: str, data_type: str = "STRING",
                       position: str = "children",
                       path: str | None = None) -> dict[str, Any]:
    """引用前序节点出参字段。output_name 形如 `_CREATE_VARIABLE_uX6yCl`。"""
    attr_key = f"{dto_full}.{field_name}"
    return {
        "type": "SelectParam",
        "selectParam": {
            "key": f"{output_name}{attr_key}",
            "name": field_name,
            "id": attr_key,
            "appName": dto_full.split(".")[3] if dto_full.count(".") >= 4 else "",
            "description": caption,
            "position": position,
            "path": path or attr_key.replace(".", "").replace("-", ""),
            "outputName": output_name,
            "type": "OBJECT",
            "dataType": data_type,
            "javaType": _JAVA_BY_TYPE.get(data_type, "java.lang.String"),
        },
        "desc": f"{caption} [{data_type}]",
    }


def _uniformity(param_id: str, category: str, ext: dict | None) -> dict[str, Any]:
    return {
        "paramId": param_id,
        "paramCategory": category,
        "extensionProperties": json.dumps(ext, ensure_ascii=False, separators=(",", ":")) if ext else "",
        "pageNodeExtension": None,
    }


def expr_context_dto(*, output_name: str, description: str, dto_full: str,
                     base_name: str, fields: Iterable[tuple[str, str, str]]) -> list[dict[str, Any]]:
    """构造带 uniformityParams 的三级 context（节点出参 → DTO 对象 → 字段）。"""
    props = []
    for fname, fcap, ftype in fields:
        pid = f"{dto_full}.{fname}"
        props.append({
            "name": fname, "description": fcap, "type": ftype,
            "selectable": True, "enableDataI18n": False,
            "uniformityParams": _uniformity(pid, ftype, {
                "id": pid, "relationType": "NONE",
                "javaType": _JAVA_BY_TYPE.get(ftype, "java.lang.String"),
            }),
        })
    return [{
        "name": output_name, "description": description, "type": "OBJECT",
        "selectable": False, "enableDataI18n": False,
        "properties": [{
            "name": base_name, "description": description, "type": "OBJECT",
            "selectable": True, "enableDataI18n": False,
            "properties": props,
            "uniformityParams": _uniformity(dto_full, "OBJECT", {"id": dto_full}),
        }],
        "uniformityParams": _uniformity(dto_full, "DTO", {"id": dto_full, "javaType": dto_full}),
    }]


def expr_context_var(*, name: str, description: str, data_type: str) -> list[dict[str, Any]]:
    """基本变量在表达式 context 里是扁平一层（非嵌套 OBJECT+properties）。
    嵌套结构会让检测端 checkExpressionNode 解析时 ArrayList.get 越界。"""
    return [{
        "name": name, "description": description, "type": data_type,
        "selectable": True, "enableDataI18n": False,
    }]


def value_expression(*, translation: str, result_type: str, context: list[dict],
                     tokens: list[dict], runtime_prefix: str) -> dict[str, Any]:
    """表达式值。runtime_prefix 用于拼 executableExpr（真实样本为固定 base64 前缀）。"""
    return {
        "type": "Expression",
        "expression": {
            "title": "{%s}" % translation,
            "schema": json.dumps({
                "designData": {
                    "expressionTranslation": translation,
                    "resultTypeInfo": result_type,
                    "resultTypeFullName": None,
                    "terminalType": "BACKEND",
                    "isMultiSelect": False,
                    "context": context,
                    "tokens": tokens,
                    "sourceAppName": None,
                },
                "runtimeData": {
                    "executableExpr": runtime_prefix + "".join(t["value"] for t in tokens),
                },
            }, ensure_ascii=False),
        },
    }


def token(kind: str, value: str, desc: str) -> dict[str, str]:
    return {"uid": str(uuid.uuid4()), "type": kind, "value": value, "desc": desc}


# --------------------------------------------------------------------------
# 节点构造：把"插入数据"模板换实体/换字段
# --------------------------------------------------------------------------
def create_entity_node(*, app_id: str | int, app_name: str, entity_name: str,
                       entity_caption: str, entity_id: str | int,
                       attrs: list[tuple[str, str, str, str, dict]],
                       caption: str = "插入数据",
                       template: dict[str, Any] | None = None) -> dict[str, Any]:
    """构造 CREATE_ENTITY 节点。

    attrs: [(字段名, 字段中文, 数据类型, 属性id, value对象), ...]
    """
    node = copy.deepcopy(template or load_template())
    pkg = f"com.seeyon.{app_name}"
    dto_full = f"{pkg}.dto.{_cap(entity_name)}Dto"
    domain = f"{pkg}.domain.entity.{_cap(entity_name)}"

    node["caption"] = caption
    node["actionType"] = "CREATE_ENTITY"
    node["app"] = {"appId": str(app_id), "appName": app_name, "caption": "",
                   "inApp": True, "udcApp": True, "dynamicDependency": False}
    node["structure"] = {
        "key": domain, "id": dto_full, "label": entity_caption,
        "dataType": "DTO", "entity": domain, "dtoType": "MASTER_ENTITY",
        "udcApp": True, "fullName": dto_full, "relationEntity": str(entity_id),
        "entityId": str(entity_id),
        "methodLegal": {"available": True, "complexCondition": True,
                        "seniorMethod": True, "serviceType": "NONE",
                        "interfaceClassFullName": None},
    }
    node["title"] = entity_caption
    node["output"] = {
        "id": dto_full, "javaType": dto_full, "dataType": "DTO", "type": "OBJECT",
        "desc": entity_caption, "appName": app_name, "dtoType": "MASTER_ENTITY",
        "udcApp": True, "relationEntity": str(entity_id),
        "name": f"_CREATE_ENTITY_{node['nodeId'].split('_')[-1]}",
    }
    node["methodLegal"] = copy.deepcopy(node["structure"]["methodLegal"])
    node["mappingType"] = "attrs"

    proto = (template or load_template())["attrs"][0]["attrType"]
    built = []
    for order, (fname, fcap, ftype, attr_id, value) in enumerate(attrs):
        at = copy.deepcopy(proto)
        attr_key = f"{dto_full}.{fname}"
        at.update({
            "id": attr_key, "name": fname, "fullName": attr_key,
            "javaType": _JAVA_BY_TYPE.get(ftype, "java.lang.String"),
            "dataType": ftype, "caption": fcap, "desc": fcap, "sort": order,
            "refApp": app_name,
            "customs": {
                "basicType": False, "mfDataI18n": False,
                "defaultOrExpression": False, "notNull": False,
                "sourceType": "ENTITY", "dataType": ftype,
                "name": fname, "id": str(attr_id),
            },
        })
        built.append({"attrType": at, "value": value})
    node["attrs"] = built
    return node


def replace_node(schema: dict[str, Any], node_id: str, new_node: dict[str, Any]) -> dict[str, Any]:
    """按 nodeId 就地替换（保留连线，因为 lines 按 nodeId 关联）。"""
    for i, n in enumerate(schema["nodes"]):
        if n.get("nodeId") == node_id:
            new_node["nodeId"] = node_id
            if n.get("runAfter") is not None:
                new_node["runAfter"] = n["runAfter"]
            schema["nodes"][i] = new_node
            return schema
    raise KeyError(f"node not found: {node_id}")
