"""设置域 · 导入导出模板 / 二维码 的资产落位与契约闸门。

锁住 2026-10-21 落位的结构与关键事实。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

SETTING = ROOT / "components" / "udc" / "setting"
FACTS = ROOT / "core" / "facts" / "udc" / "setting"


# ---------------------------------------------------------------- 落位
def test_impl_and_facts_exist():
    for name in ("excel_template_constraints.py", "qrcode_constraints.py"):
        assert (SETTING / name).exists(), f"缺实现: {name}"
    for sub in ("excel-template", "qrcode"):
        assert (FACTS / sub / "create.md").exists(), f"缺事实格: {sub}"


# ---------------------------------------------------------------- 导入导出模板
def test_excel_is_rest_not_graphql():
    """导入导出模板走 REST /service/udc/excel/*，不是 GraphQL。"""
    txt = (FACTS / "excel-template" / "create.md").read_text(encoding="utf-8")
    assert "/service/udc/excel/create-template" in txt
    assert "REST" in txt, "须点明是 REST 不是 GraphQL"
    assert "server_404" in txt, "须保留 /service/excel/* 路径错误的证据"


def test_excel_iscustom_gate_documented():
    """isCustom=false 才进 search 列表（反编译实证）。"""
    txt = (FACTS / "excel-template" / "create.md").read_text(encoding="utf-8")
    assert "isCustom" in txt
    assert "search-custom-list-by-conditions" in txt
    assert "强制" in txt or "只查" in txt, "须写明 search 强制 isCustom=false"

    from components.udc.setting.excel_template_constraints import build_template_body
    body = build_template_body("1", "2", name="t", main_full_name="com.seeyon.a.b.C",
                               sheets=[[{"attributeFullName": "com.seeyon.a.b.C.f",
                                         "displayName": "字段"}]])
    # 默认 is_custom 必须是 pure Python bool，可被外部改
    assert isinstance(body["isCustom"], bool)


def test_excel_column_anchor_is_attribute_full_name():
    """列的唯一锚点是 attributeFullName，表头是 displayName。"""
    from components.udc.setting.excel_template_constraints import build_column
    col = build_column("com.seeyon.a.b.C.f1", "编号", data_type="STRING")
    assert col["attributeFullName"] == "com.seeyon.a.b.C.f1"
    assert col["displayName"] == "编号"
    assert col["safetyDto"]["encryption"] == "NOT_ENCRYPTION"


def test_excel_validator_catches_missing_anchor():
    from components.udc.setting.excel_template_constraints import (
        build_template_body, validate_template_body)
    bad_col = {"displayName": "字段"}      # 缺 attributeFullName
    body = build_template_body("1", "2", name="t", main_full_name="com.seeyon.a.b.C",
                               sheets=[[bad_col]])
    errs = validate_template_body(body)
    assert any("attributeFullName" in e for e in errs), "缺锚点必须被拦"


def test_excel_name_length_limit():
    from components.udc.setting.excel_template_constraints import (
        build_template_body, validate_template_body)
    col = {"attributeFullName": "com.seeyon.a.b.C.f", "displayName": "x"}
    body = build_template_body("1", "2", name="x" * 21,
                               main_full_name="com.seeyon.a.b.C", sheets=[[col]])
    assert any("20" in e for e in validate_template_body(body)), "超 20 字必须被拦"


# ---------------------------------------------------------------- 二维码
def test_qrcode_enums_from_decompilation():
    from components.udc.setting.qrcode_constraints import QR_TYPE, LINK_TYPE
    assert QR_TYPE == {"BARCODE": 0, "LINKQRCODE": 1, "FIELDQRCODE": 2, "QRCODE": 3}
    assert LINK_TYPE == {"APP": 0, "CUSTOM": 1}


def test_qrcode_sort_must_be_null_not_empty_dict():
    """sort 传 {} 会 BOOT_3000；必须 null。"""
    from components.udc.setting.qrcode_constraints import build_search_body
    q = build_search_body(app_id="1")
    assert q["sort"] is None, "sort 必须是 None，不能是 {}"
    txt = (FACTS / "qrcode" / "create.md").read_text(encoding="utf-8")
    assert "sort" in txt and "null" in txt, "须写明 sort 必须 null"


def test_qrcode_search_no_page_has_no_sort_key():
    from components.udc.setting.qrcode_constraints import build_search_no_page_body
    q = build_search_no_page_body(app_id="1")
    assert "sort" not in q, "search-no-page 不应带 sort key"


def test_qrcode_validator_requires_value_field_for_field_type():
    from components.udc.setting.qrcode_constraints import (
        build_qr_rule_body, validate_qr_rule_body)
    body = build_qr_rule_body("1", "2", name="qr", entity_full_name="com.seeyon.a.b.C",
                              type_="FIELDQRCODE", value_field_code="")
    errs = validate_qr_rule_body(body)
    assert any("valueFieldCode" in e for e in errs), "FIELDQRCODE 缺 valueFieldCode 必须被拦"


def test_qrcode_validator_requires_path_for_link_type():
    from components.udc.setting.qrcode_constraints import (
        build_qr_rule_body, validate_qr_rule_body)
    body = build_qr_rule_body("1", "2", name="qr", entity_full_name="com.seeyon.a.b.C",
                              type_="LINKQRCODE", value_field_code="")
    errs = validate_qr_rule_body(body)
    assert any("pcPagePath" in e or "mobilePagePath" in e for e in errs)


def test_qrcode_name_length_limit():
    from components.udc.setting.qrcode_constraints import (
        build_qr_rule_body, validate_qr_rule_body)
    body = build_qr_rule_body("1", "2", name="x" * 51,
                              entity_full_name="com.seeyon.a.b.C",
                              type_="QRCODE")
    assert any("50" in e for e in validate_qr_rule_body(body))


# ---------------------------------------------------------------- registry
def test_registry_has_new_setting_contracts():
    from components.platform_operations.registry import UdcOperationRegistry
    reg = UdcOperationRegistry.default()
    for oid in ("setting.excel.template.create", "setting.excel.template.search",
                "setting.excel.template.delete",
                "setting.qrcode.rule.create", "setting.qrcode.rule.search"):
        assert reg.has(oid), f"registry 缺契约: {oid}"
    # 两条关键陷阱必须写进 verification_rules
    ex = " ".join(reg.get("setting.excel.template.create").verification_rules)
    assert "isCustom" in ex and "columnList" in ex
    qr = " ".join(reg.get("setting.qrcode.rule.search").verification_rules)
    assert "sort" in qr and "null" in qr


# ---------------------------------------------------------------- 关联实体展开
def test_excel_relation_column_has_two_level_path():
    """关联实体字段展开成两层 levelPath（用户截图那个下拉框）。"""
    from components.udc.setting.excel_template_constraints import build_column
    ent = "com.seeyon.app.domain.entity.Foo"
    rel = "com.seeyon.organization.domain.core.entity.OrgMember"
    col = build_column(
        f"{rel}.code", "创建人/编号",
        entity_type="MASTER_ENTITY", relation_app="organization",
        relation_entity="",
        level_path=[
            ["app", ent, "实体", f"{ent}.creator", "创建人"],
            ["organization", rel, "人员", f"{rel}.code", "编号"],
        ])
    assert len(col["levelPath"]) == 2, "关联实体展开必须两层"
    assert col["levelPath"][1][3] == f"{rel}.code", "第二层是关联实体属性"
    assert col["attributeFullName"] == f"{rel}.code", "锚点取第二层全名"
    assert col["displayName"] == "创建人/编号", "displayName 用 父/子 形式"
    assert col["entityType"] == "MASTER_ENTITY", "展开列不是 SUB_ENTITY"
    assert col["relationEntity"] == "", "relationEntity 用空串"


def test_excel_fact_documents_level_path_expansion():
    txt = (FACTS / "excel-template" / "create.md").read_text(encoding="utf-8")
    assert "levelPath" in txt and "两层" in txt, "须写明 levelPath 两层展开"
    assert "OrgMember" in txt, "须给出 organization 关联实例"
    assert "创建人/编号" in txt or "销售员/编号" in txt, "须给出 displayName 形式"
    assert "MASTER_ENTITY" in txt, "须说明不是 SUB_ENTITY"


# ---------------------------------------------------------------- 三种类型全验
def test_qrcode_all_three_types_constructable():
    """页面只提供三种：FIELDQRCODE / BARCODE / LINKQRCODE。"""
    from components.udc.setting.qrcode_constraints import (
        build_qr_rule_body, validate_qr_rule_body)
    ef = "com.seeyon.app.domain.entity.Foo"
    # 字段二维码
    b1 = build_qr_rule_body("1", "2", name="字段二维码", entity_full_name=ef,
                            type_="FIELDQRCODE", value_field_code="code")
    assert not validate_qr_rule_body(b1)
    # 条形码
    b2 = build_qr_rule_body("1", "2", name="条形码", entity_full_name=ef,
                            type_="BARCODE", value_field_code="code")
    assert not validate_qr_rule_body(b2)
    # 链接二维码（页面值必须是 udc_page_info.page_url，不能自编 URL）
    b3 = build_qr_rule_body("1", "2", name="链接二维码", entity_full_name=ef,
                            type_="LINKQRCODE", pc_page_path="someListPage")
    assert not validate_qr_rule_body(b3)


def test_qrcode_three_types_ordinals():
    """DB 里的 ordinal：BARCODE=0 / LINKQRCODE=1 / FIELDQRCODE=2。"""
    from components.udc.setting.qrcode_constraints import QR_TYPE
    assert QR_TYPE["BARCODE"] == 0
    assert QR_TYPE["LINKQRCODE"] == 1
    assert QR_TYPE["FIELDQRCODE"] == 2


def test_qrcode_fact_covers_all_three():
    txt = (FACTS / "qrcode" / "create.md").read_text(encoding="utf-8")
    for name in ("FIELDQRCODE", "BARCODE", "LINKQRCODE"):
        assert name in txt, f"事实格须覆盖 {name}"
    assert "R-E1" in txt and "R-E9" in txt, "须是九段式事实格"
    assert "VACUUM" in txt, "QRCODE(3) 须标 VACUUM"


def test_qrcode_link_pagetype_comes_from_udc_page_info():
    """★ 链接码 pcPagePath = udc_page_info.page_url，禁止自编 URL。"""
    txt = (FACTS / "qrcode" / "create.md").read_text(encoding="utf-8")
    assert "udc_page_info" in txt, "须写明权威表"
    assert "page_url" in txt, "须写明取 page_url"
    assert "禁止自编 URL" in txt or "不能自己编" in txt, "须写明禁令"
    assert "必须先选实体" in txt or "先选实体" in txt, "须写明顺序"

    from components.udc.setting.qrcode_constraints import (
        build_qr_rule_body, validate_link_page_path)
    b = build_qr_rule_body("1", "2", name="x", entity_full_name="com.seeyon.a.b.C",
                           type_="LINKQRCODE", pc_page_path="/main/portal/1")
    errs = validate_link_page_path(b)
    assert errs and any("自编 URL" in e for e in errs), "自编 URL 必须被拦"

    b2 = build_qr_rule_body("1", "2", name="x", entity_full_name="com.seeyon.a.b.C",
                            type_="LINKQRCODE", pc_page_path="notInCandidates")
    errs2 = validate_link_page_path(b2, {"realPageA", "realPageB"})
    assert errs2 and any("不在该实体" in e for e in errs2), "不在候选里必须被拦"

    b3 = build_qr_rule_body("1", "2", name="x", entity_full_name="com.seeyon.a.b.C",
                            type_="LINKQRCODE", pc_page_path="realPageA")
    assert not validate_link_page_path(b3, {"realPageA", "realPageB"}), "合法 code 应通过"


def test_qrcode_page_candidate_query_uses_page_info():
    """候选查询必须查 udc_page_info 且不含 is_deleted（该表没这列）。"""
    from components.udc.setting.qrcode_constraints import (
        build_page_candidate_query, build_page_candidate_query_by_url)
    sql, args = build_page_candidate_query("1", "com.seeyon.a.b.C")
    assert "udc_page_info" in sql
    assert "page_url" in sql
    assert "is_deleted" not in sql, "udc_page_info 没有 is_deleted 列"
    assert "master_entity_ids" in sql or "include_entity_ids" in sql, "须按实体过滤"
    sql2, _ = build_page_candidate_query_by_url("1", "sjypzxx")
    assert "page_url LIKE" in sql2


def test_qrcode_contract_doc_exists():
    p = ROOT / "docs" / "operation-contracts" / "udc" / "setting" / "qrcode-contracts.md"
    assert p.exists(), "缺操作契约文档"
    txt = p.read_text(encoding="utf-8")
    assert "udc_page_info" in txt and "page_url" in txt


# ---------------------------------------------------------------- 流水号九段式
def test_serial_fact_is_nine_section():
    txt = (FACTS / "serial" / "create.md").read_text(encoding="utf-8")
    for sec in ("R-E1", "R-E2", "R-E3", "R-E4", "R-E5", "R-E6", "R-E7", "R-E8", "R-E9"):
        assert sec in txt, f"缺 {sec} 段"


def test_serial_contract_doc_exists():
    p = ROOT / "docs" / "operation-contracts" / "udc" / "setting" / "serial-contracts.md"
    assert p.exists(), "缺操作契约文档"
    txt = p.read_text(encoding="utf-8")
    assert "serialSectionDtoList" in txt, "契约须写明段列表真实字段名"
    assert "SerialRuleTypeEnum" in txt, "契约须写明 serialType 用哪个枚举"
