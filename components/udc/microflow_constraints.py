"""UDC 微流程节点约束模型（后端权威，反编译 udc-biz 5.3.517 提取）。

证据：
- ActivityNodeTypeEnum / MicroFlowNodeTypeEnum / DataMappingRow$DataMappingMode /
  DataMappingActivity$DataMappingTargetTypeEnum / RetrieveEntityArrayActivity$FetchType /
  ListOperationTypeEnum / MapOperationTypeEnum / MappingTypeEnum / AttrValueTypeEnum /
  NullHandlingEnum / CronTypeEnum / RotationTypeEnum / MicroFlowDtoTypeEnum /
  MicroFlowParseErrorEnum 等（com.seeyon.udc.enums.microflow.* + domain.bo.flow.*）
- 每节点 parseActivityNode() 里 NodeUtils.getXxx("f", node, required) 的 required 标志

生成前置校验：planner/生成器应据此判必填与值域，避免"形状对、约束错"。
"""
from __future__ import annotations

# ---- 活动节点 actionType 全值域（ActivityNodeTypeEnum，strCode）----
ACTIVITY_NODE_TYPES: dict[str, int] = {
    "CONNECTOR": 0, "CREATE_VARIABLE": 1, "CHANGE_VARIABLE": 2, "CREATE_LIST": 3, "CHANGE_LIST": 4,
    "PUBLISH_BUSINESS_EVENT": 5, "ATTRIBUTE_REQUIRED": 6, "ASSIGN_VALUE": 7, "SHOW_MESSAGE": 8,
    "ATTRIBUTE_UNIQUE": 9, "RETRIEVE": 10, "RETRIEVE_ARRAY": 11, "CHANGE_ENTITY": 12,
    "CREATE_ENTITY": 13, "DELETE_ENTITY": 14, "LIST_OPERATION": 15, "SUB_MICROFLOW": 16,
    "CALL_MICRO_FLOW": 17, "CALL_APP_SERVICE": 18, "CALL_DATA_FLOW": 19, "DEFAULT_VALUE": 21,
    "CONVERT_DATA": 40, "CREATE_BATCH_ENTITY": 41, "CHANGE_BATCH_ENTITY": 42, "CREATE_MAP": 43,
    "MAP_OPERATION": 44, "DATA_MAPPING": 45, "CALL_DATA_FLOW_FRONT": 46, "EXTEND_ACTION": 47,
    "SET_DATASOURCE": 48,
}

# ---- 控制节点 type（MicroFlowNodeTypeEnum）----
CONTROL_NODE_TYPES: dict[str, int] = {
    "CONDITION": 0, "FOR_EACH": 1, "BRANCH": 2, "CUSTOM_ERROR": 3, "END": 4, "ACTIVITY": 5,
    "FOR": 6, "BREAK": 7,
}

# ---- 节点必填字段（★权威：全库真实节点反推，不是反编译推断）----
# 取法：state=20 的 3000 条微流程 → 每个 actionType 统计字段**出现率**，
#       只把 100% 出现的算必填（N>=30 才采信）。
#
# ★ 旧表大面积是错的（阳性对照实测）：
#     CREATE_VARIABLE  1782/1782 = 100% 误杀（旧表写 metaDataType/otherType，
#                      真实落库是 dataType/paramType/title）
#     CHANGE_ENTITY     374/ 374 = 100%（旧表写 mappingType，真实是 selectParam/title）
#     LIST_OPERATION   1017/1095 =  93%（旧表写 indexValue，真实是 selectParam/
#                      operationType/title）
#     SUB_MICROFLOW     327/ 640 =  51%（旧表写 mappingType，真实是 mfService）
#     CONVERT_DATA       96/ 215 =  45%（旧表写 regex，真实是 convertType/
#                      selectParam/title）
#     RETRIEVE_ARRAY    122/ 523 =  23%
#   根因：旧表按「反编译 required=true 的参数名」写，与落库字段名不是同一套。
#
# ★★ 有一批字段是**选择器回填的元数据**（用户/生成器不能自己编，见
#    SELECTOR_FILLED_FIELDS）：RETRIEVE/RETRIEVE_ARRAY 的 app/structure/title/
#    selectType/scope/methodLegal —— 必须先走实体选择器拿到 app+structure。
# ★★ 权威来源（2026-10-24 更正）：**前端画布的 requiredFields 表**
#   证据：在页面打开流程时 console 打印
#     "CHANGE_LIST_fh6ng3 的所有必填属性=> ['selectParam','action','dataSource']"
#     "值为空的必填属性=> dataSource null {...}"
#   前端这张表才是保存/画布渲染的闸门；按落库出现率反推会漏掉「必填但常为空」的字段。
#
# ★ 已证伪的旧结论（都按出现率推的，全部错）：
#     CHANGE_LIST 缺 dataSource  → 页面一打开就告警
#     CREATE_ENTITY 缺 value     → 同上
#     MAP_OPERATION 缺 selectMap/entries
#     FOR 缺 targetName（反而 operator 前端不要）
#     CUSTOM_ERROR 要求 type/errorType（前端只要 error）
#     BRANCH 要求 conditions / CONDITION 要求 nodes（前端都不要）
#     RETRIEVE 要求 8 个（前端只要 app/structure/title）
#     CREATE_MAP 要求 generics（前端只要 title）
NODE_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    # ---- 变量 ----
    # 基础版 paramType/dataType/title；实体版 paramType/app/structure/title
    # （按 paramType 二选一，见 CREATE_VARIABLE_BY_PARAMTYPE）
    "CREATE_VARIABLE": ("paramType", "title"),
    "CREATE_VARIABLE_FRONT": ("paramType", "title"),
    "CHANGE_VARIABLE": ("selectParam",),
    "CHANGE_VARIABLE_FRONT": ("selectParam",),
    # ---- 列表 / Map ----
    "CREATE_LIST": ("paramType", "title", "dataType"),
    "CREATE_LIST_FRONT": ("paramType", "title", "dataType"),
    "CHANGE_LIST": ("selectParam", "action", "dataSource"),   # ★ dataSource 必填
    "CHANGE_LIST_FRONT": ("selectParam", "action", "dataSource"),
    "CREATE_MAP": ("title",),                                  # ★ 只要 title
    "MAP_OPERATION": ("selectMap", "operationType"),  # ★ entries 只对 PUT/REMOVE 必填（真实 6/6 GET 无 entries）
    "LIST_OPERATION": ("selectParam", "operationType", "title"),
    "FED_LIST_OPERATION": ("selectParam", "operationType", "title"),
    "VALUE_HANDLE": ("items",),
    "ADVANCED_PROPERTIES": ("items",),
    # ---- 提示 ----
    "MESSAGE_INFO": ("messageType", "showInfo"),
    # ---- 数据 ----
    "RETRIEVE": ("app", "structure", "title"),                 # ★ 前端只要 3 个
    "RETRIEVE_ARRAY": ("app", "structure", "variableTitle"),   # ★ variableTitle 不是 title
    "CREATE_ENTITY": ("app", "structure", "mappingType", "value", "title"),  # ★ value
    "CHANGE_ENTITY": ("selectParam", "title"),
    "CREATE_BATCH_ENTITY": ("selectParam", "title"),
    "CHANGE_BATCH_ENTITY": ("selectParam", "title"),
    "DELETE_ENTITY": ("deleteType", "app", "structure", "condition", "title"),
    "CONVERT_DATA": ("convertType", "selectParam", "title"),
    # ---- 调用 ----
    "SUB_MICROFLOW": ("mfService",),
    "CALL_MICRO_FLOW": ("mfService",),
    "CALL_APP_SERVICE": ("app", "selectMethod"),      # 另有 validate_call_app_service
    "OPEN_PAGE": ("config",),
    "CONTROL_ACTION": ("config",),
    # ---- 流程控制 ----
    "BRANCH": (),          # ★ 前端不要求 conditions
    "CONDITION": (),       # ★ 前端不要求 nodes
    "BREAK": (),
    "FOR": ("forStart", "forEnd", "forStep", "targetName"),   # ★ targetName 必填
    "CUSTOM_ERROR": ("error",),                               # ★ 只要 error
    # ---- 样本不足，保守 ----
    "DATA_MAPPING": ("targetType", "mappingRows"),
    "CALL_DATA_FLOW": ("dataFlowMappingId", "structure", "entityId"),
    "PUBLISH_BUSINESS_EVENT": ("mappingType",),
}

# CREATE_VARIABLE 按 paramType 分叉（前端两张表）
CREATE_VARIABLE_BY_PARAMTYPE: dict[str, tuple[str, ...]] = {
    "BASIC": ("dataType",),
    "ENTITY_OBJECT": ("app", "structure"),
    "FRONTEND_PARAM": ("app", "structure"),
}

# ============================================================================
# 保存校验必填表（2026-10-28 实测，LIVE）
# ============================================================================
# 来源：点击「保存并提交」后，前端逐节点 console.log：
#   `X 的所有必填属性=> [...]`
# 这是**保存时的全量校验**，包含条件必填（如 RETRIEVE 的 nullPromptMessage
# 仅在 nullHandling=TERMINATION 时要求）。因此它与上面的 NODE_REQUIRED_FIELDS
# （= 打开抽屉时表单上可见的 required）是**两个不同层次**，不能互相覆盖：
#
#   NODE_REQUIRED_FIELDS   → UI 表单必填（生成节点时填什么）
#   SAVE_REQUIRED_FIELDS   → 保存校验必填（提交前必须满足，含条件分支）
#
# 用法：生成节点时用前者；保存前用后者做最终闸门。
SAVE_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "START": (),
    "END": (),
    "BRANCH": (),
    "CONDITION": (),
    "BREAK": (),
    "CREATE_VARIABLE": ("dataType", "otherType", "paramType", "title"),
    "CHANGE_VARIABLE": ("selectParam",),
    "CREATE_LIST": ("dataType", "paramType", "title"),
    "CHANGE_LIST": ("action", "selectParam"),
    "CREATE_MAP": ("title",),
    "MAP_OPERATION": ("arrayOrObject", "basic", "nullPromptMessage", "operationType",
                      "paramType", "selectMap", "theKey", "title"),
    "LIST_OPERATION": ("operationType", "selectParam", "title"),
    "RETRIEVE": ("app", "nullPromptMessage", "structure", "title"),
    "RETRIEVE_ARRAY": ("app", "pageInfo", "structure", "variableTitle"),
    "CREATE_ENTITY": ("app", "attrs", "mappingType", "structure", "title"),
    "CHANGE_ENTITY": ("selectParam", "title"),
    "CREATE_BATCH_ENTITY": ("selectParam", "title"),
    "CHANGE_BATCH_ENTITY": ("selectParam", "title"),
    "DELETE_ENTITY": ("app", "deleteType", "structure", "title", "value"),
    "CONVERT_DATA": ("convertType", "selectParam", "title"),
    "DATA_MAPPING": ("app", "mappingRule", "selectParam", "structure", "targetType",
                     "title"),
    "SUB_MICROFLOW": ("mappingType", "mfService", "outputName"),
    "CALL_APP_SERVICE": ("app", "outputName", "selectMethod"),
    "CUSTOM_ERROR": ("attrError", "attrType", "selectParam", "sourceData"),
    "FOR": ("forEnd", "forStart", "forStep", "targetName"),
    "FOR_EACH": ("selectParam", "targetName"),
}

# 保存校验里**条件必填**的字段（并集里出现，但不是恒需）
SAVE_CONDITIONAL_FIELDS: dict[str, dict[str, str]] = {
    "RETRIEVE": {"nullPromptMessage": "仅 nullHandling=TERMINATION 时必填"},
    "CUSTOM_ERROR": {
        "attrError": "仅 errorType=POSITION 时必填",
        "attrType": "仅 errorType=POSITION 时必填",
        "selectParam": "仅 errorType=POSITION 时必填",
        "sourceData": "仅 errorType=POSITION 时必填",
    },
    "MAP_OPERATION": {
        "theKey": "仅 operationType=GET 时必填",
        "basic": "仅 paramType=BASIC 时必填",
        "nullPromptMessage": "仅 nullHandling=TERMINATION 时必填",
    },
    "CREATE_VARIABLE": {"otherType": "仅 paramType=其他 时必填"},
}

# UI 表单必填与保存校验必填的**真实分歧**（2026-10-28 实测）
# 这些字段在 UI 表单上标 required，但保存校验的必填清单里没有；
# 反之亦然。生成节点时必须两者都满足。
UI_VS_SAVE_DIVERGENCE: dict[str, dict[str, str]] = {
    "CHANGE_LIST": {
        "dataSource": "UI 表单必填，但保存校验未列入（实测该字段有默认值）",
    },
    "CREATE_ENTITY": {
        "value": "UI 表单必填，但保存校验要 attrs（attrs 才是真实提交字段）",
    },
    "DELETE_ENTITY": {
        "condition": "UI 表单必填，保存校验要 value（条件查询用 value 承载）",
    },
    "CUSTOM_ERROR": {
        "error": "GLOBAL 模式的字段，保存校验清单是 POSITION 模式的并集",
    },
    "DATA_MAPPING": {
        "mappingRows": "UI 表单必填，保存校验要整个 mappingRule 对象",
    },
}

# 选择器回填字段：生成器必须从候选集取，不能自造
SELECTOR_FILLED_FIELDS: dict[str, tuple[str, ...]] = {
    "RETRIEVE": ("app", "structure", "title", "selectType", "scope", "methodLegal"),
    "RETRIEVE_ARRAY": ("app", "structure", "variableTitle", "selectType", "scope",
                       "methodLegal"),
    "CHANGE_ENTITY": ("selectParam", "title"),
    "CALL_APP_SERVICE": ("app", "selectMethod"),
    "SUB_MICROFLOW": ("mfService",),
    "CALL_MICRO_FLOW": ("mfService",),
}

# ---- RETRIEVE_ARRAY 分 fetchType 的必填 ----
RETRIEVE_ARRAY_FETCH_TYPES: dict[str, int] = {"CONDITION": 0, "IDS": 1, "COUNT": 2, "OTHERS": 3}
# ★ CONDITION 分支是「condition 或 value 至少一个」：全库实测 condition 66%、
#   value 24%，两者覆盖 90%；剩下 10% 是真不完整节点，本来就该被拦。
RETRIEVE_ARRAY_BY_FETCHTYPE: dict[str, tuple[str, ...]] = {
    "CONDITION": (),                # 见 required_fields 的 OR 分支
    "IDS": ("value",),
    "COUNT": (),
    "OTHERS": ("aggFunction",),
}
# RETRIEVE 分 fetchType
RETRIEVE_BY_FETCHTYPE: dict[str, tuple[str, ...]] = {
    "CONDITION": (),                # 见 required_fields 的 OR 分支
    "IDS": ("value",),
    "COUNT": (),
    "OTHERS": (),
}

# ---- DATA_MAPPING ----
DATA_MAPPING_TARGET_TYPES: tuple[str, ...] = ("ENTITY", "DTO")            # DataMappingTargetTypeEnum
DATA_MAPPING_MODES: tuple[str, ...] = ("REFERENCE", "CONSTANT")           # DataMappingRow$DataMappingMode
DATA_MAPPING_CONSTANT_TYPES: tuple[str, ...] = ("SIMPLE", "JAVA_ENUM", "CTP_ENUM")

# ---- 条件操作符（★权威：boot-starter-condition 5.3.308 OperatorEnum）----
#   值 = {代码: (SQL片段, 显示名, 右参数个数)}
#   ★不是前端看到的 20 个——权威 22 个，多了 ZERO/NOTZERO；NEQ 是 "<>" 不是 "!="
CONDITION_OPERATORS: dict[str, tuple[str, str, int]] = {
    "EQ": ("=", "等于", 1), "NEQ": ("<>", "不等于", 1),
    "GT": (">", "大于", 1), "LT": ("<", "小于", 1),
    "GE": (">=", "大于等于", 1), "LE": ("<=", "小于等于", 1),
    "RLIKE": ("like", "右匹配", 1), "LLIKE": ("like", "左匹配", 1),
    "LIKE": ("like", "全匹配", 1), "NOTLIKE": ("not like", "不匹配", 1),
    "IN": ("in", "包含", 1), "NOTIN": ("not in", "不包含", 1),
    "NULL": ("is null", "为空", 0), "NOTNULL": ("not null", "不为空", 0),
    "ZERO": ("= 0", "为零", 0), "NOTZERO": ("<> 0", "不为零", 0),
    "BETWEEN": ("between", "介于", 2), "NOTBETWEEN": ("not between", "不介于", 2),
    "INCLUDEALL": ("include all", "包含全部", 1), "INCLUDEANY": ("include any", "包含任一个", 1),
    "NOTINCLUDEALL": ("not include all", "不包含全部", 1),
    "NOTINCLUDEANY": ("not include any", "不包含任一个", 1),
}
# 无右参（size=0）/ 双右参（size=2）
CONDITION_NO_RIGHTPARAM: frozenset[str] = frozenset(
    k for k, v in CONDITION_OPERATORS.items() if v[2] == 0)
CONDITION_TWO_RIGHTPARAM: frozenset[str] = frozenset(
    k for k, v in CONDITION_OPERATORS.items() if v[2] == 2)
# 右值类型（SingleConditionDto 左值 Type + ParamTypeEnum + RightParamDto.type）
CONDITION_LEFT_TYPES: tuple[str, ...] = ("OBJECT", "ARRAY")        # Type
CONDITION_PARAM_TYPES: tuple[str, ...] = ("CONSTANT", "EXPRESSION")  # ParamTypeEnum
CONDITION_RIGHT_TYPES: tuple[str, ...] = ("CONSTANT", "EXPRESSION", "CONTEXT_VARIABLE")  # RightParamDto.type
# 右值为空时的处理策略（LeftParamDto.nullRightValueCondType）
NULL_RIGHT_VALUE_COND_TYPES: tuple[str, ...] = (
    "IGNORE_IF_ANY_NULL", "USE_DEFAULT_VALUE", "INVALID_IF_ANY_NULL")
# 条件项关系（分组）
CONDITION_RELATIONS: tuple[str, ...] = ("ONE2ONE", "ONE2MANY")   # RelationEnum
# 条件逻辑操作符（★权威 BaseConditionDto$LogicalOperator）：desc/symbol/value
CONDITION_LOGICAL_OPERATORS: dict[str, tuple[str, str, str]] = {
    "AND": ("and", "&&", "and"),
    "OR": ("or", "||", "or"),
}
# 条件项类型（BaseConditionDto @JsonSubTypes：GROUP / CONDITION）
CONDITION_ITEM_TYPES: tuple[str, ...] = ("GROUP", "CONDITION")
# 左值必填字段（LeftParamDto）：@NotBlank dto + @NotBlank field
CONDITION_LEFT_REQUIRED: tuple[str, ...] = ("dto", "field")
# ---- 后端 ConditionService.check 契约（boot-starter-condition 5.3.318 反编译）----
#   ConditionService.checkDetail / checkConditionLegal：
#     1) leftParam / operator / rightParams 三者均不可为 null，否则 BusinessException
#     2) GROUP 内从第 2 个条件起 logicalOperator 不可为空（"条件组内条件logicOperator不能为空"）
#     3) type 只能是 GROUP / CONDITION，否则抛 "暂不支持这种类型的条件:<type>"
CONDITION_REQUIRED_PARTS: tuple[str, ...] = ("leftParam", "operator", "rightParams")
CONDITION_GROUP_LOGICAL_OPERATOR_REQUIRED_FROM_INDEX: int = 1

def condition_operator_size(op: str) -> int:
    """返回某操作符需要的右参数个数（-1 表示未知操作符）。"""
    return CONDITION_OPERATORS.get(op, ("", "", -1))[2]

# ---- 实体属性数据类型（★权威：udc-common 5.3.517 UdcDataType 实例注册表 + DataType enum）----
ENTITY_DATA_TYPES: tuple[str, ...] = (
    "STRING", "MULTILINESTRING", "CONTENT", "OPINION", "DOCUMENTNUMBER",
    "INTEGER", "BIGINTEGER", "DECIMAL", "CURRENCY", "SERIAL",
    "BOOLEAN", "DATE", "TIME", "DATETIME",
    "ENUM", "CTPENUM", "ENTITY",
    "ATTACHMENT", "MULTIATTACHMENT",
    "MULTIENUM", "MULTIENTITY", "MULTICTPENUM",
)
# 各类型对应 UdcDataType 实现类（udc-common .../datatype/instance/*）
ENTITY_DATA_TYPE_IMPLS: dict[str, str] = {
    "STRING": "StringDataType", "MULTILINESTRING": "MultilineStringDataType",
    "CONTENT": "ContentDataType", "OPINION": "OpinionDataType",
    "DOCUMENTNUMBER": "DocumentnumberDataType", "INTEGER": "IntegerDataType",
    "BIGINTEGER": "BigIntegerDataType", "DECIMAL": "DecimalDataType",
    "CURRENCY": "CurrencyDataType", "SERIAL": "SerialDataType",
    "BOOLEAN": "BooleanDataType", "DATE": "DateDataType", "TIME": "TimeDataType",
    "DATETIME": "DateTimeDataType", "ENUM": "EnumDataType", "CTPENUM": "CtpEnumDataType",
    "ENTITY": "EntityDataType", "ATTACHMENT": "AttachmentDataType",
}

# 活动节点 actionType → 中文名（★权威：SourceDataTypeEnum 内嵌节点类型表）
ACTIVITY_NODE_CAPTIONS: dict[str, str] = {
    "CONNECTOR": "连接器", "CREATE_VARIABLE": "创建变量", "CHANGE_VARIABLE": "修改变量",
    "CREATE_LIST": "创建列表", "CHANGE_LIST": "修改列表", "PUBLISH_BUSINESS_EVENT": "业务消息",
    "ATTRIBUTE_REQUIRED": "必填", "ASSIGN_VALUE": "设置值", "SHOW_MESSAGE": "提示信息",
    "ATTRIBUTE_UNIQUE": "唯一", "RETRIEVE": "查询单记录", "RETRIEVE_ARRAY": "查询多记录",
    "CHANGE_ENTITY": "更新数据", "CREATE_ENTITY": "插入数据", "DELETE_ENTITY": "删除数据",
    "LIST_OPERATION": "列表操作", "SUB_MICROFLOW": "子流程", "CALL_MICRO_FLOW": "后端微流程",
    "CALL_APP_SERVICE": "服务调用", "CALL_DATA_FLOW": "生单规则", "VISIBLE": "可见性",
    "DEFAULT_VALUE": "默认值", "ATTR_VISIBLE": "可见性", "SET_VALUE": "设置值",
    "SET_REQUIRED": "必填", "ENABLE": "启用禁用", "READ_ONLY": "只读",
    "OPEN_PAGE": "打开页面", "CLOSE_PAGE": "关闭页面",
}

# 微流程分组类型中文（MicroFlowManualTypeLike）
MICROFLOW_GROUP_TYPES: dict[str, str] = {
    "MICRO_FLOW_MANUAL": "服务定义", "MICRO_FLOW_FRONTEND": "前端微流程",
    "MICRO_FLOW_ENTITY_RULE": "实体规则", "MICRO_FLOW_BUSINESS_EVENT": "业务事件",
    "MICRO_FLOW_SCHEDULE": "定时任务",
}
# 组件来源（ComponentSourceTypeEnum）
COMPONENT_SOURCE_TYPES: dict[int, str] = {1: "内置", 2: "自定义", 3: "第三方"}

# ---- 其它枚举值域 ----
CHANGE_LIST_ACTIONS: tuple[str, ...] = ("ADD", "REMOVE", "CLEAR", "REPLACE")   # ChangeListActionTypeEnum
MAP_OPERATIONS: tuple[str, ...] = ("GET", "PUT", "REMOVE", "KEY_SET")          # MapOperationTypeEnum
CALL_DATA_FLOW_SOURCE_TYPES: tuple[str, ...] = ("CONDITION", "SELECT_PARAM")   # CallDataFlowActivity$DataSourceTypeEnum
MAPPING_TYPES: tuple[str, ...] = ("attrs", "value", "mapping")                 # MappingTypeEnum
ATTR_VALUE_TYPES: tuple[str, ...] = ("Expression", "SelectParam", "CtpEnum", "Simple", "System",
                                     "SelectPeopleData", "Enum", "CONTEXT_VARIABLE")  # AttrValueTypeEnum
NULL_HANDLING: tuple[str, ...] = ("TERMINATION", "CONTINUE")                   # NullHandlingEnum
CRON_TYPES: tuple[str, ...] = ("FIRST", "LAST", "ANY")                         # CronTypeEnum
ROTATION_TYPES: tuple[str, ...] = ("DAY", "HOUR", "MINUTE")                    # RotationTypeEnum
DTO_TYPES: tuple[str, ...] = ("MASTER_ENTITY", "SUB_ENTITY", "CUSTOM", "THIRD", "MESSAGE",
                              "MICRO_FLOW_EVENT")                              # MicroFlowDtoTypeEnum
META_DATA_TYPES: tuple[str, ...] = ("ENTITY", "PAGE")                          # MetaDataTypeEnum
CUSTOM_ERROR_TYPES: tuple[str, ...] = ("USER",)                                # CustomErrorTypeEnum
EVENT_TYPES: tuple[str, ...] = ("AMONG_APP", "IN_APP")                         # MicroFlowEventTypeEnum
DTO_PARSER_TYPES: tuple[str, ...] = ("JSON", "XML")                            # DtoParserTypeEnum

# LIST_OPERATION 操作类型（ListOperationTypeEnum，含中文）
LIST_OPERATIONS: dict[str, str] = {
    "sum": "求和", "size": "计数", "max": "最大值", "min": "最小值", "filter": "过滤",
    "find": "查找", "sort": "排序", "union": "并集", "intersect": "交集", "subtract": "差集",
    "contains": "包含", "equals": "相等", "groupAndSum": "分组汇总", "firstOne": "第一条",
    "lastOne": "最后一条", "pickOne": "选择一条", "distinct": "去重", "subList": "获取子列表",
    "map": "字段收集",
}

# AppServiceTypeEnum：每活动节点调用的平台服务（checkUdcEntityOpenApi 用）
APP_SERVICE_TYPES: dict[str, int] = {
    "NONE": -1, "SELECT_PAGE_BY_COMPLEX_CONDITIONS": 0, "SELECT_PAGE_BY_CONDITIONS": 1,
    "CREATE": 2, "CREATE_BATCH": 3, "UPDATE": 4, "UPDATE_BATCH": 5, "DELETE_BY_ID": 6,
    "DELETE_BY_IDS": 7, "SELECT_BY_ID": 8, "SELECT_BY_IDS": 9, "SELECT_BY_CASCADE_ID": 10,
    "SELECT_BY_CASCADE_IDS": 11, "SELECT_LIST_BY_CONDITIONS": 12, "SELECT_COUNT_BY_CONDITIONS": 13,
    "SELECT_LIST_BY_COMPLEX_CONDITIONS": 14, "SELECT_COUNT_BY_COMPLEX_CONDITIONS": 15,
    "DELETE_BY_CONDITIONS": 16, "DELETE_BY_SELECT": 17, "DELETE_BY_COMPLEX_CONDITIONS": 18,
    "SELECT_LIST_FUNC_BY_COMPLEX_CONDITIONS": 19,
}

# 校验错误码（MicroFlowParseErrorEnum 精选，用于理解"限制条件"文案与落点）
PARSE_ERRORS: dict[str, str] = {
    "PROPERTY_IS_REQUIRED": "必填参数未配置，请点击该节点参数设置",
    "NOT_MATCH": "数据类型不匹配",
    "OUT_OF_SCOPE": "前序节点发生变更请重新选择",
    "NOT_RELEASE": "调用的微流程不是正式态",
    "WITHOUT_OUTPUT": "没有定义出参",
    "LOOP_CALL": "存在循环调用",
    "ENTITY_DELETE": "实体已删除",
    "EVENT_USED": "订阅的业务事件已被其他微流程使用",
    "METADATA_DELETE": "微流程配置的元数据已被删除",
    "SCHEDULE_NOT_EXIST": "微流程配置的定时任务在调度中心不存在",
    "CONNECTOR_APP_SERVICE_DELETED": "所选连接器不存在",
    "MQ_DELETE": "所选 MQ 消息不存在",
}

# 入参 paramType（前端 FLOW_INPUT；MicroFlowParamDataTypeEnum = {DTO, Entity}）
TRIGGER_PARAM_TYPES: tuple[str, ...] = ("NONE", "BASIC", "ENTITY_OBJECT", "DEFAULT_OBJECT")
TRIGGER_BASIC_TYPES: tuple[str, ...] = ("STRING", "INTEGER", "LONG", "BIGINTEGER", "DECIMAL",
                                        "BOOLEAN", "DATE", "DATETIME", "OBJECT", "DTO", "ARRAY")


def _apply_param_type(action_type: str, node: dict | None,
                      base: tuple[str, ...]) -> tuple[str, ...]:
    """CREATE_VARIABLE/CREATE_LIST 的必填随 paramType 变化。"""
    if action_type not in ("CREATE_VARIABLE", "CREATE_LIST") or not node:
        return base
    extra = CREATE_VARIABLE_BY_PARAMTYPE.get(str(node.get("paramType") or ""), ())
    return tuple(dict.fromkeys(base + extra))


def required_fields(action_type: str, node: dict | None = None) -> tuple[str, ...]:
    """返回某活动节点在当前配置下的必填字段（含 fetchType / nullHandling 分支）。"""
    if action_type in ("RETRIEVE", "RETRIEVE_ARRAY"):
        ft = (node or {}).get("fetchType") or "CONDITION"
        table = (RETRIEVE_BY_FETCHTYPE if action_type == "RETRIEVE"
                 else RETRIEVE_ARRAY_BY_FETCHTYPE)
        # ★ 基础必填 + 分支必填都要（旧实现 RETRIEVE 只返回分支，漏了 app/structure 等）
        base = list(NODE_REQUIRED_FIELDS[action_type]) + list(table.get(ft, ()))
        if (node or {}).get("nullHandling") == "TERMINATION":
            base.append("nullPromptMessage")   # 后端仅在 TERMINATION 时 required
        out = tuple(dict.fromkeys(base))
        # CONDITION 分支：condition 或 value 至少一个（实测 66% / 24%）
        if ft == "CONDITION" and (node or {}).get("condition") is None \
                and (node or {}).get("value") is None:
            return out + ("condition|value",)
        return out
    return _apply_param_type(action_type, node,
                             NODE_REQUIRED_FIELDS.get(action_type, ()))


def _resolve_field(node: dict, f: str):
    """按真实落点取字段值（不是所有必填都长在节点顶层）。

    ★ CALL_DATA_FLOW 的 entityId 真实落点是 `structure.entityId`：全库 4 条样本
      都没有节点级 entityId，实体 id 只在 structure 里（字符串雪花 id）。
      平台 checkSchema 的 path 报成 `.<nodeCaption>.entityId` 是解析器的相对路径，
      在顶层补 entityId 反而不被读到（实测 V11 顶层给了字符串仍报必填）。
    """
    v = node.get(f)
    if v is not None and v != "" and not (isinstance(v, (list, dict)) and len(v) == 0):
        return v
    if f == "entityId":
        return (node.get("structure") or {}).get("entityId")
    return v


def validate_node_fields(action_type: str, node: dict) -> list[str]:
    """按全库反推的必填字段校验节点；返回错误列表（空=通过）。

    ★ 2026-10-28：叠加 UI 层校验（`microflow_ui_constraints.validate_node_ui`），
      覆盖结构层看不到的前端联动/值域事实（convertType 必须有 value、
      DATA_MAPPING output.type=ARRAY、BREAK 只能在循环体内等）。
    """
    errs = []
    if action_type == "DATA_MAPPING":
        mr = node.get("mappingRule") or {}
        for f in ("targetType", "mappingRows"):
            v = mr.get(f)
            if v is None or v == "" or (isinstance(v, (list, dict)) and len(v) == 0):
                errs.append(f"{action_type} 缺必填字段 mappingRule.{f}")
        errs.extend(_ui_layer_errors(action_type, node))
        return errs
    # ★ CREATE_ENTITY：mappingType=attrs 时 value 可为空（真实样本 31 个 attrs、value 缺失）
    #   前端 requiredFields 只覆盖 value（对象引用）那一支，字段映射支用 attrs 承载。
    skip = set()
    if action_type == "CREATE_ENTITY" and node.get("mappingType") == "attrs"             and node.get("attrs"):
        skip.add("value")
    for f in required_fields(action_type, node):
        if f in skip:
            continue
        if f == "condition|value":
            if node.get("condition") is None and node.get("value") is None:
                errs.append(f"{action_type} fetchType=CONDITION 时 condition 与 value 至少要有一个")
            continue
        v = _resolve_field(node, f)
        if v is None or v == "" or (isinstance(v, (list, dict)) and len(v) == 0):
            hint = ""
            if f in SELECTOR_FILLED_FIELDS.get(action_type, ()):
                hint = "（选择器回填字段，须先从候选集取，不能自造）"
            errs.append(f"{action_type} 缺必填字段 {f}{hint}")
    if action_type == "CALL_APP_SERVICE":
        errs.extend(validate_call_app_service(node))
    errs.extend(_ui_layer_errors(action_type, node))
    return errs


def _ui_layer_errors(action_type: str, node: dict) -> list[str]:
    """UI 层校验（前端联动/值域事实）。延迟导入避免循环依赖。"""
    try:
        from components.udc.microflow_ui_constraints import validate_node_ui
    except ImportError:
        return ["UNVERIFIED: microflow UI validation unavailable"]
    return validate_node_ui(node)


# ---- CALL_APP_SERVICE 调用配置校验 ----
# 证据：docs/operation-contracts/udc/microflow/cappservice-parameter-semantics.md §5 逐字段总表
# （本应用 LIVE 3 节点 + 全库 395 节点扫描 + 12 条跨应用样本）。
# 为什么必须本地校验：该类节点在 NODE_REQUIRED_FIELDS 里是空元组（等于不校验），
# 而平台 checkSchema 是浅校验（microflow-rest-write-chain.md §4），
# 调错方法/参数载体/入参类型都会静默通过，只在运行期失败。
CALL_APP_SERVICE_PARAMETER_TYPES: frozenset[str] = frozenset({"SingleRequest", "PageDtoRequest"})
CALL_APP_SERVICE_RETURN_TYPES: frozenset[str] = frozenset(
    {"SingleResponse", "ListResponse", "PageResponse"})
CALL_APP_SERVICE_MAPPING_TYPE: str = "attrs"


def _type_short_name(t) -> str:
    """取类型短名。

    ★ 真实数据里 `parameter.type` / `returnValue.type` 是**全限定名**
      （`com.seeyon.boot.transport.SingleRequest`），不是短名。
      只比短名会把 100% 的真实节点判非法 —— 实测 83/83 全拦。
    """
    s = str(t or "")
    return s.rsplit(".", 1)[-1].strip()


def _type_in(t, allowed: frozenset[str]) -> bool:
    return _type_short_name(t) in allowed


def validate_call_app_service(node: dict) -> list[str]:
    """校验 CALL_APP_SERVICE 节点的「调用配置」是否可定位到唯一服务。

    只断言契约 §5 中有硬规则的字段；md5 明确禁等值比对（同一 fullName 可有多 md5，
    容器条键可缺省），故不参与校验。pageInfo 等标 UNVERIFIED 的字段不在此断言。
    """
    errs: list[str] = []
    sm = node.get("selectMethod")
    if not isinstance(sm, dict) or not sm:
        return ["CALL_APP_SERVICE 缺 selectMethod —— 无法定位被调服务"
                "（契约 §5：fullName 是唯一稳定匹配键）"]

    full = sm.get("fullName")
    if not full or not isinstance(full, str):
        errs.append("CALL_APP_SERVICE 缺 selectMethod.fullName —— 唯一稳定匹配键，缺则无法定位服务")
    else:
        # §2.1：fullName == implClass + "." + 方法名
        impl = sm.get("implClass")
        if impl and not str(full).startswith(str(impl) + "."):
            errs.append(
                f"CALL_APP_SERVICE selectMethod.implClass={impl!r} 不是 fullName={full!r} 的前缀"
                "（契约 §2.1：fullName == implClass + '.' + 方法名）")

    param = sm.get("parameter")
    if not isinstance(param, dict):
        errs.append("CALL_APP_SERVICE 缺 selectMethod.parameter —— 无法确定请求载体")
    else:
        ptype = param.get("type")
        if not _type_in(ptype, CALL_APP_SERVICE_PARAMETER_TYPES):
            errs.append(
                f"CALL_APP_SERVICE selectMethod.parameter.type={ptype!r} 越界"
                f"（合法值 {sorted(CALL_APP_SERVICE_PARAMETER_TYPES)}）")
        item = param.get("item") if isinstance(param.get("item"), dict) else {}
        if not item.get("itemType"):
            errs.append("CALL_APP_SERVICE selectMethod.parameter.item.itemType 为空"
                        "（作用域键，attrs[].attrType.id 须以其为前缀）")

    ret = sm.get("returnValue")
    if not isinstance(ret, dict):
        errs.append("CALL_APP_SERVICE 缺 selectMethod.returnValue —— 无法确定响应载体")
    else:
        rtype = ret.get("type")
        if not _type_in(rtype, CALL_APP_SERVICE_RETURN_TYPES):
            errs.append(
                f"CALL_APP_SERVICE selectMethod.returnValue.type={rtype!r} 越界"
                f"（合法值 {sorted(CALL_APP_SERVICE_RETURN_TYPES)}）")
        ritem = ret.get("item") if isinstance(ret.get("item"), dict) else {}
        if not ritem.get("itemType"):
            errs.append("CALL_APP_SERVICE selectMethod.returnValue.item.itemType 为空")

    # ★ mappingType 只在「入参是 DTO（需要字段映射）」时要求 attrs。
    #   实测 39 个真实节点：itemType=java.lang.Long/String 的 15 个节点 mappingType 为 null、
    #   attrs 为空、靠 value 传单值；itemType 是 DTO 的 24 个才是 attrs。
    #   按「必须 attrs」一刀切会把 38% 的合法节点判非法。
    mt = node.get("mappingType")
    _p_item = param.get("item") if isinstance(param, dict) and isinstance(param.get("item"), dict) else {}
    _pt = str(_p_item.get("itemType") or "")
    _scalar = _pt.startswith(("java.lang.", "java.math.", "java.util.Date", "int", "long",
                              "double", "boolean", "float", "short", "byte", "char"))
    if not _scalar and mt != CALL_APP_SERVICE_MAPPING_TYPE:
        errs.append(f"CALL_APP_SERVICE mappingType={mt!r} 应为 {CALL_APP_SERVICE_MAPPING_TYPE!r}"
                    "（入参是 DTO 时必须做字段映射；标量入参可用 value 传单值，不要求）")

    # 入参绑定前缀：把 A 类型字段绑到 B 类型服务参数上，平台不报错、运行期才炸
    want = ""
    if isinstance(param, dict) and isinstance(param.get("item"), dict):
        want = str(param["item"].get("itemType") or "")
    if want:
        for i, attr in enumerate(node.get("attrs") or []):
            if not isinstance(attr, dict):
                continue
            at = attr.get("attrType")
            aid = str((at or {}).get("id") or "") if isinstance(at, dict) else ""
            if aid and not aid.startswith(want + "."):
                errs.append(
                    f"CALL_APP_SERVICE attrs[{i}].attrType.id={aid!r} 前缀不是"
                    f" parameter.item.itemType={want!r}"
                    "（入参绑定了别的类型，平台不拦、运行期错）")
    return errs


# ---- DATA_MAPPING.mappingRule / mappingRows 的 parse 必填集（CFR udc-biz 5.3.517 实证）----
# 证据：DataMappingActivity.parseMappingRule(:109) 逐键 NodeUtils.getXxx(required=true)：
#   uuid / type / javaType / name / mappingRows / subobjects
# ★ 反直觉点 1：rule 级 type / javaType / name / subobjects 都是 required=true，
#   而设计器落库的“健康”mappingRule 常只有 {uuid,targetType,mappingRows}（缺以上 4 键）。
#   即：DB 能存、构造能过，但一旦 state=RELEASE 走检测/发布就报
#   PROPERTY_IS_REQUIRED | ...mappingRule.type（这是 UDC_CE_MICRO_FLOW_04003 的根因之一）。
# ★ 反直觉点 2（错误落点不可区分）：DataMappingField.buildDataMappingField -> parsePath
#   -> BaseMicroFlowComponent.buildByObjectNode(node, location, ...) 复用 rule 的 location，
#   于是 row 的 targetField / value.reference（holder）及其 path[] 每个元素的
#   name/dataType/type/javaType 缺失，全部被报成同一个 .mappingRule.<key>。
#   => 看到 mappingRule.type 报错时，缺键可能在 rule 本身，也可能在任意 row 的 holder/path 元素。
MAPPING_RULE_REQUIRED_KEYS: tuple[str, ...] = ("uuid", "type", "javaType", "name",
                                               "mappingRows", "subobjects")

# holder（targetField / value.reference）与其 path[] 元素经 BaseMicroFlowComponent 解析时必填
MAPPING_FIELD_REQUIRED_KEYS: tuple[str, ...] = ("name", "dataType", "type", "javaType")

# ---- 触发节点 BusinessEventTrigger.eventDataFullName（同属 04003 根因集）----
# 证据：BusinessEventTrigger(:64) NodeUtils.getString(eventDataFullName, objectNode, true, ...)
# 实测：非空即可（DTO 全名 / 实体全名 / 非空串均放行；空串等同缺失）。
BUSINESS_EVENT_TRIGGER_REQUIRED_KEYS: tuple[str, ...] = (
    "eventFullName", "eventDataFullName", "eventMfCustomDtoName", "eventName",
    "currentId", "currentType")


def validate_mapping_rule(mr: dict | None) -> list[str]:
    # 按 parse 必填集校验 mappingRule（含 row holder 与其 path 元素）。空列表=通过。
    # 文案显式标注“落点不可区分”，避免使用者误改 rule 本身。
    errs: list[str] = []
    if not isinstance(mr, dict):
        return ["mappingRule 缺（DataMappingActivity.parseMappingRule 要求对象）"]
    for k in MAPPING_RULE_REQUIRED_KEYS:
        if k not in mr:
            errs.append(f"mappingRule 缺 parse 必填键 {k!r}（rule 级 required=true）")
    for i, row in enumerate(mr.get("mappingRows") or []):
        pairs = (("targetField", row.get("targetField")),
                 ("value.reference", (row.get("value") or {}).get("reference")))
        for holder_name, holder in pairs:
            if not isinstance(holder, dict):
                continue
            for k in MAPPING_FIELD_REQUIRED_KEYS:
                if holder.get(k) in (None, ""):
                    errs.append(f"mappingRows[{i}].{holder_name} 缺 {k!r}"
                                f"（parse 复用 rule location，服务端报到 .mappingRule.{k}）")
            for j, el in enumerate(holder.get("path") or []):
                for k in MAPPING_FIELD_REQUIRED_KEYS:
                    if el.get(k) in (None, ""):
                        errs.append(f"mappingRows[{i}].{holder_name}.path[{j}] 缺 {k!r}"
                                    f"（同上：服务端落点不可区分）")
    return errs


# =====================================================================
# 第二十七轮 LIVE 新增：RELEASE 闸门 + 发布判据 + 校验器读数面
# 证据等级：LIVE（REST 实测）+ VERIFIED_STATIC_BYTECODE（CFR udc-biz 5.3.517）
# =====================================================================

# ★ 关键端点：只有 checkSchemaAndUpdate 会「校验 + 发布」，其余全部强制草稿。
# CFR MicroFlowAppService(:330) checkSchemaAndUpdate：
#   if (MicroFlowDataStateEnum.RELEASE.equals(dto.getState())) { checkSchema -> ... -> update }
# CFR MicroFlowAppService(:383) update / (:372) create 均先调 setServiceMfToDraft(:926)
#   => 仅当 MicroFlowTypeEnum.SERVICE 时把 state 置 DRAFT（SERVICE 型永不可能经 update 发布）。
# LIVE 双向验证（本轮）：
#   DRAFT  --(checkSchema/update, state=RELEASE)-->  RELEASE
#   RELEASE --(update,             state=DRAFT)  -->  DRAFT
# 结论：**发布判据 = 客户端必须在 DTO 里自带 state=RELEASE**；服务端不回写、不推断。
PUBLISH_ENDPOINT = "POST /service/udc/microflow/checkSchema/update"

# ★ RELEASE 是「深度校验闸门」。同 body 换 state 会走不同校验分支：
#   state=DRAFT   -> 浅校验（只报必填一层），历史多轮都用它 => 长期看不出真问题
#   state=RELEASE -> 深度 parse 校验（PROPERTY_IS_REQUIRED / NOT_OBJECT / DATA_INVALID 逐层下钻）
RELEASE_GATE_NOTE = ("state=RELEASE 才触发深度 parse 校验；"
                     "state=DRAFT 走浅校验 => 用 DRAFT 判内容正确是假安全")

# ★ 校验器是 fail-fast：每个节点只报**第一条**缺失属性。
# 实测（打地鼠）：DATA_MAPPING 节点依次只报 type -> javaType -> type -> name，
# 补齐一个才暴露下一个，从不一次列全。=> 本地必须一次校验完，不能靠反复试。
PARSER_IS_FAIL_FAST = True

# ★ endNode.value 的真实契约（RELEASE 暴露）
# 报错路径 root.endNode.value.value 会逐层下钻：
#   value=None                          -> "root.endNode.value.value"
#   value={type:CONSTANT}               -> "root.endNode.value.value.type" (DATA_INVALID)
#   value={type:SelectParam, selectParam 缺 dtoType} -> "....selectParam.dtoType"
# 合法值：type="SelectParam" 且 selectParam.dtoType 非空（LIVE：补 dtoType 后该错消失）。
# 全库对照（4734 行 data_schema 扫描）：endNode.value.type 仅出现 {null, SelectParam, Expression}
#   其中 SelectParam 72 行；同 paramType 下 null 亦可 => 无强绑定。
# 判据：**paramType 非空时 value 必须有值**；value 非空时 type 必须是下列之一。
END_NODE_VALUE_TYPES: tuple[str, ...] = ("SelectParam", "Expression")

# ★ RETRIEVE_ARRAY.sortParams 元素契约（RELEASE 暴露；全库仅 4 行样本）
# 设计器真实形态 = {"sortType": "ASC|DESC", "attrType": <完整属性对象>}
# 陷阱：attrType 给**字符串**报 NOT_OBJECT；给对象但缺 sortType 报 PROPERTY_IS_REQUIRED。
SORT_PARAM_REQUIRED_KEYS: tuple[str, ...] = ("sortType", "attrType")
SORT_PARAM_ATTRTYPE_REQUIRED_KEYS: tuple[str, ...] = ("id", "name", "dataType", "type", "javaType")

# ★ mappingRule.row holder 的**完整**必填集（本轮 LIVE 修正上一轮 CFR 推断）
# 上一轮只写了 path 元素的 4 键；RELEASE 实测 **holder 自身也需要**这 4 键：
#   row.targetField / row.value.reference 各自缺 name/dataType/type/javaType 会被报出。
# 补齐 holder 后 check=True errors=0（LIVE PASS）。
MAPPING_HOLDER_REQUIRED_KEYS: tuple[str, ...] = ("name", "dataType", "type", "javaType")


def validate_release_readiness(dto: dict) -> list:
    """发布前置校验（RELEASE 闸门真正会检查的那批）。返回错误列表，空 = 可发布。"""
    errs = []
    if not isinstance(dto, dict):
        return ["dto 不是对象"]
    if str(dto.get("state") or "").upper() != "RELEASE":
        errs.append("state 非 RELEASE：checkSchema/update 会静默返回 check=true 但**不发布**（闸门不触发）")
    ds_raw = dto.get("dataSchema")
    if not ds_raw:
        return errs + ["dataSchema 为空：RELEASE 校验无从进行"]
    import json as _json
    try:
        ds = _json.loads(ds_raw) if isinstance(ds_raw, str) else ds_raw
    except Exception as e:
        return errs + ["dataSchema 不是合法 JSON: %s" % e]
    en = ds.get("endNode") or {}
    if en.get("paramType") and not en.get("value"):
        errs.append("endNode.paramType 非空但 value 为空 -> root.endNode.value.value")
    v = en.get("value")
    if isinstance(v, dict):
        if v.get("type") not in END_NODE_VALUE_TYPES:
            errs.append("endNode.value.type=%r 不在 %s" % (v.get("type"), END_NODE_VALUE_TYPES))
        sp = v.get("selectParam")
        if v.get("type") == "SelectParam" and isinstance(sp, dict) and not sp.get("dtoType"):
            errs.append("endNode.value.selectParam 缺 dtoType（RELEASE 报 selectParam.dtoType）")
    for n in ds.get("nodes") or []:
        nid = n.get("nodeId")
        if n.get("actionType") == "RETRIEVE_ARRAY":
            for i, sp in enumerate(n.get("sortParams") or []):
                if not isinstance(sp, dict):
                    errs.append("%s.sortParams[%d] 必须是对象" % (nid, i)); continue
                for k in SORT_PARAM_REQUIRED_KEYS:
                    if not sp.get(k):
                        errs.append("%s.sortParams[%d] 缺 %r" % (nid, i, k))
                at = sp.get("attrType")
                if isinstance(at, str):
                    errs.append("%s.sortParams[%d].attrType 是字符串 -> NOT_OBJECT" % (nid, i))
                elif isinstance(at, dict):
                    for k in SORT_PARAM_ATTRTYPE_REQUIRED_KEYS:
                        if not at.get(k):
                            errs.append("%s.sortParams[%d].attrType 缺 %r" % (nid, i, k))
        if n.get("actionType") == "DATA_MAPPING":
            mr = n.get("mappingRule") or {}
            for k in MAPPING_RULE_REQUIRED_KEYS:
                if k not in mr:
                    errs.append("%s.mappingRule 缺 %r" % (nid, k))
            for r, row in enumerate(mr.get("mappingRows") or []):
                for hname, holder in (("targetField", row.get("targetField")),
                                      ("value.reference", (row.get("value") or {}).get("reference"))):
                    if not isinstance(holder, dict):
                        continue
                    for k in MAPPING_HOLDER_REQUIRED_KEYS:
                        if not holder.get(k):
                            errs.append("%s.mappingRows[%d].%s 缺 holder 必填 %r" % (nid, r, hname, k))
                    for j, el in enumerate(holder.get("path") or []):
                        for k in MAPPING_HOLDER_REQUIRED_KEYS:
                            if not el.get(k):
                                errs.append("%s.mappingRows[%d].%s.path[%d] 缺 %r" % (nid, r, hname, j, k))
    return errs


# =====================================================================
# 第三十一轮 LIVE 新增：04003(WARN) 的**掩蔽机制** + SERVICE 型三态 + holder javaType 真因
# 证据等级：LIVE（REST 实测）+ VERIFIED_STATIC_BYTECODE（CFR udc-biz/udc-common 5.3.517）
# =====================================================================

# **发现 1（本轮最重要）：`UDC_CE_MICRO_FLOW_04003` 是检测掩蔽器，不是普通提示。**
# CFR CheckUtils.parallelDetection(:430-479)：
#   if (dto.enableLastVersionMetadata() && lastVersionMicroFlowMap.containsKey(dto.getId())) {
#       dto = lastVersionMicroFlowMap.get(dto.getId()); nodeContext.setLastVersionMicroFlow(true); }
#   ...
#   if (MicroFlowDataStateEnum.RELEASE == dto.getState()) { <按 type 分派深度校验> }
#   else { CheckUtils.warn(..., DRAFT_MICRO_FLOW); }   <- DRAFT 直接短路，不做任何深度校验
# -> state=DRAFT 的微流程只产出一条 04003 WARN，其内部真实缺陷（DTO_ATTR_DELETE / ENTITY_DELETE /
#    ILLEGAL_DATA_SYSTEM / OUT_OF_SCOPE / NOT_MATCH ...）全部不报。
# LIVE 实证（test2，微流程 1524985498115296151「小爪标品事件监听」）：
#   state=DRAFT   -> ERROR=0 / WARN=2（04003x2，看起来"只差保存"）
#   state=RELEASE -> ERROR=10 / WARN=1（10 条 04004 全部现形）
# 还原（POST /udc/microflow/update）后回到 ERROR=0 / WARN=2。
# => 铁律：不得把 04003 当作"未保存、无风险"处理；先 RELEASE 把深度校验跑出来再判内容正确。
DRAFT_WARN_MASKS_DEEP_VALIDATION: bool = True
DRAFT_WARN_CODE: str = "UDC_CE_MICRO_FLOW_04003"

# 深度校验按 type 分派（同一 switch 的证据）：
RELEASE_VALIDATION_DISPATCH_BY_TYPE: dict = {
    "FRONTEND": "MicroFlowFrontEndService.detection",
    "FUNCTION": "MicroFlowFrontEndService.detection",
    "ENTITY_RULE": "sourceId 为空则完全跳过（continue）；否则 check",
    "其他（含 SERVICE / CUSTOM）": "CheckUtils.check（全局深度 parse 校验）",
}

# **发现 2：MicroFlowTypeEnum.SERVICE 并非"永不可能发布"。**
# CFR（udc-common-5.3.517，本轮反编译）com/seeyon/udc/common/enums/MicroFlowTypeEnum.java：
#     SERVICE(0), FRONTEND(1), ENTITY_RULE(2), CUSTOM(3), FUNCTION(4)
#   BACKEND_TYPES  = {SERVICE, CUSTOM}
#   FRONTEND_TYPES = {FRONTEND, FUNCTION}
# MicroFlowAppService.setServiceMfToDraft(:926) 只影响 create/update 两个入口：
#     if (MicroFlowTypeEnum.SERVICE.equals(dto.getType())) dto.setState(DRAFT);
# checkSchemaAndUpdate(:330) 不调用 setServiceMfToDraft —— 它只做
#     if (RELEASE.equals(dto.getState())) { checkSchema -> ... -> update }
# -> SERVICE 型可以经 checkSchema/update 发布（旧结论只覆盖 create/update 入口，不够）。
# LIVE：微流程 1524985498115296151（type=SERVICE, state=10/DRAFT）经 checkSchema/update 后
#       state 落库为 20/RELEASE —— 证明 SERVICE 型可发布，DRAFT 是历史遗留而非不可变约束。
MICRO_FLOW_TYPE_CODES: dict = {
    "SERVICE": 0, "FRONTEND": 1, "ENTITY_RULE": 2, "CUSTOM": 3, "FUNCTION": 4,
}
MICRO_FLOW_DATA_STATES: dict = {"DRAFT": 10, "RELEASE": 20}
SERVICE_TYPE_CAN_BE_RELEASED: bool = True
SERVICE_DRAFT_FORCED_ONLY_BY_CREATE_AND_UPDATE: bool = True

# **发现 3：04004 的真实触发点 = DATA_MAPPING path 元素的 dataType<->javaType 不配对。**
# CFR CheckUtils.check:625/663/670/677 报 ENTITY_DELETE / DTO_ATTR_DELETE。
# LIVE（微流程 1524985498115296151，6 个 path 元素中 4 个不配对）：
#   expNum dataType=INTEGER javaType=java.lang.String  -> 2 条（targetField + value.reference 各一）
#   expFlag dataType=BOOLEAN javaType=java.lang.String  -> 2 条
#   经 components/udc/data_type_java_type.normalize_holder_java_types 修正 4 处后，
#   这 4 条消失（10 -> 6）；余 6 条属实体/属性级删除与数据体系问题（另一根因族，未闭合）。
# => 判据：DATA_MAPPING holder 的 path[] 元素也必须过 data_type_java_type 配对校验
#   （此前只查 holder 自身 4 键必填；path 元素只查必填、不查配对 => 真因被漏）。
MAPPING_PATH_ELEMENTS_NEED_JAVA_TYPE_PAIRING: bool = True
LIVE_04004_FROM_MAPPING_PATH_PAIRING: int = 4


# =====================================================================
# 第三十二轮 LIVE 新增：04004 最后 1 条的**真因 = endNode.value.selectParam.outputName 必须指向
# `context.put()` 实际注册的变量名（= 触发点 output.javaType 去掉所有 "."）**
# 证据等级：LIVE（同一条微流程 4 次发布 A/B）+ VERIFIED_STATIC_BYTECODE（CFR udc-biz 5.3.517）
# =====================================================================
#
# 【CFR：变量名的唯一权威定义处】
#   CheckUtils.detectionTrigger:1461-1471（BusinessEventTrigger 分支）
#     MicroFlowParameterDefDto output = trigger.getOutput();
#     variableBo.setName(output.getJavaType().replace(".", ""));          // :1468
#     context.put(output.getJavaType().replace(".", ""), variableBo);     // :1471
#   => context 里的键**不是** output.name（`_FLOW_OUTPUT_evt1` / `_BUSINESS_EVENT_xxxxxx`），
#      而是 javaType 的**去点全串**（例：`xzhExp950795.com.seeyon.udc.common.event.AfterUpdateEvent`
#      -> `xzhExp950795comseeyonudccommoneventAfterUpdateEvent`）。
#
# 【CFR：谁拿这个键去查】
#   MicroFlowComponentUtils.checkSelectParam:912
#     if (!CheckUtils.checkScope(nodeInfo, selectParam.getOutputName(), context)) -> OUT_OF_SCOPE
#   CheckUtils.checkScope:1266-1284
#     MicroFlowVariableBo variableBo = context.get(selectParamOutputName);
#     if (variableBo == null) return false;                 // 键查不到 = 立即 OUT_OF_SCOPE
#     variableBo.getNodeIds().forEach(nodeId -> { if (nodeInfo.getNodePath().contains(nodeId)) flag=true; });
#   => **只有 outputName 参与查表**；nodeInfo.getNodePath() 是 `NodeUtils.getNodePath`（:234-241）在 **parse 期**
#      写进 schema 的 `"nodePath":"root.MFEndNode"`，**不是** RequestBody 里的字段，也不由 selectParam 提供。
#      trigger 注册的 nodeId 字面量是 `"root"`（:1463），而 endNode 的 nodePath 也以 `root` 开头
#      => contains 判据恒真，只要 **outputName 命中键**即可通过。
#
# 【LIVE 隔离实验（决定性，非推断）】微流程 1524985498115296151「小爪标品事件监听」（type=SERVICE）
#   统一 RELEASE 发布，只改 endNode.value.selectParam 的四个字符串字段：
#     X 组（对照，上一轮的状态）：outputName=<去点 javaType>，name=path=key=`_FLOW_OUTPUT_evt1`（占位）
#                                  -> ERROR=0 / WARN=1，**该微流程不再出现**（残留 04004 清零）✅
#     Y 组（canonical 四键一致）：所有键都 = 去点 javaType（key = outputName + 原始 javaType）
#                                  -> ERROR=0 / WARN=1 ✅（同样通过）
#   而上一轮失败态（outputName=`_FLOW_OUTPUT_evt1`）-> ERROR=10，含 1 条
#     route=`MFEndNode_&_value` / `OUT_OF_SCOPE`（"前序节点发生变更请重新选择(事件数据)"）。
#   => **判据收敛为一元**：`endNode.value.selectParam.outputName` 必须是 `trigger.output.javaType.replace(".","")`。
#      `name`/`path`/`key` 在本判据里**既不参与查表也不被校验**（X 组带占位值仍全绿）——
#      这**更正**了本轮早先「需要四键一致」的猜测。
#
# 【与 4 条 holder 不变量并列的完整 04004 真因族（全部已 LIVE 收口）】
#   1) messageInfo.eventDataFullName  = **DTO fullName**（`<base>.dto.<Cap>Dto`）  [CheckUtils.check:1427-1431]
#   2) messageInfo.eventMfCustomDtoName = `<实体短名>.<eventClassName>`（**两键不可互换**）  [同上:1433-1435]
#   3) DATA_MAPPING holder 的 `name` 不可占位、`id` 必须 `<DTOFQN>.<attr>`  [DataMappingActivity checkTargetFieldList]
#   4) mappingRule.javaType 必须 = 目标 DTO FQN（不能是 java.lang.Object）  [DataMappingActivity:173]
#   5) ★ 本轮：endNode.value.selectParam.outputName = trigger.output.javaType 去点全串
#
# 证据锚点：CFR CheckUtils.detectionTrigger:1461-1471 / checkScope:1266-1284 / NodeUtils.getNodePath:234-241
#           / MicroFlowComponentUtils.checkSelectParam:902-915 / MicroFlowOutputValueBo.checkEndNodeValue:98-113
END_NODE_SELECT_PARAM_OUTPUT_NAME_IS_CONTEXT_KEY: bool = True

# context 变量名公式（唯一权威）：CFR CheckUtils:1471
def trigger_output_context_key(java_type: str) -> str:
    """trigger.output.javaType -> NodeContext 变量名（去点全串）。CFR CheckUtils:1471。"""
    return (java_type or "").replace(".", "")

# endNode.value.selectParam 中**参与查表**的字段只有一个；其余为 UI 回显/级联载体。
SELECT_PARAM_SCOPE_RESOLVING_KEYS: tuple = ("outputName",)
SELECT_PARAM_DISPLAY_ONLY_KEYS: tuple = ("name", "path", "key")


def validate_end_node_scope(dto: dict) -> list:
    """校验 endNode.value 的 SelectParam 能否在 NodeContext 里解析到（防 OUT_OF_SCOPE 04004）。

    只校验唯一被判据使用的 outputName（LIVE 隔离实验 X 组证明 name/path/key 不参与）。
    """
    import json as _json
    errs = []
    if not isinstance(dto, dict):
        return ["dto 不是对象"]
    ds = dto.get("dataSchema")
    try:
        ds = _json.loads(ds) if isinstance(ds, str) else ds
    except Exception as e:
        return ["dataSchema 不是合法 JSON: %s" % e]
    if not isinstance(ds, dict):
        return ["dataSchema 不是对象"]
    end = ds.get("endNode") or {}
    val = end.get("value") if isinstance(end, dict) else None
    if not isinstance(val, dict) or val.get("type") != "SelectParam":
        return errs
    sp = val.get("selectParam")
    if not isinstance(sp, dict):
        return errs
    trig = ds.get("trigger") or {}
    if trig.get("type") != "BUSINESS_EVENT":
        return errs   # 变量名公式仅对 BusinessEventTrigger 经 CFR 证实
    jt = (trig.get("output") or {}).get("javaType")
    if not jt:
        errs.append("trigger.output.javaType 为空：无法推导 context 变量名")
        return errs
    expected = trigger_output_context_key(jt)
    got = sp.get("outputName")
    if got != expected:
        errs.append(
            "endNode.value.selectParam.outputName=%r 与 context 注册键 %r 不一致 -> "
            "RELEASE 报 MFEndNode_&_value / OUT_OF_SCOPE（前序节点发生变更请重新选择）" % (got, expected))
    return errs


# ---------------------------------------------------------------------
# 第二轮 LIVE 复核（本仓第三十三轮）：同一微流程 A/B 两臂复现，附**负控**
# 证据等级：LIVE（每臂 REST findById + MySQL udc_microflow_info.state 双面确认 state=20/RELEASE）
# ---------------------------------------------------------------------
# A 臂（正）：outputName = 去点 FQN，name/path/key 全为占位 `_FLOW_OUTPUT_evt1`
#   -> checkSchema/update check:true errors:0；state=20；该微流程**从检测面消失**
# B 臂（负控）：只把 outputName 改回 `_FLOW_OUTPUT_evt1`（name/path/key 不变）
#   -> checkSchema/update 仍 check:true errors:0；state=20；检测面 **ERROR=1**
#       code=UDC_MICRO_FLOW_04004 route=MFEndNode_&_value
#       msg=「结束:前序节点发生变更请重新选择(事件数据)」
# ⇒ 唯一自变量 = outputName ⇒ 一元判据经**负控**确认（非仅正例）。
LIVE_END_NODE_AB_VERTICAL_SLICE: dict = {
    "micro_flow_id": "1524985498115296151",
    "caption": "小爪标品事件监听",
    "trigger_output_java_type": "xzhExp950795.com.seeyon.udc.common.event.AfterUpdateEvent",
    "positive": {"output_name": "xzhExp950795comseeyonudccommoneventAfterUpdateEvent",
                 "error_count": 0, "micro_flow_present_in_detection": False},
    "negative_control": {"output_name": "_FLOW_OUTPUT_evt1",
                         "error_count": 1, "code": "UDC_MICRO_FLOW_04004",
                         "route": "MFEndNode_&_value",
                         "message": "结束:前序节点发生变更请重新选择(事件数据)"},
}
# checkSchema 在两臂**都**是 check:true errors:0 ⇒ 浅校验不覆盖本判据（必须 RELEASE + 检测面观测）
END_NODE_SCOPE_IS_INVISIBLE_TO_CHECK_SCHEMA: bool = True


# ======================================================================
# 第四十四轮：04004「依赖应用已删除」= appName 未跨接（单变量 2×3 臂 LIVE）
# 证据等级：LIVE（REST checkSchema/update + 检测面 status/code + MySQL state 三面）
# ----------------------------------------------------------------------
# 现象对象：微流程 -1014184770817921434「小爪标准微流程-全节点流转(最终)」
#   检测面：ERROR=1  UDC_MICRO_FLOW_04004  element=['微流程入参']  message='微流程入参:依赖应用已删除'
#   该 ERROR 只有在**非 DRAFT**（RELEASE）时可见 —— DRAFT 会被 04003 短路掩蔽
#   （见 draft-warn-masking-mechanism.md）。
#
# CFR（udc-biz 5.3.517，com/seeyon/udc/microflow/util/CheckUtils.java）：
#   check():282-287  仅当 triggerType == MANUAL 时对 **input** 调 detectionInputOutput
#   check():294-297  对 **output** 恒调 detectionInputOutput
#   detectionInputOutput():315-341
#       boolean b = parameterDefDto.getInApp().booleanValue();   // ← 主判据就是 inApp
#       inApp == true  -> 本应用资源，走 detectionStructure（此处不查 appName）
#       inApp == false -> detectionApp(parameterDefDto.getAppName(), ..., "app")  // ← 抛点
#   detectionApp():543-556  detectionEnum == GLOBAL 时：
#       if (appNameSet.contains(appName)) break;   // 表内 -> 放行
#       else error(APP_DELETE)                     // 表外 -> '依赖应用已删除'
#   appNameSet 来源 ImmutableNodeContext.from():174
#       = udc_dependent_application 全部 dep_app_name 的集合（取自元数据面）
#   ★ inApp 是 **Boolean 包装类型**：键缺失 = null ⇒ NPE 风险 / 实测走非 inApp 分支
#     ⇒ 「键缺失」与「显式 false」在检测面上**同分支**（下 B/E 两臂同结论，实测）。
#
# LIVE 单变量矩阵（每次只改一个键，arm 间互相反向验证；检测面以 do/detection-state status
# 轮询到非 doing 再读 search/detection；DB 以 udc_microflow_info.state / data_schema 回读）：
#   臂                          input.inApp  input.appName  检测面(本对象)                    DB state
#   E0 原状                       键缺失        本应用       ERROR 04004「依赖应用已删除」        20
#   E1 inApp=true                 显式 true    本应用       ERROR 清除 (err 1->0)              20  ✅
#   B  inApp=false                显式 false   本应用       ERROR 04004「依赖应用已删除」        20  ← 复现
#   C  inApp=false                false        'bpm'        换码: 04004「OpenApi标识不匹配」     20  ← 换病不治病
#   D  inApp=缺失 + appName=null   键缺失        null        **假干净**（state 被压回 10 → 04003 掩蔽）
#   R  还原为原状                  键缺失        本应用       ERROR 04004 复现（可逆）            20  ✅
#
# E1 为真实修复：appName 已经是本应用，但 inApp 缺键 ⇒ 参数被当「外部应用」参数 ⇒
# 本应用 appName 不在 udc_dependent_application 里（该表只有外部应用）⇒ APP_DELETE。
# 显式声明 inApp=true 即声明「本应用资源」，绕过 appName 查询 ⇒ ERROR 清零。
# ★ 通用规则：**微流程 input/output 的 appName 必须落在依赖应用表内**；
#   本应用资源必须用 inApp=true 表达，绝不能靠 appName 表达。
INPUT_OUTPUT_APPNAME_MUST_BE_REGISTERED_DEPENDENT_APP: bool = True
INPUT_OUTPUT_APPNAME_TABLE: str = "udc_dependent_application.dep_app_name"
INPUT_OUTPUT_INAPP_IS_BOOLEAN_WRAPPER: bool = True   # 键缺失==null⇒非 inApp 分支（非 NPE 于 input 支）
INPUT_OUTPUT_DEP_DETECTION_ONLY_NOT_IN_TABLE: bool = True   # ★ 只有 GLOBAL 检测枚举会抛
# ★ 廉价判据（无需 RELEASE）：把每个参数按 inApp + appName 逐条过一遍这张支票
def input_output_detection_branch(param: dict | None) -> str:
    """复刻 CheckUtils.detectionInputOutput():316 的分支选择（只看 inApp）。"""
    if not isinstance(param, dict):
        return "absent"
    return "inapp" if param.get("inApp") is True else "external"


def validate_input_output_dependency(param: dict | None, dep_app_names, *,
                                     is_real_global: bool = True,
                                     label: str = "input") -> list[str]:
    """input/output 参数的 appName 跨接校验（GLOBAL 检测枚举下的 APP_DELETE 前置判据）。

    返回问题描述列表；空列表 = 该参数不会触发 APP_DELETE / OpenApi 不匹配。
    """
    problems: list[str] = []
    if not isinstance(param, dict):
        return [f"{label}: 参数体缺失（无法判定 inApp / appName）"]
    branch = input_output_detection_branch(param)
    if branch == "inapp":
        return problems
    app_name = param.get("appName")
    if is_real_global:
        if not app_name:
            problems.append(f"{label}: 走外部应用分支但 appName 为空 ⇒ 依赖判据无目标（且 APP_DELETE/OpenApi 判据都无从成立）")
        else:
            known = set(dep_app_names or ())
            if app_name not in known:
                problems.append(
                    f"{label}: appName={app_name!r} 不在依赖应用表 ⇒ UDC_MICRO_FLOW_04004 '依赖应用已删除'"
                    f"（本应用资源应改用 inApp=true，或用已注册的外部应用名）")
    # 注意：appName 跨接通过后仍可能撞 OpenApi 判据（isRealGlobalDetection + SERVICE/CUSTOM ⇒ checkOpenApi），
    # 该判据的完整真值面未取到 ⇒ 只提示，不断言（诚实边界）。
    return problems


# ★★ 竞态观察（第四十四轮，**非本任务写入**）：探测期间该对象被**并发本地工作流**改写
#   （git 91b9d9e 16:42:39「微流程 update 禁硬编码 type/state，恢复全节点流转为标准微流程(SERVICE/0)」）：
#     data_schema 149955 字节 -> 123702 字节；type 3 -> 0；state 20 -> 10。
#   ⇒ 本对象处于**活跃并发编辑**；单对象的 DB 终态不作为本轮交付物（避免与并发工作流互写）。
#   ⇒ 也解释了一个陷阱：**并发写入会让「我改了又不动」看起来像判据失效** —— 先查 git log / DB update_time。
LIVE_R44_CONCURRENT_WRITER: dict = {
    "object": "-1014184770817921434",
    "competing_commit": "91b9d9e",
    "effect": "type 3->0(SERVICE), state 20->10(DRAFT), data_schema 149955->123702 bytes",
    "note": "本任务不再回写该对象；结论以臂级（每臂即时 DB+检测双面）为准",
}
# ★ WARN 计数再次上移：并发工作流把该对象压回 DRAFT 后，它成为第 6 条 04003
#   （构成 04003x5 + 04009x1 -> 04003x6 时 warn=6，实测）。再次坐实 WARN 是移动量。
LIVE_R44_WARN_SNAPSHOT: dict = {"UDC_CE_MICRO_FLOW_04003": 6, "UDC_MICRO_FLOW_04009": 1}
# ★ 臂矩阵常量（供护栏复算；每臂 = 单变量，检测面 + DB state 双面读数）
LIVE_R44_ARMS: dict = {
    "E0_orig_missing_inapp_own_appname": {"input_inApp": None, "input_appName": "datamigration9000000000000000001",
                                          "error_count": 1, "code": "UDC_MICRO_FLOW_04004",
                                          "message_contains": "依赖应用已删除", "db_state": 20},
    "E1_inapp_true": {"input_inApp": True, "input_appName": "datamigration9000000000000000001",
                      "error_count": 0, "db_state": 20},
    "B_inapp_false_own_appname": {"input_inApp": False, "input_appName": "datamigration9000000000000000001",
                                  "error_count": 1, "message_contains": "依赖应用已删除", "db_state": 20},
    "C_inapp_false_bpm_appname": {"input_inApp": False, "input_appName": "bpm",
                                  "error_count": 1, "message_contains": "OpenApi标识不匹配", "db_state": 20},
    "D_missing_inapp_appname_null": {"input_inApp": None, "input_appName": None,
                                     "error_count": 0, "false_clean": True, "db_state": 10},
    "R_restore": {"input_inApp": None, "input_appName": "datamigration9000000000000000001",
                  "error_count": 1, "db_state": 20},
}
# ★ 「假干净」陷阱：臂 D（appName 置 null）检测面 ERROR=0，但**不是**因为配置被修好 ——
#   update 把它压回 DRAFT(10)，04003 短路掩蔽取代了 04004。⇒ 只看 errorCount 会把 D 误判为修复。
R44_FALSE_CLEAN_ARM_IS_DRAFT_MASKED: bool = True
# ★ checkSchema 对两臂（E1 / B）都返回 check:true errors:0 ⇒ 浅校验不覆盖本判据（第 5 个实例）。
R44_APPNAME_DEP_GATE_IS_INVISIBLE_TO_CHECK_SCHEMA: bool = True
