"""Config loader — assembles source jar refs from config/ (no hardcoded machine paths).

铁律 040402: 代码/测试/文档/契约禁止写死 jar 绝对路径/版本号/网关/appId/凭据，一律引用
config/。本模块从 config/environments.yaml（environments[env].maven_root）+ 
config/artifact-versions.yaml（path_template）组装 source jar ref。

纯 pyyaml；模块级读一次并缓存（lru_cache）。只 import yaml + pathlib，
registry.py 可安全 import 本模块，无循环导入。
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # 分发给别人时未必装了 pyyaml
    yaml = None  # type: ignore[assignment]


def _need_yaml():
    """缺 pyyaml 时给可操作的错误，而不是裸 ModuleNotFoundError。

    ★ 不能在模块级 raise —— registry / deployment 会 import 本模块，
      MCP 的 tools/list 也走这条路；模块级 raise 会让"列工具"这一步直接 internal error，
      用户看到的是一句没有线索的 internal error，根本不知道要去装包。
    """
    if yaml is None:
        raise ModuleNotFoundError(
            "缺少 pyyaml。安装：pip install 'pyyaml>=6.0'（在仓库根也可 pip install -e .）"
        )

# _config_loader.py 在 components/platform_operations/，上溯 2 级 = 仓库根。
_REPO_ROOT = Path(__file__).resolve().parents[2]
_ENVIRONMENTS = _REPO_ROOT / "config" / "environments.yaml"
_ARTIFACT_VERSIONS = _REPO_ROOT / "config" / "artifact-versions.yaml"
_DEFAULT_TEMPLATE = "{maven_root}/{artifact}/{version}/{artifact}-{version}.jar"


@lru_cache(maxsize=None)
def _load_environments() -> dict:
    _need_yaml()
    with _ENVIRONMENTS.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache(maxsize=None)
def _load_path_template() -> str:
    _need_yaml()
    with _ARTIFACT_VERSIONS.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data.get("path_template", _DEFAULT_TEMPLATE)


def source_jar_ref(stem: str, version: str, env: str = "local-maven") -> str:
    """返回某 Maven artifact 的 jar:file 源引用（机器路径不写死，全走 config/）。

    maven_root 取自 config/environments.yaml 的 environments[env].maven_root；
    目录布局取自 config/artifact-versions.yaml 的 path_template。
    结果形如 jar:file:///<MAVEN_REPO>/com/seeyon/<stem>/<version>/<stem>-<version>.jar。
    """
    envs = _load_environments().get("environments", {})
    maven_root = envs.get(env, {}).get("maven_root")
    if not maven_root:
        raise KeyError(f"config/environments.yaml: environments[{env!r}].maven_root missing")
    rel = _load_path_template().format(
        maven_root=maven_root, artifact=stem, version=version
    )
    rel = rel.replace("\\", "/")
    return f"jar:file:///{rel}"


# ── S6-CONFIG-PROJECTS-NACOS-ACCESSOR : 3 pure-read accessors (offline · 0 live/SSH/DB · credential 值 0) ──
# config/environments.yaml 已并入 projects + nacos_endpoints 段（S6-CONFIG-PROJECTS-MERGE 面）
# 本 accessor 仅 yaml.safe_load 本地读取·0 触网·不写仓·不升 READONLY-LIVE FACT（活体读取仍归 live 门控）

@lru_cache(maxsize=None)
def _load_projects() -> dict:
    """纯读 accessor：返回 config/environments.yaml 的 projects 顶层段（离线·本地·无 live）。"""
    return _load_environments().get("projects") or {}


@lru_cache(maxsize=None)
def _load_nacos_endpoints() -> dict:
    """纯读 accessor：返回 config/environments.yaml 的 nacos_endpoints 顶层段（离线·本地·无 live）。"""
    return _load_environments().get("nacos_endpoints") or {}


def project_ref(app_id: str) -> dict:
    """纯读 accessor：返回 projects[app_id] 全块（display/running_profile/k8s_namespace/nacos/key_refs）。

    据实不臆造：app_id 未知 → KeyError；nacos 键含 endpoint_ref/tenant/group/dataIds，
    key_refs 值走 Nacos 只读（config 内 redacted/占位符，本 accessor 不载 secret 真值）。
    """
    projects = _load_projects()
    if app_id not in projects:
        raise KeyError(f"config/environments.yaml: projects[{app_id!r}] not found (known: {sorted(projects)})")
    return projects[app_id]


def nacos_endpoint_ref(endpoint_ref: str) -> dict:
    """纯读 accessor：返回 nacos_endpoints[endpoint_ref] 全块（kind/host_hint/port/protocol/readonly/credential）。

    credential 悂 2 键 {ref, file}（占位符/仓库外路径，无 secret 真值）。
    据实不臆造：endpoint_ref 未知 → KeyError。
    """
    endpoints = _load_nacos_endpoints()
    if endpoint_ref not in endpoints:
        raise KeyError(f"config/environments.yaml: nacos_endpoints[{endpoint_ref!r}] not found (known: {sorted(endpoints)})")
    return endpoints[endpoint_ref]


def nacos_key_source(app_id: str, key: str) -> str:
    """纯读 accessor：返回 projects[app_id].key_refs[key].source（dataId/group/tenant 三元组字符串）。

    据实不臆造：app_id 或 key 缺失 / 该 key 无 source 字段 → KeyError。
    不解析三元组为独立数据·不触 Nacos·不外推可读活体。
    """
    block = project_ref(app_id)
    key_refs = block.get("key_refs") or {}
    entry = key_refs.get(key)
    if entry is None:
        raise KeyError(f"config/environments.yaml: projects[{app_id!r}].key_refs[{key!r}] not found")
    if not isinstance(entry, dict) or "source" not in entry:
        raise KeyError(f"config/environments.yaml: projects[{app_id!r}].key_refs[{key!r}] has no 'source' field")
    return entry["source"]
