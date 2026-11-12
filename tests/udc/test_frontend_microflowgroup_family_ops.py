"""设计器 bundle micro-flow-group 族 op 全集护栏（第十五轮 · 候选 (viii)）。

**为什么需要**：第九轮 LIVE 在真实 URL 面观测到 `/udc/micro-flow-group/search-list`，
而 674 契约与部署态字节码内均无该 mapping ⇒ 候选 (vi) 需区分三种来源：
**设计器前端 / 客户应用页面 / 其它构件或死路径**。
第十四轮用 scratch 里的 unpacked 产物做了该误判排除，但 scratch 受 24h 闲置清理约束（证据不可耐久）。
本护栏把结论落到**仓内耐久面**：
`docs/audit/artifacts/udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js`
（原始 webpack chunk，非 wakaru 解包产物 —— 后者会丢字面量，见 `test_decompile_loss.py`）。

**钉死的事**（三条独立轴，缺一不可）：
  1. **LOADER 约定**：族内 op 全集 = **6**（`udcMicroFlowGroup` 前缀 + `Post`），
     逐条 paramsType = 同名 + `InputBody`、paramsKey = `body` ⇒ 无 `SearchList`；
  2. **RAW_REST 约定**：同 chunk 内 kebab 字面量 `micro-flow-group` = **0**
     ⇒ 即便走 `ajax.post("/udc/...")` 约定也不可能发出该请求；
  3. **反证不是命名习惯**：同一 chunk 内 `udc*SearchList*` 字面量**确实存在**（他族）
     ⇒ 族内缺 SearchList 是**真负证据**，不是搜索模式造成的假阴性。

证据件：`docs/audit/udc-semantics/frontend-microflowgroup-family-ops.json`。
本文件不含客户业务明细：只引平台 op 名、平台路径与平台构件版本。
（本文件刻意不用反斜杠转义：换行一律 chr(10)。）
"""
import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EVID = (ROOT / "docs" / "audit" / "udc-semantics" / "frontend-microflowgroup-family-ops.json")
CHUNK = (ROOT / "docs" / "audit" / "artifacts" / "udc-frontend-5.3.496" / "chunks" / "src_redux_store_ts.14dc061e.js")

EXPECTED_SHA256 = "6051e1df6c574df74c842f9e4c0714fae5c7ff0df6e86e5ffa5b2d4f994f387d"
EXPECTED_BYTES = 2530724
UNLOCATED = ROOT / "docs" / "audit" / "udc-semantics" / "frontend-udc-unlocated.json"
FAMILY_OPS = (
    "udcMicroFlowGroupBatchMovePost",
    "udcMicroFlowGroupCreatePost",
    "udcMicroFlowGroupDeleteBatchPost",
    "udcMicroFlowGroupDeletePost",
    "udcMicroFlowGroupSelectByTypePost",
    "udcMicroFlowGroupUpdatePost",
)

pytestmark = pytest.mark.skipif(not (EVID.exists() and CHUNK.exists() and UNLOCATED.exists()),
    reason="族 op 证据件 / 仓内 chunk 快照 / 余量名单缺失")


def _evid():
    return json.loads(EVID.read_text(encoding="utf-8"))


def _chunk_text():
    return CHUNK.read_bytes().decode("utf-8", errors="replace")


def test_chunk_snapshot_is_byte_identical_to_the_pinned_sha256():
    got = hashlib.sha256(CHUNK.read_bytes()).hexdigest()
    assert got == EXPECTED_SHA256, (got, EXPECTED_SHA256)
    assert CHUNK.stat().st_size == 2530724


def test_evidence_json_pins_the_same_chunk_digest():
    src = _evid()["source_durable"]
    assert src["sha256"] == EXPECTED_SHA256
    assert src["bytes"] == 2530724
    assert src["path"].replace("\\", "/") == "docs/audit/artifacts/udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js"


def test_family_op_set_in_chunk_is_exactly_the_six_declared_ops():
    s = _chunk_text()
    found = sorted(set(re.findall(r"udcMicroFlowGroup[A-Za-z0-9]*", s)))
    expected = sorted(set(FAMILY_OPS) | {o + "InputBody" for o in FAMILY_OPS})
    assert found == expected, (found, expected)
    assert len(FAMILY_OPS) == 6


def test_no_search_list_member_inside_the_family():
    s = _chunk_text()
    fam = [t for t in re.findall(r"udcMicroFlowGroup[A-Za-z0-9]*", s) if "SearchList" in t]
    assert fam == [], fam


def test_each_family_op_binds_body_with_matching_inputbody_paramstype():
    s = _chunk_text()
    for op in FAMILY_OPS:
        marker = "fieldType:" + chr(34) + op + chr(34)
        i = s.find(marker)
        assert i >= 0, op
        blk = s[i:i + 400]
        assert "paramsType:" + chr(34) + op + "InputBody" + chr(34) in blk, op
        assert "paramsKey:" + chr(34) + "body" + chr(34) in blk, op


def test_kebab_micro_flow_group_literal_is_absent_from_the_chunk():
    assert _chunk_text().count("micro-flow-group") == 0


def test_chunk_does_use_the_raw_rest_convention_somewhere():
    """负证据的成立前提：该 chunk 确实存在「直接写 REST 路径」的约定。"""
    s = _chunk_text()
    assert "/udc/microflow/disable-last-version-metadata" in s
    assert "/udc/refer-config/list" in s
    assert s.count("/udc/") >= 10


def test_naming_habit_counter_example_searchlist_exists_in_same_chunk():
    s = _chunk_text()
    assert "udcDataTransferObjectSearchListPost" in s
    assert "udcDataTransferObjectSearchListPostInputBody" in s
    assert s.count("search-list") == 0


def test_evidence_json_records_the_three_conclusion_axes():
    d = _evid()
    assert d["family_ops"]["op_count"] == 6
    assert d["family_ops"]["raw_literal_token_count"] == 12
    assert d["family_ops"]["search_list_present"] is False
    assert d["kebab_path_literals"]["micro-flow-group"] == 0
    assert d["kebab_path_literals"]["search-list"] == 0
    ce = d["counter_example_naming_habit"]["evidence_in_same_chunk"]
    assert any("SearchList" in x for x in ce)


def test_evidence_json_does_not_overclaim_beyond_the_designer_frontend():
    d = _evid()
    c = d["conclusion"]
    assert c["excluded"] == "设计器前端（LOADER 约定 + RAW_REST 约定，双轴均否）"
    assert set(c["still_open"]) == {"客户应用页面", "其它构件提供", "死路径"}
    assert c["searchlist_route_status"].startswith("UNVERIFIED")
    assert len(d["limitations"]) >= 3


def test_evidence_json_has_no_client_identifiers():
    raw = EVID.read_text(encoding="utf-8")
    # 先剥掉本件已声明为平台事实的两个长数字串：chunk sha256 与字节数。
    scrubbed = raw.replace(EXPECTED_SHA256, "").replace(str(EXPECTED_BYTES), "")
    assert not re.search(r"[0-9]{6,}", scrubbed), "证据件出现 6 位以上数字串（疑似客户标识）"
    assert "appId" not in raw


def test_family_ops_are_not_in_the_60_unlocated_list():
    """族内 6 条 op 早已归位 udc-web，故不得出现在余量名单里。"""
    u = json.loads((ROOT / "docs" / "audit" / "udc-semantics" / "frontend-udc-unlocated.json").read_text(encoding="utf-8"))
    remaining = set(u["remaining_ops"])
    assert remaining & set(FAMILY_OPS) == set()
    assert not any("microflowgroup" in o.lower() for o in remaining)

