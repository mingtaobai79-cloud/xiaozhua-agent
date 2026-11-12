"""React 受控组件交互原语的结构测试（不连浏览器，只验 JS 模板正确性）。"""
from __future__ import annotations

import importlib.util
import os

import pytest

PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "components", "udc", "microflow", "live", "react_click.py",
)


@pytest.fixture(scope="module")
def rc():
    spec = importlib.util.spec_from_file_location("react_click_under_test", PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_module_exports_four_primitives(rc):
    """四个原语都在"""
    for name in ("react_click", "set_controlled_input",
                 "open_antd_select", "pick_option"):
        assert callable(getattr(rc, name)), name


def test_react_click_js_uses_props_onclick(rc):
    """react_click 必须走 __reactProps$ 的 onClick，不是 el.click()"""
    js = rc._REACT_CLICK_JS
    assert "__reactProps$" in js
    assert "onClick" in js
    # 必须有 fiber 回退
    assert "__reactFiber$" in js
    # 不能只靠 DOM click
    assert ".click()" not in js


def test_set_input_js_bypasses_value_tracker(rc):
    """受控 input 必须用原型 setter 绕过 React value tracker"""
    js = rc._SET_INPUT_JS
    assert "getOwnPropertyDescriptor" in js
    assert "HTMLInputElement.prototype" in js
    assert "HTMLTextAreaElement.prototype" in js
    # 三个事件都要派发
    for ev in ("input", "change", "blur"):
        assert ev in js, ev


def test_open_select_js_dispatches_three_events(rc):
    """antd Select 需要 mousedown+mouseup+click 序列"""
    js = rc._OPEN_SELECT_JS
    for ev in ("mousedown", "mouseup", "click"):
        assert ev in js, ev


def test_pick_option_handles_both_dropdown_kinds(rc):
    """下拉项兼容普通 option 与 tree node"""
    js = rc._PICK_OPTION_JS
    assert "ant-select-item-option" in js
    assert "ant-select-tree-treenode" in js
    assert "hidden" in js  # 必须过滤隐藏的 dropdown


def test_react_click_supports_scoping(rc):
    """react_click 支持 root 限定范围（抽屉内 vs 全局）"""
    js = rc._REACT_CLICK_JS
    assert "scope" in js
    assert "querySelector(root)" in js or "document.querySelector(root)" in js
