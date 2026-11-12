"""Validate explicitly listed distribution sources; content review is separate."""
from pathlib import Path, PureWindowsPath
import ast
import json
import io
import re
import zipfile

_TEXT_SUFFIXES = {'.md', '.json', '.py', '.yaml', '.yml', '.txt', '.toml', '.js', '.sh'}
_CONTENT_PATTERNS = {
    # SYNTHETIC-FIXTURE: 判据定义行（客户标识识别用），不是泄漏数据
    'customer_identifier': re.compile(r'(?i)(?:datamigration|znxmglpt)(?!9000000000000000\d{3}(?!\d))\d{6,}'),  # SYNTHETIC-FIXTURE
    'credential_assignment': re.compile(r'''(?i)["']?(?:password|passwd|secret|token|api[_-]?key)["']?\s*[:=]\s*["'][^"'\s]{4,}["']'''),
    'private_key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
}

_DENIED = {'.git', 'scratch', '__pycache__', '_attic_pending', 'node_modules'}


def validate_sources(root, entries):
    root = Path(root).resolve(strict=True)
    result = []
    for entry in entries:
        p = Path(entry)
        windows = PureWindowsPath(str(entry))
        if p.is_absolute() or windows.is_absolute() or windows.drive or '..' in p.parts or '..' in windows.parts:
            raise ValueError('unsafe path')
        if not p.parts or any(part.lower() in _DENIED for part in p.parts):
            raise ValueError('excluded path')
        current = root
        for part in p.parts:
            current = current / part
            if current.is_symlink() or current.is_junction():
                raise ValueError('link or junction not allowed')
        if not current.is_file() or not current.resolve().is_relative_to(root):
            raise ValueError('missing or non-regular file')
        result.append(p)
    if not result:
        raise ValueError('empty source list')
    return result


def _scan_bytes(path, data):
    if path.suffix.lower() not in _TEXT_SUFFIXES:
        raise ValueError('unsupported content format')
    try:
        text = data.decode('utf-8')
    except UnicodeError as exc:
        raise ValueError('unreadable text') from exc
    if '\x00' in text:
        raise ValueError('unsupported text encoding')
    findings = []
    if path.suffix.lower() == '.py':
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            raise ValueError('invalid Python source') from exc
        for node in tree.body:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
            if any(isinstance(target, ast.Name) and target.id.startswith('LIVE_') for target in targets):
                findings.append({'path': path.as_posix(), 'line': node.lineno, 'category': 'live_fixture'})
    if path.suffix.lower() == '.json':
        try:
            value = json.loads(text)
        except ValueError as exc:
            raise ValueError('invalid JSON') from exc
        def has_readback(obj):
            if isinstance(obj, dict):
                return 'db_after' in obj or any(has_readback(v) for v in obj.values())
            if isinstance(obj, list):
                return any(has_readback(v) for v in obj)
            return False
        if has_readback(value):
            findings.append({'path': path.as_posix(), 'line': None, 'category': 'runtime_business_data'})
    for category, pattern in _CONTENT_PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append({'path': path.as_posix(), 'line': text.count('\n', 0, match.start()) + 1, 'category': category})
    return findings


def scan_content(root, entries):
    """Return redacted heuristic findings; no findings is not proof of safety."""
    paths = validate_sources(root, entries)
    findings = []
    for path in paths:
        try:
            data = (Path(root) / path).read_bytes()
        except OSError as exc:
            raise ValueError('unreadable text') from exc
        findings.extend(_scan_bytes(path, data))
    return findings


def snapshot_sources(root, entries):
    """Return the exact checked bytes; heuristic checks do not approve release."""
    paths = validate_sources(root, entries)
    result = {}
    for path in paths:
        try:
            data = (Path(root) / path).read_bytes()
        except OSError as exc:
            raise ValueError('unreadable text') from exc
        if _scan_bytes(path, data):
            raise ValueError('content preflight failed')
        result[path] = data
    return result


def build_snapshot_zip(root, entries, output):
    """Write checked snapshots exclusively; not a release approval."""
    snapshot = snapshot_sources(root, entries)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path, data in snapshot.items():
            archive.writestr(path.as_posix(), data)
    with open(output, 'xb') as stream:
        stream.write(buffer.getvalue())
