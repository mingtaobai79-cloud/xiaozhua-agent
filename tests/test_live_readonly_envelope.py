"""LiveReadonlyRunner 验收器缺陷复现：HTTP 500 / 业务信封 status!=0 不应判 PASS。

背景（a9 离线探针复现）：runner 只比两次响应 md5 + auth-fail，
不查 HTTP status 与业务信封 status 字段。500 响应两次相同 → verdict=PASS，
业务 status=3（Seeyon 失败码）两次相同 → verdict=PASS。验收器因此不可信。

铁律（Seeyon UDC 信封）：业务 status=0 成功 / status=3 失败（BOOT_3000 等）；
HTTP 500 是传输层异常。任一不成立都不得 PASS。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from core.providers import ProviderResult, ProviderError
from components.platform_operations.live_readonly import LiveReadonlyRunner


class EnvelopeClient:
    """可控 HTTP status + 业务 body；模拟 500 / 业务错 / 正常。"""

    def __init__(self, http=200, body=None, allow_network=True):
        self.base_url = "https://stub"
        self.allow_network = allow_network
        self.http = http
        self.body = body
        self.calls = []

    def post(self, path, *, body=None, headers=None):
        self.calls.append((path, body, dict(headers or {})))
        if not self.allow_network:
            return ProviderResult({"classification": "BLOCKED", "response": None},
                                  error=ProviderError("unavailable", "network disabled", {}))
        return ProviderResult(
            {"classification": "PASS", "response": {"status": self.http, "body": self.body}})


def _resolver():
    return lambda ref: {"Content-Type": "application/json", "Cookie": "SY_ACCESS_TOKEN=***"}


def test_http_500_is_not_pass():
    client = EnvelopeClient(http=500, body={"status": 3, "code": "BOOT_5000", "message": "internal"})
    out = LiveReadonlyRunner(client, _resolver(), "app-x").run()
    assert out["status"] != "PASS", out
    for op, v in out["endpoints"].items():
        assert v["verdict"] != "PASS", f"{op} 在 HTTP 500 下不得 PASS: {v}"


def test_business_envelope_failure_is_not_pass():
    # HTTP 200 但业务 status=3（Seeyon 失败码）—— 不得判 PASS
    client = EnvelopeClient(http=200, body={"status": 3, "code": "BOOT_3000", "message": "业务失败"})
    out = LiveReadonlyRunner(client, _resolver(), "app-x").run()
    assert out["status"] != "PASS", out
    for op, v in out["endpoints"].items():
        assert v["verdict"] != "PASS", f"{op} 业务 status=3 不得 PASS: {v}"


def test_business_success_envelope_still_passes():
    # 回归护栏：HTTP 200 + 业务 status=0（BOOT_0000）必须仍 PASS
    client = EnvelopeClient(http=200, body={"status": 0, "code": "BOOT_0000",
                                            "data": {"content": [{"pageUrl": "hj"}]}})
    out = LiveReadonlyRunner(client, _resolver(), "app-x").run()
    assert out["status"] == "PASS", out
    for v in out["endpoints"].values():
        assert v["verdict"] == "PASS", f"正常成功信封应 PASS: {v}"
