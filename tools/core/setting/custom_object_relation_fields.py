"""跑通 4 种关系型字段（枚举 / 选项集 / 对象 / 关联实体）——接口组装，不点页面。

数据源（打开编辑弹窗时平台真实加载的 6 个接口）：
  udcDataTransferObjectSelectDtoGet        当前 DTO 全文（含全部 attributes）
  udcDataTransferObjectSearchListPost      自定义对象候选      → "对象"
  udcMicroflowTreeEntityDtoPost            微流程树 DTO 候选   → "对象"
  udcMetaDataSelectJavaEnumByAppPost       Java 枚举候选       → "枚举"
  udcMetaDataSelectCtpEnumAppGet           CTP 枚举候选        → "选项集"
  udcEntityAssociationEntityAppGet         关联实体候选        → "关联实体"

组装规则（实证）：
  attributes[] 是全量替换 —— 必须把已有字段一起带上，否则被覆盖丢失。
  dataTypeCategory / type / relationType 是枚举字符串，不是数字。
  类别只有两个：type = OBJECT（单个）/ LIST（列表）。

用法：
  python tools/core/setting/custom_object_relation_fields.py --mode dump
  python tools/core/setting/custom_object_relation_fields.py --mode build --i-have-write-authorization
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from providers.cdp import CdpClient  # noqa: E402

APP_ID = None  # ★ 运行时由 --app-id / XIAOZHUA_APP_ID 提供（原写死值已移除）
# 应用名按 appId 从 udc_application 运行时解析（仓库内不落客户应用名常量）
APP_NAME = ""
PROBE_OID = "-7340588150208408653"


def resolve_app_name(c, app_id):
    """从平台侧解析应用名，避免在仓库里硬编码客户标识。"""
    r = call(c, "udcDataTransferObjectSelectDtoGet", {"appId": app_id, "id": PROBE_OID})
    nm = ((r.get("data") or {}).get("content") or {}).get("appName")
    return nm or ""


def call(c, op, params, *, query=True):
    if query:
        q = ("query graphqlLoader ($params0: %sInputPath) { \n"
             "  data0: %s(path: $params0) { code message status data { content } } }" % (op, op))
    else:
        q = ("mutation graphqlLoader ($params0: %sInputBody) { \n"
             "  data0: %s(body: $params0) { code message status data { content } } }" % (op, op))
    payload = {"query": q, "variables": {"params0": params}}
    js = ("(async()=>{const r=await fetch('/service/udc/graphql?%s',{method:'POST',credentials:'include',"
          "headers:{'Content-Type':'application/json'},body:%s});return await r.text();})()"
          % (op, json.dumps(json.dumps(payload, ensure_ascii=False))))
    raw = c.evaluate(js, await_promise=True)
    try:
        return json.loads(raw).get("data", {}).get("data0", {})
    except Exception:
        return {"raw": raw[:300]}


def content_of(resp):
    return (resp.get("data") or {}).get("content")


def get_dto(c, oid):
    return content_of(call(c, "udcDataTransferObjectSelectDtoGet",
                           {"appId": APP_ID, "id": oid})) or {}


def dump(c, oid):
    out = {}
    dto = get_dto(c, oid)
    out["dto"] = {
        "name": dto.get("name"), "caption": dto.get("caption"),
        "source": dto.get("source"), "sourceType": dto.get("sourceType"),
        "appName": dto.get("appName"),
        "attributes": [{"name": a.get("name"), "dataType": a.get("dataType"),
                        "dataTypeCategory": a.get("dataTypeCategory"),
                        "type": a.get("type"), "relationApp": a.get("relationApp"),
                        "relationEntity": a.get("relationEntity")}
                       for a in (dto.get("attributes") or [])],
    }

    lst = content_of(call(c, "udcDataTransferObjectSearchListPost", {"appId": APP_ID}, query=False)) or []
    out["customObjects"] = [{"id": x.get("id"), "name": x.get("name"),
                             "caption": x.get("caption"), "fullName": x.get("fullName"),
                             "source": x.get("source")}
                            for x in lst if isinstance(x, dict)][:8]

    ctp = content_of(call(c, "udcMetaDataSelectCtpEnumAppGet", {"appId": APP_ID}))
    # content 是 list[{categoryAndItemDtos:[...]}] —— 外层要多剥一层
    if isinstance(ctp, list) and ctp and isinstance(ctp[0], dict) and "categoryAndItemDtos" in ctp[0]:
        ctp = ctp[0].get("categoryAndItemDtos") or []
    elif isinstance(ctp, dict):
        ctp = ctp.get("categoryAndItemDtos") or []
    groups = []
    for g in (ctp or [])[:8]:
        if not isinstance(g, dict):
            continue
        gname = g.get("name")
        if isinstance(gname, str) and gname.strip().startswith("{"):
            try:
                gname = json.loads(gname).get("zh_CN") or gname
            except Exception:
                pass
        items = []
        for x in (g.get("children") or []):
            if not isinstance(x, dict):
                continue
            nm = x.get("name")
            if isinstance(nm, str) and nm.strip().startswith("{"):
                try:
                    nm = json.loads(nm).get("zh_CN") or nm
                except Exception:
                    pass
            items.append({"id": x.get("id"), "name": nm, "code": x.get("code"),
                          "fullName": x.get("fullName"), "enumType": x.get("enumType")})
        if items:
            groups.append({"group": gname, "items": items[:6]})
    out["ctpEnumGroups"] = groups

    assoc = content_of(call(c, "udcEntityAssociationEntityAppGet", {"appId": APP_ID})) or []
    ents = []
    for app in (assoc if isinstance(assoc, list) else [])[:4]:
        if not isinstance(app, dict):
            continue
        for e in (app.get("entityDtos") or [])[:5]:
            ents.append({"app": app.get("name"), "entity": e.get("relationEntity"),
                         "caption": e.get("relationEntityName") or e.get("caption"),
                         "category": e.get("relationEntityCategory")})
    out["assocEntities"] = ents

    app_name = resolve_app_name(c, APP_ID)
    je = content_of(call(c, "udcMetaDataSelectJavaEnumByAppPost",
                         {"appId": APP_ID, "hostAppName": app_name}, query=False)) or {}
    if isinstance(je, dict):
        out["javaEnums"] = [{"id": x.get("id"), "name": x.get("name"),
                             "caption": x.get("caption"), "fullName": x.get("fullName")}
                            for x in (je.get("enums") or [])][:8]
    return out


def build(c, oid, picks):
    app_name = resolve_app_name(c, APP_ID)
    dto = get_dto(c, oid)
    attrs = list(dto.get("attributes") or [])
    existing = {a.get("name") for a in attrs}

    def make(name, caption, **kw):
        base = {"name": name, "caption": caption, "notNull": False,
                "dataType": "STRING", "dataTypeCategory": "PRIMITIVE",
                "type": "OBJECT", "description": "", "defaultValue": None,
                "appId": APP_ID}
        base.update(kw)
        return base

    new = []
    if picks.get("enum"):
        e = picks["enum"]
        new.append(make("rel_enum", "枚举字段", dataType="CTPENUM",
                        relationApp=e.get("app") or app_name, relationEntity=e["id"],
                        relationType="Many2OneAssociation"))
    if picks.get("optset"):
        o = picks["optset"]
        new.append(make("rel_optset", "选项集字段", dataType="CTPENUM",
                        relationApp=o.get("app") or app_name, relationEntity=o["id"],
                        relationType="Many2OneAssociation"))
    if picks.get("obj"):
        t = picks["obj"]
        new.append(make("rel_obj", "对象字段", dataType=t["fullName"],
                        dataTypeCategory="COMPOSITE", type="OBJECT",
                        relationEntity=t.get("id"),
                        relationType="Many2OneAssociation"))
    if picks.get("objList"):
        t = picks["objList"]
        new.append(make("rel_objlist", "对象列表字段", dataType=t["fullName"],
                        dataTypeCategory="COMPOSITE", type="LIST",
                        relationEntity=t.get("id"),
                        relationType="Many2OneAssociation"))
    if picks.get("entity"):
        t = picks["entity"]
        new.append(make("rel_entity", "关联实体字段", dataType="ENTITY",
                        relationApp=t["app"], relationEntity=t["entity"],
                        relationType="Many2OneAssociation"))

    attrs = attrs + [a for a in new if a["name"] not in existing]
    body = {"appId": APP_ID, "name": dto.get("name"), "caption": dto.get("caption"),
            "description": dto.get("description"), "source": dto.get("source"),
            "attributes": attrs, "id": oid}
    resp = call(c, "udcDataTransferObjectUpdateDtoPost", body, query=False)
    return {"sent": new, "attributeCount": len(attrs), "resp": resp}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--target", default="A886072E39FD374937FE966D008AABC5")
    ap.add_argument("--object-id", default=PROBE_OID)
    ap.add_argument("--mode", choices=["dump", "build"], default="dump")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\co-type-probe")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    a = ap.parse_args()

    import urllib.request
    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    tgt = [t for t in tgts if t.get("id") == a.target][0]
    c = CdpClient(a.port, allow_network=True, timeout=90)
    c.connect(target=tgt)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    if a.mode == "dump":
        d = dump(c, a.object_id)
        (out / "candidates.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(d, ensure_ascii=False, indent=1)[:7000])
        print("\n-> " + str(out / "candidates.json"))
        c.close()
        return 0

    if not a.i_have_write_authorization:
        print("写操作需显式确认：加 --i-have-write-authorization")
        c.close()
        return 1

    d = dump(c, a.object_id)
    app_name = resolve_app_name(c, APP_ID)
    picks = {}
    for g in d.get("ctpEnumGroups") or []:
        for it in g.get("items") or []:
            if not it.get("id"):
                continue
            if not picks.get("enum"):
                picks["enum"] = {"app": app_name, "id": it["id"],
                                 "name": it.get("name"), "code": it.get("code")}
            elif not picks.get("optset"):
                picks["optset"] = {"app": app_name, "id": it["id"],
                                   "name": it.get("name"), "code": it.get("code")}
    for o in d.get("customObjects") or []:
        if o.get("fullName"):
            if not picks.get("obj"):
                picks["obj"] = {"fullName": o["fullName"], "id": o["id"], "name": o.get("name")}
            elif not picks.get("objList"):
                picks["objList"] = {"fullName": o["fullName"], "id": o["id"], "name": o.get("name")}
                break
    for e in d.get("assocEntities") or []:
        if e.get("entity") and not picks.get("entity"):
            picks["entity"] = {"app": e.get("app"), "entity": e["entity"],
                               "caption": e.get("caption")}
    print("picks:", json.dumps(picks, ensure_ascii=False))
    r = build(c, a.object_id, picks)
    print("send:", json.dumps(r["sent"], ensure_ascii=False, indent=1)[:2000])
    print("resp:", json.dumps(r["resp"], ensure_ascii=False)[:400])

    after = get_dto(c, a.object_id)
    print("\n回读 attributes:")
    for x in (after.get("attributes") or []):
        print(f"  {x['name']:<16} {str(x.get('caption')):<10} dt={str(x.get('dataType'))[:34]:<36} "
              f"cat={x.get('dataTypeCategory'):<10} type={x.get('type'):<8} "
              f"relApp={x.get('relationApp')} relEnt={x.get('relationEntity')}")
    (out / "relation-fields.json").write_text(
        json.dumps({"picks": picks, "sent": r["sent"], "resp": r["resp"],
                    "after": after.get("attributes")}, ensure_ascii=False, indent=1), encoding="utf-8")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
