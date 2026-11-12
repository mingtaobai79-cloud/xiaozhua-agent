#!/usr/bin/env python
"""预检：对 223 个"无引用"自定义对象做 id/guid 形式的引用复核 + 全量行级备份。

只读。输出：
  - backups/custom-object-delete-<ts>/udc_data_transfer_object.json   全量 229 行的完整备份
  - backups/custom-object-delete-<ts>/precheck.json                   删除候选清单 + 复核结论
"""
from __future__ import annotations
import json, sys, datetime
from pathlib import Path

REPO = Path(r"<SEEYON_AGENT_ROOT>")
sys.path.insert(0, str(REPO))

APP = None  # ★ 运行时由 --app-id / SEEYON_APP_ID 提供（原写死值已移除）
DB = "udc_test2"
TABLE = "udc_data_transfer_object"

# 引用源：与 custom_object_reference_analysis.py 一致
SOURCE_TABLES = {
    "微流程": ("udc_microflow_info", ["data_schema"]),
    "页面": ("udc_page_schema", ["page_schema", "draft_page_schema"]),
    "页面信息": ("udc_page_info", ["page_schema", "layout_info", "description"]),
    "实体": ("udc_entity", ["description", "table_name"]),
    "规则": ("udc_rule", ["rule_schema", "content", "description"]),
    "数据流": ("udc_data_flow", ["data_schema", "content"]),
    "导出模板": ("ctp_excel_export_template", ["metadata_content", "excel_head_info"]),
    "资源": ("udc_resource", ["url_parameters", "out_parameters", "description"]),
}


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
    from providers.mysql_readonly import MySQLConnectionAdapter
    e = env()
    conn = MySQLConnectionAdapter(host=e.get("SEEYON_DB_HOST", ""), port=e.get("SEEYON_DB_PORT") or 3306,
                                  user=e.get("SEEYON_DB_USERNAME", ""), password=e.get("SEEYON_DB_PASSWORD", ""))

    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = Path(r"<HERMES_HOME>\backups") / f"custom-object-delete-{ts}"
    out.mkdir(parents=True, exist_ok=True)

    rows = conn.query(f"SELECT * FROM {DB}.{TABLE} WHERE app_id=%s", (APP,))
    backup = [{k: (str(v) if v is not None else None) for k, v in r.items()} for r in rows]
    (out / f"{TABLE}.json").write_text(json.dumps(backup, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"备份 {len(backup)} 行 → {out / (TABLE + '.json')}")

    # 收集引用源
    sources = []
    dist = {}
    for label, (table, wanted) in SOURCE_TABLES.items():
        try:
            have = {c["COLUMN_NAME"] for c in conn.describe_table(DB, table)["columns"]}
        except Exception:
            continue
        tcols = [c for c in wanted if c in have]
        if not tcols:
            continue
        try:
            rs = conn.query(f"SELECT id, {', '.join(tcols)} FROM {DB}.{table} WHERE app_id=%s", (APP,))
        except Exception:
            continue
        n = 0
        for r in rs:
            blob = " ".join(str(r.get(c) or "") for c in tcols)
            if blob.strip():
                sources.append((label, str(r["id"]), blob))
                n += 1
        dist[label] = n
    print(f"引用源 {len(sources)} 个 {dist}")

    # 阳性对照：实体名必须能被检出
    ctrl = conn.query(f"SELECT name FROM {DB}.udc_entity WHERE app_id=%s LIMIT 4", (APP,))
    ctrl_hits = [{"name": c["name"], "hits": [f"{k}({i})" for k, i, b in sources if c["name"] in b]} for c in ctrl]
    valid = bool(ctrl_hits) and all(c["hits"] for c in ctrl_hits)
    print(f"阳性对照 {sum(1 for c in ctrl_hits if c['hits'])}/{len(ctrl_hits)} → {'有效' if valid else '无效'}")
    if not valid:
        print("阳性对照未通过：无引用结论不可信，终止（不产出删除清单）")
        conn.close()
        return 2

    def hits_for(o):
        forms = {"name": str(o.get("name") or ""), "caption": str(o.get("caption") or ""),
                 "id": str(o.get("id") or ""), "guid": str(o.get("guid") or "")}
        found = []
        for kind, tok in forms.items():
            if not tok or tok in ("0", "None") or len(tok) < 3:
                continue
            for k, i, b in sources:
                if tok in b:
                    found.append(f"{kind}:{tok}@{k}({i})")
        return list(dict.fromkeys(found))

    referenced, candidates = [], []
    for o in backup:
        h = hits_for(o)
        rec = {"id": o["id"], "name": o["name"], "caption": o["caption"],
               "create_time": o["create_time"], "source": o["source"]}
        if h:
            referenced.append({**rec, "refs": h})
        else:
            candidates.append(rec)

    report = {"app_id": APP, "total": len(backup), "source_count": len(sources),
              "source_distribution": dist, "control": ctrl_hits, "method_valid": valid,
              "referenced": referenced, "candidates": candidates,
              "backup_dir": str(out)}
    (out / "precheck.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n有引用（保留） {len(referenced)}")
    for r in referenced:
        print(f"  {r['id']:<22} {str(r['name'])[:32]:<34} ← {r['refs'][:2]}")
    print(f"\n删除候选     {len(candidates)}")
    print(f"预检报告 → {out / 'precheck.json'}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
