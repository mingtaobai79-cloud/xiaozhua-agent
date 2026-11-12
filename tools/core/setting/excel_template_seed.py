"""设置域 · 导入导出模板：建两个样本（导入 + 导出）供用户验收。

后台 JSON 优先（用户 2026-10-21 指示），不点页面。

用法：
  python tools/core/setting/excel_template_seed.py --port 9231 \
      --entity 郑杰验证实体 --dump                # 只读：拉实体元数据 + 现有模板
  python tools/core/setting/excel_template_seed.py --port 9231 \
      --entity 郑杰验证实体 --i-have-write-authorization   # 建模板
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from components.udc.setting.excel_template_constraints import (  # noqa: E402
    build_column, build_template_body, validate_template_body,
)

APP_ID = None  # ★ 由 --app-id / SEEYON_APP_ID 提供
APP_ID = __import__("os").environ.get("SEEYON_APP_ID") or APP_ID

APP_GUID = "2275741415570096882"
APP_NAME = ""   # 运行时从 udc_application 解析，仓库内不落客户应用名

BASE = ""   # 主机名从当前页面 location.origin 取，仓库内不落客户域名


def resolve_app_name(rows, app_id):
    """从实体列表里反查应用名，避免硬编码客户标识。"""
    for r in rows or []:
        fn = str(r.get("fullName") or "")
        if fn.startswith("com.seeyon."):
            seg = fn.split(".")[2]
            if seg.startswith(str(app_id)) or seg.endswith(str(app_id)):
                return seg
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--entity", default="郑杰验证实体", help="实体中文名")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\excel-seed")
    a = ap.parse_args()

    import urllib.request
    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    pages = [t for t in tgts if t.get("type") == "page" and "lowcode-test2" in t.get("url", "")]
    from providers.cdp import CdpClient
    c = CdpClient(a.port, allow_network=True, timeout=120)
    c.connect(target=pages[0])

    def post(path, body):
        js = ("(async()=>{const r=await fetch('%s',{method:'POST',credentials:'include',"
              "headers:{'Content-Type':'application/json'},body:%s});return await r.text();})()"
              % (path, json.dumps(json.dumps(body, ensure_ascii=False))))
        raw = c.evaluate(js, await_promise=True)
        try:
            return json.loads(raw)
        except Exception:
            return {"raw": raw[:400]}

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    # ---- 1) 找实体
    ents = post("/service/udc/graphql?udcEntitySelectAllByAppidAppGet",
                {"appId": APP_ID}) if False else None
    # 实体列表走 GraphQL；这里改用它（页面就是这么拉的）
    def gql_get(op, path_params):
        q = ("query graphqlLoader ($params0: %sInputPath) { \n"
             "  data0: %s(path: $params0) { code message status data { content } } }" % (op, op))
        payload = {"query": q, "variables": {"params0": path_params}}
        js = ("(async()=>{const r=await fetch('/service/udc/graphql?%s',{method:'POST',credentials:'include',"
              "headers:{'Content-Type':'application/json'},body:%s});return await r.text();})()"
              % (op, json.dumps(json.dumps(payload, ensure_ascii=False))))
        try:
            return json.loads(c.evaluate(js, await_promise=True))["data"]["data0"]
        except Exception as exc:
            return {"error": str(exc)[:200]}

    el = gql_get("udcEntitySelectAllByAppidAppGet", {"appId": APP_ID})
    content = (el.get("data") or {}).get("content") or []
    target = None
    for e in content:
        if isinstance(e, dict) and a.entity in str(e.get("caption") or ""):
            target = e
            break
    if not target:
        print(f"没找到实体「{a.entity}」。可用实体：")
        for e in content[:20]:
            print("  ", e.get("caption"), "|", e.get("fullName"))
        c.close()
        return 1

    app_name = resolve_app_name(content, APP_ID)
    globals()["APP_NAME"] = app_name or APP_NAME
    full_name = target.get("fullName")
    print(f"实体: {target.get('caption')}  fullName={full_name}  id={target.get('id')}")

    # ---- 2) 拉实体属性（Excel 列来源）—— 走 DB，比 GraphQL 直接
    def db_attrs(entity_id):
        env = {}
        ep = Path(r"<HERMES_HOME>\skills\seeyon\01-platform\seeyon-low-code-environment\.env")
        for line in ep.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, sep, v = line.partition("=")
            if sep:
                env[k.strip()] = v.strip().strip('"').strip("'")
        from providers.mysql_readonly import MySQLConnectionAdapter
        db = MySQLConnectionAdapter(host=env.get("SEEYON_DB_HOST", ""),
                                    port=env.get("SEEYON_DB_PORT") or 3306,
                                    user=env.get("SEEYON_DB_USERNAME", ""),
                                    password=env.get("SEEYON_DB_PASSWORD", ""))
        rows = db.query(
            "SELECT name, caption, data_type, multi_select, is_not_null, "
            "relation_app, relation_entity, relation_type, db_column_name, order_no "
            "FROM udc_test2.udc_attribute WHERE entity_id=%s ORDER BY order_no", (entity_id,))
        db.close()
        return rows

    # 先试 GraphQL，失败回落 DB（DB 是权威）
    al = gql_get("udcAttributeSelectAllByEntityIdAppGet",
                 {"appId": APP_ID, "entityId": str(target.get("id"))})
    attrs = (al.get("data") or {}).get("content") or []
    if not attrs:
        attrs = db_attrs(target.get("id"))
        print(f"（属性走 DB 读取：{len(attrs)} 个）")
    print(f"属性数: {len(attrs)}")
    for at in attrs[:10]:
        print("  ", at.get("name"), "|", at.get("caption"), "|", at.get("data_type"))

    # ---- 3) 现有模板
    cur = post("/service/udc/excel/search",
               {"pageInfo": {"pageNumber": 1, "pageSize": 50},
                "params": {"appId": APP_ID, "mainFullName": full_name}})
    items = ((cur.get("data") or {}).get("content") or [])
    print(f"\n该实体现有模板: {len(items)}")
    for t in items:
        print("  ", t.get("id"), "|", t.get("name"), "| isImport=", t.get("isImport"))

    (out / "dump.json").write_text(json.dumps(
        {"entity": target, "attributes": attrs, "templates": items},
        ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"\n-> {out/'dump.json'}")

    if a.dump or not a.i_have_write_authorization:
        print("只读模式，未写入。加 --i-have-write-authorization 才建模板。")
        c.close()
        return 0

    # ---- 4) 建两个模板（导入 + 导出）
    if not attrs:
        print("拿不到实体属性，无法建模板")
        c.close()
        return 2

    cols = []
    for at in attrs:
        fname = at.get("name")
        afn = f"{full_name}.{fname}"
        cols.append(build_column(
            afn,
            at.get("caption") or fname,
            data_type=str(at.get("data_type") or "STRING"),
            java_type="java.lang.String",
            entity_type="MASTER_ENTITY",
            level_path=[[APP_NAME, full_name,
                         target.get("caption") or "", afn,
                         at.get("caption") or fname]],
            column_type=None,
            relation="NONE",
            relation_app=APP_NAME,
            cur_col_index=len(cols),
        ))
    sheets = [cols]

    results = []
    for is_import, label in ((True, "导入"), (False, "导出")):
        body = build_template_body(
            APP_ID, APP_GUID,
            name=f"验收{label}模板",
            main_full_name=full_name,
            sheets=sheets,
            app_name=APP_NAME,
            is_import=is_import,
            is_custom=False,   # false 才进 search 列表（search 强制 isCustom=false）
        )
        errs = validate_template_body(body)
        print(f"\n[{label}] 本地校验: {errs or '✅ 通过'}  （{len(cols)} 列）")
        if errs:
            results.append({"label": label, "errors": errs})
            continue
        r = post("/service/udc/excel/create-template", body)
        ok = r.get("status") == 0
        print(f"{'✅' if ok else '❌'} {label}模板: "
              + (f"id={r['data']}" if ok else json.dumps(r, ensure_ascii=False)[:250]))
        results.append({"label": label, "ok": ok,
                        "id": (r.get("data") if ok else None),
                        **({} if ok else {"resp": r})})
        if not ok:
            break

    (out / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    print(f"\n-> {out/'result.json'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
