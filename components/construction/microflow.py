"""MicroFlow 构造骨架 — 模板填充 + create/checkSchema body 组装（宿主执行）。

证据基线（skill seeyon-udc-design-time-build，metadata-artifact-apis.md L71-73）：
- 新建微流程走 REST ``POST /service/udc/microflow/create``（字符串枚举
  triggerType=BUSINESS_EVENT|MANUAL|SCHEDULE、type=SERVICE、state=DRAFT），
  与 GraphQL ``udcMicroflowUpdatePost``（数字枚举）是两套契约，别互套。
- create 前必过 ``POST /service/udc/microflow/checkSchema``（同 body）：
  ``content.check=true, errors=0`` 才创建；失败样例带 nodeId/path/errorCode=DATA_INVALID。
- ``dataSchema`` 是 JSON **字符串**非嵌套对象。
- 节点富结构（RETRIEVE condition / CHANGE_ENTITY attrType ~18 键）离线不可证 →
  构造器只做「模板深拷贝 + 占位符替换」，模板来自标品既有微流程 data_schema
  或 udc_microflow_preset_template，宿主填真实 ID/文案。零缺失零多余键铁律：
  多一个键 / 少一个键都可能让 checkSchema 静默不过。
"""
from __future__ import annotations

import json
import re
from typing import Any

SCHEMA_ID = "udc.construction.microflow.v1"

# create body 键位字典（skill metadata-artifact-apis L71，逐字照录，勿增删）
CREATE_BODY_KEYS: frozenset[str] = frozenset({
    "name", "caption", "appId", "triggerType", "type", "creationMethod",
    "groupType", "businessEventCaption", "scheduleCaption", "microFlowGroupId",
    "orderNum", "sourceId", "versionCode", "state", "serviceInterface",
    "openApi", "restApi", "restPath", "dataSchema",
})

# create REST 的 triggerType 字符串枚举值域（证据 skill L71；非 DB 数字枚举）
TRIGGER_TYPE_VALUES: tuple[str, ...] = ("BUSINESS_EVENT", "MANUAL", "SCHEDULE")

_PLACEHOLDER = re.compile(r"\$\{([A-Za-z0-9_.]+)\}")


def _fill_walk(o: Any, replacements: dict[str, Any], unresolved: set[str]) -> Any:
    """递归替换所有 ${key} 占位符；未提供的 key 保留原样并记入 unresolved。"""
    if isinstance(o, dict):
        return {k: _fill_walk(v, replacements, unresolved) for k, v in o.items()}
    if isinstance(o, list):
        return [_fill_walk(v, replacements, unresolved) for v in o]
    if isinstance(o, str):
        def _sub(m: re.Match) -> str:
            key = m.group(1)
            if key in replacements:
                return str(replacements[key])
            unresolved.add(m.group(0))
            return m.group(0)
        return _PLACEHOLDER.sub(_sub, o)
    return o


def fill_schema_template(template: Any, replacements: dict[str, Any]) -> tuple[Any, list[str]]:
    """深拷贝 template 并把所有 ${key} 占位符按 replacements 替换。

    返回 (filled, unresolved)：unresolved 是仍残留的占位符字面（sorted），
    宿主必须补齐这些键才提交——残留保持原样，不静默吞掉。
    填充前后键位集合不变（零缺失零多余，skill 铁律）。
    """
    unresolved: set[str] = set()
    filled = _fill_walk(template, dict(replacements), unresolved)
    return filled, sorted(unresolved)


def _local_schema_errors(data_schema: Any) -> list[str]:
    """在构造期跑本地语义校验，返回错误列表（空=通过）。

    覆盖两类「平台不拦、生成期炸 / 运行期错」的配置：
      1. MESSAGE 监听分支要求根 input 完整（microflow_model._validate_message_trigger_root_input）
         —— 否则 BusinessEventListener.java.ftl:117 抛 InvalidReferenceException
      2. CALL_APP_SERVICE 节点的调用配置必须可定位唯一服务（microflow_constraints.
         validate_call_app_service）—— 该类节点在 NODE_REQUIRED_FIELDS 里是空元组

    用 parse_data_schema 的返回值而非抛异常：构造器是纯函数，既有调用方依赖它
    总是返回 body；错误通过 unknowns 通道暴露，由调用方决定是否提交。
    """
    if not isinstance(data_schema, (dict, str)):
        return []
    try:
        from components.udc.microflow_model import parse_data_schema
        graph = parse_data_schema(data_schema)
        errs = list(getattr(graph, "errors", []) or [])
    except Exception as exc:  # 解析器自身异常不静默：写进 unknowns 而不是吞掉
        return [f"本地 schema 解析失败: {exc!r}"]

    # 逐节点跑类型级校验（parse_data_schema 只做通用键校验）
    if isinstance(data_schema, str):
        try:
            data_schema = json.loads(data_schema)
        except json.JSONDecodeError:
            return errs
    if isinstance(data_schema, dict):
        try:
            from components.udc.microflow_constraints import validate_node_fields
        except ImportError:
            return [*errs, "UNVERIFIED: microflow node validation unavailable"]
        for raw in data_schema.get("nodes") or []:
            if not isinstance(raw, dict):
                continue
            at = raw.get("actionType")
            if not at:
                continue
            try:
                errs.extend(validate_node_fields(str(at), raw))
            except Exception as exc:
                errs.append(f"节点 {raw.get('nodeId')} 类型级校验失败: {exc!r}")
    return errs


def build_microflow_create_body(*, name: str, caption: str, app_id: int,
                                data_schema: Any, trigger_type: str = "MANUAL",
                                mf_type: str = "SERVICE",
                                creation_method: str = "MANUAL",
                                group_type: str = "DEFAULT",
                                state: str = "DRAFT",
                                service_interface: str = "CustomMicroFlowAppService",
                                order_num: int = 0, source_id: str = "",
                                micro_flow_group_id: str = "", version_code: int = 100,
                                open_api: str = "STOP", rest_api: str = "DISABLED",
                                rest_path: str = "",
                                business_event_caption: str = "-",
                                schedule_caption: str = "-") -> dict[str, Any]:
    """组装 create / checkSchema body（键位照 skill L71，缺键报错码不同）。

    data_schema 入参是 Python 对象，函数内 json.dumps 成字符串（create 只认字符串）。
    非法 trigger_type 进 unknowns，不臆造合法值。
    """
    unknowns: list[str] = []
    if trigger_type not in TRIGGER_TYPE_VALUES:
        unknowns.append(
            f"triggerType={trigger_type!r} 不在 create REST 字符串枚举值域 {TRIGGER_TYPE_VALUES}"
            f"（证据 skill L71；非法值进 unknowns 不臆造）")
    # 本地语义校验：平台 checkSchema 是浅校验（microflow-rest-write-chain.md §4），
    # 下列配置在平台侧静默通过、只在生成期炸或运行期错，必须在构造期就暴露。
    unknowns.extend(_local_schema_errors(data_schema))
    try:
        from components.udc.microflow.capability_registry import advisory
        advisory_schema = json.loads(data_schema) if isinstance(data_schema, str) else data_schema
        if isinstance(advisory_schema, dict):
            unknowns.extend(advisory(advisory_schema))
    except Exception:
        unknowns.append("UNVERIFIED: capability advisory unavailable")
    body: dict[str, Any] = {
        "name": name,
        "caption": caption,
        "appId": app_id,
        "triggerType": trigger_type,
        "type": mf_type,
        "creationMethod": creation_method,
        "groupType": group_type,
        "businessEventCaption": business_event_caption,
        "scheduleCaption": schedule_caption,
        "microFlowGroupId": micro_flow_group_id,
        "orderNum": order_num,
        "sourceId": source_id,
        "versionCode": version_code,
        "state": state,
        "serviceInterface": service_interface,
        "openApi": open_api,
        "restApi": rest_api,
        "restPath": rest_path,
        "dataSchema": json.dumps(data_schema, ensure_ascii=False),
    }
    if unknowns:
        body["unknowns"] = unknowns
    return body


def check_schema_body(create_body: dict[str, Any]) -> dict[str, Any]:
    """checkSchema 与 create 同 body（skill：同 body POST checkSchema → check 才 create）。

    校验类键（unknowns）不入 check 请求，返回剔除后的副本。
    """
    return {k: v for k, v in create_body.items() if k != "unknowns"}


__all__ = [
    "SCHEMA_ID", "CREATE_BODY_KEYS", "TRIGGER_TYPE_VALUES",
    "fill_schema_template", "build_microflow_create_body", "check_schema_body",
]
