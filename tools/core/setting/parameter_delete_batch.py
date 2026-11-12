"""设置域 · 参数批量删除执行器（受控写）。

⚠ 注意：`udcCtpParameterDefinitonDeletePost` 只认**单条** body `{appId, id}`。
   `{appId, ids:[...]}` 返回 content=0（0 条），不是批量删。

纪律：
  1. 只删传入的 id 列表，不做任何二次推断
  2. 逐个删 + 逐条 DB 回读（is_delete=1 或行消失）
  3. 失败即停，不重试
  4. progress.json 可续跑
  5. 必须显式 --i-have-write-authorization

用法：
  python tools/core/setting/parameter_delete_batch.py \
      --app-id <id> --ids-file <json 数组文件> --port 9231 \
      --i-have-write-authorization
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

DB = "udc_test2"
TABLE = "ctp_parameter_definition"


def env():
    p = Path(r"<HERMES_HOME>\skills\seeyon\01-platform\seeyon-low-code-environment\.env")
    d = {}
    for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, sep, v = line.partition("=")
        if sep:
            d[k.strip()] = v.strip().strip('"').strip("'")
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-id", required=True)
    ap.add_argument("--ids-file", required=True, help="JSON 数组文件，每项为参数 id")
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--out", default="", help="progress.json 目录，默认与 ids-file 同目录")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    a = ap.parse_args()
    if not a.i_have_write_authorization:
        print("写操作需显式确认：加 --i-have-write-authorization")
        return 1

    from providers.mysql_readonly import MySQLConnectionAdapter
    from providers.cdp import CdpClient

    ids = json.loads(Path(a.ids_file).read_text(encoding="utf-8"))
    outdir = Path(a.out) if a.out else Path(a.ids_file).parent
    prog_path = outdir / "parameter-progress.json"
    done: list[str] = []
    if prog_path.exists():
        done = json.loads(prog_path.read_text(encoding="utf-8")).get("deleted", [])
        print(f"续跑：已完成 {len(done)}")

    e = env()
    conn = MySQLConnectionAdapter(host=e.get("SEEYON_DB_HOST", ""), port=e.get("SEEYON_DB_PORT") or 3306,
                                  user=e.get("SEEYON_DB_USERNAME", ""),
                                  password=e.get("SEEYON_DB_PASSWORD", ""))
    client = CdpClient(a.port, allow_network=True, timeout=90)
    client.connect(url_substr="lowcode-test2")

    q = ("mutation graphqlLoader ($params0: udcCtpParameterDefinitonDeletePostInputBody) { \n"
         "  data0: udcCtpParameterDefinitonDeletePost(body: $params0) "
         "{ code message status data { content } } }")

    def call(body):
        payload = {"query": q, "variables": {"params0": body}}
        js = ("(async()=>{const r=await fetch('/service/udc/graphql?udcCtpParameterDefinitonDeletePost',"
              "{method:'POST',credentials:'include',"
              "headers:{'Content-Type':'application/json'},body:%s});return await r.text();})()"
              % json.dumps(json.dumps(payload, ensure_ascii=False)))
        raw = client.evaluate(js, await_promise=True)
        return json.loads(raw)["data"]["data0"]

    todo = [i for i in ids if str(i) not in done]
    before = conn.query(f"SELECT COUNT(*) n FROM {DB}.{TABLE} WHERE app_id=%s AND is_delete=0",
                        (a.app_id,))[0]["n"]
    print(f"待删 {len(todo)} / 总 {len(ids)} | 删前有效参数 {before}")

    ok, fail = 0, None
    for n, pid in enumerate(todo, 1):
        row = conn.query(f"SELECT id,name,caption FROM {DB}.{TABLE} WHERE id=%s", (pid,))
        if not row:
            done.append(str(pid))
            continue
        try:
            r = call({"appId": a.app_id, "id": str(pid)})
        except Exception as exc:
            fail = {"id": pid, "stage": "request", "error": str(exc)[:200]}
            break
        if r.get("status") != 0:
            fail = {"id": pid, "stage": "biz", "resp": r}
            break
        # 回读：行仍在但 is_delete=1 也算删成功（逻辑删除）
        back = conn.query(f"SELECT id,is_delete FROM {DB}.{TABLE} WHERE id=%s", (pid,))
        if back and int(back[0].get("is_delete") or 0) == 0:
            fail = {"id": pid, "stage": "readback", "resp": r, "row": back[0]}
            break
        if not back:
            pass  # 物理删除也接受
        done.append(str(pid))
        ok += 1
        prog_path.write_text(json.dumps({"deleted": done, "failed": None}, ensure_ascii=False),
                             encoding="utf-8")
        if n % 10 == 0 or n <= 3:
            print(f"  {n:>3}/{len(todo)}  {row[0]['name']}  content={r.get('content')}")

    after = conn.query(f"SELECT COUNT(*) n FROM {DB}.{TABLE} WHERE app_id=%s AND is_delete=0",
                       (a.app_id,))[0]["n"]
    if fail:
        prog_path.write_text(json.dumps({"deleted": done, "failed": fail}, ensure_ascii=False),
                             encoding="utf-8")
        print(f"\n❌ 失败即停：{json.dumps(fail, ensure_ascii=False)[:300]}")
    print(f"\n已删 {ok} / 本轮 {len(todo)} | 有效参数 {before} → {after}")
    client.close()
    conn.close()
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
