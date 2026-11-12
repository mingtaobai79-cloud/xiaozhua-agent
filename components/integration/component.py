from core.evidence import Evidence, Status, Result, report
import json
from pathlib import Path
from core.evidence import Evidence, Result

class IntegrationComponent:
    name = "integration"
    read_only = True
    def __init__(self, snapshot_path=None, provider=None):
        self.snapshot_path = Path(snapshot_path) if snapshot_path else None
        self.provider = provider
    def capabilities(self): return ["trace_http", "inspect_logs", "compare_database_snapshot"]
    def inspect(self, target):
        if self.provider is not None:
            return report(self.name, target, Status.FACT, [Evidence(Status.FACT, "provider", "read")], mode="read-only", snapshot=self.provider.read())
        if self.snapshot_path and self.snapshot_path.exists():
            return report(self.name, target, Status.FACT, [Evidence(Status.FACT, "snapshot", str(self.snapshot_path))], mode="read-only", snapshot=json.loads(self.snapshot_path.read_text(encoding="utf-8")))
        return report(self.name, target, Status.UNVERIFIED, [Evidence(Status.UNVERIFIED, "runtime", "snapshot")], mode="read-only")
