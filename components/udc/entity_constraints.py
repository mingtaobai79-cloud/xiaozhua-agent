"""UDC 实体域 DTO 字段约束模型（后端权威，反编译 udc-common 5.3.517）。

证据：
- com.seeyon.udc.common.dto.EntityDto / EntityBaseDto（EntityDto.java 反编译）
- com.seeyon.udc.common.dto.AttributeDto / BaseUdcAttributeDto
- 约束来自 @NotNull / @NotBlank / @Length(max=...) 注解（javax.validation 权威）

用途：实体/属性创建或更新前的必填与长度校验，避免"形状对、约束错"。
"""
from __future__ import annotations

# ---- 实体创建/更新（EntityBaseDto + EntityDto）----
#   value = (类型, 是否必填, 说明, 最大长度)
ENTITY_FIELDS: dict[str, tuple[str, bool, str, int | None]] = {
    "appId": ("Long", True, "实体所属应用Id", None),
    "name": ("String", True, "实体编码（首字母大写）", 21),
    "caption": ("String", True, "实体名称", 50),
    "description": ("String", False, "描述", 200),
    "tableName": ("String", False, "运行态表名", 100),
    "stereotype": ("String", True, "业务版型 archive/standard/bill/archiveTree/form", None),
    "features": ("String", True, "业务标签 basic/disable/treeEntity", None),
    "searchable": ("Boolean", False, "启用全文检索（默认 true）", None),
    "parentEntityId": ("Long", False, "父实体Id（默认 NULL_ID）", None),
    "entityType": ("String", False, "主/子实体：MASTER_ENTITY/SUB_ENTITY", None),
    "multiplicity": ("EntityRelationMultiplicityEnum", False, "关系基数（默认 ONE2MANY）", None),
    "category": ("EntityCategoryEnum", False, "实体类别（默认 ENTITY）", None),
    "fullName": ("String", False, "实体 fullName", None),
    "dtoFullName": ("String", False, "DTO fullName", None),
    "attributes": ("List<AttributeDto>", False, "属性列表", None),
}
ENTITY_REQUIRED: tuple[str, ...] = tuple(k for k, v in ENTITY_FIELDS.items() if v[1])

# ---- 实体属性创建/更新（BaseUdcAttributeDto + AttributeDto）----
ATTRIBUTE_FIELDS: dict[str, tuple[str, bool, str, int | None]] = {
    "appId": ("Long", True, "所属应用ID", None),
    "entityId": ("Long", True, "实体主键ID", None),
    "name": ("String", True, "属性编码", None),
    "caption": ("String", True, "属性名称", 255),
    "dataType": ("String", True, "数据类型（见 ENTITY_DATA_TYPES）", None),
    "notNull": ("Boolean", False, "是否必填", None),
    "description": ("String", False, "备注", None),
    "minLength": ("Integer", False, "最小长度（≥0）", None),
    "maxLength": ("Integer", False, "最大长度（≥0）", None),
    "decimalDigits": ("Integer", False, "小数位数（≥0）", None),
    "multiSelect": ("Boolean", False, "是否多选", None),
    "relationEntity": ("String", False, "关联实体", None),
    "relationType": ("RelationType", False, "关系", None),
    "dataFormat": ("String", False, "显示格式（DecimalFormat/DateFormat pattern）", 60),
    "attributeGroup": ("String", False, "属性分组", 50),
    "attributeGroupId": ("Long", False, "字段分组id", None),
    "inCondition": ("Boolean", False, "是否参与条件（默认 true）", None),
    "uniqueness": ("Boolean", False, "是否唯一", None),
    "permission": ("Boolean", False, "是否权限控制", None),
    "auditLog": ("Boolean", False, "是否审计", None),
    "enableEncryption": ("Boolean", False, "是否开启加密", None),
    "encryption": ("EncryptionType", False, "加密类型（默认 NOT_ENCRYPTION）", None),
    "enableDesensitization": ("Boolean", False, "是否开启脱敏", None),
    "desensitization": ("MaskType", False, "脱敏类型（默认 None）", None),
    "system": ("Boolean", False, "是否系统属性", None),
    "hidden": ("Boolean", False, "是否隐藏", None),
    "edit": ("Boolean", False, "是否可编辑", None),
    "orderNo": ("Integer", False, "排序号", None),
    "defaultValueIsChange": ("Boolean", False, "默认值是否允许更改", None),
    "defaultValueSystemVariable": ("String", False, "默认值系统变量", None),
    "calculate": ("AttributeCalculateEnum", False, "计算属性 NORMAL/计算/聚合（默认 NORMAL）", None),
    "expressionDesignData": ("String", False, "表达式设计态 schema", None),
    "expressionRuntimeData": ("String", False, "表达式运行态 schema", None),
}
ATTRIBUTE_REQUIRED: tuple[str, ...] = tuple(k for k, v in ATTRIBUTE_FIELDS.items() if v[1])

# ---- 实体属性 dataType 权威值域 ----
# 证据（前端设计器为准，后端 starter 为运行时补充）：
#  - 前端类型注册表 src_redux_store_ts(module-65420) JavaType->dataType：34 种全量
#  - 前端字段模板/值域/中文名 src_redux_store_ts(module-31623) Uz/WB/d4/fU
#  - 后端 boot-starter-datatype 5.3.358 instance/*（15 个运行时基础类型，
#    caption i18n key = com.seeyon.boot.enums.DataType.<NAME>）

# 属性 dataType 全量值域（前端 JavaType->dataType 注册表，34 种）
ENTITY_DATA_TYPES: tuple[str, ...] = (
    "STRING",
    "INTEGER",
    "FLOAT",
    "DOUBLE",
    "LONG",
    "BIGINTEGER",
    "DECIMAL",
    "BOOLEAN",
    "DATE",
    "DATETIME",
    "TIME",
    "ENTITY",
    "OBJECT",
    "DTO",
    "CTPENUM",
    "ENUM",
    "ATTACHMENT",
    "CURRENCY",
    "MULTILINESTRING",
    "IMAGE",
    "ARRAY",
    "SELECTPEOPLE",
    "Serial",
    "CONTENT",
    "OPINIONHANDLER",
    "MAP",
    "ORGGROUP",
    "ASSOCIATEDOCUMENT",
    "METADATA",
    "DATA_SOURCE",
    "DOCUMENTNUMBER",
    "OPINION",
    "ELEMENT",
    "PERSONSELECTOR",
)

# 设计器可新建字段的类型（前端 mG 白名单，9 种：文本/整数/长整数/小数/货币/日期/时间/日期时间/布尔）
ENTITY_CREATABLE_DATA_TYPES: tuple[str, ...] = (
    "STRING",  # 文本
    "INTEGER",  # 整数
    "BIGINTEGER",  # 长整数
    "DECIMAL",  # 小数
    "CURRENCY",  # 货币
    "DATE",  # 日期
    "TIME",  # 时间
    "DATETIME",  # 日期时间
    "BOOLEAN",  # 布尔
)

# 设计器字段模板覆盖的类型（前端 Uz，14 种，含实体/枚举/附件等引用型）
ENTITY_FIELD_DATA_TYPES: tuple[str, ...] = (
    "STRING",
    "MULTILINESTRING",
    "INTEGER",
    "BIGINTEGER",
    "DECIMAL",
    "CURRENCY",
    "DATE",
    "TIME",
    "DATETIME",
    "BOOLEAN",
    "ENUM",
    "CTPENUM",
    "ENTITY",
    "ATTACHMENT",
)

# dataType -> 中文名（前端 d4 Map）
DATA_TYPE_LABELS: dict[str, str] = {
    "ARRAY": "数组",
    "STRING": "文本",
    "MULTILINESTRING": "多行文本",
    "INTEGER": "整数",
    "FLOAT": "单精度浮点数",
    "DOUBLE": "双精度浮点数",
    "LONG": "长整数",
    "BIGINTEGER": "长整数",
    "DECIMAL": "小数",
    "DATE": "日期",
    "TIME": "时间",
    "DATETIME": "日期时间",
    "BOOLEAN": "布尔",
    "ENUM": "选项集",
    "CTPENUM": "枚举",
    "ENTITY": "实体",
    "DTO": "对象",
    "ATTACHMENT": "附件",
    "CURRENCY": "货币",
    "IMAGE": "图片",
    "SELECTPEOPLE": "发布范围",
    "Serial": "政务流水号当前值",
    "CONTENT": "正文",
    "OPINIONHANDLER": "处理意见",
    "MAP": "映射",
    "ORGGROUP": "机构组",
    "ASSOCIATEDOCUMENT": "关联文档",
    "METADATA": "元数据",
    "OBJECT": "对象",
}

# 日期时间类型 -> 显示格式（前端 fU）
DATA_TYPE_DATE_FORMAT: dict[str, str] = {
    "DATETIME": "YYYY-MM-DD HH:mm:ss",
    "DATE": "YYYY-MM-DD",
    "TIME": "HH:mm:ss",
}

# 数值/长度类值域（前端 WB，权威 min/max）
DATA_TYPE_VALUE_RANGE: dict[str, tuple] = {
    "STRING": (0, 4000),
    "MULTILINESTRING": (0, 10000),
    "INTEGER": (-2147483648, 2147483647),
    "BIGINTEGER": ('-9007199254740991', '9007199254740991'),
    "DECIMAL": ('-9007199254740991', '9007199254740991'),
    "CURRENCY": ('-9007199254740991', '9007199254740991'),
}

# dataType -> 运行时渲染控件（前端 py，PC/MOBILE）
DATA_TYPE_WIDGET: dict[str, dict[str, str]] = {
    "STRING": {"PC": "Input", "MOBILE": "Input"},
    "MULTILINESTRING": {"PC": "TextArea", "MOBILE": "TextArea"},
    "INTEGER": {"PC": "InputNumber", "MOBILE": "InputNumber"},
    "BIGINTEGER": {"PC": "Input", "MOBILE": "Input"},
    "DECIMAL": {"PC": "InputNumber", "MOBILE": "InputNumber"},
    "CURRENCY": {"PC": "Currency", "MOBILE": "Currency"},
    "DATE": {"PC": "DatePicker", "MOBILE": "DateTimePicker"},
    "TIME": {"PC": "TimePicker", "MOBILE": "TimePicker"},
    "DATETIME": {"PC": "DatePicker", "MOBILE": "DateTimePicker"},
    "BOOLEAN": {"PC": "Switch", "MOBILE": "Switch"},
    "ENUM": {"PC": "TreeSelect", "MOBILE": "CascaderSelect"},
    "CTPENUM": {"PC": "TreeSelect", "MOBILE": "CascaderSelect"},
    "ATTACHMENT": {"PC": "Attachment", "MOBILE": "Upload"},
    "ENTITY": {"PC": "UdcReference", "MOBILE": "UdcReference"},
    "Serial": {"PC": "Input", "MOBILE": "Input"},
    "CONTENT": {"PC": "UiBusinessContent", "MOBILE": "UiBusinessContent"},
    "DOCUMENTNUMBER": {"PC": "UiBusinessEdocMark", "MOBILE": "UiBusinessEdocMark"},
    "OPINION": {"PC": "UiBusinessEdocOpinionBox", "MOBILE": "UiBusinessEdocOpinionBox"},
    "PERSONSELECTOR": {"PC": "UiBusinessSelectPeople", "MOBILE": "UiBusinessSelectPeople"},
}

# dataType -> 设计器默认属性模板（前端 Uz；省略的键走通用默认）
DATA_TYPE_DEFAULT_TEMPLATE: dict[str, dict] = {
    "STRING": {
        'notNull': False,
        'searchable': False,
        'dataI18n': False,
        'defaultValue': '',
        'defaultValueSystemVariable': '',
        'defaultValueExpressionDesignData': '',
        'defaultValueExpressionRuntimeData': '',
        'expressionDesignData': '',
        'expressionRuntimeData': '',
        'uniqueness': False,
        'minLength': 0,
        'maxLength': 50,
        'patternMessage': '',
        'auditLog': False,
        'enableEncryption': False,
        'enableDesensitization': False,
        'desensitization': 'None',
        'encryption': 'NOT_ENCRYPTION',
        'defaultValueIsChange': True,
        'calculate': 'NORMAL',
        'sourceType': 'ENTITY',
        'columnName': '',
    },
    "MULTILINESTRING": {
        'notNull': False,
        'searchable': False,
        'defaultValue': '',
        'defaultValueSystemVariable': '',
        'defaultValueExpressionDesignData': '',
        'defaultValueExpressionRuntimeData': '',
        'expressionDesignData': '',
        'expressionRuntimeData': '',
        'minLength': 0,
        'maxLength': 300,
        'defaultValueIsChange': True,
        'calculate': 'NORMAL',
        'sourceType': 'ENTITY',
        'columnName': '',
    },
    "INTEGER": {
        'notNull': False,
        'searchable': False,
        'defaultValue': 0,
        'defaultValueSystemVariable': '',
        'defaultValueExpressionDesignData': '',
        'defaultValueExpressionRuntimeData': '',
        'expressionDesignData': '',
        'expressionRuntimeData': '',
        'uniqueness': False,
        'min': '',
        'max': '',
        'auditLog': False,
        'defaultValueIsChange': True,
        'calculate': 'NORMAL',
        'sourceType': 'ENTITY',
        'columnName': '',
    },
    "BIGINTEGER": {
        'notNull': False,
        'searchable': False,
        'defaultValue': '',
        'expressionDesignData': '',
        'expressionRuntimeData': '',
        'uniqueness': False,
        'auditLog': False,
        'min': '',
        'max': '',
        'defaultValueSystemVariable': '',
        'defaultValueExpressionDesignData': '',
        'defaultValueExpressionRuntimeData': '',
        'defaultValueIsChange': True,
        'calculate': 'NORMAL',
        'sourceType': 'ENTITY',
        'columnName': '',
    },
    "DECIMAL": {
        'notNull': False,
        'searchable': False,
        'defaultValue': 0,
        'expressionDesignData': '',
        'expressionRuntimeData': '',
        'auditLog': False,
        'decimalDigits': 2,
        'min': '',
        'max': '',
        'defaultValueSystemVariable': '',
        'defaultValueExpressionDesignData': '',
        'defaultValueExpressionRuntimeData': '',
        'defaultValueIsChange': True,
        'calculate': 'NORMAL',
        'sourceType': 'ENTITY',
        'columnName': '',
    },
    "CURRENCY": {
        'notNull': False,
        'searchable': False,
        'defaultValue': 0,
        'expressionDesignData': '',
        'expressionRuntimeData': '',
        'auditLog': False,
        'decimalDigits': 2,
        'min': '',
        'max': '',
        'defaultValueSystemVariable': '',
        'defaultValueExpressionDesignData': '',
        'defaultValueExpressionRuntimeData': '',
        'defaultValueIsChange': True,
        'calculate': 'NORMAL',
        'sourceType': 'ENTITY',
        'columnName': '',
    },
    "DATE": {
        'notNull': False,
        'searchable': False,
        'defaultValue': '',
        'expressionDesignData': '',
        'expressionRuntimeData': '',
        'auditLog': False,
        'min': '',
        'max': '',
        'defaultValueSystemVariable': '',
        'defaultValueExpressionDesignData': '',
        'defaultValueExpressionRuntimeData': '',
        'defaultValueIsChange': True,
        'calculate': 'NORMAL',
        'sourceType': 'ENTITY',
        'columnName': '',
    },
    "TIME": {
        'notNull': False,
        'searchable': False,
        'defaultValue': '',
        'expressionDesignData': '',
        'expressionRuntimeData': '',
        'auditLog': False,
        'min': '',
        'max': '',
        'defaultValueSystemVariable': '',
        'defaultValueExpressionDesignData': '',
        'defaultValueExpressionRuntimeData': '',
        'defaultValueIsChange': True,
        'calculate': 'NORMAL',
        'sourceType': 'ENTITY',
        'columnName': '',
    },
    "DATETIME": {
        'notNull': False,
        'defaultValue': '',
        'expressionDesignData': '',
        'expressionRuntimeData': '',
        'auditLog': False,
        'min': '',
        'max': '',
        'defaultValueSystemVariable': '',
        'defaultValueExpressionDesignData': '',
        'defaultValueExpressionRuntimeData': '',
        'defaultValueIsChange': True,
        'calculate': 'NORMAL',
        'sourceType': 'ENTITY',
        'columnName': '',
    },
    "BOOLEAN": {
        'expressionDesignData': '',
        'expressionRuntimeData': '',
        'auditLog': False,
        'defaultValue': 'true',
        'defaultValueSystemVariable': '',
        'defaultValueExpressionDesignData': '',
        'defaultValueExpressionRuntimeData': '',
        'defaultValueIsChange': True,
        'calculate': 'NORMAL',
        'sourceType': 'ENTITY',
        'columnName': '',
    },
    "ENUM": {
        'auditLog': False,
        'notNull': False,
        'uniqueness': False,
        'defaultValue': '',
        'multiSelect': False,
        'defaultValueSystemVariable': '',
        'defaultValueExpressionDesignData': '',
        'defaultValueExpressionRuntimeData': '',
        'defaultValueIsChange': True,
        'sourceType': 'ENTITY',
        'relationApp': '',
        'relationEntityName': '',
        'relationEntity': '',
        'relationType': 'Many2OneAssociation',
        'columnName': '',
    },
    "CTPENUM": {
        'auditLog': False,
        'notNull': False,
        'uniqueness': False,
        'multiSelect': False,
        'defaultValueSystemVariable': '',
        'defaultValueExpressionDesignData': '',
        'defaultValueExpressionRuntimeData': '',
        'defaultValueIsChange': True,
        'sourceType': 'ENTITY',
        'relationApp': '',
        'relationEntityName': '',
        'relationEntity': '',
        'relationCode': '',
        'relationType': 'Many2OneAssociation',
        'columnName': '',
    },
    "ENTITY": {
        'auditLog': False,
        'notNull': False,
        'uniqueness': False,
        'defaultValue': '',
        'multiSelect': False,
        'defaultValueSystemVariable': '',
        'defaultValueExpressionDesignData': '',
        'defaultValueExpressionRuntimeData': '',
        'defaultValueIsChange': True,
        'sourceType': 'ENTITY',
        'relationType': 'Many2OneAssociation',
        'relationApp': '',
        'relationEntityName': '',
        'relationEntity': '',
        'relationEntityCategory': None,
        'columnName': '',
    },
    "ATTACHMENT": {
        'auditLog': False,
        'notNull': False,
        'searchable': False,
        'multiSelect': True,
        'sourceType': 'ENTITY',
        'columnName': '',
    },
}

# ---- 属性字段操作类型（AttributeActionType）----
ATTRIBUTE_ACTIONS: dict[str, int] = {"ADD": 0, "UPDATE": 1, "DELETE": 2, "DEFAULT": 3}

# ---- 实体版型（stereotype / 业务版型）----
ENTITY_STEREOTYPES: tuple[str, ...] = ("archive", "standard", "bill", "archiveTree", "form")
# ---- 业务标签 features ----
ENTITY_FEATURES: tuple[str, ...] = ("basic", "disable", "treeEntity")
# ---- 实体类别（★权威 EntityCategoryEnum，extmetadata 5.3.318 反编译：6 种+code）----
#   ENTITY(0) 普通实体 / EXT(1) 扩展实体 / EXT_GLOBAL(2) 全局扩展 /
#   THIRD(3) 三方实体 / COMPONENT_ENTITY(4) 组件实体 / BASIC_DATA(5) 基础数据
ENTITY_CATEGORIES: tuple[str, ...] = (
    "ENTITY", "EXT", "EXT_GLOBAL", "THIRD", "COMPONENT_ENTITY", "BASIC_DATA")
ENTITY_CATEGORY_CODES: dict[str, int] = {
    "ENTITY": 0, "EXT": 1, "EXT_GLOBAL": 2, "THIRD": 3,
    "COMPONENT_ENTITY": 4, "BASIC_DATA": 5,
}
# ---- 关系基数（EntityRelationMultiplicityEnum，权威 2 种）----
ENTITY_MULTIPLICITY: tuple[str, ...] = ("ONE2ONE", "ONE2MANY")
# ---- 属性计算类型（AttributeCalculateEnum，权威 3 种+code）----
ATTRIBUTE_CALCULATE_TYPES: tuple[str, ...] = ("NORMAL", "COMPUTE", "AGGREGATION")
ATTRIBUTE_CALCULATE_CODES: dict[str, int] = {"NORMAL": 0, "COMPUTE": 1, "AGGREGATION": 2}
# ---- 属性来源（AttributeSourceTypeEnum，权威 5 种+code）----
ATTRIBUTE_SOURCE_TYPES: tuple[str, ...] = (
    "ENTITY", "ATTRIBUTESET", "SYSTEM_ATTRIBUTE_SET", "SYSTEM", "EXT")
ATTRIBUTE_SOURCE_CODES: dict[str, int] = {
    "ENTITY": 0, "ATTRIBUTESET": 1, "SYSTEM_ATTRIBUTE_SET": 2, "SYSTEM": 4, "EXT": 5,
}
# ---- 页面来源（PageSourceTypeEnum，权威 4 种+code）----
PAGE_SOURCE_TYPES: tuple[str, ...] = ("DESIGNER", "PRESET", "COPY", "TEMPLATE")
PAGE_SOURCE_CODES: dict[str, int] = {"DESIGNER": 0, "PRESET": 1, "COPY": 2, "TEMPLATE": 3}
# ---- 页面类型（MedaDataPageTypeEnum，权威 14 种+code）----
PAGE_META_TYPES: tuple[str, ...] = (
    "PORTAL", "WELCOME", "REPORT_FORM", "DETAIL", "LIST", "APPROVAL", "PORTLET",
    "SEARCH_LIST", "EDIT_LIST", "LIST_DETAIL", "ASSIST_INFO", "OTHER", "LAYOUT", "SUBPAGE")
PAGE_META_CODES: dict[str, int] = {
    "PORTAL": 1, "WELCOME": 2, "REPORT_FORM": 3, "DETAIL": 4, "LIST": 5,
    "APPROVAL": 6, "PORTLET": 7, "SEARCH_LIST": 8, "EDIT_LIST": 9,
    "LIST_DETAIL": 10, "ASSIST_INFO": 11, "OTHER": 12, "LAYOUT": 14, "SUBPAGE": 13,
}
# ---- 打开方式（OpenWayEnum）----
OPEN_WAYS: tuple[str, ...] = ("REFRESH", "NEW_PAGE")
# ---- 依赖应用类型（DependentAppTypeEnum，5 种+code+中文名）----
DEPENDENT_APP_TYPES: dict[str, tuple[int, str]] = {
    "SERVICE": (0, "应用依赖"), "STARTER": (1, "后端组件"),
    "FROM": (2, "表单应用"), "FRONTEND": (3, "前端组件"), "PLATFORM": (4, "平台"),
}


def validate_entity(body: dict) -> list[str]:
    """校验实体创建/更新入参的必填与长度（空=通过）。"""
    errs = []
    for f in ENTITY_REQUIRED:
        v = body.get(f)
        if v is None or v == "":
            errs.append(f"Entity 缺必填字段 {f}（{ENTITY_FIELDS[f][2]}）")
    for f, (typ, req, desc, maxlen) in ENTITY_FIELDS.items():
        if maxlen and isinstance(body.get(f), str) and len(body[f]) > maxlen:
            errs.append(f"Entity.{f} 长度 {len(body[f])} 超限 {maxlen}")
    return errs


def validate_attribute(body: dict) -> list[str]:
    """校验实体属性创建/更新入参的必填与长度（空=通过）。"""
    errs = []
    for f in ATTRIBUTE_REQUIRED:
        v = body.get(f)
        if v is None or v == "":
            errs.append(f"Attribute 缺必填字段 {f}（{ATTRIBUTE_FIELDS[f][2]}）")
    for f, (typ, req, desc, maxlen) in ATTRIBUTE_FIELDS.items():
        if maxlen and isinstance(body.get(f), str) and len(body[f]) > maxlen:
            errs.append(f"Attribute.{f} 长度 {len(body[f])} 超限 {maxlen}")
    for f in ("minLength", "maxLength", "decimalDigits"):
        v = body.get(f)
        if isinstance(v, int) and v < 0:
            errs.append(f"Attribute.{f} 须 ≥0，实为 {v}")
    errs.extend(validate_attribute_datatype(body))
    return errs


# dataType -> 该类型允许携带的约束属性（由前端 Uz 模板反推的“类型-属性矩阵”）
DATA_TYPE_ALLOWED_ATTRS: dict[str, frozenset] = {
    "STRING": frozenset({"minLength", "maxLength", "uniqueness", "searchable", "dataFormat", "patternMessage"}),
    "MULTILINESTRING": frozenset({"minLength", "maxLength"}),
    "INTEGER": frozenset({"min", "max", "uniqueness"}),
    "BIGINTEGER": frozenset({"min", "max", "uniqueness"}),
    "DECIMAL": frozenset({"min", "max", "decimalDigits"}),
    "CURRENCY": frozenset({"min", "max", "decimalDigits"}),
    "DATE": frozenset({"min", "max"}),
    "TIME": frozenset({"min", "max"}),
    "DATETIME": frozenset({"min", "max"}),
    "BOOLEAN": frozenset(),
    "ENUM": frozenset({"multiSelect", "uniqueness", "relationType", "relationApp", "relationEntityName", "relationEntity"}),
    "CTPENUM": frozenset({"multiSelect", "uniqueness", "relationType", "relationApp", "relationEntityName", "relationEntity", "relationCode"}),
    "ENTITY": frozenset({"multiSelect", "uniqueness", "relationType", "relationApp", "relationEntityName", "relationEntity"}),
    "ATTACHMENT": frozenset({"multiSelect", "searchable"}),
}


def validate_attribute_datatype(body: dict) -> list[str]:
    """校验 dataType 值域、类型-属性交叉、数值/长度值域（空=通过）。"""
    errs: list[str] = []
    dt = body.get("dataType")
    if not dt:
        return errs
    if dt not in ENTITY_DATA_TYPES:
        errs.append(f"Attribute.dataType '{dt}' 不在权威值域（见 ENTITY_DATA_TYPES）")
        return errs
    # 类型-属性交叉：不允许的属性若有非空值则报错
    allowed = DATA_TYPE_ALLOWED_ATTRS.get(dt)
    if allowed is not None:
        for f in ("minLength", "maxLength", "min", "max", "decimalDigits",
                  "multiSelect", "relationType", "relationEntity", "patternMessage"):
            v = body.get(f)
            if f not in allowed and v not in (None, "", False, 0):
                errs.append(f"Attribute.dataType={dt} 不支持属性 {f}={v!r}")
    # 值域校验
    if dt in ("STRING", "MULTILINESTRING"):
        rng = DATA_TYPE_VALUE_RANGE.get(dt)
        ml = body.get("maxLength")
        if rng and isinstance(ml, int) and ml > rng[1]:
            errs.append(f"Attribute.maxLength {ml} 超 {dt} 值域上限 {rng[1]}")
    if dt in ("INTEGER", "BIGINTEGER", "DECIMAL", "CURRENCY"):
        rng = DATA_TYPE_VALUE_RANGE[dt]
        for k in ("min", "max"):
            v = body.get(k)
            if v in (None, ""):
                continue
            try:
                n = float(v)
            except (TypeError, ValueError):
                errs.append(f"Attribute.{k} 非数值：{v!r}")
                continue
            lo, hi = float(rng[0]), float(rng[1])
            if n < lo or n > hi:
                errs.append(f"Attribute.{k}={v} 超 {dt} 值域 [{rng[0]}, {rng[1]}]")
    if dt in ("DECIMAL", "CURRENCY"):
        dd = body.get("decimalDigits")
        if isinstance(dd, int) and dd > 6:
            errs.append(f"Attribute.decimalDigits {dd} 过大（前端默认 2，上限建议 ≤6）")
    if dt in ("ENUM", "CTPENUM", "ENTITY") and not body.get("relationType"):
        errs.append(f"Attribute.dataType={dt} 需 relationType（默认 Many2OneAssociation）")
    return errs
