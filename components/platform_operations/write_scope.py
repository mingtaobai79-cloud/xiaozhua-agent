"""写通道：显式授权范围内的写操作（默认仍 fail-closed）。

背景：xiaozhua-agent 原本在三个位置硬编码只读——
  ``layer.py:23``  ``if contract.write or method != "GET" or not effective: DENIED``
  ``policy.py``    ``MUTATING_METHODS = {POST, PUT, PATCH, DELETE}`` 一律 DENIED
  ``registry.py``  微流程写契约根本没登记

要真正搭实体和微流程，必须放开写。但**不能**简单删掉那三道门——那会让整个
仓库从"只读骨架"变成"任意写"，与既有证据纪律和安全边界冲突。

本模块的设计：**写权限是一个显式对象，不传就是没有**。

    scope = WriteScope(application_ids={APP_ID}   # 调用方自己传入，勿写死,
                       operations={"udc.entity.create", ...},
                       max_writes=10)
    layer.execute(intent, ctx, write_scope=scope)   # 不传 write_scope = 仍 DENIED

三重约束（缺一不可）：
  1. **操作白名单**：只有 ``scope.operations`` 里列出的 operation_id 可写
  2. **应用白名单**：intent.application_id 必须在 ``scope.application_ids`` 内
  3. **次数上限**：``max_writes`` 用尽后自动关闭（防失控循环）

失败语义（用户明确要求）：**失败即停，不重试**。本模块不实现任何重试逻辑；
``WriteScope`` 一旦某次写失败即置 ``aborted=True``，后续写全部拒绝。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WriteScope:
    """一次显式授权的写范围。

    ``operations`` 为空集合表示"不允许任何写"（默认行为）。
    """

    application_ids: set[str] = field(default_factory=set)
    operations: set[str] = field(default_factory=set)
    max_writes: int = 1
    reason: str = ""
    # 运行态
    used: int = 0
    aborted: bool = False
    abort_reason: str = ""

    def allows(self, operation_id: str, application_id: str) -> tuple[bool, str]:
        """返回 (是否允许, 拒绝原因)。"""
        if self.aborted:
            return False, f"写范围已中止: {self.abort_reason}（失败即停，不重试）"
        if not self.operations:
            return False, "未声明任何可写操作（默认 fail-closed）"
        if operation_id not in self.operations:
            return False, f"操作 {operation_id} 不在授权白名单内"
        if str(application_id) not in {str(x) for x in self.application_ids}:
            return False, f"应用 {application_id} 不在授权白名单内"
        if self.used >= self.max_writes:
            return False, f"写次数已用尽（{self.used}/{self.max_writes}）"
        return True, ""

    def record_success(self) -> None:
        self.used += 1

    def record_failure(self, reason: str) -> None:
        """失败即停：置 aborted，后续所有写一律拒绝。"""
        self.aborted = True
        self.abort_reason = reason

    def snapshot(self) -> dict[str, Any]:
        return {
            "application_ids": sorted(str(x) for x in self.application_ids),
            "operations": sorted(self.operations),
            "max_writes": self.max_writes,
            "used": self.used,
            "remaining": max(0, self.max_writes - self.used),
            "aborted": self.aborted,
            "abort_reason": self.abort_reason,
            "reason": self.reason,
        }


__all__ = ["WriteScope"]
