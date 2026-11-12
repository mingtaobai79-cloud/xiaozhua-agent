"""余量 60 op 的前端 loader 契约护栏（第五轮；第六轮同步 corrected 口径 92/32/60）。

证据：docs/audit/udc-semantics/frontend-op-loader-contract.json（**机械复算产物**）
      docs/audit/udc-semantics/COMPONENT-COVERAGE-EXHAUSTION.md
等级：BUNDLE_LITERAL —— udc-frontend/unpacked（1474 js）里 fieldType/paramsType/paramsKey 直读。

本测试在**无 bundle**的仓库内钉住三件事：
  1. 口径互斥穷尽：with_loader_contract + without_loader_contract == remaining_total == 60；
  2. 有 loader 证据的 op 必有 paramsType；无证据的 op 两项均空（不得半填）；
  3. 命名规约**不是铁律**：已知 4 条偏离必须显式登记（防止下一代按 op 名臆造 DTO）。
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_LOADER = ROOT / "docs" / "audit" / "udc-semantics" / "frontend-op-loader-contract.json"
_UNLOC = ROOT / "docs" / "audit" / "udc-semantics" / "frontend-udc-unlocated.json"

pytestmark = pytest.mark.skipif(not _LOADER.exists(), reason="loader 契约件缺失")

# 已知偏离：op -> (paramsType, paramsKey)。改这里必须同步文档与 json。
_NONSTANDARD = {
    "udcCtpManagerTransferSelectGet": (["udcBackendComponentSearchAppPostInputBody"], []),
    "udcEnvCurrentEnvGet": (["udcApplicationSearchNewWithVersionListPostInputBody"], []),
    "udcSandboxResourcesGet": (["udcSandboxBatchCleanStopPostInputBody"], ["body"]),
    "udcSandboxClearDataPost": (["String"], ["body"]),
}


def _load():
    return json.loads(_LOADER.read_text(encoding="utf-8"))


def test_counting_contract_is_mutually_exclusive_and_exhaustive():
    d = _load()
    assert (d["with_loader_contract"] + d["without_loader_contract"]
            == d["remaining_total"] == 60), d["remaining_total"]


def test_scope_matches_remaining_list():
    d, u = _load(), json.loads(_UNLOC.read_text(encoding="utf-8"))
    assert sorted(r["op"] for r in d["records"]) == sorted(u["remaining_ops"])
    assert d["remaining_total"] == u["remaining"] == 60


def test_loader_evidence_implies_params_type():
    for r in _load()["records"]:
        if r["has_loader_contract"]:
            assert r["paramsType"], r["op"]
        else:
            assert not r["paramsType"] and not r["paramsKey"], r["op"]


def test_loader_kinds_are_known():
    kinds = set()
    for r in _load()["records"]:
        kinds.update(r["loader"])
    assert kinds <= {"udcMutationLoader", "udcQueryLoader", "udcApolloQuery",
                     "udcApolloMutation"}, kinds


def test_naming_deviation_set_is_pinned():
    """偏离集合是硬断言：多一条/少一条都要显式同步（防止静默按 op 名臆造 DTO）。"""
    got = {r["op"]: (r["paramsType"], r["paramsKey"])
           for r in _load()["records"] if r["has_loader_contract"] and not r.get("standard_naming")}
    assert got == _NONSTANDARD, got


def test_deviation_count_matches_declared():
    d = _load()
    assert d["naming_deviations"] == len(_NONSTANDARD) == 4


def test_standard_naming_is_derived_not_assumed():
    """标准命名必须由 op 名机械推导（paramsKey 决定 Path/Query/Body 后缀）。"""
    for r in _load()["records"]:
        if not r["has_loader_contract"] or not r.get("standard_naming"):
            continue
        assert r["paramsType"] == [r["expected_if_standard"]], r["op"]


@pytest.mark.parametrize("op", sorted(_NONSTANDARD))
def test_nonstandard_ops_are_in_scope(op):
    assert op in {r["op"] for r in _load()["records"]}


def test_scope_field_does_not_claim_the_stale_raw_count():
    """`scope` 是人读的元数据，历史上曾与 `remaining_total` 自相矛盾（写 62 而实际 60）。

    这类字段无护栏就会漂移：口径更正只改了计数键，`scope` 仍说 62，读者会以为范围是 62 条。
    """
    d = _load()
    scope = d["scope"]
    assert str(d["remaining_total"]) in scope, scope
    # 不得把 62 说成当前范围（62 只允许作为**已作废**的说明出现）
    assert "62 条余量 op" not in scope or "raw 62 已作废" in scope, scope
    assert "62 条余量 op" not in scope.split("（")[0], scope
    assert scope.strip().startswith("frontend-udc-unlocated.json"), scope


def test_declared_counts_match_records_and_unlocated():
    """三个计数键必须同时等于记录条数、余量名单长度，且互斥穷尽。"""
    d, u = _load(), json.loads(_UNLOC.read_text(encoding="utf-8"))
    recs = d["records"]
    assert len(recs) == d["remaining_total"] == u["remaining"], len(recs)
    assert (sum(1 for r in recs if r["has_loader_contract"])
            == d["with_loader_contract"]), d["with_loader_contract"]
    assert (sum(1 for r in recs if not r["has_loader_contract"])
            == d["without_loader_contract"]), d["without_loader_contract"]
    assert d["with_loader_contract"] + d["without_loader_contract"] == len(recs)
