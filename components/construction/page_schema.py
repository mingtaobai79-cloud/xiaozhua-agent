"""PageSchemaRenderer — 实体 → 最小可用列表页 pageSchema 树（声明级骨架）。

证据基线：skill xiaozhua-udc-design-time-build / references/page-schema-api-construction.md
（zzprobe LIVE 验证 jar 1.0.4 成功）+ 前端 bundle getControlSchema 契约。

离线只产声明级骨架：三控件（UdcFilter/UdcToolBar/UdcDataGridView）+
collectComponentStatus 三 operate 键 + grid dataSource 11 键 + 列映射。
列 ~58 全键离线不可证 → 进 unverified_fields，不臆造全量。
宿主拿 pageSchema 填真实 entity id / fullName 后走 submitPage → deploy-normal。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_ID = "udc.construction.page-schema.v1"

# grid dataSource 11 键（放控件顶层，非 settings）
_DATA_SOURCE_KEYS = (
    "type", "subType", "key", "isRoot", "isRef",
    "dataShape", "entity", "fields", "dataTarget", "fieldBindMap", "hiddenFields",
)
_ENTITY_META_KEYS = ("id", "name", "fullName", "caption", "stereotype",
                     "category", "supportOrderNo", "appName", "appId")

# collectComponentStatus 契约：每个控件 settings 都须存在这三个键（缺 → 部署 TypeError）
_OPERATE_KEYS = ("topOperates", "actionColumnOperates", "operateButtons")


@dataclass
class PageSchemaSkeleton:
    entity_name: str
    application_id: str
    schema: str = SCHEMA_ID
    readonly_plan: bool = True
    pageSchema: dict[str, Any] = field(default_factory=dict)
    unverified_fields: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "readonly_plan": self.readonly_plan,
            "entity_name": self.entity_name,
            "application_id": self.application_id,
            "pageSchema": self.pageSchema,
            "unverified_fields": self.unverified_fields,
            "evidence": self.evidence,
        }


class PageSchemaRenderer:
    """实体 → 最小列表页 pageSchema 控件树（声明级，宿主执行）。"""

    def __init__(self, app_id: str):
        self.app_id = app_id

    def render(self, model, entity_meta: dict[str, Any]) -> PageSchemaSkeleton:
        """生成列表页骨架。

        model: NormalizedEntityModel（含 attributes）
        entity_meta: 实体元数据六件套 {id, name, fullName, caption, appName, appId}
        """
        x = model.entity_name
        # 控件 id（离线占位，宿主可覆盖）
        filter_id = f"udcFilter_{x.lower()}"
        toolbar_id = f"udcToolBar_{x.lower()}"
        grid_id = f"udcDataGridView_{x.lower()}"
        data_key = f"{grid_id}-{entity_meta.get('id', '')}"

        # entity 完整元数据（11 键 entity 子对象）
        ent_meta = {k: entity_meta.get(k, UNKNOWN_VAL) for k in _ENTITY_META_KEYS}

        # --- UdcDataGridView ---
        grid: dict[str, Any] = {
            "id": grid_id,
            "type": "UdcDataGridView",
            "componentName": "重复表查询",
            "name": x,
            "children": [],
            "extraChildren": [],
            "uiModel": {},
            "settings": {
                "columns": [
                    self._make_column(a, i)
                    for i, a in enumerate(self._attr_names(model))
                ],
                "dataSource": {"entity": ent_meta},
                "borderStyles": ["hborder"],
                "zebra": False,
                "paginationAlign": "right",
                "inputPagenationNum": "10",
                "showSetting": False,
                "enableOrderNumber": True,
                "enableActionColumn": True,
                "topOperates": [],
                "actionColumnOperates": [
                    {"id": f"btn_edit_{x.lower()}", "type": "item", "name": "编辑",
                     "buttonType": "link", "status": {"type": "Simple", "simple": "basic"}},
                    {"id": f"btn_del_{x.lower()}", "type": "item", "name": "删除",
                     "buttonType": "link", "status": {"type": "Simple", "simple": "basic"}},
                ],
                "operateButtons": [],
            },
            # 行操作事件（skill 列页四查形态）：
            #  行编辑 = buildin openPage 穿透详情（不用 ENTITY_EDIT 行内编辑）
            #  行删除 = widget ENTITY_DELETE + ROW_DATA + noticeEntitys（漏则删完不刷新）
            "events": [
                {"id": f"ev_edit_{x.lower()}", "eventType": f"btn_edit_{x.lower()}",
                 "condition": False, "actionType": "buildin", "actionName": "openPage",
                 "pageInfoType": "DETAIL",
                 "paramsMapping": {
                     "PRESET_ID": {"type": "CONTEXT_VARIABLE",
                                    "value": f"CURRENT_ROW id {grid_id}"},
                     "PRESET_DETAIL_PAGE_OPEN_MODE": "edit",
                 }},
                {"id": f"ev_del_{x.lower()}", "eventType": f"btn_del_{x.lower()}",
                 "condition": False, "actionType": "widget", "actionName": "ENTITY_DELETE",
                 "target": grid_id, "callbackDataType": "ROW_DATA",
                 "noticeEntitys": [ent_meta.get("fullName", "")]},
            ],
            # dataSource 11 键在控件顶层（不在 settings）
            "dataSource": {
                "type": "ENTITY",
                "subType": "NORMAL",
                "key": data_key,
                "isRoot": True,
                "isRef": False,
                "dataShape": "LIST",
                "entity": ent_meta,
                "fields": [],
                "dataTarget": grid_id,
                "fieldBindMap": {},
                "hiddenFields": [],
            },
        }

        # --- UdcFilter ---
        filt: dict[str, Any] = {
            "id": filter_id,
            "type": "UdcFilter",
            "componentName": "过滤器",
            "name": "filter",
            "children": [],
            "extraChildren": [],
            "uiModel": {},
            "settings": {
                "filterSetting": {
                    "relatedComponentId": [grid_id],
                    "enableList": ["quickSearch"],
                    "addOperates": [],
                },
                "topOperates": [],
                "actionColumnOperates": [],
                "operateButtons": [],
            },
            "dataSource": {},
        }

        # --- UdcToolBar ---
        # 工具栏按钮（skill L50）：addOperates 对象含 type item / buttonType item /
        # status Simple basic；events 按 eventType=按钮id 绑定（没绑=按钮无行为）
        toolbar_btn = {
            "id": f"tb_add_{x.lower()}", "type": "item", "name": "新增",
            "buttonType": "item", "status": {"type": "Simple", "simple": "basic"},
        }
        toolbar: dict[str, Any] = {
            "id": toolbar_id,
            "type": "UdcToolBar",
            "componentName": "工具栏",
            "name": "toolbar",
            "children": [],
            "extraChildren": [],
            "uiModel": {},
            "settings": {
                "addOperates": [toolbar_btn],
                "operateNum": -1,
                "topOperates": [],
                "actionColumnOperates": [],
                "operateButtons": [],
            },
            "events": [
                {"id": f"tb_ev_add_{x.lower()}", "eventType": toolbar_btn["id"],
                 "condition": False, "actionType": "buildin", "actionName": "openPage",
                 "pageInfoType": "DETAIL",
                 "paramsMapping": {
                     "PRESET_DETAIL_PAGE_OPEN_MODE": "create",
                 }},
            ],
            "dataSource": {},
        }

        child_by_id = {filter_id: filt, toolbar_id: toolbar, grid_id: grid}
        page_schema: dict[str, Any] = {
            "pageType": "SEARCH_LIST",
            "pageUrl": f"{x.lower()}list",
            "urlType": "PC",
            "guid": "<page_guid>",
            "relationGroupId": "<relation_group_id>",
            "masterEntityIds": entity_meta.get("id", ""),
            "version": "2.4.0",
            "extraChildren": [],
            "extraConfig": {},
            "dataSourceDtoList": None,
            "children": [filter_id, toolbar_id, grid_id],
            "childById": child_by_id,
            "settings": {},
        }

        unverified = [
            "column ~58 full keys (deep-copy from standard product page required at execution time)",
            "guid / relationGroupId placeholders (must be filled from udc_page_info)",
            "topOperates / actionColumnOperates button objects (page-specific, not derivable offline)",
            "filterSetting advancedSetting fields (entity-specific field IDs)",
        ]

        return PageSchemaSkeleton(
            entity_name=x,
            application_id=self.app_id,
            schema=SCHEMA_ID,
            pageSchema=page_schema,
            unverified_fields=unverified,
            evidence=[
                "skill:xiaozhua-udc-design-time-build/references/page-schema-api-construction.md",
                "zzprobe LIVE jar 1.0.4 successful deploy",
            ],
        )

    def render_detail_page(self, model, entity_meta: dict[str, Any]) -> PageSchemaSkeleton:
        """详情页骨架（webpack 2879 UdcForm 注册 schema + 61325 UdcSubPage 证据）。

        UdcForm：dataShape SINGLE + settings items（dataSource/condition/returnNull/
        disableAutoLoad）+ rules BIND_ENTITY + onDataLoad 事件。
        UdcSubPage：子页外框（height + activeRule 占位）。
        UdcPanel/弹窗零字段级证据 → 不生成，登记 unverified_fields。
        """
        x = model.entity_name
        ent_meta = {k: entity_meta.get(k, UNKNOWN_VAL) for k in _ENTITY_META_KEYS}
        form_id = f"udcForm_{x.lower()}"
        sub_id = f"udcSubPage_{x.lower()}"
        data_key = f"{form_id}-{entity_meta.get('id', '')}"

        form: dict[str, Any] = {
            "id": form_id,
            "type": "UdcForm",
            "name": "单一记录",
            "containerBox": True,
            "children": [],
            "extraChildren": [],
            "uiModel": {},
            "controlActions": [
                {"value": "create", "label": "新增"},
                {"value": "edit", "label": "编辑"},
                {"value": "view", "label": "查看"},
                {"value": "delete", "label": "删除"},
            ],
            "rules": [{"rule": "BIND_ENTITY"}],
            "settings": {
                "dataSource": {"entity": ent_meta},
                "condition": {
                    "defaultField": "id", "defaultOperator": "EQ",
                    "config": {"enableUpTraverse": False, "enableDownTraverse": False},
                },
                "returnNull": {"visible": True},
                "disableAutoLoad": False,
                "topOperates": [],
                "actionColumnOperates": [],
                "operateButtons": [],
            },
            "events": [
                {"id": f"ev_onDataLoad_{x.lower()}", "eventType": "onDataLoad",
                 "condition": False, "afterAction": "noOperation"},
            ],
            "dataSource": {
                "type": "ENTITY", "subType": "NORMAL", "key": data_key,
                "isRoot": True, "isRef": False, "dataShape": "SINGLE",
                "entity": ent_meta, "fields": [], "dataTarget": form_id,
                "fieldBindMap": {}, "hiddenFields": [],
            },
        }

        # webpack 61325：子页控件（controlActions switch 激活规则；settings height+activeRule）
        sub: dict[str, Any] = {
            "id": sub_id,
            "type": "UdcSubPage",
            "name": "子页面",
            "children": [],
            "extraChildren": [],
            "uiModel": {},
            "controlActions": [{"value": "switch", "label": "执行激活规则"}],
            "settings": {
                "height": "",
                "activeRule": [],
                "topOperates": [],
                "actionColumnOperates": [],
                "operateButtons": [],
            },
        }

        child_by_id = {form_id: form, sub_id: sub}
        page_schema: dict[str, Any] = {
            "pageType": "DETAIL",
            "pageUrl": f"{x.lower()}detail",
            "urlType": "PC",
            "guid": "<page_guid>",
            "relationGroupId": "<relation_group_id>",
            "masterEntityIds": entity_meta.get("id", ""),
            "version": "2.4.0",
            "extraChildren": [],
            "extraConfig": {},
            "dataSourceDtoList": None,
            "children": [form_id, sub_id],
            "childById": child_by_id,
            "settings": {},
        }

        unverified = [
            "UdcPanel / 弹窗（panel）无字段级证据（webpack 该版本 chunk 未见注册体），禁止手拼，宿主先取证再生成",
            "UdcSubPage activeRule / relatedSubPages 内容（页面-子页映射，运行时才有值）",
            "UdcForm condition 具体过滤条件（实体相关，宿主补）",
            "guid / relationGroupId placeholders（must be filled from udc_page_info）",
            "UdcForm columns/fields 渲染键（deep-copy 标品详情页）",
        ]

        return PageSchemaSkeleton(
            entity_name=x,
            application_id=self.app_id,
            schema=SCHEMA_ID,
            readonly_plan=True,
            pageSchema=page_schema,
            unverified_fields=unverified,
            evidence=[
                "webpack 5.3.517 module 2879 UdcForm registration (controlActions/SINGLE/BIND_ENTITY)",
                "webpack 5.3.517 module 61325 UdcSubPage registration (switch/activeRule)",
                "skill:xiaozhua-udc-design-time-build/references/page-schema-api-construction.md",
            ],
        )

    @staticmethod
    def _attr_names(model) -> list[dict[str, Any]]:
        """从 NormalizedEntityModel.attributes 提取列定义。"""
        attrs = []
        for a in (model.attributes or []):
            if hasattr(a, "name"):
                attrs.append({"name": a.name, "caption": getattr(a, "caption", a.name)})
            elif isinstance(a, dict):
                attrs.append({"name": a.get("name", ""), "caption": a.get("caption", a.get("name", ""))})
        return attrs

    @staticmethod
    def _make_column(attr: dict[str, Any], index: int) -> dict[str, Any]:
        """列骨架：只填可离线推导的键，~58 全键由宿主 deep-copy 标品补全。"""
        return {
            "columnId": f"col_{attr['name']}",
            "columnIndex": index,
            "dataIndex": attr["name"],
            "dataFieldCaption": attr.get("caption", attr["name"]),
            "componentName": "列",
            "title": attr.get("caption", attr["name"]),
            "hide": False,
            "widthValue": 120,
        }


UNKNOWN_VAL = "UNKNOWN"

__all__ = ["PageSchemaRenderer", "PageSchemaSkeleton", "SCHEMA_ID", "_DATA_SOURCE_KEYS", "_OPERATE_KEYS"]
