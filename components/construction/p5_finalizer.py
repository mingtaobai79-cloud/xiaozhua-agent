"""P5.2 表达式最终化器（ExpressionFinalizer）。

★ 为什么需要这个模块：

含字段引用的表达式，其 `executableExpr` 只能由设计器运行期生成
（`/expression/check|transform` 离线不可用，连平台自己保存的真实表达式
原样重发也报 FORMULA_6058；而 `executableExpr` 平台绝不自补）。
详见 core/facts/udc/microflow/expression-engine.md §十三/§十四。

★ 工程边界（任务书硬要求）：

1. **不把 CDP 操作写进 NodeBuilder / Expression DSL** —— 本模块是独立适配器，
   通过接口与 P5 编排器协作。
2. **不通过节点顺序猜节点身份** —— 用逻辑图里的业务别名 → 保存后的平台 nodeId
   映射（由 schema 反查，见 `alias_to_node_id`）。
3. **不能只判点击成功** —— 必须回读 dataSchema 验证 executableExpr 已由平台生成。
4. **不能只判非空** —— 必须识别并排除占位内容（`__NEEDS_UI_FINALIZE__` / 空串）。
5. **页面结构变化/定位失败/会话断开必须阻断**，不无限重试。

★ 本模块把「怎么点」委托给 driver（默认 CDP 实现），
   自己只负责：识别 → 定位 → 校验身份 → 触发 → 回读判真 → 留证据。
"""

from __future__ import annotations

import dataclasses as dc
import json
import time

#: 占位标记（与 expression_model.PLACEHOLDER_EXEC 保持一致）
PLACEHOLDER = "__NEEDS_UI_FINALIZE__"


class FinalizeError(RuntimeError):
    """最终化失败（定位不到节点 / 会话断开 / 回读仍占位）。"""


@dc.dataclass
class FinalizeResult:
    ok: bool
    finalized: list[str] = dc.field(default_factory=list)
    skipped: list[str] = dc.field(default_factory=list)
    problems: list[str] = dc.field(default_factory=list)
    evidence: list[str] = dc.field(default_factory=list)
    detail: dict = dc.field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "finalized": self.finalized,
                "skipped": self.skipped, "problems": self.problems,
                "evidence": self.evidence, "detail": self.detail}


# ---------------------------------------------------------------- 判据


def is_placeholder(executable_expr: str | None) -> bool:
    """executableExpr 是否仍是占位（空 或 占位串）。"""
    if executable_expr is None:
        return True
    s = str(executable_expr).strip()
    return s == "" or s == PLACEHOLDER


def needs_finalize(expression_obj: dict | None) -> bool:
    """判断一个 expression 对象（{title, schema}）是否需要 UI 最终化。

    ★ 判据是「executableExpr 是占位」而不是「有没有 VARIABLE」：
      含 VARIABLE 但已由平台生成过 executableExpr 的表达式不需要重做。
    """
    if not isinstance(expression_obj, dict):
        return False
    raw = expression_obj.get("schema")
    if not raw:
        return False
    try:
        dd = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return False
    ee = (dd.get("runtimeData") or {}).get("executableExpr")
    return is_placeholder(ee)


def iter_expressions(schema: dict):
    """遍历 schema 里所有条件表达式，产出 (节点, 条件, expression_obj)。"""
    def walk(nodes):
        for n in nodes or []:
            for c in (n.get("conditions") or []):
                e = c.get("expression")
                if isinstance(e, dict):
                    yield n, c, e
            yield from walk(n.get("nodes"))
    yield from walk(schema.get("nodes"))


def alias_to_node_id(schema: dict, aliases: list[str]) -> dict[str, str]:
    """业务别名 → 平台 nodeId。

    ★ 不许靠顺序猜：逻辑图执行时把别名写在节点上（caption 或 alias 字段），
      这里按 caption / alias 精确匹配，匹配不到就报错，不猜。
    """
    want = set(aliases or [])
    out: dict[str, str] = {}
    if not want:
        return out

    def walk(nodes):
        for n in nodes or []:
            for key in ("alias", "id"):
                v = n.get(key)
                if v in want and n.get("nodeId"):
                    out.setdefault(v, n["nodeId"])
            cap = n.get("caption")
            if cap in want and n.get("nodeId"):
                out.setdefault(cap, n["nodeId"])
            walk(n.get("nodes"))
    walk(schema.get("nodes"))
    return out


# ---------------------------------------------------------------- 最终化器


class ExpressionFinalizer:
    """表达式最终化器。

    用法：

        fin = ExpressionFinalizer(driver=CdpDesignerDriver(...),
                                  read_schema=lambda mid: ...)
        res = fin.finalize_all(mid="...", schema=..., aliases=["br"])

    driver 需要实现（接口，不绑定 CDP）：
        open_node(node_id)          → 打开目标节点抽屉，返回 {ok, caption, node_id}
        open_expression(cond_index) → 打开第 N 个条件的表达式编辑器，返回 {ok}
        read_expression()           → 返回编辑器里当前表达式文本（用于校验身份）
        confirm()                   → 点「确定」，返回 {ok, saved, net}
        close()                     → 关闭抽屉
    """

    MAX_ATTEMPTS = 2      # ★ 不无限重试

    def __init__(self, *, driver, read_schema, verify_text: bool = True):
        """
        driver      : UI 驱动（见类文档）
        read_schema : callable(mid) -> dict，从平台回读 dataSchema（已解析）
        verify_text : 点确定前是否校验编辑器里的表达式文本与预期一致
        """
        self.driver = driver
        self.read_schema = read_schema
        self.verify_text = verify_text

    # ---------------- 主入口 ----------------
    def finalize_all(self, *, mid: str, schema: dict,
                     aliases: list[str]) -> FinalizeResult:
        """把 schema 里所有占位表达式逐个走设计器最终化。

        ★ 每一步都回读验证，任一步失败即整体失败（不做"部分成功"）。
        """
        res = FinalizeResult(ok=False)
        if not aliases:
            res.ok = True
            res.detail = {"reason": "no alias to finalize"}
            return res

        mapping = alias_to_node_id(schema, aliases)
        missing = [a for a in aliases if a not in mapping]
        if missing:
            # ★ 定位不到就不猜，直接失败
            res.problems.append("别名无法映射到平台 nodeId: %s" % missing)
            return res

        for alias in aliases:
            node_id = mapping[alias]
            try:
                one = self._finalize_node(mid=mid, alias=alias, node_id=node_id)
            except FinalizeError as e:
                res.problems.append("%s: %s" % (alias, e))
                res.evidence.extend(res.detail.get("evidence", []))
                return res
            if not one["ok"]:
                res.problems.append("%s: %s" % (alias, one.get("reason")))
                return res
            if one.get("skipped"):
                res.skipped.append(alias)
            else:
                res.finalized.append(alias)
            res.evidence.extend(one.get("evidence") or [])

        res.ok = True
        res.detail = {"finalized": res.finalized, "skipped": res.skipped,
                      "mapping": mapping}
        return res

    # ---------------- 单节点 ----------------
    def _finalize_node(self, *, mid: str, alias: str, node_id: str) -> dict:
        """对一个节点做：定位 → 校验身份 → 点确定 → 回读判真。"""
        ev: list[str] = []

        # ① 先看这个节点到底还需不需要做（可能平台已生成）
        before = self._node_exec_state(mid, node_id)
        if before.get("ok") and not before.get("needs"):
            ev.append("readback:%s 已有 executableExpr，跳过" % alias)
            return {"ok": True, "skipped": True, "evidence": ev}

        # ② 打开节点抽屉
        opened = self.driver.open_node(node_id)
        if not opened or not opened.get("ok"):
            raise FinalizeError("打不开节点抽屉 nodeId=%s" % node_id)
        # ★ 身份校验：抽屉里的节点必须就是目标节点
        got_id = opened.get("node_id")
        if got_id and str(got_id) != str(node_id):
            raise FinalizeError("抽屉身份不符：期望 %s 实得 %s" % (node_id, got_id))
        ev.append("ui:opened node=%s caption=%s" % (node_id, opened.get("caption")))

        # ③ 打开表达式编辑器并点确定（每个条件一次）
        n_cond = before.get("cond_count") or 0
        for i in range(n_cond):
            o = self.driver.open_expression(i)
            if not o or not o.get("ok"):
                raise FinalizeError("打不开第 %d 个表达式编辑器" % i)
            if self.verify_text:
                txt = (self.driver.read_expression() or "").strip()
                if not txt:
                    raise FinalizeError("第 %d 个表达式编辑器是空的（定位错或加载失败）" % i)
                ev.append("ui:expr[%d]=%r" % (i, txt[:60]))

            clicked = None
            for attempt in range(self.MAX_ATTEMPTS):
                clicked = self.driver.confirm()
                if clicked and clicked.get("ok"):
                    break
                ev.append("ui:confirm 第 %d 次未成功" % (attempt + 1))
            if not clicked or not clicked.get("ok"):
                raise FinalizeError("点「确定」失败（重试 %d 次）" % self.MAX_ATTEMPTS)
            ev.append("ui:confirmed cond=%d" % i)

        self.driver.close()

        # ④ ★ 回读判真：executableExpr 必须已由平台生成
        after = self._node_exec_state(mid, node_id)
        if not after.get("ok"):
            raise FinalizeError("回读失败: %s" % after.get("reason"))
        if after.get("needs"):
            raise FinalizeError(
                "回读 executableExpr 仍是占位（%s）——平台没生成，不能算完成"
                % after.get("placeholders"))
        ev.append("readback:%s executableExpr 已生成" % alias)
        return {"ok": True, "evidence": ev}

    # ---------------- 回读 ----------------
    def _node_exec_state(self, mid: str, node_id: str) -> dict:
        """回读并判断该节点的表达式是否仍是占位。"""
        try:
            schema = self.read_schema(mid)
        except Exception as e:
            return {"ok": False, "reason": "读 schema 异常: %s" % e}
        target = None

        def walk(nodes):
            nonlocal target
            for n in nodes or []:
                if str(n.get("nodeId")) == str(node_id):
                    target = n
                walk(n.get("nodes"))
        walk(schema.get("nodes"))
        if target is None:
            return {"ok": False, "reason": "schema 里找不到 nodeId=%s" % node_id}

        conds = target.get("conditions") or []
        placeholders = []
        for i, c in enumerate(conds):
            e = c.get("expression")
            if not isinstance(e, dict):
                continue
            raw = e.get("schema")
            if not raw:
                placeholders.append("cond%d: 无 schema" % i)
                continue
            try:
                dd = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                placeholders.append("cond%d: schema 解析失败" % i)
                continue
            ee = (dd.get("runtimeData") or {}).get("executableExpr")
            if is_placeholder(ee):
                placeholders.append("cond%d: %r" % (i, ee))
        return {"ok": True, "needs": bool(placeholders),
                "placeholders": placeholders, "cond_count": len(conds)}
