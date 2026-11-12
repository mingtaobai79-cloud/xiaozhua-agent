"""R2a: C1 微流程只读契约 udc.microflow.function_node_tree 入 registry 的最小验证。

证据等级 VERIFIED_STATIC_BYTECODE（离线反编译，非 LIVE）。
路径按控制器原路径登记（udc-runtime/meta-data/select-function-node-tree/{appName}），
网关 service 前缀与 /service 组合离线不可确证，本测试同时断言路径未拼网关前缀。
"""
from components.platform_operations.models import OperationStatus
from components.platform_operations.registry import UdcOperationRegistry

OP = "udc.microflow.function_node_tree"


def _contract():
    reg = UdcOperationRegistry.default()
    assert reg.has(OP), "registry 未登记 udc.microflow.function_node_tree"
    return reg.get(OP)


def test_microflow_contract_registered():
    reg = UdcOperationRegistry.default()
    c = reg.get(OP)
    assert c.operation_id == OP
    assert c.method == "GET"
    assert c.write is False
    assert c.status is OperationStatus.VERIFIED_STATIC_BYTECODE
    assert c.effective is True
    # 路径按控制器原路径，未拼网关 service 前缀
    assert c.path == "udc-runtime/meta-data/select-function-node-tree/{appName}"
    assert "service/" not in c.path
    assert c.request_type == "String appName(SingleRequest)"
    assert c.response_type == "ListResponse<UdcFunctionNodeMetadataDto>"
    assert c.required_inputs == ("appName",)
    assert c.verification_rules[0] == "同一 appName 回读节点树 identity_matches"
    assert c.verification_rules[1] == "响应非空 UdcFunctionNodeMetadataDto 列表"


def test_microflow_locator_eight_elements_bound():
    c = _contract()
    ev = c.evidence[0]
    for key in ("artifact", "version", "class", "method", "class_sha256", "javap", "evidence_level", "source"):
        assert key in ev, f"locator 缺要素 {key}"
    assert ev["artifact"] == "udc-starter-runtime-5.3.517.jar"
    assert ev["version"] == "5.3.517"
    assert ev["class"] == "com.seeyon.boot.starter.udcrt.controller.UdcFunctionNodeController"
    assert ev["method"] == "selectFunctionNodeTreeMetaData"
    assert ev["class_sha256"] == "efd8f9143d0fd44d4e3033a4bb4877c09e891a1049f66382df1ae1d7d08a7748"
    assert ev["javap"] == "docs/audit/artifacts/udc-runtime-5.3.517/UdcFunctionNodeController.javap.txt"
    assert ev["evidence_level"] == "VERIFIED_STATIC_BYTECODE"
