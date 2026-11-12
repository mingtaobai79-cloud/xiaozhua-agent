from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ProfileBuilder:
    """Build evidence-bounded independent profiles from local manifests."""

    def __init__(self, *, nacos_manifest: str | Path, udc_manifest: str | Path):
        self.nacos_manifest = Path(nacos_manifest)
        self.udc_manifest = Path(udc_manifest)

    @staticmethod
    def _read(path: Path) -> dict[str, Any] | None:
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None

    def build(self) -> dict[str, Any]:
        nacos = self._read(self.nacos_manifest)
        udc = self._read(self.udc_manifest)
        missing = [str(path) for path, value in ((self.nacos_manifest, nacos), (self.udc_manifest, udc)) if value is None]
        if missing:
            return {
                "schema_version": "profiles.v1",
                "status": "UNVERIFIED",
                "mode": "offline",
                "network": "disabled",
                "profiles": [],
                "unverified": [],
                "missing_inputs": missing,
                "limitations": ["Profile construction requires readable local evidence manifests."],
            }

        application_id = str(nacos.get("application_id") or udc.get("application_id") or "").strip()
        files = nacos.get("files", [])
        data_ids = [str(item.get("dataId")) for item in files if isinstance(item, dict) and item.get("dataId")]
        nacos_ref = str(self.nacos_manifest)
        udc_ref = str(self.udc_manifest)
        profiles = [
            {
                "id": "udc-platform",
                "kind": "udc_platform",
                "status": "FACT",
                "evidence_refs": [udc_ref],
                "data_ids": [item for item in data_ids if item in {"udc", "udc-app-yaml"}],
                "application_id": None,
                "relations": [],
            },
        ]
        if application_id:
            profiles.append({
                "id": application_id,
                "kind": "customer_udc_application",
                "status": "FACT",
                "evidence_refs": [nacos_ref],
                "data_ids": [item for item in data_ids if item == application_id or item == f"{application_id}-yaml"],
                "application_id": application_id,
                "relations": [],
            })
        unverified = []
        for kind in ("standard_product_application", "extension_service"):
            unverified.append(kind)
        return {
            "schema_version": "profiles.v1",
            "status": "FACT" if profiles and application_id else "UNVERIFIED",
            "mode": "offline",
            "network": "disabled",
            "profiles": profiles,
            "unverified": unverified,
            "missing_inputs": [],
            "limitations": [
                "No standard product or extension profile is created without direct evidence.",
                "Nacos manifest presence does not prove live runtime loading or deployment behavior.",
            ],
        }
