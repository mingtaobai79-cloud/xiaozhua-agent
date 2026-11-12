"""应用域只读面 LIVE 探针（CDP 取浏览器既有会话 cookie → Python HTTP 直发）。

为什么这样发：设计器页面的 window.fetch 打到 /service/ 会被网关断链
（CDP Network 显示 net::ERR_CONNECTION_CLOSED），而浏览器导航与 curl 都正常。
所以沿用本仓既有做法：从 CDP 读同源 session cookie（TK_EXP/SY_UID/SY_ACCESS_TOKEN），
只在单请求生命周期内作为请求头使用，不落盘、不打印、不重签 token。

硬边界：
  * 只允许下方 ALLOWLIST 内的只读端点（GET / 语义为查询的 POST）。
  * 绝不发 app-delta-deploy / app-online / deploy-normal / sandbox flexible
    create|delete|restart / front-log/create / disable-last-version-metadata /
    page-info create|update|delete / dependent-application/delete-by-ids。
  * 输出文件不含 cookie，只含 status / code / traceId / data 形状。

用法：
  python tools/core/application/gateway_readonly_probe.py \
      --port 9250 --app-id <appId> \
      --out <HERMES_HOME>/cache/scratch/app-gql/live-readonly-probe.json
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request

import websocket

DEFAULT_BASE = os.environ.get("UDC_GATEWAY_BASE", "")  # 形如 https://<gateway-host>，不写死客户域名
APP_NAME = "udc"

# (op, method, path, body, 期望 data.content 形态说明)
ALLOWLIST: list[tuple[str, str, str, object, str]] = [
    ("udc.application.get", "GET", "/service/udc/application/{app_id}", None, "对象（控制组）"),
    ("udc.application.user_role", "GET", "/service/udc/application/user-role?appName=" + APP_NAME, None, "角色 id 列表"),
    ("udc.application.role_resource", "GET", "/service/udc/application/role-resource?appName=" + APP_NAME, None, "角色→资源映射"),
    ("udc.deployment.latest_test_info", "POST", "/service/udc/deployment/latest-test-info", {"appId": "{app_id}"}, "最近测试信息"),
    ("udc.application.front_detection", "POST", "/service/udc/application/search/front-detection", {"appId": "{app_id}"}, "前端检测结果"),
    ("udc.sandbox.delta_build_info", "GET", "/service/udc/sandbox/delta-build-info/{app_id}", None, "增量构建信息"),
    ("udc.sandbox.is_deploy_war", "GET", "/service/udc/sandbox/system/config/is-deploy-war", None, "布尔配置"),
    ("udc.sandbox.app_search", "POST", "/service/udc/sandbox/app/search",
     {"pageInfo": {"pageNo": 1, "pageSize": 10}, "params": {}}, "分页列表"),
    ("sandbox.flexible.test_status", "POST", "/service/udc/sandbox/flexible/test-status", None, "弹性测试状态"),
]

WRITE_LIKE = (  # 仅用于自检断言：这些词绝不允许出现在 ALLOWLIST 里
    "app-delta-deploy", "app-online", "deploy-normal", "create-deployment",
    "delete-deployment", "restart-deployment", "front-log/create",
    "disable-last-version-metadata", "delete-by-ids", "page-info/create", "page-info/update",
)


def session_cookies(port: int) -> str:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5) as r:
        tabs = json.loads(r.read().decode("utf-8"))
    host = BASE.split("//", 1)[-1].split("/", 1)[0]
    pages = [t for t in tabs if t.get("type") == "page" and host in (t.get("url") or "")]
    if not pages:
        raise SystemExit("no matching page tab on port %d (host=%s)" % (port, host))
    ws = websocket.create_connection(pages[0]["webSocketDebuggerUrl"], timeout=30,
                                     max_size=None, suppress_origin=True)
    ws.send(json.dumps({"id": 1, "method": "Network.getCookies", "params": {"urls": [BASE + "/"]}}))
    got = None
    ws.settimeout(1)
    limit = time.time() + 15
    while time.time() < limit:
        try:
            raw = ws.recv()
        except Exception:
            continue
        if not raw:
            continue
        m = json.loads(raw)
        if m.get("id") == 1:
            got = m
            break
    ws.close()
    cookies = (got or {}).get("result", {}).get("cookies", [])
    if not cookies:
        raise SystemExit("no cookies returned by CDP")
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


def call(cookie_header: str, method: str, path: str, body: object, timeout: float = 25.0) -> dict:
    url = BASE + path
    data = None
    headers = {"Cookie": cookie_header, "Accept": "application/json, text/plain, */*"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            status = r.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        status = e.code
    except Exception as e:  # 网络层
        return {"http": None, "error": type(e).__name__ + ":" + str(e)[:120],
                "ms": int((time.time() - t0) * 1000)}
    ms = int((time.time() - t0) * 1000)
    text = raw.decode("utf-8", "replace")
    try:
        env = json.loads(text)
    except Exception:
        return {"http": status, "error": "NON_JSON", "bytes": len(raw), "ms": ms,
                "body_head": text[:200]}
    content = ((env.get("data") or {}).get("content") if isinstance(env.get("data"), dict) else None)
    return {
        "http": status,
        "code": env.get("code"),
        "message": env.get("message"),
        "traceId": env.get("traceId"),
        "bytes": len(raw),
        "ms": ms,
        "content_type": type(content).__name__,
        "content_size": len(content) if hasattr(content, "__len__") else None,
        "content_head": (json.dumps(content, ensure_ascii=False)[:300] if content is not None else None),
    }


def verdict_of(res: dict) -> str:
    if "http" not in res or res.get("http") is None:
        return "NETWORK_ERROR"
    if res.get("http") != 200:
        return "FAIL"
    if res.get("code") != "BOOT_0000":
        return "AUTH_REDIRECT" if res.get("code") == "BOOT_1006" else "FAIL"
    ct, cs = res.get("content_type"), res.get("content_size")
    if ct in ("NoneType",) or (cs in (0, None) and ct != "bool"):
        return "CALLED_NO_DATA"
    return "LIVE_PASS"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9250)
    ap.add_argument("--base", default=DEFAULT_BASE, help="网关基址，可用 UDC_GATEWAY_BASE 环境变量")
    ap.add_argument("--app-id", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not args.base:
        raise SystemExit("缺少 --base（或 UDC_GATEWAY_BASE）")
    global BASE
    BASE = args.base.rstrip("/")

    for op, _m, path, _b, _e in ALLOWLIST:
        assert not any(w in path for w in WRITE_LIKE), f"写端点混入只读白名单: {op} {path}"

    cookie_header = session_cookies(args.port)
    print("cookies loaded (names only):",
          [c.split("=")[0] for c in cookie_header.split("; ")])

    rows = []
    for op, method, path, body, expect in ALLOWLIST:
        p = path.replace("{app_id}", args.app_id)
        b = json.loads(json.dumps(body).replace("{app_id}", args.app_id)) if body else None
        res = call(cookie_header, method, p, b)
        res.update({"op": op, "method": method, "path": p, "expect": expect,
                    "verdict": verdict_of(res)})
        rows.append(res)
        print(f"  {res['verdict']:14s} {res.get('http')} {method:4s} {p[:66]}"
              f" code={res.get('code')} ct={res.get('content_type')} n={res.get('content_size')}")

    summary = {
        "total": len(rows),
        "live_pass": sum(1 for r in rows if r["verdict"] == "LIVE_PASS"),
        "called_no_data": sum(1 for r in rows if r["verdict"] == "CALLED_NO_DATA"),
        "fail": sum(1 for r in rows if r["verdict"] not in ("LIVE_PASS", "CALLED_NO_DATA")),
    }
    doc = {"captured_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "base": BASE, "app_id": args.app_id, "auth": "browser session cookie (not persisted)",
           "summary": summary, "probes": rows}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print("summary:", summary, "->", args.out)


if __name__ == "__main__":
    main()
