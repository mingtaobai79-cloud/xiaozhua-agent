"""OperationResult evidence 的最小 JSON 持久化边界。"""
from __future__ import annotations

import json
from pathlib import Path

from .models import OperationResult


class OperationEvidenceStore:
    """保存和回读已脱敏的 OperationResult；不接触 CredentialProvider。"""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, result: OperationResult) -> None:
        payload = result.to_dict()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))


__all__ = ["OperationEvidenceStore"]
