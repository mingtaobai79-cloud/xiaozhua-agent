"""UDC v0.2 只读能力的统一平台操作层组合。"""
from __future__ import annotations

from dataclasses import dataclass

from .models import OperationRequest


class UdcApplicationAdapter:
    def __init__(self, registry):
        self.registry = registry

    def get(self, application_id):
        contract = self.registry.get("udc.application.get")
        return OperationRequest(contract.operation_id, contract.method, contract.path.replace("{id}", str(application_id)), write=False, evidence=contract.evidence)


class UdcEntityAdapter:
    def __init__(self, registry):
        self.registry = registry

    def select_by_id(self, entity_id):
        contract = self.registry.get("udc.entity.get")
        return OperationRequest(contract.operation_id, contract.method, contract.path.replace("{id}", str(entity_id)), write=False, evidence=contract.evidence)

    def list_by_application(self, application_id):
        contract = self.registry.get("udc.entity.list")
        return OperationRequest(contract.operation_id, contract.method, contract.path.replace("{appId}", str(application_id)), write=False, evidence=contract.evidence)

    def select_all_attributes(self, entity_id):
        contract = self.registry.get("udc.entity.attributes.list")
        return OperationRequest(contract.operation_id, contract.method, contract.path.replace("{entityId}", str(entity_id)), write=False, evidence=contract.evidence)

    def list_attributes(self, entity_id):
        contract = self.registry.get("udc.attribute.list")
        return OperationRequest(contract.operation_id, contract.method, contract.path.replace("{entityId}", str(entity_id)), write=False, evidence=contract.evidence)

    def create_payload(self, payload):
        contract = self.registry.get("udc.entity.create")
        return OperationRequest(contract.operation_id, contract.method, contract.path, payload=payload, write=True, evidence=contract.evidence)


@dataclass(frozen=True)
class UdcReadAdapter:
    """把 Application 与 Entity readonly 语义聚合为一个适配器边界。"""

    application: UdcApplicationAdapter
    entity: UdcEntityAdapter


__all__ = ["UdcApplicationAdapter", "UdcEntityAdapter", "UdcReadAdapter"]
