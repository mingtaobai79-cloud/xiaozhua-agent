#!/usr/bin/env python
"""批量删除自定义对象（受控写）。

前置：tools/core/setting/custom_object_delete_precheck.py 已产出 precheck.json
      （含阳性对照通过的 candidates 清单 + 全量行备份）

纪律：
  1. 只删 precheck.json 里 candidates 的 id，不做任何二次推断
  2. 逐个删（平台无批量删除 operation）
  3. 每个都回读 DB 确认消失；失败即停，不重试
  4. 进度实时写进 progress.json，中断可续（已删的跳过）
  5. 必须显式 --i-have-write-authorization

用法：
  python tools/core/setting/custom_object_delete_batch.py \
      --precheck <precheck.json> --port 9231 --i-have-write-authorization [--limit N]
"""
from __future__ import annotations

import argparse, json, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

DB = "udc_test2"
TABLE = "udc_data_transfer_object"

Q = ("mutation graphqlLoader ($params0: udcDataTransferObjectDeletePostInputBody) { \n"
     "  data0: udcDataTransferObjectDeletePost(body: $params0) "
     "{ code data { content } message status } }")


def env():
    p = Path(r"<HERMES_HOME>\skills\xiaozhua\01-platform\xiaozhua-low-code-environment\.env")
    d = {}
    for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, sep, v = line.partition("=")
        if sep:
            d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def gql(client, op, body):
    payload = {"query": Q, "variables": {"params0": body}}
    raw = client.evaluate(f"""(async () => {{
      const r = await fetch('/service/udc/graphql?{op}', {{
        method:'POST', credentials:'include',
        headers:{{'Content-Type':'application/json','Accept':'application/json'}},
        body: {json.dumps(json.dumps(payload, ensure_ascii=False))}
      }});
      const t = await r.text();
      let j=null; try{{j=JSON.parse(t);}}catch(e){{}}
      const d=j&&j.data&&j.data.data0;
      return JSON.stringify({{http:r.status, code:d&&d.code, biz:d&&d.status,
        msg:String((d&&d.message)||'').slice(0,160),
        content:d&&d.data&&d.data.content, trace:j&&j.traceId}});
    }})()""", await_promise=True)
    return json.loads(raw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--precheck", required=True)
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--i-have-write-authorization", action="store_true")
    a = ap.parse_args()
    if not a.i_have_write_authorization:
        print("写操作需显式确认：加 --i-have-write-authorization")
        return 1

    from providers.mysql_readonly import MySQLConnectionAdapter
    from providers.cdp import CdpClient

    pre = json.loads(Path(a.precheck).read_text(encoding="utf-8"))
    app_id = pre["app_id"]
    pf = Path(a.precheck).parent
    prog_path = pf / "progress.json"
    done = set()
    if prog_path.exists():
        done = set(json.loads(prog_path.read_text(encoding="utf-8")).get("deleted", []))
        print(f"续跑：已完成 {len(done)}")

    e = env()
    conn = MySQLConnectionAdapter(host=e.get("XIAOZHUA_DB_HOST", ""), port=e.get("XIAOZHUA_DB_PORT") or 3306,
                                  user=e.get("XIAOZHUA_DB_USERNAME", ""), password=e.get("XIAOZHUA_DB_PASSWORD", ""))

    port = a.port
    if not port:
        pf2 = Path(r"<HERMES_HOME>\cache\scratch\live_port.txt")
        port = int(pf2.read_text().strip()) if pf2.exists() else 9231
    client = CdpClient(port, allow_network=True, timeout=90)
    client.connect(url_substr="lowcode-test2")

    candidates = [c for c in pre["candidates"] if c["id"] not in done]
    if a.limit:
        candidates = candidates[: a.limit]
    print(f"待删 {len(candidates)} / 候选 {len(pre['candidates'])}")

    before = conn.query(f"SELECT COUNT(*) n FROM {DB}.{TABLE} WHERE app_id=%s", (app_id,))[0]["n"]
    print(f"删除前对象数 {before}")

    ok, fail = 0, None
    deleted = list(done)
    for i, c in enumerate(candidates, 1):
        oid = c["id"]
        body = {"appId": app_id, "id": oid}
        try:
            r = gql(client, "udcDataTransferObjectDeletePost", body)
        except Exception as exc:
            fail = {"id": oid, "stage": "request", "error": str(exc)[:200]}
            break
        # 回读判定（成功码不代表删掉了）
        left = conn.query(f"SELECT id FROM {DB}.{TABLE} WHERE id=%s", (oid,))
        if left:
            fail = {"id": oid, "name": c["name"], "stage": "readback", "resp": r}
            break
        deleted.append(oid)
        ok += 1
        prog_path.write_text(json.dumps({"deleted": deleted, "failed": None}, ensure_ascii=False), encoding="utf-8")
        if i % 20 == 0 or i <= 3:
            print(f"  {i:>3}/{len(candidates)}  {c['name'][:34]:<36} code={r.get('code')} trace={str(r.get('trace'))[:12]}")

    after = conn.query(f"SELECT COUNT(*) n FROM {DB}.{TABLE} WHERE app_id=%s", (app_id,))[0]["n"]
    if fail:
        prog_path.write_text(json.dumps({"deleted": deleted, "failed": fail}, ensure_ascii=False), encoding="utf-8")
        print(f"\n❌ 失败即停：{json.dumps(fail, ensure_ascii=False)[:300]}")
    print(f"\n已删 {ok} / 本轮 {len(candidates)}  对象数 {before} → {after}")
    client.close()
    conn.close()
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
