# -*- coding: utf-8 -*-
"""实体规则（微流程）读写工具 —— 规则域构造器

覆盖：列表 / 详情 / 新建 / 改条件表达式 / 删除

★ 三个已踩的坑（都写进代码了）
  1 `checkSchema` 返回 **BOOT_0000 也可能 check=False**，而且**失败不阻塞 create**
     —— 成功码不可信，必须读 content.check
  2 条件表达式 `expression` 的形状是
     {"title": "<翻译>", "schema": "<JSON 字符串>"}
     ★ schema 是**字符串**不是对象，内含 {"designData":..., "runtimeData":...}
     —— 与表达式域 transform 的返回完全同构，直接用 expression/transform 生成
  3 新建时 `dataSchema` 必须完整（nodes/input/sourceType），
     update 前必须 findById 完整回读后改（否则字段被清空）

用法
----
    # 列规则
    python tools/core/entity/write_entity_rule.py --app-id <id> --entity-id <id> --action list

    # 看一条（含完整 dataSchema）
    ... --action show --rule-id <id>

    # 新建（条件 f03int > 100）
    ... --action create --caption 我的规则 --cond 'f03int > 100'

    # 给已有规则设条件
    ... --action set-condition --rule-id <id> --cond 'f03int > 100'
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from components.platform_operations.graphql_call import call, call_rest  # noqa: E402
from providers.cdp import CdpClient  # noqa: E402

BASE = "/service/udc/microflow"
EXPR_TRANSFORM = "/service/udc/expression/transform"


# ---------------------------------------------------------------- 基础
def _get(client, path: str) -> dict:
    js = ("(async () => { const r = await fetch(%s, {method:'GET', credentials:'include',"
          "headers:{'Accept':'application/json'}}); const t = await r.text();"
          "return JSON.stringify({http:r.status, body:t});})()" % json.dumps(path))
    o = json.loads(client.evaluate(js, await_promise=True))
    try:
        return json.loads(o["body"])
    except Exception:
        return {"raw": o.get("body")}


def list_rules(client, entity_id: str) -> list[dict]:
    r = call(client, "udcMicroflowSearchEntityRulePost",
             {"pageInfo": {"needTotal": True, "pageNumber": 1, "pageSize": 100},
              "params": {"sourceId": entity_id}},
             selection="code message status data { content }")
    ct = r.content
    if isinstance(ct, dict):
        return ct.get("rows") or []
    return ct or []


def get_rule(client, rule_id: str) -> dict:
    doc = _get(client, "%s/findById/%s" % (BASE, rule_id))
    ct = (doc.get("data") or {}).get("content")
    if not ct:
        raise RuntimeError("规则 %s 读不到：%s" % (rule_id, str(doc)[:160]))
    return ct


def check_schema(client, dto: dict) -> dict:
    """★ 返回 content（含 check/errors），**不看 code**。"""
    r = call_rest(client, "%s/checkSchema" % BASE, dto)
    return r["content"] or {}


def create_rule(client, dto: dict) -> str:
    """新建规则。

    ★★ 平台硬限制：**同一实体只能有一条 DEFAULT_VALUE（默认值）规则**。
       再建会返回 `UDC_MICROFLOW_0027 当前实体下已存在默认值规则，无法再次新建！`
       全库 type=2 AND group_type=3 只有 1 条，就是这条限制的结果。
       要验证默认值规则，只能换实体（或先删旧的）。
       VALIDATE（校验）规则没有这个限制，同一实体可以有多条。

    ★★ state 必须是 20（RELEASE），不能是 "DRAFT"。
       实测：state=10 的规则在 `udcMicroflowSearchEntityRulePost` 里**查不到**，
       建完等于隐形（页面规则列表看不见，只有直接拼编辑器 URL 才进得去）。
       用户会以为根本没建成功。所以这里默认就写 20。

    ★★ 建之前先做域作用域校验（fail-closed）。
       三个域允许的节点集合互不相交：默认值域只允许 分支/默认值/子微流程，
       塞「设置值」（页面域节点）前端不报错但节点行为不对。
       见 docs/audit/udc-semantics/RULE-DOMAIN-SCOPE-CONSTRAINTS.md
    """
    schema = dto.get("dataSchema")
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except ValueError:
            schema = None
    if isinstance(schema, dict):
        from components.udc.rule_domain_scope import (
            iter_action_nodes, validate_rule_scope, validate_sub_microflow_service,
        )
        gt = dto.get("groupType")
        errs = validate_rule_scope(schema, gt)
        for at, node in iter_action_nodes(schema):
            if at == "SUB_MICROFLOW":
                errs.extend(validate_sub_microflow_service(node.get("mfService")))
        if errs:
            raise ValueError(
                "规则越域，拒绝创建（%s 域）：\n  - %s" % (gt, "\n  - ".join(errs))
            )

    r = call_rest(client, "%s/create" % BASE, dto)
    if r["code"] != "BOOT_0000":
        raise RuntimeError("create 失败：%s %s" % (r["code"], r["message"]))
    return str(r["content"])


def update_rule(client, dto: dict) -> dict:
    return call_rest(client, "%s/update" % BASE, dto)


# ---------------------------------------------------------------- 表达式
def build_condition(client, app_id: str, entity_id: str, expr: str,
                    entity_name: str, fields: dict,
                    entity_desc: str = "", input_name: str = "dto",
                    desc_prefix: str = "实体规则.开始.") -> dict:
    """把 `f03int > 100` 这类表达式编译成规则条件节点要的 expression。

    fields: {code: (paramId, dataType, caption)}
    input_name: 开始节点的 output.name，实体规则固定为 `"dto"`
                （用户手配样本 -1423060900604263009 / -412839993779275673 实测）。
    """
    tokens, schemas = _compile(client, app_id, entity_id, expr, entity_name,
                               fields, entity_desc, input_name, desc_prefix)
    r = call_rest(client, EXPR_TRANSFORM, {
        "appId": app_id, "paramType": "ENTITY", "terminalSupportType": "BACKEND",
        "resultTypeInfo": "BOOLEAN", "isMultiSelect": False,
        "tokens": tokens, "schemas": schemas})
    ct = r["content"] or {}
    dd, rt = ct.get("designData"), ct.get("runtimeData")
    if not dd or not rt:
        raise RuntimeError("transform 未返回完整表达式：%s" % str(r)[:200])
    # ★ transform 会多返回 terminalType / version，规则条件的 designData 不能带
    #   （实测样本只有 7 个键；带 version 时前端「检查」报
    #     UDC_MICRO_FLOW_04007「历史版本表达式数据异常」）
    # ★ 只裁 version。terminalType 必须保留 —— 实测合法样本（用户手配）
    #   designData 带 terminalType 且无 version；把 terminalType 一起裁掉会被判
    #   「历史版本表达式数据异常」(UDC_MICRO_FLOW_04007)。
    dd = {k: v for k, v in dd.items() if k != "version"}
    return {"title": dd.get("expressionTranslation") or "",
            "schema": json.dumps({"designData": dd, "runtimeData": rt},
                                 ensure_ascii=False)}


def _compile(client, app_id, entity_id, expr, entity_name, fields,
             entity_desc: str = "", input_name: str = "dto",
             desc_prefix: str = "实体规则.开始."):
    """极简表达式 → tokens/schemas（变量 + 比较/算术 + 字面量）。

    ★★ desc 必须带实体标题前缀（2026-10-23 用户截图报错后修）：
       只写「整数字段」→ 页面「变量 整数字段 在上下文中不存在，请确认!」
       必须写「小爪验收实体全量.整数字段」
       与 attribute-expression-write 的实体树+点路径是同一条规则，
       客户真实规则样本的 desc 也是完整路径
       （如 `微流程.查询单条数据(1).投标报备申请_1 [投标报备申请].流程类型`）。

    ★★ 规则条件与字段计算值的 context 结构不同（2026-10-23 实测）：
       字段计算值：context 根 name = 实体 name，token.value = "<实体>.<字段>"（一层）
       规则条件  ：context 根 name = 前序节点输出名（input.name / _RETRIEVE_xxx），
                   且要再套一层同名属性，token.value = "<根>.<根>.<字段>"（两层）
                   实测 -9207748144528243587：
                     ctx.name=_BUSINESS_EVENT_uTREKP, properties[0].name 同名
                     token.value=_BUSINESS_EVENT_uTREKP._BUSINESS_EVENT_uTREKP.info...
       传 input_name 即走规则条件形态。
    """
    import re
    import uuid as _uuid
    ids = {code: v[0] for code, v in fields.items()}
    types = {code: v[1] for code, v in fields.items()}
    caps = {code: v[2] for code, v in fields.items()}
    # ★ 规则条件的 desc 是「微流程.<输入节点caption>.<实体标题>.<字段标题>」，
    #   字段计算值的 desc 只有「<实体标题>.<字段标题>」。
    #   实测样本：微流程.事件监听.销售数据[...].应收填报-销售更新后.应收填报-销售状态
    if desc_prefix and entity_desc:
        prefix = "%s%s." % (desc_prefix, entity_desc)
    elif desc_prefix:
        prefix = desc_prefix            # 实体标题缺失时不留空点
    elif entity_desc:
        prefix = "%s." % entity_desc
    else:
        prefix = ""
    used = [c for c in ids if re.search(r"\b%s\b" % re.escape(c), expr)]
    tokens, _i = [], [0]
    # 规则条件：value 前缀是「根名.根名.」；字段计算值：只是「实体名.」
    val_prefix = "%s.%s." % (input_name, input_name) if input_name else "%s." % entity_name

    def nxt():
        _i[0] += 1
        return _i[0]

    # ★ 整条表达式就是一次函数调用时（如 isNull(fText)），走函数 token 路径。
    #   否则下面的标识符扫描会把函数名当成未知字段。
    _ft = _func_token(expr, fields, val_prefix, prefix, not bool(input_name))
    if _ft:
        tokens.extend(_ft)
        for m0 in re.finditer(r"([A-Za-z_]\w*)", expr):
            if m0.group(1) in ids and m0.group(1) not in [c for c in used]:
                used.append(m0.group(1))
    else:
     for m in re.finditer(r"\b([A-Za-z_]\w*)\b|(\d+(?:\.\d+)?)|(\"[^\"]*\")"
                          r"|(>=|<=|!=|==|>|<|\+|-|\*|/|%)", expr):
         var, num, lit, op = m.groups()
         if var:
             if var not in ids:
                 raise ValueError("未知字段/标识符：%s（可用：%s）" % (var, list(ids)))
             # ★ 规则条件的 VARIABLE token 不带 paramId（实测客户样本就没有）：
             #   带了 transform 会在 executableExpr 前插一段 base64
             #   （如 93gDaq3/...=），后端解析时抛
             #   NumberFormatException.forInputString → UDC_CE_MICRO_FLOW_04000
             tk = {"uid": str(_uuid.uuid4()), "type": "VARIABLE",
                   "value": "%s%s" % (val_prefix, var),
                   "desc": "%s%s" % (prefix, caps[var]), "g_l_index": str(nxt())}
             if not input_name:
                 tk["paramId"] = ids[var]
             tokens.append(tk)
         elif num:
             tokens.append({"uid": str(_uuid.uuid4()), "type": "CONSTANT",
                            "value": num, "desc": num})
         elif lit:
             tokens.append({"uid": str(_uuid.uuid4()), "type": "CONSTANT",
                            "value": lit.strip('"'), "desc": lit.strip('"')})
         elif op:
             tokens.append({"uid": str(_uuid.uuid4()), "type": "OPERATOR",
                            "value": op, "desc": op})
    props = [{"name": c, "description": caps[c], "type": types[c],
              "selectable": True, "enableDataI18n": False,
              "uniformityParams": {"paramId": ids[c], "paramCategory": types[c]}}
             for c in used]
    if not used:
        return tokens, []
    if input_name:
        # 规则条件：根 = 前序节点输出，里面再套一层同名属性
        ext = json.dumps({"id": entity_id, "appName": "", "caption": entity_desc},
                         ensure_ascii=False, separators=(",", ":"))
        root_up = {"paramId": entity_id, "paramCategory": "ENTITY",
                   "extensionProperties": ext, "pageNodeExtension": None}
        # ★ 属性层的 paramCategory 是 OBJECT（不是 ENTITY）——
        #   对应前端 N() 里 `type = dataType === Entity ? Object : dataType`
        #   实测对象（用户手配校验规则）prop.uniformityParams.paramCategory = "OBJECT"
        prop_up = dict(root_up, paramCategory="OBJECT")
        schemas = [{"name": input_name, "description": "开始", "type": "OBJECT",
                    "selectable": False, "enableDataI18n": False,
                    "uniformityParams": root_up,
                    "properties": [{"name": input_name, "description": entity_desc,
                                    "type": "OBJECT", "selectable": True,
                                    "enableDataI18n": False,
                                    "uniformityParams": prop_up,
                                    "properties": props}]}]
    else:
        schemas = [{"name": entity_name, "description": entity_desc, "type": "OBJECT",
                    "selectable": True, "enableDataI18n": False,
                    "uniformityParams": {"paramId": entity_id, "paramCategory": "Entity"},
                    "properties": props}]
    return tokens, schemas


# ---------------------------------------------------------------------------
# 函数调用支持（表达式引擎的 FUNCTION token）
#   结构（LIVE 实测，用户手配样本）：
#     {"uid": <uuid>, "type": "FUNCTION", "value": "isNull", "desc": "为空",
#      "subOps": [[<参数1 的 tokens>], [<参数2 的 tokens>]]}
#   ★ subOps 是二维数组：外层 = 参数序号，内层 = 该参数的 token 序列。
#   函数目录来自 POST /service/udc/expression/preset/list
#   常用：isNull 为空 / textToLong 文本转长整数 / substring 按长度截取字符串
# ---------------------------------------------------------------------------

FUNC_CATALOG = {
    # 条件判断
    "isNull": "为空", "isNotNull": "不为空", "contains": "包含(全部)",
    "notContains": "不包含(全部)", "containsAny": "包含任一",
    "notContainsAny": "不包含任一", "thereIn": "属于",
    "memberBelongsTo": "人员隶属", "unitBelongsTo": "组织隶属",
    # 数学
    "textToInt": "文本转整数", "textToLong": "文本转长整数",
    "textToDecimal": "文本转小数", "roundOff": "取整",
    "roundOffCeiling": "向上取整", "roundOffFloor": "向下取整",
    "abs": "绝对值", "round": "四舍五入", "quotient": "取商",
    # 文本
    "substring": "按长度截取字符串", "substringByIndex": "按位置截取字符串",
    "len": "获取字符串长度", "startsWith": "开头为", "endsWith": "结尾为",
    "containsText": "文本包含", "replace": "按位置替换字符串",
    "split": "按指定符号分割文本", "join": "按指定符号合并文本数组",
    # 日期
    "dateToString": "日期转文本", "stringToDate": "文本转日期",
    "dateDiff": "日期天数差", "year": "获取指定日期的年份",
    "month": "获取指定日期的月份", "day": "获取指定日期的天数",
    # 条件 / 其他
    "ifs": "条件返回", "changeTo": "值变化",
    "getEnumItemName": "获取枚举项名称", "getEnumItemValue": "获取枚举项值",
}


def _split_args(text: str) -> list:
    """按顶层逗号切参数（忽略括号内的逗号）。"""
    out, depth, cur = [], 0, ""
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def _func_token(expr: str, fields: dict, val_prefix: str, prefix: str,
                with_param_id: bool) -> list:
    """把 `textToLong("123")` 编译成 FUNCTION token；非函数返回空列表。"""
    import re
    import uuid as _uuid
    body = expr.strip()
    m = re.fullmatch(r"([A-Za-z_]\w*)\s*\((.*)\)", body, re.S)
    if not m:
        return []
    fname, argstr = m.group(1), m.group(2)
    if fname not in FUNC_CATALOG:
        return []          # 未知函数，交给普通表达式处理
    subops = []
    for arg in _split_args(argstr):
        arg = arg.strip()
        sub = []
        for m2 in re.finditer(r'"([^"]*)"|(\d+(?:\.d+)?)|\b([A-Za-z_]\w*)\b', arg):
            lit, num, var = m2.group(1), m2.group(2), m2.group(3)
            if lit is not None:
                # ★ 字符串常量必须保留引号，否则 transform 按数字推断类型
                #   （实测：textToLong("123") 传裸 123 → FORMULA_6158 期望 STRING 实际 INTEGER）
                sub.append({"uid": str(_uuid.uuid4()), "type": "CONSTANT",
                            "value": '"%s"' % lit, "desc": lit})
            elif num:
                sub.append({"uid": str(_uuid.uuid4()), "type": "CONSTANT",
                            "value": num, "desc": num})
            elif var in fields:
                fid, dtype, cap = fields[var]
                tk = {"uid": str(_uuid.uuid4()), "type": "VARIABLE",
                      "value": "%s%s" % (val_prefix, var),
                      "desc": "%s%s" % (prefix, cap)}
                if with_param_id:
                    tk["paramId"] = fid
                sub.append(tk)
            else:
                sub.append({"uid": str(_uuid.uuid4()), "type": "CONSTANT",
                            "value": var, "desc": var})
        subops.append(sub)
    return [{"uid": str(_uuid.uuid4()), "type": "FUNCTION",
             "value": fname, "desc": FUNC_CATALOG[fname], "subOps": subops}]


def end_node() -> dict:
    """结束节点 —— 真实实体规则 schema 的固定顶层成员。

    实测样本（client 规则 -9205305882361576511 / -9196582754851490168）：
      endNode = {id:"", name:"", type:"END", actionType:"END_NODE",
                 nodeId:"MFEndNode", caption:"结束", description:"",
                 input:null, output:null}
    没有 endNode 时画布缺「结束」这一环。
    """
    return {"id": "", "name": "", "type": "END", "actionType": "END_NODE",
            "nodeId": "MFEndNode", "caption": "结束", "description": "",
            "input": None, "output": None}


def _expr_const(client, app_id: str, text: str, data_type: str = "STRING") -> dict:
    """把字面量编译成 expression（CONSTANT token），供 ACTION 节点的 value 用。"""
    from components.platform_operations.graphql_call import call_rest
    dto = {"appId": app_id, "paramType": "ENTITY", "terminalSupportType": "BACKEND",
           "resultTypeInfo": data_type, "isMultiSelect": False,
           "tokens": [{"uid": "rtC1", "type": "CONSTANT", "value": text,
                       "desc": text}], "schemas": []}
    r = call_rest(client, "/service/udc/expression/transform", dto)
    ct = r["content"] or {}
    dd, rt = ct.get("designData"), ct.get("runtimeData")
    if not dd or not rt:
        raise RuntimeError("常量表达式编译失败：%s" % str(r)[:160])
    return {"schema": json.dumps({"designData": dd, "runtimeData": rt},
                                 ensure_ascii=False),
            "title": dd.get("expressionTranslation") or text}


def assign_value_node(client, app_id: str, entity_id: str, dto_class: str,
                      code: str, info: tuple, value_text: str,
                      suffix: str) -> dict:
    """实体规则的「设置值」节点（给当前实体字段赋值）。

    ★★ 2026-10-23 逐个试出来的必填形态（checkSchema 会一项项报缺）：
        type       = "ACTIVITY"      （不是 ASSIGN_VALUE；写 ASSIGN_VALUE 报「无效的数据」）
        actionType = "ASSIGN_VALUE"  （不是 SET_VALUE；写 SET_VALUE 会校验通过，
                                      但页面按「页面规则版」渲染成 element 语义，是假绿）
        param.caption  非空          （只给 desc 会报 param.caption 缺）
        param.path     必须是非空数组（给字符串永远报缺；元素结构后端不校验）
    正确形态 checkSchema → check=True errors=0，页面分支里出现「设置值」节点。

    权威依据：前端 bundle 模块定义 t8（实体规则版，key = param + value），
    与页面规则版 ez（key = element + value）是两个同 type 的不同定义。
    """
    fid, dtype, cap = info
    from components.udc.data_type_java_type import DATA_TYPE_TO_JAVA_TYPE
    ex = _expr_const(client, app_id, value_text, dtype)
    return {
        "nodeId": "ASSIGN_VALUE_%s" % suffix,
        "type": "ACTIVITY",
        "actionType": "ASSIGN_VALUE",
        "caption": "设置值",
        "description": None,
        "runAfter": None,
        "input": None,
        "output": None,
        "isCompleted": True,
        "param": {
            "name": code,
            "id": "%s.%s" % (dto_class, code),
            "fullName": "%s.%s" % (dto_class, code),
            "caption": cap,
            "path": [{"fieldId": fid,
                      "entity": {"id": entity_id, "appName": None}}],
            "javaType": DATA_TYPE_TO_JAVA_TYPE.get(dtype, "java.lang.String"),
            "dataType": dtype,
            "type": "OBJECT",
            "desc": cap,
            "relationApp": None,
            "relationEntity": "",
            "relationEntityId": "",
            "refApp": None,
            "multiSelect": False,
            "filterDataType": dtype,
            "filterRelationEntity": "",
            "filterType": "OBJECT",
            "filterFullName": "%s.%s" % (dto_class, code),
            "dataI18n": False,
            "sort": 0,
            "description": "",
        },
        "value": {"type": "Expression", "expression": ex, "desc": value_text},
    }


# ---------------------------------------------------------------------------
# 实体规则的动作节点（按 groupType 分三类，结构各不相同 —— 均为 LIVE 回读实测）
#   校验 VALIDATE      : SHOW_MESSAGE / ATTRIBUTE_REQUIRED
#   默认值 DEFAULT_VALUE: DEFAULT_VALUE
#   赋值 ASSIGN_VALUE  : ASSIGN_VALUE
# ---------------------------------------------------------------------------

def _field_param(fid: str, code: str, caption: str, dtype: str) -> dict:
    """动作节点里的字段对象（实测形态：id 是字段 id，path 为空数组）。"""
    from components.udc.data_type_java_type import DATA_TYPE_TO_JAVA_TYPE
    return {
        "id": fid, "name": code, "caption": caption, "path": [],
        "javaType": DATA_TYPE_TO_JAVA_TYPE.get(dtype, "java.lang.String"),
        "dataType": dtype, "enums": None,
        "relationEntity": None, "relationApp": None, "relationType": None,
        "multiSelect": False, "dataI18n": False,
        "businessProps": {}, "validation": {},
    }


def _simple_value(text: str) -> dict:
    return {"type": "Simple", "simple": text, "desc": text}


def default_value_node(entity_id: str, code: str, info: tuple,
                       value_text: str, suffix: str) -> dict:
    """「默认值」节点（DEFAULT_VALUE）。

    实测样本（规则「测试流程查询出参」-412839993779275673）：
      attrs = [{"param": <字段对象, path:[]>,
                "value": {"type":"Simple","simple":null,"desc":"空值",
                          "constantShowPlaceholderKey":"where_emptyvalue"}}]
    ★ 与「设置值」(ASSIGN_VALUE) 不同：这里字段在 attrs 数组里，不是顶层 param。
    """
    fid, dtype, cap = info
    if value_text in (None, "", "空值"):
        val = {"type": "Simple", "simple": None, "desc": "空值",
               "constantShowPlaceholderKey": "where_emptyvalue"}
    else:
        val = _simple_value(value_text)
    return {
        "nodeId": "DEFAULT_VALUE_%s" % suffix,
        "name": None, "type": "ACTIVITY",
        "caption": "默认值", "description": None,
        "runAfter": None, "input": None, "output": None, "isCompleted": True,
        "actionType": "DEFAULT_VALUE",
        "attrs": [{"param": _field_param(fid, code, cap, dtype), "value": val}],
    }


def show_message_node(fid: str, code: str, info: tuple, text: str,
                      suffix: str, level: str = "error") -> dict:
    """「显示信息」节点（SHOW_MESSAGE）—— 校验规则最常用的动作。

    实测样本（规则「是否在变更中校验」）：
      param = <字段对象>, level = "error",
      value = {"type":"Simple","simple":"<提示语>","desc":"<提示语>"}
    """
    _fid, dtype, cap = info
    return {
        "nodeId": "SHOW_MESSAGE_%s" % suffix,
        "name": None, "type": "ACTIVITY",
        "caption": "显示信息", "description": None,
        "runAfter": None, "input": None, "output": None, "isCompleted": True,
        "actionType": "SHOW_MESSAGE",
        "param": _field_param(fid, code, cap, dtype),
        "level": level,
        "value": _simple_value(text),
    }


def required_node(fid: str, code: str, info: tuple, text: str,
                  suffix: str) -> dict:
    """「必填」节点（ATTRIBUTE_REQUIRED）—— 校验规则。

    实测样本（规则「服务费比例校验规则」）：
      params = [<字段对象>, ...]（★ 复数数组，与 SHOW_MESSAGE 的单 param 不同）
      value  = {"type":"Simple","simple":"<提示语>","desc":"<提示语>"}
    """
    _fid, dtype, cap = info
    return {
        "nodeId": "ATTRIBUTE_REQUIRED_%s" % suffix,
        "name": None, "type": "ACTIVITY",
        "caption": "必填", "description": None,
        "runAfter": None, "input": None, "output": None, "isCompleted": True,
        "actionType": "ATTRIBUTE_REQUIRED",
        "params": [_field_param(fid, code, cap, dtype)],
        "value": _simple_value(text),
    }


def node_template(source_id: str, app_id: str, name: str, caption: str,
                  dto_class: str = "", app_name: str = "",
                  entity_desc: str = "") -> dict:
    """最小规则 schema：开始 → 条件分支(if/else) → 结束。

    ★ input / trigger 必须是「开始节点输出」的完整形态，否则前端在
      「检查」时报 `UDC_MICRO_FLOW_04006 前序节点发生变更请重新选择`
      （条件表达式里的 context 根找不到对应节点）。
      实测客户样本 -9205305882361576511（MANUAL + 实体 DTO）：
        input   = {id:<Dto全名>, javaType:<Dto全名>, inApp:true, appName,
                   dataType:"DTO", type:"OBJECT", desc:<实体标题>,
                   dtoType:"MASTER_ENTITY", udcApp:true, hasPagination:false,
                   name:"_FLOW_INPUT_<6位>"}
        trigger = {nodeId:"MFStartNode", type:"MANUAL", output:<同 input>,
                   paramType:"ENTITY_OBJECT", app:{...}, entityObject:{...}}
      旧版写 input={dataType:"ENTITY",name:"dto",id:<实体id>} + trigger={} 是错的。
    """
    ts = str(int(time.time()))[-6:]
    # ★★ 实体规则的 input 就是「开始节点指向实体」的最简形态（用户手配实测
    #    校验规则 -1423060900604263009 / 默认值规则 -412839993779275673 都是）：
    #      {"dataType":"ENTITY","type":"OBJECT","name":"dto","id":<实体id>}
    #    context 根 name = "dto"，token.value = "dto.dto.<字段>"（两层），
    #    desc = "实体规则.开始.<实体标题>.<字段标题>"。
    #    之前臆造的 _FLOW_INPUT_xxx 是错的。
    input_name = "dto"
    inp = {"dataType": "ENTITY", "type": "OBJECT",
           "name": "dto", "id": source_id}
    return {
        "id": "", "appId": app_id, "sourceId": source_id,
        "version": "0", "versionCode": 0,
        "type": "ENTITY_RULE", "triggerType": "MANUAL",
        "name": name, "description": "",
        "nodes": [{
            "nodeId": "BRANCH_%s" % ts, "name": "userBranch", "type": "BRANCH",
            "caption": "分支(1)", "description": "", "runAfter": None,
            "conditions": [
                {"nodeId": "CONDITION_if%s" % ts, "name": "ifBranch",
                 "type": "CONDITION", "caption": "符合条件即进入该分支",
                 "description": "", "runAfter": None,
                 "expression": None, "isCompleted": False, "nodes": []},
                {"nodeId": "CONDITION_el%s" % ts, "name": "elseBranch",
                 "type": "CONDITION", "caption": "不符合条件即进入该分支",
                 "description": "", "runAfter": None,
                 "expression": None, "isCompleted": True, "nodes": []},
            ]}],
        "endNode": end_node(),
        "input": inp,
        "output": None,
        # 实测前端保存后 trigger 恒为 {}（我补的 MFStartNode 那套会被清掉）
        "trigger": {},
        "sourceType": "PAGE", "caption": caption,
    }


# ---------------------------------------------------------------- CLI
def main() -> int:
    ap = argparse.ArgumentParser(description="实体规则读写")
    ap.add_argument("--app-id", required=True)
    ap.add_argument("--entity-id", required=True)
    ap.add_argument("--action", required=True,
                    choices=("list", "show", "create", "set-condition", "delete"))
    ap.add_argument("--rule-id")
    ap.add_argument("--caption")
    ap.add_argument("--cond", help="条件表达式，如 'f03int > 100'")
    ap.add_argument("--set-field", help="要赋值的字段 code（如 f01text）")
    ap.add_argument("--if-value", help="条件成立时给 --set-field 赋的值（常量）")
    ap.add_argument("--else-value", help="条件不成立时给 --set-field 赋的值（常量）")
    ap.add_argument("--entity-name", help="实体 name（拼点路径用；不给则查 schema）")
    ap.add_argument("--group-type", default="validate",
                    choices=("validate", "default", "assign"),
                    help="规则类型：validate=校验 / default=默认值 / assign=赋值")
    ap.add_argument("--port", type=int, default=None)
    a = ap.parse_args()

    client = CdpClient(a.port or 9250, allow_network=True, timeout=90)
    client.connect(url_substr="app-design")

    if a.action == "list":
        rows = list_rules(client, a.entity_id)
        print("规则 %d 条：" % len(rows))
        for x in rows:
            print("  %-22s %-12s %-7s %s" % (str(x.get("caption"))[:22],
                                             x.get("name"), x.get("state"),
                                             x.get("groupType")))
        client.close()
        return 0

    if a.action == "show":
        dto = get_rule(client, a.rule_id)
        print(json.dumps({k: v for k, v in dto.items() if k != "dataSchema"},
                         ensure_ascii=False, indent=2)[:1200])
        print("\ndataSchema:\n" + str(dto.get("dataSchema"))[:1600])
        client.close()
        return 0

    # 以下都要读规则 schema，先确保能找到字段表
    ent_name = a.entity_name
    ent_desc = ""
    app_name = ""
    app_caption = ""
    dto_class = ""
    fields = {}
    if a.cond or a.set_field:
        # ★ 不用 GraphQL 猜字段选择器（attributes 的子字段名不稳定），直接读库：
        #   udc_attribute 的 id 就是 paramId，data_type 就是类型
        try:
            from tools.core._env import connect_db, load_env, query
            from components.udc.data_type_java_type import DATA_TYPE_TO_JAVA_TYPE  # noqa: F401
            conn = connect_db(load_env("test2"), "udc_test2")
            rows = query(conn,
                         "SELECT id, name, caption, data_type FROM udc_attribute "
                         "WHERE entity_id = %s", (int(a.entity_id),))
            ent = query(conn, "SELECT name, caption FROM udc_entity WHERE id = %s",
                        (int(a.entity_id),))
            app = query(conn, "SELECT name, caption FROM udc_application WHERE id = %s",
                        (int(a.app_id),))
            if ent:
                ent_name = ent_name or ent[0]["name"]
                ent_desc = ent[0].get("caption") or ent[0]["name"]
            conn.close()
            app_name = app[0]["name"] if app else ""
            app_caption = app[0].get("caption") or app_name if app else ""
            # 实体 name → DTO 类名：ysFull6956 → Ysfull6956Dto（capitalize 其余小写）
            dto_class = ("com.seeyon.%s.dto.%sDto" % (app_name, ent_name.capitalize())
                         if app_name and ent_name else "")
            for r in rows:
                fields[r["name"]] = (str(r["id"]), r["data_type"],
                                     r["caption"] or r["name"])
        except Exception as exc:
            print("⚠ 读库取字段表失败：%s" % exc)
        if not fields:
            print("❌ 取不到字段表，无法编译条件")
            client.close()
            return 1
        print("字段表 %d 个，实体 %s / %s" % (len(fields), ent_name, ent_desc))

    if a.action == "create":
        name = "ruleLZ%s" % str(int(time.time()))[-6:]
        sc = node_template(a.entity_id, a.app_id, name,
                           a.caption or "小爪规则-%s" % name[-6:],
                           dto_class, app_name, ent_desc)
        if a.cond:
            sc["nodes"][0]["conditions"][0]["expression"] = build_condition(
                client, a.app_id, a.entity_id, a.cond, ent_name, fields,
                ent_desc, sc["input"]["name"], "实体规则.开始.")
            sc["nodes"][0]["conditions"][0]["isCompleted"] = True
        dto = {"appId": a.app_id, "name": name,
               "caption": sc["caption"], "type": "ENTITY_RULE",
               "triggerType": "MANUAL",
               "groupType": {"validate": "VALIDATE", "default": "DEFAULT_VALUE",
                             "assign": "ASSIGN_VALUE"}[a.group_type],
               "sourceId": a.entity_id, "state": 20,
               "creationMethod": "MANUAL", "orderNum": 325, "description": "",
               "dataSchema": json.dumps(sc, ensure_ascii=False)}
        chk = check_schema(client, dto)
        print("checkSchema: check=%s errors=%s" % (chk.get("check"), chk.get("errors")))
        for e in (chk.get("errorMessage") or [])[:3]:
            print("  err:", str(e.get("errorMessage") or e)[:140])
        new_id = create_rule(client, dto)
        print("✅ created id=%s caption=%s" % (new_id, sc["caption"]))
        client.close()
        return 0

    if a.action == "set-condition":
        dto = get_rule(client, a.rule_id)
        sc = json.loads(dto["dataSchema"])
        br = (sc.get("nodes") or [{}])[0]
        conds = br.get("conditions") or []
        if not conds:
            print("❌ 该规则没有条件分支节点")
            client.close()
            return 1
        # ★ 旧 schema 的 input/trigger 是残缺形态 → 用标准模板覆盖
        #   （否则前端「检查」报 UDC_MICRO_FLOW_04006 前序节点发生变更）
        tmpl = node_template(a.entity_id, a.app_id,
                             dto.get("name") or "rule", sc.get("caption") or "",
                             dto_class, app_name, ent_desc)
        cur_name = (sc.get("input") or {}).get("name") or ""
        if not cur_name.startswith(("_FLOW_INPUT_", "_RETRIEVE_",
                                    "_BUSINESS_EVENT_")) or                 (sc.get("trigger") or {}).get("nodeId") != "MFStartNode":
            # ★ 旧 input.name 可能是 "dto" 这种非法值（早期版本写错），
            #   只沿用合法的 _FLOW_INPUT_/_RETRIEVE_/_BUSINESS_EVENT_ 前缀名
            old_name = (sc.get("input") or {}).get("name") or ""
            sc["input"] = dict(tmpl["input"])
            if old_name.startswith(("_FLOW_INPUT_", "_RETRIEVE_", "_BUSINESS_EVENT_")):
                sc["input"]["name"] = old_name
                tmpl["trigger"]["output"] = dict(tmpl["trigger"]["output"])
                tmpl["trigger"]["output"]["name"] = old_name
            sc["trigger"] = tmpl["trigger"]
            print("已升级 input/trigger → %s" % sc["input"]["name"])
        if a.cond:
            conds[0]["expression"] = build_condition(
                client, a.app_id, a.entity_id, a.cond, ent_name, fields,
                ent_desc, sc["input"]["name"], "实体规则.开始.")
            conds[0]["isCompleted"] = True
        if a.set_field:
            if a.set_field not in fields:
                print("❌ 未知字段 %s（可用：%s）" % (a.set_field, list(fields)[:12]))
                client.close()
                return 1
            ts = str(int(time.time()))[-6:]
            if a.if_value is not None:
                conds[0]["nodes"] = [assign_value_node(
                    client, a.app_id, a.entity_id, dto_class, a.set_field,
                    fields[a.set_field], a.if_value, "If%s" % ts)]
            if a.else_value is not None and len(conds) > 1:
                conds[1]["nodes"] = [assign_value_node(
                    client, a.app_id, a.entity_id, dto_class, a.set_field,
                    fields[a.set_field], a.else_value, "El%s" % ts)]
                conds[1]["isCompleted"] = True
            print("赋值动作：%s ← if=%r else=%r（DTO %s）" % (
                a.set_field, a.if_value, a.else_value, dto_class))
        # ★ 补齐「结束」节点 —— 真实规则 schema 必有 endNode，缺了画布少一环
        if not sc.get("endNode"):
            sc["endNode"] = end_node()
        if "runAfter" not in br:
            br["runAfter"] = None
        dto["dataSchema"] = json.dumps(sc, ensure_ascii=False)
        chk = check_schema(client, dto)
        print("checkSchema: check=%s errors=%s" % (chk.get("check"), chk.get("errors")))
        for e in (chk.get("errorMessage") or [])[:3]:
            print("  err:", str(e.get("errorMessage") or e)[:140])
        if not chk.get("check"):
            print("⚠ check=False —— 已写但校验未过，页面可能显示空条件")
        r = update_rule(client, dto)
        print("update: code=%s content=%s" % (r["code"], r["content"]))
        back = get_rule(client, a.rule_id)
        c0 = (json.loads(back["dataSchema"])["nodes"][0]["conditions"][0])
        print("回读 title:", str((c0.get("expression") or {}).get("title"))[:70])
        client.close()
        return 0

    if a.action == "delete":
        r = call(client, "udcMicroflowDeletePost",
                 {"appId": a.app_id, "id": a.rule_id},
                 selection="code message status")
        print("delete: code=%s msg=%s" % (r.code, r.message))
        client.close()
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
