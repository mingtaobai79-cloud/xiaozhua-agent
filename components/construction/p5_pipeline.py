"""P5.1 微流程全自动交付编排器（Pipeline Orchestrator）。

★ 本模块**只做编排**，不重新实现任何已有能力：
    - 需求编译      → components/construction/requirement_compiler.py
    - 图校验        → components/construction/logic_graph.validate_graph
    - 图执行        → components/construction/logic_graph.LogicGraphRunner
    - 保存/校验     → components/udc/microflow/save_pipeline.run_pipeline
    - 发布/构建     → components/udc/microflow/deploy.py
    - 表达式最终化  → p5_finalizer.ExpressionFinalizer（独立适配器，CDP）

设计原则（P5 任务书）：

1. **阶段状态显式**，不允许把函数串起来就交付。
2. **NEEDS_UI_FINALIZE 不是成功状态**——不完成就不能进最终交付。
3. **断点恢复基于平台真实状态**，不能盲目重跑。
4. **失败不静默**：每阶段有输入、输出、证据。
5. BLOCKED 时禁止继续构造。

状态流转（合法迁移，非法迁移直接抛错）：

    DRAFT_READY → GRAPH_VALIDATED → CONSTRUCTED → SAVED
    → PLATFORM_VALIDATED → [NEEDS_UI_FINALIZE → UI_FINALIZED]
    → READBACK_VERIFIED → PUBLISHED → BUILD_SUCCESS

任意阶段可迁到 FAILED / BLOCKED（终态）。
"""

from __future__ import annotations

import dataclasses as dc
import time
from typing import Any, Callable

# ---------------------------------------------------------------- 阶段与状态


class Stage:
    """阶段名常量（字符串常量而非 Enum，便于 JSON 落盘与跨进程恢复）。"""

    DRAFT_READY = "DRAFT_READY"
    GRAPH_VALIDATED = "GRAPH_VALIDATED"
    CONSTRUCTED = "CONSTRUCTED"
    SAVED = "SAVED"
    PLATFORM_VALIDATED = "PLATFORM_VALIDATED"
    NEEDS_UI_FINALIZE = "NEEDS_UI_FINALIZE"
    UI_FINALIZED = "UI_FINALIZED"
    READBACK_VERIFIED = "READBACK_VERIFIED"
    PUBLISHED = "PUBLISHED"
    BUILD_SUCCESS = "BUILD_SUCCESS"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"

    #: 线性主序（用于「从哪继续」的判断）
    ORDER = (
        DRAFT_READY, GRAPH_VALIDATED, CONSTRUCTED, SAVED,
        PLATFORM_VALIDATED, NEEDS_UI_FINALIZE, UI_FINALIZED,
        READBACK_VERIFIED, PUBLISHED, BUILD_SUCCESS,
    )
    TERMINAL = (BUILD_SUCCESS, BLOCKED, FAILED)


#: 合法迁移表。★ 显式列出，拒绝"想跳就跳"。
ALLOWED = {
    None: {Stage.DRAFT_READY, Stage.BLOCKED, Stage.FAILED},
    Stage.DRAFT_READY: {Stage.GRAPH_VALIDATED, Stage.BLOCKED, Stage.FAILED},
    Stage.GRAPH_VALIDATED: {Stage.CONSTRUCTED, Stage.BLOCKED, Stage.FAILED},
    Stage.CONSTRUCTED: {Stage.SAVED, Stage.FAILED},
    Stage.SAVED: {Stage.PLATFORM_VALIDATED, Stage.FAILED},
    Stage.PLATFORM_VALIDATED: {Stage.NEEDS_UI_FINALIZE, Stage.READBACK_VERIFIED,
                               Stage.FAILED},
    Stage.NEEDS_UI_FINALIZE: {Stage.UI_FINALIZED, Stage.FAILED},
    Stage.UI_FINALIZED: {Stage.READBACK_VERIFIED, Stage.FAILED},
    Stage.READBACK_VERIFIED: {Stage.PUBLISHED, Stage.FAILED},
    Stage.PUBLISHED: {Stage.BUILD_SUCCESS, Stage.FAILED},
    Stage.BUILD_SUCCESS: set(),
    Stage.BLOCKED: set(),
    Stage.FAILED: set(),
}


class PipelineError(RuntimeError):
    """编排层错误（非法迁移、跳过闸门等）。"""


class StageFailed(RuntimeError):
    """阶段执行失败，携带阶段名与原始异常。"""

    def __init__(self, stage: str, message: str, *, cause: Exception | None = None):
        super().__init__("[%s] %s" % (stage, message))
        self.stage = stage
        self.message = message
        self.cause = cause


# ---------------------------------------------------------------- 记录结构


@dc.dataclass
class StageRecord:
    """单个阶段的执行记录（可序列化，用于断点恢复与报告）。"""

    stage: str
    ok: bool
    started_at: float = 0.0
    ended_at: float = 0.0
    detail: dict = dc.field(default_factory=dict)
    problems: list[str] = dc.field(default_factory=list)
    error: str = ""

    @property
    def elapsed(self) -> float:
        if not self.ended_at:
            return 0.0
        return round(self.ended_at - self.started_at, 2)

    def to_dict(self) -> dict:
        return {"stage": self.stage, "ok": self.ok, "elapsed": self.elapsed,
                "detail": self.detail, "problems": self.problems,
                "error": self.error}


@dc.dataclass
class DeliveryReport:
    """交付报告（P5.4）。★ 结构化，含证据引用。"""

    app_id: str = ""
    app_name: str = ""
    flow_name: str = ""
    flow_caption: str = ""
    mid: str = ""
    requirement_summary: str = ""
    compile_status: str = ""
    graph: dict | None = None
    state: str = ""
    stages: list[StageRecord] = dc.field(default_factory=list)
    needs_ui_finalize: list[str] = dc.field(default_factory=list)
    platform_checks: dict = dc.field(default_factory=dict)
    build: dict = dc.field(default_factory=dict)
    failure: dict = dc.field(default_factory=dict)
    human_interventions: list[str] = dc.field(default_factory=list)
    evidence: list[str] = dc.field(default_factory=list)
    started_at: float = dc.field(default_factory=time.time)
    ended_at: float = 0.0
    # —— P7-E2E-1 全链路追踪新增 ——
    execution_id: str = ""                 # 贯穿 original→draft→graph→build→run→db 的统一 id
    original_draft: dict = dc.field(default_factory=dict)
    normalized_draft: dict = dc.field(default_factory=dict)
    resolution_report: dict = dc.field(default_factory=dict)
    node_id_mapping: dict = dc.field(default_factory=dict)  # 业务别名 → 平台 nodeId
    run: dict = dc.field(default_factory=dict)              # 运行结果
    db_assertions: list = dc.field(default_factory=list)    # 数据库断言

    @property
    def ok(self) -> bool:
        """★ 只有 BUILD_SUCCESS 才算交付成功。
        NEEDS_UI_FINALIZE / PUBLISHED 都不算。"""
        return self.state == Stage.BUILD_SUCCESS

    def stage(self, name: str) -> StageRecord | None:
        for s in self.stages:
            if s.stage == name:
                return s
        return None

    def to_dict(self) -> dict:
        return {
            "app_id": self.app_id, "app_name": self.app_name,
            "flow_name": self.flow_name, "flow_caption": self.flow_caption,
            "mid": self.mid,
            "requirement_summary": self.requirement_summary,
            "compile_status": self.compile_status,
            "graph": self.graph,
            "state": self.state,
            "ok": self.ok,
            "elapsed": round((self.ended_at or time.time()) - self.started_at, 2),
            "stages": [s.to_dict() for s in self.stages],
            "needs_ui_finalize": self.needs_ui_finalize,
            "platform_checks": self.platform_checks,
            "build": self.build,
            "failure": self.failure,
            "human_interventions": self.human_interventions,
            "evidence": self.evidence,
            "execution_id": self.execution_id,
            "original_draft": self.original_draft,
            "normalized_draft": self.normalized_draft,
            "resolution_report": self.resolution_report,
            "node_id_mapping": self.node_id_mapping,
            "run": self.run,
            "db_assertions": self.db_assertions,
        }


# ---------------------------------------------------------------- 编排器


class MicroflowPipeline:
    """微流程全自动交付编排器。

    用法：

        pipe = MicroflowPipeline(host=..., cookie=..., app_id=..., app_name=...,
                                 live_refs=lr, backend=be)
        report = pipe.run(draft={...}, text="业务需求原文",
                          flow_name="autoFlow", flow_caption="自动流程")

    断点恢复：

        report = pipe.resume(report_path="...json")   # 从记录状态继续

    ★ 所有平台副作用（建流程/发布/构建）都在 save_pipeline / deploy 里，
      本类只负责「什么时候调、调完怎么判、失败了怎么记」。
    """

    def __init__(self, *, host: str, cookie: str, app_id: str, app_name: str,
                 live_refs=None, backend=None, group_id: str = "",
                 finalizer=None, builder=None, execution_id: str = ""):
        self.host = host
        self.cookie = cookie
        self.app_id = app_id
        self.app_name = app_name
        self.lr = live_refs
        self.be = backend
        self.group_id = group_id
        # 可选注入：表达式最终化器 / 构建器（便于单测与替换实现）
        self.finalizer = finalizer
        self.builder = builder

        self.state: str | None = None
        self.report = DeliveryReport(app_id=app_id, app_name=app_name,
                                     execution_id=execution_id)
        self._graph: dict | None = None
        self._schema: dict | None = None
        self._mid: str | None = None
        self._ref_resolver = None   # 构造阶段的引用解析器（含 alias→node 映射）
        self._trigger_type_value = "MANUAL"
        self._schedule_config: dict = {}
        self._skip_l2 = False

    # ---------------- 状态机 ----------------
    def _advance(self, to: str, *, detail: dict | None = None,
                 problems: list[str] | None = None, error: str = "",
                 ok: bool = True) -> StageRecord:
        """迁移到指定阶段并落一条记录。非法迁移直接抛 PipelineError。"""
        allowed = ALLOWED.get(self.state, set())
        if to not in allowed:
            raise PipelineError(
                "非法阶段迁移 %r → %r（允许：%s）"
                % (self.state, to, sorted(allowed) or "无（终态）"))
        rec = StageRecord(stage=to, ok=ok, started_at=time.time(),
                          detail=detail or {}, problems=list(problems or []),
                          error=error)
        rec.ended_at = time.time()
        self.report.stages.append(rec)
        self.state = to
        self.report.state = to
        return rec

    def _fail(self, stage: str, message: str, *, problems=None) -> None:
        """失败落记录。★ 失败也要走状态机，不能静默。

        两种情形：
          - 当前状态 == stage（同阶段失败）：不迁移，只记失败证据；
          - 其他：迁移到 FAILED。
        无论哪种，report.failure 一定被写入，state 一定进终态。
        """
        problems = list(problems or [])
        rec = StageRecord(stage=stage, ok=False, started_at=time.time(),
                          problems=problems, error=message)
        rec.ended_at = time.time()
        self.report.stages.append(rec)
        self.report.failure = {"stage": stage, "message": message,
                               "problems": problems}
        # ★ 无论当前在哪个阶段，失败一律进 FAILED 终态，
        #   不能停留在 NEEDS_UI_FINALIZE 这种半完成状态。
        self.state = Stage.FAILED
        self.report.state = Stage.FAILED
        raise StageFailed(stage, message)

    # ---------------- 主流程 ----------------
    def run(self, *, draft: dict, text: str = "",
            flow_name: str = "", flow_caption: str = "",
            require_build: bool = True, keep: bool = False,
            trigger_type: str = "MANUAL", schedule: dict | None = None,
            skip_l2: bool = False) -> DeliveryReport:
        """从草稿一路跑到 BUILD_SUCCESS。

        参数：
            draft       : 宿主 LLM 已结构化的业务草稿（★ 本模块不调 LLM）
            text        : 原始需求原文，用于歧义扫描
            require_build: True 才做发布+构建；False 停在 READBACK_VERIFIED
                           （用于只验构造/保存的场景）
            keep        : 是否保留验证流（默认删，避免污染应用）
            trigger_type: MANUAL / SCHEDULE / EVENT / MQ（决定触发器形态）
            schedule    : SCHEDULE 触发器的周期配置
                          {job_caption, cycle_type, rotation_type, value}
            skip_l2     : True 跳过 L2 页面状态读取（CDP 依赖；定时任务流程
                          的编辑器页面不稳定，且 L2 非业务结果正确性核心）
        """
        self._trigger_type_value = trigger_type
        self._schedule_config = schedule or {}
        self._skip_l2 = skip_l2
        self.report.flow_name = flow_name
        self.report.flow_caption = flow_caption
        self.report.requirement_summary = text or ""
        if not self.report.execution_id:
            import uuid
            self.report.execution_id = "e2e-%s" % uuid.uuid4().hex[:12]

        try:
            self._stage_draft(draft)
            self._stage_validate()
            self._stage_construct()
            self._stage_save(keep=keep)
            self._stage_platform_validate()
            self._stage_finalize_expressions()
            self._stage_readback()
            if require_build:
                self._stage_publish()
                self._stage_build()
            else:
                self.report.human_interventions.append(
                    "require_build=False：未发布/未构建，交付未完成")
        except StageFailed as e:
            # 已由 _fail 落记录
            if self.state not in Stage.TERMINAL:
                self.state = Stage.FAILED
                self.report.state = Stage.FAILED
            self.report.ended_at = time.time()
            return self.report
        self.report.ended_at = time.time()
        return self.report

    # ---------------- 各阶段 ----------------
    def _stage_draft(self, draft: dict) -> None:
        from components.construction.requirement_compiler import (
            BusinessRequirementCompiler)

        comp = BusinessRequirementCompiler(self.lr)
        res = comp.compile(draft, app_id=self.app_id, app_name=self.app_name,
                           text=self.report.requirement_summary)
        self.report.compile_status = res.status
        self.report.graph = res.graph

        if res.status == "BLOCKED":
            # ★ BLOCKED 禁止继续构造（任务书硬要求）
            self._advance(Stage.DRAFT_READY, ok=False,
                          detail={"compile_status": res.status,
                                  "issues": [i.to_dict() for i in res.issues]})
            msgs = [i.message for i in res.issues]
            self.report.failure = {"stage": Stage.DRAFT_READY,
                                   "message": "编译 BLOCKED",
                                   "problems": msgs[:10]}
            self._advance(Stage.BLOCKED, ok=False, problems=msgs[:10])
            raise StageFailed("DRAFT_READY", "编译 BLOCKED：%s" % (msgs[:3],))
        if res.status == "AMBIGUOUS":
            self._advance(Stage.DRAFT_READY, ok=False,
                          detail={"compile_status": res.status,
                                  "issues": [i.to_dict() for i in res.issues]})
            msgs = ["AMBIGUOUS: " + i.message for i in res.issues]
            self.report.failure = {"stage": Stage.DRAFT_READY,
                                   "message": "编译 AMBIGUOUS，需人工拍板",
                                   "problems": msgs[:10]}
            self._advance(Stage.BLOCKED, ok=False, problems=msgs[:10])
            raise StageFailed("DRAFT_READY",
                              "编译 AMBIGUOUS，需人工拍板：%s"
                              % ([i.message for i in res.issues][:3],))

        self._graph = res.graph
        # ★ 归一化阶段产物：原始草稿 / 归一化草稿 / 解析映射，全链路可追踪
        self.report.original_draft = getattr(res, "original_draft", None) or {}
        self.report.normalized_draft = getattr(res, "normalized_draft", None) or {}
        self.report.resolution_report = res.resolved
        self._advance(Stage.DRAFT_READY, detail={
            "compile_status": res.status,
            "fixes": res.fixes,
            "resolved": res.resolved,
        })

    def _stage_validate(self) -> None:
        from components.construction.logic_graph import validate_graph

        try:
            problems = validate_graph(self._graph) or []
        except Exception as e:
            self._fail(Stage.GRAPH_VALIDATED, "图校验异常: %s" % e)
            return
        if problems:
            self._fail(Stage.GRAPH_VALIDATED, "图校验未通过", problems=problems[:10])
        self._advance(Stage.GRAPH_VALIDATED, detail={"node_count":
                                                     len(self._graph.get("nodes") or [])})

    def _stage_construct(self) -> None:
        from components.construction.microflow_composer import MicroflowComposer
        from components.construction.logic_graph import LogicGraphRunner
        from components.construction.node_builder import NodeBuilder
        from components.construction.microflow_params import make_trigger_entity

        try:
            b = NodeBuilder(app_id=self.app_id, app_name=self.app_name)
            mc = MicroflowComposer(b, self.lr, app_id=self.app_id,
                                   app_name=self.app_name)
            # 触发方式跟图走：有 $input 用 ENTITY_OBJECT，否则 NONE
            trig = self._make_trigger(mc)
            mc.trigger = trig
            ref_resolver = self._resolver()
            self._ref_resolver = ref_resolver
            runner = LogicGraphRunner(mc, resolver=ref_resolver, backend=self.be)
            schema = runner.run(self._graph)
        except Exception as e:
            self._fail(Stage.CONSTRUCTED, "构造失败: %s" % e)
            return
        self._schema = schema
        # ★ 业务别名 → 平台 nodeId 映射（ReferenceResolver._aliases 是唯一来源）
        aliases = getattr(self._ref_resolver, "_aliases", {}) or {}
        self.report.node_id_mapping = {
            alias: (node.get("nodeId") if isinstance(node, dict) else None)
            for alias, node in aliases.items()}
        # ★ 含字段引用的表达式要标记出来，供最终化阶段处理
        self.report.needs_ui_finalize = list(getattr(runner, "needs_ui_finalize", []) or [])
        self._advance(Stage.CONSTRUCTED, detail={
            "node_count": len(schema.get("nodes") or []),
            "needs_ui_finalize": self.report.needs_ui_finalize,
            "node_id_mapping": self.report.node_id_mapping,
            "advisories": list(mc.advisories),
        })

    def _make_trigger(self, mc):
        """按图里是否用 $input 决定触发入参形态；SCHEDULE 走定时触发器。"""
        if self._trigger_type_value == "SCHEDULE":
            cfg = self._schedule_config
            return mc.trigger_schedule(
                job_caption=cfg.get("job_caption") or self.report.flow_caption
                or "定时任务",
                cycle_type=cfg.get("cycle_type") or "SIMPLE",
                rotation_type=cfg.get("rotation_type") or "MINUTE",
                value=cfg.get("value") or "5")
        if not self._uses_flow_input(self._graph):
            return mc.trigger_manual(param_type="NONE")
        em = self._entity_of_graph()
        if em is None:
            return mc.trigger_manual(param_type="NONE")
        from components.construction.microflow_params import make_trigger_entity
        trig, _inp = make_trigger_entity(self.app_id, self.app_name, em,
                                         desc="流程入参")
        return trig

    def _uses_flow_input(self, graph: dict) -> bool:
        def walk(o) -> bool:
            if isinstance(o, dict):
                if o.get("input") == "$input" or o.get("ref") == "$input":
                    return True
                if o.get("source") == "$input":
                    return True
                return any(walk(v) for v in o.values())
            if isinstance(o, list):
                return any(walk(v) for v in o)
            return False
        return walk(graph.get("nodes") or [])

    def _entity_of_graph(self):
        """图里第一个实体的模型（用于 $input 入参）。"""
        if self.lr is None:
            return None
        for n in self._graph.get("nodes") or []:
            ent = n.get("entity")
            if ent:
                try:
                    return self.lr.entity_model(self.app_id, self.app_name, label=ent)
                except Exception:
                    return None
        return None

    def _resolver(self):
        from components.udc.microflow.expression_refs import ReferenceResolver
        r = ReferenceResolver(self.app_id, self.app_name, live_refs=self.lr)
        return r

    def _stage_save(self, *, keep: bool) -> None:
        from components.udc.microflow.save_pipeline import run_pipeline

        name = self.report.flow_name or ("auto%d" % int(time.time()))
        caption = self.report.flow_caption or name
        try:
            out = run_pipeline(host=self.host, cookie=self.cookie,
                               app_id=self.app_id, app_name=self.app_name,
                               schema=self._schema, name=name, caption=caption,
                               group_id=self.group_id, keep=keep, l2=False,
                               backend=self.be)
        except Exception as e:
            self._fail(Stage.SAVED, "保存链异常: %s" % e)
            return
        self._mid = out.get("mid")
        self.report.mid = self._mid or ""
        self.report.platform_checks["save"] = {
            "ok": out.get("ok"), "state": out.get("state"),
            "stages": [s.as_dict() if hasattr(s, "as_dict") else s
                       for s in (out.get("stages") or [])],
        }
        if not out.get("ok"):
            self._fail(Stage.SAVED, "保存失败 state=%s" % out.get("state"),
                       problems=out.get("problems") or [])
        self._advance(Stage.SAVED, detail={"mid": self._mid, "state": out.get("state")})

    def _stage_platform_validate(self) -> None:
        """L2 整体状态读取（L3 定向抽屉按需，不在默认链里跑）。"""
        from components.udc.microflow.save_pipeline import l2_check

        if getattr(self, "_skip_l2", False):
            self.report.human_interventions.append(
                "skip_l2=True：跳过 L2 页面状态读取（CDP 依赖，非业务结果核心）")
            self._advance(Stage.PLATFORM_VALIDATED,
                          detail={"l2": "skipped"})
            return
        if not self._mid:
            self._fail(Stage.PLATFORM_VALIDATED, "没有 mid，无法做 L2")
        try:
            r = l2_check(self.app_id, self._mid, self.host, cookie=self.cookie)
        except TypeError:
            # 兼容不同签名
            r = l2_check(self.app_id, self._mid, self.host)
        except Exception as e:
            self._fail(Stage.PLATFORM_VALIDATED, "L2 异常: %s" % e)
            return
        ok = bool(getattr(r, "ok", False))
        self.report.platform_checks["l2"] = {
            "ok": ok,
            "detail": getattr(r, "detail", {}),
            "problems": getattr(r, "problems", []),
        }
        if not ok:
            self._fail(Stage.PLATFORM_VALIDATED, "L2 未通过",
                       problems=getattr(r, "problems", [])[:10])
        self._advance(Stage.PLATFORM_VALIDATED, detail=self.report.platform_checks["l2"])

    def _stage_finalize_expressions(self) -> None:
        """表达式最终化（P5.2）。

        ★ 没有 needs_ui_finalize 时**直接跳过**（正常流程）；
          有则必须真做，做完才能 READBACK_VERIFIED。
        ★ NEEDS_UI_FINALIZE 不是成功状态。
        """
        if not self.report.needs_ui_finalize:
            self.report.human_interventions.append(
                "无需 UI 最终化（无字段引用表达式）")
            return
        if self.finalizer is None:
            # 有需要但没注入最终化器 → 必须阻断，不能假装成功
            self._advance(Stage.NEEDS_UI_FINALIZE, ok=False,
                          detail={"nodes": self.report.needs_ui_finalize})
            self._fail(Stage.NEEDS_UI_FINALIZE,
                       "存在 %d 个待最终化表达式，但未注入 ExpressionFinalizer"
                       % len(self.report.needs_ui_finalize),
                       problems=self.report.needs_ui_finalize)

        self._advance(Stage.NEEDS_UI_FINALIZE,
                      detail={"nodes": self.report.needs_ui_finalize})
        try:
            res = self.finalizer.finalize_all(
                mid=self._mid, schema=self._schema,
                aliases=self.report.needs_ui_finalize)
        except Exception as e:
            self._fail(Stage.NEEDS_UI_FINALIZE, "最终化异常: %s" % e)
            return
        if not getattr(res, "ok", False):
            self._fail(Stage.NEEDS_UI_FINALIZE, "最终化未通过",
                       problems=getattr(res, "problems", [])[:10])
        self.report.evidence.extend(getattr(res, "evidence", []) or [])
        self._advance(Stage.UI_FINALIZED, detail=getattr(res, "detail", {}))

    def _stage_readback(self) -> None:
        """回读确认最终数据（★ 表达式最终化后必须重新读）。"""
        from components.udc.microflow import deploy as DP

        if not self._mid:
            self._fail(Stage.READBACK_VERIFIED, "没有 mid，无法回读")
        try:
            back = DP.get(self.host, self.cookie, self._mid)
        except Exception as e:
            self._fail(Stage.READBACK_VERIFIED, "回读异常: %s" % e)
            return
        state = back.get("state")
        self.report.platform_checks["readback"] = {"state": state}
        if state not in ("RELEASE", "DRAFT"):
            self._fail(Stage.READBACK_VERIFIED, "回读 state 异常: %r" % state)
        # ★ 有最终化需求时，必须确认占位串已消失
        if self.report.needs_ui_finalize:
            bad = self._find_placeholder(back.get("dataSchema") or "{}")
            if bad:
                self._fail(Stage.READBACK_VERIFIED,
                           "回读发现占位 executableExpr 未消除",
                           problems=bad[:10])
        self._advance(Stage.READBACK_VERIFIED, detail={"state": state})

    def _find_placeholder(self, data_schema: str) -> list[str]:
        """回读 schema 里是否还有占位 executableExpr。"""
        import json as _json
        try:
            sc = _json.loads(data_schema)
        except Exception:
            return ["dataSchema 无法解析"]
        bad = []

        def walk(nodes):
            for n in nodes or []:
                for c in (n.get("conditions") or []):
                    s = (c.get("expression") or {}).get("schema")
                    if not s:
                        continue
                    try:
                        dd = _json.loads(s)
                    except Exception:
                        continue
                    ee = (dd.get("runtimeData") or {}).get("executableExpr") or ""
                    if not ee or ee == "__NEEDS_UI_FINALIZE__":
                        bad.append("%s: executableExpr=%r"
                                   % (n.get("caption") or n.get("nodeId"), ee))
                walk(n.get("nodes"))
        walk(sc.get("nodes"))
        return bad

    def _stage_publish(self) -> None:
        from components.udc.microflow import deploy as DP

        try:
            ok, info = DP.publish(
                self.host, self.cookie, self._mid, app_id=self.app_id,
                schema=self._schema, name=self.report.flow_name,
                caption=self.report.flow_caption, group_id=self.group_id,
                trigger_type=self._trigger_type())
        except Exception as e:
            self._fail(Stage.PUBLISHED, "发布异常: %s" % e)
            return
        if not ok:
            errs = (info or {}).get("errors") or []
            self._fail(Stage.PUBLISHED, "发布被拒",
                       problems=["%s %s" % (e.get("nodeCaption"), e.get("errorCode"))
                                 for e in errs][:10])
        self.report.platform_checks["publish"] = {"ok": True}
        self._advance(Stage.PUBLISHED, detail={"mid": self._mid})

    def _trigger_type(self) -> str:
        return getattr(self, "_trigger_type_value", "MANUAL")

    def _stage_build(self) -> None:
        """发布后构建（页面测试对应的构建接口 + 轮询 + backBuild.log）。"""
        if self.builder is None:
            # 没注入构建器：★ 不能假装成功
            self._fail(Stage.BUILD_SUCCESS,
                       "未注入构建器，无法验证构建（不允许把构建当成已完成）")
        try:
            res = self.builder.build(app_id=self.app_id, mid=self._mid)
        except TypeError:
            res = self.builder.build()
        except Exception as e:
            self._fail(Stage.BUILD_SUCCESS, "构建异常: %s" % e)
            return
        ok = bool(getattr(res, "ok", False))
        detail = getattr(res, "detail", None)
        self.report.build = detail if isinstance(detail, dict) else (res.to_dict()
                                                                    if hasattr(res, "to_dict") else {})
        if not ok:
            self._fail(Stage.BUILD_SUCCESS, "构建失败 state=%s"
                       % getattr(res, "state", "?"),
                       problems=getattr(res, "problems", [])[:10])
        self._advance(Stage.BUILD_SUCCESS, detail=self.report.build)

    # ---------------- 落盘与追踪 ----------------
    def dump(self, path: str) -> str:
        """把完整交付报告（含 execution_id 全链路追踪字段）落盘 JSON。

        返回写入的绝对路径。落盘内容 = report.to_dict()：original_draft /
        normalized_draft / resolution_report / graph / node_id_mapping /
        build / run / db_assertions 全部在同一个 execution_id 下。
        """
        import json as _json
        import os
        data = self.report.to_dict()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            _json.dump(data, f, ensure_ascii=False, indent=2)
        return os.path.abspath(path)

    # ---------------- 断点恢复 ----------------
    def resume_from(self, saved: dict) -> str:
        """从已保存的报告字典恢复，返回「下一步该做什么」。

        返回值：
            "DONE"              已完成
            "NEED_HUMAN"        失败/阻断/状态冲突，交人工
            "RESTART"           从头开始
            某个阶段名          从该阶段继续

        ★ 只算「下一步该做什么」，**不**代替平台状态检查：
          真正重入前必须核对平台（mid 是否还在、state 是什么）。
        """
        from .p5_report import plan_resume
        plan = plan_resume(saved,
                           platform_state=saved.get("platform_state"))
        if plan["action"] == "RESUME":
            return plan["from_stage"]
        return plan["action"]


def build_pipeline(*, host: str, cookie: str, app_id: str, app_name: str,
                   live_refs=None, backend=None, group_id: str = "",
                   cdp=None, node_caption: dict | None = None,
                   report_dir: str = "", poll_interval: float = 10.0,
                   timeout_s: float = 900.0, probe_only: bool = False):
    """工厂：按生产配置装配一条完整流水线（编排器 + 最终化器 + 构建器）。

    ★ 只在这里做依赖装配，各组件之间仍是接口协作。
    """
    from components.construction.p5_builder import PlatformBuilder, attach_semantics
    from components.construction.p5_cdp_driver import (
        CdpDesignerDriver, read_schema_via_api)
    from components.construction.p5_finalizer import ExpressionFinalizer

    # 构建器：需要一个 post_json/get_json 的 HTTP 封装
    http = _HttpAdapter(host=host, cookie=cookie)
    builder = PlatformBuilder(http=http, app_id=app_id,
                              poll_interval=poll_interval, timeout_s=timeout_s)

    finalizer = None
    if cdp is not None:
        driver = CdpDesignerDriver(cdp, node_caption=node_caption,
                                   probe_only=probe_only)
        finalizer = ExpressionFinalizer(
            driver=driver, read_schema=read_schema_via_api(host, cookie))

    return MicroflowPipeline(host=host, cookie=cookie, app_id=app_id,
                             app_name=app_name, live_refs=live_refs,
                             backend=backend, group_id=group_id,
                             finalizer=finalizer, builder=builder)


class _HttpAdapter:
    """把平台 REST 调用包成 post_json/get_json（PlatformBuilder 需要）。"""

    def __init__(self, *, host: str, cookie: str, timeout: float = 60.0):
        self.host = host.rstrip("/")
        self.cookie = cookie
        self.timeout = timeout

    def _call(self, method: str, path: str, body=None) -> dict:
        import json as _json
        import subprocess
        url = self.host + path if path.startswith("/") else "%s/%s" % (self.host, path)
        cmd = ["curl", "-s", "-X", method, url,
               "-H", "Cookie: %s" % self.cookie,
               "-H", "Content-Type: application/json",
               "--max-time", str(int(self.timeout))]
        if body is not None:
            cmd += ["-d", _json.dumps(body, ensure_ascii=False)]
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        try:
            return _json.loads(r.stdout or "{}")
        except Exception:
            return {"code": "PARSE_FAIL", "message": (r.stdout or "")[:300]}

    def post_json(self, path: str, body) -> dict:
        return self._call("POST", path, body)

    def get_json(self, path: str) -> dict:
        return self._call("GET", path)
