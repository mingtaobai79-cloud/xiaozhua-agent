"""菜单功能节点（FunctionNode）模型与校验器 —— 页面可见链的关系完整性。

证据基线（docs/audit/udc-semantics/page-menu-source-audit.md，源码行号）：
- FunctionNode 是独立对象（§3.4）：菜单/页面引用不是 pageSchema 顶层字段。
  关系链（页面能从菜单打开的关键）：
    FunctionNode(PAGE).resourceId → PageInfoEntity.id
    FunctionNode(PAGE).relationId → PageInfoEntity.relationGroupId
    FunctionNode.id / parentId     节点自身/父菜单
    FunctionNode.type ∈ {PAGE, MENU}；url = PageInfoEntity.pageUrl
- 创建默认行为（FunctionNodeService.createFunctionNode，§6.2）：
  appId 必须真实；PAGE 节点必须有非空 relationId；无 parentId 挂终端根节点；
  orderNo 调整同层顺序；按类型/来源设 schemaState。
- 设默认页约束（setFunctionDefaultPage，§6.3）：
  页面引用必须是菜单**直接子节点**；SUBPAGE 不能做菜单默认页（excludeSubPage）；
  页面资源 id 必须查到真实 PageInfo。
- 菜单查重（createMenuRefer，§6.1）：按 name+terminalType+type=MENU+parentId+appId
  查重，存在复用，否则新建。
- Controller 字面路径（§2.2，不拼 Gateway 前缀）：
  POST /udc/function、/udc/function/create/function-refer、/update/function-refer、
  /select/function-tree、/find/tree-and-group、/default_page、GET /page/in_params/{referId}

离线校验面：关系完整性 + 约束；can_execute=False（未接执行器）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_ID = "udc.construction.function-node.v1"

FUNCTION_NODE_TYPES: frozenset[str] = frozenset({"PAGE", "MENU"})
TERMINAL_TYPES: frozenset[str] = frozenset({"PC", "MOBILE"})

# Controller 字面路径（证据纪律：不拼 /service 前缀）
FUNCTION_ENDPOINTS: dict[str, str] = {
    "create": "POST /udc/function",
    "create_page_refer": "POST /udc/function/create/function-refer",
    "update_page_refer": "POST /udc/function/update/function-refer",
    "select_tree": "POST /udc/function/select/function-tree",
    "find_tree_and_group": "POST /udc/function/find/tree-and-group",
    "set_default_page": "POST /udc/function/default_page",
    "page_in_params": "GET /udc/function/page/in_params/{referId}",
}


@dataclass
class FunctionNode:
    node_id: str = ""
    parent_id: str = ""            # 空 = 挂终端根节点（createFunctionNode 默认行为）
    node_type: str = "PAGE"        # PAGE | MENU
    app_id: str = ""
    terminal_type: str = "PC"
    name: str = ""
    url: str = ""                  # PAGE 节点 = PageInfoEntity.pageUrl
    resource_id: str = ""          # PAGE 节点 → PageInfoEntity.id
    relation_id: str = ""          # PAGE 节点 → PageInfoEntity relationGroupId
    page_type: str = ""            # LIST/DETAIL/SUBPAGE…（默认页约束用）
    order_no: int = 0
    is_default_page: bool = False
    raw: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        if self.node_type not in FUNCTION_NODE_TYPES:
            errors.append(f"type={self.node_type!r} 不在 {sorted(FUNCTION_NODE_TYPES)}")
        if self.terminal_type not in TERMINAL_TYPES:
            errors.append(f"terminalType={self.terminal_type!r} 不在 {sorted(TERMINAL_TYPES)}")
        if not self.app_id:
            errors.append("缺 appId（createFunctionNode 要求对应真实应用）")
        if self.node_type == "PAGE":
            if not self.relation_id:
                errors.append("PAGE 节点必须非空 relationId（FunctionNodeService.java:161-208）")
            if not self.resource_id:
                errors.append("PAGE 节点缺 resourceId（→ PageInfoEntity.id，页面可见链断点）")
            if not self.url:
                errors.append("PAGE 节点缺 url（= PageInfoEntity.pageUrl）")
        if not self.parent_id:
            warnings.append("无 parentId → 挂终端根节点（默认行为，宿主确认是否本意）")
        return {"schema": SCHEMA_ID, "kind": "function_node", "node_id": self.node_id,
                "status": "FAIL" if errors else ("UNVERIFIED" if warnings else "PASS"),
                "errors": errors, "warnings": warnings, "can_execute": False}


@dataclass
class FunctionTree:
    """菜单树（节点集），承载父子/默认页关系校验。"""
    nodes: list[FunctionNode] = field(default_factory=list)

    def _by_id(self) -> dict[str, FunctionNode]:
        return {n.node_id: n for n in self.nodes if n.node_id}

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        seen_ids: set[str] = set()
        by_id = self._by_id()
        for n in self.nodes:
            r = n.validate()
            errors.extend(r["errors"])
            warnings.extend(r["warnings"])
            if n.node_id:
                if n.node_id in seen_ids:
                    errors.append(f"节点 id 重复: {n.node_id}")
                seen_ids.add(n.node_id)
            # 父子链完整性：有 parentId 但树里找不到父 → 断链
            if n.parent_id and n.parent_id not in by_id:
                warnings.append(f"节点 {n.node_id or n.name} 的父 {n.parent_id} 不在树内（跨请求依赖，宿主确认）")
            # 默认页约束
            if n.is_default_page:
                if n.node_type != "PAGE":
                    errors.append(f"默认页节点 type={n.node_type} 必须 PAGE（setFunctionDefaultPage）")
                if n.page_type == "SUBPAGE":
                    errors.append(f"SUBPAGE 不能作菜单默认页（excludeSubPage 硬约束，§6.3）")
                parent = by_id.get(n.parent_id)
                if parent is not None and parent.node_type != "MENU":
                    errors.append(f"默认页必须菜单的直接子节点，父 {n.parent_id} type={parent.node_type}≠MENU")
                if parent is None:
                    warnings.append(f"默认页节点 {n.node_id} 父不在树内，直接子约束未验（UNVERIFIED）")
        return {"schema": SCHEMA_ID, "kind": "function_tree",
                "status": "FAIL" if errors else ("UNVERIFIED" if warnings else "PASS"),
                "errors": errors, "warnings": warnings,
                "node_count": len(self.nodes), "can_execute": False}


def menu_duplication_key(node: FunctionNode) -> tuple:
    """createMenuRefer 查重键（§6.1 逐字）：存在复用，否则创建。"""
    return (node.name, node.terminal_type, node.node_type, node.parent_id, node.app_id)


__all__ = [
    "SCHEMA_ID", "FUNCTION_NODE_TYPES", "TERMINAL_TYPES", "FUNCTION_ENDPOINTS",
    "FunctionNode", "FunctionTree", "menu_duplication_key",
]
