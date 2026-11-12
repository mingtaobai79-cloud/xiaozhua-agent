"""R7: C4 元数据锚点契约（udc.metadata.page_tree）入 registry 的最小验证。

证据等级 VERIFIED_STATIC_BYTECODE（本地 Maven <MAVEN_REPO> 5.3.517 离线反编译，非 LIVE；
source=local-maven-53517，与 test2 部署 5.3.496 分列不混写）。路径按控制器原值
（udc-runtime/meta-data 类级 @RequestMapping + 方法级 @PostMapping 段），网关 service 前缀
离线不可确证 → UNVERIFIED，禁止拼前缀。class_sha256 为 jar 内该 class 字节的实测值。

已知边界（非 FAIL）：本端点 javap 原文为 @PostMapping —— registry 登记=契约声明；
PlatformOperationLayer 执行链仅放行 GET，故 C4 在只读执行链上为 DENIED/POLICY_DENIED，
直至运行态（P4）确证其为只读读面。故本单测不断言 effective=True（POST → effective False）。
"""
from components.platform_operations.models import OperationStatus
from components.platform_operations.registry import UdcOperationRegistry

C4 = "udc.metadata.page_tree"

C4_CLASS_SHA = "7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02"

EVIDENCE_KEYS = ("artifact", "version", "class", "method", "class_sha256", "javap", "source", "evidence_level")


def _registry():
    return UdcOperationRegistry.default()


def test_metadata_page_tree_registered():
    reg = _registry()
    c = reg.get(C4)
    assert reg.has(C4)
    assert c.operation_id == C4
    assert c.method == "POST"
    assert c.write is False
    assert c.status is OperationStatus.VERIFIED_STATIC_BYTECODE
    assert c.path == "udc-runtime/meta-data/select-host-and-only-page-pages"
    assert "service/" not in c.path  # 未拼网关前缀
    assert c.request_type == "UdcPagesMetaDataSearchDto(RequestBody)"
    assert c.response_type == "ListResponse<UdcMainPageMetadataDto>"
    assert c.required_inputs == ("UdcPagesMetaDataSearchDto",)
    # 已知边界：POST 契约在执行层（仅放行 GET）不可 effective
    assert c.effective is False


def test_metadata_page_tree_locator_evidence():
    c = _registry().get(C4)
    ev = c.evidence[0]
    for key in EVIDENCE_KEYS:
        assert key in ev, f"locator 缺要素 {key}"
    assert ev["artifact"] == "udc-starter-runtime-5.3.517.jar"
    assert ev["version"] == "5.3.517"
    assert ev["class"] == "com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController"
    assert ev["method"] == "selectHostAppAndOnlyPageAppPages"
    assert ev["class_sha256"] == C4_CLASS_SHA
    assert ev["javap"] == "docs/audit/artifacts/udc-entity-5.3.517/UdcRtPageInfoController.javap.txt"
    assert ev["source"] == "local-maven-53517"
    assert ev["evidence_level"] == "VERIFIED_STATIC_BYTECODE"
    # 层次 note：运行态元数据层，非设计态配置/生成物/物理表/Redis
    note = ev.get("note", "")
    assert "meta-data" in note and "Redis" in note
