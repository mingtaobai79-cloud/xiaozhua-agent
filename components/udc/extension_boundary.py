"""Offline customer extension boundary classification."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping

CLASSIFICATIONS = ("UDC_CORE", "CUSTOMER_EXTENSION", "SPI_DEPENDENCY", "INTEGRATION_DEPENDENCY", "UNKNOWN")
_SUFFIXES = {".py", ".java", ".kt", ".groovy", ".xml", ".js", ".ts", ".json", ".yaml", ".yml", ".txt"}

def load_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else {"value": value}

def _classification(text: str, path: Path):
    low, name = text.lower(), path.name.lower()
    if any(x in low for x in ("com.seeyon.udc.core", "udc.core", "/udc/core", "\\udc\\core")) or "core" in name:
        line = next((x.strip() for x in text.splitlines() if "core" in x.lower()), path.name)
        return "UDC_CORE", ["source:" + line], []
    if any(x in low for x in ("com.seeyon.spi", "implements extension", "extends extension", "spi.")) or "spi" in name:
        line = next((x.strip() for x in text.splitlines() if "spi" in x.lower() or "extension" in x.lower()), path.name)
        return "SPI_DEPENDENCY", ["source:" + line], []
    if any(x in low for x in ("requests", "httpx", "urllib", "resttemplate", "webclient", "dingtalk", "oauth", "integration")) or "integration" in name or "client" in name:
        line = next((x.strip() for x in text.splitlines() if any(t in x.lower() for t in ("requests", "http", "integration", "client"))), path.name)
        return "INTEGRATION_DEPENDENCY", ["source:" + line], []
    if any(x in low for x in ("com.customer", "customer.", "customer/", "customer\\", "custom", "tenant")) or any(x in name for x in ("customer", "custom", "tenant")):
        line = next((x.strip() for x in text.splitlines() if any(t in x.lower() for t in ("customer", "custom", "tenant"))), path.name)
        return "CUSTOMER_EXTENSION", ["source:" + line], []
    return "UNKNOWN", [], ["classification requires stronger source evidence"]

def build_extension_boundary(source_dir: str | Path | None, facts_json: str | Path | Mapping[str, Any] | None = None) -> dict[str, Any]:
    facts = facts_json if isinstance(facts_json, Mapping) else {}
    if facts_json and not isinstance(facts_json, Mapping):
        try: facts = load_json(facts_json)
        except (OSError, ValueError): facts = {"status": "UNVERIFIED"}
    base = {"schema_version": "phase-d-extension-boundary.v1", "items": [], "evidence_refs": [], "facts_loaded": bool(facts), "network": "disabled", "read_only": True}
    if not source_dir:
        return {**base, "status": "UNVERIFIED", "gaps": ["source directory is required; facts JSON cannot replace source evidence"]}
    root = Path(source_dir)
    if not root.is_dir():
        return {**base, "status": "UNVERIFIED", "gaps": [f"source directory does not exist: {root}"]}
    items=[]
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in _SUFFIXES):
        try: text=path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError): text=""
        cls, refs, gaps = _classification(text, path)
        items.append({"path": path.relative_to(root).as_posix(), "classification": cls, "status": "FACT" if refs else "UNVERIFIED", "evidence_refs": refs, "gaps": gaps})
    refs=[r for i in items for r in i["evidence_refs"]]
    status="FACT" if items and all(i["status"]=="FACT" for i in items) else ("PARTIALLY_VERIFIED" if refs else "UNVERIFIED")
    gaps=[f"{i['path']}: {g}" for i in items for g in i["gaps"]]
    if not items: gaps.append("no supported source files found")
    return {**base, "status": status, "items": items, "evidence_refs": refs, "gaps": gaps}
