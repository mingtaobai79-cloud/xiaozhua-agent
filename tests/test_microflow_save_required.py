"""保存校验必填表（SAVE_REQUIRED_FIELDS）测试。

数据来源：2026-10-28 在真实编辑器点「保存并提交」，
前端逐节点 console.log `X 的所有必填属性=> [...]`。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from components.udc.microflow_constraints import (
    NODE_REQUIRED_FIELDS,
    SAVE_CONDITIONAL_FIELDS,
    SAVE_REQUIRED_FIELDS,
    UI_VS_SAVE_DIVERGENCE,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "scratch" / "node-full-evidence" / "REQUIRED-FROM-SAVE.json"


def test_save_table_covers_core_node_types():
    """至少覆盖 26 类运行时实测节点"""
    assert len(SAVE_REQUIRED_FIELDS) >= 26


def test_control_nodes_have_no_required():
    """控制节点无必填"""
    for a in ("START", "END", "BRANCH", "CONDITION", "BREAK"):
        assert SAVE_REQUIRED_FIELDS[a] == (), a


def test_convert_data_save_required():
    """CONVERT_DATA 保存校验要 3 个（与实测一致）"""
    assert set(SAVE_REQUIRED_FIELDS["CONVERT_DATA"]) == {"convertType", "selectParam", "title"}


def test_custom_error_save_required_is_position_mode():
    """CUSTOM_ERROR 保存并集是 POSITION 模式字段（不是 error）"""
    req = set(SAVE_REQUIRED_FIELDS["CUSTOM_ERROR"])
    assert req == {"sourceData", "selectParam", "attrType", "attrError"}
    assert "error" not in req


def test_map_operation_save_required_8_fields():
    """MAP_OPERATION 保存校验 8 个字段"""
    assert len(SAVE_REQUIRED_FIELDS["MAP_OPERATION"]) == 8
    assert "theKey" in SAVE_REQUIRED_FIELDS["MAP_OPERATION"]


def test_for_save_required():
    """FOR 保存校验 4 个（operator 不在内，有默认值）"""
    assert set(SAVE_REQUIRED_FIELDS["FOR"]) == {"forStart", "forEnd", "forStep", "targetName"}
    assert "operator" not in SAVE_REQUIRED_FIELDS["FOR"]


def test_sub_microflow_save_required():
    """SUB_MICROFLOW 保存校验要 mappingType/outputName（不止 mfService）"""
    assert set(SAVE_REQUIRED_FIELDS["SUB_MICROFLOW"]) == {"mfService", "mappingType", "outputName"}


def test_save_table_superset_or_equal_of_ui_table():
    """UI 表字段应在保存表里，除非是已登记的真实分歧"""
    problems = []
    for action, ui_fields in NODE_REQUIRED_FIELDS.items():
        if action not in SAVE_REQUIRED_FIELDS:
            continue
        save_fields = set(SAVE_REQUIRED_FIELDS[action])
        known = set(UI_VS_SAVE_DIVERGENCE.get(action, {}))
        missing = set(ui_fields) - save_fields - known
        if missing:
            problems.append((action, sorted(missing)))
    assert problems == [], "UI 必填未包含在保存校验中且未登记分歧：%s" % problems


def test_divergence_is_real():
    """登记的分歧必须确实存在（防止登记表变成垃圾桶）"""
    for action, div in UI_VS_SAVE_DIVERGENCE.items():
        ui = set(NODE_REQUIRED_FIELDS.get(action, ()))
        save = set(SAVE_REQUIRED_FIELDS.get(action, ()))
        for field, why in div.items():
            # 分歧 = UI 有但保存没有，或保存有但 UI 没有
            assert (field in ui) != (field in save), (
                "%s.%s 不是真分歧（UI=%s save=%s）" % (
                    action, field, field in ui, field in save))
            assert why


def test_conditional_fields_documented():
    """条件必填字段必须有说明"""
    for action, cond in SAVE_CONDITIONAL_FIELDS.items():
        assert action in SAVE_REQUIRED_FIELDS, action
        for field, why in cond.items():
            assert field in SAVE_REQUIRED_FIELDS[action], (action, field)
            assert why, (action, field)


def test_no_single_char_fields():
    """防止单元素元组写成字符串（("title") 会迭代成字符）"""
    for action, fields in SAVE_REQUIRED_FIELDS.items():
        assert all(len(f) > 1 for f in fields), action
    for action, fields in NODE_REQUIRED_FIELDS.items():
        assert all(len(f) > 1 for f in fields), action


@pytest.mark.skipif(not EVIDENCE.exists(), reason="运行时证据缺失")
def test_matches_runtime_evidence():
    """与真实保存校验抓到的清单逐项一致"""
    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))["extracted"]
    diffs = []
    for action, fields in ev.items():
        mine = SAVE_REQUIRED_FIELDS.get(action)
        if mine is None:
            diffs.append((action, "缺失"))
            continue
        if set(mine) != set(fields):
            diffs.append((action, sorted(set(fields) - set(mine)),
                          sorted(set(mine) - set(fields))))
    assert diffs == [], "与运行时证据不一致：%s" % diffs
