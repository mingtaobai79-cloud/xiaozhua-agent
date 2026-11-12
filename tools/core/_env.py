"""tools 公用环境入口 —— 所有脚本的 appId / 端口 / 环境都从这里来。

为什么有这个文件
----------------
`tools/core/**` 下曾有 16 个脚本各自写死 `APP_ID = "<某个 19 位数字>"`，
或各自抄一段 8 行的 `.env` 解析。后果：
  · 换个应用就要改代码，改了还可能漏改（同一脚本里 11 处）
  · appId 是"某次实测的目标"，写进代码等于把测试值当配置
  · 每份 .env 解析都自己拼路径，挪仓库就全崩

用法
----
    from tools.core._env import bootstrap, resolve_app_id, connect_db

    ap = argparse.ArgumentParser()
    ap.add_argument("--app-id", help="UDC 应用 id（也可用 SEEYON_APP_ID）")
    args, client = bootstrap(ap)          # 建好 CDP 连接
    app_id = resolve_app_id(args.app_id)  # 缺失就报错退出，不给默认值

约定
----
★ **不提供任何默认 appId。** 缺参数就报错 —— 静默用错的 appId
  会把数据写到另一个应用里，比报错危险得多。
★ 数据库凭据只从 .env 读，容器里没有就报错，不硬编码。
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# .env 由外部技能目录提供；允许用环境变量覆盖，便于容器/CI
ENV_FILE = Path(os.environ.get("SEEYON_ENV_FILE")
                or r"<HERMES_HOME>\skills\seeyon\01-platform"
                   r"\seeyon-low-code-environment\.env")
ENV_SCRIPTS = Path(os.environ.get("SEEYON_ENV_SCRIPTS")
                   or r"<HERMES_HOME>\skills\seeyon\01-platform"
                      r"\seeyon-low-code-environment\scripts")

DEFAULT_PORT = int(os.environ.get("SEEYON_CDP_PORT", "0") or 0)


class EnvError(RuntimeError):
    """环境缺失（.env / appId / 数据库凭据）。不静默兜底。"""


def load_env(env: str = "test2") -> dict:
    """加载平台环境配置（数据库等）。找不到 .env 直接报错。"""
    if not ENV_FILE.is_file():
        raise EnvError(
            "找不到环境文件：%s（可用 SEEYON_ENV_FILE 指定）" % ENV_FILE)
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
    if str(ENV_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(ENV_SCRIPTS))
    from env import load_env as _load  # noqa: WPS433  平台自带
    return _load(env)


def resolve_app_id(app_id: str | None, *, required: bool = True) -> str:
    """取 appId：参数 > 环境变量 > 报错。

    ★ 永远不返回默认值。`required=False` 时返回 None（给纯平台级脚本用）。
    """
    val = (app_id or os.environ.get("SEEYON_APP_ID") or "").strip()
    if not val:
        if required:
            raise EnvError(
                "缺少 appId：请传 --app-id，或设环境变量 SEEYON_APP_ID。\n"
                "  （本工具不提供默认 appId —— 用错的 appId 会把数据写到别的应用）")
        return None
    if not val.isdigit():
        raise EnvError("appId 必须是纯数字，收到 %r" % val)
    return val


def resolve_port(port: int | None, *, default: int | None = None) -> int:
    """取 CDP 端口：参数 > 环境变量 > default > 报错。"""
    if port:
        return int(port)
    if DEFAULT_PORT:
        return DEFAULT_PORT
    if default:
        return int(default)
    raise EnvError("缺少 CDP 端口：请传 --port，或设 SEEYON_CDP_PORT")


def connect_db(cfg: dict | None = None, database: str = "udc_test2"):
    """连 UDC 库。凭据只从环境变量取。

    database 必须显式给 —— 连错库读到的"成功"全是假的。
    """
    import pymysql

    cfg = cfg or load_env()
    m = cfg["mysql"]
    user = os.environ.get("SEEYON_DB_USERNAME")
    pwd = os.environ.get("SEEYON_DB_PASSWORD")
    if not user or not pwd:
        raise EnvError("缺数据库凭据：SEEYON_DB_USERNAME / SEEYON_DB_PASSWORD")
    return pymysql.connect(
        host=m["host"], port=int(m["port"]), user=user, password=pwd,
        database=database, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor)


def connect_client(port: int | None = None, *, url_substr: str = "app-design",
                   timeout: int = 60):
    """连 CDP 页面。端口必须显式（或 env），不猜。"""
    from providers.cdp import CdpClient

    c = CdpClient(resolve_port(port), allow_network=True, timeout=timeout)
    c.connect(url_substr=url_substr)
    return c


def bootstrap(parser: argparse.ArgumentParser, *, url_substr: str = "app-design",
              with_client: bool = True, with_app_id: bool = True):
    """给脚本加统一参数并返回 (args, client)。

        ap = argparse.ArgumentParser()
        args, client = bootstrap(ap)
        app_id = resolve_app_id(args.app_id)
    """
    parser.add_argument("--port", type=int, default=None,
                        help="CDP 端口（默认读 SEEYON_CDP_PORT）")
    if with_app_id:
        parser.add_argument("--app-id", default=None,
                            help="UDC 应用 id（默认读 SEEYON_APP_ID）")
    parser.add_argument("--env", default="test2", help="环境名（test2/uat）")
    args = parser.parse_args()
    client = None
    if with_client:
        client = connect_client(args.port, url_substr=url_substr)
    return args, client


def query(conn, sql: str, params=None) -> list:
    """一次查询，返回 dict 列表。"""
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()
