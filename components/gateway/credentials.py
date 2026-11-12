"""仅在执行窗口内解析认证引用；不持久化原始凭据。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping

from components.platform_operations.models import AuthContext


class CredentialProvider(ABC):
    """按 credential_ref 临时解析认证材料。"""

    @abstractmethod
    def resolve(self, context: AuthContext) -> Mapping[str, str]:
        """返回只供当前请求使用的 HTTP headers。"""


class MappingCredentialProvider(CredentialProvider):
    """测试或宿主运行时注入的凭据引用映射。"""

    def __init__(self, credentials: Mapping[str, Mapping[str, str]] | None = None):
        self._credentials = {str(key): dict(value) for key, value in (credentials or {}).items()}

    def resolve(self, context: AuthContext) -> Mapping[str, str]:
        if context.credential_ref not in self._credentials:
            raise LookupError("credential reference cannot be resolved")
        return dict(self._credentials[context.credential_ref])


__all__ = ["CredentialProvider", "MappingCredentialProvider"]
