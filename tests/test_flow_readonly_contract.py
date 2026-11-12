"""R15: flow 域 8 条只读契约（bpm_node_info / form_data / data_flow_map / data_flow_mapping）入 registry 的最小验证。

证据等级 VERIFIED_STATIC_BYTECODE（本地 Maven 5.3 族离线反编译，非 LIVE；source=local-maven-53517，与 test2 部署态版本族隔离）。
路径按控制器原值（类级 @RequestMapping + 方法级 @*Mapping），不拼网关 service 前缀（离线不可确证 → UNVERIFIED）。
SHA 本轮 zipfile 直读 3 个 jar（customplan/runtime/dataflow）内 4 class 独立重算自证，与 md 声明一致：
  BpmNodeInfo=95e1752d / UdcFormDataQuery=cabd3122 / DataFlowRtMap=455df593 / DataFlowRtMapping=ee742c70。
第 2 条 udc.flow.function_node_tree 已跨域归一为 C1 udc.microflow.function_node_tree（同 controller+method+SHA），
  本轮不重复登记（去重沿用 C1）。写侧 3 条（write=True）不纳入本轮（维持 A5 POLICY_DENIED）。

.effective 判定（models.py：status∈{PASS,VERIFIED_STATIC_BYTECODE,OBSERVED} 且 write=False 且 method==GET）：
- GET 只读 2 条 → effective True（data_flow_map_get_by_id / data_flow_mapping_get_by_id，与 C1/C2/C3 同）。
- POST 读型 6 条 → effective False（执行链仅放行 GET，PlatformOperationLayer 上 DENIED/POLICY_DENIED，与 C4-C8 同边界，可执行性留活体 P4）。
"""
from components.platform_operations.models import OperationStatus
from components.platform_operations.registry import UdcOperationRegistry

# 8 条 flow 只读契约（第 1/3/4/5/6/7/8/9 条；第 2 条已归一为 C1，不在此列）
POST_CONTRACTS = (
    "udc.flow.bpm_node_info_search",
    "udc.flow.form_data_query",
    "udc.flow.data_flow_map_search",
    "udc.flow.data_flow_mapping_search_original",
    "udc.flow.data_flow_mapping_init_data",
    "udc.flow.data_flow_mapping_detail",
)
GET_CONTRACTS = (
    "udc.flow.data_flow_map_get_by_id",
    "udc.flow.data_flow_mapping_get_by_id",
)
ALL = POST_CONTRACTS + GET_CONTRACTS

# class_sha256（本轮独立重算，对照 md 声明）
SHA = {
    "udc.flow.bpm_node_info_search": "95e1752d83c9152e6236d825b2aaea1e82fd60516b1f7c2a3c2f2249df395bb2",
    "udc.flow.form_data_query": "cabd312210665274361568181b6d41b9a86f7ed13f1dba7e3f844dc2e5ea5584",
    "udc.flow.data_flow_map_get_by_id": "455df593d43558055e01d69f4aacc70ce337ec80b4f7275adc471c49a22d1d95",
    "udc.flow.data_flow_map_search": "455df593d43558055e01d69f4aacc70ce337ec80b4f7275adc471c49a22d1d95",
    "udc.flow.data_flow_mapping_get_by_id": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8",
    "udc.flow.data_flow_mapping_search_original": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8",
    "udc.flow.data_flow_mapping_init_data": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8",
    "udc.flow.data_flow_mapping_detail": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8",
}

EVIDENCE_KEYS = ("artifact", "version", "class", "method", "class_sha256", "javap", "source", "evidence_level")


def _registry():
    return UdcOperationRegistry.default()


def test_flow_readonly_eight_registered():
    reg = _registry()
    for op in ALL:
        assert reg.has(op), f"missing {op}"
        c = reg.get(op)
        assert c.write is False, f"{op} write should be False"
        assert c.status is OperationStatus.VERIFIED_STATIC_BYTECODE
    # GET 只读 2 条：执行链可放行（method=GET 且 write=False 且 VERIFIED）
    for op in GET_CONTRACTS:
        assert _registry().get(op).effective is True, f"{op} GET 只读应 effective=True"
    # POST 读型 6 条：执行链仅放行 GET → effective=False（与 C4-C8 同边界）
    for op in POST_CONTRACTS:
        assert _registry().get(op).effective is False, f"{op} POST 读型应 effective=False"


def test_flow_readonly_locator_evidence():
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
        # POST 读型 evidence note 须含网关前缀 UNVERIFIED 标注
        note = ev.get("note", "")
        if c.method == "POST":
            assert "UNVERIFIED" in note, f"{op} POST 读型缺网关 service 前缀 UNVERIFIED 标注"


def test_flow_function_node_tree_dedup_not_re_registered():
    """第 2 条 udc.flow.function_node_tree 已归一为 C1 udc.microflow.function_node_tree，本轮不重复登记。"""
    reg = _registry()
    # 归一目标 C1 仍在（沿用）
    assert reg.has("udc.microflow.function_node_tree")
    # flow 域不新登记重复 operation_id（去重删一留一）
    assert not reg.has("udc.flow.function_node_tree"), "udc.flow.function_node_tree 不得与 C1 重复登记"


def test_flow_write_side_not_in_readonly_merge():
    """写侧 3 条（write=True）不纳入本轮只读 MERGE，维持 A5 POLICY_DENIED。"""
    reg = _registry()
    for op in ("udc.flow.bpm_fill_error_data", "udc.flow.data_flow_mapping_update", "udc.flow.data_flow_mapping_update_state"):
        assert not reg.has(op), f"{op} 写侧契约不应入本轮只读 MERGE"
