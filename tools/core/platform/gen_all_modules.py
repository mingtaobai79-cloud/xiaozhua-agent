# -*- coding: utf-8 -*-
"""批量生成所有应用模块 README 并汇总待定语义数。

用法: python gen_all_modules.py [--only slug1,slug2]
"""
import os, sys, json, io, subprocess, re

REPO = "C:/Users/白明涛/xiaozhua-agent"
T = f"{REPO}/tools/core/platform"

MODULES = [
    # (domain, pkg, slug, group, name, title)
    ("organization", None, "organization", "03-business-app", "organization", "组织架构（organization）"),
    ("bpm", None, "bpm", "03-business-app", "bpm", "流程（bpm）"),
    ("ctp", "affair", "ctp-affair", "03-business-app", "ctp-affair", "协同事项（affair）"),
    ("ctp", "user", "ctp-user", "03-business-app", "ctp-user", "用户中心（user）"),
    ("ctp", "message", "ctp-message", "03-business-app", "ctp-message", "消息通知（message）"),
    ("cip", "connector", "cip-connector", "03-business-app", "cip-connector", "连接器（connector）"),
    ("cip", "capability", "cip-capability", "03-business-app", "cip-capability", "集成能力（capability）"),
    ("cip", "provider", "cip-provider", "03-business-app", "cip-provider", "集成提供方（provider）"),
    ("ctp", "application", "ctp-other", "03-business-app", "ctp-other", "应用管理/日志/媒体（application·manager·media·log·metadata）"),
    ("cip", "application", "cip-other", "03-business-app", "cip-other", "集成周边（application·plug·basic·convert·openapi·custom）"),
    ("udc", None, "udc", "02-udc", "udc", "低代码平台（udc）"),
    ("boot", None, "boot", "01-platform", "boot", "平台内核（boot）"),
    ("cdp", None, "cdp", "03-business-app", "cdp", "数据平台（cdp）"),
    ("app", None, "app", "03-business-app", "app", "通用应用（app）"),
    ("portal", None, "portal", "03-business-app", "portal", "门户（portal）"),
    ("m5", None, "m5", "03-business-app", "m5", "移动端（m5）"),
    ("ocip", None, "ocip", "03-business-app", "ocip", "开放集成（ocip）"),
    ("ai", None, "ai", "03-business-app", "ai", "AI 能力（ai）"),
    ("devops", None, "devops", "01-platform", "devops", "运维（devops）"),
    ("gateway", None, "gateway", "01-platform", "gateway", "网关（gateway）"),
    ("maven", None, "maven", "01-platform", "maven", "构建插件（maven）"),
    ("MyMojo", None, "mymojo", "01-platform", "mymojo", "构建 Mojo（MyMojo）"),
]


def run(argv):
    """argv 为列表；参数全部来自本文件内的 MODULES 常量，无外部输入。"""
    r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    only = None
    if "--only" in sys.argv:
        only = set(sys.argv[sys.argv.index("--only") + 1].split(","))

    rows = []
    for dom, pkg, slug, group, name, title in MODULES:
        if only and slug not in only:
            continue
        # 1) facade json
        pj = f"{REPO}/docs/audit/artifacts/facade/{slug}.json"
        if not os.path.exists(pj):
            argv = [sys.executable, f"{T}/dump_facade.py", dom, "--slug", slug]
            if pkg:
                argv += ["--pkg", pkg]
            rc, out = run(argv + ["--json"])
            if rc:
                print(f"  ✗ facade {slug}: {out[:200]}")
                continue
        # 2) README
        argv = [sys.executable, f"{T}/gen_module_readme.py", dom,
                "--slug", slug, "--group", group, "--name", name, "--title", title]
        if pkg:
            argv += ["--pkg", pkg]
        rc, out = run(argv)
        if rc:
            print(f"  ✗ gen {slug}: {out[-300:]}")
            continue
        m = re.search(r"接口 (\d+) / 方法 (\d+) / 服务 (\d+) / 事件 (\d+) / 监听 (\d+) "
                      r"/ Controller (\d+) / 待定语义 (\d+)", out)
        if m:
            rows.append((slug,) + tuple(int(x) for x in m.groups()))
        else:
            print(f"  ? {slug}: 无法解析 {out[-120:]}")

    print(f"\n{'模块':<18}{'接口':>6}{'方法':>8}{'服务':>6}{'事件':>6}{'监听':>6}{'Ctrl':>6}{'待定':>6}")
    print("-" * 62)
    t = [0] * 7
    for r in rows:
        print(f"{r[0]:<18}{r[1]:>6}{r[2]:>8}{r[3]:>6}{r[4]:>6}{r[5]:>6}{r[6]:>6}{r[7]:>6}")
        for i in range(7):
            t[i] += r[i + 1]
    print("-" * 62)
    print(f"{'合计':<18}{t[0]:>6}{t[1]:>8}{t[2]:>6}{t[3]:>6}{t[4]:>6}{t[5]:>6}{t[6]:>6}")
    return 0


if __name__ == "__main__":
    sys.exit(main())