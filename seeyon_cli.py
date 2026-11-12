"""Unified, offline and read-only Seeyon Agent CLI."""
import argparse
import json
from pathlib import Path

from components.integration import IntegrationComponent
from components.runtime import RuntimeComponent
from components.udc.component import UdcComponent, UdcRequest
from core.providers import JSONProbeProvider
from providers.registry import default_provider_registry
from components.probe_summary import DEFAULT_RUNTIME, DEFAULT_HTTP

DEFAULT_GATEWAY_URL = "https://lowcode-test2.example.com"


class _FileCredentialProvider:
    """从本地 JSON 文件按 credential_ref 读取认证 headers；只在单次请求生命周期内使用。"""

    def __init__(self, path):
        self._credentials = json.loads(Path(path).read_text(encoding="utf-8-sig"))

    def resolve(self, context):
        ref = context.credential_ref
        if ref not in self._credentials:
            raise LookupError("credential reference cannot be resolved")
        return dict(self._credentials[ref])


def build_operation_layer(gateway_adapter, registry=None, credential_provider=None):
    """组装统一 PlatformOperationLayer（human-path integration 的唯一入口）。"""
    from components.platform_operations import (
        PlatformOperationLayer, UdcApplicationAdapter, UdcEntityAdapter, UdcOperationRegistry, UdcReadAdapter,
    )

    resolved_registry = registry or UdcOperationRegistry.default()
    return PlatformOperationLayer(
        resolved_registry,
        UdcReadAdapter(
            application=UdcApplicationAdapter(resolved_registry),
            entity=UdcEntityAdapter(resolved_registry),
        ),
        gateway_adapter,
    )


def _run_op_execute(args):
    """CLI -> PlatformOperationLayer 的 human-path。默认离线，真实网络必须显式开启。"""
    from components.gateway import GatewayAdapter, GatewayReadonlyClient
    from components.platform_operations import ExecutionContext
    from components.platform_operations.evidence import OperationEvidenceStore
    from components.platform_operations.models import OperationIntent

    allow_network = bool(args.allow_network)
    credential_provider = None
    if args.credential_file:
        try:
            credential_provider = _FileCredentialProvider(args.credential_file)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            _json({
                "operation": args.operation, "status": "BLOCKED", "mode": "readonly",
                "network": "disabled" if not allow_network else "explicit",
                "error": {"kind": "CREDENTIAL_RESOLUTION_FAILED", "code": "CREDENTIAL_RESOLUTION_FAILED", "message": f"credential file unavailable: {exc}"},
            })
            return 2
    client = GatewayReadonlyClient(
        base_url=args.gateway_url, allow_network=allow_network,
        timeout=args.timeout,
    )
    gateway = GatewayAdapter(client, gateway_name=args.gateway_url, credential_provider=credential_provider)
    layer = build_operation_layer(gateway)
    context = ExecutionContext(
        session_id="cli-session", run_id="cli-run",
        principal_id=args.principal, credential_ref=args.credential_ref,
        auth_scope=(f"{args.application_id}:readonly",),
    )
    try:
        intent = OperationIntent(
            args.operation, args.application_id,
            entity_id=args.entity_id, entity_name=args.entity_name,
        )
        result = layer.execute(intent, context)
    except ValueError as exc:
        _json({
            "operation": args.operation, "status": "UNVERIFIED", "mode": "readonly",
            "network": "disabled" if not allow_network else "explicit",
            "error": {"kind": "INTENT_INVALID", "code": "INTENT_INVALID", "message": str(exc)},
        })
        return 2
    payload = result.to_dict()
    payload["network"] = "disabled" if not allow_network else "explicit"
    payload["gateway_url"] = args.gateway_url
    if args.evidence_out:
        OperationEvidenceStore(args.evidence_out).save(result)
    _json(payload)
    return 0 if payload["status"] == "PASS" else 2


def _json(value):
    # Every CLI response carries the same explicit offline boundary.
    if isinstance(value, dict):
        value = {"network": "disabled", **value}
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _add_target(parser):
    parser.add_argument("--target", required=True, help="logical application, pod, or integration target")


def build_parser():
    parser = argparse.ArgumentParser(prog="seeyon", description="Seeyon Agent offline read-only reports")
    sub = parser.add_subparsers(dest="command", required=True)
    nem = sub.add_parser("nacos-evidence-manifest", help="build secret-safe manifest from a local Nacos snapshot")
    nem.add_argument("--snapshot-dir", required=True)
    nem.add_argument("--application-id", required=True)
    nem.add_argument("--tenant", required=True)
    nem.add_argument("--group", required=True)
    va = sub.add_parser("version-audit", help="audit local UDC artifact/version/SHA-256 evidence")
    va.add_argument("--audit-dir", required=True)
    va.add_argument("--version", action="append", dest="versions", help="version to audit; repeatable (default: all declared versions)")
    inventory = sub.add_parser("artifact-inventory", help="inventory local Maven JAR/POM artifacts without network access")
    inventory.add_argument("--root", "--repo", dest="root", default=r"<PATH>")
    inventory.add_argument("--keyword", action="append", dest="keywords", help="case-insensitive keyword filter; repeatable (default: udc/lowcode/seeyon)")
    inventory.add_argument("--output", default=None, help="manifest JSON output path (default: <root>/artifact-inventory.manifest.json)")
    report = sub.add_parser("udc-report", help="report UDC evidence catalog")
    report.add_argument("--audit-dir", required=True); _add_target(report)
    analyze = sub.add_parser("udc-analyze", help="analyze UDC domains")
    analyze.add_argument("--audit-dir", required=True); _add_target(analyze)
    runtime = sub.add_parser("runtime-report", help="report a runtime snapshot")
    runtime.add_argument("--snapshot", required=True); _add_target(runtime)
    integration = sub.add_parser("integration-report", help="report an integration snapshot")
    integration.add_argument("--snapshot", required=True); _add_target(integration)
    summary = sub.add_parser("audit-summary", help="aggregate offline audit reports")
    probe = sub.add_parser("probe-summary", help="aggregate read-only runtime and HTTP probes")
    ledger = sub.add_parser("evidence-ledger", help="build offline evidence ledger")
    dynamic = sub.add_parser("dynamic-evidence", help="project read-only provider results into ledger and path matrix")
    bundle = sub.add_parser("audit-bundle", help="assemble a unified offline audit bundle")
    diagnostic = sub.add_parser("diagnostic-report", help="aggregate a cross-component offline diagnostic conclusion")
    for name in ("evidence-context", "dynamic-evidence", "path-matrix", "impact-graph", "version-audit"):
        diagnostic.add_argument("--" + name, required=True, dest=name.replace("-", "_"))
    for name in ("version-audit", "runtime", "http", "path-matrix", "impact-graph", "evidence-context"):
        bundle.add_argument("--" + name, required=True, dest=name.replace("-", "_"))
    for name in ("http", "k8s", "nacos", "mysql", "redis"):
        dynamic.add_argument(f"--{name}", required=False)
    dynamic.add_argument("--environment")
    dynamic.add_argument("--namespace")
    dynamic.add_argument("--application-id")
    dynamic.add_argument("--trace-id")
    dynamic.add_argument("--time-window")
    version_impact = sub.add_parser("version-impact-summary", help="associate version audit with path matrix and impact graph")
    version_impact.add_argument("--version-audit", required=True)
    version_impact.add_argument("--path-matrix", required=True)
    version_impact.add_argument("--impact-graph", required=True)
    matrix = sub.add_parser("udc-path-matrix", help="build offline UDC critical-path matrix")
    impact = sub.add_parser("impact-graph", help="build offline Phase E impact graph")
    impact.add_argument("--path-matrix", required=True)
    profile_build = sub.add_parser("profile-build", help="build independent profiles from local evidence manifests")
    profile_build.add_argument("--nacos-manifest", required=True)
    profile_build.add_argument("--udc-manifest", required=True)
    profile_graph = sub.add_parser("profile-graph", help="build offline Profile Evidence Graph (conflicts/gaps/status)")
    profile_graph.add_argument("--profiles-json", required=True)
    extension = sub.add_parser("extension-boundary", help="classify offline customer extension boundary")
    extension.add_argument("--source-dir", default=None)
    extension.add_argument("--facts-json", required=True)
    matrix.add_argument("--udc-json", required=True)
    matrix.add_argument("--runtime", required=True)
    matrix.add_argument("--http", required=True)
    ledger.add_argument("--udc-json", required=True)
    ledger.add_argument("--runtime", required=True)
    ledger.add_argument("--http", required=True)
    probe.add_argument("--runtime", "--runtime-probe", dest="runtime", default=None)
    probe.add_argument("--http", "--http-probe", dest="http", default=None)
    summary.add_argument("--audit-dir", required=True)
    summary.add_argument("--udc-json", required=True)
    sub.add_parser("capabilities", help="list available read-only capabilities")
    sub.add_parser("module-catalog", help="list independent module boundaries and evidence-gated relations")
    test_report = sub.add_parser("test-report", help="report local pytest acceptance evidence")
    test_report.add_argument("--result", help="existing pytest output file; run pytest when omitted")
    sub.add_parser("provider-capabilities", help="list provider capabilities and safety boundaries")
    dry_run = sub.add_parser("dry-run", help="generate an offline execution plan without performing writes")
    dry_run.add_argument("--action", required=True, choices=("create-entity", "add-field", "publish", "deploy"))
    _add_target(dry_run)
    dry_run.add_argument("--environment", required=True, help="logical environment name")
    execute = sub.add_parser("udc-execute", help="attempt a UDC action; writes are denied")
    execute.add_argument("action"); execute.add_argument("target"); execute.add_argument("--audit-dir", required=True)
    op = sub.add_parser("op-execute", help="run a readonly UDC operation through PlatformOperationLayer (offline by default)")
    op.add_argument("--operation", required=True, help="operation id, e.g. udc.application.get")
    op.add_argument("--application-id", required=True)
    op.add_argument("--entity-id", default=None)
    op.add_argument("--entity-name", default=None)
    op.add_argument("--gateway-url", default=DEFAULT_GATEWAY_URL)
    op.add_argument("--credential-file", default=None, help="JSON file mapping credential_ref -> HTTP headers")
    op.add_argument("--credential-ref", default="cli-default")
    op.add_argument("--principal", default="cli")
    op.add_argument("--timeout", type=float, default=15.0)
    op.add_argument("--evidence-out", default=None, help="persist the redacted OperationResult JSON")
    op.add_argument("--allow-network", action="store_true", help="explicitly enable live GET (default: network disabled)")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "artifact-inventory":
        from components.artifact_inventory import write_manifest
        output = args.output or str(Path(args.root) / "artifact-inventory.manifest.json")
        result = write_manifest(args.root, output, args.keywords)
        _json(result)
        return 0
    if args.command == "op-execute":
        return _run_op_execute(args)
    if args.command == "nacos-evidence-manifest":
        from providers.nacos_evidence_manifest import build_manifest
        _json(build_manifest(args.snapshot_dir, application_id=args.application_id, tenant=args.tenant, group=args.group))
        return 0
    if args.command == "diagnostic-report":
        from components.diagnostic_report import build_diagnostic_report, load_json
        result = build_diagnostic_report(
            evidence_context=load_json(args.evidence_context),
            dynamic_evidence=load_json(args.dynamic_evidence),
            path_matrix=load_json(args.path_matrix),
            impact_graph=load_json(args.impact_graph),
            version_audit=load_json(args.version_audit),
        )
        _json(result)
        return 0 if result["status"] == "FACT" else 2
    if args.command == "audit-bundle":
        from components.audit_bundle import build_audit_bundle
        result = build_audit_bundle({"version_audit": args.version_audit, "runtime": args.runtime, "http": args.http, "path_matrix": args.path_matrix, "impact_graph": args.impact_graph, "evidence_context": args.evidence_context})
        _json(result)
        return 0 if result["status"] != "UNVERIFIED" else 2
    if args.command == "dynamic-evidence":
        from components.dynamic_evidence import build_dynamic_evidence_report
        values = {name: getattr(args, name) for name in ("http", "k8s", "nacos", "mysql", "redis")}
        time_window = json.loads(args.time_window) if args.time_window else None
        values["evidence_context"] = {"environment": args.environment, "namespace": args.namespace, "application_id": args.application_id, "trace_id": args.trace_id, "time_window": time_window}
        _json(build_dynamic_evidence_report(values))
        return 0
    if args.command == "version-audit":
        from components.udc.version_audit import audit_versions
        result = audit_versions(args.audit_dir, args.versions)
        _json(result)
        return 0
    if args.command == "dry-run":
        from components.dry_run import build_dry_run
        result = build_dry_run(args.target, args.environment, action=args.action, evidence={"status": "FACT", "refs": ["cli-input"]})
        result["executed"] = False
        result["confirmations_required"] = [
            "explicit operator confirmation is required before any execution",
            f"confirm target environment: {args.environment}",
        ]
        _json(result)
        return 0
    if args.command == "version-impact-summary":
        from components.version_impact_summary import build_version_impact_summary, load_json
        try:
            _json(build_version_impact_summary(load_json(args.version_audit), load_json(args.path_matrix), load_json(args.impact_graph)))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            _json({
                "status": "UNAVAILABLE",
                "mode": "offline",
                "network": "disabled",
                "read_only": True,
                "missing_inputs": [args.version_audit, args.path_matrix, args.impact_graph],
                "error": "version-impact input could not be loaded",
            })
            return 2
        return 0
    if args.command == "impact-graph":
        from components.impact_graph import build_impact_graph, load_json
        _matrix_path = Path(args.path_matrix)
        if not _matrix_path.is_file():
            _json({
                "mode": "offline",
                "network": "disabled",
                "read_only": True,
                "missing_inputs": [args.path_matrix],
                "error": "impact-graph input could not be loaded",
            })
            return 2
        result = build_impact_graph(load_json(args.path_matrix))
        _json(result)
        return 0
    if args.command == "profile-build":
        from components.profiles.builder import ProfileBuilder
        result = ProfileBuilder(nacos_manifest=args.nacos_manifest, udc_manifest=args.udc_manifest).build()
        _json(result)
        return 0 if result["status"] == "FACT" else 2
    if args.command == "profile-graph":
        from components.profile_graph import build_profile_graph, load_json
        try:
            result = build_profile_graph(load_json(args.profiles_json))
        except (OSError, ValueError, json.JSONDecodeError):
            _json({
                "status": "UNVERIFIED",
                "mode": "offline",
                "error": "profile input could not be loaded",
            })
            return 2
        _json(result)
        return 2 if result["status"] == "CONFLICT" else 0
    if args.command == "extension-boundary":
        from components.udc.extension_boundary import build_extension_boundary
        result = build_extension_boundary(args.source_dir, args.facts_json)
        _json(result)
        return 2 if result["status"] == "UNVERIFIED" else 0
    if args.command == "udc-path-matrix":
        from components.udc.path_matrix import build_path_matrix, load_json
        try:
            result = build_path_matrix(load_json(args.udc_json), load_json(args.runtime), load_json(args.http))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            _json({
                "status": "UNVERIFIED",
                "mode": "offline",
                "network": "disabled",
                "read_only": True,
                "missing_inputs": [args.udc_json, args.runtime, args.http],
                "error": "udc-path-matrix input could not be loaded",
            })
            return 2
        _json(result)
        return 0
    if args.command == "evidence-ledger":
        from components.evidence_ledger import build_evidence_ledger
        result = build_evidence_ledger(udc_json=args.udc_json, runtime=json.loads(Path(args.runtime).read_text(encoding="utf-8-sig")), http=json.loads(Path(args.http).read_text(encoding="utf-8-sig")))
        _json(result)
        return 0 if result["status"] != "UNVERIFIED" else 2
    if args.command == "probe-summary":
        from components.probe_summary import build_probe_summary
        result = build_probe_summary(provider=JSONProbeProvider(args.runtime or DEFAULT_RUNTIME, args.http or DEFAULT_HTTP)) if args.runtime or args.http else build_probe_summary()
        _json(result)
        return 0 if result["status"] != "UNVERIFIED" else 2
    if args.command == "audit-summary":
        from components.audit_summary import build_summary
        result = build_summary(args.audit_dir, args.udc_json)
        _json(result)
        return 2 if result["status"] == "UNVERIFIED" else 0
    if args.command == "provider-capabilities":
        _json(default_provider_registry().capabilities())
        return 0
    if args.command == "test-report":
        from components.test_report import build_test_report
        result = build_test_report(args.result)
        _json(result)
        return 0
    if args.command == "module-catalog":
        from components.module_catalog import build_module_catalog
        _json(build_module_catalog())
        return 0
    if args.command == "capabilities":
        components = {
            "udc": {"read_only": True, "capabilities": UdcComponent().capabilities()},
            "runtime": {"read_only": True, "capabilities": RuntimeComponent().capabilities()},
            "integration": {"read_only": True, "capabilities": IntegrationComponent().capabilities()},
        }
        _json({"mode": "read-only", "network": "disabled", "components": components})
        return 0
    if args.command == "runtime-report":
        _json(RuntimeComponent(snapshot_path=args.snapshot).inspect(args.target)); return 0
    if args.command == "integration-report":
        _json(IntegrationComponent(snapshot_path=args.snapshot).inspect(args.target)); return 0
    component = UdcComponent(audit_dir=args.audit_dir)
    if args.command == "udc-report":
        _json(component.report(args.target)); return 0
    if args.command == "udc-analyze":
        _json(component.analyze(args.target)); return 0
    result = component.execute(UdcRequest(args.action, args.target))
    _json(result)
    return 2 if result.get("status") == "DENIED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
