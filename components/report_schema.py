"""Machine-readable contracts for offline read-only fact reports."""

SCHEMA_VERSION = "1.0"
REQUIRED_FIELDS = ("schema_version", "scope", "limitations")

def validate_report_schema(report):
    """Validate the stable metadata required by fact-report consumers."""
    missing = [field for field in REQUIRED_FIELDS if field not in report]
    if not isinstance(report.get("scope"), dict):
        missing.append("scope")
    if not isinstance(report.get("limitations"), list):
        missing.append("limitations")
    if missing:
        return {"valid": False, "status": "UNVERIFIED", "missing": sorted(set(missing))}
    return {"valid": True, "status": report.get("status", "UNVERIFIED"), "missing": []}

def report_metadata(*, scope, limitations):
    return {"schema_version": SCHEMA_VERSION, "scope": scope, "limitations": list(limitations)}

def enforce_report_schema(report):
    """Return report unchanged when valid, otherwise fail closed."""
    validation = validate_report_schema(report)
    if validation["valid"]:
        return report
    result = dict(report)
    result["status"] = "UNVERIFIED"
    result["schema_errors"] = validation["missing"]
    return result
