"""设置域 · 字段集：字段级配置项实测（默认值/描述/控件/能力开关）。

覆盖用户点名的项：
  - 类型（18 种，见 attribute_set_type_matrix.py）
  - 默认值（默认值下拉 + 加号 → 系统变量 / 表达式）
  - 描述
  - WEB/移动端默认控件
  - 多选 / 必填 / 唯一 / 审计 / 全文检索（能力开关）
  - 加密 / 脱敏
  - 最小长度 / 最大长度 / 输入校验（正则）/ 格式错误提示

用法：
  python tools/core/setting/attribute_set_field_config.py --dump \
      --set-id <字段集id>
  python tools/core/setting/attribute_set_field_config.py --run \
      --set-id <字段集id> --i-have-write-authorization
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

# 控件候选（页面「WEB端默认控件」下拉）
WIDGETS = ("Input", "InputNumber", "TextArea", "Select", "DatePicker",
           "DateTimePicker", "TimePicker", "Switch", "Upload", "InputNumber")


def call_gql(c, op, body):
    q = ("mutation graphqlLoader ($params0: %sInputBody) { \n"
         "  data0: %s(body: $params0) { code message status data { content } } }" % (op, op))
    payload = {"query": q, "variables": {"params0": body}}
    js = ("(async()=>{const r=await fetch('/service/udc/graphql?%s',{method:'POST',credentials:'include',"
          "headers:{'Content-Type':'application/json'},body:%s});return await r.text();})()"
          % (op, json.dumps(json.dumps(payload, ensure_ascii=False))))
    return json.loads(c.evaluate(js, await_promise=True))["data"]["data0"]


def call_rest(c, path, body):
    js = ("(async()=>{const r=await fetch('%s',{method:'POST',credentials:'include',"
          "headers:{'Content-Type':'application/json'},body:%s});return await r.text();})()"
          % (path, json.dumps(json.dumps(body, ensure_ascii=False))))
    try:
        return json.loads(c.evaluate(js, await_promise=True))
    except Exception as exc:
        return {"err": str(exc)[:150]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--app-id", default=None)
    ap.add_argument("--set-id", required=True)
    ap.add_argument("--prefix", default="cfg")
    ap.add_argument("--ctp-enum-id", default="")
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\field-config")
    a = ap.parse_args()

    import urllib.request
    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    pages = [t for t in tgts if t.get("type") == "page"
             and f"appId={a.app_id}" in t.get("url", "")]
    if not pages:
        pages = [t for t in tgts if t.get("type") == "page" and "lowcode-test2" in t.get("url", "")]
    from providers.cdp import CdpClient
    c = CdpClient(a.port, allow_network=True, timeout=120)
    c.connect(target=pages[0])

    if a.dump or not a.run:
        r = call_rest(c, "/service/udc/attributeSet/select-attribute-list",
                      {"attributeSetId": a.set_id})
        attrs = (r.get("data") or {}).get("content") or []
        print(f"字段数: {len(attrs)}\n")
        for x in attrs:
            print(f"== {x.get('name')} / {x.get('caption')} / {x.get('dataType')}")
            interesting = {
                "notNull": x.get("notNull"), "uniqueness": x.get("uniqueness"),
                "multiSelect": x.get("multiSelect"), "searchable": x.get("searchable"),
                "auditLog": x.get("auditLog"),
                "minLength": x.get("minLength"), "maxLength": x.get("maxLength"),
                "decimalDigits": x.get("decimalDigits"),
                "dataFormat": x.get("dataFormat"),
                "patternMessage": x.get("patternMessage"),
                "defaultValue": x.get("defaultValue"),
                "defaultValueCaption": x.get("defaultValueCaption"),
                "defaultValueSystemVariable": x.get("defaultValueSystemVariable"),
                "defaultValueIsChange": x.get("defaultValueIsChange"),
                "enableEncryption": x.get("enableEncryption"),
                "encryption": x.get("encryption"),
                "enableDesensitization": x.get("enableDesensitization"),
                "desensitization": x.get("desensitization"),
                "description": x.get("description"),
                "widgetConfig": x.get("widgetConfig"),
            }
            print("   " + json.dumps({k: v for k, v in interesting.items() if v not in (None, "", False, 0)},
                                     ensure_ascii=False))
        c.close()
        return 0

    if not a.i_have_write_authorization:
        print("写操作需显式确认：加 --i-have-write-authorization")
        c.close()
        return 1

    def mk(name, caption, dtype, **kw):
        b = build_attribute_field_body(a.app_id, a.set_id, name=name,
                                       caption=caption, data_type=dtype)
        b.update(kw)
        return b

    cases = []

    # 1) 能力开关：必填 / 唯一 / 多选 / 审计 / 全文检索
    cases.append(("能力-必填", mk(f"{a.prefix}Req", "必填测试", "STRING", notNull=True)))
    cases.append(("能力-唯一", mk(f"{a.prefix}Uni", "唯一测试", "STRING", uniqueness=True)))
    _mul = mk(f"{a.prefix}Mul", "多选测试", "CTPENUM", multiSelect=True)
    _mul["relationEntity"] = a.ctp_enum_id or ""
    _mul["relationApp"] = a.app_id
    _mul["relationType"] = "Many2OneAssociation"
    _mul["rootEnumId"] = a.ctp_enum_id or ""
    _mul["ctpEnums"] = [a.ctp_enum_id] if a.ctp_enum_id else []
    cases.append(("能力-多选", _mul))
    cases.append(("能力-审计", mk(f"{a.prefix}Aud", "审计测试", "STRING", auditLog=True)))
    cases.append(("能力-检索", mk(f"{a.prefix}Sea", "检索测试", "STRING", searchable=True)))

    # 2) 长度 / 精度
    cases.append(("长度-短", mk(f"{a.prefix}Len", "长度测试", "STRING",
                               minLength=2, maxLength=8)))
    # DECIMAL 必须同时给 maxLength（= 总精度，真实样本 20/22/24）与 decimalDigits
    cases.append(("精度-小数", mk(f"{a.prefix}Dec", "精度测试", "DECIMAL",
                                 decimalDigits=3, maxLength=20)))

    # 3) 默认值（固定值 / 系统变量）
    cases.append(("默认值-固定", mk(f"{a.prefix}Dft", "默认值固定", "STRING",
                                   defaultValue="固定默认值")))
    cases.append(("默认值-系统变量", mk(f"{a.prefix}Sys", "默认值系统变量", "DATE",
                                      defaultValueIsChange=False,
                                      defaultValueSystemVariable="CURRENT_DATE")))

    # 4) 描述
    cases.append(("描述", mk(f"{a.prefix}Des", "描述测试", "STRING",
                            description="这是字段描述，用于说明用途")))

    # 5) 输入校验（正则 + 提示）
    cases.append(("输入校验", mk(f"{a.prefix}Pat", "正则校验", "STRING",
                                dataFormat="^[0-9]{6}$",
                                patternMessage="必须是6位数字")))

    # 6) 加密 / 脱敏
    # 加密 / 脱敏枚举值（反编译 boot-core MaskType + EncryptionType 实拉）
    #   EncryptionType: NOT_ENCRYPTION(0) / REVERSIBLE_ENCRYPTION(1) / DECRYPT_ONLY(2)
    #   MaskType:       None(-1) / Auto(0) / All(1) / Custom(2)
    cases.append(("加密", mk(f"{a.prefix}Enc", "加密测试", "STRING",
                            enableEncryption=True, encryption="REVERSIBLE_ENCRYPTION")))
    cases.append(("脱敏-全", mk(f"{a.prefix}MskAll", "脱敏全", "STRING",
                              enableDesensitization=True, desensitization="All")))
    cases.append(("脱敏-自动", mk(f"{a.prefix}MskAuto", "脱敏自动", "STRING",
                                enableDesensitization=True, desensitization="Auto")))
    cases.append(("脱敏-自定义", mk(f"{a.prefix}MskCus", "脱敏自定义", "STRING",
                                  enableDesensitization=True, desensitization="Custom")))
    cases.append(("敏感词", mk(f"{a.prefix}Swc", "敏感词测试", "STRING",
                              enableSensitiveWordCheck=True)))

    # 7) 控件配置（WEB / 移动端）
    for wi, w in enumerate(("Input", "InputNumber", "TextArea", "Select")):
        cases.append((f"控件-{w}", mk(f"{a.prefix}Wg{wi:02d}", f"控件{w}", "STRING",
                                     widgetConfig=json.dumps(
                                         {"pc": w, "mobile": w, "list": True,
                                          "detail": True, "quickSearch": True},
                                         ensure_ascii=False, separators=(",", ":")))))

    results = []
    for label, body in cases:
        errs = validate_attribute_field_body(body, set_id=a.set_id)
        if errs:
            print(f"  {label:<16} 本地校验: {errs[:1]}")
            results.append({"case": label, "ok": False, "errors": errs})
            continue
        r = call_gql(c, "udcEntityAttributePost", body)
        ok = r.get("code") == "BOOT_0000"
        print(f"  {label:<16} {'✅' if ok else '❌'} {r.get('code')} "
              f"{str((r.get('data') or {}).get('content') or r.get('message'))[:44]}")
        results.append({"case": label, "ok": ok, "name": body["name"],
                        "id": (r.get("data") or {}).get("content") if ok else None,
                        **({} if ok else {"resp": r})})

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    print(f"\n成功 {sum(1 for x in results if x['ok'])}/{len(results)}  -> {out/'result.json'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
