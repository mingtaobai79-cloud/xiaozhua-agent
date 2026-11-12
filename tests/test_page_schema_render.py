"""PageSchemaRenderer — 实体 → 最小可用列表页 pageSchema 树（声明级骨架，宿主执行）。

证据基线：skill seeyon-udc-design-time-build 的 references/page-schema-api-construction.md
（zzprobe jar 1.0.2 失败 → 1.0.4 成功 LIVE 验证）+ 前端 bundle getControlSchema 契约。

离线只产声明级骨架：控件树 + 必填键位 + dataSource 11 键 + 列映射；
列的 ~58 全键与真实标品 deep-copy 离线不可证 → 进 unverified_fields，不臆造。
宿主（Hermes/CC/Codex）拿 pageSchema 填真实 id 后走 submitPage → deploy-normal。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from components.construction.models import NormalizedEntityModel, NormalizedAttribute
from components.construction.page_schema import PageSchemaRenderer, PageSchemaSkeleton


def _model():
    attrs = [
        NormalizedAttribute(name="orderNo", caption="订单号"),
        NormalizedAttribute(name="amount", caption="金额"),
        NormalizedAttribute(name="participants", caption="人员",
                            type="ENTITY", required=True),
    ]
    return NormalizedEntityModel("appx", None, "Order", attrs, caption="订单")


def _entity_meta():
    # 离线占位：宿主执行时换成真实 entity id/fullName
    return {"id": "<entity_id>", "name": "Order", "fullName": "com.seeyon.appx.Order",
            "caption": "订单", "appName": "appx", "appId": "1"}


def _render():
    return PageSchemaRenderer("appx").render(_model(), _entity_meta()).to_dict()


def test_render_builds_three_controls_with_operate_keys():
    out = _render()
    tree = out["pageSchema"]
    child_by_id = tree["childById"]
    types = {v["type"] for v in child_by_id.values()}
    assert {"UdcFilter", "UdcToolBar", "UdcDataGridView"} <= types, f"缺控件：{types}"
    # collectComponentStatus 契约：三 operate 键每个控件都必须存在（缺 → 部署 state=2 TypeError）
    for ctl in child_by_id.values():
        for key in ("topOperates", "actionColumnOperates", "operateButtons"):
            assert key in ctl.get("settings", {}), f"{ctl.get('type')} 缺 {key}"


def test_render_grid_datasource_is_top_level_11_keys():
    out = _render()
    grid = next(v for v in out["pageSchema"]["childById"].values() if v["type"] == "UdcDataGridView")
    ds = grid.get("dataSource")
    assert ds is not None, "grid dataSource 必须在控件顶层（放 settings 里 → 渲染层没选实体）"
    for key in ("type", "subType", "key", "isRoot", "isRef", "dataShape",
                "entity", "fields", "dataTarget", "fieldBindMap", "hiddenFields"):
        assert key in ds, f"dataSource 缺 11 键之一：{key}"
    ent = ds["entity"]
    for key in ("id", "name", "fullName", "caption", "appName", "appId"):
        assert key in ent, f"entity 六件套缺：{key}"
    assert ds["dataShape"] == "LIST"


def test_render_columns_map_from_attributes():
    out = _render()
    grid = next(v for v in out["pageSchema"]["childById"].values() if v["type"] == "UdcDataGridView")
    cols = grid["settings"]["columns"]
    assert len(cols) == 3, "列数应等于属性数"
    assert [c["dataIndex"] for c in cols] == ["orderNo", "amount", "participants"]
    for c in cols:
        assert c.get("componentName") == "列", "列缺 componentName:'列' 渲染器不识别"


def test_render_page_type_is_search_list():
    out = _render()
    assert out["pageSchema"]["pageType"] == "SEARCH_LIST"
    assert out["pageSchema"]["dataSourceDtoList"] is None, "标品 dataSourceDtoList 保持 null"


def test_render_marks_58key_columns_unverified():
    out = _render()
    # 列 ~58 全键离线不可证 → 必须进 unverified，不能臆造全量
    assert any("column" in u for u in out["unverified_fields"]), out["unverified_fields"]
    assert out["schema"] == "udc.construction.page-schema.v1"


def test_render_filter_related_to_grid():
    out = _render()
    tree = out["pageSchema"]
    grid_id = next(k for k, v in tree["childById"].items() if v["type"] == "UdcDataGridView")
    filt = next(v for v in tree["childById"].values() if v["type"] == "UdcFilter")
    assert filt["settings"]["filterSetting"]["relatedComponentId"] == [grid_id]
