"""运行日志读侧的回归防护。

★ 核心教训：前缀是**应用名**，不是 `udc`。
   拼错时报「udc-runtime 服务不存在，请重启服务或重新发布应用后再试！」，
   这句话听起来像运行时挂了，实际只是路径错。
"""
import pytest

from components.udc.microflow.live import runtime_log as RL


def _row(code="rtprobe1", success=True, start="1793540000000", end="1793540000006"):
    return {"microFlowCode": code, "caption": code, "success": success,
            "logStartTime": start, "logEndTime": end,
            "moduleType": "MICRO_FLOW", "subModuleType": "MICRO_FLOW_SCHEDULE"}


def test_log_path_prefix_is_app_name_not_udc(monkeypatch):
    """★ 前缀必须是 /service/{appName}/udc-runtime/...，不是 /service/udc-runtime/...。"""
    seen = {}

    def fake_post(host, path, cookie, body, timeout=60):
        seen["path"] = path
        return {"code": "BOOT_0000", "data": {"content": [], "pageInfo": {"total": 0}}}

    monkeypatch.setattr(RL, "_post", fake_post)
    RL.search_microflow_log("https://h", "ck", "myapp123")
    assert seen["path"] == "/service/myapp123/udc-runtime/app-log/search/microflow"
    assert "/service/udc-runtime/" not in seen["path"]


def test_log_kinds(monkeypatch):
    """三种日志只差最后一段。"""
    seen = []

    def fake_post(host, path, cookie, body, timeout=60):
        seen.append(path)
        return {"code": "BOOT_0000", "data": {"content": [], "pageInfo": {}}}

    monkeypatch.setattr(RL, "_post", fake_post)
    for k in RL.LOG_KINDS:
        RL.search_microflow_log("https://h", "ck", "a", kind=k)
    assert seen == ["/service/a/udc-runtime/app-log/search/%s" % k
                    for k in RL.LOG_KINDS]


def test_empty_rows_is_not_failure(monkeypatch):
    """空列表是「无该类日志」，code 才是判据。"""
    monkeypatch.setattr(RL, "_post", lambda *a, **k: {
        "code": "BOOT_0000", "data": {"content": [], "pageInfo": {"total": 0}}})
    r = RL.search_microflow_log("https://h", "ck", "a")
    assert r["rows"] == [] and r["code"] == "BOOT_0000"


def test_assert_ran_raises_when_no_record(monkeypatch):
    """★ 日志里没有该流程的记录 → 抛错，绝不能当通过。"""
    monkeypatch.setattr(RL, "fetch_all", lambda *a, **k: [_row("other")])
    with pytest.raises(RuntimeError, match="不能判 RUNTIME_VERIFIED"):
        RL.assert_ran("https://h", "ck", "a", "rtprobe1")


def test_assert_ran_raises_on_failure(monkeypatch):
    monkeypatch.setattr(RL, "fetch_all",
                        lambda *a, **k: [_row("rtprobe1", success=False)])
    with pytest.raises(RuntimeError, match="运行失败"):
        RL.assert_ran("https://h", "ck", "a", "rtprobe1")


def test_assert_ran_ok(monkeypatch):
    monkeypatch.setattr(RL, "fetch_all", lambda *a, **k: [_row("rtprobe1")])
    r = RL.assert_ran("https://h", "ck", "a", "rtprobe1")
    assert r["runs"] == 1


def test_summarize_counts_and_duration():
    rows = [_row("a", True, "1000", "1006"), _row("a", True, "2000", "2200"),
            _row("b", False, "3000", "3010")]
    s = RL.summarize(rows)
    assert s["total"] == 3 and s["success"] == 2 and s["failed"] == 1
    assert s["by_flow"] == {"a": 2, "b": 1}
    assert s["duration_ms"]["min"] == 6 and s["duration_ms"]["max"] == 200
