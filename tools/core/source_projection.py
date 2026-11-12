"""Fail-closed build-time projection of microflow dependency sources.

This primitive deletes exactly the top-level declarations named by the caller
and refuses everything it cannot prove: unknown symbols, duplicate
declarations, residual references to removed names, dynamic name resolution and
unsupported AST constructs. It is *not de-identification*: it neither detects
nor redacts customer identifiers, credentials or business data, and a successful
projection is not a release approval.
"""

import ast
import keyword
from dataclasses import dataclass

_RESOLVERS = {'globals', 'locals', 'vars', 'eval', 'exec', 'compile', '__import__'}
_KNOWN_NODES = {
    name for name, value in vars(ast).items()
    if isinstance(value, type) and issubclass(value, ast.AST)
}


@dataclass(frozen=True)
class ProjectionResult:
    source: str
    code: object
    removed: tuple
    remaining: tuple


def _bound_names(node):
    """Names bound by one supported top-level statement."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return [node.name]
    if isinstance(node, ast.Assign):
        names = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for element in target.elts:
                    if not isinstance(element, ast.Name):
                        raise ValueError('unsupported AST construct: assign target')
                    names.append(element.id)
            else:
                raise ValueError('unsupported AST construct: assign target')
        return names
    if isinstance(node, ast.AnnAssign):
        if not isinstance(node.target, ast.Name):
            raise ValueError('unsupported AST construct: annotated target')
        return [node.target.id]
    if isinstance(node, ast.Import):
        return [alias.asname or alias.name.split('.')[0] for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        names = []
        for alias in node.names:
            if alias.name == '*':
                raise ValueError('unsupported AST construct: star import')
            names.append(alias.asname or alias.name)
        return names
    return None


def _validate_removed(remove):
    if isinstance(remove, str) or not isinstance(remove, (list, tuple)):
        raise ValueError('removed symbols must be an explicit symbol list')
    if not remove:
        raise ValueError('removed symbols must be an explicit symbol list')
    entries = []
    for entry in remove:
        if not isinstance(entry, str):
            raise ValueError('removed symbols must be an explicit symbol list')
        if not entry.isidentifier() or keyword.iskeyword(entry):
            raise ValueError('removed entry must be an explicit symbol name: %r' % (entry,))
        entries.append(entry)
    if len(set(entries)) != len(entries):
        raise ValueError('removed entry listed twice')
    return tuple(entries)


def project_tree(tree, lines, remove, expect_remaining=None):
    """Project an already parsed tree; ``lines`` are the original source lines."""
    removed = _validate_removed(remove)

    for node in ast.walk(tree):
        if type(node).__name__ not in _KNOWN_NODES:
            raise ValueError('unsupported AST construct: %s' % type(node).__name__)

    declarations = {}
    order = []
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str) and node is tree.body[0]:
            continue
        names = _bound_names(node)
        if names is None:
            raise ValueError('unsupported AST construct: %s' % type(node).__name__)
        for name in names:
            if name in declarations:
                raise ValueError('duplicate declaration: %s' % name)
            declarations[name] = node
            order.append(name)

    missing = [name for name in removed if name not in declarations]
    if missing:
        raise ValueError('removed symbol not declared: %s' % ', '.join(missing))

    dropped = {id(declarations[name]) for name in removed}
    for node in tree.body:
        if id(node) not in dropped:
            continue
        if set(_bound_names(node)) - set(removed):
            raise ValueError('shared declaration cannot be partially removed')
        start = min([node.lineno] + [d.lineno for d in getattr(node, 'decorator_list', [])])
        if any(other is not node and getattr(other, 'lineno', 0) <= node.end_lineno
               and getattr(other, 'end_lineno', 0) >= start for other in tree.body):
            raise ValueError('shared source line cannot be removed')

    def kept_nodes(root):
        """Walk the tree but never descend into a removed declaration."""
        stack = [root]
        while stack:
            node = stack.pop()
            if id(node) in dropped:
                continue
            yield node
            stack.extend(reversed(list(ast.iter_child_nodes(node))))

    for node in kept_nodes(tree):
        if isinstance(node, ast.Name) and node.id in _RESOLVERS:
            raise ValueError('dynamic name resolution not allowed: %s' % node.id)
        if isinstance(node, ast.Attribute) and node.attr == 'getframe':
            raise ValueError('dynamic name resolution not allowed: getframe')

    for node in kept_nodes(tree):
        if isinstance(node, ast.Name) and node.id in removed:
            raise ValueError('residual reference to removed symbol: %s' % node.id)

    for node in kept_nodes(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and node.value in removed:
            raise ValueError('residual reference to removed symbol: %s' % node.value)


    keep = set(removed)
    remaining = tuple(name for name in order if name not in keep)
    if expect_remaining is not None:
        expected = tuple(expect_remaining)
        absent = [name for name in expected if name not in remaining]
        if absent:
            raise ValueError('missing expected declaration: %s' % ', '.join(absent))
        extra = [name for name in remaining if name not in expected]
        if extra:
            raise ValueError('unexpected declaration: %s' % ', '.join(extra))

    blanked = set()
    for node in tree.body:
        if id(node) not in dropped:
            continue
        start = min([node.lineno] + [d.lineno for d in getattr(node, 'decorator_list', [])])
        end = node.end_lineno
        if start - 1 >= 1 and not lines[start - 2].strip():
            start -= 1
        blanked.update(range(start, end + 1))

    source = ''.join(
        line for number, line in enumerate(lines, start=1) if number not in blanked
    )
    try:
        code = compile(source, '<projection>', 'exec')
    except SyntaxError as exc:
        raise ValueError('syntax error in projected source') from exc
    return ProjectionResult(source=source, code=code, removed=removed, remaining=remaining)


def project_module(source, remove, expect_remaining=None):
    """Project one module's source; not de-identification, not a release approval."""
    if not isinstance(source, str):
        raise ValueError('source must be text')
    lines = source.splitlines(keepends=True)
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError('syntax error in source') from exc
    return project_tree(tree, lines, remove=remove, expect_remaining=expect_remaining)
