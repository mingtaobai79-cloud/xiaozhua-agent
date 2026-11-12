"""节点构造 v2 补充：列表/映射/逻辑/批量/数据加工节点。"""
from __future__ import annotations

import os
from typing import Any

from .microflow_fields import (
    entity_structure, field_attr, simple, condition_group,
)
from .microflow_nodes_v2 import _entity_output, _write_output
from .node_builder import NodeBuilder

# 前端 treeListSelector 的选项 label（映射取值「数据类型」等用它回显）
_DT_LABELS: dict[str, str] = {
    "STRING": "文本", "INTEGER": "整数", "BIGINTEGER": "长整数",
    "DECIMAL": "小数", "BOOLEAN": "布尔", "DATE": "日期", "DATETIME": "日期时间",
}


def _list_ref(src_node: dict[str, Any], builder: NodeBuilder) -> dict[str, Any]:
    """引用前序列表的 selectParam。

    ★ 必须带 `dtoType`：真实 654 个 LIST_OPERATION 样本里 598 个都有，
      缺它 checkSchema 直接报 `selectParam.dtoType PROPERTY_IS_REQUIRED`。
      引实体列表时为 MASTER_ENTITY / SUB_ENTITY，引基础类型列表时为 CUSTOM。
    """
    out = src_node.get("output") or {}
    is_entity = out.get("dataType") == "DTO"
    ref = {
        "id": out.get("id"), "javaType": out.get("javaType", "java.lang.String"),
        "dataType": out.get("dataType", "STRING"), "type": "ARRAY",
        "desc": src_node.get("title") or "", "name": builder.output_name(src_node),
        "position": "parent", "outputName": builder.output_name(src_node),
        "description": src_node.get("title") or "",
        "dtoType": ("MASTER_ENTITY" if is_entity
                    else (out.get("dtoType") or "CUSTOM")),
        "nodeInfo": {"nodeId": src_node["nodeId"], "type": "ACTIVITY",
                     "actionType": src_node.get("actionType")},
        "iconKey": "LinedEnquiryForm" if is_entity else "LinedCreateBar",
        "parentLabel": "", "disabled": False,
    }
    if is_entity:
        ref["udcApp"] = True
        ref["appName"] = out.get("appName")
        ref["path"] = out.get("path")
        ref["relationEntity"] = out.get("relationEntity")
        ref["relationEntityFullName"] = out.get("relationEntityFullName")
    return ref


def _basic_ref(src_node: dict[str, Any], builder: NodeBuilder) -> dict[str, Any]:
    out = src_node.get("output") or {}
    return {
        "id": None, "javaType": out.get("javaType", "java.lang.String"),
        "dataType": out.get("dataType", "STRING"),
        "type": out.get("type", "OBJECT"),   # ★ 用源节点 output.type，List2multiAssociation 源是 ARRAY
        "desc": src_node.get("title") or "", "name": builder.output_name(src_node),
        "position": "parent", "outputName": builder.output_name(src_node),
        "description": src_node.get("title") or "",
        "nodeInfo": {"nodeId": src_node["nodeId"], "type": "ACTIVITY",
                     "actionType": src_node.get("actionType")},
    }


# --------------------------------------------------------------------------
# 列表活动
# --------------------------------------------------------------------------
def create_list(builder: NodeBuilder, title: str, data_type: str = "STRING",
                caption: str = "创建列表",
                default_value: Any = None) -> dict[str, Any]:
    """创建列表。

    ★ `value` 必须是**数组**（真实 239 个样本：181 个 `[]`、42 个 `[SelectParam]`、16 个 null），
      **不是** `{type:"Simple",...}` 单值对象。写成 Simple 对象抽屉回显为空。
      - 空列表：`value: []`
      - 带默认值：`value: [{type:"Simple", simple:..., desc:...}]`（基础类型）
        或 `value: [SelectParam]`（引用前序列表，42 个真实样本都是这种）
    """
    node = builder.build("CREATE_LIST", caption=caption)
    node["paramType"] = "BASIC"
    node["title"] = title
    node["dataType"] = data_type
    node["structure"] = None   # 契约 C-C：键须在（语料 BASIC 731 条 null 合法）
    if default_value is None:
        node["value"] = []                     # 真实最常见形态（181/239）
    else:
        node["value"] = [{"type": "Simple", "simple": default_value,
                          "desc": str(default_value)}]
    node["output"] = {
        "id": None,
        "javaType": {"STRING": "java.lang.String", "INTEGER": "java.lang.Integer",
                     "BIGINTEGER": "java.lang.Long"}.get(data_type, "java.lang.String"),
        "dataType": data_type, "type": "ARRAY", "desc": title, "name": "_" + node["nodeId"],
    }
    return node


CHANGE_LIST_ACTIONS = ("ADD", "REPLACE", "CLEAR", "REMOVE")


def _element_ref(item_node: dict[str, Any], builder: NodeBuilder) -> dict[str, Any]:
    """实体对象引用（dataSource 用）。基础类型请用 _basic_ref。"""
    o = item_node.get("output") or {}
    dto = o.get("id") or o.get("javaType") or ""
    on = builder.output_name(item_node)
    return {
        "description": item_node.get("title") or o.get("desc") or "",
        "dataType": "DTO", "outputName": on, "position": "parent",
        "udcApp": True, "dtoType": "SUB_ENTITY",
        "appName": o.get("appName") or builder.app_name,
        "path": str(dto).replace(".", ""), "id": dto,
        "name": str(dto).replace(".", ""), "type": "OBJECT", "javaType": dto,
        "relationEntity": o.get("relationEntity"),
        "relationEntityFullName": o.get("relationEntityFullName"),
        "nodeInfo": {"nodeId": item_node["nodeId"], "type": "ACTIVITY",
                     "actionType": item_node.get("actionType")},
        "key": on + str(dto), "iconKey": "LinedModifyVariable",
        "parentLabel": "", "disabled": False,
    }


def change_list(builder: NodeBuilder, list_node: dict[str, Any],
                src_node: dict[str, Any] | None = None,
                action: str = "ADD", caption: str = "修改变量(列表)",
                count_attrs: list | None = None) -> dict[str, Any]:
    """修改列表。四种动作的真实形态（317 条样本实测）：

      ADD     266 条  selectParam + dataSource(元素)
      REPLACE  28 条  selectParam + dataSource(元素)
      CLEAR    15 条  只有 selectParam —— **没有 dataSource**
      REMOVE    8 条  selectParam + dataSource + countAttrs（按 id 匹配要删的元素）

    ★ 枚举里没有 DELETE。早期构造器默认 action="ADD" 且无条件写 dataSource，
      还塞了个语料里不存在的 `value` 键 —— CLEAR 会因此带上非法 dataSource。
    """
    act = (action or "ADD").upper()
    if act == "DELETE":
        raise ValueError("CHANGE_LIST 没有 DELETE 动作，真实枚举是 %s"
                         % (CHANGE_LIST_ACTIONS,))
    if act not in CHANGE_LIST_ACTIONS:
        raise ValueError("CHANGE_LIST action=%r 非法，真实枚举是 %s"
                         % (action, CHANGE_LIST_ACTIONS))
    node = builder.build("CHANGE_LIST", caption=caption)
    node["selectParam"] = _list_ref(list_node, builder)
    node["action"] = act
    if act == "CLEAR":
        # 模板是从真实 ADD 样本复制来的，自带 dataSource/countAttrs 骨架，必须清掉
        node.pop("dataSource", None)
        node.pop("countAttrs", None)
        return node
    if src_node is None:
        raise ValueError("CHANGE_LIST action=%s 需要 dataSource（元素或列表）" % act)
    # 真实语料：REPLACE 25/28、REMOVE 8/8 的 dataSource 是**列表**（type=ARRAY）；
    # ADD 两种都有（元素 OBJECT 125 条 / 列表 ARRAY 52 条）。
    # ★ 但 REPLACE 另有 3 条是**单元素 OBJECT**（用首元素整体替换），
    #   所以 REPLACE 不能按动作写死 ARRAY —— 按来源节点出参类型选，
    #   否则 G31 会报「引用 type=ARRAY 与出参声明 OBJECT 不一致」。
    out = src_node.get("output") or {}
    if act == "REMOVE" or (act == "REPLACE" and out.get("type") == "ARRAY") \
            or (act == "ADD" and out.get("type") == "ARRAY"):
        ds = _list_ref(src_node, builder)
        ds["position"] = "parent"
        node["dataSource"] = ds
    else:
        node["dataSource"] = _element_ref(src_node, builder)
    if act == "REMOVE":
        node["countAttrs"] = count_attrs or []
        if not node["countAttrs"]:
            raise ValueError("CHANGE_LIST REMOVE 需要 countAttrs（按哪些字段匹配元素）")
    return node


def list_operation(builder: NodeBuilder, list_node: dict[str, Any],
                   op_type: str = "SIZE", title: str = "列表处理后结果",
                   caption: str = "列表处理", sort_params: list | None = None,
                   count_attrs: list | None = None,
                   index_value=None, second_node: dict[str, Any] | None = None,
                   expression: dict[str, Any] | None = None,
                   group_by: list | None = None) -> dict[str, Any]:
    """列表操作。出参类型随操作类型走，不能一律 INTEGER。

    真实 654 条样本的 op × 出参：
      FIRST_ONE/LAST_ONE/PICK_ONE → OBJECT（元素；93+9+34 条）
      SIZE/MIN/MAX/SUM            → OBJECT 标量（INTEGER/DECIMAL）
      FILTER/SORT/DISTINCT/MAP/...→ ARRAY
    ★ 早期这里把出参写死 INTEGER，取元素（FIRST_ONE）就造不出来。
    """
    node = builder.build("LIST_OPERATION", caption=caption)
    node["selectParam"] = _list_ref(list_node, builder)
    node["operationType"] = {"type": op_type}
    node["title"] = title
    src = list_node.get("output") or {}
    # ★ 各操作的真实附加键（654 条语料裁决）：
    #   SORT → sortParams[{sortType, attrType}]；SUM/MIN/MAX/MAP → countAttrs[字段]；
    #   PICK_ONE → indexValue{Simple}；DISTINCT/LAST_ONE/SIZE → 无附加键。
    if op_type == "FILTER":
        # 过滤条件必须带平台编译过的表达式（microflow_filter.build_filter_expression）
        if not expression:
            raise ValueError("LIST_OPERATION FILTER 需要 expression（过滤条件）")
        node["expression"] = expression
    if second_node is not None:
        # SUBTRACT / INTERSECT 是二元操作：selectParam=被减/左，operationParam=减数/右
        node["operationParam"] = _list_ref(second_node, builder)
    if sort_params:
        node["sortParams"] = sort_params
    if count_attrs:
        node["countAttrs"] = count_attrs
    if op_type == "GROUP_AND_SUM":
        # 分组汇总：groupByAttrs=分组字段，countAttrs=被汇总字段（语料唯一 1 条样本）
        if not group_by:
            raise ValueError("GROUP_AND_SUM 需要 group_by（分组字段）")
        node["groupByAttrs"] = group_by
    if op_type == "PICK_ONE":
        node["indexValue"] = {"type": "Simple", "simple": index_value,
                              "desc": str(index_value)}
    if op_type in ("FIRST_ONE", "LAST_ONE", "PICK_ONE"):
        # 元素出参：直接沿用被操作数组的元素描述（id 是 DTO 全名，供字段引用解析）
        node["output"] = {
            "id": src.get("id"), "javaType": src.get("javaType"),
            "type": "OBJECT", "dataType": src.get("dataType") or "DTO",
            "desc": title, "dtoType": src.get("dtoType"),
            "appName": src.get("appName"), "udcApp": src.get("udcApp", True),
            "name": "_" + node["nodeId"],
        }
    elif op_type in ("SORT", "DISTINCT", "FILTER", "SUBTRACT", "INTERSECT",
                     "GROUP_AND_SUM"):
        # 仍然返回**列表**的操作：出参是 ARRAY（元素描述沿用输入数组）
        node["output"] = {"id": src.get("id"), "javaType": src.get("javaType"),
                          "type": "ARRAY", "dataType": src.get("dataType") or "DTO",
                          "desc": title, "dtoType": src.get("dtoType"),
                          "appName": src.get("appName"), "udcApp": src.get("udcApp", True),
                          "name": "_" + node["nodeId"]}
    elif op_type in ("SUM", "MIN", "MAX"):
        # 聚合出参随字段类型：SUM(INTEGER)→INTEGER、SUM(DECIMAL)→DECIMAL、MIN(DATETIME)→DATETIME
        f = (count_attrs or [{}])[0]
        dt = f.get("dataType") or "INTEGER"
        jt = f.get("javaType") or {"INTEGER": "java.lang.Integer",
                                   "BIGINTEGER": "java.lang.Long",
                                   "DECIMAL": "java.math.BigDecimal",
                                   "DATETIME": "java.util.Date"}.get(dt, "java.lang.Integer")
        node["output"] = {"id": None, "javaType": jt, "dataType": dt,
                          "type": "OBJECT", "desc": title, "name": "_" + node["nodeId"]}
    elif op_type == "MAP":
        # MAP 出参是数组（元素类型=被取字段类型）
        f = (count_attrs or [{}])[0]
        dt = f.get("dataType") or "STRING"
        node["output"] = {"id": None, "javaType": {"INTEGER": "java.lang.Integer",
                                                   "BIGINTEGER": "java.lang.Long",
                                                   "DECIMAL": "java.math.BigDecimal"}.get(dt, "java.lang.String"),
                          "dataType": dt, "type": "ARRAY", "desc": title,
                          "name": "_" + node["nodeId"]}
    elif op_type in ("SUM", "MIN", "MAX"):
        # 聚合出参随字段类型：SUM(INTEGER)→INTEGER / SUM(DECIMAL)→DECIMAL / MIN(DATETIME)→DATETIME
        f = (count_attrs or [{}])[0]
        dt = f.get("dataType") or "INTEGER"
        jt = f.get("javaType") or {"INTEGER": "java.lang.Integer",
                                   "BIGINTEGER": "java.lang.Long",
                                   "DECIMAL": "java.math.BigDecimal",
                                   "DATETIME": "java.util.Date"}.get(dt, "java.lang.Integer")
        node["output"] = {"id": None, "javaType": jt, "dataType": dt,
                          "type": "OBJECT", "desc": title, "name": "_" + node["nodeId"]}
    elif op_type == "MAP":
        f = (count_attrs or [{}])[0]
        dt = f.get("dataType") or "STRING"
        node["output"] = {"id": None,
                          "javaType": {"INTEGER": "java.lang.Integer",
                                       "BIGINTEGER": "java.lang.Long",
                                       "DECIMAL": "java.math.BigDecimal"}.get(dt, "java.lang.String"),
                          "dataType": dt, "type": "ARRAY", "desc": title,
                          "name": "_" + node["nodeId"]}
    else:
        node["output"] = {
            "id": None, "javaType": "java.lang.Integer", "dataType": "INTEGER",
            "type": "OBJECT", "desc": title, "name": "_" + node["nodeId"],
        }
    return node


# --------------------------------------------------------------------------
# 映射活动
# --------------------------------------------------------------------------
def create_map(builder: NodeBuilder, title: str = "vMap",
               caption: str = "创建Map",
               key_type: str = "STRING", value_type: str = "STRING") -> dict[str, Any]:
    """创建映射组。

    ★ `paramType`/`dataType` 必须显式为 None（前端按 null 走「映射组」分支）；
      漏字段与显式 None 在 UI 上表现一致，但保持与活体结构一致便于比对。
    """
    node = builder.build("CREATE_MAP", caption=caption)
    # ★ 真实 4 个生产样本里**没有** paramType/dataType 这两个键（不是 None，是根本不存在）。
    #   写过它们会被契约闸门判为「真实样本从未出现的字段」。
    node["title"] = title
    node["generics"] = {
        "keyType": {"dataType": key_type, "type": "OBJECT", "javaType": "java.lang.String"},
        "valueType": {"dataType": value_type, "type": "OBJECT",
                      "javaType": "java.lang.String"},
    }
    node["output"] = {
        "id": None, "javaType": "java.util.Map", "dataType": "MAP", "type": "OBJECT",
        "desc": title, "name": "_" + node["nodeId"],
        "generics": [{"dataType": key_type}, {"dataType": value_type}],
    }
    return node


def map_operation(builder: NodeBuilder, map_node: dict[str, Any],
                  key_value: dict[str, Any] = None, value_value: dict[str, Any] = None,
                  op_type: str = "PUT", caption: str = "Map操作",
                  result_title: str = "映射取值", data_type: str = "STRING",
                  array_or_object: str = "OBJECT",
                  null_prompt: str = None) -> dict[str, Any]:
    """映射操作。

    ★ op_type=GET 时前端必填 4 项：selectMap / operationType / theKey / basic / arrayOrObject
      - `basic`（「数据类型」）必须是 treeListSelector 的选项对象
        `{label,value,key,dataType}`，**不能是裸字符串 "STRING"**：
        传字符串时下拉渲染成空占位「选择数据类型」，且 `structure:{...basic}`
        会把字符串迭代成 `{"0":"S","1":"T",...}` 垃圾。
      - `structure` = `{...basic, fullName: javaType}`（前端 dataSchema() 原样推导）。
      - `entries` 只对 PUT 需要，GET 模式必须删掉。
    ★ op_type=PUT 时必填 entries（键值对列表）。
    """
    node = builder.build("MAP_OPERATION", caption=caption)
    out = map_node.get("output") or {}
    node["selectMap"] = {
        "id": None, "javaType": "java.util.Map", "dataType": "MAP", "type": "OBJECT",
        "desc": map_node.get("title") or "", "name": builder.output_name(map_node),
        "generics": {"keyType": {"dataType": "String"},
                     "valueType": {"dataType": "Object", "javaType": "java.lang.Object"}},
        "position": "parent", "outputName": builder.output_name(map_node),
        "description": map_node.get("title") or "",
        "nodeInfo": {"nodeId": map_node["nodeId"], "type": "ACTIVITY", "actionType": "CREATE_MAP"},
    }
    node["operationType"] = op_type
    node["title"] = result_title

    if op_type == "GET":
        _java = {"STRING": "java.lang.String", "INTEGER": "java.lang.Integer",
                 "BIGINTEGER": "java.lang.Long", "BOOLEAN": "java.lang.Boolean",
                 "DATE": "java.util.Date", "DATETIME": "java.util.Date"}.get(
                     data_type, "java.lang.String")
        _dt_opt = {"label": _DT_LABELS.get(data_type, "文本"), "value": data_type,
                   "key": data_type, "dataType": data_type}
        node["paramType"] = "BASIC"
        node["basic"] = dict(_dt_opt)
        node["structure"] = dict(_dt_opt, fullName=_java)
        node["arrayOrObject"] = array_or_object
        node["theKey"] = key_value if isinstance(key_value, dict) else simple(key_value)
        # ★ 真实 10 个 GET 样本全部 nullHandling=CONTINUE、无 nullPromptMessage；
        #   写 TERMINATION+提示语会被契约闸门拦（样本从未出现的字段）。
        node["nullHandling"] = "TERMINATION" if null_prompt else "CONTINUE"
        if null_prompt:
            node["nullPromptMessage"] = null_prompt
        node.pop("entries", None)
        node["output"] = {
            "id": None, "javaType": _java, "dataType": data_type,
            "type": array_or_object, "desc": result_title,
            "name": "_" + node["nodeId"],
        }
    elif op_type == "KEY_SET":
        # 获取键列表：出参=键组成的列表（ARRAY of STRING）。必填仅 3 项：
        # 选择映射/操作类型/出参名称，不需要 theKey/basic（node-settings-capability 的
        # 「获取键列表」模式）。
        node["paramType"] = "BASIC"
        node["arrayOrObject"] = "ARRAY"
        node["output"] = {
            "id": None, "javaType": "java.lang.String", "dataType": "STRING",
            "type": "ARRAY", "desc": result_title,
            "name": "_" + node["nodeId"],
        }
        node.pop("entries", None)
    else:
        node["entries"] = [{"key": key_value, "value": value_value}]
    return node


# --------------------------------------------------------------------------
# 逻辑活动
# --------------------------------------------------------------------------
def custom_error(builder: NodeBuilder, message: str, error_type: str = "GLOBAL",
                 caption: str = "自定义错误") -> dict[str, Any]:
    node = builder.build("CUSTOM_ERROR", caption=caption)
    node["error"] = simple(message)
    node["errorType"] = error_type
    return node


def branch(builder: NodeBuilder, conditions: list[dict[str, Any]],
           caption: str = "分支") -> dict[str, Any]:
    """conditions: 分支条件表达式列表（每个含 expression），返回 BRANCH 节点。
    注意：分支体节点（nodes）需要后续手动挂到 conditions[i]['nodes']。
    关键：必须带 elseBranch（expression=null, nodes=[]）作为默认出口，
    否则所有分支都塞自定义错误会被检测判为「无法正常返回」。"""
    import uuid as _uuid
    node = builder.build("BRANCH", caption=caption)
    node["conditions"] = []
    for i, cond_expr in enumerate(conditions):
        # 两种入参都接受：
        #   ① 直接给 expression 对象 {title, schema}
        #   ② 给 {expression: <expression对象>, nodes: [分支体节点]}
        # ★ 旧实现把 ② 的整个 dict 当成 expression 塞进去（只认 type=="Expression"
        #   一种包装），结果分支条件落库是 {"expression":...,"nodes":[...]}，
        #   平台 checkSchema 报 PROPERTY_IS_REQUIRED（条件表达式未配置）——
        #   表达式引擎生成得再对，也被这一层吞掉。
        body: list = []
        if isinstance(cond_expr, dict):
            if cond_expr.get("type") == "Expression":
                cond_expr = cond_expr.get("expression") or cond_expr
            elif "expression" in cond_expr:
                body = list(cond_expr.get("nodes") or [])
                cond_expr = cond_expr.get("expression")
        node["conditions"].append({
            "nodeId": builder._new_id("CONDITION"),
            "name": "ifBranch", "type": "CONDITION",
            "caption": "符合条件即进入该分支", "description": "",
            "runAfter": None, "expression": cond_expr, "nodes": body,
            "isCompleted": True,
        })
    node["conditions"].append({
        "nodeId": builder._new_id("CONDITION"),
        "name": "elseBranch", "type": "CONDITION",
        "caption": "不符合条件即进入该分支", "description": "",
        "runAfter": None, "expression": None, "nodes": [],
        "isCompleted": True,
    })
    return node


def for_count(builder: NodeBuilder, start: dict[str, Any], end: dict[str, Any],
              step: int, caption: str = "计数循环") -> dict[str, Any]:
    node = builder.build("FOR", caption=caption)
    node["foreach"] = None
    node["forStart"] = start
    node["forEnd"] = end
    node["forStep"] = step  # 数字（模板 forStep=1）
    node["targetName"] = "计数循环变量_1"
    node["operator"] = "<="
    node["nodes"] = []
    return node


# --------------------------------------------------------------------------
# 批量数据活动
# --------------------------------------------------------------------------
def create_batch_entity(builder: NodeBuilder, entity: dict[str, Any],
                        list_node: dict[str, Any],
                        field_values: list[tuple[str, dict[str, Any]]],
                        caption: str = "批量插入数据") -> dict[str, Any]:
    node = builder.build("CREATE_BATCH_ENTITY", caption=caption)
    node["selectParam"] = _list_ref(list_node, builder)
    node["title"] = entity["caption"]
    node["output"] = _write_output("CREATE_BATCH_ENTITY", node["nodeId"])
    # ★ 真实 6 个 CREATE_BATCH_ENTITY 样本**全部只有 selectParam**，没有 attrs。
    #   批量插入的字段值由列表元素自带（列表来自 CREATE_LIST / RETRIEVE_ARRAY），
    #   节点本身不做字段映射。曾在此写 attrs → 契约闸门判「真实从未出现」。
    _ = field_values
    return node


def change_batch_entity(builder: NodeBuilder, entity: dict[str, Any],
                        list_node: dict[str, Any],
                        field_values: list[tuple[str, dict[str, Any]]],
                        caption: str = "批量更新数据") -> dict[str, Any]:
    node = builder.build("CHANGE_BATCH_ENTITY", caption=caption)
    node["selectParam"] = _list_ref(list_node, builder)
    node["title"] = entity["caption"]
    node["output"] = _write_output("CHANGE_BATCH_ENTITY", node["nodeId"])
    # ★ 真实 41 个 CHANGE_BATCH_ENTITY 样本**全部只有 selectParam**，没有任何 attrs。
    #   批量更新的字段值由列表元素自带（列表是 CREATE_LIST / RETRIEVE_ARRAY 产出的
    #   实体列表），节点本身不再做字段映射。曾在此写 attrs → 契约闸门判「真实从未出现」。
    #   field_values 参数保留仅为向后兼容，不落库；真要逐字段覆盖请改用单条 CHANGE_ENTITY。
    _ = field_values
    return node


# --------------------------------------------------------------------------
# 数据加工
# --------------------------------------------------------------------------
# CONVERT_DATA 的 convertType 真实取值（114 个生产样本全量，只有这 5 种）。
# ★ convertType 必须是对象 {desc,value,dataType,type}，不能是裸字符串。
_CONVERT_TYPES = {
    "Split": {"desc": "指定符号拆分文本", "value": "Split",
              "dataType": "STRING", "type": "ARRAY"},
    "multiAssociation2List": {"desc": "多选数据拆分为长整数列表",
                              "value": "multiAssociation2List",
                              "dataType": "BIGINTEGER", "type": "ARRAY"},
    "List2multiAssociation": {"desc": "长整数列表拼接为多选数据",
                              "value": "List2multiAssociation",
                              "dataType": "STRING", "type": "OBJECT"},
    "BasicData2String": {"desc": "基础类型转文本", "value": "BasicData2String",
                         "dataType": "STRING", "type": "OBJECT"},
    "String2Long": {"desc": "文本转长整数【ID】", "value": "String2Long",
                    "dataType": "BIGINTEGER", "type": "OBJECT"},
}


def convert_data(builder: NodeBuilder, src_node: dict[str, Any], convert_type: str,
                 title: str, caption: str = "数据转换") -> dict[str, Any]:
    """数据转换。

    ★ convertType 必须是对象（真实 114 个样本 100% 是对象），且取值只有 5 种，
      见 _CONVERT_TYPES。传裸字符串会让「转换方式」下拉回显空。
    """
    if convert_type not in _CONVERT_TYPES:
        raise ValueError("未知转换类型 %r，真实平台只有 %s"
                         % (convert_type, list(_CONVERT_TYPES)))
    node = builder.build("CONVERT_DATA", caption=caption)
    node["convertType"] = dict(_CONVERT_TYPES[convert_type])
    node["title"] = title
    node["selectParam"] = _basic_ref(src_node, builder)
    # 出参形态由转换方式决定（114 条真实样本）：
    #   Split                  → ARRAY  STRING     （53 条，恒带 regex）
    #   multiAssociation2List  → ARRAY  BIGINTEGER （42 条）
    #   List2multiAssociation  → OBJECT STRING     （13 条）
    #   BasicData2String       → OBJECT STRING     （ 5 条）
    #   String2Long            → OBJECT BIGINTEGER （ 1 条）
    # 模板默认是 Split 形态，其它类型不纠正就会输出 ARRAY/STRING（G32 拦）。
    shape = {"Split": ("ARRAY", "STRING", "java.lang.String"),
             "multiAssociation2List": ("ARRAY", "BIGINTEGER", "java.lang.Long"),
             "List2multiAssociation": ("OBJECT", "STRING", "java.lang.String"),
             "BasicData2String": ("OBJECT", "STRING", "java.lang.String"),
             "String2Long": ("OBJECT", "BIGINTEGER", "java.lang.Long")}[convert_type]
    out = node.get("output") or {}
    out["type"], out["dataType"], out["javaType"] = shape
    out["desc"] = title
    # javaType 必须一起改：只改 dataType 的话代码生成仍按模板的 String 声明变量，
    # 运行期赋 Long → 编译报「Long 无法转换为 String」（2026-11-03 实测）。
    if convert_type != "Split":
        node.pop("regex", None)   # 语料里只有 Split 带 regex
    node["output"] = out
    return node

def create_list_entity(builder: NodeBuilder, entity: dict[str, Any], title: str,
                       caption: str = "创建列表") -> dict[str, Any]:
    """创建「实体对象列表」（空列表，往里面 ADD 元素）。真实形态 1657496744010280686。

    paramType=ENTITY_OBJECT + structure(实体) + value=[]，出参是 DTO/ARRAY。
    ★ 与 create_list（BASIC）区别：元素是实体对象，后续 CREATE_BATCH_ENTITY 直接消费。
    """
    from .microflow_nodes_v2 import _entity_output, entity_structure
    node = builder.build("CREATE_LIST", caption=caption)
    node["paramType"] = "ENTITY_OBJECT"
    node["app"] = builder._app_ref()
    node["title"] = title
    node["dataType"] = "DTO"
    node["structure"] = entity_structure(entity)
    node["value"] = []
    out = _entity_output(entity, node["nodeId"], caption_suffix="", is_array=True)
    out["desc"] = title
    node["output"] = out
    return node


def change_list_add(builder: NodeBuilder, list_node: dict[str, Any],
                    item_node: dict[str, Any], caption: str = "列表添加元素") -> dict[str, Any]:
    """往实体对象列表追加一个元素（action=ADD，317 个样本里 266 个是 ADD）。"""
    return change_list(builder, list_node, item_node, action="ADD", caption=caption)


def list_size(builder: NodeBuilder, list_node: dict[str, Any], title: str,
              caption: str = "列表操作") -> dict[str, Any]:
    """统计列表条数（LIST_OPERATION operationType=SIZE，15 个真实样本）。

    出参 INTEGER/java.lang.Integer，后端返回 List.size()。
    ★ LIST_OPERATION 共 14 种操作，没有 ADD；加元素要用 change_list_add。
    """
    node = builder.build("LIST_OPERATION", caption=caption)
    o = list_node.get("output") or {}
    on = builder.output_name(list_node)
    node["selectParam"] = {
        "description": list_node.get("title") or o.get("desc") or "",
        "name": on, "outputName": on,
        "dataType": o.get("dataType") or "DTO", "type": "ARRAY",
        "desc": list_node.get("title") or o.get("desc") or "",
        "javaType": o.get("javaType"), "position": "parent",
        "nodeInfo": {"nodeId": list_node["nodeId"], "type": "ACTIVITY",
                     "actionType": list_node.get("actionType")},
        "key": on + "_" + on, "iconKey": "LinedCut",
        "parentLabel": "", "disabled": False,
        # 引实体列表必须带 dtoType（闸门 G：803/803 真实样本都有）
        "dtoType": o.get("dtoType") or "MASTER_ENTITY",
        "udcApp": True, "appName": o.get("appName") or builder.app_name,
        "relationEntity": o.get("relationEntity"),
    }
    node["operationType"] = {"type": "SIZE"}
    node["title"] = title
    node["output"] = {"id": "", "javaType": "java.lang.Integer", "type": "OBJECT",
                      "dataType": "INTEGER", "desc": title,
                      "name": "_LIST_OPERATION_" + "".join(
                          __import__("random").choices(
                              __import__("string").ascii_letters + __import__("string").digits, k=6))}
    return node


# ─────────────────────────────── 基础服务类节点 ───────────────────────────────
JAVA_OF = {"INTEGER": "java.lang.Integer", "BIGINTEGER": "java.lang.Long",
           "STRING": "java.lang.String", "BOOLEAN": "java.lang.Boolean",
           "DECIMAL": "java.math.BigDecimal", "DATETIME": "java.util.Date"}


def _rid(n: int = 6) -> str:
    import random, string
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def mf_service(flow_name: str, caption: str, out_desc: str = "结果",
               out_type: str = "INTEGER", has_input: bool = False,
               service_id: str | None = None) -> dict:
    """构造「子微流程」可选服务。真实形态取自 643 条语料 SUB_MICROFLOW（305 例）+ 本应用
    udcMicroflowSearchRestExcludeBootPost 实测（path=/microflow/{flowName}）。"""
    return {
        "id": service_id, "appCaption": None, "appId": None,
        "appName": os.environ.get("UDC_APP_NAME", ""),
        "caption": caption, "description": "", "hasInput": has_input, "hasOutput": True,
        "hostPath": None, "input": None, "method": "POST", "name": flow_name,
        # ★ 必须带 output：平台用它与当前服务定义比对，缺了就报
        #   UDC_MICRO_FLOW_04004「微流程已更改」（检测层 error，发布层不报）
        "output": {"inApp": True, "udcApp": False, "hasPagination": False,
                   "dataType": out_type, "javaType": JAVA_OF.get(out_type, "java.lang.Object"),
                   "type": "OBJECT", "name": "_FLOW_OUTPUT_" + _rid(),
                   "description": out_desc, "required": False},
        "path": "/microflow/" + flow_name, "triggerType": "MANUAL",
        "type": "SERVICE", "restType": "POST",
    }


def sub_microflow(builder: NodeBuilder, service: dict,
                  attrs: list | None = None, out_desc: str = "子流程结果",
                  out_type: str = "INTEGER", caption: str = "子微流程") -> dict:
    """子微流程：调用本应用已发布的微流程（appId 由 builder 注入）。"""
    node = builder.build("SUB_MICROFLOW", caption=caption)
    svc = dict(service)
    svc["appId"] = builder.app_id
    svc["name"] = service["name"]
    node["mfService"] = svc
    node["mappingType"] = "attrs"
    node["attrs"] = attrs or []
    node["outPutDesc"] = out_desc
    node["outputName"] = "_SUB_MICROFLOW_" + _rid()
    node["output"] = {
        "appName": builder.app_name, "id": None, "type": "OBJECT", "dataType": out_type,
        "javaType": JAVA_OF.get(out_type, "java.lang.Object"), "dtoType": None,
        "desc": out_desc, "name": "_SUB_MICROFLOW_" + _rid(), "udcApp": True,
    }
    return node


CONVERT_BASIC2STRING = {"desc": "基础类型转文本", "value": "BasicData2String",
                        "dataType": "STRING", "type": "OBJECT"}
CONVERT_STRING2LONG = {"desc": "文本转长整数【ID】", "value": "String2Long",
                       "dataType": "BIGINTEGER", "type": "OBJECT"}


# ───────────────────── 自定义服务 / 事件投递 / 执行生单规则 ─────────────────────
def call_app_service(builder: NodeBuilder, app: dict, method: dict,
                     param_value: dict, out_desc: str, caption: str = "自定义服务") -> dict:
    """自定义服务。app/method 必须来自接口原样返回：
    udcMicroflowSearchAppsPost → SearchAppServiceByAppNamePost → SearchMethodByNamePost（含 md5）。
    """
    node = builder.build("CALL_APP_SERVICE", caption=caption)
    node["app"] = {"appId": app.get("appId"), "appName": app.get("name") or app.get("appName"),
                   "caption": app.get("caption"), "inApp": bool(app.get("inApp")),
                   "udcApp": bool(app.get("udcApp")),
                   "dynamicDependency": app.get("dynamicDependency") or "NONE"}
    node["selectMethod"] = method
    node["value"] = param_value
    node["attrs"] = []          # builder 模板里的默认 attrs 带死引用，必须清空
    rv = (method.get("returnValue") or {}).get("item") or {}
    node["output"] = {"id": rv.get("itemType") or rv.get("javaType"),
                      "javaType": rv.get("javaType") or rv.get("itemType"),
                      "dataType": "DTO", "type": "OBJECT", "desc": out_desc,
                      "appName": node["app"]["appName"],
                      "name": "_CALL_APP_SERVICE_" + _rid()}
    node["outPutDesc"] = None
    node["outputName"] = out_desc
    return node


def publish_business_event(builder: NodeBuilder, event: dict,
                           attrs: list[dict], caption: str = "事件投递") -> dict:
    """事件投递（应用内 IN_APP）。event 来自 udcMicroflowSearchEventListPost。"""
    node = builder.build("PUBLISH_BUSINESS_EVENT", caption=caption)
    full = event.get("fullName")
    node["eventType"] = "IN_APP"
    node["selectEvent"] = {"key": full, "label": event.get("caption"), "value": full,
                           "fullName": full, "caption": event.get("caption"),
                           "source": event.get("source") or "MICRO_FLOW",
                           "dtoType": event.get("dtoType") or "CUSTOM",
                           "udcApp": bool(event.get("udcApp"))}
    node["mappingType"] = "attrs"
    node["attrs"] = attrs
    node["output"] = None
    return node


def call_data_flow(builder: NodeBuilder, structure: dict, rule: dict,
                   condition: list | None, out_desc: str,
                   caption: str = "执行生单规则",
                   data_source_type: str = "CONDITION") -> dict:
    """执行生单规则。rule 来自 udcDataFlowListManuallyMappingPost（按 sourceEntityId 查）。"""
    node = builder.build("CALL_DATA_FLOW", caption=caption)
    node["structure"] = structure
    # ★★ 2026-11-02 定案（前端 merge 规则 + 运行时解析器双证）：
    #   ① 设计器保存时执行 `merge:{dataFlowMappingId:"dataFlow.id"}`，
    #      → 两者**必然相等**，不可能出现「dataFlow.id 是规则 id、mappingId 是行 id」。
    #   ② 运行时 `CallDataFlowActivity.parseActivityNode` **只读 dataFlowMappingId**，
    #      `dataFlow` 对象根本不参与解析（纯 UI 字段）。
    #   ③ 校验集合的键名是 `data-flow-mapping-id-used-by-micro-flow`，
    #      由 `DataFlowMappingDto.getId()` 填充 → dataFlowMappingId = **DataFlowMapping 主键**，
    #      即 udcDataFlowListManuallyMappingPost 列表行的 `id`（不是 dataFlowId）。
    #   所以 dataFlow.id 也必须是列表行 id；dataFlowId 只作为行内 FK 保留。
    rid = str(rule.get("id"))
    node["dataFlow"] = {"id": rid, "key": rid, "value": rid, "title": rule.get("caption"),
                        "appId": rule.get("appId"), "appUrl": rule.get("appUrl"),
                        "caption": rule.get("caption"), "name": rule.get("name"),
                        "sourceEntityId": rule.get("sourceEntityId"),
                        "dataFlowId": rule.get("dataFlowId"), "g_l_index": "1"}
    node["dataSourceType"] = data_source_type
    node["title"] = out_desc
    node["dataFlowMappingId"] = rid
    node["condition"] = condition or []
    node["output"] = {"id": "com.seeyon.boot.starter.udcrt.dto.CallDataFlowResultDto",
                      "javaType": "com.seeyon.boot.starter.udcrt.dto.CallDataFlowResultDto",
                      "dataType": "DTO", "type": "OBJECT", "udcApp": True,
                      "dtoType": "CUSTOM", "desc": out_desc,
                      "appName": builder.app_name, "name": "_CALL_DATA_FLOW_" + _rid()}
    return node
