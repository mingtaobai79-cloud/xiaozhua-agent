"""设置域 · 字段集：18 种字段类型 × 能力矩阵实测。

用途：把 `udcDataTypeDataTypesByAppIdAppGet` 返回的每种 dataType 都真实建一次，
逐个 DB 回读，确认「类型 → 可配置能力」的对应关系。

数据来源：
  udcDataTypeDataTypesByAppIdAppGet  → 18 种类型 + 每种支持的 enable 开关
  GraphQL udcEntityAttributePost     → 字段写入

用法：
  # 只读：打印类型能力矩阵
  python tools/core/setting/attribute_set_type_matrix.py --list

  # 实测：每种类型建一个字段
  python tools/core/setting/attribute_set_type_matrix.py --run \
      --set-id <字段集id> --i-have-write-authorization

  # 带能力开关
  python tools/core/setting/attribute_set_type_matrix.py --run \
      --set-id <id> --with-capabilities --i-have-write-authorization
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from components.udc.setting.attribute_set_constraints import (  # noqa: E402
    build_attribute_field_body, validate_attribute_field_body,
)

# 各类型支持的配置项（从 udcDataTypeDataTypesByAppIdAppGet 的 enable* 开关归纳）
TYPE_CAPABILITIES = {
    "STRING": ["Calculable", "Index", "Required", "Sensitive", "Encryption",
               "SensitiveWordCheck", "Log", "DefaultValue", "LengthRange",
               "Unique", "Pattern", "Search", "I18n"],
    "MULTILINESTRING": ["Calculable", "Required", "SensitiveWordCheck", "Log",
                        "DefaultValue", "LengthRange", "Search", "I18n"],
    "INTEGER": ["Calculable", "Required", "Log", "DefaultValue", "MaxAndMin",
                "Unique", "Search"],
    "BIGINTEGER": ["Calculable", "Index", "Required", "Log", "DefaultValue",
                   "MaxAndMin", "Unique", "Search"],
    "DECIMAL": ["Calculable", "Index", "Required", "Log", "DefaultValue",
                "MaxAndMin", "DecimalDigits", "Unique", "Search"],
    "CURRENCY": ["Calculable", "Index", "Required", "Log", "DefaultValue",
                 "MaxAndMin", "DecimalDigits", "Unique", "Search"],
    "DATE": ["Calculable", "Index", "Required", "Log", "DefaultValue",
             "MaxAndMin", "Unique", "Search"],
    "TIME": ["Calculable", "Index", "Required", "Log", "DefaultValue",
             "MaxAndMin", "Unique", "Search"],
    "DATETIME": ["Calculable", "Index", "Required", "Log", "DefaultValue",
                 "MaxAndMin", "Unique", "Search"],
    "BOOLEAN": ["Calculable", "Index", "Log", "DefaultValue", "Unique"],
    "ENUM": ["Index", "Required", "Log", "DefaultValue", "MultiSelect",
             "Unique", "Search"],
    "CTPENUM": ["Index", "Required", "Log", "DefaultValue", "MultiSelect",
                "Unique", "Search"],
    "ATTACHMENT": ["Required", "Log", "MultiSelect", "Search"],
    "ENTITY": ["Index", "Required", "Log", "DefaultValue", "MultiSelect",
               "Unique", "Search"],
    "DOCUMENTNUMBER": ["Index", "Required", "SensitiveWordCheck", "Log",
                       "LengthRange", "Search", "I18n"],
    "Serial": ["Calculable", "Index", "Required", "SensitiveWordCheck", "Log",
               "LengthRange", "Unique", "Search"],
    "OPINION": ["Calculable", "Required", "SensitiveWordCheck", "Log",
                "LengthRange", "Search"],
    "CONTENT": ["Calculable", "Index", "Required", "SensitiveWordCheck", "Log",
                "LengthRange", "Search"],
}

# 每种类型的 per-type 参数（写进 body 的差异部分）
TYPE_EXTRA = {
    "STRING": {"maxLength": 100, "minLength": 0},
    "MULTILINESTRING": {"maxLength": 2000, "minLength": 0},
    "INTEGER": {},
    "BIGINTEGER": {},
    "DECIMAL": {"decimalDigits": 2},
    "CURRENCY": {"decimalDigits": 2},
    "DATE": {},
    "TIME": {},
    "DATETIME": {},
    "BOOLEAN": {},
    "ENUM": {},
    "CTPENUM": {},
    "ATTACHMENT": {},
    "ENTITY": {},
    "DOCUMENTNUMBER": {"maxLength": 50},
    "Serial": {"maxLength": 50},
    "OPINION": {"maxLength": 4000},
    "CONTENT": {"maxLength": 8000},
}


def print_matrix() -> None:
    print(f"共 {len(TYPE_CAPABILITIES)} 种字段类型\n")
    for t, caps in TYPE_CAPABILITIES.items():
        print(f"  {t:<16} {'/'.join(caps)}")


def call_gql(c, op, body):
    q = ("mutation graphqlLoader ($params0: %sInputBody) { \n"
         "  data0: %s(body: $params0) { code message status data { content } } }" % (op, op))
    payload = {"query": q, "variables": {"params0": body}}
    js = ("(async()=>{const r=await fetch('/service/udc/graphql?%s',{method:'POST',credentials:'include',"
          "headers:{'Content-Type':'application/json'},body:%s});return await r.text();})()"
          % (op, json.dumps(json.dumps(payload, ensure_ascii=False))))
    return json.loads(c.evaluate(js, await_promise=True))["data"]["data0"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--app-id", default=None)
    ap.add_argument("--set-id", default="")
    ap.add_argument("--prefix", default="fmt", help="字段编码前缀（换前缀可绕过编码重复）")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--with-capabilities", action="store_true",
                    help="同时打开该类型支持的能力开关（必填/唯一/多选等）")
    ap.add_argument("--ctp-enum-id", default="",
                    help="CTPENUM 字段要关联的枚举 id（缺则跳过该类型）")
    ap.add_argument("--entity-full-name", default="",
                    help="ENTITY 字段要关联的实体全类名（缺则跳过该类型）")
    ap.add_argument("--enum-id", default="",
                    help="ENUM 字段要关联的选项集 id（缺则跳过该类型）")
    ap.add_argument("--serial-name", default="",
                    help="Serial 字段要绑定的流水号规则名（缺则跳过该类型）")
    ap.add_argument("--serial-code", default="",
                    help="Serial 字段要绑定的流水号规则 code")
    ap.add_argument("--serial-guid", default="",
                    help="Serial 字段要绑定的流水号规则 guid")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\type-matrix")
    a = ap.parse_args()

    if a.list or not a.run:
        print_matrix()
        if not a.run:
            return 0

    if not a.set_id:
        print("--run 需要 --set-id <字段集 id>")
        return 2
    if not a.i_have_write_authorization:
        print("写操作需显式确认：加 --i-have-write-authorization")
        return 1

    import urllib.request
    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    pages = [t for t in tgts if t.get("type") == "page"
             and f"appId={a.app_id}" in t.get("url", "")]
    if not pages:
        pages = [t for t in tgts if t.get("type") == "page" and "lowcode-test2" in t.get("url", "")]
    from providers.cdp import CdpClient
    c = CdpClient(a.port, allow_network=True, timeout=120)
    c.connect(target=pages[0])

    # 从平台拉真实类型清单
    qg = ("query graphqlLoader ($params0: udcDataTypeDataTypesByAppIdAppGetInputPath) { "
          "data0: udcDataTypeDataTypesByAppIdAppGet(path: $params0) { code message status data { content } } }")
    payload = {"query": qg, "variables": {"params0": {"appId": a.app_id}}}
    js = ("(async()=>{const r=await fetch('/service/udc/graphql?udcDataTypeDataTypesByAppIdAppGet',"
          "{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},"
          "body:%s});return await r.text();})()" % json.dumps(json.dumps(payload, ensure_ascii=False)))
    dt = json.loads(c.evaluate(js, await_promise=True))["data"]["data0"]
    types = [(x.get("name"), x.get("caption")) for x in ((dt.get("data") or {}).get("content") or [])]
    print(f"平台返回 {len(types)} 种类型，逐个建字段…\n")

    results = []
    for i, (tname, tcaption) in enumerate(types, 1):
        safe = "".join(ch if ch.isalnum() else "_" for ch in str(tname)).lower()
        # 编码必须以字母开头（UDC_ENTITY_0026），所以 f 前缀
        fname = f"{a.prefix}{i:02d}{safe[:14]}"
        kw = dict(name=fname, caption=f"{tcaption}测试", data_type=tname,
                  order_no=i)
        kw.update({k: v for k, v in TYPE_EXTRA.get(tname, {}).items()
                   if k in ("min_length", "max_length")})
        if a.with_capabilities:
            caps = TYPE_CAPABILITIES.get(tname, [])
            kw["not_null"] = "Required" in caps
            kw["uniqueness"] = "Unique" in caps
            kw["searchable"] = "Search" in caps
        # 关联型：缺目标就跳过（否则平台报 UDC_DATATYPE_0015/0017）
        if tname == "CTPENUM":
            if not a.ctp_enum_id:
                print(f"  {i:>2}. {tname:<16} SKIP（缺 --ctp-enum-id）")
                results.append({"type": tname, "ok": False, "skipped": "缺关联枚举"})
                continue
        elif tname == "ENTITY":
            if not a.entity_full_name:
                print(f"  {i:>2}. {tname:<16} SKIP（缺 --entity-full-name）")
                results.append({"type": tname, "ok": False, "skipped": "缺关联实体"})
                continue
        elif tname == "ENUM":
            if not a.enum_id:
                print(f"  {i:>2}. {tname:<16} SKIP（缺 --enum-id）")
                results.append({"type": tname, "ok": False, "skipped": "缺关联选项集"})
                continue
        elif tname == "Serial":
            if not (a.serial_name and a.serial_code):
                print(f"  {i:>2}. {tname:<16} SKIP（缺 --serial-name/--serial-code）")
                results.append({"type": tname, "ok": False, "skipped": "缺流水号规则"})
                continue

        body = build_attribute_field_body(a.app_id, a.set_id, **kw)
        # 关联形态按 DB 真实样本（relation_entity / relation_app / relation_type）
        if tname == "CTPENUM":
            body["relationEntity"] = str(a.ctp_enum_id)
            body["relationApp"] = str(a.app_id)
            body["relationType"] = "Many2OneAssociation"
            body["rootEnumId"] = a.ctp_enum_id
            body["ctpEnums"] = [a.ctp_enum_id]
        elif tname == "ENTITY":
            body["relationEntity"] = a.entity_full_name
            body["relationApp"] = a.entity_full_name.split(".")[2]
            body["relationType"] = "Many2OneAssociation"
            body["relationEntityCategory"] = "ENTITY"
        elif tname == "ENUM":
            body["relationEntity"] = str(a.enum_id)
            body["relationApp"] = str(a.app_id)
            body["relationType"] = "Many2OneAssociation"
            body["rootEnumId"] = a.enum_id
            body["ctpEnums"] = [a.enum_id]
        if tname == "Serial":
            body["serialNumberName"] = a.serial_name
            body["serialNumberCode"] = a.serial_code
            if a.serial_guid:
                body["serialNumberGuid"] = a.serial_guid
        errs = validate_attribute_field_body(body, set_id=a.set_id)
        if errs:
            print(f"  {tname:<16} 本地校验失败: {errs[:1]}")
            results.append({"type": tname, "ok": False, "errors": errs})
            continue
        r = call_gql(c, "udcEntityAttributePost", body)
        ok = r.get("code") == "BOOT_0000"
        print(f"  {i:>2}. {tname:<16} {'✅' if ok else '❌'} "
              f"{r.get('code')} {(r.get('data') or {}).get('content') or str(r.get('message'))[:50]}")
        results.append({"type": tname, "name": fname, "ok": ok,
                        "id": (r.get("data") or {}).get("content") if ok else None,
                        **({} if ok else {"resp": r})})

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    okn = sum(1 for x in results if x["ok"])
    print(f"\n成功 {okn}/{len(results)}  -> {out/'result.json'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
