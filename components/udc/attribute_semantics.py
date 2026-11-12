"""实体字段（Attribute）语义模型 —— 默认值/参照/多选/唯一性 用法分层固化。

证据分层铁律（两层证据强度不同，绝不互套）：
  L1 装配面（源码行号证据，UDC-MAINLINE-AUDIT §5，AttributeService.java）：
     - 默认值六件套（:298-332）：defaultValue / defaultValueCaption /
       defaultValueExpressionDesignData / defaultValueExpressionRuntimeData /
       defaultValueSystemVariable / defaultValueIsChange
     - 多选人员族 = dataType:ENTITY + relationType:Many2OneAssociation +
       relationApp + relationEntity + multiSelect=true
     - 实体装配单独加载 属性/索引/实体规则标志（:1245-1259, :1350-1376, :1408-1425）
     - 实体规则标志来自 microFlowService.loadHasRuleEntityId(appId)，
       按 VALIDATE / DEFAULT_VALUE / ASSIGN_VALUE 区分 —— 字段 defaultValue ≠ 实体规则默认值
  L2 create REST 受键面（LIVE 探针证据，xiaozhua-udc-design-time-build skill）：
     - 已证白名单：multiSelect / relationType / relationApp / relationEntity / uniqueness
       （deployment.py _ATTR_SEMANTIC_KEYS 同源）
     - 六件套在 create 面是否受键 = **UNVERIFIED**（未实测；本模型不冒充已证）

组件面（前端 bundle 注册证据）：
  - 多选人员实际渲染组件 = UiBusinessSelectPeople（不是自定义 UserSelect）
  - 参照类组件 = UdcReference / 关系字段 schema
  - 枚举字段 dataType=ENUM；选项集=CtpEnum 另一族（DATADICT 审计：UDC_ENUM 模块码标签是"选项集"）

关系形态（勿混两套）：
  - 设计态装配字符串形态：relationType=Many2OneAssociation（源码证据）
  - LIVE 建属性数字形态：relationType=1（deployment.py 回读 multi_select=1 同源）
  两套都登记，宿主按通道选用，模型不擅自归一。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCHEMA_ID = "udc.construction.attribute-semantics.v1"

# ---------------------------------------------------------------- 值域（分层登记）

# L1：默认值六件套（AttributeService.java:298-332 装配面字段全集）
DEFAULT_VALUE_KEYS: tuple[str, ...] = (
    "defaultValue",
    "defaultValueCaption",
    "defaultValueExpressionDesignData",
    "defaultValueExpressionRuntimeData",
    "defaultValueSystemVariable",
    "defaultValueIsChange",
)

# L2：create REST 已证受键白名单（与 deployment.py._ATTR_SEMANTIC_KEYS 同源，双处一致）
CREATE_ACCEPTED_SEMANTIC_KEYS: tuple[str, ...] = (
    "multiSelect", "relationType", "relationApp", "relationEntity", "uniqueness",
)

# 关系类型两套形态（登记不合并）
RELATION_TYPE_STRING = "Many2OneAssociation"     # 装配面（源码）
RELATION_TYPE_NUMERIC_LIVE = 1                  # create/回读面（LIVE multi_select=1 同 app 数字形态）

# 多选人员族标准组合（MAINLINE §5，LIVE 建后回读证实）
MULTI_SELECT_PEOPLE_COMBO: dict[str, Any] = {
    "dataType": "ENTITY",
    "relationType": RELATION_TYPE_STRING,
    "relationApp": "organization",
    "relationEntity": "com.seeyon.organization.domain.core.entity.OrgMember",
    "multiSelect": True,
}

# 前端组件登记（bundle 证据）
PEOPLE_COMPONENT = "UiBusinessSelectPeople"
REFERENCE_COMPONENTS = ("UdcReference",)

# 实体规则组（microFlowService.loadHasRuleEntityId；字段默认值≠此组）
ENTITY_RULE_FLAGS: tuple[str, ...] = ("VALIDATE", "DEFAULT_VALUE", "ASSIGN_VALUE")

# dataType 值域（deployment.py DATATYPES 同源快照，勿漂移；引用不复制语义）
DATATYPES = ("ENTITY", "DATETIME", "ENUM", "STRING", "MULTILINESTRING",
             "BOOLEAN", "BIGINTEGER", "INTEGER", "DECIMAL", "DATE", "Serial")

# bundle 权威 dataType 枚举（module 65420 `pe` 逐字，35 值；与上方 deployment 快照
# **非同源**——快照是已落库子集，此处是前端枚举全集，两处独立登记勿互相覆盖）。
# 证据：src_redux_store_ts module 65420 `!function(e){e.String="STRING",…}`
BUNDLE_DATATYPE_ENUM: dict[str, str] = {
    "String": "STRING", "Integer": "INTEGER", "Float": "FLOAT", "Double": "DOUBLE",
    "Long": "LONG", "BigInteger": "BIGINTEGER", "Decimal": "DECIMAL", "Boolean": "BOOLEAN",
    "Date": "DATE", "DateTime": "DATETIME", "Time": "TIME", "Entity": "ENTITY",
    "Object": "OBJECT", "Dto": "DTO", "CtpEnum": "CTPENUM", "Enum": "ENUM",
    "Attachment": "ATTACHMENT", "Currency": "CURRENCY", "MultilineString": "MULTILINESTRING",
    "Image": "IMAGE", "Array": "ARRAY", "Selectpeople": "SELECTPEOPLE", "Serial": "Serial",
    "Content": "CONTENT", "Opinionhandler": "OPINIONHANDLER", "Map": "MAP",
    "OrgGroup": "ORGGROUP", "AssociateDocument": "ASSOCIATEDOCUMENT", "METADATA": "METADATA",
    "DATA_SOURCE": "DATA_SOURCE", "Documentnumber": "DOCUMENTNUMBER", "Opinion": "OPINION",
    "ELEMENT": "ELEMENT", "PERSONSELECTOR": "PERSONSELECTOR",
}
# 事件 eventDataType 取值（§2.8.2① 组件 77200 `d.pe.Object` → "OBJECT"）
EVENT_DATA_TYPE_OBJECT = "OBJECT"


# ---------------------------------------------------------------- 模型

@dataclass
class AttributeSemantics:
    """一个字段的全部语义面声明（哪层有证据、哪层 UNVERIFIED 显式登记）。"""
    name: str
    caption: str = ""
    data_type: str = "STRING"
    default_value: dict[str, Any] = field(default_factory=dict)   # 六件套子集
    relation: dict[str, Any] = field(default_factory=dict)        # relationType/App/Entity
    multi_select: bool | None = None
    uniqueness: bool | None = None
    note: str = ""

    def validate(self) -> dict[str, Any]:
        errors: list[str] = []
        unknowns: list[str] = []
        if self.data_type not in DATATYPES:
            errors.append(f"dataType={self.data_type!r} 不在实测值域（DATADICT/169实体快照）")
        # 默认值键：六件套之外的键 = 未知键（create 面六件套本身也 UNVERIFIED）
        for k in self.default_value:
            if k not in DEFAULT_VALUE_KEYS:
                errors.append(f"defaultValue 键 {k!r} 不在六件套 {DEFAULT_VALUE_KEYS}")
            else:
                unknowns.append(
                    f"create REST 受键 {k!r}=UNVERIFIED（装配面有证据、create 面未实测；宿主先取证再提交）")
        # 多选人员组合校验
        if self.multi_select:
            if self.data_type != "ENTITY":
                errors.append(f"multiSelect=True 须 dataType=ENTITY（多选=多选关联，不是文本数组）")
            rt = self.relation.get("relationType")
            if rt not in (RELATION_TYPE_STRING, RELATION_TYPE_NUMERIC_LIVE):
                errors.append(f"multiSelect=True 缺 relationType（两套登记形态：{RELATION_TYPE_STRING!r} 或 {RELATION_TYPE_NUMERIC_LIVE}）")
            if not self.relation.get("relationEntity"):
                errors.append("multiSelect=True 缺 relationEntity（参照实体全名）")
        # uniqueness Boolean 纪律（字符串报 BOOT_3002，skill 证据）
        if self.uniqueness is not None and not isinstance(self.uniqueness, bool):
            errors.append(f"uniqueness 须 Boolean，实际 {type(self.uniqueness).__name__}（BOOT_3002 教训）")
        return {
            "schema": SCHEMA_ID, "name": self.name,
            "status": "FAIL" if errors else ("UNVERIFIED" if unknowns else "PASS"),
            "errors": errors, "unknowns": unknowns,
            "create_body_keys_allowed": list(CREATE_ACCEPTED_SEMANTIC_KEYS),
            "component": PEOPLE_COMPONENT if (self.multi_select and self.relation.get("relationApp") == "organization") else None,
        }


def build_attribute_plan(sem: AttributeSemantics) -> dict[str, Any]:
    """输出给宿主的分面提交计划：
    create 面只放 L2 已证键；六件套放 plan_only（等取证后宿主补带）。"""
    result = sem.validate()
    create_body: dict[str, Any] = {"name": sem.name, "caption": sem.caption or sem.name,
                                   "dataType": sem.data_type}
    if sem.multi_select is not None:
        create_body["multiSelect"] = sem.multi_select
    for k in ("relationType", "relationApp", "relationEntity"):
        if k in sem.relation:
            create_body[k] = sem.relation[k]
    if sem.uniqueness is not None:
        create_body["uniqueness"] = sem.uniqueness
    result["create_body_proven"] = create_body
    result["plan_only_unverified_keys"] = dict(sem.default_value)  # 六件套暂不进 create body
    return result


def field_default_value_is_not_entity_rule_flag() -> str:
    """对象边界声明（防混用回归）：字段 defaultValue 属性 ≠ 实体规则 DEFAULT_VALUE 组。"""
    return ("实体规则标志来自 microFlowService.loadHasRuleEntityId，按 "
            "VALIDATE/DEFAULT_VALUE/ASSIGN_VALUE 区分（EntityService.java:1245-1259 族）；"
            "字段 defaultValue 六件套是属性列语义，两者不互替。")


__all__ = [
    "SCHEMA_ID", "DEFAULT_VALUE_KEYS", "CREATE_ACCEPTED_SEMANTIC_KEYS",
    "RELATION_TYPE_STRING", "RELATION_TYPE_NUMERIC_LIVE", "MULTI_SELECT_PEOPLE_COMBO",
    "PEOPLE_COMPONENT", "REFERENCE_COMPONENTS", "ENTITY_RULE_FLAGS", "DATATYPES",
    "BUNDLE_DATATYPE_ENUM", "EVENT_DATA_TYPE_OBJECT",
    "AttributeSemantics", "build_attribute_plan",
    "field_default_value_is_not_entity_rule_flag",
]
