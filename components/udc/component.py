from core.evidence import Evidence, Status, Result, report
import json
from dataclasses import dataclass
from pathlib import Path
from .catalog import UdcEvidenceCatalog
from .analyzers import UdcAnalyzer
from core.evidence import Evidence, Result

@dataclass(frozen=True)
class UdcRequest:
    action: str
    target: str

class UdcComponent:
    name = "udc"
    read_only = True
    def __init__(self, audit_path=None, audit_dir=None):
        self.audit_path = Path(audit_path) if audit_path else None
        self.audit_dir = Path(audit_dir) if audit_dir else None
    def capabilities(self):
        return ["inspect_application", "inspect_entity", "inspect_field", "inspect_page", "inspect_page_schema", "inspect_microflow", "inspect_dataflow", "inspect_version", "inspect_generated_app", "inspect_runtime_metadata", "inspect_deployment", "dry_run"]
    def analyze(self, target):
        if self.audit_dir is None:
            return report(self.name, target, Status.UNVERIFIED, [Evidence(Status.UNVERIFIED, "udc", "audit_directory")], domains={})
        return UdcAnalyzer(self.audit_dir).analyze(target)

    def domain_report(self, target):
        if self.audit_dir is None:
            return report(self.name, target, Status.UNVERIFIED, [Evidence(Status.UNVERIFIED, "udc", "audit_directory")], domains={}, unverified=["audit_directory"])
        report = UdcEvidenceCatalog(self.audit_dir).report()
        return {
            "status": report["status"], "target": target,
            "domains": {
                "frontend": {"status": report["domains"].get("frontend_contracts", {}).get("status", "UNVERIFIED"), "unique_calls": report["counts"].get("frontend_contracts", 0)},
                "backend": {"status": report["domains"].get("backend_contracts", {}).get("status", "UNVERIFIED"), "endpoints": report["counts"].get("backend_contracts", 0)},
                "versions": {"status": report["domains"].get("versions", {}).get("status", "UNVERIFIED"), "count": report["facts"].get("sampled_versions", 0)},
                "persistence": report["domains"].get("persistence", {"status": "UNVERIFIED"}),
                "deployment": report["domains"].get("deployment", {"status": "UNVERIFIED"}),
            },
            "facts": report["facts"], "unverified": report["unverified"],
        }

    def report(self, target):
        if self.audit_dir is None:
            return report(self.name, target, Status.UNVERIFIED, [Evidence(Status.UNVERIFIED, "udc", "audit_directory")], mode="read-only")
        base = UdcEvidenceCatalog(self.audit_dir).report()
        base["analysis"] = UdcAnalyzer(self.audit_dir).analyze(target)
        return Result(component=self.name, target=target, status=base.get("status", Status.UNVERIFIED), evidence=[Evidence(base.get("status", Status.UNVERIFIED), "udc-catalog", str(self.audit_dir))], **{k: v for k, v in base.items() if k != "status"})
    def inspect_application(self, target):
        if self.audit_path and self.audit_path.exists():
            data=json.loads(self.audit_path.read_text(encoding="utf-8"))
            return Result(component=self.name, target=target, status=Status.FACT, evidence=[Evidence(Status.FACT, "audit", str(self.audit_path))], mode="read-only", **data)
        if self.audit_dir and self.audit_dir.exists():
            return report(self.name, target, Status.FACT, [Evidence(Status.FACT, "audit-directory", str(self.audit_dir))], mode="read-only", artifact_version="5.3.517", evidence_files=len(list(self.audit_dir.glob("udc_*.json"))))
        return report(self.name, target, Status.UNVERIFIED, [Evidence(Status.UNVERIFIED, "udc", "audit")], mode="read-only")
    def execute(self, request):
        if request.action not in self.capabilities():
            return report(self.name, request.target, Status.DENIED, [Evidence(Status.DENIED, "policy", request.action)], action=request.action)
        if request.action == "inspect_application":
            return self.report(request.target) if self.audit_dir else self.inspect_application(request.target)
        if request.action in {"inspect_field", "inspect_page_schema", "inspect_dataflow"}:
            gap = "dynamic_contract_fields"
            return report(
                self.name, request.target, Status.UNVERIFIED,
                [Evidence(Status.UNVERIFIED, "udc-dynamic-contract", str(self.audit_dir / "udc_dynamic_contract_gap_catalog.json") if self.audit_dir else gap)],
                action=request.action, domain=request.action.removeprefix("inspect_"), mode="read-only",
                unverified=[gap], limitations=["DTO/schema fields remain incomplete in the bounded static evidence."],
            )
        if request.action == "inspect_version":
            analysis = self.analyze(request.target)
            detail = dict(analysis.get("domains", {}).get("version", {}))
            status = detail.pop("status", Status.UNVERIFIED)
            return report(self.name, request.target, status, [Evidence(status, "udc-version", str(self.audit_dir / detail.get("evidence_file", "")) if self.audit_dir else "version")], action=request.action, domain="version", mode="read-only", **detail)
        if request.action in {"inspect_generated_app", "inspect_deployment"}:
            analysis = self.analyze(request.target)
            detail = dict(analysis.get("domains", {}).get("deployment", {}))
            status = detail.pop("status", Status.UNVERIFIED)
            return report(self.name, request.target, status, [Evidence(status, "udc-deployment", str(self.audit_dir / detail.get("evidence_file", "")) if self.audit_dir else "deployment")], action=request.action, domain="generated_app" if request.action == "inspect_generated_app" else "deployment", mode="read-only", unverified=["frontend_static_source"], limitations=["Static artifact evidence does not prove OSS/Ingress byte provenance."], **detail)
        if request.action == "inspect_runtime_metadata":
            return report(self.name, request.target, Status.UNVERIFIED, [Evidence(Status.UNVERIFIED, "udc-runtime", str(self.audit_dir / "udc_runtime_side_effect_catalog.json") if self.audit_dir else "runtime_metadata")], action=request.action, domain="runtime_metadata", mode="read-only", unverified=["runtime_metadata_live_state"], limitations=["No current live runtime metadata readback is included in the offline fixture."])
        if request.action in {"inspect_entity", "inspect_page", "inspect_microflow"}:
            analysis = self.analyze(request.target)
            domain = request.action.removeprefix("inspect_")
            detail = dict(analysis.get("domains", {}).get(domain, {}))
            status = detail.pop("status", Status.UNVERIFIED)
            return report(
                self.name, request.target, status,
                [Evidence(status, "udc-domain", str(self.audit_dir / detail.get("evidence_file", "")) if self.audit_dir else domain)],
                action=request.action, domain=domain, mode="read-only",
                unverified=[gap for gap in analysis.get("unverified", []) if gap == "dynamic_contract_fields" and domain == "microflow"],
                **detail,
            )
        if request.action == "dry_run":
            from .models import ApplicationSpec
            from .planner import UdcPlanner
            plan = UdcPlanner().plan(ApplicationSpec(name=request.target, caption=request.target))
            return {**plan, "component": self.name, "target": request.target, "status": "UNVERIFIED", "executed": False, "writes_performed": False, "evidence": [], "verification_level": "STATIC", "facts": {}, "unverified": ["execution_not_authorized"], "conflicts": [], "limitations": ["Planning only; no write operation was executed."], "next_actions": []}
        return report(self.name, request.target, Status.UNVERIFIED, [Evidence(Status.UNVERIFIED, "udc", request.action)], action=request.action, mode="read-only")
    def inspect(self, target):
        result = self.inspect_application(target)
        if "evidence" not in result:
            result = Result(component=self.name, target=target, status=result.get("status", "UNVERIFIED"), evidence=[Evidence(result.get("status", "UNVERIFIED"), "component", self.name)], **{k: v for k, v in result.items() if k not in {"component", "target", "status"}})
        return result
