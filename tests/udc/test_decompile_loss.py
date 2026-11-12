"""反编译丢失面护栏（2026-10-15 第六轮）。

**为什么需要**：本仓库把原始 chunk（`docs/audit/artifacts/udc-frontend-5.3.496/chunks/`）
与 wakaru 解包产物（`unpacked/`）当作**可互换**的证据源 —— 事实并非如此。原始 chunk 里被
decompiler 丢掉的模块，其字符串字面量在解包产物中会消失。

**后果（本轮发现）**：任何「op X 在 bundle 里 0 命中」这类**负面结论**，必须回到原始 chunk 复检，
否则会把「反编译丢失」误读成「前端从未引用 X」。实测 346 条 harvest op 中有 **6 条**
存在于原始 chunk、却不在解包产物里，其中 2 条 udc* 由 udc-web 契约**独立推导得出**
（`udcDesignMetadataAggEntityExcludeBootGet` / `udcPageInfoDeletePost`）=> 反证「解包产物是完整事实源」。

**范围界定**：本护栏只覆盖该 6 条**已知**丢失；它**不**声称 6 是上界（原始 chunk 自身受采集完整度限制）。
本节证据的原始 chunk 侧在 scratch（`<HERMES_HOME>/cache/scratch/udc-frontend/chunks/`，158 js），
受 24h 闲置清理约束 —— 故 scratch 缺失时本文件整体 skip，而不是误判为 PASS。
"""
import json
from pathlib import Path

import pytest

from components.udc.graphql_op_naming import derive_ops

ROOT = Path(__file__).resolve().parents[2]
EXTRACTION = ROOT / "docs/audit/udc-semantics" / "frontend-extraction.json"
API = (ROOT / "docs" / "audit" / "artifacts" / "udc-web-5.3.517-contracts" / "_api_full.json")
CHUNKS_PINNED = ROOT / "docs" / "audit" / "artifacts" / "udc-frontend-5.3.496" / "chunks"
CHUNKS = Path("<HERMES_HOME>/cache/scratch/udc-frontend/chunks")
DECODED = Path("<HERMES_HOME>/cache/scratch/udc-frontend/unpacked")

# 已知丢失（钉死）：改这里必须同步 COMPONENT-RELOCATION.md 第 6.3 节。
KNOWN_LOST = (
    "appCommonImageSearch",
    "appCommonImageStoreCategoryGet",
    "cipManagerManageSelectActivexCapabilityEnumGet",
    "organizationOrgMemberAvatarIdsPost",
    "udcDesignMetadataAggEntityExcludeBootGet",
    "udcPageInfoDeletePost",
)

pytestmark = pytest.mark.skipif(
    not (CHUNKS.is_dir() and DECODED.is_dir() and API.exists() and EXTRACTION.exists()),
    reason="原始 chunk / 解包产物 / 契约件缺失（scratch 受 24h 清理约束）",
)


def _ops():
    return list(json.loads(EXTRACTION.read_text(encoding="utf-8"))["frontend_ops"]["ops"])


_CACHE = {}


def _corpus(directory):
    """一次性把 *.js 读进内存（护栏慢 = 护栏会被跳过，故必须在会话内缓存）。"""
    key = str(directory)
    if key not in _CACHE:
        _CACHE[key] = [(p.name, p.read_text(encoding="utf-8", errors="replace"))
                       for p in sorted(directory.rglob("*.js"))]
    return _CACHE[key]


def _hits(op, directory):
    import re
    pat = re.compile(re.escape(op))
    return sorted(name for name, text in _corpus(directory) if pat.search(text))


def _lost():
    return [o for o in _ops() if _hits(o, CHUNKS) and not _hits(o, DECODED)]


def test_decompile_loss_is_pinned_and_does_not_grow_silently():
    """丢失集合是硬断言：多一条/少一条都必须显式同步文档（防静默丢失被当理所当然）。"""
    assert sorted(_lost()) == sorted(KNOWN_LOST), sorted(_lost())


@pytest.mark.parametrize("op", KNOWN_LOST)
def test_lost_op_is_present_in_raw_chunks(op):
    """每条已知丢失都必须在原始 chunk 里有字面量（否则「丢失」说法本身无依据）。"""
    assert _hits(op, CHUNKS), op


@pytest.mark.parametrize("op", KNOWN_LOST)
def test_lost_op_is_absent_from_decompiled_bundle(op):
    """且确实在解包产物里 0 命中 —— 两侧对照才构成「丢失」而不是「前端没有」。"""
    assert not _hits(op, DECODED), op


def test_some_lost_ops_are_independently_derived_from_udc_web_contract():
    """★ 关键反证：丢失条里有 udc* 且由 udc-web 契约独立推导 => 解包产物不是完整事实源。"""
    derived = set(derive_ops(json.loads(API.read_text(encoding="utf-8"))))
    overlapped = sorted(o for o in _lost() if o.startswith("udc") and o in derived)
    assert overlapped == ["udcDesignMetadataAggEntityExcludeBootGet",
                          "udcPageInfoDeletePost"], overlapped


def test_remaining_and_relocated_lists_are_unaffected_by_the_loss():
    """范围界定：60 余量 + 32 归位**不**受该缺口影响 —— 每条在解包产物内仍有 >=1 处字面量。

    这是「本轮 62->60 的更正是可信的」这一claim 的必要前提：如果名单里混入解包丢失条，
    那 60 这个数就是假的。
    """
    spec = json.loads((ROOT / "docs" / "audit" / "udc-semantics"
                       / "frontend-udc-unlocated.json").read_text(encoding="utf-8"))
    scope = list(spec["remaining_ops"]) + list(spec["relocated_ops"])
    assert len(scope) == 92, len(scope)
    missing = [o for o in scope if not _hits(o, DECODED)]
    assert missing == [], missing


def test_pinned_snapshot_chunk_is_a_strict_subset_of_the_raw_chunk_set():
    """仓内快照只有 store 那个 chunk —— 记录该事实，防止有人以为仓内已有全量 chunk。"""
    pinned = sorted(p.name for p in CHUNKS_PINNED.rglob("*.js"))
    raw = sorted(p.name for p in CHUNKS.rglob("*.js"))
    assert len(pinned) == 1, pinned
    assert set(pinned) <= set(raw), (pinned, len(raw))
