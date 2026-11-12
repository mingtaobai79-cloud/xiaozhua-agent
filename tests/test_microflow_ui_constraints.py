"""微流程节点 UI 层约束校验器测试（2026-10-28，22 类节点实测）。

覆盖：
1. 正向：真实后端 dataSchema（23 类 27 节点）全部通过
2. 反向：14 项注入缺陷必须被抓
3. 值域常量与前端 bundle 定义一致
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from components.udc.microflow_ui_constraints import (
    CONVERT_TYPES,
    CONVERT_TYPES_WITH_REGEX,
    CUSTOM_ERROR_FIELDS_BY_TYPE,
    DATA_MAPPING_MODES,
    DATA_MAPPING_REQUIRED,
    DATA_MAPPING_TARGET_TYPES,
    EVENT_SELECT_FIELD,
    EVENT_TYPES,
    FOR_OPERATORS,
    MAP_OPERATION_FIELDS_BY_TYPE,
    MAP_OPERATION_TYPES,
    MAP_PARAM_TYPES,
    MESSAGE_TYPES,
    ROOT_LEVEL_NODE_PANEL,
    SPLIT_SYMBOLS,
    validate_convert_data,
    validate_custom_error,
    validate_data_mapping,
    validate_for,
    validate_map_operation,
    validate_node_ui,
    validate_publish_business_event,
    validate_schema_ui,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / 'scratch' / 'ui-constraint-evidence' / 'backend-schema-full.json'


# ============================================================================
# 值域常量（与前端 bundle 定义一致性）
# ============================================================================

def test_for_operators_match_bundle():
    """FOR operator 4 值（bundle executionConditions）"""
    assert FOR_OPERATORS == ("<=", "<", ">=", ">")


def test_map_operation_types_match_bundle():
    """MAP_OPERATION 4 值（bundle eD）"""
    assert MAP_OPERATION_TYPES == ("GET", "PUT", "REMOVE", "KEY_SET")
    assert set(MAP_OPERATION_FIELDS_BY_TYPE) == set(MAP_OPERATION_TYPES)


def test_map_param_types_match_backend_enum():
    """映射值类型 = 后端 ParamTypeEnum 8 种（CFR 反编译 cfr-r31b 权威）"""
    from components.udc.microflow_ui_constraints import (
        PARAM_TYPE_ENUM,
        UI_PARAM_TYPES,
    )
    assert MAP_PARAM_TYPES == ("BASIC", "ENTITY_OBJECT", "DEFAULT_OBJECT", "ENUM",
                               "MAP", "METADATA", "MESSAGE", "OTHER")
    assert set(PARAM_TYPE_ENUM) == set(MAP_PARAM_TYPES)
    # 后端 code 连续 0..7
    assert sorted(v["code"] for v in PARAM_TYPE_ENUM.values()) == list(range(8))
    # 前端「选择数据」radio 7 类，不含 MAP
    assert set(UI_PARAM_TYPES) == set(MAP_PARAM_TYPES) - {"MAP"}


def test_convert_types_match_bundle():
    """类型转换 9 值（bundle convertTypeSelector）"""
    assert len(CONVERT_TYPES) == 9
    assert CONVERT_TYPES_WITH_REGEX == ("Split",)
    assert len(SPLIT_SYMBOLS) == 10


def test_custom_error_modes_match_bundle():
    """自定义错误 2 模式（bundle errorType radio）"""
    assert set(CUSTOM_ERROR_FIELDS_BY_TYPE) == {"GLOBAL", "POSITION"}
    assert CUSTOM_ERROR_FIELDS_BY_TYPE["GLOBAL"] == ("error",)
    assert "attrError" in CUSTOM_ERROR_FIELDS_BY_TYPE["POSITION"]


def test_data_mapping_target_types_match_bundle():
    """数据转换目标类型 2 值 + 映射方式 2 值"""
    assert DATA_MAPPING_TARGET_TYPES == ("ENTITY", "DTO")
    assert DATA_MAPPING_MODES == ("值拷贝", "常量")
    assert len(DATA_MAPPING_REQUIRED) == 6


def test_event_types_match_bundle():
    """事件投递：2 种 eventType + 2 种 messageType + 两种字段名"""
    assert EVENT_TYPES == ("AMONG_APP", "IN_APP")
    assert MESSAGE_TYPES == ("DEFAULT", "DELAY")
    assert EVENT_SELECT_FIELD == {"AMONG_APP": "selectMq", "IN_APP": "selectEvent"}


def test_root_panel_excludes_break():
    """根级面板 24 项不含「跳出循环」（只能在循环体内添加）"""
    assert len(ROOT_LEVEL_NODE_PANEL) == 24
    assert "跳出循环" not in ROOT_LEVEL_NODE_PANEL


# ============================================================================
# 正向：真实后端 dataSchema
# ============================================================================

@pytest.mark.skipif(not SCHEMA_PATH.exists(), reason="真实 schema 证据缺失")
def test_real_schema_passes_ui_validation():
    """23 类 27 节点的真实流程必须全部通过 UI 校验"""
    schema = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    problems = validate_schema_ui(schema)
    assert problems == [], "真实数据不应有问题：%s" % problems[:5]


@pytest.mark.skipif(not SCHEMA_PATH.exists(), reason="真实 schema 证据缺失")
def test_real_schema_covers_23_actions():
    """证据文件应覆盖 23 类 actionType"""
    schema = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    seen = set()

    def walk(nodes):
        for n in nodes or []:
            seen.add(n.get('actionType') or n.get('type'))
            walk(n.get('nodes'))
            for c in n.get('conditions') or []:
                walk(c.get('nodes'))

    walk(schema.get('nodes'))
    assert len(seen) == 23, "期望 23 类，实际 %d: %s" % (len(seen), sorted(seen))


# ============================================================================
# 反向：注入缺陷必须被抓
# ============================================================================

def test_convert_data_missing_value_key():
    """convertType 只有 key 没有 value（UI 选中形态）→ 必须报错"""
    node = {'actionType': 'CONVERT_DATA',
            'convertType': {'key': 'BasicData2String', 'dataType': 'String'},
            'selectParam': {'name': 'x'}, 'title': 't',
            'output': {'dataType': 'String'}}
    problems = validate_convert_data(node)
    assert problems
    assert 'value' in problems[0]


def test_convert_data_regex_only_for_split():
    """非 Split 带 regex → 必须报错"""
    node = {'actionType': 'CONVERT_DATA',
            'convertType': {'value': 'BasicData2String', 'key': 'BasicData2String'},
            'selectParam': {'name': 'x'}, 'title': 't', 'regex': 'COMMA',
            'output': {'dataType': 'String'}}
    assert validate_convert_data(node)


def test_convert_data_split_requires_regex():
    """Split 缺 regex → 必须报错"""
    node = {'actionType': 'CONVERT_DATA',
            'convertType': {'value': 'Split', 'key': 'Split'},
            'selectParam': {'name': 'x'}, 'title': 't',
            'output': {'dataType': 'String'}}
    assert validate_convert_data(node)


def test_convert_data_output_datatype_casing():
    """output.dataType 大小写不敏感匹配语料值（保存态 STRING / 回读态 String 都合法）"""
    node = {'actionType': 'CONVERT_DATA',
            'convertType': {'value': 'BasicData2String', 'key': 'BasicData2String'},
            'selectParam': {'name': 'x'}, 'title': 't',
            'output': {'dataType': 'STRING'}}
    assert not validate_convert_data(node)
    node2 = {'actionType': 'CONVERT_DATA',
             'convertType': {'value': 'BasicData2String', 'key': 'BasicData2String'},
             'selectParam': {'name': 'x'}, 'title': 't',
             'output': {'dataType': 'String'}}       # 回读态 casing
    assert not validate_convert_data(node2)
    node3 = {'actionType': 'CONVERT_DATA',
             'convertType': {'value': 'BasicData2String', 'key': 'BasicData2String'},
             'selectParam': {'name': 'x'}, 'title': 't',
             'output': {'dataType': 'BIGINTEGER'}}   # 真错
    assert validate_convert_data(node3)


def test_custom_error_position_missing_attr_error():
    """POSITION 缺 attrError → 必须报错"""
    node = {'actionType': 'CUSTOM_ERROR', 'errorType': 'POSITION',
            'sourceData': {'a': 1}, 'selectParam': {'a': 1}, 'attrType': [{'a': 1}]}
    assert validate_custom_error(node)


def test_custom_error_global_leftover_position_fields():
    """GLOBAL 残留 POSITION 字段 → 必须报错"""
    node = {'actionType': 'CUSTOM_ERROR', 'errorType': 'GLOBAL',
            'error': {'type': 'Simple', 'simple': 'x'}, 'attrType': [{'a': 1}]}
    assert validate_custom_error(node)


def test_data_mapping_mapping_mode_domain():
    """mappingMode 越界 → 必须报错"""
    node = {'actionType': 'DATA_MAPPING', 'targetType': 'ENTITY',
            'selectParam': {'a': 1}, 'app': {'a': 1}, 'structure': {'a': 1},
            'mappingRule': {'mappingRows': [{'targetField': {'a': 1},
                                             'mappingMode': 'FieldCopy'}]},
            'title': 't', 'output': {'type': 'ARRAY'}}
    problems = validate_data_mapping(node)
    assert problems and 'mappingMode' in problems[0]


def test_data_mapping_reference_requires_value():
    """REFERENCE 缺 value.reference → 必须报错"""
    node = {'actionType': 'DATA_MAPPING', 'targetType': 'ENTITY',
            'selectParam': {'a': 1}, 'app': {'a': 1}, 'structure': {'a': 1},
            'mappingRule': {'mappingRows': [{'targetField': {'a': 1},
                                             'mappingMode': 'REFERENCE'}]},
            'title': 't', 'output': {'type': 'ARRAY'}}
    problems = validate_data_mapping(node)
    assert problems and 'reference' in problems[0]


def test_data_mapping_output_type_must_be_array():
    """output.type 必须是 ARRAY（产出列表）"""
    node = {'actionType': 'DATA_MAPPING', 'targetType': 'ENTITY',
            'selectParam': {'a': 1}, 'app': {'a': 1}, 'structure': {'a': 1},
            'mappingRule': {'uuid': 'u', 'subobjects': [],
                            'mappingRows': [{'targetField': {'a': 1},
                                             'mappingMode': 'REFERENCE',
                                             'value': {'reference': {'a': 1}}}]},
            'title': 't', 'output': {'type': 'OBJECT'}}
    problems = validate_data_mapping(node)
    assert problems and 'ARRAY' in problems[0]


def test_event_among_app_requires_select_mq():
    """AMONG_APP 必须用 selectMq，不能用 selectEvent"""
    node = {'actionType': 'PUBLISH_BUSINESS_EVENT', 'eventType': 'AMONG_APP',
            'selectEvent': {'a': 1}}
    assert validate_publish_business_event(node)


def test_event_select_mq_requires_content_dto():
    """selectMq 缺 contentDto → 必须报错"""
    node = {'actionType': 'PUBLISH_BUSINESS_EVENT', 'eventType': 'AMONG_APP',
            'selectMq': {'fullName': 'x', 'caption': 'y'}}
    problems = validate_publish_business_event(node)
    assert problems and 'contentDto' in problems[0]


def test_event_delay_requires_execute_time():
    """DELAY 缺 executeTime → 必须报错"""
    node = {'actionType': 'PUBLISH_BUSINESS_EVENT', 'eventType': 'AMONG_APP',
            'messageType': 'DELAY',
            'selectMq': {'fullName': 'x', 'contentDto': {'a': 1}}}
    problems = validate_publish_business_event(node)
    assert problems and 'executeTime' in problems[0]


def test_break_outside_loop_rejected():
    """BREAK 在根级 → 必须报错"""
    node = {'actionType': 'BREAK', 'type': 'BREAK'}
    problems = validate_node_ui(node, [])
    assert problems and '循环体' in problems[0]


def test_break_inside_loop_allowed():
    """BREAK 在 FOR_EACH 内 → 通过"""
    node = {'actionType': 'BREAK', 'type': 'BREAK'}
    assert validate_node_ui(node, ['FOR_EACH']) == []


def test_activity_node_type_must_be_activity(monkeypatch):
    import sys
    from components.udc.microflow_constraints import validate_node_fields
    with monkeypatch.context() as patch:
        patch.setitem(sys.modules, 'components.udc.microflow_ui_constraints', None)
        errors = validate_node_fields('NONEXISTENT_ACTION', {'type': 'WRONG', 'actionType': 'NONEXISTENT_ACTION'})
        assert any('UNVERIFIED' in error for error in errors)

    """活动节点 type 必须是 ACTIVITY"""
    node = {'actionType': 'CREATE_ENTITY', 'type': 'CREATE_ENTITY',
            'app': {'a': 1}, 'structure': {'a': 1}, 'mappingType': 'attrs',
            'value': {'a': 1}, 'title': 't'}
    problems = validate_node_ui(node, [])
    assert problems and 'ACTIVITY' in problems[0]


def test_map_operation_get_requires_the_key():
    """GET 缺 theKey → 必须报错"""
    node = {'actionType': 'MAP_OPERATION', 'operationType': 'GET',
            'selectMap': {'a': 1}, 'paramType': 'BASIC', 'basic': {'key': 'STRING'},
            'title': 't'}
    assert validate_map_operation(node)


def test_map_operation_put_rejects_the_key():
    """PUT 带 theKey → 必须报错"""
    node = {'actionType': 'MAP_OPERATION', 'operationType': 'PUT',
            'selectMap': {'a': 1}, 'entries': [{'k': 1}], 'theKey': {'simple': 'x'}}
    assert validate_map_operation(node)


def test_for_operator_value_domain():
    """FOR operator 越界 → 必须报错"""
    node = {'actionType': 'FOR', 'operator': '==', 'forStep': 1}
    assert validate_for(node)


def test_for_step_must_be_int():
    """forStep 非整数 → 必须报错"""
    node = {'actionType': 'FOR', 'operator': '<=', 'forStep': '1'}
    assert validate_for(node)
