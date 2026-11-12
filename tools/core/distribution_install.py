"""Manifest-driven offline install primitive (synthetic-content use only).

This is not a release pipeline: it reuses ``distribution_manifest`` for path and
content preflight, adds a declarative file manifest, and can install a bundle
into an isolated directory and invoke it in a separate interpreter. It does not
approve publishing, does not resolve dependency closures and does not sandbox
the invoked code.
"""
from pathlib import Path, PurePosixPath
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

from tools.core import distribution_manifest

SCHEMA = 'xiaozhua-offline-bundle.v1'
MANIFEST_NAME = 'bundle-manifest.json'
_INVOKE_TIMEOUT_SECONDS = 60

_INVOKE_SCRIPT = """
import importlib, json, sys
sys.path.insert(0, sys.argv[1])
module_name, _, attribute = sys.argv[2].partition(':')
try:
    module = importlib.import_module(module_name)
    function = getattr(module, attribute) if attribute else module
    print(json.dumps({'ok': True, 'value': function()}))
except BaseException as exc:
    print(json.dumps({'ok': False, 'error': type(exc).__name__}))
"""


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _manifest_bytes(name, version, entry, snapshot):
    payload = {
        'schema': SCHEMA,
        'name': name,
        'version': version,
        'entry': entry,
        'files': [
            {'path': path.as_posix(), 'sha256': _sha256(data), 'size': len(data)}
            for path, data in sorted(snapshot.items(), key=lambda item: item[0].as_posix())
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True).encode('utf-8')


def build_bundle(root, entries, output, *, name, version, entry):
    """Write a bundle from exactly the listed sources; never overwrites output."""
    snapshot = distribution_manifest.snapshot_sources(root, entries)
    if not isinstance(name, str) or not name.strip():
        raise ValueError('invalid bundle name')
    if not isinstance(version, str) or not version.strip():
        raise ValueError('invalid bundle version')
    if not isinstance(entry, str) or ':' not in entry:
        raise ValueError('invalid entry point')
    manifest = _manifest_bytes(name, version, entry, snapshot)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        members = {path.as_posix(): data for path, data in snapshot.items()}
        members[MANIFEST_NAME] = manifest
        for member in sorted(members):
            archive.writestr(member, members[member])
    with open(output, 'xb') as stream:
        stream.write(buffer.getvalue())
    return json.loads(manifest)


def _safe_relative(name):
    posix = PurePosixPath(name)
    if posix.is_absolute() or '..' in posix.parts or not posix.parts or '\\' in name:
        raise ValueError('undeclared or unsafe path in archive')
    return posix.as_posix()


def _read_manifest(archive):
    try:
        raw = archive.read(MANIFEST_NAME)
    except KeyError as exc:
        raise ValueError('bundle manifest missing') from exc
    try:
        manifest = json.loads(raw)
    except ValueError as exc:
        raise ValueError('bundle manifest invalid') from exc
    if not isinstance(manifest, dict) or manifest.get('schema') != SCHEMA:
        raise ValueError('bundle manifest invalid')
    files = manifest.get('files')
    if not isinstance(files, list) or not files:
        raise ValueError('bundle manifest has no files')
    return manifest


def install_bundle(archive_path, destination):
    """Extract a bundle only after every declared file matches its hash.

    The destination must not already exist. Concurrent replacement safety is
    not guaranteed; this primitive remains unsuitable for release installs.
    """
    destination = Path(destination)
    if os.path.lexists(destination):
        raise ValueError('destination existing non-empty or empty')
    with zipfile.ZipFile(archive_path) as archive:
        manifest = _read_manifest(archive)
        declared = {}
        folded_paths = set()
        for item in manifest['files']:
            path = _safe_relative(item['path'])
            if path.casefold() in folded_paths:
                raise ValueError('case collision in manifest')
            folded_paths.add(path.casefold())
            if path in declared:
                raise ValueError('duplicate path in manifest')
            declared[path] = item
        members = {}
        for name in archive.namelist():
            if name == MANIFEST_NAME:
                continue
            path = _safe_relative(name)
            if path not in declared:
                raise ValueError('undeclared file in archive: undeclared or unsafe path')
            members[path] = archive.read(name)
        for path, item in declared.items():
            if path not in members:
                raise ValueError(f'missing from archive: {path}')
            data = members[path]
            if _sha256(data) != item['sha256'] or len(data) != item['size']:
                raise ValueError(f'hash mismatch: {path}')

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.install-staging-', dir=destination.parent))
    try:
        for path, data in members.items():
            target = staging / path
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, 'xb') as stream:
                stream.write(data)
        if os.path.lexists(destination):
            raise ValueError('destination existing non-empty or empty')
        os.rename(staging, destination)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    return manifest


def invoke_installed(destination, entry, cwd=None):
    """Call the entry point in a fresh isolated interpreter.

    ``-I`` ignores environment and user site, ``-B`` writes no bytecode; the
    install root is prepended to ``sys.path`` so a same-named module in ``cwd``
    cannot shadow it. Failures are reported as names only, never tracebacks.
    """
    destination = Path(destination)
    if not destination.is_dir():
        raise ValueError('installed destination missing')
    if not isinstance(entry, str) or ':' not in entry:
        raise ValueError('invalid entry point')
    command = [sys.executable, '-I', '-B', '-c', _INVOKE_SCRIPT, str(destination), entry]
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd is not None else str(destination),
        capture_output=True,
        text=True,
        timeout=_INVOKE_TIMEOUT_SECONDS,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if completed.returncode != 0 or not lines:
        return {'ok': False, 'error': 'invocation failed'}
    try:
        result = json.loads(lines[-1])
    except ValueError:
        return {'ok': False, 'error': 'unreadable output'}
    if not isinstance(result, dict) or 'ok' not in result:
        return {'ok': False, 'error': 'unreadable output'}
    return result
