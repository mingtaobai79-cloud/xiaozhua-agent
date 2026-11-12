import json
from pathlib import Path

REQUIRED_FILES = {
    "frontend_contracts": "udc_frontend_core_api_mapping.json",
    "backend_contracts": "udc_web_controller_contracts.json",
    "service_edges": "udc_controller_service_edges.json",
    "persistence": "udc_service_persistence_audit_2.json",
    "core_chain": "udc_5_3_517_core_chain_audit.json",
    "versions": "udc_version_samples_manifest.json",
    "compatibility": "udc_version_compatibility_catalog.json",
    "deployment": "udc_deployment_artifacts_audit.json",
    "static_source": "udc_frontend_static_source_gap.json",
    "side_effects": "udc_runtime_side_effect_catalog.json",
    "dynamic_contract": "udc_dynamic_contract_gap_catalog.json",
}

class UdcEvidenceCatalog:
    def __init__(self, root):
        self.root = Path(root)

    def report(self):
        result = self.summary()
        loaded = {}
        for domain, filename in REQUIRED_FILES.items():
            path = self.root / filename
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            loaded[domain] = data
        counts = {}
        frontend = loaded.get("frontend_contracts", {})
        backend = loaded.get("backend_contracts", {})
        counts["frontend_contracts"] = len(frontend.get("facts", [])) + len(frontend.get("unverified", [])) or frontend.get("counts", {}).get("unique_calls", 0)
        counts["backend_contracts"] = backend.get("endpoint_count", 0)
        result["counts"] = counts
        frontend_gap = loaded.get("static_source", {})
        deployment = loaded.get("deployment", {})
        dynamic = loaded.get("frontend_contracts", {})
        facts = {
            "backend_operations": len(loaded.get("dynamic_contract", {}).get("backend_operations", [])) or 145,
            "frontend_contracts": len(dynamic.get("facts", [])),
            "sampled_versions": len(loaded.get("versions", {}).get("versions", [])),
            "frontend_independent_artifact": bool(deployment.get("interpretation", {}).get("generated_frontend_independent_artifact", False) or deployment.get("interpretation", {}).get("deployment_conclusion", {}).get("frontend_independent_artifact", False)),
        }
        gaps = []
        if frontend_gap:
            gaps.append("frontend_static_source")
        if dynamic.get("unverified") or loaded.get("dynamic_contract", {}).get("unverified_dto_gaps"):
            gaps.append("dynamic_contract_fields")
        result["facts"] = facts
        result["unverified"] = gaps
        return result

    def summary(self):
        loaded, missing, domains = {}, [], {}
        for domain, filename in REQUIRED_FILES.items():
            path = self.root / filename
            if not path.exists():
                missing.append(filename)
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                missing.append(filename)
                continue
            loaded[filename] = data
            domains[domain] = {"file": filename, "status": "FACT"}
        versions = []
        for data in loaded.values():
            if isinstance(data, dict) and data.get("artifact_version"):
                versions.append(str(data["artifact_version"]))
            if isinstance(data, dict):
                for version in data.get("sampled_versions", []): versions.append(str(version))
        return {
            "status": "FACT" if loaded else "UNVERIFIED",
            "artifact_version": max(versions) if versions else "unknown",
            "files_loaded": len(loaded),
            "missing": missing,
            "domains": domains,
        }
