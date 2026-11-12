"""GraphQL 公用调用器：双层解析与「假成功」纪律必须被锁住。

锁的是**仓内实际踩过的坑**：
  1 code 在 data.data0.code，不在顶层（一轮把 14 个存在的 op 全判成"未定"）
  2 str(None)=="None" 恒真（把"没返回"当"有返回"）
  3 空 body 回 BOOT_0000 不代表成功（delete 缺 id 时 content=0）
  4 REST 域用 GraphQL 探是假阴性（404 才是"不存在"）
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from components.platform_operations.graphql_call import (  # noqa: E402
    DEFAULT_SELECTION,
    GraphqlCallError,
    GraphqlResult,
    OK_CODE,
    build_body,
    call_rest,
    parse_response,
)


# ---------------------------------------------------------------- build_body
def test_build_body_mutation_shape():
    b = build_body("udcEnumPost", {"appId": "1"})
    assert b["query"].startswith("mutation graphqlLoader")
    assert "udcEnumPostInputBody" in b["query"]
    assert "data0: udcEnumPost(body: $params0)" in b["query"]
    assert b["variables"] == {"params0": {"appId": "1"}}


def test_build_body_query_uses_path_and_inputpath():
    b = build_body("udcApplicationDetailGet", {"id": "1"},
                   kind="query", arg_name="path")
    assert b["query"].startswith("query graphqlLoader")
    assert "udcApplicationDetailGetInputPath" in b["query"]
    assert "(path: $params0)" in b["query"]


def test_build_body_rejects_unknown_kind():
    try:
        build_body("x", {}, kind="subscription")
    except ValueError as exc:
        assert "mutation" in str(exc)
    else:
        raise AssertionError("非法 kind 应抛 ValueError")


def test_build_body_default_selection():
    b = build_body("x", {})
    assert DEFAULT_SELECTION in b["query"]


# ---------------------------------------------------------------- 双层解析
def _resp(d0: dict, trace="t1"):
    return json.dumps({"traceId": trace, "data": {"data0": d0}})


def test_parse_reads_nested_data0_not_top_level():
    """★ 核心：code 在 data.data0.code。顶层没有 code。"""
    text = _resp({"code": "BOOT_0000", "status": 0,
                  "data": {"content": {"id": "9"}}, "message": "SUCCESS"})
    r = parse_response("op", 200, text)
    assert r.code == "BOOT_0000"
    assert r.status == 0
    assert r.ok is True
    assert r.content == {"id": "9"}
    assert r.trace_id == "t1"


def test_parse_does_not_treat_top_level_code_as_result():
    """响应若把 code 放在顶层（非法形态），不得当成功。"""
    text = json.dumps({"code": "BOOT_0000", "data": {}})
    r = parse_response("op", 200, text)
    assert r.code is None
    assert r.ok is False


def test_parse_keeps_none_message_as_none():
    """★ str(None) 恒真 —— message 必须保留原始 None。"""
    text = _resp({"code": "BOOT_3000", "status": 3, "message": None, "data": None})
    r = parse_response("op", 200, text)
    assert r.message is None
    assert r.code == "BOOT_3000"
    assert r.ok is False


def test_parse_surfaces_graphql_errors():
    """字段不存在要暴露，不能被当空结果静默吞掉。"""
    text = json.dumps({"errors": [{"message": "Validation error: FieldUndefined"}],
                       "data": {"data0": None}})
    r = parse_response("zzzNotReal", 200, text)
    assert r.parse_error == "GraphQL errors"
    assert "FieldUndefined" in (r.message or "")
    assert r.ok is False


def test_parse_non_json_response():
    r = parse_response("op", 200, "HTTP/1.1 404 Not Found\n\n")
    assert r.parse_error
    assert r.code is None
    assert r.ok is False


# ---------------------------------------------------------------- 假成功
def test_ok_is_platform_level_not_business_success():
    """★ BOOT_0000 + content=0 仍算"平台成功"，但业务没生效。"""
    text = _resp({"code": "BOOT_0000", "status": 0, "message": "SUCCESS",
                  "data": {"content": 0}})
    r = parse_response("delete", 200, text)
    assert r.ok is True, "平台层确实是成功的"
    assert r.is_empty_content is True, "但业务层要能识别空内容"


def test_require_ok_raises_with_diagnostics():
    text = _resp({"code": "BOOT_1001", "status": 1,
                  "message": "应用ID 不能为null", "data": None})
    r = parse_response("op", 200, text)
    try:
        r.require_ok()
    except GraphqlCallError as exc:
        s = str(exc)
        assert "BOOT_1001" in s and "应用ID" in s
    else:
        raise AssertionError("require_ok 应抛 GraphqlCallError")


def test_require_ok_returns_self_on_success():
    text = _resp({"code": OK_CODE, "status": 0, "message": "SUCCESS",
                  "data": {"content": 1}})
    r = parse_response("op", 200, text).require_ok()
    assert isinstance(r, GraphqlResult)
    assert r.content == 1


# ---------------------------------------------------------------- REST
class _FakeClient:
    def __init__(self, http, body):
        self._http, self._body = http, body

    def evaluate(self, *_a, **_k):
        return json.dumps({"http": self._http, "body": self._body})


def test_call_rest_404_is_vacuum():
    c = _FakeClient(404, json.dumps({"code": "server_404", "message": None}))
    r = call_rest(c, "/service/udc/excel/delete-template", {})
    assert r["vacuum"] is True


def test_call_rest_business_error_is_not_vacuum():
    """★ 业务错码 = 路径存在。只有 404 才算不存在。"""
    c = _FakeClient(200, json.dumps({"code": "BOOT_1001",
                                     "message": "模板Id 不能为null",
                                     "data": {"content": None}}))
    r = call_rest(c, "/service/udc/excel/export-excel-template", {})
    assert r["vacuum"] is False
    assert r["code"] == "BOOT_1001"


def test_call_rest_success_content():
    c = _FakeClient(200, json.dumps({"code": "BOOT_0000",
                                     "data": {"content": [1, 2]}}))
    r = call_rest(c, "/service/udc/attributeSet/search-list", {})
    assert r["vacuum"] is False
    assert r["content"] == [1, 2]


# ---------------------------------------------------------------- 事实登记
def test_domain_survey_fact_exists_and_registered():
    f = ROOT / "core" / "facts" / "udc" / "DOMAIN-SURVEY.md"
    assert f.is_file()
    txt = f.read_text(encoding="utf-8")
    assert "九" in txt and "契约" in txt
    idx = (ROOT / "core" / "facts" / "INDEX.md").read_text(encoding="utf-8")
    assert "DOMAIN-SURVEY.md" in idx


def test_survey_records_real_gaps():
    """盘点必须点名 0 契约的域，不能只说"都完成了"。"""
    txt = (ROOT / "core" / "facts" / "udc" / "DOMAIN-SURVEY.md").read_text(
        encoding="utf-8")
    assert "规则域" in txt and "栏目域" in txt
    assert "0 契约" in txt
