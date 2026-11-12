#!/usr/bin/env python
"""自定义对象引用分析器 —— 删除前的安全闸门。

为什么需要（2026-10-20 实测背景）：
  自定义对象是「微流程/页面规则之间的数据传递载体」。删掉被引用的对象 →
  引用方悬空 → 微流程运行失败。所以删除前必须先证明"没人引用它"。

本工具做三件事：
  1. 收集全部引用源（微流程 / 页面 / 导出模板 / 页面信息 / 实体 / 规则 …）
  2. **阳性对照**：用已知确实被引用的实体名验证检测方法有效
     —— 检不出就说明方法有缺口，此时的"无引用"结论不可信
  3. 逐对象分类（有引用 / 无引用 / 无引用且命名可疑）

用法：
    python tools/core/setting/custom_object_reference_analysis.py \
        --app-id <appId> [--json] [--output <file>]

只读：全部走 SELECT，不写任何数据。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]   # tools/core/setting/ → 仓库根
sys.path.insert(0, str(REPO))

# 引用源表 → 文本列候选（按实际存在的列取，不硬编码）
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

# 命名可疑特征（实验残留）
SUSPICIOUS = re.compile(
    r"(?i)(zxj|xzh|小爪|实验|probe|test|tmp|临时|aaa|xxx|^[0-9]{1,3}$)")


def _env():
    p = Path(r"<HERMES_HOME>\skills\xiaozhua\01-platform\xiaozhua-low-code-environment\.env")
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-id", required=True)
    ap.add_argument("--app-guid", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--output", default="")
    a = ap.parse_args()

    from providers.mysql_readonly import MySQLConnectionAdapter
    env = _env()
    conn = MySQLConnectionAdapter(
        host=env.get("XIAOZHUA_DB_HOST", ""),
        port=env.get("XIAOZHUA_DB_PORT") or 3306,
        user=env.get("XIAOZHUA_DB_USERNAME", ""),
        password=env.get("XIAOZHUA_DB_PASSWORD", ""))
    app = a.app_id
    DB = "udc_test2"

    def cols_of(table):
        try:
            return {c["COLUMN_NAME"] for c in conn.describe_table(DB, table)["columns"]}
        except Exception:
            return set()

    objs = conn.query(
        f"SELECT id, name, caption, source, is_root, publish_state, create_time "
        f"FROM {DB}.udc_data_transfer_object WHERE app_id=%s", (app,))

    # 收集引用源
    sources = []
    for label, (table, wanted) in SOURCE_TABLES.items():
        have = cols_of(table)
        tcols = [c for c in wanted if c in have]
        if not tcols:
            continue
        try:
            rows = conn.query(
                f"SELECT id, {', '.join(tcols)} FROM {DB}.{table} WHERE app_id=%s", (app,))
        except Exception:
            continue
        for r in rows:
            blob = " ".join(str(r.get(c) or "") for c in tcols)
            if blob.strip():
                sources.append((label, str(r["id"]), blob))

    def refs_of(token):
        token = str(token or "").strip()
        if not token or len(token) < 3:
            return []
        return [f"{k}({i})" for k, i, b in sources if token in b]

    # 阳性对照
    ctrl = conn.query(f"SELECT name FROM {DB}.udc_entity WHERE app_id=%s LIMIT 4", (app,))
    ctrl_detail = [{"name": e["name"], "hits": refs_of(e["name"])} for e in ctrl]
    ctrl_hit = sum(1 for c in ctrl_detail if c["hits"])
    method_valid = ctrl_hit == len(ctrl_detail)

    referenced, unreferenced = [], []
    for o in objs:
        hits = list(dict.fromkeys(refs_of(o["name"]) + refs_of(o["caption"])))
        row = {"id": str(o["id"]), "name": o["name"], "caption": o["caption"],
               "source": o["source"], "create_time": str(o["create_time"])}
        if hits:
            referenced.append({**row, "refs": hits})
        else:
            unreferenced.append(row)

    suspicious_unref = [o for o in unreferenced
                         if SUSPICIOUS.search(str(o["name"]) or "")
                         or SUSPICIOUS.search(str(o["caption"]) or "")]
    suspicious_ref = [o for o in referenced
                      if SUSPICIOUS.search(str(o["name"]) or "")
                      or SUSPICIOUS.search(str(o["caption"]) or "")]

    report = {
        "app_id": app,
        "total": len(objs),
        "source_count": len(sources),
        "source_distribution": {k: sum(1 for s, _, _ in sources if s == k)
                                for k in {s for s, _, _ in sources}},
        "control_detail": ctrl_detail,
        "control_hit": ctrl_hit,
        "control_total": len(ctrl_detail),
        "method_valid": method_valid,
        "referenced_count": len(referenced),
        "unreferenced_count": len(unreferenced),
        "referenced": referenced,
        "suspicious_unreferenced": suspicious_unref,
        "suspicious_referenced": suspicious_ref,
    }

    if a.json:
        out = json.dumps(report, ensure_ascii=False, indent=2, default=str)
    else:
        lines = [
            "=" * 70,
            f"自定义对象引用分析  app_id={app}",
            "=" * 70,
            f"对象总数        {report['total']}",
            f"引用源          {report['source_count']} 个 {report['source_distribution']}",
            f"阳性对照        {ctrl_hit}/{report['control_total']} "
            f"→ 检测方法{'有效 ✅' if method_valid else '无效 ❌（无引用结论不可信）'}",
            "",
            f"有引用（不可删）  {report['referenced_count']}",
            f"无引用            {report['unreferenced_count']}",
            "",
            f"--- 无引用且命名可疑（实验残留候选）: {len(suspicious_unref)} ---",
        ]
        for o in suspicious_unref:
            lines.append(f"  {o['id']:<22} {str(o['name'])[:30]:<32} {str(o['caption'])[:26]}")
        lines.append("")
        lines.append(f"--- 有引用但命名可疑（需人工判断）: {len(suspicious_ref)} ---")
        for o in suspicious_ref:
            lines.append(f"  {o['id']:<22} {str(o['name'])[:30]:<32} ← {o['refs'][:2]}")
        out = "\n".join(lines)

    print(out)
    if a.output:
        Path(a.output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"\n报告已写: {a.output}")
    conn.close()
    return 0 if method_valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
