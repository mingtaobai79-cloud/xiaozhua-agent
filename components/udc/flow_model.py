"""生单(DataFlow)与扣减(Deduction)域模型与校验器 —— 证据驱动，对象边界铁律。

证据基线（docs/audit/udc-semantics/flow-excel-source-audit.md，逐行引用可复核）：
- DataFlow 图与映射是独立对象（§2）：POST /udc/data-flow、/udc/data-flow/mapping。
- Deduction 图/规则/算法/明细四层独立表（§3）：udc_deduction_map/rule/algorithm/rule_detail。
- 值域受控（§2/§3）：
  * triggerPoint ∈ {MANUALLY, EVENT_SUBSCRIBE}（TriggerPointEnum.java:14-22）
  * operationType ∈ {CREATE, UPDATE, CREATE_OR_UPDATE}（DataFlowOperationTypeEnum.java:12-24）
  * 扣减生命周期 ∈ {BeforeCreate:DO, BeforeUpdate:UNDO+DO, BeforeDelete:UNDO}
- 对象边界（§1 纠正两条结论，必须保持）：
  * CALL_DATA_FLOW = 生单规则调用节点，只调 <SourceEntity>DataFlowRuntimeService，
    CallDataFlowResultDto 只暴露 targetIds/updateIds —— 没有直接调用 Deduction 的证据。
  * 扣减是独立生命周期监听器（生成的 BeforeCreate/BeforeUpdate/BeforeDelete），
    不是 CHANGE_ENTITY 别名；DeductionController 是规则版本管理面 ≠ 扣减执行面。
- 图校验硬规则（§3）：禁止实体连自身；拒绝 bill 作为目标实体。
- 副作用显式分类（§6.4）：check 端点不当只读；新建 DataFlow 图可能预制 DATA_FLOW 菜单/页面。

本模块只做「值域 + 对象边界 + 结构完整性」离线校验；
can_execute 恒 false（未接入平台执行器）；不声称任何 live 验收。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_ID = "udc.construction.flow-model.v1"

# ---------------------------------------------------------------- 受控值域（全有源码证据）

TRIGGER_POINTS: frozenset[str] = frozenset({"MANUALLY", "EVENT_SUBSCRIBE"})
DATA_FLOW_OPERATION_TYPES: frozenset[str] = frozenset({"CREATE", "UPDATE", "CREATE_OR_UPDATE"})

# 扣减生命周期与动作（Deduction*Listener.ftl 三模板实证，§3 表）
DEDUCTION_LIFECYCLE: frozenset[str] = frozenset({"BeforeCreate", "BeforeUpdate", "BeforeDelete"})
DEDUCTION_LIFECYCLE_DO_UNDO: dict[str, tuple[str, ...]] = {
    "BeforeCreate": ("DO",),
    "BeforeUpdate": ("UNDO", "DO"),   # 先按新旧数据求 UNDO 再 DO
    "BeforeDelete": ("UNDO",),
}

# 持久化表名（静态确认；表无行≠功能未启用）
DATAFLOW_TABLES: dict[str, str] = {
    "graph": "udc_data_flow",
    "mapping": "udc_data_flow_mapping",
}
DEDUCTION_TABLES: dict[str, str] = {
    "map": "udc_deduction_map",
    "rule": "udc_deduction_rule",
    "algorithm": "udc_deduction_algorithm",
    "detail": "udc_deduction_rule_detail",
}

# Controller 字面路径（不拼 Gateway/宿主前缀——证据纪律）
DATAFLOW_ENDPOINTS: dict[str, str] = {
    "create_graph": "POST /udc/data-flow",
    "read_graph": "GET /udc/data-flow/{id}",
    "create_mapping": "POST /udc/data-flow/mapping",
    "update_mapping": "POST /udc/data-flow/mapping/update",
    "read_mapping": "GET /udc/data-flow/mapping/{id}",
}
DEDUCTION_ENDPOINTS: dict[str, str] = {
    "save_map": "POST /udc/deduction/map",
    "read_map": "GET /udc/deduction/map/{id}",
    "save_rule": "POST /udc/deduction/rule",
    "valid_rule": "POST /udc/deduction/validRule",
    "read_rule": "GET /udc/deduction/rule/{id}",
}


# ---------------------------------------------------------------- 模型

@dataclass
class DataFlowLine:
    """生单图上的一条连线（source→target 实体）。"""
    source_entity_id: str
    target_entity_id: str
    operation_type: str = "CREATE"
    trigger_point: str = "MANUALLY"
    raw: dict[str, Any] = field(default_factory=dict)

    def violations(self) -> list[str]:
        out: list[str] = []
        if self.source_entity_id == self.target_entity_id:
            out.append(f"连线 {self.source_entity_id}→自身 被图校验禁止（DeductionMapService.java:579-634 同规）")
        if self.operation_type not in DATA_FLOW_OPERATION_TYPES:
            out.append(f"operationType={self.operation_type!r} 不在 {sorted(DATA_FLOW_OPERATION_TYPES)}")
        if self.trigger_point not in TRIGGER_POINTS:
            out.append(f"triggerPoint={self.trigger_point!r} 不在 {sorted(TRIGGER_POINTS)}")
        return out


@dataclass
class DataFlowGraph:
    """生单图（definition: nodes/lines/transform）+ 映射引用。"""
    graph_id: str = ""
    app_id: str = ""
    lines: list[DataFlowLine] = field(default_factory=list)
    mapping_id: str = ""
    note: str = ""
    can_execute: bool = False       # 主线未接执行器（§6）
    raw_entities: dict[str, dict[str, Any]] = field(default_factory=dict)

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        if not self.lines:
            warnings.append("空图：合法（未配置连线），不代表功能未启用")
        for ln in self.lines:
            errors.extend(ln.violations())
        # bill 目标拒绝（§3：扣减图校验；生单图同族校验，保守只对扣减断言）
        if self.note == "deduction_graph":
            for ln in self.lines:
                if _looks_like_bill(ln.target_entity_id, self.raw_entities):
                    errors.append(f"目标实体 {ln.target_entity_id} 疑似 bill，图校验拒绝 bill 作目标")
        return {
            "schema": SCHEMA_ID, "kind": "dataflow_graph", "graph_id": self.graph_id,
            "status": "FAIL" if errors else ("UNVERIFIED" if warnings else "PASS"),
            "errors": errors, "warnings": warnings,
            "can_execute": self.can_execute,
            "table": DATAFLOW_TABLES["graph"],
        }

    raw_entities: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class DeductionRule:
    """扣减规则四层对象（map/rule/algorithm/detail 之一视角的结构骨架）。"""
    rule_id: str = ""
    map_id: str = ""
    source_root_entity: str = ""
    target_root_entity: str = ""
    source_leaf_entity: str = ""
    target_leaf_entity: str = ""
    lifecycle: str = ""
    algorithms: list[dict[str, Any]] = field(default_factory=list)
    details: list[dict[str, Any]] = field(default_factory=list)
    can_execute: bool = False

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        if not (self.source_root_entity and self.target_root_entity):
            errors.append("规则缺 source/target 根实体（DeductionRuleDto.java:25-106）")
        if self.lifecycle and self.lifecycle not in DEDUCTION_LIFECYCLE:
            errors.append(f"lifecycle={self.lifecycle!r} 不在 {sorted(DEDUCTION_LIFECYCLE)}")
        if not self.algorithms:
            warnings.append("无算法配置：DeductionCodeTask 只有非空规则元数据才生成代码（§3），保存≠生成")
        return {
            "schema": SCHEMA_ID, "kind": "deduction_rule", "rule_id": self.rule_id,
            "status": "FAIL" if errors else ("UNVERIFIED" if warnings else "PASS"),
            "errors": errors, "warnings": warnings,
            "lifecycle_do_undo": DEDUCTION_LIFECYCLE_DO_UNDO.get(self.lifecycle, ()),
            "tables": list(DEDUCTION_TABLES.values()),
            "can_execute": self.can_execute,
        }


def _looks_like_bill(entity_ref: str, raw_entities: dict[str, dict[str, Any]]) -> bool:
    """bill 判定只基于已知实体元数据（category/stereotype），不猜名字。"""
    meta = raw_entities.get(entity_ref) or {}
    return meta.get("category") == "bill" or meta.get("stereotype") == "bill"


# ---------------------------------------------------------------- 对象边界断言器（防混用回归）

def assert_object_boundary_facts() -> list[str]:
    """返回本轮不可混用边界清单（测试与文档引用同一事实源，防口口相传失真）。"""
    return [
        "CALL_DATA_FLOW 只调 <SourceEntity>DataFlowRuntimeService；CallDataFlowResultDto 仅 targetIds/updateIds，无直接调用 Deduction 的证据",
        "扣减=独立生命周期监听器（BeforeCreate/BeforeUpdate/BeforeDelete），不是 CHANGE_ENTITY 别名",
        "DeductionController 是规则版本管理/查询面 ≠ 扣减执行面",
        "实体规则 VALIDATE 组 ≠ 页面动作 VALIDATE_ENTITY ≠ 页面规则微流程(FRONTEND) ≠ 过滤方案(udc_filter_plan)",
        "udcMicroflowUpdatePost（GraphQL 数字枚举）与 POST /microflow/create（REST 字符串枚举）是两套契约，勿互套",
        "check 端点（excel/check-excel、microflow/checkSchema）有副作用或仅结构校验，不得自动归只读执行白名单",
    ]


__all__ = [
    "SCHEMA_ID", "TRIGGER_POINTS", "DATA_FLOW_OPERATION_TYPES",
    "DEDUCTION_LIFECYCLE", "DEDUCTION_LIFECYCLE_DO_UNDO",
    "DATAFLOW_TABLES", "DEDUCTION_TABLES", "DATAFLOW_ENDPOINTS", "DEDUCTION_ENDPOINTS",
    "DataFlowLine", "DataFlowGraph", "DeductionRule",
    "assert_object_boundary_facts",
]
