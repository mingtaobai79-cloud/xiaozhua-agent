"""受控写执行器：把 WriteScope 授权的写操作真正发出去，并做写后回读。

与 ``PlatformOperationLayer`` 的分工：
  - Layer 负责契约查表、路径拼装、只读校验（它的 GET 只读路径已验证可用）。
  - 本模块负责**写**：直接 POST 到 UDC REST 面，附带证据（请求/响应/traceId），
    写完立刻用 findById 或 DB 回读核对。

为什么不用 Layer 发写：Layer 的 gateway_adapter 目前只做 GET 语义，且它的
``_verify`` 是只读身份校验。写操作需要自己的成功判据（BOE 信封 + 回读），
混进去会让只读路径也变复杂。保持两条链路清晰。

失败语义（用户明确要求）：**失败即停，不重试**。
任何一次写失败 → ``WriteScope.record_failure`` → 后续写全部拒绝。
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from .write_scope import WriteScope


@dataclass
class WriteEvidence:
    """一次写操作的完整证据（可复算）。"""

    operation: str
    url: str
    method: str
    request_body: Any = None
    http_status: int | None = None
    response_body: Any = None
    trace_id: str | None = None
    business_code: str | None = None
    business_status: Any = None
    ok: bool = False
    error: str | None = None
    readback: Any = None
    readback_ok: bool | None = None
    elapsed_ms: int | None = None
    at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation, "url": self.url, "method": self.method,
            "request_body": self.request_body, "http_status": self.http_status,
            "response_body": self.response_body, "trace_id": self.trace_id,
            "business_code": self.business_code, "business_status": self.business_status,
            "ok": self.ok, "error": self.error,
            "readback": self.readback, "readback_ok": self.readback_ok,
            "elapsed_ms": self.elapsed_ms, "at": self.at,
        }


class WriteExecutor:
    """按 WriteScope 授权执行写操作。

    ``base_url`` 例：``https://lowcode-test2.example.com``
    ``headers``  例：``{"Cookie": "SY_ACCESS_TOKEN=..."}``（由调用方提供，本模块不读凭据文件）
    """

    def __init__(self, base_url: str, headers: dict[str, str], *,
                 scope: WriteScope, timeout: float = 30.0,
                 allow_network: bool = False):
        self.base_url = base_url.rstrip("/")
        self.headers = dict(headers)
        self.headers.setdefault("Content-Type", "application/json")
        self.headers.setdefault("Accept", "application/json")
        self.scope = scope
        self.timeout = timeout
        self.allow_network = allow_network
        self.history: list[WriteEvidence] = []

    # ---------------------------------------------------------------- 底层 POST
    def _post(self, path: str, body: Any) -> tuple[int, Any, dict[str, str]]:
        if not self.allow_network:
            raise PermissionError("allow_network=False，拒绝任何网络写")
        url = f"{self.base_url}{path}"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self.headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read().decode("utf-8", "replace")
                return r.status, (json.loads(raw) if raw.strip().startswith("{") else raw), dict(r.headers)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = raw[:800]
            return e.code, parsed, dict(e.headers)

    # ---------------------------------------------------------------- 业务信封
    @staticmethod
    def _envelope(body: Any) -> tuple[bool, str | None, Any, str | None]:
        """解析 xiaozhua 业务信封。返回 (ok, code, status, traceId)。

        判据：HTTP 2xx 且业务 ``status == 0``。**BOOT_0000 / HTTP 200 单独不作为成功**，
        这是仓库既有铁律（TASK-GOAL 硬约束第 1 条）。
        """
        if not isinstance(body, dict):
            return False, None, None, None
        code = body.get("code")
        status = body.get("status")
        trace = body.get("traceId")
        ok = (status == 0) and (code in (None, "BOOT_0000"))
        return ok, code, status, trace

    # ---------------------------------------------------------------- 执行一次
    def execute(self, operation: str, path: str, body: Any, *,
                application_id: str, readback=None) -> WriteEvidence:
        """执行一次写。``readback`` 是一个零参可调用，返回回读结果（可选）。"""
        allowed, why = self.scope.allows(operation, str(application_id))
        ev = WriteEvidence(operation=operation, url=f"{self.base_url}{path}",
                           method="POST", request_body=body,
                           at=time.strftime("%Y-%m-%dT%H:%M:%S"))
        if not allowed:
            ev.ok = False
            ev.error = f"denied by scope: {why}"
            self.history.append(ev)
            return ev

        t0 = time.time()
        try:
            status, resp, hdrs = self._post(path, body)
        except PermissionError as exc:
            ev.ok = False
            ev.error = str(exc)
            self.scope.record_failure(ev.error)
            self.history.append(ev)
            return ev
        except Exception as exc:
            ev.ok = False
            ev.error = f"transport: {type(exc).__name__}: {str(exc)[:200]}"
            self.scope.record_failure(ev.error)   # 失败即停
            self.history.append(ev)
            return ev
        ev.elapsed_ms = int((time.time() - t0) * 1000)
        ev.http_status = status
        ev.response_body = resp
        ok, code, bstatus, trace = self._envelope(resp)
        ev.business_code = code
        ev.business_status = bstatus
        ev.trace_id = trace or (hdrs.get("Traceid") or hdrs.get("traceid"))

        if not (200 <= status < 300):
            ev.ok = False
            ev.error = f"HTTP {status}"
        elif not ok:
            ev.ok = False
            ev.error = f"业务失败 code={code} status={bstatus}"
        else:
            # 显式置 True：dataclass 默认 False，只置 False 的分支写法会让成功也停在 False
            ev.ok = True

        # 写后回读（只在写成功时才做，避免噪声）
        if ev.ok and readback is not None:
            try:
                ev.readback = readback()
                ev.readback_ok = True
            except Exception as exc:
                ev.readback_ok = False
                ev.readback = f"readback error: {type(exc).__name__}: {str(exc)[:200]}"

        if ev.ok:
            self.scope.record_success()
        else:
            self.scope.record_failure(ev.error or "unknown")   # 失败即停，不重试
        self.history.append(ev)
        return ev

    # ---------------------------------------------------------------- 报告
    def report(self) -> dict[str, Any]:
        return {
            "scope": self.scope.snapshot(),
            "writes": [e.to_dict() for e in self.history],
            "ok_count": sum(1 for e in self.history if e.ok),
            "fail_count": sum(1 for e in self.history if not e.ok),
        }


__all__ = ["WriteExecutor", "WriteEvidence"]
