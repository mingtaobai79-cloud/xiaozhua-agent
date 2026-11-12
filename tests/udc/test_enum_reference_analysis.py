"""枚举引用分析器 —— 把 2026-10-20 踩过的坑全部钉死。

踩过的坑（每个都对应本文件里的一项测试）：
  1. 载体查错表：页面 schema 在 udc_page_schema，不在 udc_page_info
     → 误判「页面 0 命中」，差点把 363 个有引用的枚举全删
  2. 泛化子串匹配：code="bool" 会命中 "boolean"
     → 必须只认 ctpEnumInfo 块 / enumId-enumCode 字段
  3. 漏判引用方有效性：引用方自身 is_deleted=1 时不算活引用
     → 第一版还漏 SELECT is_deleted 字段，把 31 条已删资源误判成活引用
  4. 没有阳性对照：分析方法有缺口时，"无引用"结论不可信却照样下结论
  5. 没有阴性对照：子串误判无从发现
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.setting.enum_reference_analysis import (
    classify, enum_ref_values)


# ---------------------------------------------------------------- 值抽取

def test_extracts_ctp_enum_info_id_and_code():
    """ctpEnumInfo 是权威载体，必须抽出 id 与 code。"""
    blob = ('[{"label":"业务类型","ctpEnumInfo":{"id":"4052178930695160713",'
            '"caption":"业务类型","code":"business_type","appId":"8704",'
            '"CTPENUM":{"fullName":"business_type","id":"4052178930695160713"}}} ]')
    vals = enum_ref_values(blob)
    assert "4052178930695160713" in vals
    assert "business_type" in vals


def test_extracts_enum_id_code_fields():
    """微流程里常见 enumId / enumCode 字段对。"""
    blob = '{"enumId":"123","enumCode":"SyncMode"}'
    vals = enum_ref_values(blob)
    assert "123" in vals and "SyncMode" in vals


def test_does_not_match_arbitrary_substring():
    """阴性对照：code=bool 不应命中 boolean 这类无关词。"""
    blob = '{"paramName":"boolean","label":"是否"}'
    vals = enum_ref_values(blob)
    assert "bool" not in vals, f"不得做泛化子串匹配: {vals}"


def test_ignores_plain_code_field_without_enum_context():
    """普通 "code" 字段（控件编码）不算枚举引用。"""
    blob = '{"code":"canshumingcheng1","label":"合同档案ID"}'
    vals = enum_ref_values(blob)
    assert "canshumingcheng1" not in vals


# ---------------------------------------------------------------- 归类

def _enums():
    return [
        {"id": "1", "code": "codeType", "is_delete": 0},
        {"id": "2", "code": "business_type", "is_delete": 0},
        {"id": "3", "code": "unusedEnum", "is_delete": 0},
    ]


def test_live_reference_keeps_enum():
    """引用方有效 → 枚举必须保留。"""
    blob = '{"ctpEnumInfo":{"id":"1","code":"codeType"}}'
    rep = classify(_enums(), [("udc_page_schema", "p1", True, blob)],
                   app_id="app1", control_codes=["codeType"], control_total=1)
    assert rep.live_referenced.get("1"), "codeType 有活引用，必须在 keep 里"
    assert "1" in rep.keep_ids
    assert "1" not in rep.deletable_ids


def test_dead_reference_is_not_live():
    """引用方已删（is_deleted=1）→ 不算活引用，但要被记录。"""
    blob = '{"ctpEnumInfo":{"id":"2","code":"business_type"}}'
    rep = classify(_enums(), [("udc_resource", "r1", False, blob)],
                   app_id="app1")
    assert "2" not in rep.live_referenced, "已删的引用方不构成活引用"
    assert "2" in rep.dead_referenced, "死引用要留档以便审计"


def test_unreferenced_is_deletable():
    """没有任何引用时，全部枚举都可删。"""
    rep = classify(_enums(), [], app_id="app1")
    assert "3" in rep.deletable_ids
    assert rep.deletable_ids == {"1", "2", "3"}
    assert rep.keep_ids == set()


def test_deletable_excludes_referenced():
    """有活引用的枚举必须从可删集合里排除。"""
    blob = '{"ctpEnumInfo":{"id":"1","code":"codeType"}}'
    rep = classify(_enums(), [("udc_page_schema", "p1", True, blob)], app_id="app1")
    assert "1" not in rep.deletable_ids
    assert "3" in rep.deletable_ids


def test_matching_by_enum_id_not_only_code():
    """引用方只给了 id（没给 code）也要能匹配上。"""
    blob = '{"ctpEnumInfo":{"id":"1"}}'
    rep = classify(_enums(), [("udc_page_schema", "p1", True, blob)], app_id="app1")
    assert "1" in rep.live_referenced


# ---------------------------------------------------------------- 对照门

def test_positive_control_failure_marks_method_invalid():
    """阳性对照检不出 → 方法无效，结论不可信（必须让 method_valid=False）。"""
    rep = classify(_enums(), [], app_id="app1",
                   control_codes=["codeType"], control_total=1)
    assert rep.method_valid is False, "对照失败必须标方法无效"


def test_negative_control_failure_marks_method_invalid():
    """阴性对照命中 → 方法有子串误判风险，标无效。"""
    blob = '{"ctpEnumInfo":{"id":"1","code":"ZZZ_NOT_EXIST"}}'
    rep = classify(_enums(), [("udc_page_schema", "p1", True, blob)], app_id="app1",
                   control_codes=["codeType"], control_total=1,
                   negative_codes=["ZZZ_NOT_EXIST"])
    assert rep.method_valid is False


def test_method_valid_when_both_controls_pass():
    blob = '{"ctpEnumInfo":{"id":"1","code":"codeType"}}'
    rep = classify(_enums(), [("udc_page_schema", "p1", True, blob)], app_id="app1",
                   control_codes=["codeType"], control_total=1,
                   negative_codes=["ZZZ_NOT_EXIST"])
    assert rep.method_valid is True


def test_summary_reports_key_numbers():
    rep = classify(_enums(), [], app_id="app1")
    s = rep.summary()
    assert s["total_enums"] == 3
    assert s["app_id"] == "app1"
    assert "method_valid" in s
