"""Offline Profile Evidence Graph: four profile kinds as independent nodes.

Only six relation types are allowed:
udc_builds, standard_supports, extension_for, config_binds, pod_runs, app_depends_on.

Detectors:
- same-ID role conflict (one id used by two different profile kinds),
- standard product embedded inside a UDC platform (boundary violation),
- pod responsibility inferred without evidence.

Output: conflicts / gaps / status. CLI reads local JSON and prints one-line JSON.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from components.profile_graph import build_profile_graph, load_json

ROOT = Path(__file__).parents[1]


def _platform(id="udc", **kw):
    base = {"id": id, "kind": "udc_platform", "status": "FACT", "evidence_refs": ["audit:udc"]}
    base.update(kw)
    return base


def _standard(id="bpm", **kw):
    base = {"id": id, "kind": "standard_product_application", "status": "FACT", "evidence_refs": ["inventory:bpm"]}
    base.update(kw)
    return base


def _customer(id="app-1", **kw):
    base = {"id": id, "kind": "customer_udc_application", "application_id": id, "status": "FACT",
            "evidence_refs": ["nacos:app-1"]}
    base.update(kw)
    return base


def _extension(id="ext-1", **kw):
    base = {"id": id, "kind": "extension_service", "status": "FACT", "evidence_refs": ["src:ext-1"]}
    base.update(kw)
    return base


# ---------------------------------------------------------------- node model

def test_profiles_become_independent_nodes_preserving_kind_and_status():
    result = build_profile_graph({"profiles": [_platform(), _standard(), _customer(), _extension()]})
    assert result["mode"] == "offline"
    assert result["network"] == "disabled"
    nodes = {node["id"]: node for node in result["nodes"]}
    assert set(nodes) == {"udc", "bpm", "app-1", "ext-1"}
    assert nodes["udc"]["kind"] == "udc_platform"
    assert nodes["bpm"]["kind"] == "standard_product_application"
    assert nodes["app-1"]["kind"] == "customer_udc_application"
    assert nodes["ext-1"]["kind"] == "extension_service"
    assert nodes["app-1"]["status"] == "FACT"
    assert nodes["app-1"]["evidence_refs"] == ["nacos:app-1"]


# ------------------------------------------------------------- relations

def test_only_allowlisted_relations_are_kept_and_others_reported():
    profiles = [
        _platform(),
        _customer(relations=[
            {"type": "udc_builds", "target": "udc"},
            {"type": "app_depends_on", "target": "bpm"},
            {"type": "calls", "target": "mystery"},
            {"type": "COPY_DATA", "target": "bpm"},
        ]),
    ]
    result = build_profile_graph({"profiles": profiles})
    edges = [(edge["source"], edge["type"], edge["target"]) for edge in result["edges"]]
    assert ("app-1", "udc_builds", "udc") in edges
    assert ("app-1", "app_depends_on", "bpm") in edges
    assert ("app-1", "calls", "mystery") not in edges
    assert len(result["edges"]) == 2
    rejected = {(e["source"], e["type"], e["target"]) for e in result["rejected_relations"]}
    assert ("app-1", "calls", "mystery") in rejected
    assert ("app-1", "COPY_DATA", "bpm") in rejected


def test_each_allowed_relation_type_is_accepted():
    profiles = [
        _platform(id="udc"),
        _standard(id="bpm"),
        _customer(id="app-1", relations=[
            {"type": "udc_builds", "target": "udc"},
            {"type": "app_depends_on", "target": "bpm"},
        ]),
        _extension(id="ext-1", relations=[{"type": "extension_for", "target": "app-1"}]),
        {"id": "pod-1", "kind": "extension_service", "status": "FACT", "evidence_refs": ["k8s:pod-1"],
         "relations": [{"type": "pod_runs", "target": "ext-1"}]},
        _customer(id="app-2", relations=[
            {"type": "config_binds", "target": "bpm", "evidence_refs": ["config:app-2"]},
            {"type": "standard_supports", "target": "udc"},
        ]),
        _platform(id="udc2"),
        {"id": "pod-2", "kind": "extension_service", "status": "FACT", "evidence_refs": ["k8s:pod-2"],
         "relations": [{"type": "pod_runs", "target": "ext-1"}]},
    ]
    result = build_profile_graph({"profiles": profiles})
    edge_types = {edge["type"] for edge in result["edges"]}
    assert edge_types <= {"udc_builds", "standard_supports", "extension_for", "config_binds", "pod_runs", "app_depends_on"}
    for relation in ("udc_builds", "standard_supports", "extension_for", "config_binds", "pod_runs", "app_depends_on"):
        assert relation in edge_types, relation


# ------------------------------------------------------------- conflict detection

def test_same_id_used_by_two_profile_kinds_is_a_conflict():
    profiles = [
        _platform(id="shared-1"),
        _standard(id="shared-1"),
        _customer(id="app-1"),
    ]
    result = build_profile_graph({"profiles": profiles})
    assert result["status"] == "CONFLICT"
    conflict_types = [conflict["type"] for conflict in result["conflicts"]]
    assert "same_id_role_conflict" in conflict_types
    conflict = next(c for c in result["conflicts"] if c["type"] == "same_id_role_conflict")
    assert conflict["id"] == "shared-1"
    assert set(conflict["kinds"]) == {"udc_platform", "standard_product_application"}


def test_conflict_nodes_keep_only_the_first_role_and_preserve_evidence():
    profiles = [
        _platform(id="shared-1"),
        _standard(id="shared-1", evidence_refs=["inventory:shared-1"]),
    ]
    result = build_profile_graph({"profiles": profiles})
    ids = [node["id"] for node in result["nodes"]]
    assert ids.count("shared-1") == 1
    node = next(n for n in result["nodes"] if n["id"] == "shared-1")
    assert node["kind"] == "udc_platform"
    node_refs = node["evidence_refs"]
    assert "audit:udc" in node_refs
    assert "inventory:shared-1" in node_refs


# ------------------------------------------------------------- boundary violation

def test_standard_product_nested_inside_udc_platform_is_reported():
    profiles = [
        _platform(id="udc"),
        _standard(id="bpm"),
        _customer(id="app-1", relations=[{"type": "standard_supports", "target": "udc"}]),
        {"id": "bpm", "kind": "udc_platform", "status": "FACT", "evidence_refs": ["audit:bpm"],
         "relations": [{"type": "udc_builds", "target": "app-1"}]},
    ]
    result = build_profile_graph({"profiles": profiles})
    conflict_types = [c["type"] for c in result["conflicts"]]
    assert "standard_product_embedded_in_udc" in conflict_types
    conflict = next(c for c in result["conflicts"] if c["type"] == "standard_product_embedded_in_udc")
    assert conflict["standard_id"] == "bpm"
    assert result["status"] == "CONFLICT"


# ------------------------------------------------------------- pod gap detection

def test_pod_responsibility_without_evidence_is_a_gap_not_a_conflict():
    profiles = [
        _platform(id="udc"),
        _extension(id="ext-1"),
        {"id": "pod-1", "kind": "extension_service", "evidence_refs": [], "relations": []},
        {"id": "pod-2", "kind": "extension_service", "evidence_refs": ["k8s:pod-2"],
         "relations": [{"type": "pod_runs", "target": "ext-1"}]},
    ]
    result = build_profile_graph({"profiles": profiles})
    assert result["status"] != "CONFLICT"
    assert "pod-1: pod responsibility inferred without evidence" in result["gaps"]
    assert not any("pod-2" in gap for gap in result["gaps"])


def test_pod_with_relations_but_no_evidence_still_flags_gap():
    profiles = [
        {"id": "pod-x", "kind": "extension_service", "evidence_refs": [],
         "relations": [{"type": "pod_runs", "target": "anything"}]},
    ]
    result = build_profile_graph({"profiles": profiles})
    assert "pod-x: pod responsibility inferred without evidence" in result["gaps"]


# ------------------------------------------------------------- status

def test_status_fact_when_no_conflicts_and_no_gaps():
    profiles = [
        _platform(id="udc"),
        _standard(id="bpm"),
        _customer(id="app-1", relations=[{"type": "udc_builds", "target": "udc", "evidence_refs": ["audit:build-app-1"]}]),
        _extension(id="ext-1"),
        {"id": "pod-1", "kind": "extension_service", "evidence_refs": ["k8s:pod-1"],
         "relations": [{"type": "pod_runs", "target": "ext-1"}]},
    ]
    result = build_profile_graph({"profiles": profiles})
    assert result["conflicts"] == []
    assert result["gaps"] == []
    assert result["status"] == "FACT"


def test_status_partial_when_gaps_present_but_no_conflicts():
    profiles = [
        _platform(id="udc"),
        {"id": "pod-1", "kind": "extension_service", "evidence_refs": [], "relations": []},
    ]
    result = build_profile_graph({"profiles": profiles})
    assert result["status"] == "PARTIALLY_VERIFIED"
    assert result["conflicts"] == []


def test_status_unverified_when_no_input():
    result = build_profile_graph({"profiles": []})
    assert result["status"] == "UNVERIFIED"
    assert result["nodes"] == []


def test_build_profile_graph_tolerates_none_and_non_dict_profiles():
    assert build_profile_graph(None)["status"] == "UNVERIFIED"
    assert build_profile_graph({"profiles": "nope"})["status"] == "UNVERIFIED"


# ------------------------------------------------------------- CLI

def test_cli_profile_graph_reads_local_json_and_prints_single_line(tmp_path):
    payload = {"profiles": [
        _platform(id="udc"),
        _standard(id="bpm"),
        _customer(id="app-1", relations=[{"type": "app_depends_on", "target": "bpm", "evidence_refs": ["config:app-1"]}]),
        _extension(id="ext-1"),
        {"id": "pod-1", "kind": "extension_service", "evidence_refs": ["k8s:pod-1"],
         "relations": [{"type": "pod_runs", "target": "ext-1", "evidence_refs": ["k8s:pod-1"]}]},
    ]}
    source = tmp_path / "profiles.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "xiaozhua_cli", "profile-graph", "--profiles-json", str(source)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().count("\n") == 0
    parsed = json.loads(result.stdout)
    assert parsed["network"] == "disabled"
    assert parsed["status"] == "FACT"
    assert {node["id"] for node in parsed["nodes"]} == {"udc", "bpm", "app-1", "ext-1", "pod-1"}


def test_cli_profile_graph_conflict_exit_code_two(tmp_path):
    payload = {"profiles": [_platform(id="dup"), _standard(id="dup")]}
    source = tmp_path / "profiles.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "xiaozhua_cli", "profile-graph", "--profiles-json", str(source)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 2
    parsed = json.loads(result.stdout)
    assert parsed["status"] == "CONFLICT"


def test_cli_profile_graph_requires_profiles_json(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "xiaozhua_cli", "profile-graph"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "profiles-json" in result.stderr


def test_load_json_reads_bom_file(tmp_path):
    source = tmp_path / "profiles.json"
    source.write_text(json.dumps({"profiles": []}), encoding="utf-8-sig")
    assert load_json(str(source)) == {"profiles": []}


# ------------------------------------------------ evidence integrity regressions

def test_unverified_or_unevidenced_node_cannot_make_graph_fact():
    result = build_profile_graph({"profiles": [
        {"id": "udc-x", "kind": "udc_platform", "status": "UNVERIFIED", "evidence_refs": []},
    ]})
    assert result["status"] == "PARTIALLY_VERIFIED"
    assert "udc-x: profile is not backed by FACT evidence" in result["gaps"]


def test_static_live_claim_is_downgraded_and_reported():
    result = build_profile_graph({"profiles": [
        {"id": "app-live", "kind": "customer_udc_application", "status": "LIVE", "evidence_refs": ["static:audit.json"]},
    ]})
    node = result["nodes"][0]
    assert node["status"] == "UNVERIFIED"
    assert result["status"] == "PARTIALLY_VERIFIED"
    assert "app-live: static input status LIVE was downgraded to UNVERIFIED" in result["gaps"]


def test_unknown_profile_kind_is_rejected_not_promoted_to_fact():
    result = build_profile_graph({"profiles": [
        {"id": "mystery", "kind": "super_admin", "status": "FACT", "evidence_refs": ["input:mystery"]},
    ]})
    assert result["nodes"] == []
    assert result["status"] == "UNVERIFIED"
    assert result["rejected_profiles"] == [
        {"id": "mystery", "kind": "super_admin", "reason": "profile kind is not allowed"}
    ]


def test_relation_without_own_evidence_stays_unevidenced():
    result = build_profile_graph({"profiles": [
        _customer(id="app-1", relations=[{"type": "app_depends_on", "target": "bpm"}]),
        _standard(id="bpm"),
    ]})
    edge = result["edges"][0]
    assert edge["evidence_refs"] == []
    assert "nacos:app-1" not in edge["evidence_refs"]


def test_cli_profile_graph_missing_file_returns_single_line_json_error(tmp_path):
    missing = tmp_path / "missing.json"
    result = subprocess.run(
        [sys.executable, "-m", "xiaozhua_cli", "profile-graph", "--profiles-json", str(missing)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert result.stdout.strip().count("\n") == 0
    parsed = json.loads(result.stdout)
    assert parsed["status"] == "UNVERIFIED"
    assert parsed["error"] == "profile input could not be loaded"
    assert "Traceback" not in result.stderr
