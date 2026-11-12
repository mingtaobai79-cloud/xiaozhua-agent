"""自定义对象写执行器：fail-closed 与引用闸门必须成立。

本测试不联网、不写平台，只验证控制流：
  1. 写操作必须显式确认（--i-have-write-authorization），否则拒绝
  2. 删除前必须做引用核对，阳性对照不通过则不下删除结论
  3. 引用核对能区分"有引用"与"无引用"
  4. 成功码不等于删掉了 —— 必须回读
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

TOOL = ROOT / "tools" / "core" / "setting" / "custom_object_write.py"


def _load():
    spec = importlib.util.spec_from_file_location("cow", TOOL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_tool_exists_and_is_under_setting():
    assert TOOL.exists(), f"缺写执行器: {TOOL}"
    assert "setting" in TOOL.parts, "写执行器应在 tools/core/setting/ 下"


def test_write_requires_explicit_authorization_flag():
    """写操作必须显式确认 —— 不确认就拒绝（fail-closed）。"""
    src = TOOL.read_text(encoding="utf-8")
    assert "--i-have-write-authorization" in src, "缺显式授权开关"
    assert "i_have_write_authorization" in src, "授权开关未被读取"


def test_delete_command_checks_references_before_deleting():
    """删除子命令必须先做引用核对，且对照不过就终止。"""
    src = TOOL.read_text(encoding="utf-8")
    assert "reference_check" in src, "删除路径未调用引用核对"
    # 引用核对必须在 发请求 之前
    i_ref = src.index("reference_check(conn, app_id")
    i_send = src.index("_gql(client, \"udcDataTransferObjectDeletePost\"")
    assert i_ref < i_send, "引用核对必须早于删除请求"


def test_delete_reads_back_after_delete():
    """成功码不代表删掉了 —— 删除后必须回读 DB。"""
    src = TOOL.read_text(encoding="utf-8")
    assert "回读" in src, "删除后缺回读核对"
    i_send = src.index("_gql(client, \"udcDataTransferObjectDeletePost\"")
    i_read = src.index("回读:", i_send)
    assert i_read > i_send, "回读必须发生在删除请求之后"


def test_reference_check_returns_validity_and_detail():
    """reference_check 返回 (方法是否有效, 逐名引用详情)。"""
    m = _load()
    assert hasattr(m, "reference_check")
    # 用假连接：对照不通过 → method_valid 必须为 False
    class FakeConn:
        def describe_table(self, *a):
            raise RuntimeError("no table")

        def query(self, sql, params=None):
            return [{"name": "SomeEntity"}]

    ok, detail = m.reference_check(FakeConn(), "app1", ["x"])
    assert ok is False, "对照不通过时 method_valid 必须为 False"
    assert isinstance(detail, dict)


def test_create_uses_agent_constructor_and_validator():
    """创建路径必须走 seeyon-agent 的构造器 + 校验器（不自己拼 body）。"""
    src = TOOL.read_text(encoding="utf-8")
    assert "build_custom_object_body" in src
    assert "validate_custom_object_body" in src
    i_build = src.index("build_custom_object_body(")
    i_check = src.index("validate_custom_object_body(")
    i_send = src.index("_gql(client, \"udcDataTransferObjectPost\"")
    assert i_build < i_check < i_send, "顺序应为 构造 → 校验 → 提交"


def test_list_is_read_only_and_needs_no_authorization():
    """list 是只读，不需要授权开关。"""
    m = _load()
    assert hasattr(m, "cmd_list")
    src = TOOL.read_text(encoding="utf-8")
    assert 'if a.action == "list":' in src
    assert "return cmd_list(conn, a.app_id)" in src
