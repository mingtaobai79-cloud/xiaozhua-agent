"""R5: 微流程只读证据可被 evidence-ledger / audit-bundle 离线聚合的最小验证 (A3).

输入 = docs/operation-contracts/udc/microflow/microflow-ledger-inputs/ 下 7 份 JSON
（main 离线取证落盘，取材 registry locator + test2 活体 raw + 网关事实 md）。
证据等级纪律：A2 未 LIVE，http-probe 一律 UNVERIFIED，bundle live_pass_count==0。
全部离线，network=disabled，不升级证据等级。
"""
import json
from pathlib import Path

from components.evidence_ledger import build_evidence_ledger
from components.audit_bundle import build_audit_bundle

L = Path(__file__).parents[1] / "docs" / "operation-contracts" / "udc" / "microflow" / "microflow-ledger-inputs"
CONTRACTS = {"udc.microflow.function_node_tree", "udc.datatype.get_all", "udc.applog.select_by_id"}


def _load(name: str):
    return json.loads((L / name).read_text(encoding="utf-8-sig"))


def test_ledger_aggregates_three_static_contracts_and_three_http_probes():
    ledger = build_evidence_ledger(udc_json=_load("udc.json"), runtime=_load("runtime.json"), http=_load("http.json"))
    entries = ledger["entries"]
    static = [e for e in entries if e["source"] == "udc-static"]
    probes = [e for e in entries if e["source"] == "http-probe"]
    # 3 条微流程只读契约 fact（registry locator 已绑定 artifact+version+class+method+sha）
    assert {e["claim"] for e in static} == CONTRACTS
    assert all(e["status"] == "FACT" for e in static)
    for e in static:
        r = e["result"]
        for key in ("artifact", "version", "class", "method", "class_sha256", "path", "http_method", "response_type", "evidence_level"):
            assert key in r, f"locator 缺要素 {key}"
        assert r["write"] is False and r["http_method"] == "GET"
    # 3 条活体 probe 均 UNVERIFIED（test2 微流程路径段 404，A2 未 LIVE，不升 PASS）
    assert len(probes) == 3 and all(e["status"] == "UNVERIFIED" for e in probes)
    # 无冲突 + 离线 + 部分验证（含 UNVERIFIED 但不全 FAIL/CONFLICT）
    assert ledger["conflict_count"] == 0
    assert ledger["network"] == "disabled"
    assert ledger["status"] == "PARTIALLY_VERIFIED"


def test_audit_bundle_offline_with_no_live_pass():
    paths = {
        "version_audit": str(L / "version_audit.json"),
        "runtime": str(L / "runtime.json"),
        "http": str(L / "http.json"),
        "path_matrix": str(L / "path_matrix.json"),
        "impact_graph": str(L / "impact_graph.json"),
        "evidence_context": str(L / "evidence_context.json"),
    }
    bundle = build_audit_bundle(paths)
    assert bundle["network"] == "disabled" and bundle["mode"] == "offline"
    assert not bundle["missing_inputs"], "6 输入须全部就位"
    assert bundle["status_summary"]["live_pass_count"] == 0
    assert bundle["status_summary"]["unverified_count"] >= 3
    gaps = " ".join(bundle["gaps"])
    # A2 精确缺口必须被聚进 gaps（token 过期 + 微流程路径段 404 + Long 型 target）
    assert "token" in gaps and "404" in gaps
