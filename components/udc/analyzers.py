import json
from pathlib import Path


class UdcAnalyzer:
    """Build a domain report solely from collected audit facts."""

    DOMAIN_SPECS = {
        "application": ("udc_web_controller_contracts.json", ("domains", "Application")),
        "entity": ("udc_web_controller_contracts.json", ("domains", "Entity")),
        "page": ("udc_web_controller_contracts.json", ("domains", "Page")),
        "microflow": ("udc_web_controller_contracts.json", ("domains", "MicroFlow")),
        "version": ("udc_version_samples_manifest.json", ("versions",)),
        "deployment": ("udc_deployment_artifacts_audit.json", ("artifact_index", "customer_frontend", "entry_count")),
    }

    def __init__(self, root):
        self.root = Path(root)

    def _load(self, name):
        path = self.root / name
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _lookup(data, path):
        value = data
        for key in path:
            if not isinstance(value, dict) or key not in value:
                return "UNVERIFIED"
            value = value[key]
        return value if isinstance(value, int) and not isinstance(value, bool) else (len(value) if path[-1] == "versions" and isinstance(value, list) else "UNVERIFIED")

    def analyze(self, target):
        loaded = {name: self._load(name) for name, _ in self.DOMAIN_SPECS.values()}
        frontend = self._load("udc_frontend_core_api_mapping.json")
        dynamic = self._load("udc_dynamic_contract_gap_catalog.json")
        static_source = self._load("udc_frontend_static_source_gap.json")
        domains = {}
        for domain, (filename, path) in self.DOMAIN_SPECS.items():
            count = self._lookup(loaded[filename], path)
            domains[domain] = {
                "status": "FACT" if count != "UNVERIFIED" else "UNVERIFIED",
                "count": count,
                "evidence_file": filename,
                **({"frontend_operations": frontend.get("counts", {}).get("unique_calls", "UNVERIFIED")} if domain == "page" else {}),
                **({"backend_operations": len(dynamic.get("backend_operations", [])) if isinstance(dynamic.get("backend_operations"), list) else "UNVERIFIED"} if domain == "microflow" else {}),
            }
        statuses = [item["status"] for item in domains.values()]
        unverified = [name for name, item in domains.items() if item["status"] == "UNVERIFIED"]
        if dynamic.get("unverified_dto_gaps") or dynamic.get("unverified"):
            unverified.append("dynamic_contract_fields")
        if static_source:
            unverified.append("frontend_static_source")
        return {
            "status": "FACT" if all(status == "FACT" for status in statuses) else "UNVERIFIED",
            "target": target,
            "domains": domains,
            "unverified": sorted(set(unverified)),
        }
