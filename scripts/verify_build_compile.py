#!/usr/bin/env python3
"""触发一次 DELTA 构建并判定后端 Java 编译是否通过。

用途：UDC 微流程「发布 RELEASE」只写元数据，不编译。写操作出参写成 DTO、
写操作直引 FOR_EACH 循环项这类缺陷 checkSchema/发布/UI 全过，只有应用构建生成
Java 时才炸。本脚本是唯一能证明「生成的代码能编译」的手段。

用法：
    python verify_build_compile.py --app 8704025620829192834
    python verify_build_compile.py --app <id> --cdp 9333 --expect-biz-sources 116

前置：浏览器已登录 UDC 环境（低代码设计器页签在），CDP 端口可达。
退出码：0 = BUILD SUCCESS；1 = BUILD FAILURE / 取不到日志；2 = 环境/参数问题。
"""
from __future__ import annotations

import argparse
import json
import re
import os
import sys
import time
import urllib.request

BASE = "http://127.0.0.1"


def cdp_cookies(host: str, port: int) -> str:
    """从 CDP 取当前会话 cookie。"""
    import websocket  # websockets 包（.venv 缺失时 u v pip install websockets）

    targets = json.loads(urllib.request.urlopen(
        "%s:%d/json/list" % (BASE, port), timeout=10).read().decode())
    page = next((t for t in targets
                 if t.get("type") == "page" and host.split("//")[-1].split("/")[0] in t.get("url", "")), None)
    if page is None:
        raise SystemExit("CDP 里没有该环境的页签，先在设计器页面打开一次")
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=30)
    cookies = []
    try:
        ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
        ws.send(json.dumps({"id": 2, "method": "Network.getCookies",
                            "params": {"urls": [host]}}))
        for _ in range(80):          # 跳过事件帧，只等 id==2 的响应
            msg = json.loads(ws.recv())
            if msg.get("id") == 2:
                cookies = (msg.get("result") or {}).get("cookies") or []
                break
    finally:
        ws.close()
    return "; ".join("%s=%s" % (c["name"], c["value"]) for c in cookies
                    if c["name"] in ("SY_UID", "SY_ACCESS_TOKEN"))


class Api:
    def __init__(self, host: str, cookie: str):
        self.host, self.cookie = host.rstrip("/"), cookie

    def req(self, path: str, body=None, method: str = "POST") -> dict:
        data = json.dumps(body if body is not None else {}).encode()
        r = urllib.request.Request(
            self.host + path, data=data, method=method,
            headers={"Content-Type": "application/json;charset=UTF-8",
                     "Cookie": self.cookie})
        return json.loads(urllib.request.urlopen(r, timeout=90).read().decode())

    def raw(self, path: str) -> bytes:
        r = urllib.request.Request(self.host + path, headers={"Cookie": self.cookie})
        return urllib.request.urlopen(r, timeout=90).read()


def trigger_delta(api: Api, app_id: str) -> str:
    """POST deploy-normal；body 必须包成 {"deployDto": {...}}（@MultiRequestBody）。"""
    out = api.req("/service/udc/runtime/deploy-normal",
                  {"deployDto": {"appId": app_id, "deployType": "DELTA",
                                 "projectType": "ALL", "terminalType": "ALL"}})
    content = ((out.get("data") or {}).get("content")) or {}
    deploy_id = content.get("deployId")
    if not deploy_id:
        raise SystemExit("deploy-normal 没返回 deployId：%s" % json.dumps(out)[:300])
    return str(deploy_id)


def wait_build_version(api: Api, deploy_id: str, timeout: int = 300) -> str:
    """⚠ data.content 是数组；buildVersion 出现即可去读编译日志，不必等部署完。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        out = api.req("/service/udc/runtime/search-deploy-status/%s" % deploy_id)
        rows = ((out.get("data") or {}).get("content")) or []
        if isinstance(rows, dict):
            rows = [rows]
        if rows and rows[0].get("buildVersion"):
            return rows[0]["buildVersion"]
        time.sleep(8)
    raise SystemExit("等不到 buildVersion：%s" % deploy_id)


def read_log(api: Api, app_id: str, build_version: str, name: str) -> str | None:
    key = "compile-info/%s/%s/%s" % (app_id, build_version, name)
    try:
        return api.raw("/service/app-sandbox/file/download?storageKey=" + key).decode(
            "utf-8", "replace")
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True, help="应用 appId（纯数字）")
    ap.add_argument("--host", default=os.environ.get("UDC_HOST", ""))
    ap.add_argument("--cdp", type=int, default=9333)
    ap.add_argument("--expect-biz-sources", type=int, default=0,
                    help="预期 biz 模块源文件数；新增流程后应比上次 +1，用来证明新代码真进了编译")
    ap.add_argument("--timeout", type=int, default=420)
    args = ap.parse_args()

    api = Api(args.host, cdp_cookies(args.host, args.cdp))
    deploy_id = trigger_delta(api, args.app)
    print("deployId:", deploy_id)
    bv = wait_build_version(api, deploy_id)
    print("buildVersion:", bv)

    log = None
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        log = read_log(api, args.app, bv, "backBuild.log")
        if log and ("BUILD SUCCESS" in log or "BUILD FAILURE" in log):
            break
        time.sleep(15)
    if not log:
        print("取不到 backBuild.log", file=sys.stderr)
        return 2

    errs = re.findall(r"(\w+\.java:\[\d+,\d+\][^\n]*)", log)
    biz = re.search(r"-biz\] \[INFO\] Compiling (\d+) source files", log)
    ok = "BUILD SUCCESS" in log and not errs
    print("biz 源文件数:", biz.group(1) if biz else "?")
    print("编译报错:", len(errs))
    for e in errs[:10]:
        print("  ", e[:200])

    if args.expect_biz_sources and biz and int(biz.group(1)) != args.expect_biz_sources:
        print("⚠ 源文件数 %s != 预期 %s —— 新流程可能没进本次生成，SUCCESS 不算证据"
              % (biz.group(1), args.expect_biz_sources))
        ok = False

    # 前端日志只作参考
    flog = read_log(api, args.app, bv, "frontBuild.log") or ""
    print("前端 build success:", "build success" in flog.lower(),
          "| ERROR:", flog.count("ERROR"))

    try:
        st = api.req("/service/udc/deployment/app-ready-state", {"appId": args.app})
        c = ((st.get("data") or {}).get("content")) or {}
        print("应用就绪:", c.get("state"), c.get("msg"))
    except Exception as exc:
        print("app-ready-state 查询失败:", str(exc)[:120])

    print("RESULT:", "BUILD OK" if ok else "BUILD FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
