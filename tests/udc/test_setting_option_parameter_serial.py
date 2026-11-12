"""设置域 · 选项集 / 参数 / 流水号 的资产落位与契约闸门。

锁住 2026-10-21 落位的结构与关键事实，防止以后被改回去：

  实现   components/udc/setting/{option_set,parameter,serial}_constraints.py
  事实   core/facts/udc/setting/{option-set,parameter,serial}/create.md
  契约   registry 里 udc.option_set.* / udc.parameter.* / udc.serial.*
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

SETTING = ROOT / "components" / "udc" / "setting"
FACTS = ROOT / "core" / "facts" / "udc" / "setting"


# ---------------------------------------------------------------- 落位
def test_impl_files_exist():
    for name in ("option_set_constraints.py", "parameter_constraints.py",
                 "serial_constraints.py"):
        assert (SETTING / name).exists(), f"缺实现: {SETTING / name}"


def test_fact_files_exist():
    for sub in ("option-set", "parameter", "serial"):
        p = FACTS / sub / "create.md"
        assert p.exists(), f"缺事实格: {p}"


# ---------------------------------------------------------------- 选项集
def test_option_set_tables_are_not_enum_tables():
    """选项集落 udc_enum*，绝不能和枚举的 ctp_enum* 混。"""
    txt = (FACTS / "option-set" / "create.md").read_text(encoding="utf-8")
    assert "udc_enum" in txt and "ctp_enum" in txt, "事实格须点明两套表的区别"
    assert "两套" in txt or "完全独立" in txt, "须写明两套表独立、id 不互通"


def test_option_set_operation_prefix_is_udc_udc():
    """选项集的 operation 是 udcUdc* 前缀，不是 udcEnum*。"""
    txt = (FACTS / "option-set" / "create.md").read_text(encoding="utf-8")
    for op in ("udcUdcEnumCategoryPost", "udcUdcEnumPost", "udcUdcEnumItemPost"):
        assert op in txt, f"缺 operation: {op}"
    assert "udcUdcEnumCategorySelectCategoryAndEnumPost" in txt, "缺读接口"


def test_option_set_code_must_be_capitalized():
    """UDC_ENUM_0001：编码首字母必须大写。"""
    txt = (FACTS / "option-set" / "create.md").read_text(encoding="utf-8")
    assert "UDC_ENUM_0001" in txt, "须保留首字母大写的校验码"
    assert "首字母大写" in txt, "须写明首字母大写规则"

    from components.udc.setting.option_set_constraints import (
        build_option_set_body, validate_option_set_body)
    bad = build_option_set_body("1", "2", name="zxjLower", caption="x", category_id="3")
    assert any("大写" in e for e in validate_option_set_body(bad)), "校验器须拦住小写编码"
    ok = build_option_set_body("1", "2", name="ZxjUpper", caption="x", category_id="3")
    assert not validate_option_set_body(ok), "大写编码应通过"


def test_option_set_item_needs_three_slots():
    """选项项 name/caption/code 三个都不能少。"""
    from components.udc.setting.option_set_constraints import (
        build_option_set_item_body, validate_option_set_item_body)
    full = build_option_set_item_body("1", "2", enum_id="3", name="ONE",
                                      caption="选项甲", code=1)
    assert not validate_option_set_item_body(full)
    for key in ("name", "caption"):
        broken = dict(full)
        broken[key] = ""
        assert validate_option_set_item_body(broken), f"缺 {key} 必须被拦住"


def test_option_set_field_category_is_enum():
    """自定义对象里的选项集字段，dataTypeCategory 必须是 ENUM。"""
    from components.udc.setting.option_set_constraints import (
        validate_custom_object_enum_field)
    errs = validate_custom_object_enum_field(
        data_type="3934748939202274853", data_type_category="PRIMITIVE",
        type_="OBJECT", relation_app="8704025620829192834",
        relation_entity="3934748939202274853")
    assert errs and any("ENUM" in e for e in errs), "写成 PRIMITIVE 必须报错"


# ---------------------------------------------------------------- 参数
def test_parameter_operation_has_typo_definition():
    """平台拼写错误 Definiton（少一个 i）必须照抄。"""
    txt = (FACTS / "parameter" / "create.md").read_text(encoding="utf-8")
    assert "udcCtpParameterDefinitonPost" in txt, "缺 create operation"
    assert "Definiton" in txt, "须保留平台拼写"
    assert "拼写错误" in txt, "须说明这是平台拼写错误"


def test_parameter_properties_must_be_object():
    """dataTypeProperties 传字符串必须被本地拦住。"""
    from components.udc.setting.parameter_constraints import (
        build_parameter_body, validate_parameter_body)
    bad = build_parameter_body("1", "2", name="p", caption="参数",
                               data_type="STRING")
    bad["dataTypeProperties"] = '{"minLength":0}'
    errs = validate_parameter_body(bad)
    assert errs and any("对象" in e for e in errs), "字符串形态必须被拦"

    good = build_parameter_body("1", "2", name="p", caption="参数",
                                data_type="STRING")
    assert not validate_parameter_body(good), "默认形态应通过"


# ---------------------------------------------------------------- 流水号
def test_serial_section_types_documented():
    """段类型来自反编译 SerialTypeEnum。"""
    txt = (FACTS / "serial" / "create.md").read_text(encoding="utf-8")
    for name in ("CONSTANT", "CONTEXT", "ENTITY", "SERIAL"):
        assert name in txt, f"须写明段类型枚举 {name}"
    from components.udc.setting.serial_constraints import SERIAL_TYPE
    assert SERIAL_TYPE == {"CONSTANT": 0, "CONTEXT": 1, "ENTITY": 2, "SERIAL": 3}


def test_serial_section_list_field_name():
    """段列表字段名必须是 serialSectionDtoList（反编译实证）。"""
    txt = (FACTS / "serial" / "create.md").read_text(encoding="utf-8")
    assert "serialSectionDtoList" in txt, "须写明真实字段名"
    assert "不校验未知字段" in txt, "须保留「GraphQL 不校验未知字段」这条方法论"
    assert ("逐字节相同" in txt or "猜错和猜对返回完全一样" in txt
            or "无法收敛" in txt), "须写明为什么不能靠猜"

    from components.udc.setting.serial_constraints import (
        build_serial_scheme_body, build_serial_section, validate_serial_scheme_body)
    sec = build_serial_section(type_="SERIAL", size=4, section_rank=1)
    body = build_serial_scheme_body("1", "2", code="S", name="流水", sections=[sec])
    assert "serialSectionDtoList" in body, "构造器必须用真实字段名"
    assert not validate_serial_scheme_body(body), "合法 body 应通过"


def test_serial_dto_field_names_differ_from_db():
    """DTO 用 size/dateType/show，不是 sectionSize/isDateType/isShow。"""
    from components.udc.setting.serial_constraints import build_serial_section
    s = build_serial_section(type_="CONTEXT", size=8, section_rank=1,
                             date_type=True, date_pattern="yyyyMMdd", show=True,
                             flow=True, increase=True)
    assert "size" in s and "sectionSize" not in s, "DTO 字段名是 size"
    assert "dateType" in s and "isDateType" not in s
    assert "show" in s and "isShow" not in s
    assert "flow" in s and "isFlow" not in s
    assert "increase" in s and "isIncrease" not in s


def test_serial_type_uses_rule_type_enum():
    """serialType 用 SerialRuleTypeEnum（APP/BIG/SMALL），不是 SerialTypeEnum。"""
    from components.udc.setting.serial_constraints import (
        build_serial_scheme_body, build_serial_section, validate_serial_scheme_body,
        RULE_TYPE, SERIAL_TYPE)
    assert set(RULE_TYPE) == {"APP", "BIG", "SMALL"}
    assert set(SERIAL_TYPE) == {"CONSTANT", "CONTEXT", "ENTITY", "SERIAL"}
    sec = build_serial_section(type_="SERIAL", size=4, section_rank=1)
    # 正确：APP
    ok = build_serial_scheme_body("1", "2", code="S", name="x", sections=[sec],
                                  serial_type="APP")
    assert not validate_serial_scheme_body(ok)
    # 错误：用了段类型枚举
    bad = build_serial_scheme_body("1", "2", code="S", name="x", sections=[sec],
                                   serial_type="CONSTANT")
    assert any("serialType" in e for e in validate_serial_scheme_body(bad)), \
        "把 SerialTypeEnum 当 serialType 必须被拦住"


def test_serial_rejects_section_size_key():
    """段里用 sectionSize 而不是 size，必须被拦。"""
    from components.udc.setting.serial_constraints import (
        build_serial_scheme_body, build_serial_section, validate_serial_scheme_body)
    sec = build_serial_section(type_="SERIAL", size=4, section_rank=1)
    sec["sectionSize"] = sec.pop("size")
    body = build_serial_scheme_body("1", "2", code="S", name="x", sections=[sec])
    errs = validate_serial_scheme_body(body)
    assert any("sectionSize" in e for e in errs), "须提示应该用 size"


def test_serial_code_rejects_chinese():
    from components.udc.setting.serial_constraints import (
        build_serial_scheme_body, build_serial_section, validate_serial_scheme_body)
    sec = build_serial_section(type_="SERIAL", size=4, section_rank=1)
    body = build_serial_scheme_body("1", "2", code="流水号", name="x", sections=[sec])
    assert any("中文" in e for e in validate_serial_scheme_body(body))


def test_serial_is_now_live_not_partial():
    """流水号已经从 PARTIAL 升级为 LIVE PASS，事实格须反映。"""
    txt = (FACTS / "serial" / "create.md").read_text(encoding="utf-8")
    assert "LIVE PASS" in txt, "证据等级须是 LIVE PASS"
    assert "反编译" in txt, "须写明字段名来自反编译"


def test_serial_validator_checks_section_count():
    from components.udc.setting.serial_constraints import (
        build_serial_scheme_body, build_serial_section,
        validate_serial_scheme_body, MAX_SECTIONS)
    sec = build_serial_section(type_="SERIAL", size=4, section_rank=1)
    ok = build_serial_scheme_body("1", "2", code="S", name="流水", sections=[sec])
    assert not validate_serial_scheme_body(ok), "单段应通过"
    too_many = build_serial_scheme_body(
        "1", "2", code="S", name="流水",
        sections=[build_serial_section(type_="SERIAL", size=1, section_rank=i)
                  for i in range(MAX_SECTIONS + 1)])
    errs = validate_serial_scheme_body(too_many)
    assert errs and any(f"1..{MAX_SECTIONS}" in e or "1~12" in e for e in errs), \
        "超 12 段必须被拦"


# ---------------------------------------------------------------- registry
def test_registry_has_setting_domain_contracts():
    from components.platform_operations.registry import UdcOperationRegistry
    reg = UdcOperationRegistry.default()
    for oid in ("udc.option_set.create", "udc.option_set.item.create",
                "udc.parameter.create", "udc.serial.create",
                "udc.serial.delete", "udc.serial.search_page"):
        assert reg.has(oid), f"registry 缺契约: {oid}"
    # 流水号已 LIVE PASS，必须标 OBSERVED（有 LIVE 证据）
    assert reg.get("udc.serial.create").status.name == "OBSERVED", \
        "流水号写面已 LIVE，状态须为 OBSERVED"
    # 且必须写明显式授权
    notes = " ".join(reg.get("udc.serial.create").verification_rules)
    assert "WriteScope" in notes, "写契约须提示 WriteScope"
    assert "serialSectionDtoList" in notes, "须写明真实段列表字段名"
