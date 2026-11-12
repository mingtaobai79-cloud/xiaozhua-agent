"""IntentDraft 正式 schema（P7-E2E-2 产品化）。

这是宿主 LLM 产出「业务意图草稿」的权威契约。它和
`BusinessRequirementCompiler.compile()` 吃的 draft、`LogicGraphRunner` 执行的
LogicGraph 是同一份结构——这里把「LLM 该产什么」固化成一个可导出、可校验的规范。

三个硬边界（不越位）：
- LLM 只产 IntentDraft（业务意图草稿），不产平台 JSON、不调构造器。
- 实体名/字段名可以是**中文 caption**，由编译器做真名归一化；但绝不许猜一个
  不存在的名字——猜错了编译器会 BLOCKED，不会静默用。
- 跨环境 id（子流程 id / 事件对象 / 生单规则）**不许写进草稿**，只写业务名，
  由编译器运行时对着 LiveRefs 拉活引用。

单一事实源：`NODE_SPECS`（28 个 kind 的字段）。`_STEP_KINDS` 在 logic_graph.py
是执行器侧的事实源，这里加「字段级」说明与示例，二者靠测试对齐（
`tests/test_intent_draft_schema.py` 断言两边 kind 集合一致）。
"""
from __future__ import annotations

from .logic_graph import _STEP_KINDS

# ---------------------------------------------------------------- 值槽三态
# 写节点 fields 的值、变量的 value 等「值」位置，只有三种合法形态。
VALUE_SLOTS = {
    "const": "字面量常量：{\"const\": <bool|int|float|str>}",
    "field": "节点出参引用：{\"field\": \"<节点别名>\"} 整节点；"
             "{\"field\": \"<节点别名>.<字段名>\"} 取 DTO 字段",
    "input": "流程入参：{\"input\": \"<入参名>\"}（或 {\"field\": \"$input.<名>\"}）",
}

# ---------------------------------------------------------------- 表达式 DSL 形态
# FILTER 的 filter、branch 的 condition 等布尔/值表达式，由这些 JSON 节点递归组成。
EXPRESSION_FORMS = {
    "const":  {"const": "<值>"},
    "op":     {"op": "EQ|NE|GT|GE|LT|LE|IN", "left": "<expr>", "right": "<expr>"},
    "logic":  {"logic": "AND|OR", "items": ["<expr>", ...]},
    "arith":  {"arith": "ADD|SUB|MUL|DIV", "items": ["<expr>", ...]},
    "fn":     {"fn": "containsText|isNotNull|year|...",
               "args": [["<参数1>"], ["<参数2>"]], "dtype": "BOOLEAN|STRING|..."},
    "cond":   {"cond": {"if": "<expr>", "then": "<expr>", "else": "<expr>"}},
    "field":  {"field": "<实体字段名>"},   # 表达式内：实体字段；写节点 fields 内：节点引用
    "item":   {"item": "<循环别名>", "field": "<字段名>"},   # 循环项字段
    "input":  {"input": "<入参名>"},
    "sys":    {"sys": "<系统变量名>"},
}
# 表达式里 field 的两种语义（易混，必须区分）：
#   表达式上下文（filter/condition）：{"field": "processedRows"} = 实体字段名
#   值槽上下文（fields/value）：    {"field": "sz"}            = 节点 sz 的整节点出参
# 值槽里取 DTO 字段用点号：{"field": "ra.taskId"} = 节点 ra 的 taskId 字段。

# ---------------------------------------------------------------- 28 kind 字段定义
# required：缺了必炸（_do_* 直接 n["x"] 或语义必需）；optional：有默认值。
NODE_SPECS: dict[str, dict] = {
    # ---- 读 ----
    "retrieve": {
        "required": ["entity"], "optional": ["by_id_from", "from_field",
            "cond_field", "right", "null_handling", "null_message", "caption"],
        "doc": "查单条。by_id_from=按某节点出参 id 查；否则 cond_field=right 条件查。",
        "example": {"kind": "retrieve", "entity": "数据源配置信息",
                    "cond_field": "名称", "right": {"const": "mysql主库"},
                    "null_handling": "TERMINATION", "null_message": "数据源不存在"},
    },
    "retrieve_array": {
        "required": ["entity"], "optional": ["cond_field", "right", "conditions",
            "fetch_type", "ids_from", "page_info_from", "sort_by", "sort_dir",
            "caption"],
        "doc": "查多条。conditions=多条件(AND)；cond_field+right=单条件；"
              "fetch_type=CONDITION|COUNT|IDS。★必须带条件，全量也要一条恒真。",
        "example": {"kind": "retrieve_array", "entity": "迁移任务批次账本",
                    "cond_field": "任务ID", "right": {"const": "MIG-001"}},
    },
    # ---- 写（单条）----
    "create_entity": {
        "required": ["entity", "fields"], "optional": ["caption"],
        "doc": "插入单条实体记录。fields={字段名: 值槽}。",
        "example": {"kind": "create_entity", "entity": "迁移断点",
                    "fields": {"任务标识": {"const": "X"}, "已处理行数": {"const": 3}}},
    },
    "change_entity": {
        "required": ["entity", "from_node", "fields"], "optional": ["caption"],
        "doc": "更新单条。from_node=要改的那条记录的节点出参；fields=改哪些字段。",
        "example": {"kind": "change_entity", "entity": "迁移断点",
                    "from_node": "r", "fields": {"已处理行数": {"const": 999}}},
    },
    "delete_entity": {
        "required": ["entity"], "optional": ["from_node", "cond_field", "right",
            "caption"],
        "doc": "删除。from_node=按节点出参删(SELECT_PARAM)；否则 cond_field+right 条件删。"
              "★动态记录必须 from_node（条件右值不能是节点引用）。",
        "example": {"kind": "delete_entity", "entity": "迁移断点", "from_node": "r"},
    },
    # ---- 写（批量）----
    "create_batch_entity": {
        "required": ["entity", "list_node"], "optional": ["caption"],
        "doc": "批量插入。list_node=元素列表(必须是无 id 的新对象，否则主键冲突)。",
        "example": {"kind": "create_batch_entity", "entity": "迁移断点",
                    "list_node": "lst"},
    },
    "change_batch_entity": {
        "required": ["entity", "list_node"], "optional": ["caption"],
        "doc": "批量更新。写列表元素自带的字段值（节点无 attrs）。",
        "example": {"kind": "change_batch_entity", "entity": "迁移断点",
                    "list_node": "lst"},
    },
    # ---- 变量 / 列表 / Map ----
    "create_variable": {
        "required": ["title"], "optional": ["entity", "data_type", "value",
            "caption"],
        "doc": "创建变量。entity=实体型变量；否则 data_type+value=标量变量。",
        "example": {"kind": "create_variable", "title": "计数",
                    "data_type": "INTEGER", "value": {"const": 0}},
    },
    "change_variable": {
        "required": ["target"], "optional": ["value", "from_node", "field",
            "caption"],
        "doc": "给变量赋值。value=值槽；或 from_node+field=取某节点字段。",
        "example": {"kind": "change_variable", "target": "cnt",
                    "value": {"field": "sz"}},
    },
    "create_list": {
        "required": ["title"], "optional": ["data_type", "default_value",
            "caption"],
        "doc": "创建列表变量。default_value 是数组（元素是值槽）。",
        "example": {"kind": "create_list", "title": "结果列表",
                    "data_type": "STRING"},
    },
    "change_list": {
        "required": [], "optional": ["list_node", "from_node", "action",
            "count_fields", "caption"],
        "doc": "修改列表。action=ADD|REPLACE|CLEAR|REMOVE；list_node=目标列表，"
              "from_node=来源（元素/列表）。",
        "example": {"kind": "change_list", "list_node": "lst", "from_node": "ra",
                    "action": "ADD"},
    },
    "create_list_entity": {
        "required": ["entity"], "optional": ["title", "caption"],
        "doc": "创建实体对象列表（批量写的前置：造元素列表）。",
        "example": {"kind": "create_list_entity", "entity": "迁移断点",
                    "title": "断点列表"},
    },
    "change_list_add": {
        "required": ["list_node"], "optional": ["item", "caption"],
        "doc": "往列表加一个元素。item=元素来源节点。",
        "example": {"kind": "change_list_add", "list_node": "lst", "item": "e"},
    },
    "create_map": {
        "required": [], "optional": ["title", "key_type", "value_type",
            "caption"],
        "doc": "创建 Map 变量。",
        "example": {"kind": "create_map", "title": "映射", "key_type": "STRING",
                    "value_type": "STRING"},
    },
    "map_operation": {
        "required": ["map_node"], "optional": ["op_type", "key_value",
            "value_value", "result_title", "data_type", "array_or_object",
            "caption"],
        "doc": "Map 操作。op_type=PUT|GET|REMOVE 等；key_value/value_value=值槽。",
        "example": {"kind": "map_operation", "map_node": "m", "op_type": "PUT",
                    "key_value": {"const": "k"}, "value_value": {"const": "v"}},
    },
    # ---- 列表操作（聚合/过滤/排序）----
    "list_operation": {
        "required": ["list_node"], "optional": ["op_type", "title", "sort_by",
            "sort_dir", "count_fields", "index_value", "second_list", "filter",
            "group_by", "caption"],
        "doc": "列表操作。op_type=SIZE|FILTER|SUM|MIN|MAX|GROUP_AND_SUM|PICK_ONE|"
              "SORT|DISTINCT|MAP 等。SUM/MIN/MAX 用 count_fields；FILTER 用 filter；"
              "GROUP_AND_SUM 用 group_by+count_fields。",
        "example": {"kind": "list_operation", "list_node": "ra", "op_type": "SUM",
                    "count_fields": ["失败行数"]},
    },
    "page_info": {
        "required": [], "optional": ["page_number", "page_size", "need_total",
            "caption"],
        "doc": "分页参数对象（配合 retrieve_array 的 page_info_from）。",
        "example": {"kind": "page_info", "page_size": 2},
    },
    "convert_data": {
        "required": ["convert_type"], "optional": ["from_node", "title",
            "caption"],
        "doc": "数据类型转换。convert_type=Split|BasicData2String|String2Long|...",
        "example": {"kind": "convert_data", "from_node": "s",
                    "convert_type": "String2Long"},
    },
    "data_mapping": {
        "required": ["entity", "from_node"], "optional": ["src_field",
            "dst_field", "caption"],
        "doc": "数据映射。from_node 必须是列表；src_field→dst_field 字段映射。",
        "example": {"kind": "data_mapping", "entity": "迁移断点", "from_node": "ra",
                    "src_field": "taskId", "dst_field": "sourceTable"},
    },
    # ---- 服务 / 事件 / 子流程 ----
    "call_app_service": {
        "required": ["method_full"], "optional": ["attrs", "caption"],
        "doc": "调应用服务。method_full=完整类.方法名（签名运行时拉）。",
        "example": {"kind": "call_app_service",
                    "method_full": "com.xx.FooService.getSerialNumber",
                    "attrs": {"serialSchemeCode": {"const": "TEST"}}},
    },
    "sub_microflow": {
        "required": [], "optional": ["sub_name", "sub_id", "attrs", "inputs",
            "value", "out_desc", "caption"],
        "doc": "调子微流程。sub_name=业务名（不写 id，跨环境 id 必变）；"
              "inputs=字段映射传参；value=标量入参。",
        "example": {"kind": "sub_microflow", "sub_name": "生成采购单",
                    "inputs": {"taskId": {"const": "X"}}},
    },
    "publish_business_event": {
        "required": ["event"], "optional": ["attrs", "caption"],
        "doc": "投递业务事件。event 必须是 LiveRefs 查出的活事件对象（含 fullName）。",
        "example": {"kind": "publish_business_event",
                    "event": {"fullName": "com.xx.dto.ChangedEvent"},
                    "attrs": {"eventCode": {"const": "X"}}},
    },
    "call_data_flow": {
        "required": ["entity", "rule"], "optional": ["condition", "out_desc",
            "data_source_type", "caption"],
        "doc": "执行生单规则。rule 是 LiveRefs.data_flow_candidates 查出的活规则行。",
        "example": {"kind": "call_data_flow", "entity": "迁移断点",
                    "rule": {"id": "..."}},
    },
    # ---- 控制流 ----
    "branch": {
        "required": ["condition", "then"], "optional": ["else", "caption"],
        "doc": "条件分支。condition=布尔表达式；then/else=子节点列表。",
        "example": {"kind": "branch",
                    "condition": {"op": "GT", "left": {"field": "sz"},
                                  "right": {"const": 0}},
                    "then": [{"kind": "create_entity", "entity": "X",
                              "fields": {}}]},
    },
    "for_each": {
        "required": ["list", "body"], "optional": ["caption"],
        "doc": "遍历列表。list=列表节点别名；body 内用 {\"item\": \"<本循环id>\", "
              "\"field\": \"<字段>\"} 取循环项字段。",
        "example": {"kind": "for_each", "list": "arr", "body": [
            {"kind": "retrieve", "entity": "X", "by_id_from": "each",
             "from_field": "id"}]},
    },
    "for_count": {
        "required": ["start", "end", "body"], "optional": ["step", "caption"],
        "doc": "计数循环。start/end=值槽，step=步长。",
        "example": {"kind": "for_count", "start": {"const": 1},
                    "end": {"const": 3}, "body": []},
    },
    "break": {
        "required": [], "optional": ["caption"],
        "doc": "跳出循环（只能放 for_each/for_count 的 body 内）。",
        "example": {"kind": "break"},
    },
    "custom_error": {
        "required": [], "optional": ["message", "error_type", "caption"],
        "doc": "主动失败（让运行结果可断言：查询空→抛错，success=false 即证据）。",
        "example": {"kind": "custom_error", "message": "标记不存在"},
    },
}

# 顶层结构
TOP_LEVEL = {
    "nodes": "节点数组（必填）。每个元素含 id + kind + kind 专属字段。",
    "end": "出参定义（可选）：{\"from\": \"<节点别名>\", \"desc\": \"<中文名>\", "
           "\"basic_out\": \"<类型>\"}",
    "entities": "语义名→真名候选映射（可选）：{\"数据源\": \"数据源配置信息\"}",
}


# ---------------------------------------------------------------- 导出
def to_json_schema() -> dict:
    """导出为 JSON Schema（draft-07），供工具/宿主 LLM 参考。"""
    node_anyof = []
    for kind, spec in NODE_SPECS.items():
        props = {"id": {"type": "string"},
                 "kind": {"const": kind}}
        for k in spec["required"] + spec["optional"]:
            props[k] = {}
        node_anyof.append({"type": "object", "required": ["kind"] + spec["required"],
                           "properties": props,
                           "additionalProperties": True,
                           "description": spec["doc"]})
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "udc.logic-graph.compile.v1",
        "title": "IntentDraft",
        "type": "object",
        "required": ["nodes"],
        "properties": {
            "nodes": {"type": "array",
                      "items": {"oneOf": node_anyof}},
            "end": {"type": "object"},
            "entities": {"type": "object"},
        },
    }


def render_markdown() -> str:
    """导出人读规范（可直接喂给 LLM 当草稿格式参考）。"""
    lines = ["# IntentDraft 草稿格式", ""]
    lines.append("顶层：`{\"nodes\": [...], \"end\": {...}, \"entities\": {...}}`")
    lines.append("")
    for k, v in TOP_LEVEL.items():
        lines.append("- `%s`: %s" % (k, v))
    lines.append("")
    lines.append("## 值槽（值位置的三态）")
    for k, v in VALUE_SLOTS.items():
        lines.append("- `%s`: %s" % (k, v))
    lines.append("")
    lines.append("## 表达式 DSL 形态（filter/condition 用）")
    for k, v in EXPRESSION_FORMS.items():
        lines.append("- `%s`: `%s`" % (k, v))
    lines.append("")
    lines.append("## 28 个节点 kind")
    lines.append("")
    for kind, spec in NODE_SPECS.items():
        lines.append("### `%s`" % kind)
        lines.append("- 必填：%s" % (", ".join(spec["required"]) or "（无）"))
        lines.append("- 可选：%s" % (", ".join(spec["optional"]) or "（无）"))
        lines.append("- %s" % spec["doc"])
        lines.append("")
    return "\n".join(lines)


def validate(draft: dict) -> list[str]:
    """结构校验（复用 P3 validate_graph + 字段级 kind 白名单）。返回问题列表。"""
    from .logic_graph import validate_graph
    if not isinstance(draft, dict):
        return ["草稿必须是对象"]
    if "nodes" not in draft or not isinstance(draft["nodes"], list):
        return ["草稿缺 nodes 数组"]
    problems: list[str] = []

    def walk(seq):
        for n in seq:
            if not isinstance(n, dict):
                problems.append("节点必须是对象：%r" % (n,))
                continue
            kind = n.get("kind")
            if kind not in _STEP_KINDS:
                problems.append("节点 kind 非法：%r（可用 %s）"
                                % (kind, sorted(_STEP_KINDS)))
                continue
            spec = NODE_SPECS.get(kind)
            for req in spec["required"]:
                if req not in n:
                    problems.append("节点 %r 缺必填字段 %r"
                                    % (n.get("id"), req))
            for bk in ("then", "else", "body"):
                if isinstance(n.get(bk), list):
                    walk(n[bk])
    walk(draft["nodes"])
    problems += validate_graph({"nodes": draft["nodes"], "end": draft.get("end") or {}})
    return problems
