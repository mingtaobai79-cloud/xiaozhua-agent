"""P6：能力登记（capability_registry）契约测试。

它保证三件事：
  1. 矩阵能被结构化读出（22 类、等级、范围限定）
  2. 生成出来的流程能拿到「哪些节点还没有运行证据」的提示
  3. 等级只能由带通过用例的证据提升，空 payload 会被拒绝
"""
import json
import os
import shutil

import pytest

from components.udc.microflow import capability_registry as CR


def test_matrix_loads_all_types():
    caps = CR.load()
    assert len(caps) >= 20, len(caps)
    assert "RETRIEVE_ARRAY" in caps and "CHANGE_LIST" in caps


def test_level_and_scope():
    unverified = CR.Capability('X', 1, '0%', '', '', note='CONSTRUCTED (RUNTIME_VERIFIED not yet established)')
    assert unverified.level == 'CONSTRUCTED'
    assert not unverified.verified
    caps = CR.load()
    ra = caps["RETRIEVE_ARRAY"]
    assert ra.level == "RUNTIME_VERIFIED"
    assert "CONDITION" in ra.scope or "未验" in ra.scope


def test_summary_covers_all():
    assert CR.summary({}) == {}
    s = CR.summary()
    total = sum(v["instances"] for v in s.values())
    all_inst = sum(c.instances for c in CR.load().values())
    assert total == all_inst
    assert 0 < s["RUNTIME_VERIFIED"]["pct"] <= 100


def _fake_caps(**levels):
    return {k: CR.Capability(k, 1, "0%", "✓", "✓", note="**%s**" % v)
            for k, v in levels.items()}


def _backed_caps(**levels):
    """同 _fake_caps，但把每个类型标成「有机器可读通过证据」。

    矩阵声明 RUNTIME_VERIFIED 已不足以让 advisory 闭嘴（见 evidence_backed），
    需要证据的类型必须显式带上证据（含运行来源），否则测试会把声明当证据。
    """
    return {k: CR.Capability(k, 1, "0%", "✓", "✓", note="**%s**" % v,
                             evidence=["%s-runtime.json" % k.lower()], evidence_passed=1,
                             evidence_provenance=1)
            for k, v in levels.items()}


def test_level_and_evidence_are_separate_axes():
    """等级是矩阵声明，证据是另一根轴；声明不能冒充证据。"""
    declared_only = CR.Capability('X', 1, '0%', '', '', note='**RUNTIME_VERIFIED**（矩阵自述）')
    assert declared_only.level == 'RUNTIME_VERIFIED'
    assert declared_only.verified, 'verified 仍表示矩阵声明，保持旧语义'
    assert not declared_only.evidence_backed, '没有机器可读证据就不能算有证据'

    backed = CR.Capability('X', 1, '0%', '', '', note='**RUNTIME_VERIFIED**',
                           evidence=['x-runtime.json'], evidence_passed=3,
                           evidence_provenance=3)
    assert backed.evidence_backed
    # 有证据文件但零通过用例，仍不算有证据
    empty = CR.Capability('X', 1, '0%', '', '', note='**RUNTIME_VERIFIED**',
                          evidence=['x-runtime.json'], evidence_passed=0)
    assert not empty.evidence_backed
    # 有 pass 但一条都不可追溯来源/回读 → 仍不算有证据
    self_report = CR.Capability('X', 1, '0%', '', '', note='**RUNTIME_VERIFIED**',
                                evidence=['x-runtime.json'], evidence_passed=3,
                                evidence_provenance=0)
    assert not self_report.evidence_backed, '自报 pass 不能单独构成证据'


def test_advisory_flags_declared_but_unbacked_runtime_level():
    """矩阵写 RUNTIME_VERIFIED 但没有机器可读证据 → advisory 必须明确 UNVERIFIED。"""
    caps = {
        'NODE_DECL': CR.Capability('NODE_DECL', 1, '0%', '✓', '✓',
                                   note='**RUNTIME_VERIFIED**'),
        'NODE_BACKED': CR.Capability('NODE_BACKED', 1, '0%', '✓', '✓',
                                     note='**RUNTIME_VERIFIED**',
                                     evidence=['b.json'], evidence_passed=2,
                                     evidence_provenance=2),
    }
    schema = {"nodes": [
        {"actionType": "NODE_DECL", "type": "ACTIVITY"},
        {"actionType": "NODE_BACKED", "type": "ACTIVITY"},
    ]}
    adv = CR.advisory(schema, caps)
    flagged = [a for a in adv if a.startswith('NODE_DECL')]
    assert flagged and all('UNVERIFIED' in a for a in flagged), adv
    assert 'RUNTIME_VERIFIED' in flagged[0], '要能看出这是「声明」而非「证据」'
    assert not any(a.startswith('NODE_BACKED') for a in adv), adv


def test_load_counts_only_machine_readable_pass_evidence(tmp_path):
    matrix = tmp_path / 'matrix.md'
    matrix.write_text(
        '| 节点 | 语料 | 占比 | 构造 | Schema | 运行证据 |\n|---|---|---|---|---|---|\n'
        '| NODE_OK | 1 | 1.0% | ✓ | ✓ | **RUNTIME_VERIFIED** |\n'
        '| NODE_ZERO | 1 | 1.0% | ✓ | ✓ | **RUNTIME_VERIFIED** |\n'
        '| NODE_PROSE | 1 | 1.0% | ✓ | ✓ | **RUNTIME_VERIFIED** |\n', encoding='utf-8')
    ev = tmp_path / 'evidence'
    ev.mkdir()
    (ev / 'ok.json').write_text(json.dumps({
        "node": "NODE_OK", "app_id": "1", "flow": {"name": "f"},
        "cases": [{"case": "a", "expect": 3, "after": 3, "pass": True},
                  {"case": "b", "pass": False}],
    }), encoding='utf-8')
    (ev / 'zero.json').write_text(json.dumps({
        "node": "NODE_ZERO", "cases": [{"case": "a", "pass": False}],
    }), encoding='utf-8')
    (ev / 'prose.json').write_text(json.dumps({
        "node": "NODE_PROSE", "run": {"success": True}, "notes": "人工看过",
    }), encoding='utf-8')
    (ev / 'broken.json').write_text('[1, 2, 3]', encoding='utf-8')  # 非 dict 不能炸

    caps = CR.load(str(matrix), str(ev))
    assert caps['NODE_OK'].evidence_passed == 1, '只数 pass=True'
    assert caps['NODE_OK'].evidence_backed, '来源齐全 + 数值回读一致才算证据'
    assert caps['NODE_ZERO'].level == 'RUNTIME_VERIFIED'
    assert not caps['NODE_ZERO'].evidence_backed, '全是 pass=False 不算证据'
    assert not caps['NODE_PROSE'].evidence_backed, '散文式证据不可机器判定'


def test_repo_matrix_declared_level_is_not_counted_as_evidence():
    caps = CR.load()
    assert caps['RETRIEVE_ARRAY'].evidence_backed, '有 cases 证据的类型应被认到'
    declared_only = [a for a, c in caps.items()
                     if c.level == 'RUNTIME_VERIFIED' and not c.evidence]
    for act in declared_only:
        assert not caps[act].evidence_backed
    adv = CR.advisory({"nodes": [{"actionType": a} for a in declared_only]}, caps)
    assert len(adv) == len(declared_only), '每个声明型 RUNTIME_VERIFIED 都要点名'
    assert all('UNVERIFIED' in a for a in adv), adv


def test_advisory_flags_unverified_node():
    caps = _backed_caps(NODE_A="RUNTIME_VERIFIED", NODE_B="SCHEMA_VERIFIED")
    schema = {"nodes": [
        {"actionType": "NODE_B", "type": "ACTIVITY", "nodes": []},
        {"actionType": "NODE_A", "type": "ACTIVITY", "nodes": []},
    ]}
    adv = CR.advisory(schema, caps)
    assert any(a.startswith("NODE_B") for a in adv), adv
    assert not any(a.startswith("NODE_A") for a in adv), adv


def test_advisory_dedupes_and_walks_branches():
    caps = _fake_caps(NODE_B="CONSTRUCTED")
    schema = {"nodes": [
        {"actionType": "NODE_B", "type": "ACTIVITY",
         "conditions": [{"nodes": [{"actionType": "NODE_B", "type": "ACTIVITY"}]}]},
    ]}
    adv = CR.advisory(schema, caps)
    assert len(adv) == 1, adv


def test_advisory_reports_unknown_action_with_explicit_empty_registry(tmp_path):
    with pytest.raises(FileNotFoundError):
        CR.load(str(tmp_path / 'missing-matrix.md'), str(tmp_path / 'evidence'))
    invalid = tmp_path / 'invalid.md'
    invalid.write_text('not a capability matrix', encoding='utf-8')
    with pytest.raises(ValueError, match='matrix'):
        CR.load(str(invalid), str(tmp_path / 'evidence'))
    schema = {"nodes": [{"type": "ACTIVITY", "actionType": "NONEXISTENT_ACTION"}]}
    result = CR.advisory(schema, {})
    assert any("NONEXISTENT_ACTION" in entry and "UNVERIFIED" in entry for entry in result)


def test_advisory_failure_is_visible_through_composer(monkeypatch):
    from components.construction.microflow_composer import MicroflowComposer
    from components.construction.node_builder import NodeBuilder

    def broken(_schema):
        raise OSError('matrix unavailable')

    monkeypatch.setattr(CR, 'advisory', broken)
    composer = MicroflowComposer(NodeBuilder(app_id='9000000000000000001', app_name='app9000000000000000001'), None,
                                 app_id='9000000000000000001', app_name='app9000000000000000001')
    composer.nodes.append({'type': 'ACTIVITY', 'actionType': 'NONEXISTENT_ACTION'})
    composer.finish(gate=False)
    assert any('UNVERIFIED' in item for item in composer.advisories)


def test_record_evidence_rejects_empty_cases():
    with pytest.raises(ValueError):
        CR.record_evidence("CALL_APP_SERVICE", {"cases": [{"pass": False}]})


def test_record_evidence_updates_matrix(tmp_path):
    matrix = tmp_path / "matrix.md"
    evdir = tmp_path / "evidence"
    shutil.copy(CR.MATRIX, matrix)
    payload = {"date": "2099-01-01", "node": "CALL_APP_SERVICE",
               "cases": [{"case": "x", "pass": True, "before": 1, "after": 2}]}
    path = CR.record_evidence("CALL_APP_SERVICE", payload, note="**RUNTIME_VERIFIED**（测试用例）",
                              matrix_path=str(matrix), evidence_dir=str(evdir))
    assert os.path.exists(path)
    caps = CR.load(str(matrix), str(evdir))
    assert caps["CALL_APP_SERVICE"].level == "RUNTIME_VERIFIED"
    assert caps["CALL_APP_SERVICE"].evidence, "证据文件应挂到该类型上"
    assert json.loads(open(path, encoding="utf-8").read())["node"] == "CALL_APP_SERVICE"


# ---------------------------------------------------------------------------
# 自报 pass ≠ 证据：来源、可比对回读、范围三项必须能分开说
# ---------------------------------------------------------------------------

_DECL_MATRIX = (
    '| 节点 | 语料 | 占比 | 构造 | Schema | 运行证据 |\n|---|---|---|---|---|---|\n'
    '| NODE_SYN | 1 | 1.0% | ✓ | ✓ | **RUNTIME_VERIFIED** |\n'
    '| NODE_OK | 1 | 1.0% | ✓ | ✓ | **RUNTIME_VERIFIED** |\n')


def _registry(tmp_path, files, matrix_text=_DECL_MATRIX):
    matrix = tmp_path / 'm.md'
    matrix.write_text(matrix_text, encoding='utf-8')
    ev = tmp_path / 'ev'
    ev.mkdir(exist_ok=True)
    for name, payload in files.items():
        (ev / name).write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    return CR.load(str(matrix), str(ev))


def test_single_self_reported_pass_does_not_clear_advisory(tmp_path):
    """合成 {node, cases:[{pass:true}]} 不得让 advisory 闭嘴（主线程反例）。"""
    caps = _registry(tmp_path, {'syn.json': {"node": "NODE_SYN",
                                             "cases": [{"case": "看着过了", "pass": True}]}})
    syn = caps['NODE_SYN']
    assert syn.level == 'RUNTIME_VERIFIED', '矩阵声明仍在，不篡改声明'
    assert syn.evidence_passed == 1, '自报通过仍计数，但只作为「自报」'
    assert not syn.evidence_backed, '无来源、无回读的自报 pass 不是证据'
    adv = CR.advisory({"nodes": [{"actionType": "NODE_SYN"}]}, caps)
    assert adv and 'UNVERIFIED' in adv[0], adv
    assert '自报' in adv[0] or '来源' in adv[0], '要说明缺的是来源/回读，不是「无证据」'


def test_pass_contradicting_numeric_readback_is_not_evidence(tmp_path):
    """pass=True 但回读值与预期矛盾 → 自相矛盾，不算证据。"""
    caps = _registry(tmp_path, {'bad.json': {
        "node": "NODE_SYN", "app_id": "8704025620829192834",
        "cases": [{"case": "分页返回 3 条", "expect": 3, "after": 5, "pass": True}]}})
    assert caps['NODE_SYN'].evidence_passed == 1
    assert not caps['NODE_SYN'].evidence_backed, '矛盾用例不能因写了 pass=True 就算证据'
    assert CR.advisory({"nodes": [{"actionType": "NODE_SYN"}]}, caps)


def test_readback_without_run_provenance_is_not_evidence(tmp_path):
    """用例有回读但文件没有运行来源（app/env/flow/build）→ 说不清哪次运行。"""
    caps = _registry(tmp_path, {'noenv.json': {
        "node": "NODE_SYN",
        "cases": [{"case": "a", "expect": 3, "after": 3, "pass": True}]}})
    assert not caps['NODE_SYN'].evidence_backed
    assert 'UNVERIFIED' in CR.advisory({"nodes": [{"actionType": "NODE_SYN"}]}, caps)[0]


def test_readback_with_provenance_is_evidence(tmp_path):
    """回读一致 + 运行来源齐全 → 才允许 advisory 闭嘴（正例，防止修复过度）。"""
    caps = _registry(tmp_path, {'ok.json': {
        "node": "NODE_SYN", "app_id": "8704025620829192834", "date": "2026-11-03",
        "flow": {"name": "p6x", "mid": "1"},
        "cases": [{"case": "a", "expect": 3, "after": 3, "pass": True,
                   "evidence": "P6X-A=3"}]}})
    ok = caps['NODE_SYN']
    assert ok.evidence_backed
    assert CR.advisory({"nodes": [{"actionType": "NODE_SYN"}]}, caps) == []


def test_advisory_reports_scope_gap_of_backed_node(tmp_path):
    """pass 不能证明范围：已验但 not_covered 非空时要点明未覆盖项。"""
    caps = _registry(tmp_path, {'ok.json': {
        "node": "NODE_SYN", "app_id": "1", "flow": {"name": "f"},
        "cases": [{"case": "a", "expect": 1, "after": 1, "pass": True}],
        "not_covered": ["needTotal 回读", "多条件 OR 语义"]}})
    adv = CR.advisory({"nodes": [{"actionType": "NODE_SYN"}]}, caps)
    assert adv, '范围缺口必须可见，不能静默'
    assert '未覆盖' in adv[0] and 'needTotal 回读' in adv[0], adv
    assert 'UNVERIFIED' not in adv[0], '有证据的类型不该被报成未验证'


def test_record_evidence_self_reported_pass_does_not_upgrade_level(tmp_path):
    """写入路径同样：裸 pass 落盘留痕，但不得把矩阵等级抬到 RUNTIME_VERIFIED。"""
    matrix = tmp_path / 'm.md'
    matrix.write_text(_DECL_MATRIX.replace('| NODE_SYN | 1 | 1.0% | ✓ | ✓ | **RUNTIME_VERIFIED** |',
                                           '| NODE_SYN | 1 | 1.0% | ✓ | ✓ | CONSTRUCTED |'),
                      encoding='utf-8')
    ev = tmp_path / 'ev'
    CR.record_evidence('NODE_SYN', {"date": "2099-01-02",
                                    "cases": [{"case": "自报", "pass": True}]},
                       matrix_path=str(matrix), evidence_dir=str(ev))
    assert (ev / 'node_syn-runtime-2099-01-02.json').exists(), '证据仍落盘（audit 只增）'
    caps = CR.load(str(matrix), str(ev))
    assert caps['NODE_SYN'].level != 'RUNTIME_VERIFIED', '裸 pass 不能提升等级'
    assert not caps['NODE_SYN'].evidence_backed


def test_record_evidence_traceable_upgrade_requires_provenance(tmp_path):
    """有回读但 payload 无运行来源 → 落盘留痕、仍不升级（写入与读取同一把尺子）。"""
    matrix = tmp_path / 'm.md'
    matrix.write_text(_DECL_MATRIX.replace('| NODE_SYN | 1 | 1.0% | ✓ | ✓ | **RUNTIME_VERIFIED** |',
                                           '| NODE_SYN | 1 | 1.0% | ✓ | ✓ | CONSTRUCTED |'),
                      encoding='utf-8')
    ev = tmp_path / 'ev'
    p = CR.record_evidence('NODE_SYN', {"date": "2099-01-03",
                                        "cases": [{"case": "a", "expect": 3, "after": 3,
                                                   "pass": True}]},
                           matrix_path=str(matrix), evidence_dir=str(ev))
    saved = json.loads(open(p, encoding='utf-8').read())
    assert saved['evidence_strength'] == 'self_report'
    assert '不提升矩阵等级' in saved['_upgrade_blocked']
    assert CR.load(str(matrix), str(ev))['NODE_SYN'].level == 'CONSTRUCTED'
    # 补齐来源后同一份用例才升级
    CR.record_evidence('NODE_SYN', {"date": "2099-01-04", "app_id": "1",
                                    "flow": {"name": "f"},
                                    "cases": [{"case": "a", "expect": 3, "after": 3,
                                               "pass": True}]},
                       matrix_path=str(matrix), evidence_dir=str(ev))
    up = CR.load(str(matrix), str(ev))['NODE_SYN']
    assert up.level == 'RUNTIME_VERIFIED'
    # 两天的证据文件都在盘上，但只有补了来源的那一份用例可追溯
    assert up.evidence_passed == 2 and up.evidence_provenance == 1
    assert up.evidence_backed


def test_cli_reports_traceable_vs_self_reported(capsys):
    """CLI 也要把「可追溯」和「自报」分开显示，不能只看 pass 总数。"""
    assert CR._main(['RETRIEVE_ARRAY']) == 0
    out = capsys.readouterr().out
    assert '可追溯用例' in out
    assert '未覆盖' in out, 'not_covered 必须在人读输出里可见'
    assert CR._main(['BREAK']) == 0
    out = capsys.readouterr().out
    assert 'UNVERIFIED' in out and '可追溯用例: 0/0' in out, out


def test_real_bootstrap_body_still_flags_synthetic_evidence(tmp_path, monkeypatch):
    """真实宿主入口：bootstrap()['microflow_create_body'] 消费合成证据时仍报 UNVERIFIED。"""
    from seeyon_host_bootstrap import bootstrap
    matrix = tmp_path / 'm.md'
    ev = tmp_path / 'ev'
    matrix.write_text(_DECL_MATRIX, encoding='utf-8')
    ev.mkdir()
    (ev / 'syn.json').write_text(json.dumps({"node": "NODE_SYN", "cases": [
        {"case": "看着过了", "pass": True}]}), encoding='utf-8')
    real_load = CR.load
    monkeypatch.setattr(CR, 'load', lambda *a, **k: real_load(str(matrix), str(ev)))
    body = bootstrap()['microflow_create_body'](
        'demo', 'demo', '1',
        {"nodes": [{"nodeId": "n1", "type": "ACTIVITY", "actionType": "NODE_SYN"}]})
    assert any('NODE_SYN' in u and 'UNVERIFIED' in u for u in body.get('unknowns', [])), \
        body.get('unknowns')
