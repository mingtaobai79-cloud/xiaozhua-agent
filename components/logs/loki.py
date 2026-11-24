# -*- coding: utf-8 -*-
"""Loki 日志查询（只读）。

走 Grafana 的 datasource proxy：`{grafana}/api/datasources/proxy/{id}/loki/api/v1/*`，
用 Grafana 账号（basic auth）或 API token。不直连 Loki 3100 —— 那是集群内地址，
本机不可达；Grafana 的 proxy 已经把鉴权和租户选好了。

配置（非机密，不进仓库）放 `~/.xiaozhua/logs.yaml`，环境名与 datasource 都由使用者自己定：

```yaml
environments:
  <env-name>:
    grafana: https://grafana.example.com      # 你的 Grafana 根地址
    datasource: <loki datasource 名字或 id>    # 名字会先查 /api/datasources
```

工具本身不认识任何具体环境：不写死主机、命名空间、app、pod。

凭据只从环境变量取：`GRAFANA_USER` / `GRAFANA_PASSWORD`，或 `GRAFANA_TOKEN`
（Bearer，优先生效）。本模块不读、不写任何密码文件。
"""
from __future__ import annotations

import base64
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path.home() / ".xiaozhua" / "logs.yaml"
TIMEOUT = 30


class LokiError(RuntimeError):
    pass


# ------------------------------------------------------------------ 配置
def _config_path() -> Path:
    return Path(os.environ.get("XIAOZHUA_LOKI_CONFIG") or DEFAULT_CONFIG).expanduser()


def load_config() -> dict[str, Any]:
    path = _config_path()
    if not path.exists():
        return {"environments": {}}
    import yaml  # 依赖已在 pyproject 里（pyyaml）

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data.setdefault("environments", {})
    return data


def env_names() -> list[str]:
    return sorted(load_config()["environments"])


def _env_conf(env: str) -> dict[str, Any]:
    if not env:
        raise LokiError(
            f"必须指定 env（{_config_path()} 里的 environments 键之一："
            f"{', '.join(env_names()) or '尚未配置'}）")
    conf = load_config()["environments"].get(env)
    if not conf:
        raise LokiError(
            f"未配置环境 {env}；在 {_config_path()} 里加 environments.{env} "
            f"（现有：{', '.join(env_names()) or '无'}）")
    return conf


def _auth_headers() -> dict[str, str]:
    token = os.environ.get("GRAFANA_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}"}
    user = os.environ.get("GRAFANA_USER")
    pwd = os.environ.get("GRAFANA_PASSWORD")
    if not (user and pwd):
        raise LokiError("缺凭据：设置 GRAFANA_USER/GRAFANA_PASSWORD，或 GRAFANA_TOKEN")
    raw = f"{user}:{pwd}".encode("utf-8")
    return {"Authorization": "Basic " + base64.b64encode(raw).decode("ascii")}


def _get(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers=_auth_headers())
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise LokiError(f"HTTP {exc.code} {url.split('?')[0]} → {detail}") from exc
    except Exception as exc:  # noqa: BLE001
        raise LokiError(f"请求失败 {url.split('?')[0]} → {exc}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise LokiError(f"返回不是 JSON：{body[:200]}") from exc


def _datasource_id(env: str) -> tuple[str, str]:
    """返回 (grafana 根地址, datasource 数字 id)。名字会先查一次 /api/datasources。"""
    conf = _env_conf(env)
    grafana = str(conf.get("grafana") or os.environ.get("GRAFANA_URL") or "").rstrip("/")
    if not grafana:
        raise LokiError(f"环境 {env} 缺 grafana 地址（配置里 grafana: 或 GRAFANA_URL）")
    ds = conf.get("datasource")
    if ds is None:
        raise LokiError(f"环境 {env} 缺 datasource（名字或数字 id）")
    if str(ds).isdigit():
        return grafana, str(ds)

    listing = _get(f"{grafana}/api/datasources")
    for item in listing:
        if item.get("name") == ds:
            return grafana, str(item["id"])
    names = [i.get("name") for i in listing if i.get("type") == "loki"]
    raise LokiError(f"找不到 datasource {ds!r}；可选：{', '.join(sorted(names))}")


# ------------------------------------------------------------------ 查询
def _logql(namespace: str, app: str, pod: str, grep: str, query: str) -> str:
    if query.strip():
        return query.strip()
    parts = []
    if namespace:
        parts.append(f'namespace=~"{namespace}"')
    if app:
        parts.append(f'app=~"{app}"')
    if pod:
        parts.append(f'pod=~"{pod}"')
    selector = "{" + ",".join(parts) + "}" if parts else '{namespace=~".+"}'
    if grep:
        selector += f' |= "{grep}"'
    return selector


def search(env: str = "", query: str = "", namespace: str = "",
           app: str = "", pod: str = "", grep: str = "", minutes: int = 15,
           limit: int = 200, direction: str = "backward") -> dict[str, Any]:
    """按时间窗拉日志。返回 {env, datasource, query, streams, lines[], stats}。

    lines 里每条是 {ts, pod, app, line}，按时间倒序，最多 limit 条。
    """
    grafana, ds_id = _datasource_id(env)
    expr = _logql(namespace, app, pod, grep, query)
    now = time.time()
    start = int((now - max(1, minutes) * 60) * 1e9)
    end = int(now * 1e9)
    data = _get(
        f"{grafana}/api/datasources/proxy/{ds_id}/loki/api/v1/query_range",
        {"query": expr, "start": start, "end": end,
         "limit": max(1, min(limit, 5000)), "direction": direction},
    )
    result = (data.get("data") or {}).get("result") or []
    lines: list[dict[str, Any]] = []
    for stream in result:
        labels = stream.get("stream") or {}
        for ts, line in stream.get("values") or []:
            ns = int(ts)
            lines.append({
                "_ns": ns,
                "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ns / 1e9)),
                "pod": labels.get("pod", ""),
                "app": labels.get("app", ""),
                "line": line,
            })
    # 按原始纳秒排序，别按格式化到秒的字符串（同秒内会乱序）
    lines.sort(key=lambda x: x["_ns"], reverse=(direction == "backward"))
    for item in lines:
        item.pop("_ns", None)
    truncated = len(lines) > limit
    return {
        "env": env, "datasource": ds_id, "query": expr,
        "window_minutes": minutes,
        "streams": len(result),
        "returned": min(len(lines), limit),
        "truncated": truncated,
        "lines": lines[:limit],
    }


def labels(env: str = "", label: str = "") -> dict[str, Any]:
    """列 label 名；给了 label 就返回它的取值（用来发现 app/pod/namespace）。"""
    grafana, ds_id = _datasource_id(env)
    base = f"{grafana}/api/datasources/proxy/{ds_id}/loki/api/v1"
    if label:
        data = _get(f"{base}/label/{urllib.parse.quote(label)}/values")
    else:
        data = _get(f"{base}/labels")
    return {"env": env, "label": label or None, "values": (data.get("data") or [])}


def doctor() -> dict[str, Any]:
    """连通性自检：配置了什么环境、每个环境能否列 label。"""
    out: dict[str, Any] = {"config": str(_config_path()), "environments": {}}
    for env in env_names():
        try:
            got = labels(env=env)
            out["environments"][env] = {"ok": True, "labels": len(got["values"])}
        except Exception as exc:  # noqa: BLE001
            out["environments"][env] = {"ok": False, "error": str(exc)[:200]}
    return out