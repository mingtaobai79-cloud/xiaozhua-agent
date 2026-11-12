"""P4 业务需求 → 逻辑图编译器（离线，假 LiveRefs）。"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.construction.requirement_compiler import (  # noqa: E402
    BusinessRequirementCompiler, CompileError,
)

ENTITIES = [
    {"caption": "数据源配置信息", "dtoFullName": "com.seeyon.app.dto.MigrationDatasourceDto",
     "fullName": "com.seeyon.app.domain.MigrationDatasource"},
    {"caption": "数据源连接池", "dtoFullName": "com.seeyon.app.dto.PoolDto",
     "fullName": "com.seeyon.app.domain.Pool"},
    {"caption": "迁移方案配置", "dtoFullName": "com.seeyon.app.dto.MigrationPlanDto",
     "fullName": "com.seeyon.app.domain.MigrationPlan"},
]


class FakeRefs:
    def entity(self, app_id, app_name):
        return [dict(e) for e in ENTITIES]


def C():
    return BusinessRequirementCompiler(FakeRefs())


# ---------------------------------------------------------------- 基础
def test_non_dict_draft_blocked():
    with pytest.raises(CompileError):
        C().compile(["x"])


def test_minimal_ready():
    r = C().compile({"nodes": [
        {"id": "ds", "kind": "retrieve", "entity": "数据源配置信息", "by_field": "id"}],
        "end": {"from": "ds"}})
    assert r.status == "READY", [i.to_dict() for i in r.issues]
    assert r.graph["nodes"][0]["entity"] == "数据源配置信息"


def test_empty_nodes_blocked():
    r = C().compile({"nodes": []})
    assert r.status == "BLOCKED"
    assert any(i.code == "STRUCTURE" for i in r.issues)


# ---------------------------------------------------------------- 真名解析
def test_entity_exact_name_resolved():
    r = C().compile({"nodes": [
        {"id": "a", "kind": "retrieve", "entity": "数据源配置信息"}]})
    assert r.status == "READY"
    assert r.resolved["entities"]["数据源配置信息"] == "数据源配置信息"


def test_entity_by_dto_resolved():
    r = C().compile({"nodes": [
        {"id": "a", "kind": "retrieve",
         "entity": "com.seeyon.app.dto.MigrationDatasourceDto"}]})
    assert r.status == "READY"
    assert r.graph["nodes"][0]["entity"] == "数据源配置信息"


def test_entity_unique_substring_fixed():
    """★ 用户口语「连接池」→ 唯一候选「数据源连接池」可以自动纠，但必须留痕。"""
    r = C().compile({"nodes": [{"id": "a", "kind": "retrieve", "entity": "连接池"}]})
    assert r.status == "READY"
    assert r.graph["nodes"][0]["entity"] == "数据源连接池"
    assert any("唯一候选" in f for f in r.fixes)


def test_entity_not_found_blocked():
    r = C().compile({"nodes": [{"id": "a", "kind": "retrieve", "entity": "不存在实体"}]})
    assert r.status == "BLOCKED"
    assert any(i.code == "ENTITY_NOT_FOUND" for i in r.issues)
    assert r.graph is None


def test_entity_ambiguous_blocked():
    """多个候选绝不替用户挑。"""
    r = C().compile({"nodes": [{"id": "a", "kind": "retrieve", "entity": "数据源"}]})
    assert r.status == "BLOCKED"
    issue = next(i for i in r.issues if i.code == "ENTITY_AMBIGUOUS")
    assert "候选" in issue.message


def test_entity_resolved_in_nested_blocks():
    r = C().compile({"nodes": [
        {"id": "b", "kind": "branch", "condition": {"const": True},
         "then": [{"id": "t", "kind": "retrieve", "entity": "迁移方案配置"}]}]})
    assert r.status == "READY"
    assert r.graph["nodes"][0]["then"][0]["entity"] == "迁移方案配置"


def test_no_live_refs_is_warn_not_error():
    r = BusinessRequirementCompiler(None).compile(
        {"nodes": [{"id": "a", "kind": "retrieve", "entity": "任意"}]})
    assert r.status == "AMBIGUOUS"
    assert any(i.code == "NO_LIVE_REFS" for i in r.issues)


# ---------------------------------------------------------------- 归一化
def test_for_each_source_ref_normalized():
    """草稿常写 source:{ref:...}，归一成 list 并留痕。"""
    r = C().compile({"nodes": [
        {"id": "arr", "kind": "retrieve_array", "entity": "数据源配置信息"},
        {"id": "e", "kind": "for_each", "source": {"ref": "arr"}, "body": []}]})
    assert r.status == "READY"
    fe = r.graph["nodes"][1]
    assert fe["list"] == "arr"
    assert any("source.ref" in f for f in r.fixes)


def test_missing_id_gets_placeholder():
    r = C().compile({"nodes": [{"kind": "retrieve", "entity": "数据源配置信息"}]})
    assert r.graph["nodes"][0]["id"].startswith("retrieve_")
    assert any("补别名" in f for f in r.fixes)


# ---------------------------------------------------------------- 语义歧义
def test_other_scope_ambiguous():
    r = C().compile({"nodes": [{"id": "a", "kind": "retrieve", "entity": "数据源配置信息"}]},
                    text="把这个数据源停用，同时停用其他启用的数据源")
    assert r.status == "AMBIGUOUS"
    assert any(i.code == "EXCLUDE_SELF" for i in r.issues)


def test_modify_scope_ambiguous():
    r = C().compile({"nodes": [{"id": "a", "kind": "retrieve", "entity": "数据源配置信息"}]},
                    text="改成停用然后修改数据")
    assert any(i.code == "MODIFY_SCOPE" for i in r.issues)


def test_ambiguity_issue_carries_suggestion():
    r = C().compile({"nodes": [{"id": "a", "kind": "retrieve", "entity": "数据源配置信息"}]},
                    text="判断 jdbc 是否包含 mysql")
    issues = [i for i in r.issues if i.code in ("JUDGE_TARGET", "MATCH_PRECISION")]
    assert issues and all(i.suggestion for i in issues)


# ---------------------------------------------------------------- 业务陷阱自检
def test_write_on_loop_item_blocked():
    """G20 提前拦：写操作对象不能直引循环项。"""
    r = C().compile({"nodes": [
        {"id": "arr", "kind": "retrieve_array", "entity": "数据源配置信息"},
        {"id": "e", "kind": "for_each", "list": "arr", "body": [
            {"id": "upd", "kind": "change_entity", "entity": "数据源配置信息",
             "from_node": "e", "fields": {"enabled": False}}]}]})
    assert r.status == "BLOCKED"
    assert any(i.code == "WRITE_ON_LOOP_ITEM" for i in r.issues)


def test_correct_loop_chain_ready():
    """正确链路：循环项 → RETRIEVE → 写操作。"""
    r = C().compile({"nodes": [
        {"id": "arr", "kind": "retrieve_array", "entity": "数据源配置信息"},
        {"id": "e", "kind": "for_each", "list": "arr", "body": [
            {"id": "cur", "kind": "retrieve", "entity": "数据源配置信息",
             "by_id_from": "e", "from_field": "id"},
            {"id": "upd", "kind": "change_entity", "entity": "数据源配置信息",
             "from_node": "cur", "fields": {"enabled": False}}]}]})
    assert r.status == "READY", [i.to_dict() for i in r.issues]


def test_self_check_ignores_write_outside_loop():
    r = C().compile({"nodes": [
        {"id": "a", "kind": "retrieve", "entity": "数据源配置信息"},
        {"id": "u", "kind": "change_entity", "entity": "数据源配置信息",
         "from_node": "a", "fields": {"enabled": False}}]})
    assert r.status == "READY"


# ---------------------------------------------------------------- 结果契约
def test_result_to_dict_serializable():
    import json
    r = C().compile({"nodes": [{"id": "a", "kind": "retrieve", "entity": "数据源配置信息"}]})
    json.dumps(r.to_dict(), ensure_ascii=False)      # 不抛即通过
    assert r.ok is True


def test_blocked_never_returns_graph():
    """★ 一旦 BLOCKED，graph 必须是 None —— 不许"带着问题上路"。"""
    r = C().compile({"nodes": [{"id": "a", "kind": "teleport"}]})
    assert r.status == "BLOCKED" and r.graph is None


# ---------------------------------------------------------------- 字段真名解析
class FakeRefsWithModel(FakeRefs):
    ATTRS = {
        "数据源配置信息": {"enabled": {"dataType": "BOOLEAN", "caption": "启用"},
                        "name": {"dataType": "STRING", "caption": "名称"},
                        "priority": {"dataType": "INTEGER", "caption": "优先级"}},
        "迁移方案配置": {"planCode": {"dataType": "STRING", "caption": "方案编码"}},
    }

    def entity_model(self, app_id, app_name, *, label="", dto_full=""):
        if label not in self.ATTRS:
            return {"attributes": {}}
        return {"attributes": dict(self.ATTRS[label])}


def CM():
    return BusinessRequirementCompiler(FakeRefsWithModel())


def test_field_resolved_records_into_resolved():
    r = CM().compile({"nodes": [
        {"id": "a", "kind": "retrieve", "entity": "数据源配置信息",
         "cond_field": "name", "right": {"const": "x"}}]})
    assert r.status == "READY", [i.to_dict() for i in r.issues]
    assert "数据源配置信息.name" in r.resolved["fields"]


def test_unknown_field_blocked():
    r = CM().compile({"nodes": [
        {"id": "a", "kind": "retrieve", "entity": "数据源配置信息",
         "cond_field": "noSuchField"}]})
    assert r.status == "BLOCKED"
    assert any(i.code == "FIELD_NOT_FOUND" for i in r.issues)


def test_from_field_not_validated_against_entity():
    # from_field 是循环项元素字段（by_id_from 节点），不是本节点 entity 字段。
    # 修复前：from_field 被按 entity 归一化/校验，循环内
    # RETRIEVE(by_id_from=each, from_field=外键) 会误报 FIELD_NOT_FOUND
    # （外键属于源列表元素实体，不属于查询目标实体）。
    r = CM().compile({"nodes": [
        {"id": "ra", "kind": "retrieve_array", "entity": "迁移方案配置",
         "cond_field": "planCode", "right": {"const": "x"}},
        {"id": "each", "kind": "for_each", "list": "ra", "body": [
            {"id": "sup", "kind": "retrieve", "entity": "数据源配置信息",
             "by_id_from": "each", "from_field": "planCode"},
        ]}]})
    # planCode 是「迁移方案配置」（循环项元素）的字段，不是「数据源配置信息」（查询目标）的字段
    assert r.status == "READY", [i.to_dict() for i in r.issues]


def test_list_operation_fields_resolved_via_source():
    r = CM().compile({"nodes": [
        {"id": "ra", "kind": "retrieve_array", "entity": "数据源配置信息"},
        {"id": "g", "kind": "list_operation", "list_node": "ra", "op_type": "GROUP_AND_SUM",
         "group_by": ["name"], "count_fields": ["priority"]}]})
    assert r.status == "READY", [i.to_dict() for i in r.issues]
    assert "数据源配置信息.name" in r.resolved["fields"]
    assert "数据源配置信息.priority" in r.resolved["fields"]


def test_filter_expr_field_resolved_recursively():
    r = CM().compile({"nodes": [
        {"id": "ra", "kind": "retrieve_array", "entity": "数据源配置信息"},
        {"id": "f", "kind": "list_operation", "list_node": "ra", "op_type": "FILTER",
         "filter": {"expr": {"op": "GT",
                             "left": {"field": "priority"}, "right": {"const": 3}}}}]})
    assert r.status == "READY", [i.to_dict() for i in r.issues]
    assert "数据源配置信息.priority" in r.resolved["fields"]


def test_id_field_always_allowed():
    r = CM().compile({"nodes": [
        {"id": "a", "kind": "retrieve", "entity": "数据源配置信息", "by_field": "id"}]})
    assert r.status == "READY", [i.to_dict() for i in r.issues]


# ---------------------------------------------------------------- 归一化阶段（P7-E2E-1）
def test_original_draft_not_polluted():
    draft = {"nodes": [{"id": "a", "kind": "retrieve", "entity": "数据源配置信息",
                        "cond_field": "名称", "right": {"const": "x"}}]}
    r = CM().compile(draft)
    assert r.status == "READY", [i.to_dict() for i in r.issues]
    # 原始草稿原样保留（中文字段名 + 实体名都不被改）
    assert draft["nodes"][0]["cond_field"] == "名称"
    assert draft["nodes"][0]["entity"] == "数据源配置信息"


def test_field_label_normalized_to_real_name():
    draft = {"nodes": [{"id": "a", "kind": "retrieve", "entity": "数据源配置信息",
                        "cond_field": "名称", "right": {"const": "x"}}]}
    r = CM().compile(draft)
    # 归一化草稿：中文字段名回填成真名
    assert r.normalized_draft["nodes"][0]["cond_field"] == "name"
    # 逻辑图用的也是真名
    assert r.graph["nodes"][0]["cond_field"] == "name"
    # 映射记录 original label → 真名
    assert r.resolved["fields"]["数据源配置信息.名称"] == "name"


def test_field_already_real_name_unchanged():
    draft = {"nodes": [{"id": "a", "kind": "retrieve", "entity": "数据源配置信息",
                        "cond_field": "name", "right": {"const": "x"}}]}
    r = CM().compile(draft)
    assert r.resolved["fields"]["数据源配置信息.name"] == "name"
    assert r.normalized_draft["nodes"][0]["cond_field"] == "name"


def test_fields_dict_key_normalized():
    draft = {"nodes": [{"id": "c", "kind": "create_entity",
                        "entity": "数据源配置信息",
                        "fields": {"名称": {"const": "x"},
                                   "优先级": {"const": 3}}}]}
    r = CM().compile(draft)
    assert r.status == "READY", [i.to_dict() for i in r.issues]
    assert set(r.normalized_draft["nodes"][0]["fields"]) == {"name", "priority"}


def test_filter_expr_field_label_normalized():
    draft = {"nodes": [
        {"id": "ra", "kind": "retrieve_array", "entity": "数据源配置信息"},
        {"id": "f", "kind": "list_operation", "list_node": "ra", "op_type": "FILTER",
         "filter": {"expr": {"op": "GT", "left": {"field": "优先级"},
                             "right": {"const": 3}}}}]}
    r = CM().compile(draft)
    assert r.status == "READY", [i.to_dict() for i in r.issues]
    # expr 里字段回填成真名
    assert r.normalized_draft["nodes"][1]["filter"]["expr"]["left"]["field"] == "priority"


def test_conditions_array_field_normalized():
    """retrieve_array 多条件 conditions 数组里的中文 field 也要归一化。"""
    draft = {"nodes": [
        {"id": "ra", "kind": "retrieve_array", "entity": "数据源配置信息",
         "conditions": [
             {"field": "名称", "op": "EQ", "right": {"const": "x"}},
             {"field": "优先级", "op": "GT", "right": {"const": 3}}]}]}
    r = CM().compile(draft)
    assert r.status == "READY", [i.to_dict() for i in r.issues]
    conds = r.normalized_draft["nodes"][0]["conditions"]
    assert conds[0]["field"] == "name"
    assert conds[1]["field"] == "priority"
    assert "数据源配置信息.名称" in r.resolved["fields"]
    assert "数据源配置信息.优先级" in r.resolved["fields"]
