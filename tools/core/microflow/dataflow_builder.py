"""真实数据流样板：每个节点都真正用起来，不是空壳。

设计（用 ysFull6956 的 30 个真实字段）：

  入参 _FLOW_INPUT_xxx : f01text 文本  "验收输入"

  1  CREATE_VARIABLE 文本  vText          （空壳，待赋值）
  2  CHANGE_VARIABLE  vText = 入参         （mappingType=value + SelectParam）
  3  CREATE_LIST     文本  vTexts
  4  CHANGE_LIST     ADD vTexts ← vText   （列表真的有数据）
  5  LIST_OPERATION  SIZE vTexts → vCount （非空计数）
  6  BRANCH  条件: 微流程.vCount > 0
       if  : RETRIEVE 条件 f01text EQ vText，未查到 TERMINATION
       else: CUSTOM_ERROR 表达式消息
  7  CREATE_MAP + MAP_OPERATION PUT(k←vText, v←vCount) + GET(k=vText)
  8  RETRIEVE_ARRAY 条件 f01text EQ vText + 分页 limit 20
  9  CREATE_ENTITY  mappingType=attrs  字段映射 f01text ← vText
 10  CHANGE_ENTITY  vFound 字段映射 f01text ← vText
 11  CONVERT_DATA   文本转整数 vCount
 12  SUB_MICROFLOW
 13  FOR 1..3 { BRANCH(if 计数>0) { BREAK } else {} }
 14  CUSTOM_ERROR
"""
from __future__ import annotations

import argparse
import json
import random
import string
import urllib.parse
import uuid
from pathlib import Path

# ---------------------------------------------------------------- 基础
JAVA = {"STRING": "java.lang.String", "BIGINTEGER": "java.lang.Long",
        "INTEGER": "java.lang.Integer", "DECIMAL": "java.math.BigDecimal",
        "BOOLEAN": "java.lang.Boolean", "DATE": "java.util.Date",
        "DATETIME": "java.util.Date", "MULTILINESTR": "java.lang.String",
        "MAP": "java.util.Map"}

MAP_GENERICS = {"keyType": {"dataType": "String"},
                "valueType": {"dataType": "Object", "javaType": "java.lang.Object"}}

METHOD_LEGAL = {"available": True, "complexCondition": True, "seniorMethod": True,
                "serviceType": "NONE", "interfaceClassFullName": None}

# ★ executableExpr 前缀（1019/1025 真实样本都是它）；后面直接拼明文
EXEC_PREFIX = "93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ="


def rid(n: int = 6) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def uid() -> str:
    return str(uuid.uuid4())


def token(ttype: str, value: str, desc: str, **extra) -> dict:
    t = {"uid": uid(), "type": ttype, "value": value, "desc": desc}
    t.update(extra)
    return t


def expression(tokens: list[dict], translation: str, runtime: str,
               result: str = "BOOLEAN", context: list | None = None) -> dict:  # noqa: D401
    """构造表达式。

    ★ runtimeData.executableExpr = 固定前缀 + URL 编码的明文表达式。
      真实样本证实：纯 true 的是 `前缀+true`，复杂的是 `前缀+%28++%28...`。
    ★ tokens 五种：OPERATOR / FUNCTION / VARIABLE / CONSTANT / SYSTEM
      VARIABLE 的 value 格式：`<nodeId>.<outputName>`，desc 是中文路径
    """
    design = {
        "expressionTranslation": translation,
        "resultTypeInfo": result,
        "resultTypeFullName": None,
        "terminalType": "BACKEND",
        "isMultiSelect": False,
        "context": context or [],
        "tokens": tokens,
        "sourceAppName": None,
    }
    inner = {"designData": design,
             "runtimeData": {"executableExpr": EXEC_PREFIX + urllib.parse.quote_plus(runtime)}}
    return {"title": translation, "schema": json.dumps(inner, ensure_ascii=False)}


def _basic(data_type: str) -> dict:
    """MAP_OPERATION.basic 的对象形态（真实样本：{"key":"STRING","dataType":"STRING"}）。"""
    return {"key": data_type, "dataType": data_type}


def _struct(data_type: str) -> dict:
    """MAP_OPERATION.structure 的对象形态（真实样本带 fullName）。"""
    return {"key": data_type, "dataType": data_type,
            "fullName": JAVA.get(data_type, "java.lang.Object")}


def simple(v) -> dict:
    return {"type": "Simple", "simple": v, "desc": v}


# ---------------------------------------------------------------- 引用
def var_token(node: dict, output: dict, desc: str) -> dict:
    """VARIABLE token：引用某节点出参。

    ★ value 格式是 `<outputName>.<outputName>`（两段都是出参名，**不是 nodeId**）。
      真实样本：_LIST_OPERATION_Rg4IMN._LIST_OPERATION_Rg4IMN
      nodeId 是不带前导下划线的 `LIST_OPERATION_Rg4IMN`，用它做引用会 BOOT_3000。
    """
    name = output["name"]
    return token("VARIABLE", "%s.%s" % (name, name), desc)


def var_context(nodes_and_outputs: list[tuple[dict, dict, str]]) -> list:
    """给 VARIABLE token 配套的 context 变量树。

    ★ 只要 tokens 里出现 VARIABLE，designData.context **必须**给出对应节点树；
      给空数组会 BOOT_3000（后端解析引用时找不到定义）。
    """
    ctx = []
    for node, output, desc in nodes_and_outputs:
        dt = output.get("dataType") or "OBJECT"
        scalar = dt in ("INTEGER", "BIGINTEGER", "STRING", "BOOLEAN", "DECIMAL", "DATE", "DATETIME")
        ctx.append({
            "name": output["name"],
            "description": node.get("caption") or "",
            "type": "OBJECT",
            "selectable": False,
            "enableDataI18n": False,
            "properties": [{
                "name": output["name"],
                "description": desc,
                "type": dt if scalar else "OBJECT",
                "selectable": True,
                "enableDataI18n": False,
                "uniformityParams": {
                    "paramId": "",
                    "paramCategory": dt,
                    "extensionProperties": "",
                    "pageNodeExtension": None,
                },
            }],
        })
    return ctx


def ctx_var(flow_input: dict) -> dict:
    """入参引用（CONTEXT_VARIABLE）：value 是 JSON 字符串。"""
    ref = {"id": None, "javaType": flow_input.get("javaType"),
           "dataType": flow_input.get("dataType"), "type": "OBJECT",
           "desc": flow_input.get("desc"), "dtoType": None, "udcApp": None,
           "name": flow_input["name"], "key": flow_input["name"],
           "path": flow_input["name"], "outputName": flow_input["name"],
           "description": flow_input.get("desc"), "position": "parent"}
    return {"type": "CONTEXT_VARIABLE",
            "value": json.dumps(ref, ensure_ascii=False),
            "desc": flow_input.get("desc")}


def select_param(flow_input: dict) -> dict:
    """入参的 SelectParam 形态（给 CHANGE_VARIABLE.value 用）。"""
    ref = {"id": None, "javaType": flow_input.get("javaType"),
           "dataType": flow_input.get("dataType"), "type": "OBJECT",
           "desc": flow_input.get("desc"), "dtoType": None, "udcApp": None,
           "name": flow_input["name"], "key": flow_input["name"],
           "path": flow_input["name"], "outputName": flow_input["name"],
           "description": flow_input.get("desc"), "position": "parent"}
    return {"type": "SelectParam", "selectParam": ref}


def field_ref(node: dict, output: dict, field: str, java_type: str,
              data_type: str, desc: str) -> dict:
    """引用「某节点出参的某个字段」。

    ★ 这是让节点之间真正穿起来的唯一方式：
      outName 形如 `_RETRIEVE_xxx`，字段 key 形如 `<outName><Dto>.<field>`
    """
    out_name = output["name"]
    dto = output.get("javaType") or ""
    key = "%s%s.%s" % (out_name, dto.replace(".", ""), field)
    return {"key": key, "name": field, "id": "%s.%s" % (dto, field),
            "appName": output.get("appName"),
            "description": desc, "position": "children",
            "path": "%s.%s" % (dto.replace(".", ""), field),
            "outputName": out_name, "dataType": data_type, "type": "OBJECT",
            "javaType": java_type, "dtoType": output.get("dtoType"),
            "udcApp": output.get("udcApp"), "multiSelect": False,
            "nodeInfo": {"nodeId": node["nodeId"], "type": node.get("type", "ACTIVITY"),
                         "actionType": node.get("actionType")}}


class Builder:
    def __init__(self, app_id: str, app_name: str, entity: str, entity_id: str,
                 entity_caption: str, subflow: dict | None = None):
        self.app_id = app_id
        self.app_name = app_name
        self.entity = entity
        self.entity_id = entity_id
        self.entity_caption = entity_caption
        self.subflow = subflow
        self.app = {"appId": app_id, "appName": app_name, "caption": "",
                    "inApp": True, "udcApp": True, "dynamicDependency": False}
        self.nodes: list[dict] = []

    # ---- 基础设施 ----
    def node(self, _action, _caption, _type="ACTIVITY", **kw):
        n = {"nodeId": "%s_%s" % (_action, rid()), "name": None, "type": _type,
             "caption": _caption, "description": None, "runAfter": None,
             "input": None, "output": None, "isCompleted": True, "actionType": _action}
        n.update(kw)
        return n

    def _cls(self) -> str:
        return self.entity[0].upper() + self.entity[1:]

    def structure(self) -> dict:
        c = self._cls()
        base = "com.seeyon.%s" % self.app_name
        return {"key": "%s.domain.entity.%s" % (base, c),
                "id": "%s.dto.%sDto" % (base, c),
                "label": self.entity_caption, "dataType": "DTO",
                "entity": "%s.domain.entity.%s" % (base, c),
                "dtoType": "MASTER_ENTITY", "udcApp": True,
                "fullName": "%s.dto.%sDto" % (base, c),
                "relationEntity": self.entity_id,
                "methodLegal": dict(METHOD_LEGAL)}

    def dto_out(self, action, n, label, *, array=False) -> dict:
        c = self._cls()
        base = "com.seeyon.%s.dto.%sDto" % (self.app_name, c)
        return {"id": base, "javaType": base, "dataType": "DTO",
                "type": "ARRAY" if array else "OBJECT", "desc": label,
                "appName": self.app_name, "dtoType": "MASTER_ENTITY", "udcApp": True,
                "relationEntity": self.entity_id,
                "name": "_%s_%s" % (action, n["nodeId"].split("_")[-1])}

    def simple_out(self, action, n, data_type, *, array=False, desc="", extra=None) -> dict:
        o = {"id": None, "javaType": JAVA.get(data_type, "java.lang.Object"),
             "dataType": data_type, "type": "ARRAY" if array else "OBJECT",
             "desc": desc, "name": "_%s_%s" % (action, n["nodeId"].split("_")[-1])}
        if extra:
            o.update(extra)
        return o

    @staticmethod
    def ref(action, n, out, *, position="parent") -> dict:
        r = dict(out)
        r.update({"position": position, "outputName": out["name"], "name": out["name"],
                  "description": out.get("desc") or "",
                  "nodeInfo": {"nodeId": n["nodeId"], "type": n.get("type", "ACTIVITY"),
                               "actionType": action}})
        return r

    # ---- 变量 ----
    def create_variable(self, title, data_type="STRING", *, entity=False, value=None,
                        mapping=None, attrs=None):
        if entity:
            n = self.node("CREATE_VARIABLE", "创建变量(%s)" % title,
                          paramType="ENTITY_OBJECT", dataType="DTO", title=title,
                          app=dict(self.app), structure=self.structure(),
                          mappingType="value" if value is not None or mapping is not None
                          else None,
                          value=value, attrs=attrs, mapping=mapping)
            n["output"] = self.dto_out("CREATE_VARIABLE", n, title)
        else:
            n = self.node("CREATE_VARIABLE", "创建变量(%s)" % title, paramType="BASIC",
                          dataType=data_type, title=title, value=value)
            n["output"] = self.simple_out("CREATE_VARIABLE", n, data_type, desc=title)
        return n

    def change_variable(self, src, src_out, value, *, mapping_type="value"):
        """修改变量：一定要给 value（Expression 或 SelectParam）。"""
        return self.node("CHANGE_VARIABLE", "修改变量(%s)" % src_out["desc"],
                         selectParam=self.ref("CREATE_VARIABLE", src, src_out),
                         mappingType=mapping_type, value=value)

    # ---- 列表 / Map ----
    def create_list(self, title, data_type="STRING", *, entity=False):
        if entity:
            n = self.node("CREATE_LIST", "创建列表(%s)" % title, paramType="ENTITY_OBJECT",
                          dataType="DTO", title=title, app=dict(self.app),
                          structure=self.structure())
            n["output"] = self.dto_out("CREATE_LIST", n, title, array=True)
        else:
            n = self.node("CREATE_LIST", "创建列表(%s)" % title, paramType="BASIC",
                          dataType=data_type, title=title)
            n["output"] = self.simple_out("CREATE_LIST", n, data_type, array=True, desc=title)
        return n

    def change_list(self, src, src_out, data_source, *, action="ADD"):
        return self.node("CHANGE_LIST", "修改变量(列表)-%s" % action,
                         selectParam=self.ref("CREATE_LIST", src, src_out),
                         action=action, dataSource=data_source)

    def list_operation(self, src, src_out, op="SIZE", *, title="计数"):
        n = self.node("LIST_OPERATION", "列表处理(%s)" % op,
                      selectParam=self.ref("CREATE_LIST", src, src_out),
                      operationType={"type": op}, title=title)
        # SIZE/SUM 之类的出参是标量
        dt = "INTEGER" if op in ("SIZE", "SUM", "MAX", "MIN") else "OBJECT"
        n["output"] = self.simple_out("LIST_OPERATION", n, dt, desc=title)
        return n

    def create_map(self, title):
        n = self.node("CREATE_MAP", "创建Map(%s)" % title, paramType=None, dataType=None,
                      title=title, generics=MAP_GENERICS, entries=[])
        n["output"] = self.simple_out("CREATE_MAP", n, "MAP", desc=title,
                                      extra={"generics": MAP_GENERICS})
        return n

    def map_put(self, mp, mp_out, key_ref, value_ref):
        """赋值：往 Map 里写键值对（entries 必填）。"""
        entries = [{"key": {"type": "SelectParam", "selectParam": key_ref},
                    "value": {"type": "SelectParam", "selectParam": value_ref}}]
        n = self.node("MAP_OPERATION", "Map操作(赋值)",
                      selectMap=self.ref("CREATE_MAP", mp, mp_out),
                      operationType="PUT", generics=MAP_GENERICS, entries=entries)
        return n

    def map_get(self, mp, mp_out, key_ref, out_data_type="INTEGER", value_ref=None):
        """获取：按键取值（出参是映射值）。

        ★ 前端把 entries 列为**无条件必填**，GET/KEY_SET 也不例外，
          所以这里也塞一条键值对（GET 只用 key 部分）。
        """
        # ★ GET 的键字段叫 theKey；出参类型五件套必须成对象形态：
        #   basic / structure 都是 {"key":..., "dataType":...}，
        #   给字符串会让后端按 dict(str) 拆成 {"0":"I","1":"N",...} 并把 dataType 清空。
        n = self.node("MAP_OPERATION", "Map操作(获取)",
                      selectMap=self.ref("CREATE_MAP", mp, mp_out),
                      operationType="GET", generics=MAP_GENERICS,
                      theKey={"type": "SelectParam", "selectParam": key_ref},
                      paramType="BASIC", basic=_basic(out_data_type),
                      arrayOrObject="OBJECT", dataType=out_data_type,
                      nullHandling="CONTINUE", structure=_struct(out_data_type))
        n["output"] = self.simple_out("MAP_OPERATION", n, out_data_type, desc="映射值")
        return n

    def map_keyset(self, mp, mp_out, key_ref=None):
        # ★ 同上：entries 前端无条件必填
        entries = ([{"key": {"type": "SelectParam", "selectParam": key_ref},
                     "value": {"type": "SelectParam", "selectParam": key_ref}}]
                   if key_ref else [])
        n = self.node("MAP_OPERATION", "Map操作(键列表)",
                      selectMap=self.ref("CREATE_MAP", mp, mp_out),
                      operationType="KEY_SET", generics=MAP_GENERICS,
                      entries=entries)
        n["output"] = self.simple_out("MAP_OPERATION", n, "STRING", array=True, desc="键列表")
        return n

    # ---- 实体 ----
    def retrieve(self, *, title="查询单条", cond=None, null_handling="TERMINATION",
                 fetch="CONDITION"):
        # ★ nullHandling=TERMINATION 时后端还要求 nullPromptMessage（提示文案）
        extra = {}
        if null_handling == "TERMINATION":
            extra["nullPromptMessage"] = "未查询到%s，流程终止" % self.entity_caption
        n = self.node("RETRIEVE", title, app=dict(self.app), structure=self.structure(),
                      selectType="DTO", scope="OBJECT", methodLegal=dict(METHOD_LEGAL),
                      fetchType=fetch, nullHandling=null_handling,
                      title=title, condition=cond or [], sortParams=[], **extra)
        n["output"] = self.dto_out("RETRIEVE", n, title)
        return n

    def retrieve_array(self, *, variable_title="查询多条", cond=None, page_size=20,
                       fetch="CONDITION"):
        # ★ size / pageSearch 是**节点顶层**字段（真实 3/4 有 size=999），
        #   不是 pageInfo.size —— 写成 pageInfo 会报「[节点].size 必填」。
        n = self.node("RETRIEVE_ARRAY", variable_title, app=dict(self.app),
                      structure=self.structure(), selectType="DTO",
                      scope="ARRAY",                     # ★ 必须 ARRAY（362/363）
                      methodLegal=dict(METHOD_LEGAL), fetchType=fetch,
                      variableTitle=variable_title,
                      condition=cond or [], sortParams=[],
                      size=page_size, pageSearch="false")
        n["output"] = self.dto_out("RETRIEVE_ARRAY", n, variable_title, array=True)
        return n

    def create_entity(self, *, attrs=None, value=None, mapping_type="attrs"):
        # ★ 前端把 value 也列为必填（即使 mappingType=attrs 用字段映射）
        if value is None:
            value = {"type": "SelectParam", "selectParam": {
                "name": self.entity, "description": self.entity_caption,
                "dataType": "DTO", "type": "OBJECT", "position": "parent",
                "outputName": "_" + self.entity}}
        n = self.node("CREATE_ENTITY", "新增数据", app=dict(self.app),
                      structure=self.structure(), title=self.entity_caption,
                      methodLegal=dict(METHOD_LEGAL), mappingType=mapping_type,
                      value=value, attrs=attrs or [])
        n["output"] = self.dto_out("CREATE_ENTITY", n, self.entity_caption)
        return n

    def change_entity(self, src, src_out, *, attrs=None):
        n = self.node("CHANGE_ENTITY", "修改数据",
                      selectParam=self.ref("RETRIEVE", src, src_out),
                      title=self.entity_caption, attrs=attrs or [])
        n["output"] = self.dto_out("CHANGE_ENTITY", n, self.entity_caption)
        return n

    def delete_entity(self, cond):
        n = self.node("DELETE_ENTITY", "删除数据", app=dict(self.app),
                      structure=self.structure(), title=self.entity_caption,
                      methodLegal=dict(METHOD_LEGAL), deleteType="CONDITION",
                      condition=cond)
        n["output"] = self.dto_out("DELETE_ENTITY", n, self.entity_caption)
        return n

    # ---- 别的 ----
    def sub_microflow(self):
        if not self.subflow:
            return None
        return self.node("SUB_MICROFLOW", "子微流程", mfService=dict(self.subflow),
                         outputName=None, outPutDesc=None)

    def custom_error(self, msg_expr):
        # ★ error 必须是 {"type":"Expression","expression":{title,schema}} —— 少这层包装
        #   后端反序列化会失败（checkSchema 报 BOOT_3000，而 create 却成功）
        if isinstance(msg_expr, dict) and "schema" in msg_expr and "type" not in msg_expr:
            # ★ 真实样本 error.expression 只有 schema（不带 title），
            #   多带 title 页面「填写错误」会显示成空。
            msg_expr = {"type": "Expression",
                        "expression": {"schema": msg_expr["schema"]}}
        return self.node("CUSTOM_ERROR", "自定义错误", _type="CUSTOM_ERROR",
                         error=msg_expr, errorType="GLOBAL")

    def for_loop(self, inner, *, start=1, end=3, target="序号"):
        return {"nodeId": "FOR_%s" % rid(), "name": None, "type": "FOR",
                "caption": "计数循环(1)", "description": None, "runAfter": None,
                "foreach": None, "isCompleted": True, "targetName": target,
                "operator": "<=", "forStep": 1,
                "forStart": simple(start), "forEnd": simple(end),
                "output": {"id": None, "javaType": "java.lang.Integer",
                           "dataType": "INTEGER", "type": "OBJECT", "desc": "",
                           "name": "_FOR_%s" % rid()},
                "nodes": inner}

    def branch(self, if_expr, if_nodes, else_nodes=None, *, if_caption="条件成立",
               else_caption="不符合条件即进入该分支"):
        return {"nodeId": "BRANCH_%s" % rid(), "name": None, "type": "BRANCH",
                "caption": "分支(1)", "description": None, "runAfter": None,
                "conditions": [
                    {"nodeId": "CONDITION_%s" % rid(), "name": "ifBranch",
                     "type": "CONDITION", "caption": if_caption, "description": None,
                     "runAfter": None, "expression": if_expr, "isCompleted": True,
                     "nodes": if_nodes},
                    {"nodeId": "CONDITION_%s" % rid(), "name": "elseBranch",
                     "type": "CONDITION", "caption": else_caption, "description": None,
                     "runAfter": None, "expression": None, "isCompleted": True,
                     "nodes": else_nodes or []},
                ]}
