"""MySQL 只读 provider：安全门 + 多 schema 寻址 + 凭据解析。

背景：seeyon test2 是「一个实例多个 schema」——元数据库 udc_test2、用户库
ctp_user_test2、组织库 organization_test2、每个应用的业务库 <appId>_test2 全在同一台。
所以适配器不绑定单一 database，按 schema 名寻址；绑定单库会让跨库查询全部 1046。

本测试全程不连真实数据库（无网络），用假连接对象验证：
  1. 写/DDL 语句必须被拒（且理由可读）
  2. 注释截断、多语句、FOR UPDATE 等绕过手法必须被拒
  3. 只读语句放行，且参数化传递（不拼字符串）
  4. 凭据优先级：显式参数 > 环境变量 > 凭据文件
  5. 连接不传 database（多 schema 前提）
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

import pytest

from core.providers import ProviderError
from providers.mysql_readonly import (
    MySQLConnectionAdapter,
    MySQLReadonlyProvider,
    _deny_reason,
)


# ---------------------------------------------------------------- 安全门

@pytest.mark.parametrize("sql", [
    "INSERT INTO t VALUES (1)",
    "UPDATE t SET a=1",
    "DELETE FROM t",
    "DROP TABLE t",
    "TRUNCATE t",
    "ALTER TABLE t ADD c INT",
    "CREATE TABLE t (a INT)",
    "GRANT ALL ON *.* TO 'x'@'%'",
    "SELECT 1; DROP TABLE t",              # 多语句
    "SELECT 1 -- comment",                 # 注释截断
    "SELECT /* x */ 1",                    # 块注释
    "SELECT * FROM t FOR UPDATE",          # 加锁
    "SET GLOBAL max_conn=1",
    "CALL proc()",
])
def test_write_and_bypass_forms_are_denied(sql):
    """写语句与常见绕过手法必须给出拒绝理由。"""
    assert _deny_reason(sql), f"应拒绝: {sql}"


@pytest.mark.parametrize("sql", [
    "SELECT 1",
    "select * from information_schema.TABLES",
    "WITH x AS (SELECT 1) SELECT * FROM x",
    "SHOW TABLES",
    "DESC udc_microflow_info",
    "EXPLAIN SELECT 1",
])
def test_readonly_forms_are_allowed(sql):
    """只读语句必须放行（deny 返回 None）。"""
    assert _deny_reason(sql) is None, f"应放行: {sql}"


def test_deny_reason_is_human_readable():
    """拒绝理由必须说明原因，不能只返回 True。"""
    r = _deny_reason("INSERT INTO t VALUES (1)")
    assert isinstance(r, str) and len(r) > 5


# ---------------------------------------------------------------- 假连接

class FakeCursor:
    def __init__(self, log, rows=None):
        self.log = log
        self._rows = rows or []

    def execute(self, sql, params=None):
        self.log.append(("execute", sql, params))

    def fetchall(self):
        return list(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeConn:
    def __init__(self, log, rows=None):
        self.log = log
        self.rows = rows

    def cursor(self):
        return FakeCursor(self.log, self.rows)

    def close(self):
        self.log.append(("close",))


def _adapter_with_fake(monkeypatch, rows=None):
    """装一个假连接，记录所有 execute，用于验证参数化与多 schema 寻址。"""
    log = []
    a = MySQLConnectionAdapter(host="h", port=3306, user="u", password="p")
    monkeypatch.setattr(a, "_connect", lambda: FakeConn(log, rows))
    return a, log


def test_query_is_parameterized_not_concatenated(monkeypatch):
    """schema/table 名必须走参数占位符，不能拼进 SQL 字符串。"""
    a, log = _adapter_with_fake(monkeypatch)
    a.query("SELECT 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s", ("udc_test2",))
    method, sql, params = log[0]
    assert method == "execute"
    assert "%s" in sql, "必须用占位符"
    assert params == ("udc_test2",), f"参数须原样传递: {params}"
    assert "udc_test2" not in sql, "值不得出现在 SQL 文本里"


def test_write_query_never_reaches_cursor(monkeypatch):
    """写语句必须在到达 cursor 之前就被拒（不是靠数据库报错）。"""
    from providers.mysql_readonly import _ConnFailure
    a, log = _adapter_with_fake(monkeypatch)
    with pytest.raises(_ConnFailure) as ei:
        a.query("DELETE FROM udc_entity WHERE id=1")
    assert ei.value.kind == "permission"
    assert not any(entry[0] == "execute" for entry in log), "写语句不得触达 cursor"


def test_describe_table_queries_columns_and_indexes(monkeypatch):
    """describe_table 应分别查 COLUMNS 与 STATISTICS（多 schema 用全限定名）。"""
    a, log = _adapter_with_fake(monkeypatch)
    a.describe_table("udc_test2", "udc_microflow_info")
    sqls = [e[1] for e in log if e[0] == "execute"]
    assert len(sqls) == 2
    assert "information_schema.COLUMNS" in sqls[0]
    assert "information_schema.STATISTICS" in sqls[1]
    for e in log:
        if e[0] == "execute":
            assert e[2] == ("udc_test2", "udc_microflow_info"), e[2]


# ---------------------------------------------------------------- 凭据解析

def test_explicit_args_win_over_env(monkeypatch):
    monkeypatch.setenv("SEEYON_DB_HOST", "from-env")
    monkeypatch.setenv("SEEYON_DB_USERNAME", "env-user")
    a = MySQLConnectionAdapter(host="explicit-host", user="explicit-user")
    cred = a._resolve()
    assert cred["host"] == "explicit-host"
    assert cred["user"] == "explicit-user"


def test_env_used_when_args_missing(monkeypatch):
    monkeypatch.setenv("SEEYON_DB_HOST", "env-host")
    monkeypatch.setenv("SEEYON_DB_USERNAME", "env-user")
    monkeypatch.setenv("SEEYON_DB_PASSWORD", "env-pass")
    a = MySQLConnectionAdapter()
    cred = a._resolve()
    assert cred["host"] == "env-host"
    assert cred["user"] == "env-user"
    assert cred["password"] == "env-pass"


def test_credential_file_used_as_last_resort(monkeypatch, tmp_path):
    for k in ("SEEYON_DB_HOST", "SEEYON_DB_USERNAME", "SEEYON_DB_PASSWORD"):
        monkeypatch.delenv(k, raising=False)
    f = tmp_path / "cred.json"
    f.write_text('{"host":"file-host","user":"file-user","password":"file-pass"}',
                 encoding="utf-8")
    a = MySQLConnectionAdapter(credential_file=f)
    cred = a._resolve()
    assert cred["host"] == "file-host"
    assert cred["user"] == "file-user"


def test_missing_host_returns_unavailable_result(monkeypatch):
    """缺 host 时 provider 层返回 error 结果，而不是抛异常（仓库约定）。"""
    from providers.mysql_readonly import _ConnFailure
    for k in ("SEEYON_DB_HOST", "SEEYON_DB_USERNAME", "SEEYON_DB_PASSWORD"):
        monkeypatch.delenv(k, raising=False)
    a = MySQLConnectionAdapter()
    # adapter 内部抛 _ConnFailure（承载 ProviderError），边界处转 ProviderResult
    with pytest.raises(_ConnFailure) as ei:
        a._connect()
    assert ei.value.kind == "unavailable"
    assert "host" in ei.value.error.message.lower()

    # provider 包装层必须把同一情况变成 error 结果
    out = a.list_schemas("%test2%")
    assert not out.ok
    assert out.error.kind == "unavailable"


# ---------------------------------------------------------------- provider 包装

def test_fixture_adapter_still_works_offline():
    """fixture 路径必须保持可用（既有离线测试依赖它）。"""
    from providers.mysql_readonly import MySQLFixtureAdapter
    p = MySQLReadonlyProvider(MySQLFixtureAdapter(
        {"tables": {"udc_entity": {"columns": [{"name": "id"}], "indexes": []}}}))
    out = p.read_tables()
    assert out.ok and out["classification"] == "PASS"
    assert out["tables"] == ["udc_entity"]


def test_provider_denies_write_even_when_network_enabled():
    """即使 allow_network=True，写语句仍被 DENIED（不依赖数据库层）。"""
    from providers.mysql_readonly import MySQLFixtureAdapter
    p = MySQLReadonlyProvider(MySQLFixtureAdapter({"tables": {}}), allow_network=True)
    out = p.query("DELETE FROM t")
    assert out["classification"] == "DENIED"
    assert out.error is not None


def test_provider_blocks_live_query_on_fixture_adapter():
    """fixture 适配器不支持 live 查询，必须明确 BLOCKED 而不是假装成功。"""
    from providers.mysql_readonly import MySQLFixtureAdapter
    p = MySQLReadonlyProvider(MySQLFixtureAdapter({"tables": {}}), allow_network=True)
    out = p.query("SELECT 1")
    assert out["classification"] == "BLOCKED"
    assert "不支持 live" in out.error.message
