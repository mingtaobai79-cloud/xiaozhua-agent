"""LiveReadonlyRunner 离线确定性测试：用 stub client 验证只读 POST 判定逻辑，不联网。

铁律：只读优先。POST 只读是 P4 活体边界，静态层判 effective=False；
本测试验证 runner 的双发 identity / auth-fail→BLOCKED / 无样本→BLOCKED / 网络关闭→BLOCKED
逻辑，全部离线、确定性，进默认收集（不联网、不依赖 test2）。
"""
import json
import pytest

from core.providers import ProviderResult, ProviderError
from components.platform_operations.live_readonly import LiveReadonlyRunner


class StubClient:
    """可控的 POST 返回体；allow_network=False 时模拟网络关闭。"""

    def __init__(self, responses=None, allow_network=True):
        self.base_url = "https://stub"
        self.allow_network = allow_network
        self.calls = []
        self._responses = responses or {}

    def post(self, path, *, body=None, headers=None):
        self.calls.append((path, body, dict(headers or {})))
        if not self.allow_network:
            return ProviderResult({"classification": "BLOCKED", "response": None},
                                  error=ProviderError("unavailable", "network disabled", {}))
        # 按 path 尾匹配固定响应
        for key, resp in self._responses.items():
            if path.endswith(key):
                return ProviderResult({"classification": "PASS", "response": {"status": 200, "body": resp}})
        return ProviderResult({"classification": "UNVERIFIED", "response": None},
                              error=ProviderError("not_found", "stub miss", {}))


def _resolver():
    return lambda ref: {"Content-Type": "application/json", "Cookie": "SY_ACCESS_TOKEN=***"}


def test_runner_all_pass_when_4_endpoints_stable():
    client = StubClient({
        "select-host-and-only-page-pages": {"status": 0, "code": "BOOT_0000",
                                             "data": {"content": [{"pageUrl": "hj", "urlType": "PC"}]}},
        "check-page-exists": {"status": 0, "code": "BOOT_0000", "data": {"content": [True]}},
        "search": {"status": 0, "code": "BOOT_0000", "data": {"content": []}},
        "search-non-metadata": {"status": 0, "code": "BOOT_0000", "data": {"content": []}},
    })
    out = LiveReadonlyRunner(client, _resolver(), "app-x").run()
    assert out["status"] == "PASS", out
    assert out["network"] == "explicit"
    for op in ("udc.page_info.select_host_and_only_page", "udc.page_info.check_exists",
               "udc.page_log.search", "udc.page_log.search_non_metadata"):
        assert out["endpoints"][op]["verdict"] == "PASS", (op, out["endpoints"][op])


def test_check_exists_blocks_when_no_sample_from_select_host():
    # select-host 返回空 content → check-exists 无合法样本，必须 BLOCKED（禁臆造）
    client = StubClient({
        "select-host-and-only-page-pages": {"status": 0, "code": "BOOT_0000", "data": {"content": []}},
        "check-page-exists": {"status": 0, "code": "BOOT_0000", "data": {"content": [True]}},
        "search": {"status": 0, "code": "BOOT_0000", "data": {"content": []}},
        "search-non-metadata": {"status": 0, "code": "BOOT_0000", "data": {"content": []}},
    })
    out = LiveReadonlyRunner(client, _resolver(), "app-x").run()
    assert out["endpoints"]["udc.page_info.check_exists"]["verdict"] == "BLOCKED"
    assert out["status"] != "PASS"


def test_auth_fail_marks_blocked_not_pass():
    client = StubClient({
        "select-host-and-only-page-pages": {"code": "BOOT_1006", "message": "unauthorized"},
    })
    out = LiveReadonlyRunner(client, _resolver(), "app-x").run()
    assert out["status"] == "BLOCKED"
    assert out["endpoints"]["udc.page_info.select_host_and_only_page"]["verdict"] == "BLOCKED"


def test_network_disabled_all_blocked():
    client = StubClient({
        "select-host-and-only-page-pages": {"status": 0, "code": "BOOT_0000", "data": {"content": [1]}},
    }, allow_network=False)
    out = LiveReadonlyRunner(client, _resolver(), "app-x").run()
    assert out["status"] == "BLOCKED"
    assert all(v["verdict"] == "BLOCKED" for v in out["endpoints"].values())


def test_credential_resolution_failure_is_blocked():
    def bad_resolver(ref):
        raise LookupError("credential reference cannot be resolved")
    client = StubClient({})
    out = LiveReadonlyRunner(client, bad_resolver, "app-x").run()
    assert out["status"] == "BLOCKED"
    assert "CREDENTIAL_RESOLUTION_FAILED" in out["reason"]


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
