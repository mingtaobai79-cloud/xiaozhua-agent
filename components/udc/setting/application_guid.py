"""取 appGuid —— 设置域 9 个子域的共同前置，做成可复用入口。

为什么要有这个模块
------------------
设置域每个 `udc*Post` 都强制要 `appGuid`，而 `appGuid ≠ appId`。
以前这条规则写在 `core/facts/udc/setting/precondition-appguid.md` 里，
但**事实写了不等于能被找到**：

    在别处用 xiaozhua-agent 建枚举 → 第一步 appGuid 就卡住
    → 搜 INDEX 没有这一行 → 翻了三四分钟 → 最后直接查库

所以这条前置不能只作为「文档」，必须有一个**代码入口**：
调用方不需要知道 appGuid 从哪来，只调 `resolve_app_guid(client, app_id)`。

取法（LIVE 实证，2026-10-23）
---------------------------
```
POST /service/udc/graphql?udcApplicationDetailGet
  body {"query":"query graphqlLoader ($p0: udcApplicationDetailGetInputPath) { data0: udcApplicationDetailGet(path: $p0) { code data { content { id name guid caption } } message status } }",
        "variables":{"p0":{"id":"<appId>"}}}
  → data.data0.data.content.guid
```
- `path.id` 传 **appId**（不是 guid），返回体里的 `guid` 才是 appGuid
- selection 精简到 `{id name guid caption}` 即可（不必照抄页面的 19 字段）
- 偶发 `server_500 /udc/graphql 服务异常` 属瞬时抖动，重试即可，**不要改 payload**
- `GET /service/udc/application/{appId}` 返回 HTML，不是这条路
- 兜底（接口不可用时）：`SELECT guid FROM udc_application WHERE id = <appId>`

⚠ `appGuid` 缺了会怎样：`BOOT_1001`，或**静默落成 `app_guid=-1`**
（枚举项尤其明显：DB 查得到、页面「枚举管理」显示「暂无数据」）。
"""
from __future__ import annotations

import json

# 平台常量（不是测试值）：operation 与 selection
APP_DETAIL_OP = "udcApplicationDetailGet"
APP_DETAIL_QUERY = (
    "query graphqlLoader ($p0: udcApplicationDetailGetInputPath) { "
    "data0: udcApplicationDetailGet(path: $p0) { code data { content "
    "{ id name guid caption } } message status } }"
)
APP_DETAIL_PATH = "/service/udc/graphql?" + APP_DETAIL_OP


class AppGuidError(RuntimeError):
    """取不到 appGuid。带出原因，不要静默返回空串。"""


def _post(client, path: str, body: dict) -> dict:
    """（保留）原始请求通道。新代码请直接用 graphql_call.call。"""
    js = (
        '(async () => { const r = await fetch(' + json.dumps(path) + ', '
        '{method:"POST", credentials:"include", '
        'headers:{"Content-Type":"application/json","Accept":"application/json"}, '
        'body: ' + json.dumps(json.dumps(body, ensure_ascii=False)) + '}); '
        'const t = await r.text(); return JSON.stringify({http:r.status, body:t}); })()'
    )
    raw = json.loads(client.evaluate(js, await_promise=True))
    try:
        return json.loads(raw["body"])
    except Exception:
        raise AppGuidError("响应不是 JSON：%s" % raw["body"][:160])


def fetch_application(client, app_id) -> dict:
    """取应用详情（含 guid/name/caption）。失败抛错，不返回空。"""
    if app_id in (None, ""):
        raise AppGuidError("app_id 不能为空")
    # 走公用调用器：双层响应解析与 GraphQL 错误暴露都在那边统一处理
    from components.platform_operations.graphql_call import call_query
    res = call_query(client, APP_DETAIL_OP, {"id": str(app_id)},
                     selection="code data { content { id name guid caption } } message status")
    if res.parse_error and not res.code:
        raise AppGuidError("udcApplicationDetailGet 解析失败：%s" % res.message)
    if not res.ok:
        raise AppGuidError(
            "udcApplicationDetailGet 失败：code=%s msg=%s"
            % (res.code, res.message))
    content = res.content or {}
    if not content.get("guid"):
        # ★ 不返回空串兜底 —— 空 guid 会静默落成 app_guid=-1，比报错难查得多
        raise AppGuidError("接口返回没有 guid（app_id=%s）" % app_id)
    return content


def resolve_app_guid(client, app_id) -> str:
    """最常用：只要 appGuid 字符串。"""
    return str(fetch_application(client, app_id)["guid"])


def resolve_app_context(client, app_id) -> dict:
    """{appId, appGuid, appName, caption} —— 建对象时常要一起用。

    ★ appName 是 `datamigration<appId>` 这种形态，不是 caption。
    """
    c = fetch_application(client, app_id)
    return {"appId": str(app_id), "appGuid": str(c["guid"]),
            "appName": c.get("name"), "caption": c.get("caption")}


def app_guid_sql(app_id) -> tuple[str, tuple]:
    """接口不可用时的兜底查询（只读 provider 用）。"""
    return ("SELECT id, name, guid, caption FROM udc_application WHERE id = %s",
            (str(app_id),))
