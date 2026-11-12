"""RED: 公开构造入口必须复用本地校验器，而不是造完直接返回。

问题：`components/udc/microflow_model._validate_message_trigger_root_input` 已能拦住
"MESSAGE + 根 input 缺失"，`validate_call_app_service` 已能拦住"调用配置不可定位服务"，
但公开入口 `build_microflow_create_body` 只校验 triggerType 枚举，**从未调用这两者**。
于是通过 bootstrap['microflow_create_body'] 造出的 body 仍然带着必炸的配置，
调用者（宿主/脚本）拿到的是一个看起来合法、实际必炸的请求体。

为什么这是硬缺口而不是美观问题：
  平台 checkSchema 实测为浅校验（microflow-write-chain §4），不会拦；
  一旦提交并在页面上点构建，就复现 12:24:33 那次 FreeMarker 失败。

设计取舍：构造器已有 `unknowns` 这个既有信号通道（triggerType 非法即写进去），
保持同一语义——本地校验不过就写进 unknowns，由调用方决定是否提交，
而不是直接抛异常（构造器是纯函数，抛异常会破坏既有调用方）。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from components.construction.microflow import build_microflow_create_body, check_schema_body

BPM_EVENT = "com.seeyon.bpm.dto.message.event.BpmStartEvent"


def _schema(root_input):
    return {
        "input": root_input,
        "output": {"name": "_FLOW_OUTPUT_x"},
        "endNode": {"type": "END", "actionType": "END_NODE", "nodeId": "MFEndNode"},
        "sourceType": "PAGE",
        "trigger": {
            "nodeId": "MFStartNode", "type": "BUSINESS_EVENT",
            "messageInfo": {"messageSource": "MESSAGE", "caption": "c",
                            "eventDataFullName": BPM_EVENT, "topic": "BPM"},
            "output": {"id": 1, "dataType": "OBJECT", "type": "OBJECT",
                       "javaType": BPM_EVENT, "appName": "bpm"},
        },
        "nodes": [],
    }


def test_public_builder_flags_message_null_input():
    """公开构造入口遇 MESSAGE + 根 input=null 必须写入 unknowns。"""
    body = build_microflow_create_body(
        name="t", caption="t", app_id=1, trigger_type="BUSINESS_EVENT",
        data_schema=_schema(None))
    unknowns = body.get("unknowns") or []
    assert unknowns, f"必须把本地校验错误写进 unknowns，实际无: {body.get('unknowns')}"
    joined = " ".join(unknowns)
    assert "input" in joined.lower(), f"unknowns 须点名 input: {unknowns}"


def test_public_builder_passes_valid_message_schema():
    """回归护栏：MESSAGE + 完整 input 不得产生 input 相关 unknowns。"""
    ok = {"name": "_FLOW_INPUT_a", "javaType": BPM_EVENT,
          "dataType": "OBJECT", "type": "OBJECT"}
    body = build_microflow_create_body(
        name="t", caption="t", app_id=1, trigger_type="BUSINESS_EVENT",
        data_schema=_schema(ok))
    unknowns = body.get("unknowns") or []
    assert not [u for u in unknowns if "input" in u.lower()], unknowns


def test_public_builder_flags_invalid_call_app_service_node():
    """公开构造入口遇不可定位服务的 CALL_APP_SERVICE 节点必须写入 unknowns。

    这类节点在 NODE_REQUIRED_FIELDS 里是空元组，原本完全不校验；
    平台也不拦，只在运行期失败——所以必须在构造期暴露。
    """
    schema = _schema({"name": "_FLOW_INPUT_a", "javaType": BPM_EVENT,
                      "dataType": "OBJECT", "type": "OBJECT"})
    schema["nodes"] = [{
        "actionType": "CALL_APP_SERVICE",
        "nodeId": "CALL_APP_SERVICE_x1",
        "type": "ACTIVITY",
        "caption": "调服务",
        "mappingType": "rows",           # 错：应 attrs
        "selectMethod": {},              # 错：缺 selectMethod 内容
    }]
    body = build_microflow_create_body(
        name="t", caption="t", app_id=1, trigger_type="BUSINESS_EVENT",
        data_schema=schema)
    unknowns = body.get("unknowns") or []
    assert unknowns, "非法 CALL_APP_SERVICE 节点必须写入 unknowns"
    joined = " ".join(unknowns)
    assert "CALL_APP_SERVICE" in joined, f"unknowns 须点名节点类型: {unknowns}"


def test_check_schema_body_keeps_unknowns_visible_to_caller():
    """check_schema_body 会把 unknowns 剔除（原本设计），但调用方必须能先读到它。

    这里只锁定契约：build 返回的 body 里 unknowns 可读，
    且 check_schema_body 后不再带 unknowns（避免把它发到平台）。
    """
    body = build_microflow_create_body(
        name="t", caption="t", app_id=1, trigger_type="BUSINESS_EVENT",
        data_schema=_schema(None))
    assert body.get("unknowns"), "build 结果必须暴露 unknowns"
    assert "unknowns" not in check_schema_body(body), "checkSchema 请求体不得携带 unknowns"
