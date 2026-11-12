"""SUB_MICROFLOW 带参调用 + 流程入参引用的回归测试。

两条新能力（2026-11-02 实测支撑，见 core/facts/udc/microflow/node-sub-microflow.md）：

① 流程入参引用：写节点把 trigger.output（_FLOW_INPUT_xxx）当值用。
   真实形态取自语料 85 个写节点样本：SelectParam{id/dtoType/udcApp=null,
   name=key=path=outputName=入参名, position:"parent"}。
② 子微流程带参调用：mfService.input/output 必须来自子流程**当前**定义，
   契约不一致时平台在构建期报「一致性检测未通过」。
"""
import json

import pytest

from components.construction import logic_graph as LG
from components.construction.microflow_nodes_svc import sub_microflow


class _Ast:
    def __init__(self, dtype, ref):
        self.dtype = dtype
        self.ref = ref


class _Builder:
    app_name = "app"

    def build(self, action_type, caption=None):
        return {"nodeId": "SUB_MICROFLOW_abc", "type": "ACTIVITY",
                "actionType": action_type, "caption": caption}


# ── ① 流程入参引用形态 ──────────────────────────────────────────────────────
def test_flow_input_ref_shape():
    r = LG.LogicGraphRunner.__new__(LG.LogicGraphRunner)
    ast = _Ast("STRING", {"outputName": "_FLOW_INPUT_abc", "title": "父流程传入标记"})
    v = r._flow_input_ref(ast, "_FLOW_INPUT_abc")
    sp = v["selectParam"]
    assert v["type"] == "SelectParam"
    assert v["desc"] == "父流程传入标记 [文本]"
    assert sp["id"] is None and sp["dtoType"] is None and sp["udcApp"] is None
    assert sp["name"] == sp["key"] == sp["path"] == sp["outputName"] == "_FLOW_INPUT_abc"
    assert sp["position"] == "parent"
    assert sp["dataType"] == "STRING" and sp["javaType"] == "java.lang.String"


def test_flow_input_ref_numeric_type():
    r = LG.LogicGraphRunner.__new__(LG.LogicGraphRunner)
    ast = _Ast("BIGINTEGER", {"outputName": "_FLOW_INPUT_n1", "title": "数量"})
    v = r._flow_input_ref(ast, "_FLOW_INPUT_n1")
    assert v["selectParam"]["javaType"] == "java.lang.Long"
    assert v["desc"] == "数量 [整数]"


# ── ② 子微流程带参调用 ──────────────────────────────────────────────────────
SVC_IN = {"id": None, "javaType": "java.lang.String", "dataType": "STRING",
          "type": "OBJECT", "desc": "父流程传入标记", "dtoType": None,
          "udcApp": None, "name": "_FLOW_INPUT_ef19b7"}
SVC_OUT = {"id": None, "javaType": "java.lang.String", "dataType": "STRING",
           "type": "OBJECT", "desc": "子流程返回", "dtoType": None,
           "udcApp": None, "hasPagination": None, "name": "_FLOW_OUTPUT_2d7da7"}
MF = {"id": "-2153764118257917841", "name": "p5subc1", "caption": "子流程取证",
      "appId": "1", "hasInput": True, "hasOutput": True, "input": SVC_IN,
      "output": SVC_OUT, "path": "/microflow/p5subc1", "method": "POST",
      "triggerType": "MANUAL", "type": "SERVICE", "restType": "POST"}


def test_sub_microflow_carries_real_contract():
    node = sub_microflow(_Builder(), MF, caption="调用子流程")
    assert node["mfService"]["hasInput"] is True
    assert node["mfService"]["input"]["name"] == "_FLOW_INPUT_ef19b7"
    assert node["mfService"]["hasOutput"] is True
    assert node["mfService"]["output"]["dataType"] == "STRING"
    assert node["mfService"]["path"].endswith("p5subc1")


def test_sub_microflow_scalar_mapping_uses_value():
    val = {"type": "SelectParam", "selectParam": {"name": "_CREATE_VARIABLE_x"}}
    node = sub_microflow(_Builder(), MF, caption="调用子流程",
                         value=val, out_desc="子流程返回")
    assert node["mappingType"] == "value"
    assert node["value"] is val
    assert node["outputName"] == "子流程返回"
    assert node["output"]["desc"] == "子流程返回"
    assert "attrs" not in node, "标量入参不该带 attrs"


def test_sub_microflow_output_follows_child_type():
    mf = json.loads(json.dumps(MF))
    mf["output"] = {**SVC_OUT, "dataType": "BIGINTEGER", "javaType": "java.lang.Long"}
    node = sub_microflow(_Builder(), mf, caption="调用子流程")
    assert node["output"]["dataType"] == "BIGINTEGER"
    assert node["output"]["javaType"] == "java.lang.Long"


def test_sub_microflow_without_output_keeps_boolean_default():
    mf = json.loads(json.dumps(MF))
    mf["hasOutput"] = False
    mf["output"] = None
    node = sub_microflow(_Builder(), mf, caption="调用子流程")
    assert node["output"]["dataType"] == "BOOLEAN"
