"""证据文件只能增不能改：同一天第二次 record_evidence 必须合并而不是覆盖。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.udc.microflow import capability_registry as CR

MATRIX = """| 节点 | 语料 | 占比 | 构造 | Schema | 运行证据 |
|---|---|---|---|---|---|
| DEMO_NODE | 1 | 0.1% | ✓ | ✓ | 未验证 |
"""


def _matrix(tmp_path):
    p = tmp_path / "m.md"
    p.write_text(MATRIX, encoding="utf-8")
    return str(p)


def _payload(case, **kw):
    d = {"date": "2026-01-01", "cases": [{"case": case, "pass": True}]}
    d.update(kw)
    return d


def test_second_run_merges_cases(tmp_path):
    ev = str(tmp_path / "evidence")
    mx = _matrix(tmp_path)
    CR.record_evidence("DEMO_NODE", _payload("A"), matrix_path=mx, evidence_dir=ev)
    CR.record_evidence("DEMO_NODE", _payload("B"), matrix_path=mx, evidence_dir=ev,
                       note="**RUN**")
    d = json.load(open(os.path.join(ev, "demo_node-runtime-2026-01-01.json"), encoding="utf-8"))
    assert [c["case"] for c in d["cases"]] == ["B", "A"], "新用例在前，旧用例保留"
    assert d["runs"] == 2


def test_not_covered_accumulates(tmp_path):
    ev = str(tmp_path / "evidence")
    mx = _matrix(tmp_path)
    CR.record_evidence("DEMO_NODE", _payload("A", not_covered=["x"]),
                       matrix_path=mx, evidence_dir=ev)
    CR.record_evidence("DEMO_NODE", _payload("B", not_covered=["y"]),
                       matrix_path=mx, evidence_dir=ev, note="**RUN**")
    d = json.load(open(os.path.join(ev, "demo_node-runtime-2026-01-01.json"), encoding="utf-8"))
    assert d["not_covered"] == ["y", "x"]


def test_same_case_text_overwrites_not_duplicates(tmp_path):
    ev = str(tmp_path / "evidence")
    mx = _matrix(tmp_path)
    CR.record_evidence("DEMO_NODE", _payload("A", cases=[{"case": "A", "pass": True,
                                                          "after": 1}]),
                       matrix_path=mx, evidence_dir=ev)
    CR.record_evidence("DEMO_NODE", _payload("A", cases=[{"case": "A", "pass": True,
                                                          "after": 2}]),
                       matrix_path=mx, evidence_dir=ev, note="**RUN**")
    d = json.load(open(os.path.join(ev, "demo_node-runtime-2026-01-01.json"), encoding="utf-8"))
    assert len(d["cases"]) == 1
    assert d["cases"][0]["after"] == 2, "同一用例以最新一次为准"


def test_no_pass_case_still_rejected(tmp_path):
    ev = str(tmp_path / "evidence")
    mx = _matrix(tmp_path)
    try:
        CR.record_evidence("DEMO_NODE", {"date": "2026-01-01",
                                         "cases": [{"case": "A", "pass": False}]},
                           matrix_path=mx, evidence_dir=ev)
    except ValueError:
        return
    raise AssertionError("没有 pass=True 的用例必须拒绝")
