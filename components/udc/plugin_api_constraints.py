"""UDC 插件契约边界（udc-plugin-api 5.3.517）约束模型。

证据（CFR 反编译 udc-plugin-api-5.3.517.jar）：
- com.seeyon.udc.api.*（24 个 AppService 接口，应用/实体/页面/枚举/流水号/门户对外契约）
- com.seeyon.udc.auth.*（AuthCheck/AuthCheckFacade/AuthOperationType 权限模型）
- app_feature/{6类}/backend_config.json（应用类型功能开关，jar 内资源）

用途：
1. 应用类型（6 种）→ 实体 stereotype → 宿主依赖 三级约束（什么应用能建什么实体）
2. 权限操作类型（AuthOperationType）与 AuthCheck 契约
3. 插件契约层方法目录（ApplicationAppService 52 方法等）
"""
from __future__ import annotations

# ---- 应用类型（app_feature/backend_config.json，6 种，jar 内资源权威）----
APP_FEATURE_TYPES: tuple[str, ...] = (
    "BUSINESS", "STANDARD", "FORM", "INTEGRATION", "LAYOUT", "ONLYPAGE")

# ---- 应用类型 → 实体版型（stereotype）矩阵 ----
#   ★约束：实体 stereotype 必须在所属应用类型允许的版型集合内
APP_TYPE_STEREOTYPES: dict[str, tuple[str, ...]] = {
    "BUSINESS": ("archive", "archiveTree", "bill", "standard"),
    "STANDARD": ("standard",),
    "FORM": ("standard", "form"),
    "INTEGRATION": ("standard",),
    "LAYOUT": ("standard", "form"),
    "ONLYPAGE": ("standard", "form"),
}
APP_TYPE_DEFAULT_STEREOTYPE: dict[str, str] = {
    "BUSINESS": "standard", "STANDARD": "standard", "FORM": "form",
    "INTEGRATION": "standard", "LAYOUT": "standard", "ONLYPAGE": "standard",
}

# ---- 应用类型 → 宿主依赖（dependentService）----
APP_TYPE_DEPENDS: dict[str, tuple[str, ...]] = {
    "BUSINESS": ("organization", "bpm", "ctp-affair", "ctp-message", "cip-connector",
                 "cdp-data", "portal", "ctp-user", "app-common"),
    "STANDARD": ("organization", "ctp-message", "cip-connector", "cdp-data", "portal", "ctp-user"),
    "FORM": ("organization", "ctp-user", "bpm", "ctp-affair", "app-common"),
    "INTEGRATION": ("organization", "ctp-user"),
    "LAYOUT": ("organization", "ctp-user", "ctp-affair", "bpm"),
    "ONLYPAGE": ("organization", "ctp-user", "bpm"),
}

# ---- 应用类型 → 是否动态服务 ----
APP_TYPE_DYNAMIC: dict[str, bool] = {
    "BUSINESS": False, "STANDARD": False,
    "FORM": True, "INTEGRATION": True, "LAYOUT": True, "ONLYPAGE": True,
}

# ---- 权限操作类型（AuthOperationType，4 种+code）----
AUTH_OPERATION_TYPES: dict[str, int] = {"CREATE": 1, "DELETE": 2, "UPDATE": 3, "SELECT": 4}
AUTH_OPERATION_UNKNOWN: str = "UNKNOWN"  # code=0

# ---- AuthCheck 契约（接口形态）----
#   AuthCheck.check(AuthOperationType, UdcBaseEntityDto | Long) -> AuthCheckResultDto
#   AuthCheckFacade.check(AuthModel, AuthOperationType, UdcBaseEntityDto | Long)
#   AuthModel 是注解（@AuthModel(name=...)），模型名与实体/资源对应
#   AuthCheckResultDto: {success: bool, message: str, msgParams: str[]}

# ---- 插件契约层 AppService 目录（24 个，方法数）----
PLUGIN_API_SERVICES: dict[str, int] = {
    "ApplicationAppService": 52,
    "UdcCtpEnumAppService": 16,
    "UdcPortalPortletAppService": 7,
    "ResourceAppService": 6,
    "UdcSerialSchemeAppService": 5,
    "LastVersionMetadataManagerService": 5,
    "PluginPageInfoAppService": 5,
    "UdcCtpEnumProxyAppService": 6,
    "UdcFunctionAppService": 4,
    "ConsistenceDetectionAppService": 4,
    "PluginReferConfigGroupAppService": 3,
    "UdcPageLayoutPluginAppService": 3,
    "ApplicationShelfService": 2,
    "LateralAuthChecker": 2,
    "PluginEntityAppService": 2,
    "DeployBeforeService": 1,
    "DeployFinishService": 1,
    "ExprConsistencyValidator": 1,
    "ExtendAppOperationAuthCheck": 1,
    "MetadataHandleService": 1,
    "PluginAttributeAppService": 1,
    "UdcBpmAppService": 1,
    "UdcPortalSetAppService": 1,
    "UdcPortalSpaceAppService": 1,
}
# UdcSerialSchemeAppService（流水号方案插件契约）
SERIAL_SCHEME_OPERATIONS: tuple[str, ...] = (
    "selectSerialScheme", "selectSerialSchemeById", "selectSerialRange",
    "createEasyScheme", "selectDepAppSerialScheme",
)


def validate_entity_stereotype_for_app(app_type: str, stereotype: str) -> list[str]:
    """校验应用类型与实体版型的匹配（空=通过）。"""
    errs: list[str] = []
    allowed = APP_TYPE_STEREOTYPES.get(app_type)
    if allowed is None:
        errs.append(f"未知应用类型 '{app_type}'（见 APP_FEATURE_TYPES）")
        return errs
    if stereotype not in allowed:
        errs.append(
            f"应用类型 {app_type} 不支持实体版型 '{stereotype}'"
            f"（允许：{', '.join(allowed)}）")
    return errs


def validate_app_type(app_type: str) -> list[str]:
    """校验应用类型本身合法。"""
    if app_type not in APP_FEATURE_TYPES:
        return [f"未知应用类型 '{app_type}'（见 APP_FEATURE_TYPES）"]
    return []


def app_type_depends_complete(app_type: str, host_apps: list[str]) -> list[str]:
    """校验宿主依赖是否齐全（缺依赖=应用无法运行）。"""
    errs: list[str] = []
    need = APP_TYPE_DEPENDS.get(app_type)
    if need is None:
        return [f"未知应用类型 '{app_type}'"]
    missing = [d for d in need if d not in host_apps]
    if missing:
        errs.append(f"应用类型 {app_type} 缺少宿主依赖：{', '.join(missing)}")
    return errs


def default_stereotype_for(app_type: str) -> str | None:
    """应用类型的默认实体版型。"""
    return APP_TYPE_DEFAULT_STEREOTYPE.get(app_type)
