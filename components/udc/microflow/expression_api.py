"""表达式后端校验 —— /check 与 /transform 的正式封装。

## 为什么微流程也能用

早期认为「微流程用不了表达式接口」，因为 `/expression/schema`
对 `paramType=MICROFLOW` 返回 `BOOT_3000`（未注册）。

**这是错的。** 前端从不调 `/schema`，它走的是：

    schemas  ← 从主流程节点元数据自己拼（dataSchema 里就有）
    tokens   ← 表达式里现成的
    POST /expression/check      → content:true
    POST /expression/transform  → designData + runtimeData

`/check` 与 `/transform` **只要 schemas，不要 paramType**，所以微流程完全能用。

## 关键细节

- `schemas` 每层必须带 `skip: true`
- `executableExpr` 前缀（`93gDaq3/...`）是服务端固定产物，
  同一表达式多次 transform 结果一致，不是逐次签名
- 请求必须在页面内发（带会话 cookie），且 `await_promise=True`

## 用法

    from components.udc.microflow.expression_api import (
        build_save_dto, context_to_schemas, check_expression_remote,
        transform_expression_remote,
    )

    dto = build_save_dto(expr)          # expr 为 dataSchema 里的 expression 对象
    r = check_expression_remote(d, dto)  # {'ok': True, 'code': 'BOOT_0000', ...}
"""
from __future__ import annotations

import json

from .expression_audit import parse_expression

# schemas 节点保留的键（context → schemas 的映射白名单）
SCHEMA_KEYS: tuple[str, ...] = (
    "name", "description", "type", "selectable",
    "enableDataI18n", "uniformityParams", "properties",
)

# schemas 必须带的标记键
SCHEMA_MARKER_KEY = "skip"

EXPRESSION_PREFIX = "/service/udc/expression"
CHECK_PATH = "/check"
TRANSFORM_PATH = "/transform"

_FETCH_JS = r"""
(async () => {
  const r = await fetch(%(url)s, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: %(body)s
  });
  const t = await r.text();
  let j = null;
  try { j = JSON.parse(t); } catch (e) {}
  return JSON.stringify({status: r.status, json: j, raw: t.slice(0, 1500)});
})()
"""


def context_to_schemas(context: list) -> list:
    """designData.context → ExpressionSaveDto.schemas。

    差异只有两处：每层加 `skip: true`；不带 pageNodeExtension。
    """
    def conv(node):
        if not isinstance(node, dict):
            return node
        out = {k: node[k] for k in SCHEMA_KEYS if k in node}
        out[SCHEMA_MARKER_KEY] = True
        if node.get("properties"):
            out["properties"] = [conv(c) for c in node["properties"]]
        return out

    return [conv(c) for c in context or []]


def build_save_dto(expr: dict) -> dict:
    """从 dataSchema 里的 expression 对象装配 ExpressionSaveDto。"""
    info = parse_expression(expr)
    return {
        "resultTypeInfo": info["resultType"],
        "schemas": context_to_schemas(info["context"]),
        "tokens": [
            {k: t.get(k) for k in ("uid", "type", "value", "desc", "subOps",
                                   "controlData")
             if t.get(k) is not None}
            for t in info["tokens"]
        ],
        "isMultiSelect": bool(info.get("isMultiSelect", False)),
        "terminalSupportType": info["terminalType"],
    }


def _post(d, path: str, body: dict) -> dict:
    expr = _FETCH_JS % {
        "url": json.dumps(EXPRESSION_PREFIX + path),
        "body": json.dumps(json.dumps(body, ensure_ascii=False)),
    }
    raw = d.eval(expr, await_promise=True)
    if not isinstance(raw, str):
        return {"status": None, "json": None, "error": str(raw)}
    try:
        return json.loads(raw)
    except Exception:
        return {"status": None, "json": None, "raw": raw[:800]}


def _verdict(resp: dict, need_content_true: bool = False) -> dict:
    j = resp.get("json") or {}
    code = j.get("code")
    content = (j.get("data") or {}).get("content")
    ok = code == "BOOT_0000"
    if need_content_true:
        ok = ok and content is True
    return {
        "ok": ok,
        "code": code,
        "message": j.get("message"),
        "content": content,
        "status": resp.get("status"),
        "raw": resp.get("raw"),
    }


def check_expression_remote(d, dto: dict) -> dict:
    """POST /expression/check。ok=True 表示 code=BOOT_0000 且 content=true。"""
    return _verdict(_post(d, CHECK_PATH, dto), need_content_true=True)


def transform_expression_remote(d, dto: dict) -> dict:
    """POST /expression/transform。成功时 content 含 designData + runtimeData。"""
    v = _verdict(_post(d, TRANSFORM_PATH, dto))
    content = v.get("content")
    if isinstance(content, dict):
        rt = (content.get("runtimeData") or {}).get("executableExpr") or ""
        v["executableExpr"] = rt
        v["designData"] = content.get("designData")
    return v


def verify_expression(d, expr: dict) -> dict:
    """一条表达式的完整校验：先 check 再 transform，并比对库中 executableExpr。"""
    info = parse_expression(expr)
    dto = build_save_dto(expr)

    chk = check_expression_remote(d, dto)
    out = {"check": chk, "transform": None, "roundtripSame": None}

    if chk["ok"]:
        tr = transform_expression_remote(d, dto)
        out["transform"] = tr
        if tr["ok"]:
            old = info.get("executableExpr") or ""
            new = tr.get("executableExpr") or ""
            out["roundtripSame"] = (old == new) if old else None

    out["ok"] = bool(chk["ok"] and out["transform"] and out["transform"]["ok"])
    return out
