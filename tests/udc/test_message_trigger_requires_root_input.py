"""RED: MESSAGE 监听分支要求微流程根 input 非空，本地模型必须拦住。

线上事实（2026-10-20 12:24:33 真实发布失败，用户提供原文）：
  freemarker.core.InvalidReferenceException
  microFlowBo.input 缺失
  autocode/JAVA/2.9/templates/microflow/event/BusinessEventListener.java.ftl:117

模板机理（本机 cfr-r30 反编译副本已核实 L115-L119）：
  docs/audit/artifacts/decompiled/cfr-r30/biz/autocode/JAVA/2.9/templates/microflow/event/BusinessEventListener.java.ftl
  <#elseif messageSource == "MESSAGE">
    <#assign subscribeType = subscribedMessageDto?then("...MessageDto", microFlowBo.input.javaType)>
    public void on${microFlowBo.input.name?cap_first}(${subscribeType} ${paramName})

?then 是惰性求值：
  subscribedMessageDto=true  → 只取字面量，不碰 input，L117 不炸，走到 L119 才炸 input.name
  subscribedMessageDto=false → 求值 input.javaType，input 为 null 立即炸在 117:109

→ 两种分支最终都要求根 input 存在。**MESSAGE 监听的微流程根 input 不得为 null。**

当前缺口（本轮实测）：components/udc/microflow_model.parse_data_schema 与
microflow_constraints 都不检查根 input，含 input=null 的 schema 返回 errors=[],
warnings=[] 静默通过。本地模型因此不能阻止这类必然炸在生成期的配置。

铁律：这是「生成前置校验」，必须在本地模型做——平台 checkSchema 已实测为浅校验
（microflow-rest-write-chain.md §4：4 类非法值全部 check:true），不能兜底。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.microflow_model import parse_data_schema

BPM_EVENT = "com.seeyon.bpm.dto.message.event.BpmStartEvent"


def _schema(message_source, root_input, trigger_output=None):
    """最小可解析 schema；只改 messageSource 与根 input 做对照。"""
    return {
        "input": root_input,
        "output": {"name": "_FLOW_OUTPUT_x"},
        "endNode": {"type": "END", "actionType": "END_NODE", "nodeId": "MFEndNode"},
        "sourceType": "PAGE",
        "trigger": {
            "nodeId": "MFStartNode",
            "type": "BUSINESS_EVENT",
            "messageInfo": {"messageSource": message_source,
                            "caption": "c", "eventDataFullName": BPM_EVENT,
                            "topic": "BPM"},
            "output": trigger_output or {
                "id": 1, "dataType": "OBJECT", "type": "OBJECT",
                "javaType": BPM_EVENT, "appName": "bpm"},
        },
        "nodes": [],
    }


def _errors(schema):
    g = parse_data_schema(json.dumps(schema))
    return list(getattr(g, "errors", []) or [])


def test_message_trigger_with_null_root_input_must_be_error():
    """MESSAGE 监听 + 根 input=null ⇒ 必须报硬错（不是 warning、不是静默通过）。"""
    errs = _errors(_schema("MESSAGE", None))
    assert errs, "MESSAGE 监听且根 input=null 必须报错（该组合必炸 BusinessEventListener.java.ftl:117）"
    joined = " ".join(errs)
    assert "input" in joined.lower(), f"错误信息须点名 input: {errs}"
    assert "MESSAGE" in joined, f"错误信息须点名触发源 MESSAGE: {errs}"


def test_message_trigger_with_input_missing_java_type_must_be_error():
    """MESSAGE 监听 + input 存在但缺 javaType ⇒ 同样必须报错。

    这是输入非空但取不到 javaType 的第二种形态：subscribedMessageDto=false 时
    同样炸在 117:109。只查「input 是否存在」会漏掉这一种。
    """
    errs = _errors(_schema("MESSAGE", {"name": "_FLOW_INPUT_a", "dataType": "OBJECT"}))
    assert errs, "MESSAGE 监听且 input 缺 javaType 必须报错"
    assert any("javaType" in e for e in errs), f"错误须点名 javaType: {errs}"


def test_message_trigger_with_complete_input_passes():
    """回归护栏：MESSAGE + 完整 input（含 javaType/name）不得报此错。"""
    ok_input = {"name": "_FLOW_INPUT_a", "javaType": BPM_EVENT,
                "dataType": "OBJECT", "type": "OBJECT"}
    errs = _errors(_schema("MESSAGE", ok_input))
    assert not [e for e in errs if "input" in e.lower()], f"完整 input 不应报 input 错: {errs}"


def test_event_trigger_with_null_input_is_not_this_rule():
    """范围护栏：EVENT（应用内实体事件）走另一个模板分支，不用 input.name/javaType，
    不得被本条 MESSAGE 规则误伤。"""
    errs = _errors(_schema("EVENT", None))
    assert not [e for e in errs if "MESSAGE" in e], f"EVENT 分支不应套用 MESSAGE 规则: {errs}"
