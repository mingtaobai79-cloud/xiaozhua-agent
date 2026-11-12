"""UDC-MERGE 批2: resource 域 5 条只读契约（attachment.template × 3 / jar.download / jar.export_app）
入 registry 的最小验证。

证据等级 VERIFIED_STATIC_BYTECODE（本地 Maven 5.3 族离线反编译，非 LIVE；source=local-maven-53517，
与 test2 部署态版本族隔离）。路径按控制器原值（类级 @RequestMapping + 方法级 @*Mapping），
不拼网关 service 前缀（离线不可确证 → UNVERIFIED）。

class SHA 本轮 zipfile 直读 jar 内 class 字节独立重算自证，与 registry-entries.md 声明一致：
  AttachmentTemplateController=72241cb3 / DynamicJarController=0eb1fd79。

.effective 判定（models.py：status∈{PASS,VERIFIED_STATIC_BYTECODE,OBSERVED} 且 write=False 且 method==GET）：
- GET 3 条（template_get_by_guid / template_list_by_app_id / jar.download）→ effective=True
- POST 读型 2 条（template_list_by_guids / jar.export_app）→ effective=False（执行链仅放行 GET）；
  jar.export_app 的"POST 导出是否属只读边界"已在 evidence note 保留主控裁定标注，不在此测试代决。

排除纪律：resource 域写形态（upload 等 5 条 W 段）不入 registry；runtime 域 13 条建议未落库（待裁定）。
"""
from components.platform_operations.models import OperationStatus
from components.platform_operations.registry import UdcOperationRegistry

GET_CONTRACTS = (
    "udc.attachment.template_get_by_guid",
    "udc.attachment.template_list_by_app_id",
    "udc.jar.download",
)
POST_CONTRACTS = (
    "udc.attachment.template_list_by_guids",
    "udc.jar.export_app",
)
ALL = GET_CONTRACTS + POST_CONTRACTS

# class_sha256（本轮独立重算，对照 registry-entries.md 声明）
SHA = {
    "udc.attachment.template_get_by_guid": "72241cb3ae302c91cd3baba690eaa25656adcedc13e7cdf25413deebd31444f3",
    "udc.attachment.template_list_by_guids": "72241cb3ae302c91cd3baba690eaa25656adcedc13e7cdf25413deebd31444f3",
    "udc.attachment.template_list_by_app_id": "72241cb3ae302c91cd3baba690eaa25656adcedc13e7cdf25413deebd31444f3",
    "udc.jar.download": "0eb1fd79e96e09eb0122c0aafd77d8922ee3163f46f5436a44c98b476726def2",
    "udc.jar.export_app": "0eb1fd79e96e09eb0122c0aafd77d8922ee3163f46f5436a44c98b476726def2",
}

EVIDENCE_KEYS = ("artifact", "version", "class", "method", "class_sha256", "source", "evidence_level")


def _registry():
    return UdcOperationRegistry.default()


def test_resource_readonly_all_registered():
    reg = _registry()
    for op in ALL:
        assert reg.has(op), f"{op} 应已落库"
        c = reg.get(op)
        assert c.status == OperationStatus.VERIFIED_STATIC_BYTECODE, f"{op} 分级应封顶 VERIFIED_STATIC_BYTECODE"
        assert c.write is False, f"{op} 只读契约 write 应为 False"


def test_resource_readonly_effective_boundary():
    reg = _registry()
    # GET 3 条：执行链可放行
    for op in GET_CONTRACTS:
        assert reg.get(op).effective is True, f"{op} GET 只读应 effective=True"
    # POST 读型 2 条：执行链仅放行 GET → effective=False
    for op in POST_CONTRACTS:
        assert reg.get(op).effective is False, f"{op} POST 读型应 effective=False"


def test_resource_readonly_locator_evidence():
    reg = _registry()
    for op in ALL:
        c = reg.get(op)
        ev = c.evidence[0]
        for key in EVIDENCE_KEYS:
            assert key in ev, f"{op} locator 缺要素 {key}"
        assert ev["source"] == "local-maven-53517"
        assert ev["evidence_level"] == "VERIFIED_STATIC_BYTECODE"
        assert ev["class_sha256"] == SHA[op], f"{op} class_sha256 与本轮独立重算值不符"
        # 未拼网关 service 前缀
        assert "service/" not in c.path, f"{op} 路径误拼网关前缀"
        # 网关前缀离线不可确证 → verification_rules 尾条必须含 UNVERIFIED 标注（5 条均在 rules，照建议件原样）
        rules = " ".join(c.verification_rules or ())
        assert "UNVERIFIED" in rules, f"{op} 缺网关 service 前缀 UNVERIFIED 标注"


def test_resource_write_side_not_registered():
    """写形态（upload 等）不入只读 MERGE；runtime 域建议未落库（待裁定）。"""
    reg = _registry()
    for op in (
        "udc.attachment.upload",
        "udc.attachment.create",
        "udc.attachment.delete",
        "udc.runtime.env_check_build_info",  # runtime 建议 #1，未裁定不得提前落库
        "udc.runtime.graphql_proxy_graphql",
    ):
        assert not reg.has(op), f"{op} 不应在只读 MERGE 范围内"
