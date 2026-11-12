"""live —— UDC 微流程「真实浏览器」探测驱动。零硬编码，全部运行时发现。

三个模块，职责单一：
  cdp.Driver   CDP WebSocket 驱动：挂 Network/Log 域抓接口 + Runtime.evaluate + 真实鼠标。
               从 /json/list 现查 tab（换域名/reload 后自动重连），不写死 tabId/wsUrl。
  env.Context  运行时环境发现：appId ← 编辑器 URL；appName ← 流程 schema 里
               com.seeyon.<appName>. 反推；实体/字段 ← udcMicroflowSearchTreeEntityPost /
               udcMicroflowFindDtoByEntityPost 现查；凭证 ← CDP Network.getAllCookies。
  ui           节点抽屉/下拉/提交通用操作：ensure_visible / click / open_select /
               pick_option / submit（三级兜底）。全部接 Driver，duck-typing 不绑具体应用。

用法：
    from components.udc.microflow.live import cdp, env, ui

    ctx = env.Context.load()                 # 自动发现 appId/mid/实体/字段/凭证
    d = cdp.Driver()                         # 完全运行时发现 tab，无需 tab_state
    d.attach()
    ui.open_node(d, "查询单条")              # 打开节点抽屉
    ...

环境变量：
  UDC_BASE   平台根地址（默认 http://localhost:3000）
  UDC_CDP    CDP 端点（默认 http://127.0.0.1:9222）
  UDC_COOKIE_FILE  兜底 cookie 文件（CDP 取不到时用）

依赖：websockets（CDP WebSocket 客户端）。
"""
from . import cdp, env, ui  # noqa: F401

__all__ = ["cdp", "env", "ui"]
