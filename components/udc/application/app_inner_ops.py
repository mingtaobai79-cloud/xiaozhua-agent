"""应用内功能页取数口与请求体构造（纯函数，不联网）。

事实来源：2026-10-22 test2 实机抓包 + 主动重放，见
  core/facts/udc/application/app-inner/create.md
  core/facts/udc/application/app-inner/app-inner-write-chain.md
  docs/operation-contracts/udc/application/app-inner-contracts.md

设计约束：
  1. 只构造请求体与做形状校验，不发网络请求 —— 探针脚本负责发送。
  2. 写面（构建/依赖加删）构造出来的 body 带 ``_write=True`` 标记，
     调用方必须显式核对白名单才能发出。
  3. 一切路径常量都按仓库脱敏规则书写：网关主机用 ``<gateway-host>``，
     appId 用 ``9000000000000000001`` 占位。
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

SCHEMA_ID = "udc.application.app-inner.v1"
EVIDENCE_LEVEL = "LIVE"
EVIDENCE_DIR = "core/facts/udc/application/evidence/app-inner-build-2026-10-22"

# ---------------------------------------------------------------- 页面 / 日志

# 应用设计器左侧菜单 → 子路由（右侧「应用内功能页」区）
APP_INNER_PAGES: Dict[str, str] = {
    "testPage": "页面测试",
    "testVersion": "沙箱测试",
    "version": "发布版本",
    "dependentApp": "应用依赖",
    "dependentCmp": "组件依赖",
    "team": "团队设置",
    "appTheme": "应用主题",
}

# 设计器「检查」/「测试」面板下的四类日志 tab；只有前三类有独立取数口
APP_LOG_TYPES: Dict[str, str] = {
    "design": "设计日志",
    "microflow": "微流程运行日志",
    "dataflow": "生单规则运行日志",
    "deduction": "扣减规则运行日志",
}

# 应用日志的 REST 命名规则（证伪出来的：前缀是 {appName}/udc-runtime）
APP_LOG_PATH = "/service/{app_name}/udc-runtime/app-log/search/{log_type}"

# ---------------------------------------------------------------- 构建链路

# 工具栏「测试」→「立即构建」的六段链路，顺序即实测顺序
BUILD_CHAIN: Tuple[Dict[str, Any], ...] = (
    {"step": 1, "op": "udcApplicationSearchDetectionPost", "transport": "graphql",
     "kind": "mutation", "role": "一致性检测"},
    {"step": 2, "op": "udcRuntimeDeployNormalPost", "transport": "graphql",
     "kind": "write_declared_query", "role": "构建+部署"},
    {"step": 3, "op": "udcSandboxBuildInfoAppGet", "transport": "graphql",
     "kind": "query", "role": "构建信息轮询（含 logs[]）"},
    {"step": 4, "op": "udc_detection_channel", "transport": "ws",
     "kind": "push", "role": "检测/构建实时状态"},
    {"step": 5, "op": "udc_deploy_channel", "transport": "ws",
     "kind": "push", "role": "部署实时状态"},
    {"step": 6, "op": "common-message", "transport": "ws",
     "kind": "push", "role": "完成通知"},
)

WS_CHANNELS: Tuple[str, ...] = ("udc_detection_channel", "udc_deploy_channel", "common-message")

# 版本列表（REST 裸数组，IN_appId 传 appName 而不是数字 appId）
VERSION_LIST_PATH = "/service/ctp-application/appcenter/search-app-edition"

# 依赖设置
DEP_SELECT_OP = "udcApplicationDependentApplicationSelectByConditionPost"
DEP_CREATE_OP = "udcApplicationDependentApplicationCreateBatchPost"
DEP_DELETE_OP = "udcApplicationDependentApplicationDeleteByIdPost"
DEP_CANDIDATE_OP = "udcMetaDataSearchAvailableAppMultiVersionPost"
DEP_DETECTION_OP = "udcApplicationSearchDetectionPost"
# 组件依赖的批量删除走 REST，跟应用依赖的 GraphQL DeleteByIdPost 不是一条路
CMP_DELETE_PATH = "/service/udc/application/dependent-application/delete-by-ids"

_GRAPHQL_PREFIX = "/service/udc/graphql?"


# ---------------------------------------------------------------- 请求体构造

def _graphql(op: str, var_type: str, selection: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    query = (
        f"mutation graphqlLoader ($params0: {var_type}) {{ "
        f"data0: {op}(body: $params0) {{ code data {{ content }} message status }} }}"
    )
    return {"query": query, "variables": {"params0": variables}}


def build_build_info_query(app_id: str) -> Dict[str, Any]:
    """构建信息 / 沙箱日志。

    ⚠ 别名是 ``path:`` 不是 ``body:`` —— 照 ``body:`` 写会拿不到 data0。
    返回的 content 含 ``{state, progress, totalTime, buildVersion, logs[]}``，
    ``logs`` 就是「[展开沙箱日志]」的全部内容，不需要在构建窗口内抓流。

    ★ 参数类型必须声明成 ``Map``。实测 test2：
        udcSandboxBuildInfoAppGetInputBody  → GraphQL-3001 Unknown type
        udcSandboxBuildInfoAppGetInput      → 同上
        Map                                 → BOOT_0000，content 正常返回
      这个 operation 是 ``path:`` 入参，平台没给它生成 InputBody 类型
      （按名称猜 InputBody 是惯例陷阱，别的 operation 都有，这个没有）。
    """
    return {
        "query": (
            "query graphqlLoader ($params0: Map) { "
            "data0: udcSandboxBuildInfoAppGet(path: $params0) { code data { content } message status } }"
        ),
        "variables": {"params0": {"appId": app_id}},
        "_write": False,
    }


def build_deploy_normal(app_id: str, *, project_type: str = "ALL",
                        terminal_type: str = "ALL", deploy_type: str = "RELEASE") -> Dict[str, Any]:
    """构建+部署（沙箱「立即构建」）。

    ⚠ 平台把它声明成 ``query``，实际是写操作。``projectType/terminalType`` 取 ALL
    时前后端同时构建（实测 前端 PC 14s / 前端 MOBILE 8s / 后端编译 33s / 部署 124s）。
    """
    body = _graphql(
        "udcRuntimeDeployNormalPost",
        "udcRuntimeDeployNormalPostInputBody",
        "",  # selection 在 _graphql 里固定
        {"deployDto": {
            "projectType": project_type,
            "terminalType": terminal_type,
            "deployType": deploy_type,
            "appId": app_id,
            "generateLog": True,
        }},
    )
    body["_write"] = True
    return body


def build_dependency_create(app_id: str, *, dep_app_name: str, dep_app_caption: str,
                            dep_app_version: str, dep_app_base_package: str = "com.seeyon",
                            dependent_app_type: str = "SERVICE",
                            extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """添加依赖（应用依赖 SERVICE / 组件依赖 FRONTEND 共用同一个写口）。

    FRONTEND 行额外带 ``description/dynamicModuleGroup/dynamicService/enableDelete/
    needGenerate/sort/supportUpgrade/terminalType/sourceType/packageType``，
    实测 ``packageType=CONTROL``、``terminalType=PC``、``dynamicService=True``，
    用 ``extra`` 透传。
    """
    if dependent_app_type not in ("SERVICE", "FRONTEND"):
        raise ValueError("dependentAppType 只能是 SERVICE（应用依赖）或 FRONTEND（组件依赖）")
    row: Dict[str, Any] = {
        "appId": app_id,
        "depAppName": dep_app_name,
        "depAppCaption": dep_app_caption,
        "depAppVersion": dep_app_version,
        "depAppBasePackage": dep_app_base_package,
        "dependentAppType": dependent_app_type,
    }
    if extra:
        row.update(extra)
    body = _graphql(
        DEP_CREATE_OP,
        "[udcApplicationDependentApplicationCreateBatchPostInputBody]",
        "",
        [row],
    )
    body["_write"] = True
    return body


def build_dependency_delete(row_id: str) -> Dict[str, Any]:
    """移除应用依赖。

    ⚠ ``id`` 是**依赖行 id**，不是 appId、也不是 depAppName。
    传后两者平台不会报错，只会删不掉（或删错行），这是本项目踩过的坑。
    """
    if not str(row_id).lstrip("-").isdigit():
        raise ValueError("param 必须是依赖行 id（纯数字），不是 appId / depAppName")
    body = _graphql(
        DEP_DELETE_OP,
        "udcApplicationDependentApplicationDeleteByIdPostInputBody",
        "",
        {"id": str(row_id)},
    )
    body["_write"] = True
    return body


def build_component_delete(ids: Iterable[str]) -> Dict[str, Any]:
    """组件依赖批量删除（REST，body ``{"ids":[...]}``）。

    该请求用 CDP ``requestWillBeSent`` 常抓不到（事件被 Runtime.evaluate 往返吞掉），
    要用页面内 hook XMLHttpRequest/fetch 记 ``window.__CAP__``。
    """
    id_list: List[str] = [str(i) for i in ids]
    if not id_list:
        raise ValueError("ids 不能为空")
    for i in id_list:
        if not i.lstrip("-").isdigit():
            raise ValueError(f"非法依赖行 id: {i!r}")
    return {"url": CMP_DELETE_PATH, "body": {"ids": id_list}, "_write": True}


def build_version_list(app_name: str, *, page_size: int = 20) -> Dict[str, Any]:
    """发布版本列表（REST 裸数组，不套 code 信封）。``IN_appId`` 传 appName 字符串。"""
    return {
        "url": VERSION_LIST_PATH,
        "body": {
            "pageInfo": {"needTotal": False, "pageNumber": 1, "pageSize": page_size},
            "params": {"IN_appId": [app_name], "clientType": "PC"},
        },
        "_write": False,
    }


# ---------------------------------------------------------------- 归属分类

def is_application_inner_path(path: str) -> bool:
    """是否属于应用内功能页的取数口（用于探针过滤 / 只读面审计）。"""
    p = path.split("?", 1)[0]
    return bool(
        p.startswith(_GRAPHQL_PREFIX)
        or p.startswith("/service/ctp-application/appcenter/search-app-edition")
        or p.startswith("/service/udc/application/dependent-application/")
        or "/udc-runtime/app-log/search/" in p
    )


def classify(path: str) -> Tuple[str, str]:
    """把一条请求归到 (子路由, 入口名)；无法归类返回 ("unknown", "")。"""
    p = path.split("?", 1)[0]
    op = path.split("?", 1)[1] if "?" in path else ""
    table = {
        DEP_CANDIDATE_OP: ("dependentApp", "可选应用"),
        DEP_SELECT_OP: ("dependentApp|dependentCmp", "依赖列表"),
        DEP_CREATE_OP: ("dependentApp|dependentCmp", "添加依赖"),
        DEP_DELETE_OP: ("dependentApp", "移除依赖"),
        DEP_DETECTION_OP: ("dependentApp", "写后一致性检测"),
        "udcRuntimeDeployNormalPost": ("testVersion", "构建+部署"),
        "udcSandboxBuildInfoAppGet": ("testVersion", "构建信息/日志"),
        "udcDeploymentAppReadyStatePost": ("testVersion", "沙箱就绪态"),
        "udcCollaborationAppGet": ("team", "团队设置"),
        "udcOperationLogSearchInitDataAppGet": ("design", "操作日志 init"),
    }
    if op in table:
        return table[op]
    if p.endswith("/dependent-application/delete-by-ids"):
        return ("dependentCmp", "组件依赖批量删除")
    if p.endswith("/search-app-edition"):
        return ("version", "发布版本列表")
    if "/app-log/search/" in p:
        return ("design", "应用日志 " + p.rsplit("/", 1)[-1])
    return ("unknown", "")
