"""设计器 8 导航域 → udc-web controller/API 归类模型（导航域覆盖面）。

导航域（左侧边栏 8 项，用户指定）：应用 / 实体 / 菜单 / 规则 / 流程 / BI / 栏目 / 设置。

数据源：`docs/audit/artifacts/udc-web-5.3.517-contracts/_api_full.json`
（javap 实证类级路径 + 方法级 http/path/描述；udc-web-5.3.517.jar，STATIC_BYTECODE）。

用途：
- 逐域给出该域覆盖的 controller、API 总数、写操作数、registry 落点；
- 与仓库现有 op 目录（graphql_write_ops / registry）对账，暴露「有 API 但无模型」的缺口；
- 作为 `tests/udc/test_domain_coverage.py` 的补强面（8 域 API 级，不止模块级）。

证据边界：STATIC_BYTECODE（udc-web javap）。流程域走独立 bpm 服务、BI 域走 cdp-data，
不在 udc-web 54 controller 内，另表登记。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.designer.nav-domain.v1"

_API_JSON = (Path(__file__).resolve().parents[2] / "docs" / "audit" / "artifacts"
             / "udc-web-5.3.517-contracts" / "_api_full.json")

# 8 导航域 → 该域 controller（udc-web 内；流程/BI 另属 bpm/cdp-data 服务）
NAV_DOMAIN_CONTROLLERS: dict[str, list[str]] = {
    "应用": ["ApplicationController", "PublishStateController", "SandboxController",
             "DeployController", "DeploymentController", "BackendComponentController",
             "AppCollaborationController", "DependencyAnalysisController"],
    "实体": ["EntityController", "EntityGroupController", "AttributeSetController",
             "AttributeGroupController", "ReferConfigController", "EventController",
             "IndexController", "ScalabilityController", "ScalabilityOptionController",
             "DataTypeController", "StereotypeController", "EntityOpenApiController"],
    "菜单": ["FunctionNodeController", "PageRouteController"],
    "规则": ["MicroFlowController", "MicroFlowGroupController", "MicroFlowMacroController",
             "MicroFlowRefactorController", "MicroFlowUpgradeController",
             "MicroFlowFunctionalCheckController", "DeductionRuleController",
             "TempPresetMicroFlowController"],
    "流程": [],   # bpm 服务（/service/bpm/graphql）
    "BI": [],     # cdp-data 服务（/service/cdp-data/*）
    "栏目": ["PortletController", "PortletGroupController", "PageLayoutController",
             "PageInfoController", "PageTemplateController", "PageTemplateClassController",
             "PageTemplatePublishedController"],
    "设置": ["UdcEnumController", "UdcEnumItemController", "UdcEnumCategoryController",
             "UdcCtpEnumController", "DataTransferObjectController", "DataFlowDesignController",
             "FeatureController", "ParameterController", "MetaDataController",
             "UdcDesignMetadataController", "MultiEditController", "OperationLogController",
             "AttachmentTemplateController", "COLISplitController", "UdcFileController",
             "UdcSandBoxLogController", "UdcManagerController"],
}

# 各域的独立服务（流程= bpm，BI= cdp-data）；round2 LIVE 已建 op 目录
EXTERNAL_SERVICE_DOMAINS: dict[str, dict[str, str]] = {
    "流程": {"service": "bpm", "gateway_prefix": "/service/bpm/",
             "op_catalog": "components.udc.bi_flow_ops:flow_ops"},
    "BI": {"service": "cdp-data", "gateway_prefix": "/service/cdp-data/",
           "op_catalog": "components.udc.bi_flow_ops:bi_ops"},
}


def load_api_by_controller() -> dict[str, dict[str, Any]]:
    if not _API_JSON.exists():
        return {}
    return json.loads(_API_JSON.read_text(encoding="utf-8"))


def domain_apis(domain: str) -> dict[str, Any]:
    """某导航域的 controller → API 明细 + 汇总（方法级完整路径）。"""
    data = load_api_by_controller()
    ctrls = NAV_DOMAIN_CONTROLLERS.get(domain)
    if ctrls is None:
        return {"domain": domain, "error": f"未知导航域（{list(NAV_DOMAIN_CONTROLLERS)}）"}
    if not ctrls:
        ext = EXTERNAL_SERVICE_DOMAINS.get(domain, {})
        return {"domain": domain, "external_service": ext.get("service", ""),
                "gateway_prefix": ext.get("gateway_prefix", ""),
                "op_catalog": ext.get("op_catalog", ""),
                "note": "独立服务域，不在 udc-web 54 controller 内"}
    total = 0
    writes = 0
    per: dict[str, dict] = {}
    for c in ctrls:
        v = data.get(c)
        if not v:
            per[c] = {"missing": True}
            continue
        ms = v.get("methods", [])
        n = len(ms)
        w = sum(1 for a in ms if a.get("http") == "POST")
        total += n
        writes += w
        per[c] = {"class_mapping": v["class_mapping"], "roles": v["roles"],
                  "api_count": n, "post_count": w,
                  "methods": [{"method": a["method"], "http": a.get("http"),
                               "full_path": a.get("full_path"), "desc": a.get("desc", ""),
                               "is_write": a.get("is_write", False)} for a in ms]}
    return {"domain": domain, "controllers": len(ctrls), "api_total": total,
            "post_total": writes, "per_controller": per}


def domain_full_paths(domain: str) -> list[str]:
    """某导航域全部方法级完整路径（去重排序）。"""
    info = domain_apis(domain)
    paths: set[str] = set()
    for v in info.get("per_controller", {}).values():
        for m in v.get("methods", []):
            if m.get("full_path"):
                paths.add(m["full_path"])
    return sorted(paths)


def nav_domain_catalog() -> dict[str, Any]:
    """8 域全量目录（含每域 API 数 + 外部服务域）。"""
    out: dict[str, Any] = {"schema": SCHEMA_ID,
                           "evidence": "udc-web-5.3.517.jar javap（STATIC_BYTECODE）",
                           "domains": {}}
    for d in NAV_DOMAIN_CONTROLLERS:
        info = domain_apis(d)
        out["domains"][d] = {
            "controllers": info.get("controllers", 0),
            "api_total": info.get("api_total", 0),
            "post_total": info.get("post_total", 0),
            "external_service": info.get("external_service", ""),
        }
    return out


__all__ = ["SCHEMA_ID", "NAV_DOMAIN_CONTROLLERS", "EXTERNAL_SERVICE_DOMAINS",
           "load_api_by_controller", "domain_apis", "nav_domain_catalog"]
