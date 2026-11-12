# -*- coding: utf-8 -*-
"""护栏：04003(WARN) 掩蔽机制 + SERVICE 型可发布 + 04004 holder path 配对（第三十一轮）。

铁律：每条断言必须能追溯到 CFR 字节码类，或本轮 LIVE 实测口径。
任何只靠"写法直觉"的断言不许进来。含**对抗自证**：被证伪的旧结论必须能被咬住。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.microflow_constraints import (
    END_NODE_SELECT_PARAM_OUTPUT_NAME_IS_CONTEXT_KEY,
    SELECT_PARAM_DISPLAY_ONLY_KEYS,
    SELECT_PARAM_SCOPE_RESOLVING_KEYS,
    trigger_output_context_key,
    validate_end_node_scope,
)
from components.udc.microflow_constraints import (
    DRAFT_WARN_CODE,
    DRAFT_WARN_MASKS_DEEP_VALIDATION,
    LIVE_04004_FROM_MAPPING_PATH_PAIRING,
    MAPPING_PATH_ELEMENTS_NEED_JAVA_TYPE_PAIRING,
    MICRO_FLOW_DATA_STATES,
    MICRO_FLOW_TYPE_CODES,
    RELEASE_VALIDATION_DISPATCH_BY_TYPE,
    SERVICE_DRAFT_FORCED_ONLY_BY_CREATE_AND_UPDATE,
    SERVICE_TYPE_CAN_BE_RELEASED,
)


def test_04003_is_the_draft_warn_code():
    assert DRAFT_WARN_CODE == "UDC_CE_MICRO_FLOW_04003"


def test_draft_warn_masks_deep_validation():
    """CFR CheckUtils.parallelDetection:430-479 的 else 支：DRAFT 直接 warn 短路。"""
    assert DRAFT_WARN_MASKS_DEEP_VALIDATION is True


def test_release_dispatch_covers_frontend_family_and_entity_rule_skip():
    assert "MicroFlowFrontEndService.detection" in RELEASE_VALIDATION_DISPATCH_BY_TYPE["FRONTEND"]
    assert "MicroFlowFrontEndService.detection" in RELEASE_VALIDATION_DISPATCH_BY_TYPE["FUNCTION"]
    # ENTITY_RULE 且 sourceId 为空 -> continue（完全跳过），这是实测口径
    assert "跳过" in RELEASE_VALIDATION_DISPATCH_BY_TYPE["ENTITY_RULE"]


def test_service_type_code_is_zero():
    """MicroFlowTypeEnum 声明序（CFR udc-common 5.3.517）。"""
    assert MICRO_FLOW_TYPE_CODES == {
        "SERVICE": 0, "FRONTEND": 1, "ENTITY_RULE": 2, "CUSTOM": 3, "FUNCTION": 4,
    }


def test_data_state_codes():
    """MicroFlowDataStateEnum DRAFT(10) / RELEASE(20)。"""
    assert MICRO_FLOW_DATA_STATES == {"DRAFT": 10, "RELEASE": 20}


def test_service_type_can_be_released():
    """LIVE：1524985498115296151(type=SERVICE,state=10) 经 checkSchema/update 落 20/RELEASE。"""
    assert SERVICE_TYPE_CAN_BE_RELEASED is True
    assert SERVICE_DRAFT_FORCED_ONLY_BY_CREATE_AND_UPDATE is True


def test_old_claim_service_can_never_publish_is_refuted():
    """对抗自证：旧结论「SERVICE 型永不可能发布」必须被咬住。"""
    # 旧措辞的判据是「setServiceMfToDraft 对所有入口生效」=> 与 checkSchemaAndUpdate 不受其影响冲突
    assert SERVICE_DRAFT_FORCED_ONLY_BY_CREATE_AND_UPDATE is True
    assert SERVICE_TYPE_CAN_BE_RELEASED is True


def test_mapping_path_elements_need_pairing():
    assert MAPPING_PATH_ELEMENTS_NEED_JAVA_TYPE_PAIRING is True
    assert LIVE_04004_FROM_MAPPING_PATH_PAIRING == 4


def test_live_count_consistent_with_real_schema():
    """复算 LIVE 样本：6 个 path 元素中 4 个 dataType<->javaType 不配对。"""
    from components.udc.data_type_java_type import java_type_mismatches
    bad = [
        {"dataType": "INTEGER", "javaType": "java.lang.String", "name": "expNum"},
        {"dataType": "INTEGER", "javaType": "java.lang.String", "name": "expNum"},
        {"dataType": "BOOLEAN", "javaType": "java.lang.String", "name": "expFlag"},
        {"dataType": "BOOLEAN", "javaType": "java.lang.String", "name": "expFlag"},
    ]
    ok = [
        {"dataType": "STRING", "javaType": "java.lang.String", "name": "h"},
        {"dataType": "STRING", "javaType": "java.lang.String", "name": "h"},
    ]
    assert sum(1 for f in bad if java_type_mismatches(f)) == LIVE_04004_FROM_MAPPING_PATH_PAIRING
    assert all(not java_type_mismatches(f) for f in ok)


# =====================================================================
# 第三十二轮 LIVE 新增：04004 最后 1 条 = endNode.value.selectParam.outputName 未命中 context 注册键
# 证据等级：LIVE 四臂 A/B（每臂都用 REST + MySQL 双面确认 state=20/RELEASE）+ CFR udc-biz 5.3.517
# =====================================================================

LIVE_MF_ID = "1524985498115296151"
LIVE_TRIGGER_JAVA_TYPE = "xzhExp950795.com.seeyon.udc.common.event.AfterUpdateEvent"


def test_context_key_formula_is_stripped_java_type():
    """CFR CheckUtils.detectionTrigger:1468/1471 = javaType.replace(".","")。

    ★ 关键：**不是** output.name（`_FLOW_OUTPUT_evt1` / `_BUSINESS_EVENT_xxxxxx`）。
    全库 252 条 BUSINESS_EVENT 微流程扫描：仅 1 条 endNode.value 非空，且其 outputName
    正是去点 FQN —— 与公式一致（唯一能对照的样本）。
    """
    assert trigger_output_context_key(LIVE_TRIGGER_JAVA_TYPE) ==         "xzhExp950795comseeyonudccommoneventAfterUpdateEvent"
    # 与 output.name 明确不同：这是本轮真正踩的坑
    assert trigger_output_context_key(LIVE_TRIGGER_JAVA_TYPE) != "_FLOW_OUTPUT_evt1"
    assert END_NODE_SELECT_PARAM_OUTPUT_NAME_IS_CONTEXT_KEY is True


def test_only_output_name_resolves_scope():
    """checkSelectParam:912 只把 selectParam.getOutputName() 交给 checkScope。

    name/path/key 不参与查表 -> LIVE X 组带占位值仍全绿。
    """
    assert SELECT_PARAM_SCOPE_RESOLVING_KEYS == ("outputName",)
    assert set(SELECT_PARAM_DISPLAY_ONLY_KEYS) == {"name", "path", "key"}


def test_validate_end_node_scope_flags_wrong_output_name():
    """LIVE P 臂：outputName=`_FLOW_OUTPUT_evt1` -> RELEASE 报 MFEndNode_&_value / OUT_OF_SCOPE。"""
    dto = {"dataSchema": _live_schema_shaped(end_node_output_name="_FLOW_OUTPUT_evt1")}
    errs = validate_end_node_scope(dto)
    assert len(errs) == 1
    assert "OUT_OF_SCOPE" in errs[0] or "前序节点发生变更请重新选择" in errs[0]


def test_validate_end_node_scope_accepts_canonical_output_name():
    """LIVE Q 臂：outputName = 去点 FQN -> 该微流程从检测面消失（ERROR 0）。"""
    dto = {"dataSchema": _live_schema_shaped(
        end_node_output_name=trigger_output_context_key(LIVE_TRIGGER_JAVA_TYPE))}
    assert validate_end_node_scope(dto) == []


def test_placeholder_name_path_key_do_not_matter():
    """对抗自证：本轮早先「四键需一致」的猜测必须被咬住。

    LIVE X 组：outputName 正确、name/path/key 全为占位 `_FLOW_OUTPUT_evt1` -> 仍然通过。
    """
    dto = {"dataSchema": _live_schema_shaped(
        end_node_output_name=trigger_output_context_key(LIVE_TRIGGER_JAVA_TYPE),
        name="_FLOW_OUTPUT_evt1", path="_FLOW_OUTPUT_evt1", key="_FLOW_OUTPUT_evt1")}
    assert validate_end_node_scope(dto) == []


def test_validate_end_node_scope_skips_non_business_event():
    """公式仅对 BusinessEventTrigger 经 CFR 证实 => 其它 trigger 不误报。"""
    import json as _json
    ds = _json.loads(_live_schema_shaped(end_node_output_name="_FLOW_OUTPUT_evt1"))
    ds["trigger"]["type"] = "MANUAL"
    assert validate_end_node_scope({"dataSchema": _json.dumps(ds)}) == []


def _live_schema_shaped(end_node_output_name, name=None, path=None, key=None):
    """按 LIVE 实测形状（读面 JSON）构造最小 schema；仅保留判据相关字段。"""
    import json as _json
    return _json.dumps({
        "trigger": {
            "nodeId": "SERVICE_Fzkl08",
            "type": "BUSINESS_EVENT",
            "output": {"javaType": LIVE_TRIGGER_JAVA_TYPE, "name": "_FLOW_OUTPUT_evt1",
                       "dataType": "DTO", "type": "OBJECT"},
        },
        "endNode": {
            "nodeId": "MFEndNode", "paramType": "ENTITY_OBJECT",
            "value": {"type": "SelectParam", "selectParam": {
                "name": name or "_FLOW_OUTPUT_evt1",
                "path": path or "_FLOW_OUTPUT_evt1",
                "key": key or "_FLOW_OUTPUT_evt1",
                "outputName": end_node_output_name,
                "javaType": "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto",
                "dataType": "DTO", "type": "OBJECT", "dtoType": "MASTER_ENTITY",
            }},
        },
        "nodes": [],
    })


def test_live_ab_vertical_slice_with_negative_control():
    """本件判据须有**负控**支撑，不能只有正例。

    A 臂（正）outputName=去点 FQN -> ERROR=0 且该微流程不出现在检测面；
    B 臂（负控）**只**改 outputName 回 `_FLOW_OUTPUT_evt1` -> ERROR=1 / route MFEndNode_&_value。
    两臂 state 均由 REST + MySQL 双面确认为 20（RELEASE）。
    """
    from components.udc.microflow_constraints import LIVE_END_NODE_AB_VERTICAL_SLICE as S
    assert S["micro_flow_id"] == LIVE_MF_ID
    assert S["trigger_output_java_type"] == LIVE_TRIGGER_JAVA_TYPE
    pos, neg = S["positive"], S["negative_control"]
    assert pos["output_name"] == trigger_output_context_key(LIVE_TRIGGER_JAVA_TYPE)
    assert pos["error_count"] == 0 and pos["micro_flow_present_in_detection"] is False
    assert neg["output_name"] == "_FLOW_OUTPUT_evt1"
    assert neg["error_count"] == 1
    assert neg["code"] == "UDC_MICRO_FLOW_04004"
    assert neg["route"] == "MFEndNode_&_value"
    # 负控必须是**单变量**对照：除 outputName 外三键与正例相同（皆占位）
    assert pos["output_name"] != neg["output_name"]


def test_check_schema_cannot_observe_end_node_scope():
    """对抗自证：拿 checkSchema 当判据必须被咬住。

    两臂 checkSchema/update 均返回 check:true, errors:0 而检测面 ERROR 0 vs 1
    => 浅校验对本判据**完全不可见**，必须 RELEASE + 检测面观测。
    """
    from components.udc.microflow_constraints import END_NODE_SCOPE_IS_INVISIBLE_TO_CHECK_SCHEMA
    assert END_NODE_SCOPE_IS_INVISIBLE_TO_CHECK_SCHEMA is True
