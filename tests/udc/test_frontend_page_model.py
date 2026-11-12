"""设计器前端页面功能地图模型测试（STATIC，function-map.json 派生）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.frontend_page_model import (
    PAGES, PAGE_COUNT, pages_with_direct_ops, pages_with_buttons,
    pages_with_drag, backend_contract_of, SCHEMA_ID)


def test_pages_loaded():
    assert PAGE_COUNT >= 100
    assert len(PAGES) == PAGE_COUNT


def test_direct_ops_pages_are_reliable_subset():
    d = pages_with_direct_ops()
    assert 0 < len(d) < PAGE_COUNT
    for k, v in d.items():
        assert v["direct_ops"], k
        assert all(isinstance(o, str) and o.startswith(("udc", "appCommon", "bpm", "portal", "ctp", "main")) for o in v["direct_ops"])


def test_buttons_pages_have_chinese_labels():
    b = pages_with_buttons()
    assert len(b) >= 50
    for v in list(b.values())[:20]:
        assert v["buttons"]
        assert all(any('\u4e00' <= c <= '\u9fff' for c in btn) for btn in v["buttons"])


def test_drag_pages():
    d = pages_with_drag()
    assert len(d) >= 2


def test_backend_contract_lookup():
    # 任一 direct op 的后端契约应能反查
    for v in pages_with_direct_ops().values():
        for op, be in v.get("direct_ops_backend", {}).items():
            r = backend_contract_of(op)
            assert r is not None and op in r["op"]
            break
        break


def test_direct_ops_backend_shape():
    for v in pages_with_direct_ops().values():
        for op, be in v.get("direct_ops_backend", {}).items():
            assert "Controller." in be and be.startswith("/udc/") or "Controller." in be
