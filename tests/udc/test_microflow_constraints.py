"""测试：微流程节点约束模型（后端权威）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.microflow_constraints import (
    ACTIVITY_NODE_TYPES, CONTROL_NODE_TYPES, DATA_MAPPING_MODES, DATA_MAPPING_TARGET_TYPES,
    RETRIEVE_ARRAY_BY_FETCHTYPE, LIST_OPERATIONS, required_fields, validate_node_fields,
    MAPPING_TYPES, NULL_HANDLING, CONDITION_OPERATORS,
)


def test_activity_node_types_have_48_codes():
    assert ACTIVITY_NODE_TYPES["RETRIEVE"] == 10
    assert ACTIVITY_NODE_TYPES["DATA_MAPPING"] == 45
    assert ACTIVITY_NODE_TYPES["SET_DATASOURCE"] == 48
    assert "CONNECTOR" in ACTIVITY_NODE_TYPES


def test_control_node_types():
    assert CONTROL_NODE_TYPES["ACTIVITY"] == 5
    assert CONTROL_NODE_TYPES["BRANCH"] == 2


def test_data_mapping_enums():
    assert DATA_MAPPING_TARGET_TYPES == ("ENTITY", "DTO")
    assert DATA_MAPPING_MODES == ("REFERENCE", "CONSTANT")
    assert "FieldCopy" not in DATA_MAPPING_MODES


def test_retrieve_array_fetchtype_requires():
    # ★ 基础必填（选择器回填）任何 fetchType 都在
    assert "structure" in required_fields("RETRIEVE_ARRAY", {"fetchType": "CONDITION"})
    assert "variableTitle" in required_fields("RETRIEVE_ARRAY", {"fetchType": "CONDITION"})
    # 分支必填
    assert "value" in required_fields("RETRIEVE_ARRAY", {"fetchType": "IDS"})
    assert "aggFunction" in required_fields("RETRIEVE_ARRAY", {"fetchType": "OTHERS"})
    # CONDITION 分支：condition 与 value 都没有时给出联合必填
    assert "condition|value" in required_fields("RETRIEVE_ARRAY", {"fetchType": "CONDITION"})
    assert "condition|value" not in required_fields(
        "RETRIEVE_ARRAY", {"fetchType": "CONDITION", "condition": {"type": "CONDITION"}})
    # size 不是必填（实测 62%，旧表按必填要求是错的）
    assert "size" not in required_fields("RETRIEVE_ARRAY", {"fetchType": "CONDITION"})


def test_retrieve_null_prompt_only_stop():
    assert "nullPromptMessage" in required_fields("RETRIEVE", {"nullHandling": "TERMINATION"})
    assert "nullPromptMessage" not in required_fields("RETRIEVE", {"nullHandling": "CONTINUE", "fetchType": "CONDITION"})


def test_validate_node_fields():
    # ★ 前端权威必填是 5 项（deleteType/app/structure/condition/title），不是只有 deleteType
    assert validate_node_fields("DELETE_ENTITY", {}) == [
        "DELETE_ENTITY 缺必填字段 deleteType", "DELETE_ENTITY 缺必填字段 app",
        "DELETE_ENTITY 缺必填字段 structure", "DELETE_ENTITY 缺必填字段 condition",
        "DELETE_ENTITY 缺必填字段 title"]
    assert validate_node_fields("DATA_MAPPING", {"mappingRule": {"targetType": "ENTITY", "mappingRows": [{"uuid": "x"}]}}) == []
    errs = validate_node_fields("DATA_MAPPING", {})
    assert any("mappingRule.targetType" in e for e in errs) and any("mappingRule.mappingRows" in e for e in errs)
    errs = validate_node_fields("CALL_DATA_FLOW", {"dataFlowMappingId": "1"})
    assert any("structure" in e for e in errs) and any("entityId" in e for e in errs)


def test_list_operations_and_enums():
    assert LIST_OPERATIONS["sum"] == "求和"
    assert LIST_OPERATIONS["groupAndSum"] == "分组汇总"
    assert MAPPING_TYPES == ("attrs", "value", "mapping")
    assert NULL_HANDLING == ("TERMINATION", "CONTINUE")


def test_condition_operator_size():
    from components.udc.microflow_constraints import condition_operator_size
    assert condition_operator_size("EQ") == 1
    assert condition_operator_size("NULL") == 0
    assert condition_operator_size("ZERO") == 0
    assert condition_operator_size("BETWEEN") == 2
    assert condition_operator_size("BOGUS") == -1
    assert CONDITION_OPERATORS["NEQ"][0] == "<>"


def test_entity_data_types_and_captions():
    from components.udc.microflow_constraints import (
        ENTITY_DATA_TYPES, ENTITY_DATA_TYPE_IMPLS, ACTIVITY_NODE_CAPTIONS, MICROFLOW_GROUP_TYPES,
        CONDITION_LOGICAL_OPERATORS, CONDITION_ITEM_TYPES)
    assert "DATETIME" in ENTITY_DATA_TYPES and "CTPENUM" in ENTITY_DATA_TYPES
    assert ENTITY_DATA_TYPE_IMPLS["ENTITY"] == "EntityDataType"
    assert ACTIVITY_NODE_CAPTIONS["RETRIEVE_ARRAY"] == "查询多记录"
    assert ACTIVITY_NODE_CAPTIONS["DELETE_ENTITY"] == "删除数据"
    assert MICROFLOW_GROUP_TYPES["MICRO_FLOW_SCHEDULE"] == "定时任务"
    assert CONDITION_LOGICAL_OPERATORS["AND"] == ("and", "&&", "and")
    assert CONDITION_LOGICAL_OPERATORS["OR"][0] == "or"
    assert CONDITION_ITEM_TYPES == ("GROUP", "CONDITION")

# ---- DATA_MAPPING.mappingRule / BusinessEventTrigger 的 parse 必填集（CFR udc-biz 5.3.517）----

def test_mapping_rule_required_keys_are_the_parse_set():
    from components.udc.microflow_constraints import (
        MAPPING_RULE_REQUIRED_KEYS, MAPPING_FIELD_REQUIRED_KEYS,
        BUSINESS_EVENT_TRIGGER_REQUIRED_KEYS)
    assert MAPPING_RULE_REQUIRED_KEYS == ("uuid", "type", "javaType", "name",
                                          "mappingRows", "subobjects")
    assert MAPPING_FIELD_REQUIRED_KEYS == ("name", "dataType", "type", "javaType")
    assert "eventDataFullName" in BUSINESS_EVENT_TRIGGER_REQUIRED_KEYS
    assert "eventFullName" in BUSINESS_EVENT_TRIGGER_REQUIRED_KEYS


def test_validate_mapping_rule_non_object():
    from components.udc.microflow_constraints import validate_mapping_rule
    assert validate_mapping_rule(None) != []
    assert validate_mapping_rule("x") != []
    assert any("parseMappingRule" in e for e in validate_mapping_rule(None))


def test_validate_mapping_rule_empty_reports_every_rule_key():
    from components.udc.microflow_constraints import (
        validate_mapping_rule, MAPPING_RULE_REQUIRED_KEYS)
    errs = validate_mapping_rule({})
    assert len(errs) == len(MAPPING_RULE_REQUIRED_KEYS)
    for k in MAPPING_RULE_REQUIRED_KEYS:
        assert any(repr(k) in e for e in errs)


def test_validate_mapping_rule_complete_rule_passes():
    from components.udc.microflow_constraints import validate_mapping_rule
    ok = {"uuid": "r1", "type": "OBJECT", "javaType": "java.lang.Object",
          "name": "_mr", "mappingRows": [], "subobjects": []}
    assert validate_mapping_rule(ok) == []
    thin = {"uuid": "r1", "targetType": "ENTITY", "mappingRows": []}
    errs = validate_mapping_rule(thin)
    assert errs and all("rule 级 required=true" in e for e in errs)
    assert not any("mappingRows[" in e for e in errs)


def test_validate_mapping_rule_holder_and_path_elements():
    from components.udc.microflow_constraints import validate_mapping_rule
    base = {"uuid": "r1", "type": "OBJECT", "javaType": "java.lang.Object",
            "name": "_mr", "subobjects": []}
    mr = dict(base, mappingRows=[{"targetField": {"name": "f", "dataType": "STRING",
                                                  "type": "OBJECT"}}])
    errs = validate_mapping_rule(mr)
    assert any("mappingRows[0].targetField" in e and "javaType" in e for e in errs)
    assert any("mappingRule" in e and "parse 复用 rule location" in e for e in errs)
    mr2 = dict(base, mappingRows=[{"targetField": {
        "name": "f", "dataType": "STRING", "type": "OBJECT", "javaType": "java.lang.String",
        "path": [{"name": "a", "type": "OBJECT", "javaType": "java.lang.String"}]}}])
    errs2 = validate_mapping_rule(mr2)
    assert any(".path[0]" in e and "dataType" in e for e in errs2)
    mr3 = dict(base, mappingRows=[{"value": {"reference": {"name": "r"}}}])
    errs3 = validate_mapping_rule(mr3)
    assert any("mappingRows[0].value.reference" in e for e in errs3)


def test_validate_mapping_rule_accepts_fully_populated_row():
    from components.udc.microflow_constraints import validate_mapping_rule
    holder = {"name": "f", "dataType": "STRING", "type": "OBJECT", "javaType": "java.lang.String",
              "path": [{"name": "a", "dataType": "STRING", "type": "OBJECT",
                        "javaType": "java.lang.String"}]}
    mr = {"uuid": "r1", "type": "OBJECT", "javaType": "java.lang.Object", "name": "_mr",
          "subobjects": [], "mappingRows": [{"targetField": dict(holder)}]}
    assert validate_mapping_rule(mr) == []


# ---- 第二十七轮：RELEASE 发布闸门 / 深度校验（LIVE udc-test2 实测 + CFR 字节码）----

def test_publish_endpoint_and_gate_semantics():
    from components.udc.microflow_constraints import (
        PUBLISH_ENDPOINT, RELEASE_GATE_NOTE, PARSER_IS_FAIL_FAST)
    # 只有 checkSchema/update 会发布；update/create 强制草稿（CFR setServiceMfToDraft）
    assert PUBLISH_ENDPOINT == "POST /service/udc/microflow/checkSchema/update"
    assert "RELEASE" in RELEASE_GATE_NOTE
    # 每节点只报第一条缺失属性（LIVE 打地鼠实测）
    assert PARSER_IS_FAIL_FAST is True


def test_end_node_and_sort_param_contracts():
    from components.udc.microflow_constraints import (
        END_NODE_VALUE_TYPES, SORT_PARAM_REQUIRED_KEYS, SORT_PARAM_ATTRTYPE_REQUIRED_KEYS,
        MAPPING_HOLDER_REQUIRED_KEYS)
    assert END_NODE_VALUE_TYPES == ("SelectParam", "Expression")
    assert SORT_PARAM_REQUIRED_KEYS == ("sortType", "attrType")
    assert "javaType" in SORT_PARAM_ATTRTYPE_REQUIRED_KEYS
    assert MAPPING_HOLDER_REQUIRED_KEYS == ("name", "dataType", "type", "javaType")


def test_release_readiness_flags_non_release_state():
    from components.udc.microflow_constraints import validate_release_readiness
    errs = validate_release_readiness({"state": "DRAFT", "dataSchema": "{}"})
    assert any("不发布" in e for e in errs)


def test_release_readiness_flags_endnode_missing_value():
    import json
    from components.udc.microflow_constraints import validate_release_readiness
    ds = json.dumps({"endNode": {"paramType": "ENTITY_OBJECT", "value": None}, "nodes": []})
    errs = validate_release_readiness({"state": "RELEASE", "dataSchema": ds})
    assert any("endNode.value" in e for e in errs)


def test_release_readiness_flags_selectparam_without_dtotype():
    import json
    from components.udc.microflow_constraints import validate_release_readiness
    ds = json.dumps({"endNode": {"paramType": "ENTITY_OBJECT",
                                 "value": {"type": "SelectParam", "selectParam": {}}}, "nodes": []})
    errs = validate_release_readiness({"state": "RELEASE", "dataSchema": ds})
    assert any("dtoType" in e for e in errs)


def test_release_readiness_flags_sortparam_attrtype_as_string():
    import json
    from components.udc.microflow_constraints import validate_release_readiness
    node = {"nodeId": "RA1", "actionType": "RETRIEVE_ARRAY",
            "sortParams": [{"sortType": "DESC", "attrType": "expNum"}]}
    ds = json.dumps({"endNode": {}, "nodes": [node]})
    errs = validate_release_readiness({"state": "RELEASE", "dataSchema": ds})
    assert any("NOT_OBJECT" in e for e in errs)


def test_release_readiness_accepts_the_known_good_shape():
    """本轮 LIVE 打通的那份 body（补 holder 4 键后 check=True errors=0）必须判通过。"""
    import json
    from components.udc.microflow_constraints import validate_release_readiness
    path_el = {"id": "X.f", "name": "f", "dataType": "STRING",
               "javaType": "java.lang.String", "type": "OBJECT"}
    holder = {"type": "OBJECT", "dataType": "STRING", "javaType": "java.lang.String",
              "name": "h", "path": [path_el]}
    ds = json.dumps({
        "endNode": {"paramType": "ENTITY_OBJECT",
                    "value": {"type": "SelectParam", "selectParam": {"dtoType": "MASTER_ENTITY"}}},
        "nodes": [{
            "nodeId": "RA1", "actionType": "RETRIEVE_ARRAY",
            "sortParams": [{"sortType": "DESC", "attrType": {
                "id": "X.n", "name": "n", "dataType": "INTEGER",
                "type": "OBJECT", "javaType": "java.lang.Integer"}}]},
            {"nodeId": "DM1", "actionType": "DATA_MAPPING",
             "mappingRule": {"uuid": "u", "type": "ENTITY", "javaType": "java.lang.Object",
                             "name": "_mr", "subobjects": [],
                             "mappingRows": [{"targetField": holder,
                                              "value": {"reference": holder}}]}}]})
    assert validate_release_readiness({"state": "RELEASE", "dataSchema": ds}) == []


def test_release_readiness_catches_missing_holder_own_keys():
    """holder 自身缺 name/dataType/type/javaType 必须被咬住（本轮 LIVE 才暴露的差异）。"""
    import json
    from components.udc.microflow_constraints import validate_release_readiness
    ds = json.dumps({
        "endNode": {},
        "nodes": [{"nodeId": "DM1", "actionType": "DATA_MAPPING",
                   "mappingRule": {"uuid": "u", "type": "ENTITY", "javaType": "j",
                                   "name": "n", "subobjects": [],
                                   "mappingRows": [{"targetField": {"path": []}}]}}]})
    errs = validate_release_readiness({"state": "RELEASE", "dataSchema": ds})
    assert any("holder 必填" in e for e in errs)


# ======================================================================
# 第四十四轮：04004「依赖应用已删除」= appName 未跨接（单变量臂矩阵）
# ======================================================================
def test_r44_input_output_branch_selection_follows_inapp():
    """分支由 inApp 单独决定；**键缺失与显式 false 同分支**（Boolean 包装类型）。"""
    from components.udc.microflow_constraints import input_output_detection_branch
    assert input_output_detection_branch({"inApp": True, "appName": "x"}) == "inapp"
    assert input_output_detection_branch({"inApp": False, "appName": "x"}) == "external"
    assert input_output_detection_branch({"appName": "x"}) == "external"      # 键缺失
    assert input_output_detection_branch({"inApp": None, "appName": "x"}) == "external"
    assert input_output_detection_branch(None) == "absent"


def test_r44_own_appname_without_inapp_is_the_04004_cause():
    """LIVE 真因：appName=本应用 但未声明 inApp ⇒ 当外部应用查依赖表 ⇒ APP_DELETE。"""
    from components.udc.microflow_constraints import validate_input_output_dependency
    ERR = "依赖应用已删除"
    dep = ["bpm", "ctp-user", "organization", "cip-connector"]     # 表内只有**外部**应用
    bad = {"inApp": None, "appName": "datamigration9000000000000000001", "dataType": "BIGINTEGER"}
    problems = validate_input_output_dependency(bad, dep)
    assert len(problems) == 1 and ERR in problems[0]
    bad2 = dict(bad, inApp=False)                                  # 显式 false 同结论（臂 B）
    assert validate_input_output_dependency(bad2, dep)[0] == problems[0]


def test_r44_inapp_true_clears_and_registered_external_passes():
    """对照组：inApp=true 恒清白；inApp=false + 已注册外部应用名 也清白。"""
    from components.udc.microflow_constraints import validate_input_output_dependency
    dep = ["bpm", "ctp-user"]
    assert validate_input_output_dependency({"inApp": True, "appName": "datamigration9000000000000000001"}, dep) == []
    assert validate_input_output_dependency({"inApp": False, "appName": "bpm"}, dep) == []
    # appName 空 + 外部分支：不作为「已修复」放行，但也不与 APP_DELETE 混淆
    msg = validate_input_output_dependency({"inApp": False, "appName": None}, dep)
    assert msg and "appName 为空" in msg[0]


def test_r44_arm_matrix_is_self_consistent():
    """臂矩阵：E1 清零 / B 复现 / C 换码 / D 假干净 / R 可逆，五者不可互相冒充。"""
    from components.udc.microflow_constraints import (
        LIVE_R44_ARMS, R44_FALSE_CLEAN_ARM_IS_DRAFT_MASKED,
        R44_APPNAME_DEP_GATE_IS_INVISIBLE_TO_CHECK_SCHEMA)
    A = LIVE_R44_ARMS
    assert A["E0_orig_missing_inapp_own_appname"]["error_count"] == 1
    assert A["E1_inapp_true"]["error_count"] == 0
    assert A["B_inapp_false_own_appname"]["error_count"] == 1
    assert A["B_inapp_false_own_appname"]["message_contains"] == A["E0_orig_missing_inapp_own_appname"]["message_contains"]
    assert A["C_inapp_false_bpm_appname"]["message_contains"] == "OpenApi标识不匹配"
    assert A["C_inapp_false_bpm_appname"]["message_contains"] != A["E0_orig_missing_inapp_own_appname"]["message_contains"]
    assert A["D_missing_inapp_appname_null"]["false_clean"] is True
    assert A["D_missing_inapp_appname_null"]["db_state"] == 10        # 被压回 DRAFT ⇒ 04003 掩蔽
    assert A["R_restore"]["error_count"] == 1                         # 还原可逆
    # 只有 E1 是「ERROR=0 且 state=20」的干净态；D 的 0 不算
    clean = [k for k, v in A.items() if v["error_count"] == 0 and v.get("db_state") == 20]
    assert clean == ["E1_inapp_true"], clean
    assert R44_FALSE_CLEAN_ARM_IS_DRAFT_MASKED is True
    assert R44_APPNAME_DEP_GATE_IS_INVISIBLE_TO_CHECK_SCHEMA is True


def test_r44_warn_snapshot_moves_with_concurrent_writers():
    """WARN 计数是移动量：并发工作流把对象压回 DRAFT 后会多出一条 04003。"""
    from components.udc.microflow_constraints import LIVE_R44_WARN_SNAPSHOT
    # 锚点已迁到 tools 固定装置
    from tools.core._fixtures.live_targets import (
        LIVE_DETECTION_WARN_COUNT_IS_MOVING_SNAPSHOT,
    )
    assert LIVE_R44_WARN_SNAPSHOT == {"UDC_CE_MICRO_FLOW_04003": 6, "UDC_MICRO_FLOW_04009": 1}
    assert sum(LIVE_R44_WARN_SNAPSHOT.values()) == 7


def test_r44_concurrent_writer_is_recorded_not_silently_ignored():
    """并发写入者的痕迹必须留在仓库里：否则单对象终态会被误读成「我的判据失效」。"""
    from components.udc.microflow_constraints import LIVE_R44_CONCURRENT_WRITER
    rec = LIVE_R44_CONCURRENT_WRITER
    assert rec["object"] == "-1014184770817921434"
    assert "3->0" in rec["effect"] and "20->10" in rec["effect"]
    assert "149955" in rec["effect"] and "123702" in rec["effect"]
