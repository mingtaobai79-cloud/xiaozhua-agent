"""配置文件读取：仓库内的通用骨架 + 机器本地的覆盖层。

分发模型：

* `config/environments.yaml` —— 跟着仓库走，只有**骨架和占位符**（`<MAVEN_REPO>`、
  `*.example.com`），任何人都能 `git clone` 后看懂结构。
* `config/environments.local.yaml` —— 只在本机存在，写真实环境（主机、命名空间、
  appId、租户、凭据引用路径），**不进 git**。

读取时后者深合并覆盖前者，所以代码只认 `environments[env][key]`，不关心值从哪来。
本机没有 local 文件时，骨架里的占位符会照常读出来（`<MAVEN_REPO>` 这类），
调用方拿到占位符就该报「未配置」而不是拿它去连库。
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = _REPO_ROOT / "config"
BASE = CONFIG_DIR / "environments.yaml"
# 本机覆盖层两个位置都认：仓库工作区里、或装机后的 ~/.xiaozhua/config/
LOCALS = (
    CONFIG_DIR / "environments.local.yaml",
    Path.home() / ".xiaozhua" / "config" / "environments.local.yaml",
)


def _deep_merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


@lru_cache(maxsize=None)
def load() -> dict[str, Any]:
    """返回合并后的环境配置；两文件都不存在时返回空 dict（不抛，让调用方决定）。"""
    import yaml

    def _read(path: Path) -> dict[str, Any]:
        if not path.is_file():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    merged = _read(BASE)
    for path in LOCALS:
        merged = _deep_merge(merged, _read(path))
    return merged


def reload() -> dict[str, Any]:
    """清缓存后重读（测试/诊断用）。"""
    load.cache_clear()
    return load()


def env(env: str) -> dict[str, Any]:
    return (load().get("environments") or {}).get(env) or {}


def is_placeholder(value: Any) -> bool:
    """`<MAVEN_REPO>` / `<仓库外路径>` 这类骨架占位符，当「未配置」对待。"""
    text = str(value or "")
    return text.startswith("<") and text.endswith(">")


def source_files() -> list[str]:
    return [str(p) for p in (BASE, *LOCALS) if p.is_file()]