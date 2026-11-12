"""平台操作层：Intent、Contract、Adapter 与 OperationResult 的唯一编排边界。"""
from __future__ import annotations

import re
from collections.abc import MutableSequence
from typing import Any

from .models import ErrorKind, ExecutionContext, OperationIntent, OperationRequest, OperationResult, OperationStatus


class PlatformOperationLayer:
    def __init__(self, registry, udc_adapter, gateway_adapter):
        self.registry = registry
        self.udc_adapter = udc_adapter
        self.gateway_adapter = gateway_adapter

    def execute(self, intent: OperationIntent, execution_context: ExecutionContext | None = None, *, session: MutableSequence[dict[str, Any]] | None = None, write_scope=None) -> OperationResult:
        if execution_context is None:
            return self._record(session, OperationResult(intent.operation, OperationStatus.BLOCKED, intent.mode, None, None, error={"kind": ErrorKind.CONNECTION_ERROR.value, "code": "MISSING_EXECUTION_CONTEXT", "message": "execution context is required"}))
        if not self.registry.has(intent.operation):
            return self._record(session, self._result(intent, OperationStatus.UNVERIFIED, execution_context, error={"kind": ErrorKind.DISCOVERY_ERROR.value, "code": ErrorKind.DISCOVERY_ERROR.value, "message": "operation contract is not declared"}, unknowns=["operation contract is missing"]))
        contract = self.registry.get(intent.operation)
        # 写通道：只有显式传入 WriteScope 且该 operation/app 都在白名单内才放行。
        # 不传 write_scope（默认）时行为与改动前完全一致：一律 DENIED。
        is_write = bool(contract.write) or contract.method != "GET"
        if is_write:
            allowed = False
            deny_reason = "write scope not provided (fail-closed)"
            if write_scope is not None:
                allowed, deny_reason = write_scope.allows(
                    contract.operation_id, str(intent.application_id))
            if not allowed:
                return self._record(session, self._result(
                    intent, OperationStatus.DENIED, execution_context,
                    error={"kind": ErrorKind.POLICY_DENIED.value,
                           "code": ErrorKind.POLICY_DENIED.value,
                           "message": f"write denied: {deny_reason}"},
                    evidence=list(contract.evidence)))
        elif not contract.effective:
            return self._record(session, self._result(intent, OperationStatus.DENIED, execution_context, error={"kind": ErrorKind.POLICY_DENIED.value, "code": ErrorKind.POLICY_DENIED.value, "message": "operation is not an effective GET-only readonly contract"}, evidence=list(contract.evidence)))
        if execution_context.auth_scope and f"{intent.application_id}:readonly" not in execution_context.auth_scope and not is_write:
            return self._record(session, self._result(intent, OperationStatus.DENIED, execution_context, error={"kind": ErrorKind.POLICY_DENIED.value, "code": "AUTH_SCOPE_DENIED", "message": "application is outside auth scope"}))
        request = self._request(intent, contract)
        gateway_result = self.gateway_adapter.read(contract.operation_id, request.path, auth_context=self._auth_context(execution_context), service="udc", route="/service/udc/{target_path}")
        if getattr(gateway_result, "error", None):
            info = gateway_result.get("error") if isinstance(gateway_result.get("error"), dict) else {}
            kind = info.get("kind", "CONNECTION_ERROR")
            status = OperationStatus.BLOCKED if kind in {"MISSING_EXECUTION_CONTEXT", "CREDENTIAL_RESOLUTION_FAILED", "unavailable", "timeout", "auth", "permission", "CONNECTION_ERROR"} else OperationStatus.FAIL
            return self._record(session, self._result(intent, status, execution_context, request=dict(gateway_result.get("request") or {}), response=gateway_result.get("response"), evidence=self._evidence(contract, gateway_result), error={"kind": kind, "code": self._error_code(kind), "message": info.get("message", gateway_result.error.message)}))
        payload = gateway_result.get("response") or {}
        normalized = self._normalize(payload.get("body") if isinstance(payload, dict) else None)
        verified = bool(gateway_result.get("verified")) and self._verify(intent, normalized)
        if bool(gateway_result.get("verified")) and normalized == []:
            return self._record(session, self._result(intent, OperationStatus.FAIL, execution_context, request=dict(gateway_result.get("request") or {}), response=payload, normalized_data=normalized, verification={"gateway_response": True, "business_object_present": False, "identity_matches": False}, evidence=self._evidence(contract, gateway_result), error={"kind": ErrorKind.BUSINESS_NOT_FOUND.value, "code": ErrorKind.BUSINESS_NOT_FOUND.value, "message": "readonly collection is empty"}))
        return self._record(session, self._result(intent, OperationStatus.PASS if verified else OperationStatus.UNVERIFIED, execution_context, request=dict(gateway_result.get("request") or {}), response=payload, normalized_data=normalized, verification={"gateway_response": bool(gateway_result.get("verified")), "business_object_present": normalized is not None, "identity_matches": self._verify(intent, normalized)}, evidence=self._evidence(contract, gateway_result), unknowns=[] if verified else ["response identity cannot be verified"]))

    @staticmethod
    def _evidence(contract, gateway_result):
        return [*contract.evidence, {"source": "PlatformOperationLayer", "execution_owner": "PlatformOperationLayer", "gateway": gateway_result.get("gateway"), "route": gateway_result.get("route"), "service": gateway_result.get("service"), "live_composition": True}]

    @staticmethod
    def _with_gateway_prefix(request: OperationRequest) -> OperationRequest:
        if request.path.startswith("/service/"):
            return request
        # 两种契约路由形态（5.3.517 活体证据）：
        #   /udc/...          设计态面 → /service/udc/...
        #   udc-runtime/...   运行态面 → /service/udc/udc-runtime/...
        if request.path.startswith("/udc/"):
            return OperationRequest(request.operation_id, request.method, "/service" + request.path, request.payload, request.write, request.evidence)
        return OperationRequest(request.operation_id, request.method, "/service/udc/" + request.path, request.payload, request.write, request.evidence)

    def _request(self, intent, contract) -> OperationRequest:
        # 通用契约分派：路径/方法/参数形态全部来自 registry 契约（证据链），
        # 不再按 operation 硬编码。意图参数统一从 intent.context / intent 字段取。
        params: dict[str, Any] = dict(getattr(intent, "context", None) or {})
        path = contract.path
        # 路径占位符替换：{id}/{appId}/{entityId}/{guid}/{appName} 等按常见键名 + 契约声明参数名填充
        placeholder_names = re.findall(r"\{(\w+)\}", path)
        declared = tuple(getattr(contract, "required_inputs", ()) or ())
        values: dict[str, str] = {}
        if intent.application_id is not None:
            values.update({"appId": str(intent.application_id),
                           "appName": str(intent.application_id), "applicationId": str(intent.application_id)})
            # UDC 设计态实体面 {appId}/{id} 是 Long 数字（write-chain R1R2 LIVE 证据）；
            # application_id 常为「拼音前缀+数字」形态 → 数字形态作 {appIdNum} 并作数字回退

        if getattr(intent, "entity_id", None) is not None:
            values.update({"entityId": str(intent.entity_id), "id": str(intent.entity_id)})
        elif intent.application_id is not None and "id" not in values:
            # {id} 无显式实体值时回退 application_id（契约 required_inputs 是 application 语义，如 udc.application.get）
            values["id"] = str(intent.application_id)
        for key, val in params.items():
            values.setdefault(str(key), str(val))
        for name in dict.fromkeys(placeholder_names + [n for n in declared if n not in placeholder_names]):
            if "{" + name + "}" in path and name in values:
                v = values[name]
                # {appId}/{id} 长整型占位符：UDC 设计态面实测要求 Long 数字（字符串名被 Spring
                # NumberFormatException 拒，2026-10-09 活体）；「前缀+数字」app 名取其数字段（R1R2 证据）
                if name in ("appId", "applicationId", "id") and v == str(intent.application_id):
                    m_num = re.search(r"(\d{10,})", v)
                    if m_num:
                        v = m_num.group(1)
                path = path.replace("{" + name + "}", v)
        # 仍残留未解析占位符 = 意图参数不足，拒绝臆造（证据纪律：缺参是 UNKNOWN 不是猜）
        leftover = re.findall(r"\{(\w+)\}", path)
        if leftover:
            raise ValueError(f"missing path parameters {leftover} for {intent.operation}")
        request = OperationRequest(contract.operation_id, contract.method, path, evidence=contract.evidence)
        return self._with_gateway_prefix(request)
    @staticmethod
    def _auth_context(context):
        from .models import AuthContext
        return AuthContext(context.credential_ref, context.principal_id, context.auth_scope)

    @staticmethod
    def _normalize(body: Any):
        if not isinstance(body, dict): return None
        data = body.get("data", body)
        content = data.get("content") if isinstance(data, dict) else None
        return content

    @staticmethod
    def _verify(intent, data):
        if isinstance(data, dict):
            if intent.operation == "udc.application.get":
                m_a = re.search(r"(\d{10,})", str(intent.application_id))
                return str(data.get("id")) == str(intent.application_id) or (m_a and str(data.get("id")) == m_a.group(1))
            if intent.operation == "udc.entity.get": return str(data.get("id")) == str(intent.entity_id) and str(data.get("appId")) == str(intent.application_id)
        if intent.operation == "udc.entity.list":
            if not isinstance(data, list): return False
            known = intent.context.get("known_entity_id")
            m_a = re.search(r"(\d{10,})", str(intent.application_id))
            want = {str(intent.application_id)} | ({m_a.group(1)} if m_a else set())
            return bool(data) and all(isinstance(item, dict) and str(item.get("appId")) in want for item in data) and (known is None or any(str(item.get("id")) == str(known) for item in data))
        if intent.operation == "udc.attribute.list":
            return isinstance(data, list) and bool(data) and all(isinstance(item, dict) and str(item.get("entityId")) == str(intent.entity_id) for item in data)
        if isinstance(data, list):
            # 通用列表回读：非空 dict 列表即业务对象在场；appId 字段存在时须与意图一致
            # （identity 归一：app 名「前缀+数字」与响应纯数字 Long 视为同一，R1R2/write-chain 证据）
            if not data or not all(isinstance(item, dict) for item in data):
                return False
            def _numkey(v):
                m = re.search(r"(\d{10,})", str(v))
                return m.group(1) if m else str(v)
            want = _numkey(intent.application_id)
            app_ids = {_numkey(item.get("appId")) for item in data if item.get("appId") is not None}
            return not app_ids or app_ids == {want}
        if isinstance(data, dict): return data.get("id") is not None
        return False

    @staticmethod
    def _error_code(kind):
        return {"CREDENTIAL_RESOLUTION_FAILED":"CREDENTIAL_RESOLUTION_FAILED", "auth":ErrorKind.GATEWAY_AUTH_ERROR.value, "permission":ErrorKind.GATEWAY_AUTH_ERROR.value, "not_found":ErrorKind.GATEWAY_ROUTE_ERROR.value, "parse":ErrorKind.UDC_RESPONSE_ERROR.value, "timeout":ErrorKind.CONNECTION_ERROR.value, "unavailable":ErrorKind.CONNECTION_ERROR.value}.get(kind, ErrorKind.UDC_TRANSPORT_ERROR.value)

    @staticmethod
    def _result(intent, status, context, **kwargs): return OperationResult(intent.operation, status, intent.mode, context.session_id, context.run_id, **kwargs)
    @staticmethod
    def _record(session, result):
        if session is not None: session.append(result.to_dict())
        return result
