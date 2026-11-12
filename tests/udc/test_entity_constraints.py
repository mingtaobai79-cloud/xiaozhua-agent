"""测试：实体域 DTO 字段约束（后端权威 @NotNull/@NotBlank/@Length）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.entity_constraints import (
    ENTITY_REQUIRED, ATTRIBUTE_REQUIRED, ENTITY_FIELDS, ATTRIBUTE_FIELDS,
    ENTITY_STEREOTYPES, ENTITY_FEATURES, ATTRIBUTE_ACTIONS,
    validate_entity, validate_attribute,
    ENTITY_DATA_TYPES, ENTITY_CREATABLE_DATA_TYPES, ENTITY_FIELD_DATA_TYPES,
    DATA_TYPE_LABELS, DATA_TYPE_DATE_FORMAT, DATA_TYPE_VALUE_RANGE,
    DATA_TYPE_WIDGET, DATA_TYPE_DEFAULT_TEMPLATE,
    ENTITY_CATEGORIES, ENTITY_CATEGORY_CODES, ENTITY_MULTIPLICITY,
    ATTRIBUTE_CALCULATE_TYPES, ATTRIBUTE_CALCULATE_CODES,
    ATTRIBUTE_SOURCE_TYPES, ATTRIBUTE_SOURCE_CODES,
    PAGE_SOURCE_TYPES, PAGE_SOURCE_CODES, PAGE_META_TYPES, PAGE_META_CODES,
    OPEN_WAYS, DEPENDENT_APP_TYPES,
)


def test_entity_required_fields():
    assert set(ENTITY_REQUIRED) == {"appId", "name", "caption", "stereotype", "features"}
    assert ENTITY_FIELDS["name"][3] == 21
    assert ENTITY_FIELDS["caption"][3] == 50


def test_attribute_required_fields():
    assert set(ATTRIBUTE_REQUIRED) == {"appId", "entityId", "name", "caption", "dataType"}
    assert ATTRIBUTE_FIELDS["caption"][3] == 255


def test_validate_entity_reports_missing():
    errs = validate_entity({"appId": 1, "name": "X", "caption": "x"})
    assert any("stereotype" in e for e in errs) and any("features" in e for e in errs)


def test_validate_entity_ok_and_length():
    ok = {"appId": 1, "name": "XzhExp", "caption": "小爪", "stereotype": "standard", "features": "basic"}
    assert validate_entity(ok) == []
    bad = dict(ok, name="A" * 30)
    assert any("超限 21" in e for e in validate_entity(bad))


def test_validate_attribute_reports_missing_and_min():
    errs = validate_attribute({"appId": 1, "entityId": 2, "name": "x"})
    assert any("caption" in e for e in errs) and any("dataType" in e for e in errs)
    ok = {"appId": 1, "entityId": 2, "name": "expText", "caption": "实验文本",
          "dataType": "STRING", "minLength": 0, "maxLength": 100}
    assert validate_attribute(ok) == []
    bad = dict(ok, minLength=-1)
    assert any("须 ≥0" in e for e in validate_attribute(bad))


def test_entity_enums():
    assert "standard" in ENTITY_STEREOTYPES and "archive" in ENTITY_STEREOTYPES
    assert ENTITY_FEATURES == ("basic", "disable", "treeEntity")
    assert ATTRIBUTE_ACTIONS == {"ADD": 0, "UPDATE": 1, "DELETE": 2, "DEFAULT": 3}


def test_extmetadata_enum_domains():
    # ★权威（extmetadata 5.3.318 反编译），修正原先的残缺值域
    # EntityCategoryEnum 6 种（原模型只写了 1 种 "ENTITY"）
    assert ENTITY_CATEGORIES == (
        "ENTITY", "EXT", "EXT_GLOBAL", "THIRD", "COMPONENT_ENTITY", "BASIC_DATA")
    assert ENTITY_CATEGORY_CODES["THIRD"] == 3 and ENTITY_CATEGORY_CODES["BASIC_DATA"] == 5
    # AttributeCalculateEnum 3 种
    assert ATTRIBUTE_CALCULATE_TYPES == ("NORMAL", "COMPUTE", "AGGREGATION")
    # AttributeSourceTypeEnum 5 种（注意 code 跳过 3）
    assert ATTRIBUTE_SOURCE_TYPES == ("ENTITY", "ATTRIBUTESET", "SYSTEM_ATTRIBUTE_SET", "SYSTEM", "EXT")
    assert ATTRIBUTE_SOURCE_CODES["SYSTEM"] == 4
    # PageSourceTypeEnum 4 种
    assert PAGE_SOURCE_TYPES == ("DESIGNER", "PRESET", "COPY", "TEMPLATE")
    # MedaDataPageTypeEnum 14 种
    assert len(PAGE_META_TYPES) == 14
    assert PAGE_META_CODES["LAYOUT"] == 14 and PAGE_META_CODES["SUBPAGE"] == 13
    # OpenWayEnum / DependentAppTypeEnum
    assert OPEN_WAYS == ("REFRESH", "NEW_PAGE")
    assert DEPENDENT_APP_TYPES["STARTER"] == (1, "后端组件")
    assert ENTITY_MULTIPLICITY == ("ONE2ONE", "ONE2MANY")


# ---- dataType 权威值域 / 类型-属性矩阵 / 值域校验（前端设计器注册表 31623/65420）----

def test_data_type_domain_authoritative():
    # 34 种全量值域（前端 JavaType->dataType 注册表）
    assert len(ENTITY_DATA_TYPES) == 34
    for t in ("STRING", "INTEGER", "DECIMAL", "CTPENUM", "PERSONSELECTOR", "METADATA"):
        assert t in ENTITY_DATA_TYPES
    # 设计器可新建的 9 种基础类型白名单
    assert ENTITY_CREATABLE_DATA_TYPES == (
        "STRING", "INTEGER", "BIGINTEGER", "DECIMAL", "CURRENCY", "DATE", "TIME", "DATETIME", "BOOLEAN")
    # 字段模板覆盖 14 种（含引用型）
    assert "ATTACHMENT" in ENTITY_FIELD_DATA_TYPES and "ENTITY" in ENTITY_FIELD_DATA_TYPES


def test_data_type_template_and_range():
    assert DATA_TYPE_DEFAULT_TEMPLATE["STRING"]["maxLength"] == 50
    assert DATA_TYPE_DEFAULT_TEMPLATE["MULTILINESTRING"]["maxLength"] == 300
    assert DATA_TYPE_DEFAULT_TEMPLATE["DECIMAL"]["decimalDigits"] == 2
    assert DATA_TYPE_DEFAULT_TEMPLATE["ATTACHMENT"]["multiSelect"] is True
    assert DATA_TYPE_DEFAULT_TEMPLATE["BOOLEAN"]["defaultValue"] == "true"
    assert DATA_TYPE_VALUE_RANGE["STRING"] == (0, 4000)
    assert DATA_TYPE_VALUE_RANGE["MULTILINESTRING"] == (0, 10000)
    assert DATA_TYPE_VALUE_RANGE["INTEGER"] == (-2147483648, 2147483647)
    assert DATA_TYPE_DATE_FORMAT["DATETIME"] == "YYYY-MM-DD HH:mm:ss"
    assert DATA_TYPE_LABELS["CTPENUM"] == "枚举" and DATA_TYPE_LABELS["ENUM"] == "选项集"
    assert DATA_TYPE_WIDGET["ENTITY"]["PC"] == "UdcReference"


def test_validate_attribute_datatype_rules():
    base = {"appId": 1, "entityId": 2, "name": "f", "caption": "字段"}
    # 未知 dataType
    assert any("不在权威值域" in e for e in validate_attribute(dict(base, dataType="BOGUS")))
    # 值域超限
    assert any("值域上限 4000" in e for e in validate_attribute(dict(base, dataType="STRING", maxLength=5000)))
    assert any("值域 [" in e for e in validate_attribute(dict(base, dataType="INTEGER", max=99999999999)))
    # 类型-属性交叉
    assert any("不支持属性" in e for e in validate_attribute(dict(base, dataType="STRING", decimalDigits=2)))
    # 引用型需 relationType
    assert any("relationType" in e for e in validate_attribute(dict(base, dataType="ENTITY")))
    ok = dict(base, dataType="DECIMAL", decimalDigits=2, min=0, max="9999999")
    assert validate_attribute(ok) == []
