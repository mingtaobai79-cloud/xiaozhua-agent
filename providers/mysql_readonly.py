"""Read-only MySQL provider with both fixture and live adapters.

两种适配器同接口（``read()`` / ``query()``），由 ``MySQLReadonlyProvider`` 统一封装：

  MySQLFixtureAdapter      —— 读本地 JSON 快照（离线确定性测试用，默认路径）
  MySQLConnectionAdapter   —— 直连真实 MySQL（只读，默认关闭，需显式开启）

多数据库适配要点（实测 test2 实例 5.7.28-log，128 个 schema）：
  1. **一个实例多个 schema**：xiaozhua 的元数据库（udc_test2）、用户库（ctp_user_test2）、
     组织库（organization_test2）、每个应用的业务库（<appId>_test2）都在同一实例上。
     因此适配器不绑定单一 database，而是按 schema 名寻址。
  2. **版本差异**：5.7 无 ``information_schema.COLUMNS.EXTRA`` 的
     ``GENERATED`` 语义细节、8.0 才有 ``STATISTICS.EXPRESSION``。
     列/索引查询只用 5.7 与 8.0 都存在的列，避免版本分支。
  3. **不假设 database 已选中**：连接不传 database，所有查询显式写
     ``information_schema`` 或 ``<schema>.<table>`` 全限定名。
  4. **字符集**：统一 utf8mb4，与平台侧一致（中文 caption 必须原样回读）。

安全边界（沿用仓库铁律，不放宽）：
  - 只允许 SELECT / WITH / SHOW / DESC；
  - 正则先拦写关键字（与既有 ``_WRITE`` 同源）；
  - 额外拦多语句（分号后还有内容）与注释注入；
  - 真实连接默认关闭，``allow_network=True`` 才连；
  - 凭据只从环境变量或仓外文件读，**永不写入仓库**。
"""
from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from core.providers import ProviderError, ProviderResult

# 只读语句白名单（首关键字）
_READONLY_LEAD = re.compile(r"^\s*(SELECT|WITH|SHOW|DESC|DESCRIBE|EXPLAIN)\b", re.I)
# 写/DDL 关键字（出现在语句任意位置即拒，比只看首词更严）
_WRITE_ANYWHERE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|REPLACE|MERGE|UPSERT|CREATE|ALTER|DROP|TRUNCATE|RENAME|"
    r"GRANT|REVOKE|CALL|EXEC|EXECUTE|LOAD|INTO\s+OUTFILE|INTO\s+DUMPFILE|LOCK|UNLOCK|"
    r"SET\s+GLOBAL|SET\s+SESSION|START\s+TRANSACTION|COMMIT|ROLLBACK|SAVEPOINT|"
    r"HANDLER|PREPARE|DEALLOCATE)\b", re.I)
# 多语句 / 注释注入
_MULTI_STMT = re.compile(r";\s*\S")
_COMMENT = re.compile(r"(--[^\n]*$|/\*|\*/|#)", re.M)


def _deny_reason(sql: str) -> str | None:
    """返回拒绝原因；None = 允许。顺序：注释 → 多语句 → 非只读首词 → 写关键字。"""
    if _COMMENT.search(sql):
        return "SQL 含注释，拒绝执行（防注释截断绕过）"
    if _MULTI_STMT.search(sql):
        return "SQL 含多条语句，拒绝执行"
    if not _READONLY_LEAD.match(sql):
        return "非只读语句（首关键字须为 SELECT/WITH/SHOW/DESC/DESCRIBE/EXPLAIN）"
    # SELECT ... FOR UPDATE 会加锁
    if re.search(r"\bFOR\s+UPDATE\b", sql, re.I):
        return "SELECT ... FOR UPDATE 会加锁，只读取证不放行"
    hit = _WRITE_ANYWHERE.search(sql)
    if hit:
        return f"SQL 含写/DDL 关键字 {hit.group(0)!r}，拒绝执行"
    return None


class _ConnFailure(Exception):
    """把 ProviderError（不可抛的 frozen dataclass）包成可抛异常。

    仓库约定 Provider 层用 ProviderResult(error=...) 表达失败；但 _connect/_query
    内部需要中断流程，故用这个内部异常承载 ProviderError，边界处统一转成
    ProviderResult。调用方只看到 ProviderResult，不看到本异常。
    """

    def __init__(self, error: ProviderError):
        super().__init__(error.message)
        self.error = error

    @property
    def kind(self) -> str:
        return self.error.kind


class MySQLFixtureAdapter:
    """Read MySQL metadata from a mapping or local JSON fixture."""

    def __init__(self, source: str | Path | Mapping[str, Any]):
        self.source = source

    def read(self) -> ProviderResult[dict[str, Any]]:
        if isinstance(self.source, Mapping):
            return ProviderResult(dict(self.source))
        path = Path(self.source)
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError as exc:
            return ProviderResult(error=ProviderError(
                "unavailable", "MySQL fixture was not found",
                {"path": str(path), "exception": type(exc).__name__}))
        except (OSError, UnicodeError) as exc:
            return ProviderResult(error=ProviderError(
                "unavailable", "MySQL fixture is unavailable",
                {"path": str(path), "exception": type(exc).__name__}))
        except (TypeError, ValueError) as exc:
            return ProviderResult(error=ProviderError(
                "parse", "MySQL fixture is not valid JSON",
                {"path": str(path), "exception": type(exc).__name__}))
        if not isinstance(payload, dict):
            return ProviderResult(error=ProviderError(
                "parse", "MySQL fixture must be a JSON object", {"path": str(path)}))
        return ProviderResult(payload)


class MySQLConnectionAdapter:
    """Read-only live MySQL adapter (pymysql).

    凭据解析顺序（先环境变量，后仓外文件；**任何值都不进仓库**）：
      1. 显式参数 host/port/user/password
      2. 环境变量：XIAOZHUA_DB_HOST / XIAOZHUA_DB_PORT / XIAOZHUA_DB_USERNAME /
         XIAOZHUA_DB_PASSWORD / XIAOZHUA_DB_NAME
      3. credential_file 指向的仓外 JSON，键同上（小写亦可）

    不传 database：xiaozhua 一个实例承载多个 schema，绑定单库会让跨库查询全 1046。
    """

    network = "live"
    allow_network = True

    def __init__(self, *, host: str = "", port: int | str = 0, user: str = "",
                 password: str = "", database: str = "",
                 credential_file: str | Path | None = None,
                 connect_timeout: int = 10, charset: str = "utf8mb4"):
        self._explicit = {"host": host, "port": port, "user": user,
                          "password": password, "database": database}
        self.credential_file = Path(credential_file) if credential_file else None
        self.connect_timeout = connect_timeout
        self.charset = charset
        self._conn = None

    # ---------- 凭据 ----------
    def _resolve(self) -> dict[str, str]:
        out = {k: ("" if v in (0, None) else str(v)) for k, v in self._explicit.items()}
        envmap = {"host": "XIAOZHUA_DB_HOST", "port": "XIAOZHUA_DB_PORT",
                  "user": "XIAOZHUA_DB_USERNAME", "password": "XIAOZHUA_DB_PASSWORD",
                  "database": "XIAOZHUA_DB_NAME"}
        for key, env in envmap.items():
            if not out.get(key):
                out[key] = os.environ.get(env, "")
        if self.credential_file and self.credential_file.exists():
            try:
                doc = json.loads(self.credential_file.read_text(encoding="utf-8-sig"))
            except Exception:
                doc = {}
            if isinstance(doc, dict):
                for key in ("host", "port", "user", "password", "database"):
                    if not out.get(key):
                        val = doc.get(key, doc.get(key.upper(), ""))
                        if val not in (None, ""):
                            out[key] = str(val)
        return out

    def _connect(self):
        if self._conn is not None:
            return self._conn
        cred = self._resolve()
        if not cred.get("host"):
            # 仓库约定：Provider 层不抛异常，用 ProviderError 表达（kind 限定 6 值）
            raise _ConnFailure(ProviderError(
                "unavailable",
                "MySQL host 未解析到（set XIAOZHUA_DB_HOST or pass credential_file）",
                {"resolved_keys": sorted(k for k, v in cred.items() if v)}))
        try:
            import pymysql
        except ImportError as exc:
            raise _ConnFailure(ProviderError(
                "unavailable", "pymysql 未安装", {"exception": repr(exc)})) from exc
        try:
            self._conn = pymysql.connect(
                host=cred["host"],
                port=int(cred.get("port") or 3306),
                user=cred.get("user") or "",
                password=cred.get("password") or "",
                database=cred.get("database") or None,
                connect_timeout=self.connect_timeout,
                charset=self.charset,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,   # 只读会话不提交任何事务
            )
        except Exception as exc:  # 连接失败是环境事实，不静默
            raise _ConnFailure(ProviderError(
                "unavailable", f"MySQL 连接失败: {type(exc).__name__}",
                {"host": cred["host"], "port": cred.get("port"),
                 "message": str(exc)[:200]})) from exc
        return self._conn

    # ---------- 只读查询 ----------
    def query(self, sql: str, params: tuple | list | None = None) -> list[dict[str, Any]]:
        reason = _deny_reason(sql)
        if reason:
            raise _ConnFailure(ProviderError("permission", reason, {"sql": sql[:200]}))
        conn = self._connect()
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return list(cur.fetchall())

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None

    # ---------- ProviderResult 接口（与 fixture 适配器一致） ----------
    def read(self) -> ProviderResult[dict[str, Any]]:
        """返回实例级元数据摘要（schema 列表 + 服务端版本）。"""
        try:
            rows = self.query(
                "SELECT VERSION() AS version, @@version_comment AS comment")
            ver = rows[0] if rows else {}
            schemas = [r["SCHEMA_NAME"] for r in self.query(
                "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA "
                "ORDER BY SCHEMA_NAME")]
        except _ConnFailure as exc:
            return ProviderResult(error=exc.error)
        return ProviderResult({"server": ver, "schemas": schemas})

    # ---------- 面向 xiaozhua 的多库寻址 ----------
    def list_schemas(self, pattern: str | None = None) -> ProviderResult[dict[str, Any]]:
        sql = ("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA "
               + ("WHERE SCHEMA_NAME LIKE %s " if pattern else "")
               + "ORDER BY SCHEMA_NAME")
        try:
            rows = self.query(sql, (pattern,) if pattern else None)
        except _ConnFailure as exc:
            return ProviderResult(error=exc.error)
        return ProviderResult({"schemas": [r["SCHEMA_NAME"] for r in rows],
                               "count": len(rows), "classification": "PASS"})

    def list_tables(self, schema: str, pattern: str | None = None) -> ProviderResult[dict[str, Any]]:
        sql = ("SELECT TABLE_NAME, TABLE_ROWS, TABLE_COMMENT, ENGINE "
               "FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s "
               + ("AND TABLE_NAME LIKE %s " if pattern else "")
               + "ORDER BY TABLE_NAME")
        try:
            rows = self.query(sql, (schema, pattern) if pattern else (schema,))
        except _ConnFailure as exc:
            return ProviderResult(error=exc.error)
        return ProviderResult({"schema": schema, "tables": rows,
                               "count": len(rows), "classification": "PASS"})

    def describe_table(self, schema: str, table: str) -> ProviderResult[dict[str, Any]]:
        """列 + 索引。只用 5.7/8.0 共有列，避免版本分支。"""
        try:
            cols = self.query(
                "SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, "
                "COLUMN_DEFAULT, COLUMN_KEY, COLUMN_COMMENT, ORDINAL_POSITION "
                "FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s ORDER BY ORDINAL_POSITION",
                (schema, table))
            idx = self.query(
                "SELECT INDEX_NAME, NON_UNIQUE, SEQ_IN_INDEX, COLUMN_NAME, INDEX_TYPE "
                "FROM information_schema.STATISTICS "
                "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s "
                "ORDER BY INDEX_NAME, SEQ_IN_INDEX",
                (schema, table))
        except _ConnFailure as exc:
            return ProviderResult(error=exc.error)
        return ProviderResult({"schema": schema, "table": table,
                               "columns": cols, "indexes": idx,
                               "classification": "PASS" if cols else "NOT_FOUND"})


class MySQLReadonlyProvider:
    """Expose table, column, and index metadata; writes always denied."""

    _WRITE = re.compile(
        r"^\s*(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE|RENAME|REPLACE|"
        r"GRANT|REVOKE|CALL|LOAD|SET)\b", re.I)

    def __init__(self, adapter, *, allow_network: bool = False):
        if not hasattr(adapter, "read"):
            raise TypeError("adapter must provide read()")
        self.adapter = adapter
        # 真实连接必须显式开启；fixture 适配器不需要网络，保持 disabled
        self.network = "live" if allow_network else "disabled"
        self.allow_network = allow_network

    @staticmethod
    def capabilities() -> list[str]:
        return ["read_tables", "read_columns", "read_indexes"]

    def _base(self, **fields):
        return {"network": self.network, "classification": "UNVERIFIED", **fields}

    def _load(self):
        return self.adapter.read()

    @staticmethod
    def _tables(payload):
        raw = payload.get("tables", {})
        if isinstance(raw, list):
            raw = {str(t.get("name")): t for t in raw
                   if isinstance(t, Mapping) and t.get("name")}
        if not isinstance(raw, Mapping):
            raise ValueError("MySQL fixture tables must be an object or list")
        return {str(k): dict(v) for k, v in raw.items() if isinstance(v, Mapping)}

    def read_tables(self) -> ProviderResult[dict[str, Any]]:
        base = self._base(tables=[], metadata={})
        loaded = self._load()
        if not loaded.ok:
            return ProviderResult(base, error=loaded.error)
        try:
            tables = self._tables(loaded)
        except ValueError as exc:
            return ProviderResult(base, error=ProviderError("parse", str(exc)))
        base.update(tables=sorted(tables), metadata=tables, classification="PASS")
        return ProviderResult(base)

    def read_table(self, table: str, *, columns: list[str] | None = None) -> ProviderResult[dict[str, Any]]:
        base = self._base(table=table, columns=[], indexes=[])
        loaded = self._load()
        if not loaded.ok:
            return ProviderResult(base, error=loaded.error)
        try:
            item = self._tables(loaded).get(table)
        except ValueError as exc:
            return ProviderResult(base, error=ProviderError("parse", str(exc)))
        if item is None:
            base["classification"] = "FAIL"
            return ProviderResult(base, error=ProviderError(
                "not_found", f"MySQL table was not found: {table}", {"table": table}))
        cols = item.get("columns", [])
        indexes = item.get("indexes", [])
        if not isinstance(cols, list) or not isinstance(indexes, list):
            base["classification"] = "FAIL"
            return ProviderResult(base, error=ProviderError(
                "parse", "table columns/indexes must be lists", {"table": table}))
        if columns is not None:
            cols = [c for c in cols if isinstance(c, Mapping) and c.get("name") in columns]
        base.update(columns=cols, indexes=indexes, classification="PASS")
        return ProviderResult(base)

    def query(self, sql: str, params: tuple | list | None = None) -> ProviderResult[None]:
        base = self._base(sql=sql)
        reason = _deny_reason(sql)
        if reason:
            base["classification"] = "DENIED"
            return ProviderResult(base, error=ProviderError(
                "permission", reason, {"sql": sql[:200]}))
        if not self.allow_network:
            base["classification"] = "BLOCKED"
            return ProviderResult(base, error=ProviderError(
                "unavailable", "network access is disabled",
                {"allow_network": False}))
        run = getattr(self.adapter, "query", None)
        if run is None:
            base["classification"] = "BLOCKED"
            return ProviderResult(base, error=ProviderError(
                "unavailable",
                "adapter 不支持 live 查询（fixture 适配器只读快照，直连请用 MySQLConnectionAdapter）"))
        try:
            rows = run(sql, params)
        except _ConnFailure as exc:
            base["classification"] = ("DENIED" if exc.kind == "permission" else "FAIL")
            return ProviderResult(base, error=exc.error)
        except Exception as exc:  # 适配器其他异常也不静默
            base["classification"] = "FAIL"
            return ProviderResult(base, error=ProviderError(
                "unavailable", f"provider 查询异常: {type(exc).__name__}",
                {"message": str(exc)[:200]}))
        base.update(classification="PASS", rows=rows, row_count=len(rows))
        return ProviderResult(base)


__all__ = ["MySQLFixtureAdapter", "MySQLConnectionAdapter", "MySQLReadonlyProvider"]
