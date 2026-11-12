"""P2-3 引用解析器：静态推导 / 顺序裁决 / 缓存应用隔离（离线）。"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.udc.microflow.expression_refs import (  # noqa: E402
    ReferenceError_, ReferenceResolver,
)

APP = "datamigration9000000000000000001"
DTO = "com.seeyon.%s.dto.PlanDto" % APP


def mk(nid, at, out=None, structure=None, title="", nodes=None, conditions=None, **kw):
    n = {"nodeId": nid, "actionType": at, "title": title or at, "caption": title or at,
         "output": out, "structure": structure}
    if nodes:
        n["nodes"] = nodes
    if conditions:
        n["conditions"] = conditions
    n.update(kw)
    return n


def ret_node(nid="_RETRIEVE_a1", title="查询方案"):
    return mk(nid, "RETRIEVE",
                out={"name": nid, "id": DTO, "dataType": "DTO", "type": "OBJECT"},
                structure={"id": DTO, "caption": "迁移方案"},
                title=title,
                selectParam={"name": "expNum", "dataType": "INTEGER", "id": DTO + ".expNum",
                             "description": "实验数量"})


def ret_array_node(nid="_RETRIEVE_ARRAY_a2"):
    return mk(nid, "RETRIEVE_ARRAY",
              out={"name": nid, "id": DTO, "dataType": "DTO", "type": "ARRAY"},
              structure={"id": DTO, "caption": "迁移方案"}, title="查询列表",
              selectParam={"name": "expNum", "dataType": "INTEGER", "id": DTO + ".expNum",
                           "description": "实验数量"})


# ------------------------------------------------------------------ 顺序语义
def test_index_before_excludes_self_and_later():
    nodes = [ret_node(), mk("_CHANGE_VARIABLE_x", "CHANGE_VARIABLE")]
    r = ReferenceResolver(APP, "app")
    avail = r.index_before(nodes, "_CHANGE_VARIABLE_x")
    assert list(avail) == ["_RETRIEVE_a1"]


def test_ref_later_node_rejected():
    """引用后序节点：平台 check 会过但运行期取不到值 —— 必须解析期拦。"""
    nodes = [mk("_CREATE_VARIABLE_b", "CREATE_VARIABLE"), ret_node()]
    r = ReferenceResolver(APP, "app")
    with pytest.raises(ReferenceError_):
        r.ref_from_output_name(nodes, "_RETRIEVE_a1", "expNum", "_CREATE_VARIABLE_b")


def test_unknown_node_id_rejected():
    r = ReferenceResolver(APP, "app")
    with pytest.raises(ReferenceError_):
        r.index_before([ret_node()], "_NOPE")


def test_nested_branch_nodes_are_indexed():
    inner = mk("_CREATE_VARIABLE_c", "CREATE_VARIABLE",
               out={"name": "_CREATE_VARIABLE_c", "dataType": "INTEGER", "type": "OBJECT"})
    br = mk("BRANCH_1", "BRANCH", nodes=[], conditions=[{"expression": None, "nodes": [inner]}])
    nodes = [ret_node(), br, mk("_CHANGE_VARIABLE_d", "CHANGE_VARIABLE")]
    r = ReferenceResolver(APP, "app")
    avail = r.index_before(nodes, "_CHANGE_VARIABLE_d")
    assert "_CREATE_VARIABLE_c" in avail      # 分支内节点也算已执行


# ------------------------------------------------------------------ 静态推导
def test_field_ref_reads_node_carried_metadata():
    r = ReferenceResolver(APP, "app")
    nf = r.field_ref_from_node(ret_node(), "expNum")
    assert nf.ref["outputName"] == "_RETRIEVE_a1"
    assert nf.ref["fields"]["expNum"]["dataType"] == "INTEGER"
    assert nf.ref["dto_id"] == DTO
    assert nf.dtype == "INTEGER"


def test_array_output_marks_is_array():
    r = ReferenceResolver(APP, "app")
    nf = r.field_ref_from_node(ret_array_node(), "expNum")
    assert nf.ref["is_array"] is True


def test_missing_field_without_liverefs_reports_clearly():
    r = ReferenceResolver(APP, "app")     # live_refs=None
    with pytest.raises(ReferenceError_) as ei:
        r.field_ref_from_node(ret_node(), "noSuchField")
    assert "live_refs" in str(ei.value) or "structure" in str(ei.value)


def test_node_without_output_name_rejected():
    r = ReferenceResolver(APP, "app")
    with pytest.raises(ReferenceError_):
        r.field_ref_from_node({"nodeId": "X", "actionType": "RETRIEVE"}, "f")


# ------------------------------------------------------------------ 动态 + 缓存
class FakeLiveRefs:
    def __init__(self):
        self.calls = []

    def entity_model(self, app_id, app_name, label=""):
        self.calls.append((app_id, label))
        return {"attributes": {"expNum": {"dataType": "INTEGER", "id": DTO + ".expNum",
                                          "caption": "实验数量"}},
                "fullName": DTO}


def test_lookup_field_uses_cache():
    fake = FakeLiveRefs()
    r = ReferenceResolver(APP, "app", live_refs=fake)
    n = {"nodeId": "N1", "actionType": "RETRIEVE", "output": {"name": "_X"},
         "structure": {"id": DTO, "caption": "迁移方案"}}
    r.field_ref_from_node(n, "expNum")
    r.field_ref_from_node(n, "expNum")
    assert len(fake.calls) == 1


def test_cache_is_app_scoped():
    """★ 不同应用同名实体必须各自查询：串缓存会生成指向错误 DTO 的表达式。"""
    fake = FakeLiveRefs()
    r1 = ReferenceResolver("appA", "appA", live_refs=fake)
    r2 = ReferenceResolver("appB", "appB", live_refs=fake)
    r1.entity_model("迁移方案")
    r2.entity_model("迁移方案")
    assert len(fake.calls) == 2
    assert fake.calls[0][0] == "appA" and fake.calls[1][0] == "appB"


# ------------------------------------------------------------------ 类型归一
def test_type_normalization_both_casings():
    r = ReferenceResolver(APP, "app")
    n = ret_node()
    n["selectParam"]["dataType"] = "Integer"      # 回读态首字母大写
    assert r.field_ref_from_node(n, "expNum").dtype == "INTEGER"


def test_sysvar_requires_name():
    r = ReferenceResolver(APP, "app")
    with pytest.raises(ReferenceError_):
        r.sysvar("", "DATETIME")
    assert r.sysvar("currentTime", "DATETIME").name == "currentTime"
