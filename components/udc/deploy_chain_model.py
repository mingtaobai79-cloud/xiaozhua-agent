"""构建/部署链 op 目录 —— GraphQL 面 op 名/参数形态/状态机固化。

证据基线（docs/audit/udc-semantics/SETTINGS-TABS-CALLCHAIN.md 附节，2026-10-12 抓包 + 主 store）：
- URL query 形态：POST /service/udc/graphql?<op名>；?op 与 body.operationName 两形态
  均活体验证 BOOT_0000（一致）。
- udcRuntimeDeployNormalPost = 测试构建执行器：
  paramsType=InputBody、paramsKey=body、**params={deployDto:e}（必须按形参名包裹）**、
  queryFields=content{appId,deployId,deployType,projectType,terminalType}、走 queryLoader（非 mutation）。
  平铺 body → DTO=null → EL1007E（09-27 LIVE 教训，registry udc.deploy.normal note 同源）。
- 就绪/状态/上线 op 族（附节全表）；状态枚举 NONE|STOP|RUNNING|PENDING|FAILED|UNKNOWN。
- 前端拼装形态（DATADICT §5.1 chunk 原文）：
  RELEASE 全量={projectType:ALL,terminalType:ALL,deployType:RELEASE,appId,generateLog}
  DELTA 前端增量={deployType:DELTA,appId,projectType:FRONTEND,terminalType:ALL}
  页面调试={appId,projectType:FRONTEND,terminalType:PC|MOBILE}
  上线=udcDeploymentAppOnlineNewPost + {...e, deployType:"ON_ONLINE"}
- DeployParamDto 字段（DATADICT §5.2 javap）：appId:Long/deployType/projectType/
  terminalType/deployId/pushEnv/extraParamMap；DeployNormalDto 附加 generateLog/
  lockCompatibility/entityFullNameCondition。
- 错误码特判：UDC_DEPLOY_0002（前端 catch → 触发重新构建）。
- 硬门：一致性检测（CdpDataDetectionTask ~2 分钟）不过则整单 state=2，无部分成功。

纪律：can_execute=False（写面 DENIED，宿主授权执行）；
构建必须走设计器页面按钮抓包等价性验证后才可称页面按钮路径（此边界未闭合，见 round3）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_ID = "udc.xiaozhua-agent.deploy-op-catalog.v1"

DEPLOY_STATE_ENUM: tuple[str, ...] = ("NONE", "STOP", "RUNNING", "PENDING", "FAILED", "UNKNOWN")

DEPLOY_TYPES: tuple[str, ...] = ("TEST", "RELEASE", "ON_ONLINE", "DELTA")
PROJECT_TYPES: tuple[str, ...] = ("ALL", "FRONTEND", "BACKEND")   # ProjectTypeEnum（DATADICT §5.2）
TERMINAL_TYPES: tuple[str, ...] = ("ALL", "PC", "MOBILE")

# 构建 op 族（GraphQL 面，op 名即 URL query 形态）
DEPLOY_OPS: dict[str, dict[str, Any]] = {
    "udcRuntimeDeployNormalPost": {
        "purpose": "测试构建执行器（deploy-normal）",
        "params_key": "body", "params_type": "...InputBody",
        "wrapper": "deployDto",           # params={deployDto:e} 强制包裹
        "query_fields": "content{appId,deployId,deployType,projectType,terminalType}",
        "loader": "queryLoader",
        "write": True,
    },
    "udcDeploymentAppOnlineNewPost": {
        "purpose": "上线发布（deployType=ON_ONLINE 强制）",
        "params_key": "body", "wrapper": None,
        "extra": {"deployType": "ON_ONLINE"},
        "write": True,
    },
    "udcDeploymentAppReadyStatePost": {
        "purpose": "就绪状态", "params_key": "body", "params": {"appId": "<appId>"},
        "write": False,
        "live_shape": "{validate, appName, appVersion, appId, terminalType:null, enableLoginEntry, enableClearEntry, state}",
    },
    "udcDeploymentLatestTestInfoPost": {
        "purpose": "最新测试部署信息", "params_key": "body", "write": False,
    },
    "udcManagerRequestStatusRequestGet": {
        "purpose": "构建请求状态", "params_key": "path",
        "params_type": "...InputPath", "write": False,
    },
    "udcRuntimeAuthAccessUrlPost": {
        "purpose": "沙箱/构建访问 URL", "params_key": "body", "params": {"appName": "<appName>"},
        "write": False,
    },
}

# 前端拼装形态（chunk 原文语义，非发明）
ASSEMBLY_SHAPES: dict[str, dict[str, Any]] = {
    "release_full": {"projectType": "ALL", "terminalType": "ALL",
                     "deployType": "RELEASE", "appId": "<id>", "generateLog": True},
    "delta_frontend": {"deployType": "DELTA", "appId": "<id>",
                       "projectType": "FRONTEND", "terminalType": "ALL"},
    "page_debug": {"appId": "<id>", "projectType": "FRONTEND", "terminalType": "<PC|MOBILE>"},
    "online": {"appId": "<id>", "deployType": "ON_ONLINE"},
}

# DeployNormalDto 字段（javap，DATADICT §5.2；继承 DeployParamDto）
DEPLOY_PARAM_FIELDS: tuple[str, ...] = (
    "appId", "deployType", "projectType", "terminalType", "deployId", "pushEnv", "extraParamMap")
DEPLOY_NORMAL_EXTRA_FIELDS: tuple[str, ...] = ("generateLog", "lockCompatibility", "entityFullNameCondition")

SPECIAL_ERROR_CODES: dict[str, str] = {
    "UDC_DEPLOY_0002": "前端 catch 特判 → 触发重新构建逻辑（不是终止态）",
    "EL1007E": "deployDto 平铺（未按形参名包裹）→ DTO=null",
}

HARD_GATES: tuple[str, ...] = (
    "一致性检测 CdpDataDetectionTask（约 2 分钟）不过 → 整单 state=2，无部分成功；明细只在 Redis",
    "构建即部署（非实体级 publish 密码面）",
    "沙箱/发布链依赖构建成功：构建 FAIL 时写链 BLOCKED（本 app 1.0.2 实证）",
)


@dataclass
class DeployRequest:
    """构建 dry-run 请求体生成（只组包，不执行；can_execute=False）。"""
    app_id: str = ""
    deploy_type: str = "RELEASE"
    project_type: str = "ALL"
    terminal_type: str = "ALL"
    generate_log: bool = True

    def validate(self) -> tuple[list[str], list[str]]:
        errors, unknowns = [], []
        if not self.app_id:
            errors.append("缺 appId")
        if self.deploy_type not in DEPLOY_TYPES:
            errors.append(f"deployType={self.deploy_type!r} 不在 {DEPLOY_TYPES}")
        if self.project_type not in PROJECT_TYPES:
            errors.append(f"projectType={self.project_type!r} 不在 {PROJECT_TYPES}")
        if self.terminal_type not in TERMINAL_TYPES:
            errors.append(f"terminalType={self.terminal_type!r} 不在 {TERMINAL_TYPES}")
        return errors, unknowns

    def body(self) -> dict[str, Any]:
        """强制 deployDto 包裹形态（平铺即 EL1007E，LIVE 教训）。"""
        return {"deployDto": {
            "appId": self.app_id, "deployType": self.deploy_type,
            "projectType": self.project_type, "terminalType": self.terminal_type,
            "generateLog": self.generate_log,
        }}

    def dry_run(self) -> dict[str, Any]:
        errors, unknowns = self.validate()
        status = "FAIL" if errors else "DRY_RUN_ONLY"
        return {"schema": SCHEMA_ID, "kind": "deploy_request", "status": status,
                "op": "udcRuntimeDeployNormalPost",
                "http": "POST /service/udc/graphql?udcRuntimeDeployNormalPost",
                "body": self.body(),
                "errors": errors, "unknowns": unknowns,
                "can_execute": False,
                "note": "agent 只出方案；执行=宿主授权面；页面按钮等价性未抓包前不得称页面路径"}


def catalog() -> dict[str, Any]:
    return {"schema": SCHEMA_ID, "date": "2026-10-12",
            "evidence": "docs/audit/udc-semantics/SETTINGS-TABS-CALLCHAIN.md 附节 + DATADICT-AND-BASESETTING-APIS.md §5",
            "url_forms": ["POST /service/udc/graphql?<op名>（Apollo 带 op query）",
                          "POST /service/udc/graphql（body.operationName）",
                          "两形态活体一致 BOOT_0000"],
            "ops": {k: v for k, v in DEPLOY_OPS.items()},
            "assembly_shapes": ASSEMBLY_SHAPES,
            "dto_fields": {"param": list(DEPLOY_PARAM_FIELDS), "normal_extra": list(DEPLOY_NORMAL_EXTRA_FIELDS)},
            "state_enum": list(DEPLOY_STATE_ENUM),
            "special_error_codes": SPECIAL_ERROR_CODES,
            "hard_gates": list(HARD_GATES)}


__all__ = [
    "SCHEMA_ID", "DEPLOY_STATE_ENUM", "DEPLOY_TYPES", "PROJECT_TYPES", "TERMINAL_TYPES",
    "DEPLOY_OPS", "ASSEMBLY_SHAPES", "DEPLOY_PARAM_FIELDS", "DEPLOY_NORMAL_EXTRA_FIELDS",
    "SPECIAL_ERROR_CODES", "HARD_GATES", "DeployRequest", "catalog",
]
