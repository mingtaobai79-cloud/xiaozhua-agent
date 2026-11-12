"""微流程事件监听（BUSINESS_EVENT 触发）约束 —— 事件两类 + 监听 4 种源写链 LIVE 固化。

证据分层（本轮全部实测，禁止跨层互套）：

LIVE（test2，app=8704025620829192834，实体 474806313816300867，微流程 -1516089433318810738）：
  - POST /udc/microflow/checkSchema + POST /udc/microflow/update -> 落库
  - GET  /udc/microflow/findById/{id}                          -> 回读（messageInfo 逐键比对）
  - POST /udc/microflow/filter/event                            -> 事件选择器读面（含负控）
  - POST /udc/application/do/detection + do/detection-state + search/detection

CFR（本仓权威字节码，版本 5.3.517，逐类注明来源构件）：
  - udc-biz-5.3.517.jar
      microflow/domain/bo/trigger/BusinessEventTrigger.parse:55-84      <- 4 源字段闸门
      microflow/domain/bo/trigger/BusinessEventTrigger.checkIllegal:87-104
      microflow/domain/bo/trigger/MicroFlowBusinessEventBo.from:52-54   <- checkIllegal 唯一上游
      microflow/domain/service/MicroFlowService.filterEvents:518-540    <- 选择器真分支
      microflow/domain/service/MicroFlowService.selectAutoCodeTriggerMicroFlow:542-552
      entity/domain/service/EventService.selectEntityEvent:427-460
      entity/domain/service/EventService.selectMicroFlowEvent:462-483
      entity/domain/service/EventService.selectBusinessEvent:387-425
      entity/domain/service/EventService.selectEntityAndBussinessEvent:514-518
      entity/domain/service/EntityService.selectPrimaryEntityByAppId:949-958
      common/utils/EntityEventLoader.listEntityEvents / afterPropertiesSet
      enums/MessageSourceEnum#getByStringEnumItem
      appservice/EventAppServiceImpl.selectEvents:160-176
      microflow/dto/MicroFlowEventQueryDto extends EventQueryParamDto
      microflow/domain/bo/param/MessageInfo（8 字段，与 parse 写入集逐一对上）
  - udc-plugin-api-5.3.517.jar
      common/enums/{EventSourceEnum,EventTypeEnum,EventActionTypeEnum,EventTriggerTypeEnum,
                    ObjectTypeEnum,MessageTypeEnum,DtoSourceEnum}
      common/dto/EventQueryParamDto（appId/entityId/sourceTypes/eventTypes）
      common/dto/EventDto（写侧 24 字段 + className 派生）
  - udc-common-5.3.517.jar
      common/enums/MicroFlowTriggerTypeEnum（NON_MANUAL_TRIGGER_TYPES）
      common/enums/MicroFlowEventTypeEnum（AMONG_APP 应用间 / IN_APP 应用内）
  - 资源：udc-biz presetData/event/defaultevent.json（9 条实体事件模板，逐字落进本模块）

★ 本轮四条新证的不变量（缺一即误判，均已实测）：
  1. sourceTypes 是 null-致命键，但空数组合法且被忽略：
     filterEvents 首行即 paramDto.getSourceTypes().contains(...) => sourceTypes 缺失(=null) 抛
     BOOT_3000（实测「仅传 entityId」即报）；sourceTypes=[] 不报错、走 else 支、返回全应用根实体事件
     （实测 n=54，与 sourceTypes=["ENTITY"]/["MICRO_FLOW"] 完全同响应）。
     => 拿 sourceTypes 当「过滤开关」会得到假阳；真正的过滤条件是 contains(MICRO_FLOW_EVENT)。
  2. eventTypes 对 /filter/event 完全无效（它只服务另一端点 selectEvents）：
     filterEvents 不读 eventTypes => sourceTypes=["ENTITY"]+eventTypes=["BUSINESS_EVENT"] 仍返回实体事件 54 条。
  3. ★ checkSchema 通过 != 配置正确（本模块最重要的一条）：
     MessageSourceEnum.getByStringEnumItem 用 name().equals()（不是 equalsIgnoreCase）且
     orElse(null)，parse 把 null 静默写进 messageInfo；checkIllegal 只被 MicroFlowBusinessEventBo.from
     调用，不在 checkSchema（MicroFlowParser.readWithInfo）链上 => 实测 messageSource="ZZZ" /
     "EVENTX" 均返回 check:true, errors:0。MESSAGE 携带 connectorMessageInfo（空或非空）同样 check:true。
     => 必须以回读 messageInfo 判成败，不能以 checkSchema 判成败。
  4. 事件选择器条数 = 根实体数 x 9（闭式）：
     selectEntityEvent 无 entityId 时走 selectPrimaryEntityByAppId（parent_entity_id=NULL_ID 且
     category=ENTITY），每实体 9 条来自 presetData/event/defaultevent.json（EntityEventLoader 逐条
     setSourceId/setSource=ENTITY/setAppId + caption=实体caption+模板caption）。
     LIVE 54 = DB 根实体 6 x 9（9 个实体中 6 个 parent_entity_id=0，3 个是子实体）——两路独立对账一致。

事件监听「两类」：应用内（INTERNAL）= ENTITY / MICRO_FLOW_EVENT；应用间（EXTERNAL）= MESSAGE / CONNECTOR。
「4 种源」= messageInfo.messageSource 的 4 个枚举值，各自必填键集不同（见 MESSAGE_SOURCE_CONTRACT）。
"""
from __future__ import annotations

# ---------------------------------------------------------------- 枚举（CFR，逐个注明构件）

# udc-biz com.seeyon.udc.enums.MessageSourceEnum：code 即声明序，message 为中文
MESSAGE_SOURCES: dict = {
    "EVENT": 0, "MESSAGE": 1, "CONNECTOR": 2, "MICRO_FLOW_EVENT": 3,
}
# ★ getByStringEnumItem 用 name().equals() 精确匹配 + orElse(null) => 非法值静默落 null，parse 不报错
MESSAGE_SOURCE_LOOKUP_IS_EXACT_NOT_IGNORECASE: bool = True
MESSAGE_SOURCE_INVALID_SILENTLY_BECOMES_NULL: bool = True

# udc-plugin-api com.seeyon.udc.common.enums.EventSourceEnum（getByName 用 equalsIgnoreCase）
EVENT_SOURCES: dict = {"ENTITY": 0, "MICRO_FLOW": 1, "MICRO_FLOW_EVENT": 2}
# udc-plugin-api EventTypeEnum
EVENT_TYPES: dict = {"ENTITY_EVENT": 0, "BUSINESS_EVENT": 1}
# udc-plugin-api EventActionTypeEnum（nameStr 参与 className 组装语义，非显示名）
EVENT_ACTION_TYPES: dict = {
    "CREATE": (0, "create"), "UPDATE": (1, "update"),
    "DELETE": (2, "delete"), "SELECT": (3, "select"),
}
# udc-plugin-api EventTriggerTypeEnum
EVENT_TRIGGER_TYPES: dict = {
    "BEFORE": (0, "before"), "AFTER": (1, "after"),
    "TRANSACTION_SUCCESS": (2, "transactionSuccess"),
    "TRANSACTION_EXCEPTION": (3, "transactionException"),
}
# udc-plugin-api ObjectTypeEnum（output 的 type 键值域 = 输出数据形态）
OBJECT_TYPES: dict = {"OBJECT": 0, "LIST": 1}
# udc-common MicroFlowEventTypeEnum：★ 声明序 AMONG_APP 在前（应用间=0 / 应用内=1）
MICRO_FLOW_EVENT_TYPES: dict = {"AMONG_APP": 0, "IN_APP": 1}
# udc-common MicroFlowTriggerTypeEnum + NON_MANUAL_TRIGGER_TYPES
MICRO_FLOW_TRIGGER_TYPES: dict = {
    "BUSINESS_EVENT": 0, "SCHEDULE": 1, "MANUAL": 2, "FRONTEND_PARAM": 3,
}
NON_MANUAL_TRIGGER_TYPES: tuple = ("BUSINESS_EVENT", "SCHEDULE")
# udc-plugin-api MessageTypeEnum（EventDto.messageType 默认 DEFAULT）
MESSAGE_TYPES: dict = {"DEFAULT": 0, "DELAY": 1}
# udc-plugin-api DtoSourceEnum（selectMicroFlowEvent 用 MICRO_FLOW_EVENT = 4 查 DTO）
DTO_SOURCES: dict = {
    "ENTITY_BUSINESS_EVENT": 0, "MICRO_FLOW": 1, "ENTITY": 2, "CONNECTOR": 3,
    "MICRO_FLOW_EVENT": 4, "MICRO_FLOW_MESSAGE": 5, "PAGE_VARIABLE": 6, "DYNAMIC_DEPENDENCY": 7,
}

# ---------------------------------------------------------------- 事件两类

# 事件两类（前端弹层两个 tab）-> 内部 4 种 messageSource
EVENT_CATEGORIES: dict = {
    "应用内": {"tab": "INTERNAL", "messageSources": ("EVENT", "MICRO_FLOW_EVENT")},
    "应用间": {"tab": "EXTERNAL", "messageSources": ("MESSAGE", "CONNECTOR")},
}


def category_of(message_source):
    """messageSource -> 事件类别（未知值返回 None，不猜）。"""
    for cat, spec in EVENT_CATEGORIES.items():
        if message_source in spec["messageSources"]:
            return cat
    return None

# ---------------------------------------------------------------- messageInfo 契约（CFR parse:55-84 + LIVE）

# ★ messageInfo 全键 = MessageInfo 的 8 个字段
MESSAGE_INFO_KEYS: tuple = (
    "messageSource", "caption", "eventDataFullName", "eventName",
    "eventFullName", "eventMfCustomDtoName", "topic", "connectorMessageInfo",
)

# 4 种源各自的 parse 闸门（parse 里 getString(...,true) 的键 = 必填；false = 可选）
MESSAGE_SOURCE_CONTRACT: dict = {
    "EVENT": {
        "category": "应用内", "kind": "实体事件",
        "required": ("messageSource", "caption", "eventDataFullName",
                     "eventFullName", "eventMfCustomDtoName"),
        "optional": ("eventName",), "extra": (),
        "cfr": "BusinessEventTrigger.parse:72-74",
    },
    "MICRO_FLOW_EVENT": {
        "category": "应用内", "kind": "微流程事件",
        "required": ("messageSource", "caption", "eventDataFullName",
                     "eventMfCustomDtoName"),
        "optional": ("eventName",), "extra": (),
        "cfr": "BusinessEventTrigger.parse:78-79",
    },
    "MESSAGE": {
        "category": "应用间", "kind": "消息总线",
        "required": ("messageSource", "caption", "eventDataFullName", "topic"),
        "optional": ("eventName",), "extra": (),
        # ★ eventName 缺省时服务端派生：lowerFirst(eventDataFullName 最后一段)
        "cfr": "BusinessEventTrigger.parse:66-71",
    },
    "CONNECTOR": {
        "category": "应用间", "kind": "连接器回调",
        "required": ("messageSource", "caption", "eventDataFullName",
                     "connectorMessageInfo"),
        "optional": ("eventName",), "extra": ("connectorMessageInfo",),
        "cfr": "BusinessEventTrigger.parse:75-77",
    },
}

# 回读键集（LIVE findById 实测；= 客户端写入键，服务端不回填未提供的键）
MESSAGE_INFO_READBACK_KEYS: dict = {
    "EVENT": ("caption", "currentId", "currentType", "eventDataFullName",
              "eventFullName", "eventMfCustomDtoName", "eventName", "messageSource", "output"),
    "MICRO_FLOW_EVENT": ("caption", "currentId", "currentType", "eventDataFullName",
                         "eventMfCustomDtoName", "eventName", "messageSource", "output"),
    "MESSAGE": ("caption", "currentId", "currentType", "eventDataFullName",
                "messageSource", "output", "topic"),
    "CONNECTOR": ("caption", "connectorMessageInfo", "currentId", "currentType",
                  "eventDataFullName", "messageSource", "output", "topic"),
}
# MESSAGE 源特有：eventName 缺省时派生规则（复算用）
MESSAGE_EVENT_NAME_DERIVED_WHEN_ABSENT: bool = True


def derive_message_event_name(event_data_full_name):
    """复算 parse:68-70 的 eventName 派生：lowerFirst(最后一段)。

    'com.seeyon.bpm.dto.message.event.BpmStartEvent' -> 'bpmStartEvent'。
    """
    tail = (event_data_full_name or "").rsplit(".", 1)[-1]
    return tail[:1].lower() + tail[1:]

# ---------------------------------------------------------------- 触发器终态形状（CFR + LIVE）

# BUSINESS_EVENT trigger 终态键（LIVE 回读键集）
BUSINESS_EVENT_TRIGGER_KEYS: tuple = (
    "nodeId", "name", "caption", "description", "type", "input", "output",
    "messageInfo", "expression", "title",
)
BUSINESS_EVENT_TRIGGER_TYPE_VALUE: str = "BUSINESS_EVENT"
BUSINESS_EVENT_TRIGGER_CAPTION: str = "事件监听"
BUSINESS_EVENT_TRIGGER_DEFAULT_TITLE: str = "事件数据"

# 节点保存链（checkSchema -> update 全量回传；LIVE PASS）
BUSINESS_EVENT_ENDPOINTS: dict = {
    "check_schema": {"method": "POST", "path": "/udc/microflow/checkSchema",
                     "gives": "MicroFlowDeserializationResult{check,errors,errorMessage}"},
    "update": {"method": "POST", "path": "/udc/microflow/update",
               "gives": "SingleResponse<Long>"},
    "find_by_id": {"method": "GET", "path": "/udc/microflow/findById/{id}",
                   "gives": "MicroFlowDefinitionDto"},
    "filter_event": {"method": "POST", "path": "/udc/microflow/filter/event",
                     "body": "MicroFlowEventQueryDto extends EventQueryParamDto",
                     "gives": "List<EventQueryResultDto>"},
    "filter_mq": {"method": "POST", "path": "/udc/microflow/filter/mq",
                  "body": "MetaDataQueryDto", "gives": "List<MfMqDto>"},
}

# 选择器读面（CFR filterEvents:518-540）
# 真过滤条件（唯一）：是否包含 MICRO_FLOW_EVENT
SELECTOR_BRANCH_KEY: str = "MICRO_FLOW_EVENT"
SOURCE_TYPES_IS_NULL_FATAL: bool = True            # 不变量 1：null -> BOOT_3000
SOURCE_TYPES_EMPTY_IS_IGNORED: bool = True         # 不变量 1：[] -> 走 else 支
EVENT_TYPES_IS_IGNORED_BY_FILTER_EVENT: bool = True  # 不变量 2

# 实体事件模板（udc-biz presetData/event/defaultevent.json，逐字）
DEFAULT_ENTITY_EVENTS: tuple = (
    {"name": "BeforeCreateEvent", "caption": "新增事件(操作前)",
     "actionType": "CREATE", "triggerType": "BEFORE"},
    {"name": "AfterCreateEvent", "caption": "新增事件(操作后)",
     "actionType": "CREATE", "triggerType": "AFTER"},
    {"name": "TransactionSuccessCreateEvent", "caption": "新增事件(操作成功)",
     "actionType": "CREATE", "triggerType": "TRANSACTION_SUCCESS"},
    {"name": "BeforeUpdateEvent", "caption": "更新事件(操作前)",
     "actionType": "UPDATE", "triggerType": "BEFORE"},
    {"name": "AfterUpdateEvent", "caption": "更新事件(操作后)",
     "actionType": "UPDATE", "triggerType": "AFTER"},
    {"name": "TransactionSuccessUpdateEvent", "caption": "更新事件(操作成功)",
     "actionType": "UPDATE", "triggerType": "TRANSACTION_SUCCESS"},
    {"name": "BeforeDeleteEvent", "caption": "删除事件(操作前)",
     "actionType": "DELETE", "triggerType": "BEFORE"},
    {"name": "AfterDeleteEvent", "caption": "删除事件(操作后)",
     "actionType": "DELETE", "triggerType": "AFTER"},
    {"name": "TransactionSuccessDeleteEvent", "caption": "删除事件(操作成功)",
     "actionType": "DELETE", "triggerType": "TRANSACTION_SUCCESS"},
)
DEFAULT_EVENT_JSON_PATH: str = "presetData/event/defaultevent.json"
ENTITY_EVENTS_PER_ENTITY: int = 9
EVENT_CLASS_PACKAGE: str = "com.seeyon.udc.common.event"


def entity_event_class_name(event_name):
    """eventClassName = com.seeyon.udc.common.event.<事件名>。"""
    return EVENT_CLASS_PACKAGE + "." + event_name


def entity_event_mf_custom_dto_name(entity_short_name, event_name):
    """eventMfCustomDtoName = <实体短名>.<eventClassName>（LIVE 实测）。"""
    return entity_short_name + "." + entity_event_class_name(event_name)


def entity_events_for(entity_short_name, entity_caption):
    """复算 EntityEventLoader.listEntityEvents 的产出（9 条/实体）。"""
    out = []
    for tpl in DEFAULT_ENTITY_EVENTS:
        out.append({
            "name": tpl["name"],
            "caption": entity_caption + tpl["caption"],
            "eventClassName": entity_event_class_name(tpl["name"]),
            "eventMfCustomDtoName": entity_event_mf_custom_dto_name(entity_short_name, tpl["name"]),
        })
    return out

# ---------------------------------------------------------------- checkIllegal（CFR:87-104）

# checkIllegal 返回 true 的三条判据（= 非法），以及它的唯一上游
CHECK_ILLEGAL_REASONS: dict = {
    "messageInfo 为 null": "BusinessEventTrigger.checkIllegal:89-92",
    "messageSource 不在 MessageSourceEnum": "BusinessEventTrigger.checkIllegal:94-97",
    "messageSource=CONNECTOR 且 connectorMessageInfo 为空": "BusinessEventTrigger.checkIllegal:99-101",
}
CHECK_ILLEGAL_CALLER: str = "MicroFlowBusinessEventBo.from:52-54"
# ★ 该闸门不在 checkSchema 链上（不变量 3）
CHECK_ILLEGAL_IS_NOT_ON_CHECK_SCHEMA_PATH: bool = True

# ---------------------------------------------------------------- 错误码（CFR / LIVE）

EVENT_ERROR_CODES: dict = {
    "PROPERTY_IS_REQUIRED": "必填参数未配置，请点击该节点参数设置（parse 的 getString/getObject required=true）",
    "BOOT_3000": "filter/event 的 sourceTypes 为 null（filterEvents 首行 NPE 前置校验）",
    "BOOT_3002": "sourceTypes 含非法枚举值：No enum constant com.seeyon.udc.common.enums.EventSourceEnum.<X>",
    "BOOT_1001": "selectEvents 入参为 null（EventAppServiceImpl:161-163）",
    "UDC_EVENT_0004": "Duplicate message identification（udc_event 同 eventData 重复）",
    "UDC_MICROFLOW_0001": "checkMicroFlowNameIsExists",
    "UDC_MICROFLOW_0002": "checkMicroFlowCaptionIsExists",
    "EVENT_USED": "订阅的业务事件已被其他微流程使用（filterEvents 用 usedEventDataNameSet 过滤候选）",
    "EVENT_DELETE": "订阅的业务事件已被删除（BusinessEventActivity 检测项，属性键 selectEvent/selectMq）",
}

# ---------------------------------------------------------------- 校验器

_BASE_REQUIRED: tuple = ("messageSource", "caption", "eventDataFullName")


def validate_message_info(mi, *, strict_source=True):
    """校验 trigger.messageInfo（空=通过）。

    strict_source=True（默认）：messageSource 必须是 4 个合法枚举值之一。
    ★ 为什么默认严格：parse 对非法 messageSource 静默落 null 且 checkSchema 仍 PASS
      （不变量 3），服务端不会替你拦 => 校验器必须拦。
    """
    errs = []
    if mi in (None, ""):
        return ["messageInfo 缺失 —— trigger 无法解析（LIVE: PROPERTY_IS_REQUIRED @ ...messageInfo）"]
    if not isinstance(mi, dict):
        return ["messageInfo 须为对象，实为 " + type(mi).__name__]
    ms = mi.get("messageSource")
    if not ms:
        errs.append("messageInfo.messageSource 缺失（LIVE: PROPERTY_IS_REQUIRED @ ...messageSource）")
        return errs
    if strict_source and ms not in MESSAGE_SOURCES:
        errs.append("messageInfo.messageSource='" + str(ms) + "' 非法 —— 合法值 "
                    + str(sorted(MESSAGE_SOURCES))
                    + "；★ 服务端不会报错（getByStringEnumItem 落 null 且 checkSchema 仍 check:true）")
        return errs
    spec = MESSAGE_SOURCE_CONTRACT.get(ms)
    if spec is None:
        return errs
    for k in spec["required"]:
        if k == "messageSource":
            continue
        v = mi.get(k)
        bad = v is None or v == ""
        if k == "connectorMessageInfo" and not v:
            bad = True
        if bad:
            errs.append("messageSource=" + ms + " 时 messageInfo." + k + " 必填（"
                        + spec["cfr"] + "）—— 空值会得 PROPERTY_IS_REQUIRED @ ..." + k)
    return errs


def validate_event_output(out):
    """校验 trigger.output（事件数据 DTO 输出）；空=通过。"""
    errs = []
    if not isinstance(out, dict):
        return ["trigger.output 须为对象，实为 " + type(out).__name__]
    for k in ("id", "dataType", "type", "javaType", "appName"):
        if not out.get(k):
            errs.append("trigger.output." + k + " 缺失（BUSINESS_EVENT.output 模板必带键）")
    t = out.get("type")
    if t and t not in OBJECT_TYPES:
        errs.append("trigger.output.type='" + str(t) + "' 非法 —— 合法值 " + str(sorted(OBJECT_TYPES)))
    return errs


def validate_business_event_trigger(trigger):
    """校验 BUSINESS_EVENT trigger 整体（空=通过）。"""
    errs = []
    if trigger in (None, ""):
        return ["trigger 缺失"]
    if not isinstance(trigger, dict):
        return ["trigger 须为对象，实为 " + type(trigger).__name__]
    t = trigger.get("type")
    if t != BUSINESS_EVENT_TRIGGER_TYPE_VALUE:
        errs.append("trigger.type 须为 '" + BUSINESS_EVENT_TRIGGER_TYPE_VALUE + "'，实为 '" + str(t) + "'")
    missing = [k for k in BUSINESS_EVENT_TRIGGER_KEYS if k not in trigger]
    if missing:
        errs.append("trigger 缺键 " + str(missing) + "（LIVE 回读键集 = "
                    + str(list(BUSINESS_EVENT_TRIGGER_KEYS)) + "）")
    errs.extend(validate_message_info(trigger.get("messageInfo")))
    out = trigger.get("output")
    if out in (None, ""):
        errs.append("trigger.output 缺失 —— 节点出参数据（BUSINESS_EVENT 必带事件数据 DTO）")
    else:
        errs.extend(validate_event_output(out))
    return errs


def validate_selector_query(body):
    """校验 /microflow/filter/event 入参（空=通过）；含两条本轮新证的反直觉规则。"""
    errs = []
    if not isinstance(body, dict):
        return ["filter/event 入参须为对象，实为 " + type(body).__name__]
    if body.get("appId") in (None, "", 0):
        errs.append("appId 必填（selectEntityEvent 无 appId 直接返回空；filterEvents 侧亦无兜底）")
    if "sourceTypes" not in body or body.get("sourceTypes") is None:
        errs.append("sourceTypes 必填：null 会让 filterEvents 首行 NPE（LIVE: BOOT_3000）")
    else:
        for s in body["sourceTypes"]:
            if s not in EVENT_SOURCES:
                errs.append("sourceTypes 含非法值 '" + str(s) + "'（LIVE: BOOT_3002 No enum constant "
                            "EventSourceEnum." + str(s) + "）；合法值 " + str(sorted(EVENT_SOURCES)))
    return errs


def selector_effective_source_types(body):
    """复算 filterEvents 的有效分支（而非回显入参）。

    ★ 不变量 1+2：只有 MICRO_FLOW_EVENT 在 sourceTypes 里才切换分支；
      否则一律实体事件支（空数组亦然）。eventTypes 不参与。
    """
    st = (body or {}).get("sourceTypes") or []
    if SELECTOR_BRANCH_KEY in st:
        return ["MICRO_FLOW_EVENT"]
    return ["ENTITY"]


def expected_entity_event_count(root_entity_count):
    """不变量 4：无 entityId 时的条数闭式 = 根实体数 x 9。"""
    return root_entity_count * ENTITY_EVENTS_PER_ENTITY


def is_valid_entity_event_count(body, n, root_entity_count):
    """给定量根实体数，判 filter/event 返回条数是否自洽（负控用）。"""
    eff = selector_effective_source_types(body)
    if eff == ["MICRO_FLOW_EVENT"]:
        return n >= 0
    if (body or {}).get("entityId") not in (None, "", 0):
        return n == ENTITY_EVENTS_PER_ENTITY
    return n == expected_entity_event_count(root_entity_count)


# ---------------------------------------------------------------- ★ 第四十三轮：appName 缺键 = 硬 NPE（LIVE 4 臂 2x2）

# 判据链（CFR udc-biz 5.3.517，逐行）：
#   CheckUtils.detectionTrigger:1388  boolean inApp = isInAppEventOrMessage(trigger, applicationDto)
#   CheckUtils.isInAppEventOrMessage:1496-1502
#       messageSource=EVENT -> true
#       else -> Optional.ofNullable(trigger.getOutput()).map(getAppName)
#                    .map(i -> applicationDto.getName().equals(i)).orElse(true)
#       ★ 返回值三元：appName 命中本应用 -> true；非本应用 -> false 且**不短路**；
#         appName 键缺失/null -> orElse(true) -> 判为 inApp = true
#   CheckUtils.detectionTrigger:1389-1422（MESSAGE 且 inApp）-> 走 dtoMap 支（GLOBAL 下查 dtoMap）
#   CheckUtils.detectionTrigger:1461-1471 -> **无条件**读 output appName 之外的三键后
#       variableBo.setName(output.getJavaType()...) 等；上行
#   CheckUtils.detectionTrigger:1412（MESSAGE 且 !inApp）-> detectionApp(refAppName = output.getAppName(), ...)
#       -> CheckUtils.detectionApp:543-544 appNameSet.contains(null)
#       -> HashSet.contains(null) 本应返回 false，但 LIVE 实测为 **NPE**（见下）
# ⇒ 单变量 2x2 实测（每臂 REST state + MySQL state=20 双面确认）：
#   | output.appName     | 1) 存在=非本应用 | 2) 存在=本应用 | 3) =null | 4) 键缺失 |
#   | MESSAGE + 外部DTO  | SUCCESS/无04004  | SUCCESS/无04004 | **FAIL/NPE** | **FAIL/NPE** |
#   | MESSAGE + 本应用DTO| SUCCESS          | SUCCESS        |     —       | **FAIL/NPE** |
#   自变量只有「output.appName 是否存在且非 null」：外部 DTO 与本应用 DTO 同结论
#   ⇒ 唯一复现条件 = appName 键缺失或为 null（与 DTO 归属无关）。
APP_NAME_KEY_ABSENCE_CAUSES_DETECTION_NPE: bool = True
# detection 整轮中止的特征返回（LIVE 原文）
DETECTION_NPE_SIGNATURE: dict = {
    "status": "FAIL",
    "message": "System Error[java.lang.NullPointerException]",
    "count": "0", "errorCount": "0", "seriouCount": "0", "warnCount": "0",
}
# ★ 这一条与「不变量 3（checkSchema 假绿）」并列，是最强的「绿 != 对」实例：
#   checkSchema 对上述 4 臂**全部**返回 {"check": true, "errors": 0}，
#   唯一能分辨的观测面是 RELEASE 后的 detection-state.status。
CHECK_SCHEMA_CANNOT_SEE_APPNAME_NPE: bool = True
# ★ 附带的观测面陷阱：NPE 中止时 search/detection 返回 **0 条**（不是「该对象无问题」，
#   而是整轮无结果）；READ 0 条 + state=FAIL 必须判为「中断」而非「干净」。
DETECTION_NPE_YIELDS_EMPTY_READ_FACE: bool = True

# LIVE 锚点（第四十三轮，对象 = 小爪消息总线监听）
LIVE_R43_READBACK_KEYS_MESSAGE: tuple = (
    "caption", "currentId", "currentType", "eventDataFullName",
    "messageSource", "output", "topic",
)

# ---------------------------------------------------------------- ★ CONNECTOR 源：合法目标 = 连接器动态 DTO（CFR + 存储面 LIVE）

# CFR 判据（udc-biz 5.3.517）
#   MicroFlowUtil.CONNECTOR_DYNAMIC_DTO_MARKER = "cip.connector.dynamic.dto."
#   FullNameUtil.isConnectorDto:320 = fullName.contains(marker)
#   CheckUtils.detectionTrigger:1452-1459（CONNECTOR 支）：
#       if (!context.isRealGlobalDetection()) return;
#       notExist = output.javaType 非空 且 !context.getConnectorDtoMap().containsKey(javaType)
#       notExist -> error(..., "messageInfo", EVENT_DATA_DELETE)
#   ConnectorDtoFullNameCollector.extractDtoFullNameByTrigger:98
#       只把 FullNameUtil.isConnectorDto(javaType) 为真的 output 收进 connectorDtoMap
#   MicroFlowDetectionMetadataAware.putDtoMetadata:125-137
#       connectorDtoMap 来自 search.appName = **depApp.getDepAppName()**（依赖应用名）
#       ⇒ 与 udcAppDtoMap 走**两条不同元数据通道**
CONNECTOR_DYNAMIC_DTO_MARKER: str = "cip.connector.dynamic.dto."
CONNECTOR_TARGET_MUST_BE_DYNAMIC_DTO: bool = True
CONNECTOR_APP_NAME: str = "cip-connector"
# ★ cap 声明 ≠ 可解析：连接器动态 DTO 只在 udc_dependent_application 有
#   dep_app_name='cip-connector' 记录时会进 depAppMap，否则 collector 收得到、
#   metadataAware 解析不到，仍然 notExist -> 04004 / propertyKey=messageInfo。
CONNECTOR_RESOLUTION_REQUIRES_DEPENDENT_APPLICATION_ROW: bool = True

# 读面负证据（LIVE，test2 本租户全量）：**/microflow/filter/mq 永远取不到连接器动态 DTO**
CONNECTOR_DTOS_ARE_INVISIBLE_TO_FILTER_MQ: bool = True
FILTER_MQ_PLANE_LIVE: dict = {
    "cip-connector": {"8704025620829192834": 0, "2378987216360786643": 0,
                      "3289082814923688017": 0, "1656355078954763084": 0},
    "cip-manager": {"8704025620829192834": 0, "2378987216360786643": 0,
                    "3289082814923688017": 0, "1656355078954763084": 0},
    "cip-capability": {"8704025620829192834": 7, "2378987216360786643": 7,
                       "3289082814923688017": 7, "1656355078954763084": 7},
}
# cip-capability 那 7 条 topic=CONNECTOR_CALLBACK 是 connector **方法参数** DTO
# （cip.capability.dto.*），不是合法监听目标 —— 第四十二轮负控 E 已实测报 04004。
CONNECTOR_CALLBACK_TOPIC_IS_NOT_A_LISTEN_TARGET: bool = True
# ★ 合法目标的真身只在连接器主数据里（MySQL，另一条通道：cip_linker_metadata_info）
CONNECTOR_DTO_REGISTRY_TABLE: str = "cip_linker_metadata_info"
CONNECTOR_DTO_REGISTRY_DB: str = "cip_connector_test2"
CONNECTOR_DTO_REGISTRY_LIVE: dict = {
    "rows": 54, "linker_type_histogram": {"0": 33, "2": 5, "3": 2, "4": 1, "5": 13},
    "dynamic_dto_prefix": "com.seeyon.cip.connector.dynamic.dto.",
    "sample_links": {"VDAIBANJICHENG": "V5待办集成", "ZHJHZZTB": "客户方_组织集成",
                     "CESHIDANDIANDENGLU": "测试单点登录", "JICHENGCESHI": "集成测试",
                     "CESHIYINGYONG": "测试应用", "FASONGXIAOXI": "发送消息"},
}
# ★ 读取通道错配（诚实边界）：前端 EXTERNAL 弹层走 filter/mq，而该端点在 test2
#   对 cip-connector/cip-manager 恒返回 0 条 ⇒ 平台面本身取不到合法 CONNECTOR 目标。
#   已存在的 CONNECTOR 监听配置在 500 条微流程的 messageSource 直方图里 **0 条**
#   （EVENT 12 / MESSAGE 8 / MICRO_FLOW_EVENT 3），与之一致。
CONNECTOR_SELECTOR_IS_UNREACHABLE_ON_THIS_TENANT: bool = True
LIVE_MESSAGE_SOURCE_HISTOGRAM: dict = {"EVENT": 12, "MESSAGE": 8, "MICRO_FLOW_EVENT": 3}

# ---------------------------------------------------------------- LIVE 证据锚点（可复核）

# ★ 诚实标注：WARN 计数是**移动量**（= 当时处于草稿态的对象数），不是常量。
#   9 是记录该锚点那一轮的实测快照；第四十三轮实测同一应用为 6。
#   第四十三轮的 6 条构成必须逐条记录，否则会被误读成「同一批对象少了」：
#     5 x UDC_CE_MICRO_FLOW_04003（标品事件监听 / 标品服务定义 / 标准微流程-真数据全节点 /
#       标准微流程-全节点流转(最终) / 消息总线监听）+ 1 x UDC_MICRO_FLOW_04009（页面规则-全前端节点）
#   ⇒ 与历史快照的 9 **不是同一批对象**，只可比较「计数是否自洽」，不可比较「对象是否减少」。
#   引用它做「判据是否成立」的断言时，必须重新实测，不得把它当不变量。
LIVE_R43_DETECTION_PAIR: tuple = (0, 6)
LIVE_R43_WARN_BREAKDOWN: dict = {"UDC_CE_MICRO_FLOW_04003": 5, "UDC_MICRO_FLOW_04009": 1}


# ================================================================ 第四十四轮
# ★ 纠正第四十三轮的机制归属：CONNECTOR 阻塞**不是** dynamic_dependency（红鲱鱼）。
#
# CFR（udc-biz 5.3.517，docs/audit/artifacts/scratch-migrated/cfr-r31b）：
#   DynamicDependencyTypeEnum = { NONE, FORM_NORMAL, INTEGRATION }
#     （boot-starter-extmetadata 常量池逐字；@EnumAttribute 三态）
#   唯一读 dynamic_dependency 的 MQ 通道 = MicroFlowMetaDataQueryService:2074
#     Optional.ofNullable(depApplication).map(getDynamicDependency)
#       .filter(FORM_NORMAL::equals).isPresent() -> return emptyList()
#     => 只有 FORM_NORMAL 会让结果置空；NONE / INTEGRATION / 行缺失都不置空。
#   filterSystemMqInfo:1130-1165（= POST /udc/microflow/filter/mq 的实现，
#     MicroFlowController.javap L1872 value=[/filter/mq]）
#     完全不读 dynamic_dependency：只按 appName 走两条元数据通道
#     （本应用 -> queryDesign；外部 -> queryIntegration）。
DYNAMIC_DEPENDENCY_ENUM: tuple = ("NONE", "FORM_NORMAL", "INTEGRATION")
DYNAMIC_DEPENDENCY_EMPTY_ONLY_WHEN: str = "FORM_NORMAL"
DYNAMIC_DEPENDENCY_GATES_MQ: bool = True
DYNAMIC_DEPENDENCY_GATES_FILTER_MQ: bool = False   # ★ 纠正：/filter/mq 不读它
CONNECTOR_BLOCKER_IS_NOT_DYNAMIC_DEPENDENCY: bool = True

# ★ 真因：本租户连接器动态元数据未注册（DTO + appService 都不在 UDC 元数据面）。
#   LIVE 对照（app=8704025620829192834, tenant=-8112660841495312922，与连接器主数据同租户）：
#     POST /udc/microflow/search/apps            -> 30 行，cip-connector 在列，dynamicDependency="NONE"
#     POST /udc/microflow/search/appService-by-appName {cip-connector}  -> 0 条
#     POST /udc/microflow/search/appService-by-appName {cip-capability} -> 28 条
#     POST /udc/microflow/filter/mq {cip-connector}  -> 0 条
#     POST /udc/microflow/filter/mq {cip-capability} -> 7 条
#   => 同租户、同通道、同次调用：cip-capability 有元数据、cip-connector 无。
#   => 阻塞 = 连接器主数据(cip_linker_metadata_info 54 行)未物化进 UDC 元数据面，
#      不是判据缺失、不是 dynamic_dependency、也不是 REST 入口找不到。
CONNECTOR_METADATA_NOT_MATERIALIZED_ON_THIS_TENANT: bool = True
CONNECTOR_APPSERVICE_PLANE_LIVE: dict = {
    "cip-connector": 0, "cip-manager": 0, "cip-capability": 28,
}
CONNECTOR_APPS_RESULT_LIVE: dict = {
    "row_total": 30, "cip-connector_visible": True,
    "cip-connector_dynamicDependency": "NONE",
}

# ★ 新证据：udc-cip-5.3.517.jar 可枚举（推翻上轮磁盘侧静态不可枚举的结论）。
#   位置 = scratch 缓存 deployed-extra / djars，
#   sha256 前缀 7757e0346e89e611，19149 B，与 DEPLOYED-LIB-INVENTORY 的
#   udc_missing_locally 声明冲突（该 inventory 只扫 <MAVEN_REPO>）。
#   内容 = 10 个 .class，包 com.seeyon.udc.cip.{task,constants,transport,transport.dto,util}，
#   metadata/starter_info.json type="1"（plugin 模块），pom parent=udc-plugins。
#   逐类常量池：0 个带 bind/annotation、0 个带 javax/ws/rs/Path、
#   0 个带 @WebServlet|@WebFilter，0 个 Controller 命名类
#   => 该 jar 不可能承载 Linker 的 REST 路由；上轮候选宿主假设已被证伪（强负面）。
UDC_CIP_JAR_ENUMERABLE: bool = True
UDC_CIP_SHA256_PREFIX: str = "7757e0346e89e611"
UDC_CIP_CLASS_COUNT: int = 10
UDC_CIP_HTTP_ROUTE_ANNOTATION_COUNT: int = 0
UDC_CIP_CANNOT_HOST_LINKER_REST: bool = True

# ★ 新证据：CONNECTOR 监听器的生成代码决定运行期匹配键。
#   udc-biz-5.3.517.jar :: autocode/JAVA/2.9/templates/microflow/event/
#                          ConnectorBusinessEventListener.java.ftl
#   模板类 com.seeyon.udc.autocode.template.ConnectorBusinessEventTemplate
#     -> 产物 domain/event/listener/microflow/MicroFlowConnectorListener.java
#   生成物注解固定：@MessageListener(topic = "CONNECTOR_CALLBACK")
#     （与 cip-capability 那 7 条 topic=CONNECTOR_CALLBACK 一致）
#   入参：com.seeyon.cip.connector.dto.execute.EventCallBackMessageDto
#   匹配： if ("${connectorMessageInfo.appName}".equals(appName)
#            && "${connectorMessageInfo.eventName}".equals(eventName))
#   => connectorMessageInfo 必须带 appName + eventName 两键才可能命中回调。
#   EventCallBackMessageDto 字段（cip-connector-facade-5.3.321 常量池）：
#     appId, appName, eventId, eventName, fullName, data, send
CONNECTOR_CALLBACK_TOPIC_FIXED: str = "CONNECTOR_CALLBACK"
CONNECTOR_CALLBACK_DTO: str = "com.seeyon.cip.connector.dto.execute.EventCallBackMessageDto"
CONNECTOR_CALLBACK_DTO_FIELDS: tuple = ("appId", "appName", "eventId", "eventName",
                                        "fullName", "data", "send")
CONNECTOR_MESSAGE_INFO_MUST_CARRY: tuple = ("appName", "eventName")
CONNECTOR_LISTENER_TEMPLATE: str = ("autocode/JAVA/2.9/templates/microflow/event/"
                                    "ConnectorBusinessEventListener.java.ftl")

# ★ 第四十四轮 LIVE 收获：CONNECTOR 的 messageInfo 写链是通的（首次 RELEASE + MySQL 双面）。
#   对象 = 微流程 3832725036227491834，臂 F（docs/audit/artifacts/scratch-migrated/root/r43_arms.json 复核：
#   messageSource=CONNECTOR + 真实 cip.connector.dynamic.dto.* + appName=cip-connector
#   + topic=CONNECTOR_CALLBACK）：
#     checkSchema/update -> {"check":true,"errors":0}；REST state=RELEASE；MySQL state=20；
#     回读 messageInfo 8 键 = 本模块 CONNECTOR 读回键集，逐键一致。
#   但检测面仍报 04004（EVENT_DATA_DELETE，errorCount=1）
#     => 阻塞在元数据解析面（appService/DTO 未注册），不在写入面。
#   状态：messageInfo 写链 LIVE PASS；CONNECTOR 正例仍 UNVERIFIED（不得冒充）。
CONNECTOR_MESSAGE_INFO_WRITE_CHAIN_LIVE: str = "LIVE_PASS"
CONNECTOR_POSITIVE_STILL_UNVERIFIED: bool = True
LIVE_R44_CONNECTOR_ARM: dict = {
    "micro_flow_id": "3832725036227491834", "readback_keys": 8,
    "checkSchema": {"check": True, "errors": 0},
    "rest_state": "RELEASE", "mysql_state": 20,
    "detection_code": "UDC_MICRO_FLOW_04004", "detection_error_count": 1,
}
