"""Live readonly POST runner — opt-in live capability (P4) for readonly POST contracts.

xiaozhua UDC 的只读端点大部分是 POST（/udc-runtime/meta-data/* 等，7 域已坐实）。
静态层刻意把「POST 读型」判为 effective=False（执行链仅放行 GET），可执行性留活体（P4）。
本模块就是那个活体落点：用 agent 自己的 GatewayReadonlyClient(allow_network=True) +
按 ref 解析的 cookie 凭据 + config/environments.yaml 的环境常量，跑 test2 已坐实的 4 个
只读 POST 端点，出逐端点 PASS/BLOCKED + 双发 identity。

铁律 040402：URL/appId/版本/凭据 一律来自 config/ 与凭据引用，代码不写死机器值。
默认关：allow_network=False 时全端点 BLOCKED（不联网、不出伪造 live PASS）；
离线确定性测试用 stub client + fixture 凭据。
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from components.platform_operations.models import AuthContext


# --- 4 个 test2 已坐实的只读 POST 端点（operation_id + 端点路径 + 请求体） ---
# 路径/方法/DTO 与 registry.py 的 VERIFIED_STATIC_BYTECODE 契约一致；请求体取最小合法样本
# （select-host 用 appName 枚举；check-exists 需先枚举取样本，取不到即 BLOCKED 禁臆造；
#  page-log 用 pageInfo 空分页=读回面稳定）。
_READONLY_POST_ENDPOINTS: tuple[dict[str, Any], ...] = (
    {
        "op": "udc.page_info.select_host_and_only_page",
        "path": "udc-runtime/meta-data/select-host-and-only-page-pages",
        "method": "POST",
        "body_template": lambda app: {"appName": app},
        "sample_source": "self",          # 自身可枚举，直接发
        "nonempty_ok": True,             # content 可非空
    },
    {
        "op": "udc.page_info.check_exists",
        "path": "udc-runtime/meta-data/check-page-exists",
        "method": "POST",
        "body_template": None,           # 需先取样本；select-host 的样本源
        "sample_source": "from_select_host",
        "nonempty_ok": False,           # content=[bool] 空列表也算自证
    },
    {
        "op": "udc.page_log.search",
        "path": "udc-runtime/rt-page-log/search",
        "method": "POST",
        "body_template": lambda app: {"pageInfo": {"pageNo": 1, "pageSize": 20}},
        "sample_source": "self",
        "nonempty_ok": True,
    },
    {
        "op": "udc.page_log.search_non_metadata",
        "path": "udc-runtime/rt-page-log/search-non-metadata",
        "method": "POST",
        "body_template": lambda app: {"pageInfo": {"pageNo": 1, "pageSize": 20}},
        "sample_source": "self",
        "nonempty_ok": True,
    },
)


def _strip_trace_id(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_trace_id(v) for k, v in obj.items() if k != "traceId"}
    if isinstance(obj, list):
        return [_strip_trace_id(v) for v in obj]
    return obj


def _md5_stripped(raw: bytes) -> str:
    try:
        obj = json.loads(raw)
        return hashlib.md5(json.dumps(_strip_trace_id(obj), sort_keys=True).encode()).hexdigest()
    except Exception:
        return hashlib.md5(raw).hexdigest()


def _is_auth_fail(raw: bytes) -> bool:
    txt = raw.decode("utf-8", "replace")
    low = txt.lower()
    return ("BOOT_1006" in txt) or ("BOOT_1001" in txt and "redirectUrl" in txt) \
        or ("oauth" in low and "authorize" in low) or txt.startswith("401")


def _content_of(raw: bytes) -> Any:
    try:
        return json.loads(raw).get("data", {}).get("content")
    except Exception:
        return None


def _envelope_gates(http_status: Any, body: Any) -> list[str]:
    """验收门槛（a9 缺陷修复）：HTTP 非 2xx / 业务信封 status!=0 → 返回非空原因列表。

    背景：xiaozhua 业务信封 status=0 成功 / status=3（BOOT_3000 等）失败；
    HTTP 500 是传输层异常。runner 旧逻辑只比两次响应 identity（md5 相同），
    不查 status/envelope，导致 500 与业务错都判 PASS——验收器不可信。
    非 dict body（如流式下载）或无 status 键的 body 不做业务检查（不臆造）。
    """
    reasons: list[str] = []
    if isinstance(http_status, int):
        if not 200 <= http_status < 300:
            reasons.append(f"HTTP_{http_status}")
    else:
        reasons.append("HTTP_MISSING")
    if isinstance(body, dict) and "status" in body and body.get("status") != 0:
        reasons.append(f"BUSINESS_{body.get('status')}")
    return reasons


class LiveReadonlyRunner:
    """按 ref 解析凭据，对 4 个只读 POST 端点做双发 identity + 逐端点终态判定。

    gateway_client: 已配好 base_url/allow_network 的 GatewayReadonlyClient（须支持 .post）。
    resolve_headers(cred_ref): 返回 cookie 等请求头（供单请求生命周期使用，不持久化）。
    application_id: 目标 app（网关前缀由调用方拼进 base_url 或 path）。
    """

    def __init__(self, gateway_client, resolve_headers, application_id: str):
        self._client = gateway_client
        self._resolve_headers = resolve_headers
        self._app = application_id

    def run(self) -> dict[str, Any]:
        try:
            headers = dict(self._resolve_headers(self._app))
        except Exception as exc:
            return {"status": "BLOCKED", "reason": f"CREDENTIAL_RESOLUTION_FAILED: {exc}", "endpoints": {}}
        base = getattr(self._client, "base_url", "")
        results: dict[str, Any] = {}
        select_host_sample: Any = None

        for ep in _READONLY_POST_ENDPOINTS:
            key = ep["op"]
            path = f"{ep['path']}"
            if ep["body_template"] is not None:
                body = ep["body_template"](self._app)
                ok_to_send = True
            else:
                # check-exists：从 select-host 取一个合法样本（禁臆造）
                sample = select_host_sample
                if not sample:
                    results[key] = {"path": path, "verdict": "BLOCKED",
                                     "reason": "NO_SAMPLE_FROM_SELECT_HOST", "auth_fail": True}
                    continue
                body = {"pageExistsDtoList": sample[:3]}
                ok_to_send = True

            r1 = self._client.post(path, body=body, headers=headers)
            r2 = self._client.post(path, body=body, headers=headers)
            # client.post 返回 ProviderResult(dict) 带 response{status, body}
            resp1 = (r1.get("response") or {}) if not r1.error else {}
            resp2 = (r2.get("response") or {}) if not r2.error else {}
            raw1 = json.dumps(resp1.get("body"), ensure_ascii=False, sort_keys=True).encode() if resp1.get("body") is not None else b""
            raw2 = json.dumps(resp2.get("body"), ensure_ascii=False, sort_keys=True).encode() if resp2.get("body") is not None else b""
            if not resp1 or not resp2:
                err = r1.error or r2.error
                results[key] = {"path": path, "verdict": "BLOCKED",
                                "reason": f"TRANSPORT: {err.kind if err else 'no-response'}"}
                if key.endswith("select_host_and_only_page"):
                    select_host_sample = None
                continue
            m1, m2 = _md5_stripped(raw1), _md5_stripped(raw2)
            auth_fail = _is_auth_fail(raw1) or _is_auth_fail(raw2)
            identity = m1 == m2
            # 双读的语义是「两次独立请求都成功且内容一致」。只校验 resp1 会让
            # 「第一次 200 / 第二次 500」这类半失败升级成 PASS —— 一致性没有证据基础。
            # 因此两次响应都必须过信封门，并分别标注来源轮次（R1/R2）便于复算。
            gate1 = _envelope_gates(resp1.get("status"), resp1.get("body"))
            gate2 = _envelope_gates(resp2.get("status"), resp2.get("body"))
            gate = [f"R1:{g}" for g in gate1] + [f"R2:{g}" for g in gate2]
            gate_reason = None
            if auth_fail:
                verdict = "BLOCKED"
            elif gate:
                verdict = "BLOCKED"
                gate_reason = "+".join(gate)
            elif key.endswith("select_host_and_only_page"):
                content = _content_of(raw1)
                select_host_sample = content or []
                verdict = "PASS" if identity and select_host_sample else ("PASS" if identity else "BLOCKED")
            elif key.endswith("check_exists"):
                verdict = "PASS" if identity else "BLOCKED"
            else:
                verdict = "PASS" if identity else "BLOCKED"
            row = {"path": path, "verdict": verdict, "md5": m1, "ident": identity,
                   "auth_fail": auth_fail, "http1": resp1.get("status"), "http2": resp2.get("status")}
            if gate_reason:
                row["gate"] = gate_reason
            results[key] = row
        all_pass = all(v.get("verdict") == "PASS" for v in results.values()) and len(results) == len(_READONLY_POST_ENDPOINTS)
        return {"status": "PASS" if all_pass else "BLOCKED", "network": "explicit",
                "application_id": self._app, "endpoints": results}


def make_cookie_headers_resolver(credential: Mapping[str, Any]):
    """从 test2 凭据 JSON 渲染 cookie 请求头（值只用于单请求，不持久化）。"""
    def resolve(cred_ref: str) -> Mapping[str, str]:
        tmpl = str(credential.get("cookie_header_template", ""))
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if tmpl:
            cookie = (tmpl.replace("{sy_access_token}", str(credential.get("sy_access_token", "")))
                          .replace("{tk_exp}", str(credential.get("tk_exp", "")))
                          .replace("{sy_uid}", str(credential.get("sy_uid", ""))))
            headers["Cookie"] = cookie
        return headers
    return resolve


__all__ = ["LiveReadonlyRunner", "make_cookie_headers_resolver", "_READONLY_POST_ENDPOINTS"]
