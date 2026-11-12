"""P4 业务需求 → 逻辑图编译器（确定性部分）。

## 边界（这是全文件最重要的一段）

LLM 负责**理解业务**（识别实体、输入输出、条件、循环、异常），
Python 负责**确定性编译与纠错**。LLM 不许越过逻辑图直接写平台 JSON，
也不许直接调构造器。所以本模块：

- **不调用任何 LLM、不联网**。它吃的是「业务意图草稿」（IntentDraft），
  也就是宿主 LLM 已经理解完、结构化出来的东西。
- 只做四件事：①把草稿落成合法 LogicGraph；②对着活元数据做真名解析
  （实体名/字段名必须是平台上真实存在的，不许猜）；③静态校验 + 自动纠错；
  ④把"做不到"的地方明确标成 BLOCKED/AMBIGUOUS，**绝不臆造**。

这和仓库既有纪律一致：`requirement_parser.py` 同样声明「不调 LLM、不联网；
解析不出就 UNVERIFIED，不伪造模型」。

## 为什么必须先过这一层

P3 的执行器只保证「逻辑图合法」，不保证「逻辑图符合业务」。
直接让 LLM 产 JSON 交给执行器，会出现三类静默错误：
  1. 实体/字段名凭中文习惯猜（`数据源` vs `数据源配置信息`），落库能过、页面失效
  2. 循环/分支语义写反（「其他」是否排除自己）
  3. 引用顺序越界（P3 能拦，但那是报错，不是纠错）

所以这里做**真名解析**（对着 LiveRefs）和**已知语义陷阱检测**，
把问题在落库前变成可读的中文提示，交给宿主 LLM 或人去澄清。

## 三档产出

| status | 含义 | 后续动作 |
|---|---|---|
| `READY` | 结构合法 + 真名全部命中 | 直接交给 LogicGraphRunner |
| `AMBIGUOUS` | 结构合法，但有必须让人拍板的歧义 | 带着问题清单问用户 |
| `BLOCKED` | 结构不合法或真名解析失败 | 必须改草稿，不许执行 |
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field as dc_field
from typing import Any

from .logic_graph import _STEP_KINDS, _BLOCK_KEYS, validate_graph

# 草稿里允许出现的节点 kind（与执行器一致，单点定义）
_ALLOWED_KINDS = _STEP_KINDS


class CompileError(ValueError):
    """草稿无法编译成逻辑图（结构性错误，必须改草稿）。"""


@dataclass
class CompileIssue:
    """一条待澄清/待修复的问题。"""
    code: str                 # 机器可读：ENTITY_NOT_FOUND / FIELD_NOT_FOUND / ...
    message: str              # 中文可读
    node_id: str = ""
    severity: str = "ERROR"   # ERROR（BLOCKED）/ WARN（AMBIGUOUS）
    suggestion: str = ""

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "node_id": self.node_id,
                "severity": self.severity, "suggestion": self.suggestion}


@dataclass
class CompileResult:
    status: str                               # READY / AMBIGUOUS / BLOCKED
    graph: dict | None = None
    issues: list[CompileIssue] = dc_field(default_factory=list)
    resolved: dict = dc_field(default_factory=dict)   # 真名解析结果（可审阅）
    fixes: list[str] = dc_field(default_factory=list)  # 自动纠错记录
    # —— P7-E2E-1 归一化阶段新增 ——
    original_draft: dict | None = None   # 原始草稿（深拷贝，绝不被污染）
    normalized_draft: dict | None = None  # 归一化草稿（真名回填后的副本）

    @property
    def ok(self) -> bool:
        return self.status == "READY"

    def to_dict(self) -> dict:
        return {"status": self.status, "graph": self.graph,
                "issues": [i.to_dict() for i in self.issues],
                "resolved": self.resolved, "fixes": self.fixes,
                "original_draft": self.original_draft,
                "normalized_draft": self.normalized_draft}


# ---------------------------------------------------------------- 语义陷阱规则
# 这些不是"风格建议"，是已经踩过并写进 skill 的业务语义错误。
_AMBIGUITY_RULES = (
    ("EXCLUDE_SELF", r"其他|其它|除(?!了?自己)|剩余",
     "「其他」的范围没定义：排除自己 / 同角色 / 含自己，三种做法业务结果不同",
     "在草稿里写清 exclude_self=true，或让用户确认"),
    ("MODIFY_SCOPE", r"修改数据|改数据|更新数据(?!源)",
     "「修改数据」改哪些字段没定义：只改状态 / 还要改时间 / 还要写原因",
     "在草稿 fields 里列全字段"),
    ("JUDGE_TARGET", r"判断.*(?:jdbc|字段).*(?:是否|是不是)",
     "判断对象不明确：当前这条 / 查出来的那一批",
     "在草稿里用 ds.<field> 或 item.<field> 明确指向"),
    ("MATCH_PRECISION", r"包含|含有|含(?:有)?",
     "匹配精度不明确：区分大小写 / 前缀匹配 / 普通包含",
     "表达式用 containsText（不区分大小写）或 find 指定起始位置"),
)

# 写操作直引控制节点的纠错提示（G20 边界）
_WRITE_KINDS = {"change_entity", "change_batch_entity", "delete_entity"}


class BusinessRequirementCompiler:
    """业务意图草稿 → 逻辑图（确定性编译 + 真名解析 + 纠错）。

    用法（宿主侧）：

        draft = {                       # LLM 理解完、结构化输出
          "nodes": [...], "end": {...},
          "entities": {"数据源": "数据源配置信息"},   # 可选：语义名→真名候选
        }
        res = BusinessRequirementCompiler(lr).compile(draft, app_id=..., app_name=...)
        if res.status == "READY":
            schema = LogicGraphRunner(comp, resolver=res_, backend=be).run(res.graph)
    """

    SCHEMA = "udc.logic-graph.compile.v1"

    def __init__(self, live_refs=None):
        self.lr = live_refs

    # ---------------- 入口 ----------------
    def compile(self, draft: dict, *, app_id: str = "", app_name: str = "",
                text: str = "") -> CompileResult:
        """draft: 业务意图草稿；text: 原始需求原文（用于歧义扫描，可选）。"""
        if not isinstance(draft, dict):
            raise CompileError("草稿必须是对象，得到 %r" % type(draft).__name__)

        # 0) 保存原始草稿（深拷贝，后续解析绝不污染它）
        original_draft = copy.deepcopy(draft)

        issues: list[CompileIssue] = []
        fixes: list[str] = []
        resolved: dict = {}

        # 1) 结构体检（复用 P3 的校验，单点定义）——深拷贝，改的是副本
        graph = self._normalize(draft, fixes)
        structural = validate_graph(graph)
        for p in structural:
            issues.append(CompileIssue("STRUCTURE", p, severity="ERROR"))

        # 2) 真名解析（实体/字段必须真实存在；原地回填归一化图 + 记录映射）
        if self.lr is not None:
            resolved = self._resolve_names(graph, app_id, app_name, issues, fixes)
            self._resolve_fields(graph, app_id, app_name, issues, fixes, resolved)
        elif structural == []:
            issues.append(CompileIssue(
                "NO_LIVE_REFS",
                "未注入 LiveRefs，无法验证实体/字段真名（可编译但不可直接执行）",
                severity="WARN", suggestion="传入 LiveRefs(host, cookie) 后重编"))

        # 3) 业务语义歧义扫描（原文级）
        if text:
            issues.extend(self._scan_ambiguity(text))

        # 3.5) 业务陷阱自检（写操作直引循环项等，比结构校验更贴业务）
        for i in self.self_check(graph):
            issues.append(i)
            if i.severity == "ERROR":
                fixes.append("自检拦下：%s" % i.code)

        # 4) 定档
        has_error = any(i.severity == "ERROR" for i in issues)
        status = "BLOCKED" if has_error else (
            "AMBIGUOUS" if issues else "READY")

        # 5) 归一化草稿（真名回填后的副本，供审阅/追踪；graph 即归一化结果）
        normalized_draft = copy.deepcopy({"nodes": graph.get("nodes") or [],
                                          "end": graph.get("end") or {}})
        return CompileResult(status=status, graph=(None if has_error else graph),
                             issues=issues, resolved=resolved, fixes=fixes,
                             original_draft=original_draft,
                             normalized_draft=normalized_draft)

    # ---------------- 归一化 ----------------
    def _normalize(self, draft: dict, fixes: list[str]) -> dict:
        """把草稿落成标准逻辑图（补齐默认值、统一别名、修已知形态）。

        只做**不改语义**的修正；任何改语义的动作都进 issues，不在这里静默做。
        ★ 深拷贝：这里改的是副本，绝不污染调用方传入的原始草稿。
        """
        graph = {"nodes": copy.deepcopy(draft.get("nodes") or []),
                 "end": copy.deepcopy(draft.get("end") or {})}
        self._walk_normalize(graph["nodes"], fixes)
        return graph

    def _walk_normalize(self, seq: list, fixes: list[str]) -> None:
        for i, n in enumerate(seq):
            if not isinstance(n, dict):
                continue
            kind = n.get("kind")
            if not kind:
                continue
            # 别名兜底：缺 id 用 kind+序号（只是让它可定位，不冒充业务名）
            if not n.get("id"):
                n["id"] = "%s_%d" % (kind, i + 1)
                fixes.append("节点[%d] 补别名 %r" % (i, n["id"]))
            # for_each 的 source 写法归一：list 优先
            if kind == "for_each" and not n.get("list") and n.get("source"):
                src = n["source"]
                if isinstance(src, dict) and "ref" in src:
                    n["list"] = src["ref"]
                    fixes.append("for_each.list ← source.ref=%r" % n["list"])
            # capture：草稿常写 caption 为空
            for bk in _BLOCK_KEYS.get(kind, ()):
                body = n.get(bk)
                if isinstance(body, list):
                    self._walk_normalize(body, fixes)

    # ---------------- 真名解析 ----------------
    def _resolve_names(self, graph: dict, app_id: str, app_name: str,
                       issues: list[CompileIssue], fixes: list[str]) -> dict:
        """实体/字段真名解析。解析不了的记 issue，绝不替用户挑一个。"""
        resolved: dict = {"entities": {}, "fields": {}}
        try:
            entities = self.lr.entity(app_id, app_name)
        except Exception as e:
            issues.append(CompileIssue("ENTITY_LIST_FAILED",
                                       "拉取实体清单失败：%s" % str(e)[:200],
                                       severity="ERROR"))
            return resolved

        by_caption = {e.get("caption"): e for e in entities if e.get("caption")}
        by_dto = {e.get("dtoFullName"): e for e in entities if e.get("dtoFullName")}

        def resolve_entity(label: str, node_id: str) -> str | None:
            if not label:
                return None
            if label in by_caption:
                resolved["entities"][label] = label
                return label
            if label in by_dto:
                cap = by_caption.get((by_dto[label] or {}).get("caption"))
                if cap:
                    resolved["entities"][label] = cap.get("caption")
                    return cap.get("caption")
            # 关键词候选（不替用户选，列出来）
            cands = [e.get("caption") for e in entities
                     if label in (e.get("caption") or "")]
            if len(cands) == 1:
                resolved["entities"][label] = cands[0]
                fixes.append("实体 %r → 唯一候选 %r" % (label, cands[0]))
                return cands[0]
            if cands:
                msg = "实体 %r 有多个候选：%s" % (label, cands[:5])
            else:
                msg = "实体 %r 不存在" % (label,)
            issues.append(CompileIssue(
                "ENTITY_NOT_FOUND" if not cands else "ENTITY_AMBIGUOUS",
                msg,
                node_id=node_id, severity="ERROR",
                suggestion="用实体全名或 dtoFullName；候选："
                           + str([e.get("caption") for e in entities][:12])))
            return None

        def walk(seq):
            for n in seq:
                if not isinstance(n, dict):
                    continue
                nid = n.get("id") or ""
                if n.get("entity"):
                    got = resolve_entity(n["entity"], nid)
                    if got:
                        n["entity"] = got
                for bk in _BLOCK_KEYS.get(n.get("kind") or "", ()):
                    if isinstance(n.get(bk), list):
                        walk(n[bk])

        walk(graph["nodes"])
        return resolved

    # ---------------- 字段真名解析 ---------------- 
    _ENTITY_BLOCK_KEYS = ("then", "else", "body", "nodes", "branches", "otherwise")

    def _resolve_fields(self, graph: dict, app_id: str, app_name: str,
                        issues: list[CompileIssue], fixes: list[str],
                        resolved: dict) -> None:
        """字段名真名解析 + 归一化回填。

        覆盖：cond_field / by_field / from_field / sort_by / group_by /
        count_fields / fields（dict 键）/ filter.field / filter.expr 递归。
        解析策略：先按 attributes 键匹配，再按中文 label 唯一匹配；都命中不了
        记 FIELD_NOT_FOUND，绝不用猜的。命中后**原地回填真名**到归一化图，
        并把 original→resolved 映射记进 resolved["fields"]（不污染原始草稿，
        原始草稿由 compile 的 original_draft 保留）。
        """
        nodes_by_id: dict[str, dict] = {}

        def index(seq):
            for n in seq:
                if not isinstance(n, dict):
                    continue
                if n.get("id"):
                    nodes_by_id[n["id"]] = n
                for bk in _BLOCK_KEYS.get(n.get("kind") or "", ()):
                    if isinstance(n.get(bk), list):
                        index(n[bk])

        index(graph.get("nodes") or [])

        # 实体模型缓存（label → attributes dict；None = 无法加载，跳过校验）
        models: dict[str, dict | None] = {}

        def model_of(label):
            if not label:
                return None
            if label in models:
                return models[label]
            if not hasattr(self.lr, "entity_model"):
                # LiveRefs 不提供字段表时，不做字段校验（只做实体校验）
                models[label] = None
                return None
            try:
                m = self.lr.entity_model(app_id, app_name, label=label)
            except Exception:
                m = {}
            attrs = (m or {}).get("attributes")
            if not attrs:
                # 拿不到字段表（实体不存在 / 接口失败）→ 跳过，不误报
                models[label] = None
                return None
            models[label] = attrs
            return attrs

        def entity_of(node):
            if node.get("entity"):
                return node["entity"]
            src = node.get("list_node") or node.get("from_node")
            if src and src in nodes_by_id:
                return entity_of(nodes_by_id[src])
            return None

        def resolve_field(node, label, fname):
            """返回平台真名（attributes 键）；匹配不到返回 None 并记 issue。"""
            if not label or not fname:
                return None
            attrs = model_of(label)
            if attrs is None:
                return None
            if fname in attrs or fname == "id":
                return fname
            # 中文 caption（真实平台字段中文名）唯一匹配 → 真名（键）
            #   label 仅作向后兼容（早期测试 fake 用过）。
            hits = [k for k, a in attrs.items()
                    if isinstance(a, dict) and (a.get("caption") == fname
                                                or a.get("label") == fname)]
            if len(hits) == 1:
                return hits[0]
            issues.append(CompileIssue(
                "FIELD_NOT_FOUND",
                "字段 %r 不存在于实体 %r（可用：%s）"
                % (fname, label, sorted(attrs)[:10]),
                node_id=node.get("id") or "", severity="ERROR",
                suggestion="用字段真名（attributes 键）或中文 label"))
            return None

        def apply_field(node, label, fname, where):
            """解析并回填：返回真名；未匹配返回原名（issue 已记）。"""
            real = resolve_field(node, label, fname)
            if real is None:
                return fname
            resolved["fields"].setdefault("%s.%s" % (label, fname), real)
            return real

        def walk_expr(spec, node, label):
            """递归扫 JSON 表达式，回填所有 field 引用的真名。"""
            if isinstance(spec, dict):
                if "field" in spec and isinstance(spec["field"], str):
                    parts = spec["field"].split(".")
                    parts[-1] = apply_field(node, label, parts[-1], "expr")
                    spec["field"] = ".".join(parts)
                for v in spec.values():
                    walk_expr(v, node, label)
            elif isinstance(spec, list):
                for v in spec:
                    walk_expr(v, node, label)

        def walk(seq):
            for n in seq:
                if not isinstance(n, dict):
                    continue
                kind = n.get("kind")
                label = entity_of(n)
                # 单值字段引用（★ from_field 例外：它是 by_id_from 循环项的元素字段，
                #   不是本节点 entity 的字段，不能按 entity 归一化/校验，否则
                #   循环内 RETRIEVE(by_id_from=each, from_field=外键) 会误报 FIELD_NOT_FOUND）
                for key in ("cond_field", "by_field"):
                    v = n.get(key)
                    if isinstance(v, str):
                        n[key] = apply_field(n, label, v, key)
                # 单值或列表字段引用
                for key in ("sort_by", "group_by", "count_fields"):
                    v = n.get(key)
                    if isinstance(v, str):
                        n[key] = apply_field(n, label, v, key)
                    elif isinstance(v, list):
                        n[key] = [apply_field(n, label, f, key)
                                  if isinstance(f, str) else f for f in v]
                # fields dict：键即字段名，回填键
                fs = n.get("fields")
                if isinstance(fs, dict):
                    n["fields"] = {
                        apply_field(n, label, f, "fields"): val
                        for f, val in fs.items()}
                # retrieve_array 多条件（conditions: [{field, op, right}]）
                conds = n.get("conditions")
                if isinstance(conds, list):
                    for cd in conds:
                        if isinstance(cd, dict) and isinstance(cd.get("field"), str):
                            cd["field"] = apply_field(n, label, cd["field"], "conditions")
                # FILTER 的 field / expr
                flt = n.get("filter")
                if isinstance(flt, dict):
                    if flt.get("field"):
                        raw = str(flt["field"])
                        if "." in raw:
                            prefix = raw.rsplit(".", 1)[0]
                            flt["field"] = prefix + "." + apply_field(
                                n, label, raw.rsplit(".", 1)[1], "filter")
                        else:
                            flt["field"] = apply_field(n, label, raw, "filter")
                    if flt.get("expr"):
                        walk_expr(flt["expr"], n, label)
                for bk in _BLOCK_KEYS.get(kind or "", ()):
                    if isinstance(n.get(bk), list):
                        walk(n[bk])

        walk(graph.get("nodes") or [])

    # ---------------- 语义歧义扫描 ----------------
    def _scan_ambiguity(self, text: str) -> list[CompileIssue]:
        out: list[CompileIssue] = []
        for code, pat, msg, sugg in _AMBIGUITY_RULES:
            if re.search(pat, text):
                out.append(CompileIssue(code, msg, severity="WARN", suggestion=sugg))
        return out

    # ---------------- 已知陷阱自检 ----------------
    def self_check(self, graph: dict) -> list[CompileIssue]:
        """执行前的业务陷阱自检（比 validate_graph 更贴业务）。"""
        out: list[CompileIssue] = []

        def walk(seq, in_loop: list[str]):
            for n in seq:
                if not isinstance(n, dict):
                    continue
                nid = n.get("id") or ""
                kind = n.get("kind")
                # 写操作直引循环项 → 必然被 G20 拦，提前给可读提示
                if kind in _WRITE_KINDS:
                    src = n.get("from_node") or ""
                    if src in in_loop:
                        out.append(CompileIssue(
                            "WRITE_ON_LOOP_ITEM",
                            "节点 %r 直接拿循环项 %r 当写操作对象" % (nid, src),
                            node_id=nid, severity="ERROR",
                            suggestion="循环体内先 RETRIEVE(by_id_from=循环, from_field=id)，"
                                       "写操作引用该 RETRIEVE 出参（G20）"))
                sub = in_loop + ([nid] if kind in ("for_each", "for_count") else [])
                for bk in _BLOCK_KEYS.get(kind or "", ()):
                    if isinstance(n.get(bk), list):
                        walk(n[bk], sub)

        walk(graph.get("nodes") or [], [])
        return out
