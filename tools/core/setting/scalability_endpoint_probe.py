"""B-1/B-2 探针：扩展实体的 delete 端点 + data-type 端点。

只在有有效会话时跑（CDP 会话过期时 fetch 会卡在 SSO 重定向）。
按「以后台 JSON 为先」直发 REST，不点页面。

用法：
  python tools/core/setting/scalability_endpoint_probe.py --list
  python tools/core/setting/scalability_endpoint_probe.py --run \
      --app-id <appId> --option-id <要删的方案id> --i-have-write-authorization

⚠ delete 是写操作，会真的删方案。默认只跑 data-type（只读）；
  delete 必须显式加 --confirm-delete 且给 --option-id。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

ENDPOINTS = {
    "data_types": {
        "method": "GET",
        "path": "/service/udc/scalability-option/data-type/{app_id}",
        "write": False,
        "desc": "扩展实体可用的数据类型清单（界面「数据类型」下拉的候选源）",
    },
    "select_by_appid": {
        "method": "GET",
        "path": "/service/udc/scalability-option/select-by-appid/with-detail/{app_id}",
        "write": False,
        "desc": "读方案（含预留组明细）",
    },
    "delete": {
        "method": "POST",
        "path": "/service/udc/scalability-option/delete",
        "write": True,
        "desc": "删方案（body 形态待验：{id} / bare Long / {appId,id}）",
    },
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--target-prefix", default="A886072E")
    ap.add_argument("--app-id", default=None)
    ap.add_argument("--option-id", default=None, help="delete 的目标方案 id")
    ap.add_argument("--probe-set-id", default=None,
                    help="会话探测用的字段集 id（任何存在的 id 均可）")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--confirm-delete", action="store_true",
                    help="delete 是写操作，必须显式确认")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    a = ap.parse_args()

    if a.list or not a.run:
        print("扩展实体端点探针：\n")
        for k, v in ENDPOINTS.items():
            tag = "写" if v["write"] else "读"
            print(f"  {k:<16} [{tag}] {v['method']:<4} {v['path']}")
            print(f"  {'':16} {v['desc']}")
        if not a.run:
            return 0

    if not a.app_id:
        print("必须给 --app-id")
        return 1

    from providers.cdp import CdpClient

    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    cand = [t for t in tgts if t.get("type") == "page"
            and str(t.get("id", "")).startswith(a.target_prefix)]
    if not cand:
        print(f"找不到 {a.target_prefix} 标签页")
        return 2
    c = CdpClient(a.port, allow_network=True, timeout=90)
    c.connect(target=cand[0])

    # 会话健康检查：★ 发真实只读请求判断，不看 document.cookie
    #   document.cookie 只显示非 HttpOnly 的 cookie；会话 token 是 HttpOnly，
    #   所以「cookie 只有 SY_UID/TK_EXP」完全可能是正常会话（2026-10-22 误判过一次）。
    probe = c.evaluate(
        "fetch('/service/udc/attributeSet/select-attribute-list',{method:'POST',"
        "credentials:'include',headers:{'Content-Type':'application/json'},"
        f"body:JSON.stringify({{attributeSetId:'{a.probe_set_id or '-1'}'}})}})"
        ".then(r=>r.status).catch(e=>'ERR:'+e.message)",
        await_promise=True)
    print(f"会话探测: status={probe}")
    if not (isinstance(probe, int) and probe in (200, 400, 500)):
        print("⚠ 会话不可用（fetch 卡住或被 SSO 重定向）——先恢复登录")
        c.close()
        return 3

    def get(path, to=40):
        js = (f"fetch('{path}',{{credentials:'include'}})"
              ".then(async r=>JSON.stringify({status:r.status,body:(await r.text()).slice(0,20000)}))"
              ".catch(e=>'ERR:'+e.message)")
        try:
            return json.loads(c.evaluate(js, await_promise=True))
        except Exception as e:
            return {"err": type(e).__name__, "detail": str(e)[:100]}

    def post(path, body, to=40):
        js = (f"fetch('{path}',{{method:'POST',credentials:'include',"
              f"headers:{{'Content-Type':'application/json'}},"
              f"body:{json.dumps(json.dumps(body, ensure_ascii=False))}}})"
              ".then(async r=>JSON.stringify({status:r.status,body:(await r.text()).slice(0,20000)}))"
              ".catch(e=>'ERR:'+e.message)")
        try:
            return json.loads(c.evaluate(js, await_promise=True))
        except Exception as e:
            return {"err": type(e).__name__, "detail": str(e)[:100]}

    out = {}
    print("\n1) data-type（只读）...")
    out["data_types"] = get(ENDPOINTS["data_types"]["path"].format(app_id=a.app_id))
    print(f"   {json.dumps(out['data_types'], ensure_ascii=False)[:300]}")

    print("\n2) select-by-appid/with-detail（只读）...")
    out["select"] = get(ENDPOINTS["select_by_appid"]["path"].format(app_id=a.app_id))
    print(f"   {json.dumps(out['select'], ensure_ascii=False)[:220]}")

    if a.confirm_delete and a.option_id:
        if not a.i_have_write_authorization:
            print("\n⚠ delete 需 --i-have-write-authorization")
        else:
            print(f"\n3) delete 方案 {a.option_id} ...")
            for label, body in [
                ("{id}", {"id": a.option_id}),
                ("bare Long", a.option_id),
                ("{appId,id}", {"appId": a.app_id, "id": a.option_id}),
                ("{appId,ids:[id]}", {"appId": a.app_id, "ids": [a.option_id]}),
            ]:
                r = post(ENDPOINTS["delete"]["path"], body)
                snippet = json.dumps(r, ensure_ascii=False)[:260]
                print(f"   {label:<18} {snippet}")
                out[f"delete_{label}"] = r
                # 首个成功的就停（避免重复删）
                if '"BOOT_0000"' in snippet:
                    print("   ↑ 成功，停止后续变体")
                    break
    else:
        print("\n3) delete 跳过（需 --confirm-delete 且 --option-id）")

    p = Path(a.out if hasattr(a, "out") else
             r"<HERMES_HOME>\cache\scratch\scalability-probe")
    p.mkdir(parents=True, exist_ok=True)
    (p / "result.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
    print(f"\n-> {p / 'result.json'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
