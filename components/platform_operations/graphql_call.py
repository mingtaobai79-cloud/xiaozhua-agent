"""GraphQL 公用调用器 —— UDC 全平台的统一入口。

为什么抽这个
------------
`mutation/query graphqlLoader` 这套样板在仓内被手写了 **25 处**，每处都要
自己拼 query 字符串、自己解析响应。而响应是**双层**的，踩过两次：

```python
# ❌ 恒为 None：字段其实成功了，却判失败
ok = r.get("code") == "BOOT_0000"

# ✅ 正确层级
d0   = (r.get("data") or {}).get("data0") or {}
code = d0.get("code")
body = (d0.get("data") or {}).get("content")
```

同一轮里 `probe_setting_ops` 就因为这一条把 14 个存在的 op 全判成"未定"。

还有两个已经撞过的坑，都在本模块里一次性解决：

```
① str(None) == "None" 为真 → 拿 message 判真假会把"没返回"当"有返回"
② 空 body 回 BOOT_0000 不代表成功（delete 缺 id 时 content=0）
   → 本模块只做「结构解析」，**不做成功判定**；成功一律由调用方回读 DB
```

设计取舍
--------
本模块**只归一化结构**，不判断业务成功。`GraphqlResult.ok` 的含义是
「平台返回了 BOOT_0000 且 status==0」，这仍不等于「数据写对了」。
判据永远在调用方：DB 回读 / 页面渲染。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

GATEWAY_PATH = "/service/udc/graphql"

# 平台约定：成功码
OK_CODE = "BOOT_0000"

# 默认 selection —— 覆盖绝大多数写面的返回形状
DEFAULT_SELECTION = "code data { content } message status"


@dataclass
class GraphqlResult:
    """归一化后的 GraphQL 结果。"""

    operation: str
    http: int
    code: str | None
    status: int | None
    message: str | None
    trace_id: str | None
    content: object = None
    raw: dict = field(default_factory=dict)
    parse_error: str | None = None

    @property
    def ok(self) -> bool:
        """平台层成功。★ 不等于业务成功 —— 必须回读目标表。"""
        return self.code == OK_CODE and (self.status == 0)

    @property
    def is_empty_content(self) -> bool:
        """content 为空 / 0 / [] / {} —— 平台常见「假成功」形态。"""
        return self.content in (None, "", 0, [], {})

    def require_ok(self) -> "GraphqlResult":
        """调用方显式要求平台成功；不满足抛错（带上 code/message/trace）。"""
        if not self.ok:
            raise GraphqlCallError(
                "%s 失败：code=%s status=%s message=%s trace=%s"
                % (self.operation, self.code, self.status,
                   self.message, self.trace_id))
        return self


class GraphqlCallError(RuntimeError):
    """平台返回非成功，或响应无法解析。"""


def build_body(operation: str, params: dict | None = None, *,
               kind: str = "mutation",
               selection: str = DEFAULT_SELECTION,
               arg_name: str = "body",
               input_type: str | None = None,
               var_name: str = "params0") -> dict:
    """构造 GraphQL 请求体。

    operation  平台 operation 名，如 `udcEnumPost`
    params     真正的业务 body（进 variables）
    kind       mutation / query
    arg_name   平台签名里的参数名：写面多为 `body`，读面多为 `path`
    input_type 入参类型名，省略时按 `<op>InputBody` / `<op>InputPath` 推断
    """
    if not operation:
        raise ValueError("operation 不能为空")
    if kind not in ("mutation", "query"):
        raise ValueError("kind 只能是 mutation / query，收到 %r" % (kind,))
    if input_type is None:
        suffix = "InputPath" if arg_name == "path" else "InputBody"
        input_type = operation + suffix
    query = ("%s graphqlLoader ($%s: %s) { data0: %s(%s: $%s) { %s } }"
             % (kind, var_name, input_type, operation, arg_name, var_name, selection))
    return {"query": query, "variables": {var_name: params if params is not None else {}}}


def parse_response(operation: str, http: int, text: str) -> GraphqlResult:
    """解析响应。**双层结构**与 `str(None)` 两个坑都在这里处理。"""
    doc: dict = {}
    parse_error = None
    try:
        doc = json.loads(text)
    except Exception as exc:
        parse_error = "响应非 JSON：%s（前 120 字：%s）" % (exc, (text or "")[:120])
        doc = {}

    # GraphQL 错误数组（字段不存在等）优先暴露，别让它被静默当空结果
    errors = doc.get("errors") if isinstance(doc, dict) else None
    if errors:
        msg = str((errors[0] or {}).get("message"))[:200] if isinstance(errors, list) else str(errors)[:200]
        return GraphqlResult(operation=operation, http=http, code=None, status=None,
                             message=msg, trace_id=doc.get("traceId"),
                             raw=doc, parse_error="GraphQL errors")

    d0 = ((doc.get("data") or {}).get("data0") or {}) if isinstance(doc, dict) else {}
    # ★ 必须取嵌套 data0，不是顶层
    return GraphqlResult(
        operation=operation,
        http=http,
        code=d0.get("code") if isinstance(d0, dict) else None,
        status=d0.get("status") if isinstance(d0, dict) else None,
        # ★ 保留原始 None 语义，不 str() 化
        message=d0.get("message") if isinstance(d0, dict) else None,
        trace_id=doc.get("traceId") if isinstance(doc, dict) else None,
        content=((d0.get("data") or {}).get("content")) if isinstance(d0, dict) else None,
        raw=doc,
        parse_error=parse_error,
    )


# ---------------------------------------------------------------- 浏览器侧执行
_FETCH_JS = (
    '(async () => { const r = await fetch(PATH, {method:"POST", credentials:"include", '
    'headers:{"Content-Type":"application/json","Accept":"application/json"}, '
    'body: BODY}); const t = await r.text(); '
    'return JSON.stringify({http:r.status, body:t}); })()'
)


def call(client, operation: str, params: dict | None = None, *,
         kind: str = "mutation", selection: str = DEFAULT_SELECTION,
         arg_name: str = "body", input_type: str | None = None,
         path: str = GATEWAY_PATH) -> GraphqlResult:
    """在已连接的 CDP 页里发一次 GraphQL 调用并归一化。"""
    body = build_body(operation, params, kind=kind, selection=selection,
                      arg_name=arg_name, input_type=input_type)
    js = (_FETCH_JS
          .replace("PATH", json.dumps("%s?%s" % (path, operation)))
          .replace("BODY", json.dumps(json.dumps(body, ensure_ascii=False))))
    raw = json.loads(client.evaluate(js, await_promise=True))
    return parse_response(operation, raw.get("http"), raw.get("body"))


def call_query(client, operation: str, params: dict | None = None, **kw) -> GraphqlResult:
    """读面：参数名默认 `path`。"""
    kw.setdefault("kind", "query")
    kw.setdefault("arg_name", "path")
    return call(client, operation, params, **kw)


# ---------------------------------------------------------------- REST 侧
def call_rest(client, path: str, body: dict | None = None) -> dict:
    """REST 通道（字段集 / 二维码 / 导入导出模板走这条）。

    返回 {http, code, message, content}；404 表示路径不存在（VACUUM）。
    """
    js = (_FETCH_JS
          .replace("PATH", json.dumps(path))
          .replace("BODY", json.dumps(json.dumps(body or {}, ensure_ascii=False))))
    raw = json.loads(client.evaluate(js, await_promise=True))
    http, text = raw.get("http"), raw.get("body") or ""
    try:
        doc = json.loads(text)
    except Exception:
        return {"http": http, "code": None, "message": None,
                "content": None, "raw": text[:200],
                "vacuum": http == 404}
    return {
        "http": http,
        "code": doc.get("code"),
        "message": doc.get("message"),
        "content": (doc.get("data") or {}).get("content"),
        "raw": doc,
        # ★ 404 才是「路径不存在」；其余（含业务错误码）都是「存在」
        "vacuum": http == 404 or str(doc.get("code") or "").lower().find("server_404") >= 0,
    }
