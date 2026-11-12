"""写通道授权：默认 fail-closed，只有显式 WriteScope 才放行。

这是把仓库从"只读骨架"扩到"受控可写"的关键一层，所以必须先证明：
不传 WriteScope 时**一切写仍然被拒**，行为与改动前完全一致。

约束（用户 2026-10-20 明确授权）：
  应用     仅 datamigration9000000000000000001（test2）
  失败语义 失败即停，不重试
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

import pytest

from components.platform_operations.write_scope import WriteScope

APP = "8704025620829192834"


def test_empty_scope_denies_everything():
    """默认构造的 scope 不允许任何写（fail-closed）。"""
    s = WriteScope()
    ok, why = s.allows("udc.entity.create", APP)
    assert not ok
    assert "fail-closed" in why


def test_scope_allows_only_whitelisted_operation():
    s = WriteScope(application_ids={APP}, operations={"udc.entity.create"}, max_writes=5)
    assert s.allows("udc.entity.create", APP)[0] is True
    ok, why = s.allows("udc.entity.delete", APP)
    assert not ok and "白名单" in why


def test_scope_allows_only_whitelisted_application():
    s = WriteScope(application_ids={APP}, operations={"udc.entity.create"}, max_writes=5)
    ok, why = s.allows("udc.entity.create", "9999999999999999999")
    assert not ok and "应用" in why


def test_max_writes_exhausts():
    s = WriteScope(application_ids={APP}, operations={"udc.entity.create"}, max_writes=2)
    assert s.allows("udc.entity.create", APP)[0]
    s.record_success()
    assert s.allows("udc.entity.create", APP)[0]
    s.record_success()
    ok, why = s.allows("udc.entity.create", APP)
    assert not ok and "用尽" in why


def test_failure_aborts_immediately_no_retry():
    """失败即停：record_failure 后所有后续写一律拒绝，不重试。"""
    s = WriteScope(application_ids={APP}, operations={"udc.entity.create"}, max_writes=99)
    s.record_failure("平台返回 BOOT_1000")
    ok, why = s.allows("udc.entity.create", APP)
    assert not ok
    assert "中止" in why
    assert "不重试" in why


def test_snapshot_is_auditable():
    s = WriteScope(application_ids={APP}, operations={"a", "b"}, max_writes=3,
                   reason="user authorized")
    s.record_success()
    snap = s.snapshot()
    assert snap["used"] == 1 and snap["remaining"] == 2
    assert snap["application_ids"] == [APP]
    assert snap["operations"] == ["a", "b"]
    assert snap["aborted"] is False


def test_application_id_compared_as_string():
    """appId 可能是 int 也可能是 '前缀+数字'，比较须归一为字符串。"""
    s = WriteScope(application_ids={APP}, operations={"op"}, max_writes=1)
    assert s.allows("op", int(APP))[0] is True
