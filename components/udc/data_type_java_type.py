# -*- coding: utf-8 -*-
"""UDC dataType <-> JavaType 权威配对规则（字节码实证 + 平台样本对账）。

★ 第二十七轮整表重写：原表只含 11 条「固定映射」且把 ENUM/CTPENUM/ENTITY 写成单值，
  被平台真实样本**证伪**（见 §被证伪的旧结论 A/B/C）。本文件为修正后版本。
★ 第二十八轮（当前版本）**修正上一轮 docstring 两处失真**（我自己的账，见 §口径更正）：
  ① 上一轮把抽样口径写成「全库」—— 7666 载体 / 106 假阳 实为
     `app 3289082814923688017 AND state=20 LIMIT 500` 这 500 行样本的口径，**不是全库**；
  ② 上一轮记「重写后 0 假阳」仅在该样本口径成立；**全库**同口径仍有 54 条残差，
     且 54/54 全部落在 **DATA_MAPPING holder 之外**（见 §判据适用范围）。

证据等级与来源（均为被审计构件本体 + 平台自产数据）：
  1. VERIFIED_STATIC_BYTECODE —— udc-common-5.3.517.jar
     sha256 30085724949703b1c2f96a37e72813a6ed9e7b752ebc206c7a47d26afceb30d7
     com/seeyon/udc/common/datatype/instance/*DataType 与 Abstract*DataType 的
     getJavaType()。**只有 8 个类覆写**（javap 逐类复算 getJavaType 命中数）：
       BigIntegerDataType -> Long.class.getCanonicalName()      (java.lang.Long)
       IntegerDataType    -> Integer.class.getCanonicalName()    (java.lang.Integer)
       BooleanDataType    -> Boolean.class.getCanonicalName()    (java.lang.Boolean)
       DecimalDataType    -> BigDecimal.class.getCanonicalName() (java.math.BigDecimal)
       CurrencyDataType   -> BigDecimal.class.getCanonicalName() (java.math.BigDecimal)
       CtpEnumDataType    -> Long.class.getCanonicalName()       (java.lang.Long)
       EntityDataType     -> Long.class.getCanonicalName()       (java.lang.Long)
       EnumDataType       -> String.class.getCanonicalName()     (java.lang.String)
     其余不覆写，走基类：
       AbstractStringDataType#getJavaType -> java.lang.String
         （StringDataType / MultilineStringDataType / **TimeDataType** / AttachmentDataType 经
           AbstractFileDataType）
       AbstractDateDataType#getJavaType   -> java.util.Date（DateDataType / DateTimeDataType）
     ★ TimeDataType extends AbstractStringDataType（javap 类头逐字）⇒ TIME -> java.lang.String

  2. VERIFIED_STATIC_BYTECODE —— 三处独立复算器（udc-biz-5.3.517 / boot-core-5.3.358，CFR）
     a) com/seeyon/udc/common/utils/ExprDataTypeTransferUtil（静态 Map 逐条 put）：
        STRING->String, MULTILINESTRING->String, BOOLEAN->Boolean, CURRENCY->BigDecimal,
        DECIMAL->BigDecimal, INTEGER->Integer, BIGINTEGER->Long, **TIME->String**,
        DATE->Date, DATETIME->Date（未收录者抛「不支持的表达式返回值类型」）
     b) com/seeyon/boot/enums/DataType 枚举本体（code 逐条）：
        STRING(0) INTEGER(1) BIGINTEGER(5) DECIMAL(6) BOOLEAN(7) DATETIME(8) DATE(9) TIME(10)
        ENTITY(11) OBJECT(12) ENUM(13) ATTACHMENT(14) MULTILINESTRING(15) CURRENCY(17)
        CTPENUM(18) ARRAY(20) MAP(21) SORTORDER(22) METADATA(23)
     c) com/seeyon/udc/entity/util/DtoAttributeUtil（类级常量 + getJavaTypeByDtoAttribute）：
        MULTI_SELECT_DATA_TYPES = Sets.newHashSet(DataType.CTPENUM.name(),
                                                  DataType.ENTITY.name(),
                                                  DataType.ATTACHMENT.name());
        getJavaTypeByDtoAttribute 按 dataTypeCategory 三分支：
          PRIMITIVE -> UdcDataTypeUtil.getJavaTypeFullName（走 UdcDataType.getJavaType，即上表 1）
          COMPOSITE -> 原样返回 attributeDto.getDataType()
          ENUM      -> 若是数字则查 javaEnumMap 取 UdcEnumDto.getFullName()，否则原样返回
                       ⇒ **ENUM 不走 AbstractStringDataType**，javaType = 应用自产枚举全名

  3. LIVE 平台样本对账（test2，口径逐条可复算，见 §口径更正）

★ 判据适用范围（**本轮新增，防误用 —— 关键**）：
  本模块 `java_type_mismatches` 的**权威域是微流程 DATA_MAPPING 的 holder**，即
  `nodes[..].mappingRule.mappingRows[].targetField` 与 `.value.reference`
  （因果链见下节：只有这两处会触发 DataMappingActivity 的 DTO_ATTR_CHANGE）。
  微流程文档里**还有形状相似的其它载体**（`leftParam`、`selectParam`、
  `attrs[].value/selectParam`、`attrs[].attrType`、`output`、`value/selectParam`），
  它们的 dataType/javaType/multiSelect 是**页面与控件层的表示**，不遵守本条 DATA_MAPPING 判据。
  若对整篇文档做「见 path 键即校验」的宽口径遍历，会把这批载体一并收进来 -> **非 holder 残差**
  （全库实测 54 条，逐条已核实全部位于 holder 之外、0 条落在 holder 内）。
  => **调用方必须自己保证传入的是 holder**；本模块不猜载体种类（见 is_authoritative_holder）。

★ 被平台样本证伪的旧结论（必须记住，勿再犯）：
  A. 「CTPENUM 恒为 java.lang.Long」—— 错。**多选** CTPENUM = java.lang.String。
     与字节码一致：CTPENUM ∈ MULTI_SELECT_DATA_TYPES。
  B. 「ENTITY 恒为 java.lang.Long」—— 错。**多选** ENTITY = java.lang.String。
     与字节码一致：ENTITY ∈ MULTI_SELECT_DATA_TYPES。
  C. 「ENUM 恒为 java.lang.String」—— 错。ENUM 的 javaType 是**应用自产 Java 枚举全名**
     `com.seeyon.{appName}.enums.{Code}`。
     与字节码一致：DtoAttributeUtil#getJavaTypeByDtoAttribute 的 case ENUM 分支不用 UdcDataTypeUtil。
  D. 「ATTACHMENT 恒为 java.lang.String」—— **成立**，且它是 MULTI_SELECT_DATA_TYPES 成员；
     实测单选/多选**全为 String**。

★ 单/多选切分的 LIVE 实证位点在**条件载体**而非 holder：
  DATA_MAPPING holder（mappingRows）实测**从不携带 `multiSelect` 键**（RELEASE 508/508、
  全库 514/514 均缺失）⇒ 对 CTPENUM/ENTITY 的 holder 而言**判据不可判定，必须放行**。
  单/多选切分被真实数据**确证**的位点是条件/计数器载体（`leftParam` / `selectParam`），
  它们**带** multiSelect 且与上表严格一致（RELEASE 口径实测）：
    leftParam ENTITY   multiSelect=False -> java.lang.Long     152 例
    leftParam ENTITY   multiSelect=True  -> java.lang.String    17 例
    leftParam CTPENUM  multiSelect=False -> java.lang.Long     248 例
    leftParam CTPENUM  multiSelect=True  -> java.lang.String    10 例
    ENUM：无论单/多选，javaType 恒为 `com.seeyon.<app>.enums.<Code>`（多选 ENUM 的 type=ARRAY 亦然）
  => A/B 两条反转由此 **LIVE 证实**（不依赖 holder）。

★ 为什么这是「必需」而不是「建议」（因果链，未变）：
  微流程 DATA_MAPPING 的 row holder（targetField / value.reference）只要 dataType 与 javaType
  不配对，`DataMappingActivity.checkTargetFieldList:369` 与
  `checkReferenceValue -> simpleCheckReference -> checkNotSameType` 就**各自**报一条
  `DTO_ATTR_CHANGE`（MicroFlowParseErrorEnum code 17，见 microflow_parse_errors.py），
  检测面合并成 `UDC_MICRO_FLOW_04004`(ERROR)。=> 一行 holder 写错 javaType 会产生 **2 条** 04004。
  LIVE A/B 单变量实证：holder javaType="java.lang.String"（与 dataType=INTEGER/BOOLEAN 不符）
    -> ERROR=4 / WARN=2，文案恒为 DTO_ATTR_CHANGE；
    仅改这两处 javaType 为 java.lang.Integer / java.lang.Boolean（其余全不动）
    -> ERROR=0 / WARN=2 => 因果闭合。

★ 口径更正（第二十八轮，登记上一轮失真，逐条给真值）：
  | 上一轮措辞 | 实测真值 |
  |---|---|
  | 「全库 7666 个真实 healthholder」 | 7666 = `app 3289082814923688017 AND state=20 LIMIT 500`
  |  | 这 500 行样本内「含 path 键」的宽口径载体数；**全库**同口径为 **28855** |
  | 「旧表假阳 106 个（1.38%）」 | 该 500 行样本口径**确为 106**（复现一致）；全库同口径 **296** |
  | 「重写后 0 假阳」 | 该样本口径确为 **0**；全库同口径 **54**，54/54 全在 holder 之外 |
  | — | **真 holder 口径**（mappingRows）：RELEASE 508 / 全库 514；旧表假阳 **2**、新表 **0** |
  该样本口径 500 行内旧表 106 假阳分布（复现一致）：ENTITY+String 125、CTPENUM+String 49、
  ENUM+枚举全名 30+17、STRING+DTO 全名 15、DECIMAL+None 8 …

未取到 LIVE 样本项（判据已字节码证实，平台样本 0 例；禁止据此反推）：
  * TIME —— 字节码三源一致 => java.lang.String；**全库 4734 条 microflow 内 dataType=TIME 载体 0 例**
            => LIVE 样本维度仍未验证（判据本身为 VERIFIED）。
  * OBJECT/ARRAY/MAP/SORTORDER/METADATA 不是建表字段类型，javaType 由 type 层决定
    （ARRAY->List<%s> / MAP->Map<K,V>，见 MicroFlowAutoCodeJavaTypeResolver#getFullJavaType），不在本表范围。
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# 1. 固定映射（与 multiSelect / 应用无关）—— 字节码直证
# ---------------------------------------------------------------------------
DATA_TYPE_TO_JAVA_TYPE: dict[str, str] = {
    # AbstractStringDataType#getJavaType -> String.class.getCanonicalName()
    "STRING": "java.lang.String",
    "MULTILINESTRING": "java.lang.String",
    # TimeDataType extends AbstractStringDataType（不覆写）★ 字节码三源一致
    "TIME": "java.lang.String",
    # AbstractFileDataType#getJavaType -> String.class.getCanonicalName()
    "ATTACHMENT": "java.lang.String",
    # IntegerDataType#getJavaType -> Integer.class.getCanonicalName()
    "INTEGER": "java.lang.Integer",
    # BooleanDataType#getJavaType -> Boolean.class.getCanonicalName()
    "BOOLEAN": "java.lang.Boolean",
    # BigIntegerDataType#getJavaType -> Long.class.getCanonicalName()  ★ 反直觉
    "BIGINTEGER": "java.lang.Long",
    # DecimalDataType#getJavaType -> BigDecimal.class.getCanonicalName()
    "DECIMAL": "java.math.BigDecimal",
    # CurrencyDataType#getJavaType -> BigDecimal.class.getCanonicalName()
    "CURRENCY": "java.math.BigDecimal",
    # AbstractDateDataType#getJavaType -> Date.class.getCanonicalName()（DATE/DATETIME 共用）
    "DATE": "java.util.Date",
    "DATETIME": "java.util.Date",
}

# ---------------------------------------------------------------------------
# 2. 受 multiSelect 影响的类型（字节码：DtoAttributeUtil.MULTI_SELECT_DATA_TYPES）
# ---------------------------------------------------------------------------
MULTI_SELECT_DATA_TYPES: tuple[str, ...] = ("CTPENUM", "ENTITY", "ATTACHMENT")
# 多选（集合）形态 javaType：LIVE 条件载体 multiSelect=True 全为 String
MULTI_SELECT_JAVA_TYPE: str = "java.lang.String"
# 单选「关联」形态 javaType：LIVE 条件载体 multiSelect=False 全为 Long
SINGLE_RELATION_JAVA_TYPE: str = "java.lang.Long"
# 判据依赖 multiSelect 的类型（键缺失 => 不可判定 => 放行）
MULTI_SELECT_DEPENDENT_DATA_TYPES: tuple[str, ...] = ("CTPENUM", "ENTITY")

# ---------------------------------------------------------------------------
# 3. ENUM：javaType 是应用自产 Java 枚举全名
# ---------------------------------------------------------------------------
ENUM_DATA_TYPE: str = "ENUM"
ENUM_JAVA_TYPE_TEMPLATE: str = "com.seeyon.{app_name}.enums.{code}"
# 简单类型集合：ENUM 的 javaType 落在其中即判为不配对
SIMPLE_JAVA_TYPES: tuple[str, ...] = tuple(sorted(set(DATA_TYPE_TO_JAVA_TYPE.values())))

# ---------------------------------------------------------------------------
# 3b. 判据的权威域（第二十八轮新增；调用方必须据此选择合适的载体）
# ---------------------------------------------------------------------------
# 权威域：微流程 DATA_MAPPING holder 的相对路径
HOLDER_PATH_SUFFIXES: tuple[str, ...] = (
    "mappingRule.mappingRows[].targetField",
    "mappingRule.mappingRows[].value.reference",
)
# 非权威域（形状相似但属页面/控件层表示，不得套用本判据）
NON_HOLDER_CARRIERS: tuple[str, ...] = (
    "leftParam", "selectParam", "attrs[].value/selectParam", "attrs[].attrType",
    "output", "value/selectParam",
)
# 真 holder 实测从不携带 multiSelect（=> CTPENUM/ENTITY 判据不可判定，必须放行）
HOLDER_MULTI_SELECT_ALWAYS_ABSENT: bool = True

# ---------------------------------------------------------------------------
# 4. 反向 / 歧义 / 跨表对账
# ---------------------------------------------------------------------------
JAVA_TYPE_TO_DATA_TYPES: dict[str, tuple[str, ...]] = {}
for _dt, _jt in DATA_TYPE_TO_JAVA_TYPE.items():
    JAVA_TYPE_TO_DATA_TYPES[_jt] = JAVA_TYPE_TO_DATA_TYPES.get(_jt, ()) + (_dt,)

# ★ 第二十八轮改为**推导**（原为手写，实测漏掉 java.lang.Boolean / java.lang.Integer
#   两个只对应单一 dataType 的 javaType；手写表必然漂移，故不再手写）：
#   碰撞表 = 固定映射的反向索引 ∪ 条件类型在两态下的落点。
JAVA_TYPE_COLLISIONS: dict[str, tuple[str, ...]] = {}
for _jt, _dts in JAVA_TYPE_TO_DATA_TYPES.items():
    JAVA_TYPE_COLLISIONS[_jt] = tuple(_dts)
# 条件类型（CTPENUM/ENTITY）按单选/多选两态并入对应 javaType
for _dt in MULTI_SELECT_DEPENDENT_DATA_TYPES:
    for _jt in (MULTI_SELECT_JAVA_TYPE, SINGLE_RELATION_JAVA_TYPE):
        JAVA_TYPE_COLLISIONS.setdefault(_jt, ())
        if _dt not in JAVA_TYPE_COLLISIONS[_jt]:
            JAVA_TYPE_COLLISIONS[_jt] = JAVA_TYPE_COLLISIONS[_jt] + (_dt,)

# 判据已字节码证实、但 LIVE 样本维度 0 例（非 UNVERIFIED 判据）
# CURRENCY 已于第二十八轮取到 LIVE 样本（21 例，全 java.math.BigDecimal）=> 移出本表
LIVE_SAMPLE_MISSING: tuple[str, ...] = ("TIME",)

# DataType 枚举 code（boot-core-5.3.358 CFR）—— 供跨表对账，不参与判据
DATA_TYPE_CODES: dict[str, int] = {
    "STRING": 0, "INTEGER": 1, "BIGINTEGER": 5, "DECIMAL": 6, "BOOLEAN": 7, "DATETIME": 8,
    "DATE": 9, "TIME": 10, "ENTITY": 11, "OBJECT": 12, "ENUM": 13, "ATTACHMENT": 14,
    "MULTILINESTRING": 15, "CURRENCY": 17, "CTPENUM": 18, "ARRAY": 20, "MAP": 21,
    "SORTORDER": 22, "METADATA": 23,
}

# LIVE 对账锚点（可复算口径，第二十八轮实测）


def _norm(dt) -> str:
    return str(dt).strip().upper() if dt else ""


def java_type_for(data_type: str, *, multi_select: bool | None = None,
                  app_name: str | None = None, enum_code: str | None = None) -> str | None:
    """dataType -> 权威 javaType；**不可判定 / 未收录**一律返回 None（禁止猜）。

    multi_select : 载体的 multiSelect 布尔键；None = 键缺失
                   （对 CTPENUM/ENTITY 即不可判定 —— 真 holder 恒缺失，见模块 docstring）
    app_name     : 应用名（ENUM 需要，用于拼 com.seeyon.{app}.enums.{code}）
    enum_code    : ENUM 的枚举编码；缺省时返回 None（不可判定）
    """
    dt = _norm(data_type)
    if not dt:
        return None
    if dt in MULTI_SELECT_DEPENDENT_DATA_TYPES:
        if multi_select is True:
            return MULTI_SELECT_JAVA_TYPE
        if multi_select is False:
            return SINGLE_RELATION_JAVA_TYPE
        return None                      # 键缺失 => 不可判定（fail-open）
    if dt == ENUM_DATA_TYPE:
        if app_name and enum_code:
            return ENUM_JAVA_TYPE_TEMPLATE.format(app_name=app_name, code=enum_code)
        return None                      # 无应用名/编码 => 不可判定
    return DATA_TYPE_TO_JAVA_TYPE.get(dt)


def is_authoritative_holder(relative_path: str) -> bool:
    """判断某载体相对路径是否落在本判据的**权威域**（DATA_MAPPING holder）内。

    只认 mappingRule.mappingRows[].targetField / .value.reference 两处。
    非权威载体（leftParam / selectParam / attrs[..].attrType / output 等）返回 False ——
    它们不遵守 DATA_MAPPING 判据，套用会产生非 holder 残差（全库实测 54 条）。
    """
    p = str(relative_path or "")
    return ("mappingRows[" in p) and (p.endswith("targetField") or p.endswith("reference"))


def java_type_mismatches(field: dict, *, app_name: str | None = None) -> list[str]:
    """校验单个 **DATA_MAPPING holder**（targetField / value.reference）的 dataType<->javaType 配对。

    返回不配对描述列表；空 = 通过。**不可判定项一律放行**（不猜、不假阳）。
    调用方须自行保证传入的是 holder；非 holder 载体请勿传入（见 is_authoritative_holder）。
    """
    if not isinstance(field, dict):
        return []
    dt = _norm(field.get("dataType"))
    if not dt:
        return []
    jt = field.get("javaType")
    ms = field.get("multiSelect")
    if not isinstance(ms, bool):
        ms = None
    # ENUM：javaType 必须是应用枚举全名，不得是简单类型
    if dt == ENUM_DATA_TYPE:
        if jt in (None, ""):
            return ["dataType=ENUM 但 javaType 缺失（应为 com.seeyon.<app>.enums.<Code>）"]
        if str(jt) in SIMPLE_JAVA_TYPES:
            return ["dataType=ENUM 与 javaType=%r 不配对（ENUM 的 javaType 必须是应用"
                    "自产枚举全名 com.seeyon.<app>.enums.<Code>，不是简单类型）" % (jt,)]
        return []
    want = java_type_for(dt, multi_select=ms, app_name=app_name)
    if want is None:
        return []                        # 未收录 / 不可判定 => 放行
    if jt in (None, ""):
        return ["dataType=%s 但 javaType 缺失（应为 %s）" % (dt, want)]
    if jt != want:
        return ["dataType=%s（multiSelect=%s）与 javaType=%r 不配对（应为 %r；"
                "不配对会各报一条 DTO_ATTR_CHANGE -> 04004）" % (dt, ms, jt, want)]
    return []


def normalize_holder_java_types(node: dict, *, app_name: str | None = None) -> int:
    """就地修正 DATA_MAPPING 节点内所有 holder 的 javaType，返回改动数。

    覆盖 row.targetField / row.value.reference 及其 path 元素（递归）。
    **不可判定项跳过**（不猜）。ENUM 的 javaType 无法权威推导时**不置空**（避免破坏既有值）。
    """
    fixed = 0
    if not isinstance(node, dict):
        return 0
    mr = node.get("mappingRule")
    if not isinstance(mr, dict):
        return 0

    def walk(o):
        nonlocal fixed
        if isinstance(o, dict):
            if o.get("dataType"):
                if _norm(o.get("dataType")) == ENUM_DATA_TYPE:
                    pass                       # ENUM 由调用方按应用枚举表补全，本函数不猜
                else:
                    ms = o.get("multiSelect") if isinstance(o.get("multiSelect"), bool) else None
                    want = java_type_for(o.get("dataType"), multi_select=ms, app_name=app_name)
                    if want and o.get("javaType") != want:
                        o["javaType"] = want
                        fixed += 1
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for row in mr.get("mappingRows") or []:
        walk(row.get("targetField"))
        walk((row.get("value") or {}).get("reference"))
    return fixed
