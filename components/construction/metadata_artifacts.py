"""实体配置面生成器 — 索引/枚举/事件+DTO/过滤方案 body data（宿主执行，agent 不出写）。

证据基线（skill seeyon-udc-design-time-build / references/metadata-artifact-apis.md，
全部 test2 LIVE 探针推进所得，逐字段照录不臆造）：
- 索引 POST /service/udc/index：{caption, entityId, fieldIds=逗号分隔字符串}
  （fieldIds 给数组报 BOOT_3002 ... to type String）
- 枚举 POST /service/udc/graphql?udcEnumPost：body 见 build_enum_body docstring
  （2026-10-20 设计器 UI 抓包 + ctp_enum DB 回读逐字段证实；**不是** REST /udc/udc-enum）
- 枚举项 POST /service/udc/udc-enum-item：{appId, enumId, caption, code(Int), name,
  orderNo, enable:1}（code 传字符串报 BOOT_3002 to type Int）
- DTO POST /service/udc/data-transfer-object/create-dto-with-attrs：body=**ArrayList**
  （对象形态报反序列化错）；元素 {appId, caption, name, source:5, sourceId:0,
  isMetaData:1, isRoot:1, isCommandDto:0, attributes:[...]}；
  attributes 每条 {name, caption, dataType, dataTypeCategory:0, type:0, notNull:false}
  （**不认 javaType**，报 dataTypeCategory must not be null）
- 事件 POST /service/udc/event：{appId, caption, name:拼音, sourceId:0, source:1,
  actionType:1, numberFiredOnce:"1", messageType:0, enabled:1, eventData:<DTO id>,
  eventDataType:0}（action_type 全库恒 1；事件与 DTO 同名配对；eventData 指向
  udc_data_transfer_object.id）
- 过滤方案 POST /service/udc/udc-runtime/filter-plan/create-new（udc-bi jar
  FilterPlanController，网关须双 udc 前缀）：planType:0=FILTER 列表页**隐藏**
  （用户「页面规则没建立」根因）/ 2=LIST 可见；sourceId=`<page_id>_udcDataGridView_<后缀>`；
  content 是 JSON **字符串**（cond 树）
"""
from __future__ import annotations

import json
from typing import Any

SCHEMA_ID = "udc.construction.metadata-artifacts.v1"


def _plan(body: Any, unknowns: list[str] | None = None, note: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": SCHEMA_ID,
        "readonly_plan": True,
        "body": body,
        "note": note,
    }
    if unknowns:
        out["unknowns"] = unknowns
    return out


def build_index_body(caption: str, entity_id: int,
                     field_ids) -> dict[str, Any]:
    """索引 body：fieldIds 逗号分隔字符串（给数组被拒，LIVE BOOT_3002 to type String）。"""
    if not isinstance(field_ids, (list, tuple)):
        field_ids = [field_ids]
    return {
        "caption": caption,
        "entityId": entity_id,
        "fieldIds": ",".join(str(f) for f in field_ids),
    }


def build_enum_body(app_id: int, caption: str, name: str,
                    order_no: int = 100, *,
                    category_id: str = "0",
                    app_guid: str | None = None,
                    enum_type: str = "SAME_LEVEL",
                    expandable: bool = True,
                    enable: bool = True,
                    biz_type: str = "UDC_DESIGN",
                    host_app_name: str | None = None) -> dict[str, Any]:
    """枚举 body —— 与设计器真实提交逐字段对齐（2026-10-20 UI 抓包 + DB 回读证实）。

    设计器「设置 → 枚举 → +」的真实请求体（抓包原文）：
        {"name": "{\\"zh_CN\\":\\"显示名\\"}",   ← name 存 i18n JSON 字符串
         "code": "英文编码",                     ← code 才是编码
         "orderNo": 88, "categoryId": "0",
         "expansible": true, "enable": true, "enumType": "SAME_LEVEL",
         "children": [], "appId": "<appId 字符串>", "hostAppName": null,
         "appGuid": "<udc_application.guid>", "dataStatus": false,
         "bizType": "UDC_DESIGN"}

    两条容易踩的坑（都已实测）：
      1. `name` 是 i18n JSON 字符串，不是裸文本。传裸文本报
         `BOOT_1001 枚举编码 不能为空`——报错说「编码」，实际缺的是 name 的 i18n 形态。
      2. `appGuid` 必须取自 `udc_application.guid`，不是 appId。

    ⚠ 输入法陷阱（2026-10-20 实测）：
       自动化填「枚举编码」框时，若用「先 set('') 再 set(value)」的方式填中文，
       React 受控组件会拿到**拼音中间态**——实测想填 zxjUiTraceEnum，
       提交出去变成 `UIguijimeiju`（拼音转换结果）。自动化填编码框必须
       用英文/数字，或用原生 setter 一次性赋值且不触发 IME 组合事件。

    落库表：`ctp_enum`（不是 udc_enum）。
    """
    body: dict[str, Any] = {
        "name": json.dumps({"zh_CN": caption}, ensure_ascii=False),
        "code": name,
        "orderNo": order_no,
        "categoryId": str(category_id),
        "expansible": expandable,
        "enable": enable,
        "enumType": enum_type,
        "children": [],
        "appId": str(app_id),
        "hostAppName": host_app_name,
        "dataStatus": False,
        "bizType": biz_type,
    }
    if app_guid:
        body["appGuid"] = str(app_guid)
    return body


def build_enum_category_body(app_id: int, name: str, *,
                             order_no: int = 100,
                             parent_id: int | None = None,
                             description: str = "") -> dict[str, Any]:
    """枚举分组（分类）body —— UdcEnumCategoryController.create。

    表结构依据（本轮 DB 实读 udc_enum_category）：
      id / create_time / tenant_id / update_time / version / guid /
      app_id / description / name / order_no / parent_id / preset

    平台必填：appId / name / orderNo（orderNo 缺失与枚举同族，报 BOOT_1001）。
    parentId 为 None 表示顶层分组；平台要 Long，故不接受字符串。
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("枚举分组 name 不能为空（平台必填）")
    if parent_id is not None and not isinstance(parent_id, int):
        raise ValueError(
            f"枚举分组 parent_id={parent_id!r} 须为整数或 None"
            f"（平台要 Long，字符串会被拒）")
    if not isinstance(order_no, int):
        raise ValueError(f"枚举分组 order_no={order_no!r} 须为整数（平台报 BOOT_1001）")
    body: dict[str, Any] = {
        "appId": app_id,
        "name": name.strip(),
        "orderNo": order_no,
    }
    if parent_id is not None:
        body["parentId"] = parent_id
    if description:
        body["description"] = description
    return body


def build_enum_item_body(app_id: int, enum_id: int, caption: str,
                         item_value: str, enum_code: str, order_no: int,
                         enable: int = 1, parent_id: str = "0",
                         item_level: int = 1,
                         app_guid: str | int | None = None) -> dict[str, Any]:
    """枚举项 body —— 与 ctp_enum_item 表结构逐字段对齐（2026-10-20 实读证实）。

    平台必填（从报错反推 + 表结构双向确认）：
      itemValue  枚举项值      ← 报「枚举项编码 不能为空」指的就是它
      parentId   上级枚举项ID  ← 报「上级枚举项ID 不能为null」；顶层填 "0"
      enumId / enumCode  所属枚举
      name       枚举项名称（i18n JSON 字符串，样本见 ctp_enum_item.name）

    ⚠ 老构造器用的是 code / caption，与平台真实槽位不符：
      code 不是枚举项的值，平台报「枚举项编码 不能为空」；
      caption 不是枚举项名称的槽位。

    注意：UDC_ENUM_0002「The code contains only uppercase letters and underscores」
    实际校验的是 **name**（name 带数字被拒）——别把报错字段名当真。
    """
    if item_value in (None, ""):
        raise ValueError(
            "枚举项 item_value 不能为空（平台报「枚举项编码 不能为空」；"
            "该槽位对应 ctp_enum_item.item_value，不是 code）")
    return {
        "appId": str(app_id),
        "enumId": str(enum_id),
        "enumCode": enum_code,
        "name": json.dumps({"zh_CN": caption}, ensure_ascii=False),
        "itemValue": str(item_value),
        "parentId": str(parent_id),
        "itemLevel": item_level,
        "leaf": 1,
        "enable": enable,
        "orderNo": order_no,
        # ★ appGuid 必须取自 udc_application.guid（不是 appId）。
        #   缺了它平台落库成 app_guid=-1，枚举项在「枚举管理」页查不出来（实测）。
        **({"appGuid": str(app_guid)} if app_guid is not None else {}),
    }


def build_dto_with_attrs_body(app_id: int, caption: str, name: str,
                              attributes: list[dict[str, Any]],
                              source: int = 5) -> list[dict[str, Any]]:
    """DTO（数据转移对象）create body = **ArrayList 单元素**（对象形态报反序列化错，LIVE）。

    attributes 每条补 dataTypeCategory=0（消息类字段全库分布 4089/223/6）+
    type 默认 0；不注入 javaType（平台不认，报 dataTypeCategory must not be null）。
    ★ 空值约束字段名是 notNull（Boolean），不是 isNotNull ——
      BaseUdcAttributeDto 的字段是 private Boolean notNull，getter getNotNull()。
    返回裸 list（平台 body 就是数组，不包一层对象）；source:5=微流程消息 DTO
    （全库分布 {1,4,5}，事件监听走 5），事件与 DTO 同名配对。
    """
    attrs = []
    for a in attributes:
        entry = {"name": a.get("name"), "caption": a.get("caption", a.get("name")),
                 "dataType": a.get("dataType", "STRING"),
                 "dataTypeCategory": a.get("dataTypeCategory", 0),
                 "type": a.get("type", 0),
                 "notNull": bool(a.get("notNull") or a.get("isNotNull"))}
        attrs.append(entry)
    return [{"appId": app_id, "caption": caption, "name": name, "source": source,
             "sourceId": 0, "isMetaData": 1, "isRoot": 1, "isCommandDto": 0,
             "attributes": attrs}]


def build_event_body(app_id: int, caption: str, event_name: str,
                     dto_id: int) -> dict[str, Any]:
    """事件 body（LIVE 全字段字典）；eventData 指向 udc_data_transfer_object.id。"""
    return {
        "appId": app_id, "caption": caption, "name": event_name,
        "sourceId": 0, "source": 1, "actionType": 1,
        "numberFiredOnce": "1", "messageType": 0, "enabled": 1,
        "eventData": dto_id, "eventDataType": 0,
    }


def build_event_with_data_body(app_id: int, caption: str, event_name: str,
                               entity_id: int, attrs: list[dict[str, Any]],
                               description: str = "",
                               message_type: int = 0) -> dict[str, Any]:
    """事件 tab「新建事件」真实 body —— 组件 77200 createEventWithData（§2.8.2① 逐字）。

    UDC 实体事件与「裸事件」不同：它携带 eventDataList（消息源=微流程），
    走 udcEventCreateWithDataPost，不是 udcEventPost。

    attrs 每条来自**微流程节点输出参数**（selectParam），键：
      outputName / description / dataType / javaType / type(OBJECT|LIST)
    dataType 规则（§2.8.2①）：Dto/Enum 类型取 javaType，否则用 dataType 原值。
    type 规则：selectParam.type.toUpperCase()=="ARRAY" ? "LIST" : "OBJECT"。

    本构造器把 attrs 归一为 attributes；dataTypeCategory 由调用方按 dataType 查
    数据类型能力表（udcDataTypeDataTypesByAppIdAppGet）后传入，缺省 0（不臆造）。
    """
    attributes = []
    for a in attrs:
        sp = a.get("selectParam", a)   # 允许直接传已展平的 selectParam
        dt = sp.get("dataType")
        java_type = sp.get("javaType")
        # Dto/Enum → 取 javaType（§2.8.2① 三元判断）
        resolved_dt = java_type if (sp.get("isDto") or sp.get("isEnum")) else dt
        attributes.append({
            "name": sp.get("outputName") or sp.get("name"),
            "caption": sp.get("description", ""),
            "dataType": resolved_dt,
            "dataTypeCategory": sp.get("dataTypeCategory", 0),
            "type": "LIST" if str(sp.get("type", "")).upper() == "ARRAY" else "OBJECT",
            "description": "",
        })
    event_data_list = {
        "appId": app_id, "name": event_name, "caption": caption,
        "source": "MICRO_FLOW_MESSAGE", "sourceId": entity_id,
        "attributes": attributes,
    }
    return {
        "appId": app_id, "caption": caption, "name": event_name,
        "source": "MICRO_FLOW", "sourceId": entity_id,
        "eventDataType": "OBJECT", "description": description,
        "eventDataList": [event_data_list], "messageType": message_type,
    }


def build_refer_config_body(app_id: int, entity_id: int, caption: str,
                            refer_type: str, terminals: dict[str, Any],
                            group_id: Any = None) -> dict[str, Any]:
    """参照配置提交 body —— 组件 53993 e1() 逐字（module-53993.js:614-667）。

    顶层：{appId, entityId, caption, type, id, referConfigDetail[]}
      id = 参照组 id（新建 null）；有 id → planner 路由到 UpdateConfigInfo，否则 Create。

    referConfigDetail：多终端时 [PC detail, MOBILE detail]，否则按 er 命中单终端。

    terminals 入参形态（PC/MOBILE 各自一份）：
      {
        "PC":     {"config": {...}, "display_name": [...], "id": None, "pull_display_name": [...]},
        "MOBILE": {"config": {...}, "display_name": [...], "id": None},
      }
    - config：终端配置对象（List 默认 {columns,orders,whereCond,entities}；TreeList 加
      onlyLastLevel；LeftTreeRightList 加 treeConfig/treeWhereCond/treeColumns）——
      e1 里 configInfo = JSON.stringify(config)，本构造器照做。
    - display_name：显示字段对象数组（[{path,uuid}] 形态），JSON.stringify 后入 displayName。
    - pull_display_name：仅 PC detail 有此键（eA 下拉显示字段），空则 ""。
    - id：该终端参照配置记录 id（有则 actionType=UPDATE）。

    refer_type 字面值（module-75586）："List" | "TreeList" | "LeftTreeRightList"。
    """
    if refer_type not in ("List", "TreeList", "LeftTreeRightList"):
        raise ValueError(
            "refer_type 必须是 List / TreeList / LeftTreeRightList 之一，收到 %r。"
            "（module-75586 F/Sv 字面量）。"
            "注意：ENTITY / BASIC_DATA 是 ReferConfigSourceTypeEnum 的值，"
            "那是 sourceType 字段，不是这里的 type。" % (refer_type,))
    unknowns: list[str] = []

    def _detail(spec: dict[str, Any], terminal_type: str, include_pull: bool) -> dict[str, Any]:
        cfg = spec.get("config") or {}
        d = {
            "appId": app_id,
            "entityId": entity_id,
            "configInfo": json.dumps(cfg, ensure_ascii=False),
            "caption": caption,
            "type": refer_type,
            "displayName": json.dumps(spec.get("display_name") or [], ensure_ascii=False),
            "terminalType": terminal_type,
            "id": spec.get("id") or None,
            "actionType": "UPDATE" if spec.get("id") else "INSERT",
        }
        if include_pull:  # 仅 PC detail（module-53993.js:635）
            pull = spec.get("pull_display_name") or []
            d["pullDisplayName"] = json.dumps(pull, ensure_ascii=False) if pull else ""
        return d

    detail: list[dict[str, Any]] = []
    has_pc, has_mobile = "PC" in terminals, "MOBILE" in terminals
    if has_pc and has_mobile:
        detail = [_detail(terminals["PC"], "PC", True),
                  _detail(terminals["MOBILE"], "MOBILE", False)]
    elif has_pc:
        detail = [_detail(terminals["PC"], "PC", True)]
    elif has_mobile:
        detail = [_detail(terminals["MOBILE"], "MOBILE", False)]
    else:
        unknowns.append("terminals 未含 PC/MOBILE，referConfigDetail 为空（参照提交必拒）")

    body: dict[str, Any] = {
        "appId": app_id, "entityId": entity_id, "caption": caption,
        "type": refer_type, "id": group_id if group_id else None,
        "referConfigDetail": detail,
    }
    # ★ unknowns 不进 body —— 平台 DTO（ReferConfigInfoDto）没有这个字段。
    #   以前直接塞进 body 一起发出去，等于往平台灌垃圾键。
    return body


def build_filter_plan_body(app_name: str, app_id: int, page_id: int,
                           grid_suffix: str, driven_entity: str, caption: str,
                           conditions: list[dict[str, Any]],
                           plan_type: int = 2, order_no: int = 1000) -> dict[str, Any]:
    """页面过滤方案 body（udc-bi jar FilterPlanController，网关须双 udc 前缀）。

    **证据分层（两套通道，勿互套）**：
    - 本构造器 = **LIVE 探针坐实**的 REST 写面：`POST /service/udc/udc-runtime/filter-plan/create-new`，
      写面收**数字码** planType（0=FILTER 隐藏 / 2=LIST 可见），响应回读为枚举名（0→"FILTER"/2→"LIST"），
      DB plan_type 存数字码（0 自建/2 平台默认）。写面/读面/DB 三层形态不同（skill §33）。
    - 设计器前端另走 GraphQL `udcUdcRuntimeFilterPlanPost`（bundle module 51796，planType 字符串），
      是**设计态 UI 调用链**，与上述 LIVE REST 面并存，勿互相覆盖。

    planType=2（LIST）列表页可见（平台「列表默认方案」形态）；
    planType=0（FILTER）列表页**隐藏**——用户「页面规则没建立」观感的根因，
    显式传 0 时进 unknowns 警示。
    sourceId = `<page_id>_udcDataGridView_<grid_suffix>`（必须用目标列表页真实
    page id + grid 控件后缀，拼错同样不可见）。
    content 是 JSON 字符串（cond 树），宿主补属性真实 id。
    """
    unknowns: list[str] = []
    cond_tree: list[dict[str, Any]] = [{
        "type": "GROUP", "uuid": "<uuid>",
        "conditions": [
            {
                "type": "CONDITION",
                "leftParam": {"id": c.get("attribute_id", "<attribute_id>"),
                              "entityId": "<entity_id>", "entityAppName": app_name},
                "operator": {"value": c.get("operator", "EQ"),
                              "desc": {"EQ": "=", "LT": "<", "GT": ">",
                                       "CONTAINS": "包含"}.get(c.get("operator", "EQ"), c.get("operator", "EQ"))},
                "rightParams": [{"type": "CONSTANT",
                                  "value": c.get("value"),
                                  "desc": str(c.get("value"))}],
                "uuid": "<uuid>", "logicalOperator": "AND",
            }
            for c in conditions
        ],
    }]
    body = {
        "appName": app_name, "drivenEntity": driven_entity, "caption": caption,
        "sourceId": f"{page_id}_udcDataGridView_{grid_suffix}",
        "pageId": page_id, "pageUrl": "<pageUrl>", "pageUrlType": 1,
        "planType": plan_type, "isDefault": False, "appId": app_id,
        "sourceType": 0, "orderNo": order_no,
        "content": json.dumps(
            {"caption": caption, "entities": ["<entity_id>"], "cond": cond_tree,
             "sortSetting": [], "isDefault": False, "orderNo": order_no},
            ensure_ascii=False),
    }
    if plan_type == 0:
        unknowns.append(
            "planType=0（FILTER）列表页方案区不可见（LIVE 对照：0=FILTER 隐藏 / 2=LIST 可见）；"
            "若需求是列表页可见的页面规则，用 planType=2")
    return _plan(body, unknowns=unknowns,
                 note="LIVE 探针 REST 写面：POST /service/udc/udc-runtime/filter-plan/create-new"
                      "（须双 udc 前缀；单拼 /service/udc-runtime/... 报「服务不存在」）；"
                      "planType 数字码 0/2（响应回读 FILTER/LIST）；content 属性 id 占位需宿主替换真实值；"
                      "设计器前端另走 GraphQL udcUdcRuntimeFilterPlanPost（bundle 51796），两者并存不互换")
