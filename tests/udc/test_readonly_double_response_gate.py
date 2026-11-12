"""RED: 双读验收器必须校验【两次】响应，而不是只校验第一次。

背景（本轮审计实测复现）：live_readonly.py run() 里只对 resp1 调 _envelope_gates，
resp2 只参与 body 摘要与 auth 检测。于是"第一次 200、第二次 500"这种半失败会被判 PASS。

业务含义：所谓"双读 identity_matches 通过"本意是两次独立请求都成功且内容一致。
若第二次请求已经 500，一致性没有证据基础，不能升级为 PASS。

铁律：任一响应 HTTP 非 2xx / 业务 status!=0 ⇒ 该端点不得 PASS，总状态不得 PASS。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from core.providers import ProviderResult
from components.platform_operations.live_readonly import LiveReadonlyRunner


class SequenceClient:
    """按给定序列依次返回不同的 HTTP status / body。"""

    def __init__(self, sequence):
        self.base_url = "https://stub"
        self.allow_network = True
        self._seq = list(sequence)
        self._i = 0

    def post(self, path, *, body=None, headers=None):
        http, payload = self._seq[self._i % len(self._seq)]
        self._i += 1
        return ProviderResult(
            {"classification": "PASS", "response": {"status": http, "body": payload}})


def _resolver():
    return lambda ref: {"Content-Type": "application/json", "Cookie": "SY_ACCESS_TOKEN=***"}


_OK = {"status": 0, "code": "BOOT_0000",
       "data": {"content": [{"pageUrl": "hj"}]}}


def test_second_response_http_500_must_not_pass():
    """第一次 200、第二次 500 → 端点不得 PASS，总状态不得 PASS。"""
    client = SequenceClient([(200, _OK), (500, _OK)])
    out = LiveReadonlyRunner(client, _resolver(), "app-x").run()

    assert out["status"] != "PASS", out
    # 只对真正发出两次请求的端点断言（check_exists 依赖 select_host 样本，
    # 样本因门失败被拒后如实 BLOCKED(NO_SAMPLE)，不是本测试要验的路径）
    gated = {op: v for op, v in out["endpoints"].items() if "http1" in v}
    assert gated, "至少应有一个端点完成双读"
    for op, v in gated.items():
        assert v["verdict"] != "PASS", f"{op} 第二次 HTTP 500 不得 PASS: {v}"
        assert "gate" in v and "HTTP_500" in v["gate"], f"{op} 须登记 HTTP_500 门原因: {v}"
        assert v["gate"].startswith("R2:"), f"{op} 门原因须标明来自第二次响应: {v}"


def test_second_response_business_failure_must_not_pass():
    """第一次业务成功、第二次业务 status=3 → 同样不得 PASS。"""
    fail = {"status": 3, "code": "BOOT_3000", "message": "业务失败"}
    client = SequenceClient([(200, _OK), (200, fail)])
    out = LiveReadonlyRunner(client, _resolver(), "app-x").run()

    assert out["status"] != "PASS", out
    gated = {op: v for op, v in out["endpoints"].items() if "http1" in v}
    assert gated, "至少应有一个端点完成双读"
    for op, v in gated.items():
        assert v["verdict"] != "PASS", f"{op} 第二次业务失败不得 PASS: {v}"
        assert "gate" in v and "BUSINESS_3" in v["gate"], f"{op} 须登记 BUSINESS_3: {v}"


def test_both_responses_ok_still_passes():
    """回归护栏：两次都 HTTP 200 + status=0 必须仍 PASS。"""
    client = SequenceClient([(200, _OK)])
    out = LiveReadonlyRunner(client, _resolver(), "app-x").run()
    assert out["status"] == "PASS", out
    for v in out["endpoints"].values():
        assert v["verdict"] == "PASS", v
