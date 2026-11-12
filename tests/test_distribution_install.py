"""Synthetic-only checks for the manifest-driven offline install primitive.

Every fixture here is generated in ``tmp_path``; no customer data, no repo
assets, no network. These tests do not approve a release and do not install
the real skills.
"""
import json
import zipfile
from pathlib import Path

import pytest


def _write_tree(root):
    (root / 'pkg').mkdir(parents=True)
    (root / 'pkg' / '__init__.py').write_text('', encoding='utf-8')
    (root / 'pkg' / 'helper.py').write_text('VALUE = "from-install-root"\n', encoding='utf-8')
    (root / 'pkg' / 'entry.py').write_text(
        'from . import helper\n\n\ndef main():\n    return {"value": helper.VALUE}\n',
        encoding='utf-8',
    )
    (root / 'README.md').write_text('# synthetic bundle\n', encoding='utf-8')
    return ['README.md', 'pkg/__init__.py', 'pkg/helper.py', 'pkg/entry.py']


def _build(root, output, files=None, **overrides):
    from tools.core import distribution_install as install
    kwargs = dict(name='synthetic-demo', version='0.0.1', entry='pkg.entry:main')
    kwargs.update(overrides)
    return install.build_bundle(root, files if files is not None else _write_tree(root), output, **kwargs)


def test_synthetic_bundle_roundtrip_runs_in_isolated_process(tmp_path):
    from tools.core import distribution_install as install

    root = tmp_path / 'src'
    root.mkdir()
    output = tmp_path / 'bundle.zip'
    manifest = _build(root, output)

    assert output.exists()
    paths = [item['path'] for item in manifest['files']]
    assert paths == ['README.md', 'pkg/__init__.py', 'pkg/entry.py', 'pkg/helper.py']
    assert all(len(item['sha256']) == 64 for item in manifest['files'])
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        assert names == sorted(names), names
        assert 'bundle-manifest.json' in names
        manifest_in_zip = json.loads(archive.read('bundle-manifest.json'))
        assert manifest_in_zip['name'] == 'synthetic-demo'

    dest = tmp_path / 'installed'
    existing = tmp_path / 'already-empty'
    existing.mkdir()
    with pytest.raises(ValueError, match='existing'):
        install.install_bundle(output, existing)
    assert not list(existing.iterdir())
    installed = install.install_bundle(output, dest)
    assert installed['version'] == '0.0.1'
    assert (dest / 'pkg' / 'entry.py').is_file()

    decoy = tmp_path / 'decoy-cwd'
    decoy.mkdir()
    (decoy / 'pkg').mkdir()
    (decoy / 'pkg' / '__init__.py').write_text('', encoding='utf-8')
    (decoy / 'pkg' / 'helper.py').write_text('VALUE = "from-cwd-decoy"\n', encoding='utf-8')

    result = install.invoke_installed(dest, 'pkg.entry:main', cwd=decoy)
    assert result['ok'] is True, result
    assert result['value'] == {'value': 'from-install-root'}


def test_missing_source_file_blocks_build_without_writing(tmp_path):
    from tools.core import distribution_install as install

    root = tmp_path / 'src'
    root.mkdir()
    files = _write_tree(root)
    files.append('pkg/absent.py')
    output = tmp_path / 'bundle.zip'

    with pytest.raises(ValueError, match='missing or non-regular file'):
        _build(root, output, files=files)
    assert not output.exists()


def test_archive_that_disagrees_with_manifest_is_refused(tmp_path):
    from tools.core import distribution_install as install

    root = tmp_path / 'src'
    root.mkdir()
    output = tmp_path / 'bundle.zip'
    _build(root, output)

    tampered = tmp_path / 'tampered.zip'
    with zipfile.ZipFile(output) as source, zipfile.ZipFile(tampered, 'w') as target:
        for name in source.namelist():
            data = source.read(name)
            if name == 'pkg/helper.py':
                data = b'VALUE = "swapped"\n'
            target.writestr(name, data)
    dest = tmp_path / 'installed-tampered'
    with pytest.raises(ValueError, match='hash mismatch'):
        install.install_bundle(tampered, dest)
    assert not dest.exists()

    dropped = tmp_path / 'dropped.zip'
    with zipfile.ZipFile(output) as source, zipfile.ZipFile(dropped, 'w') as target:
        for name in source.namelist():
            if name != 'pkg/helper.py':
                target.writestr(name, source.read(name))
    with pytest.raises(ValueError, match='missing from archive'):
        install.install_bundle(dropped, tmp_path / 'installed-dropped')
    assert not (tmp_path / 'installed-dropped').exists()

    escaped = tmp_path / 'escaped.zip'
    with zipfile.ZipFile(output) as source, zipfile.ZipFile(escaped, 'w') as target:
        for name in source.namelist():
            target.writestr(name, source.read(name))
        target.writestr('../outside.py', b'x')
    with pytest.raises(ValueError, match='undeclared|unsafe'):
        install.install_bundle(escaped, tmp_path / 'installed-escaped')
    assert not (tmp_path / 'installed-escaped').exists()
    assert not (tmp_path / 'outside.py').exists()

    collision = tmp_path / 'collision.zip'
    with zipfile.ZipFile(output) as source, zipfile.ZipFile(collision, 'w') as target:
        manifest = json.loads(source.read('bundle-manifest.json'))
        item = next(x for x in manifest['files'] if x['path'] == 'pkg/helper.py')
        manifest['files'].append({**item, 'path': 'pkg/HELPER.py'})
        for name in source.namelist():
            data = json.dumps(manifest).encode() if name == 'bundle-manifest.json' else source.read(name)
            target.writestr(name, data)
        target.writestr('pkg/HELPER.py', source.read('pkg/helper.py'))
    with pytest.raises(ValueError, match='case collision'):
        install.install_bundle(collision, tmp_path / 'installed-collision')
    assert not (tmp_path / 'installed-collision').exists()


def test_invoke_reports_missing_module_instead_of_traceback(tmp_path):
    from tools.core import distribution_install as install

    root = tmp_path / 'src'
    root.mkdir()
    output = tmp_path / 'bundle.zip'
    _build(root, output)
    dest = tmp_path / 'installed'
    install.install_bundle(output, dest)
    (dest / 'pkg' / 'entry.py').unlink()

    result = install.invoke_installed(dest, 'pkg.entry:main')
    assert result['ok'] is False
    assert result['error'] == 'ModuleNotFoundError'
    assert 'Traceback' not in json.dumps(result)

    with pytest.raises(ValueError, match='existing non-empty'):
        install.install_bundle(output, dest)
