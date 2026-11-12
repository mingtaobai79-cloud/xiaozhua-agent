"""宿主入口暴露生成器（a7 收口）：bootstrap() 返回 dict 增加生成面能力。

证据：生成器全部已在 construction 层落地并有单测（列表页/详情页/微流程/
元信息 6 生成器 + 部署方案），bootstrap 只是暴露入口，不新增逻辑。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from seeyon_host_bootstrap import bootstrap


def _b():
    return bootstrap()  # 离线只读，无凭据


def test_bootstrap_exposes_list_page_schema_generator():
    out = _b()["list_page_schema"]("appx", "Order", "订单",
                                   [{"name": "orderNo", "type": "STRING", "caption": "订单号"}],
                                   {"id": "1", "fullName": "com.seeyon.appx.Order", "caption": "订单",
                                    "name": "Order", "appName": "appx", "appId": "1"})
    types = {v["type"] for v in out["pageSchema"]["childById"].values()}
    assert {"UdcFilter", "UdcToolBar", "UdcDataGridView"} <= types
    assert out["readonly_plan"] is True


def test_bootstrap_exposes_detail_page_schema_generator():
    out = _b()["detail_page_schema"]("appx", "Order", "订单",
                                     [{"name": "orderNo", "type": "STRING", "caption": "订单号"}],
                                     {"id": "1", "fullName": "com.seeyon.appx.Order", "caption": "订单",
                                      "name": "Order", "appName": "appx", "appId": "1"})
    assert out["pageSchema"]["pageType"] == "DETAIL"
    assert any(v["type"] == "UdcForm" for v in out["pageSchema"]["childById"].values())


def test_bootstrap_exposes_microflow_and_metadata_generators():
    b = _b()
    mf = b["microflow_create_body"]("queryOrder", "查询订单", "1", {"nodes": []})
    assert mf["dataSchema"] == '{"nodes": []}' and mf["type"] == "SERVICE"
    idx = b["index_body"]("订单号索引", 1, ["3729580767880732084"])
    assert idx["fieldIds"] == "3729580767880732084"
    enum = b["enum_body"](1, "订单状态", "ddzt")
    assert enum["orderNo"] == 100
    ev = b["event_body"](1, "订单审核事件", "ddshsj", 2)
    assert ev["eventData"] == 2
    fp = b["filter_plan_body"]("appx", 1, 9, "usOJ", "Order", "已审核",
                                [{"attribute_id": "3", "value": "CHECKED"}])
    assert fp["body"]["planType"] == 2
    assert b["capabilities"]["readonly_only"] is True
    assert b["allow_network"] is False


def test_microflow_unknown_action_is_visible_to_host(monkeypatch):
    from components.construction.microflow import check_schema_body
    from components.udc.microflow import capability_registry
    schema = {'nodes': [{'nodeId': 'n1', 'type': 'ACTIVITY', 'actionType': 'NONEXISTENT_ACTION'}]}
    result = _b()['microflow_create_body']('demo', 'demo', '1', schema)
    assert any('NONEXISTENT_ACTION' in msg and 'UNVERIFIED' in msg for msg in result.get('unknowns', []))
    assert 'unknowns' not in check_schema_body(result)
    with monkeypatch.context() as isolated:
        isolated.setitem(sys.modules, 'components.udc.microflow_ui_constraints', None)
        result = _b()['microflow_create_body']('demo', 'demo', '1', schema)
        assert 'UNVERIFIED: microflow UI validation unavailable' in result['unknowns']
        assert 'unknowns' not in check_schema_body(result)
    with monkeypatch.context() as isolated:
        isolated.setitem(sys.modules, 'components.udc.microflow_constraints', None)
        result = _b()['microflow_create_body']('demo', 'demo', '1', schema)
        assert 'UNVERIFIED: microflow node validation unavailable' in result['unknowns']
    with monkeypatch.context() as isolated:
        cap = capability_registry.Capability('NONEXISTENT_ACTION', 1, '0%', '', '', 'CONSTRUCTED')
        isolated.setattr(capability_registry, 'load', lambda: {'NONEXISTENT_ACTION': cap})
        result = _b()['microflow_create_body']('demo', 'demo', '1', schema)
        assert any('NONEXISTENT_ACTION' in msg and 'CONSTRUCTED' in msg for msg in result.get('unknowns', []))
    monkeypatch.setattr(capability_registry, 'load', lambda: {})
    result = _b()['microflow_create_body']('demo', 'demo', '1', schema)
    assert any('NONEXISTENT_ACTION' in msg and 'UNVERIFIED' in msg for msg in result['unknowns'])
    def fail(_schema):
        raise RuntimeError('sensitive marker')
    monkeypatch.setattr(capability_registry, 'advisory', fail)
    result = _b()['microflow_create_body']('demo', 'demo', '1', schema)
    assert 'UNVERIFIED: capability advisory unavailable' in result['unknowns']
    assert 'sensitive marker' not in str(result)


def test_bootstrap_no_new_network_capability():
    b = _b()
    assert b["allow_network"] is False
    assert b["capabilities"]["credential_mode"] == "path-ref-only"


def test_list_page_schema_fullname_default_is_placeholder_not_fabricated():
    """审计点：fullName 缺省必须是明显占位符，不得臆造 com.seeyon.{app}.{Entity} 浅包名。

    真实 fullName 是深包名（证据：com.seeyon.udc.deduction.domain.entity.DeductionMap），
    离线推不出包结构；臆造的 plausable 包名会让宿主误当真值用。
    """
    out = _b()["list_page_schema"]("appx", "Order", "订单",
                                   [{"name": "orderNo", "type": "STRING", "caption": "订单号"}],
                                   {"id": "1"})  # 只给 id，不给 fullName
    grid = next(v for v in out["pageSchema"]["childById"].values()
                if v["type"] == "UdcDataGridView")
    fn = grid["dataSource"]["entity"]["fullName"]
    assert fn == "<entity_full_name>", f"fullName 缺省臆造了包名：{fn}"


def test_list_page_schema_appname_default_is_obvious_placeholder():
    """appName 缺省=application_id（可推）；appId 缺省：无尾数段出占位符不臆造。"""
    out = _b()["list_page_schema"]("appx", "Order", "订单",
                                   [{"name": "orderNo", "type": "STRING", "caption": "订单号"}],
                                   {"id": "1"})
    grid = next(v for v in out["pageSchema"]["childById"].values()
                if v["type"] == "UdcDataGridView")
    ent = grid["dataSource"]["entity"]
    assert ent["appName"] == "appx", "appName 缺省用 application_id（即 app 名，可推）"
    assert ent["appId"] == "<numeric_app_id>", \
        f"application_id 无尾数段，appId 出占位符不臆造：{ent['appId']}"


def test_list_page_schema_appid_extracts_trailing_digits():
    """有尾数段的 application_id 提取数字 appId（skill：app name 末尾数段即 appId）。"""
    out = _b()["list_page_schema"]("app9000000000000000001", "Order", "订单",
                                   [{"name": "orderNo", "type": "STRING", "caption": "订单号"}],
                                   {"id": "1"})
    grid = next(v for v in out["pageSchema"]["childById"].values()
                if v["type"] == "UdcDataGridView")
    ent = grid["dataSource"]["entity"]
    assert ent["appId"] == "9000000000000000001", f"尾数段应提取为 appId：{ent['appId']}"
    assert ent["appName"] == "app9000000000000000001"
