"""测试：流水号机制（boot-starter-serialnumber 5.3.318）约束模型。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from components.udc.serialnumber_constraints import (
    SERIAL_CONTROLLERS, SERIAL_ENDPOINTS, SERIAL_SECTION_TYPES, SERIAL_RULE_TYPES,
    SERIAL_RESET_RULES, SERIAL_RANGE_TYPES, SERIAL_FILL_TYPES, SERIAL_CUT_TYPES,
    SERIAL_DB_TABLES, SERIAL_SCHEME_REQUIRED,
    validate_serial_scheme, validate_serial_section,
)


def test_controllers():
    assert SERIAL_CONTROLLERS["SerialSchemeController"] == "serial-scheme"
    assert SERIAL_CONTROLLERS["SerialNumberController"] == "serial-number"
    assert len(SERIAL_CONTROLLERS) == 4


def test_endpoints():
    # 45 个端点
    assert len(SERIAL_ENDPOINTS) == 45
    # 取号是写操作（消耗流水号）
    ro = {f"{SERIAL_CONTROLLERS[c]}/{s}": readonly for c, _m, s, _d, readonly in SERIAL_ENDPOINTS}
    assert ro["serial-number/get-serial-number"] is False
    assert ro["serial-number/preview-serial-value"] is True
    assert ro["serial-scheme/search-no-page"] is True
    assert ro["serial-scheme/createEasyScheme"] is False


def test_enum_domains():
    assert SERIAL_SECTION_TYPES == {"CONSTANT": 0, "CONTEXT": 1, "ENTITY": 2, "SERIAL": 3}
    assert SERIAL_RULE_TYPES == {"APP": 0, "BIG": 1, "SMALL": 2}
    assert SERIAL_RESET_RULES == {"NONE": 0, "YEAR": 1, "MONTH": 2, "DAY": 3}
    assert SERIAL_RANGE_TYPES == {"RESERVE": 0, "UNUSED": 1}
    assert SERIAL_FILL_TYPES == {"LEFT": 0, "RIGHT": 1, "NONE": 2}
    assert SERIAL_CUT_TYPES == {"LEFT": 0, "RIGHT": 1, "NONE": 2}


def test_db_tables():
    # 6 张表，方案表 17 列全覆盖
    assert set(SERIAL_DB_TABLES) == {
        "ctp_serial_scheme", "ctp_serial_section", "ctp_serial_range",
        "ctp_serial_condition", "ctp_serial_current", "ctp_serial_history"}
    cols = SERIAL_DB_TABLES["ctp_serial_scheme"]["columns"]
    assert len(cols) == 17
    assert cols["code"][0] == "VARCHAR(50)" and cols["code"][1] is False
    assert cols["is_active"][2] is True  # 默认启用
    sec = SERIAL_DB_TABLES["ctp_serial_section"]["columns"]
    assert len(sec) == 19
    assert sec["fill_char"][2] == "0"
    assert sec["section_size"][2] == 4


def test_validate_scheme():
    ok = {"code": "ORDER_NO", "name": "订单编号", "serialType": "APP",
          "entityFullName": "com.seeyon.Order"}
    assert validate_serial_scheme(ok) == []
    assert any("缺必填" in e for e in validate_serial_scheme({}))
    bad = dict(ok, serialType="BOGUS")
    assert any("不在值域" in e for e in validate_serial_scheme(bad))
    bad2 = dict(ok, serialResetRule="WEEK")
    assert any("serialResetRule" in e for e in validate_serial_scheme(bad2))


def test_validate_section():
    ok = {"type": "SERIAL", "size": 4, "startValue": 1, "endValue": 9999,
          "fillType": "LEFT", "fillChar": "0"}
    assert validate_serial_section(ok) == []
    assert any("type" in e for e in validate_serial_section({"type": "BOGUS"}))
    assert any("startValue" in e for e in validate_serial_section(
        {"type": "SERIAL", "startValue": 100, "endValue": 10}))
    assert any("size" in e for e in validate_serial_section({"size": 0}))
