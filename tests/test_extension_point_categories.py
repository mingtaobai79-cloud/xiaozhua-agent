# -*- coding: utf-8 -*-
"""扩展点分档闸门：plain / plugin / spi 三档必须分得清、数得准。

踩过的坑：把 150 个 UDC 接口混成一张表，人按 plain 的写法去实现 PluginDefinition /
cip-connector-api 的扩展点 —— 代码能编译，但插件根本不会被加载，因为注册格式不同。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CLASSIFIED = (ROOT / "docs" / "audit" / "artifacts" / "extension-surface-20261118"
              / "extension-points-classified.json")


@pytest.fixture(scope="module")
def data():
    assert CLASSIFIED.exists(), "分档件不在盘，先跑 tools/core/platform/classify_extension_points.py"
    return json.loads(CLASSIFIED.read_text(encoding="utf-8"))


def test_counts_are_three_way(data):
    c = data["counts"]
    assert sum(c.values()) == data["total"] == 127, f"总数不对：{c}"
    assert c["plain"] == 124
    assert c["plugin"] == 3
    assert c.get("spi", 0) == 0, "UDC 表里不该出现平台 SPI（那 20 个在 cip-connector-api）"


def test_plugin_bucket_is_the_udc_plugin_subsystem(data):
    got = {p["fqn"] for p in data["points"] if p["category"] == "plugin"}
    assert got == {
        "com.seeyon.udc.PluginDefinition",
        "com.seeyon.udc.plugin.PluginExecutor",
        "com.seeyon.udc.plugin.handler.PluginHandler",
    }


def test_every_point_has_registration_hint(data):
    reg = data["registration"]
    for p in data["points"]:
        assert p["category"] in reg, f"{p['fqn']} 的档没有注册说明"
        assert reg[p["category"]], f"{p['category']} 注册说明为空"


def test_spi_catalog_supports_category_filter():
    import xiaozhua_host_bootstrap as b

    caps = b.bootstrap()
    cat = caps["spi_catalog"]
    assert cat()["categoryCounts"]["plain"] == 124
    plugin = cat(category="plugin")
    assert {p["name"] for p in plugin["points"]} == {"PluginDefinition", "PluginExecutor", "PluginHandler"}
    assert cat(term="Handler", limit=50)["points"], "term 过滤失效"


def test_code_targets_catalog_path_exists():
    """code_targets(target='spi') 以前指向 20261029 的死链，这类路径必须真实存在。"""
    from components.construction.code_targets import targets_for

    out = targets_for("spi", "demo", backend_dir=".")
    cat = out["catalog"].split("（")[0]
    assert (ROOT / cat).exists(), f"catalog 指向不存在的文件：{cat}"
    assert "extension-points-classified.json" in cat
