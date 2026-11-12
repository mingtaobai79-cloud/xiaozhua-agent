"""写执行器：授权、信封判据、失败即停。

这些测试全程不发网络请求（用桩替换 _post），验证的是控制流与判据：
  1. 未授权 → 拒绝，不发请求
  2. 业务 status!=0 → 失败，且置 scope.aborted（失败即停）
  3. HTTP 500 → 失败 + 中止
  4. 失败后下一次写直接被拒（证明"不重试"）
  5. 成功后 used 递增，超额后拒绝
  6. 写后回读被记录
  7. BOOT_0000 + status=0 才 ok（HTTP 200 单独不算）
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from components.platform_operations.write_executor import WriteExecutor
from components.platform_operations.write_scope import WriteScope

APP = "8704025620829192834"


def _exec(scope, responses):
    """构造一个把 _post 替换成队列的 executor。"""
    ex = WriteExecutor("https://example.invalid", {"Cookie": "x"}, scope=scope,
                       allow_network=True)
    seq = list(responses)

    def fake_post(path, body):
        status, resp = seq.pop(0)
        return status, resp, {}

    ex._post = fake_post
    return ex


def _scope(max_writes=5, ops=None):
    return WriteScope(application_ids={APP},
                      operations=ops or {"udc.microflow.create"},
                      max_writes=max_writes)


def test_unauthorized_write_blocked_before_request():
    s = WriteScope()          # 空 scope
    ex = WriteExecutor("https://example.invalid", {}, scope=s, allow_network=True)
    called = []
    ex._post = lambda p, b: called.append(1) or (200, {})
    ev = ex.execute("udc.microflow.create", "/x", {}, application_id=APP)
    assert not ev.ok
    assert "denied by scope" in ev.error
    assert not called, "未授权时不得发出任何请求"


def test_business_failure_aborts_and_blocks_next():
    s = _scope()
    ex = _exec(s, [
        (200, {"status": 3, "code": "BOOT_3000", "message": "业务失败"}),
    ])
    ev = ex.execute("udc.microflow.create", "/x", {}, application_id=APP)
    assert not ev.ok
    assert "业务失败" in ev.error
    assert s.aborted is True, "失败即停：scope 必须置 aborted"

    # 第二次写应直接被拒（不需要再发请求）
    ex2 = _exec(s, [(200, {"status": 0, "code": "BOOT_0000"})])
    ev2 = ex2.execute("udc.microflow.create", "/x", {}, application_id=APP)
    assert not ev2.ok
    assert "中止" in ev2.error


def test_http_500_is_failure_and_aborts():
    s = _scope()
    ex = _exec(s, [(500, {"error": "internal"})])
    ev = ex.execute("udc.microflow.create", "/x", {}, application_id=APP)
    assert not ev.ok
    assert "HTTP 500" in ev.error
    assert s.aborted


def test_success_requires_business_status_zero():
    """HTTP 200 但缺 status 字段 → 不算成功。"""
    s = _scope(max_writes=1)
    ex = _exec(s, [(200, {"data": {"content": 123}})])
    ev = ex.execute("udc.microflow.create", "/x", {}, application_id=APP)
    assert not ev.ok, "缺业务 status 不得判成功"


def test_success_increments_used():
    s = _scope(max_writes=2)
    ex = _exec(s, [
        (200, {"status": 0, "code": "BOOT_0000", "traceId": "t1", "data": {"content": 1}}),
        (200, {"status": 0, "code": "BOOT_0000", "traceId": "t2", "data": {"content": 2}}),
    ])
    e1 = ex.execute("udc.microflow.create", "/x", {}, application_id=APP)
    assert e1.ok and e1.trace_id == "t1"
    assert s.used == 1
    e2 = ex.execute("udc.microflow.create", "/x", {}, application_id=APP)
    assert e2.ok and s.used == 2
    e3 = ex.execute("udc.microflow.create", "/x", {}, application_id=APP)
    assert not e3.ok and "用尽" in e3.error


def test_readback_recorded_on_success():
    s = _scope()
    ex = _exec(s, [(200, {"status": 0, "code": "BOOT_0000", "data": {"content": 9}})])
    ev = ex.execute("udc.microflow.create", "/x", {}, application_id=APP,
                    readback=lambda: {"id": 9, "input": "ok"})
    assert ev.ok and ev.readback_ok is True
    assert ev.readback == {"id": 9, "input": "ok"}


def test_readback_error_does_not_flip_write_result():
    """回读失败不改写结果（写已成功），但必须记录。"""
    s = _scope()
    ex = _exec(s, [(200, {"status": 0, "code": "BOOT_0000"})])

    def bad():
        raise RuntimeError("db down")

    ev = ex.execute("udc.microflow.create", "/x", {}, application_id=APP, readback=bad)
    assert ev.ok is True
    assert ev.readback_ok is False
    assert "db down" in str(ev.readback)


def test_transport_exception_aborts():
    s = _scope()
    ex = WriteExecutor("https://example.invalid", {}, scope=s, allow_network=True)

    def boom(p, b):
        raise OSError("network unreachable")

    ex._post = boom
    ev = ex.execute("udc.microflow.create", "/x", {}, application_id=APP)
    assert not ev.ok and "transport" in ev.error
    assert s.aborted


def test_network_disabled_blocks_write():
    s = _scope()
    ex = WriteExecutor("https://example.invalid", {}, scope=s, allow_network=False)
    ev = ex.execute("udc.microflow.create", "/x", {}, application_id=APP)
    assert not ev.ok
    assert "allow_network" in ev.error


def test_report_shape():
    s = _scope()
    ex = _exec(s, [(200, {"status": 0, "code": "BOOT_0000"})])
    ex.execute("udc.microflow.create", "/x", {}, application_id=APP)
    rep = ex.report()
    assert rep["ok_count"] == 1 and rep["fail_count"] == 0
    assert rep["scope"]["application_ids"] == [APP]
    assert len(rep["writes"]) == 1
