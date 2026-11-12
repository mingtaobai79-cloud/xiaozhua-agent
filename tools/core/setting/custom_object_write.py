#!/usr/bin/env python
"""自定义对象：删除 / 创建 的端到端执行器（受控写）。

用法：
    python tools/core/setting/custom_object_write.py delete --app-id <id> --object-id <oid>
    python tools/core/setting/custom_object_write.py create --app-id <id> \
        --caption "显示名" --name "objCode" [--app-guid <guid>]
    python tools/core/setting/custom_object_write.py list --app-id <id>

纪律（写操作必须守的）：
  1. **删前必做引用分析**，阳性对照不通过则不下删除结论（失败即停）
  2. 逐个删（平台**无**批量删除 operation）
  3. **成功码不代表删掉了** —— 缺 id 时平台也回 BOOT_0000/content=0
     → 必须回读 DB 核对行数
  4. 失败即停，不重试
  5. 创建走 seeyon-agent 自己的构造器 + 校验器，本地校验不过不提交
  6. 写操作需显式 --i-have-write-authorization 显式确认（fail-closed）

写通道本身（WriteScope + 平台契约）见：
  components/platform_operations/write_scope.py
  components/udc/setting/custom_object_constraints.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]      # tools/core/setting/ → 仓库根
sys.path.insert(0, str(REPO))

from components.udc.setting.custom_object_constraints import (
    build_custom_object_body,
    build_custom_object_delete_body,
    validate_custom_object_body,
    validate_custom_object_delete_body,
)

DB = "udc_test2"
TABLE = "udc_data_transfer_object"


def _env():
    p = Path(r"<HERMES_HOME>\skills\seeyon\01-platform\seeyon-low-code-environment\.env")
    env = {}
    if p.exists():
        for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, sep, v = line.partition("=")
            if sep:
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _conn():
    from providers.mysql_readonly import MySQLConnectionAdapter
    env = _env()
    return MySQLConnectionAdapter(
        host=env.get("SEEYON_DB_HOST", ""),
        port=env.get("SEEYON_DB_PORT") or 3306,
        user=env.get("SEEYON_DB_USERNAME", ""),
        password=env.get("SEEYON_DB_PASSWORD", ""))


def _gql(client, op, query, body):
    payload = {"query": query, "variables": {"params0": body}}
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


# ---------------------------------------------------------------- 引用分析
def reference_check(conn, app_id: str, names: list[str]) -> tuple[bool, dict]:
    """对给定名字做引用核对。先做阳性对照，对照不过则结论不可信。"""
    sources = []
    for label, (table, wanted) in {
        "微流程": ("udc_microflow_info", ["data_schema"]),
        "页面": ("udc_page_schema", ["page_schema", "draft_page_schema"]),
        "页面信息": ("udc_page_info", ["page_schema", "layout_info", "description"]),
        "实体": ("udc_entity", ["description", "table_name"]),
        "资源": ("udc_resource", ["url_parameters", "out_parameters", "description"]),
        "导出模板": ("ctp_excel_export_template", ["metadata_content", "excel_head_info"]),
    }.items():
        try:
            have = {c["COLUMN_NAME"] for c in conn.describe_table(DB, table)["columns"]}
        except Exception:
            continue
        tcols = [c for c in wanted if c in have]
        if not tcols:
            continue
        try:
            rows = conn.query(
                f"SELECT id, {', '.join(tcols)} FROM {DB}.{table} WHERE app_id=%s", (app_id,))
        except Exception:
            continue
        for r in rows:
            blob = " ".join(str(r.get(c) or "") for c in tcols)
            if blob.strip():
                sources.append((label, str(r["id"]), blob))

    ctrl = conn.query(f"SELECT name FROM {DB}.udc_entity WHERE app_id=%s LIMIT 3", (app_id,))
    ctrl_hit = sum(1 for e in ctrl if any(e["name"] in b for _, _, b in sources))
    method_valid = bool(ctrl) and ctrl_hit == len(ctrl)

    detail = {}
    for n in names:
        detail[n] = [f"{k}({i})" for k, i, b in sources if n in b]
    return method_valid, detail


# ---------------------------------------------------------------- 子命令
def cmd_list(conn, app_id):
    rows = conn.query(
        f"SELECT id, name, caption, source, publish_state, create_time "
        f"FROM {DB}.{TABLE} WHERE app_id=%s ORDER BY create_time DESC", (app_id,))
    print(f"自定义对象 {len(rows)} 个（app_id={app_id}）")
    for r in rows:
        print(f"  {str(r['id']):<22} {str(r['name'])[:30]:<32} {str(r['caption'])[:26]}")
    return 0


def cmd_delete(conn, client, app_id, object_id, app_guid, force):
    row = conn.query(
        f"SELECT id, name, caption FROM {DB}.{TABLE} WHERE id=%s AND app_id=%s",
        (object_id, app_id))
    if not row:
        print(f"对象 {object_id} 不存在（app_id={app_id}）")
        return 1
    name = row[0]["name"]

    print("=== 删前引用核对 ===")
    valid, detail = reference_check(conn, app_id, [name])
    if not valid:
        print("  ❌ 阳性对照未通过 → 检测方法有缺口，'无引用'结论不可信，终止")
        return 2
    hits = detail.get(name, [])
    print(f"  {name}: 引用 {hits or '无 ✅'}")
    if hits and not force:
        print("  ❌ 有引用，拒绝删除（--force 可跳过，但请先人工确认）")
        return 3

    body = build_custom_object_delete_body(app_id, object_id)
    errs = validate_custom_object_delete_body(body)
    if errs:
        print(f"  本地校验未过: {errs}")
        return 1

    before = conn.query(f"SELECT COUNT(*) n FROM {DB}.{TABLE} WHERE app_id=%s", (app_id,))[0]["n"]
    q = ("mutation graphqlLoader ($params0: udcDataTransferObjectDeletePostInputBody) { \n"
         "  data0: udcDataTransferObjectDeletePost(body: $params0) "
         "{ code data { content } message status } }")
    r = _gql(client, "udcDataTransferObjectDeletePost", q, body)
    print(f"  平台返回: {json.dumps(r, ensure_ascii=False)[:200]}")
    if r.get("biz") != 0:
        print("  ❌ 失败即停")
        return 1

    left = conn.query(f"SELECT id FROM {DB}.{TABLE} WHERE id=%s", (object_id,))
    after = conn.query(f"SELECT COUNT(*) n FROM {DB}.{TABLE} WHERE app_id=%s", (app_id,))[0]["n"]
    print(f"  回读: {'仍在 ❌' if left else '已删除 ✅'} | 对象数 {before} → {after}")
    return 0 if not left else 1


def cmd_create(conn, client, app_id, app_guid, caption, name, order_no):
    body = build_custom_object_body(app_id, app_guid, caption=caption, name=name,
                                     order_no=order_no)
    print(f"  build : {json.dumps(body, ensure_ascii=False)}")
    errs = validate_custom_object_body(body)
    print(f"  check : {'✅ 通过' if not errs else '❌ ' + str(errs)}")
    if errs:
        return 1
    q = ("mutation graphqlLoader ($params0: udcDataTransferObjectPostInputBody) { \n"
         "  data0: udcDataTransferObjectPost(body: $params0) "
         "{ code data { content } message status } }")
    r = _gql(client, "udcDataTransferObjectPost", q, body)
    print(f"  submit: {json.dumps(r, ensure_ascii=False)[:200]}")
    if r.get("biz") != 0:
        return 1
    new_id = r.get("content")
    row = conn.query(
        f"SELECT id, name, caption, source, publish_state, create_time "
        f"FROM {DB}.{TABLE} WHERE id=%s", (new_id,))
    print("  回读:")
    if row:
        for k, v in row[0].items():
            print(f"    {k:<16} {v}")
    else:
        print("    ❌ DB 未查到")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["delete", "create", "list"])
    ap.add_argument("--app-id", required=True)
    ap.add_argument("--app-guid", default="")
    ap.add_argument("--object-id", default="")
    ap.add_argument("--caption", default="")
    ap.add_argument("--name", default="")
    ap.add_argument("--order-no", type=int, default=100)
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    a = ap.parse_args()

    conn = _conn()
    if a.action == "list":
        return cmd_list(conn, a.app_id)

    if not a.i_have_write_authorization:
        print("写操作需显式确认：加 --i-have-write-authorization")
        return 1

    # 找有有效会话的 CDP 端口
    port = a.port
    if not port:
        from pathlib import Path as _P
        pf = _P(r"<HERMES_HOME>\cache\scratch\live_port.txt")
        port = int(pf.read_text().strip()) if pf.exists() else 9231
    from providers.cdp import CdpClient
    client = CdpClient(port, allow_network=True, timeout=90)
    try:
        client.connect(url_substr="lowcode-test2")
    except Exception as exc:
        print(f"无法连接 CDP {port}: {exc}")
        return 1
    try:
        if a.action == "delete":
            return cmd_delete(conn, client, a.app_id, a.object_id, a.app_guid, a.force)
        return cmd_create(conn, client, a.app_id, a.app_guid, a.caption, a.name, a.order_no)
    finally:
        client.close()
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
