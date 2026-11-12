import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from components.artifact_inventory import scan_repository

ROOT = Path(__file__).parents[1]

def make_artifact(root, group, artifact, version, classes=("A.class",)):
    base = root / Path(*group.split(".")) / artifact / version
    base.mkdir(parents=True)
    jar = base / f"{artifact}-{version}.jar"
    with zipfile.ZipFile(jar, "w") as zf:
        for name in classes:
            zf.writestr(name, b"class")
        zf.writestr("META-INF/MANIFEST.MF", b"Manifest-Version: 1.0\n")
    pom = base / f"{artifact}-{version}.pom"
    pom.write_text("<project/>", encoding="utf-8")
    return jar, pom

def test_scan_reports_coordinates_files_digest_and_class_count(tmp_path):
    jar, pom = make_artifact(tmp_path, "com.seeyon", "udc-core", "1.2.3", ("A.class", "x/B.class"))
    result = scan_repository(tmp_path)
    assert result["network"] == "disabled"
    assert result["artifacts"] == [{
        "artifact": "udc-core", "version": "1.2.3", "group": "com.seeyon",
        "jar": str(jar), "pom": str(pom),
        "sha256": hashlib.sha256(jar.read_bytes()).hexdigest(), "class_count": 2,
    }]

def test_scan_keyword_filter_is_case_insensitive_and_matches_coordinates(tmp_path):
    make_artifact(tmp_path, "com.example", "other", "1.0", ("A.class",))
    make_artifact(tmp_path, "com.seeyon", "lowcode-ui", "2.0", ("A.class",))
    result = scan_repository(tmp_path, keywords=["LOWCODE"])
    assert [x["artifact"] for x in result["artifacts"]] == ["lowcode-ui"]

def test_scan_ignores_non_maven_jars_and_missing_pom_is_null(tmp_path):
    (tmp_path / "random.jar").write_bytes(b"not zip")
    jar, _ = make_artifact(tmp_path, "org.demo", "xiaozhua-api", "3.0")
    (jar.with_suffix(".pom")).unlink()
    result = scan_repository(tmp_path)
    assert len(result["artifacts"]) == 1
    assert result["artifacts"][0]["pom"] is None

def test_cli_artifact_inventory_writes_manifest(tmp_path):
    make_artifact(tmp_path, "com.seeyon", "udc-web", "5.3.517")
    output = tmp_path / "manifest.json"
    result = subprocess.run([sys.executable, "-m", "xiaozhua_cli", "artifact-inventory", "--root", str(tmp_path), "--keyword", "udc", "--output", str(output)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["manifest"] == str(output)
    assert json.loads(output.read_text(encoding="utf-8"))["artifacts"][0]["artifact"] == "udc-web"
