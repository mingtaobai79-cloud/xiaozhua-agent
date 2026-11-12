"""P5.1 编排器状态机与闸门语义测试（纯本地，不碰平台）。"""
import sys
import pytest

sys.path.insert(0, ".")

from components.construction.p5_pipeline import (
    ALLOWED, DeliveryReport, MicroflowPipeline, PipelineError, Stage,
    StageFailed, StageRecord)


# ---------------------------------------------------------------- 状态机

def test_construct_report_exposes_advisory_failure(monkeypatch):
    from components.udc.microflow import capability_registry

    monkeypatch.setattr(capability_registry, 'advisory', lambda schema: (_ for _ in ()).throw(RuntimeError('private')))
    p = MicroflowPipeline(host='h', cookie='c', app_id='1', app_name='app')
    p.state = Stage.GRAPH_VALIDATED
    p._graph = {'nodes': [{'id': 'v', 'kind': 'create_variable', 'title': 'v', 'data_type': 'STRING', 'value': 'x'}]}
    p._stage_construct()
    detail = p.report.stage(Stage.CONSTRUCTED).detail
    assert detail['advisories'] == ['UNVERIFIED: capability advisory unavailable']
    import json
    serialized = json.dumps(p.report.to_dict(), ensure_ascii=False)
    report = json.loads(serialized)
    stage = next(s for s in report['stages'] if s['stage'] == Stage.CONSTRUCTED)
    assert stage['detail']['advisories'] == detail['advisories']
    assert 'private' not in serialized


def test_stage_order_is_linear_and_complete():
    """主序必须线性、末位是 BUILD_SUCCESS、且不含 BLOCKED/FAILED。"""
    assert Stage.ORDER[-1] == Stage.BUILD_SUCCESS
    assert Stage.BLOCKED not in Stage.ORDER
    assert Stage.FAILED not in Stage.ORDER
    assert len(set(Stage.ORDER)) == len(Stage.ORDER), "主序有重复"
    # 除末位外每个阶段都应有出边
    for s in Stage.ORDER[:-1]:
        assert ALLOWED[s], "%s 应有出边" % s


def test_terminal_states_have_no_outgoing():
    for t in Stage.TERMINAL:
        assert ALLOWED[t] == set(), "终态 %s 不应有出边" % t


def test_every_stage_is_reachable_from_none():
    """从 None 出发，沿合法迁移能走到每个主序阶段。"""
    seen = set()
    frontier = set(ALLOWED[None])
    while frontier:
        cur = frontier.pop()
        if cur in seen:
            continue
        seen.add(cur)
        frontier |= (ALLOWED.get(cur, set()) - seen)
    missing = set(Stage.ORDER) - seen
    assert not missing, "不可达阶段: %s" % sorted(missing)


def test_cannot_skip_constructed():
    """★ 不许从 GRAPH_VALIDATED 直接跳到 SAVED。"""
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    p.state = Stage.GRAPH_VALIDATED
    with pytest.raises(PipelineError):
        p._advance(Stage.SAVED)


def test_cannot_jump_to_build_from_saved():
    """★ 不许从 SAVED 直接 BUILD_SUCCESS（必须先发布）。"""
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    p.state = Stage.SAVED
    with pytest.raises(PipelineError):
        p._advance(Stage.BUILD_SUCCESS)


def test_cannot_skip_ui_finalize():
    """★ NEEDS_UI_FINALIZE 不能直接跳到 READBACK_VERIFIED。"""
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    p.state = Stage.NEEDS_UI_FINALIZE
    with pytest.raises(PipelineError):
        p._advance(Stage.READBACK_VERIFIED)


def test_platform_validated_can_go_straight_to_readback():
    """无字段引用时可以跳过 UI 最终化。"""
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    p.state = Stage.PLATFORM_VALIDATED
    rec = p._advance(Stage.READBACK_VERIFIED)
    assert rec.stage == Stage.READBACK_VERIFIED


# ---------------------------------------------------------------- 报告语义

def test_needs_ui_finalize_is_not_success():
    """★ NEEDS_UI_FINALIZE 不是成功状态。"""
    r = DeliveryReport(state=Stage.NEEDS_UI_FINALIZE)
    assert not r.ok


def test_published_is_not_success():
    """★ 发布成功也不算交付完成（还要构建）。"""
    r = DeliveryReport(state=Stage.PUBLISHED)
    assert not r.ok


def test_only_build_success_is_ok():
    r = DeliveryReport(state=Stage.BUILD_SUCCESS)
    assert r.ok


def test_stage_record_elapsed():
    rec = StageRecord(stage="X", ok=True, started_at=100.0, ended_at=102.5)
    assert rec.elapsed == 2.5


def test_report_stage_lookup():
    r = DeliveryReport()
    r.stages.append(StageRecord(stage=Stage.SAVED, ok=True))
    assert r.stage(Stage.SAVED).ok
    assert r.stage(Stage.BUILD_SUCCESS) is None


def test_report_to_dict_is_json_serializable():
    import json
    r = DeliveryReport(app_id="1", state=Stage.BUILD_SUCCESS,
                       stages=[StageRecord(stage=Stage.SAVED, ok=True)])
    r.ended_at = r.started_at + 1
    json.dumps(r.to_dict())          # 不抛即通过


# ---------------------------------------------------------------- 闸门：BLOCKED

class _FakeCompilerResult:
    def __init__(self, status, issues=None, graph=None, fixes=None):
        self.status = status
        self.issues = issues or []
        self.graph = graph
        self.fixes = fixes or []
        self.resolved = {}


class _FakeIssue:
    def __init__(self, msg):
        self.message = msg
        self.code = "X"

    def to_dict(self):
        return {"code": self.code, "message": self.message}


def _patch_compiler(monkeypatch, result):
    import components.construction.requirement_compiler as RC

    class Fake(RC.BusinessRequirementCompiler):
        def compile(self, draft, *, app_id="", app_name="", text=""):
            return result

    monkeypatch.setattr(RC, "BusinessRequirementCompiler", Fake)


def test_blocked_stops_before_construct(monkeypatch):
    """★ BLOCKED 必须禁止继续构造。"""
    _patch_compiler(monkeypatch, _FakeCompilerResult(
        "BLOCKED", issues=[_FakeIssue("实体不存在")]))
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    rep = p.run(draft={"nodes": []}, text="随便")
    assert rep.state == Stage.BLOCKED
    assert not rep.ok
    assert rep.failure["stage"] == Stage.DRAFT_READY
    # 没有任何构造/保存记录
    names = [s.stage for s in rep.stages]
    assert Stage.CONSTRUCTED not in names
    assert Stage.SAVED not in names


def test_ambiguous_stops_and_asks_human(monkeypatch):
    """★ AMBIGUOUS 也不能越过编译闸门。"""
    _patch_compiler(monkeypatch, _FakeCompilerResult(
        "AMBIGUOUS", issues=[_FakeIssue("「其他」范围没定义")]))
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    rep = p.run(draft={"nodes": []})
    assert rep.state == Stage.BLOCKED
    assert "AMBIGUOUS" in " ".join(rep.stage(Stage.BLOCKED).problems)


def test_ready_advances_to_draft_ready(monkeypatch):
    _patch_compiler(monkeypatch, _FakeCompilerResult(
        "READY", graph={"nodes": [], "end": {}}))
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    # 只跑到 draft 阶段就够
    p.report.requirement_summary = ""
    p._stage_draft({"nodes": []})
    assert p.state == Stage.DRAFT_READY


# ---------------------------------------------------------------- 闸门：图校验

def test_graph_validation_failure_fails(monkeypatch):
    _patch_compiler(monkeypatch, _FakeCompilerResult(
        "READY", graph={"nodes": [{"id": "x"}], "end": {}}))
    import components.construction.logic_graph as LG
    monkeypatch.setattr(LG, "validate_graph", lambda g: ["节点 x 缺 kind"])

    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    rep = p.run(draft={"nodes": [{"id": "x"}]})
    assert rep.state == Stage.FAILED
    assert rep.failure["stage"] == Stage.GRAPH_VALIDATED


# ---------------------------------------------------------------- 闸门：最终化

def test_no_finalize_needed_records_skip():
    """无字段引用表达式时，不进入 NEEDS_UI_FINALIZE。"""
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    p.state = Stage.PLATFORM_VALIDATED
    p.report.needs_ui_finalize = []
    p._stage_finalize_expressions()
    assert p.state == Stage.PLATFORM_VALIDATED      # 没迁移
    assert any("无需 UI 最终化" in x for x in p.report.human_interventions)


def test_finalize_needed_without_finalizer_blocks():
    """★ 有需求但没最终化器 → 必须阻断，不能假装成功。"""
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    p.state = Stage.PLATFORM_VALIDATED
    p.report.needs_ui_finalize = ["br"]
    p._mid = "m1"
    with pytest.raises(StageFailed):
        p._stage_finalize_expressions()
    assert p.state == Stage.FAILED
    assert "未注入 ExpressionFinalizer" in p.report.failure["message"]


def test_finalizer_failure_blocks():
    class BadFin:
        def finalize_all(self, **kw):
            raise RuntimeError("抽屉打不开")

    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n",
                          finalizer=BadFin())
    p.state = Stage.PLATFORM_VALIDATED
    p.report.needs_ui_finalize = ["br"]
    p._mid = "m1"
    with pytest.raises(StageFailed):
        p._stage_finalize_expressions()
    assert p.state == Stage.FAILED


def test_finalizer_not_ok_blocks():
    class NotOkFin:
        def finalize_all(self, **kw):
            class R:
                ok = False
                problems = ["回读仍是占位"]
                evidence = []
                detail = {}
            return R()

    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n",
                          finalizer=NotOkFin())
    p.state = Stage.PLATFORM_VALIDATED
    p.report.needs_ui_finalize = ["br"]
    p._mid = "m1"
    with pytest.raises(StageFailed):
        p._stage_finalize_expressions()
    assert p.state == Stage.FAILED


def test_finalizer_ok_advances():
    class OkFin:
        def finalize_all(self, **kw):
            class R:
                ok = True
                problems = []
                evidence = ["ui:node=br"]
                detail = {"finalized": ["br"]}
            return R()

    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n",
                          finalizer=OkFin())
    p.state = Stage.PLATFORM_VALIDATED
    p.report.needs_ui_finalize = ["br"]
    p._mid = "m1"
    p._stage_finalize_expressions()
    assert p.state == Stage.UI_FINALIZED
    assert "ui:node=br" in p.report.evidence


# ---------------------------------------------------------------- 闸门：构建

def test_build_without_builder_fails():
    """★ 没注入构建器不能假装构建成功。"""
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    p.state = Stage.PUBLISHED
    p._mid = "m1"
    with pytest.raises(StageFailed):
        p._stage_build()
    assert p.state == Stage.FAILED
    assert "未注入构建器" in p.report.failure["message"]


def test_build_failure_recorded():
    class BadBuilder:
        def build(self, **kw):
            class R:
                ok = False
                problems = ["BUILD FAILED: compile error"]
                detail = {"log": "..."}
            return R()

    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n",
                          builder=BadBuilder())
    p.state = Stage.PUBLISHED
    p._mid = "m1"
    with pytest.raises(StageFailed):
        p._stage_build()
    assert p.state == Stage.FAILED
    assert "BUILD FAILED" in " ".join(p.report.failure["problems"])


def test_build_success_is_terminal_ok():
    class GoodBuilder:
        def build(self, **kw):
            class R:
                ok = True
                problems = []
                detail = {"status": "BUILD SUCCESS"}
            return R()

    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n",
                          builder=GoodBuilder())
    p.state = Stage.PUBLISHED
    p._mid = "m1"
    p._stage_build()
    assert p.state == Stage.BUILD_SUCCESS
    assert p.report.ok


# ---------------------------------------------------------------- 占位检测

def test_find_placeholder_detects_placeholder():
    import json
    inner = json.dumps({"designData": {"tokens": []},
                        "runtimeData": {"executableExpr": "__NEEDS_UI_FINALIZE__"}})
    schema = json.dumps({"nodes": [
        {"nodeId": "B", "caption": "判断",
         "conditions": [{"expression": {"title": "t", "schema": inner}}]}]})
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    bad = p._find_placeholder(schema)
    assert bad and "__NEEDS_UI_FINALIZE__" in bad[0]


def test_find_placeholder_detects_empty():
    import json
    inner = json.dumps({"designData": {"tokens": []}, "runtimeData": {"executableExpr": ""}})
    schema = json.dumps({"nodes": [
        {"nodeId": "B", "caption": "判断",
         "conditions": [{"expression": {"title": "t", "schema": inner}}]}]})
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    assert p._find_placeholder(schema)


def test_find_placeholder_passes_real_exec():
    import json
    inner = json.dumps({"designData": {"tokens": []},
                        "runtimeData": {"executableExpr": "entityIsNotNull(_A._A.f)"}})
    schema = json.dumps({"nodes": [
        {"nodeId": "B", "caption": "判断",
         "conditions": [{"expression": {"title": "t", "schema": inner}}]}]})
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    assert p._find_placeholder(schema) == []


def test_find_placeholder_walks_nested():
    """嵌套在循环/分支里的表达式也要查到。"""
    import json
    inner = json.dumps({"designData": {}, "runtimeData": {"executableExpr": "__NEEDS_UI_FINALIZE__"}})
    schema = json.dumps({"nodes": [
        {"nodeId": "FE", "type": "FOR_EACH", "nodes": [
            {"nodeId": "B2", "caption": "内层判断",
             "conditions": [{"expression": {"title": "t", "schema": inner}}]}]}]})
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    bad = p._find_placeholder(schema)
    assert bad and "内层判断" in bad[0]


# ---------------------------------------------------------------- 断点恢复

def test_resume_returns_next_stage():
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    # ★ 已 SAVED 之后必须带平台实况，否则按"读不到平台"处理
    assert p.resume_from({"state": Stage.SAVED, "platform_state": "DRAFT"}) \
        == Stage.PLATFORM_VALIDATED
    assert p.resume_from({"state": Stage.NEEDS_UI_FINALIZE,
                          "platform_state": "DRAFT"}) == Stage.UI_FINALIZED
    assert p.resume_from({"state": Stage.BUILD_SUCCESS}) == "DONE"


def test_resume_at_saved_without_platform_state_needs_human():
    """★ 已 SAVED 但读不到平台状态 → 交人工，不盲目前进。"""
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    assert p.resume_from({"state": Stage.SAVED}) == "NEED_HUMAN"


def test_resume_from_failed_is_not_auto_retry():
    """★ 失败态不自动重试，交人工判断。"""
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    assert p.resume_from({"state": Stage.FAILED}) == "NEED_HUMAN"
    assert p.resume_from({"state": Stage.BLOCKED}) == "NEED_HUMAN"


def test_resume_from_unknown_starts_over():
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    assert p.resume_from({"state": "WHATEVER"}) == "RESTART"
    assert p.resume_from({}) == "RESTART"


# ---------------------------------------------------------------- $input 识别

def test_uses_flow_input_detects_forms():
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    assert p._uses_flow_input({"nodes": [{"id": "a", "input": "$input"}]})
    assert p._uses_flow_input({"nodes": [{"id": "a", "by_id_from": {"ref": "$input"}}]})
    assert not p._uses_flow_input({"nodes": [{"id": "a", "const": 1}]})


# ---------------------------------------------------------------- P7-E2E-1 追踪
def test_execution_id_auto_generated_on_run(monkeypatch):
    _patch_compiler(monkeypatch, _FakeCompilerResult(
        "BLOCKED", issues=[_FakeIssue("实体不存在")]))
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n")
    rep = p.run(draft={"nodes": []})
    assert rep.execution_id.startswith("e2e-")
    assert len(rep.execution_id) > 10


def test_execution_id_passed_through(monkeypatch):
    _patch_compiler(monkeypatch, _FakeCompilerResult(
        "BLOCKED", issues=[_FakeIssue("x")]))
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n",
                          execution_id="e2e-fixed-0001")
    rep = p.run(draft={"nodes": []})
    assert rep.execution_id == "e2e-fixed-0001"


def test_dump_writes_full_trace(tmp_path):
    import json
    p = MicroflowPipeline(host="h", cookie="c", app_id="a", app_name="n",
                          execution_id="e2e-trace-001")
    p.report.state = Stage.BUILD_SUCCESS
    p.report.original_draft = {"nodes": [{"id": "ra"}]}
    p.report.normalized_draft = {"nodes": [{"id": "ra", "entity": "真名"}]}
    p.report.node_id_mapping = {"ra": "RETRIEVE_ARRAY_abc123"}
    path = p.dump(str(tmp_path / "report.json"))
    d = json.load(open(path, encoding="utf-8"))
    assert d["execution_id"] == "e2e-trace-001"
    assert d["node_id_mapping"]["ra"] == "RETRIEVE_ARRAY_abc123"
    assert d["original_draft"]["nodes"][0]["id"] == "ra"
    assert d["normalized_draft"]["nodes"][0]["entity"] == "真名"
