"""BI 域(cdp-data) 与 流程域(bpm) 设计态只读契约测试（活体取证固化）。

证据来源：docs/audit/udc-semantics/NAV-LIVE-CAPTURE-20261012-ROUND2.md
"""
import json

from components.udc.bi_flow_ops import (
    BI_DATANAALYSIS_TABS, FLOW_PAGE_TABS, FLOW_TEMPLATE_KINDS,
    bi_ops, flow_ops, to_catalog_json,
)


def test_bi_ops_all_cdp_data_service():
    ops = bi_ops()
    assert len(ops) >= 4
    for op in ops:
        assert op.service == "cdp-data", op.op_id
        assert op.path.startswith("/service/cdp-data/"), op.path
        assert op.readonly is True
        assert op.method in {"GET", "POST"}


def test_flow_ops_all_bpm_service():
    ops = flow_ops()
    assert ops
    for op in ops:
        assert op.service == "bpm", op.op_id
        assert op.path.startswith("/service/bpm/"), op.path


def test_bi_dataanalysis_tabs_dom_proven():
    assert BI_DATANAALYSIS_TABS == ("数据集", "数据流", "指标管理", "报表管理")


def test_flow_page_tabs_and_kinds_dom_proven():
    assert FLOW_PAGE_TABS == ("流程模板", "流程配置")
    assert FLOW_TEMPLATE_KINDS == ("固定流程", "自由流程")


def test_catalog_json_roundtrip():
    cat = to_catalog_json()
    # 可落盘 + 可回读（事实件契约）
    blob = json.loads(json.dumps(cat, ensure_ascii=False))
    assert blob["schema"] == cat["schema"]
    assert len(blob["bi"]["ops"]) == len(bi_ops())
    assert len(blob["flow"]["ops"]) == len(flow_ops())
    # 边界声明在场（防止日后误把 POST 查询当只读放行）
    assert any("POLICY_DENIED" in b for b in blob["boundary"])


def test_evidence_level_capped_at_observed_live():
    cat = to_catalog_json()
    for op in cat["bi"]["ops"] + cat["flow"]["ops"]:
        # 活体取证封顶 OBSERVED_LIVE，不得冒称 VERIFIED_STATIC_BYTECODE
        assert op["evidence"] in {"OBSERVED_LIVE", "OBSERVED"}, op["op_id"]
