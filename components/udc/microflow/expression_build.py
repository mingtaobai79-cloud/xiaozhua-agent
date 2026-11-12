"""从流程节点出参构造表达式 context 树，并走 /transform 产出真实表达式。

## 为什么需要这个模块

BRANCH 条件、变量赋值里的表达式**不能手写 `executableExpr`**——
它的前缀是服务端产物，客户端造不出来。必须：
    context(变量树) + tokens → POST /expression/check → /expression/transform
    → 拿到 designData + runtimeData.executableExpr

## context 树结构（照抄真实活体 expression.schema 的 designData.context）

三级嵌套，一层节点、两层出参、三层字段：

```
{name: <节点出参名>, description: <节点标题>, type:"OBJECT", selectable:false,
 properties: [
   {name: <同节点出参名>, description: <出参desc>, type:"OBJECT"|"ARRAY", selectable:true,
    uniformityParams: {paramId: <DTO>, paramCategory:"OBJECT",
                       extensionProperties: '{"id":"<DTO>"}'},
    properties: [ 每个字段 {name, description, type:<dataType>, uniformityParams:{...}} ]}
 ],
 uniformityParams: {paramId:<DTO>, paramCategory:"DTO",
                    extensionProperties:'{"id":"<DTO>","javaType":"<DTO>"}'}}
```

## VARIABLE token 的 value 是三级

`<节点出参名>.<节点出参名>.<字段名>`
（注意是三级，不是两级；写两级报 FORMULA_6058 CVariable does not exist）
"""
from __future__ import annotations

import json
import uuid

from .expression_api import (
    build_save_dto, check_expression_remote, transform_expression_remote,
)

_JAVA = {
    "STRING": "java.lang.String", "INTEGER": "java.lang.Integer",
    "BIGINTEGER": "java.lang.Long", "BOOLEAN": "java.lang.Boolean",
    "DECIMAL": "java.math.BigDecimal", "DOUBLE": "java.lang.Double",
    "DATETIME": "java.util.Date", "DATE": "java.util.Date",
}


def _uid() -> str:
    return str(uuid.uuid4())


def field_node(fname: str, fmeta: dict) -> dict:
    """context 第三层：字段节点。"""
    dt = fmeta.get("dataType") or "STRING"
    dto = fmeta.get("id") or ""
    ext = {"id": dto, "relationType": "NONE", "javaType": _JAVA.get(dt, dt)}
    return {
        "name": fname,
        "description": fmeta.get("caption") or fname,
        "type": dt if dt not in ("ENTITY",) else "BIGINTEGER",
        "selectable": True,
        "enableDataI18n": False,
        "uniformityParams": {
            "paramId": dto,
            "paramCategory": dt,
            "extensionProperties": json.dumps(ext, ensure_ascii=False),
            "pageNodeExtension": None,
        },
    }


def basic_scalar_context_entry(name: str, title: str, data_type: str) -> dict:
    """BASIC 标量变量（SUM/SIZE/MIN/MAX/CREATE_VARIABLE 出参）的 context 顶层项。

    ★ 两级 `X.X`，不是三级 DTO 树。2026-11-03 用 /expression/check 反推出的合法形态：
      顶层 OBJECT + 子项 type=<标量类型>（BIGINTEGER/INTEGER/...），无 properties。
      token 侧对应 `_go` 的 `field==outputName` 分支（value="X.X"）。
    """
    java = _JAVA.get(data_type, data_type)
    ext = json.dumps({"id": java, "relationType": "NONE", "javaType": java})
    return {
        "name": name,
        "description": title or name,
        "type": "OBJECT",
        "selectable": False,
        "enableDataI18n": False,
        "properties": [{
            "name": name,
            "description": title or name,
            "type": data_type,
            "selectable": True,
            "enableDataI18n": False,
            "uniformityParams": {
                "paramId": java, "paramCategory": "OBJECT",
                "extensionProperties": ext, "pageNodeExtension": None,
            },
        }],
        "uniformityParams": {
            "paramId": java, "paramCategory": "DTO",
            "extensionProperties": json.dumps({"id": java, "javaType": java}),
            "pageNodeExtension": None,
        },
    }


def node_context_entry(node: dict, entity_model: dict) -> dict:
    """把流程里一个节点转成 context 顶层一项。

    node 需要有：output.name、title/caption、structure（实体标识）
    entity_model 提供 attributes（字段元数据）
    """
    o = node.get("output") or {}
    out_name = o.get("name")
    if not out_name:
        raise ValueError("节点 %r 没有 output.name" % node.get("nodeId"))
    ent = node.get("structure") or {}
    dto = ent.get("id") or o.get("id") or ent.get("fullName")
    if not dto:
        raise ValueError("节点 %r 缺 DTO 标识（structure.id / output.id）" % node.get("nodeId"))
    is_array = o.get("dataType") == "DTO" and o.get("type") == "ARRAY"

    attrs = (entity_model or {}).get("attributes") or {}
    fields = [field_node(fn, fm) for fn, fm in sorted(attrs.items())]

    out_item = {
        "name": out_name,
        "description": node.get("title") or node.get("caption") or out_name,
        "type": "ARRAY" if is_array else "OBJECT",
        "selectable": True,
        "enableDataI18n": False,
        "uniformityParams": {
            "paramId": dto, "paramCategory": "OBJECT",
            "extensionProperties": json.dumps({"id": dto}, ensure_ascii=False),
            "pageNodeExtension": None,
        },
        "properties": fields,
    }
    if is_array:
        out_item["items"] = {"type": "OBJECT", "properties": []}

    return {
        "name": out_name,
        "description": node.get("caption") or out_name,
        "type": "OBJECT",
        "selectable": False,
        "enableDataI18n": False,
        "properties": [out_item],
        "uniformityParams": {
            "paramId": dto, "paramCategory": "DTO",
            "extensionProperties": json.dumps(
                {"id": dto, "javaType": dto}, ensure_ascii=False),
            "pageNodeExtension": None,
        },
    }


def var_token(node: dict, field: str) -> dict:
    """引用节点字段的 VARIABLE token（value 是三级路径）。"""
    o = node.get("output") or {}
    n = o.get("name")
    return {"uid": _uid(), "type": "VARIABLE",
            "value": "%s.%s.%s" % (n, n, field),
            "desc": "%s.%s" % (node.get("title") or n, field)}


def op_token(value: str) -> dict:
    return {"uid": _uid(), "type": "OPERATOR", "value": value, "desc": value}


def const_token(value, dtype: str = "STRING") -> dict:
    v = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return {"uid": _uid(), "type": "CONSTANT", "value": v, "desc": v}


def func_token(name: str, arg_groups: list, desc: str = "") -> dict:
    return {"uid": _uid(), "type": "FUNCTION", "value": name, "desc": desc or name,
            "subOps": arg_groups}


def build_dto(tokens: list, context: list, result_type: str = "BOOLEAN",
              result_full: str | None = None) -> dict:
    """拼 ExpressionSaveDto（/check 与 /transform 的入参）。"""
    dto = {
        "resultTypeInfo": result_type,
        "schemas": context,
        "tokens": tokens,
        "isMultiSelect": False,
        "terminalSupportType": "BACKEND",
        "expressionTranslation": "",
    }
    if result_full:
        dto["resultTypeFullName"] = result_full
    return dto


def make_expression(d, tokens: list, context: list, result_type: str = "BOOLEAN",
                    want_translation: str | None = None) -> dict:
    """走 /check + /transform，返回可直接落库的 expression 对象。

    返回 {title, schema}，且 schema 里 designData/runtimeData 都是服务端产物。
    失败抛 RuntimeError（不返回半成品）。
    """
    dto = build_dto(tokens, context, result_type)
    chk = check_expression_remote(d, dto)
    if not chk.get("ok"):
        raise RuntimeError("表达式 /check 未通过: %s" % json.dumps(chk, ensure_ascii=False)[:500])
    tr = transform_expression_remote(d, dto)
    if not tr.get("ok"):
        raise RuntimeError("表达式 /transform 失败: %s" % json.dumps(tr, ensure_ascii=False)[:500])
    dd = tr.get("designData") or {}
    ee = tr.get("executableExpr") or ""
    if not ee:
        raise RuntimeError("transform 未返回 executableExpr")
    schema = json.dumps({"designData": dd,
                         "runtimeData": {"executableExpr": ee}},
                        ensure_ascii=False)
    title = (dd.get("expressionTranslation") or want_translation or "")
    return {"title": title, "schema": schema}


def field_equals(node: dict, field: str, value, dtype: str = "BOOLEAN",
                 context: list | None = None) -> dict:
    """构造「节点.字段 == 常量」表达式（布尔结果）。

    dtype 决定常量形态：BOOLEAN 用 true/false，其它用字面量。
    """
    if dtype == "BOOLEAN":
        lit = "true" if value in (True, "true", "True", 1) else "false"
    else:
        lit = str(value)
    tokens = [var_token(node, field), op_token("=="), const_token(lit)]
    ctx = context if context is not None else []
    return {"tokens": tokens, "context": ctx}


def text_contains(node: dict, field: str, needle: str,
                  context: list | None = None) -> dict:
    """构造「文本包含(节点.字段, 'needle')」表达式。"""
    tokens = [func_token("containsText",
                         [[var_token(node, field)], [const_token(needle)]],
                         "文本包含")]
    ctx = context if context is not None else []
    return {"tokens": tokens, "context": ctx}
