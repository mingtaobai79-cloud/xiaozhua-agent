"""P3 逻辑图执行器：结构 → 构造器 → schema（离线，假 composer / 假元数据）。

真实平台实证（数据源有效校验，9 节点 / 嵌套 BRANCH / 多条件查询 / 函数表达式）：
save PASS + readback PASS + expression_verify PASS（2026-11-01）。
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.construction.logic_graph import (  # noqa: E402
    GraphError, LogicGraphRunner, _norm_cond_op, validate_graph,
)
from components.construction.microflow_fields import to_context_variable  # noqa: E402

DTO = "com.seeyon.app.dto.PlanDto"


# ---------------------------------------------------------------- 条件右值（语料裁决）
def test_context_variable_is_json_string():
    """★ 条件右值只能是 CONTEXT_VARIABLE/CONSTANT/EXPRESSION（470/193/136）。
    SelectParam 在 799 条语料里出现 0 次，塞进去平台回 BOOT_1001。"""
    ref = {"type": "SelectParam", "selectParam": {
        "outputName": "_RETRIEVE_a", "name": "_RETRIEVE_a.expNum",
        "id": DTO + ".expNum", "dataType": "INTEGER", "javaType": "java.lang.Integer",
        "description": "数量", "position": "children",
        "nodeInfo": {"nodeId": "RETRIEVE_a"}}}
    cv = to_context_variable(ref)
    assert cv["type"] == "CONTEXT_VARIABLE"
    assert isinstance(cv["value"], str)          # JSON 字符串，不是对象
    import json
    inner = json.loads(cv["value"])
    assert inner["outputName"] == "_RETRIEVE_a"
    assert "nodeInfo" not in inner               # UI 键不能带进去
    assert inner["parentLabel"] == ""


def test_context_variable_idempotent():
    cv = {"type": "CONTEXT_VARIABLE", "value": "{}", "desc": ""}
    assert to_context_variable(cv) is cv


def test_cond_op_normalization():
    for raw, want in (("==", "EQ"), ("!=", "NE"), (">", "GT"), (">=", "GE"),
                      ("<", "LT"), ("<=", "LE"), ("=", "EQ"), (None, "EQ")):
        assert _norm_cond_op(raw) == want


def test_cond_op_unknown_blocked():
    with pytest.raises(GraphError):
        _norm_cond_op("~=")


# ---------------------------------------------------------------- 图结构
def test_validate_nested_branch_and_loop():
    g = {"nodes": [
        {"id": "b", "kind": "branch", "condition": {"const": True},
         "then": [{"id": "f", "kind": "for_each", "list": "arr",
                   "body": [{"id": "x", "kind": "change_entity", "entity": "E",
                             "from_node": "f", "fields": {"a": 1}}]}]}]}
    assert validate_graph(g) == []


def test_validate_end_from_nested_ok():
    g = {"nodes": [{"id": "b", "kind": "branch", "condition": {"const": True},
                    "then": [{"id": "inner", "kind": "retrieve", "entity": "E"}]}],
         "end": {"from": "inner"}}
    assert validate_graph(g) == []


# ---------------------------------------------------------------- 执行器（假 composer）
class FakeComposer:
    """最小 composer：只验证执行器的容器/顺序/登记语义，不碰平台。"""

    def __init__(self):
        self.nodes = []
        self.by_alias = {}
        self.trigger = {"nodeId": "MFStartNode", "type": "MANUAL",
                        "output": {"name": "_FLOW_INPUT_x", "dataType": "DTO"}}
        self.refs = None
        self.b = object()          # 假 builder（真实构造器才用得上）
        self.finished = None
        self._n = 0

    def _mk(self, at, caption, **extra):
        self._n += 1
        node = {"nodeId": "%s_%d" % (at, self._n), "actionType": at, "type": "ACTIVITY",
                "caption": caption, "output": {"name": "_%s_%d" % (at, self._n),
                                               "dataType": "DTO", "type": "OBJECT"}}
        node.update(extra)
        return node

    def step(self, kind, alias, **kw):
        node = self._mk(kind.upper(), kw.get("caption") or alias)
        self.nodes.append(node)         # 模拟 composer._st_* 自己 _add
        return node

    def refs_field(self, node, field):
        return {"type": "SelectParam", "selectParam": {
            "outputName": (node.get("output") or {}).get("name"),
            "name": "%s.%s" % ((node.get("output") or {}).get("name"), field),
            "id": DTO + "." + field, "dataType": "STRING", "javaType": "java.lang.String",
            "position": "children", "description": field}}

    def _out_ref(self, node):
        return {"type": "SelectParam", "selectParam": {
            "outputName": (node.get("output") or {}).get("name")}}

    def finish(self, *, end_from="", trigger=None, out_desc="", basic_out=None):
        self.finished = {"end_from": end_from, "trigger": trigger,
                         "out_desc": out_desc, "basic_out": basic_out}
        return {"trig": trigger, "nodes": self.nodes}


def _runner():
    c = FakeComposer()
    return c, LogicGraphRunner(c, resolver=None, backend=None)


def test_branch_body_goes_into_condition_nodes():
    c, r = _runner()
    seen = {}

    def fake_branch_node(builder, conds, caption="", **kw):
        seen["conds"] = conds
        return {"nodeId": "BRANCH_1", "type": "BRANCH", "actionType": "BRANCH",
                "caption": caption, "conditions": [
                    {"name": "ifBranch", "expression": conds[0]["expression"], "nodes": []},
                    {"name": "elseBranch", "expression": None, "nodes": []}]}

    import components.construction.microflow_nodes_extra as X
    orig = X.branch
    X.branch = fake_branch_node
    try:
        # 绕过表达式后端：直接给一个假条件（build_expression 会要求 backend）
        r._build_expression = lambda spec, rt, n=None: {"title": "t", "schema": "{}"}
        r.run({"nodes": [
            {"id": "a", "kind": "retrieve", "entity": "E"},
            {"id": "b", "kind": "branch", "condition": {"const": True},
             "then": [{"id": "t1", "kind": "create_variable", "title": "v1",
                       "data_type": "STRING", "value": "x"}],
             "else": [{"id": "e1", "kind": "create_variable", "title": "v2",
                       "data_type": "STRING", "value": "y"}]}]})
    finally:
        X.branch = orig
    br = c.by_alias["b"]
    then_nodes = br["conditions"][0]["nodes"]
    else_nodes = br["conditions"][-1]["nodes"]
    assert len(then_nodes) == 1 and len(else_nodes) == 1
    assert then_nodes[0]["actionType"] == "CREATE_VARIABLE"
    assert else_nodes[0]["actionType"] == "CREATE_VARIABLE"
    # ★ 分支体节点不能留在顶层（否则分支是空壳、节点全跑顶层）
    top_ids = {n["nodeId"] for n in c.nodes}
    assert then_nodes[0]["nodeId"] not in top_ids
    assert else_nodes[0]["nodeId"] not in top_ids


def test_top_level_nodes_not_duplicated():
    """★ composer._st_* 已经 _add 过；执行器再 append 会让每个节点出现两次。"""
    c, r = _runner()
    r.run({"nodes": [{"id": "a", "kind": "retrieve", "entity": "E"},
                     {"id": "b", "kind": "create_variable", "title": "v",
                      "data_type": "STRING", "value": "x"}]})
    assert len(c.nodes) == 2
    assert len({n["nodeId"] for n in c.nodes}) == 2


def test_finish_receives_trigger():
    """★ finish(trigger=None) 会丢掉注入的入参 DTO → G2 把入参引用全判悬空。"""
    c, r = _runner()
    r.run({"nodes": [{"id": "a", "kind": "retrieve", "entity": "E"}]})
    assert c.finished["trigger"] is c.trigger


def test_branch_marks_self_before_body():
    """分支体内可引用外层已执行节点；分支外的后序节点必须仍不可见。"""
    c, r = _runner()
    order = []

    import components.construction.microflow_nodes_extra as X
    orig = X.branch
    X.branch = lambda b, conds, caption="", **kw: {
        "nodeId": "BRANCH_1", "type": "BRANCH", "actionType": "BRANCH", "caption": caption,
        "conditions": [{"name": "ifBranch", "expression": None, "nodes": []},
                       {"name": "elseBranch", "expression": None, "nodes": []}]}
    r._build_expression = lambda spec, rt, n=None: {"title": "t", "schema": "{}"}
    try:
        r._exec_node({"id": "a", "kind": "retrieve", "entity": "E"})
        r._exec_node({"id": "b", "kind": "branch", "condition": {"const": True},
                      "then": [{"id": "t1", "kind": "retrieve", "entity": "E"}]})
    finally:
        X.branch = orig
    assert r.scope.has("a") and r.scope.has("b") and r.scope.has("t1")
    assert c.by_alias["b"]["conditions"][0]["nodes"][0]["nodeId"].startswith("RETRIEVE")


def test_unknown_kind_fails_loudly():
    c, r = _runner()
    with pytest.raises(GraphError):
        r.run({"nodes": [{"id": "a", "kind": "retrieve", "entity": "E"},
                         {"id": "z", "kind": "branch", "condition": {"const": True},
                          "then": []}]}, )


# ---------------------------------------------------------------- 条件右值类型
#
# ★★ 语料裁决（pmp_schemas.json，全部 CONSTANT 条件 240 条）：
#     BOOLEAN → value 是 bool（15/15）
#     DECIMAL → value 是 float（1/1）
#     STRING/ENUM/CTPENUM → value 是 str
#   右值类型必须与左值字段 dataType 一致，否则前端按文本渲染
#   （设计器下拉给的是「是/否」），后端也拿不到布尔值。

def test_constant_boolean_is_real_bool():
    """BOOLEAN 字段的条件右值必须是 JSON 布尔，不是字符串 "true"。"""
    from components.construction.logic_graph import _constant

    r = _constant(True, "BOOLEAN")
    assert r["type"] == "CONSTANT"
    assert r["value"] is True and r["desc"] is True

    r2 = _constant("true", "BOOLEAN")      # 字符串也要归一成布尔
    assert r2["value"] is True

    r3 = _constant(False, "BOOLEAN")
    assert r3["value"] is False


def test_constant_numeric_types_match_field():
    from components.construction.logic_graph import _constant

    assert _constant(5, "INTEGER")["value"] == 5
    assert isinstance(_constant(5, "INTEGER")["value"], int)
    assert isinstance(_constant("5", "INTEGER")["value"], int)
    d = _constant(3.14, "DECIMAL")
    assert isinstance(d["value"], float) and abs(d["value"] - 3.14) < 1e-9


def test_constant_string_types_stay_string():
    from components.construction.logic_graph import _constant

    assert _constant("mysql", "STRING")["value"] == "mysql"
    assert _constant("active", "ENUM")["value"] == "active"
    assert _constant("x", "CTPENUM")["value"] == "x"


def test_cond_value_uses_left_field_datatype():
    """★ 执行器必须按左值字段的 dataType 决定右值类型（不是一律字符串）。"""
    ents = {"E": {"caption": "E", "attributes": {
        "enabled": {"dataType": "BOOLEAN", "id": DTO + ".enabled", "caption": "是否启用"},
        "amount": {"dataType": "DECIMAL", "id": DTO + ".amount", "caption": "金额"},
        "name": {"dataType": "STRING", "id": DTO + ".name", "caption": "名称"},
    }}}

    class C(FakeComposer):
        def entity(self, label):
            return ents[label]

    c = C()
    r = LogicGraphRunner(c, resolver=None, backend=None)
    m = c.entity("E")

    v = r._cond_value({"const": True}, {"id": "n"}, entity=m, field="enabled")
    assert v["value"] is True and v["desc"] is True

    v2 = r._cond_value({"const": 12.5}, {"id": "n"}, entity=m, field="amount")
    assert isinstance(v2["value"], float)

    v3 = r._cond_value({"const": "abc"}, {"id": "n"}, entity=m, field="name")
    assert v3["value"] == "abc"


def test_entity_fields_numeric_const_stringified():
    """★ 写实体数值字段（BIGINTEGER/INTEGER/DECIMAL）的 const 常量必须转字符串。

    检测器 CheckUtils 读 attrValue.getSimple()（String）后 Long.valueOf 校验，
    传 int/float 会报「不是长整数类型」（NOT_BIGINTEGER，MF-01 构建暴露）。
    """
    ents = {"E": {"caption": "E", "attributes": {
        "deptId": {"dataType": "BIGINTEGER", "id": DTO + ".deptId"},
        "amount": {"dataType": "DECIMAL", "id": DTO + ".amount"},
        "name": {"dataType": "STRING", "id": DTO + ".name"},
    }}}

    class C(FakeComposer):
        def entity(self, label):
            return ents[label]

    r = LogicGraphRunner(C(), resolver=None, backend=None)
    out = r._entity_fields(
        {"deptId": {"const": 1}, "amount": {"const": 1000.0}, "name": {"const": "x"}},
        {"entity": "E"})
    assert out["deptId"]["simple"] == "1"
    assert out["amount"]["simple"] == "1000.0"
    assert out["name"]["simple"] == "x"


def test_enum_cond_desc_is_display_name():
    """★ ENUM/CTPENUM 条件的 desc 必须是显示名，不是枚举标识。

    语料：{"value":"-3062090190298864225","desc":"投标报备申请"}
    写成 desc=标识，设计器里就显示一串数字，人读不出来。
    多选用逗号拼接：value="ID1,ID2" desc="显示名1,显示名2"
    """
    attr = {"dataType": "ENUM", "enumItemObjects": [
        {"name": "PENDING", "caption": "待处理"},
        {"name": "DONE", "caption": "已完成"},
    ]}
    m = {"caption": "E", "attributes": {"st": attr}}
    r = LogicGraphRunner(FakeComposer(), resolver=None, backend=None)

    v = r._cond_value({"const": "PENDING"}, {"id": "n"}, entity=m, field="st")
    assert v["value"] == "PENDING" and v["desc"] == "待处理"

    v2 = r._cond_value({"const": "PENDING,DONE"}, {"id": "n"},
                       entity=m, field="st")
    assert v2["value"] == "PENDING,DONE"
    assert v2["desc"] == "待处理,已完成"


def test_enum_cond_unknown_code_falls_back_to_code():
    """查不到的枚举码不能编造显示名，回退成码本身。"""
    m = {"caption": "E", "attributes": {
        "st": {"dataType": "CTPENUM", "enumItemObjects": [
            {"name": "A", "caption": "甲"}]}}}
    r = LogicGraphRunner(FakeComposer(), resolver=None, backend=None)
    v = r._cond_value({"const": "ZZZ"}, {"id": "n"}, entity=m, field="st")
    assert v["value"] == "ZZZ" and v["desc"] == "ZZZ"
