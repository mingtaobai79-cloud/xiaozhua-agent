# -*- coding: utf-8 -*-
"""微流程 parse/校验错误码权威表（MicroFlowParseErrorEnum，CFR udc-biz 5.3.517）。

来源：`com/seeyon/udc/enums/microflow/MicroFlowParseErrorEnum.class`
反编译（CFR 0.152）后把 \\uXXXX 转义还原为中文。
证据等级：VERIFIED_STATIC_BYTECODE。

★ 为什么需要这张表：
  - `UDC_MICRO_FLOW_04004`（ERROR，= `UDC_MICRO_FLOW_NODE_DATA_ERROR`）的检测面
    `message` 文本**就是**这里某个枚举的 message（`CheckUtils.error(...)` 把它塞进
    `ParseResult`，再经 `CheckUtils.quoteDetection` 变成检测条目）。
  - `UDC_CE_MICRO_FLOW_04003`（WARN）的 message **恒为** `DRAFT_MICRO_FLOW[119]`
    （见 `CheckUtils.parallelDetection` 的 else 分支），与微流程内容无关。
  ⇒ 看到检测面文案即可反查枚举名，进而定位校验分支。

注意：**同一 code 数字可对应多个枚举名**（历史追加，如 29/30/31/32/39 各出现两次），
且 code 并非唯一标识 —— 反查请用枚举名或 message 文本，不要用数字。
"""

# 枚举名 -> (code, message)
MICRO_FLOW_PARSE_ERRORS: dict[str, tuple[int, str]] = {
    'OUT_OF_SCOPE': (0, '前序节点发生变更请重新选择'),
    'NOT_MATCH': (1, '数据类型不匹配'),
    'UNIQUE': (2, '值重复'),
    'PROPERTY_IS_REQUIRED': (3, '必填参数未配置，请点击该节点参数设置'),
    'DATA_INVALID': (4, '无效的数据'),
    'UNDEFINED_KEY': (5, '数据结构中找不到这个属性key'),
    'NOT_STRING': (6, '不是文本类型'),
    'NOT_INTEGER': (7, '不是整数类型'),
    'NOT_BIGINTEGER': (8, '不是长整数类型'),
    'NOT_DATE': (9, '不是日期类型'),
    'NOT_BOOLEAN': (10, '不是布尔类型'),
    'NOT_DECIMAL': (11, '不是小数类型'),
    'NOT_ARRAY': (12, '不是多条数据'),
    'NOT_OBJECT': (13, '右值的数据不是单条数据，请检查'),
    'NOT_ENTITY': (14, '不是实体'),
    'NOT_DTO': (15, '对象类型不匹配'),
    'DTO_DELETE': (16, '已配置的对象已删除'),
    'DTO_ATTR_CHANGE': (17, '已配置的对象的属性发生了更改，请检查'),
    'DTO_ATTR_DELETE': (18, '对象中配置的属性已被删除或编码被修改'),
    'ENTITY_DELETE': (19, '实体已删除'),
    'ENTITY_ATTR_CHANGE': (20, '实体属性已更改'),
    'ENTITY_ATTR_DELETE': (21, '实体属性已删除'),
    'PAGE_ELEMENT_DELETE': (22, '页面元素已删除'),
    'NOT_CTP_ENUM': (23, '不是数据库枚举'),
    'EVENT_DELETE': (24, '事件已删除'),
    'EVENT_CHANGE': (25, '事件已改变'),
    'MICRO_FLOW_DELETE': (26, '微流程已删除'),
    'MICRO_FLOW_CHANGE': (27, '微流程已更改'),
    'CUSTOM_ERROR_DELETE': (28, '自定义异常码已删除'),
    'CTP_ENUM_ITEM_DELETE': (29, '枚举项已删除'),
    'CTP_ENUM_DELETE': (30, '枚举已删除'),
    'PAGE_DELETE': (31, '页面已删除'),
    'PAGE_IN_PARAM_CHANGE': (31, '配置的页面入参已不存在'),
    'AFFAIR_VALUE_ONLY_SELECT_PARAM': (32, '该节点参数映射中，只允许选择前序节点中对应的实体对象，请勿使用其他赋值方式'),
    'AFFAIR_VALUE_ONLY_DTO_OR_ENTITY': (39, '该节点的参数映射中，只允许选择前序节点中对应的实体对象或者记录，请勿选择其他数据'),
    'AFFAIR_RECEIVERS_ONLY_SELECT_PARAM': (33, '接收人或者发送人只允许选择前序节点中的关联组织机构数据，不支持其他数据类型'),
    'AFFAIR_RECEIVERS_ONLY_ENTITY': (34, '接收人或者发送人只允许选择前序节点中关联的组织机构数据或者人员ID或者ID列表'),
    'AFFAIR_SENDER_ONLY_ONE': (35, '发送人只允许单选人员'),
    'COUNT_ATTRS_ONLY_ONE': (36, '该列表操作类型计算字段只允许单选！'),
    'CONVERT_NEED_ID_LIST': (37, '该操作只支持长整数列表数据！'),
    'CONVERT_NEED_MULTI_ENTITY': (38, '该操作只支持字段类型为实体或者枚举，并且多选的字段数据！'),
    'APP_DELETE': (39, '依赖应用已删除'),
    'NOT_RELEASE': (40, '调用的微流程不是正式态'),
    'WITHOUT_OUTPUT': (41, '没有定义出参'),
    'WITHOUT_END_NODE': (42, '没有设置出参节点'),
    'MESSAGE_CATEGORY_DELETE': (43, '消息分类已删除'),
    'MESSAGE_LINK_DELETE': (44, '消息链接已删除'),
    'AFFAIR_DELETE': (45, '待办分类已删除'),
    'EVENT_USED': (46, '订阅的业务事件已被其他微流程使用'),
    'NOT_MASTER_ENTITY': (47, '不是根实体对象'),
    'LOOP_CALL': (48, '存在循环调用'),
    'JAVA_TYPE_NOT_SAME': (49, '操作数据选择的列表或者对象和选择的列表对象类型不同！'),
    'LIST_NOT_SUPPORTED_OPEN': (50, '列表数据不支持展开选择里面的元素！'),
    'JAVA_ENUM_ITEM_DELETE': (29, '选项集选项已删除'),
    'JAVA_ENUM_DELETE': (30, '选项集已删除'),
    'EVENT_DATA_ATTR_DELETE': (51, '消息组装的参数已被删除，请删除当前消息后重新配置'),
    'EVENT_DATA_DELETE': (52, '消息的参数已被删除，请删除当前消息后重新配置'),
    'ENUM_NOT_MATCH': (32, '请选择同一个选项集类型进行赋值！'),
    'NOT_ENUM': (53, '该操作只支持字段类型选项集的数据！'),
    'NOT_STR': (54, '该操作只支持文本，或者多选实体，或者多选枚举类型的数据！'),
    'NOT_SUPPORT_ATTR_VALUE_TYPE': (55, '不支持的赋值类型'),
    'CONNECTOR_APP_SERVICE_DELETED': (56, '所选连接器不存在，可能已被删除，或前往连接器配置界面重新发布'),
    'CONNECTOR_METHOD_DELETED': (57, '所选连接器方法不存在，可能已被删除，或前往连接器配置界面重新发布'),
    'APP_SERVICE_METHOD_DELETED': (58, '所选自定义服务方法不存在，可能已被删除，请前往所选应用确认'),
    'SELECTED_METHOD_PARAM_CHANGE': (59, '所选方法的参数已变更，请重新选择该方法'),
    'SELECTED_METHOD_RETURN_VALUE_CHANGE': (60, '所选方法的返回值已变更，请重新选择该方法'),
    'MQ_DELETE': (61, '所选 MQ 消息不存在，可能已被删除，请前往所选应用确认'),
    'DEFAULT_VALUE_CANNOT_BE_MODIFIED': (62, '配置了禁止修改默认值的字段不能被修改'),
    'ENUM_MULTI_SELECT_CHANGE': (63, '选项集字段的类型发生了变更，请检查并修改'),
    'DTO_ATTR_TYPE_CHANGE': (64, '选择的对象的属性类型变更，请检查该属性是需要单条还是列表'),
    'METADATA_DELETE': (65, '微流程配置的的元数据已被删除，请检查是否需要修改'),
    'SCHEDULE_NOT_EXIST': (66, '微流程配置的定时任务在调度中心不存在,请检查并重新配置'),
    'LIST_OPERATION_SUB_LIST_INDEX_LESS_THAN_ONE': (67, '列表操作-获取子列表-获取的开始或者结束条数不能小于1！'),
    'LIST_OPERATION_SUB_LIST_S_GREATER_THAN_E': (68, '列表操作-获取子列表-获取的结束条数不能大于开始条数！'),
    'LIST_OPERATION_PICK_ONE_LESS_THAN_ONE': (70, '列表操作-获取第N条-获取的条数不能小于1'),
    'UNAVAILABLE_SERVICE': (71, '该实体对象不支持该实体节点操作，请重新选择！'),
    'EVENT_SELF_CIRCULATION': (72, '所投递的事件与触发该微流程的事件相同，可能会导致死循环，请检查'),
    'ENTITY_EVENT_SELF_CIRCULATION': (73, '该数据活动可能会导致实体业务事件再次触发该微流程，这将会导致死循环，请检查'),
    'CALL_SERVICE_CIRCULARLY': (74, '请慎重在循环中配置调用了服务的节点，这可能会导致该微流程执行超时'),
    'CONCURRENT_MODIFICATION': (75, '不允许对列表循环中选择的列表进行修改，这将导致并发修改异常'),
    'FRONTEND_MICRO_FLOW_CHANGE': (76, '已调用的页面规则出入参发生了变更，请检查！'),
    'DATA_FLOW_NOT_EXIST': (77, '生单规则已被删除'),
    'PAGE_ELEMENT_DELETE_EXPRESSION': (78, '表达式中使用的页面元素已不存在！'),
    'LIST_OPERATION_PICK_ONE_NOT_NUMBER': (79, '列表操作-获取第N条-需要获取的条目值不是整数，请重新配置'),
    'NOT_MATCH_ENUM': (80, '不是指定的枚举类型'),
    'THIRD_IS_NOT_RELEASE': (81, '第三方实体默认微流程未保存正式态'),
    'PARAM_PATH_IS_NOT_EMPTY': (82, '默认值节点不支持选择子实体'),
    'APP_IS_NOT_EXIST': (83, '选择的实体的应用信息不存在，可能导致构建异常，请重新选择并配置该节点'),
    'ILLEGAL_DATA_SYSTEM': (84, '非法的数据体系，请重新选择来源数据进行映射'),
    'SUBOBJECT_NOT_EXIST': (85, '子对象不存在'),
    'INCONSISTENT_DATA_QUANTITY': (86, '数据量不一致'),
    'UNSUPPORTED_EXPRESSION_OPERATION': (87, '不支持的表达式操作'),
    'ENTITY_OPERATION_CIRCULAR_REFERENCE': (88, '调用的微流程中存在该实体的数据活动'),
    'MAP_KEY_TYPE_MISMATCH': (89, '映射的键类型不匹配'),
    'MAP_VALUE_TYPE_MISMATCH': (90, '映射的值类型不匹配'),
    'EXPRESSION_CONTROL_DATA_EXCEPTION': (100, '表达式控件数据异常，请重新保存表达式'),
    'INCOMPLETE_MAP_CONDITION_DATA': (101, '不完整的过滤条件，请重新选择'),
    'DUPLICATE_ENTITY_EVENT_SUBSCRIPTION': (102, '重复的实体事件订阅'),
    'CTP_PARAMETER_DELETED': (103, '表达式中使用的应用参数信息不存在'),
    'CTP_PARAMETER_TYPE_CHANGED': (104, '表达式中的应用参数信息类型已修改'),
    'CTP_PARAMETER_NAME_CHANGED': (105, '表达式中的应用参数信息名称已修改'),
    'EXPRESSION_CHECK_FAILED': (106, '表达式校验失败'),
    'SUB_MICRO_FLOW_NOT_INCLUDE_PAGE_INFO': (107, '调用的子微流程不包含分页信息'),
    'EXCEEDING_MAX_ALLOWED_NODE_COUNT': (108, '超过允许的最大节点数量，这可能出现意料之外的错误，请将当前微流程重构为多个子微流程'),
    'ABNORMAL_EXPRESSION_STRUCTURE': (109, '表达式结构异常，请重新配置'),
    'HISTORICAL_VERSION_EXPRESSION_EXCEPTION': (110, '历史版本表达式数据异常，请尝试修改，这可能导致潜在的错误'),
    'ATTRIBUTE_CHANGED': (111, '选择的字段信息已被修改，请重新选择字段'),
    'ONLY_ALLOW_SINGLE_SELECTION': (112, '只允许单选'),
    'DATA_SELF_REFERENCE': (113, '数据自引用'),
    'ENTITY_ATTR_DATA_TYPE_CHANGE': (114, '实体属性的数据类型已更改'),
    'ILLEGAL_APPLICATION_SELECTION': (115, '所选应用与当前微流程的OpenApi标识不匹配'),
    'UNSUPPORTED_DATA': (116, '不支持的数据，请更换所选数据'),
    'STALE_DATA': (117, '过时的数据，请重新配置，这可能导致检查失效'),
    'SELECT_AT_LEAST_ONE': (118, '至少选择一个'),
    'DRAFT_MICRO_FLOW': (119, '未保存的微流程或者页面规则，这可能会影响调用'),
    'ALL_CONDITION_END_WITH_ERROR': (120, '所有分支中都配置了自定义错误节点，这将无法正常返回'),
    'UNSUPPORTED_OPERATION': (122, '不支持的操作'),
    'NOT_RECOMMENDED_OPERATION': (123, '不推荐的操作'),
    'RELATION_ENTITY_TYPE_NOT_MATCH': (124, '关联实体类型不匹配'),
    'RELATION_CTP_ENUM_TYPE_NOT_MATCH': (125, '关联枚举类型不匹配'),
    'FRONTEND_MICRO_FLOW_INPUT_CHANGE': (201, '事件绑定的页面规则入参有变更，请重新配置！'),
    'FRONTEND_MICRO_FLOW_INPUT_JAVA_TYPE_CHANGE': (202, '事件绑定的页面规则入参的数据类型变更，请重新配置！'),
    'FRONTEND_MICRO_FLOW_INPUT_TYPE_CHANGE': (203, '事件绑定的页面规则入参对象/列表类型变更，请重新配置！'),
    'FRONTEND_MICRO_FLOW_INPUT_ATTR_NOT_EXIST': (204, '事件绑定的页面规则中入参映射的参数已不存在，请重新配置！'),
    'FRONTEND_MICRO_FLOW_INPUT_ATTR_DATA_TYPE_CHANGE': (205, '事件绑定的页面规则中入参映射的参数数据类型发生变更，请重新配置！'),
    'FRONTEND_MICRO_FLOW_INPUT_ATTR_TYPE_CHANGE': (206, '事件绑定的页面规则中入参映射的对象/列表类型发生变更，请重新配置！'),
    'PAGE_VARIABLE_DATA_TYPE_CHANGE': (207, '使用的页面变量数据类型发生了变更，请重新配置'),
    'PUBLISHED_MICRO_FLOW_CAN_NOT_DRAFT': (208, '已经正式发布的微流程，不允许草稿态发布，请正式保存后再发布'),
    'FRONTEND_MICRO_FLOW_INPUT_ATTR_VALUE_NOT_EXIST': (209, '事件绑定的页面规则中入参映射的值已不存在，请重新选择！'),
    'CONTROL_ACTION_NOT_EXIST': (210, '该控件的控件动作已不支持，请重新选择！'),
    'CONTROL_ACTION_NOT_MULTI': (211, '该控件的控件动作只支持多选模式，请检查页面中该控件的模式！'),
    'NOT_POSITIVE_INTEGER': (212, '调度参数需要是正整数，请检查定时调度配置！'),
    'NOT_RELEASE_FRONTEND': (213, '调用的页面规则不是正式态'),
    'NOT_RELEASE_FUNCTION': (214, '调用的公共页面规则不是正式态'),
    'NOT_APPLICABLE_CONDITION_OPERATOR': (215, '存在和左值类型不适用的条件操作符，请重新选择！'),
    'ILLEGAL_SERVICE_RETURN': (216, '不支持的接口返回参数格式:SingleResponse<List<xxx>>，请联系服务提供方调整！'),
    'PAGE_DATA_SOURCE_HIDDEN_FIELD_DELETE': (217, '数据源配置的隐藏字段已被移除，请重新选择！'),
    'UDC_ENTITY_OPEN_API_DELETE': (218, '所选择的UDC实体未暴露对应节点的OpenApi方法，请检查对应应用中该实体的OpenApi配置'),
    'UDC_ENTITY_ATTR_ATTACHMENT_MULTI_SELECT': (219, '附件的单多选类型已变更，请检查'),
    'FRONTEND_PAGE_RULE_DELETE': (220, '页面规则已删除'),
    'FUNCTION_PAGE_RULE_DELETE': (221, '公共页面规则已删除'),
    'LAST_VERSION_MICRO_FLOW_VERIFICATION_FAILED': (222, '和已启用的微流程配置冲突，请停用或保存并提交当前微流程'),
    'STOP_NODE': (999, '请勿在该节点后配置其他操作'),
    'BUG': (9999, '这是bug联系开发人员！'),
}

# code -> (枚举名, ...)（多对一是常态，见模块 docstring）
MICRO_FLOW_PARSE_ERRORS_BY_CODE: dict[int, tuple[str, ...]] = {}
for _name, (_code, _msg) in MICRO_FLOW_PARSE_ERRORS.items():
    MICRO_FLOW_PARSE_ERRORS_BY_CODE[_code] = MICRO_FLOW_PARSE_ERRORS_BY_CODE.get(_code, ()) + (_name,)

# message -> 枚举名（检测面文案反查）
MICRO_FLOW_PARSE_ERRORS_BY_MESSAGE: dict[str, str] = {
    _msg: _name for _name, (_code, _msg) in MICRO_FLOW_PARSE_ERRORS.items()}

# ---- 本轮 LIVE 打通的两条「检测码 <-> parse 枚举」因果链 ----
# 04004 = ERROR：`CheckUtils.error(...)` 逐条落 `MicroFlowParseErrorEnum` 的 message
DETECTION_ERROR_CODE = "UDC_MICRO_FLOW_04004"
# 04003 = WARN：`CheckUtils.warn(..., DRAFT_MICRO_FLOW)` 的固定文案
DETECTION_DRAFT_WARN_CODE = "UDC_CE_MICRO_FLOW_04003"
DETECTION_DRAFT_WARN_ENUM = "DRAFT_MICRO_FLOW"
DETECTION_DRAFT_WARN_MESSAGE = MICRO_FLOW_PARSE_ERRORS[DETECTION_DRAFT_WARN_ENUM][1]


def enum_of_detection_message(message: str) -> str | None:
    """把检测面 message 反查成 parse 枚举名；未收录返回 None。"""
    return MICRO_FLOW_PARSE_ERRORS_BY_MESSAGE.get((message or '').strip())
