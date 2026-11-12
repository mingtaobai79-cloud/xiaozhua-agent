"""Offline aggregation for read-only runtime and HTTP probes."""
from pathlib import Path

from core.providers import JSONProbeProvider, ReadOnlyProbeProvider
from .report_schema import enforce_report_schema, report_metadata

DEFAULT_FIXTURE = Path(__file__).parents[1] / "fixtures" / "default_probe_inputs.json"
DEFAULT_RUNTIME = DEFAULT_FIXTURE
DEFAULT_HTTP = DEFAULT_FIXTURE


def _entry(label, value, source, **extra):
    item = {"label": label, "source": source}
    if isinstance(value, dict): item.update(value)
    else: item["value"] = value
    item.update(extra)
    return item


def build_probe_summary(runtime_path=DEFAULT_RUNTIME, http_path=DEFAULT_HTTP, provider=None, http_provider=None, http_requests=None):
    if provider is None:
        provider = JSONProbeProvider(runtime_path, http_path)
    facts, unverified, blocked = [], [], []
    sources = getattr(provider, "sources", {"runtime": str(runtime_path), "http": str(http_path)})
    runtime = http = None
    is_default_bundle = Path(runtime_path) == DEFAULT_FIXTURE and Path(http_path) == DEFAULT_FIXTURE
    for kind, read in (("runtime", provider.read_runtime), ("http", provider.read_http)):
        bucket = unverified
        source = sources[kind]
        try:
            data = read()
        except (OSError, UnicodeError, ValueError) as exc:
            bucket.append(_entry(kind, None, source, reason=("input file is missing" if isinstance(exc, FileNotFoundError) else f"invalid JSON: {exc}")))
            continue
        if getattr(data, "error", None) is not None:
            bucket.append(_entry(kind, None, source, error_kind=data.error.kind, reason=data.error.message))
            continue
        if kind == "runtime":
            runtime = data.get("runtime.json", data) if is_default_bundle else data
        else:
            http = data.get("http.json", data) if is_default_bundle else data
    if runtime is not None:
        resources = runtime.get("resources", {})
        for name, value in resources.items(): facts.append(_entry(f"runtime.resources.{name}", value, sources["runtime"]))
        live = runtime.get("live_probe", {})
        if str(live.get("status", "")).upper() == "BLOCKED": blocked.append(_entry("runtime.live_probe", live, sources["runtime"]))
        for name, value in runtime.get("workload_inventory", {}).items():
            if str(value.get("status", "")).upper() in {"NOT_INDEPENDENTLY_VERIFIED", "UNVERIFIED"}: unverified.append(_entry(f"runtime.workload_inventory.{name}", value, sources["runtime"]))
        for name, value in runtime.get("conclusion", {}).items():
            cls = str(value).upper()
            if cls in {"PASS", "FACT"}: facts.append(_entry(f"runtime.conclusion.{name}", value, sources["runtime"]))
            elif cls == "BLOCKED": blocked.append(_entry(f"runtime.conclusion.{name}", value, sources["runtime"]))
            elif cls in {"FAIL", "UNVERIFIED", "NOT_INDEPENDENTLY_VERIFIED"}: unverified.append(_entry(f"runtime.conclusion.{name}", value, sources["runtime"]))
    if http_provider is not None:
        requests = http_requests or []
        http = {"probes": [http_provider.request(method, url) for method, url in requests]}
        sources["http"] = getattr(http_provider, "fixture_path", sources["http"]).__str__()
    if http is not None:
        for i, probe in enumerate(http.get("probes", [])):
            cls = str(probe.get("classification", "")).upper()
            item = _entry(probe.get("label", f"{probe.get('method', '')} {probe.get('url', '')}".strip() or f"probe-{i}"), probe, sources["http"])
            if cls == "BLOCKED": blocked.append(item)
            elif cls in {"PASS", "FACT"} and "unverified" not in str(probe.get("note", "")).lower(): facts.append(item)
            else: unverified.append(item)
    status = "PARTIALLY_VERIFIED" if facts and (unverified or blocked) else ("FACT" if facts else ("PARTIALLY_VERIFIED" if blocked else "UNVERIFIED"))
    return enforce_report_schema({**report_metadata(scope={"read_only": True, "areas": ["runtime", "http"]}, limitations=["does not connect to live systems"]), "status": status, "facts": facts, "unverified": unverified, "blocked": blocked, "sources": sources})
