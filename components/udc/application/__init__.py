"""UDC 应用域实现（九域之一：应用）。

当前覆盖：
  app_inner_ops            应用内功能页（页面测试/沙箱测试/发布版本/依赖/团队/主题 + 四类日志）
                           的取数口、请求体构造与路径归属分类（纯函数，不联网）
  dependency_constraints   依赖设置（应用依赖 SERVICE / 组件依赖 FRONTEND）的本地校验

证据等级：LIVE（2026-10-22 test2 全程抓包 + 主动重放）
事实格：core/facts/udc/application/app-inner/create.md
契约：  docs/operation-contracts/udc/application/app-inner-contracts.md
"""

from components.udc.application.app_inner_ops import (  # noqa: F401
    APP_INNER_PAGES,
    APP_LOG_TYPES,
    BUILD_CHAIN,
    WS_CHANNELS,
    build_build_info_query,
    build_dependency_create,
    build_dependency_delete,
    build_deploy_normal,
    classify,
    is_application_inner_path,
)
