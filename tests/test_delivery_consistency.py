# -*- coding: utf-8 -*-
"""交付物一致性守卫。

本轮出过一次真事故：手抄工具状态表，把 `option_set_body` / `option_set_item_body`
标成「已验证」，而 batch1 其实只验了它们的**分类**（`option_set_category_body`）。
手抄必漂，所以这里钉死三件事：

1. `tool-status.json` 覆盖的 key 必须与代码里 `TOOL_KEYS` 完全一致（不多不少不重复）
2. README 里的生成区必须与生成器输出逐字节一致（改了 JSON 忘了回写 → 红）
3. 状态字段必须是已知值，且「未验证/不通」的必须写 blocker

这样别人改状态时，忘回写 README、或漏标原因，测试会直接拦住。
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "docs" / "delivery" / "tool-status.json"
README = ROOT / "README.md"
GEN = ROOT / "tools" / "core" / "delivery" / "gen_tool_table.py"

ALLOWED_STATUS = {"VERIFIED", "PARTIAL", "UNVERIFIED", "NEEDS_AUTH", "BROKEN"}
ALLOWED_KIND = {"local", "read", "write", "delete"}


def _doc() -> dict:
    return json.loads(STATUS.read_text(encoding="utf-8"))


def _tool_keys() -> set[str]:
    sys.path.insert(0, str(ROOT))
    from adapters.mcp.server import TOOL_KEYS  # noqa: WPS433
    return set(TOOL_KEYS)


def _load_gen():
    spec = importlib.util.spec_from_file_location("gen_tool_table", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_status_covers_exactly_the_real_tool_keys():
    """JSON 必须与代码工具集一一对应 —— 少一个说明漏登记，多一个说明登记了不存在的工具。"""
    doc = _doc()
    listed = [t["key"] for t in doc["tools"]]
    real = _tool_keys()

    assert len(listed) == len(set(listed)), (
        "tool-status.json 有重复 key：%s"
        % [k for k in set(listed) if listed.count(k) > 1]
    )
    assert set(listed) == real, (
        "tool-status.json 与 TOOL_KEYS 不一致\n  缺登记: %s\n  多登记: %s"
        % (sorted(real - set(listed)), sorted(set(listed) - real))
    )


def test_every_entry_has_valid_enums():
    doc = _doc()
    bad = []
    for t in doc["tools"]:
        if t.get("status") not in ALLOWED_STATUS:
            bad.append("%s: status=%r" % (t.get("key"), t.get("status")))
        if t.get("kind") not in ALLOWED_KIND:
            bad.append("%s: kind=%r" % (t.get("key"), t.get("kind")))
        if not isinstance(t.get("write"), bool):
            bad.append("%s: write 必须是 bool" % t.get("key"))
        if not isinstance(t.get("auth"), bool):
            bad.append("%s: auth 必须是 bool" % t.get("key"))
    assert not bad, "枚举值非法：\n  " + "\n  ".join(bad)


def test_unverified_and_broken_must_explain_why():
    """「未验证」「已知不通」必须写原因 —— 不允许出现只有状态没有理由的条目。"""
    doc = _doc()
    bad = [
        t["key"]
        for t in doc["tools"]
        if t["status"] in {"UNVERIFIED", "BROKEN", "NEEDS_AUTH", "PARTIAL"}
        and not (t.get("blocker") or "").strip()
    ]
    assert not bad, (
        "这些工具标了未完成状态却没写 blocker，读者无法判断为什么：%s" % bad
    )


def test_verified_entries_do_not_claim_a_blocker():
    """已验的条目不该还挂着 blocker —— 两边矛盾说明状态没维护。"""
    doc = _doc()
    bad = [t["key"] for t in doc["tools"]
           if t["status"] == "VERIFIED" and t.get("blocker")]
    assert not bad, "这些标了 VERIFIED 却还写着 blocker：%s" % bad


def test_readme_table_matches_generator_output():
    """README 生成区必须与生成器输出逐字节一致（改了 JSON 忘回写 → 红）。"""
    gen = _load_gen()
    expected = gen.render()
    text = README.read_text(encoding="utf-8")

    assert gen.BEGIN in text and gen.END in text, "README 缺少生成标记"
    actual = text.split(gen.BEGIN, 1)[1].split(gen.END, 1)[0]
    actual = gen.BEGIN + actual + gen.END

    assert actual == expected, (
        "README 的工具表与 tool-status.json 不同步。\n"
        "跑 `python tools/core/delivery/gen_tool_table.py --write` 重新生成。"
    )


def test_counts_in_prose_are_derived_not_guessed():
    """README 开头声称的「54 个 / 42 个平台 / 21 个已验证 / 12 个本地」必须与 JSON 一致。

    这四个数字是手写的散文，最容易过期。本轮就发生过「说 20 个其实 21 个」。
    """
    doc = _doc()
    tools = doc["tools"]
    plat = [t for t in tools if t["kind"] != "local"]
    local = [t for t in tools if t["kind"] == "local"]
    plat_v = [t for t in plat if t["status"] == "VERIFIED"]

    text = README.read_text(encoding="utf-8")
    head = text[: text.index("## 1.")]  # 只看开头摘要，避免匹配到表格

    assert "**%d 个 MCP 工具**" % len(tools) in head, "开头没写对总工具数 %d" % len(tools)
    assert "平台侧 %d 个" % len(plat) in head, "开头没写对平台工具数 %d" % len(plat)
    assert "**%d 个**在 test2 真机跑过" % len(plat_v) in head, (
        "开头没写对已验证数 %d" % len(plat_v))
    assert "本地工具 %d 个" % len(local) in head, "开头没写对本地工具数 %d" % len(local)
