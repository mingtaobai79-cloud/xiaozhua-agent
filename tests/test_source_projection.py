"""Build-time projection primitive for microflow dependency sources.

All sources below are synthetic. The primitive removes exactly the symbols a
caller lists, and fails closed on anything it cannot prove about the module it
is projecting. It is not a de-identification tool.
"""

import ast
import importlib.util

import pytest


SOURCE = '''"""synthetic module"""
LIVE_ALPHA = "alpha-value"
LIVE_BETA = "beta-value"
LIVE_INDEX = (LIVE_ALPHA, LIVE_BETA)

BASE = 10

def is_live(value):
    return value in LIVE_INDEX

def add_base(x):
    return x + BASE
'''

CLOSURE = ("LIVE_ALPHA", "LIVE_BETA", "LIVE_INDEX", "is_live")


def _primitive():
    spec = importlib.util.find_spec("tools.core.source_projection")
    assert spec is not None, "source projection primitive missing"
    module = importlib.import_module("tools.core.source_projection")
    assert hasattr(module, "project_module"), "project_module entrypoint missing"
    return module


def test_projection_removes_only_explicitly_listed_symbols_and_executes():
    result = _primitive().project_module(
        SOURCE, remove=CLOSURE, expect_remaining=("BASE", "add_base")
    )

    assert result.removed == CLOSURE
    assert set(result.remaining) == {"BASE", "add_base"}
    assert "LIVE_ALPHA" not in result.source
    assert "def add_base(x):" in result.source

    namespace = {}
    exec(result.code, namespace)  # noqa: S102 - synthetic source only

    assert namespace["add_base"](5) == 15
    assert "is_live" not in namespace
    assert "LIVE_INDEX" not in namespace


def test_projection_preserves_untouched_lines_verbatim():
    result = _primitive().project_module(SOURCE, remove=("LIVE_BETA", "LIVE_INDEX", "is_live"))

    assert '"beta-value"' not in result.source
    # untouched formatting and the leading module docstring survive byte-for-byte
    assert result.source.startswith('"""synthetic module"""\n')
    assert "BASE = 10\n\ndef add_base(x):\n    return x + BASE\n" in result.source


def test_projection_requires_an_explicit_symbol_list():
    module = _primitive()
    for source in ('SECRET = KEEP = 7\n', 'SECRET = 1; KEEP = 7\n'):
        with pytest.raises(ValueError, match='shared'):
            module.project_module(source, remove=('SECRET',), expect_remaining=('KEEP',))
    with pytest.raises(ValueError, match="explicit symbol list"):
        module.project_module(SOURCE, remove=())
    with pytest.raises(ValueError, match="explicit symbol"):
        module.project_module(SOURCE, remove=("*LIVE*",))


def test_missing_declaration_fails_closed():
    with pytest.raises(ValueError, match="not declared"):
        _primitive().project_module(SOURCE, remove=("LIVE_GAMMA",))


def test_duplicate_declaration_fails_closed():
    source = "VALUE = 1\nVALUE = 2\n"
    with pytest.raises(ValueError, match="duplicate"):
        _primitive().project_module(source, remove=("VALUE",))


def test_unexpected_new_declaration_fails_closed():
    with pytest.raises(ValueError, match="unexpected"):
        _primitive().project_module(
            SOURCE, remove=CLOSURE, expect_remaining=("BASE",)
        )


def test_expected_declaration_that_vanished_fails_closed():
    with pytest.raises(ValueError, match="missing expected"):
        _primitive().project_module(
            SOURCE, remove=CLOSURE, expect_remaining=("BASE", "add_base", "keep_me")
        )


def test_residual_reference_to_removed_symbol_fails_closed():
    with pytest.raises(ValueError, match="residual reference"):
        _primitive().project_module(SOURCE, remove=("LIVE_ALPHA",))


def test_string_reference_to_removed_symbol_fails_closed():
    source = 'LIVE_A = "a"\nALLOWED = {"LIVE_A": 1}\n'
    with pytest.raises(ValueError, match="residual reference"):
        _primitive().project_module(source, remove=("LIVE_A",))


def test_export_list_reference_to_removed_symbol_fails_closed():
    source = 'LIVE_A = "a"\n__all__ = ["LIVE_A"]\n'
    with pytest.raises(ValueError, match="residual reference"):
        _primitive().project_module(source, remove=("LIVE_A",))


def test_dynamic_name_resolution_is_rejected():
    source = 'LIVE_A = "a"\n\ndef pick(name):\n    return globals()[name]\n'
    with pytest.raises(ValueError, match="dynamic name resolution"):
        _primitive().project_module(source, remove=("LIVE_A",))


def test_unknown_ast_construct_is_rejected():
    module = _primitive()

    class _UnknownConstruct(ast.AST):
        _fields = ()

    tree = ast.parse(SOURCE)
    tree.body.append(_UnknownConstruct())
    ast.fix_missing_locations(tree)

    with pytest.raises(ValueError, match="unsupported AST construct"):
        module.project_tree(tree, SOURCE.splitlines(keepends=True), remove=CLOSURE)


def test_syntax_error_is_rejected():
    with pytest.raises(ValueError, match="syntax"):
        _primitive().project_module("def broken(:\n", remove=("broken",))


def test_projection_does_not_claim_deidentification():
    module = _primitive()
    doc = (module.__doc__ or "").lower()
    assert "not de-identification" in doc
    assert "not de-identification" in (module.project_module.__doc__ or "").lower()
