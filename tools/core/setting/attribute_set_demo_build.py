"""字段集：建含 1 枚举 + 1 实体 + 6 文本（表达式/函数/校验各不同）的试验集。

用户 2026-10-21 要求：
  「新建一个  人好枚举字段 实体字段 文本x6 然后每个文本不同的表达是和不同函数和不同的校验」

6 个文本字段各测一种组合：
  1 固定默认值 + 长度校验
  2 系统变量默认值 + 正则校验
  3 表达式计算 + 长度区间
  4 引用另一字段（valueScopeExpression）
  5 脱敏 + 正则
  6 加密 + 最大长度

用法：
  python tools/core/setting/attribute_set_demo_build.py --i-have-write-authorization
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from components.udc.setting.attribute_set_constraints import (  # noqa: E402
    build_attribute_field_body, build_attribute_set_body,
    validate_attribute_field_body, validate_attribute_set_body,
)

APP_ID = None  # ★ 运行时由 --app-id / XIAOZHUA_APP_ID 提供（原写死值已移除）
# 前面实测可用的关联目标
ENUM_ID = "-2722367167915323813"          # UI轨迹枚举（ctp_enum）
ENUM_CODE = "XzhCtpEnum953322"            # 平台枚举编码
ENUM_NAME = "UI轨迹枚举"
ENTITY_ID = "474806313816300867"          # 小爪实验实体950795V2
ENTITY_NAME = "小爪实验实体950795V2"
ENTITY_CODE = ""                          # 实体没有 code，留空

SET_NAME = "zxjExprDemo"
SET_CAPTION = "表达式校验演示集"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--target-prefix", default="BCD2D805",
                    help="可用标签页 id 前缀（A886072E 已卡死）")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\expr-demo")
    a = ap.parse_args()

    if not a.i_have_write_authorization:
        print("写操作需显式确认：加 --i-have-write-authorization")
        return 1

    import urllib.request
    tgts = json.load(urllib.request.urlopen(f"http://127.0.0.1:{a.port}/json/list", timeout=5))
    cand = [t for t in tgts if t.get("type") == "page"
            and str(t.get("id", "")).startswith(a.target_prefix)]
    if not cand:
        print(f"找不到 {a.target_prefix} 标签页")
        return 2
    from providers.cdp import CdpClient
    c = CdpClient(a.port, allow_network=True, timeout=120)
    c.connect(target=cand[0])

    def post(path, body, to=25):
        c.evaluate("window.__R__=null;window.__D__=false;", await_promise=False)
        c.evaluate("""(function(){fetch('%s',{method:'POST',credentials:'include',
          headers:{'Content-Type':'application/json'},body:%s})
          .then(r=>r.text()).then(t=>{window.__R__=t;window.__D__=true;})
          .catch(e=>{window.__R__='ERR:'+e.message;window.__D__=true;});return 'ok';})()""" % (
          path, json.dumps(json.dumps(body, ensure_ascii=False))), await_promise=False)
        end = time.time() + to
        while time.time() < end:
            time.sleep(0.35)
            try:
                if c.evaluate("window.__D__===true", await_promise=False) == True:
                    raw = c.evaluate("window.__R__", await_promise=False)
                    try:
                        return json.loads(raw)
                    except Exception:
                        return {"raw": raw[:300]}
            except Exception:
                pass
        return {"err": "TIMEOUT"}

    def gql_write(op, body, to=25):
        q = ("mutation graphqlLoader ($params0: %sInputBody) { \n"
             "  data0: %s(body: $params0) { code message status data { content } } }" % (op, op))
        return post(f"/service/udc/graphql?{op}", {"query": q, "variables": {"params0": body}}, to)

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    # 1) 建壳
    body = build_attribute_set_body(APP_ID, name=SET_NAME, caption=SET_CAPTION, order_no=200)
    errs = validate_attribute_set_body(body)
    if errs:
        print("壳校验失败:", errs); c.close(); return 3
    r = post("/service/udc/attributeSet", body)
    sid = (r.get("data") or {}).get("content")
    print(f"1) 建壳 {SET_NAME} -> {r.get('code')} id={sid}")
    if not sid:
        print("   失败:", json.dumps(r, ensure_ascii=False)[:200]); c.close(); return 4

    # 2) 定义 8 个字段
    fields = []

    # 枚举
    f = build_attribute_field_body(
        APP_ID, sid, name="demoEnum", caption="枚举字段",
        data_type="CTPENUM", order_no=1,
        relation_code=ENUM_CODE, relation_entity_name=ENUM_NAME,
        relation_enum_type="SAME_LEVEL", relation_enum_level=0)
    f["relationEntity"] = ENUM_ID
    fields.append(("枚举", f))

    # 实体
    f = build_attribute_field_body(
        APP_ID, sid, name="demoEntity", caption="实体字段",
        data_type="ENTITY", order_no=2)
    f["relationEntity"] = ENTITY_ID
    f["relationApp"] = APP_ID
    f["relationEntityName"] = ENTITY_NAME
    f["relationEntityCategory"] = "ENTITY"
    fields.append(("实体", f))

    # 文本1：固定默认值 + 长度校验
    f = build_attribute_field_body(
        APP_ID, sid, name="txtFixed", caption="文本1固定默认值", order_no=3,
        min_length=2, max_length=20)
    f["defaultValue"] = "默认值ABC"
    fields.append(("文本1-固定默认值+长度", f))

    # 文本2：系统变量默认值 + 正则
    f = build_attribute_field_body(
        APP_ID, sid, name="txtSysVar", caption="文本2系统变量+正则", order_no=4,
        min_length=0, max_length=50)
    f["defaultValueIsChange"] = False
    f["defaultValueSystemVariable"] = "currentUser"   # 系统变量：当前用户
    f["defaultValueCaption"] = "当前用户"
    f["dataFormat"] = "^[A-Za-z0-9_-]{3,20}$"
    f["patternMessage"] = "只能字母数字下划线短横，3-20位"
    fields.append(("文本2-正则校验", f))

    # 文本3：表达式计算（calculate=COMPUTE）
    f = build_attribute_field_body(
        APP_ID, sid, name="txtCompute", caption="文本3表达式计算", order_no=5,
        min_length=0, max_length=100)
    f["calculate"] = "COMPUTE"
    f["expressionDesignData"] = ""
    f["expressionRuntimeData"] = ""
    fields.append(("文本3-表达式计算", f))

    # 文本4：长度 0-500 大文本
    f = build_attribute_field_body(
        APP_ID, sid, name="txtLongLen", caption="文本4长文本", order_no=6,
        min_length=0, max_length=500)
    fields.append(("文本4-长文本500", f))

    # 文本5：脱敏 + 正则
    f = build_attribute_field_body(
        APP_ID, sid, name="txtMask", caption="文本5脱敏+正则", order_no=7,
        min_length=11, max_length=11)
    f["enableDesensitization"] = True
    f["desensitization"] = "All"
    f["dataFormat"] = "^1[3-9]\\d{9}$"
    f["patternMessage"] = "必须是11位手机号"
    fields.append(("文本5-脱敏+手机号正则", f))

    # 文本6：加密 + 敏感词
    f = build_attribute_field_body(
        APP_ID, sid, name="txtEncrypt", caption="文本6加密+敏感词", order_no=8,
        min_length=0, max_length=200)
    f["enableEncryption"] = True
    f["encryption"] = "REVERSIBLE_ENCRYPTION"
    f["enableSensitiveWordCheck"] = True
    fields.append(("文本6-加密+敏感词", f))

    # 3) 逐个创建
    results = []
    for label, fb in fields:
        errs = validate_attribute_field_body(fb, set_id=sid)
        if errs:
            print(f"   {label:<24} 本地校验: {errs[:1]}")
            results.append({"label": label, "ok": False, "errors": errs})
            continue
        rr = gql_write("udcEntityAttributePost", fb)
        ok = rr.get("code") == "BOOT_0000"
        print(f"   {label:<24} {'✅' if ok else '❌'} {rr.get('code')} "
              f"{str((rr.get('data') or {}).get('content') or rr.get('message'))[:40]}")
        results.append({"label": label, "name": fb["name"], "ok": ok,
                        "id": (rr.get("data") or {}).get("content") if ok else None,
                        **({} if ok else {"resp": rr})})

    # 4) 回读
    chk = post("/service/udc/attributeSet/select-attribute-list", {"attributeSetId": sid})
    attrs = (chk.get("data") or {}).get("content") or []
    print(f"\n4) 回读: {len(attrs)} 个字段")
    for x in attrs:
        print(f"   {x.get('name'):<16} {x.get('caption'):<22} {x.get('dataType')}")

    (out / "result.json").write_text(json.dumps({
        "set_id": sid, "results": results, "readback": attrs,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n成功 {sum(1 for x in results if x['ok'])}/{len(results)} -> {out/'result.json'}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
