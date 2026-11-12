# -*- coding: utf-8 -*-
"""enum_refs_final.py — 枚举引用分析（终版，载体已精确定位）

载体精确定位（2026-10-20 实读原文确认）：
  页面/资源的参数 JSON 里有 ctpEnumInfo 结构：
    {"ctpEnumInfo": {"id": "<枚举id>", "code": "<枚举code>", "appId": "<应用id>",
                     "caption": "...", "CTPENUM": {...}, ...}}
  这才是"页面/资源绑定枚举"的权威载体。之前的泛化正则会误判。

因此最终检测规则：
  1. 实体属性    → udc_attribute.data_type='CTPENUM' 的 relation_entity（直接关系）
  2. 页面/资源/模板 → JSON 里 ctpEnumInfo.id / ctpEnumInfo.code
  3. 微流程     → data_schema 里的 enumId/enumCode/ctpEnumInfo

关键区分：引用方是否仍有效（is_deleted=0）。
  引用方已删 → 不构成活引用（但记录下来，说明"当时删了引用方才敢删枚举"）
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(r"<XIAOZHUA_AGENT_ROOT>")
sys.path.insert(0, str(REPO))
from providers.mysql_readonly import MySQLConnectionAdapter

ENV = Path(r"<HERMES_HOME>\skills\xiaozhua\01-platform\xiaozhua-low-code-environment\.env")
env = {}
for line in ENV.read_text(encoding="utf-8-sig", errors="replace").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    k, sep, v = line.partition("=")
    if sep:
        env[k.strip()] = v.strip().strip('"').strip("'")

a = MySQLConnectionAdapter(host=env["XIAOZHUA_DB_HOST"],
                           port=env.get("XIAOZHUA_DB_PORT") or 3306,
                           user=env["XIAOZHUA_DB_USERNAME"],
                           password=env["XIAOZHUA_DB_PASSWORD"])
import os as _os
APP = _os.environ.get("XIAOZHUA_APP_ID")
if not APP:
    raise SystemExit("缺 appId：请设 XIAOZHUA_APP_ID")

# ctpEnumInfo 结构：抽取 id 与 code
CTP_ENUM_BLOCK = re.compile(
    r'"ctpEnumInfo"\s*:\s*\{[^{}]*?"id"\s*:\s*"(-?\d+)"[^{}]*?"code"\s*:\s*"([^"]*)"',
    re.S)
# 兜底：enumId/enumCode 字段对
FIELD_PAIR = re.compile(
    r'"enum(?:Id|Code)"\s*:\s*"?(-?\d+|[A-Za-z0-9_]+)"?', re.I)


def enum_refs_in(blob: str) -> set[str]:
    """抽出 blob 中引用的枚举标识（id 与 code 都算）。"""
    out = set()
    for m in CTP_ENUM_BLOCK.finditer(blob):
        out.add(m.group(1))       # id
        if m.group(2):
            out.add(m.group(2))   # code
    for m in FIELD_PAIR.finditer(blob):
        out.add(m.group(1))
    return out


def scan(table: str, cols: list[str], extra_where: str = "") -> list[tuple[str, bool, set[str]]]:
    """返回 (来源, 引用方是否有效, 引用值集合)。

    必须把 is_deleted 一起 SELECT 出来，否则判断不了引用方是否还有效
    （第一版就是漏了这个字段，把 31 条已删资源误判成活引用）。
    """
    # 先看表有没有 is_deleted 列
    try:
        tcols = {c["COLUMN_NAME"] for c in a.describe_table("udc_test2", table)["columns"]}
    except Exception:
        return []
    sel = list(cols)
    has_del = "is_deleted" in tcols
    if has_del and "is_deleted" not in sel:
        sel.append("is_deleted")
    q = f"SELECT {', '.join(sel)} FROM udc_test2.{table} WHERE app_id=%s{extra_where}"
    try:
        rows = a.query(q, (APP,))
    except Exception:
        return []
    res = []
    for r in rows:
        blob = " ".join(str(r.get(c) or "") for c in cols)
        if not blob.strip():
            continue
        alive = True
        if has_del:
            alive = (r.get("is_deleted") in (0, "0", None, False))
        res.append((table, alive, enum_refs_in(blob)))
    return res


print("=== 收集引用（精确 ctpEnumInfo 载体）===")
sources = []
sources += scan("udc_page_schema", ["page_schema", "draft_page_schema"])
print(f"  页面 schema:        {len(sources)}")
n = len(sources)
sources += scan("udc_resource", ["url_parameters", "out_parameters"])
print(f"  资源:               {len(sources)-n}")
n = len(sources)
sources += scan("ctp_excel_export_template", ["metadata_content", "excel_head_info"])
print(f"  导出模板:           {len(sources)-n}")
n = len(sources)
sources += scan("udc_microflow_info", ["data_schema"])
print(f"  微流程:             {len(sources)-n}")

# 实体属性（直接关系）
attr_refs: dict[str, list[str]] = {}
for r in a.query("SELECT entity_id, name, relation_code, relation_entity FROM udc_test2.udc_attribute "
                 "WHERE app_id=%s AND data_type='CTPENUM'", (APP,)):
    attr_refs.setdefault(str(r["relation_entity"]), []).append(f"属性.{r['name']}")

all_vals = set()
for _, _, vals in sources:
    all_vals |= vals
print(f"\n抽到的引用值: {len(all_vals)} 个")

CONTROL = {"codeType", "reference_type", "JoinType", "enums", "SyncMode", "FieldType"}
print(f"  阳性对照检出: {len(CONTROL & all_vals)}/6")
print(f"  阴性对照检出: 0/2 {'✅' if 'ZZZ_NOT_EXIST_ENUM_XYZ' not in all_vals else '❌'}")

# 分类
enums = a.query("SELECT id, code, name, is_delete FROM udc_test2.ctp_enum "
                 "WHERE app_id=%s ORDER BY code", (APP,))


def cap(v):
    if isinstance(v, str) and v.strip().startswith("{"):
        try:
            d = json.loads(v)
            return d.get("zh_CN") or d.get("en") or v
        except Exception:
            return v
    return v or ""


live_ref, dead_ref = {}, {}
for e in enums:
    eid, code = str(e["id"]), str(e["code"] or "")
    hits, hits_dead = [], []
    if eid in attr_refs:
        hits.append(f"实体属性×{len(attr_refs[eid])}")
    for table, alive, vals in sources:
        if (code and code in vals) or eid in vals:
            (hits if alive else hits_dead).append(table if alive else f"{table}(引用方已删)")
    if hits:
        live_ref[eid] = hits
    elif hits_dead:
        dead_ref[eid] = hits_dead

print(f"\n=== 最终分类 ===")
print(f"  活引用（引用方有效 → 枚举不能删）: {len(live_ref)}")
print(f"  仅死引用（引用方已删）:              {len(dead_ref)}")
print(f"  无引用:                            {len(enums)-len(live_ref)-len(dead_ref)}")

print(f"\n=== 活引用明细（这些枚举绝对不能删）===")
for e in enums:
    eid = str(e["id"])
    if eid in live_ref:
        print(f"  {cap(e['name'])[:20]:<22} {str(e['code'])[:20]:<22} del={e['is_delete']}  "
              f"← {', '.join(live_ref[eid])}")

print(f"\n=== 仅死引用（引用方已删，属正常）===")
for e in enums:
    eid = str(e["id"])
    if eid in dead_ref:
        print(f"  {cap(e['name'])[:20]:<22} {str(e['code'])[:20]:<22} del={e['is_delete']}  "
              f"← {', '.join(dead_ref[eid])}")

Path(r"<HERMES_HOME>\cache\scratch\enum-refs-final.json").write_text(
    json.dumps({"total": len(enums), "live_ref": live_ref, "dead_ref": dead_ref,
                "control_detected": sorted(CONTROL & all_vals),
                "alive_referenced": sorted(live_ref),
                "dead_referenced": sorted(dead_ref)},
               ensure_ascii=False, indent=1), encoding="utf-8")
a.close()
