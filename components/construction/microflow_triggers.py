"""微流程 trigger 构造（3 种触发方式，权威结构来自 CDP 抓包 2026-10-26）。

- 服务定义 MANUAL：paramType(NONE/BASIC/ENTITY_OBJECT/DEFAULT_OBJECT) + output(入参)
- 事件监听 BUSINESS_EVENT：messageInfo(事件数据) + output(事件数据出参)
- 定时任务 SCHEDULE：scheduleCronRule(jobCode/jobCaption/cronRules)

参考事实：core/facts/udc/microflow/{trigger-and-type-mapping,event-listener-structure,schedule-structure}.md
"""
from __future__ import annotations
import random
import string
import time
from typing import Any

EVENT_FULL_NAME_PREFIX = "com.seeyon.udc.common.event."

# 注意：appId / appName 是运行时上下文，必须由调用方显式传入（见 make_create_body /
# make_update_body 的 app_id 参数），不得在此写死客户 appId/实体名。

# dataType → javaType 权威映射（DataTransferObjectUtil.getDataTypeFromCtpMetadata 反推）
_JAVA_TYPE = {
    "STRING": "java.lang.String",
    "INTEGER": "java.lang.Integer",
    "BIGINTEGER": "java.lang.Long",
    "BOOLEAN": "java.lang.Boolean",
    "DATETIME": "java.util.Date",
    "DATE": "java.util.Date",
    "DECIMAL": "java.math.BigDecimal",
    "DOUBLE": "java.lang.Double",
}


def _rid(n: int) -> str:
    """随机码（对齐前端 nanoid 字符集）。"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


# ───────────────────────── 服务定义（MANUAL）─────────────────────────

def manual_trigger(*, node_id: str, param_type: str, output: dict | None,
                   caption: str = "开始", basic: str | None = None,
                   default_object: dict | None = None, entity_object: dict | None = None,
                   desc: str = "") -> dict[str, Any]:
    """服务定义 trigger。param_type ∈ NONE/BASIC/ENTITY_OBJECT/DEFAULT_OBJECT。"""
    t: dict[str, Any] = {
        "id": "",
        "nodeId": node_id,
        "caption": caption,
        "description": "",
        "type": "MANUAL",
        "input": None,
        "output": output,
        "paramType": param_type,
        "hasPagination": False,
        "isArray": False,
        "desc": desc,
    }
    if param_type == "BASIC" and basic:
        t["basic"] = basic
    elif param_type == "DEFAULT_OBJECT" and default_object:
        t["defaultObject"] = default_object
        t["app"] = default_object.get("app")
    elif param_type == "ENTITY_OBJECT" and entity_object:
        t["entityObject"] = entity_object
    return t


def basic_param(name: str, data_type: str, desc: str, is_array: bool = False) -> dict[str, Any]:
    """基本类型入参（BASIC）。

    ★ 真实样本（MANUAL+BASIC 全量）：name 恒为 _FLOW_INPUT_xxxxxx（随机 6 位），
      desc 才是业务名。调用方传的 name 参数只作 desc 语义参考，真正的引用名
      必须生成 _FLOW_INPUT_* 形态，否则引用它的 SelectParam 前端不认。
    """
    import random
    import string as _s
    suffix = "".join(random.choices(_s.ascii_letters + _s.digits, k=6))
    return {
        "id": None, "javaType": _JAVA_TYPE.get(data_type, "java.lang.String"),
        "dataType": data_type, "type": "OBJECT", "desc": desc,
        "dtoType": None, "udcApp": None, "hasPagination": None,
        "name": "_FLOW_INPUT_" + suffix,
    }


def make_end_basic(name: str, data_type: str, desc: str) -> dict[str, Any]:
    """结束节点出参（BASIC）。★ 真实样本 name 恒为 _FLOW_OUTPUT_xxxxxx。"""
    import random
    import string as _s
    suffix = "".join(random.choices(_s.ascii_letters + _s.digits, k=6))
    return {
        "id": None, "javaType": _JAVA_TYPE.get(data_type, "java.lang.String"),
        "dataType": data_type, "type": "OBJECT", "desc": desc,
        "dtoType": None, "udcApp": None, "hasPagination": None,
        "name": "_FLOW_OUTPUT_" + suffix,
    }


# ───────────────────────── 事件监听（BUSINESS_EVENT）─────────────────────────

def event_trigger(*, node_id: str, event: dict[str, Any], out_param_name: str = "事件数据") -> dict[str, Any]:
    """事件监听 trigger。event 来自 udcMicroflowFilterEventPost 列表项。

    该接口直接返回 eventClassName(=eventFullName 事件类全名)、
    eventDataFullName(=实体 DTO 全名)、eventMfCustomDtoName(=DTO未首大写名.事件类全名)、
    name(事件名)、sourceId(来源实体id)、caption，无需自行推导。
    字段映射见 event-listener-structure.md。
    """
    event_name = event["name"]
    event_mf_custom = event["eventMfCustomDtoName"]
    dto_full = event["eventDataFullName"]
    out_name = "_BUSINESS_EVENT_" + _rid(6)
    app_name = event.get("appName")

    output = {
        "id": event_mf_custom,
        "name": out_name,
        "javaType": event_mf_custom,
        "dataType": "DTO", "type": "OBJECT",
        "desc": out_param_name,
        "appName": app_name,
        "dtoType": "",
    }
    return {
        "nodeId": node_id,
        "name": None,
        "caption": "事件监听",
        "title": out_param_name,
        "description": None,
        "type": "BUSINESS_EVENT",
        "input": None,
        "output": output,
        "messageInfo": {
            "caption": event["caption"],
            "messageSource": "EVENT",
            "eventFullName": event["eventClassName"],
            "eventDataFullName": dto_full,
            "eventMfCustomDtoName": event_mf_custom,
            "eventName": event_name,
            "currentId": event_name,
            "currentType": str(event.get("sourceId") or ""),
            "output": {
                "id": dto_full,
                "dataType": "DTO", "type": "OBJECT",
                "javaType": event_mf_custom,
                "appName": app_name,
            },
        },
        # ★ 缺这个设计器里「事件监听」节点是红的（未完成态）。61/61 真实事件触发都有。
        "isCompleted": True,
    }


def mq_trigger(*, node_id: str, mq: dict[str, Any], app_name: str, app_caption: str, out_param_name: str = "消息数据") -> dict[str, Any]:
    """应用间事件监听 trigger（MESSAGE 源）。mq 来自 udcMicroflowFilterMqPost 列表项。

    ★ BusinessEventTrigger.parse 反编译契约（MESSAGE 源）：
    必填 messageSource/eventDataFullName/caption/topic；eventName 缺省时由
    eventDataFullName 最后一段 lowerFirst 推导。currentType=appName（来源应用）。
    """
    full_name = mq["fullName"]
    topic = mq.get("topic") or ""
    out_name = "_BUSINESS_MESSAGE_" + _rid(6)
    return {
        "nodeId": node_id,
        "name": None,
        "caption": "事件监听",
        "title": out_param_name,
        "description": None,
        "type": "BUSINESS_EVENT",
        "input": None,
        "output": {
            "id": full_name,
            "name": out_name,
            "javaType": full_name,
            "dataType": "DTO", "type": "OBJECT",
            "desc": out_param_name,
            "appName": app_name,
            "dtoType": "",
        },
        "messageInfo": {
            "caption": mq["caption"],
            "messageSource": "MESSAGE",
            "eventFullName": None,
            "eventDataFullName": full_name,
            "eventMfCustomDtoName": None,
            "eventName": None,
            "topic": topic,
            "currentId": full_name,
            "currentType": app_name,
            "output": {
                "id": full_name,
                "dataType": "DTO", "type": "OBJECT",
                "javaType": full_name,
                "appName": app_name,
            },
        },
    }


def mf_event_trigger(*, node_id: str, event: dict[str, Any], out_param_name: str = "事件数据") -> dict[str, Any]:
    """应用内微流程事件监听 trigger（MICRO_FLOW_EVENT 源）。

    ★ BusinessEventTrigger.parse 反编译契约（MICRO_FLOW_EVENT 源）：
    必填 messageSource/eventDataFullName/caption/eventMfCustomDtoName；
    eventFullName 不需要（微流程事件没有固定事件类）。
    """
    dto_full = event["eventDataFullName"]
    mf_custom = event["eventMfCustomDtoName"]
    out_name = "_BUSINESS_EVENT_" + _rid(6)
    app_name = event.get("appName")
    return {
        "nodeId": node_id,
        "name": None,
        "caption": "事件监听",
        "title": out_param_name,
        "description": None,
        "type": "BUSINESS_EVENT",
        "input": None,
        "output": {
            "id": mf_custom,
            "name": out_name,
            "javaType": mf_custom,
            "dataType": "DTO", "type": "OBJECT",
            "desc": out_param_name,
            "appName": app_name,
            "dtoType": "",
        },
        "messageInfo": {
            "caption": event["caption"],
            "messageSource": "MICRO_FLOW_EVENT",
            "eventFullName": None,
            "eventDataFullName": dto_full,
            "eventMfCustomDtoName": mf_custom,
            "eventName": event.get("name"),
            "currentId": event.get("name"),
            "currentType": str(event.get("sourceId") or "0"),
            "output": {
                "id": dto_full,
                "dataType": "DTO", "type": "OBJECT",
                "javaType": mf_custom,
                "appName": app_name,
            },
        },
    }


# ───────────────────────── 定时任务（SCHEDULE）─────────────────────────

def schedule_trigger(*, node_id: str, job_caption: str, cycle_type: str = "SIMPLE",
                     rotation_type: str = "MINUTE", value: str = "5",
                     day_of_week: int = 1) -> dict[str, Any]:
    """定时任务 trigger。

    - cycle_type=SIMPLE：固定周期轮换，rotation_type ∈ MINUTE/HOUR/DAY/WEEK/MONTH，
      value=间隔数。★ MINUTE 最小 5（平台约束，低于 5 分钟非法）。
    - cycle_type=CRON：rotation_type 置 None，value=cron 表达式。
    """
    start_time = str(int(time.time() * 1000))
    cron_rule: dict[str, Any] = {
        "cycleType": cycle_type,
        "startTime": start_time,
        "endTime": None,
        "rotationType": rotation_type,
        "type": "FIRST",
        "value": value,
    }
    if cycle_type == "SIMPLE" and rotation_type == "WEEK":
        cron_rule["dayOfWeek"] = day_of_week
    return {
        "nodeId": node_id,
        "name": None,
        "caption": "定时任务",
        "description": None,
        "type": "SCHEDULE",
        "input": None,
        "output": None,
        "scheduleCronRule": {
            "jobCode": _rid(16),
            "jobCaption": job_caption,
            "cronRules": [cron_rule],
        },
        "isCompleted": True,
    }


# ───────────────────────── dataSchema 顶层 ─────────────────────────

def make_data_schema(*, name: str, caption: str, mf_type: str, trigger_type: str,
                     trigger: dict[str, Any], nodes: list, end_output: dict | None = None,
                     input_param: dict | None = None, description: str = "") -> dict[str, Any]:
    """dataSchema 完整结构（update 时用）。"""
    schema: dict[str, Any] = {
        "endNode": {
            "id": "", "name": "", "type": "END", "actionType": "END_NODE",
            "nodeId": "MFEndNode", "caption": "结束", "description": "",
            "input": None, "output": end_output,
        },
        "sourceType": "PAGE",
        "trigger": trigger,
    }
    if input_param is not None:
        schema["input"] = input_param
    if nodes:
        schema["title"] = caption
        schema["isCompleted"] = True
        schema["nodes"] = nodes
    else:
        schema["nodes"] = []
    return schema


def make_create_body(*, app_id: str, name: str, caption: str, mf_type: str, trigger_type: str,
                     trigger: dict[str, Any], order_num: int, group_id: str = "0",
                     description: str = "") -> dict[str, Any]:
    """create 请求 body（初始骨架）。app_id 由调用方从运行时上下文传入。"""
    schema = {
        "id": "", "appId": app_id, "sourceId": "", "version": "0", "versionCode": 0,
        "name": name, "caption": caption, "description": description,
        "type": mf_type, "triggerType": trigger_type,
        "entityId": "", "eventId": "",
        "input": None, "output": None,
        "trigger": trigger,
        "nodes": [], "sourceType": "PAGE",
    }
    return {
        "appId": app_id, "caption": caption, "description": description,
        "dataSchema": __import__("json").dumps(schema, ensure_ascii=False),
        "name": name, "sourceId": "", "orderNum": order_num,
        "type": mf_type, "triggerType": trigger_type,
        "versionCode": 100, "groupType": "DEFAULT", "state": "DRAFT",
        "microFlowGroupId": group_id,
    }


def make_update_body(*, app_id: str, mid: str, guid: str, name: str, caption: str, mf_type: str,
                     trigger_type: str, data_schema: dict[str, Any], group_id: str = "0",
                     service_interface: str = "CustomMicroFlowAppService",
                     description: str = "") -> dict[str, Any]:
    """update 请求 body（完整结构）。app_id 由调用方从运行时上下文传入。"""
    import json as _json
    return {
        "appId": app_id, "businessEventCaption": "-", "caption": caption,
        "description": description, "guid": guid, "id": mid, "name": name,
        "publishState": "UNPUBLISH", "scheduleCaption": "-", "sourceId": "",
        "type": mf_type, "state": "RELEASE", "triggerType": trigger_type,
        "groupType": "DEFAULT", "versionCode": 100, "creationMethod": "MANUAL",
        "serviceInterface": service_interface, "openApi": "STOP",
        "microFlowGroupId": group_id, "restApi": "DISABLED", "restPath": "",
        "lastVersionMetadataState": "DISABLED", "lastEnableTime": None,
        "lastEnableVersion": None, "sourceType": "PAGE",
        "dataSchema": _json.dumps(data_schema, ensure_ascii=False),
    }
