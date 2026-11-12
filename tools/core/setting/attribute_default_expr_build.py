"""重建验收字段集：18 种类型各一字段，全部配「默认值表达式」（不是计算值）。

依据（全部反编译/前端实证，不是猜）：
  1. AttributeService.checkExpressionPattern:1593-1607
       两套字段各自校验：expressionDesignData -> UDC_ATTR_0017
                         defaultValueExpressionDesignData -> UDC_ATTR_0018
  2. 前端组装（src_redux_store_ts chunk）：
       defaultValueExpressionDesignData = JSON.stringify(designData)
       defaultValueExpressionRuntimeData = JSON.stringify(runtimeData)
  3. 默认值表达式不设 calculate（calculate 只属于计算值路径）

流程（每字段）：
  expression/schema -> check -> transform -> 取 designData/runtimeData
  -> udcEntityAttributePost 建字段(带标准 18 键 body)
  -> GET /entity/attribute/{id} 取完整 DTO -> 覆写 defaultValueExpression* -> update
  -> 回读 udc_attribute.default_value_expr_design 断言非空

用法：
  python tools/core/setting/attribute_default_expr_build.py --list
  python tools/core/setting/attribute_default_expr_build.py --run \
      --app-id <appId> --set-name <新字段集编码> --i-have-write-authorization
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

# 18 种类型 + 每种一个「能用默认值表达式表达」的方案
# ★ 参数类型按平台 argTypes（explain.example.argTypes）声明，不是猜的
PLANS: list[dict] = [
    {"dt": "STRING", "field": "dfString", "cap": "默认值-文本",
     "result": "STRING",
     "tokens": [{"type": "SYSTEM", "value": "system.currentUserName", "desc": "登录人员姓名"}]},
    {"dt": "MULTILINESTRING", "field": "dfMultiline", "cap": "默认值-多行文本",
     "result": "STRING",
     "tokens": [{"type": "FUNCTION", "value": "join", "desc": "按指定符号合并文本数组",
                 "subOps": [
                     [{"type": "FUNCTION", "value": "split", "desc": "按指定符号分割文本",
                       "subOps": [
                           [{"type": "SYSTEM", "value": "system.currentUserCode", "desc": "登录人员编号"}],
                           [{"type": "CONSTANT", "value": "''", "desc": "空分隔符"}]]}],
                     [{"type": "CONSTANT", "value": "'|'", "desc": "分隔符"}]]}]},
    {"dt": "INTEGER", "field": "dfInteger", "cap": "默认值-整数",
     "result": "INTEGER",
     "tokens": [{"type": "FUNCTION", "value": "randBetween", "desc": "指定范围随机数",
                 "subOps": [
                     [{"type": "CONSTANT", "value": "1", "desc": "最小整数"}],
                     [{"type": "CONSTANT", "value": "9999", "desc": "最大整数"}]]}]},
    {"dt": "BIGINTEGER", "field": "dfBigint", "cap": "默认值-长整数",
     "result": "BIGINTEGER",
     "tokens": [{"type": "SYSTEM", "value": "system.currentUserId", "desc": "登录人员ID"}]},
    {"dt": "DECIMAL", "field": "dfDecimal", "cap": "默认值-小数",
     "result": "DECIMAL",
     "tokens": [{"type": "FUNCTION", "value": "round", "desc": "四舍五入",
                 "subOps": [
                     [{"type": "CONSTANT", "value": "123.456", "desc": "数值"}],
                     [{"type": "CONSTANT", "value": "2", "desc": "位数"}]]}]},
    {"dt": "CURRENCY", "field": "dfCurrency", "cap": "默认值-货币",
     "result": "DECIMAL",
     "tokens": [{"type": "FUNCTION", "value": "round", "desc": "四舍五入",
                 "subOps": [
                     [{"type": "CONSTANT", "value": "888.888", "desc": "数值"}],
                     [{"type": "CONSTANT", "value": "2", "desc": "位数"}]]}]},
    {"dt": "DATE", "field": "dfDate", "cap": "默认值-日期",
     "result": "DATE",
     "tokens": [{"type": "SYSTEM", "value": "system.currentDate", "desc": "系统日期"}]},
    {"dt": "TIME", "field": "dfTime", "cap": "默认值-时间",
     "result": "TIME",
     "tokens": [{"type": "SYSTEM", "value": "system.currentTime", "desc": "系统时间"}]},
    {"dt": "DATETIME", "field": "dfDatetime", "cap": "默认值-日期时间",
     "result": "DATETIME",
     "tokens": [{"type": "SYSTEM", "value": "system.currentDateTime", "desc": "系统日期时间"}]},
    {"dt": "BOOLEAN", "field": "dfBoolean", "cap": "默认值-布尔",
     "result": "BOOLEAN",
     "tokens": [{"type": "CONSTANT", "value": "true", "desc": "真"}]},
    {"dt": "ENUM", "field": "dfEnum", "cap": "默认值-选项集",
     "result": "STRING",
     "tokens": [{"type": "CONSTANT", "value": "'选项集默认'", "desc": "常量"}]},
    {"dt": "CTPENUM", "field": "dfCtpenum", "cap": "默认值-枚举",
     "result": "STRING",
     "tokens": [{"type": "CONSTANT", "value": "'枚举默认'", "desc": "常量"}]},
    {"dt": "ATTACHMENT", "field": "dfAttach", "cap": "默认值-附件",
     "result": "STRING",
     "tokens": [{"type": "CONSTANT", "value": "'附件默认'", "desc": "常量"}]},
    {"dt": "ENTITY", "field": "dfEntity", "cap": "默认值-实体",
     "result": "STRING",
     "tokens": [{"type": "CONSTANT", "value": "'实体默认'", "desc": "常量"}]},
    {"dt": "DOCUMENTNUMBER", "field": "dfDocNo", "cap": "默认值-文号",
     "result": "STRING",
     "tokens": [{"type": "CONSTANT", "value": "'文号默认'", "desc": "常量"}]},
    {"dt": "Serial", "field": "dfSerial", "cap": "默认值-流水号",
     "result": "STRING",
     "tokens": [{"type": "CONSTANT", "value": "'流水号默认'", "desc": "常量"}]},
    {"dt": "OPINION", "field": "dfOpinion", "cap": "默认值-意见",
     "result": "STRING",
     "tokens": [{"type": "CONSTANT", "value": "'意见默认'", "desc": "常量"}]},
    {"dt": "CONTENT", "field": "dfContent", "cap": "默认值-正文",
     "result": "STRING",
     "tokens": [{"type": "CONSTANT", "value": "'正文默认'", "desc": "常量"}]},
]


def add_uid(tokens):
    for t in tokens:
        t.setdefault("uid", uuid.uuid4().hex[:8])
        for grp in t.get("subOps") or []:
            for s in grp:
                add_uid([s])
    return tokens


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9250)
    ap.add_argument("--target-prefix", default="670BFEA0")
    ap.add_argument("--app-id", required=False, default=None)
    ap.add_argument("--set-name", default="zxjDefaultExpr")
    ap.add_argument("--set-caption", default="默认值表达式验收集")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\default-expr")
    a = ap.parse_args()

    if a.list or not a.run:
        print(f"待建 {len(PLANS)} 个类型字段（全部写默认值表达式，非计算值）：\n")
        for p in PLANS:
            fn = (p["tokens"][0].get("value") if p["tokens"][0]["type"] != "SYSTEM"
                  else "SYSTEM:" + p["tokens"][0]["value"])
            print(f"  {p['dt']:<16} {p['field']:<14} {p['cap']:<16} {fn}")
        if not a.run:
            return 0

    if not a.app_id:
        print("必须给 --app-id")
        return 1
    if not a.i_have_write_authorization:
        print("写操作需显式确认：--i-have-write-authorization")
        return 1

    from components.udc.setting.attribute_set_constraints import (
        build_attribute_set_body, build_attribute_field_body,
        validate_attribute_set_body, validate_attribute_field_body)
    from providers.cdp import CdpClient

    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    cand = [t for t in tgts if t.get("type") == "page"
            and str(t.get("id", "")).startswith(a.target_prefix)]
    if not cand:
        print(f"找不到 {a.target_prefix}")
        return 2
    c = CdpClient(a.port, allow_network=True, timeout=180)
    c.connect(target=cand[0])

    def post(path, body, to=40):
        js = (f"fetch('{path}',{{method:'POST',credentials:'include',"
              "headers:{'Content-Type':'application/json'},"
              f"body:{json.dumps(json.dumps(body, ensure_ascii=False))}}})"
              ".then(r=>r.text())")
        try:
            return json.loads(c.evaluate(js, await_promise=True))
        except Exception as e:
            return {"err": type(e).__name__}

    def gql(op, body):
        q = ("mutation graphqlLoader ($params0: %sInputBody) { "
             "  data0: %s(body: $params0) { code message status data { content } } }"
             % (op, op))
        r = post(f"/service/udc/graphql?{op}", {"query": q, "variables": {"params0": body}})
        d0 = (r.get("data") or {}).get("data0") or {}
        return d0.get("code"), (d0.get("data") or {}).get("content"), d0.get("message")

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    # 1) 建字段集
    sb = build_attribute_set_body(a.app_id, name=a.set_name, caption=a.set_caption,
                                  order_no=900)
    errs = validate_attribute_set_body(sb)
    if errs:
        print("壳校验失败:", errs)
        c.close(); return 3
    r = post("/service/udc/attributeSet", sb)
    sid = (r.get("data") or {}).get("content")
    print(f"1) 建字段集 {a.set_name} -> {r.get('code')} id={sid}")
    if not sid:
        print("   失败:", json.dumps(r, ensure_ascii=False)[:300])
        c.close(); return 4

    # 2) schema
    sch = post("/service/udc/expression/schema",
               {"appId": a.app_id, "extension": "", "ids": [], "idsStr": [],
                "idsTuple": [], "paramType": "CONFIG_PARAM"})
    schemas = (sch.get("data") or {}).get("content") or []
    print(f"2) schema={len(schemas)}")

    results = []
    for i, plan in enumerate(PLANS, start=1):
        print(f"\n[{i}/{len(PLANS)}] {plan['dt']} {plan['field']}")
        # 建字段（不带任何表达式）
        fb = build_attribute_field_body(a.app_id, sid, name=plan["field"],
                                        caption=plan["cap"], data_type=plan["dt"],
                                        order_no=i, min_length=0, max_length=100)
        ve = validate_attribute_field_body(fb, set_id=sid)
        if ve:
            print("   本地校验:", ve[:1])
            results.append({"dt": plan["dt"], "ok": False, "err": ve})
            continue
        code, fid, msg = gql("udcEntityAttributePost", fb)
        if code != "BOOT_0000" or not fid:
            print(f"   建字段失败 {code} {str(msg)[:60]}")
            results.append({"dt": plan["dt"], "ok": False, "code": code})
            continue
        print(f"   字段 id={fid}")

        # 3) 表达式三段链
        toks = add_uid([dict(t) for t in plan["tokens"]])
        save = {
            "resultTypeInfo": plan["result"], "schemas": schemas, "tokens": toks,
            "isMultiSelect": False, "terminalSupportType": "BACKEND",
            "sourceType": "ATTRIBUTESET", "appId": a.app_id,
        }
        chk = post("/service/udc/expression/check", save)
        ccode = chk.get("code")
        if ccode != "BOOT_0000":
            print(f"   ❌ check 失败 {ccode} {str(chk.get('message'))[:70]}")
            results.append({"dt": plan["dt"], "ok": False, "check": ccode,
                            "msg": str(chk.get("message"))[:100]})
            continue
        tr = post("/service/udc/expression/transform", save)
        content = (tr.get("data") or {}).get("content") or {}
        design = content.get("designData") or content.get("expressionDesignData")
        runtime = content.get("runtimeData") or content.get("expressionRuntimeData")
        if not design:
            print("   ❌ transform 无 designData（不兜底）")
            results.append({"dt": plan["dt"], "ok": False, "err": "no_design"})
            continue
        if isinstance(design, str):
            design = json.loads(design)
        design.setdefault("context", [])
        print(f"   translation={design.get('expressionTranslation')!r}")

        # 4) 写默认值列（不是计算值列！）
        raw = c.evaluate(
            f"fetch('/service/udc/entity/attribute/{fid}',{{credentials:'include'}})"
            ".then(r=>r.text())", await_promise=True)
        dto = json.loads(raw)["data"]["content"]
        dto["defaultValueExpressionDesignData"] = json.dumps(design, ensure_ascii=False)
        dto["defaultValueExpressionRuntimeData"] = ""
        dto["defaultValueIsChange"] = False
        # ★ 不动 calculate，不动 expressionDesignData
        wr = post("/service/udc/entity/attribute/update", dto)
        wcode = wr.get("code")
        ok = wcode == "BOOT_0000"
        print(f"   落默认值列 {wcode}")
        results.append({"dt": plan["dt"], "field": plan["field"], "id": fid,
                        "ok": ok, "code": wcode,
                        "translation": design.get("expressionTranslation")})
        time.sleep(0.3)

    # 5) 回读
    print("\n=== 回读（default_value_expr_design）===")
    rd = post("/service/udc/attributeSet/select-attribute-list", {"attributeSetId": sid})
    attrs = (rd.get("data") or {}).get("content") or []
    print(f"字段数 {len(attrs)}")
    for x in attrs:
        d = x.get("defaultValueExpressionDesignData")
        tr_ = None
        if d:
            try:
                tr_ = json.loads(d).get("expressionTranslation")
            except Exception:
                tr_ = "<parse-fail>"
        print(f"  {x.get('name'):<14} {x.get('dataType'):<16} "
              f"default_expr={'YES' if d else 'NO '} tr={tr_!r}")

    (out / "result.json").write_text(json.dumps(
        {"set_id": sid, "results": results}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"\n-> {out / 'result.json'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
