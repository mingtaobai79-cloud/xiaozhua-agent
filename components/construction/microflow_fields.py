"""字段/实体引用工具（定义驱动：字段从 definitions/ 取真实 md5，禁止手写 id/md5）。"""
from __future__ import annotations

import json
from typing import Any

_JAVA_BY_TYPE = {
    "STRING": "java.lang.String", "MULTILINESTRING": "java.lang.String",
    "INTEGER": "java.lang.Integer", "LONG": "java.lang.Long",
    "BIGINTEGER": "java.lang.Long", "DECIMAL": "java.math.BigDecimal",
    "BOOLEAN": "java.lang.Boolean", "DATE": "java.util.Date",
    "DATETIME": "java.util.Date",
}


def entity_structure(entity: dict[str, Any]) -> dict[str, Any]:
    """实体的 structure 引用（RETRIEVE/CREATE_ENTITY 等节点的 structure 块）。"""
    dto = entity["fullName"]
    domain = entity["entity"]
    return {
        "key": domain, "id": dto, "label": entity["caption"],
        "dataType": "DTO", "entity": domain, "dtoType": "MASTER_ENTITY",
        "udcApp": True, "fullName": dto,
        "relationEntity": entity["relationEntityId"],
        "entityId": entity["relationEntityId"],
        "methodLegal": {"available": True, "complexCondition": True,
                        "seniorMethod": True, "serviceType": "NONE",
                        "interfaceClassFullName": None},
    }


def entity_ref(entity: dict[str, Any]) -> dict[str, Any]:
    """实体对象引用（trigger/endNode 的 entityObject，10 键，LIVE 定准）。"""
    domain = entity["entity"]
    dto = entity["fullName"]
    return {
        "key": domain, "id": dto, "label": entity["caption"], "dataType": "DTO",
        "entity": domain, "dtoType": "MASTER_ENTITY", "udcApp": True,
        "fullName": dto, "relationEntity": entity["relationEntityId"],
        "methodLegal": {"available": True, "complexCondition": True,
                        "seniorMethod": True, "serviceType": "NONE",
                        "interfaceClassFullName": None},
    }


def field_attr(entity: dict[str, Any], fname: str, sort: int = 0) -> dict[str, Any]:
    """字段 attrType —— 真实键集（643 条语料统计，83+79 例）。

    ★ 2026-10-30 修正：旧版造了 validate/md5/caption/customs/refType 等 19 键，
      但真实 attrs[].attrType 只有 16 键，且必须带 filterDataType/filterType/filterFullName
      /relationApp —— 缺这几个，设计器「创建变量 → 字段映射」左侧下拉全部红字
      「所选数据已失效，请重新选择」（前端只认自己的绑定键，checkSchema/发布都不报）。

    真实 16 键：name/id/fullName/javaType/dataType/type/desc/description/relationApp/
    refApp/multiSelect/filterDataType/filterType/filterFullName/dataI18n/sort
    关联字段（dataType=ENTITY）另加：refId/relationEntity/relationEntityId/filterRelationEntity
    """
    f = entity["attributes"][fname]
    app = f.get("refApp") or entity.get("refApp")
    a = {
        "name": fname,
        "id": f["id"],
        "fullName": f["fullName"],
        "javaType": f["javaType"],
        "dataType": f["dataType"],
        "type": "OBJECT",
        "desc": f["caption"],
        "description": f.get("description", "") or "",
        "relationApp": app,
        "refApp": app,
        "multiSelect": bool(f.get("multiSelect", False)),
        "filterDataType": f["dataType"],
        "filterType": "OBJECT",
        "filterFullName": f["fullName"],
        "dataI18n": bool(f.get("dataI18n", False)),
        "sort": sort,
    }
    # ★ 2026-10-31：refId/relationEntity/relationEntityId/filterRelationEntity 四个键
    # 无论是否关联字段都必须出现（空串），否则设计器「创建变量→字段映射」左侧红字
    # 「所选数据已失效，请重新选择」。真实语料 20 键恒定存在。
    a["refId"] = f.get("refId", "") or ""
    a["relationEntity"] = f.get("relationEntity") or ""
    a["relationEntityId"] = f.get("relationEntityId") or ""
    a["filterRelationEntity"] = f.get("filterRelationEntity") or ""
    if f.get("dataType") == "ENTITY":
        a["refId"] = f.get("refId", "") or ""
        a["relationEntity"] = f.get("relationEntity") or ""
        a["relationEntityId"] = f.get("relationEntityId") or ""
        a["filterRelationEntity"] = f.get("relationEntity") or ""
    return a

def field_left_param(entity: dict[str, Any], fname: str) -> dict[str, Any]:
    """查询条件 leftParam（RETRIEVE/RETRIEVE_ARRAY/DELETE 的 condition）。"""
    f = entity["attributes"][fname]
    return {
        "id": f["id"], "type": "OBJECT", "javaType": f["javaType"],
        "dto": "_" + fname, "field": fname, "desc": f["caption"],
        "dataType": f["dataType"], "multiSelect": f.get("multiSelect", False),
    }


def field_select_param(entity: dict[str, Any], fname: str, output_name: str,
                       caption: str, position: str = "children") -> dict[str, Any]:
    """引用前序节点出参的字段（SelectParam，实体字段）。
    权威（V16）：name=字段名、description=字段caption、desc=实体caption、outputName=节点出参名。"""
    f = entity["attributes"][fname]
    return {
        "id": f["id"], "type": "OBJECT", "javaType": f["javaType"],
        "dataType": f["dataType"], "dtoType": "MASTER_ENTITY", "udcApp": True,
        "desc": caption, "name": fname, "outputName": output_name,
        "position": position, "relationEntity": entity["relationEntityId"],
        "appName": f.get("refApp"),
        "description": f["caption"],
    }


def basic_select_param(output_name: str, title: str, data_type: str,
                       node_id: str, action_type: str) -> dict[str, Any]:
    """引用基本类型变量（id=null，name=outputName，nodeInfo）。"""
    return {
        "id": None, "javaType": _JAVA_BY_TYPE.get(data_type, "java.lang.String"),
        "dataType": data_type, "type": "OBJECT", "desc": title,
        "name": output_name, "outputName": output_name, "position": "parent",
        "description": title,
        "nodeInfo": {"nodeId": node_id, "type": "ACTIVITY", "actionType": action_type},
    }


def context_variable(input_name: str, entity: dict[str, Any], fname: str) -> dict[str, Any]:
    """引用入参字段（条件右值 CONTEXT_VARIABLE），value 是 JSON 字符串。"""
    f = entity["attributes"][fname]
    dto = entity["fullName"]
    value = json.dumps({
        "key": f"{input_name}{dto}.{fname}", "name": fname, "id": f["id"],
        "appName": f.get("refApp"), "description": f["caption"],
        "position": "children", "path": dto.replace(".", "") + fname,
        "outputName": input_name, "dataType": f["dataType"], "type": "OBJECT",
        "javaType": f["javaType"], "dtoType": "MASTER_ENTITY", "udcApp": True,
        "multiSelect": f.get("multiSelect", False),
        "customs": f.get("customs", {}), "parentLabel": entity["caption"],
    }, ensure_ascii=False)
    return {"type": "CONTEXT_VARIABLE", "value": value, "desc": f["caption"]}


def condition_group(entity: dict[str, Any], left_fname: str, right_value: dict[str, Any],
                    operator: str = "EQ") -> dict[str, Any]:
    """构造一条 GROUP/CONDITION 查询条件。right_value 是 rightParams[0]。

    ★ 条件右值只有三种真实形态：CONTEXT_VARIABLE / CONSTANT / EXPRESSION（实测 337/90/65）。
      没有 "Simple" —— 传 simple() 进来会 BOOT_1001 Parameter Error，这里统一归一成 CONSTANT。
    """
    import uuid as _uuid
    if isinstance(right_value, dict) and right_value.get("type") == "Simple":
        v = right_value.get("simple")
        right_value = {"type": "CONSTANT",
                       "value": "" if v is None else str(v),
                       "desc": right_value.get("desc") if right_value.get("desc") is not None else str(v)}
    return {
        "type": "GROUP", "uuid": str(_uuid.uuid4()),
        "conditions": [{
            "type": "CONDITION",
            "leftParam": field_left_param(entity, left_fname),
            "operator": {"value": operator, "desc": {"EQ": "=", "NEQ": "!=", "GT": ">",
                        "LT": "<", "GE": ">=", "LE": "<="}.get(operator, operator)},
            "rightParams": [right_value],
            "uuid": str(_uuid.uuid4()), "logicalOperator": "AND",
        }],
    }


def constant(value: str, desc: str | None = None) -> dict[str, Any]:
    return {"type": "CONSTANT", "value": value, "desc": desc if desc is not None else value}


def simple(value: Any) -> dict[str, Any]:
    return {"type": "Simple", "simple": value, "desc": value}

def to_context_variable(select_param_ref: dict, entity_model: dict | None = None) -> dict:
    """SelectParam 引用 → 查询条件右值 CONTEXT_VARIABLE（语料 470 条裁决）。

    ★ 查询条件右值只能是三态：CONTEXT_VARIABLE(470) / CONSTANT(193) / EXPRESSION(136)。
      把 SelectParam 直接塞进 rightParams 平台回 `BOOT_1001 Parameter Error`
      （无明细，最难定位的一种）。799 条语料里 SelectParam 出现 0 次。

    平台形态：value 是 **JSON 字符串**，内层键与 SelectParam 相同 +
    parentLabel，且不带 nodeInfo/iconKey 这类 UI 键。
    """
    import json as _json

    if isinstance(select_param_ref, dict) and select_param_ref.get("type") == "CONTEXT_VARIABLE":
        return select_param_ref
    sp = (select_param_ref or {}).get("selectParam") or select_param_ref or {}
    inner = {
        "key": sp.get("key") or ("%s_%s" % (sp.get("outputName", ""), sp.get("id", ""))),
        "name": sp.get("name") or sp.get("description") or "",
        "id": sp.get("id"),
        "appName": sp.get("appName") or ((entity_model or {}).get("refApp") or ""),
        "description": sp.get("description") or sp.get("desc") or "",
        "position": sp.get("position") or "children",
        "path": sp.get("path") or "",
        "outputName": sp.get("outputName"),
        "dataType": sp.get("dataType"),
        "type": sp.get("type") or "OBJECT",
        "javaType": sp.get("javaType"),
        "dtoType": sp.get("dtoType") or "CUSTOM",
        "udcApp": sp.get("udcApp", False),
        "multiSelect": sp.get("multiSelect", False),
        "customs": sp.get("customs") or {"basicType": False},
        "parentLabel": sp.get("parentLabel") or "",
    }
    return {"type": "CONTEXT_VARIABLE",
            "value": _json.dumps(inner, ensure_ascii=False),
            "desc": inner["description"] or inner["name"]}
