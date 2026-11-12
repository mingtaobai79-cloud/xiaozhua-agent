"""R17: entity 域 13 条只读契约（serial / entity_data / applog / role / appinfo / database /
entity.history / entity.ext.{tree,list,available_datatype,attribute}）入 registry 的最小验证。

证据等级 VERIFIED_STATIC_BYTECODE（本地 Maven 5.3 族离线反编译，非 LIVE；source=local-maven，
照 docs/operation-contracts/udc/entity/registry-entries.md 原值；与 test2 部署态版本族隔离）。
8 个 class SHA 本轮对本机 jar（udc-starter-runtime / udc-starter-customplan）zipfile 直读独立重算自证不抄，
与 md 声明 + main 核实值全匹配：
  UdcSerialConfigController=fe1e5a72 / UdcFormDataQueryController=cabd3122 /
  UdcAppLogController=f6a2111d / UdcRoleRtController=ed024802 /
  UdcBaseAppInfoController=deebcc39 / UdcRuntimeDatabaseController=588bc1cf /
  UdcRuntimeHistoryMetaDataController=9f197e35 / ScalabilityFieldController=4c6b8365。
怪值逐字保留：#3 双斜杠 udc-runtime/data//query（与 F2 udc.flow.form_data_query 同端点逐字不同，保留双 ID）；
#8 deploy-info 类级 @RequestMapping 缺省无前缀 → 完整路由 UNVERIFIED 不拼前缀（与 A3 udc.application.deploy_info 保留双 ID）；
#11 GET 携带请求体 RuntimeDataBaseQueryDataReqDto 原样。
排除 3 条端点重复（按 R15 C1 去重先例，删一留一，不重复登记）：
  udc.applog.select_app_data_by_id ≡ 已登 C3 udc.applog.select_by_id；
  udc.page.check_exists ≡ 已登 C5 udc.metadata.page_exists_check；
  udc.page.select_host_only_pages ≡ 已登 C4 udc.metadata.page_tree。
既有 C3/C4/C5/F2/A3 未改写。写/破坏语义端点（md 排除项）一律不入。

.effective 判定（models.py：status∈{PASS,VERIFIED_STATIC_BYTECODE,OBSERVED} 且 write=False 且 method=="GET"）：
- GET 只读 5 条（serial.select_entity_list / applog.list_app_data_by_dataid / role.has_system_admin /
  appinfo.get_deploy_info / database.query_data）→ effective=True。
- POST 读型 8 条 → effective=False（执行链仅放行 GET，PlatformOperationLayer 上 DENIED/POLICY_DENIED，
  与 C4-C8 / F / A5 同边界，可执行性留活体 P4）。
"""
from components.platform_operations.models import OperationStatus
from components.platform_operations.registry import UdcOperationRegistry

# 13 条 MERGE 契约
GET_CONTRACTS = (
    "udc.serial.select_entity_list",
    "udc.applog.list_app_data_by_dataid",
    "udc.role.has_system_admin",
    "udc.appinfo.get_deploy_info",
    "udc.database.query_data",
)
POST_CONTRACTS = (
    "udc.serial.select_entity_by_serial",
    "udc.entity_data.query_form_data",
    "udc.applog.search_app_data_log",
    "udc.entity.history.select_by_condition",
    "udc.entity.ext.tree",
    "udc.entity.ext.list",
    "udc.entity.ext.available_datatype",
    "udc.entity.ext.attribute",
)
E13 = GET_CONTRACTS + POST_CONTRACTS

# 排除 3 条（端点重复，不得入 registry）
EXCLUDED = (
    "udc.applog.select_app_data_by_id",
    "udc.page.check_exists",
    "udc.page.select_host_only_pages",
)

# 既有跨域同端点条目（须未被改写）
EXISTING = (
    "udc.applog.select_by_id",            # C3
    "udc.metadata.page_tree",             # C4
    "udc.metadata.page_exists_check",     # C5
    "udc.flow.form_data_query",           # F2
    "udc.application.deploy_info",        # A3
)

SHA = {
    "udc.serial.select_entity_list": "fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658",
    "udc.serial.select_entity_by_serial": "fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658",
    "udc.entity_data.query_form_data": "cabd312210665274361568181b6d41b9a86f7ed13f1dba7e3f844dc2e5ea5584",
    "udc.applog.list_app_data_by_dataid": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775",
    "udc.applog.search_app_data_log": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775",
    "udc.role.has_system_admin": "ed024802b6c205041e4368840993412be184ff67c5f9b12938bee5a13a2aae47",
    "udc.appinfo.get_deploy_info": "deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95",
    "udc.database.query_data": "588bc1cf97cf53357ce0a851d16eb28244b6a9607aa5c813b80e4c2c8d4b3c48",
    "udc.entity.history.select_by_condition": "9f197e358d9b7b38e19e1afe280ebcd75b0a2c09f73b29c6f6e0f0cbe025ef1c",
    "udc.entity.ext.tree": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151",
    "udc.entity.ext.list": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151",
    "udc.entity.ext.available_datatype": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151",
    "udc.entity.ext.attribute": "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151",
}

# 路径逐字（含怪值原样）
PATH = {
    "udc.serial.select_entity_list": "udc-runtime/serial-config/select-entity-list",
    "udc.serial.select_entity_by_serial": "udc-runtime/serial-config/select-entity-by-serial-id",
    "udc.entity_data.query_form_data": "udc-runtime/data//query",   # ⚠双斜杠逐字
    "udc.applog.list_app_data_by_dataid": "udc-runtime/app-log/datalog/list-by-dataid/{dataId}",
    "udc.applog.search_app_data_log": "udc-runtime/app-log/datalog/search",
    "udc.role.has_system_admin": "udc-runtime/udc-role/has-system-admin/{appName}",
    "udc.appinfo.get_deploy_info": "deploy-info",                    # ⚠类级前缀缺省，不拼前缀
    "udc.database.query_data": "udc-runtime/database/query-data",
    "udc.entity.history.select_by_condition": "udc-runtime/history-metadata/select-by-condition",
    "udc.entity.ext.tree": "udc-runtime/scalability/ext-entity-tree",
    "udc.entity.ext.list": "udc-runtime/scalability/list-ext-field",
    "udc.entity.ext.available_datatype": "udc-runtime/scalability/available-datatype",
    "udc.entity.ext.attribute": "udc-runtime/scalability/select-attribute",
}

METHOD = {
    "udc.serial.select_entity_list": "GET",
    "udc.serial.select_entity_by_serial": "POST",
    "udc.entity_data.query_form_data": "POST",
    "udc.applog.list_app_data_by_dataid": "GET",
    "udc.applog.search_app_data_log": "POST",
    "udc.role.has_system_admin": "GET",
    "udc.appinfo.get_deploy_info": "GET",
    "udc.database.query_data": "GET",
    "udc.entity.history.select_by_condition": "POST",
    "udc.entity.ext.tree": "POST",
    "udc.entity.ext.list": "POST",
    "udc.entity.ext.available_datatype": "POST",
    "udc.entity.ext.attribute": "POST",
}

EVIDENCE_KEYS = ("source", "artifact", "version", "class", "method", "class_sha256", "javap", "evidence_level")


def _registry():
    return UdcOperationRegistry.default()


def test_entity_readonly_thirteen_registered():
    reg = _registry()
    for op in E13:
        assert reg.has(op), f"missing {op}"
        c = reg.get(op)
        assert c.write is False, f"{op} write should be False"
        assert c.status is OperationStatus.VERIFIED_STATIC_BYTECODE, f"{op} status should be VERIFIED"
    for op in GET_CONTRACTS:
        assert reg.get(op).effective is True, f"{op} GET 只读应 effective=True"
    for op in POST_CONTRACTS:
        assert reg.get(op).effective is False, f"{op} POST 读型应 effective=False"


def test_entity_readonly_locator_evidence():
    reg = _registry()
    for op in E13:
        c = reg.get(op)
        ev = c.evidence[0]
        for key in EVIDENCE_KEYS:
            assert key in ev, f"{op} locator 缺要素 {key}"
        assert ev["source"] == "local-maven", f"{op} source 应为 md 原值 local-maven"
        assert ev["evidence_level"] == "VERIFIED_STATIC_BYTECODE"
        assert ev["class_sha256"] == SHA[op], f"{op} class_sha256 与本轮独立重算值不符"
        # 路径逐字（含双斜杠 / deploy-info 无前缀等怪值原样）
        assert c.path == PATH[op], f"{op} path 须逐字 = {PATH[op]!r}，实为 {c.path!r}"
        assert c.method == METHOD[op], f"{op} method 须 {METHOD[op]}"
        # 未拼网关 service 前缀（deploy-info 本就连 udc-runtime 都无，更无前缀）
        assert "service/" not in c.path, f"{op} 路径误拼网关前缀"


def test_entity_excluded_three_not_registered():
    """端点重复 3 条（按 R15 C1 去重先例删一留一）不得入 registry。"""
    reg = _registry()
    for op in EXCLUDED:
        assert reg.has(op) is False, f"{op} 为端点重复排除项，不应入 registry"


def test_entity_existing_cross_domain_not_rewritten():
    """既有跨域同端点条目 C3/C4/C5/F2/A3 未被本轮改写（保留原路径/方法/SHA）。"""
    reg = _registry()
    for op in EXISTING:
        assert reg.has(op), f"existing {op} missing"
    c3 = reg.get("udc.applog.select_by_id")
    assert c3.path == "udc-runtime/app-log/datalog/{id}" and c3.evidence[0]["class_sha256"].startswith("f6a2111d")
    c4 = reg.get("udc.metadata.page_tree")
    assert c4.path == "udc-runtime/meta-data/select-host-and-only-page-pages" and c4.evidence[0]["class_sha256"].startswith("76787348")
    c5 = reg.get("udc.metadata.page_exists_check")
    assert c5.path == "udc-runtime/meta-data/check-page-exists" and c5.evidence[0]["class_sha256"].startswith("76787348")
    f2 = reg.get("udc.flow.form_data_query")
    assert f2.path == "udc-runtime/data/query" and f2.evidence[0]["class_sha256"].startswith("cabd3122")
    a3 = reg.get("udc.application.deploy_info")
    assert a3.path == "{currentAppName}/app-info/deploy-info" and a3.evidence[0]["class_sha256"].startswith("deebcc39")


def test_entity_form_data_double_slash_kept_verbatim():
    """#3 双斜杠 udc-runtime/data//query 逐字保留；与 F2 单斜杠同端点分域并存，note 标注。"""
    c = _registry().get("udc.entity_data.query_form_data")
    assert c.path == "udc-runtime/data//query", "双斜杠不得美化"
    f2 = _registry().get("udc.flow.form_data_query")
    assert f2.path == "udc-runtime/data/query", "F2 单斜杠未被双斜杠改写"
    blob = " ".join(str(v) for v in c.evidence[0].values() if isinstance(v, str))
    assert "udc.flow.form_data_query" in blob, "双斜杠条目须 note 标注与 F2 同端点分域"
    assert "UNVERIFIED" in blob, "双斜杠路由归一化 LIVE 复核 UNVERIFIED 标注须保留"


def test_entity_deploy_info_no_prefix_and_unverified():
    """#8 deploy-info 类级前缀缺省，完整路由 UNVERIFIED 不拼前缀；与 A3 分域并存。"""
    c = _registry().get("udc.appinfo.get_deploy_info")
    assert c.path == "deploy-info", "类级前缀缺省不得拼前缀"
    a3 = _registry().get("udc.application.deploy_info")
    assert a3.path == "{currentAppName}/app-info/deploy-info", "A3 原路径未被改写"
    blob = " ".join(str(v) for v in c.evidence[0].values() if isinstance(v, str))
    assert "UNVERIFIED" in blob, "完整路由 UNVERIFIED 标注须保留"
    assert "udc.application.deploy_info" in blob, "deploy-info 条目须 note 标注与 A3 同端点分域"


def test_entity_database_get_with_body_kept():
    """#11 GET 携带请求体 RuntimeDataBaseQueryDataReqDto 原样保留。"""
    c = _registry().get("udc.database.query_data")
    assert c.method == "GET"
    assert c.request_type == "com.seeyon.boot.starter.udcrt.dto.RuntimeDataBaseQueryDataReqDto"
    blob = " ".join(str(v) for v in c.evidence[0].values() if isinstance(v, str)) + " ".join(c.verification_rules)
    assert "GET" in blob and "请求体" in blob, "GET 带请求体语义标注须保留"


def test_entity_ext_four_same_class_independent_evidence():
    """ext 4 条同 class ScalabilityFieldController 同 SHA 4c6b8365，但逐条独立 evidence 不复用。"""
    reg = _registry()
    ext_ops = ("udc.entity.ext.tree", "udc.entity.ext.list", "udc.entity.ext.available_datatype", "udc.entity.ext.attribute")
    for op in ext_ops:
        ev = reg.get(op).evidence[0]
        assert ev["class"] == "com.seeyon.boot.starter.customplan.controller.ScalabilityFieldController"
        assert ev["class_sha256"] == SHA[op], f"{op} ext SHA 不符"
        assert ev["class_sha256"] == "4c6b836521d216b8f130d75e099727c6dfd16eee38c76ede08d1d6b05b3c0151"
    # 4 条 method 各不相同（selectMetadataExtEntityTree / listExtFileds / selectAvailableDatatype / selectAttribute）
    methods = [reg.get(op).evidence[0]["method"] for op in ext_ops]
    assert methods == [
        "selectMetadataExtEntityTree(String)",
        "listExtFileds(ScalabilityFieldQueryDto)",
        "selectAvailableDatatype(ScalabilityFieldQueryDto)",
        "selectAttribute(ScalabilityFieldQueryDto)",
    ], "ext 4 条须逐条独立 method，不复用同一条 evidence"
    # 4 条是 4 个不同 evidence dict 对象（逐条独立，不复用引用）
    ids = [id(reg.get(op).evidence[0]) for op in ext_ops]
    assert len(set(ids)) == 4, "ext 4 条 evidence 须为 4 个独立 dict（不复用同一引用）"
