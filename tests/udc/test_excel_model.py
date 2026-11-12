"""Excel 模板/异步模型测试（flow-excel-source-audit §1/§4 证据）。"""
from components.udc.excel_model import (
    APP_ID_IS_STRING,
    COLUMN_STRUCTURES,
    EXCEL_TEMPLATE_TABLE,
    KNOWN_EXCEPTION_GAP,
    REFERENCE_FIELD_RULES,
    SIDE_EFFECT_OPERATIONS,
    TEMPLATE_REUSE_LOOKUP_KEYS,
    ExcelAsyncTask,
    ExcelTemplateModel,
    side_effect_classification,
)


def test_template_table_and_app_id_string_discipline():
    assert EXCEL_TEMPLATE_TABLE == "ctp_excel_export_template"
    assert APP_ID_IS_STRING is True


def test_int_app_id_rejected():
    m = ExcelTemplateModel(app_id="x", main_full_name="e.Order")
    # 正常 str 过
    assert "app_id" not in " ".join(m.validate()["errors"])
    m2 = ExcelTemplateModel(app_id=123, main_full_name="e.Order")  # type: ignore[arg-type]
    assert any("String" in e for e in m2.validate()["errors"])


def test_missing_head_info_is_error():
    m = ExcelTemplateModel(app_id="a", main_full_name="e.Order",
                           metadata_content=[{"col": "name"}])
    assert any("excelHeadInfo" in e or "两份结构" in e for e in m.validate()["errors"])


def test_no_signature_warns_side_effect():
    m = ExcelTemplateModel(app_id="a", main_full_name="e.Order",
                           metadata_content=[{}], excel_head_info=[])
    r = m.validate()
    assert r["status"] == "UNVERIFIED"
    assert any("templateService.create" in w for w in r["warnings"])


def test_complete_template_passes():
    m = ExcelTemplateModel(app_id="a", main_full_name="e.Order", signature_code="SIG",
                           metadata_content=[{}], excel_head_info=[{}])
    assert m.validate()["status"] == "PASS"


def test_check_endpoint_is_side_effect_not_readonly():
    # §1 纠正结论：check 不能因叫 check 进只读白名单
    assert "excel/check-excel" in SIDE_EFFECT_OPERATIONS
    assert "模板" in SIDE_EFFECT_OPERATIONS["excel/check-excel"]
    # 消费接口同步可用
    assert side_effect_classification()["excel/import"].count("ASYNC") >= 1


def test_async_task_needs_full_acceptance():
    t = ExcelAsyncTask(redis_key="rk", state="SUCCESS")   # 只有句柄
    assert t.validate()["status"] == "UNVERIFIED"
    ok = ExcelAsyncTask(redis_key="rk", state="SUCCESS",
                        file_ready=True, row_results_checked=True)
    assert ok.validate()["status"] == "PASS"


def test_export_direction_checked():
    assert "direction" in " ".join(ExcelAsyncTask(direction="delete").validate()["errors"])


def test_reference_field_rules_and_exception_gap_registered():
    assert any("Many2One" in r for r in REFERENCE_FIELD_RULES)
    assert any("CTPENUM" in r or "选项集" in r for r in REFERENCE_FIELD_RULES)
    assert "successFlag" in KNOWN_EXCEPTION_GAP
    # 双结构常量（层级+拉平）
    assert any("metadata" in c for c in COLUMN_STRUCTURES)
    assert any("excel_head" in c for c in COLUMN_STRUCTURES)


def test_template_reuse_lookup_keys():
    assert set(TEMPLATE_REUSE_LOOKUP_KEYS) == {"appId", "mainFullName", "isImport", "isCustom", "isDefault"}
