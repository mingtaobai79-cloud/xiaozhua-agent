"""应用域子菜单模型 —— 侧边栏"应用"域的 8 个子菜单 → API 映射。

侧边栏「应用」域展开的 8 个子项（用户截图）：页面测试 / 沙箱测试 / 发布版本 /
依赖设置 / 应用（设置）/ 组件（设置）/ 团队设置 / 应用主题。

数据源：udc-web-5.3.517 javap（_api_by_controller.json，STATIC_BYTECODE）。
每子项映射到其 API（方法名 + HTTP + controller + 类级路径），含读写语义标注。

证据边界：STATIC_BYTECODE。这是「导航结构 → 后端 API」的可复核映射，
不声称 live 行为；写操作是否真生效需宿主执行回读。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.nav.application.submenu.v1"

_API_JSON = (Path(__file__).resolve().parents[2] / "docs" / "audit" / "artifacts"
             / "udc-web-5.3.517-contracts" / "_api_by_controller.json")

# 应用域 8 子菜单 → (controller, 方法名) 清单
# 依据：方法名语义 + controller 归属 + udc_deploy_record/分诊证据
APP_SUBMENUS: dict[str, dict[str, Any]] = {
    "页面测试": {   # 前端页面预览/检测
        "controllers": ["ApplicationController"],
        "methods": ["selectDetectionListByAppId", "selectSummaryDetectionByAppId",
                    "detectionByAppId", "runDetectionState", "selectFrontDetectionByAppId",
                    "frontDetectionByAppId", "detectionAllFormApp", "selectDetectionAllFormApp"],
        "note": "前后端一致性检测 + 前端检测（页面测试观感）",
    },
    "沙箱测试": {   # TEST 构建 + 沙箱
        "controllers": ["DeployController", "SandboxController", "DeploymentController"],
        "methods": ["deployNormal", "searchStatus", "expectDeployTime", "statistics",
                    "selectSandboxByAppId", "getBuildInfo", "getDeltaBuildInfo",
                    "getReleaseBuildInfo", "selectRoles", "getAppReadyStatus",
                    "restartApp", "latestTestInfo"],
        "note": "TEST 构建（deployNormal deployType=TEST）+ 沙箱状态/构建信息",
    },
    "发布版本": {   # RELEASE / 上线 / 版本
        "controllers": ["DeploymentController", "DeployController", "ApplicationController",
                        "PublishStateController"],
        "methods": ["appOnline", "appOnlineNew", "appDeltaDeploy", "deployForm",
                    "crossDeployForm", "migrationApp", "update", "selectAppVersionByAppGuid",
                    "selectHasPublishAppByAppGuid", "selectPublishStatus",
                    "isLastVersionApp", "fetchLastVersionMetadata"],
        "note": "上线（ON_ONLINE）/ RELEASE / 版本状态；PublishStateController.update 是实体级发布（要密码）",
    },
    "依赖设置": {
        "controllers": ["ApplicationController", "BackendComponentController",
                        "DependencyAnalysisController"],
        "methods": ["createDepApp", "createDepAppBatch", "selectDepByCondition",
                    "updateDepAppVersion", "updateBatchDepAppVersion", "deleteDepAppsByAppId",
                    "deleteDepAppsById", "deleteDepAppsByIds", "selectDepAppListByAppId",
                    "dependencyAnalysis", "analysisAppDepRelationship",
                    "selectListByDependentId", "refreshComponent", "refreshVersion"],
        "note": "依赖应用 CRUD + 依赖关系分析",
    },
    "应用": {       # 应用设置：基本信息/特征/字典
        "controllers": ["ApplicationController", "BackendComponentController"],
        "methods": ["create", "update", "deleteById", "delete", "deleteByGuid",
                    "updateCaptionByGuid", "selectById", "selectDetailById",
                    "selectPlatformVersion", "selectPlatformVersionMap", "selectMultiVersion",
                    "getAppFeatureByAppId", "getAppFeatureByAppType", "dataDictionary",
                    "registerJar", "selectDesignDataChange",
                    "checkDesignModifiedAfterLastRelease", "compatibilityLock"],
        "note": "应用基本信息 CRUD + 特征（getAppFeature）+ 数据字典 + 设计变更检测",
    },
    "组件": {       # 后端组件管理
        "controllers": ["BackendComponentController"],
        "methods": ["selectAllListByConditions", "selectAppPageByConditions",
                    "create", "update", "selectById", "selectMultiVersionById"],
        "note": "后端组件（backend-component）管理",
    },
    "团队设置": {
        "controllers": ["AppCollaborationController", "ApplicationController",
                        "SandboxController"],
        "methods": ["selectCollaborationRecordsByAppId", "selectCollaborationMembersByAppGuid",
                    "createMember", "deleteMemberById", "handoverApp",
                    "selectCurrentOrgMemberByCondition", "selectRoleResource", "selectUserRole",
                    "selectRoles"],
        "note": "协作成员（create/delete/handover）+ 角色资源矩阵（selectRoleResource/selectUserRole）",
    },
    "应用主题": {   # 主题/皮肤配置（前端为主，后端接口未见独立 controller）
        "controllers": [],
        "methods": [],
        "note": "应用主题以前端配置为主；udc-web 无独立主题 controller（UNVERIFIED：可能存 "
                "udc_application 扩展字段或前端主题包，需前端 bundle/DB 取证）",
    },
}


def _load() -> dict[str, dict[str, Any]]:
    if not _API_JSON.exists():
        return {}
    return json.loads(_API_JSON.read_text(encoding="utf-8"))


def submenu_apis(submenu: str) -> dict[str, Any]:
    spec = APP_SUBMENUS.get(submenu)
    if not spec:
        return {"error": f"未知子菜单（{list(APP_SUBMENUS)}）"}
    data = _load()
    found = []
    for ctrl in spec["controllers"]:
        v = data.get(ctrl, {})
        for a in v.get("apis", []):
            if a["method"] in spec["methods"]:
                found.append({"controller": ctrl, "class_mapping": v.get("class_mapping"),
                              "roles": v.get("roles", []), "method": a["method"],
                              "http": a["http"],
                              "is_write": a["http"] == "POST"})
    missing = [m for m in spec["methods"]
               if not any(f["method"] == m for f in found)]
    return {"submenu": submenu, "note": spec["note"],
            "declared": len(spec["methods"]), "matched": len(found),
            "apis": found, "unmatched": missing}


def application_submenu_catalog() -> dict[str, Any]:
    return {"schema": SCHEMA_ID,
            "evidence": "udc-web-5.3.517 javap（STATIC_BYTECODE）",
            "submenus": {k: {"note": v["note"], "api_count": len(v["methods"])}
                         for k, v in APP_SUBMENUS.items()}}


__all__ = ["SCHEMA_ID", "APP_SUBMENUS", "submenu_apis", "application_submenu_catalog"]
