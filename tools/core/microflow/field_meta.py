"""字段元数据 → 节点 attrType / 条件 / 排序的真实构造器（供 all_nodes_demo 复用）。

证据（全部取自 udc_microflow_info 真实节点）：
  · 条件 leftParam：{"id": "<dto全名>.<字段>", "dto": "_<字段名>", "field": "<字段名>"}
    ★ dto 是「_ + 字段名」，不是「_ + 实体名」（这是之前过滤条件的老毛病）
  · 排序 sortParams：{"sortType": "ASC|DESC", "attrType": {完整属性对象}}
  · CREATE_ENTITY.attrs[]：{"attrType": {...}, "value": {"type": "Simple|SelectParam|Expression", ...}}
  · CHANGE_VARIABLE(实体)：selectParam + mappingType="attrs" + attrs[]
"""
from __future__ import annotations

import json
import uuid

JAVA_BY_TYPE = {
    "STRING": "java.lang.String", "BIGINTEGER": "java.lang.Long",
    "INTEGER": "java.lang.Integer", "DECIMAL": "java.math.BigDecimal",
    "BOOLEAN": "java.lang.Boolean", "DATE": "java.util.Date",
    "DATETIME": "java.util.Date", "TIME": "java.util.Date",
}


def dto_full(app_name: str, cls: str) -> str:
    return "com.seeyon.%s.dto.%sDto" % (app_name, cls)


def attr_type(app_name: str, cls: str, field: str, meta: dict) -> dict:
    """完整属性对象（排序 / attrs.attrType 通用）。"""
    dto = dto_full(app_name, cls)
    dt = meta["dataType"]
    return {
        "validate": True, "id": "%s.%s" % (dto, field), "name": field,
        "fullName": "%s.%s" % (dto, field),
        "md5": str(meta.get("md5") or ""),
        "javaType": meta.get("javaType") or JAVA_BY_TYPE.get(dt, "java.lang.Object"),
        "dataType": dt, "type": "OBJECT", "caption": meta["caption"],
        "desc": meta["caption"], "description": "",
        "refId": "", "refApp": app_name, "refType": "NONE",
        "multiSelect": False, "dataI18n": False,
        "sort": int(meta.get("sort") or 0),
        "customs": {
            "basicType": False, "mfDataI18n": False, "defaultOrExpression": False,
            "notNull": bool(meta.get("notNull") or False),
            "sourceType": "ENTITY", "dataType": dt, "name": field,
            "id": str(meta["id"]),
        },
    }


def sort_params(app_name: str, cls: str, field: str, meta: dict, direction="DESC") -> list:
    return [{"sortType": direction,
             "attrType": attr_type(app_name, cls, field, meta)}]


def simple(v) -> dict:
    return {"type": "Simple", "simple": v, "desc": str(v)}


def constant(v) -> dict:
    """条件右值必须是 CONSTANT / EXPRESSION / CONTEXT_VARIABLE。

    ★ 用 {"type":"Simple",...} 当条件右值会让整个请求解析失败：
      平台返回 BOOT_1001「参数错误」，不指字段、不指节点（实测二分定位）。
    """
    return {"type": "CONSTANT", "value": v, "desc": str(v)}


def condition(app_name: str, cls: str, field: str, meta: dict, right: dict) -> list:
    """条件组：[{type:GROUP, conditions:[{type:CONDITION, leftParam, operator, rightParams}]}]"""
    dto = dto_full(app_name, cls)
    dt = meta["dataType"]
    return [{
        "type": "GROUP", "uuid": str(uuid.uuid4()),
        "conditions": [{
            "type": "CONDITION",
            "leftParam": {
                "id": "%s.%s" % (dto, field),
                "type": "OBJECT",
                "javaType": meta.get("javaType") or JAVA_BY_TYPE.get(dt, "java.lang.Object"),
                # ★ 关键：dto 用「_+字段名」
                "dto": "_" + field,
                "field": field,
                "desc": meta["caption"],
                "dataType": dt,
                "multiSelect": False,
            },
            "operator": {"value": "EQ", "desc": "="},
            "rightParams": [right],
            "uuid": str(uuid.uuid4()),
            "logicalOperator": "AND",
        }],
    }]


def select_param_value(app_name: str, cls: str, field: str, meta: dict,
                       output_name: str, *, parent_label="") -> dict:
    """attrs[].value = {type:SelectParam, selectParam:{...}}（引用上游变量字段）。"""
    dto = dto_full(app_name, cls)
    dt = meta["dataType"]
    at = attr_type(app_name, cls, field, meta)
    return {"type": "SelectParam", "selectParam": {
        "key": "%s%s.%s" % (output_name, dto, field),
        "name": field, "id": "%s.%s" % (dto, field),
        "appName": app_name, "description": meta["caption"], "position": "children",
        "path": ("%s.%s" % (dto, field)).replace(".", ""),
        "outputName": output_name, "dataType": dt, "type": "OBJECT",
        "javaType": at["javaType"], "dtoType": "CUSTOM", "udcApp": True,
        "multiSelect": False, "customs": at["customs"], "parentLabel": parent_label}}


def boolean_expression(value: bool = True) -> dict:
    """真实可执行表达式（engine 编译产物），来自 expression_templates.json。"""
    from pathlib import Path
    tpl = json.loads(Path(__file__).with_name("expression_templates.json")
                     .read_text(encoding="utf-8"))["boolean_true"]
    out = json.loads(json.dumps(tpl))
    if not value:
        inner = json.loads(out["schema"])
        inner["designData"]["expressionTranslation"] = "false "
        for tok in inner["designData"].get("tokens") or []:
            if tok.get("value") == "true":
                tok["value"] = tok["desc"] = "false"
        out["schema"] = json.dumps(inner, ensure_ascii=False)
        out["title"] = "false "
    return out
