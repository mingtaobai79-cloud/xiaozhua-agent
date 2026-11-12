"""页面事件/动作 值域模型与校验器 —— 证据驱动，只锁可证值域。

证据基线（docs/audit/udc-semantics/UDC-MAINLINE-AUDIT.md §3 + page-menu-source-audit.md）：
- 动作类型 actionType 真实值域：buildin | widget | microflow | enevtThrow
  （原文拼写 enevtThrow 是平台 bundle 原样，禁止"修正"）
- 行编辑 = buildin/openPage 穿透详情页 + paramsMapping（PRESET_ID / PRESET_DETAIL_PAGE_OPEN_MODE）
- 行删除 = widget + actionName=ENTITY_DELETE + callbackDataType=ROW_DATA + noticeEntitys
- 面板开/关 = widget + targetAction=panel_openPanel/panel_closePanel + target
- 微流程按钮 = actionType=microflow 必带真实 microflow id（否则按钮只渲染无行为）
- 事件挂载点：pageSchema.childById[controlId].events[]（eventDefine 只登记元数据，
  不能替代行为绑定；没绑 events 的按钮不会有行为）
- 对象边界：实体规则 VALIDATE 组 ≠ 页面动作 VALIDATE_ENTITY（勿混）

校验器只做「值域 + 绑定完整性」检查（离线可证面）；不证明运行态行为，
  不替代设计器页面按钮的抓包等价性验证（那需宿主 Network 逐字捕获）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_ID = "udc.construction.page-event.v1"

# ---- 值域（全部有 bundle/源码证据）----
ACTION_TYPES: frozenset[str] = frozenset({"buildin", "widget", "microflow", "enevtThrow"})

# buildin 动作名（openPage 穿透详情/新增；值域随版本，这里只锁已证）
BUILTIN_ACTIONS: frozenset[str] = frozenset({"openPage"})
# widget 动作名（已证）
WIDGET_ACTIONS: frozenset[str] = frozenset({"ENTITY_DELETE", "panel_openPanel", "panel_closePanel"})
# pageInfoType（buildin openPage 目标页类型）
PAGE_INFO_TYPES: frozenset[str] = frozenset({"DETAIL", "LIST"})
# DETAIL 打开模式
DETAIL_OPEN_MODES: frozenset[str] = frozenset({"create", "edit", "view"})


@dataclass
class PageEvent:
    """单个控件 events[] 项（childById[controlId].events）。"""
    event_id: str
    event_type: str
    action_type: str
    action_name: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def target(self) -> Any:
        return self.raw.get("target")

    @property
    def params_mapping(self) -> dict[str, Any]:
        return self.raw.get("paramsMapping") or {}


class PageEventValidator:
    """事件/动作值域 + 绑定完整性校验（离线可证面）。"""

    def __init__(self, events: list[dict[str, Any]] | None = None):
        self.events = [PageEvent(
            event_id=str(e.get("id", "")),
            event_type=str(e.get("eventType", "")),
            action_type=str(e.get("actionType", "")),
            action_name=str(e.get("actionName", "")),
            raw=e,
        ) for e in (events or [])]

    def errors(self) -> list[str]:
        out: list[str] = []
        for e in self.events:
            if not e.event_id:
                out.append(f"事件缺 id（事件绑定需唯一 id）")
            if e.action_type and e.action_type not in ACTION_TYPES:
                out.append(
                    f"事件 {e.event_id} actionType={e.action_type!r} 不在值域 {sorted(ACTION_TYPES)}"
                )
            out.extend(self._check_action(e))
        return out

    def warnings(self) -> list[str]:
        out: list[str] = []
        for e in self.events:
            out.extend(self._check_binding(e))
        return out

    @staticmethod
    def _check_action(e: PageEvent) -> list[str]:
        out: list[str] = []
        at, an = e.action_type, e.action_name
        if at == "buildin":
            if an not in BUILTIN_ACTIONS:
                out.append(f"事件 {e.event_id} buildin actionName={an!r} 未见证据值域 {sorted(BUILTIN_ACTIONS)}")
            if an == "openPage":
                pit = e.params_mapping.get("pageInfoType")
                if pit not in PAGE_INFO_TYPES:
                    out.append(f"事件 {e.event_id} openPage 缺 pageInfoType（值域 {sorted(PAGE_INFO_TYPES)}）")
                mode = e.params_mapping.get("PRESET_DETAIL_PAGE_OPEN_MODE")
                if pit == "DETAIL" and mode not in DETAIL_OPEN_MODES and mode is not None:
                    out.append(f"事件 {e.event_id} PRESET_DETAIL_PAGE_OPEN_MODE={mode!r} 越界 {sorted(DETAIL_OPEN_MODES)}")
                # 行编辑穿透详情需 PRESET_ID
                if pit == "DETAIL" and mode in {"edit", "view"} and "PRESET_ID" not in e.params_mapping:
                    out.append(f"事件 {e.event_id} 行穿透详情缺 PRESET_ID（无法定位目标行）")
        elif at == "widget":
            if an not in WIDGET_ACTIONS:
                out.append(f"事件 {e.event_id} widget actionName={an!r} 未见证据值域 {sorted(WIDGET_ACTIONS)}")
            if an == "ENTITY_DELETE" and e.callback_datatype() != "ROW_DATA":
                out.append(f"事件 {e.event_id} ENTITY_DELETE 缺 callbackDataType=ROW_DATA（删完不刷新）")
            if an in {"panel_openPanel", "panel_closePanel"} and not e.target:
                out.append(f"事件 {e.event_id} 面板动作缺 target（面板控件 id）")
        elif at == "microflow":
            if not e.microflow_ref():
                out.append(f"事件 {e.event_id} microflow 动作缺真实微流程 id（无行为绑定）")
        return out

    @staticmethod
    def _check_binding(e: PageEvent) -> list[str]:
        # 软检查：widget 动作未给 target/microflow 动作未给 id → 按钮只渲染无行为
        out: list[str] = []
        if e.action_type == "widget" and e.action_name in {"panel_openPanel", "panel_closePanel"} and not e.target:
            out.append(f"事件 {e.event_id} 面板动作未绑 target → 行为不生效（UNVERIFIED）")
        if e.action_type == "microflow" and not e.microflow_ref():
            out.append(f"事件 {e.event_id} 微流程按钮未绑 microflow id → 只渲染无行为（UNVERIFIED）")
        return out

    def status(self) -> str:
        return "FAIL" if self.errors() else ("UNVERIFIED" if self.warnings() else "PASS")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_ID,
            "status": self.status(),
            "errors": self.errors(),
            "warnings": self.warnings(),
            "events": [
                {"id": e.event_id, "eventType": e.event_type,
                 "actionType": e.action_type, "actionName": e.action_name}
                for e in self.events
            ],
        }


# 两个小工具（挂在 PageEvent 上）
def _callback_datatype(self: PageEvent) -> str:
    return str(self.raw.get("callbackDataType", ""))

def _microflow_ref(self: PageEvent) -> Any:
    # 微流程动作的绑定键：microFlowId / microflowId / target（不同版本键名）
    for k in ("microFlowId", "microflowId", "targetMicroFlowId", "target"):
        if self.raw.get(k):
            return self.raw.get(k)
    return None

PageEvent.callback_datatype = _callback_datatype
PageEvent.microflow_ref = _microflow_ref


__all__ = [
    "SCHEMA_ID", "ACTION_TYPES", "BUILTIN_ACTIONS", "WIDGET_ACTIONS",
    "PAGE_INFO_TYPES", "DETAIL_OPEN_MODES",
    "PageEvent", "PageEventValidator",
]
