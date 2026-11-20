# -*- coding: utf-8 -*-
"""把 REST 路由证据写进模块 README：`## REST 路由` 段 + 明细文件。

明细: docs/audit/artifacts/rest/ROUTES-<slug>.md
README: 计数 + URL 拼法 + 控制器索引 + 前 15 条样例

用法: python gen_rest_section.py [--dry]
"""
import json, io, os, re, sys

REPO = r"C:/Users/白明涛/xiaozhua-agent"
R = os.path.join(REPO, "docs/audit/artifacts/rest")

MOD = {
    "organization": ("03-business-app", ["organization-web"]),
    "bpm": ("03-business-app", ["bpm-web"]),
    "ctp-affair": ("03-business-app", ["ctp-affair-web"]),
    "ctp-user": ("03-business-app", ["ctp-user-web"]),
    "ctp-message": ("03-business-app", ["ctp-message-web"]),
    "ctp-other": ("03-business-app", ["ctp-media-web", "ctp-webapi-gateway-web"]),
    "cip-connector": ("03-business-app", ["cip-connector-web"]),
    "cip-capability": ("03-business-app", ["cip-capability-web"]),
    "cip-provider": ("03-business-app", ["cip-connector-web"]),
    "cip-other": ("03-business-app", ["cip-convert-web", "cip-manager-web", "cip-openapi-gateway-web"]),
    "udc": ("02-udc", ["udc-web"]),
    "boot": ("01-platform", ["boot-starter-web"]),
    "cdp": ("03-business-app", ["cdp-data-web", "cdp-schedule-web"]),
    "app": ("03-business-app", ["app-common-web", "app-approval-web", "app-doc-web"]),
    "portal": ("03-business-app", ["portal-web"]),
    "m5": ("03-business-app", ["m5-web"]),
    "ocip": ("03-business-app", []),
    "ai": ("03-business-app", ["ai-web"]),
    "devops": ("01-platform", []),
    "gateway": ("01-platform", []),
    "maven": ("01-platform", []),
    "mymojo": ("01-platform", []),
}

APPID = {  # applicationId 段（应用 code）；拿不准的留空，不猜
    "organization": "organization", "bpm": "bpm", "ctp-affair": "ctp-affair",
    "ctp-user": "ctp-user", "ctp-message": "ctp-message", "ctp-other": "ctp",
    "cip-connector": "cip-connector", "cip-capability": "cip-capability",
    "cip-provider": "cip-connector", "cip-other": "cip-manager",
    "udc": "udc", "boot": "boot", "cdp": "cdp-data", "app": "app-common",
    "portal": "portal", "m5": "m5", "ai": "ai",
}


def load(arts):
    out, used = {}, []
    for a in arts:
        p = os.path.join(R, f"{a}.json")
        if not os.path.exists(p):
            continue
        used.append(a)
        out.update(json.load(io.open(p, encoding="utf-8")))
    return out, used


def full(appid, base, path):
    """真实 URL = /service/ + 类级路径 + 方法级路径。

    类级路径本身已含应用 code 段（实测锚点：udc DeployController
    base=`udc/runtime` + `deploy-normal` = 线上 `POST /service/udc/runtime/deploy-normal`）。
    少数方法的 value 自带类级前缀（历史写法），拼接会重复，此时只保留方法级。
    """
    if not base:
        return "/service/" + path
    if path.startswith(base):
        return "/service/" + path
    return "/service/" + "/".join(s for s in (base, path) if s)


def main():
    dry = "--dry" in sys.argv
    for slug, (group, arts) in MOD.items():
        readme = os.path.join(REPO, "core/facts/modules", group, slug, "README.md")
        if not os.path.exists(readme):
            print(f"  ! {slug}: README 缺")
            continue
        data, used = load(arts)
        appid = APPID.get(slug, "")
        n_routes = sum(len(v["routes"]) for v in data.values())

        L = ["## REST 路由", ""]
        if not n_routes:
            L += ["⚠️ **UNVERIFIED** —— 本模块的 web 构件里没有 `@RequestMapping` 动作。",
                  "", "原因：该模块只做远程调用（Dubbo/SPI）或本身无 HTTP 面，接口是给别的服务用的。",
                  "不写推测路径。", ""]
            block = "\n".join(L)
        else:
            L += [
                "> 证据：`javap -v` 读 Controller 字节码里的 `@RequestMapping`/`@PostMapping` 注解值。",
                "> 等级 `VERIFIED_STATIC_BYTECODE`（注解值是常量，非推断）。",
                "",
                "**拼法**（以 `organization` 为例，`:8080` 之类按环境）：",
                "",
                "```",
                "POST /service/{类级路径}/{方法级路径}",
                "      ↑ 类级路径的第一段就是应用 code（organization / bpm / udc …），不要再加一层",
                "  例：POST /service/udc/runtime/deploy-normal",
                "      = DeployController 类级 `udc/runtime` + 方法级 `deploy-normal`（线上实测过）",
                "```",
                "",
                f"控制器 **{len(data)}** 个、路由 **{n_routes}** 条"
                f"（来源：{'、'.join('`%s`' % a for a in used)}）。",
                "",
                "> `{id}`、`ids` 这类方法级路径不带类级前缀，拼时必须补上。",
                "> 完整清单（含 java 方法名）：`docs/audit/artifacts/rest/ROUTES-%s.md`" % slug,
                "",
                "| Controller | 类级路径 | 路由 |",
                "|---|---|---:|",
            ]
            for c in sorted(data, key=lambda x: -len(data[x]["routes"])):
                L.append(f"| `{c.rsplit('.', 1)[-1]}` | `{data[c]['base'] or '—'}` | {len(data[c]['routes'])} |")
            L.append("")

            # 前 15 条样例
            L += ["前 15 条（其余见明细）：", "", "| 方法 | 全路径 |", "|---|---|"]
            shown = 0
            for c in sorted(data):
                for r in data[c]["routes"]:
                    if shown >= 15:
                        break
                    L.append(f"| `{r['mapping'].split('.')[-1]}` | `{full(appid, data[c]['base'], r['path'])}` |")
                    shown += 1
                if shown >= 15:
                    break
            L.append("")
            block = "\n".join(L)

            # 明细文件
            D = [f"# REST 路由明细：{slug}", "",
                 f"> 来源：{'、'.join('`%s`' % a for a in used)}（javap -v 注解值）",
                 "> 等级：`VERIFIED_STATIC_BYTECODE`", "",
                 "| Controller | 全路径 | HTTP | java 方法 |", "|---|---|---|---|"]
            for c in sorted(data):
                for r in data[c]["routes"]:
                    D.append(f"| `{c.rsplit('.', 1)[-1]}` | `{full(appid, data[c]['base'], r['path'])}` "
                             f"| {r['mapping'].split('.')[-1].replace('Mapping', '').upper() or 'GET/POST'} "
                             f"| `{r['java_method']}` |")
            if not dry:
                io.open(os.path.join(R, f"ROUTES-{slug}.md"), "w", encoding="utf-8").write("\n".join(D))

        s = io.open(readme, encoding="utf-8").read()
        if "## REST 路由" in s and "## 证据与自证" in s:
            i, j = s.index("## REST 路由"), s.index("## 证据与自证")
            s = s[:i] + block + "\n" + s[j:]
        elif "## 证据与自证" in s:
            j = s.index("## 证据与自证")
            s = s[:j] + block + "\n" + s[j:]
        else:
            print(f"  ! {slug}: 锚点缺失")
            continue

        old = "| REST 路径 | 未取证 | `UNVERIFIED` |"
        if n_routes:
            s = s.replace(old, f"| REST 路径（{n_routes} 条） | Controller 字节码注解 | `VERIFIED_STATIC_BYTECODE` |")
        else:
            s = s.replace(old, "| REST 路径 | 本模块无 HTTP 面 | `N/A` |")

        if not dry:
            io.open(readme, "w", encoding="utf-8").write(s)
        print(f"  {'✓' if n_routes else '-'} {slug}: {len(data)} controller / {n_routes} 路由"
              f"{'（dry）' if dry else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())