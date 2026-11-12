"""优先级 2：列表页工具栏按钮+行操作事件 / 详情页 UdcForm+子页 骨架（证据驱动）。

证据基线：
- 列表页行操作 + 工具栏按钮：skill page-schema-api-construction（行删除 widget
  ENTITY_DELETE + callbackDataType ROW_DATA + target 表格id + noticeEntitys；行编辑
  buildin openPage + pageInfoType DETAIL + paramsMapping PRESET_ID/PRESET_DETAIL_PAGE_OPEN_MODE
  含 CURRENT_ROW；工具栏按钮 events 按 eventType=按钮id 绑定，没绑=按钮无行为）。
- 详情页 UdcForm 控件注册 schema：webpack 5.3.517 module 2879（controlActions
  create/edit/view/delete、dataSource dataShape SINGLE、settings items
  dataSource/condition/returnNull/disableAutoLoad、rules BIND_ENTITY）。
- 子页 UdcSubPage：webpack module 61325（controlActions switch、settings height+activeRule）。
- UdcPanel/弹窗：无字段级证据 → 不生成，登记 unverified_fields。
纪律：readonly_plan=True（声明级，宿主执行）；按钮/事件给结构不给臆造文案。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from components.construction.models import NormalizedEntityModel, NormalizedAttribute
from components.construction.page_schema import PageSchemaRenderer


def _model():
    attrs = [NormalizedAttribute(name="orderNo", caption="订单号"),
             NormalizedAttribute(name="amount", caption="金额")]
    return NormalizedEntityModel("appx", None, "Order", attrs, caption="订单")


def _meta():
    return {"id": "<entity_id>", "name": "Order", "fullName": "com.seeyon.appx.Order",
            "caption": "订单", "appName": "appx", "appId": "1"}


def _list():
    return PageSchemaRenderer("appx").render(_model(), _meta()).to_dict()


def _detail():
    return PageSchemaRenderer("appx").render_detail_page(_model(), _meta()).to_dict()


def _ctl(tree, ctype):
    return next(v for v in tree["childById"].values() if v["type"] == ctype)


# ---------- 列表页（render） ----------

def test_toolbar_button_object_shape():
    out = _list()
    tb = _ctl(out["pageSchema"], "UdcToolBar")
    btn = tb["settings"]["addOperates"][0]
    assert btn["type"] == "item" and btn["buttonType"] == "item"
    assert btn["status"] == {"type": "Simple", "simple": "basic"}
    assert btn["id"], "按钮需 nanoId（events 按 eventType=按钮id 绑定）"


def test_toolbar_event_bound_to_button_id():
    out = _list()
    tb = _ctl(out["pageSchema"], "UdcToolBar")
    btn = tb["settings"]["addOperates"][0]
    ev = tb["events"][0]
    assert ev["eventType"] == btn["id"], "事件必须挂到按钮 id（没绑=按钮无行为）"
    assert ev["id"], "事件需 nanoId"


def test_grid_row_delete_widget_form():
    out = _list()
    grid = _ctl(out["pageSchema"], "UdcDataGridView")
    assert any(a.get("buttonType") == "link" for a in grid["settings"]["actionColumnOperates"]), \
        "行操作用 buttonType:link 放操作列"
    d = next(e for e in grid["events"] if e.get("actionName") == "ENTITY_DELETE")
    assert d["actionType"] == "widget"
    assert d["callbackDataType"] == "ROW_DATA"
    assert d["target"] == grid["id"]
    assert d["noticeEntitys"] == ["com.seeyon.appx.Order"], "漏 noticeEntitys 删完不刷新"


def test_grid_row_edit_openpage_detail_form():
    out = _list()
    grid = _ctl(out["pageSchema"], "UdcDataGridView")
    op = next(e for e in grid["events"] if e.get("actionName") == "openPage")
    assert op["actionType"] == "buildin" and op["pageInfoType"] == "DETAIL"
    pm = op["paramsMapping"]
    assert "PRESET_ID" in pm and "PRESET_DETAIL_PAGE_OPEN_MODE" in pm
    assert "CURRENT_ROW" in str(pm["PRESET_ID"]), "当前行取参 = CONTEXT_VARIABLE CURRENT_ROW <字段> <表格id>"


# ---------- 详情页（render_detail_page） ----------

def test_detail_has_udc_form_single_datasource():
    out = _detail()
    tree = out["pageSchema"]
    assert tree["pageType"] == "DETAIL"
    form = _ctl(tree, "UdcForm")
    assert form["dataSource"]["dataShape"] == "SINGLE"
    ent = form["dataSource"]["entity"]
    assert ent["id"] == "<entity_id>" and ent["fullName"] == "com.seeyon.appx.Order"


def test_detail_form_settings_and_rules_match_registration():
    out = _detail()
    form = _ctl(out["pageSchema"], "UdcForm")
    st = form["settings"]
    for key in ("dataSource", "condition", "returnNull", "disableAutoLoad"):
        assert key in st, f"UdcForm settings 缺注册键：{key}"
    assert st["condition"].get("defaultField") == "id"
    assert any(x.get("rule") == "BIND_ENTITY" for x in form.get("rules", []))


def test_detail_subpage_present_panel_not():
    out = _detail()
    tree = out["pageSchema"]
    sub = _ctl(tree, "UdcSubPage")
    assert sub is not None, "需求：子页面+外框 → UdcSubPage 骨架"
    assert not any(v["type"] == "UdcPanel" for v in tree["childById"].values()), \
        "UdcPanel 无字段级证据，禁止手拼"
    assert any("panel" in u.lower() for u in out["unverified_fields"])


def test_detail_readonly_plan_flag():
    out = _detail()
    assert out["readonly_plan"] is True
