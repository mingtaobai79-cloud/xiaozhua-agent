"""R11/R12/R13: C6 微流程日志搜索 + C7 微流程日志详情搜索 + C8 微流程 flowLog 详情契约入 registry 的最小验证。

证据等级 VERIFIED_STATIC_BYTECODE（本地 Maven <MAVEN_REPO> 5.3.517 离线反编译，非 LIVE；
source=local-maven-53517，与 test2 部署 5.3.496 分列不混写）。路径按控制器原值
（udc-runtime/app-log 类级 @RequestMapping + 方法级 @PostMapping），网关 service 前缀
离线不可确证 → UNVERIFIED，禁止拼前缀。
class_sha256 = f6a2111d…ee775（jar 内 UdcAppLogController.class 字节，各轮独立重算自证，与 C3 同 class 同值）。
C6/C7/C8 各带独立 evidence（method=search / searchDetails / searchFlowDetails，不复用 C3 的 selectAppDataById）。

已知边界（非 FAIL，与 C4/C5 同）：
- C6/C7/C8 端点 javap 原文为 @PostMapping —— registry 登记 = 契约声明；PlatformOperationLayer
  执行链仅放行 GET，故三者在只读执行链上为 DENIED/POLICY_DENIED，可执行性留活体（P4）。
- 微流程只读契约族：运行态日志层（app-log microflow 搜索/详情/flowLog 面，非 meta-data 层）。
  本单测不断言 effective=True（POST → effective False）。
"""
from components.platform_operations.models import OperationStatus
from components.platform_operations.registry import UdcOperationRegistry

C6 = "udc.applog.search_microflow"
C7 = "udc.applog.search_details_microflow"
C8 = "udc.applog.search_details_microflow_flowlog"

C6_CLASS_SHA = "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775"
C7_CLASS_SHA = "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775"
C8_CLASS_SHA = "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775"

EVIDENCE_KEYS = ("artifact", "version", "class", "method", "class_sha256", "javap", "source", "evidence_level")


def _registry():
    return UdcOperationRegistry.default()


def test_applog_search_microflow_registered():
    reg = _registry()
    c = reg.get(C6)
    assert reg.has(C6)
    assert c.operation_id == C6
    assert c.method == "POST"
    assert c.write is False
    assert c.status is OperationStatus.VERIFIED_STATIC_BYTECODE
    assert c.path == "udc-runtime/app-log/search/microflow"
    assert "service/" not in c.path  # 未拼网关前缀
    assert c.request_type == "PageDtoRequest<MicroFlowLogSearchDto>(RequestBody)"
    assert c.response_type == "PageResponse<MicroFlowLogResultDto>"
    assert c.required_inputs == ("MicroFlowLogSearchDto",)
    # 已知边界：POST 契约在执行层（仅放行 GET）不可 effective
    assert c.effective is False


def test_applog_search_microflow_locator_evidence():
    c = _registry().get(C6)
    ev = c.evidence[0]
    for key in EVIDENCE_KEYS:
        assert key in ev, f"locator 缺要素 {key}"
    assert ev["artifact"] == "udc-starter-runtime-5.3.517.jar"
    assert ev["version"] == "5.3.517"
    assert ev["class"] == "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController"
    assert ev["method"] == "search"  # 独立 evidence，非 C3 的 selectAppDataById
    assert ev["class_sha256"] == C6_CLASS_SHA
    assert ev["javap"] == "docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt"
    assert ev["source"] == "local-maven-53517"
    assert ev["evidence_level"] == "VERIFIED_STATIC_BYTECODE"
    # 层次 note：运行态日志层微流程搜索面，非 meta-data 层
    note = ev.get("note", "")
    assert "microflow" in note.lower() and "app-log" in note


def test_applog_search_details_microflow_registered():
    reg = _registry()
    c = reg.get(C7)
    assert reg.has(C7)
    assert c.operation_id == C7
    assert c.method == "POST"
    assert c.write is False
    assert c.status is OperationStatus.VERIFIED_STATIC_BYTECODE
    assert c.path == "udc-runtime/app-log/search-details/microflow"
    assert "service/" not in c.path  # 未拼网关前缀
    assert c.request_type == "PageDtoRequest<MicroFlowLogDetailsSearchDto>(RequestBody)"
    assert c.response_type == "PageResponse<MicroFlowLogDetailsResultDto>"
    assert c.required_inputs == ("MicroFlowLogDetailsSearchDto",)
    # 已知边界：POST 契约在执行层（仅放行 GET）不可 effective（与 C4/C5/C6 同边界）
    assert c.effective is False


def test_applog_search_details_microflow_locator_evidence():
    c = _registry().get(C7)
    ev = c.evidence[0]
    for key in EVIDENCE_KEYS:
        assert key in ev, f"locator 缺要素 {key}"
    assert ev["artifact"] == "udc-starter-runtime-5.3.517.jar"
    assert ev["version"] == "5.3.517"
    assert ev["class"] == "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController"
    assert ev["method"] == "searchDetails"  # 独立 evidence，非 C6 的 search
    assert ev["class_sha256"] == C7_CLASS_SHA
    assert ev["javap"] == "docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt"
    assert ev["source"] == "local-maven-53517"
    assert ev["evidence_level"] == "VERIFIED_STATIC_BYTECODE"
    # 层次 note：运行态日志层微流程详情搜索面，非 meta-data 层
    note = ev.get("note", "")
    assert "microflow" in note.lower() and "app-log" in note and "详情" in note


def test_applog_search_details_microflow_flowlog_registered():
    reg = _registry()
    c = reg.get(C8)
    assert reg.has(C8)
    assert c.operation_id == C8
    assert c.method == "POST"
    assert c.write is False
    assert c.status is OperationStatus.VERIFIED_STATIC_BYTECODE
    assert c.path == "udc-runtime/app-log/search-details/microflow/flowLog"
    assert "service/" not in c.path  # 未拼网关前缀
    # C8 请求为裸 MicroFlowLogDetailsSearchDto(RequestBody)，非 PageDtoRequest 包装（按 javap L539 原文）
    assert c.request_type == "MicroFlowLogDetailsSearchDto(RequestBody)"
    assert c.response_type == "SingleResponse<MicroFlowFlowLogResultDto>"
    assert c.required_inputs == ("MicroFlowLogDetailsSearchDto",)
    # 已知边界：POST 契约在执行层（仅放行 GET）不可 effective（与 C4/C5/C6/C7 同边界）
    assert c.effective is False


def test_applog_search_details_microflow_flowlog_locator_evidence():
    c = _registry().get(C8)
    ev = c.evidence[0]
    for key in EVIDENCE_KEYS:
        assert key in ev, f"locator 缺要素 {key}"
    assert ev["artifact"] == "udc-starter-runtime-5.3.517.jar"
    assert ev["version"] == "5.3.517"
    assert ev["class"] == "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController"
    assert ev["method"] == "searchFlowDetails"  # 独立 evidence，非 C7 的 searchDetails
    assert ev["class_sha256"] == C8_CLASS_SHA
    assert ev["javap"] == "docs/audit/artifacts/udc-entity-5.3.517/UdcAppLogController.javap.txt"
    assert ev["source"] == "local-maven-53517"
    assert ev["evidence_level"] == "VERIFIED_STATIC_BYTECODE"
    # 层次 note：运行态日志层微流程 flowLog 详情面，非 meta-data 层
    note = ev.get("note", "")
    assert "microflow" in note.lower() and "app-log" in note and "flowlog" in note.lower()
