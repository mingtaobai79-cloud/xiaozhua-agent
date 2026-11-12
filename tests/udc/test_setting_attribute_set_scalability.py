"""设置域 · 字段集 / 扩展实体 的资产落位与契约闸门。

两者都是「父 REST + 子 GraphQL」的混合协议两级结构 ——
这是本轮最重要的发现，必须锁死，防止后人又回到「REST update 带子集合」的死路。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

SETTING = ROOT / "components" / "udc" / "setting"
FACTS = ROOT / "core" / "facts" / "udc" / "setting"


def test_impl_files_exist():
    for name in ("attribute_set_constraints.py", "scalability_constraints.py"):
        assert (SETTING / name).exists(), f"缺实现: {name}"


def test_fact_files_exist():
    for sub in ("attribute-set", "scalability"):
        assert (FACTS / sub / "create.md").exists(), f"缺事实格: {sub}"


# ---------------------------------------------------------------- 核心：混合协议
def test_attribute_set_field_write_is_graphql_not_rest():
    """★ 字段写入走 GraphQL udcEntityAttributePost，不是 REST attributeSet/update。"""
    txt = (FACTS / "attribute-set" / "create.md").read_text(encoding="utf-8")
    assert "udcEntityAttributePost" in txt, "须写明字段写入的真实 GraphQL op"
    assert "两种协议" in txt or "父子两级" in txt, "须点明父 REST / 子 GraphQL"
    assert "REST 父级接口不处理子集合" in txt or "不处理子集合" in txt, \
        "须写明为什么 REST update 带 attributes 无效"

    from components.udc.setting.attribute_set_constraints import (
        build_attribute_field_body, validate_attribute_field_body)
    body = build_attribute_field_body("1", "999", name="probeA", caption="探针A")
    assert body["sourceType"] == "ATTRIBUTESET"
    assert body["entityId"] == "999" and body["sourceId"] == "999"
    assert "0" in body, "页面发的排序占位键是字符串 '0'"
    assert not validate_attribute_field_body(body, set_id="999")


def test_attribute_set_widget_config_is_json_string():
    from components.udc.setting.attribute_set_constraints import (
        build_attribute_field_body, validate_attribute_field_body)
    body = build_attribute_field_body("1", "9", name="a", caption="b")
    assert isinstance(body["widgetConfig"], str), "widgetConfig 必须是 JSON 字符串"
    body["widgetConfig"] = {"pc": "Input"}
    errs = validate_attribute_field_body(body)
    assert any("JSON" in e for e in errs), "传对象要拦"


def test_attribute_set_path_is_camel_case():
    txt = (FACTS / "attribute-set" / "create.md").read_text(encoding="utf-8")
    assert "udc/attributeSet" in txt and "403" in txt
    assert "attribute-group" in txt, "须对比分组的连字符路径"


def test_attribute_set_read_uses_attribute_set_id_key():
    from components.udc.setting.attribute_set_constraints import (
        build_read_attributes_body)
    assert build_read_attributes_body("123") == {"attributeSetId": "123"}
    txt = (FACTS / "attribute-set" / "create.md").read_text(encoding="utf-8")
    assert "UDC_ENTITY_0022" in txt


def test_attribute_set_name_rejects_chinese():
    from components.udc.setting.attribute_set_constraints import (
        build_attribute_field_body, validate_attribute_field_body)
    body = build_attribute_field_body("1", "9", name="中文编码", caption="显示名")
    errs = validate_attribute_field_body(body)
    assert any("中文" in e for e in errs), "字段编码含中文要拦（页面会转拼音）"


def test_attribute_set_rest_body_warns_attributes_ignored():
    from components.udc.setting.attribute_set_constraints import (
        build_attribute_set_body, validate_attribute_set_body)
    b = build_attribute_set_body("1", name="n", caption="c")
    b["attributes"] = [{"name": "x"}]
    errs = validate_attribute_set_body(b)
    assert errs and any("udcEntityAttributePost" in e for e in errs), \
        "父级带 attributes 要指向 GraphQL 正确入口"


# ---------------------------------------------------------------- 扩展实体
def test_scalability_group_write_is_graphql_not_rest():
    """★ 预留组写入走 GraphQL udcScalabilityPost。"""
    txt = (FACTS / "scalability" / "create.md").read_text(encoding="utf-8")
    assert "udcScalabilityPost" in txt, "须写明预留组的真实 GraphQL op"
    assert "不处理子集合" in txt or "两种协议" in txt

    from components.udc.setting.scalability_constraints import (
        build_scalability_group_body, validate_scalability_group_body)
    g = build_scalability_group_body("500", app_id="1", prefix="ext", count=5)
    assert g["optionId"] == "500"
    assert isinstance(g["dataTypeProperties"], str), "dataTypeProperties 是 JSON 字符串"
    assert not validate_scalability_group_body(g, option_id="500")


def test_scalability_path_is_kebab_case():
    txt = (FACTS / "scalability" / "create.md").read_text(encoding="utf-8")
    assert "udc/scalability-option" in txt, "须写明连字符路径"
    from components.udc.setting.scalability_constraints import GLOBAL_APP_ID
    assert GLOBAL_APP_ID == "-1"


def test_scalability_count_limits():
    from components.udc.setting.scalability_constraints import (
        build_scalability_group_body, validate_scalability_group_body,
        COUNT_MAX, COUNT_MAX_UI)
    over_dto = build_scalability_group_body("1", app_id="1", prefix="p",
                                            count=COUNT_MAX + 1)
    assert any(str(COUNT_MAX) in e for e in validate_scalability_group_body(over_dto))
    over_ui = build_scalability_group_body("1", app_id="1", prefix="p",
                                           count=COUNT_MAX_UI + 1)
    assert any("UI" in e for e in validate_scalability_group_body(over_ui))


def test_scalability_rest_body_warns_groups_ignored():
    from components.udc.setting.scalability_constraints import (
        build_scalability_option_body, validate_scalability_option_body)
    b = build_scalability_option_body("1", name="o", caption="方案")
    b["scalabilityDtoList"] = [{"prefix": "p"}]
    errs = validate_scalability_option_body(b)
    assert errs and any("udcScalabilityPost" in e for e in errs)


def test_both_domains_record_the_same_pattern():
    """两个域的「父 REST / 子 GraphQL」结论必须一致写进事实格。"""
    a = (FACTS / "attribute-set" / "create.md").read_text(encoding="utf-8")
    b = (FACTS / "scalability" / "create.md").read_text(encoding="utf-8")
    for txt in (a, b):
        assert "GraphQL" in txt and "REST" in txt
        assert "静默" in txt or "零写入" in txt, "须记录静默失败的坑"
    assert "同一模式" in b or "同一模式" in a, "两处都应指出是同一模式"


def test_facts_do_not_claim_blocked_anymore():
    """两块都已打通，事实格不应再标 BLOCKED（主能力层）。

    ⚠ 2026-10-22 调整：R-E9 里允许出现 BLOCKED-ENV（环境级阻塞，如 CDP 会话过期
    导致 delete 未实发）——那是"没跑"不是"跑不通"，性质与主能力 BLOCKED 不同。
    仍禁止的是把「主能力」（建壳/加组/读）标成 BLOCKED。
    """
    for sub in ("attribute-set", "scalability"):
        txt = (FACTS / sub / "create.md").read_text(encoding="utf-8")
        assert "LIVE PASS" in txt, f"{sub} 须标 LIVE PASS"
        re9 = txt.split("R-E9")[1][:1200] if "R-E9" in txt else ""
        # 主能力行不得是 BLOCKED（BLOCKED-ENV 是环境级，不算）
        for line in re9.splitlines():
            if "| **加" in line or "建壳" in line or "建方案" in line:
                assert "BLOCKED" not in line.replace("BLOCKED-ENV", ""), \
                    f"{sub} 的 R-E9 主能力行不应标 BLOCKED: {line.strip()[:80]}"


# ---------------------------------------------------------------- 类型矩阵
def test_all_18_data_types_supported():
    """字段集支持 18 种 dataType（2026-10-21 实拉 + 全量实测）。"""
    from components.udc.setting.attribute_set_constraints import (
        FIELD_DATA_TYPES, NEEDS_RELATION)
    assert len(FIELD_DATA_TYPES) == 18, f"应 18 种，实际 {len(FIELD_DATA_TYPES)}"
    for t in ("STRING", "MULTILINESTRING", "INTEGER", "BIGINTEGER", "DECIMAL",
              "CURRENCY", "DATE", "TIME", "DATETIME", "BOOLEAN",
              "ENUM", "CTPENUM", "ATTACHMENT", "ENTITY",
              "DOCUMENTNUMBER", "Serial", "OPINION", "CONTENT"):
        assert t in FIELD_DATA_TYPES, f"缺 {t}"
    assert set(NEEDS_RELATION) == {"CTPENUM", "ENUM", "ENTITY"}


def test_field_name_rule_udc_entity_0026():
    """编码必须以字母开头、不能下划线结尾（UDC_ENTITY_0026）。"""
    from components.udc.setting.attribute_set_constraints import (
        build_attribute_field_body, validate_attribute_field_body)
    for bad in ("1abc", "abc_", "_abc", "中文编码"):
        b = build_attribute_field_body("1", "9", name=bad, caption="c")
        errs = validate_attribute_field_body(b)
        assert errs and any("UDC_ENTITY_0026" in e for e in errs), f"{bad} 应被拦"
    ok = build_attribute_field_body("1", "9", name="abc_123", caption="c")
    assert not validate_attribute_field_body(ok)


def test_scalability_supports_10_base_types():
    from components.udc.setting.scalability_constraints import GROUP_DATA_TYPES
    assert len(GROUP_DATA_TYPES) == 10
    for t in ("STRING", "MULTILINESTRING", "INTEGER", "BIGINTEGER", "DECIMAL",
              "CURRENCY", "DATE", "TIME", "DATETIME", "BOOLEAN"):
        assert t in GROUP_DATA_TYPES


def test_scalability_props_are_stringified_json():
    """dataTypeProperties 是字符串化 JSON，值也是字符串。"""
    from components.udc.setting.scalability_constraints import (
        build_scalability_group_body)
    g = build_scalability_group_body("1", app_id="1", prefix="p", count=3)
    assert isinstance(g["dataTypeProperties"], str)
    import json as _j
    parsed = _j.loads(g["dataTypeProperties"])
    # 页面发的形态：minLength 是字符串 "0"，maxLength 是数字 50（照抄页面）
    assert parsed.get("minLength") == "0", "minLength 是字符串"
    assert parsed.get("maxLength") == 50, "maxLength 是数字"


def test_encryption_and_mask_enums_documented():
    """加密/脱敏枚举值必须写进事实格（猜 AES/FULL 会报 BOOT_3002）。"""
    txt = (FACTS / "attribute-set" / "create.md").read_text(encoding="utf-8")
    assert "REVERSIBLE_ENCRYPTION" in txt, "加密枚举须写明"
    assert "DECRYPT_ONLY" in txt
    assert "MaskType" in txt or "Auto(0)" in txt, "脱敏枚举须写明"
    assert "BOOT_3002" in txt, "须保留猜错枚举的证据"


def test_type_capability_matrix_documented():
    """18 种类型的能力矩阵须在事实格里。"""
    txt = (FACTS / "attribute-set" / "create.md").read_text(encoding="utf-8")
    assert "18 种字段类型" in txt
    assert "全量实测结果：18/18 通过" in txt
    assert "字段级配置项全量实测" in txt
    assert "20/20 通过" in txt


def test_decimal_uses_maxlength_not_maxvalue():
    """DECIMAL 精度靠 maxLength，不是 maxValue。"""
    txt = (FACTS / "attribute-set" / "create.md").read_text(encoding="utf-8")
    assert "靠 `maxLength` 表达" in txt or "maxLength" in txt
    assert "UDC_DATATYPE_0006" in txt


# ---------------------------------------------------------------- 系统变量默认值
def test_sysvar_plain_text_is_rejected():
    """纯文本 defaultValueSystemVariable 会让前端 JSON.parse 崩溃。"""
    from components.udc.setting.attribute_set_constraints import validate_sysvar
    errs = validate_sysvar("currentUser")
    assert errs, "纯文本必须被拦"
    assert any("JSON.parse" in e or "白屏" in e for e in errs), "须说明后果"


def test_sysvar_two_valid_formats():
    """格式 A（单 token）与格式 B（ExpressionSaveDto）都必须通过。"""
    from components.udc.setting.attribute_set_constraints import (
        build_sysvar_token, build_sysvar_expression_dto, validate_sysvar)
    a = build_sysvar_token("currentUserId")
    b = build_sysvar_expression_dto("currentUserId")
    assert not validate_sysvar(a), f"格式 A 应通过: {validate_sysvar(a)}"
    assert not validate_sysvar(b), f"格式 B 应通过: {validate_sysvar(b)}"
    import json as _j
    assert _j.loads(a)["type"] == "SYSTEM_VARIABLE"
    assert _j.loads(b)["resultTypeInfo"] == "ENTITY"
    assert isinstance(_j.loads(b)["tokens"], list)


def test_sysvar_unknown_name_raises():
    from components.udc.setting.attribute_set_constraints import build_sysvar_token
    try:
        build_sysvar_token("notExistVar")
        assert False, "未知变量应抛错"
    except ValueError:
        pass


def test_expression_component_fact_exists():
    p = FACTS / "expression-component" / "component.md"
    assert p.exists(), "缺表达式组件事实格"
    txt = p.read_text(encoding="utf-8")
    for op in ("expression/operator/list", "expression/schema", "expression/preset/list"):
        assert op in txt, f"须写明 {op}"
    assert "CONFIG_PARAM" in txt
    assert "131" in txt and "88" in txt, "须写明变量/函数数量"
    assert "idsTuple" in txt, "须写 schema 真实 body 的三个数组"


# ---------------------------------------------------------------- 控件默认值
def test_widget_defaults_cover_all_types():
    """18 种 dataType 都应有默认控件。"""
    from components.udc.setting.attribute_set_constraints import (
        DEFAULT_WIDGETS, FIELD_DATA_TYPES)
    for dt in FIELD_DATA_TYPES:
        assert dt in DEFAULT_WIDGETS, f"{dt} 缺默认控件"


def test_widget_pc_mobile_differ_for_some_types():
    """PC 与移动端控件常不同（DATE/ENUM/ATTACHMENT）。"""
    from components.udc.setting.attribute_set_constraints import DEFAULT_WIDGETS
    assert DEFAULT_WIDGETS["DATE"] == ("DatePicker", "DateTimePicker")
    assert DEFAULT_WIDGETS["DATETIME"] == ("DatePicker", "DateTimePicker")
    assert DEFAULT_WIDGETS["ENUM"] == ("TreeSelect", "CascaderSelect")
    assert DEFAULT_WIDGETS["CTPENUM"] == ("TreeSelect", "CascaderSelect")
    assert DEFAULT_WIDGETS["ATTACHMENT"] == ("Attachment", "Upload")


def test_biginteger_uses_input_not_inputnumber():
    """BIGINTEGER 真实样本是 Input（大整数超 JS 安全范围）。"""
    from components.udc.setting.attribute_set_constraints import DEFAULT_WIDGETS
    assert DEFAULT_WIDGETS["BIGINTEGER"] == ("Input", "Input")


def test_widget_config_generated_by_type():
    from components.udc.setting.attribute_set_constraints import (
        build_widget_config, build_attribute_field_body)
    import json as _j
    assert _j.loads(build_widget_config("DATE"))["pc"] == "DatePicker"
    assert _j.loads(build_widget_config("ENUM"))["pc"] == "TreeSelect"
    assert _j.loads(build_widget_config("BOOLEAN"))["pc"] == "Switch"
    # 构造器自动带
    b = build_attribute_field_body("1", "9", name="f", caption="c", data_type="ENUM")
    assert _j.loads(b["widgetConfig"])["pc"] == "TreeSelect"


def test_widget_fact_documented():
    txt = (FACTS / "attribute-set" / "create.md").read_text(encoding="utf-8")
    assert "widgetConfig 按 dataType" in txt
    assert "UdcReference" in txt and "TreeSelect" in txt
    assert "BIGINTEGER" in txt and "Input" in txt
