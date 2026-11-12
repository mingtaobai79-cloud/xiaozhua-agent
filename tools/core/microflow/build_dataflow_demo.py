"""生成一条**真实数据流**的全节点流程（不是空壳）。

用法：
  ./.venv/Scripts/python.exe tools/core/microflow/build_dataflow_demo.py \
      --app-id <id> --app-name <appName> \
      --entity <实体name> --entity-id <实体id> --entity-caption <中文名> \
      --in-field <入参对应字段name> --in-caption <字段中文名> \
      [--subflow-id ... --subflow-name ...] --out scratch/dataflow.json

与 all_nodes_demo.py 的区别：
  那个是「每种 actionType 摆一个」，校验能过但每个节点都是空的；
  这个是「一条从头跑到尾的数据流」，每个节点的取值都来自上游。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dataflow_builder import (Builder, ctx_var, expression, field_ref,  # noqa: E402
                              select_param, simple, token, var_context, var_token)


def _as_int(v):
    """entityId 前端是数字（雪花 id），字符串会算 !首先。"""
    try:
        return int(str(v))
    except (TypeError, ValueError):
        return v


def build_cond(b: Builder, field_name: str, java_type: str, data_type: str,
               field_caption: str, right: dict) -> list:
    """条件组：<实体字段> EQ <某个值>。"""
    base = "com.seeyon.%s.dto.%sDto" % (b.app_name, b._cls())
    return [{
        "type": "GROUP",
        "uuid": __import__("uuid").uuid4().hex,
        "conditions": [{
            "type": "CONDITION",
            # ★ leftParam 是「字段引用对象」，前端按 dto+field 反查实体属性渲染下拉框。
            #   dto 必须是 "_"+字段名（真实样本 dto="_hetonghao"），
            #   写成 "_"+实体名会让前端找不到属性、回退成 JSON 文本显示。
            "leftParam": {"id": "%s.%s" % (base, field_name), "type": "OBJECT",
                          "javaType": java_type, "dto": "_" + field_name,
                          "field": field_name, "desc": field_caption,
                          "dataType": data_type, "multiSelect": False,
                          "entityId": _as_int(b.entity_id)},
            "operator": {"value": "EQ", "desc": "="},
            "rightParams": [right],
            "uuid": __import__("uuid").uuid4().hex,
            "logicalOperator": "AND",
        }],
    }]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-id", required=True)
    ap.add_argument("--app-name", required=True)
    ap.add_argument("--entity", required=True)
    ap.add_argument("--entity-id", required=True)
    ap.add_argument("--entity-caption", required=True)
    ap.add_argument("--in-field", default="f01text", help="入参对应的实体字段 name")
    ap.add_argument("--in-caption", default="文本字段")
    ap.add_argument("--subflow-id")
    ap.add_argument("--subflow-name")
    ap.add_argument("--subflow-caption", default="")
    ap.add_argument("--out", default="scratch/dataflow.json")
    a = ap.parse_args()

    sub = None
    if a.subflow_id and a.subflow_name:
        sub = {"id": str(a.subflow_id), "appCaption": None, "appId": a.app_id,
               "appName": None, "caption": a.subflow_caption, "description": "",
               "hasInput": False, "hasOutput": False, "hostPath": None, "input": None,
               "method": "GET", "name": a.subflow_name, "output": None,
               "path": "/microflow/%s" % a.subflow_name,
               "triggerType": "MANUAL", "type": "CUSTOM", "restType": "GET"}

    b = Builder(a.app_id, a.app_name, a.entity, a.entity_id, a.entity_caption, sub)

    # ---------- 入参 ----------
    fi = {"id": None, "javaType": "java.lang.String", "dataType": "STRING",
          "type": "OBJECT", "desc": a.in_caption, "dtoType": None, "udcApp": None,
          "name": "_FLOW_INPUT_%s" % "".join(__import__("random").choices(
              "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", k=6))}

    nodes: list[dict] = []

    # 1) 创建变量(文本) —— 空壳
    v_text = b.create_variable("vText", "STRING")
    nodes.append(v_text)

    # 2) 修改变量 vText = 入参（真的有值）
    nodes.append(b.change_variable(v_text, v_text["output"], select_param(fi)))

    # 3) 创建列表(文本)
    v_list = b.create_list("vTexts", "STRING")
    nodes.append(v_list)

    # 4) 修改列表 增加 ← vText（列表真的有数据）
    nodes.append(b.change_list(v_list, v_list["output"],
                               data_source=b.ref("CREATE_VARIABLE", v_text, v_text["output"])))

    # 5) 列表处理 计数 → vCount
    v_count = b.list_operation(v_list, v_list["output"], "SIZE", title="文本条数")
    nodes.append(v_count)

    # 6) 条件查询（条件：入参字段 = vText），未查到就终止
    r1 = b.retrieve(title="按文本查单条",
                    cond=build_cond(b, a.in_field, "java.lang.String", "STRING",
                                    a.in_caption, ctx_var(fi)),
                    null_handling="TERMINATION")
    nodes.append(r1)

    # 7) 新增数据（字段映射：入参字段 ← vText）
    base = "com.seeyon.%s.dto.%sDto" % (a.app_name, b._cls())
    attr_map = [{
        "attrType": {"id": "%s.%s" % (base, a.in_field), "name": a.in_field,
                     "fullName": "%s.%s" % (base, a.in_field),
                     "javaType": "java.lang.String", "dataType": "STRING",
                     "type": "OBJECT", "desc": a.in_caption,
                     "relationApp": a.app_name, "refApp": a.app_name,
                     "multiSelect": False},
        "value": {"type": "SelectParam",
                  "selectParam": b.ref("CREATE_VARIABLE", v_text, v_text["output"])},
    }]
    nodes.append(b.create_entity(attrs=attr_map))

    # 8) 修改数据（字段映射：入参字段 ← vText）
    nodes.append(b.change_entity(r1, r1["output"], attrs=attr_map))

    # 9) 查询多条（条件 + 分页）
    r2 = b.retrieve_array(variable_title="按文本查列表",
                          cond=build_cond(b, a.in_field, "java.lang.String", "STRING",
                                          a.in_caption, ctx_var(fi)),
                          page_size=20)
    nodes.append(r2)

    # 10) 创建 Map + 赋值 + 获取 + 键列表
    mp = b.create_map("vMap")
    nodes.append(mp)
    nodes.append(b.map_put(mp, mp["output"],
                           b.ref("CREATE_VARIABLE", v_text, v_text["output"]),
                           b.ref("LIST_OPERATION", v_count, v_count["output"])))
    nodes.append(b.map_get(mp, mp["output"],
                           b.ref("CREATE_VARIABLE", v_text, v_text["output"]),
                           out_data_type="INTEGER"))
    nodes.append(b.map_keyset(mp, mp["output"],
                              b.ref("CREATE_VARIABLE", v_text, v_text["output"])))

    # 11) 删除数据（永假条件，防误删）
    nodes.append(b.delete_entity(build_cond(
        b, "id", "java.lang.Long", "BIGINTEGER", "ID",
        {"type": "CONSTANT", "value": -1, "desc": "-1"})))

    # 12) 子微流程
    sub_node = b.sub_microflow()
    if sub_node:
        nodes.append(sub_node)

    # 13) 条件消息（表达式拼接）
    ctx_count = var_context([(v_count, v_count["output"], "计数")])
    # ★ 字符串拼接表达式必须带 OPERATOR "+"，只有 CONSTANT/VARIABLE 拼不出结果，
    #   页面「填写错误」会显示空。
    msg_expr = expression(
        tokens=[token("CONSTANT", "文本条数：", "文本条数："),
                token("OPERATOR", "+", "+"),
                var_token(v_count, v_count["output"], "微流程.%s.计数" % v_count["caption"]),
                token("OPERATOR", "+", "+"),
                token("CONSTANT", " 条", " 条")],
        translation="文本条数： + 微流程.%s.计数 +  条" % v_count["caption"],
        runtime="'文本条数：' + %s.%s + ' 条'" % (
            v_count["output"]["name"], v_count["output"]["name"]),
        result="STRING",
        context=ctx_count)
    nodes.append(b.custom_error(msg_expr))

    # 14) 分支：计数 > 0 → 跳出循环；否则空
    brk = b.node("BREAK", "跳出循环(1)")
    has_data = expression(
        tokens=[var_token(v_count, v_count["output"], "微流程.%s.计数" % v_count["caption"]),
                token("OPERATOR", ">", ">"),
                token("CONSTANT", "0", "0")],
        translation="微流程.%s.计数 > 0 " % v_count["caption"],
        runtime="( %s.%s > 0 )" % (v_count["output"]["name"], v_count["output"]["name"]),
        context=ctx_count)
    nodes.append(b.for_loop([b.branch(has_data, [brk], [])]))

    out = {
        "trigger_type": "MANUAL",
        "input": fi,
        "output": None,
        "nodes": nodes,
        "endNode": None,
        "sourceType": None,
        "trigger": None,
    }

    types = []
    def walk(ns):
        for n in ns or []:
            types.append(n.get("actionType") or n.get("type"))
            for c in n.get("conditions") or []:
                walk(c.get("nodes"))
            walk(n.get("nodes"))
    walk(nodes)

    p = Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("顶层 %d 个节点，覆盖 %d 种类型 -> %s" % (len(nodes), len(set(types)), p))
    for t in sorted(set(types)):
        print("  ", t)
    print("\n入参:", fi["name"], fi["dataType"], fi["desc"])


if __name__ == "__main__":
    main()
