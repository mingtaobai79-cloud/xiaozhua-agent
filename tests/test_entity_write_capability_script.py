"""能力表扫描脚本的三档自检。

为什么单测这个：扫错的形态**不是报错**，而是「所有实体 has_create=false」
或「表达式数恒 0」——看起来完全合理，后果是 G34 拦掉全部流程（或一条不拦），
没人会怀疑闸门。所以脚本必须自己以非零退出码报出来，且这个行为要有测试钉住。
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "scripts"))

from entity_write_capability import self_check  # noqa: E402


def _caps(entities):
    return {"entities": entities}


def test_empty_scan_is_rejected():
    """① 一个实体都没扫到 → 一定是 glob 口径错，必须报。"""
    problems = self_check(_caps({}))
    assert problems, "空表必须被判为不可用"
    assert any("glob 口径" in p or "为 0" in p for p in problems)


def test_all_without_create_is_rejected():
    """② 所有实体 has_create=false → 口径错，不是真没有。"""
    problems = self_check(_caps({
        "A": {"has_create": False, "fields": {"x": {"require_null": False}}},
        "B": {"has_create": False, "fields": {}},
    }))
    assert any("为 0" in p for p in problems)


def test_no_overridden_field_is_rejected():
    """③ 有实体有 create 但没有任何覆盖字段 → G35 永不触发，必须报。"""
    problems = self_check(_caps({
        "A": {"has_create": True, "fields": {}},
        "B": {"has_create": True, "fields": {"x": {"require_null": True}}},
    }))
    assert any("G35 永远不会触发" in p or "require_null=false" in p for p in problems)


def test_healthy_scan_passes():
    """正常表（有 create + 至少一个覆盖字段）应通过。"""
    assert self_check(_caps({
        "A": {"has_create": True, "fields": {"x": {"require_null": False}}},
        "B": {"has_create": False, "fields": {}},
    })) == []


def test_committed_capability_table_is_healthy():
    """仓库里已提交的能力表必须能过自检（防止提交一张坏表）。"""
    import json
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "core", "facts", "udc", "microflow",
                        "entity-write-capability.json")
    table = json.load(open(path, encoding="utf-8"))
    problems = self_check(table)
    assert not problems, "已提交的能力表未通过自检: %s" % problems
