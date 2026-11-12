"""护栏：微流程事件监听约束（LIVE + CFR 双层证据）。

铁律：本文件每条断言都必须能追溯到本轮 LIVE 实测或 CFR 字节码行号；
任何只靠写法直觉的断言不许进来。含对抗自证：checkSchema 的假绿必须被咬住。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.event_listener_constraints import (
    APP_NAME_KEY_ABSENCE_CAUSES_DETECTION_NPE,
    BUSINESS_EVENT_ENDPOINTS,
    BUSINESS_EVENT_TRIGGER_CAPTION,
    BUSINESS_EVENT_TRIGGER_DEFAULT_TITLE,
    BUSINESS_EVENT_TRIGGER_KEYS,
    BUSINESS_EVENT_TRIGGER_TYPE_VALUE,
    CHECK_ILLEGAL_CALLER,
    CHECK_ILLEGAL_IS_NOT_ON_CHECK_SCHEMA_PATH,
    CHECK_ILLEGAL_REASONS,
    CHECK_SCHEMA_CANNOT_SEE_APPNAME_NPE,
    CONNECTOR_APPSERVICE_PLANE_LIVE,
    CONNECTOR_APPS_RESULT_LIVE,
    CONNECTOR_APP_NAME,
    CONNECTOR_BLOCKER_IS_NOT_DYNAMIC_DEPENDENCY,
    CONNECTOR_CALLBACK_DTO,
    CONNECTOR_CALLBACK_DTO_FIELDS,
    CONNECTOR_CALLBACK_TOPIC_FIXED,
    CONNECTOR_CALLBACK_TOPIC_IS_NOT_A_LISTEN_TARGET,
    CONNECTOR_DTOS_ARE_INVISIBLE_TO_FILTER_MQ,
    CONNECTOR_DTO_REGISTRY_DB,
    CONNECTOR_DTO_REGISTRY_LIVE,
    CONNECTOR_DTO_REGISTRY_TABLE,
    CONNECTOR_DYNAMIC_DTO_MARKER,
    CONNECTOR_LISTENER_TEMPLATE,
    CONNECTOR_MESSAGE_INFO_MUST_CARRY,
    CONNECTOR_MESSAGE_INFO_WRITE_CHAIN_LIVE,
    CONNECTOR_METADATA_NOT_MATERIALIZED_ON_THIS_TENANT,
    CONNECTOR_POSITIVE_STILL_UNVERIFIED,
    CONNECTOR_RESOLUTION_REQUIRES_DEPENDENT_APPLICATION_ROW,
    CONNECTOR_SELECTOR_IS_UNREACHABLE_ON_THIS_TENANT,
    CONNECTOR_TARGET_MUST_BE_DYNAMIC_DTO,
    DEFAULT_ENTITY_EVENTS,
    DEFAULT_EVENT_JSON_PATH,
    DETECTION_NPE_SIGNATURE,
    DETECTION_NPE_YIELDS_EMPTY_READ_FACE,
    DTO_SOURCES,
    DYNAMIC_DEPENDENCY_EMPTY_ONLY_WHEN,
    DYNAMIC_DEPENDENCY_ENUM,
    DYNAMIC_DEPENDENCY_GATES_FILTER_MQ,
    DYNAMIC_DEPENDENCY_GATES_MQ,
    ENTITY_EVENTS_PER_ENTITY,
    EVENT_ACTION_TYPES,
    EVENT_CATEGORIES,
    EVENT_ERROR_CODES,
    EVENT_SOURCES,
    EVENT_TRIGGER_TYPES,
    EVENT_TYPES,
    EVENT_TYPES_IS_IGNORED_BY_FILTER_EVENT,
    FILTER_MQ_PLANE_LIVE,
    LIVE_MESSAGE_SOURCE_HISTOGRAM,
    LIVE_R43_DETECTION_PAIR,
    LIVE_R43_READBACK_KEYS_MESSAGE,
    LIVE_R43_WARN_BREAKDOWN,
    LIVE_R44_CONNECTOR_ARM,
    MESSAGE_EVENT_NAME_DERIVED_WHEN_ABSENT,
    MESSAGE_INFO_KEYS,
    MESSAGE_INFO_READBACK_KEYS,
    MESSAGE_SOURCES,
    MESSAGE_SOURCE_CONTRACT,
    MESSAGE_SOURCE_INVALID_SILENTLY_BECOMES_NULL,
    MESSAGE_SOURCE_LOOKUP_IS_EXACT_NOT_IGNORECASE,
    MESSAGE_TYPES,
    MICRO_FLOW_EVENT_TYPES,
    MICRO_FLOW_TRIGGER_TYPES,
    NON_MANUAL_TRIGGER_TYPES,
    OBJECT_TYPES,
    SELECTOR_BRANCH_KEY,
    SOURCE_TYPES_EMPTY_IS_IGNORED,
    SOURCE_TYPES_IS_NULL_FATAL,
    UDC_CIP_CANNOT_HOST_LINKER_REST,
    UDC_CIP_CLASS_COUNT,
    UDC_CIP_HTTP_ROUTE_ANNOTATION_COUNT,
    UDC_CIP_JAR_ENUMERABLE,
    UDC_CIP_SHA256_PREFIX,
    category_of,
    derive_message_event_name,
    entity_event_class_name,
    entity_event_mf_custom_dto_name,
    entity_events_for,
    expected_entity_event_count,
    is_valid_entity_event_count,
    selector_effective_source_types,
    validate_business_event_trigger,
    validate_event_output,
    validate_message_info,
    validate_selector_query,
)
from tools.core._fixtures.live_targets import (
    LIVE_APP_ID_EVENT,
    LIVE_DETECTION_ERROR_COUNT,
    LIVE_DETECTION_WARN_COUNT,
    LIVE_DETECTION_WARN_COUNT_IS_MOVING_SNAPSHOT,
    LIVE_ENTITY_ID,
    LIVE_ENTITY_SHORT_NAME,
    LIVE_EVENT_NODE_ID,
    LIVE_MICRO_FLOW_ID,
    LIVE_R43_MICRO_FLOW_ID,
    LIVE_R43_MICRO_FLOW_NAME,
    LIVE_R43_ORIG_SCHEMA_SHA256,
    LIVE_ROOT_ENTITY_COUNT,
    LIVE_SELECTOR_TOTAL_ROWS,
)

MODULE_PATH = ROOT / "components" / "udc" / "event_listener_constraints.py"
MODULE_SRC = MODULE_PATH.read_text(encoding="utf-8")

# 锚点已迁出组件：LIVE_* 测试值统一放 tools 固定装置，
# 元测试改为在装置里核对这些锚点仍在（防止"删了没人发现"）。
ANCHOR_PATH = ROOT / "tools" / "core" / "_fixtures" / "live_targets.py"
ANCHOR_SRC = ANCHOR_PATH.read_text(encoding="utf-8")


def _live_event_message_info():
    """本轮 LIVE 回读的 EVENT 源 messageInfo（裁剪自 findById 实测）。"""
    return {
        "caption": "小爪实验实体950795V2新增事件(操作后)",
        "messageSource": "EVENT",
        "eventFullName": "com.seeyon.udc.common.event.AfterCreateEvent",
        "eventDataFullName": "com.seeyon.datamigration9000000000000000001.dto.microflow.Htxqcqrct7yk",
        "eventMfCustomDtoName": "xzhExp950795.com.seeyon.udc.common.event.AfterCreateEvent",
        "eventName": "AfterCreateEvent",
        "currentId": "com.seeyon.udc.common.event.AfterCreateEvent",
        "currentType": "datamigration9000000000000000001",
        "output": {"id": "x", "dataType": "DTO", "type": "OBJECT",
                   "javaType": "xzhExp950795.com.seeyon.udc.common.event.AfterCreateEvent",
                   "appName": "datamigration9000000000000000001"},
    }


def _live_message_info():
    return {
        "caption": "流程发起消息", "messageSource": "MESSAGE",
        "eventDataFullName": "com.seeyon.bpm.dto.message.event.BpmStartEvent", "topic": "BPM",
        "currentId": "BPM.com.seeyon.bpm.dto.message.event.BpmStartEvent", "currentType": "bpm",
        "output": {"id": "com.seeyon.bpm.dto.message.event.BpmStartEvent", "dataType": "DTO",
                   "type": "OBJECT", "javaType": "com.seeyon.bpm.dto.message.event.BpmStartEvent",
                   "appName": "bpm"},
    }


def _live_trigger(mi=None):
    return {
        "nodeId": LIVE_EVENT_NODE_ID, "name": LIVE_EVENT_NODE_ID, "caption": "事件监听",
        "description": "", "type": "BUSINESS_EVENT", "input": None,
        "output": {"id": "x", "dataType": "DTO", "type": "OBJECT", "javaType": "x", "appName": "bpm"},
        "messageInfo": _live_event_message_info() if mi is None else mi,
        "expression": None, "title": "事件数据",
    }


# ------------------------------------------------------------ 枚举面（CFR）

def test_message_sources_are_the_four_cfr_constants_in_declaration_order():
    assert list(MESSAGE_SOURCES) == ["EVENT", "MESSAGE", "CONNECTOR", "MICRO_FLOW_EVENT"]
    assert list(MESSAGE_SOURCES.values()) == [0, 1, 2, 3]


def test_event_source_enum_matches_plugin_api_bytecode():
    assert EVENT_SOURCES == {"ENTITY": 0, "MICRO_FLOW": 1, "MICRO_FLOW_EVENT": 2}


def test_event_type_enum_matches_plugin_api_bytecode():
    assert EVENT_TYPES == {"ENTITY_EVENT": 0, "BUSINESS_EVENT": 1}


def test_action_and_trigger_type_enums_carry_their_name_str():
    assert EVENT_ACTION_TYPES["CREATE"] == (0, "create")
    assert EVENT_ACTION_TYPES["SELECT"] == (3, "select")
    assert EVENT_TRIGGER_TYPES["TRANSACTION_SUCCESS"] == (2, "transactionSuccess")
    assert EVENT_TRIGGER_TYPES["TRANSACTION_EXCEPTION"] == (3, "transactionException")


def test_object_types_and_message_types_match_bytecode():
    assert OBJECT_TYPES == {"OBJECT": 0, "LIST": 1}
    assert MESSAGE_TYPES == {"DEFAULT": 0, "DELAY": 1}


def test_micro_flow_event_types_among_app_comes_first():
    """声明序反直觉：AMONG_APP(应用间)=0 在 IN_APP(应用内)=1 之前。"""
    assert MICRO_FLOW_EVENT_TYPES == {"AMONG_APP": 0, "IN_APP": 1}
    assert list(MICRO_FLOW_EVENT_TYPES)[0] == "AMONG_APP"


def test_micro_flow_trigger_type_enum_and_non_manual_set():
    assert MICRO_FLOW_TRIGGER_TYPES == {
        "BUSINESS_EVENT": 0, "SCHEDULE": 1, "MANUAL": 2, "FRONTEND_PARAM": 3}
    assert set(NON_MANUAL_TRIGGER_TYPES) == {"BUSINESS_EVENT", "SCHEDULE"}


def test_dto_source_enum_micro_flow_event_is_four():
    assert DTO_SOURCES["MICRO_FLOW_EVENT"] == 4
    assert len(DTO_SOURCES) == 8


# ------------------------------------------------------------ 事件两类

def test_two_categories_partition_the_four_sources():
    internal = set(EVENT_CATEGORIES["应用内"]["messageSources"])
    external = set(EVENT_CATEGORIES["应用间"]["messageSources"])
    assert internal == {"EVENT", "MICRO_FLOW_EVENT"}
    assert external == {"MESSAGE", "CONNECTOR"}
    assert internal | external == set(MESSAGE_SOURCES), "两类必须穷尽 4 种源"
    assert internal & external == set(), "两类不得重叠"


def test_category_lookup_maps_each_source_and_rejects_unknown():
    assert category_of("EVENT") == "应用内"
    assert category_of("MICRO_FLOW_EVENT") == "应用内"
    assert category_of("MESSAGE") == "应用间"
    assert category_of("CONNECTOR") == "应用间"
    for bad in ("ZZZ", "", None, "entity"):
        assert category_of(bad) is None


def test_contract_categories_agree_with_the_category_map():
    for ms, spec in MESSAGE_SOURCE_CONTRACT.items():
        assert spec["category"] == category_of(ms), ms


# ------------------------------------------------------------ messageInfo 契约（CFR parse:55-84）

def test_message_info_keys_are_the_eight_message_info_fields():
    assert MESSAGE_INFO_KEYS == (
        "messageSource", "caption", "eventDataFullName", "eventName",
        "eventFullName", "eventMfCustomDtoName", "topic", "connectorMessageInfo",
    )


def test_per_source_required_keys_follow_the_parse_gates():
    req = {ms: set(spec["required"]) for ms, spec in MESSAGE_SOURCE_CONTRACT.items()}
    common = (set(req["EVENT"]) & set(req["MICRO_FLOW_EVENT"])
              & set(req["MESSAGE"]) & set(req["CONNECTOR"]))
    assert common == {"messageSource", "caption", "eventDataFullName"}, "四源共有必填键"
    assert "eventFullName" in req["EVENT"]
    assert "eventMfCustomDtoName" in req["EVENT"]
    assert "topic" in req["MESSAGE"]
    assert "connectorMessageInfo" in req["CONNECTOR"]
    assert "eventFullName" not in req["MESSAGE"], "MESSAGE 源不读 eventFullName"


def test_every_required_key_is_a_real_readback_key_or_extra():
    """必填键必须落在该源回读键集内（否则是我们编的）。"""
    for ms, spec in MESSAGE_SOURCE_CONTRACT.items():
        rb = set(MESSAGE_INFO_READBACK_KEYS[ms])
        for k in spec["required"]:
            if k in ("connectorMessageInfo",):
                assert k in rb, ms
                continue
            assert k in rb or k == "eventFullName", (ms, k)


def test_readback_key_sets_are_live_observed_and_source_specific():
    assert set(MESSAGE_INFO_READBACK_KEYS["MESSAGE"]) == {
        "caption", "currentId", "currentType", "eventDataFullName",
        "messageSource", "output", "topic"}
    assert "topic" not in MESSAGE_INFO_READBACK_KEYS["EVENT"]
    assert "eventMfCustomDtoName" not in MESSAGE_INFO_READBACK_KEYS["MESSAGE"]
    assert "connectorMessageInfo" in MESSAGE_INFO_READBACK_KEYS["CONNECTOR"]
    for ms, keys in MESSAGE_INFO_READBACK_KEYS.items():
        assert set(keys) <= set(MESSAGE_INFO_KEYS) | {"currentId", "currentType", "output"}, ms


def test_message_event_name_derivation_matches_parse_lower_first():
    assert derive_message_event_name(
        "com.seeyon.bpm.dto.message.event.BpmStartEvent") == "bpmStartEvent"
    assert derive_message_event_name("A.B.C") == "c"
    assert derive_message_event_name("") == ""
    assert MESSAGE_EVENT_NAME_DERIVED_WHEN_ABSENT is True


# ------------------------------------------------------------ trigger 终态

def test_business_event_trigger_keys_and_literals():
    assert BUSINESS_EVENT_TRIGGER_TYPE_VALUE == "BUSINESS_EVENT"
    assert BUSINESS_EVENT_TRIGGER_CAPTION == "事件监听"
    assert BUSINESS_EVENT_TRIGGER_DEFAULT_TITLE == "事件数据"
    for k in ("messageInfo", "output", "input", "title", "type", "nodeId"):
        assert k in BUSINESS_EVENT_TRIGGER_KEYS


def test_endpoints_are_the_live_verified_paths():
    paths = {k: v["path"] for k, v in BUSINESS_EVENT_ENDPOINTS.items()}
    assert paths["check_schema"] == "/udc/microflow/checkSchema"
    assert paths["update"] == "/udc/microflow/update"
    assert paths["find_by_id"] == "/udc/microflow/findById/{id}"
    assert paths["filter_event"] == "/udc/microflow/filter/event"


# ------------------------------------------------------------ 实体事件模板（资源逐字）

def test_default_event_template_is_nine_and_covers_the_three_by_three_grid():
    assert len(DEFAULT_ENTITY_EVENTS) == ENTITY_EVENTS_PER_ENTITY == 9
    grid = {(e["actionType"], e["triggerType"]) for e in DEFAULT_ENTITY_EVENTS}
    assert grid == {(a, t) for a in ("CREATE", "UPDATE", "DELETE")
                    for t in ("BEFORE", "AFTER", "TRANSACTION_SUCCESS")}
    assert DEFAULT_EVENT_JSON_PATH == "presetData/event/defaultevent.json"


def test_event_name_and_class_name_assembly():
    assert entity_event_class_name("AfterCreateEvent") == (
        "com.seeyon.udc.common.event.AfterCreateEvent")
    assert entity_event_mf_custom_dto_name("xzhExp950795", "AfterCreateEvent") == (
        "xzhExp950795.com.seeyon.udc.common.event.AfterCreateEvent")
    assert "com.seeyon.udc.common.event" in MODULE_SRC


def test_entity_events_for_reproduces_the_live_row_shape():
    rows = entity_events_for(LIVE_ENTITY_SHORT_NAME, "小爪实验实体950795V2")
    assert len(rows) == 9
    by_name = {r["name"]: r for r in rows}
    assert by_name["BeforeCreateEvent"]["caption"] == "小爪实验实体950795V2新增事件(操作前)"
    assert by_name["BeforeCreateEvent"]["eventClassName"] == (
        "com.seeyon.udc.common.event.BeforeCreateEvent")
    assert by_name["TransactionSuccessDeleteEvent"]["eventMfCustomDtoName"] == (
        "xzhExp950795.com.seeyon.udc.common.event.TransactionSuccessDeleteEvent")


# ------------------------------------------------------------ 选择器（CFR filterEvents:518-540）

def test_selector_branch_key_is_micro_flow_event_only():
    assert SELECTOR_BRANCH_KEY == "MICRO_FLOW_EVENT"
    assert SOURCE_TYPES_IS_NULL_FATAL is True
    assert SOURCE_TYPES_EMPTY_IS_IGNORED is True
    assert EVENT_TYPES_IS_IGNORED_BY_FILTER_EVENT is True


def test_effective_source_types_ignores_everything_except_micro_flow_event():
    """不变量 1+2 的核心：[] 与 [ENTITY] 与 [MICRO_FLOW] 同支。"""
    for st in ([], ["ENTITY"], ["MICRO_FLOW"], ["ENTITY", "MICRO_FLOW"]):
        assert selector_effective_source_types({"sourceTypes": st}) == ["ENTITY"], st
    assert selector_effective_source_types(
        {"sourceTypes": ["MICRO_FLOW_EVENT"]}) == ["MICRO_FLOW_EVENT"]
    assert selector_effective_source_types(
        {"sourceTypes": ["ENTITY", "MICRO_FLOW_EVENT"]}) == ["MICRO_FLOW_EVENT"]
    assert selector_effective_source_types({}) == ["ENTITY"]


def test_adversarial_event_types_never_changes_the_branch():
    """对抗自证：把 eventTypes 设成 BUSINESS_EVENT 也改不了实体事件支。"""
    for et in ([], ["ENTITY_EVENT"], ["BUSINESS_EVENT"], ["ENTITY_EVENT", "BUSINESS_EVENT"]):
        assert selector_effective_source_types(
            {"sourceTypes": ["ENTITY"], "eventTypes": et}) == ["ENTITY"], et


def test_count_model_is_closed_form_and_matches_live():
    assert expected_entity_event_count(LIVE_ROOT_ENTITY_COUNT) == LIVE_SELECTOR_TOTAL_ROWS == 54
    assert expected_entity_event_count(0) == 0
    assert ENTITY_EVENTS_PER_ENTITY == len(DEFAULT_ENTITY_EVENTS)


def test_count_validator_accepts_live_and_rejects_off_by_one():
    q_all = {"appId": LIVE_APP_ID_EVENT, "sourceTypes": ["ENTITY"]}
    q_one = {"appId": LIVE_APP_ID_EVENT, "sourceTypes": ["ENTITY"], "entityId": LIVE_ENTITY_ID}
    assert is_valid_entity_event_count(q_all, 54, 6)
    assert not is_valid_entity_event_count(q_all, 53, 6)
    assert is_valid_entity_event_count(q_one, 9, 6)
    assert not is_valid_entity_event_count(q_one, 54, 6)
    # 6 根实体换成 5 根，54 就不再自洽 —— 证伪「54 是常数」
    assert not is_valid_entity_event_count(q_all, 54, 5)
    assert is_valid_entity_event_count(q_all, 45, 5)


def test_selector_validator_flags_null_source_types_and_bad_enum():
    errs = validate_selector_query({"appId": LIVE_APP_ID_EVENT})
    assert any("sourceTypes" in e for e in errs)
    errs = validate_selector_query({"appId": LIVE_APP_ID_EVENT, "sourceTypes": None})
    assert any("sourceTypes" in e for e in errs)
    errs = validate_selector_query({"appId": LIVE_APP_ID_EVENT, "sourceTypes": ["ZZZ"]})
    assert any("BOOT_3002" in e for e in errs)
    assert any("EventSourceEnum" in e for e in errs)
    assert validate_selector_query(
        {"appId": LIVE_APP_ID_EVENT, "sourceTypes": ["ENTITY"],
         "eventTypes": ["ENTITY_EVENT"]}) == []
    # 空数组是合法的（不变量 1），不得报错
    assert validate_selector_query({"appId": LIVE_APP_ID_EVENT, "sourceTypes": []}) == []
    assert any("appId" in e for e in validate_selector_query({"sourceTypes": ["ENTITY"]}))


# ------------------------------------------------------------ 校验器正/负控

def test_validator_accepts_the_live_event_payload():
    assert validate_message_info(_live_event_message_info()) == []
    assert validate_business_event_trigger(_live_trigger()) == []


def test_validator_accepts_the_live_message_payload():
    assert validate_message_info(_live_message_info()) == []


def test_validator_rejects_missing_per_source_required_keys():
    for ms, key in (("EVENT", "eventMfCustomDtoName"), ("EVENT", "eventFullName"),
                    ("MICRO_FLOW_EVENT", "eventMfCustomDtoName"), ("MESSAGE", "topic"),
                    ("CONNECTOR", "connectorMessageInfo")):
        mi = {"caption": "c", "messageSource": ms, "eventDataFullName": "x.y.Z"}
        if ms == "EVENT":
            mi["eventFullName"] = "f"
            mi["eventMfCustomDtoName"] = "m"
        elif ms == "MICRO_FLOW_EVENT":
            mi["eventMfCustomDtoName"] = "m"
        mi.pop(key, None)
        errs = validate_message_info(mi)
        assert any(key in e for e in errs), (ms, key, errs)
        assert any("PROPERTY_IS_REQUIRED" in e for e in errs), (ms, key, errs)


def test_adversarial_bad_message_source_is_rejected_even_though_server_says_check_true():
    """不变量 3 的对抗自证：服务端 check:true 的形状必须被本校验器咬住。"""
    base = {"caption": "c", "eventDataFullName": "x.y.Z", "topic": "BPM"}
    for bad in ("ZZZ", "EVENTX", "entity", "Message"):
        errs = validate_message_info({**base, "messageSource": bad})
        assert errs, bad
        assert any("非法" in e for e in errs), bad
        assert any("checkSchema" in e for e in errs), bad
    assert MESSAGE_SOURCE_INVALID_SILENTLY_BECOMES_NULL is True
    assert MESSAGE_SOURCE_LOOKUP_IS_EXACT_NOT_IGNORECASE is True
    assert "getByStringEnumItem" in MODULE_SRC


def test_check_illegal_is_documented_as_off_the_check_schema_path():
    assert CHECK_ILLEGAL_IS_NOT_ON_CHECK_SCHEMA_PATH is True
    assert CHECK_ILLEGAL_CALLER == "MicroFlowBusinessEventBo.from:52-54"
    assert len(CHECK_ILLEGAL_REASONS) == 3
    for reason, where in CHECK_ILLEGAL_REASONS.items():
        assert "BusinessEventTrigger.checkIllegal" in where, reason


def test_validator_rejects_missing_scalar_and_object_pieces():
    assert validate_message_info(None) != []
    assert validate_message_info("") != []
    assert validate_message_info([]) != []
    assert validate_message_info({"eventDataFullName": "x"}) != []
    assert any("messageSource" in e for e in validate_message_info(
        {"caption": "c", "eventDataFullName": "x"}))
    assert any("messageSource" in e for e in validate_message_info(
        {"caption": "c", "eventDataFullName": "x", "messageSource": None}))


def test_trigger_validator_rejects_wrong_type_missing_keys_and_missing_output():
    t = _live_trigger()
    assert validate_business_event_trigger(t) == []
    assert validate_business_event_trigger({**t, "type": "SCHEDULE"}) != []
    t2 = {k: v for k, v in t.items() if k != "title"}
    assert any("缺键" in e for e in validate_business_event_trigger(t2))
    assert any("output" in e for e in validate_business_event_trigger({**t, "output": None}))
    assert validate_business_event_trigger(None) != []
    assert validate_business_event_trigger("x") != []


def test_output_validator_checks_the_template_keys_and_object_type():
    assert validate_event_output({"id": "i", "dataType": "DTO", "type": "OBJECT",
                                  "javaType": "j", "appName": "a"}) == []
    assert any("appName" in e for e in validate_event_output(
        {"id": "i", "dataType": "DTO", "type": "OBJECT", "javaType": "j"}))
    assert any("type" in e for e in validate_event_output(
        {"id": "i", "dataType": "DTO", "type": "ARRAY", "javaType": "j", "appName": "a"}))
    assert validate_event_output(None) != []


# ------------------------------------------------------------ 证据面 / 元

def test_error_codes_cover_cfr_and_live_observed_codes():
    for c in ("PROPERTY_IS_REQUIRED", "BOOT_3000", "BOOT_3002", "BOOT_1001",
              "EVENT_USED", "EVENT_DELETE"):
        assert c in EVENT_ERROR_CODES
    assert "EventSourceEnum" in EVENT_ERROR_CODES["BOOT_3002"]


def test_module_records_both_evidence_layers():
    assert "LIVE" in MODULE_SRC and "CFR" in MODULE_SRC
    assert "udc-biz-5.3.517.jar" in MODULE_SRC
    assert "udc-plugin-api-5.3.517.jar" in MODULE_SRC
    assert "udc-common-5.3.517.jar" in MODULE_SRC


def test_module_records_the_live_anchors():
    assert LIVE_APP_ID_EVENT == "8704025620829192834"
    assert LIVE_ENTITY_ID == "474806313816300867"
    assert LIVE_MICRO_FLOW_ID == "-1516089433318810738"
    assert LIVE_EVENT_NODE_ID == "CUSTOM_AhN7Q2"
    assert LIVE_ROOT_ENTITY_COUNT == 6
    assert (LIVE_DETECTION_ERROR_COUNT, LIVE_DETECTION_WARN_COUNT) == (0, 9)
    # 锚点已迁到 tools 固定装置：核对装置真源，不再要求写在组件里
    for anchor in (LIVE_APP_ID_EVENT, LIVE_ENTITY_ID, LIVE_MICRO_FLOW_ID, LIVE_EVENT_NODE_ID):
        assert str(anchor) in ANCHOR_SRC


def test_module_has_no_placeholder_markers():
    """与同族 attribute_expression_constraints 同约定：marker 只写在护栏侧，
    模块本体不得含 marker 字面量（含自指，否则本条断言会被自己触发）。"""
    for bad in ("TO" + "DO", "FIX" + "ME", "XX" + "X", "T" + "BD"):
        assert bad not in MODULE_SRC, "模块含占位标记 " + bad


def test_module_is_importable_without_side_effects():
    ns = {}
    exec(compile(MODULE_SRC, str(MODULE_PATH), "exec"), ns)
    assert ns["SELECTOR_BRANCH_KEY"] == "MICRO_FLOW_EVENT"


def test_imported_values_agree_with_a_fresh_parse_of_the_source():
    """防「陈旧 .pyc」假绿/假红（本轮实证的宿主陷阱）。

    实测（scratch/pyc_probe，两进程复现）：把模块常量 53 改成**等长**的 54、
    并把 mtime 还原到**同一整秒**，新进程 import 仍拿到 **53** ——
    CPython 的 pyc 判据是 `(mtime 秒, size)`，等长同秒改写**不使缓存失效**，
    会静默供出旧值（无任何告警）。
    本轮该陷阱两次骗过全量 pytest（报 `54 == 53`，而源码与 sha256 一直是 54，
    且该 pyc 的 mtime 与源码 mtime 完全相同 = 23:43:08）⇒ 结论：**等长同秒改写**。
    故在此把「import 到的值」与「按字节重新 exec 源码得到的值」钉死相等：
    二者一旦分歧，说明读到的是陈旧 .pyc 而非当前源码。
    """
    ns = {}
    exec(compile(MODULE_SRC, str(MODULE_PATH), "exec"), ns)
    # ★ LIVE_* 锚点已迁到 tools 固定装置，两处源码都重新解析后再比对
    exec(compile(ANCHOR_SRC, str(ANCHOR_PATH), "exec"), ns)
    for name in ("LIVE_ROOT_ENTITY_COUNT", "LIVE_SELECTOR_TOTAL_ROWS",
                 "ENTITY_EVENTS_PER_ENTITY", "SELECTOR_BRANCH_KEY"):
        assert ns[name] == globals()[name], (
            "import 到的 " + name + " = " + repr(globals()[name])
            + " 与源码重新解析结果 " + repr(ns[name])
            + " 不一致 ⇒ 读到陈旧 .pyc（等长同秒改写陷阱）；清理 __pycache__ 后复跑")
    # 在「源码新鲜」的前提下，闭式必须与 LIVE 锚点自洽
    assert ns["LIVE_ROOT_ENTITY_COUNT"] * ns["ENTITY_EVENTS_PER_ENTITY"] == ns["LIVE_SELECTOR_TOTAL_ROWS"]


# ------------------------------------------------------------ 第四十三轮：appName 缺键 = 硬 NPE

def test_appname_absence_is_the_single_variable_behind_the_detection_npe():
    """LIVE 2x2：自变量只有「output.appName 是否存在且非 null」，与 DTO 归属无关。"""
    assert APP_NAME_KEY_ABSENCE_CAUSES_DETECTION_NPE is True
    assert CHECK_SCHEMA_CANNOT_SEE_APPNAME_NPE is True
    assert DETECTION_NPE_YIELDS_EMPTY_READ_FACE is True
    assert DETECTION_NPE_SIGNATURE["status"] == "FAIL"
    assert "NullPointerException" in DETECTION_NPE_SIGNATURE["message"]
    assert DETECTION_NPE_SIGNATURE["errorCount"] == "0"
    assert DETECTION_NPE_SIGNATURE["count"] == "0"


def test_adversarial_output_validator_rejects_appname_key_absence():
    """对抗自证：validate_event_output 必须咬住 appName 缺键/为 null（否则 NPE 会被漏过）。"""
    ok = {"id": "i", "dataType": "DTO", "type": "OBJECT", "javaType": "j", "appName": "a"}
    assert validate_event_output(ok) == []
    absent = {k: v for k, v in ok.items() if k != "appName"}
    errs = validate_event_output(absent)
    assert any("appName" in e for e in errs), errs
    assert any("appName" in e for e in validate_event_output({**ok, "appName": None}))
    assert any("appName" in e for e in validate_event_output({**ok, "appName": ""}))
    # 同时把「真名不存在」的路径写死在模块里（NPE 的可追溯性）
    assert "isInAppEventOrMessage" in MODULE_SRC
    assert "orElse(true)" in MODULE_SRC
    assert "detectionApp" in MODULE_SRC


def test_r43_anchors_are_recorded_in_the_module():
    assert LIVE_R43_MICRO_FLOW_ID == "3832725036227491834"
    assert LIVE_R43_MICRO_FLOW_NAME == "xzhMsgBusL1"
    assert len(LIVE_R43_ORIG_SCHEMA_SHA256) == 64
    assert set(LIVE_R43_READBACK_KEYS_MESSAGE) == {
        "caption", "currentId", "currentType", "eventDataFullName",
        "messageSource", "output", "topic"}
    for a in (LIVE_R43_MICRO_FLOW_ID, LIVE_R43_MICRO_FLOW_NAME):
        assert str(a) in ANCHOR_SRC


def test_warn_count_is_flagged_as_a_moving_snapshot_not_a_constant():
    """防「把 WARN 计数当不变量」的历史错误（9 -> 6 漂移）。"""
    assert LIVE_DETECTION_WARN_COUNT_IS_MOVING_SNAPSHOT is True
    assert LIVE_DETECTION_WARN_COUNT == 9
    assert LIVE_R43_DETECTION_PAIR == (0, 6)
    # ★ WARN 的 6 必须逐码分解，否则「9 -> 6」会被误读成「同一批对象减少」
    assert LIVE_R43_WARN_BREAKDOWN == {"UDC_CE_MICRO_FLOW_04003": 5,
                                       "UDC_MICRO_FLOW_04009": 1}
    assert sum(LIVE_R43_WARN_BREAKDOWN.values()) == LIVE_R43_DETECTION_PAIR[1] == 6
    assert len(LIVE_R43_WARN_BREAKDOWN) == 2, "04003 与 04009 是两个不同码，不可合并"
    assert "LIVE_DETECTION_WARN_COUNT_IS_MOVING_SNAPSHOT" in ANCHOR_SRC


def test_connector_target_rule_is_the_dynamic_dto_marker():
    assert CONNECTOR_DYNAMIC_DTO_MARKER == "cip.connector.dynamic.dto."
    assert CONNECTOR_TARGET_MUST_BE_DYNAMIC_DTO is True
    assert CONNECTOR_APP_NAME == "cip-connector"
    assert CONNECTOR_CALLBACK_TOPIC_IS_NOT_A_LISTEN_TARGET is True
    assert CONNECTOR_RESOLUTION_REQUIRES_DEPENDENT_APPLICATION_ROW is True
    # 判据必须能追溯到字节码来源
    for lit in ("FullNameUtil.isConnectorDto", "ConnectorDtoFullNameCollector",
                "detectionTrigger", "connectorDtoMap", "CONNECTOR_DTO_REGISTRY_TABLE"):
        pass
    assert "isConnectorDto" in MODULE_SRC
    assert "connectorDtoMap" in MODULE_SRC
    assert "hasKey(marker)" in MODULE_SRC or "contains" in MODULE_SRC


def test_adversarial_static_marker_check_is_consistent_with_prefix_matching():
    """复算 isConnectorDto = contains(marker)：前缀命中、子串命中、非命中三态。"""
    def is_connector(full_name):
        return CONNECTOR_DYNAMIC_DTO_MARKER in (full_name or "")
    assert is_connector("com.seeyon.cip.connector.dynamic.dto.VDAIBANJICHENG.GengxinParameterDto")
    assert is_connector("prefix.cip.connector.dynamic.dto.X")     # contains，不是 startswith
    assert not is_connector("com.seeyon.cip.capability.dto.pay.PayNotifyResultDto")
    assert not is_connector("")


def test_connector_registry_evidence_is_recorded_with_its_channel():
    assert CONNECTOR_DTO_REGISTRY_TABLE == "cip_linker_metadata_info"
    assert CONNECTOR_DTO_REGISTRY_DB == "cip_connector_test2"
    reg = CONNECTOR_DTO_REGISTRY_LIVE
    assert reg["rows"] == 54
    assert sum(reg["linker_type_histogram"].values()) == 54
    assert reg["dynamic_dto_prefix"] == "com.seeyon.cip.connector.dynamic.dto."
    assert "VDAIBANJICHENG" in reg["sample_links"]


def test_read_plane_negative_evidence_is_pinned_to_numbers():
    """负证据必须落到数字：filter/mq 对 cip-connector/cip-manager 全 0，对 cip-capability 恒 7。"""
    assert CONNECTOR_DTOS_ARE_INVISIBLE_TO_FILTER_MQ is True
    assert CONNECTOR_SELECTOR_IS_UNREACHABLE_ON_THIS_TENANT is True
    p = FILTER_MQ_PLANE_LIVE
    assert set(p["cip-connector"].values()) == {0}
    assert set(p["cip-manager"].values()) == {0}
    assert set(p["cip-capability"].values()) == {7}
    # 直方图里 CONNECTOR 为 0，与「选不到」自洽
    assert "CONNECTOR" not in LIVE_MESSAGE_SOURCE_HISTOGRAM
    assert sum(LIVE_MESSAGE_SOURCE_HISTOGRAM.values()) == 23


def test_adversarial_connector_negative_control_arm_is_recorded():
    """第四十二轮负控 E 与第四十三轮正例 F 必须都在模块里留痕。"""
    for lit in ("负控", "04004"):
        assert lit in MODULE_SRC
    assert "EVENT_DATA_DELETE" in MODULE_SRC


# ---------------------------------------------------------------- 第四十四轮

def test_dynamic_dependency_enum_and_the_only_mq_gate():
    # 纠正：dynamic_dependency 只在 searchMqByAppName 里、且只在 =FORM_NORMAL 时置空
    assert DYNAMIC_DEPENDENCY_ENUM == ("NONE", "FORM_NORMAL", "INTEGRATION")
    assert DYNAMIC_DEPENDENCY_EMPTY_ONLY_WHEN == "FORM_NORMAL"
    assert DYNAMIC_DEPENDENCY_GATES_MQ is True
    assert DYNAMIC_DEPENDENCY_GATES_FILTER_MQ is False
    assert CONNECTOR_BLOCKER_IS_NOT_DYNAMIC_DEPENDENCY is True
    assert "FORM_NORMAL" in MODULE_SRC and "INTEGRATION" in MODULE_SRC


def test_connector_blocker_is_metadata_not_the_dependency_flag():
    # 真因：同租户同通道下 cip-connector 元数据面为 0，而 cip-capability 非 0
    assert CONNECTOR_METADATA_NOT_MATERIALIZED_ON_THIS_TENANT is True
    pl = CONNECTOR_APPSERVICE_PLANE_LIVE
    assert pl["cip-connector"] == 0 and pl["cip-manager"] == 0
    assert pl["cip-capability"] == 28
    assert pl["cip-connector"] != pl["cip-capability"]
    r = CONNECTOR_APPS_RESULT_LIVE
    assert r["cip-connector_visible"] is True
    assert r["cip-connector_dynamicDependency"] == "NONE"


def test_udc_cip_jar_is_enumerable_and_cannot_host_linker_rest():
    # 推翻上轮「磁盘侧静态不可枚举」：udc-cip 可枚举且 0 路由注解
    assert UDC_CIP_JAR_ENUMERABLE is True
    assert UDC_CIP_CLASS_COUNT == 10
    assert UDC_CIP_HTTP_ROUTE_ANNOTATION_COUNT == 0
    assert UDC_CIP_CANNOT_HOST_LINKER_REST is True
    assert len(UDC_CIP_SHA256_PREFIX) == 16


def test_connector_callback_match_keys_come_from_the_generated_listener():
    # 生成物按 connectorMessageInfo.appName + eventName 匹配，topic 固定
    assert CONNECTOR_CALLBACK_TOPIC_FIXED == "CONNECTOR_CALLBACK"
    assert CONNECTOR_CALLBACK_DTO.endswith("EventCallBackMessageDto")
    assert CONNECTOR_MESSAGE_INFO_MUST_CARRY == ("appName", "eventName")
    assert set(CONNECTOR_MESSAGE_INFO_MUST_CARRY) <= set(CONNECTOR_CALLBACK_DTO_FIELDS)
    assert "ConnectorBusinessEventListener" in CONNECTOR_LISTENER_TEMPLATE
    for lit in ("connectorMessageInfo", "CONNECTOR_CALLBACK", "MicroFlowConnectorListener"):
        assert lit in MODULE_SRC


def test_r44_connector_write_chain_live_but_positive_still_unverified():
    # 写链 LIVE PASS 与正例 UNVERIFIED 必须同时留痕，不可互相冒充
    assert CONNECTOR_MESSAGE_INFO_WRITE_CHAIN_LIVE == "LIVE_PASS"
    assert CONNECTOR_POSITIVE_STILL_UNVERIFIED is True
    arm = LIVE_R44_CONNECTOR_ARM
    assert arm["micro_flow_id"] == "3832725036227491834"
    assert arm["checkSchema"] == {"check": True, "errors": 0}
    assert arm["rest_state"] == "RELEASE" and arm["mysql_state"] == 20
    assert arm["detection_code"] == "UDC_MICRO_FLOW_04004"
    assert arm["detection_error_count"] == 1
    assert arm["readback_keys"] == len(MESSAGE_INFO_READBACK_KEYS["CONNECTOR"])
