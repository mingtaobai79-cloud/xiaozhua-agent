"""R9: C5 元数据存在性探测契约（udc.metadata.page_exists_check）入 registry 的最小验证。

证据等级 VERIFIED_STATIC_BYTECODE（本地 Maven <MAVEN_REPO> 5.3.517 离线反编译，非 LIVE；
source=local-maven-53517，与 test2 部署 5.3.496 分列不混写）。路径按控制器原值
（udc-runtime/meta-data 类级 @RequestMapping + 方法级 @PostMapping("check-page-exists")），
网关 service 前缀离线不可确证 → UNVERIFIED，禁止拼前缀。
class_sha256 = 76787348…4a2e02（jar 内 UdcRtPageInfoController.class 字节，本轮独立重算自证，与 C4 同 class 同值）。

已知边界（非 FAIL，与 C4 同）：
- 本端点 javap 原文为 @PostMapping —— registry 登记 = 契约声明；PlatformOperationLayer
  执行链仅放行 GET，故 C5 在只读执行链上为 DENIED/POLICY_DENIED，可执行性留活体（R11/P4）。
- 响应 ListResponse<Boolean>：按 08:45 元数据锚点规则②（Boolean/HTTP 200 不作 identity 锚点），
  本契约 = 存在性探测面，非验收 identity 面。故本单测不断言 effective=True（POST → effective False）。
"""
from components.platform_operations.models import OperationStatus
from components.platform_operations.registry import UdcOperationRegistry

C5 = "udc.metadata.page_exists_check"

C5_CLASS_SHA = "7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02"

EVIDENCE_KEYS = ("artifact", "version", "class", "method", "class_sha256", "javap", "source", "evidence_level")


def _registry():
    return UdcOperationRegistry.default()


def test_metadata_page_exists_check_registered():
    reg = _registry()
    c = reg.get(C5)
    assert reg.has(C5)
    assert c.operation_id == C5
    assert c.method == "POST"
    assert c.write is False
    assert c.status is OperationStatus.VERIFIED_STATIC_BYTECODE
    assert c.path == "udc-runtime/meta-data/check-page-exists"
    assert "service/" not in c.path  # 未拼网关前缀
    assert c.request_type == "List<UdcRtPageExistsDto>(RequestBody)"
    assert c.response_type == "ListResponse<Boolean>"
    assert c.required_inputs == ("UdcRtPageExistsDto",)
    # 已知边界：POST 契约在执行层（仅放行 GET）不可 effective；且 Boolean 响应不作 identity 锚点
    assert c.effective is False


def test_metadata_page_exists_check_locator_evidence():
    c = _registry().get(C5)
    ev = c.evidence[0]
    for key in EVIDENCE_KEYS:
        assert key in ev, f"locator 缺要素 {key}"
    assert ev["artifact"] == "udc-starter-runtime-5.3.517.jar"
    assert ev["version"] == "5.3.517"
    assert ev["class"] == "com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController"
    assert ev["method"] == "checkPageExistsByConditions"
    assert ev["class_sha256"] == C5_CLASS_SHA
    assert ev["javap"] == "docs/audit/artifacts/udc-entity-5.3.517/UdcRtPageInfoController.javap.txt"
    assert ev["source"] == "local-maven-53517"
    assert ev["evidence_level"] == "VERIFIED_STATIC_BYTECODE"
    # 层次 note：运行态元数据层存在性探测面；Boolean 不作 identity 锚点
    note = ev.get("note", "")
    assert "存在性探测" in note and "Redis" in note and "identity" in note
