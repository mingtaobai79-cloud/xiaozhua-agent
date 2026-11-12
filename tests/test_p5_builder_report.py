"""P5.3 构建验证 + P5.4 报告/断点恢复 测试（纯本地）。"""
import json
import os
import sys

import pytest

sys.path.insert(0, ".")

from components.construction.p5_builder import (
    BUILD_SEMANTICS_NOTE, BuildError, BuildResult, PlatformBuilder, attach_semantics)
from components.construction.p5_report import (
    load_report, plan_resume, render_summary, report_path, save_report)


# ---------------------------------------------------------------- 假 HTTP

class FakeHttp:
    def __init__(self, *, deploy_resp=None, states=None, raise_on_get=False):
        self.deploy_resp = deploy_resp or {"code": 0, "data": {"deployId": "D1"}}
        self.states = list(states or [])
        self.raise_on_get = raise_on_get
        self.posts: list[tuple] = []
        self.gets: list[str] = []

    def post_json(self, path, body):
        self.posts.append((path, body))
        return self.deploy_resp

    def get_json(self, path):
        self.gets.append(path)
        if self.raise_on_get:
            raise RuntimeError("网络断了")
        if self.states:
            return self.states.pop(0)
        return {"state": "BUILDING", "progress": "50"}


def _b(http, **kw):
    return PlatformBuilder(http=http, app_id="APP1", sleep=lambda s: None, **kw)


# ---------------------------------------------------------------- 触发

def test_trigger_wraps_body_in_deploy_dto():
    """★★ body 必须包在 deployDto 里（@MultiRequestBody，平铺即 EL1007E）。"""
    h = FakeHttp()
    _b(h).trigger()
    path, body = h.posts[0]
    assert path == "/service/udc/runtime/deploy-normal"
    assert "deployDto" in body
    assert body["deployDto"]["appId"] == "APP1"
    assert body["deployDto"]["deployType"] == "RELEASE"
    assert body["deployDto"]["projectType"] == "ALL"
    assert body["deployDto"]["terminalType"] == "ALL"


def test_trigger_returns_deploy_id():
    h = FakeHttp()
    assert _b(h).trigger() == "D1"


def test_trigger_accepts_platform_boot_success_code():
    """★ 平台成功码是字符串 BOOT_0000，不是数字 0 —— 只认 0 会全判失败。"""
    class H:
        def post_json(self, p, b):
            # wait() 有 deploy_id 时走 GraphQL 状态查询，要区分两种请求
            if "query" in b:
                return {"data": {"data0": {"code": "BOOT_0000",
                                           "data": {"content": [{"state": "SUCCESS"}]}}}}
            return {"code": "BOOT_0000", "status": 0,
                    "data": {"content": {"validate": True, "deployId": "D999"}}}

        def get_json(self, p):
            return {"code": "BOOT_0000",
                    "data": {"content": {"state": "SUCCESS"}}}

    b = PlatformBuilder(http=H(), app_id="A", sleep=lambda s: None)
    assert b.trigger() == "D999"
    assert b.wait("D999").ok


def test_trigger_reads_deploy_id_from_content_envelope():
    """★ deployId 在 data.content 里，直接读 data.deployId 会拿到 None。"""
    class H:
        def post_json(self, p, b):
            return {"code": "BOOT_0000",
                    "data": {"content": {"deployId": "D777"}}}

        def get_json(self, p):
            return {"state": "SUCCESS"}

    assert PlatformBuilder(http=H(), app_id="A",
                           sleep=lambda s: None).trigger() == "D777"


def test_trigger_rejects_business_error_code():
    """BOOT_1006 这类业务错误码必须当失败。"""
    h = FakeHttp(deploy_resp={"code": "BOOT_1006", "message": "token黑名单"})
    with pytest.raises(BuildError):
        _b(h).trigger()


# ---------------------------------------------------------------- 陈旧状态（★ 真实踩坑）
#
# delta-build-info 只保留「最近一次完成」的结果：
#   新构建进行中 → 返回全空（state=None）
#   新构建还没覆盖 → 返回上一次的终态（可能是 FAIL）
# 不判新旧，wait 会立刻读到上一次的 FAIL 并误判本次失败。

def test_wait_ignores_stale_fail_from_previous_build():
    """★★ 上一次构建的 FAIL 不能被当成本次结果。"""
    baseline = {"state": "FAIL", "startTime": 1000, "progress": "18"}
    stale = {"code": "BOOT_0000",
             "data": {"content": {"state": "FAIL", "startTime": 1000,
                                  "progress": "18",
                                  "logs": ["[ERROR] 旧的失败"]}}}
    fresh = {"code": "BOOT_0000",
             "data": {"content": {"state": "SUCCESS", "startTime": 2000,
                                  "progress": "100"}}}
    h = FakeHttp(states=[stale, stale, fresh])
    r = _b(h).wait("D1", baseline=baseline)
    assert r.ok and r.state == "SUCCESS"
    # 必须读过至少 3 次（前两次旧结果被跳过）
    assert len(h.gets) >= 3


def test_wait_ignores_stale_success_from_previous_build():
    """★ 反向同理：上一次的 SUCCESS 不能冒充本次成功。"""
    baseline = {"state": "SUCCESS", "startTime": 1000}
    stale = {"state": "SUCCESS", "startTime": 1000, "progress": "100"}
    fresh = {"state": "FAIL", "startTime": 3000, "progress": "18",
             "logs": ["[ERROR] 本次真的失败了"]}
    h = FakeHttp(states=[stale, fresh])
    r = _b(h).wait("D1", baseline=baseline)
    assert not r.ok and r.state == "FAIL"


def test_wait_without_baseline_keeps_old_behavior():
    """没给基线时不做陈旧判定（保持向后兼容）。"""
    h = FakeHttp(states=[{"state": "FAIL", "startTime": 1000,
                          "logs": ["[ERROR] x"]}])
    r = _b(h).wait("D1")
    assert r.state == "FAIL"


def test_build_takes_baseline_before_trigger():
    """★ build() 必须在触发前拍基线，否则无法区分新旧构建。"""
    baseline = {"state": "FAIL", "startTime": 1000}
    stale = {"state": "FAIL", "startTime": 1000, "logs": ["[ERROR] 旧的"]}
    fresh = {"state": "SUCCESS", "startTime": 5000, "progress": "100"}

    class H:
        def __init__(self):
            self.calls = 0
            self.posts = []

        def post_json(self, p, b):
            self.posts.append((p, b))
            return {"code": "BOOT_0000",
                    "data": {"content": {"deployId": "D9"}}}

        def get_json(self, p):
            self.calls += 1
            return stale if self.calls <= 2 else fresh

    h = H()
    b = PlatformBuilder(http=h, app_id="A", sleep=lambda s: None)
    # 第一次 get 是基线快照
    r = b.build()
    assert r.ok, r.problems
    assert h.calls >= 3


def test_wait_timeout_reports_stale_seen():
    """超时且一直读到旧结果时，要说明「读过几次残留」。"""
    baseline = {"state": "FAIL", "startTime": 1000}
    stale = {"state": "FAIL", "startTime": 1000}

    class H:
        def get_json(self, p):
            return stale

    # ★ 假时钟必须单调递增：patch 成常量会让 while 条件永远为真 → 死循环
    clock = {"t": 0.0}

    def fake_sleep(sec):
        clock["t"] += 10.0

    import components.construction.p5_builder as PB
    b = PlatformBuilder(http=H(), app_id="A", sleep=fake_sleep, timeout_s=25)
    orig = PB.time.time
    try:
        PB.time.time = lambda: clock["t"]
        r = b.wait("D1", baseline=baseline)
    finally:
        PB.time.time = orig
    assert r.state == "TIMEOUT" and not r.ok
    assert r.detail.get("stale_seen", 0) > 0
    assert any("残留" in p for p in r.problems)


def test_trigger_error_code_raises():
    h = FakeHttp(deploy_resp={"code": "BOOT_0001", "message": "参数错"})
    with pytest.raises(BuildError):
        _b(h).trigger()


def test_trigger_missing_deploy_id_raises():
    h = FakeHttp(deploy_resp={"code": 0, "data": {}})
    with pytest.raises(BuildError):
        _b(h).trigger()


# ---------------------------------------------------------------- 轮询

def test_wait_success():
    h = FakeHttp(states=[{"state": "BUILDING", "progress": "30"},
                         {"state": "SUCCESS", "progress": "100",
                          "totalTime": "218", "logs": ["done"]}])
    r = _b(h).wait("D1")
    assert r.ok and r.state == "SUCCESS" and r.total_time == "218"


def test_wait_failed_keeps_evidence():
    h = FakeHttp(states=[{"state": "FAILED", "progress": "60",
                          "logs": ["[ERROR] 编译失败 xxx"]}])
    r = _b(h).wait("D1")
    assert not r.ok and r.state == "FAILED"
    assert any("ERROR" in p for p in r.problems)


def test_wait_handles_platform_fail_state():
    """★ 平台真实返回 FAIL（不是 FAILED），必须识别为终态失败。"""
    h = FakeHttp(states=[{"state": "FAIL", "progress": "18",
                          "logs": ["[ERROR] 发布失败: 一致性检测未通过"]}])
    r = _b(h).wait("D1")
    assert not r.ok and r.state == "FAIL"
    assert any("一致性检测" in p for p in r.problems)


def test_wait_unwraps_data_content_envelope():
    """★ 平台响应是 {status, code, data:{content:{...}}} 两层包裹。"""
    h = FakeHttp(states=[{"code": "BOOT_0000", "status": 0,
                          "data": {"content": {"state": "SUCCESS",
                                               "progress": "100",
                                               "totalTime": "218",
                                               "logs": ["ok"]}}}])
    r = _b(h).wait("D1")
    assert r.ok and r.state == "SUCCESS" and r.total_time == "218"


def test_build_info_path_has_service_prefix():
    """★ 路径必须带 /service 前缀（裸 /udc/... 会打到 OSS 返回 XML）。"""
    assert PlatformBuilder.BUILD_INFO_PATH.startswith("/service/")
    assert PlatformBuilder.DEPLOY_PATH.startswith("/service/")


def test_building_is_not_success():
    """★ BUILDING 不是终态，不能当成功。"""
    h = FakeHttp(states=[{"state": "BUILDING", "progress": "99"}] * 3)
    r = _b(h, timeout_s=0.001).wait("D1")
    assert not r.ok and r.state == "TIMEOUT"


def test_wait_timeout_does_not_claim_success():
    h = FakeHttp(states=[{"state": "BUILDING"}])
    r = _b(h, timeout_s=0).wait("D1")
    assert not r.ok and r.state == "TIMEOUT"
    assert "超时" in r.problems[0]


def test_wait_survives_transient_get_errors():
    """单次读取异常不立刻判死（有上界）。"""
    class Flaky(FakeHttp):
        def __init__(self):
            super().__init__(states=[{"state": "SUCCESS"}])
            self.n = 0

        def get_json(self, path):
            self.n += 1
            if self.n == 1:
                raise RuntimeError("瞬断")
            return {"state": "SUCCESS"}

    r = _b(Flaky()).wait("D1")
    assert r.ok


def test_build_one_shot():
    """★ build() 先拍基线快照（1 次 GET），再轮询。
    这里第一次 GET 返回上一次的 BUILDING 残留，第二次才是本次 SUCCESS。"""
    h = FakeHttp(states=[{"state": "BUILDING", "progress": "0"},
                         {"state": "SUCCESS", "progress": "100"}])
    r = _b(h).build()
    assert r.ok and r.deploy_id == "D1"


def test_build_trigger_failure_returns_result():
    h = FakeHttp(deploy_resp={"code": "BOOT_0001", "message": "x"})
    r = _b(h).build()
    assert not r.ok and r.state == "TRIGGER_FAILED"


# ---------------------------------------------------------------- 语义声明

def test_build_success_semantics_note():
    """★ 构建成功 ≠ 运行成功，必须挂语义声明。"""
    r = attach_semantics(BuildResult(ok=True, state="SUCCESS"))
    assert "不代表微流程在业务场景下真实运行成功" in r.detail["semantics"]


def test_semantics_note_is_stable_text():
    assert "构建成功" in BUILD_SEMANTICS_NOTE


# ---------------------------------------------------------------- 断点恢复

def _rep(**kw):
    base = {"state": "SAVED", "mid": "M1", "ok": False}
    base.update(kw)
    return base


def test_resume_from_saved_goes_platform_validated():
    p = plan_resume(_rep(state="SAVED"), platform_state="DRAFT")
    assert p["action"] == "RESUME"
    assert p["from_stage"] == "PLATFORM_VALIDATED"


def test_resume_from_needs_ui_goes_ui_finalized():
    p = plan_resume(_rep(state="NEEDS_UI_FINALIZE"), platform_state="DRAFT")
    assert p["from_stage"] == "UI_FINALIZED"


def test_resume_done():
    p = plan_resume(_rep(state="BUILD_SUCCESS"), platform_state="RELEASE")
    assert p["action"] == "DONE"


def test_resume_failed_needs_human():
    """★ 失败态不自动重试。"""
    p = plan_resume(_rep(state="FAILED", failure={"message": "构建挂了"}),
                    platform_state="DRAFT")
    assert p["action"] == "NEED_HUMAN"


def test_resume_blocked_needs_human():
    p = plan_resume(_rep(state="BLOCKED"), platform_state=None)
    assert p["action"] == "NEED_HUMAN"


def test_resume_restarts_when_platform_lost_flow():
    """★ 平台已无此流程 → 本地记录作废，从头来。"""
    p = plan_resume(_rep(state="SAVED", mid="M1"), platform_exists=False)
    assert p["action"] == "RESTART"
    assert "平台无此流程" in p["conflicts"]


def test_resume_conflict_published_but_draft():
    """★ 本地记录已发布但平台是 DRAFT → 冲突，交人工。"""
    p = plan_resume(_rep(state="PUBLISHED"), platform_state="DRAFT")
    assert p["action"] == "NEED_HUMAN"
    assert any("DRAFT" in c for c in p["conflicts"])


def test_resume_no_state_restarts():
    p = plan_resume({}, platform_state=None)
    assert p["action"] == "RESTART"


def test_resume_unknown_stage_restarts():
    p = plan_resume({"state": "WEIRD", "mid": "M1"}, platform_state="DRAFT")
    assert p["action"] == "RESTART"


# ---------------------------------------------------------------- 落盘

def test_save_and_load_roundtrip(tmp_path):
    p = str(tmp_path / "r.json")
    rep = {"state": "BUILD_SUCCESS", "ok": True, "app_id": "A"}
    save_report(rep, p)
    assert load_report(p) == rep


def test_save_is_atomic_no_tmp_left(tmp_path):
    p = str(tmp_path / "r.json")
    save_report({"a": 1}, p)
    assert not os.path.exists(p + ".tmp")


def test_save_creates_parent_dir(tmp_path):
    p = str(tmp_path / "deep" / "dir" / "r.json")
    save_report({"a": 1}, p)
    assert os.path.exists(p)


def test_report_path_sanitizes_name(tmp_path):
    p = report_path(str(tmp_path), "APP", "有 空格/斜杠")
    assert " " not in os.path.basename(p)
    assert "/" not in os.path.basename(p)


def test_report_path_ends_with_json(tmp_path):
    assert report_path(str(tmp_path), "APP", "flow").endswith(".json")


# ---------------------------------------------------------------- 摘要

def test_summary_success():
    rep = {"ok": True, "state": "BUILD_SUCCESS", "app_id": "A",
           "flow_name": "f", "flow_caption": "F", "elapsed": 12,
           "stages": [{"stage": "SAVED", "ok": True, "elapsed": 1}]}
    s = render_summary(rep)
    assert "BUILD_SUCCESS" in s and "SAVED" in s


def test_summary_failure_shows_stage_and_reason():
    rep = {"ok": False, "state": "FAILED", "app_id": "A",
           "failure": {"stage": "SAVED", "message": "BOOT_3000"},
           "stages": [{"stage": "SAVED", "ok": False, "elapsed": 1,
                       "error": "BOOT_3000"}]}
    s = render_summary(rep)
    assert "SAVED" in s and "BOOT_3000" in s


def test_summary_mentions_ui_finalize_nodes():
    rep = {"ok": False, "state": "NEEDS_UI_FINALIZE", "app_id": "A",
           "needs_ui_finalize": ["br", "br2"], "stages": []}
    s = render_summary(rep)
    assert "br" in s and "br2" in s


def test_summary_includes_build_semantics():
    rep = {"ok": True, "state": "BUILD_SUCCESS", "app_id": "A", "stages": [],
           "build": {"state": "SUCCESS", "progress": "100", "total_time": "218",
                     "detail": {"semantics": BUILD_SEMANTICS_NOTE}}}
    assert "不代表微流程" in render_summary(rep)


# ---------------------------------------------------------------- 状态查询接口
#
# ★★ 真实事故（2026-11-01）：
#   RELEASE 构建从不写 delta-build-info（它只留最近一次完成的 delta 结果）。
#   拿它轮询 → 永远读到上一次的旧记录 → 加 _is_stale 后变成「永远 stale」→
#   一直空等到超时，而平台侧构建其实早就 SUCCESS 了。
#   正确入口是 GraphQL udcRuntimeSearchDeployStatusDeployIdPost。

def test_deploy_status_uses_input_path_type():
    """GraphQL 类型名必须是 ...PostInputPath。

    实测：...PostInputBody / ...PostInput / ...PostPath 全部 UnknownType，
    path: "<str>" 报 java.lang.String cannot be cast to java.util.Map。
    """
    q = PlatformBuilder.DEPLOY_STATUS_Q
    assert "udcRuntimeSearchDeployStatusDeployIdPostInputPath" in q
    assert "path: $p" in q, "参数必须是 path: {deployId}"


def test_deploy_status_unwraps_content_envelope():
    """返回 {data:{data0:{code,data:{content:[{...}]}}}} → 取 content[0]。"""

    class Http:
        def post_json(self, path, body):
            assert body["variables"]["p"]["deployId"] == "D1"
            return {"data": {"data0": {"code": "BOOT_0000",
                                       "data": {"content": [{"state": "SUCCESS",
                                                             "jarVersion": "1.0.89"}]}}}}

    b = PlatformBuilder(http=Http(), app_id="A")
    st = b.deploy_status("D1")
    assert st["state"] == "SUCCESS"
    assert st["jarVersion"] == "1.0.89"


def test_deploy_status_returns_empty_when_unreadable():
    """读不到返回 {} —— 调用方必须判空，不许当成功。"""

    class Http:
        def post_json(self, path, body):
            return {"data": {"data0": {"code": "BOOT_0000", "data": {"content": []}}}}

    b = PlatformBuilder(http=Http(), app_id="A")
    assert b.deploy_status("D1") == {}


def test_wait_prefers_deploy_status_when_id_given():
    """有 deploy_id 时走 search-deploy-status，不走 delta-build-info。"""
    calls = []

    class Http:
        def get_json(self, path):
            calls.append(("get", path))
            return {"data": {"content": {"state": "FAIL"}}}   # 旧记录

        def post_json(self, path, body):
            calls.append(("post", path))
            return {"data": {"data0": {"code": "BOOT_0000",
                                       "data": {"content": [{"state": "SUCCESS"}]}}}}

    b = PlatformBuilder(http=Http(), app_id="A", poll_interval=0, timeout_s=5)
    res = b.wait(deploy_id="D9", baseline={"startTime": 1})
    assert res.ok and res.state == "SUCCESS"
    assert not any(c[0] == "get" for c in calls), \
        "有 deploy_id 时不该再查 delta-build-info"
