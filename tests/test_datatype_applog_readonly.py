"""R4a: C2/C3 本地 5.3.517 只读契约入 registry 的最小验证 + destructive GET 排除断言 (A5).

证据等级 VERIFIED_STATIC_BYTECODE（本地 Maven <MAVEN_REPO> 离线反编译，非 LIVE；标注 local-maven-53517，
不混写 test2 版本）。路径按控制器原值登记，网关 service 前缀离线不可确证 → UNVERIFIED，禁止拼前缀。
class_sha256 为 javap -p -v 对该 class 字节的实测值。
"""
from components.platform_operations.models import OperationStatus
from components.platform_operations.registry import UdcOperationRegistry

C2 = "udc.datatype.get_all"
C3 = "udc.applog.select_by_id"

DATATYPE_CLASS_SHA = "03b3977b50574208eaad2b1925a80520a4686b268a56bacd35b87a144854bc38"
APPLOG_CLASS_SHA = "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775"

EVIDENCE_KEYS = ("artifact", "version", "class", "method", "class_sha256", "source", "evidence_level")


def _registry():
    return UdcOperationRegistry.default()


def test_datatype_contract_registered_effective():
    reg = _registry()
    c = reg.get(C2)
    assert reg.has(C2)
    assert c.operation_id == C2
    assert c.method == "GET"
    assert c.write is False
    assert c.status is OperationStatus.VERIFIED_STATIC_BYTECODE
    assert c.effective is True
    assert c.path == "udc-runtime/datatype/getAll"
    assert "service/" not in c.path
    assert c.request_type == "()"
    assert c.response_type == "ListResponse<DataTypeDto>"
    assert c.required_inputs == ()


def test_datatype_locator_evidence():
    c = _registry().get(C2)
    ev = c.evidence[0]
    for key in EVIDENCE_KEYS:
        assert key in ev, f"locator 缺要素 {key}"
    assert ev["artifact"] == "udc-starter-runtime-5.3.517.jar"
    assert ev["version"] == "5.3.517"
    assert ev["class"] == "com.seeyon.boot.starter.udcrt.controller.UdcDataTypeController"
    assert ev["method"] == "getDataTypes"
    assert ev["class_sha256"] == DATATYPE_CLASS_SHA
    assert ev["source"] == "local-maven-53517"
    assert ev["evidence_level"] == "VERIFIED_STATIC_BYTECODE"


def test_applog_contract_registered_effective():
    reg = _registry()
    c = reg.get(C3)
    assert reg.has(C3)
    assert c.operation_id == C3
    assert c.method == "GET"
    assert c.write is False
    assert c.status is OperationStatus.VERIFIED_STATIC_BYTECODE
    assert c.effective is True
    assert c.path == "udc-runtime/app-log/datalog/{id}"
    assert "service/" not in c.path
    assert c.request_type == "Long id(SingleRequest)"
    assert c.response_type == "SingleResponse<UdcEntityMonitorLogDto>"
    assert c.required_inputs == ("id",)


def test_applog_locator_evidence():
    c = _registry().get(C3)
    ev = c.evidence[0]
    for key in EVIDENCE_KEYS:
        assert key in ev, f"locator 缺要素 {key}"
    assert ev["class"] == "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController"
    assert ev["method"] == "selectAppDataById"
    assert ev["class_sha256"] == APPLOG_CLASS_SHA
    assert ev["source"] == "local-maven-53517"
    assert ev["evidence_level"] == "VERIFIED_STATIC_BYTECODE"


def test_destructive_gets_not_in_registry():
    """A5: UdcAppLogController 5 个 destructive GET（deleteAll/clearOrgManager/
    clearRuntimeDataSource/unloadDynamicApp/setRestEnableLog）不得入只读 registry。"""
    reg = _registry()
    all_contracts = reg.all()
    # 按控制器/方法名扫描：任何 evidence 含 destructive 方法名的契约都不得存在
    destructive_methods = {"deleteAll", "clearOrgManager", "clearRuntimeDataSource", "unloadDynamicApp", "setRestEnableLog"}
    for operation_id, contract in all_contracts.items():
        for ev in contract.evidence:
            assert ev.get("method") not in destructive_methods, (
                f"destructive GET 方法 {ev.get('method')} 误入只读 registry: {operation_id}"
            )
    # 反向兜底：registry 中不存在以这些方法名命名契约的 operation_id 前缀
    for op in ("udc.applog.delete_all", "udc.applog.clear_org_manager", "udc.applog.clear_runtime_data_source",
               "udc.applog.unload_dynamic_app", "udc.applog.set_rest_enable_log"):
        assert not reg.has(op), f"destructive 端点契约 {op} 不应存在于 registry"
