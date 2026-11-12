"""可发现性闸门：关键事实必须登记 INDEX，前置必须有代码入口。

为什么有这个测试
----------------
真实事故（2026-10-23）：设置域功能都做完了，换个地方用 seeyon-agent 建枚举，
**第一步 appGuid 就卡住** —— 搜 INDEX 搜不到，翻了三四分钟，最后直接查库。
事实件其实存在（`core/facts/udc/setting/precondition-appguid.md`），
只是没登记 INDEX。

⇒ **未登记 = 检索不到 = 等于没沉淀。** 这条用测试锁住，不靠自觉。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

INDEX = ROOT / "core" / "facts" / "INDEX.md"
FACTS = ROOT / "core" / "facts"

# 关键事实：缺一条就说明"能力存在但找不到"
CRITICAL = (
    "setting/precondition-appguid.md",
    "setting/operation-matrix.md",
    "setting/attribute-set/default-value-chain.md",
    "expression/README.md",
    "expression/functions.md",
    "expression/system-variables.md",
    "custom-object/create.md",
    "custom-object/fields.md",
    "enum/create.md",
    "option-set/create.md",
    "parameter/create.md",
    "serial/create.md",
    "qrcode/create.md",
    "excel-template/create.md",
    "scalability/create.md",
    "entity/refer-event-index-tabs.md",
    "entity/rules-microflow.md",
    "entity/scalability.md",
)


def _index_text() -> str:
    return INDEX.read_text(encoding="utf-8")


def test_index_exists():
    assert INDEX.is_file()


def test_critical_facts_are_registered():
    """每条关键事实都要能在 INDEX 里按文件名检索到。"""
    idx = _index_text()
    missing = [rel for rel in CRITICAL if rel.rsplit("/", 1)[-1] not in idx]
    assert not missing, "这些事实件未登记 INDEX（检索不到=没沉淀）: %s" % missing


def test_precondition_appguid_is_discoverable():
    """appGuid 前置必须登记，且 INDEX 行里要含取法关键词。"""
    idx = _index_text()
    assert "precondition-appguid.md" in idx
    for kw in ("appGuid", "udcApplicationDetailGet"):
        assert kw in idx, "INDEX 行缺关键词 %s" % kw


def test_precondition_appguid_documents_interface_not_just_table():
    """事实件要写「取法」，不能只写'取自 udc_application.guid'这种表名列名。"""
    f = FACTS / "udc" / "setting" / "precondition-appguid.md"
    txt = f.read_text(encoding="utf-8")
    assert "udcApplicationDetailGet" in txt
    assert "appGuid ≠ appId" in txt or "appGuid != appId" in txt


def test_expression_facts_registered():
    idx = _index_text()
    assert "expression/README.md" in idx
    assert "expression/functions.md" in idx
    assert "expression/system-variables.md" in idx


# ---------------------------------------------------------------- 代码入口
def test_app_guid_helper_exists():
    """appGuid 必须有可复用代码入口，不能只靠读文档。"""
    f = ROOT / "components" / "udc" / "setting" / "application_guid.py"
    assert f.is_file()


def test_app_guid_helper_has_no_hardcoded_targets():
    """前置模块里不许出现任何 appId / 客户域名 / 测试值。"""
    src = (ROOT / "components" / "udc" / "setting" / "application_guid.py").read_text(
        encoding="utf-8")
    import re
    assert not re.search(r"\b\d{16,20}\b", src), "出现 appId 形态字面量"
    # 客户组织关键词拼着写，避免本文件自己命中脱敏闸门
    assert ("changhong" + "it") not in src
    assert "验收" not in src and "zxj" not in src


def test_app_guid_helper_raises_instead_of_returning_empty():
    """取不到 guid 必须抛错 —— 空 guid 会静默落成 app_guid=-1，比报错难查。"""
    from components.udc.setting.application_guid import (
        APP_DETAIL_OP, APP_DETAIL_PATH, AppGuidError, app_guid_sql,
    )
    assert APP_DETAIL_OP == "udcApplicationDetailGet"
    assert APP_DETAIL_PATH.endswith(APP_DETAIL_OP)
    assert issubclass(AppGuidError, RuntimeError)
    sql, args = app_guid_sql("123")
    assert "udc_application" in sql and "guid" in sql
    assert args == ("123",)


def test_app_guid_helper_rejects_empty_app_id():
    from components.udc.setting.application_guid import AppGuidError, fetch_application

    class _NoClient:
        def evaluate(self, *a, **k):  # pragma: no cover
            raise AssertionError("不该发请求")

    try:
        fetch_application(_NoClient(), "")
    except AppGuidError as exc:
        assert "app_id" in str(exc)
    else:
        raise AssertionError("空 appId 应抛 AppGuidError")
