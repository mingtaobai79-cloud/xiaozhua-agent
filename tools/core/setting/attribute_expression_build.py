"""字段集：给 txtCompute 字段写入真实表达式（走 expression 域三段链）。

依据（仓库已有事实）：
  core/facts/udc/write-chain/expression-token-type-domain.md
  components/udc/attribute_expression_constraints.py

三段链：
  1) POST /udc/expression/schema     {ids:[实体id], paramType:"ENTITY", upsource:true, serverName:"udc"}
       ★ 不能带 appId（带上报 BOOT_3000）
  2) POST /udc/expression/check      {tokens, resultTypeInfo, schemas, isMultiSelect}  → Boolean
  3) POST /udc/expression/transform  ExpressionSaveDto → 双态 designData + runtimeData
  4) GraphQL udcEntityAttributeUpdatePost 落库 expressionDesignData/RuntimeData + calculate

token 形状：{uid, type, value, desc, subOps?, controlData?}
type 值域：CONSTANT / VARIABLE / SYSTEM / FUNCTION / OPERATOR（恰 5 值）

用法：
  python tools/core/setting/attribute_expression_build.py --list
  python tools/core/setting/attribute_expression_build.py --run \
      --set-id <字段集id> --field-name txtCompute --i-have-write-authorization
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

APP_ID = None  # ★ 运行时由 --app-id / XIAOZHUA_APP_ID 提供（原写死值已移除）
ENTITY_ID = "474806313816300867"     # 小爪实验实体950795V2（expression schema 用它）

TOKEN_TYPES = ("CONSTANT", "VARIABLE", "SYSTEM", "FUNCTION", "OPERATOR")

# 预设表达式方案（每个都用不同的函数/表达式）
PLANS = {
    "sys_datetime": {
        "desc": "系统日期时间（SYSTEM 单 token）",
        "resultTypeInfo": "DATETIME",
        "tokens": [{"type": "SYSTEM", "value": "system.currentDateTime", "desc": "系统日期时间"}],
    },
    "sys_userid": {
        "desc": "当前用户ID（SYSTEM 单 token，BIGINTEGER）",
        "resultTypeInfo": "BIGINTEGER",
        "tokens": [{"type": "SYSTEM", "value": "system.currentUserId", "desc": "当前用户ID"}],
    },
    "concat": {
        "desc": "字符串拼接 CONCAT('前缀', 系统日期)",
        "resultTypeInfo": "STRING",
        "tokens": [{
            "type": "FUNCTION", "value": "concat", "desc": "拼接",
            "subOps": [
                [{"type": "CONSTANT", "value": "'前缀'", "desc": "前缀"}],
                [{"type": "SYSTEM", "value": "system.currentDate", "desc": "系统日期"}],
            ],
        }],
    },
    "constant": {
        "desc": "纯常量",
        "resultTypeInfo": "STRING",
        "tokens": [{"type": "CONSTANT", "value": "'固定值'", "desc": "固定值"}],
    },
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9231)
    ap.add_argument("--target-prefix", default="BCD2D805")
    ap.add_argument("--set-id", default="-3410968647846163890")
    ap.add_argument("--field-name", default="txtCompute")
    ap.add_argument("--plan", default="sys_datetime", choices=list(PLANS))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--i-have-write-authorization", action="store_true")
    ap.add_argument("--out", default=r"<HERMES_HOME>\cache\scratch\expr-build")
    a = ap.parse_args()

    if a.list or not a.run:
        print(f"预设表达式方案（{len(PLANS)} 个）：\n")
        for k, v in PLANS.items():
            print(f"  {k:<14} {v['desc']}")
            print(f"                 rt={v['resultTypeInfo']}  tokens={len(v['tokens'])}")
        if not a.run:
            return 0

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
                        return {"raw": raw[:400]}
            except Exception:
                pass
        return {"err": "TIMEOUT"}

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    plan = PLANS[a.plan]

    # 1) schema —— ★ 不能带 appId
    print("1) expression/schema ...")
    sch = post("/service/udc/expression/schema",
               {"ids": [ENTITY_ID], "paramType": "ENTITY", "upsource": True,
                "serverName": "udc"})
    schemas = (sch.get("data") or {}).get("content") or []
    print(f"   schemas: {len(schemas)} 个  resp={str(sch)[:120]}")

    # 2) 补 uid
    tokens = []
    for tk in plan["tokens"]:
        t = dict(tk)
        t["uid"] = str(uuid.uuid4()).replace("-", "")[:8]
        if "subOps" in t:
            newops = []
            for grp in t["subOps"]:
                g2 = []
                for s in grp:
                    s2 = dict(s)
                    s2["uid"] = str(uuid.uuid4()).replace("-", "")[:8]
                    g2.append(s2)
                newops.append(g2)
            t["subOps"] = newops
        tokens.append(t)

    save = {
        "resultTypeInfo": plan["resultTypeInfo"],
        "schemas": schemas,
        "tokens": tokens,
        "isMultiSelect": False,
        "terminalSupportType": "BACKEND",
        "sourceType": "ATTRIBUTESET",
        "appId": APP_ID,
    }

    # 3) check
    print("2) expression/check ...")
    chk = post("/service/udc/expression/check", save)
    print(f"   {json.dumps(chk, ensure_ascii=False)[:200]}")

    # 4) transform —— 产出 designData + runtimeData
    print("3) expression/transform ...")
    tr = post("/service/udc/expression/transform", save)
    content = (tr.get("data") or {}).get("content") or {}
    print(f"   keys: {list(content.keys())[:10]}")
    print(f"   resp: {json.dumps(tr, ensure_ascii=False)[:300]}")

    design = content.get("expressionDesignData") or content.get("designData")
    runtime = content.get("expressionRuntimeData") or content.get("runtimeData")
    if not design:
        print("   ⚠ transform 没返回 designData，尝试直接用 tokens 构造")
        design = {"resultTypeInfo": plan["resultTypeInfo"], "tokens": tokens, "context": []}
        runtime = design
    else:
        if isinstance(design, str):
            d = json.loads(design)
            if "context" not in d:
                d["context"] = []
            design = d
        if isinstance(runtime, str):
            runtime = json.loads(runtime)

    (out / f"transform-{a.plan}.json").write_text(
        json.dumps({"save": save, "check": chk, "transform": tr,
                    "design": design, "runtime": runtime},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    # 5) 落库 —— ★ REST /entity/attribute/update（不是 GraphQL！）
    #    正确姿势（tools/one-off/r36_ab.py 实证）：
    #      GET  /service/udc/entity/attribute/{id}   → 取完整 DTO
    #      改 expressionDesignData / expressionRuntimeData / calculate
    #      POST /service/udc/entity/attribute/update → 整体回传
    print("4) 落库（REST /entity/attribute/update）...")
    rd = post("/service/udc/attributeSet/select-attribute-list", {"attributeSetId": a.set_id})
    attrs = (rd.get("data") or {}).get("content") or []
    field_id = None
    for x in attrs:
        if x.get("name") == a.field_name:
            field_id = x.get("id")
            break
    if not field_id:
        print(f"   找不到字段 {a.field_name}")
        c.close(); return 3

    # GET 完整 DTO
    get_js = ("(async()=>{const r=await fetch('/service/udc/entity/attribute/%s',"
              "{credentials:'include'});return await r.text();})()" % field_id)
    raw_dto = c.evaluate(get_js, await_promise=True)
    dto = json.loads(raw_dto)["data"]["content"]
    print(f"   DTO keys: {len(dto)} 个")

    dto["calculate"] = "COMPUTE"
    dto["expressionDesignData"] = (json.dumps(design, ensure_ascii=False)
                                   if isinstance(design, dict) else design)
    dto["expressionRuntimeData"] = (json.dumps(runtime, ensure_ascii=False)
                                    if isinstance(runtime, dict) else runtime)

    wr = post("/service/udc/entity/attribute/update", dto)
    print(f"   {json.dumps(wr, ensure_ascii=False)[:250]}")

    # 6) 回读
    rd2 = post("/service/udc/attributeSet/select-attribute-list", {"attributeSetId": a.set_id})
    for x in ((rd2.get("data") or {}).get("content") or []):
        if x.get("name") == a.field_name:
            print(f"\n5) 回读 {a.field_name}:")
            print(f"   calculate = {x.get('calculate')!r}")
            ed = x.get("expressionDesignData")
            er = x.get("expressionRuntimeData")
            print(f"   expressionDesignData  = {str(ed)[:200]}")
            print(f"   expressionRuntimeData = {str(er)[:200]}")
            break

    print(f"\n-> {out}")
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
