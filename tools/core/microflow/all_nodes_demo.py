"""全节点覆盖样板：一条流程用上微流程域 20 种节点类型。

用途
  - 作为生成器能力的**可执行验收**：能生成 → checkSchema 0 错 → 发布 → 接口读回 RELEASE
  - 作为写新流程时的**参考实现**：每种节点该长什么形状，这里都有

用法
  ./.venv/Scripts/python.exe tools/core/microflow/all_nodes_demo.py \
      --app-id <appId> --app-name <appName> --entity <实体name> --entity-id <实体id> \
      --entity-caption <实体中文名> --subflow-id <子流程id> --subflow-name <子流程name> \
      --out scratch/all_nodes.json

  # 然后用 CLI 提交
  ./.venv/Scripts/python.exe tools/core/microflow/build_microflow.py \
      --app-id <appId> --caption "全节点覆盖" --name allNodesDemo \
      --spec scratch/all_nodes.json

覆盖的 20 种
  CREATE_VARIABLE(基础/实体) CREATE_LIST CREATE_MAP CHANGE_VARIABLE
  LIST_OPERATION CHANGE_LIST MAP_OPERATION
  RETRIEVE RETRIEVE_ARRAY CREATE_ENTITY CHANGE_ENTITY
  CREATE_BATCH_ENTITY CHANGE_BATCH_ENTITY DELETE_ENTITY
  SUB_MICROFLOW FOR BRANCH CONDITION BREAK CUSTOM_ERROR

未覆盖（需要额外的语义输入，不在本样板内）
  CALL_APP_SERVICE（要真实 selectMethod 签名）
  CONVERT_DATA（要字段级 selectParam 且类型语义匹配）
  DATA_MAPPING（mappingRows 复杂）
  PUBLISH_BUSINESS_EVENT（要事件 DTO）
  CALL_DATA_FLOW（要数据流对象）

★ 关键坑见 core/facts/udc/microflow/all-nodes-coverage.md 的「铁律」
"""
from __future__ import annotations

import argparse
import json
import random
import string
import uuid
from pathlib import Path

from field_meta import (attr_type as _attr_type, boolean_expression as _bool_expr,  # noqa: E402
                        condition as _cond, constant as _const, select_param_value as _spv,
                        simple as _simple, sort_params as _sorts)

JAVA = {"STRING": "java.lang.String", "BIGINTEGER": "java.lang.Long",
        "INTEGER": "java.lang.Integer", "DECIMAL": "java.math.BigDecimal",
        "BOOLEAN": "java.lang.Boolean", "DATE": "java.util.Date",
        "DATETIME": "java.util.Date", "MAP": "java.util.Map"}

MAP_GENERICS = {"keyType": {"dataType": "String"},
                "valueType": {"dataType": "Object", "javaType": "java.lang.Object"}}

METHOD_LEGAL = {"available": True, "complexCondition": True, "seniorMethod": True,
                "serviceType": "NONE", "interfaceClassFullName": None}


def rid(n: int = 6) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def bool_expression(value: bool = True) -> dict:
    """BOOLEAN 表达式（分支条件用）。

    ★ 必须连 runtimeData.executableExpr 一起给 —— 那是后端编译产物，
      只给 designData 时后端报「必填参数未配置」，且报错 propertyKey 是
      `CONDITION_xxx,<caption>` 而不是字段名，极难定位。
    ★ 模板取自真实库（纯 true 字面量，不含 app 引用，可跨 app 复用）。
    ★ expression=null 的 CONDITION 会被前端渲染成「默认分支」，
      所以 ifBranch 必须有表达式，否则分支退化成无条件。
    """
    tpl_path = Path(__file__).with_name("expression_templates.json")
    tpl = json.loads(tpl_path.read_text(encoding="utf-8"))["boolean_true"]
    out = json.loads(json.dumps(tpl))     # 深拷贝
    if not value:
        out["title"] = "false "
        inner = json.loads(out["schema"])
        inner["designData"]["expressionTranslation"] = "false "
        for tok in inner["designData"].get("tokens") or []:
            if tok.get("value") == "true":
                tok["value"] = tok["desc"] = "false"
        out["schema"] = json.dumps(inner, ensure_ascii=False)
    return out


class Builder:
    def __init__(self, app_id: str, app_name: str, entity: str, entity_id: str,
                 entity_caption: str, subflow: dict | None = None,
                 event_full_name: str | None = None, event_caption: str | None = None,
                 dataflow: dict | None = None, attr_meta: dict | None = None):
        self.app_id = app_id
        self.app_name = app_name
        self.entity = entity
        self.entity_id = entity_id
        self.entity_caption = entity_caption
        self.subflow = subflow
        self.event_full_name = event_full_name
        self.event_caption = event_caption
        self.dataflow = dataflow
        self.attr_meta = attr_meta or {}
        self.app = {"appId": app_id, "appName": app_name, "caption": "",
                    "inApp": True, "udcApp": True, "dynamicDependency": False}

    # ---- 基础设施 ----
    def node(self, _action, _caption, _type="ACTIVITY", **kw):
        # ★ 参数名必须带下划线：CHANGE_LIST 的业务字段就叫 action，
        #   用 action 作形参会和 **kw 撞成 "got multiple values for argument 'action'"
        n = {"nodeId": "%s_%s" % (_action, rid()), "name": None, "type": _type,
             "caption": _caption, "description": None, "runAfter": None,
             "input": None, "output": None, "isCompleted": True, "actionType": _action}
        n.update(kw)
        return n

    def _cls(self) -> str:
        # ★ 首字母必须大写（平台 DTO 就是 YsFull6956Dto）。
        #   改成小写会让所有按属性取值的节点一起报
        #   「对象中配置的属性已被删除或编码被修改」（实测 8 条）。
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
                # ★ CALL_DATA_FLOW 的 entityId 校验读的是 structure.entityId（真实样本同构）
                "entityId": self.entity_id,
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

    # ---- 字段级真实构造（走 field_meta） ----
    def _cond(self, field, right):
        return _cond(self.app_name, self._cls(), field, self.attr_meta[field], right)

    def _sorts(self, field, direction="DESC"):
        return _sorts(self.app_name, self._cls(), field, self.attr_meta[field], direction)

    def _attr(self, field):
        return _attr_type(self.app_name, self._cls(), field, self.attr_meta[field])

    def _val(self, field, output_name):
        return _spv(self.app_name, self._cls(), field,
                    self.attr_meta[field], output_name)

    # ---- 各类节点 ----
    def create_variable(self, title, data_type="STRING", *, entity=False):
        if entity:
            n = self.node("CREATE_VARIABLE", "创建变量(%s)" % title, paramType="ENTITY_OBJECT",
                          dataType="DTO", title=title, app=dict(self.app),
                          structure=self.structure(), mappingType="value", value=None)
            n["output"] = self.dto_out("CREATE_VARIABLE", n, title)
        else:
            n = self.node("CREATE_VARIABLE", "创建变量(%s)" % title, paramType="BASIC",
                          dataType=data_type, title=title, value=None)
            n["output"] = self.simple_out("CREATE_VARIABLE", n, data_type, desc=title)
        return n

    def create_list(self, title, data_type="STRING"):
        n = self.node("CREATE_LIST", "创建列表(%s)" % title, paramType="BASIC",
                      dataType=data_type, title=title)
        n["output"] = self.simple_out("CREATE_LIST", n, data_type, array=True, desc=title)
        return n

    def create_map(self, title):
        n = self.node("CREATE_MAP", "创建Map", paramType=None, dataType=None,
                      title=title, generics=MAP_GENERICS, entries=[])
        n["output"] = self.simple_out("CREATE_MAP", n, "MAP", desc=title,
                                      extra={"generics": MAP_GENERICS})
        return n

    def change_variable(self, src, src_out, caption="修改变量", *, entity_attrs=False):
        """修改数据。entity_attrs=True 时按字段给实体对象赋值（对齐「修改变量」面板的字段映射）。

        ★ attrs[].value 的真实形态：
            Simple      常量          {"type":"Simple","simple":v,"desc":str(v)}
            SelectParam 引用上游字段   {"type":"SelectParam","selectParam":{...}}
            Expression  表达式         {"type":"Expression","expression":{title,schema}}  ← schema 是后端编译产物
        ★ 表达式只能用真实编译好的 blob（expression_templates.json），不能自己编 designData，
          否则保存报「必填参数未配置」。
        """
        if not entity_attrs:
            return self.node("CHANGE_VARIABLE", caption,
                             selectParam=self.ref("CREATE_VARIABLE", src, src_out),
                             mappingType=None, attrs=None, mapping=None)
        attrs = []
        for f, val in [("f01text", _simple("XZH-文本")),
                       ("f03int", _simple(100)),
                       ("f10bool", {"type": "Expression",
                                    "expression": _bool_expr(True)})]:
            if f not in self.attr_meta:
                continue
            attrs.append({"attrType": self._attr(f), "value": val,
                          "desc": self.attr_meta[f]["caption"]})
        return self.node("CHANGE_VARIABLE", caption,
                         selectParam=self.ref("CREATE_VARIABLE", src, src_out),
                         mappingType="attrs", attrs=attrs)

    def list_operation(self, src, src_out, op="SIZE"):
        # ★ operationType 是对象
        return self.node("LIST_OPERATION", "列表处理(%s)" % op,
                         selectParam=self.ref("CREATE_LIST", src, src_out),
                         operationType={"type": op}, title="列表处理后结果")

    def change_list(self, src, src_out, action="ADD", data_source=None):
        # ★ selectParam 必须 ARRAY；★ dataSource 是前端必填，不能 null
        return self.node("CHANGE_LIST", "修改变量(列表)",
                         selectParam=self.ref("CREATE_LIST", src, src_out),
                         action=action,
                         dataSource=data_source if data_source is not None
                         else self.ref("CREATE_LIST", src, src_out))

    def map_operation(self, src, src_out, op="PUT", *, key_ref=None, value_ref=None):
        # ★ 字段名是 selectMap；★ entries 是前端必填（PUT 时要有键值对）
        entries = []
        if key_ref and value_ref:
            entries = [{"key": {"type": "SelectParam", "selectParam": key_ref},
                        "value": {"type": "SelectParam", "selectParam": value_ref}}]
        return self.node("MAP_OPERATION", "Map操作(%s)" % op,
                         selectMap=self.ref("CREATE_MAP", src, src_out),
                         operationType=op, generics=MAP_GENERICS, entries=entries)

    def custom_error(self, msg, caption="自定义错误", error_type="GLOBAL"):
        # ★ type/errorType/error 三处都不是直觉形态
        return self.node("CUSTOM_ERROR", caption, _type="CUSTOM_ERROR",
                         error={"type": "Simple", "simple": msg, "desc": msg},
                         errorType=error_type)

    def retrieve(self, *, array=False):
        if array:
            n = self.node("RETRIEVE_ARRAY", "查询多条数据", app=dict(self.app),
                          structure=self.structure(), selectType="DTO", scope="OBJECT",
                          methodLegal=dict(METHOD_LEGAL), fetchType="CONDITION",
                          nullHandling="CONTINUE",
                          variableTitle=self.entity_caption + "列表",
                          condition=self._cond("f01text", _const("XZH")),
                          sortParams=self._sorts("f03int", "DESC"),
                          size=999, pageSearch="false", pageInfo=None)
            n["output"] = self.dto_out("RETRIEVE_ARRAY", n,
                                       self.entity_caption + "列表", array=True)
        else:
            n = self.node("RETRIEVE", "查询单条数据", app=dict(self.app),
                          structure=self.structure(), selectType="DTO", scope="OBJECT",
                          methodLegal=dict(METHOD_LEGAL), fetchType="CONDITION",
                          nullHandling="CONTINUE", title=self.entity_caption,
                          condition=self._cond("f01text", _const("XZH")),
                          sortParams=self._sorts("f03int", "DESC"))
            n["output"] = self.dto_out("RETRIEVE", n, self.entity_caption)
        return n

    def create_entity(self, value_ref=None, *, entity_out_name=None):
        """插入数据：mappingType=attrs（面板上的「字段映射」），逐字段赋值。

        ★ mappingType 三值：attrs（字段映射）/ value（对象引用）/ mapping。
          面板截图里「对象引用」= value + 参数选变量；「字段映射」= attrs 逐字段。
        """
        attrs = []
        if entity_out_name:
            for f in ("f01text", "f03int", "f05dec"):
                if f in self.attr_meta:
                    attrs.append({"attrType": self._attr(f),
                                  "value": self._val(f, entity_out_name)})
        if attrs:
            n = self.node("CREATE_ENTITY", "插入数据", app=dict(self.app),
                          structure=self.structure(), title=self.entity_caption,
                          methodLegal=dict(METHOD_LEGAL), mappingType="attrs",
                          attrs=attrs, value=None)
        else:
            val = {"type": "SelectParam", "selectParam": value_ref} if value_ref else None
            n = self.node("CREATE_ENTITY", "新增数据", app=dict(self.app),
                          structure=self.structure(), title=self.entity_caption,
                          methodLegal=dict(METHOD_LEGAL), mappingType="value",
                          value=val, attrs=[])
        n["output"] = self.dto_out("CREATE_ENTITY", n, self.entity_caption)
        return n

    def change_entity(self, src, src_out):
        n = self.node("CHANGE_ENTITY", "修改数据",
                      selectParam=self.ref("CREATE_VARIABLE", src, src_out),
                      title=self.entity_caption, attrs=[])
        n["output"] = self.dto_out("CHANGE_ENTITY", n, self.entity_caption)
        return n

    def batch_entity(self, src, src_out, *, create=True):
        act = "CREATE_BATCH_ENTITY" if create else "CHANGE_BATCH_ENTITY"
        n = self.node(act, "批量新增" if create else "批量修改",
                      selectParam=self.ref("RETRIEVE_ARRAY", src, src_out),
                      title=self.entity_caption + "列表")
        n["output"] = self.dto_out(act, n, self.entity_caption + "列表", array=True)
        return n

    def delete_entity(self):
        """删除数据。

        ★ condition 是**条件组数组**：[{type:"GROUP", uuid, conditions:[{type:"CONDITION", ...}]}]
          给 [] 会被判缺必填。
        ★ 样板里用 id = -1 的永假条件：结构合法，但永远匹配不到记录，
          避免这条演示流程被真调用时删数据。
        ★ 另一种写法是 deleteType="SELECT_PARAM" + selectParam（引用实体变量），
          那条路会真删，样板不采用。
        """
        base = "com.seeyon.%s.dto.%sDto" % (self.app_name, self._cls())
        cond = [{
            "type": "GROUP",
            "uuid": str(uuid.uuid4()),
            "conditions": [{
                "type": "CONDITION",
                "leftParam": {"id": base + ".id", "type": "OBJECT",
                              "javaType": "java.lang.Long", "dto": "_id",
                              "field": "id", "desc": "ID", "dataType": "BIGINTEGER",
                              "multiSelect": False},
                "operator": {"value": "EQ", "desc": "="},
                "rightParams": [{"type": "CONSTANT", "value": -1, "desc": "-1"}],
                "uuid": str(uuid.uuid4()),
                "logicalOperator": "AND",
            }],
        }]
        n = self.node("DELETE_ENTITY", "删除数据", app=dict(self.app),
                      structure=self.structure(), title=self.entity_caption,
                      methodLegal=dict(METHOD_LEGAL), deleteType="CONDITION",
                      condition=cond)
        n["output"] = self.dto_out("DELETE_ENTITY", n, self.entity_caption)
        return n

    def sub_microflow(self):
        if not self.subflow:
            return None
        return self.node("SUB_MICROFLOW", "子微流程", mfService=dict(self.subflow),
                         outputName=None, outPutDesc=None)

    # ---- 补充节点（2026-10-24，形状取自真实库样本 + 实测接口） ----
    def call_app_service(self, serial_scheme_code: str = "xiaoshouhetonghao"):
        """自定义服务：调 boot-starter-serialnumber 的 getSerialNumber。

        ★ selectMethod 必须是**完整签名对象**（fullName/implClass/parameter/returnValue/md5），
          只给方法名前端渲染不出入参表。
        ★ app.dynamicDependency 在这个节点是字符串 "NONE"（不是布尔），与 DATA_MAPPING 不同。
        ★ attrs[].attrType 是 DataFlowAttributeDto 形态，value 可以是 Simple。
        """
        method = {
            "caption": "获取下一个流水号", "description": "获取下一个流水号",
            "dubbo": False, "dubboVersion": None,
            "fullName": "com.seeyon.boot.starter.serialnumber.appservice."
                        "SerialNumberAppService.getSerialNumber",
            "group": None,
            "implClass": "com.seeyon.boot.starter.serialnumber.appservice.SerialNumberAppService",
            "interfaceClass": None, "md5": "413b1d849eaae74b9b1f8e292e4d9fc8",
            "parameter": {"caption": None, "type": "com.seeyon.boot.transport.SingleRequest",
                          "item": {"enums": None,
                                   "itemType": "com.seeyon.boot.starter.serialnumber.domain.dto.SerialNumberDto",
                                   "item": None}},
            "returnValue": {"caption": "流水号", "type": "com.seeyon.boot.transport.SingleResponse",
                            "item": {"enums": None, "itemType": "java.lang.String", "item": None}},
            "isCondition": False,
        }
        attr_type = {
            "name": "serialSchemeCode",
            "id": "com.seeyon.boot.starter.serialnumber.domain.dto.SerialNumberDto.serialSchemeCode",
            "fullName": "com.seeyon.boot.starter.serialnumber.domain.dto.SerialNumberDto.serialSchemeCode",
            "javaType": "java.lang.String", "dataType": "STRING", "type": "OBJECT",
            "desc": "方案编码", "multiSelect": False,
            "refApp": "udc", "relationApp": "udc",
            "filterDataType": "STRING", "filterType": "OBJECT",
            "filterFullName": "com.seeyon.boot.starter.serialnumber.domain.dto."
                              "SerialNumberDto.serialSchemeCode",
            "dataI18n": False, "sort": 0, "description": "",
        }
        n = self.node("CALL_APP_SERVICE", "自定义服务(流水号)",
                      app={"appId": None, "appName": "boot-starter-serialnumber",
                           "caption": "流水号组件", "inApp": False, "udcApp": False,
                           "dynamicDependency": "NONE"},
                      selectMethod=method, mappingType="attrs",
                      attrs=[{"attrType": attr_type,
                              "value": {"type": "Simple", "simple": serial_scheme_code,
                                        "desc": serial_scheme_code}}],
                      outputName="流水号")
        n["output"] = self.simple_out("CALL_APP_SERVICE", n, "STRING", desc="流水号")
        return n

    def call_app_service_inapp(self, impl: str, method: str, method_sig: dict,
                               dto_attr: dict, simple_out_type: str = "STRING",
                               title: str = ""):
        """本应用 AppService 自定义服务（入参 DTO → mappingType=attrs）。

        ★ method_sig 来自 udcMicroflowSearchMethodByNamePost（md5/FQN type 必须真实）。
        ★ attrs[].attrType.id 前缀 = parameter.item.itemType（作用域键，不能猜）。
        """
        app = {"appId": None, "appName": self.app_name,
               "caption": None, "inApp": True, "udcApp": True,
               "dynamicDependency": "NONE"}
        n = self.node("CALL_APP_SERVICE", title or ("自定义服务(%s)" % method),
                      app=app, selectMethod=method_sig, mappingType="attrs",
                      attrs=[dto_attr], outputName=title or ("自定义服务(%s)" % method))
        n["output"] = self.simple_out("CALL_APP_SERVICE", n, simple_out_type,
                                      desc="服务返回")
        return n

    def convert_data(self, src, src_out, *, field="f01text", field_caption="文本字段",
                     convert_value="Split", regex="MIDLINE", title="文本拆分"):
        """类型转换：指定符号拆分文本。

        ★ convertType 是对象 {desc,value,dataType,type}，value 是**枚举名**（Split）。
        ★ selectParam 必须是字段级引用（带 customs.sourceType=ENTITY）。
        """
        dto = "com.seeyon.%s.dto.%sDto" % (self.app_name, self._cls())
        payload = dict(src_out)
        payload.update({
            "id": "%s.%s" % (dto, field), "name": field, "description": field_caption,
            "dataType": "STRING", "type": "OBJECT", "javaType": "java.lang.String",
            "position": "children", "outputName": src_out["name"], "path": "%s.%s" % (dto, field),
            "iconKey": "LinedSearch", "parentLabel": "", "disabled": False,
            "multiSelect": False,
            "customs": {"basicType": False, "mfDataI18n": False,
                        "defaultOrExpression": False, "notNull": False,
                        "sourceType": "ENTITY", "dataType": "STRING",
                        "name": field, "id": None}})
        n = self.node("CONVERT_DATA", "类型转换(%s)" % title,
                      convertType={"desc": "指定符号拆分文本", "value": convert_value,
                                   "dataType": "STRING", "type": "ARRAY"},
                      selectParam=payload, regex=regex, title=title)
        n["output"] = self.simple_out("CONVERT_DATA", n, "STRING", array=True, desc=title)
        return n

    def publish_business_event(self, event_full_name: str, event_caption: str,
                              code_value: str = "EVT-001"):
        """事件投递（应用内 = 事件总线）。

        ★ selectEvent 必须是 customs.source=MICRO_FLOW 的 DTO，
          取「微流程 → 对象定义 → 应用内事件对象」创建出来的那个（fullName 形如
          com.seeyon.<app>.dto.microflow.event.<Name>）。
        ★ eventType: IN_APP（事件总线） / AMONG_APP（队列，用 selectMq 而非 selectEvent）。
        """
        n = self.node("PUBLISH_BUSINESS_EVENT", "事件投递(1)", eventType="IN_APP",
                      selectEvent={"key": event_full_name, "label": event_caption,
                                   "value": event_full_name, "fullName": event_full_name,
                                   "caption": event_caption, "source": "MICRO_FLOW",
                                   "dtoType": "CUSTOM", "udcApp": True},
                      mappingType="attrs",
                      attrs=[{"attrType": {"name": "eventCode",
                                           "id": "%s.eventCode" % event_full_name,
                                           "fullName": "%s.eventCode" % event_full_name,
                                           "javaType": "java.lang.String",
                                           "dataType": "STRING", "type": "OBJECT",
                                           "desc": "事件编码", "multiSelect": False},
                              "value": {"type": "Simple", "simple": code_value,
                                        "desc": code_value}}])
        return n

    def call_data_flow(self, flow: dict, src, src_out, *, mapping_id=None):
        """执行生单规则。

        ★ dataFlow 是对象 {id,key,value,title,appId,appUrl,caption,name,sourceEntityId}
          （key/value 与 id 同值，缺一个前端不显示）。
        ★ dataSourceType=SELECT_PARAM，selectParam 指向上游查询出参。
        """
        n = self.node("CALL_DATA_FLOW", "执行生单规则(1)",
                      structure=self.structure(),
                      dataFlow={"id": flow["id"], "key": flow["id"], "value": flow["id"],
                                "title": flow.get("caption", ""), "appId": self.app_id,
                                "appUrl": self.app_name,
                                "caption": flow.get("caption", ""),
                                "name": flow.get("name", ""),
                                "sourceEntityId": self.entity_id, "g_l_index": "1"},
                      dataSourceType="SELECT_PARAM",
                      title=flow.get("caption", "") + "的结果",
                      selectParam=self.ref("RETRIEVE", src, src_out),
                      dataFlowMappingId=mapping_id or flow["id"])
        n["output"] = {"id": "com.seeyon.boot.starter.udcrt.dto.CallDataFlowResultDto",
                       "javaType": "com.seeyon.boot.starter.udcrt.dto.CallDataFlowResultDto",
                       "dataType": "DTO", "type": "OBJECT", "udcApp": True,
                       "dtoType": "CUSTOM", "desc": flow.get("caption", ""),
                       "appName": self.app_name,
                       "name": "_CALL_DATA_FLOW_%s" % n["nodeId"].split("_")[-1]}
        return n

    def data_mapping(self, src, src_out, *, field="f01text", field_caption="文本字段",
                     src_node_id=None, src_action="RETRIEVE", rule_type="ARRAY",
                     fields=None):
        """数据转换：把上游 DTO（单对象或列表）按目标结构重组。

        ★ mappingRule.type 跟上游形态一致：上游是列表 → "ARRAY"，单对象 → "OBJECT"。
          写错会被应用检查判「对象中配置的属性已被删除或编码被修改」（UDC_MICRO_FLOW_04004）。
        ★ targetField.id = DTO全名.字段；reference.id = DTO全名.microflow.节点id.字段。
        """
        dto = "com.seeyon.%s.dto.%sDto" % (self.app_name, self._cls())
        rows = []
        # ★ 对齐真实样本（-8886111811829788620）：targetField/reference 是瘦对象
        #   {id,path,name,desc,dataType,type,javaType}；塞 customs 等多余键反而不认。
        dto = "com.seeyon.%s.dto.%sDto" % (self.app_name, self._cls())
        for f, cap, dt, jt in (fields or [(field, field_caption, "STRING", "java.lang.String")]):
            meta = self.attr_meta.get(f)
            if meta:
                cap, dt = meta["caption"], meta["dataType"]
                jt = meta.get("javaType") or jt
            rows.append({
                "uuid": rid(16),
                "targetField": {"id": "%s.%s" % (dto, f), "path": [], "name": f,
                                "desc": cap, "dataType": dt, "type": "OBJECT",
                                "javaType": jt},
                "mappingMode": "REFERENCE",
                # ★ 平台界面「值拷贝」写的是 **来源对象字段全名**：
                #     ...Dto.f01text      （没有 microflow.<变量>. 这一段）
                #   加 microflow 段会让检查器按属性反查失败，报
                #   「对象中配置的属性已被删除或编码被修改」。
                "value": {"reference": {
                    "id": "%s.%s" % (dto, f),
                    "path": [], "name": f, "desc": cap, "dataType": dt,
                    "type": "OBJECT", "javaType": jt}}})
        n = self.node("DATA_MAPPING", "数据转换",
                      targetType="ENTITY", app=dict(self.app), title="数据转换后的结果",
                      dataType="DTO", structure=self.structure(),
                      mappingRule={
                          "uuid": rid(16), "id": dto, "caption": self.entity_caption,
                          "type": rule_type, "javaType": dto, "subobjects": [],
                          "targetType": "ENTITY", "mappingRows": rows},
                      selectParam=self.ref(src_action, src, src_out))
        n["output"] = self.dto_out("DATA_MAPPING", n, self.entity_caption)
        return n

    def loop_with_break(self, *, start=1, end=3):
        """FOR 计数循环，内部：错误 + 分支{跳出}。

        ★ BREAK 的父必须 BRANCH；BRANCH 的 conditions[] 必须是完整 CONDITION 节点。
        """
        brk = self.node("BREAK", "跳出循环(1)")
        # ★ 应用检查会报「自定义错误(循环内):请勿在该节点后配置其他操作」——
        #   CUSTOM_ERROR 之后不能再有节点，所以它挂在 ifBranch 末尾，且必须是该分支最后一个。
        inner = self.custom_error("循环内提示", "自定义错误(循环内)")
        # ★ 分支必须成对：ifBranch 带真表达式，elseBranch 的 expression 为 null。
        #   只有一个 expression=null 的 case 时，前端把它渲染成「默认分支」，
        #   分支条件就丢了，BREAK 变成无条件执行。
        branch = {"nodeId": "BRANCH_%s" % rid(), "name": None, "type": "BRANCH",
                  "caption": "分支(1)", "description": None, "runAfter": None,
                  "conditions": [
                      {"nodeId": "CONDITION_%s" % rid(), "name": "ifBranch",
                       "type": "CONDITION", "caption": "循环已到末次",
                       "description": None, "runAfter": None,
                       "expression": bool_expression(True),
                       "isCompleted": True, "nodes": [brk, inner]},
                      {"nodeId": "CONDITION_%s" % rid(), "name": "elseBranch",
                       "type": "CONDITION", "caption": "不符合条件即进入该分支",
                       "description": None, "runAfter": None, "expression": None,
                       "isCompleted": True, "nodes": []},
                  ]}
        return {"nodeId": "FOR_%s" % rid(), "name": None, "type": "FOR",
                "caption": "计数循环(1)", "description": None, "runAfter": None,
                "foreach": None, "isCompleted": True,
                "targetName": "序号",
                "operator": "<=", "forStep": 1,
                "forStart": {"type": "Simple", "simple": start, "desc": start},
                "forEnd": {"type": "Simple", "simple": end, "desc": end},
                "output": {"id": None, "javaType": "java.lang.Integer",
                           "dataType": "INTEGER", "type": "OBJECT", "desc": "",
                           "name": "_FOR_%s" % rid()},
                "nodes": [branch]}

    # ---- 组装 ----
    def build(self) -> list[dict]:
        nodes = []
        v_text = self.create_variable("vText", "STRING")
        v_num = self.create_variable("vNum", "BIGINTEGER")
        lst = self.create_list("vList", "STRING")
        mp = self.create_map("vMap")
        nodes += [v_text, v_num, lst, mp]
        nodes.append(self.change_variable(v_text, v_text["output"]))
        nodes.append(self.list_operation(lst, lst["output"], "SIZE"))
        nodes.append(self.change_list(lst, lst["output"], "ADD",
                                      data_source=self.ref("CREATE_VARIABLE", v_text,
                                                           v_text["output"])))
        nodes.append(self.map_operation(mp, mp["output"], "PUT",
                                        key_ref=self.ref("CREATE_VARIABLE", v_text,
                                                         v_text["output"]),
                                        value_ref=self.ref("CREATE_VARIABLE", v_num,
                                                           v_num["output"])))

        v_ent = self.create_variable("vEntity", entity=True)
        nodes.append(v_ent)
        # ★ 给实体对象按字段赋值（f10bool 用真实 BOOLEAN 表达式）
        nodes.append(self.change_variable(v_ent, v_ent["output"],
                                          "修改变量(实体字段)", entity_attrs=True))
        r1 = self.retrieve(array=False)
        r2 = self.retrieve(array=True)
        nodes += [r1, r2]
        nodes.append(self.create_entity(value_ref=self.ref("CREATE_VARIABLE", v_ent, v_ent["output"]),
                                        entity_out_name=v_ent["output"]["name"]))
        nodes.append(self.change_entity(v_ent, v_ent["output"]))
        nodes.append(self.batch_entity(r2, r2["output"], create=True))
        nodes.append(self.batch_entity(r2, r2["output"], create=False))
        nodes.append(self.delete_entity())

        sub = self.sub_microflow()
        if sub:
            nodes.append(sub)

        # ★ V17：多挂自定义服务（本应用 AppService，签名来自 searchMethodByName 实测）
        svc_defs = json.loads(Path(__file__).resolve().parents[3].joinpath(
            "scratch", "svc_binds_v17.json").read_text(encoding="utf-8"))
        sigs = json.loads(Path(__file__).resolve().parents[3].joinpath(
            "scratch", "svc_full_sigs.json").read_text(encoding="utf-8"))
        appsvc = json.loads(Path(__file__).resolve().parents[3].joinpath(
            "scratch", "svc_appsvc_map.json").read_text(encoding="utf-8"))
        for key, bd in svc_defs.items():
            sig = dict(sigs[key])
            sig.setdefault("isCondition", False)
            nodes.append(self.call_app_service_inapp(
                bd["impl"], bd["method"], sig,
                {"attrType": bd["attr"],
                 "value": {"type": "Simple", "simple": bd["val"], "desc": bd["val"]}},
                simple_out_type="STRING", title=bd["title"]))

        # ★ V17：第二个子微流程（SERVICE 型既有微流程）
        sub2_spec = json.loads(Path(__file__).resolve().parents[3].joinpath(
            "scratch", "subflow2_v17.json").read_text(encoding="utf-8"))
        sub2 = self.node("SUB_MICROFLOW", sub2_spec["caption"],
                         mfService=sub2_spec["mfService"], outputName=None, outPutDesc=None)
        nodes.append(sub2)

        # ★ 2026-10-24 新增 5 类节点（截图红框那批）
        nodes.append(self.call_app_service())
        # ★ CONVERT_DATA 只接受「文本 / 多选实体 / 多选枚举」，给 DTO 会报
        #   NOT_STR「该操作只支持文本…」，所以必须挂 STRING 变量
        nodes.append(self.convert_data(r1, r1["output"]))
        if self.event_full_name:
            nodes.append(self.publish_business_event(self.event_full_name,
                                                    self.event_caption or "小爪验收事件"))
        if self.dataflow:
            nodes.append(self.call_data_flow(self.dataflow, r1, r1["output"]))
        nodes.append(self.data_mapping(
            r1, r1["output"], src_node_id=r1["output"]["name"], src_action="RETRIEVE",
            rule_type="OBJECT",
            fields=[("f01text", "文本字段", "STRING", "java.lang.String"),
                    ("f03int", "整数字段", "INTEGER", "java.lang.Integer"),
                    ("f05dec", "小数字段", "DECIMAL", "java.math.BigDecimal")]))

        nodes.append(self.loop_with_break())
        # ★ 应用检查：CUSTOM_ERROR 不能是主链路最后一个节点（END 会把它当出参来源，
        #   报「数据类型不匹配(自定义错误不可以作为出参)」）。挂进永不成立的分支里。
        ce = self.custom_error("全节点覆盖流程：走到这里说明前面都通过了")
        nodes.append({"nodeId": "BRANCH_%s" % rid(), "name": None, "type": "BRANCH",
                      "caption": "分支(错误提示)", "description": None, "runAfter": None,
                      "conditions": [
                          {"nodeId": "CONDITION_%s" % rid(), "name": "ifBranch",
                           "type": "CONDITION", "caption": "永远不成立",
                           "description": None, "runAfter": None,
                           "expression": bool_expression(False),
                           "isCompleted": True, "nodes": [ce]},
                          {"nodeId": "CONDITION_%s" % rid(), "name": "elseBranch",
                           "type": "CONDITION", "caption": "不符合条件即进入该分支",
                           "description": None, "runAfter": None, "expression": None,
                           "isCompleted": True, "nodes": []},
                      ]})
        return nodes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-id", required=True)
    ap.add_argument("--app-name", required=True)
    ap.add_argument("--entity", required=True, help="实体 name（小驼峰）")
    ap.add_argument("--entity-id", required=True)
    ap.add_argument("--entity-caption", required=True)
    ap.add_argument("--subflow-id", help="可做子流程的微流程 id")
    ap.add_argument("--subflow-name", help="微流程 name")
    ap.add_argument("--subflow-caption", default="")
    ap.add_argument("--subflow-type", default="CUSTOM", choices=["SERVICE", "CUSTOM"])
    ap.add_argument("--event-full-name", help="微流程应用内事件对象 fullName")
    ap.add_argument("--event-caption", help="事件对象中文名")
    ap.add_argument("--dataflow-id", help="生单规则 id（CALL_DATA_FLOW 用）")
    ap.add_argument("--dataflow-caption", default="")
    ap.add_argument("--dataflow-name", default="")
    ap.add_argument("--attr-json", help="字段元数据 JSON（name/caption/dataType/id/javaType）")
    ap.add_argument("--out", default="scratch/all_nodes.json")
    a = ap.parse_args()

    sub = None
    if a.subflow_id and a.subflow_name:
        sub = {"id": str(a.subflow_id), "appCaption": None, "appId": a.app_id,
               "appName": None, "caption": a.subflow_caption, "description": "",
               "hasInput": False, "hasOutput": False, "hostPath": None, "input": None,
               "method": "GET", "name": a.subflow_name, "output": None,
               "path": "/microflow/%s" % a.subflow_name,
               "triggerType": "MANUAL", "type": a.subflow_type, "restType": "GET"}

    b = Builder(a.app_id, a.app_name, a.entity, a.entity_id, a.entity_caption, sub,
                event_full_name=a.event_full_name, event_caption=a.event_caption,
                dataflow=({"id": a.dataflow_id, "caption": a.dataflow_caption,
                           "name": a.dataflow_name} if a.dataflow_id else None),
                attr_meta=(json.loads(Path(a.attr_json).read_text(encoding="utf-8"))
                           if a.attr_json else None))
    nodes = b.build()

    types = []
    def walk(ns):
        for n in ns or []:
            types.append(n.get("actionType") or n.get("type"))
            for c in n.get("conditions") or []:
                walk(c.get("nodes"))
            walk(n.get("nodes"))
    walk(nodes)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    # ★ 出入参：input=实体 DTO 数组（对齐真实样本 -9205305882361576511），output=STRING。
    #   output 非空时 endNode 必须带 value 绑定真实来源，否则 checkSchema 报
    #   「root.endNode.value.value 必填参数未配置」。
    dto = "com.seeyon.%s.dto.%sDto" % (a.app_name, b._cls())
    vname = next(n["output"]["name"] for n in nodes
                 if n.get("actionType") == "CREATE_VARIABLE"
                 and n["output"].get("dataType") == "STRING")
    spec = {
        "trigger_type": "MANUAL",
        "input": {"dataType": "DTO", "desc": a.entity_caption,
                  "id": dto, "javaType": dto, "type": "ARRAY",
                  "inApp": True, "appName": a.app_name,
                  "dtoType": "MASTER_ENTITY", "udcApp": True,
                  "hasPagination": False},
        "output": {"dataType": "STRING", "desc": "处理结果"},
        "end_node_value": {"type": "SelectParam", "selectParam": {
            "id": "", "javaType": "java.lang.String", "dataType": "STRING",
            "type": "OBJECT", "desc": "处理结果", "dtoType": "",
            "name": vname, "key": vname, "path": vname, "outputName": vname,
            "description": "处理结果", "position": "parent"},
            "desc": "处理结果 [文本]"},
        "nodes": nodes,
    }
    out.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    print("顶层 %d 个节点，覆盖 %d 种类型 -> %s" % (len(nodes), len(set(types)), out))
    for t in sorted(set(types)):
        print("  ", t)


if __name__ == "__main__":
    main()
