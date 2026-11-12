"""Offline inventory of local Maven artifacts."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Iterable

DEFAULT_KEYWORDS = ("udc", "lowcode", "xiaozhua")

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _class_count(path: Path) -> int:
    try:
        with zipfile.ZipFile(path) as archive:
            return sum(1 for name in archive.namelist() if name.endswith(".class") and not name.endswith("/") )
    except (OSError, zipfile.BadZipFile):
        return 0

def _coordinate(jar: Path, root: Path):
    rel = jar.relative_to(root)
    parts = rel.parts
    if len(parts) < 4:
        return None
    version, filename = parts[-2], parts[-1]
    artifact = parts[-3]
    if not filename.endswith(".jar") or not filename.startswith(artifact + "-"):
        return None
    group_parts = parts[:-3]
    if not group_parts:
        return None
    prefix = artifact + "-"
    suffix = ".jar"
    name_version = filename[len(prefix):-len(suffix)]
    if name_version != version:
        return None
    return ".".join(group_parts), artifact, version

def scan_repository(root: str | Path, keywords: Iterable[str] | None = None) -> dict:
    base = Path(root).expanduser().resolve()
    terms = tuple(str(k).lower() for k in (keywords if keywords is not None else DEFAULT_KEYWORDS) if str(k).strip())
    artifacts = []
    for jar in sorted(base.rglob("*.jar")):
        coordinate = _coordinate(jar, base)
        if coordinate is None:
            continue
        group, artifact, version = coordinate
        haystack = f"{group}:{artifact}:{version}".lower()
        if terms and not any(term in haystack for term in terms):
            continue
        pom = jar.with_suffix(".pom")
        artifacts.append({
            "artifact": artifact,
            "version": version,
            "group": group,
            "jar": str(jar),
            "pom": str(pom) if pom.is_file() else None,
            "sha256": _sha256(jar),
            "class_count": _class_count(jar),
        })
    return {"network": "disabled", "root": str(base), "keywords": list(terms), "artifact_count": len(artifacts), "artifacts": artifacts}

def write_manifest(root: str | Path, output: str | Path, keywords: Iterable[str] | None = None) -> dict:
    result = scan_repository(root, keywords)
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"network": "disabled", "manifest": str(target.resolve()), "artifact_count": result["artifact_count"]}
