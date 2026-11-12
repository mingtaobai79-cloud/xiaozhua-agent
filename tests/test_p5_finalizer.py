"""P5.2 ExpressionFinalizer 测试（假 driver，不碰平台）。"""
import json
import sys

import pytest

sys.path.insert(0, ".")

from components.construction.p5_finalizer import (
    ExpressionFinalizer, FinalizeError, PLACEHOLDER, alias_to_node_id,
    is_placeholder, iter_expressions, needs_finalize)


# ---------------------------------------------------------------- 判据

def test_is_placeholder_forms():
    assert is_placeholder(None)
    assert is_placeholder("")
    assert is_placeholder("   ")
    assert is_placeholder(PLACEHOLDER)
    assert not is_placeholder("entityIsNotNull(_A._A.f)")


def _expr_obj(exec_val):
    return {"title": "t", "schema": json.dumps(
        {"designData": {"tokens": []},
         "runtimeData": {"executableExpr": exec_val}})}


def test_needs_finalize_true_for_placeholder():
    assert needs_finalize(_expr_obj(PLACEHOLDER))
    assert needs_finalize(_expr_obj(""))


def test_needs_finalize_false_for_real_exec():
    """★ 已由平台生成过的表达式不需要重做。"""
    assert not needs_finalize(_expr_obj("entityIsNotNull(_A._A.f)"))


def test_needs_finalize_handles_bad_input():
    assert not needs_finalize(None)
    assert not needs_finalize({})
    assert not needs_finalize({"title": "t"})
    assert not needs_finalize({"title": "t", "schema": "not-json"})


def test_iter_expressions_walks_nested():
    inner = _expr_obj(PLACEHOLDER)
    schema = {"nodes": [
        {"nodeId": "FE", "nodes": [
            {"nodeId": "B2", "conditions": [{"expression": inner}]}]}]}
    found = list(iter_expressions(schema))
    assert len(found) == 1 and found[0][0]["nodeId"] == "B2"


# ---------------------------------------------------------------- 别名映射

def test_alias_to_node_id_by_alias_field():
    schema = {"nodes": [{"alias": "br", "nodeId": "BRANCH_1"}]}
    assert alias_to_node_id(schema, ["br"]) == {"br": "BRANCH_1"}


def test_alias_to_node_id_by_caption():
    schema = {"nodes": [{"caption": "判断", "nodeId": "BRANCH_2"}]}
    assert alias_to_node_id(schema, ["判断"]) == {"判断": "BRANCH_2"}


def test_alias_to_node_id_nested():
    schema = {"nodes": [{"nodeId": "FE", "nodes": [
        {"caption": "内层判断", "nodeId": "B3"}]}]}
    assert alias_to_node_id(schema, ["内层判断"]) == {"内层判断": "B3"}


def test_alias_to_node_id_no_guess():
    """★ 找不到就返回空，绝不按顺序猜。"""
    schema = {"nodes": [{"caption": "别的", "nodeId": "X"}]}
    assert alias_to_node_id(schema, ["br"]) == {}


# ---------------------------------------------------------------- 假 driver

class FakeDriver:
    """模拟设计器。platform 是「平台侧」的 schema，confirm 会写入 executableExpr。"""

    def __init__(self, platform: dict, *, open_fail=False, confirm_fail=False,
                 wrong_node=False, empty_expr=False, no_generate=False,
                 expr_text="X == 1"):
        self.platform = platform
        self.open_fail = open_fail
        self.confirm_fail = confirm_fail
        self.wrong_node = wrong_node
        self.empty_expr = empty_expr
        self.no_generate = no_generate
        self.expr_text = expr_text
        self.calls: list[str] = []
        self._cur = None

    def _find(self, node_id):
        def walk(nodes):
            for n in nodes or []:
                if str(n.get("nodeId")) == str(node_id):
                    return n
                r = walk(n.get("nodes"))
                if r:
                    return r
            return None
        return walk(self.platform.get("nodes"))

    def open_node(self, node_id):
        self.calls.append("open:%s" % node_id)
        if self.open_fail:
            return {"ok": False}
        self._cur = node_id
        n = self._find(node_id)
        got = ("WRONG" if self.wrong_node else node_id)
        return {"ok": True, "node_id": got,
                "caption": (n or {}).get("caption")}

    def open_expression(self, i):
        self.calls.append("expr:%d" % i)
        return {"ok": True}

    def read_expression(self):
        return "" if self.empty_expr else self.expr_text

    def confirm(self):
        self.calls.append("confirm")
        if self.confirm_fail:
            return {"ok": False}
        if not self.no_generate:
            n = self._find(self._cur)
            for c in (n or {}).get("conditions") or []:
                e = c.get("expression") or {}
                raw = e.get("schema")
                if not raw:
                    continue
                dd = json.loads(raw) if isinstance(raw, str) else raw
                dd.setdefault("runtimeData", {})["executableExpr"] = "GENERATED_BY_UI"
                e["schema"] = json.dumps(dd)
        return {"ok": True, "saved": True}

    def close(self):
        self.calls.append("close")


def _platform_schema(exec_val=PLACEHOLDER, node_id="BRANCH_1", caption="判断"):
    return {"nodes": [
        {"nodeId": node_id, "caption": caption, "type": "BRANCH",
         "conditions": [{"expression": _expr_obj(exec_val)}]}]}


def _fin(driver, platform):
    return ExpressionFinalizer(driver=driver,
                               read_schema=lambda mid: platform)


# ---------------------------------------------------------------- 主流程

def test_finalize_success():
    plat = _platform_schema()
    d = FakeDriver(plat)
    res = _fin(d, plat).finalize_all(mid="m1", schema=plat, aliases=["判断"])
    assert res.ok
    assert res.finalized == ["判断"]
    # 回读已生成
    ee = json.loads(plat["nodes"][0]["conditions"][0]["expression"]["schema"])
    assert ee["runtimeData"]["executableExpr"] == "GENERATED_BY_UI"
    assert any("readback" in e for e in res.evidence)


def test_finalize_skips_when_already_generated():
    """★ 平台已生成过 → 跳过，不重复点。"""
    plat = _platform_schema(exec_val="entityIsNotNull(_A._A.f)")
    d = FakeDriver(plat)
    res = _fin(d, plat).finalize_all(mid="m1", schema=plat, aliases=["判断"])
    assert res.ok and res.skipped == ["判断"]
    assert not any(c.startswith("confirm") for c in d.calls)


def test_finalize_empty_alias_is_ok():
    res = ExpressionFinalizer(driver=FakeDriver({}), read_schema=lambda m: {}) \
        .finalize_all(mid="m1", schema={}, aliases=[])
    assert res.ok and "no alias" in res.detail.get("reason", "")


def test_finalize_unmappable_alias_fails():
    """★ 别名映射不到 nodeId 时不许猜，直接失败。"""
    plat = _platform_schema()
    res = _fin(FakeDriver(plat), plat).finalize_all(
        mid="m1", schema=plat, aliases=["不存在的别名"])
    assert not res.ok
    assert "无法映射" in res.problems[0]


def test_finalize_open_failure_blocks():
    plat = _platform_schema()
    res = _fin(FakeDriver(plat, open_fail=True), plat).finalize_all(
        mid="m1", schema=plat, aliases=["判断"])
    assert not res.ok and "打不开节点抽屉" in res.problems[0]


def test_finalize_wrong_node_identity_blocks():
    """★ 抽屉身份不符必须阻断，不能盲点。"""
    plat = _platform_schema()
    res = _fin(FakeDriver(plat, wrong_node=True), plat).finalize_all(
        mid="m1", schema=plat, aliases=["判断"])
    assert not res.ok and "身份不符" in res.problems[0]


def test_finalize_empty_editor_blocks():
    plat = _platform_schema()
    res = _fin(FakeDriver(plat, empty_expr=True), plat).finalize_all(
        mid="m1", schema=plat, aliases=["判断"])
    assert not res.ok and "空的" in res.problems[0]


def test_finalize_confirm_failure_blocks():
    plat = _platform_schema()
    res = _fin(FakeDriver(plat, confirm_fail=True), plat).finalize_all(
        mid="m1", schema=plat, aliases=["判断"])
    assert not res.ok and "点「确定」失败" in res.problems[0]


def test_finalize_readback_still_placeholder_blocks():
    """★★ 核心闸门：点成功了但平台没生成 executableExpr → 必须失败。"""
    plat = _platform_schema()
    res = _fin(FakeDriver(plat, no_generate=True), plat).finalize_all(
        mid="m1", schema=plat, aliases=["判断"])
    assert not res.ok
    assert "仍是占位" in res.problems[0]


def test_finalize_read_schema_exception_blocks():
    plat = _platform_schema()

    def boom(mid):
        raise RuntimeError("平台 500")
    fin = ExpressionFinalizer(driver=FakeDriver(plat), read_schema=boom)
    res = fin.finalize_all(mid="m1", schema=plat, aliases=["判断"])
    assert not res.ok


def test_finalize_retries_bounded():
    """★ 点确定失败只重试 MAX_ATTEMPTS 次，不无限重试。"""
    plat = _platform_schema()
    d = FakeDriver(plat, confirm_fail=True)
    _fin(d, plat).finalize_all(mid="m1", schema=plat, aliases=["判断"])
    assert d.calls.count("confirm") == ExpressionFinalizer.MAX_ATTEMPTS


def test_finalize_multiple_conditions():
    """一个节点多个条件表达式时逐个处理。"""
    plat = {"nodes": [{"nodeId": "B", "caption": "多条件", "type": "BRANCH",
                       "conditions": [{"expression": _expr_obj(PLACEHOLDER)},
                                      {"expression": _expr_obj(PLACEHOLDER)}]}]}
    d = FakeDriver(plat)
    res = _fin(d, plat).finalize_all(mid="m1", schema=plat, aliases=["多条件"])
    assert res.ok
    assert d.calls.count("confirm") == 2


def test_finalize_nested_node():
    plat = {"nodes": [{"nodeId": "FE", "type": "FOR_EACH", "nodes": [
        {"nodeId": "B2", "caption": "内层判断", "type": "BRANCH",
         "conditions": [{"expression": _expr_obj(PLACEHOLDER)}]}]}]}
    d = FakeDriver(plat)
    res = _fin(d, plat).finalize_all(mid="m1", schema=plat, aliases=["内层判断"])
    assert res.ok and res.finalized == ["内层判断"]


def test_finalize_node_not_found_in_readback():
    plat = _platform_schema()
    d = FakeDriver(plat)
    fin = ExpressionFinalizer(driver=d,
                              read_schema=lambda m: {"nodes": []})
    res = fin.finalize_all(mid="m1", schema=plat, aliases=["判断"])
    # 第一次回读就找不到节点 → needs 为 None → 直接失败
    assert not res.ok


def test_result_to_dict_serializable():
    plat = _platform_schema()
    res = _fin(FakeDriver(plat), plat).finalize_all(
        mid="m1", schema=plat, aliases=["判断"])
    json.dumps(res.to_dict())
