import json

import pytest

from components.udc.microflow import deploy
from components.udc.microflow.live_refs import LiveRefs


@pytest.mark.parametrize('schema', [None, '{}', json.dumps({'input': None})])
def test_missing_schema_or_output_is_not_a_confirmed_null(monkeypatch, schema):
    monkeypatch.setattr(deploy, 'get', lambda *args: {'id': '1', 'dataSchema': schema})
    refs = LiveRefs.__new__(LiveRefs)
    refs._cache = {}
    refs.host = 'offline'
    refs.cookie = 'offline'
    with pytest.raises(ValueError, match='output|dataSchema'):
        refs.microflow_detail('1')


def test_composer_rejects_missing_detail_provider():
    from components.construction.microflow_composer import ComposeError, MicroflowComposer
    from components.construction.node_builder import NodeBuilder

    class Refs:
        def find_sub_mf(self, *args, **kwargs):
            return {'id': '1', 'name': 'child', 'type': 'SERVICE'}

    composer = MicroflowComposer(NodeBuilder(app_id='1', app_name='app'), Refs(), app_id='1', app_name='app')
    with pytest.raises(ComposeError, match='UNVERIFIED'):
        composer.step('SUB_MICROFLOW', alias='child', sub_name='child')


def test_composer_accepts_explicit_null_detail():
    from components.construction.microflow_composer import MicroflowComposer
    from components.construction.node_builder import NodeBuilder

    class Refs:
        def find_sub_mf(self, *args, **kwargs):
            return {'id': '1', 'name': 'child', 'type': 'SERVICE'}

        def microflow_detail(self, _id):
            return {'input': None, 'output': None}

    composer = MicroflowComposer(NodeBuilder(app_id='1', app_name='app'), Refs(), app_id='1', app_name='app')
    node = composer.step('SUB_MICROFLOW', alias='child', sub_name='child')
    assert node['mfService']['output'] is None
    assert node['mfService']['hasOutput'] is False


def test_composer_does_not_reference_child_with_explicit_no_output():
    from components.construction.microflow_composer import ComposeError, MicroflowComposer
    from components.construction.node_builder import NodeBuilder

    class Refs:
        def find_sub_mf(self, *args, **kwargs):
            return {'id': '1', 'name': 'child', 'type': 'SERVICE'}

        def microflow_detail(self, _id):
            return {'input': None, 'output': None}

    composer = MicroflowComposer(NodeBuilder(app_id='1', app_name='app'), Refs(), app_id='1', app_name='app')
    composer.step('SUB_MICROFLOW', alias='child', sub_name='child')
    with pytest.raises(ComposeError, match='子流程.*出参'):
        composer.finish(end_from='child', gate=False)


def test_explicit_null_contract_is_preserved(monkeypatch):
    monkeypatch.setattr(deploy, 'get', lambda *args: {'id': '1', 'dataSchema': json.dumps({'input': None, 'output': None})})
    refs = LiveRefs.__new__(LiveRefs)
    refs._cache = {}
    refs.host = 'offline'
    refs.cookie = 'offline'
    assert refs.microflow_detail('1')['output'] is None
