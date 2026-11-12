"""前端页面定义骨架 —— 证据驱动，字段集来自 test2 C2b LIVE 实证。

北极星落点（前端面）：需求/实体 → 页面定义骨架（JSON）。
证据边界：test2 LIVE readback（S6-LIVE-UDC-METADATA-READBACK，421 页面样本）实证
UdcMainPageMetadataDto 的 18 个字段为页面定义的可证字段集。生成骨架只填有证据的
字段，未观测字段留 null + UNVERIFIED，不臆造。

与 JavaSkeletonRenderer 同构：输入 NormalizedEntityModel，输出声明级骨架。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re

from .models import UNKNOWN, NormalizedEntityModel

# C2b LIVE 实证的页面定义字段集（UdcMainPageMetadataDto，421 样本逐字段观测）
PAGE_DEFINITION_FIELDS = (
    "appName", "caption", "clientType", "fullName", "inApp", "inParams",
    "layout", "masterEntity", "menuCode", "name", "outParameters",
    "pageType", "pageUrl", "publicAccess", "relationGroupId", "sourceType",
    "subPages", "urlType", "validate",
)


@dataclass
class PageDefinitionSkeleton:
    entity_name: str
    application_id: str
    fields: dict[str, Any]
    known_fields: list[str] = field(default_factory=list)
    unverified_fields: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "udc.construction.page-definition.v1",
            "entity_name": self.entity_name,
            "application_id": self.application_id,
            "fields": self.fields,
            "known_fields": self.known_fields,
            "unverified_fields": self.unverified_fields,
            "evidence": self.evidence,
        }


class PageDefinitionRenderer:
    """实体 → 前端页面定义骨架（最小可填面：pageUrl/masterEntity/caption）。"""

    def __init__(self, app_id: str, source_type: str = "CUSTOM", url_type: str = "PC"):
        self.app_id = app_id
        self.source_type = source_type
        self.url_type = url_type

    def render(self, model: NormalizedEntityModel) -> PageDefinitionSkeleton:
        x = model.entity_name
        known: dict[str, Any] = {
            "appName": self.app_id,
            "masterEntity": x,
            "sourceType": self.source_type,
            "urlType": self.url_type,
            "name": x,
        }
        unknown: list[str] = []
        for f in PAGE_DEFINITION_FIELDS:
            if f in known:
                continue
            if f == "pageUrl":
                # pageUrl 是 UDC 生成的运行态路由字面，离线不可证 → UNVERIFIED
                unknown.append("pageUrl")
            elif f == "caption":
                # caption 若实体模型带 caption 则填，否则 UNVERIFIED
                cap = getattr(model, "caption", UNKNOWN)
                if cap not in (None, UNKNOWN):
                    known["caption"] = cap
                else:
                    unknown.append("caption")
            elif f in ("inParams", "outParameters", "subPages"):
                unknown.append(f)  # 嵌套结构未观测到本实体 → UNVERIFIED
            else:
                unknown.append(f)
        return PageDefinitionSkeleton(
            entity_name=x,
            application_id=self.app_id,
            fields=known,
            known_fields=sorted(known),
            unverified_fields=sorted(unknown),
            evidence=["c2b-live-page-sample-fieldset", "S6-LIVE-UDC-METADATA-READBACK"],
        )


__all__ = ["PageDefinitionRenderer", "PageDefinitionSkeleton", "PAGE_DEFINITION_FIELDS"]
