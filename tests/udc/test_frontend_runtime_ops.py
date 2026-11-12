"""前端运行时 fn→op 真值表测试（RUNTIME 证据）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.frontend_runtime_ops import (
    SEMANTIC_FN_OPS, RUNTIME_FN_PATHS, RUNTIME_RESOLVED, RUNTIME_UNIQUE_OPS,
    ops_of, fns_of, SCHEMA_ID)


def test_scale():
    assert len(SEMANTIC_FN_OPS) >= 140
    assert RUNTIME_FN_PATHS >= 450
    assert RUNTIME_RESOLVED >= 300
    assert RUNTIME_UNIQUE_OPS >= 300


def test_known_mappings():
    """抽查语义正确的映射。"""
    assert "udcDataFlowMappingUpdatePost" in ops_of("handleSubmitMapping")
    assert "udcEntityAttributeBatchDeletePost" in ops_of("deleteEntityField")
    assert "udcEntityAssociationEntityAppGet" in ops_of("fetchAssociationEntityByAppId")
    assert "udcDeductionRuleDeletePost" in ops_of("delDeductRule")


def test_bidirectional():
    ops = ops_of("handleSubmitMapping")
    assert ops
    for op in ops:
        fns = fns_of(op)
        assert "handleSubmitMapping" in fns


def test_all_ops_are_known_families():
    """op 前缀族：udc/bpm/appCommon/ctp/portal/main/cdpData 及 apollo 裸名（dataFlow/deduction 等）。"""
    known_prefixes = ("udc", "app", "bpm", "ctp", "por", "mai", "cdp", "dat", "ded", "mic", "ent", "pag")
    for fn, ops in SEMANTIC_FN_OPS.items():
        for op in ops:
            assert op[:3] in known_prefixes, (fn, op)


def test_no_empty_entries():
    assert all(ops for ops in SEMANTIC_FN_OPS.values())
