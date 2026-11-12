"""设置域 · 导入导出模板：建一个带「关联实体展开」的样本（用户 2026-10-21 要求）。

用户截图那种下拉框（创建人 ▸ 姓名 ▸ 编号/性别/工作电话…）对应的结构是
**levelPath 两层**：

    levelPath[0] = 本实体字段     [appName, entityFullName, entityCaption,
                                   attrFullName, attrCaption]
    levelPath[1] = 关联实体字段   [relationApp, relationEntityFullName,
                                   relationEntityCaption, relAttrFullName, relAttrCaption]

`attributeFullName` 取**第二层**（关联实体的属性全名），
`displayName` 用「本字段名/子字段名」形式（真实样本就是这样）。

本脚本给「郑杰验证实体」的 ENTITY 类型字段（创建人/创建机构/创建部门/创建岗位）
各展开 2 个子字段，建成两个模板。

用法：
  python tools/core/setting/excel_template_entity_fields.py --dump
  python tools/core/setting/excel_template_entity_fields.py --i-have-write-authorization
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

APP_ID = None  # ★ 由 --app-id / XIAOZHUA_APP_ID 提供
APP_ID = __import__("os").environ.get("XIAOZHUA_APP_ID") or APP_ID

APP_GUID = "2275741415570096882"
APP_NAME = ""          # 运行时解析，仓库内不落客户应用名
ENTITY_ID = "5417588098661281954"   # 郑杰验证实体
ENTITY_FULL = ""       # 运行时解析

# 关联实体的可选子字段（从真实模板样本归纳的通用组织字段）
REL_CANDIDATES = {
    "organization": {
        "full_name": "com.seeyon.organization.domain.core.entity.OrgMember",
        "caption": "人员",
        "fields": [
            ("code", "编号", "java.lang.String", "STRING"),
            ("name", "姓名", "java.lang.String", "STRING"),
            ("mobile", "手机号码", "java.lang.String", "STRING"),
            ("email", "邮箱", "java.lang.String", "STRING"),
        ],
    },
    "organization_unit": {
        "full_name": "com.seeyon.organization.domain.core.entity.OrgUnit",
        "caption": "组织",
        "fields": [
            ("code", "编号", "java.lang.String", "STRING"),
            ("name", "名称", "java.lang.String", "STRING"),
        ],
    },
}


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\excel-entity")
    a = ap.parse_args()

    from providers.mysql_readonly import MySQLConnectionAdapter
    e = env()
    db = MySQLConnectionAdapter(host=e.get("XIAOZHUA_DB_HOST", ""),
                                port=e.get("XIAOZHUA_DB_PORT") or 3306,
                                user=e.get("XIAOZHUA_DB_USERNAME", ""),
                                password=e.get("XIAOZHUA_DB_PASSWORD", ""))

    ent = db.query("SELECT id, name, caption, app_id "
                   "FROM udc_test2.udc_entity WHERE id=%s", (ENTITY_ID,))
    if not ent:
        print("实体不存在")
        db.close()
        return 1
    ent = ent[0]
    # udc_entity 没有 full_name 列，从 udc_application.name 拼
    app = db.query("SELECT name FROM udc_test2.udc_application WHERE id=%s", (ent["app_id"],))
    app_name = app[0]["name"] if app else ""
    entity_full = f"com.seeyon.{app_name}.domain.entity.{ent['name'][0].upper()}{ent['name'][1:]}"
    entity_caption = ent["caption"]
    global APP_NAME
    APP_NAME = app_name

    # 1) 基本类型字段 + ENTITY 字段
    attrs = db.query(
        "SELECT id, name, caption, data_type, relation_app, relation_entity, "
        "relation_entity_name, relation_type, order_no "
        "FROM udc_test2.udc_attribute WHERE entity_id=%s ORDER BY order_no", (ENTITY_ID,))
    base = [x for x in attrs if x["data_type"] != "ENTITY"]
    rel = [x for x in attrs if x["data_type"] == "ENTITY"]
    print(f"实体 {entity_caption} / {entity_full}")
    print(f"基本字段 {len(base)} 个；关联实体字段 {len(rel)} 个")
    for x in rel:
        print(f"  REL {x['name']:<22} {x['caption']:<10} relApp={x['relation_app']} "
              f"relEnt={str(x['relation_entity'])[:50]}")

    # 2) 构造列
    cols = []

    def master_col(at):
        afn = f"{entity_full}.{at['name']}"
        return build_column(
            afn, at["caption"] or at["name"],
            data_type=str(at["data_type"] or "STRING"),
            entity_type="MASTER_ENTITY",
            level_path=[[APP_NAME, entity_full, entity_caption, afn,
                         at["caption"] or at["name"]]],
            relation_app=APP_NAME, cur_col_index=len(cols))

    for at in base:
        cols.append(master_col(at))

    # 实体字段先本身作为一列（值列）
    for at in rel:
        cols.append(master_col(at))

    # 3) 关联实体展开（levelPath 两层）
    expanded = 0
    for at in rel:
        rapp = str(at.get("relation_app") or "")
        # 人员类 → OrgMember；组织类 → OrgUnit
        spec = None
        if "Member" in str(at.get("relation_entity") or "") or rapp == "organization":
            spec = REL_CANDIDATES["organization"]
        elif "OrgUnit" in str(at.get("relation_entity") or ""):
            spec = REL_CANDIDATES["organization_unit"]
        if not spec:
            continue
        for fname, fcap, jtype, dtype in spec["fields"]:
            rel_afn = f"{spec['full_name']}.{fname}"
            cols.append(build_column(
                rel_afn,
                f"{at['caption']}/{fcap}",
                data_type=dtype, java_type=jtype,
                entity_type="MASTER_ENTITY",
                level_path=[
                    [APP_NAME, entity_full, entity_caption,
                     f"{entity_full}.{at['name']}", at["caption"] or at["name"]],
                    [rapp or "organization", spec["full_name"], spec["caption"],
                     rel_afn, fcap],
                ],
                relation="NONE", relation_app=rapp or "organization",
                relation_entity="", cur_col_index=len(cols)))
            expanded += 1

    print(f"\n总列数 {len(cols)}（其中关联实体展开 {expanded} 列）")

    sheets = [cols]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    bodies = []
    for is_import, label in ((True, "导入"), (False, "导出")):
        body = build_template_body(
            APP_ID, APP_GUID,
            name=f"验收{label}模板-实体字段"[:20],
            main_full_name=entity_full, sheets=sheets,
            app_name=APP_NAME, is_import=is_import, is_custom=False)
        errs = validate_template_body(body)
        print(f"[{label}] 本地校验: {errs or '✅ 通过'}")
        bodies.append({"label": label, "body": body, "errors": errs})

    (out / "plan.json").write_text(json.dumps(
        [{"label": b["label"], "errors": b["errors"],
          "cols": len(cols),
          "sample": cols[:2]} for b in bodies], ensure_ascii=False, indent=1), encoding="utf-8")

    if a.dump or not a.i_have_write_authorization:
        print(f"\n只构造未写入 -> {out/'plan.json'}")
        db.close()
        return 0
    if any(b["errors"] for b in bodies):
        print("有本地校验错误，拒绝提交")
        db.close()
        return 2

    # 4) 提交
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
        try:
            return json.loads(c.evaluate(js, await_promise=True))
        except Exception as exc:
            return {"raw": str(exc)[:200]}

    results = []
    for b in bodies:
        r = post("/service/udc/excel/create-template", b["body"])
        ok = r.get("status") == 0
        tid = (r.get("data") or {}).get("content") if ok else None
        print(f"{'✅' if ok else '❌'} {b['label']}模板: "
              + (f"id={tid}" if ok else json.dumps(r, ensure_ascii=False)[:220]))
        results.append({"label": b["label"], "ok": ok, "id": tid,
                        **({} if ok else {"resp": r})})
        if not ok:
            break

    (out / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    db.close()
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
