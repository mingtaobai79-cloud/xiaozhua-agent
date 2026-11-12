"""R16: application 域 5 条只读契约（search.no_page / search.page / deploy_info / draft.select / draft.exist）入 registry 的最小验证。

证据等级 VERIFIED_STATIC_BYTECODE（本地 Maven 5.3 族离线反编译，非 LIVE；source=local-maven-53517，与 test2 部署态版本族隔离）。
路径按控制器原值（类级 @RequestMapping + 方法级 @*Mapping），不拼网关 service 前缀（离线不可确证 → UNVERIFIED）。
3 个 class SHA 本轮 zipfile 直读 jar 内 class 字节独立重算自证，与 md 声明 + main 核实值一致：
  CustomApplicationController=d3e82d8b / UdcBaseAppInfoController=deebcc39 / AppDraftController=5090304d。
search.page 的控制器方法 = selectListByConditions 的 PageInfo 重载（javap 原文；方法体调后端 appservice.selectPageListByConditions，
  已在 evidence note 标注，防止把后端方法名误当控制器方法名）。

.effective 判定（models.py：status∈{PASS,VERIFIED_STATIC_BYTECODE,OBSERVED} 且 write=False 且 method=="GET"）：
- deploy_info（GET，但完整路由依赖子类类级前缀，父类无类级 @RequestMapping → UNVERIFIED 路由）→ 静态层 effective=True
- search.no_page / search.page / draft.select / draft.exist（POST，执行层仅放行 GET）→ effective=False（与 C4-C8/F 域同边界）
"""
from components.platform_operations.models import OperationStatus
from components.platform_operations.registry import UdcOperationRegistry

A5 = (
    "udc.application.search.no_page",
    "udc.application.search.page",
    "udc.application.deploy_info",
    "udc.application.draft.select",
    "udc.application.draft.exist",
)
GET_CONTRACTS = ("udc.application.deploy_info",)
POST_CONTRACTS = ("udc.application.search.no_page", "udc.application.search.page", "udc.application.draft.select", "udc.application.draft.exist")

SHA = {
    "udc.application.search.no_page": "d3e82d8bbc65dc92d5f9d30532159f1d10169f2aef1eae6ab67c70d7ad75ae55",
    "udc.application.search.page": "d3e82d8bbc65dc92d5f9d30532159f1d10169f2aef1eae6ab67c70d7ad75ae55",
    "udc.application.deploy_info": "deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95",
    "udc.application.draft.select": "5090304dcb69cd0d3cd7b4e961d6ceff5f41e56d27b60eecf48950a34e5fabb9",
    "udc.application.draft.exist": "5090304dcb69cd0d3cd7b4e961d6ceff5f41e56d27b60eecf48950a34e5fabb9",
}

EVIDENCE_KEYS = ("artifact", "version", "class", "method", "class_sha256", "javap", "source", "evidence_level")


def _registry():
    return UdcOperationRegistry.default()


def test_application_readonly_five_registered():
    reg = _registry()
    for op in A5:
        assert reg.has(op), f"missing {op}"
        c = reg.get(op)
        assert c.write is False, f"{op} write should be False"
        assert c.status is OperationStatus.VERIFIED_STATIC_BYTECODE
    for op in GET_CONTRACTS:
        assert _registry().get(op).effective is True, f"{op} GET 只读应 effective=True"
    for op in POST_CONTRACTS:
        assert _registry().get(op).effective is False, f"{op} POST 读型应 effective=False"


def test_application_readonly_locator_evidence():
    reg = _registry()
    for op in A5:
        c = reg.get(op)
        ev = c.evidence[0]
        for key in EVIDENCE_KEYS:
            assert key in ev, f"{op} locator 缺要素 {key}"
        assert ev["source"] == "local-maven-53517"
        assert ev["evidence_level"] == "VERIFIED_STATIC_BYTECODE"
        assert ev["class_sha256"] == SHA[op], f"{op} class_sha256 与本轮独立重算值不符"
        # 网关 service 前缀未拼
        assert "service/" not in c.path, f"{op} 路径误拼网关前缀"


def test_application_deploy_info_route_unverified_not_invented():
    """deploy_info 完整路由依赖子类类级前缀，父类无类级 @RequestMapping → 保留 UNVERIFIED 标注，不拼前缀。"""
    c = _registry().get("udc.application.deploy_info")
    assert c.path == "{currentAppName}/app-info/deploy-info"
    blob = " ".join(str(v) for v in c.evidence[0].values() if isinstance(v, str)) + " ".join(c.verification_rules)
    assert "UNVERIFIED" in blob, "deploy_info 完整路由 UNVERIFIED 标注须保留"
    # 子类前缀差异如实标注
    assert "FormAppInfoController" in blob and "NormalAppInfoController" in blob


def test_application_search_page_method_is_javap_controller_method():
    """search.page 控制器方法 = selectListByConditions（PageInfo 重载），非后端 appservice 的 selectPageListByConditions。"""
    ev = _registry().get("udc.application.search.page").evidence[0]
    assert ev["method"] == "selectListByConditions", "search.page 控制器方法名须按 javap 原文（PageInfo 重载），勿误用后端方法名"
    no_page_ev = _registry().get("udc.application.search.no_page").evidence[0]
    assert no_page_ev["method"] == "selectListByConditions"


def test_application_draft_pair_same_class_different_method():
    """draft.select / draft.exist 同 class（AppDraftController）不同 method（select/exist），同 SHA。"""
    reg = _registry()
    sel = reg.get("udc.application.draft.select")
    exi = reg.get("udc.application.draft.exist")
    assert sel.evidence[0]["method"] == "select"
    assert exi.evidence[0]["method"] == "exist"
    assert sel.evidence[0]["class_sha256"] == exi.evidence[0]["class_sha256"] == SHA["udc.application.draft.select"]
