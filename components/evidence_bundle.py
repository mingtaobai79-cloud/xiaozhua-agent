import json
from pathlib import Path


class EvidenceBundle:
    REQUIRED = (
        "udc_frontend_core_api_mapping.json",
        "udc_web_controller_contracts.json",
        "udc_controller_service_edges.json",
        "udc_service_persistence_audit_2.json",
        "udc_5_3_517_core_chain_audit.json",
        "udc_version_samples_manifest.json",
        "udc_version_compatibility_catalog.json",
        "udc_deployment_artifacts_audit.json",
        "udc_frontend_static_source_gap.json",
        "udc_runtime_side_effect_catalog.json",
        "udc_dynamic_contract_gap_catalog.json",
    )

    def __init__(self, root):
        self.root = Path(root)

    def validate(self):
        manifest_path = self.root / "manifest.json"
        if not manifest_path.exists():
            return {"status": "UNVERIFIED", "files_loaded": 0, "missing": ["manifest.json"]}
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return {"status": "UNVERIFIED", "files_loaded": 0, "missing": ["manifest.json"]}
        missing = [name for name in self.REQUIRED if not (self.root / name).is_file()]
        loaded = len(self.REQUIRED) - len(missing)
        result = {
            "status": "FACT" if not missing and loaded == len(self.REQUIRED) else "UNVERIFIED",
            "schema_version": manifest.get("schema_version", "unknown"),
            "application_id": manifest.get("application_id"),
            "artifact_version": manifest.get("artifact_version"),
            "verification_level": manifest.get("verification_level", "FIXTURE"),
            "files_loaded": loaded,
            "missing": missing,
            "limitations": manifest.get("limitations", []),
        }
        return result
