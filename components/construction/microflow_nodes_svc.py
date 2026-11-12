"""服务节点 + 类型转换 + 数据映射构造。复用模板骨架 + 定义库真实数据。"""
from __future__ import annotations

import copy
import json
from typing import Any

from .node_builder import NodeBuilder, load_definition
from .microflow_fields import simple, field_attr, entity_structure
from .microflow_nodes_v2 import _entity_output

_JAVA_BY_DT = {"STRING": "java.lang.String", "INTEGER": "java.lang.Integer",
               "BIGINTEGER": "java.lang.Long", "BOOLEAN": "java.lang.Boolean",
               "DATETIME": "java.util.Date", "DECIMAL": "java.math.BigDecimal"}


def _param_attr_type(svc: dict[str, Any]) -> dict[str, Any]:
    """从 selectMethod.parameter 构造完整 attrType（19 键）。
    简单类型入参：name=parameter.caption、id/fullName=itemType。"""
    param = svc.get("parameter") or {}
    item = param.get("item") or {}
    caption = param.get("caption") or ""
    item_type = item.get("itemType") or ""
    return {
        "name": caption, "id": item_type, "fullName": item_type,
        "javaType": item.get("javaType") or item_type,
        "dataType": item.get("dataType") or "STRING",
        "type": "OBJECT", "desc": caption,
        "multiSelect": False, "refApp": item.get("refApp") or "",
        "relationApp": item.get("refApp") or "",
        "filterDataType": item.get("dataType") or "STRING",
        "filterType": "OBJECT", "filterFullName": item_type,
        "dataI18n": False, "sort": 0, "description": "",
    }


def call_app_service(builder: NodeBuilder, service_name: str,
                     attrs: list[dict[str, Any]], caption: str = "自定义服务",
                     app_name: str | None = None, app_caption: str | None = None,
                     select_method: dict[str, Any] | None = None) -> dict[str, Any]:
    """自定义服务。

    ★ 签名来源优先级（改动原因）：select_method 参数 > 磁盘 definitions/services/*.json。
      磁盘那个是**某个应用专有**的写死签名（含 md5/parameter/returnValue），
      换应用时完全不可复用 —— 实测它在跨应用场景直接 FileNotFoundError。
      新代码应传 `select_method`（来自 LiveRefs.app_service_method 的活引用），
      磁盘路径仅作向后兼容保留，走它会在跨应用时崩。

    app_name 非空 = STARTER 平台服务（如 boot-starter-file 文件组件）；
    app_name 为空 = 当前应用自建 AppService。
    attrs 只传 value（attrType 由 parameter 自动构造，避免简陋 attrType 导致前端 value 被清空）。
    """
    if select_method is not None:
        if not select_method.get("fullName"):
            raise ValueError("select_method 必须是活引用签名（含 fullName），"
                             "实际: %r" % str(select_method)[:120])
        svc = select_method
    else:
        svc = load_definition(f"services/{service_name}.json")
    node = builder.build("CALL_APP_SERVICE", caption=caption)
    node["selectMethod"] = svc
    # ★ starter 组件（流水号/文件/枚举…）不属于当前 UDC 应用：
    #   真实节点里 app.appName=boot-starter-serialnumber、inApp=false。
    #   归属写成本应用会让抽屉显示错的应用、运行时也可能找不到服务。
    _impl = svc.get("implClass") or ""
    if not app_name and _impl.startswith("com.seeyon.boot.starter."):
        _stem = _impl.split(".")[4]                     # serialnumber
        app_name = "boot-starter-" + _stem
        app_caption = app_caption or {"serialnumber": "流水号组件"}.get(_stem, _stem)
    if app_name:
        node["app"] = {"appId": None, "appName": app_name, "caption": app_caption or app_name,
                       "inApp": False, "udcApp": False, "dynamicDependency": "NONE"}
    else:
        # ★ caption 用 builder 的应用名，不写死 —— 写死会让换应用时 UI 显示错的归属
        node["app"] = {"appId": builder.app_id, "appName": builder.app_name,
                       "caption": app_caption or builder.app_name,
                       "inApp": True, "udcApp": True, "dynamicDependency": False}
    full_attr = _param_attr_type(svc)
    # ★ attrType 允许调用方覆盖：parameter 是 SingleRequest<Dto> 时，
    #   平台真实节点里的 attrType 是**字段级**（Dto.serialSchemeCode），
    #   不是 DTO 级。只按 svc 推会得到 Dto 全名，字段映射对不上（V16 样本 ev）。 
    node["attrs"] = [
        {"attrType": dict(a.get("attrType") or full_attr), "value": a.get("value")}
        for a in attrs
    ]
    node["mappingType"] = "attrs"
    # output 从 returnValue.item.itemType 构造（§3.3：DTO 型→id=itemType；简单类型→id=null）
    rv = svc.get("returnValue") or {}
    item = rv.get("item") or {}
    item_type = item.get("itemType")
    # ★ 简单类型返回值不能默认 DTO：itemType=java.lang.String 时 dataType 必须是 STRING，
    #   否则下游写节点按 DTO 处理（2026-11-03 实测构造器曾默认 DTO）。
    _JT_DT = {"java.lang.String": "STRING", "java.lang.Long": "BIGINTEGER",
              "java.lang.Integer": "INTEGER", "java.math.BigDecimal": "DECIMAL",
              "java.lang.Boolean": "BOOLEAN", "java.util.Date": "DATETIME"}
    _dt = item.get("dataType") or _JT_DT.get(item_type or "", "DTO")
    if item_type:
        node["output"] = {
            "id": item_type, "javaType": item_type,
            "dataType": _dt, "type": "OBJECT",
            "desc": caption + "_1", "name": "_" + node["nodeId"],
        }
        if not item_type.startswith("java."):
            node["output"]["dtoType"] = "CUSTOM"
            node["output"]["udcApp"] = False
    else:
        node["output"] = {
            "id": None, "javaType": None, "dataType": "OBJECT", "type": "OBJECT",
            "desc": caption + "_1", "name": "_" + node["nodeId"],
        }
    node["outputName"] = "_" + node["nodeId"]
    return node


def call_data_flow(builder: NodeBuilder, entity: dict[str, Any],
                   data_flow: dict[str, Any], cond_field: str = "id",
                   right_value: dict[str, Any] | None = None,
                   caption: str = "执行生单规则") -> dict[str, Any]:
    """执行生单规则（CALL_DATA_FLOW）。

    ★ 真实样本（1 个）契约：
      - `dataSourceType="CONDITION"` + `condition=[GROUP...]`（按条件筛选源实体）
      - **没有 selectParam**（曾误写，契约闸门判定「真实从未出现」）
    ★ data_flow 必须由调用方从活引用运行时拉取（规则 id/name/caption/sourceEntityId
      都是应用专有，跨应用不可复用），函数内不再写死。
    """
    from .microflow_fields import condition_group, constant
    if not data_flow or not data_flow.get("id"):
        raise ValueError("call_data_flow 需要运行时拉取的 data_flow（含 id/caption/name）")
    node = builder.build("CALL_DATA_FLOW", caption=caption)
    node["structure"] = entity_structure(entity)
    node["dataFlow"] = {
        "id": str(data_flow["id"]), "key": str(data_flow["id"]),
        "value": str(data_flow["id"]),
        "title": data_flow.get("caption") or data_flow.get("name"),
        "appId": builder.app_id, "appUrl": builder.app_name,
        "caption": data_flow.get("caption") or data_flow.get("name"),
        "name": data_flow.get("name"),
        "sourceEntityId": data_flow.get("sourceEntityId"),
        "g_l_index": "1",
    }
    node["dataSourceType"] = "CONDITION"
    node["condition"] = [condition_group(entity, cond_field,
                                        right_value if right_value is not None
                                        else constant(""))]
    node["dataFlowMappingId"] = str(data_flow["id"])
    node["title"] = data_flow.get("caption") or "生单规则结果"
    node["output"] = {
        "id": "com.seeyon.boot.starter.udcrt.dto.CallDataFlowResultDto",
        "javaType": "com.seeyon.boot.starter.udcrt.dto.CallDataFlowResultDto",
        "dataType": "DTO", "type": "OBJECT", "udcApp": True, "dtoType": "CUSTOM",
        "desc": node["title"], "appName": builder.app_name, "name": "_" + node["nodeId"],
    }
    return node


def sub_microflow(builder: NodeBuilder, mf_service: dict[str, Any],
                  attrs: list[dict[str, Any]] | None = None,
                  caption: str = "子微流程",
                  value: dict[str, Any] | None = None,
                  out_desc: str | None = None) -> dict[str, Any]:
    """子微流程（SUB_MICROFLOW）。

    ★ mfService 必须由调用方运行时拉取（子流程 id/name/path 都是应用专有），
      函数内不写死。attrs 只在需要逐字段映射时才给。
    ★ 真实 251 个样本**没有 pageInfo**，模板带的话会被契约闸门剥掉。
    """
    if not mf_service or not mf_service.get("id"):
        raise ValueError("sub_microflow 需要运行时拉取的 mf_service（含 id/name/path）")
    node = builder.build("SUB_MICROFLOW", caption=caption)
    node["mfService"] = dict(mf_service)
    # ★ 模板带出来的残留引用必须清：SUB_MICROFLOW.json 的 attrs[].value 里
    #   含 `_RETRIEVE_KNCEzh`（模板录制时那条流程的节点），换流程后该节点不存在，
    #   G2 会报「表达式引用悬空」。传了 attrs 就用新的，没传就整个清空而不是留着旧值。
    if not attrs:
        node.pop("attrs", None)
        node.pop("mappingType", None)
        node.pop("value", None)
        node.pop("pageInfo", None)
    if attrs:
        node["attrs"] = attrs
        node["mappingType"] = "attrs"
    # ★ 标量入参（input.dataType != DTO）：mappingType 固定 "value"，value 是引用槽。
    #   运行时 parse 对非 DTO 入参直接置 mappingType="value" 并要求 value 合法；
    #   251 个真实样本里 159 个带 value（Expression/SelectParam 都有）。
    if value is not None:
        node["mappingType"] = "value"
        node["value"] = value
    # ★ output 不能留 null：模板里是 null，但真实 305 个样本都有 output.name。
    #   出参类型跟随子流程自身声明（mfService.output 或 outputName/outPutDesc），
    #   拿不到就按 BOOLEAN（真实样本里最常见：子流程出参「结果」）。
    if not (node.get("output") or {}).get("name"):
        src_out = (mf_service.get("output") or {})
        dt = src_out.get("dataType") or mf_service.get("dataType") or "BOOLEAN"
        node["output"] = {
            "appName": None, "id": src_out.get("id"),
            "type": "OBJECT", "dataType": dt,
            "javaType": src_out.get("javaType") or "java.lang.Boolean",
            "dtoType": src_out.get("dtoType"),
            "desc": mf_service.get("outPutDesc") or src_out.get("desc") or "结果",
            "name": "_" + node["nodeId"],
            "udcApp": True,
        }
    if not node.get("outPutDesc"):
        node["outPutDesc"] = node["output"]["desc"]
    if not node.get("outputName"):
        node["outputName"] = out_desc or node["output"]["name"]
    if out_desc:
        node["output"]["desc"] = out_desc
        node["outPutDesc"] = out_desc
    return node


def type_convert(builder: NodeBuilder, entity: dict[str, Any], src_node: dict[str, Any],
                 title: str, caption: str = "类型转换") -> dict[str, Any]:
    """类型转换（CONVERT_DATA，8 种写死类型，convertType.value 枚举）。"""
    from .microflow_fields import field_select_param
    node = builder.build("CONVERT_DATA", caption=caption)
    node["convertType"] = {"desc": "指定符号拆分文本", "value": "Split",
                           "dataType": "STRING", "type": "ARRAY"}
    node["title"] = title
    node["selectParam"] = field_select_param(
        entity, "expText", builder.output_name(src_node), entity["caption"], position="children")
    node["value"] = None
    node["regex"] = "MIDLINE"
    node["output"] = {
        "id": None, "javaType": "java.lang.String", "dataType": "STRING",
        "type": "ARRAY", "desc": title, "name": "_" + node["nodeId"],
    }
    return node


def data_mapping(builder: NodeBuilder, entity: dict[str, Any], src_node: dict[str, Any],
                 caption: str = "数据转换",
                 src_field: str = "name", dst_field: str | None = None,
                 target_entity: dict[str, Any] | None = None) -> dict[str, Any]:
    """数据转换（DATA_MAPPING）：把前序实体字段映射到目标实体。

    src_field/dst_field：映射行两端字段（默认 name→name，同实体自映射即可做最小验证）。
    target_entity：目标实体模型（默认与源相同 → structure.key 形如 <entity>_<entity>）。
    """
    import uuid as _uuid
    node = builder.build("DATA_MAPPING", caption=caption)
    node["app"] = builder._app_ref()
    node["structure"] = entity_structure(entity)
    node["title"] = "数据转换后的结果"
    node["dataType"] = "DTO"
    node["targetType"] = "ENTITY"
    src_name = builder.output_name(src_node)
    tgt = target_entity or entity
    sp_type = (src_node.get("output") or {}).get("type") or "OBJECT"
    sf = entity["attributes"][src_field]
    df = tgt["attributes"][dst_field or src_field]
    tfield = {"id": df["id"], "path": [], "name": dst_field or src_field,
              "desc": df["caption"], "dataType": df.get("dataType", "STRING"),
              "type": "OBJECT", "javaType": df.get("javaType", "java.lang.String")}
    node["mappingRule"] = {
        "uuid": str(_uuid.uuid4())[:16],
        "id": tgt["fullName"], "caption": tgt["caption"],
        "type": "OBJECT", "javaType": tgt["fullName"],
        "subobjects": [], "targetType": "ENTITY",
        "mappingRows": [{
            "uuid": str(_uuid.uuid4())[:16],
            "targetField": tfield,
            "mappingMode": "REFERENCE",
            "value": {"reference": {
                "id": sf["id"], "path": [], "name": src_field,
                "desc": sf["caption"], "dataType": sf.get("dataType", "STRING"),
                "type": "OBJECT", "javaType": sf.get("javaType", "java.lang.String")}},
        }],
    }
    # ★ 语料形态（构建实测两次校准 2026-10-31）：
    #   1) structure.key 恒为 <源实体全名>_<目标实体全名> 两段，同实体自映射也要拼；
    #   2) 上游为列表（RETRIEVE_ARRAY/子表，selectParam.type=ARRAY）时，节点 output.type
    #      必须是 ARRAY（javaType 仍是单个 Dto）——否则生成代码 List→单对象赋值编译失败
    #      （不兼容的类型: List<Dto> 无法转换为 Dto，backBuild.log 20261031191654）。
    node["structure"] = dict(entity_structure(entity))
    node["structure"]["key"] = "%s_%s" % (entity["entity"], tgt["entity"])
    src_out = src_node.get("output") or {}
    node["output"] = _entity_output(entity, node["nodeId"], caption_suffix="")
    # ★ 必须放在 _entity_output 之后：它会整体覆盖 output（type=OBJECT）。
    #   上游是列表时输出必须是 ARRAY，否则下游 LIST_OPERATION 引用被判
    #   「type=ARRAY 与出参声明 OBJECT 不一致」（G31，2026-11-03 实测）。
    if sp_type == "ARRAY" or src_out.get("type") == "ARRAY":
        node["output"]["type"] = "ARRAY"
    node["selectParam"] = {
        "id": entity["fullName"], "javaType": entity["fullName"], "dataType": "DTO",
        "type": sp_type, "desc": src_node.get("title") or entity["caption"],
        "dtoType": "MASTER_ENTITY", "udcApp": True, "name": src_name,
        "outputName": src_name, "position": "parent", "relationEntity": entity["relationEntityId"],
        "appName": entity.get("refApp"),
        "nodeInfo": {"nodeId": src_node["nodeId"], "type": "ACTIVITY",
                     "actionType": src_node.get("actionType")},
    }
    return node


def for_each(builder: NodeBuilder, list_node: dict[str, Any],
             caption: str = "列表循环") -> dict[str, Any]:
    """列表循环（type=FOR_EACH，不是 FOR）。前端据此区分：FOR=计数循环、FOR_EACH=列表循环。"""
    node = builder.build("FOR", caption=caption)
    node["type"] = "FOR_EACH"
    # ★ 真实 384 个 FOR_EACH 样本**全部没有 actionType 键**（控制节点靠 type 直取）。
    #   写了会被契约闸门判为「真实样本从未出现的字段」。
    node.pop("actionType", None)
    node["nodeId"] = "ForEach_" + node["nodeId"].split("_", 1)[-1]
    out = list_node.get("output") or {}
    is_entity = out.get("dataType") == "DTO"
    item_ref = {
        "id": out.get("id"), "javaType": out.get("javaType"),
        "dataType": out.get("dataType", "STRING"), "type": out.get("type", "ARRAY"),
        "desc": list_node.get("title") or out.get("desc", ""),
        "name": builder.output_name(list_node), "position": "parent",
        "outputName": builder.output_name(list_node),
        "description": list_node.get("title") or out.get("desc", ""),
        "nodeInfo": {"nodeId": list_node["nodeId"], "type": "ACTIVITY",
                     "actionType": list_node.get("actionType")},
    }
    if is_entity:
        item_ref["dtoType"] = "MASTER_ENTITY"
        item_ref["udcApp"] = True
        item_ref["relationEntity"] = out.get("relationEntity")
        item_ref["appName"] = out.get("appName")
    # ★ 真实 384 个样本的 foreach 全部是 null（不是 {sourceItemes:[]}）。
    #   {sourceItemes:[]} 只是前端「新建节点」时的临时模板形态，保存后落成 null。
    #   保存链路认的是 selectParam。
    node["foreach"] = None
    node["selectParam"] = item_ref  # FOR_EACH 的「选择列表」= selectParam（checkSchema 必填）
    # entityCaption 真实样本从未出现，删掉
    # 列表循环没有 forStart/forEnd/forStep/operator（计数循环标志）
    for k in ("forStart", "forEnd", "forStep", "operator"):
        node.pop(k, None)
    node["targetName"] = "循环对象"
    if is_entity:
        node["output"] = {
            "id": out.get("id"), "javaType": out.get("javaType"),
            "dataType": "DTO", "type": "OBJECT", "desc": "循环对象",
            "dtoType": "MASTER_ENTITY", "udcApp": True,
            "relationEntity": out.get("relationEntity"), "appName": out.get("appName"),
            "name": "_" + node["nodeId"],
        }
    else:
        node["output"] = {
            "id": None, "javaType": out.get("javaType"),
            "dataType": out.get("dataType", "STRING"), "type": "OBJECT", "desc": "循环对象",
            "name": "_" + node["nodeId"],
        }
    node["nodes"] = []
    return node


def event_delivery(builder: NodeBuilder, event_full_name: str, event_caption: str,
                   event_type: str = "IN_APP", caption: str = "事件投递",
                   ref_node: dict[str, Any] | None = None,
                   field_maps: list[tuple[str, str]] | None = None) -> dict[str, Any]:
    """事件投递（PUBLISH_BUSINESS_EVENT）。

    ★ BusinessEventActivity.parseMappingType 反编译契约：mappingType=value 时
    value 走 buildAttrValue（对象引用），attrs 时逐字段映射。ref_node 传前序
    实体节点即整对象引用（参数映射不落空）。
    """
    node = builder.build("PUBLISH_BUSINESS_EVENT", caption=caption)
    node["eventType"] = event_type
    if event_type == "IN_APP":
        node["selectEvent"] = {
            "key": event_full_name, "label": event_caption, "value": event_full_name,
            "fullName": event_full_name, "caption": event_caption,
            "source": "MICRO_FLOW", "dtoType": "CUSTOM", "udcApp": True,
        }
    if field_maps and ref_node is not None:
        entity = _event_ref_entity(builder, ref_node)
        out_name = "_" + ref_node["nodeId"]
        node["mappingType"] = "attrs"
        from .microflow_fields import basic_select_param
        attrs = []
        for evt_field, ent_field in field_maps:
            a = entity["attributes"].get(ent_field) or {}
            attrs.append({
                "attrType": {
                    "name": evt_field, "id": "%s.%s" % (event_full_name, evt_field),
                    "fullName": "%s.%s" % (event_full_name, evt_field),
                    "javaType": _JAVA_BY_DT.get(a.get("dataType"), "java.lang.String"),
                    "dataType": a.get("dataType", "STRING"), "type": "OBJECT",
                    "desc": evt_field, "multiSelect": False,
                },
                "value": {"type": "SelectParam", "selectParam": {
                    "id": entity["fullName"], "javaType": entity["fullName"],
                    "dataType": "DTO", "type": "OBJECT",
                    "desc": a.get("caption") or ent_field,
                    "dtoType": "MASTER_ENTITY", "udcApp": True,
                    "name": out_name, "outputName": out_name, "position": "parent",
                    "appName": entity.get("appName"),
                    "relationEntity": entity.get("relationEntityId"),
                    "nodeInfo": {"nodeId": ref_node["nodeId"], "type": "ACTIVITY",
                                 "actionType": ref_node["actionType"]},
                    "description": a.get("caption") or ent_field}},
            })
        node["attrs"] = attrs
    elif ref_node is not None:
        entity = _event_ref_entity(builder, ref_node)
        out_name = "_" + ref_node["nodeId"]
        node["mappingType"] = "value"
        node["value"] = {"type": "SelectParam", "selectParam": {
            "id": entity["fullName"], "javaType": entity["fullName"], "dataType": "DTO",
            "type": "OBJECT", "desc": ref_node.get("caption") or "引用数据",
            "dtoType": "MASTER_ENTITY", "udcApp": True,
            "name": out_name, "outputName": out_name, "position": "parent",
            "appName": entity.get("appName"),
            "relationEntity": entity.get("relationEntityId"),
            "nodeInfo": {"nodeId": ref_node["nodeId"], "type": "ACTIVITY",
                         "actionType": ref_node["actionType"]},
            "description": ref_node.get("caption") or "引用数据"},
            "desc": ref_node.get("caption") or "引用数据"}
        node["attrs"] = []
    else:
        node["mappingType"] = "attrs"
        node["attrs"] = []
    return node


def _event_ref_entity(builder: NodeBuilder, ref_node: dict[str, Any]) -> dict[str, Any]:
    """事件 value 引用用的实体结构。dto_short 从 ref_node 的 output 推导，不写死实体名。"""
    from .node_builder import load_entity
    out = ref_node.get("output") or {}
    full_name = out.get("id") or out.get("fullName") or ""
    dto_short = full_name.split(".")[-1]
    if not dto_short:
        raise ValueError("ref_node 无 output.id/fullName，无法推导实体 DTO 名")
    return load_entity(dto_short)
