"""v12 随机业务生成：基于 v11 构造器 + 补全节点，组装一套覆盖 12 类节点的真实业务。

业务：项目验收流程（围绕 XzhExp950795 实体，appId=8704025620829192834 真实应用）。

节点序列（真实引用 + 链路顺序）：
  1. RETRIEVE        查询源单据（按入参 recordId 过滤 id）
  2. RETRIEVE_ARRAY  查询多条（按 expFlag 过滤）
  3. CREATE_VARIABLE 创建实体变量
  4. CHANGE_VARIABLE 修改变量（字段映射）
  5. BRANCH          是否通过（expNum >= 阈值）
       ├ CHANGE_ENTITY  标记通过（expFlag=true）
       └ CREATE_ENTITY  插入验收记录
  6. CREATE_MAP      验收摘要
  7. MAP_OPERATION   取实验文本
  8. LIST_OPERATION  列表计数
  9. FOR             重试循环
       └ CONVERT_DATA  文本转整数
 10. CUSTOM_ERROR    验收失败告警

复用 v11 的：FIELD / entity_structure / attr_type / left_param / ctx_var /
node_retrieve_by_input / node_retrieve_array / node_create_variable_entity /
node_change_variable / node_list_operation / create_mf / save_mf / gql / rest / content。
"""
import json
import os
import sys
import time
import random
import string
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_v11 import (  # noqa: E402
    FIELD, APP, APP_NAME, APP_CAP, ENT_ID, ENT_DTO, ENT_FULL, ENT_LABEL,
    IN_DTO, OUT_DTO, gql, rest, content, rid, uid,
    app_ref, entity_structure, attr_type, left_param, ctx_var,
    node_retrieve_by_input, node_retrieve_array, node_create_variable_entity,
    node_change_variable, node_list_operation, create_mf, save_mf,
    Q_LIST, BODY_LIST, Q_GET, read_schema,
)

# 业务前缀，用于清理旧产物
PREFIX = "bizXzh"

# 简单值包装
def simple(v):
    return {"type": "Simple", "simple": v, "desc": v}


def expr_var(uid_, output_name, field, caption, data_type, java_type):
    """表达式 VARIABLE token（引用前序出参字段）"""
    return {"uid": uid_, "type": "VARIABLE",
            "value": "%s.%s" % (output_name, field),
            "desc": "%s.%s" % (caption, field)}


def bool_expr(output_name, field, caption, data_type, java_type, op="==", const="true"):
    """布尔表达式（designData 形态，BRANCH 条件用）"""
    toks = [
        expr_var(uid(), output_name, field, caption, data_type, java_type),
        {"uid": uid(), "type": "OPERATOR", "value": op, "desc": op},
        {"uid": uid(), "type": "CONSTANT", "value": const, "desc": const},
    ]
    return {"designData": {
        "expressionTranslation": "微流程.%s.%s %s %s" % (caption, field, op, const),
        "resultTypeInfo": "BOOLEAN", "tokens": toks}}


def node_branch(node_rid, cond_output, cond_field, cond_caption, cond_type, cond_jtype,
                true_nodes, false_nodes):
    """分支节点：一个符合条件分支 + 默认分支"""
    return {
        "nodeId": "BRANCH_" + node_rid, "name": None, "type": "BRANCH",
        "caption": "是否通过", "description": None, "runAfter": None, "input": None,
        "output": None, "isCompleted": True, "actionType": "BRANCH",
        "conditions": [
            {"nodeId": "CONDITION_" + node_rid, "type": "CONDITION",
             "caption": "通过", "description": None, "isCompleted": True,
             "expression": bool_expr(cond_output, cond_field, cond_caption,
                                     cond_type, cond_jtype, ">=", "1"),
             "nodes": true_nodes},
            {"nodeId": "CONDITION_" + node_rid + "x", "type": "CONDITION",
             "caption": "不通过", "description": None, "isCompleted": True,
             "expression": None, "nodes": false_nodes},
        ],
    }


def node_change_entity(node_rid, src_out, src_nodeid, attrs):
    """更新数据：引用前序实体，字段映射"""
    return {
        "nodeId": "CHANGE_ENTITY_" + node_rid, "name": None, "type": "ACTIVITY",
        "caption": "标记通过", "description": None, "runAfter": None, "input": None,
        "output": {"id": None, "javaType": "java.lang.Boolean", "dataType": "BOOLEAN",
                   "type": "OBJECT", "desc": "更新结果", "dtoType": None, "udcApp": None,
                   "name": "_CHANGE_ENTITY_" + node_rid},
        "isCompleted": True, "actionType": "CHANGE_ENTITY",
        "selectParam": {"id": ENT_DTO, "javaType": ENT_DTO, "dataType": "DTO",
                        "type": "OBJECT", "desc": ENT_LABEL, "appName": APP_NAME,
                        "dtoType": "MASTER_ENTITY", "udcApp": True, "relationEntity": ENT_ID,
                        "name": src_out, "position": "parent", "outputName": src_out,
                        "description": ENT_LABEL,
                        "nodeInfo": {"nodeId": src_nodeid, "type": "ACTIVITY",
                                     "actionType": "RETRIEVE"},
                        "key": src_out + "_RETRIEVE", "path": src_out},
        "mappingType": "attrs", "attrs": attrs, "title": ENT_LABEL,
    }


def node_create_entity(node_rid, attrs):
    """插入数据：字段映射"""
    return {
        "nodeId": "CREATE_ENTITY_" + node_rid, "name": None, "type": "ACTIVITY",
        "caption": "插入验收记录", "description": None, "runAfter": None, "input": None,
        "output": {"id": None, "javaType": ENT_DTO, "dataType": "DTO", "type": "OBJECT",
                   "desc": "新增记录", "dtoType": None, "udcApp": None,
                   "name": "_CREATE_ENTITY_" + node_rid},
        "isCompleted": True, "actionType": "CREATE_ENTITY",
        "app": app_ref(), "structure": entity_structure(),
        "title": ENT_LABEL, "methodLegal": entity_structure()["methodLegal"],
        "mappingType": "attrs", "attrs": attrs, "value": None,
    }


def node_create_map(node_rid, entries):
    gen = {"keyType": {"dataType": "String"},
           "valueType": {"dataType": "Object", "javaType": "java.lang.Object"}}
    return {
        "nodeId": "CREATE_MAP_" + node_rid, "name": None, "type": "ACTIVITY",
        "caption": "验收摘要", "description": None, "runAfter": None, "input": None,
        "output": {"dataType": "MAP", "javaType": "java.util.Map", "id": None,
                   "type": "OBJECT", "desc": "验收摘要",
                   "generics": gen,
                   "name": "_CREATE_MAP_" + node_rid},
        "isCompleted": True, "actionType": "CREATE_MAP",
        "paramType": None, "dataType": None, "title": "验收摘要",
        "generics": gen, "entries": entries,
    }


def node_map_operation(node_rid, map_out, map_nodeid):
    """映射操作：赋值(PUT)，往 map 加键值对。对齐 node_templates（PUT 无 output）。"""
    gen = {"keyType": {"dataType": "String"},
           "valueType": {"dataType": "Object", "javaType": "java.lang.Object"}}
    return {
        "nodeId": "MAP_OPERATION_" + node_rid, "name": None, "type": "ACTIVITY",
        "caption": "写入验收结果", "description": None, "runAfter": None, "input": None,
        "output": None,
        "isCompleted": True, "actionType": "MAP_OPERATION",
        "selectMap": {"id": None, "javaType": "java.util.Map", "dataType": "MAP",
                      "type": "OBJECT", "desc": "验收摘要", "name": map_out,
                      "generics": gen,
                      "position": "parent", "outputName": map_out,
                      "description": "验收摘要",
                      "nodeInfo": {"nodeId": map_nodeid, "type": "ACTIVITY",
                                   "actionType": "CREATE_MAP"}},
        "operationType": "PUT", "generics": gen,
        "entries": [{"key": simple("验收结果"), "value": simple("通过")}],
    }


def node_for(node_rid, body_nodes, end_val="3"):
    return {
        "nodeId": "For_" + node_rid, "type": "FOR", "caption": "重试循环",
        "description": None, "runAfter": None, "foreach": None, "isCompleted": True,
        "forStart": simple(1), "forEnd": simple(int(end_val)), "forStep": 1,
        "operator": "<=", "targetName": "重试计数",
        "output": {"id": "", "dataType": "INTEGER", "type": "OBJECT",
                   "desc": "重试计数", "javaType": "java.lang.Integer",
                   "name": "_FOR_" + node_rid},
        "nodes": body_nodes,
    }


def node_convert_data(node_rid, src_out, src_nodeid, field="expText"):
    """类型转换：文本转整数。引用实体字段（children 结构）。"""
    cap, ftype, jtype, aid = FIELD[field]
    return {
        "nodeId": "CONVERT_DATA_" + node_rid, "name": None, "type": "ACTIVITY",
        "caption": "文本转整数", "description": None, "runAfter": None, "input": None,
        "output": {"id": None, "javaType": "java.lang.Integer", "dataType": "INTEGER",
                   "type": "OBJECT", "desc": "转换结果",
                   "name": "_CONVERT_DATA_" + node_rid},
        "isCompleted": True, "actionType": "CONVERT_DATA",
        "convertType": {"desc": "文本转整数", "value": "String2Integer",
                        "dataType": "INTEGER", "type": "OBJECT"},
        "selectParam": {"id": ENT_DTO + "." + field, "javaType": jtype,
                        "dataType": ftype, "type": "OBJECT", "desc": ENT_LABEL,
                        "appName": APP_NAME, "dtoType": "MASTER_ENTITY", "udcApp": True,
                        "relationEntity": ENT_ID, "name": field, "description": cap,
                        "position": "children", "outputName": src_out,
                        "path": ENT_DTO + "." + field, "iconKey": "LinedSearch",
                        "parentLabel": "", "disabled": False, "multiSelect": False},
        "regex": None, "title": "转换结果",
    }


def node_custom_error(node_rid, msg="验收未通过，流程终止"):
    return {
        "nodeId": "CUSTOM_ERROR_" + node_rid, "name": None, "type": "CUSTOM_ERROR",
        "caption": "验收失败告警", "description": None, "runAfter": None, "input": None,
        "output": None, "isCompleted": True, "actionType": "CUSTOM_ERROR",
        "errorType": "GLOBAL", "error": simple(msg),
    }


def build_schema(input_name="_FLOW_INPUT_x1W2U3"):
    """组装完整 dataSchema。"""
    r = lambda n=6: rid(n)

    # 1. 查询源单据（按入参 recordId）
    r1 = r()
    n_retrieve = node_retrieve_by_input(r1, input_name)
    retrieve_out = "_RETRIEVE_" + r1

    # 2. 查询多条（expFlag EQ true）
    r2 = r()
    n_retrieve_arr = node_retrieve_array(r2, "expFlag", "true")
    retrieve_arr_out = "_RETRIEVE_ARRAY_" + r2

    # 3. 创建实体变量
    r3 = r()
    n_cv = node_create_variable_entity(r3)
    cv_out = "_CREATE_VARIABLE_" + r3
    cv_nodeid = "CREATE_VARIABLE_" + r3

    # 4. 修改变量（字段映射 expText）
    r4 = r()
    exp_attr = {"value": {"type": "SelectParam", "selectParam": {
        "description": "实验文本(已改)", "dataType": "STRING", "type": "OBJECT",
        "javaType": "java.lang.String", "name": retrieve_out,
        "outputName": retrieve_out, "position": "parent",
        "nodeInfo": {"nodeId": "RETRIEVE_" + r1, "type": "ACTIVITY", "actionType": "RETRIEVE"},
        "key": retrieve_out + "_RETRIEVE.expText", "path": retrieve_out + ".expText",
        "parentLabel": ENT_LABEL}},
        "attrType": attr_type("expText")}
    n_change_var = node_change_variable(r4, cv_out, cv_nodeid, [exp_attr])

    # 5. 分支：expNum >= 1
    r5 = r()
    # 通过分支：CHANGE_ENTITY + CREATE_ENTITY
    r5a = r()
    r5b = r()
    change_attrs = [{"value": simple(True), "attrType": attr_type("expFlag")}]
    n_change_entity = node_change_entity(r5a, retrieve_out, "RETRIEVE_" + r1, change_attrs)
    create_attrs = [
        {"value": {"type": "SelectParam", "selectParam": {
            "description": "实验文本(已改)", "dataType": "STRING", "type": "OBJECT",
            "javaType": "java.lang.String", "name": retrieve_out, "outputName": retrieve_out,
            "position": "parent",
            "nodeInfo": {"nodeId": "RETRIEVE_" + r1, "type": "ACTIVITY", "actionType": "RETRIEVE"},
            "key": retrieve_out + "_RETRIEVE.expText", "path": retrieve_out + ".expText",
            "parentLabel": ENT_LABEL}},
         "attrType": attr_type("expText")},
    ]
    n_create_entity = node_create_entity(r5b, create_attrs)
    # 不通过分支：CUSTOM_ERROR
    r5c = r()
    n_custom_error = node_custom_error(r5c)
    n_branch = node_branch(r5, retrieve_out, "expNum", "查询源单据", "INTEGER",
                           "java.lang.Integer",
                           [n_change_entity, n_create_entity], [n_custom_error])

    # 6. CREATE_MAP
    r6 = r()
    map_entries = [
        {"key": simple("expText"), "value": simple("验收文本")},
        {"key": simple("expNum"), "value": simple("1")},
    ]
    n_create_map = node_create_map(r6, map_entries)
    map_out = "_CREATE_MAP_" + r6
    map_nodeid = "CREATE_MAP_" + r6

    # 7. MAP_OPERATION（赋值 PUT）
    r7 = r()
    n_map_op = node_map_operation(r7, map_out, map_nodeid)

    # 8. LIST_OPERATION（计数）
    r8 = r()
    n_list_op = node_list_operation(r8, retrieve_arr_out, "RETRIEVE_ARRAY_" + r2, "SIZE")

    # 9. FOR 循环（体内 CONVERT_DATA，引用 RETRIEVE 的 expText）
    r9 = r()
    r9a = r()
    n_convert = node_convert_data(r9a, retrieve_out, "RETRIEVE_" + r1, "expText")
    n_for = node_for(r9, [n_convert], "3")

    # 组装
    return {
        "input": None,
        "output": None,
        "sourceType": "PAGE",
        "trigger": {"id": "", "nodeId": "MFStartNode", "caption": "开始",
                    "description": "", "type": "MANUAL", "input": None, "output": None},
        "nodes": [n_retrieve, n_retrieve_arr, n_cv, n_change_var, n_branch,
                  n_create_map, n_map_op, n_list_op, n_for],
        "endNode": {"id": "", "name": "", "type": "END", "actionType": "END_NODE",
                    "nodeId": "MFEndNode", "caption": "结束", "description": "",
                    "input": None, "output": None},
    }


def main():
    name = PREFIX + rid(4)
    caption = "项目验收流程-" + rid(3)
    schema = build_schema()
    print("=== 生成 %s / %s ===" % (name, caption))

    # create（DRAFT）
    mid = create_mf(name, caption, schema)
    print("create -> mid=%s" % mid)
    if not mid:
        print("!! create 失败")
        return

    # checkSchema（REST）
    res = save_mf(mid, name, caption, schema, state="RELEASE")
    print("checkSchema/update 返回:")
    print(json.dumps(res, ensure_ascii=False)[:800])

    # 回读
    time.sleep(1)
    ds = read_schema(mid)
    print("回读 dataSchema 节点数:", len((ds or {}).get("nodes", [])))

    # 落证据
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "random-biz-evidence", "generated-v12.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"mid": mid, "name": name, "caption": caption,
                   "schema": schema, "checkSchema": res}, f, ensure_ascii=False, indent=1)
    print("证据: %s" % out)


if __name__ == "__main__":
    main()
