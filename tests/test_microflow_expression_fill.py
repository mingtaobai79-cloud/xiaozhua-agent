"""expression_fill 的契约测试（不连浏览器）。"""
from __future__ import annotations

import pytest

from components.udc.microflow.expression_fill import (
    NUMERIC_TYPES,
    STRING_TYPES,
    SUPPORTED_RESULT_TYPES,
    VALUE_TYPES,
    available_vars,
    build_expression_dto,
    iter_value_slots,
    norm_type,
    pick_variable,
    slot_want_type,
    walk_ordered,
)


# ---------------------------------------------------------------- 类型归一化

def test_norm_type_lowercase_string():
    """★ 后端存在 String（小写 s），必须归一到 STRING

    不归一会导致「明明有 STRING 变量却匹配不到」，实测踩过。
    """
    assert norm_type('String') == 'STRING'
    assert norm_type('STRING') == 'STRING'
    assert norm_type('string') == 'STRING'


def test_norm_type_long_is_biginteger():
    """Long 与 BIGINTEGER 是同一概念两种写法"""
    assert norm_type('Long') == 'BIGINTEGER'
    assert norm_type('LONG') == 'BIGINTEGER'
    assert norm_type('BIGINTEGER') == 'BIGINTEGER'


def test_norm_type_object_and_dto():
    assert norm_type('Object') == 'DTO'
    assert norm_type('DTO') == 'DTO'
    assert norm_type('dto') == 'DTO'


def test_norm_type_empty_defaults_string():
    assert norm_type(None) == 'STRING'
    assert norm_type('') == 'STRING'


# ---------------------------------------------------------------- 值域

def test_supported_result_types_has_15_and_excludes_object():
    """★ resultTypeInfo 值域 15 个，OBJECT 不在其中（用了就 FORMULA_6003）"""
    assert len(SUPPORTED_RESULT_TYPES) == 15
    assert 'OBJECT' not in SUPPORTED_RESULT_TYPES
    assert 'OBJECTS' not in SUPPORTED_RESULT_TYPES
    for t in ('INTEGER', 'STRING', 'BOOLEAN', 'DATETIME', 'ENTITY'):
        assert t in SUPPORTED_RESULT_TYPES


def test_value_types_cover_three_forms():
    assert set(VALUE_TYPES) == {'Simple', 'SelectParam', 'Expression'}


# ---------------------------------------------------------------- 槽位遍历

def test_iter_value_slots_finds_nested_attrs():
    node = {
        'nodeId': 'SUB_MICROFLOW_x',
        'attrs': [{'value': {'type': 'Simple', 'simple': 0, 'desc': 0},
                   'attrType': {'name': 'days'}}],
    }
    slots = list(iter_value_slots(node))
    assert len(slots) == 1
    assert slots[0][0] == 'attrs[0].value'


def test_iter_value_slots_skips_output_input_mfService():
    """output/input/mfService 里的 type 字段不是值包装，不能误判"""
    node = {
        'output': {'type': 'OBJECT', 'name': '_X', 'dataType': 'DTO'},
        'input': {'type': 'OBJECT'},
        'mfService': {'type': 'OBJECT'},
        'value': {'type': 'Simple', 'simple': 1},
    }
    slots = list(iter_value_slots(node))
    assert [p for p, _ in slots] == ['value']


def test_iter_value_slots_handles_entries():
    node = {'entries': [{'key': {'type': 'Simple', 'simple': 'k1'},
                         'value': {'type': 'Simple', 'simple': 'v1'}}]}
    paths = [p for p, _ in iter_value_slots(node)]
    assert paths == ['entries[0].key', 'entries[0].value']


def test_iter_value_slots_ignores_expression_already():
    node = {'value': {'type': 'Expression',
                      'expression': {'title': 'x', 'schema': '{}'}}}
    assert list(iter_value_slots(node)) == []


# ---------------------------------------------------------------- 期望类型

def test_slot_want_type_from_simple_int():
    assert slot_want_type({'type': 'Simple', 'simple': 0}) == 'INTEGER'


def test_slot_want_type_from_simple_bool():
    assert slot_want_type({'type': 'Simple', 'simple': True}) == 'BOOLEAN'


def test_slot_want_type_from_simple_str():
    assert slot_want_type({'type': 'Simple', 'simple': 'AUTO'}) == 'STRING'


def test_slot_want_type_from_selectparam():
    s = {'type': 'SelectParam', 'selectParam': {'dataType': 'String'}}
    assert slot_want_type(s) == 'STRING'


# ---------------------------------------------------------------- 变量挑选

def _pool():
    return [
        {'name': '_A', 'dataType': 'DTO'},
        {'name': '_B', 'dataType': 'INTEGER'},
        {'name': '_C', 'dataType': 'STRING'},
        {'name': 'system.currentUserName', 'dataType': 'STRING', 'system': True},
    ]


def test_pick_variable_matches_numeric():
    v = pick_variable(_pool(), 'INTEGER')
    assert v['name'] == '_B'


def test_pick_variable_matches_string():
    v = pick_variable(_pool(), 'STRING')
    assert v['name'] == '_C'


def test_pick_variable_returns_none_when_absent():
    assert pick_variable(_pool(), 'DATETIME') is None


def test_available_vars_only_preceding_plus_sysvars():
    """★ 只能用前面的节点输出 + 系统变量，不能用后面的"""
    ordered = [
        {'nodeId': 'N1', 'output': {'name': '_A', 'dataType': 'INTEGER'}},
        {'nodeId': 'N2', 'output': {'name': '_B', 'dataType': 'STRING'}},
    ]
    sysvars = [{'name': 'system.currentUserName', 'dataType': 'STRING',
                'system': True}]
    pool = available_vars(ordered, 1, sysvars)
    names = [v['name'] for v in pool]
    assert '_A' in names          # 前置，可用
    assert '_B' not in names      # 自己/后面，不可用
    assert 'system.currentUserName' in names


def test_available_vars_carries_param_id():
    ordered = [{'nodeId': 'N1',
                'output': {'name': '_A', 'dataType': 'DTO',
                           'id': 'com.x.Dto'}}]
    pool = available_vars(ordered, 1, [])
    assert pool[0]['paramId'] == 'com.x.Dto'


# ---------------------------------------------------------------- DTO 构造

def test_build_dto_integer():
    dto = build_expression_dto({'name': '_B', 'dataType': 'INTEGER',
                                'desc': '行数'}, 'INTEGER')
    assert dto['resultTypeInfo'] == 'INTEGER'
    assert dto['terminalSupportType'] == 'BACKEND'
    assert len(dto['tokens']) == 3
    assert dto['tokens'][0]['type'] == 'VARIABLE'
    assert dto['tokens'][0]['value'] == '_B._B.value'
    assert len(dto['schemas']) == 1


def test_build_dto_string_single_token():
    dto = build_expression_dto({'name': '_C', 'dataType': 'STRING',
                                'desc': '名'}, 'STRING')
    assert dto['resultTypeInfo'] == 'STRING'
    assert len(dto['tokens']) == 1


def test_build_dto_dto_uses_entity_and_fullname():
    """★ DTO 必须 resultTypeInfo=ENTITY + resultTypeFullName

    缺 fullName → FORMULA_6901；用 OBJECT → FORMULA_6003。
    """
    dto = build_expression_dto({'name': '_R', 'dataType': 'DTO',
                                'paramId': 'com.x.Dto', 'desc': '结果'}, 'DTO')
    assert dto['resultTypeInfo'] == 'ENTITY'
    assert dto['resultTypeFullName'] == 'com.x.Dto'
    assert dto['resultTypeInfo'] in SUPPORTED_RESULT_TYPES


def test_build_dto_system_var_uses_system_token():
    """★ 系统变量是 SYSTEM token，不是 VARIABLE；schemas 可为空"""
    dto = build_expression_dto(
        {'name': 'system.currentUserName', 'dataType': 'STRING',
         'desc': '登录人员姓名', 'system': True}, 'STRING')
    assert dto['tokens'][0]['type'] == 'SYSTEM'
    assert dto['tokens'][0]['value'] == 'system.currentUserName'
    assert dto['schemas'] == []


def test_build_dto_system_var_datetime():
    dto = build_expression_dto(
        {'name': 'system.currentDateTime', 'dataType': 'DATETIME',
         'system': True}, 'DATETIME')
    assert dto['resultTypeInfo'] == 'DATETIME'
    assert dto['tokens'][0]['type'] == 'SYSTEM'


def test_build_dto_result_type_always_in_domain():
    """任何构造都不能产出值域外类型"""
    for want in ('INTEGER', 'BIGINTEGER', 'STRING', 'BOOLEAN', 'DATETIME', 'DTO'):
        var = {'name': '_X', 'dataType': want, 'paramId': 'com.x.D'}
        dto = build_expression_dto(var, want)
        assert dto['resultTypeInfo'] in SUPPORTED_RESULT_TYPES, want


def test_build_dto_schemas_have_skip_marker():
    """schemas 每层都要 skip:true"""
    dto = build_expression_dto({'name': '_B', 'dataType': 'INTEGER'}, 'INTEGER')
    s = dto['schemas'][0]
    assert s['skip'] is True
    assert s['properties'][0]['skip'] is True
    assert s['properties'][0]['properties'][0]['skip'] is True


def test_build_dto_token_uids_unique():
    dto = build_expression_dto({'name': '_B', 'dataType': 'INTEGER'}, 'INTEGER')
    uids = [t['uid'] for t in dto['tokens']]
    assert len(uids) == len(set(uids))


# ---------------------------------------------------------------- 顺序遍历

def test_walk_ordered_conditions_before_siblings():
    """条件分支里的节点要先于后续兄弟节点被遍历（决定可用变量范围）"""
    schema = {
        'nodes': [
            {'nodeId': 'BRANCH_1', 'type': 'BRANCH', 'conditions': [
                {'nodeId': 'C1', 'type': 'CONDITION', 'nodes': [
                    {'nodeId': 'N_IN_COND', 'type': 'CREATE_ENTITY'}]},
            ]},
            {'nodeId': 'N_AFTER', 'type': 'CHANGE_ENTITY'},
        ],
    }
    ids = [n.get('nodeId') for n in walk_ordered(schema['nodes'])]
    assert ids.index('N_IN_COND') < ids.index('N_AFTER')
