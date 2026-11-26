# -*- coding: utf-8 -*-
"""构建 → 循环监听 → 拉日志：状态判定、日志归类、写入闸门。

判据不是「跑通了」，而是：
- BUILDING / TIMEOUT 不能算成功，也不能去拉「成功日志」
- 日志拉不到（BLOCKED / 抛错）不能冒充「0 error」
- 构建是写操作，没 confirm 一律拒
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from components.construction.build_watch import (  # noqa: E402
    build_and_watch, classify_lines, watch_logs,
)


class FakeResult:
    def __init__(self, ok, state):
        self.ok, self.state = ok, state

    def to_dict(self):
        return {"ok": self.ok, "state": self.state, "deployId": "d1",
                "log_tail": [], "problems": []}


class FakeBuilder:
    def __init__(self, state="SUCCESS", trigger_error=None):
        self.state, self.trigger_error, self.calls = state, trigger_error, []

    def trigger(self, deploy_type="RELEASE"):
        if self.trigger_error:
            from components.construction.p5_builder import BuildError
            raise BuildError(self.trigger_error)
        self.calls.append(("trigger", deploy_type))
        return "deploy-1"

    def wait(self, deploy_id):
        self.calls.append(("wait", deploy_id))
        return FakeResult(self.state == "SUCCESS", self.state)


def fake_search(lines, status=None):
    def _s(**kw):
        if status:
            return {"status": status, "reason": "selector 不对"}
        return {"lines": lines}
    return _s


def test_classify_splits_error_and_warn():
    c = classify_lines([
        "2026-11-25 10:00 INFO 应用启动",
        "ERROR c.s.u.Service - 保存失败",
        "Caused by: java.lang.NullPointerException",
        "WARN cache miss",
        "ERROR c.s.u.Service - 保存失败",   # 重复行只算一次
    ])
    assert c["errorCount"] == 2 and c["warnCount"] == 1
    assert any("NullPointer" in e for e in c["errors"])


def test_watch_logs_dedupes_across_rounds():
    calls = {"n": 0}

    def s(**kw):
        calls["n"] += 1
        return {"lines": ["ERROR boot failed", "INFO round %d" % calls["n"]]}

    r = watch_logs(rounds=3, interval_s=0, search=s, sleep=lambda _: None)
    assert [x["new"] for x in r["rounds"]] == [2, 1, 1], "跨轮去重没生效"
    assert r["errorCount"] == 1


def test_watch_logs_blocked_is_not_zero_error():
    r = watch_logs(rounds=2, interval_s=0, search=fake_search([], status="BLOCKED"),
                   sleep=lambda _: None)
    assert r["failedRounds"] and r["errorCount"] == 0
    assert "别把 0 error 当结论" in r["note"]


def test_build_failed_pulls_one_round_logs():
    b = FakeBuilder(state="FAILED")
    out = build_and_watch(host="h", cookie="c", app_id="1", builder=b,
                          search=fake_search(["ERROR compile failed"]),
                          sleep=lambda _: None)
    assert out["state"] == "FAILED" and out["ok"] is False
    assert out["phase"] == "logs-failure"
    assert out["logs"]["errorCount"] == 1


def test_build_success_watches_multiple_rounds():
    b = FakeBuilder(state="SUCCESS")
    out = build_and_watch(host="h", cookie="c", app_id="1", builder=b, rounds=3,
                          interval_s=0, search=fake_search(["ERROR npe at start"]),
                          sleep=lambda _: None)
    assert out["state"] == "SUCCESS" and out["ok"] is True
    assert out["phase"] == "logs-watch" and len(out["logs"]["rounds"]) == 3


def test_building_is_not_success_and_no_logs():
    b = FakeBuilder(state="BUILDING")
    out = build_and_watch(host="h", cookie="c", app_id="1", builder=b,
                          search=fake_search(["ERROR whatever"]), sleep=lambda _: None)
    assert out["ok"] is False and out["phase"] == "done"
    assert "BUILDING" in out["note"] and "logs" not in out


def test_trigger_error_reported():
    b = FakeBuilder(trigger_error="code=BOOT_0001 msg=无权限")
    out = build_and_watch(host="h", cookie="c", app_id="1", builder=b, sleep=lambda _: None)
    assert out["phase"] == "trigger" and "BOOT_0001" in out["error"]


def test_build_watch_requires_network_and_confirm():
    import xiaozhua_host_bootstrap as bmod

    caps = bmod.bootstrap()
    r = caps["build_watch"]("123")
    assert r["status"] == "BLOCKED" and "allow_network" in r["reason"]

    caps2 = bmod.bootstrap(allow_network=True)
    r2 = caps2["build_watch"]("123")
    assert r2["status"] == "BLOCKED" and "confirm" in r2["reason"]
    assert r2["wouldDo"]["appId"] == "123"
