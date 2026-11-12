"""Drawer Locator 状态机单测（P5-R1 阶段 B）。

覆盖任务单要求的状态枚举与判据，重点是：
  * 空抽屉绝不返回 OPENED
  * 身份不符必须 DRAWER_IDENTITY_MISMATCH
  * 查看模式必须先切编辑
  * 可见性判断不能用 offsetParent（固定式元素的坑）
"""
import json

import pytest

from components.udc.microflow.live import ui


class FakeDriver:
    """按 JS 内容返回预设结果（模式匹配，不依赖调用顺序）。

    注意：这里替换的是 Driver.eval（CDP 求值方法），不是 Python 内置 eval。
    """

    def __init__(self, prompt=False, stale=-1, total=1, matched=1,
                 trigger_result="BODY_CLICK", snaps=None):
        self.prompt = prompt
        self.stale = stale
        self.total = total
        self.matched = matched
        self.trigger_result = trigger_result
        self.snaps = list(snaps or [])
        self.last = None
        self.calls = []

    def eval(self, js):
        self.calls.append(js)
        if "查看模式" in js:
            return json.dumps({"prompt": self.prompt, "hasBtn": True})
        # ★ 必须先判 snapshot：它的 JS 也含 width > 200，否则会被 stale 分支截胡
        if "bodyLen" in js:
            if self.snaps:
                self.last = self.snaps.pop(0)
            # 栈空后保持最后状态（真实环境里抽屉开着就一直开着）
            return json.dumps(self.last or {"visible": False})
        if "ant-drawer" in js and "width > 200" in js:
            return self.stale
        if "udc-microflow-editor-node-container" in js and "matched" in js:
            return json.dumps({"total": self.total, "matched": self.matched})
        if "BODY_CLICK" in js or "CARD_MOUSEDOWN" in js:
            return self.trigger_result
        if "selected|active" in js:
            return "[]"
        return "null"


def _snap(visible=False, body_len=0, title="", body_text=""):
    return {"visible": visible, "width": 1383 if visible else 0,
            "title": title, "bodyLen": body_len, "bodyText": body_text}


def test_visibility_does_not_use_offsetparent():
    """★ offsetParent 对 position:fixed 恒为 null，用它判可见会漏掉全屏 Modal。"""
    assert "offsetParent" not in ui.VIS_JS
    assert "getBoundingClientRect" in ui.VIS_JS
    assert "getComputedStyle" in ui.VIS_JS


def test_status_enum_complete():
    for name in ("OPENED", "NODE_NOT_FOUND", "NODE_NOT_SELECTED", "DRAWER_NOT_VISIBLE",
                 "DRAWER_LOADING", "DRAWER_CONTENT_EMPTY", "DRAWER_IDENTITY_MISMATCH",
                 "TIMEOUT"):
        assert getattr(ui, name) == name


def test_node_not_found():
    d = FakeDriver(matched=0, total=3)
    rep = ui.open_node_report(d, "不存在的节点", timeout=0.1)
    assert rep["status"] == ui.NODE_NOT_FOUND
    assert rep["locator_count"] == 0


def test_body_click_is_first_trigger():
    """★ node-body onClick 是实测唯一有效路径，必须排在 card_mousedown 前面。"""
    d = FakeDriver(snaps=[_snap(True, 30000, "插入数据", "组装聚合根实体")])
    rep = ui.open_node_report(d, "节点", expected_title="插入数据", timeout=5)
    assert rep["status"] == ui.OPENED
    assert "trigger[body_click]=BODY_CLICK" in " ".join(rep["diagnostic"])


def test_empty_drawer_never_opened():
    """★ 空抽屉不能返回成功——这是「假装完成」的典型。"""
    d = FakeDriver(snaps=[_snap(True, 0, "插入数据")])
    rep = ui.open_node_report(d, "节点", timeout=0.1)
    assert rep["status"] != ui.OPENED
    assert rep["status"] == ui.DRAWER_LOADING
    assert rep["drawer_visible"] is True


def test_content_empty_when_body_too_short():
    d = FakeDriver(snaps=[_snap(True, 50, "插入数据")])
    rep = ui.open_node_report(d, "节点", timeout=0.1)
    assert rep["status"] == ui.DRAWER_CONTENT_EMPTY


def test_identity_mismatch_detected():
    """抽屉打开了，但内容是别的节点 —— 必须判失败，不能当成功。"""
    d = FakeDriver(snaps=[_snap(True, 500, "更新数据", "更新数据 字段赋值")])
    rep = ui.open_node_report(d, "插入-诊断对象", timeout=0.1)
    assert rep["status"] == ui.DRAWER_IDENTITY_MISMATCH


def test_opened_when_title_matches():
    d = FakeDriver(snaps=[_snap(True, 30198, "插入数据", "组装聚合根实体单条数据 选择实体")])
    rep = ui.open_node_report(d, "节点", expected_title="插入数据", timeout=5)
    assert rep["status"] == ui.OPENED
    assert rep["drawer_title"] == "插入数据"
    assert rep["locator_count"] == 1


def test_edit_mode_prompt_detected():
    d = FakeDriver(prompt=True)
    assert ui.edit_mode_prompt(d)["prompt"] is True


def test_ensure_edit_mode_returns_true_when_no_prompt():
    d = FakeDriver(prompt=False)
    assert ui.ensure_edit_mode(d) is True


def test_stale_drawer_cleared_before_click():
    """★ 残留空壳抽屉必须先清掉，否则点击会复用空壳。"""
    d = FakeDriver(stale=0, snaps=[_snap(True, 30000, "插入数据", "内容")])
    rep = ui.open_node_report(d, "节点", expected_title="插入数据", timeout=5)
    assert "清掉残留空壳抽屉" in " ".join(rep["diagnostic"])


def test_open_node_legacy_contract():
    """旧调用方依赖 'empty drawer' 字符串，不能改坏。"""
    d = FakeDriver(matched=0)
    assert ui.open_node(d, "不存在") == "empty drawer"
