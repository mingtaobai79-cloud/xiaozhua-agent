# -*- coding: utf-8 -*-
"""UDC 手写扩展工程的「可用依赖面」模型（可执行约束）。

权威来源：`tools/core/platform/extract_extension_surface.py` 的实测产出
（`docs/audit/artifacts/extension-surface-<yyyymmdd>/surface.json`）。

★ 核心判据（用户 2026-10-29 口述 + 工程实测）：
  一个 UDC 应用的手写代码**能引用什么包，由该扩展工程的依赖解析结果决定**，
  不由平台全量构件决定。所以「我可以 import 这个类吗」的答案必须来自：
    后端  ext 工程 classpath（target/compile_args.txt 的 -cp）
    前端  pc/package.json + node_modules/@seeyon/*
  而不是「jar 在 maven 仓库里存在」。

★ 反模式：拿 maven 仓库里 com/seeyon/ 下 124 个构件当可用清单 ——
  那里面大部分不在任何应用的 classpath 里（版本也未必一致）。

用法：
    from components.udc.extension_surface import (
        load_surface, assert_backend_jar, assert_frontend_package,
        backend_artifacts, frontend_packages, SurfaceError,
    )
    s = load_surface("docs/audit/artifacts/extension-surface-20261029/surface.json")
    assert_backend_jar(s, "udc-facade")        # 不在 classpath → 抛错
    assert_frontend_package(s, "@seeyon/ui")   # 不在 dependencies → 抛错
"""
from __future__ import annotations

import json
from pathlib import Path

# 平台侧「手写扩展代码必须落在」的包路径约定（README 明文，非客户值）
BACKEND_EXTEND_PACKAGE = "com/seeyon/{app_name}/extend"
BACKEND_MYBATIS_DIR = "src/main/resources/mybatis"
BACKEND_INIT_DIRS = ("src/main/resources/init/tenant", "src/main/resources/init/file/private")

# 前端扩展工程的结构约定（实测：pc/ 与 mobile/ 并列，页面入口 customPage.tsx）
FRONTEND_ENTRY_TEMPLATE = "src/pages/{page_key}/customPage.tsx"
FRONTEND_PORTALS = ("pc", "mobile")

# 前端页面运行时路由：/main/portal/<应用编码>/<页面标识>（用户手册明文）
PORTAL_ROUTE_TEMPLATE = "/main/portal/{app_code}/{page_key}"


class SurfaceError(RuntimeError):
    """依赖面校验失败（fail-closed：不在清单里就必须报错，不许静默当作可用）。"""


def load_surface(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise SurfaceError(f"依赖面证据件不存在：{p}（先跑 extract_extension_surface.py）")
    data = json.loads(p.read_text(encoding="utf-8"))
    if "sources" not in data:
        raise SurfaceError(f"{p} 不是依赖面证据件（缺 sources 键）")
    return data


def _backend(surface: dict) -> dict:
    b = surface.get("sources", {}).get("backend")
    if not b:
        raise SurfaceError("证据件无 backend 段")
    return b


def _frontend(surface: dict) -> dict:
    f = surface.get("sources", {}).get("frontend")
    if not f:
        raise SurfaceError("证据件无 frontend 段")
    return f


def backend_artifacts(surface: dict) -> dict[str, str]:
    """classpath 里的 xiaozhua 构件 → {artifactId: version}。"""
    jars = _backend(surface)["compile_classpath"]["jars"]
    return {j["artifact"]: j["version"] for j in jars if j.get("group") == "com.seeyon"}


def all_classpath_artifacts(surface: dict) -> dict[str, str]:
    jars = _backend(surface)["compile_classpath"]["jars"]
    return {j["artifact"]: j["version"] for j in jars}


def declared_pom_dependencies(surface: dict, include_parent: bool = True) -> list[dict]:
    """工程显式声明的依赖（自有 + parent）。"""
    b = _backend(surface)["pom"]
    out = list(b.get("own_dependencies") or [])
    if include_parent:
        out += list(b.get("parent_dependencies") or [])
    return out


def frontend_packages(surface: dict) -> dict[str, str]:
    """node_modules/@seeyon/* → {包名: 版本}。"""
    return {p["package"]: p.get("version") for p in _frontend(surface).get("xiaozhua_packages", [])
            if "package" in p}


def frontend_declared(surface: dict) -> dict[str, str]:
    """package.json 里显式声明的 @seeyon 依赖（dependencies + devDependencies）。"""
    pj = _frontend(surface).get("package_json") or {}
    out: dict[str, str] = {}
    for k in ("dependencies", "devDependencies"):
        for name, ver in (pj.get(k) or {}).items():
            if name.startswith("@seeyon/"):
                out[name] = ver
    return out


def assert_backend_jar(surface: dict, artifact: str) -> str:
    """断言某后端构件在 classpath 内；返回版本号。不在则抛 SurfaceError。"""
    arts = all_classpath_artifacts(surface)
    if artifact not in arts:
        near = [a for a in arts if artifact.split("-")[0] in a][:8]
        raise SurfaceError(
            f"构件 {artifact} 不在扩展工程 classpath 内，手写代码无法 import。"
            + (f" 相近可用：{near}" if near else ""))
    return arts[artifact]


def assert_frontend_package(surface: dict, package: str) -> str | None:
    """断言某前端包已安装；返回版本（可能为 None）。未安装则抛 SurfaceError。"""
    pkgs = frontend_packages(surface)
    if package not in pkgs:
        raise SurfaceError(f"前端包 {package} 未安装到 node_modules/@seeyon/，无法 import")
    return pkgs[package]


def check_frontend_package(surface: dict, package: str) -> tuple[str, str]:
    """前端包的可用性三态判定 → (状态, 说明)。

    实测三种真实情形（都用同一个工程验过）：
      DECLARED     package.json 里显式声明        → 最稳，跟着 lockfile 走
      HOISTED      未声明，但被 @seeyon/* 传递依赖带进顶层 node_modules
                   （实测 lodash 4.17.21 就是这样：@seeyon/global、@seeyon/syf 等 5 个包依赖它）
                   → **今天能 import，但不受 lockfile 保护**：上游一换版本或改依赖树就可能断，
                     要用就先在 package.json 里补声明
      MISSING      哪里都没有                      → 必须走 third_modules 四步流程
    """
    pj = _frontend(surface).get("package_json") or {}
    declared = set((pj.get("dependencies") or {})) | set((pj.get("devDependencies") or {}))
    installed = frontend_packages(surface)
    if package in declared:
        return "DECLARED", f"{package} 在 package.json 声明（{declared and (pj.get('dependencies', {}) | pj.get('devDependencies', {})).get(package)}）"
    if package.startswith("@seeyon/") and package in installed:
        return "DECLARED", f"{package} 属平台预置包（v{installed[package]}），随 syf 提供"
    # 非 @seeyon 的包：看 node_modules 顶层有没有（hoisted）
    top = _frontend(surface).get("hoisted_top_level") or {}
    if package in top:
        return "HOISTED", (
            f"{package} 未在 package.json 声明，但作为传递依赖已落到 node_modules（v{top[package]}）。"
            "今天能 import，但不受 lockfile 保证 —— 用之前先在 package.json 里补声明")
    return "MISSING", (
        f"{package} 既不在 package.json 也不在 node_modules —— "
        "须走 third_modules 流程（third_modules 安装 → syf build-multiple-bundless-module "
        "→ webpack alias → tsconfig paths），否则构建期解析不到")


def require_third_party_justification(surface: dict, package: str) -> str:
    """非平台包的前置校验。返回状态；HOISTED 允许但需调用方登记说明；MISSING 抛错。"""
    state, msg = check_frontend_package(surface, package)
    if state == "MISSING":
        raise SurfaceError(msg)
    return state


def runtime_route(app_code: str, page_key: str) -> str:
    """自定义页面的门户路由（本地 dev 与线上同一形态）。"""
    return PORTAL_ROUTE_TEMPLATE.format(app_code=app_code, page_key=page_key)


def entry_path(page_key: str) -> str:
    """页面入口文件相对路径。"""
    return FRONTEND_ENTRY_TEMPLATE.format(page_key=page_key)
