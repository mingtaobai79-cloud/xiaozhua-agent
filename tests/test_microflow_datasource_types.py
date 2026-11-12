"""数据源类型（paramType）与后端 ParamTypeEnum 适配测试。

权威来源：CFR 反编译 cfr-r31b/com/seeyon/udc/enums/microflow/ParamTypeEnum.java
"""
from __future__ import annotations

import pytest

from components.udc.microflow_ui_constraints import (
    MAP_PARAM_TYPES,
    MAP_PARAM_TYPE_LABELS,
    PARAM_TYPE_ENUM,
    PARAM_TYPE_REQUIRED_FIELDS,
    UI_PARAM_TYPES,
)

# 后端权威定义（逐字来自 CFR 反编译）
BACKEND_ENUM = {
    "DEFAULT_OBJECT": 0,
    "BASIC": 1,
    "ENTITY_OBJECT": 2,
    "ENUM": 3,
    "MAP": 4,
    "METADATA": 5,
    "MESSAGE": 6,
    "OTHER": 7,
}

# needFullName() 只对这三种为 true
NEED_FULL_NAME = {"DEFAULT_OBJECT", "ENTITY_OBJECT", "ENUM"}


def test_backend_enum_has_8_values():
    """后端 ParamTypeEnum 是 8 种，不是 5 种"""
    assert len(PARAM_TYPE_ENUM) == 8
    assert set(PARAM_TYPE_ENUM) == set(BACKEND_ENUM)


def test_codes_match_backend():
    """code 与后端逐字一致且连续 0..7"""
    for name, code in BACKEND_ENUM.items():
        assert PARAM_TYPE_ENUM[name]["code"] == code, name
    assert sorted(v["code"] for v in PARAM_TYPE_ENUM.values()) == list(range(8))


def test_need_full_name_matches_backend():
    """needFullName() 只对 DEFAULT_OBJECT/ENTITY_OBJECT/ENUM 为 true"""
    actual = {k for k, v in PARAM_TYPE_ENUM.items() if v["need_full_name"]}
    assert actual == NEED_FULL_NAME


def test_map_param_types_is_backend_enum():
    """MAP_PARAM_TYPES 必须等于后端 8 种（不是旧的 5 种）"""
    assert set(MAP_PARAM_TYPES) == set(BACKEND_ENUM)
    # 明确断言历史漏掉的三种已在值域内
    for missing_before in ("METADATA", "MESSAGE", "OTHER"):
        assert missing_before in MAP_PARAM_TYPES, missing_before


def test_ui_param_types_excludes_map():
    """前端「选择数据」radio 只给 7 类，唯一缺口是 MAP"""
    assert set(UI_PARAM_TYPES) == set(BACKEND_ENUM) - {"MAP"}
    assert "MAP" not in UI_PARAM_TYPES


def test_labels_cover_all_types():
    """8 种都有中文标签"""
    for name in BACKEND_ENUM:
        assert name in MAP_PARAM_TYPE_LABELS, name
        assert MAP_PARAM_TYPE_LABELS[name]


def test_required_fields_cover_all_types():
    """每种 paramType 都有后端必需字段定义"""
    for name in BACKEND_ENUM:
        assert name in PARAM_TYPE_REQUIRED_FIELDS, name


def test_other_only_needs_other_type():
    """OTHER 走独立分支，只认 otherType"""
    assert PARAM_TYPE_REQUIRED_FIELDS["OTHER"] == ("otherType",)


def test_need_full_name_types_need_app_and_structure():
    """需要 fullName 的三种必须带 app + structure"""
    for name in NEED_FULL_NAME:
        req = PARAM_TYPE_REQUIRED_FIELDS[name]
        assert "app" in req, name
        assert "structure" in req, name


def test_basic_only_needs_data_type():
    """BASIC 只需 dataType"""
    assert PARAM_TYPE_REQUIRED_FIELDS["BASIC"] == ("dataType",)


def test_metadata_needs_meta_data_type():
    """METADATA 需要 metaDataType（PAGE 型还要 guid，实体型还要 entityFullName）"""
    assert "metaDataType" in PARAM_TYPE_REQUIRED_FIELDS["METADATA"]


def test_enum_needs_value():
    """ENUM 需要 value，且后端会校验 javaType 与结构一致"""
    assert "value" in PARAM_TYPE_REQUIRED_FIELDS["ENUM"]


def test_default_object_needs_mapping_type():
    """DEFAULT_OBJECT 走 DTO 分支，需要 mappingType 决定 value/mapping"""
    assert "mappingType" in PARAM_TYPE_REQUIRED_FIELDS["DEFAULT_OBJECT"]


def test_flow_param_data_type_enum_is_separate():
    """流程级入参只有 Entity/Dto 两种，别和节点级 paramType 混用"""
    from components.udc.microflow_constraints import TRIGGER_PARAM_TYPES
    # 流程级是 4 种触发类型
    assert TRIGGER_PARAM_TYPES == ("NONE", "BASIC", "ENTITY_OBJECT", "DEFAULT_OBJECT")
    # 节点级是 8 种，两者不同
    assert len(TRIGGER_PARAM_TYPES) != len(BACKEND_ENUM)
