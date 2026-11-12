from pathlib import Path

import pytest

import importlib.util


def validate_sources(*args):
    spec = importlib.util.find_spec('tools.core.distribution_manifest')
    assert spec is not None, 'distribution manifest guard missing'
    return __import__('tools.core.distribution_manifest', fromlist=['validate_sources']).validate_sources(*args)


def test_explicit_regular_file_is_accepted(tmp_path):
    (tmp_path / 'fact.md').write_text('fact', encoding='utf-8')
    assert validate_sources(tmp_path, ['fact.md']) == [Path('fact.md')]
    with pytest.raises(ValueError, match='empty'):
        validate_sources(tmp_path, [])


@pytest.mark.parametrize('entry', ['../secret', '.git/config', 'scratch/example', 'missing.md'])
def test_unsafe_or_missing_file_is_rejected(tmp_path, entry):
    with pytest.raises(ValueError):
        validate_sources(tmp_path, [entry])


def test_content_preflight_reports_redacted_findings_and_rejects_unknown_format(tmp_path):
    from tools.core import distribution_manifest as guard
    import json

    secret = 'znxmglpt123456789_test2'   # SYNTHETIC-FIXTURE 合成假值：本测试就是要验证 guard 能认出这种串，故必须像真的
    (tmp_path / 'data.json').write_text(json.dumps({'name': secret, 'password': 'synthetic-secret'}), encoding='utf-8')
    (tmp_path / 'safe.md').write_text('placeholder: datamigration9000000000000000001', encoding='utf-8')
    assert hasattr(guard, 'scan_content'), 'content preflight missing'
    findings = guard.scan_content(tmp_path, ['data.json', 'safe.md'])
    assert {item['category'] for item in findings} >= {'customer_identifier', 'credential_assignment'}
    assert all(item['path'] == 'data.json' for item in findings)
    assert secret not in str(findings) and 'synthetic-secret' not in str(findings)
    with pytest.raises(ValueError, match='content preflight failed'):
        guard.snapshot_sources(tmp_path, ['data.json'])
    (tmp_path / 'live.py').write_text('LIVE_EXAMPLE: dict = {"caption": "synthetic"}\n', encoding='utf-8')
    assert any(x['category'] == 'live_fixture' for x in guard.scan_content(tmp_path, ['live.py']))
    with pytest.raises(ValueError, match='content preflight failed'):
        guard.snapshot_sources(tmp_path, ['live.py'])
    (tmp_path / 'opaque.bin').write_bytes(b'\x00\xff')
    with pytest.raises(ValueError):
        guard.scan_content(tmp_path, ['opaque.bin'])
    (tmp_path / 'evidence.json').write_text(json.dumps({'run': {'db_after': [{'value': 'synthetic-private'}]}}), encoding='utf-8')
    findings = guard.scan_content(tmp_path, ['evidence.json'])
    assert any(x['category'] == 'runtime_business_data' for x in findings)
    assert 'synthetic-private' not in str(findings)
    with pytest.raises(ValueError, match='content preflight failed'):
        guard.snapshot_sources(tmp_path, ['evidence.json'])


def test_snapshot_retains_checked_bytes_when_source_changes(tmp_path):
    from tools.core import distribution_manifest as guard

    path = tmp_path / 'fact.md'
    path.write_bytes(b'original')
    snapshot = guard.snapshot_sources(tmp_path, ['fact.md'])
    path.write_bytes(b'changed')
    assert snapshot[Path('fact.md')] == b'original'
    import zipfile
    from unittest.mock import patch
    output = tmp_path / 'out.zip'
    with patch.object(guard, 'snapshot_sources', return_value=snapshot):
        guard.build_snapshot_zip(tmp_path, ['fact.md'], output)
    with zipfile.ZipFile(output) as archive:
        assert archive.read('fact.md') == b'original'
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        guard.build_snapshot_zip(tmp_path, ['fact.md'], output)
    assert output.read_bytes() == before
    (tmp_path / 'bad.json').write_text('{"db_after": [1]}', encoding='utf-8')
    denied = tmp_path / 'denied.zip'
    with pytest.raises(ValueError, match='content preflight failed'):
        guard.build_snapshot_zip(tmp_path, ['bad.json'], denied)
    assert not denied.exists()
    failed = tmp_path / 'failed.zip'
    with patch.object(zipfile.ZipFile, 'writestr', side_effect=RuntimeError('compression failure')):
        with pytest.raises(RuntimeError, match='compression failure'):
            guard.build_snapshot_zip(tmp_path, ['fact.md'], failed)
    assert not failed.exists()


def test_content_preflight_rejects_nul_encoded_text(tmp_path):
    from tools.core.distribution_manifest import scan_content

    (tmp_path / 'data.json').write_bytes('{"value":"hello"}'.encode('utf-16-le'))
    with pytest.raises(ValueError):
        scan_content(tmp_path, ['data.json'])


def test_windows_junction_is_rejected(tmp_path):
    import os
    import subprocess

    if os.name != 'nt':
        pytest.skip('Windows junction test')
    target = tmp_path / 'target'
    target.mkdir()
    (target / 'fact.md').write_text('fact', encoding='utf-8')
    link = tmp_path / 'junction'
    created = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(target)], capture_output=True)
    assert created.returncode == 0, created.stderr
    with pytest.raises(ValueError):
        validate_sources(tmp_path, ['junction/fact.md'])


def test_symlink_is_rejected(tmp_path):
    source = tmp_path / 'source'
    source.write_text('x', encoding='utf-8')
    link = tmp_path / 'link'
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip('symlink unavailable')
    with pytest.raises(ValueError):
        validate_sources(tmp_path, ['link'])
