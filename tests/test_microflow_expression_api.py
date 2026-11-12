"""表达式后端校验组件的契约测试（不连浏览器）。"""
from __future__ import annotations

import json

import pytest

from components.udc.microflow.expression_api import (
    CHECK_PATH,
    EXPRESSION_PREFIX,
    SCHEMA_KEYS,
    SCHEMA_MARKER_KEY,
    TRANSFORM_PATH,
    build_save_dto,
    context_to_schemas,
    verify_expression,
)

# 真实报文（脱敏：应用名/实体名替换）
CONTEXT = [
    {
        "name": "_RETRIEVE_MSwqDF",
        "description": "查询单条数据(1)",
        "type": "OBJECT",
        "selectable": False,
        "enableDataI18n": False,
        "uniformityParams": {
            "paramId": "com.seeyon.demoapp.dto.DemoDto",
            "paramCategory": "DTO",
            "extensionProperties": '{"id":"com.seeyon.demoapp.dto.DemoDto"}',
            "pageNodeExtension": None,
        },
        "properties": [
            {
                "name": "_RETRIEVE_MSwqDF",
                "description": "查询结果 [演示实体]",
                "type": "OBJECT",
                "selectable": True,
                "enableDataI18n": False,
                "uniformityParams": {
                    "paramId": "com.seeyon.demoapp.dto.DemoDto",
                    "paramCategory": "OBJECT",
                    "extensionProperties": '{"id":"com.seeyon.demoapp.dto.DemoDto"}',
                    "pageNodeExtension": None,
                },
                "properties": [
                    {
                        "name": "expNum",
                        "description": "实验数量",
                        "type": "INTEGER",
                        "selectable": True,
                        "enableDataI18n": False,
                        "sort": 14,
                        "uniformityParams": {
                            "paramId": "com.seeyon.demoapp.dto.DemoDto.expNum",
                            "paramCategory": "INTEGER",
                            "extensionProperties": '{"id":"com.seeyon.demoapp.dto.DemoDto.expNum",'
                                                   '"relationType":"NONE","javaType":"java.lang.Integer"}',
                            "pageNodeExtension": None,
                        },
                    }
                ],
            }
        ],
    }
]

TOKENS = [
    {"uid": "u1", "type": "VARIABLE",
     "value": "_RETRIEVE_MSwqDF._RETRIEVE_MSwqDF.expNum",
     "desc": "微流程.查询单条数据(1).查询结果 [演示实体].实验数量"},
    {"uid": "u2", "type": "OPERATOR", "value": ">", "desc": ">"},
    {"uid": "u3", "type": "CONSTANT", "value": "0", "desc": "0"},
]


def _expr():
    schema = {
        "designData": {
            "expressionTranslation": "微流程.查询单条数据(1).查询结果 [演示实体].实验数量 > 0 ",
            "resultTypeInfo": "BOOLEAN",
            "terminalType": "BACKEND",
            "context": CONTEXT,
            "tokens": TOKENS,
        },
        "runtimeData": {"executableExpr": "SIG(X > 0)"},
    }
    return {"title": "微流程.查询单条数据(1).查询结果 [演示实体].实验数量 > 0 ",
            "schema": json.dumps(schema, ensure_ascii=False)}


# ---------------------------------------------------------------- schemas 转换

def test_context_to_schemas_adds_skip_every_level():
    """★ 每层都要有 skip:true，漏一层就会被 reject"""
    out = context_to_schemas(CONTEXT)
    assert out[0][SCHEMA_MARKER_KEY] is True
    assert out[0]["properties"][0][SCHEMA_MARKER_KEY] is True
    assert out[0]["properties"][0]["properties"][0][SCHEMA_MARKER_KEY] is True


def test_context_to_schemas_keeps_page_node_extension_null():
    """schemas 里 uniformityParams.pageNodeExtension 保留，值为 null（实测报文如此）"""
    out = context_to_schemas(CONTEXT)
    up = out[0]["uniformityParams"]
    assert "pageNodeExtension" in up
    assert up["pageNodeExtension"] is None


def test_context_to_schemas_keeps_uniformity_params():
    """paramId 必须保留 —— VariableCheckFilter 靠它认变量"""
    out = context_to_schemas(CONTEXT)
    leaf = out[0]["properties"][0]["properties"][0]
    assert leaf["uniformityParams"]["paramId"] == "com.seeyon.demoapp.dto.DemoDto.expNum"
    assert leaf["uniformityParams"]["paramCategory"] == "INTEGER"


def test_context_to_schemas_only_whitelisted_keys():
    """只保留白名单键，不夹带 sort 等展示字段"""
    out = context_to_schemas(CONTEXT)
    leaf = out[0]["properties"][0]["properties"][0]
    assert "sort" not in leaf          # sort 不在 SCHEMA_KEYS
    for k in leaf:
        if k == SCHEMA_MARKER_KEY:
            continue
        assert k in SCHEMA_KEYS, k


def test_context_to_schemas_empty():
    assert context_to_schemas([]) == []
    assert context_to_schemas(None) == []


# ---------------------------------------------------------------- DTO 装配

def test_build_save_dto_shape():
    dto = build_save_dto(_expr())
    assert dto["resultTypeInfo"] == "BOOLEAN"
    assert dto["terminalSupportType"] == "BACKEND"
    assert dto["isMultiSelect"] is False
    assert len(dto["schemas"]) == 1
    assert len(dto["tokens"]) == 3


def test_build_save_dto_tokens_keep_uid():
    """uid 必须保留 —— 服务端回包会回填"""
    dto = build_save_dto(_expr())
    assert dto["tokens"][0]["uid"] == "u1"


def test_build_save_dto_tokens_drop_none():
    """None 值不提交，避免 IGNORE_NULL 语义干扰"""
    e = _expr()
    s = json.loads(e["schema"])
    s["designData"]["tokens"][1]["uid"] = None
    e["schema"] = json.dumps(s, ensure_ascii=False)
    dto = build_save_dto(e)
    assert "uid" not in dto["tokens"][1]


def test_build_save_dto_does_not_include_param_type():
    """★ /check 与 /transform 不需要 paramType —— 这正是微流程能用的原因"""
    dto = build_save_dto(_expr())
    assert "paramType" not in dto


# ---------------------------------------------------------------- 端点常量

def test_endpoint_paths():
    assert EXPRESSION_PREFIX == "/service/udc/expression"
    assert CHECK_PATH == "/check"
    assert TRANSFORM_PATH == "/transform"


# ---------------------------------------------------------------- 端到端（mock driver）

class _FakeDriver:
    """模拟 CDP driver，按 URL 返回预置响应。"""

    def __init__(self, check_resp, transform_resp):
        self.check_resp = check_resp
        self.transform_resp = transform_resp
        self.calls = []

    def eval(self, expr, await_promise=False):
        assert await_promise is True, "必须 await_promise=True"
        if "/check" in expr:
            self.calls.append("check")
            return json.dumps(self.check_resp)
        if "/transform" in expr:
            self.calls.append("transform")
            return json.dumps(self.transform_resp)
        raise AssertionError("unexpected url in expr")


def _ok_check():
    return {"status": 200,
            "json": {"status": 0, "code": "BOOT_0000", "message": "SUCCESS",
                     "data": {"content": True}},
            "raw": "..."}


def _ok_transform(exec_expr="SIG(X > 0)"):
    return {"status": 200,
            "json": {"status": 0, "code": "BOOT_0000", "message": "SUCCESS",
                     "data": {"content": {
                         "designData": {"tokens": TOKENS},
                         "runtimeData": {"executableExpr": exec_expr}}}},
            "raw": "..."}


def test_verify_expression_all_pass_and_roundtrip_same():
    d = _FakeDriver(_ok_check(), _ok_transform("SIG(X > 0)"))
    r = verify_expression(d, _expr())
    assert r["ok"] is True
    assert r["check"]["ok"] is True
    assert r["transform"]["ok"] is True
    assert r["roundtripSame"] is True
    assert d.calls == ["check", "transform"]


def test_verify_expression_detects_roundtrip_mismatch():
    """库中 executableExpr 与 transform 产物不同 → roundtripSame=False"""
    d = _FakeDriver(_ok_check(), _ok_transform("SIG(DIFFERENT)"))
    r = verify_expression(d, _expr())
    assert r["ok"] is True
    assert r["roundtripSame"] is False


def test_verify_expression_check_fail_short_circuits():
    """check 失败就不该再调 transform"""
    bad = {"status": 200,
           "json": {"status": 3, "code": "FORMULA_6058", "message": "变量不存在",
                    "data": None},
           "raw": "..."}
    d = _FakeDriver(bad, _ok_transform())
    r = verify_expression(d, _expr())
    assert r["ok"] is False
    assert r["check"]["ok"] is False
    assert r["check"]["code"] == "FORMULA_6058"
    assert d.calls == ["check"]


def test_verify_expression_check_content_false_is_fail():
    """BOOT_0000 但 content 不是 true → 仍算失败"""
    resp = {"status": 200,
            "json": {"status": 0, "code": "BOOT_0000",
                     "data": {"content": False}},
            "raw": "..."}
    d = _FakeDriver(resp, _ok_transform())
    r = verify_expression(d, _expr())
    assert r["check"]["ok"] is False
