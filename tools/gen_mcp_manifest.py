#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""tools/gen_mcp_manifest.py — 从实际工具面生成 MCP 工具权威清单。

**为什么要生成器**：`adapters/*/MCP-TOOL-MANIFEST.md` 是手工维护的，
工具面从 5 → 14 → 44 的每一次变更都会让它落后（2026-11-09 实测：三份
manifest 仍停在 14 个，而 server.py 已接 44 个）。手工同步必然漂移。

用法：:

    python tools/gen_mcp_manifest.py            # 写 docs/operation-contracts/mcp/TOOLS.md
    python tools/gen_mcp_manifest.py --check    # 只校验，不一致退出码 1（给 CI/测试用）
    python tools/gen_mcp_manifest.py --stdout   # 打印不落盘

数据源（唯一）：
  xiaozhua_host_bootstrap.bootstrap()  →  各能力函数
  adapters.mcp.server.TOOL_KEYS      →  暴露哪些
  adapters.mcp.server.MCP_TOOL_NAMES →  工具名
  adapters.mcp.server.build_tool_schemas → 参数 schema
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

OUT = REPO / "docs" / "operation-contracts" / "mcp" / "TOOLS.md"

# 域归属：key -> (域, 是否需要凭据, 一句话)
DOMAIN_OF = {
    # 跨模块
    "dispatch": ("跨模块", False, "按 intent 路由到组件"),
    "generate": ("跨模块", False, "实体 → 后端骨架 + 前端页面定义"),
    "generate_from_requirement": ("跨模块", False, "自然语言 → 实体模型"),
    "live_probe": ("跨模块", False, "活体只读探测（默认离线 BLOCKED）"),
    "deploy_plan": ("entity", False, "建实体四步部署方案（出 body）"),
    "capability_index": ("跨模块", False, "九大域能力总索引"),
    "spi_catalog": ("SPI", False, "SPI 扩展点事实目录"),
    "repo_state": ("跨模块", False, "客开仓库只读状态"),
    "repo_sync": ("跨模块", False, "客开仓库写操作（confirm 授权）"),
    "code_targets": ("跨模块", False, "客开代码该写在哪"),
    "project_shape": ("跨模块", False, "探工程形态（五模块/单模块）"),
    "repo_url": ("跨模块", False, "拼客开仓库地址（base 必填）"),
    # entity
    "index_body": ("entity", False, "索引 body"),
    "dto_body": ("entity", False, "DTO + 属性 body"),
    "refer_config_body": ("entity", False, "实体参照配置 body"),
    # application（应用内功能页）
    "app_dependency_body": ("application", False, "添加依赖 body（SERVICE/FRONTEND）"),
    "app_dependency_remove": ("application", False, "移除依赖 body（GraphQL 单删 / REST 批删）"),
    "app_deploy_body": ("application", False, "沙箱立即构建 body"),
    "app_version_list": ("application", False, "发布版本列表 body"),
    "app_build_info": ("application", False, "构建信息查询（含 logs[]）"),
    "entity_rule_body": ("rule", False, "实体规则 body + 作用域校验"),
    "entity_rule_publish": ("rule", True, "实体规则 checkSchema + create"),
    # setting
    "enum_body": ("setting", False, "枚举 body"),
    "enum_item_body": ("setting", False, "枚举项 body"),
    "enum_category_body": ("setting", False, "枚举分组 body"),
    "event_body": ("setting", False, "事件 body"),
    "event_data_body": ("setting", False, "带数据事件 body"),
    "option_set_category_body": ("setting", False, "选项集分组 body"),
    "option_set_body": ("setting", False, "选项集 body"),
    "option_set_item_body": ("setting", False, "选项集项 body"),
    "attribute_set_body": ("setting", False, "字段集 body（父 REST）"),
    "attribute_set_field_body": ("setting", False, "字段集字段 body（子 GraphQL）"),
    "scalability_option_body": ("setting", False, "扩展实体方案 body"),
    "scalability_field_body": ("setting", False, "扩展实体字段 body"),
    "qrcode_body": ("setting", False, "二维码/条码/链接码 body"),
    "serial_scheme_body": ("serial", False, "流水号方案 body"),
    "serial_section": ("serial", False, "流水号段"),
    "parameter_body": ("setting", False, "应用参数 body"),
    "excel_template_body": ("setting", False, "导入导出模板 body"),
    "excel_template_column": ("setting", False, "导入导出模板列"),
    # flow
    "microflow_create_body": ("flow", False, "微流程 create/checkSchema body"),
    "microflow_node": ("flow", False, "单节点构造（11 种 action）"),
    "microflow_node_actions": ("microflow", False, "列出 microflow_node 支持的 23 个 action → actionType 映射"),
    "microflow_gates": ("flow", False, "G1–G41 静态闸门"),
    "microflow_capability": ("flow", False, "节点能力矩阵"),
    "microflow_trigger": ("flow", False, "触发器（MANUAL/SCHEDULE/EVENT/MF_EVENT）"),
    "microflow_data_schema": ("flow", False, "组装 dataSchema"),
    "microflow_publish": ("flow", True, "发布到 RELEASE"),
    # expression
    "expression_catalog": ("expression", False, "88 函数 / 131 系统变量"),
    "expression_verify": ("expression", True, "校验+编译表达式"),
    "expression_filter": ("expression", True, "FILTER 过滤条件表达式"),
    # page
    "list_page_schema": ("page", False, "列表页 pageSchema 骨架"),
    "detail_page_schema": ("page", False, "详情页 pageSchema 骨架"),
    "filter_plan_body": ("page", False, "过滤方案 body"),
    "custom_page_scaffold": ("page", False, "customPage.tsx 骨架"),
}

DOMAIN_ORDER = ["跨模块", "application", "entity", "setting", "serial", "flow",
                "rule", "expression", "page", "SPI"]


def collect() -> tuple[list[dict], int]:
    from xiaozhua_host_bootstrap import bootstrap
    from adapters.mcp.server import TOOL_KEYS, MCP_TOOL_NAMES, build_tool_schemas

    b = bootstrap()
    caps = {k: b[k] for k in TOOL_KEYS}
    schemas = {s["name"]: s for s in build_tool_schemas(caps)}

    rows = []
    for key in TOOL_KEYS:
        name = MCP_TOOL_NAMES[key]
        s = schemas[name]
        props = s.get("inputSchema", {}).get("properties", {})
        req = s.get("inputSchema", {}).get("required") or []
        dom, needs_cred, brief = DOMAIN_OF.get(key, ("未归类", False, ""))
        rows.append({
            "key": key, "tool": name, "domain": dom,
            "needs_cred": needs_cred or ("host" in req and "cookie" in req),
            "required": list(req),
            "optional": [p for p in props if p not in req],
            "n_params": len(props),
            "brief": brief,
            "description": s.get("description", ""),
        })
    return rows, len(b)


def render(rows: list[dict], n_caps: int) -> str:
    domains = {}
    for r in rows:
        domains.setdefault(r["domain"], []).append(r)

    cred_tools = [r["tool"] for r in rows if r["needs_cred"]]
    L = []
    L.append("# MCP 工具权威清单（自动生成，勿手改）")
    L.append("")
    L.append("> 生成器：`tools/gen_mcp_manifest.py`（`--check` 校验一致性）")
    L.append("> 数据源：`xiaozhua_host_bootstrap.bootstrap()` + `adapters/mcp/server.py`")
    L.append("> 手工维护的 `adapters/*/MCP-TOOL-MANIFEST.md` 只作历史记录，**以本文件为准**。")
    L.append("")
    L.append("## 概览")
    L.append("")
    L.append("```")
    L.append("bootstrap 可调用能力  %d" % n_caps)
    L.append("MCP 工具总数          %d" % len(rows))
    L.append("需要凭据的工具        %d（%s）" % (len(cred_tools), " / ".join(cred_tools)))
    L.append("```")
    L.append("")
    L.append("## 按域分布")
    L.append("")
    L.append("| 域 | 工具数 |")
    L.append("|---|---:|")
    for d in DOMAIN_ORDER:
        if d in domains:
            L.append("| %s | %d |" % (d, len(domains[d])))
    for d in sorted(set(domains) - set(DOMAIN_ORDER)):
        L.append("| %s | %d |" % (d, len(domains[d])))
    L.append("")
    L.append("## 全部工具")
    L.append("")

    for d in DOMAIN_ORDER + sorted(set(domains) - set(DOMAIN_ORDER)):
        if d not in domains:
            continue
        L.append("### %s（%d）" % (d, len(domains[d])))
        L.append("")
        L.append("| 工具 | 必填参数 | 可选参数 | 说明 |")
        L.append("|---|---|---|---|")
        for r in domains[d]:
            req = ", ".join("`%s`" % x for x in r["required"]) or "—"
            opt = ", ".join("`%s`" % x for x in r["optional"]) or "—"
            cred = " 🔑" if r["needs_cred"] else ""
            L.append("| `%s`%s | %s | %s | %s |"
                     % (r["tool"], cred, req, opt, r["brief"]))
        L.append("")

    L.append("## 凭据边界")
    L.append("")
    L.append("🔑 标记的工具**强制要求 `host` + `cookie` 两个必填参数**，不传凭据根本调不起来。")
    L.append("这是「MCP 面默认只读」红线的实现方式 —— 写动作必须由宿主显式授权。")
    L.append("")
    L.append("守它的测试：`tests/test_mcp_server.py::test_write_not_exposed`")
    L.append("（断言凡是写类工具，`required` 必须包含 `host` 和 `cookie`）。")
    L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 MCP 工具权威清单")
    ap.add_argument("--check", action="store_true", help="只校验，不一致退出码 1")
    ap.add_argument("--stdout", action="store_true", help="打印不落盘")
    a = ap.parse_args()

    rows, n_caps = collect()
    text = render(rows, n_caps)

    if a.stdout:
        print(text)
        return 0
    if a.check:
        if not OUT.exists():
            print("FAIL: %s 不存在" % OUT)
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print("FAIL: %s 与实际工具面不一致，重跑生成器" % OUT)
            return 1
        print("OK: %d 个工具，清单与实际一致" % len(rows))
        return 0

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print("已写 %s（%d 个工具 / %d 个能力）" % (OUT, len(rows), n_caps))
    return 0


if __name__ == "__main__":
    sys.exit(main())
