"""P3 声明式逻辑图引擎：JSON 逻辑图 → 构造器 → schema。

## 为什么要这一层

P1/P2 之后节点构造器（26 类）和表达式引擎都齐了，但入口仍是**命令式 Python**：

```python
ret = comp.step("retrieve", "ds", entity="数据源配置信息", by_id_from="$input")
br  = comp.step("branch", "br1", conditions=[...])   # ← 实际没有这个能力
```

这对 LLM 不友好：控制流（嵌套 BRANCH、循环体）必须用代码结构表达，
模型一嵌套就错位；而且无法「先落成可审阅的 JSON，再执行」——
用户看不到方案、审计员没法只审方案。

所以本模块引入**逻辑图（LogicGraph）**——纯 JSON，可序列化、可 diff、可人工审阅：

```json
{
  "kind": "MANUAL",
  "nodes": [
    {"id": "ds", "kind": "retrieve", "entity": "数据源配置信息",
     "by_id_from": "$input", "caption": "查询-数据源"},
    {"id": "res", "kind": "create_variable", "title": "isValid",
     "data_type": "BOOLEAN", "value": false, "caption": "结果-默认否"},
    {"id": "br1", "kind": "branch", "caption": "判断-是否启用",
     "condition": {"op": "EQ", "left": {"field": "ds.enabled"}, "right": {"const": true}},
     "then": [
        {"id": "arr", "kind": "retrieve_array", "entity": "数据源配置信息",
         "conditions": [{"field": "enabled", "op": "EQ", "right": {"const": true}},
                        {"field": "id", "op": "NE", "right": {"input": "id"}}]},
        {"id": "br2", "kind": "branch", "caption": "判断-jdbc 含 mysql",
         "condition": {"fn": "containsText",
                       "args": [[{"field": "ds.jdbcUrl"}, {"const": "mysql"}]]},
         "then": [{"id": "setT", "kind": "change_variable", "target": "res",
                   "value": true}]}
     ]}
  ],
  "end": {"from": "res", "desc": "是否有效"}
}
```

## 三条设计约束（都不是风格问题，是会出错的地方）

1. **节点 id 是业务别名，不是平台 nodeId**。平台 nodeId 由构造器生成且保存会变，
   逻辑图里写平台 nodeId 一改就失效。引用一律用别名；`$input` 是保留字。
2. **控制流用嵌套数组表达**（`then` / `else` / `body`），顺序即执行。
   扁平 `next` 链表在分支里会产生歧义（哪条边跨分支？），嵌套没有。
3. **表达式用 DSL 字段而非 AST 对象**（见 `expression_dsl`）：JSON 装不下
   Python 对象；DSL 翻译成 AST 后走 P2 的编译器 + 远端 check/transform。

## 引用顺序：构图期就判

`{"field": "a.b"}` 的 `a` 必须在当前节点**之前**已执行，否则 `DslError`。
平台不拦这种错（context 给了就过），运行期才取不到值 —— 假绿经典来源。

## 分支体的正确挂法

BRANCH 的子节点属于 `conditions[i].nodes`，不属于顶层 `nodes`。
执行器按「容器栈」构造：`self._stack` 顶是当前收集容器，
进分支压栈新列表、出分支弹栈并挂回。**不要**临时替换 composer.nodes
（会破坏 composer 的 by_alias 与顺序语义）。
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any

from .loop_scope import (
    LoopFrame, LoopScopeStack, ScopeError, loop_frame_from,
)


class GraphError(RuntimeError):
    """逻辑图非法（引用越界/字段不存在/节点不支持）。绝不降级生成。"""


RESERVED_INPUT = "$input"

_STEP_KINDS = frozenset({
    "retrieve", "retrieve_array", "create_entity", "change_entity", "delete_entity",
    "create_variable", "change_variable", "create_list", "change_list",
    "page_info",
    "list_operation", "create_map", "map_operation", "convert_data",
    "call_app_service", "sub_microflow", "data_mapping",
    # ★ 2026-11-02 补齐：构造器早就有了，DSL 没入口 → LLM 生成逻辑图时用不到
    "create_batch_entity", "change_batch_entity",
    "publish_business_event", "custom_error", "call_data_flow", "break",
    "create_list_entity", "change_list_add",
    "branch", "for_each", "for_count",
})

_BLOCK_KEYS = {"branch": ("then", "else"), "for_each": ("body",),
               "for_count": ("body",)}


# ---------------------------------------------------------------- 结构校验
def validate_graph(graph: dict) -> list[str]:
    """结构级校验（不解析表达式、不查实体）。返回问题列表，空=通过。

    ★ 单列出来是因为逻辑图常由 LLM 产出：先做纯结构体检
    （kind 拼错 / block 键用错 / id 重复缺失）再进昂贵的元数据查询。
    """
    problems: list[str] = []
    if not isinstance(graph, dict):
        return ["逻辑图必须是对象"]
    nodes = graph.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        return ["nodes 必须是非空数组"]

    seen: set[str] = set()

    def walk(seq, path):
        for i, n in enumerate(seq):
            where = "%s[%d]" % (path, i)
            if not isinstance(n, dict):
                problems.append("%s 不是对象" % where)
                continue
            nid = n.get("id")
            if not nid:
                problems.append("%s 缺 id" % where)
                continue
            if nid in seen:
                problems.append("id 重复: %r" % nid)
            seen.add(nid)
            kind = n.get("kind")
            if kind not in _STEP_KINDS:
                problems.append("%s kind=%r 不支持（可用：%s）"
                                % (where, kind, sorted(_STEP_KINDS)))
                continue
            for bk in _BLOCK_KEYS.get(kind, ()):
                body = n.get(bk)
                if body is None:
                    continue
                if not isinstance(body, list):
                    problems.append("%s.%s 必须是数组" % (where, bk))
                    continue
                walk(body, "%s.%s" % (where, bk))
            if kind not in _BLOCK_KEYS:
                for bk in ("then", "else", "body"):
                    if bk in n:
                        problems.append("%s kind=%r 不支持 %s（只有控制节点有分支体）"
                                        % (where, kind, bk))
            if kind == "branch" and not n.get("condition"):
                problems.append("%s branch 缺 condition" % where)
            if kind == "for_each" and not n.get("list"):
                problems.append("%s for_each 缺 list" % where)

    walk(nodes, "nodes")
    end = graph.get("end")
    if end is not None:
        if not isinstance(end, dict):
            problems.append("end 必须是对象")
        elif end.get("from") and end["from"] not in seen:
            problems.append("end.from=%r 不在节点 id 里" % end["from"])
    return problems


# ---------------------------------------------------------------- 作用域
@dataclass
class ExecScope:
    """已执行节点顺序表（顺序裁决的唯一依据）。"""
    done: list[str] = dc_field(default_factory=list)

    def has(self, alias: str) -> bool:
        return alias in self.done or alias == RESERVED_INPUT

    def mark(self, alias: str) -> None:
        if alias not in self.done:
            self.done.append(alias)

    def available(self) -> list[str]:
        return list(self.done)


# ---------------------------------------------------------------- 执行器
class LogicGraphRunner:
    """逻辑图 → MicroflowComposer → schema。

    composer 必须已注入 refs（LiveRefs）：实体/字段元数据全部走活引用，
    本类不做任何元数据猜测。backend 是 P2 的表达式传输后端（CurlBackend）。
    """

    def __init__(self, composer, *, resolver=None, backend=None):
        self.c = composer
        self.resolver = resolver or getattr(composer, "refs", None)
        self.backend = backend
        self.scope = ExecScope()
        self._stack: list[list[dict]] = []       # 容器栈：当前收集中的节点列表
        self.loops = LoopScopeStack()            # P3.1 循环作用域栈
        # ★ 循环深度（BREAK 合法性判据）。不能只看 loops._stack：
        #   FOR_COUNT 没有循环项 frame，push 不进去，用 loops 判会把合法 BREAK 误拒。
        self._loop_depth = 0
        self.needs_ui_finalize: list[str] = []   # 需进设计器点「确定」的节点别名

    # ---------------- 入口 ----------------
    def run(self, graph: dict, *, basic_out: str | None = None) -> dict:
        problems = validate_graph(graph)
        if problems:
            raise GraphError("逻辑图非法:\n  " + "\n  ".join(problems))
        if self.resolver is not None and hasattr(self.resolver, "bind_scope"):
            self.resolver.bind_scope(self.scope)
        self._exec_block(graph["nodes"])
        end = graph.get("end") or {}
        last = end.get("from") or (self.scope.done[-1] if self.scope.done else "")
        # ★ 必须显式传 trigger：finish(trigger=None) 会回落到自建 trigger_manual()，
        #   把外部注入的入参 DTO 丢掉 —— schema.trigger 变 None、
        #   _outputs() 收不到 _FLOW_INPUT_xxx，G2 把入参引用全判成悬空。
        return self.c.finish(end_from=last, trigger=getattr(self.c, "trigger", None),
                             out_desc=end.get("desc") or "流程返回",
                             basic_out=basic_out or end.get("basic_out"))

    # ---------------- 遍历 ----------------
    def _exec_block(self, seq: list) -> None:
        for n in seq:
            self._exec_node(n)

    def _emit(self, node: dict) -> dict:
        """把节点放到当前容器（顶层 = composer.nodes，分支体内 = 栈顶列表）。"""
        if self._stack:
            self._stack[-1].append(node)
        else:
            self.c.nodes.append(node)
        return node

    def _exec_node(self, n: dict) -> None:
        kind, alias = n["kind"], n["id"]
        if kind == "branch":
            self._exec_branch(n)
        elif kind in ("for_each", "for_count"):
            self._exec_loop(n)
        else:
            handler = getattr(self, "_do_" + kind, None)
            if handler is None:
                raise GraphError("kind=%r 还没接执行器（先实现 _do_%s）" % (kind, kind))
            node = handler(n)
            if n.get("_self_registered"):
                self.scope.mark(alias)
                return
            if n["kind"] == "retrieve_array" and n.get("conditions"):
                # 多条件分支自己已经落位（见 _retrieve_array_multi）
                self._register(alias, node)
                self.scope.mark(alias)
                return
            # ★ composer._st_* 内部已经 _add() 把节点塞进 self.c.nodes（顶层）。
            #   - 顶层节点：已经在正确位置，不要再 append（会重复一份）
            #   - 分支体内：把它从顶层搬到栈顶容器（否则分支体是空壳、
            #     节点全跑顶层，平台看到的是「顺序错乱 + 分支无条件体」）
            if self._stack:
                try:
                    self.c.nodes.remove(node)
                except ValueError:
                    pass
                self._stack[-1].append(node)
            self._register(alias, node)
        self.scope.mark(alias)

    def _register(self, alias: str, node: dict) -> None:
        self.c.by_alias[alias] = node
        if self.resolver is not None and hasattr(self.resolver, "register_alias"):
            self.resolver.register_alias(alias, node)

    # ---------------- 分支 ----------------
    def _exec_branch(self, n: dict) -> None:
        from .microflow_nodes_extra import branch as branch_node

        cond = self._build_expression(n["condition"], "BOOLEAN", n)
        # ★ _build_expression 返回 Expression 值槽（type+expression 包装），
        #   branch_node 要 {title,schema} 原始对象，这里解包（否则 G12 报
        #   ifBranch expression 未配置——schema 在 expression.schema 里）。
        if isinstance(cond, dict) and cond.get("type") == "Expression":
            cond = cond.get("expression") or cond
        # 分支内的 CONDITION 节点也用别名做 id 种子（branch 不走 step，这里手动设）
        if hasattr(self.c.b, "_new_id"):
            _prev_key = getattr(self.c.b, "node_key", None)
            self.c.b.node_key = n["id"]
            try:
                br = branch_node(self.c.b, [{"expression": cond, "nodes": []}],
                                 caption=n.get("caption") or "分支")
            finally:
                self.c.b.node_key = _prev_key
        else:
            br = branch_node(self.c.b, [{"expression": cond, "nodes": []}],
                             caption=n.get("caption") or "分支")

        # ★ 先 mark 自己：分支体内的表达式/引用要能看到「本分支之前」的节点，
        #   但看不到分支外的后序节点（那些还没 mark）。
        self.scope.mark(n["id"])

        self._stack.append([])
        try:
            self._exec_block(n.get("then") or [])
            then_nodes = self._stack[-1]
        finally:
            self._stack.pop()
        br["conditions"][0]["nodes"] = then_nodes

        if n.get("else"):
            self._stack.append([])
            try:
                self._exec_block(n["else"])
                else_nodes = self._stack[-1]
            finally:
                self._stack.pop()
            br["conditions"][-1]["nodes"] = else_nodes

        self._emit(br)
        self._register(n["id"], br)

    # ---------------- 循环 ----------------
    def _exec_loop(self, n: dict) -> None:
        from .microflow_nodes_extra import for_count
        from .microflow_nodes_svc import for_each

        if n["kind"] == "for_each":
            src = self.c.by_alias.get(n["list"])
            if src is None:
                raise GraphError("for_each.list=%r 不是已构建节点" % n["list"])
            node = for_each(self.c.b, src, caption=n.get("caption") or "列表循环")
        else:
            start = self._slot_value(n.get("start"), n, "INTEGER")
            end = self._slot_value(n.get("end"), n, "INTEGER")
            node = for_count(self.c.b, start, end, int(n.get("step") or 1),
                             caption=n.get("caption") or "计数循环")

        self.scope.mark(n["id"])
        self._register(n["id"], node)

        # ★ P3.1：循环项 = FOR_EACH 节点自身出参（语料 526/526，无独立循环变量）。
        #   作用域只在 body 内有效，出循环立即弹出 —— 循环外引用必须报错。
        frame = None
        if n["kind"] == "for_each":
            src = self.c.by_alias.get(n["list"]) or {}
            # ★ 元素字段元数据优先取「实体模型」（structure 里通常没有 attributes）。
            #   RETRIEVE_ARRAY 的 structure 只有 id/caption，直接读会得到空字段表，
            #   于是每一次 item.<字段> 都被判成「字段不存在」。
            src_st = dict(src.get("structure") or {})
            if not src_st.get("attributes"):
                dto = ((src.get("output") or {}).get("id")
                       or src_st.get("id") or "")
                mdl = self._entity_by_dto(dto)
                if mdl:
                    src_st = dict(src_st, attributes=mdl.get("attributes") or {})
                    src_st.setdefault("id", mdl.get("fullName") or dto)
            frame = loop_frame_from(
                src.get("output") or {}, src_st,
                alias=n["id"], node_id=node.get("nodeId") or "",
                output_name=(node.get("output") or {}).get("name") or "",
                caption=n.get("caption") or n["id"])
            try:
                self.loops.push(frame)
            except ScopeError as e:
                raise GraphError("节点 %r: %s" % (n["id"], e)) from e

        self._stack.append([])
        self._loop_depth += 1
        try:
            self._exec_block(n.get("body") or [])
            body = self._stack[-1]
        finally:
            self._stack.pop()
            self._loop_depth -= 1
            if frame is not None:
                self.loops.pop()
        node["nodes"] = body
        self._emit(node)

    # ---------------- 普通节点 ----------------
    def _do_retrieve(self, n: dict) -> dict:
        kw = {"entity": n["entity"],
              "caption": n.get("caption") or "查询-单条"}
        if n.get("by_id_from"):
            src = n["by_id_from"]
            # ★ 循环项 ID 查询必须走循环项形态（position=parent / type=FOR_EACH），
            #   不能走 composer._id_ref（它按活动节点造 children + ACTIVITY，
            #   语料 37 条真实样本一次都不是这样）。
            if self.loops.find(src) is not None:
                return self._retrieve_by_loop_item(n)
            kw["by_id_from"] = self._alias(src, n)
            if n.get("from_field"):
                kw["from_field"] = n["from_field"]
        else:
            kw["cond_field"] = n.get("cond_field") or ""
            if "right" in n:
                kw["right_value"] = self._cond_value(
                    n.get("right"), n,
                    entity=self.c.entity(n["entity"]),
                    field=n.get("cond_field") or "")
        if n.get("null_handling"):
            kw["null_handling"] = n["null_handling"]
            kw["null_message"] = n.get("null_message") or ""
        return self._call("retrieve", n, kw)

    def _do_retrieve_array(self, n: dict) -> dict:
        conds = n.get("conditions")
        if not conds:
            return self._call("retrieve_array", n, {
                "entity": n["entity"], "cond_field": n.get("cond_field") or "",
                "right_value": self._cond_value(
                    n.get("right"), n,
                    entity=self.c.entity(n["entity"]),
                    field=n.get("cond_field") or ""),
                "fetch_type": n.get("fetch_type") or "CONDITION",
                "ids_from": n.get("ids_from"),
                "page_info_from": n.get("page_info_from"),
                "sort_by": n.get("sort_by"),
                "sort_dir": n.get("sort_dir") or "ASC",
                "caption": n.get("caption") or "查询-多条"})
        return self._retrieve_array_multi(n, conds)

    def _do_page_info(self, n: dict) -> dict:
        return self._call("page_info", n, {
            "page_number": n.get("page_number", 1),
            "page_size": n.get("page_size", 20),
            "need_total": n.get("need_total", True),
            "caption": n.get("caption") or "分页参数"})

    def _do_create_variable(self, n: dict) -> dict:
        kw = {"title": n["title"], "caption": n.get("caption") or "创建变量-" + n["title"]}
        if n.get("entity"):
            kw["entity"] = n["entity"]
            if n.get("fields"):
                # ★ 实体型变量字段映射：值槽走 _entity_fields（const/field/arith → 值槽），
                #   造「尚未落库（无 id）」的实体对象，供 change_list_add → create_batch_entity。
                kw["fields"] = self._entity_fields(n["fields"], n)
        else:
            kw["data_type"] = n.get("data_type") or "STRING"
            if "value" in n:
                kw["value"] = self._slot_value(n["value"], n, kw["data_type"])
        return self._call("create_variable", n, kw)

    def _do_change_variable(self, n: dict) -> dict:
        kw = {"target": n["target"],
              "caption": n.get("caption") or "赋值-" + n["target"]}
        if "value" in n:
            kw["value"] = self._slot_value(n["value"], n, self._target_type(n["target"]))
        elif n.get("from_node"):
            kw["from_node"] = n["from_node"]
            kw["field"] = n.get("field") or ""
        return self._call("change_variable", n, kw)

    def _do_change_entity(self, n: dict) -> dict:
        return self._call("change_entity", n, {
            "entity": n["entity"], "from_node": n["from_node"],
            "fields": self._entity_fields(n["fields"], n),
            "caption": n.get("caption") or "更新数据"})

    def _do_create_entity(self, n: dict) -> dict:
        return self._call("create_entity", n, {
            "entity": n["entity"], "fields": self._entity_fields(n["fields"], n),
            "caption": n.get("caption") or "插入数据"})

    def _do_list_operation(self, n: dict) -> dict:
        """列表操作（SIZE/GET/ADD/DEL 等）。

        ★ composer._st_list_operation 内部 self._node(list_node) 要的是**别名**，
          传节点对象会 unhashable type: 'dict'。这里传别名，并校验它存在。
        """
        alias = n.get("list_node") or ""
        if alias not in self.c.by_alias:
            raise GraphError("节点 %r 的 list_node=%r 不是已构建节点（可用：%s）"
                             % (n.get("id"), alias, sorted(self.c.by_alias)[:8]))
        return self._call("list_operation", n, {
            "list_node": alias,
            "op_type": n.get("op_type") or "SIZE",
            "title": n.get("title") or (n.get("caption") or "列表处理结果"),
            "sort_by": n.get("sort_by"),
            "sort_dir": n.get("sort_dir") or "ASC",
            "count_fields": n.get("count_fields"),
            "index_value": n.get("index_value"),
            "second_list": n.get("second_list"),
            "filter": n.get("filter"),
            "group_by": n.get("group_by"),
            "caption": n.get("caption") or "列表处理"})

    def _do_custom_error(self, n: dict) -> dict:
        """自定义错误 —— 让流程在**设计好的条件**下主动失败。

        ★ 这是「可断言」的关键能力：没有它，只能验证「跑通了」，
          没法验证「跑出来的东西对不对」。
          典型用法：查询结果为空 → CUSTOM_ERROR("标记不存在")，
          于是运行日志的 `success=false` 本身就成了一票否决的证据。

        构造器见 `microflow_nodes_extra.custom_error(builder, message, error_type)`。
        """
        msg = n.get("message") or n.get("text") or "运行验证失败"
        return self._call("custom_error", n, {
            "message": msg,
            "error_type": n.get("error_type") or "GLOBAL",
            "caption": n.get("caption") or "自定义错误"})

    def _do_create_list(self, n: dict) -> dict:
        """创建列表。

        ★ 列表的 value 是**数组**（语料 181 个 []、42 个 [SelectParam]、16 个 null），
          不是 {type:"Simple"} 单值对象。默认值也要包成 [Simple]。
        """
        dt = n.get("data_type") or "STRING"
        kw = {"title": n["title"], "data_type": dt,
              "caption": n.get("caption") or "创建列表"}
        if "default_value" in n and n["default_value"] is not None:
            kw["default_value"] = self._slot_value(n["default_value"], n, dt)
        return self._call("create_list", n, kw)

    def _do_change_list(self, n: dict) -> dict:
        alias = n.get("list_node") or ""
        src = n.get("from_node") or n.get("value_from") or ""
        for a in (alias, src):
            if a and a not in self.c.by_alias:
                raise GraphError("节点 %r 引用的列表节点 %r 不存在（可用：%s）"
                                 % (n.get("id"), a, sorted(self.c.by_alias)[:8]))
        return self._call("change_list", n, {
            "list_node": alias, "from_node": src,
            "action": n.get("action") or "ADD",
            "count_fields": n.get("count_fields"),
            "caption": n.get("caption") or "修改变量(列表)"})

    def _do_create_map(self, n: dict) -> dict:
        return self._call("create_map", n, {
            "title": n.get("title") or "vMap",
            "key_type": n.get("key_type") or "STRING",
            "value_type": n.get("value_type") or "STRING",
            "caption": n.get("caption") or "创建Map"})

    def _do_map_operation(self, n: dict) -> dict:
        alias = n.get("map_node") or ""
        if alias not in self.c.by_alias:
            raise GraphError("节点 %r 的 map_node=%r 不是已构建节点（可用：%s）"
                             % (n.get("id"), alias, sorted(self.c.by_alias)[:8]))
        kw = {"map_node": alias,
              "op_type": n.get("op_type") or "PUT",
              "caption": n.get("caption") or "Map操作",
              "result_title": n.get("result_title") or "映射取值",
              "data_type": n.get("data_type") or "STRING",
              "array_or_object": n.get("array_or_object") or "OBJECT"}
        if n.get("key_value") is not None:
            kw["key_value"] = self._slot_value(n["key_value"], n, "STRING")
        if n.get("value_value") is not None:
            kw["value_value"] = self._slot_value(n["value_value"], n, kw["data_type"])
        return self._call("map_operation", n, kw)

    def _do_convert_data(self, n: dict) -> dict:
        from_alias = n.get("from_node") or ""
        if from_alias and from_alias not in self.c.by_alias:
            raise GraphError("节点 %r 的 from_node=%r 不是已构建节点（可用：%s）"
                             % (n.get("id"), from_alias, sorted(self.c.by_alias)[:8]))
        return self._call("convert_data", n, {
            "from_node": from_alias,
            "convert_type": n["convert_type"],
            "title": n.get("title") or "转换结果",
            "caption": n.get("caption") or "数据类型转换"})

    def _do_sub_microflow(self, n: dict) -> dict:
        """子微流程。mfService 必须运行时拉取（id/name/path 是应用专有）。

        ★ 草稿里只能写业务名（sub_name），不许写 id —— 跨环境 id 必变。
        """
        lr = getattr(self.c, "refs", None)
        name = n.get("sub_name") or n.get("name") or ""
        mid = n.get("sub_id") or ""
        mf = None
        if lr is not None and hasattr(lr, "find_sub_mf"):
            try:
                mf = lr.find_sub_mf(str(self.c.app_id), name=name, mf_id=mid)
            except Exception as e:
                raise GraphError("节点 %r 拉取子流程 %r 失败: %s"
                                 % (n.get("id"), name or mid, str(e)[:200])) from e
        if not mf or not mf.get("id"):
            raise GraphError(
                "节点 %r 引用子流程 %r，但在应用内找不到可引用的 RELEASE 子流程"
                "（只收 state=RELEASE；请确认子流程已发布）" % (n.get("id"), name or mid))
        kw = {"sub_name": name or mf.get("name") or "",
              "sub_id": mf.get("id") or "",
              "caption": n.get("caption") or "子微流程",
              "attrs": n.get("attrs"),
              "inputs": n.get("inputs"),
              "out_desc": n.get("out_desc") or n.get("title")}
        # 标量入参（非 DTO）：映射方式是 mappingType="value"，value 是一个引用槽。
        # 真实形态见语料：input.dataType != DTO 时，运行时不读 mappingType（直接置 "value"），
        # 但仍要求 value 是合法 AttrValue。
        if "value" in n and n.get("value") is not None:
            kw["value"] = self._slot_value(n["value"], n)
        return self._call("sub_microflow", n, kw)

    # ---------------- 写节点 / 列表 / 服务（2026-11-02 补齐执行器） ----------------
    def _need_alias(self, n: dict, alias: str, what: str) -> str:
        """校验引用的节点别名已构建（composer 的 _node() 要别名，传对象会 unhashable）。"""
        if not alias or alias not in self.c.by_alias:
            raise GraphError("节点 %r 的 %s=%r 不是已构建节点（可用：%s）"
                             % (n.get("id"), what, alias, sorted(self.c.by_alias)[:8]))
        return alias

    def _do_delete_entity(self, n: dict) -> dict:
        """删除数据。两种模式：from_node → SELECT_PARAM；否则按条件（常量右值）。

        ★ 条件是动态记录时**必须**用 from_node：CONDITION 模式的条件右值填节点引用
          会被 publish 拒（BOOT_1001，无字段级提示），闸门 G36 已拦。
        """
        kw = {"entity": n["entity"], "caption": n.get("caption") or "删除数据"}
        if n.get("from_node"):
            kw["from_node"] = self._need_alias(n, n["from_node"], "from_node")
        else:
            kw["cond_field"] = n.get("cond_field") or ""
            kw["right"] = n.get("right", n.get("right_value"))
        return self._call("delete_entity", n, kw)

    def _do_create_batch_entity(self, n: dict) -> dict:
        """批量插入。列表元素必须是**没有 id 的新对象**（否则运行时违反主键约束）。"""
        return self._call("create_batch_entity", n, {
            "entity": n["entity"],
            "list_node": self._need_alias(n, n.get("list_node"), "list_node"),
            "caption": n.get("caption") or "批量插入数据"})

    def _do_change_batch_entity(self, n: dict) -> dict:
        """批量更新。写的是列表元素**自带的字段值**（节点没有 attrs）。"""
        return self._call("change_batch_entity", n, {
            "entity": n["entity"],
            "list_node": self._need_alias(n, n.get("list_node"), "list_node"),
            "caption": n.get("caption") or "批量更新数据"})

    def _do_create_list_entity(self, n: dict) -> dict:
        return self._call("create_list_entity", n, {
            "entity": n["entity"],
            "title": n.get("title") or (n.get("caption") or "实体对象列表"),
            "caption": n.get("caption") or "创建列表"})

    def _do_change_list_add(self, n: dict) -> dict:
        return self._call("change_list_add", n, {
            "list_node": self._need_alias(n, n.get("list_node"), "list_node"),
            "item": self._need_alias(n, n.get("item") or n.get("from_node"), "item"),
            "caption": n.get("caption") or "列表添加元素"})

    def _do_call_app_service(self, n: dict) -> dict:
        """自定义服务。method_full 是完整类.方法名，签名运行时拉（含 md5）。"""
        if not n.get("method_full"):
            raise GraphError("节点 %r 调用应用服务缺 method_full（完整类.方法名）" % n.get("id"))
        return self._call("call_app_service", n, {
            "method_full": n["method_full"],
            "attrs": n.get("attrs"),
            "caption": n.get("caption") or "自定义服务"})

    def _do_data_mapping(self, n: dict) -> dict:
        return self._call("data_mapping", n, {
            "entity": n["entity"],
            "from_node": self._need_alias(n, n.get("from_node"), "from_node"),
            "src_field": n.get("src_field") or "name",
            "dst_field": n.get("dst_field"),
            "caption": n.get("caption") or "数据转换"})

    def _do_publish_business_event(self, n: dict) -> dict:
        """事件投递。event 必须由调用方从活引用取（应用专有，禁止写死）。"""
        ev = n.get("event")
        if not isinstance(ev, dict) or not ev.get("fullName"):
            raise GraphError(
                "节点 %r 事件投递缺 event 对象（需要 udcMicroflowSearchEventListPost 的"
                "活引用行，含 fullName/caption/source/dtoType）" % n.get("id"))
        attrs = n.get("attrs")
        if isinstance(attrs, dict):
            # DSL 层 dict {字段名: 值槽} → [{attrType, value}] 列表（事件 DTO 字段级）
            attrs = self._event_attrs(ev, attrs, n)
        return self._call("publish_business_event", n, {
            "event": ev, "attrs": attrs,
            "caption": n.get("caption") or "事件投递"})

    def _event_attrs(self, ev: dict, attrs: dict, n: dict) -> list:
        """事件 DTO 字段映射 dict → [{attrType, value}] 列表（field_attr 拉真实字段元数据）。"""
        from .microflow_fields import field_attr
        lr = getattr(self.resolver, "live_refs", None)
        if lr is None:
            raise GraphError("事件 attrs 需要 LiveRefs（拉事件 DTO 字段元数据）")
        app_id = getattr(self.resolver, "app_id", None)
        app_name = getattr(self.resolver, "app_name", None)
        fields = lr.dto_attributes(app_id, app_name, ev["fullName"])
        em = {"attributes": fields, "refApp": app_name}
        out = []
        for i, (fname, val) in enumerate(attrs.items()):
            if fname not in fields:
                raise GraphError("事件字段 %r 不在 %s（可用：%s）"
                                 % (fname, ev["fullName"], sorted(fields)[:12]))
            dtype = (fields[fname] or {}).get("dataType") or "STRING"
            out.append({"attrType": field_attr(em, fname, sort=i),
                        "value": self._slot_value(val, n, dtype)})
        return out

    def _do_call_data_flow(self, n: dict) -> dict:
        """执行生单规则。rule 必须由调用方从 LiveRefs.data_flow_candidates 取。"""
        rule = n.get("rule") or n.get("data_flow")
        if not isinstance(rule, dict) or not rule.get("id"):
            raise GraphError(
                "节点 %r 执行生单规则缺 rule 对象（需要 LiveRefs.data_flow_candidates "
                "按来源实体查出的行，含 id/dataFlowId/appId/appUrl/sourceEntityId）"
                % n.get("id"))
        return self._call("call_data_flow", n, {
            "entity": n["entity"], "rule": rule,
            "condition": n.get("condition"),
            "out_desc": n.get("title") or n.get("out_desc") or "生单结果",
            "data_source_type": n.get("data_source_type") or "CONDITION",
            "caption": n.get("caption") or "执行生单规则"})

    def _do_break(self, n: dict) -> dict:
        """跳出循环。只能放在循环体内——放外面平台也不接受。"""
        if not getattr(self, "_loop_depth", 0):
            raise GraphError("节点 %r 是 BREAK，但不在任何循环体内（只能放 FOR/FOR_EACH 的 body）"
                             % n.get("id"))
        return self._call("break", n, {"caption": n.get("caption") or "跳出循环"})

    # ---------------- 值/条件构造 ----------------
    def _alias(self, alias: str, n: dict) -> str:
        """逻辑图别名 → composer 认的别名。

        ★ `$input` 必须映射到开始节点（trigger.nodeId，默认 MFStartNode）：
        composer.by_alias 里只有业务节点，不含 trigger；
        直接把 "$input" 传下去会报「引用不存在的节点别名」。
        """
        if alias == RESERVED_INPUT:
            trg = getattr(self.c, "trigger", None) or {}
            node_id = trg.get("nodeId") or "MFStartNode"
            if node_id not in self.c.by_alias:
                # 把 trigger 以开始节点身份登记，供 _id_ref / _out_ref 取用
                self.c.by_alias[node_id] = dict(trg, actionType="START",
                                                type=trg.get("type") or "MANUAL")
            return node_id
        if alias not in self.c.by_alias:
            raise GraphError("节点 %r 引用了未构建的别名 %r（可用：%s）"
                             % (n.get("id"), alias, sorted(self.c.by_alias)[:8]))
        return alias

    def _target_type(self, alias: str) -> str:
        node = self.c.by_alias.get(alias) or {}
        return (node.get("output") or {}).get("dataType") or "STRING"

    def _slot_value(self, spec: Any, n: dict, want: str = "STRING") -> dict:
        """值槽（Simple / SelectParam / Expression）。复合表达式走远端链。"""
        if _is_expr(spec):
            return self._build_expression(spec, want, n)
        if _is_ref(spec):
            return self._ref_value(spec, n)
        if isinstance(spec, dict) and "const" in spec:
            return _simple(spec["const"])
        return _simple(spec)

    def _cond_value(self, spec: Any, n: dict,
                    entity: dict | None = None, field: str | None = None) -> dict:
        """查询条件右值（CONSTANT / CONTEXT_VARIABLE / EXPRESSION 三态）。

        ★ 三种入参必须分清，否则会写进非法值槽：
          {"const": true}  → DSL 常量（要解包成 CONSTANT 槽，不能原样塞）
          {"field": ...}   → 引用（SelectParam）
          {"op"/"fn": ...} → 表达式（走远端链）

        ★★ entity/field 用来查左值字段的 dataType：CONSTANT 的 value 类型
           必须与字段类型一致（BOOLEAN→bool、DECIMAL→float、其余→str），
           否则前端按文本渲染、后端拿不到布尔值。
        """
        if _is_expr(spec):
            return self._build_expression(spec, "STRING", n)
        if _is_ref(spec):
            # ★ 查询条件右值不支持字段引用（field 含点号，如 {"field": "req.deptId"}）。
            #   实测两条路都堵死：CONTEXT_VARIABLE(children) 平台解析不了、查询静默返回空
            #   （假绿）；EXPRESSION 不能自己编（executableExpr 是后端编译 blob，自己编
            #   BOOT_1001）。正确做法：先用 create_variable 把字段值转成标量变量，
            #   再让查询条件右值引用该变量（整节点 parent 引用）。
            fv = spec.get("field")
            if isinstance(fv, str) and "." in fv:
                raise GraphError(
                    "查询条件右值不支持字段引用 %r（平台只认整节点引用/常量，"
                    "字段引用会静默返回空或 BOOT_1001）。请先用 create_variable "
                    "把该字段值转成标量变量，再引用变量。" % fv)
            return self._ref_value(spec, n, cond=True)
        dt = None
        enum_map = None
        if entity is not None and field:
            attr = (entity.get("attributes") or {}).get(field) or {}
            dt = attr.get("dataType")
            enum_map = _enum_desc_map(attr) or None
        if isinstance(spec, dict) and "const" in spec:
            return _constant(spec["const"], dt, enum_map)
        return _constant(spec, dt, enum_map)

    def _flow_input_ref(self, ast, out_name: str) -> dict:
        """流程入参 → SelectParam（真实形态取自 85 个写节点样本）。

        id/dtoType/udcApp 都是 null，name=key=path=outputName=入参变量名，
        position="parent"；外层 desc 是「标题 [类型中文]」。
        """
        from ..udc.microflow.expression_model import JAVA as _JAVA
        dt = str(getattr(ast, "dtype", "") or
                 (ast.ref or {}).get("dataType") or "STRING").upper()
        title = (ast.ref or {}).get("title") or "入参"
        label = {"STRING": "文本", "BIGINTEGER": "整数", "INTEGER": "整数",
                 "DECIMAL": "小数", "BOOLEAN": "布尔", "DATETIME": "日期时间",
                 "DATE": "日期"}.get(dt, "文本")
        return {"type": "SelectParam",
                "selectParam": {
                    "id": None, "javaType": _JAVA.get(dt, "java.lang.String"),
                    "dataType": dt, "type": "OBJECT", "desc": title,
                    "dtoType": None, "udcApp": None,
                    "name": out_name, "key": out_name, "path": out_name,
                    "outputName": out_name, "description": title,
                    "position": "parent"},
                "desc": "%s [%s]" % (title, label)}

    def _flow_input_field_ref(self, ast, out_name: str) -> dict:
        """DTO 流程入参的**字段**引用（MANUAL 触发 + input.dataType=DTO）。

        形态同字段引用：position=children、key="<入参名>_<dto>.<字段>"、
        path="<dto去点>.<字段>"、name=<纯字段名>。
        """
        from ..udc.microflow.expression_model import JAVA as _JAVA
        ref = ast.ref or {}
        dto = ref.get("dto_id") or ""
        fname = ref.get("field") or ""
        meta = (ref.get("fields") or {}).get(fname) or {}
        dt = str(getattr(ast, "dtype", "") or meta.get("dataType") or "STRING").upper()
        title = meta.get("caption") or fname
        return {"type": "SelectParam",
                "selectParam": {
                    "key": "%s_%s.%s" % (out_name, dto, fname),
                    "name": fname,
                    "id": "%s.%s" % (dto, fname),
                    "fullName": "%s.%s" % (dto, fname),
                    "appName": getattr(self.c, "app_name", "") or "",
                    "description": title,
                    "position": "children",
                    "path": "%s.%s" % (str(dto).replace(".", ""), fname),
                    "outputName": out_name,
                    "dataType": dt,
                    "type": "OBJECT",
                    "javaType": _JAVA.get(dt, "java.lang.String"),
                    "dtoType": "MASTER_ENTITY",
                    "udcApp": True,
                    "multiSelect": False},
                "desc": title}

    def _event_field_ref(self, ast, out_name: str) -> dict:
        """事件触发入参的字段引用 → SelectParam（形态取自 21 条真实订阅样本）。

        position=children、key="<触发output名>_<dto全名>.<字段>"，
        其它与普通字段引用同形。
        """
        from ..udc.microflow.expression_model import JAVA as _JAVA
        ref = ast.ref or {}
        dto = ref.get("dto_id") or ""
        fname = ref.get("field") or ""
        meta = (ref.get("fields") or {}).get(fname) or {}
        dt = str(getattr(ast, "dtype", "") or meta.get("dataType") or "STRING").upper()
        title = meta.get("caption") or fname
        app_name = (self.c.app_name if hasattr(self.c, "app_name") else "") or ""
        return {"type": "SelectParam",
                "selectParam": {
                    "key": "%s_%s.%s" % (out_name, dto, fname),
                    "name": fname,
                    "id": "%s.%s" % (dto, fname),
                    "fullName": "%s.%s" % (dto, fname),
                    "appName": app_name,
                    "description": title,
                    "position": "children",
                    "path": "%s.%s" % (str(dto).replace(".", ""), fname),
                    "outputName": out_name,
                    "dataType": dt,
                    "type": "OBJECT",
                    "javaType": _JAVA.get(dt, "java.lang.String"),
                    "dtoType": "CUSTOM",
                    "udcApp": False,
                    "multiSelect": False},
                "desc": title}

    def _ref_value(self, spec: dict, n: dict, cond: bool = False,
                   attr: bool = False) -> dict:
        """{field:"ds.x"} / {ref:"res"} / {input:"id"} → SelectParam 引用。"""
        from .expression_dsl import parse_expr
        from ..udc.microflow.expression_model import NodeField

        ast = parse_expr(spec, resolver=self.resolver, scope=self.scope,
                         loops=self.loops)
        if not isinstance(ast, NodeField):
            raise GraphError("节点 %r 的值槽只支持直接引用（field/ref/input）；"
                             "复合表达式请用 op/logic/arith/fn" % n.get("id"))
        # ★ P3.1：循环项引用的出参名是 _FOR_EACH_xxx，它不是「已构建业务节点」，
        #   而是控制节点的出参。必须单独造 SelectParam（position=parent +
        #   nodeInfo.type=FOR_EACH），否则会走到普通节点分支找不到别名。
        if ast.ref.get("position") == "parent" and ast.ref.get("outputName", "").startswith("_FOR_EACH"):
            return self._loop_item_select_param(ast, n, cond)

        out_name = ast.output_name
        # ★ 流程入参（trigger.output，名形如 _FLOW_INPUT_xxx）不是「已构建节点」，
        #   直接查 by_alias 必然失败。真实形态取自语料（85 个写节点引用入参）：
        #   SelectParam{id:null, dtoType:null, udcApp:null, name=key=path=outputName=入参名,
        #   position:"parent"}，外层 desc = "<标题> [文本]"。
        if str(out_name).startswith("_FLOW_INPUT"):
            # ★ DTO 入参（MANUAL + input.dataType=DTO）取**字段**时不能引用整个变量：
            #   整变量引用会让代码生成在同一方法里重复声明同一个局部变量
            #   （实测：已在方法 ... 中定义了变量 _FLOW_INPUT_xxx，编译失败）。
            if (ast.ref or {}).get("dto_id") and (ast.ref or {}).get("field")                     and ast.ref.get("field") != out_name:
                return self._flow_input_field_ref(ast, out_name)
            return self._flow_input_ref(ast, out_name)
        # ★ 事件触发（BUSINESS_EVENT）的入参不是节点，是 trigger.output：
        #   真实 21 条样本的 SelectParam 是 position="children" + key="<触发output>_<dto>.<字段>"，
        #   照抄节点形态会报「引用了尚未执行的节点」。
        if str(out_name).startswith("_BUSINESS_EVENT"):
            return self._event_field_ref(ast, out_name)
        node = self.c.by_alias.get(out_name)
        if node is None:
            node = next((v for v in self.c.by_alias.values()
                         if (v.get("output") or {}).get("name") == out_name), None)
        if node is None:
            raise GraphError("节点 %r 引用的出参 %r 不是已构建节点（可用：%s）"
                             % (n.get("id"), out_name, sorted(self.c.by_alias)[:8]))
        fname = ast.ref.get("field")
        # ★ BASIC 标量出参（STRING/BOOLEAN/INTEGER…）没有字段可指：
        #   parse_expr 有时把输出名塞进 field，于是 fname == 输出名，
        #   走 _select_param_from_nodefield 会生成 id=<输出名>、name=<输出名>.<输出名>
        #   这种畸形引用，G17 直接判 PageInfo 残留（2026-11-01 实测）。
        #   标量一律走 _out_ref（id/dtoType 空串）。
        _o = node.get("output") or {}
        _scalar = ((_o.get("dataType") or "").upper() in
                   ("BOOLEAN", "STRING", "BIGINTEGER", "DECIMAL", "INTEGER", "DATETIME")
                   and not _o.get("dtoType"))
        if _scalar:
            fname = None
        ref = self.c.refs_field(node, fname) if fname else None
        if ref is None and fname:
            # composer.refs_field 依赖 composer._entities 里的实体模型；
            # 某些节点（循环内 RETRIEVE 等）没登记进去时，用解析器的
            # field_ref_from_node（读节点自带元数据 / 实体模型兜底）造引用。
            try:
                from ..udc.microflow.expression_model import NodeField as _NF
                got = self.resolver.field_ref_from_node(node, fname) if self.resolver else None
                if isinstance(got, _NF) and got.ref:
                    ref = self._select_param_from_nodefield(got, node, fname)
            except Exception:
                ref = None
        if ref is None:
            ref = self.c._out_ref(node)
        # ★ 查询条件右值要 CONTEXT_VARIABLE（value 是 JSON 字符串），
        #   值槽才是 SelectParam。混用平台回 BOOT_1001（无明细）。
        if cond:
            from .microflow_fields import to_context_variable
            m = getattr(node, "_entity_model", None)
            return to_context_variable(ref, m)
        return ref

    def _entity_by_dto(self, dto_full: str) -> dict | None:
        """按 DTO 全名找实体模型（供循环元素字段推导）。"""
        if not dto_full:
            return None
        for m in (getattr(self.c, "_entities", None) or {}).values():
            if m.get("fullName") == dto_full or m.get("entity") == dto_full:
                return m
        lr = getattr(self.c, "refs", None)
        if lr is None or not hasattr(lr, "entity_model"):
            return None
        try:
            got = lr.entity_model(str(self.c.app_id), self.c.app_name, dto_full=dto_full)
        except Exception:
            return None
        return got

    def _retrieve_by_loop_item(self, n: dict) -> dict:
        """循环体内 RETRIEVE(IDS, 循环项字段)：value 的 ID 引用来自循环项。

        真实链路（G20 要求）：写操作对象必须来自这个 RETRIEVE 的出参，
        不能直引 FOR_EACH（平台会生成 int→Dto，Java 编译失败）。
        """
        from . import microflow_nodes_v2 as V2
        from .expression_dsl import parse_expr

        alias = n["by_id_from"]; field = n.get("from_field") or "id"
        # ★ 必须走 self.c.entity()：它会把实体登记进 composer._entities，
        #   后续 refs_field（attrs 字段引用）靠这个表反查字段元数据。
        #   绕过它会得到 refs_field=None → attrs 落成悬空引用（G2）。
        m = self.c.entity(n["entity"])
        ast = parse_expr({"item": alias, "field": field},
                         resolver=self.resolver, scope=self.scope, loops=self.loops)
        id_ref = self._loop_item_select_param(ast, n)
        node = V2.retrieve(self.c.b, m, "", None, caption=n.get("caption") or "查询-单条",
                           id_value=id_ref,
                           null_handling=n.get("null_handling") or "CONTINUE",
                           null_message=n.get("null_message") or "")
        # ★ 必须落位到当前容器（循环体内 = 栈顶），否则节点不在流程节点表里：
        #   G10「引用的参数已失效」+ G2/G31 悬空，而且循环体是空壳。
        if self._stack:
            self._stack[-1].append(node)
        else:
            self.c.nodes.append(node)
        self._register(n["id"], node)
        n["_self_registered"] = True
        return node

    def _select_param_from_nodefield(self, nodefield, node: dict, fname: str) -> dict:
        """NodeField → attrs 用的 SelectParam（字段级）。

        ★ 形态取自语料 463 条 children 引用（2026-11-03 校准）：
          name 是**纯字段名**，不是 "<节点>.<字段>"。
          写成带点的形式会让代码生成把节点出参名当类名 →
          「找不到符号: 类 _LIST_OPERATION_xxx」（实测编译失败）。
          key = "<outputName>_<字段全名>"，path = "<dto 去点>.<字段>"。
        """
        r = nodefield.ref
        fm = (r.get("fields") or {}).get(fname) or {}
        on = r.get("outputName")
        fid = fm.get("id") or ""
        dto = fid.rsplit(".", 1)[0] if "." in fid else ""
        return {"type": "SelectParam", "selectParam": {
            "id": fid, "javaType": fm.get("javaType") or "",
            "dataType": fm.get("dataType") or "STRING", "type": "OBJECT",
            "desc": fm.get("caption") or fname,
            "name": fname, "key": "%s_%s" % (on, fid),
            "path": ("%s.%s" % (dto.replace(".", ""), fname)) if dto else "",
            "position": "children", "outputName": on,
            "appName": self.c.app_name,
            "nodeInfo": {"nodeId": node.get("nodeId"), "type": "ACTIVITY",
                         "actionType": node.get("actionType")},
            "disabled": False}}

    def _loop_item_select_param(self, ast, n: dict, cond: bool = False) -> dict:
        """循环项 → SelectParam（语料 37 条真实形态）。

        真实形态要点：
          position=parent（不是 children）
          nodeInfo={nodeId:"ForEach_xxx", type:"FOR_EACH"}（type 是 FOR_EACH，无 actionType）
          iconKey=LinedCirculation
          字段引用时 name=字段名、id=字段全名、dataType 是**字段**类型
        """
        alias = None
        for f in getattr(self.loops, "_stack", []):
            if f.output_name == ast.ref["outputName"]:
                alias = f
                break
        if alias is None:
            raise GraphError("节点 %r 引用的循环项 %r 不在当前作用域"
                             % (n.get("id"), ast.ref["outputName"]))
        field = ast.ref.get("field")
        has_field = bool(field) and field != ast.ref["outputName"]
        fm = (ast.ref.get("fields") or {}).get(field or "") or {}

        inner = {
            "description": fm.get("caption") or (field or alias.caption or alias.alias),
            "key": "%s%s" % (alias.output_name, fm.get("id") or ""),
            "name": field if has_field else alias.caption or alias.alias,
            "id": (fm.get("id") if has_field else alias.elem_dto) or "",
            "appName": fm.get("appName") or "",
            "position": "parent",
            "path": "%s.%s" % (alias.elem_dto.replace(".", ""), field) if has_field else "",
            "outputName": alias.output_name,
            "dataType": (fm.get("dataType") if has_field else alias.elem_type) or "STRING",
            "type": "OBJECT",
            "javaType": fm.get("javaType") if has_field else None,
            "dtoType": "CUSTOM" if has_field else alias.elem_type,
            "udcApp": bool(alias.elem_dto),
            "multiSelect": False,
            "customs": {"basicType": not has_field},
            "iconKey": "LinedCirculation",
            "parentLabel": "",
            "disabled": False,
            "isLeaf": not has_field,
            "nodeInfo": {"nodeId": alias.node_id, "type": "FOR_EACH"},
        }
        ref = {"type": "SelectParam", "selectParam": inner}
        if cond:
            from .microflow_fields import to_context_variable
            return to_context_variable(ref)
        return ref

    def _scalar_value_slot(self, spec: Any, n: dict, field_name: str | None = None):
        """写结果字段赋值引用**标量出参**（SIZE/SUM/MIN/MAX 等）→ 表达式（Expression）而非 SelectParam。

        ★ 根因（P7-E2E-1 实测）：SelectParam 整节点引用（name=outputName）被平台保存时
        误当成「字段引用」，规范化成「节点.节点」畸形 executableExpr，前端红「所选"命中数"已变更」。
        改用表达式（高级模式）形态，平台保存时保持正确。

        ★ 结果类型用**字段的 dataType**（不是出参节点的 dataType）：SIZE 出参是 INTEGER，
        但目标字段可能是 BIGINTEGER，表达式 resultType 声明成 INTEGER 会被一致性检测报
        NOT_BIGINTEGER（MF-01 构建暴露）。字段 dataType 缺失时回退出参 dataType。

        返回 None 表示不是标量引用（DTO 字段引用），调用方走 SelectParam 路径。
        """
        from .expression_dsl import parse_expr
        from ..udc.microflow.expression_model import (
            ExpressionCompiler, NodeField, to_value_slot)

        ast = parse_expr(spec, resolver=self.resolver, scope=self.scope,
                         loops=self.loops)
        if not isinstance(ast, NodeField):
            return None
        ref = ast.ref or {}
        ndt = (ref.get("node_dtype") or "").upper()
        if ndt not in ("BOOLEAN", "STRING", "BIGINTEGER", "DECIMAL",
                       "INTEGER", "DATETIME"):
            return None
        # ★ 写操作（CREATE_ENTITY/CHANGE_ENTITY/DELETE_ENTITY 等）的 id/影响行数
        #   出参虽然是标量（BIGINTEGER/INTEGER），但引用它必须走 SelectParam
        #   （引用节点的 id 字段），不能走表达式——表达式会被一致性检测报
        #   NOT_BIGINTEGER（MF-01 构建暴露）。只有 LIST_OPERATION 的聚合标量
        #   （SIZE/SUM/MIN/MAX）才走表达式。
        if (ref.get("node_action") or "").upper() in (
                "CREATE_ENTITY", "CHANGE_ENTITY", "DELETE_ENTITY",
                "CREATE_BATCH_ENTITY", "CHANGE_BATCH_ENTITY"):
            return None
        # ★ 结果类型 = 字段 dataType（可能宽化，如 INTEGER 的 SIZE 写进 BIGINTEGER 字段）
        rdt = (self._field_dtype(n, field_name) if field_name else None) or ndt
        if self.backend is None:
            raise GraphError("未注入表达式后端（backend），无法生成表达式")
        comp = ExpressionCompiler(result_type=rdt)
        comp.register_node_output(ref)
        out = comp.build_remote(ast, self.backend, title="")
        return to_value_slot(out)

    def _entity_fields(self, fields: dict, n: dict) -> dict:
        """实体字段映射。实体型写操作的 attrs 值必须是 SelectParam 引用
        （Simple 常量也行），不能是 CONTEXT_VARIABLE —— 那是查询条件专用。"""
        out = {}
        for k, v in (fields or {}).items():
            if _is_expr(v):
                # ★ Expression resultType 必须用目标字段 dataType（§4.22 边界2），
                #   否则 DECIMAL 字段算成 STRING，一致性检测报类型不匹配。
                out[k] = self._build_expression(v, self._field_dtype(n, k) or "STRING", n)
            elif _is_ref(v):
                # ★ 标量出参（SIZE/SUM/MIN/MAX）走表达式，避免平台把整节点引用
                #   规范成「节点.节点」畸形（前端红「已变更」）；DTO 字段走 SelectParam。
                slot = self._scalar_value_slot(v, n, field_name=k)
                out[k] = slot if slot is not None else self._ref_value(v, n, attr=True)
            elif isinstance(v, dict) and "const" in v:
                c = v["const"]
                # ★ 数值类型字段（BIGINTEGER/INTEGER/DECIMAL）的常量值必须转字符串：
                #   检测器 CheckUtils 读 attrValue.getSimple()（String）后 Long.valueOf/
                #   NumberUtil.isNumber 校验，传 int/float 会报「不是长整数类型」
                #   （UDC_MICRO_FLOW_04004 / NOT_BIGINTEGER，MF-01 构建暴露）。
                dt = self._field_dtype(n, k)
                if dt in ("BIGINTEGER", "INTEGER", "DECIMAL") \
                        and isinstance(c, (int, float)) and not isinstance(c, bool):
                    c = str(c)
                out[k] = _simple(c)
            else:
                out[k] = _simple(v)
        return out

    def _field_dtype(self, n: dict, fname: str) -> str | None:
        """实体字段的 dataType（用于常量值类型转换）。查不到返回 None。"""
        try:
            m = self.c.entity(n.get("entity", ""))
            return ((m.get("attributes") or {}).get(fname) or {}).get("dataType")
        except Exception:
            return None

    def _build_expression(self, spec: Any, result_type: str, n: dict | None = None) -> dict:
        from .expression_dsl import parse_expr
        from ..udc.microflow.expression_model import (
            ExpressionCompiler, to_value_slot)

        if self.backend is None:
            raise GraphError("未注入表达式后端（backend），无法生成表达式")
        ast = parse_expr(spec, resolver=self.resolver, scope=self.scope,
                         loops=self.loops)
        comp = ExpressionCompiler(result_type=result_type)
        for ref in getattr(ast, "_refs", []) or []:
            comp.register_node_output(ref)
        out = comp.build_remote(ast, self.backend, title="表达式")
        # ★ 含字段引用的表达式 executableExpr 只能是占位（facts §十四）：
        #   平台不会自补，必须进设计器点「确定」由平台重算。
        #   把标记挂到收集列表上，run() 汇总后交给调用方，不允许静默。
        if out.get("needs_ui_finalize"):
            self.needs_ui_finalize.append((n or {}).get("id") or "?")
        out.pop("needs_ui_finalize", None)
        # ★ 必须包成 Expression 值槽（带 type 键），否则 checkSchema 报
        #   value.type PROPERTY_IS_REQUIRED + DATA_INVALID（to_value_slot docstring）。
        return to_value_slot(out)

    def _call(self, kind: str, n: dict, kw: dict) -> dict:
        try:
            return self.c.step(kind, n["id"], **kw)
        except Exception as e:
            raise GraphError("节点 %r (%s) 构造失败: %s"
                             % (n.get("id"), kind, str(e)[:300])) from e

    def _retrieve_array_multi(self, n: dict, conds: list) -> dict:
        """多条件查询（enabled==true && id!=入参 这类）。

        composer 的 _st_retrieve_array 只支持单条件，这里补多条件：
        构造器出来后按 condition_group 逐条写 condition[]。
        """
        from . import microflow_nodes_v2 as V2
        from .microflow_fields import condition_group

        m = self.c.entity(n["entity"])
        node = V2.retrieve_array(self.c.b, m, "", None,
                                 caption=n.get("caption") or "查询-多条")
        items = []
        for c in conds:
            fname = c.get("field")
            if fname not in (m.get("attributes") or {}):
                raise GraphError("节点 %r 条件字段 %r 不存在于实体 %r（真实字段：%s）"
                                 % (n.get("id"), fname, n["entity"],
                                    list(m.get("attributes") or {})[:8]))
            # ★ operator 必须显式传：condition_group 默认 EQ，
            #   漏传会把「id != 入参」写成「id == 入参」——语义反转且平台不报错。
            op = _norm_cond_op(c.get("op"))
            g = condition_group(m, fname,
                                self._cond_value(c.get("right"), n,
                                                 entity=m, field=fname),
                                operator=op)
            items.extend(g.get("conditions") or [])

        # ★ 语料裁决（170/170 带条件的 RETRIEVE_ARRAY）：
        #   多个条件恒为「1 个 GROUP 内含 N 个 CONDITION」，
        #   从未出现「多个 GROUP 并列」。写成多 GROUP 平台回
        #   BOOT_1001 Parameter Error（无明细，极难定位）。
        node["condition"] = [{
            "type": "GROUP",
            "uuid": str(__import__("uuid").uuid4()),
            "conditions": items,
        }]
        # ★ 走 composer 的 _add：节点必须进 composer.nodes（否则 endNode/后续引用
        #   找不到它，G10 报「引用的参数已失效」），同时登记别名。
        #   不能只 by_alias——by_alias 不是节点表。
        if self._stack:
            self._stack[-1].append(node)
        else:
            self.c.nodes.append(node)
        self.c.by_alias[n["id"]] = node
        if self.resolver is not None and hasattr(self.resolver, "register_alias"):
            self.resolver.register_alias(n["id"], node)
        return node


# ---------------------------------------------------------------- 判定/原语
_EXPR_KEYS = ("op", "logic", "arith", "fn", "cond")
_REF_KEYS = ("field", "ref", "input")


_COND_OPS = {"EQ": "EQ", "NE": "NE", "GT": "GT", "GE": "GE", "LT": "LT", "LE": "LE",
             "==": "EQ", "!=": "NE", ">": "GT", ">=": "GE", "<": "LT", "<=": "LE",
             "=": "EQ", "LIKE": "LIKE", "IN": "IN"}


def _norm_cond_op(op: Any) -> str:
    """条件运算符归一（不猜，未识别直接报）。"""
    raw = str(op or "EQ").strip()
    norm = _COND_OPS.get(raw, _COND_OPS.get(raw.upper()))
    if not norm:
        raise GraphError("条件运算符 %r 不支持（可用：%s）" % (op, sorted(set(_COND_OPS.values()))))
    return norm


def _is_expr(spec: Any) -> bool:
    return isinstance(spec, dict) and any(k in spec for k in _EXPR_KEYS)


def _is_ref(spec: Any) -> bool:
    return isinstance(spec, dict) and any(k in spec for k in _REF_KEYS)


def _simple(v):
    from .microflow_fields import simple
    return v if isinstance(v, dict) else simple(v)


def _enum_desc_map(attr: dict | None) -> dict:
    """实体字段的枚举项 → {码 或 ID: 显示名}。

    ★ 语料裁决（pmp_schemas.json）：
        ENUM/CTPENUM 条件的右值是**枚举项标识**，desc 是**显示名**：
        {"value":"-3062090190298864225","desc":"投标报备申请"}
        {"value":"4975792043723663188,-3483566000920670056","desc":"投标保证金,保证金保险"}
      把 desc 也写成标识，设计器里就显示一串数字，人看不懂。

    实体模型的 attributes[f].enumItemObjects 已含 {name(码), caption(显示名)}，
    ENUM 型可直接用；CTPENUM 可能需要另外查枚举字典（见 enum_items 参数）。
    """
    m: dict[str, str] = {}
    if not isinstance(attr, dict):
        return m
    for it in (attr.get("enumItemObjects") or []):
        if not isinstance(it, dict):
            continue
        cap = it.get("caption") or it.get("desc") or ""
        for key in ("name", "id", "code", "value"):
            v = it.get(key)
            if v not in (None, "") and cap:
                m[str(v)] = cap
    return m


def _constant(v, data_type: str | None = None, enum_desc: dict | None = None):
    """查询条件右值常量：value 的类型必须**匹配左值字段的 dataType**。

    ★★ 语料裁决（pmp_schemas.json，全部 CONSTANT 条件 240 条）：

       | 左值 dataType | value 类型 | desc 类型 | 条数 |
       |---------------|-----------|-----------|------|
       | BOOLEAN       | bool      | bool      | 15   |
       | DECIMAL       | float     | float     | 1    |
       | ENUM/CTPENUM  | str(枚举标识) | str(显示名) | 175 |
       | STRING        | str       | str       | 49   |

       即：BOOLEAN 字段的条件必须写 `value: true`（JSON 布尔），
       写成 `value: "true"`（字符串）与语料 15/15 全不符 ——
       前端设计器会把它当普通文本渲染（下拉明明给的是「是/否」），
       后端按布尔校验时也拿不到布尔值。

       早期版本无条件 `str(v)`，把布尔条件全写成了字符串，是错的。

    ★ 枚举型：value 是枚举项标识（码或雪花 ID），多选用逗号拼接，
      desc 是**显示名**（同样逗号拼接）。desc 写成标识不阻断功能，
      但设计器里显示一串数字，人没法读。
    """
    from .microflow_fields import constant
    if isinstance(v, dict):
        return v
    dt = (data_type or "").upper()
    if dt == "BOOLEAN":
        b = v if isinstance(v, bool) else str(v).strip().lower() in (
            "true", "1", "yes", "y", "是")
        return {"type": "CONSTANT", "value": b, "desc": b}
    if dt in ("INTEGER", "BIGINTEGER", "LONG"):
        try:
            n = int(v)
        except (TypeError, ValueError):
            return constant(_literal(v))
        return {"type": "CONSTANT", "value": n, "desc": n}
    if dt in ("DECIMAL", "DOUBLE", "FLOAT", "NUMBER"):
        try:
            f = float(v)
        except (TypeError, ValueError):
            return constant(_literal(v))
        return {"type": "CONSTANT", "value": f, "desc": f}
    if dt in ("ENUM", "CTPENUM") and enum_desc:
        raw = _literal(v)
        parts = [p.strip() for p in str(v).split(",") if str(p).strip()]
        caps = [enum_desc.get(p, p) for p in parts]
        return {"type": "CONSTANT", "value": raw, "desc": ",".join(caps)}
    return constant(_literal(v))


def _literal(v) -> str:
    """Python 值 → 平台字面量字符串（布尔小写，其余 str）。"""
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return ""
    return str(v)
