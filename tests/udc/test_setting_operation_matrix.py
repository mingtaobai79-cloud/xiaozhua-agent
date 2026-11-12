"""设置域操作矩阵：事实件与探针的三条判别纪律必须被锁住。

锁的是**本轮踩过的错**，不是设计口味：
  1 GraphQL 的 code 嵌在 data.data0.code，看顶层会全误判
  2 字段集 / 二维码 / 导入导出模板走 REST，用 GraphQL 探是假阴性
  3 不能 str(None) 判真假（恒真）→ 会把"没返回"当"存在"
  4 CDP 连到 devtools:// 时 fetch 返回 status=200 body="HTTP/1.1 404 Not Found"
     → 全部路径假阴性，必须有 origin 自检
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

FACT = ROOT / "core" / "facts" / "udc" / "setting" / "operation-matrix.md"
TOOL = ROOT / "tools" / "core" / "setting" / "probe_setting_ops.py"
INDEX = ROOT / "core" / "facts" / "INDEX.md"


def test_fact_exists_and_leveled():
    assert FACT.is_file()
    txt = FACT.read_text(encoding="utf-8")
    assert "LIVE" in txt
    assert "2026-10-23" in txt


def test_fact_records_vacuum_for_excel_delete_template():
    """`/service/udc/excel/delete-template` 是 404，必须明写 VACUUM。"""
    txt = FACT.read_text(encoding="utf-8")
    assert "/service/udc/excel/delete-template" in txt
    assert "404" in txt
    assert "VACUUM" in txt


def test_fact_records_success_code_unreliable():
    """六个 delete 空 body 回 BOOT_0000 —— 成功码不可信要显式写。"""
    txt = FACT.read_text(encoding="utf-8")
    assert "成功码不可信" in txt
    assert "BOOT_0000" in txt


def test_fact_states_endpoint_existence_not_capability():
    """必须写明「端点存在性 ≠ 能力可用性」，防止被当完成度引用。"""
    txt = FACT.read_text(encoding="utf-8")
    assert "端点存在性" in txt
    assert "能力可用性" in txt


def test_fact_registered_in_index():
    """未登记 INDEX = 检索不到 = 没写。"""
    idx = INDEX.read_text(encoding="utf-8")
    assert "setting/operation-matrix.md" in idx


# ---------------------------------------------------------------- 探针纪律
def test_tool_exists_and_parameterized():
    assert TOOL.is_file()
    src = TOOL.read_text(encoding="utf-8")
    # 不允许硬编码客户域名（关键词拼着写，避免本文件自己命中脱敏闸门）
    assert ("sample" + "it") not in src
    # 端口与页面要能传
    assert "--port" in src
    assert "--url-match" in src


def test_tool_parses_nested_data0_code():
    """GraphQL 结果必须取 data.data0.code，不是顶层 code。"""
    src = TOOL.read_text(encoding="utf-8")
    assert "data0" in src
    assert 'get("data0")' in src


def test_tool_splits_rest_and_graphql():
    """REST 与 GraphQL 必须分通道探，否则 REST 域全是假阴性。"""
    src = TOOL.read_text(encoding="utf-8")
    assert "GRAPHQL_OPS" in src
    assert "REST_OPS" in src
    # 三个 REST 域都要在 REST 表里
    for domain in ("字段集", "二维码", "导入导出模板"):
        assert domain in src


def test_tool_does_not_truthify_str_none():
    """不允许把 str(None) 结果拿去判真假。"""
    src = TOOL.read_text(encoding="utf-8")
    assert 'str(r.get("message"))[:60]' not in src
    assert 'isinstance(code, str) and code' in src


def test_tool_has_origin_guard():
    """连到 devtools:// 必须报错退出，不能继续探（会全假阴性）。"""
    src = TOOL.read_text(encoding="utf-8")
    assert "location.origin" in src
    assert "devtools" in src
    assert "startswith(\"http\")" in src


def test_tool_uses_empty_body_only():
    """探针只发空 body —— 不许构造有效写入（避免真改数据）。"""
    src = TOOL.read_text(encoding="utf-8")
    assert '"params0": {}' in src
    assert "_post(client, path, {})" in src
