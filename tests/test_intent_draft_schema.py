"""IntentDraft schema 与宿主 LLM Prompt 的契约测试。

锁三件事：
1. NODE_SPECS 与执行器 _STEP_KINDS 双向一致（单一事实源，不许漂移）。
2. schema 能导出 JSON Schema / Markdown，且覆盖全部 kind。
3. validate() 拦非法草稿、放过合法草稿；prompt 能渲染。

（对齐 P7-E2E-2 的「LLM 生成草稿 → 业务结果」闭环。）
"""
import pytest

from components.construction.intent_draft_schema import (
    NODE_SPECS, VALUE_SLOTS, EXPRESSION_FORMS,
    to_json_schema, render_markdown, validate,
)
from components.construction.logic_graph import _STEP_KINDS
from components.construction.host_llm_prompt import (
    SYSTEM_PROMPT, render, _CHEATSHEET_KINDS,
)


def test_node_specs_cover_all_kinds():
    """schema 的 kind 集合 == 执行器的 _STEP_KINDS（双向，不漏不重）。"""
    assert set(NODE_SPECS) == set(_STEP_KINDS), (
        "NODE_SPECS 与 _STEP_KINDS 漂移：\n"
        "  缺 = %s\n  多 = %s" % (
            sorted(set(_STEP_KINDS) - set(NODE_SPECS)),
            sorted(set(NODE_SPECS) - set(_STEP_KINDS))))


def test_every_kind_has_required_doc():
    """每个 kind 都要有 required/optional/doc（否则 prompt/文档是空的）。"""
    for kind, spec in NODE_SPECS.items():
        assert isinstance(spec.get("required"), list), kind
        assert isinstance(spec.get("optional"), list), kind
        assert spec.get("doc"), "kind %s 缺 doc" % kind


def test_json_schema_export_covers_all_kinds():
    js = to_json_schema()
    anyof = js["properties"]["nodes"]["items"]["oneOf"]
    kinds_in_schema = {o["properties"]["kind"]["const"] for o in anyof}
    assert kinds_in_schema == set(_STEP_KINDS)


def test_render_markdown_mentions_all_kinds():
    md = render_markdown()
    for kind in _STEP_KINDS:
        assert "### `%s`" % kind in md


def test_value_slots_and_expression_forms_present():
    assert set(VALUE_SLOTS) >= {"const", "field", "input"}
    # 表达式十种形态（含 item，别漏 P3.1 加的）
    assert set(EXPRESSION_FORMS) >= {
        "const", "op", "logic", "arith", "fn", "cond", "field", "item", "input", "sys"}


# 一个合法草稿（P7-E2E-2 迁移质量汇总的最小版）
GOOD_DRAFT = {
    "nodes": [
        {"id": "b1", "kind": "create_entity", "entity": "迁移任务批次账本",
         "fields": {"任务ID": {"const": "MIG-1"}, "失败行数": {"const": 3}}},
        {"id": "ra", "kind": "retrieve_array", "entity": "迁移任务批次账本",
         "cond_field": "任务ID", "right": {"const": "MIG-1"}},
        {"id": "sum", "kind": "list_operation", "list_node": "ra",
         "op_type": "SUM", "count_fields": ["失败行数"]},
        {"id": "wr", "kind": "create_entity", "entity": "迁移任务批次账本",
         "fields": {"任务ID": {"const": "MIG-1-SUM"}, "失败行数": {"field": "sum"}}},
    ],
}


def test_validate_accepts_good_draft():
    """合法草稿不报错（结构级；真名归一化由编译器做，不在这里）。"""
    assert validate(GOOD_DRAFT) == []


def test_validate_blocks_bad_kind():
    draft = {"nodes": [{"id": "x", "kind": "not_a_real_kind"}]}
    probs = validate(draft)
    assert any("kind 非法" in p for p in probs)


def test_validate_blocks_missing_required():
    draft = {"nodes": [{"id": "ce", "kind": "create_entity"}]}  # 缺 entity/fields
    probs = validate(draft)
    assert any("缺必填字段" in p for p in probs)


def test_validate_blocks_non_dict():
    assert validate("not a dict") != []
    assert validate({"nodes": "not a list"}) != []


def test_prompt_renders_with_requirement_and_entities():
    entities = [{"caption": "迁移任务批次账本", "fields": [
        {"name": "taskId", "caption": "任务ID", "dataType": "STRING"},
        {"name": "failedRows", "caption": "失败行数", "dataType": "BIGINTEGER"},
    ]}]
    system, user = render(requirement="统计失败行数总和", entities=entities)
    assert "IntentDraft" in system
    assert "统计失败行数总和" in user
    assert "迁移任务批次账本" in user
    assert "任务ID" in user


def test_prompt_cheatsheet_kinds_are_real():
    """prompt 速查里的 kind 必须都是真实存在的（不能写到一半的别名）。"""
    assert set(_CHEATSHEET_KINDS) <= set(_STEP_KINDS)
    # 核心写/读/聚合/控制流都要在速查里
    assert {"create_entity", "retrieve_array", "list_operation", "branch",
            "for_each"} <= set(_CHEATSHEET_KINDS)


def test_system_prompt_states_hard_boundaries():
    """system prompt 必须写清三条硬边界（否则 LLM 会越位）。"""
    assert "不产平台节点 JSON" in SYSTEM_PROMPT or "绝不产平台" in SYSTEM_PROMPT
    assert "绝不猜" in SYSTEM_PROMPT
    assert "跨环境 id" in SYSTEM_PROMPT
