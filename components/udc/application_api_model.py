"""应用域 —— ApplicationController + 部署/协作/依赖子域 API 模型。

controller（udc-web-5.3.517 javap，STATIC_BYTECODE）：
- ApplicationController（udc/application，73）：应用 CRUD/版本/导入导出/依赖/检测/团队角色/特征
- DeployController（udc/runtime，12）+ DeploymentController（udc/deployment，6）+ SandboxController（udc/sandbox，5）
  + PublishStateController（udc/publish-state，1）：沙箱测试/发布版本/部署链
- BackendComponentController（udc/backend-component，10）：后端组件
- AppCollaborationController（udc/collaboration，6）：团队协作
- DependencyAnalysisController（udc/dependency/analysis，2）：依赖分析

与 application_submenu_model 的分工：submenu 按侧边栏 8 子项归类；
本模型给 ApplicationController 全量语义映射（含导入导出/检测/团队）。

证据边界：STATIC_BYTECODE。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_ID = "udc.nav.application-api.v1"

_API = (Path(__file__).resolve().parents[2] / "docs" / "audit" / "artifacts"
        / "udc-web-5.3.517-contracts" / "_api_full.json")

APPLICATION_CONTROLLERS = [
    "ApplicationController", "DeployController", "DeploymentController",
    "SandboxController", "PublishStateController", "BackendComponentController",
    "AppCollaborationController", "DependencyAnalysisController",
]

APPLICATION_OPS: dict[str, tuple] = {
    # 应用 CRUD / 版本
    "应用_创建": ("ApplicationController", "create", "/udc/application"),
    "应用_删除重命名": ("ApplicationController", "deleteById"),
    "应用_删除": ("ApplicationController", "delete"),
    "应用_按guid删除": ("ApplicationController", "deleteByGuid"),
    "应用_修改": ("ApplicationController", "update"),
    "应用_改标题全版本": ("ApplicationController", "updateCaptionByGuid"),
    "应用_平台版本": ("ApplicationController", "selectPlatformVersion"),
    "应用_多版本": ("ApplicationController", "selectMultiVersion"),
    "应用_详情": ("ApplicationController", "selectDetailById"),
    "应用_历史版本": ("ApplicationController", "selectHistoryById"),
    "应用_按名批量": ("ApplicationController", "selectByAppNames"),
    "应用_分页": ("ApplicationController", "selectAppPageByConditions"),
    "应用_含版本分页": ("ApplicationController", "selectAppPageByConditionsWithVersion"),
    "应用_按guid分页": ("ApplicationController", "selectAppPageByGuid"),
    "应用_模板分页": ("ApplicationController", "selectTemplateAppPageByConditions"),
    "应用_已发布": ("ApplicationController", "selectHasPublishAppByAppGuid"),
    "应用_版本按guid": ("ApplicationController", "selectAppVersionByAppGuid"),
    "应用_最新设计态": ("ApplicationController", "selectLatestDesignAppByGuid"),
    "应用_发布状态": ("ApplicationController", "selectPublishStatus"),
    # 导入导出
    "应用_下载包": ("ApplicationController", "downloadAppPackage"),
    "应用_批量下载表单应用": ("ApplicationController", "downloadFormAppPackage",
                           "/udc/application/schema/form/download/batch/{fileNum}/{timeStamp}"),
    "应用_复制": ("ApplicationController", "copyApp"),
    "应用_复制依赖": ("ApplicationController", "copyDependentAppSchema"),
    "应用_导入依赖": ("ApplicationController", "importDependentAppSchema"),
    "应用_导入": ("ApplicationController", "importAppSchema", "/udc/application/import/new"),
    "应用_迁移表单批量": ("ApplicationController", "transferFormAppPackage"),
    "应用_导入表单校验": ("ApplicationController", "importFormAppValidate"),
    "应用_导入表单": ("ApplicationController", "importFormApp"),
    "应用_迁移": ("ApplicationController", "transferAppSchema"),
    "应用_迁移带参": ("ApplicationController", "transferAppSchemaWithParams"),
    "应用_导入离线zip": ("ApplicationController", "importOtherAppZip"),
    "应用_导入在线": ("ApplicationController", "importOtherAppOnLine"),
    "应用_下载模板包": ("ApplicationController", "downloadAppTemplatesPackage"),
    "应用_另存新设计": ("ApplicationController", "saveAsNewDesign"),
    "应用_从模板创建": ("ApplicationController", "createFromTemplate"),
    # 2026-10-15 缺陷 A 修复后恢复的同名重载（提取器旧版按方法名做 key 会静默丢端）
    "应用_创建页面应用": ("ApplicationController", "create", "/udc/application/create-page-app"),
    "应用_创建外框应用": ("ApplicationController", "create", "/udc/application/create-layout-app"),
    "应用_导入基路径": ("ApplicationController", "importAppSchema", "/udc/application/import"),
    # 特征 / 依赖
    "应用_特征按类型": ("ApplicationController", "getAppFeatureByAppType"),
    "应用_特征按应用": ("ApplicationController", "getAppFeatureByAppId"),
    "依赖_创建": ("ApplicationController", "createDepApp"),
    "依赖_按条件": ("ApplicationController", "selectDepByCondition"),
    "依赖_更新版本": ("ApplicationController", "updateDepAppVersion"),
    "依赖_批量更新版本": ("ApplicationController", "updateBatchDepAppVersion"),
    "依赖_批量创建": ("ApplicationController", "createDepAppBatch"),
    "依赖_按应用删": ("ApplicationController", "deleteDepAppsByAppId"),
    "依赖_列表按应用": ("ApplicationController", "selectDepAppListByAppId"),
    # 检测 / 设计变更
    "检测_列表": ("ApplicationController", "selectDetectionListByAppId"),
    "检测_汇总": ("ApplicationController", "selectSummaryDetectionByAppId"),
    "检测_执行": ("ApplicationController", "detectionByAppId"),
    "检测_状态": ("ApplicationController", "runDetectionState"),
    "检测_前端列表": ("ApplicationController", "selectFrontDetectionByAppId"),
    "检测_前端执行": ("ApplicationController", "frontDetectionByAppId"),
    "设计_数据变更": ("ApplicationController", "selectDesignDataChange"),
    "设计_发布后修改检查": ("ApplicationController", "checkDesignModifiedAfterLastRelease"),
    "应用_注册jar": ("ApplicationController", "registerJar"),
    "应用_取上版元数据": ("ApplicationController", "fetchLastVersionMetadata"),
    "应用_是否最新版本": ("ApplicationController", "isLastVersionApp"),
    "应用_兼容锁": ("ApplicationController", "compatibilityLock"),
    "应用_数据字典": ("ApplicationController", "dataDictionary"),
    "应用_角色资源": ("ApplicationController", "selectRoleResource"),
    "应用_用户角色": ("ApplicationController", "selectUserRole"),
    "应用_另存普通新设计": ("ApplicationController", "saveAsNormalNewDesign"),
    "应用_跨环境推送": ("ApplicationController", "pushData"),
    "应用_延续编辑时长": ("ApplicationController", "renewalAppEditingTime"),
    "应用_是否独占编辑": ("ApplicationController", "isExclusive"),
    # 部署链（Deploy/Deployment/Sandbox/PublishState）
    "部署_停止": ("DeployController", "deployStop"),
    "部署_普通构建": ("DeployController", "deployNormal"),
    "部署_表单构建": ("DeployController", "deployForm"),
    "部署_跨应用表单": ("DeployController", "crossDeployForm"),
    "部署_迁移": ("DeployController", "migrationApp"),
    "部署_前端元数据": ("DeployController", "frontendMetadata"),
    "部署_状态查询": ("DeployController", "searchStatus"),
    "部署_按应用名": ("DeployController", "selectPageByAppName"),
    "部署_条件查询": ("DeployController", "selectPageByConditions"),
    "部署_预计时间": ("DeployController", "expectDeployTime"),
    "部署_统计": ("DeployController", "statistics"),
    "部署_鉴权访问": ("DeployController", "authAccessUrl"),
    "发布_重启": ("DeploymentController", "restartApp"),
    "发布_就绪状态": ("DeploymentController", "getAppReadyStatus"),
    "发布_最近测试信息": ("DeploymentController", "latestTestInfo"),
    "发布_上线": ("DeploymentController", "appOnline"),
    "发布_上线新": ("DeploymentController", "appOnlineNew"),
    "发布_增量部署": ("DeploymentController", "appDeltaDeploy"),
    "沙箱_角色": ("SandboxController", "selectRoles"),
    "沙箱_按应用": ("SandboxController", "selectSandboxByAppId"),
    "沙箱_构建信息": ("SandboxController", "getBuildInfo"),
    "沙箱_增量构建": ("SandboxController", "getDeltaBuildInfo"),
    "沙箱_发布构建": ("SandboxController", "getReleaseBuildInfo"),
    "发布态_更新": ("PublishStateController", "update"),
    # 后端组件
    "组件_列表": ("BackendComponentController", "selectAllListByConditions"),
    "组件_应用分页": ("BackendComponentController", "selectAppPageByConditions",
                       "/udc/backend-component/search"),
    "组件_导入": ("BackendComponentController", "create"),
    "组件_刷新版本": ("BackendComponentController", "refreshVersion"),
    "组件_修改": ("BackendComponentController", "update"),
    "组件_详情": ("BackendComponentController", "selectById"),
    "组件_按依赖id列表": ("BackendComponentController", "selectListByDependentId"),
    "组件_刷新": ("BackendComponentController", "refreshComponent"),
    # 协作
    "协作_记录": ("AppCollaborationController", "selectCollaborationRecordsByAppId"),
    "协作_成员": ("AppCollaborationController", "selectCollaborationMembersByAppGuid"),
    "协作_创建成员": ("AppCollaborationController", "createMember"),
    "协作_删除成员": ("AppCollaborationController", "deleteMemberById"),
    "协作_移交": ("AppCollaborationController", "handoverApp"),
    "协作_当前组织成员": ("AppCollaborationController", "selectCurrentOrgMemberByCondition"),
    # 依赖分析
    "依赖分析_实体": ("DependencyAnalysisController", "dependencyAnalysis"),
    "依赖分析_关系": ("DependencyAnalysisController", "analysisAppDepRelationship"),
}


def _load() -> dict[str, Any]:
    if not _API.exists():
        return {}
    return json.loads(_API.read_text(encoding="utf-8"))


def _resolve(ctrl: str, spec: tuple, data: dict[str, Any]) -> dict[str, Any] | None:
    """按 (controller, 方法名[, 期望 full_path]) 定位唯一端点。

    同名重载（缺陷 A 修复后 657 -> 674 恢复 17 条）必须用 full_path 消歧，
    否则会静默取到第一个同名方法、把语义绑到错的端点上。
    """
    v = data.get(ctrl, {})
    name = spec[1]
    hint = spec[2] if len(spec) > 2 else None
    cands = [x for x in (v.get("methods") or []) if x["method"] == name]
    if hint is not None:
        return next((x for x in cands if x["full_path"] == hint), None)
    return cands[0] if cands else None


def application_api_map() -> dict[str, dict[str, Any]]:
    data = _load()
    out: dict[str, dict[str, Any]] = {}
    for op, spec in APPLICATION_OPS.items():
        ctrl = spec[0]
        v = data.get(ctrl, {})
        m = _resolve(ctrl, spec, data)
        out[op] = ({"controller": ctrl, "class_mapping": v.get("class_mapping"),
                    "http": m["http"], "full_path": m["full_path"],
                    "desc": m.get("desc", ""), "resolved": True}
                   if m else {"controller": ctrl, "method_name": spec[1], "resolved": False})
    return out


def application_summary() -> dict[str, Any]:
    data = _load()
    return {"schema": SCHEMA_ID,
            "controllers": {c: {"class_mapping": data.get(c, {}).get("class_mapping"),
                                "api_count": data.get(c, {}).get("api_count", 0)}
                            for c in APPLICATION_CONTROLLERS},
            "op_count": len(APPLICATION_OPS)}


__all__ = ["SCHEMA_ID", "APPLICATION_CONTROLLERS", "APPLICATION_OPS",
           "application_api_map", "application_summary"]
