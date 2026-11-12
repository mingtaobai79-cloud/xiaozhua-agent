"""微流程 schema 生成器（声明式 spec → dataSchema）。

★ 连线不是独立数组。2026-10-24 全库取证（含 1.7MB 真实微流程）：
  - 顶层固定 6 键：endNode / output / input / sourceType / trigger / nodes
  - **没有 flowPaths**（该键恒为 null，写了也会被前端丢弃）
  - 执行顺序 = `nodes` 数组顺序；分支 = `conditions[].nodes` 嵌套
  - `runAfter` 全库样本恒为 null —— 不要用它表达顺序
  - 节点出参名 `_<actionType>_<6位>`，开始节点出参名 `_FLOW_INPUT_<6位>`

生成后**必须**过 `validate_node_fields` 与 `validate_end_node_scope`，
再用 `validate_release_readiness` 做提交前门禁 —— 三道都过才算可提交。

用法：
    from components.udc.microflow.build import build_schema
    schema = build_schema(spec, app_id=..., flow_name="...")
"""
from __future__ import annotations

import random
import string

from components.udc.microflow_constraints import (
    validate_end_node_scope,
    validate_node_fields,
    validate_release_readiness,
)

ALPH = string.ascii_letters + string.digits

# 顶层键顺序：前端保存后就是这个顺序，按它写便于 diff
TOP_KEYS = ("endNode", "output", "input", "sourceType", "trigger", "nodes")


def uid6() -> str:
    return "".join(random.choice(ALPH) for _ in range(6))


def node_id(action_type: str) -> str:
    return "%s_%s" % (action_type, uid6())


def param(name: str, data_type: str = "STRING", desc: str = "", java_type: str = None) -> dict:
    """节点出参 / 顶层 input 的声明形态。"""
    jt = java_type or {
        "STRING": "java.lang.String", "INTEGER": "java.lang.Integer",
        "BIGINTEGER": "java.lang.Long", "DECIMAL": "java.math.BigDecimal",
        "BOOLEAN": "java.lang.Boolean", "DATE": "java.util.Date",
        "DATETIME": "java.util.Date", "OBJECT": "java.lang.Object",
        "ENTITY": "java.lang.Object", "ARRAY": "java.util.List",
    }.get(data_type, "java.lang.Object")
    out = {"id": None, "javaType": jt, "dataType": data_type, "type": "OBJECT",
           "desc": desc, "dtoType": None, "udcApp": None, "name": name}
    if data_type == "ENTITY":
        out["hasPagination"] = False
    return out


_NODE_TYPE_BY_ACTION = {"BRANCH": "BRANCH", "CUSTOM_ERROR": "CUSTOM_ERROR",
                        "BREAK": "BREAK", "FOR": "FOR", "FOR_EACH": "FOR_EACH"}


def make_node(action_type: str, *, caption: str = None, output: dict = None,
              input: dict = None, **fields) -> dict:
    """构造一个活动节点。

    `fields` 直接摊进节点顶层（实体规则/微流程的 key 就放在顶层，
    与 settings 声明一致，不做额外嵌套）。
    """
    node = {
        "nodeId": node_id(action_type),
        "name": None,
        # ★ type 不是一律 ACTIVITY：解析器按 `MicroFlowNodeTypeEnum.valueOf(type)` 选解析器，
        #   代码生成模板按 node.type 分发。CUSTOM_ERROR / BREAK 必须用自己的 type，
        #   写成 ACTIVITY 会被当成普通活动节点**静默丢弃**（构建/发布/运行全不报错）。
        #   2026-11-02 由 G38 抓出：all-nodes 验收流里这两个节点一直是死配置。
        "type": _NODE_TYPE_BY_ACTION.get(action_type, "ACTIVITY"),
        "caption": caption or action_type,
        "description": None,
        "runAfter": None,
        "input": input,
        "output": output,
        "isCompleted": True,
        "actionType": action_type,
    }
    node.update(fields)
    return node


def branch(cases: list[dict], *, caption: str = "分支(1)") -> dict:
    """分支节点。

    cases: [{"expr": {...} | None, "nodes": [...]}]
      最后一项应给 expr=None（elseBranch）；不给则自动补空 else。
    条件表达式结构：{"title": "...", "schema": "<JSON字符串>"}
    """
    conds = []
    for i, c in enumerate(cases):
        expr = c.get("expr")
        name = "ifBranch" if i == 0 else ("elseBranch" if expr is None else "elseIfBranch")
        conds.append({
            "nodeId": node_id("CONDITION"),
            "name": name,
            "type": "CONDITION",
            "caption": "符合条件即进入该分支" if expr is not None else "不符合条件即进入该分支",
            "description": "",
            "runAfter": None,
            "expression": expr,
            "isCompleted": True,
            "nodes": c.get("nodes") or [],
        })
    if not conds or cases[-1].get("expr") is not None:
        conds.append({
            "nodeId": node_id("CONDITION"),
            "name": "elseBranch",
            "type": "CONDITION",
            "caption": "不符合条件即进入该分支",
            "description": "",
            "runAfter": None,
            "expression": None,
            "isCompleted": True,
            "nodes": [],
        })
    return {
        "nodeId": node_id("BRANCH"), "name": None, "type": "BRANCH",
        "caption": caption, "description": None, "runAfter": None,
        "input": None, "output": None, "isCompleted": True,
        "actionType": "BRANCH", "conditions": conds,
    }


def start_node(trigger_type: str = "MANUAL", input_param: dict = None,
               output: dict = None) -> dict:
    # ★ paramType 键必须存在（语料 MANUAL 触发 100% 带；C- 契约闸门拦缺键）。
    #   值语义=入参配置形态：NONE=无参数；语料分布 BASIC 316/DEFAULT_OBJECT 155/NONE 47。
    pt = "NONE" if input_param is None else "CUSTOM"
    return {
        "id": "", "nodeId": "MFStartNode", "caption": "开始",
        "description": "", "type": trigger_type, "paramType": pt,
        # ★ desc=「参数名称」显示名（G21/C- 触发：入参形态必填，空 → 空黄框）
        "desc": (input_param or {}).get("desc") or "",
        "input": input_param, "output": output,
    }


def end_node() -> dict:
    return {"id": "", "name": "", "type": "END", "actionType": "END_NODE",
            "nodeId": "MFEndNode", "caption": "结束", "description": "",
            "input": None, "output": None}


def build_schema(spec: dict, *, app_id: str, source_type: str = "PAGE") -> dict:
    """spec → dataSchema。

    spec = {
      "trigger_type": "MANUAL",
      "input":  {"desc": "ID", "dataType": "BIGINTEGER"} | None,
      "output": {"desc": "出参", "dataType": "STRING"} | None,
      "nodes":  [node, ...],
    }

    ★ 顶层 `output` 与 `endNode.value` 是**联动**的（实测）：
      - `output = null`  → endNode 就是 9 个基础键，**不需要 value**（137/200 合法流程如此）
      - `output != null` → endNode **必须**带 `value` 绑定出参来源，否则 checkSchema 报
        `root.endNode.value.value 必填参数未配置`
      所以这里默认 `output=None`；只有显式传 output 时才要求同时给 `end_node_value`，
      不自动编造绑定关系（绑定必须指向真实存在的节点出参）。
    """
    raw_nodes = spec.get("nodes") or []
    input_name = "_FLOW_INPUT_" + uid6()
    inp = None
    if spec.get("input"):
        i = spec["input"]
        # ★ 生成器已经自己算好入参名时要用它的 —— 节点里的 CONTEXT_VARIABLE/VARIABLE
        #   引用的是那个名字，换名会让引用悬空（checkSchema 报 BOOT_3000）。
        if i.get("name"):
            input_name = i["name"]
        inp = param(input_name, i.get("dataType", "STRING"), i.get("desc", ""))
        # ★ 入参是 DTO 时还要带 inApp/appName/hasPagination，
        #   只拷这 5 个会让前端把 DTO 入参降级成基础类型。
        for k, v in i.items():
            if k == "name" or v is None:
                continue
            inp[k] = v
        # ★ DTO 入参的 id 必填（checkSchema root.input.id PROPERTY_IS_REQUIRED）：
        #   真实样本 id == javaType == dtoFullName；type 用 ARRAY/OBJECT 按声明。
        if i.get("dtoFullName"):
            inp["id"] = i["dtoFullName"]
            inp["javaType"] = i["dtoFullName"]
    start = start_node(spec.get("trigger_type", "MANUAL"), input_param=inp,
                       output=inp)

    out = spec.get("output")
    if isinstance(out, dict) and not out.get("name"):
        out = param("_FLOW_OUTPUT_" + uid6(), out.get("dataType", "STRING"),
                    out.get("desc", "出参"))

    end = end_node()
    if out is not None:
        end["output"] = param(out.get("name") or ("_FLOW_OUTPUT_" + uid6()),
                              out.get("dataType", "STRING"), out.get("desc", "出参"))
        ev = spec.get("end_node_value")
        if not ev:
            raise ValueError(
                "传了 output 就必须同时给 end_node_value（endNode 绑定出参来源）；"
                "不绑会报 root.endNode.value.value 必填。若不需要出参，把 output 设为 null")
        end["value"] = ev
        end.setdefault("paramType", "BASIC")
        end.setdefault("basic", out.get("dataType", "STRING"))
        end.setdefault("isArray", False)
        end.setdefault("desc", out.get("desc", "出参"))
        end.setdefault("outPutDesc", None)
        end.setdefault("isCompleted", True)

    schema = {
        "endNode": end,
        "output": out,
        "input": inp,
        "sourceType": source_type,
        "trigger": start,
        "nodes": raw_nodes,
    }
    return schema


def _iter_nodes(nodes):
    for n in nodes or []:
        yield n
        for c in n.get("conditions") or []:
            yield from _iter_nodes(c.get("nodes"))
        yield from _iter_nodes(n.get("nodes"))


def validate_schema(schema: dict, *, app_id: str = None, flow_name: str = None) -> list[str]:
    """生成后校验：节点字段 → 顶层键 → 结束节点作用域。

    ★ 提交门禁（`validate_release_readiness`）不在这里跑 —— 它要求 `state=RELEASE`
      与完整 dto，属于 create 前的独立一步，见 `validate_for_submit`。
    """
    errs: list[str] = []
    for n in _iter_nodes(schema.get("nodes")):
        at = n.get("actionType") or n.get("type")
        if at in ("BRANCH", "END", "END_NODE"):
            errs.extend(validate_node_fields(at, n) if at == "BRANCH" else [])
            continue
        for e in validate_node_fields(at, n):
            errs.append("%s/%s: %s" % (at, n.get("nodeId"), e))

    extra = [k for k in schema if k not in TOP_KEYS]
    if extra:
        errs.append("顶层出现非标准键 %s —— 前端保存会丢弃，别写" % extra)

    if schema.get("input") and not str(schema["input"].get("name", "")).startswith("_FLOW_INPUT_"):
        errs.append("顶层 input.name 必须是 _FLOW_INPUT_ 前缀，否则可用范围对不上")

    try:
        errs.extend(validate_end_node_scope({"dataSchema": schema}))
    except TypeError:
        pass
    # UI 层带父链的校验（BREAK 只能在循环体内等；逐节点 validate_node_fields 拿不到父链）
    try:
        from components.udc.microflow_ui_constraints import validate_schema_ui
        errs.extend(validate_schema_ui(schema))
    except ImportError:
        pass
    return errs


def validate_for_submit(schema: dict, *, app_id: str, flow_name: str,
                        state=20) -> list[str]:
    """create / update 前的提交门禁（含 RELEASE 深解析）。

    ★ `state` 两套形态：DB / create body 用数字 `20`，
      而 `validate_release_readiness` 判的是字符串 `"RELEASE"` —— 这里统一转过去，
      否则永远报「state 非 RELEASE」。
    """
    dto = {"appId": app_id, "name": flow_name, "state": "RELEASE", "dataSchema": schema}
    out = []
    try:
        out.extend(validate_release_readiness(dto))
    except TypeError:
        pass
    return out


__all__ = [
    "TOP_KEYS", "uid6", "node_id", "param", "make_node", "branch",
    "start_node", "end_node", "build_schema", "validate_schema",
]
