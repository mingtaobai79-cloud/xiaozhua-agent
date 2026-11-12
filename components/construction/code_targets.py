# -*- coding: utf-8 -*-
"""components/construction/code_targets.py — 客开代码该写在哪。

**为什么需要它**：客开不是「生成模板填进去」，而是「知道往哪写 + 拉代码 + 自己写」。
这个模块只回答第一件事：给定应用和目标，返回要写的路径与约束。

事实来源：
  core/facts/standard-product/code-repo-and-targets.md
  core/facts/standard-product/extension-project-skeleton.md
  core/facts/udc/page/custom-page-dev-server-glob.md

★ 模块里不含任何域名。git-base 由调用方传，或从已有 clone 的 remote 反推。
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

# 目标 → 说明
TARGETS = {
    "custom_service": "自定义服务（微流程「自定义服务」节点可选的 AppService）",
    "custom_page": "自定义页面（pc/src/pages/<pageUrl>/customPage.tsx）",
    "spi": "SPI / 扩展点实现（extend/ 下 implements 某个扩展点）",
    "entity_ext": "实体扩展（注解、DTO、枚举等自由客开代码）",
}

# 五模块工程的模块名后缀
FIVE_MODULES = ("-facade", "-biz", "-web", "-ext", "-assemble")


def detect_project_shape(backend_dir: str) -> Dict[str, Any]:
    """判断后端工程是五模块还是单模块，并给出根包路径。

    ★ 不要默认五模块 —— 两种形态在同一套规则下并存（实测样本是单模块）。
    """
    root = Path(backend_dir)
    pom = root / "pom.xml"
    if not pom.exists():
        return {"shape": "UNKNOWN", "reason": "pom.xml 不存在", "root": str(root)}

    text = pom.read_text(encoding="utf-8", errors="replace")
    mods = re.findall(r"<module>([^<]+)</module>", text)

    if mods:
        ext = [m for m in mods if m.endswith("-ext")]
        artifact = re.search(r"<artifactId>([^<]+)</artifactId>", text)
        base_pkg = "com.seeyon." + (artifact.group(1) if artifact else "<appName>")
        return {"shape": "FIVE_MODULE", "modules": mods,
                "ext_module": ext[0] if ext else None,
                "base_package": base_pkg,
                "writable_root": str(root / ext[0] / "src/main/java")
                if ext else None,
                "root": str(root)}

    # 单模块：找 com/seeyon/<appName>
    src = root / "src" / "main" / "java"
    pkg_dir = None
    if src.exists():
        for p in src.glob("com/seeyon/*"):
            if p.is_dir():
                pkg_dir = p
                break
    return {
        "shape": "SINGLE_MODULE",
        "base_package": ("com.seeyon." + pkg_dir.name) if pkg_dir else None,
        "writable_root": str(pkg_dir) if pkg_dir else None,
        "root": str(root),
        "note": "单模块工程的「自定义服务」该放哪个包 —— UNVERIFIED，"
                "样本仓库里没有 custom/service 目录，写之前先确认",
    }


def repo_url(git_base: str, app_name: str, side: str = "backend") -> str:
    """拼仓库地址。★ git_base 必须由调用方给，本模块不猜域名。"""
    if not git_base:
        raise ValueError(
            "git_base 必填。域名与仓库组是环境配置（如 <host>/<repo-group>），"
            "不是常量 —— 本仓没有「平台返回 git 地址」的证据，不臆造。")
    if side not in ("backend", "frontend"):
        raise ValueError("side 只能是 backend 或 frontend")
    return "%s/%s/%s.git" % (git_base.rstrip("/"), side, app_name)


def repo_url_from_local(repo_dir: str) -> Optional[str]:
    """从已有 clone 的 remote 反推仓库地址（拿不到返回 None，不猜）。"""
    try:
        p = subprocess.run(["git", "-C", repo_dir, "remote", "get-url", "origin"],
                           capture_output=True, text=True, timeout=20,
                           encoding="utf-8", errors="replace")
        url = (p.stdout or "").strip()
        return url or None
    except Exception:
        return None


def git_base_from_local(repo_dir: str) -> Optional[str]:
    """从已有 clone 反推 git_base（去掉 /backend/<app>.git 或 /frontend/<app>.git）。"""
    url = repo_url_from_local(repo_dir)
    if not url:
        return None
    m = re.match(r"^(.*?)/(backend|frontend)/[^/]+(?:\.git)?$", url)
    return m.group(1) if m else None


def targets_for(target: str, app_name: str, *,
                backend_dir: str = "", frontend_dir: str = "",
                page_url: str = "", extension_point: str = "") -> Dict[str, Any]:
    """给定目标，返回该写哪些文件 + 约束。**不含死模板源码** —— 代码由调用方写。

    target: custom_service / custom_page / spi / entity_ext
    """
    if target not in TARGETS:
        raise ValueError("未知 target %r；可用：%s" % (target, ", ".join(TARGETS)))

    out: Dict[str, Any] = {"target": target, "meaning": TARGETS[target],
                           "appName": app_name}

    if target == "custom_page":
        if not page_url:
            raise ValueError("custom_page 需要 page_url")
        out.update({
            "side": "frontend",
            "files": [{
                "path": "pc/src/pages/%s/customPage.tsx" % page_url,
                "side": "frontend",
                "note": "React 组件，默认导出。可自由实现，不是死模板",
            }],
            "artifact": "custom-page-%s.js" % page_url,
            "route": "/main/portal/%s/%s" % (app_name, page_url),
            "constraints": [
                "★新建目录后必须重启 dev server，否则页面显示 hello world",
                "  syf dev-udc-custom 启动时一次性 glob src/pages/**/customPage.tsx",
                "接口调用用 fetch + credentials:'include'，走 /service/... 网关前缀",
            ],
            "reference": "core/facts/udc/page/custom-page-dev-server-glob.md",
        })
        if frontend_dir:
            out["local_root"] = frontend_dir
        return out

    if not backend_dir:
        raise ValueError("%s 需要 backend_dir（用于探工程形态）" % target)

    shape = detect_project_shape(backend_dir)
    out["projectShape"] = shape
    base = shape.get("base_package") or "com.seeyon." + app_name

    if target == "custom_service":
        if shape["shape"] == "FIVE_MODULE":
            files = [
                {"path": "%s-facade/src/main/java/%s/custom/service/" % (app_name, base.replace(".", "/")),
                 "side": "backend", "note": "自定义服务**接口**。微流程「自定义服务」节点能选到的候选就是这里"},
                {"path": "%s-biz/src/main/java/%s/custom/appservice/" % (app_name, base.replace(".", "/")),
                 "side": "backend", "note": "接口的**实现**"},
            ]
        else:
            files = [{"path": (shape.get("writable_root") or "<root>"),
                      "side": "backend",
                      "note": "★单模块形态：自定义服务该放哪个包 UNVERIFIED，先确认再写"}]
        out.update({
            "files": files,
            "howItWorks": "定义接口+DTO → 构建 → 微流程「自定义服务」节点用 "
                          "udcMicroflowSearchAppServiceByAppNamePost 就能搜到它",
            "flowNodeChain": "选应用 → SearchAppServiceByAppName → SearchMethodByName"
                             "（拿出入参+md5）→ FindCustomDto（拿 attributes）→ 填参",
            "constraints": [
                "★不要往 facade/biz/web/assemble 里改已有生成物 —— 重建即整包覆盖",
                "扩展点实现要自己注册：平台没有 META-INF/services，也没有 spring.factories",
            ],
            "reference": "core/facts/standard-product/extension-project-skeleton.md",
        })
        return out

    if target == "spi":
        out.update({
            "files": [{"path": (shape.get("writable_root") or "<root>") + "/extend/",
                       "side": "backend",
                       "note": "implements 某个扩展点；类名自定"}],
            "extensionPoint": extension_point or "<待指定>",
            "catalog": "docs/audit/artifacts/extension-surface-20261029/extension-points.md（157 行表格，151 个可选）",
            "constraints": [
                "★ext 默认只有一个 package-info.java，平台不预置任何钩子",
                "★注册要自己写：无 META-INF/services、无 spring.factories 自动装配",
                "★不要拿生成的 Abstract*Controller 当继承抓手 —— 它随元数据变",
            ],
        })
        return out

    if target == "entity_ext":
        out.update({
            "files": [{"path": (shape.get("writable_root") or "<root>") + "/extend/",
                       "side": "backend", "note": "自由客开代码"}],
            "constraints": ["只写 extend/ 下的内容，其余模块重新构建会覆盖"],
        })
        return out

    return out
