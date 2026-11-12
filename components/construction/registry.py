from dataclasses import dataclass
from pathlib import Path
import json

EXECUTABLE_STATUSES = {"STATIC_RULE", "STATIC_RULE_CROSS_SAMPLE_OBSERVED"}

@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    data: dict
    @property
    def status(self): return self.data.get("status", "UNKNOWN")
    @property
    def version(self): return self.data.get("schema", "UNKNOWN").rsplit(".v", 1)[-1]
    @property
    def confidence(self): return self.status
    @property
    def limitations(self): return self.data.get("caveats", self.data.get("limitations", []))
    @property
    def evidence(self): return self.data.get("evidence", [])

class ConstructionRuleRegistry:
    def __init__(self, rules_root):
        self.rules_root = Path(rules_root); self._rules = {}
    def load(self):
        candidates = [
            self.rules_root / "entity" / "naming.json", self.rules_root / "entity" / "package.json",
            self.rules_root / "generation" / "facade.json", self.rules_root / "generation" / "biz.json",
            self.rules_root / "generation" / "web.json",
        ]
        for path in candidates:
            data = json.loads(path.read_text(encoding="utf-8"))
            rule_id = data.get("schema")
            if rule_id and data.get("status") in EXECUTABLE_STATUSES:
                self._rules[rule_id] = RuleDefinition(rule_id, data)
        return self
    def get(self, rule_id): return self._rules[rule_id]
    def has(self, rule_id): return rule_id in self._rules
    def all(self): return dict(self._rules)
